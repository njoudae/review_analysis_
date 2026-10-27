from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.models import Branch, Issue, IssueState, Review, ReviewAnalysis, Sentiment


def _bounds(start_date: date | None, end_date: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
    end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc) if end_date else None
    return start, end


def _review_filters(organization_id: str, branch_id: str | None, start: datetime | None, end: datetime | None):
    conditions = [Review.organization_id == organization_id]
    if branch_id:
        conditions.append(Review.branch_id == branch_id)
    if start:
        conditions.append(Review.published_at >= start)
    if end:
        conditions.append(Review.published_at < end)
    return conditions


def _period_metrics(db: Session, organization_id: str, branch_id: str | None, start: datetime | None, end: datetime | None) -> dict[str, Any]:
    conditions = _review_filters(organization_id, branch_id, start, end)
    row = db.execute(
        select(
            func.count(distinct(Review.id)),
            func.count(distinct(Review.reviewer_name)),
            func.avg(Review.rating),
            func.sum(case((ReviewAnalysis.sentiment == Sentiment.POSITIVE, 1), else_=0)),
            func.sum(case((ReviewAnalysis.sentiment == Sentiment.NEGATIVE, 1), else_=0)),
            func.sum(case((ReviewAnalysis.sentiment == Sentiment.NEUTRAL, 1), else_=0)),
        )
        .select_from(Review)
        .outerjoin(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        .where(*conditions)
    ).one()
    return {
        "total_reviews": int(row[0] or 0),
        "total_reviewers": int(row[1] or 0),
        "average_rating": round(float(row[2]), 2) if row[2] is not None else None,
        "positive_reviews": int(row[3] or 0),
        "negative_reviews": int(row[4] or 0),
        "neutral_reviews": int(row[5] or 0),
    }


def _comparison(current: int | float | None, previous: int | float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round(((current - previous) / previous) * 100, 1)


def dashboard_summary(
    db: Session,
    organization_id: str,
    branch_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    start, end = _bounds(start_date, end_date)
    current = _period_metrics(db, organization_id, branch_id, start, end)
    branch_conditions = [Branch.organization_id == organization_id]
    if branch_id:
        branch_conditions.append(Branch.id == branch_id)
    current["total_branches"] = db.scalar(select(func.count(Branch.id)).where(*branch_conditions)) or 0

    previous = None
    if start and end:
        duration = end - start
        previous = _period_metrics(db, organization_id, branch_id, start - duration, start)
    current["comparisons"] = {
        key: _comparison(current.get(key), previous.get(key) if previous else None)
        for key in ("total_reviews", "total_reviewers", "average_rating", "positive_reviews", "negative_reviews", "neutral_reviews")
    }

    trend_rows = db.execute(
        select(
            func.date(Review.published_at).label("day"),
            ReviewAnalysis.sentiment,
            func.count(Review.id),
        )
        .join(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        .where(*_review_filters(organization_id, branch_id, start, end))
        .group_by(func.date(Review.published_at), ReviewAnalysis.sentiment)
        .order_by(func.date(Review.published_at))
    ).all()
    days: dict[str, dict[str, Any]] = {}
    for day, sentiment, count in trend_rows:
        key = str(day)
        days.setdefault(key, {"date": key, "positive": 0, "negative": 0, "neutral": 0, "mixed": 0})
        days[key][sentiment.value if hasattr(sentiment, "value") else str(sentiment)] = count
    current["sentiment_trend"] = list(days.values())

    complaint_rows = db.execute(
        select(ReviewAnalysis.issue_category, func.count(ReviewAnalysis.id))
        .join(Review, Review.id == ReviewAnalysis.review_id)
        .where(*_review_filters(organization_id, branch_id, start, end), ReviewAnalysis.is_issue.is_(True))
        .group_by(ReviewAnalysis.issue_category)
        .order_by(func.count(ReviewAnalysis.id).desc())
        .limit(8)
    ).all()
    current["top_complaints"] = [{"category": category or "other", "count": count} for category, count in complaint_rows]

    unresolved = db.scalar(
        select(func.count(Issue.id)).where(
            Issue.organization_id == organization_id,
            Issue.status.notin_([IssueState.RESOLVED, IssueState.DISMISSED]),
            *(([Issue.branch_id == branch_id]) if branch_id else []),
        )
    )
    current["unresolved_issues"] = int(unresolved or 0)
    return current


def branch_performance(db: Session, organization_id: str, start_date: date | None = None, end_date: date | None = None) -> list[dict[str, Any]]:
    start, end = _bounds(start_date, end_date)
    branches = db.scalars(select(Branch).where(Branch.organization_id == organization_id).order_by(Branch.name)).all()
    output = []
    for branch in branches:
        metrics = _period_metrics(db, organization_id, branch.id, start, end)
        open_issues = db.scalar(
            select(func.count(Issue.id)).where(
                Issue.branch_id == branch.id,
                Issue.status.notin_([IssueState.RESOLVED, IssueState.DISMISSED]),
            )
        ) or 0
        output.append(
            {
                "id": branch.id,
                "branch": branch.name,
                "city": branch.city,
                "employee_count": branch.employee_count,
                **metrics,
                "open_issues": int(open_issues),
                "status": branch.status.value,
            }
        )
    return output

