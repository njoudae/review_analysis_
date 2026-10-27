import argparse
import json
import sqlite3
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Branch, Review, ReviewSource, ReviewState
from app.services.processing import parse_datetime


def decode(value, default):
    try:
        return json.loads(value) if value else default
    except json.JSONDecodeError:
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy legacy reviews into the normalized database without deleting the source")
    parser.add_argument("legacy_db", type=Path)
    parser.add_argument("organization_id")
    parser.add_argument("branch_id")
    args = parser.parse_args()
    if not args.legacy_db.is_file():
        raise SystemExit(f"Legacy database not found: {args.legacy_db}")

    legacy = sqlite3.connect(f"file:{args.legacy_db.resolve()}?mode=ro", uri=True)
    legacy.row_factory = sqlite3.Row
    rows = legacy.execute("SELECT * FROM reviews ORDER BY inserted_at").fetchall()
    with SessionLocal() as db:
        branch = db.get(Branch, args.branch_id)
        if not branch or branch.organization_id != args.organization_id:
            raise SystemExit("Branch does not belong to the supplied organization")
        source = db.scalar(select(ReviewSource).where(ReviewSource.branch_id == branch.id, ReviewSource.provider == "google_maps"))
        if not source:
            raise SystemExit("Branch has no Google Maps review source")
        inserted = 0
        for row in rows:
            exists = db.scalar(select(Review.id).where(Review.source_id == source.id, Review.external_review_id == row["reviewId"]))
            if exists:
                continue
            raw = decode(row["raw_json"], {})
            db.add(
                Review(
                    organization_id=args.organization_id,
                    branch_id=args.branch_id,
                    source_id=source.id,
                    external_review_id=row["reviewId"],
                    reviewer_name=raw.get("name") or raw.get("reviewerName"),
                    rating=row["stars"],
                    review_text=row["text"] or "",
                    published_at=parse_datetime(row["publishedAtDate"]),
                    review_url=row["reviewUrl"],
                    likes=row["likesCount"],
                    local_guide=bool(row["isLocalGuide"]),
                    detailed_ratings=decode(row["reviewDetailedRating_json"], {}),
                    context=decode(row["reviewContext_json"], {}),
                    images=decode(row["images_json"], []),
                    owner_reply={"date": row["owner_response_date"], "text": row["owner_response_text"]},
                    raw_json=raw,
                    processing_state=ReviewState.PENDING_ANALYSIS,
                )
            )
            inserted += 1
        db.commit()
    legacy.close()
    print(f"Copied {inserted} reviews. The legacy database was opened read-only and was not modified.")


if __name__ == "__main__":
    main()

