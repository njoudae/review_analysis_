from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Branch, CollectionRun, Organization, Review, ReviewAnalysis, ReviewEmployeeMention, ReviewMenuMention


def build_run_report(db: Session, run: CollectionRun) -> str:
    organization = db.get(Organization, run.organization_id)
    analyses = db.execute(
        select(ReviewAnalysis, Review.branch_id)
        .join(Review, Review.id == ReviewAnalysis.review_id)
        .where(Review.collection_run_id == run.id)
    ).all()
    branch_names = {branch.id: branch.name for branch in db.scalars(select(Branch).where(Branch.organization_id == run.organization_id))}
    complaints = Counter(a.issue_category or "other" for a, _ in analyses if a.is_issue)
    affected = Counter(branch_names.get(branch_id, "فرع غير معروف") for a, branch_id in analyses if a.is_issue)
    high = sum(1 for a, _ in analyses if a.severity.value in {"high", "critical"})
    medium = sum(1 for a, _ in analyses if a.severity.value == "medium")
    ratings = db.scalars(select(Review.rating).where(Review.collection_run_id == run.id, Review.rating.is_not(None))).all()
    average = round(sum(ratings) / len(ratings), 2) if ratings else None
    mentions = db.execute(
        select(ReviewEmployeeMention.match_status).join(Review, Review.id == ReviewEmployeeMention.review_id).where(Review.collection_run_id == run.id)
    ).scalars().all()
    menu_mentions = db.execute(
        select(ReviewMenuMention.mentioned_text).join(Review, Review.id == ReviewMenuMention.review_id).where(Review.collection_run_id == run.id)
    ).scalars().all()

    top_complaints = "\n".join(f"{i}. {name} — {count}" for i, (name, count) in enumerate(complaints.most_common(5), 1)) or "لا توجد مشكلات مصنفة"
    top_branches = "\n".join(f"{name} — {count} شكاوى" for name, count in affected.most_common(5)) or "لا توجد فروع متأثرة"
    top_menu = "\n".join(f"{name} — {count}" for name, count in Counter(menu_mentions).most_common(5)) or "لا توجد إشارات"
    confirmed_mentions = sum(1 for value in mentions if value in {"matched", "possible_match"})
    uncertain_mentions = sum(1 for value in mentions if value in {"ambiguous", "unidentified"})
    date_label = datetime.now().strftime("%Y-%m-%d")
    dashboard_line = f"\n\nلوحة المتابعة: {settings.dashboard_url}" if settings.dashboard_url else ""

    return f"""📊 تقرير تجربة العملاء
{date_label}

🏢 {organization.name if organization else 'المؤسسة'}

عملية السحب والتحليل اكتملت بنجاح.

الفروع المعالجة: {run.branches_processed}
المراجعات المجموعة: {run.reviews_collected}
المراجعات الجديدة: {run.new_reviews}

😊 إيجابية: {run.positive_reviews}
😐 محايدة: {run.neutral_reviews}
☹️ سلبية: {run.negative_reviews}
⭐ متوسط التقييم: {average if average is not None else 'غير متاح'}

━━━━━━━━━━
🔴 تحتاج انتباه

مرتفعة/حرجة: {high}
متوسطة: {medium}

أكثر المشكلات:
{top_complaints}

━━━━━━━━━━
📍 الفروع الأكثر تأثرًا

{top_branches}

━━━━━━━━━━
👥 إشارات الموظفين

مطابقات محتملة أو مؤكدة: {confirmed_mentions}
غير مؤكدة: {uncertain_mentions}

━━━━━━━━━━
☕ المنتجات الأكثر ورودًا

{top_menu}

ملاحظة: الإشارات الآلية لا تثبت مسؤولية موظف أو سببًا جذريًا دون تحقيق داخلي.{dashboard_line}"""

