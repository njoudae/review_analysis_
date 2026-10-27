import json
import re

from .config import OPENAI_API_KEY, OPENAI_MODEL

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)


def to_number(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def should_send_to_llm(review: dict) -> bool:
    text = (review.get("text") or "").strip()
    has_text = bool(text)

    stars = to_number(review.get("stars"))
    detailed = review.get("reviewDetailedRating") or {}
    has_any_detailed = any(to_number(v) is not None for v in detailed.values())

    if stars is not None and stars <= 3:
        return True

    if has_any_detailed:
        for v in detailed.values():
            n = to_number(v)
            if n is not None and n <= 3:
                return True

    if stars is None and not has_any_detailed and has_text:
        return True

    if stars is not None and not has_any_detailed and has_text:
        return True

    return False


def build_signal_bundle(item: dict) -> dict:
    detailed = item.get("reviewDetailedRating") or {}
    ctx = item.get("reviewContext") or {}

    owner_text = item.get("responseFromOwnerText")
    owner_date = item.get("responseFromOwnerDate")

    return {
        "place": item.get("title"),
        "branch_city": item.get("branch_city"),
        "stars": item.get("stars"),
        "publishedAtDate": item.get("publishedAtDate"),
        "publishAt": item.get("publishAt"),
        "text": item.get("text"),
        "likesCount": item.get("likesCount"),
        "hasImages": bool(item.get("reviewImageUrls")),
        "reviewDetailedRating": detailed,
        "reviewContext": ctx,
        "ownerResponse": {
            "hasResponse": bool(owner_text and str(owner_text).strip()),
            "date": owner_date,
            "text": owner_text
        }
    }


def analyze_review_full(bundle: dict) -> dict:
    prompt = f"""
أنت محلل جودة وخدمة عملاء.

 مهم جداً:
- أرجع JSON فقط
- بدون أي شرح
- بدون Markdown
- بدون ```json

بيانات المراجعة:
{json.dumps(bundle, ensure_ascii=False)}

صيغة الإخراج (التزم بها حرفياً):
{{
  "is_issue": true_or_false,
  "issue_types": [],
  "severity": "low|medium|high",
  "affected_dimensions": [],
  "key_signals": [],
  "summary": "",
  "recommended_actions": [],
  "suggested_owner_reply": ""
}}
"""

    resp = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    raw = (resp.output_text or "").strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {
        "is_issue": False,
        "issue_types": ["other"],
        "severity": "low",
        "affected_dimensions": [],
        "key_signals": ["llm_parse_failed", raw[:300]],
        "summary": "تعذر تحليل المراجعة تلقائيًا.",
        "recommended_actions": ["مراجعة التعليق يدويًا."],
        "suggested_owner_reply": ""
    }


def should_alert_full(item: dict, analysis: dict) -> bool:
    stars = to_number(item.get("stars"))
    detailed = item.get("reviewDetailedRating") or {}
    text = (item.get("text") or "").strip()
    has_text = bool(text)

    if stars is not None and stars <= 3:
        return True

    for v in detailed.values():
        n = to_number(v)
        if n is not None and n <= 3:
            return True

    has_any_detailed = any(to_number(v) is not None for v in detailed.values())
    if stars is None and not has_any_detailed and has_text:
        return True

    if analysis.get("is_issue") is True:
        return True
    if analysis.get("severity") == "high":
        return True

    return False
