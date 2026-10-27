import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class BusinessType(str, enum.Enum):
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    COMPANY = "company"
    SCHOOL = "school"
    RETAIL = "retail"
    OTHER = "other"


class RecordStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Gender(str, enum.Enum):
    F = "F"
    M = "M"


class ReviewState(str, enum.Enum):
    COLLECTED = "COLLECTED"
    PENDING_ANALYSIS = "PENDING_ANALYSIS"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    FAILED_ANALYSIS = "FAILED_ANALYSIS"
    ISSUE_CREATED = "ISSUE_CREATED"
    COMPLETED = "COMPLETED"


class RunState(str, enum.Enum):
    STARTED = "STARTED"
    COLLECTING = "COLLECTING"
    ANALYZING = "ANALYZING"
    GENERATING_REPORT = "GENERATING_REPORT"
    SENDING_REPORT = "SENDING_REPORT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Sentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueState(str, enum.Enum):
    NEW = "NEW"
    REVIEWING = "REVIEWING"
    INVESTIGATING = "INVESTIGATING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class DeliveryState(str, enum.Enum):
    PENDING = "PENDING"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_type: Mapped[BusinessType] = mapped_column(Enum(BusinessType, native_enum=False), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    default_language: Mapped[str] = mapped_column(String(10), default="ar", nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="Asia/Riyadh", nullable=False)
    branches: Mapped[list["Branch"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrganizationSetting(TimestampMixin, Base):
    __tablename__ = "organization_settings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), unique=True)
    issue_taxonomy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    analysis_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"
    __table_args__ = (Index("ix_branches_org_status", "organization_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(Text)
    google_maps_url: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    google_place_id: Mapped[str | None] = mapped_column(String(200))
    manager_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    employee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)
    organization: Mapped[Organization] = relationship(back_populates="branches")
    sources: Mapped[list["ReviewSource"]] = relationship(back_populates="branch", cascade="all, delete-orphan")


class ReviewSource(TimestampMixin, Base):
    __tablename__ = "review_sources"
    __table_args__ = (UniqueConstraint("branch_id", "provider", name="uq_source_branch_provider"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="google_maps", nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)
    branch: Mapped[Branch] = relationship(back_populates="sources")


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_employee_org_code"),
        Index("ix_employees_branch_status", "branch_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    employee_code: Mapped[str | None] = mapped_column(String(80))
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, native_enum=False), nullable=False)
    nationality: Mapped[str] = mapped_column(String(120), nullable=False)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    joined_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)


class MenuCategory(TimestampMixin, Base):
    __tablename__ = "menu_categories"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_menu_category_org_name"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)


class MenuItem(TimestampMixin, Base):
    __tablename__ = "menu_items"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_menu_item_category_name"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category_id: Mapped[str] = mapped_column(ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[RunState] = mapped_column(Enum(RunState, native_enum=False), default=RunState.STARTED, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    branches_processed: Mapped[int] = mapped_column(Integer, default=0)
    reviews_collected: Mapped[int] = mapped_column(Integer, default=0)
    new_reviews: Mapped[int] = mapped_column(Integer, default=0)
    analyzed_reviews: Mapped[int] = mapped_column(Integer, default=0)
    positive_reviews: Mapped[int] = mapped_column(Integer, default=0)
    negative_reviews: Mapped[int] = mapped_column(Integer, default=0)
    neutral_reviews: Mapped[int] = mapped_column(Integer, default=0)
    issues_generated: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("source_id", "external_review_id", name="uq_review_source_external"),
        Index("ix_reviews_org_branch_published", "organization_id", "branch_id", "published_at"),
        Index("ix_reviews_state_attempt", "processing_state", "last_attempt_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("review_sources.id", ondelete="CASCADE"), nullable=False)
    collection_run_id: Mapped[str | None] = mapped_column(ForeignKey("collection_runs.id", ondelete="SET NULL"))
    external_review_id: Mapped[str] = mapped_column(String(300), nullable=False)
    reviewer_name: Mapped[str | None] = mapped_column(String(200))
    rating: Mapped[float | None] = mapped_column(Float)
    review_text: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_url: Mapped[str | None] = mapped_column(Text)
    likes: Mapped[int | None] = mapped_column(Integer)
    local_guide: Mapped[bool] = mapped_column(Boolean, default=False)
    detailed_ratings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    images: Mapped[list[Any]] = mapped_column(JSON, default=list)
    owner_reply: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processing_state: Mapped[ReviewState] = mapped_column(Enum(ReviewState, native_enum=False), default=ReviewState.PENDING_ANALYSIS)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReviewAnalysis(Base):
    __tablename__ = "review_analysis"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    sentiment: Mapped[Sentiment] = mapped_column(Enum(Sentiment, native_enum=False), index=True)
    is_issue: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_category: Mapped[str | None] = mapped_column(String(120), index=True)
    issue_subcategory: Mapped[str | None] = mapped_column(String(120))
    severity: Mapped[Severity] = mapped_column(Enum(Severity, native_enum=False), default=Severity.LOW, index=True)
    urgency: Mapped[str] = mapped_column(String(30), default="normal")
    summary: Mapped[str] = mapped_column(Text, default="")
    problem_description: Mapped[str] = mapped_column(Text, default="")
    affected_dimensions: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_signals: Mapped[list[str]] = mapped_column(JSON, default=list)
    root_cause: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    immediate_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    preventive_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    suggested_owner_reply: Mapped[str] = mapped_column(Text, default="")
    requires_manager_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewEntity(Base):
    __tablename__ = "review_entities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0)


class ReviewEmployeeMention(Base):
    __tablename__ = "review_employee_mentions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    match_status: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    evidence: Mapped[str | None] = mapped_column(Text)
    mentioned_name: Mapped[str | None] = mapped_column(String(200))
    mentioned_role: Mapped[str | None] = mapped_column(String(120))
    mentioned_nationality: Mapped[str | None] = mapped_column(String(120))
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    confirmed_responsibility: Mapped[bool] = mapped_column(Boolean, default=False)


class ReviewMenuMention(Base):
    __tablename__ = "review_menu_mentions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    menu_item_id: Mapped[str | None] = mapped_column(ForeignKey("menu_items.id", ondelete="SET NULL"))
    mentioned_text: Mapped[str] = mapped_column(String(300), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    evidence: Mapped[str | None] = mapped_column(Text)


class Issue(TimestampMixin, Base):
    __tablename__ = "issues"
    __table_args__ = (Index("ix_issues_org_branch_status", "organization_id", "branch_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(120))
    severity: Mapped[Severity] = mapped_column(Enum(Severity, native_enum=False), nullable=False)
    status: Mapped[IssueState] = mapped_column(Enum(IssueState, native_enum=False), default=IssueState.NEW)
    assigned_to: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IssueNote(Base):
    __tablename__ = "issue_notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IssueAction(Base):
    __tablename__ = "issue_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(200))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IssueStatusHistory(Base):
    __tablename__ = "issue_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(200))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TelegramReport(Base):
    __tablename__ = "telegram_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("collection_runs.id", ondelete="CASCADE"), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_status: Mapped[DeliveryState] = mapped_column(Enum(DeliveryState, native_enum=False), default=DeliveryState.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NotificationAttempt(Base):
    __tablename__ = "notification_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("telegram_reports.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DeliveryState] = mapped_column(Enum(DeliveryState, native_enum=False), nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    response_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"))
    actor: Mapped[str | None] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

