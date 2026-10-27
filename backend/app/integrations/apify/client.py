import hashlib
import json
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings


class ApifyClient:
    def __init__(self, token: str | None = None, actor_id: str | None = None):
        self.token = token or settings.apify_token
        self.actor_id = actor_id or settings.actor_id

    @retry(
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def run(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.token or not self.actor_id:
            raise RuntimeError("APIFY_TOKEN and ACTOR_ID are required")
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/run-sync-get-dataset-items"
        response = requests.post(url, params={"token": self.token}, json=actor_input, timeout=320)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Apify returned a non-list dataset payload")
        return payload


def build_actor_input(source_url: str) -> dict[str, Any]:
    return {
        "language": "ar",
        "maxReviews": 100,
        "reviewsSort": "newest",
        "reviewsStartDate": "30 days",
        "scrapePlaceDetailPage": True,
        "scrapeReviewsPersonalData": False,
        "startUrls": [{"url": source_url}],
    }


def _stable_external_id(item: dict[str, Any]) -> str:
    existing = item.get("reviewId") or item.get("review_id") or item.get("id")
    if existing:
        return str(existing)
    basis = json.dumps(
        {
            "name": item.get("name") or item.get("reviewerName"),
            "date": item.get("publishedAtDate") or item.get("publishAt"),
            "text": item.get("text") or "",
            "stars": item.get("stars"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"derived:{hashlib.sha256(basis.encode('utf-8')).hexdigest()}"


def normalize_reviews(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        place_reviews = item.get("reviews")
        candidates = place_reviews if isinstance(place_reviews, list) else [item]
        for raw in candidates:
            if not isinstance(raw, dict):
                continue
            review = dict(raw)
            external_id = _stable_external_id(review)
            if external_id in seen:
                continue
            seen.add(external_id)
            normalized.append(
                {
                    "external_review_id": external_id,
                    "reviewer_name": review.get("name") or review.get("reviewerName"),
                    "rating": review.get("stars"),
                    "review_text": review.get("text") or "",
                    "published_at": review.get("publishedAtDate") or review.get("publishAt"),
                    "review_url": review.get("reviewUrl"),
                    "likes": review.get("likesCount"),
                    "local_guide": bool(review.get("isLocalGuide")),
                    "detailed_ratings": review.get("reviewDetailedRating") or {},
                    "context": review.get("reviewContext") or {},
                    "images": review.get("reviewImageUrls") or [],
                    "owner_reply": {
                        "text": review.get("responseFromOwnerText"),
                        "date": review.get("responseFromOwnerDate"),
                    },
                    "raw_json": review,
                }
            )
    return normalized

