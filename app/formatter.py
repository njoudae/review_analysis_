import json

def build_alert_title(place: str, city: str, stars_label: str) -> str:
    place = (place or "غير معروف").strip()
    city = (city or "غير معروف").strip()
    return f"⭐ تنبيه مراجعة — {place} — {city} — {stars_label}⭐"


def build_alert_message(it: dict, analysis: dict) -> tuple[str, str]:

    place = (it.get("title") or it.get("placeTitle") or "غير معروف").strip()
    city = (it.get("branch_city") or it.get("city") or "غير معروف").strip()

    stars = it.get("stars")
    stars_label = str(stars) if stars is not None else "N/A"

    detailed = it.get("reviewDetailedRating") or {}
    ctx = it.get("reviewContext") or {}

    published = it.get("publishedAtDate") or ""
    review_url = it.get("reviewUrl") or ""

    title = build_alert_title(place, city, stars_label)


    is_issue = analysis.get("is_issue")
    issue_types = analysis.get("issue_types", [])
    severity = analysis.get("severity")
    summary = analysis.get("summary")
    key_signals = analysis.get("key_signals", [])
    rec_actions = analysis.get("recommended_actions", [])
    owner_reply = analysis.get("suggested_owner_reply", "")

    text = (it.get("text") or "").strip()

    body = (
        f"المكان: {place}\n"
        f"المدينة: {city}\n"
        f"التقييم العام: {stars_label}\n"
        f"تفاصيل التقييم: {json.dumps(detailed, ensure_ascii=False)}\n"
        f"السياق: {json.dumps(ctx, ensure_ascii=False)}\n"
        f"وقت التعليق: {published}\n"
        f"رابط التعليق:\n{review_url}\n\n"
        f"LLM is_issue: {is_issue}\n"
        f"تصنيف المشكلة: {json.dumps(issue_types, ensure_ascii=False)}\n"
        f"الشدة: {severity}\n"
        f"ملخص: {summary}\n"
        f"إشارات: {json.dumps(key_signals, ensure_ascii=False)}\n"
        f"إجراءات مقترحة: {json.dumps(rec_actions, ensure_ascii=False)}\n\n"
        f"رد مقترح للنشر:\n{owner_reply}\n\n"
        f"نص التعليق:\n{text}\n"
    )

    return title, body
