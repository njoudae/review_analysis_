import requests
from .config import ACTOR_ID, APIFY_TOKEN


def run_apify(actor_input: dict) -> list[dict]:
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    r = requests.post(url, params={"token": APIFY_TOKEN}, json=actor_input, timeout=320)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def extract_apify_reviews(items: list[dict]) -> list[dict]:
    if not items:
        return []


    if isinstance(items[0], dict) and "reviews" in items[0]:
        out = []
        for place in items:
            title = place.get("title")
            city = place.get("city")

            for r in (place.get("reviews") or []):
                if title and not r.get("title"):
                    r["title"] = title
                r["branch_city"] = city
                out.append(r)
        return out

    return items
