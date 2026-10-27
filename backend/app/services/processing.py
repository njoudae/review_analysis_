import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.apify.client import ApifyClient, build_actor_input, normalize_reviews
from app.integrations.openai.client import OpenAIAnalyzer
from app.integrations.telegram.client import TelegramClient
from app.models import (
    Branch,
    CollectionRun,
    DeliveryState,
    Employee,
    Issue,
    MenuCategory,
    MenuItem,
    NotificationAttempt,
    RecordStatus,
    Review,
    ReviewAnalysis,
    ReviewEmployeeMention,
    ReviewMenuMention,
    ReviewSource,
    ReviewState,
    RunState,
    TelegramReport,
    utcnow,
)
from app.services.matching import match_employee, match_menu_items
from app.services.reporting import build_run_report


logger = logging.getLogger(__name__)


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def collect_reviews(db: Session, run: CollectionRun, apify: ApifyClient) -> None:
    branches = db.scalars(
        select(Branch).where(Branch.organization_id == run.organization_id, Branch.status == RecordStatus.ACTIVE)
    ).all()
    run.branches_processed = 0
    for branch in branches:
        source = db.scalar(
            select(ReviewSource).where(
                ReviewSource.branch_id == branch.id,
                ReviewSource.provider == "google_maps",
                ReviewSource.status == RecordStatus.ACTIVE,
            )
        )
        if source is None:
            logger.warning("branch_without_source", extra={"branch_id": branch.id})
            continue
        try:
            raw_items = apify.run(build_actor_input(source.source_url))
            normalized = normalize_reviews(raw_items)
            run.reviews_collected += len(normalized)
            for item in normalized:
                existing = db.scalar(
                    select(Review).where(
                        Review.source_id == source.id,
                        Review.external_review_id == item["external_review_id"],
                    )
                )
                if existing:
                    continue
                review = Review(
                    organization_id=run.organization_id,
                    branch_id=branch.id,
                    source_id=source.id,
                    collection_run_id=run.id,
                    external_review_id=item["external_review_id"],
                    reviewer_name=item["reviewer_name"],
                    rating=item["rating"],
                    review_text=item["review_text"],
                    published_at=parse_datetime(item["published_at"]),
                    review_url=item["review_url"],
                    likes=item["likes"],
                    local_guide=item["local_guide"],
                    detailed_ratings=item["detailed_ratings"],
                    context=item["context"],
                    images=item["images"],
                    owner_reply=item["owner_reply"],
                    raw_json=item["raw_json"],
                    processing_state=ReviewState.PENDING_ANALYSIS,
                )
                try:
                    with db.begin_nested():
                        db.add(review)
                        db.flush()
                    run.new_reviews += 1
                except IntegrityError:
                    logger.info(
                        "duplicate_review_skipped",
                        extra={"source_id": source.id, "external_review_id": item["external_review_id"]},
                    )
            run.branches_processed += 1
            db.commit()
        except Exception as exc:
            logger.exception("branch_collection_failed", extra={"branch_id": branch.id})
            run.last_error = f"Branch {branch.name}: {exc}"
            db.commit()


def _analysis_payload(db: Session, review: Review) -> dict[str, Any]:
    branch = db.get(Branch, review.branch_id)
    employees = db.scalars(
        select(Employee).where(Employee.branch_id == review.branch_id, Employee.status == RecordStatus.ACTIVE)
    ).all()
    menu_items = db.scalars(
        select(MenuItem)
        .join(MenuCategory, MenuCategory.id == MenuItem.category_id)
        .where(MenuCategory.organization_id == review.organization_id, MenuItem.status == RecordStatus.ACTIVE)
    ).all()
    return {
        "review": {
            "rating": review.rating,
            "text": review.review_text,
            "detailed_ratings": review.detailed_ratings,
            "context": review.context,
            "owner_reply": review.owner_reply,
        },
        "branch": {"name": branch.name if branch else None, "city": branch.city if branch else None},
        "eligible_employee_directory": [
            {"first_name": e.first_name, "last_name": e.last_name, "role": e.job_title, "nationality": e.nationality}
            for e in employees
        ],
        "menu_items": [item.name for item in menu_items],
        "matching_rules": "Employee IDs are resolved deterministically after analysis. Nationality alone is never sufficient.",
    }


def analyze_pending_reviews(db: Session, run: CollectionRun, analyzer: OpenAIAnalyzer) -> int:
    reviews = db.scalars(
        select(Review).where(
            Review.collection_run_id == run.id,
            Review.processing_state.in_([ReviewState.PENDING_ANALYSIS, ReviewState.FAILED_ANALYSIS]),
            Review.attempts < settings.external_max_attempts,
        )
    ).all()
    failures = 0
    for review in reviews:
        try:
            review.processing_state = ReviewState.ANALYZING
            review.attempts += 1
            review.last_attempt_at = utcnow()
            db.commit()

            result = analyzer.analyze(_analysis_payload(db, review))
            analysis = ReviewAnalysis(
                review_id=review.id,
                sentiment=result.sentiment,
                is_issue=result.is_issue,
                issue_category=result.issue_category,
                issue_subcategory=result.issue_subcategory,
                severity=result.severity,
                urgency=result.urgency,
                summary=result.summary,
                problem_description=result.problem_description,
                affected_dimensions=result.affected_dimensions,
                key_signals=result.key_signals,
                root_cause=result.root_cause.model_dump(),
                immediate_actions=result.immediate_actions,
                preventive_actions=result.preventive_actions,
                suggested_owner_reply=result.suggested_owner_reply,
                requires_manager_attention=result.requires_manager_attention,
                raw_analysis=result.model_dump(),
            )
            db.add(analysis)

            employees = db.scalars(select(Employee).where(Employee.branch_id == review.branch_id, Employee.status == RecordStatus.ACTIVE)).all()
            employee_match = match_employee(result.mentioned_employee, list(employees))
            mention = result.mentioned_employee
            if mention:
                db.add(
                    ReviewEmployeeMention(
                        review_id=review.id,
                        employee_id=employee_match.employee_id,
                        match_status=employee_match.status,
                        confidence=employee_match.confidence,
                        evidence=mention.evidence,
                        mentioned_name=mention.name,
                        mentioned_role=mention.role,
                        mentioned_nationality=mention.nationality,
                        candidate_count=employee_match.candidate_count,
                        confirmed_responsibility=False,
                    )
                )

            menu_items = db.scalars(
                select(MenuItem).join(MenuCategory).where(MenuCategory.organization_id == review.organization_id, MenuItem.status == RecordStatus.ACTIVE)
            ).all()
            for mentioned, item, confidence in match_menu_items(result.mentioned_menu_items, list(menu_items)):
                db.add(
                    ReviewMenuMention(
                        review_id=review.id,
                        menu_item_id=item.id if item else None,
                        mentioned_text=mentioned.name,
                        confidence=confidence,
                        evidence=mentioned.evidence,
                    )
                )

            review.processing_state = ReviewState.ANALYZED
            review.last_error = None
            run.analyzed_reviews += 1
            if result.sentiment == "positive":
                run.positive_reviews += 1
            elif result.sentiment == "negative":
                run.negative_reviews += 1
            else:
                run.neutral_reviews += 1

            if result.is_issue:
                db.add(
                    Issue(
                        organization_id=review.organization_id,
                        branch_id=review.branch_id,
                        review_id=review.id,
                        category=result.issue_category or "other",
                        subcategory=result.issue_subcategory,
                        severity=result.severity,
                        summary=result.summary or result.problem_description,
                    )
                )
                review.processing_state = ReviewState.ISSUE_CREATED
                run.issues_generated += 1
            review.processing_state = ReviewState.COMPLETED
            db.commit()
        except Exception as exc:
            db.rollback()
            failed_review = db.get(Review, review.id)
            failed_review.processing_state = ReviewState.FAILED_ANALYSIS
            failed_review.last_error = str(exc)[:2000]
            failed_review.last_attempt_at = utcnow()
            failures += 1
            db.commit()
            logger.exception("review_analysis_failed", extra={"review_id": review.id})
    return failures


def deliver_report(db: Session, run: CollectionRun, telegram: TelegramClient) -> None:
    report = db.scalar(select(TelegramReport).where(TelegramReport.run_id == run.id))
    if report and report.delivery_status == DeliveryState.SENT:
        return
    if report is None:
        report = TelegramReport(run_id=run.id, content=build_run_report(db, run))
        db.add(report)
        db.commit()
        db.refresh(report)

    report.delivery_status = DeliveryState.SENDING
    report.attempts += 1
    db.commit()
    try:
        responses = telegram.send_report(report.content)
        report.delivery_status = DeliveryState.SENT
        report.sent_at = utcnow()
        report.last_error = None
        db.add(
            NotificationAttempt(
                report_id=report.id,
                attempt_number=report.attempts,
                status=DeliveryState.SENT,
                response_metadata={"message_ids": [r.get("result", {}).get("message_id") for r in responses]},
            )
        )
        db.commit()
    except Exception as exc:
        report.delivery_status = DeliveryState.FAILED
        report.last_error = str(exc)[:2000]
        db.add(
            NotificationAttempt(
                report_id=report.id,
                attempt_number=report.attempts,
                status=DeliveryState.FAILED,
                error=report.last_error,
            )
        )
        db.commit()
        raise


def process_run(db: Session, run_id: str, apify: ApifyClient | None = None, analyzer: OpenAIAnalyzer | None = None, telegram: TelegramClient | None = None) -> None:
    run = db.get(CollectionRun, run_id)
    if not run or run.status == RunState.COMPLETED:
        return
    run.attempts += 1
    run.last_attempt_at = utcnow()
    run.started_at = run.started_at or utcnow()
    run.last_error = None
    db.commit()
    try:
        if run.reviews_collected == 0:
            run.status = RunState.COLLECTING
            db.commit()
            collect_reviews(db, run, apify or ApifyClient())

        run.status = RunState.ANALYZING
        db.commit()
        failures = analyze_pending_reviews(db, run, analyzer or OpenAIAnalyzer())
        if failures:
            raise RuntimeError(f"{failures} review(s) remain retryable after analysis failure")

        run.status = RunState.GENERATING_REPORT
        db.commit()
        run.status = RunState.SENDING_REPORT
        db.commit()
        deliver_report(db, run, telegram or TelegramClient())

        run.status = RunState.COMPLETED
        run.completed_at = utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        failed = db.get(CollectionRun, run_id)
        failed.status = RunState.FAILED
        failed.last_error = str(exc)[:2000]
        db.commit()
        logger.exception("collection_run_failed", extra={"run_id": run_id})
        raise
