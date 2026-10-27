from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.integrations.apify.client import normalize_reviews
from app.models import Branch, BusinessType, Employee, Gender, MenuCategory, MenuItem, Organization, Review, ReviewAnalysis, ReviewSource, Sentiment, Severity
from app.schemas import AIAnalysisResult, EmployeeCreate, MentionedEmployee, MentionedMenuItem
from app.services.matching import match_employee, match_menu_items
from app.services.metrics import dashboard_summary


def seed_branch(db):
    organization = Organization(name="مقهى الاختبار", business_type=BusinessType.CAFE, city="الرياض")
    db.add(organization)
    db.flush()
    branch = Branch(organization_id=organization.id, name="العليا", city="الرياض", google_maps_url="https://maps.google.com/example")
    db.add(branch)
    db.flush()
    source = ReviewSource(branch_id=branch.id, source_url=branch.google_maps_url)
    db.add(source)
    db.commit()
    return organization, branch, source


def test_review_normalization_deduplicates_and_flattens_places():
    raw = [{"title": "الفرع", "reviews": [{"reviewId": "a", "stars": 2, "text": "سيئ"}, {"reviewId": "a", "stars": 2, "text": "سيئ"}]}]
    normalized = normalize_reviews(raw)
    assert len(normalized) == 1
    assert normalized[0]["external_review_id"] == "a"
    assert normalized[0]["rating"] == 2


def test_database_prevents_duplicate_review_per_source(db):
    organization, branch, source = seed_branch(db)
    kwargs = dict(organization_id=organization.id, branch_id=branch.id, source_id=source.id, external_review_id="same")
    db.add(Review(**kwargs))
    db.commit()
    db.add(Review(**kwargs))
    with pytest.raises(IntegrityError):
        db.commit()


def test_employee_gender_accepts_only_f_or_m():
    common = dict(organization_id="o", branch_id="b", first_name="سارة", last_name="أحمد", nationality="SA", job_title="Barista")
    assert EmployeeCreate(**common, gender="F").gender == Gender.F
    assert EmployeeCreate(**common, gender="M").gender == Gender.M
    with pytest.raises(ValidationError):
        EmployeeCreate(**common, gender="X")


def test_production_rejects_weak_api_key():
    with pytest.raises(ValidationError):
        Settings(environment="production", APP_API_KEY="short", _env_file=None)


def test_ambiguous_employee_matching_never_selects_random_candidate(db):
    organization, branch, _ = seed_branch(db)
    employees = [
        Employee(organization_id=organization.id, branch_id=branch.id, first_name="أحمد", last_name="علي", gender=Gender.M, nationality="مصري", job_title="كاشير"),
        Employee(organization_id=organization.id, branch_id=branch.id, first_name="محمد", last_name="حسن", gender=Gender.M, nationality="مصري", job_title="كاشير"),
    ]
    db.add_all(employees)
    db.commit()
    result = match_employee(MentionedEmployee(nationality="مصري", role="كاشير", evidence="الموظف المصري عند الكاشير"), employees)
    assert result.status == "ambiguous"
    assert result.employee_id is None
    assert result.candidate_count == 2


def test_nationality_alone_never_matches_employee(db):
    organization, branch, _ = seed_branch(db)
    employee = Employee(organization_id=organization.id, branch_id=branch.id, first_name="أحمد", last_name="علي", gender=Gender.M, nationality="مصري", job_title="كاشير")
    result = match_employee(MentionedEmployee(nationality="مصري"), [employee])
    assert result.status == "unidentified"
    assert result.employee_id is None


def test_menu_matching_uses_real_catalog_entities(db):
    organization, _, _ = seed_branch(db)
    category = MenuCategory(organization_id=organization.id, name="مشروبات")
    db.add(category)
    db.flush()
    item = MenuItem(category_id=category.id, name="سبانش لاتيه")
    matches = match_menu_items([MentionedMenuItem(name="سبانش لاتيه", evidence="كان باردًا")], [item])
    assert matches[0][1] is item
    assert matches[0][2] >= 0.9


def test_analysis_schema_rejects_invalid_severity():
    payload = dict(
        sentiment="negative", is_issue=True, issue_category="service", severity="extreme", urgency="soon",
        summary="", problem_description="", affected_dimensions=[], key_signals=[], employee_match={"status": "not_applicable", "confidence": 0},
        mentioned_menu_items=[], root_cause={"description": "غير مؤكد", "confidence": 0.1}, immediate_actions=[], preventive_actions=[],
        suggested_owner_reply="", requires_manager_attention=False,
    )
    with pytest.raises(ValidationError):
        AIAnalysisResult.model_validate(payload)


def test_metrics_reconcile_sentiment_totals(db):
    organization, branch, source = seed_branch(db)
    reviews = []
    for index, (rating, sentiment) in enumerate([(5, Sentiment.POSITIVE), (2, Sentiment.NEGATIVE), (3, Sentiment.NEUTRAL)]):
        review = Review(organization_id=organization.id, branch_id=branch.id, source_id=source.id, external_review_id=str(index), reviewer_name=f"r{index}", rating=rating, published_at=datetime.now(timezone.utc))
        db.add(review); db.flush()
        db.add(ReviewAnalysis(review_id=review.id, sentiment=sentiment, severity=Severity.LOW))
        reviews.append(review)
    db.commit()
    summary = dashboard_summary(db, organization.id, start_date=date.today(), end_date=date.today())
    assert summary["total_reviews"] == 3
    assert summary["positive_reviews"] + summary["negative_reviews"] + summary["neutral_reviews"] == 3
    assert summary["average_rating"] == pytest.approx(3.33, abs=0.01)
