import json

from app.config import INPUT_PATH, APIFY_TOKEN, ACTOR_ID, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from app.db import db_init, db_has_review, db_save_review, db_has_analysis, db_save_analysis, get_state, set_state
from app.apify_client import run_apify, extract_apify_reviews
from app.llm import should_send_to_llm, build_signal_bundle, analyze_review_full, should_alert_full
from app.helpers import now_utc_iso, print_db_snapshot

from app.formatter import build_alert_message
from app.telegram import send_telegram_message


def main():
    required = {
        "APIFY_TOKEN": APIFY_TOKEN,
        "ACTOR_ID": ACTOR_ID,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    db_init()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        actor_input = json.load(f)

    last_run = get_state("last_run_utc")
    print(f"[i] Last run (UTC): {last_run}")
    set_state("last_run_utc", now_utc_iso())

    items = run_apify(actor_input)
    reviews = extract_apify_reviews(items)

    print(f"[i] Apify returned items: {len(items)}")
    print(f"[i] Extracted reviews: {len(reviews)}")

    if not reviews:
        print("[i] No reviews, exit.")
        return

    new_reviews = []
    skipped_no_id = 0
    for r in reviews:
        rid = r.get("reviewId")
        if not rid:
            skipped_no_id += 1
            continue
        if not db_has_review(rid):
            new_reviews.append(r)

    for r in new_reviews:
        db_save_review(r)

    print(f"[i] New reviews found: {len(new_reviews)} (skipped_no_id={skipped_no_id})")
    print_db_snapshot(limit=50)

    if not new_reviews:
        print("[i] No new reviews (already processed).")
        return

    alerts_sent = 0
    analyzed_count = 0
    max_published = None

    for it in new_reviews:
        rid = it.get("reviewId")
        city = it.get("branch_city", "")
        published = it.get("publishedAtDate") or ""

        if published and ((max_published is None) or (published > max_published)):
            max_published = published

        analysis = {
            "is_issue": False,
            "issue_types": [],
            "severity": "low",
            "affected_dimensions": [],
            "key_signals": ["not_analyzed"],
            "summary": "",
            "recommended_actions": [],
            "suggested_owner_reply": ""
        }

        if should_send_to_llm(it) and not db_has_analysis(rid):
            bundle = build_signal_bundle(it)
            analysis = analyze_review_full(bundle)

            # ✅ IMPORTANT: adjust this line based on your db.py signature
            db_save_analysis(rid, city, analysis)

            analyzed_count += 1

        if should_alert_full(it, analysis):
            title, body = build_alert_message(it, analysis)
            ok = send_telegram_message(title, body)
            if ok:
                alerts_sent += 1

    print(f"[i] LLM analyzed: {analyzed_count}")
    print(f"[i] Alerts sent: {alerts_sent}")

    if max_published:
        set_state("last_publishedAtDate", max_published)
        print(f"[i] Updated last_publishedAtDate: {max_published}")


if __name__ == "__main__":
    main()
