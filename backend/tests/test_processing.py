from app.models import (
    Branch,
    BusinessType,
    CollectionRun,
    DeliveryState,
    Issue,
    Organization,
    Review,
    ReviewSource,
    ReviewState,
    RunState,
    TelegramReport,
)
from app.schemas import AIAnalysisResult
from app.services.processing import deliver_report, process_run


class TelegramSpy:
    def __init__(self, should_fail=False):
        self.calls = 0
        self.should_fail = should_fail

    def send_report(self, text):
        self.calls += 1
        if self.should_fail:
            raise TimeoutError("telegram timeout")
        return [{"result": {"message_id": 42}}]


class ApifyStub:
    def run(self, actor_input):
        assert actor_input["scrapeReviewsPersonalData"] is False
        return [{"reviewId": "google-review-1", "name": "عميل", "stars": 2, "text": "الخدمة بطيئة"}]


class AnalyzerStub:
    def analyze(self, payload):
        assert payload["review"]["text"] == "الخدمة بطيئة"
        return AIAnalysisResult(
            sentiment="negative",
            is_issue=True,
            issue_category="service",
            issue_subcategory="slow_service",
            severity="high",
            urgency="soon",
            summary="بطء في الخدمة",
            problem_description="أبلغ العميل عن بطء الخدمة.",
            affected_dimensions=["speed"],
            key_signals=["الخدمة بطيئة"],
            employee_match={"status": "not_applicable", "confidence": 0, "reason": "no employee mentioned"},
            mentioned_menu_items=[],
            root_cause={"description": "سبب غير مؤكد", "confidence": 0.2, "is_confirmed": False},
            immediate_actions=["متابعة زمن الخدمة"],
            preventive_actions=["مراجعة توزيع المهام"],
            suggested_owner_reply="نعتذر لك، ونعمل على تحسين سرعة الخدمة.",
            requires_manager_attention=True,
        )


def seed_run(db):
    organization = Organization(name="مؤسسة", business_type=BusinessType.COMPANY, city="الرياض")
    db.add(organization); db.flush()
    run = CollectionRun(organization_id=organization.id, branches_processed=1, reviews_collected=2, new_reviews=2)
    db.add(run); db.commit()
    return run


def test_duplicate_telegram_delivery_is_prevented(db):
    run = seed_run(db)
    telegram = TelegramSpy()
    deliver_report(db, run, telegram)
    deliver_report(db, run, telegram)
    assert telegram.calls == 1
    report = db.query(TelegramReport).filter_by(run_id=run.id).one()
    assert report.delivery_status == DeliveryState.SENT


def test_failed_notification_can_be_retried(db):
    run = seed_run(db)
    failing = TelegramSpy(should_fail=True)
    try:
        deliver_report(db, run, failing)
    except TimeoutError:
        pass
    report = db.query(TelegramReport).filter_by(run_id=run.id).one()
    assert report.delivery_status == DeliveryState.FAILED
    succeeding = TelegramSpy()
    deliver_report(db, run, succeeding)
    db.refresh(report)
    assert report.delivery_status == DeliveryState.SENT
    assert report.attempts == 2


def test_full_run_persists_review_issue_and_single_report(db):
    organization = Organization(name="مؤسسة", business_type=BusinessType.COMPANY, city="الرياض")
    db.add(organization); db.flush()
    branch = Branch(
        organization_id=organization.id,
        name="فرع الرياض",
        city="الرياض",
        google_maps_url="https://maps.example/reviews",
    )
    db.add(branch); db.flush()
    db.add(ReviewSource(branch_id=branch.id, provider="google_maps", source_url="https://maps.example/reviews"))
    run = CollectionRun(organization_id=organization.id)
    db.add(run); db.commit()

    telegram = TelegramSpy()
    process_run(db, run.id, apify=ApifyStub(), analyzer=AnalyzerStub(), telegram=telegram)

    db.refresh(run)
    review = db.query(Review).one()
    assert run.status == RunState.COMPLETED
    assert run.reviews_collected == 1
    assert run.new_reviews == 1
    assert run.analyzed_reviews == 1
    assert run.issues_generated == 1
    assert review.processing_state == ReviewState.COMPLETED
    assert db.query(Issue).count() == 1
    assert db.query(TelegramReport).count() == 1
    assert telegram.calls == 1
