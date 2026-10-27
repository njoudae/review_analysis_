from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models import BusinessType, Gender, IssueState, RecordStatus, RunState, Severity


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    business_type: BusinessType
    industry: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    logo_url: HttpUrl | None = None
    default_language: str = Field(default="ar", max_length=10)
    timezone: str = Field(default="Asia/Riyadh", max_length=80)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    business_type: BusinessType | None = None
    industry: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    logo_url: HttpUrl | None = None
    default_language: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=80)


class OrganizationRead(ORMModel):
    id: str
    name: str
    business_type: BusinessType
    industry: str | None
    city: str
    logo_url: str | None
    default_language: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class BranchCreate(BaseModel):
    organization_id: str
    name: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    address: str | None = None
    google_maps_url: HttpUrl
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    google_place_id: str | None = Field(default=None, max_length=200)
    manager_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    employee_count: int = Field(default=0, ge=0)
    status: RecordStatus = RecordStatus.ACTIVE


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    address: str | None = None
    google_maps_url: HttpUrl | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    google_place_id: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    employee_count: int | None = Field(default=None, ge=0)
    status: RecordStatus | None = None


class BranchRead(ORMModel):
    id: str
    organization_id: str
    name: str
    city: str
    district: str | None
    address: str | None
    google_maps_url: str
    latitude: float | None
    longitude: float | None
    google_place_id: str | None
    manager_name: str | None
    phone: str | None
    employee_count: int
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class EmployeeCreate(BaseModel):
    organization_id: str
    branch_id: str
    employee_code: str | None = Field(default=None, max_length=80)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    gender: Gender
    nationality: str = Field(min_length=2, max_length=120)
    job_title: str = Field(min_length=2, max_length=120)
    joined_at: date | None = None
    status: RecordStatus = RecordStatus.ACTIVE


class EmployeeUpdate(BaseModel):
    branch_id: str | None = None
    employee_code: str | None = Field(default=None, max_length=80)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    gender: Gender | None = None
    nationality: str | None = Field(default=None, min_length=2, max_length=120)
    job_title: str | None = Field(default=None, min_length=2, max_length=120)
    joined_at: date | None = None
    status: RecordStatus | None = None


class EmployeeRead(ORMModel):
    id: str
    organization_id: str
    branch_id: str
    employee_code: str | None
    first_name: str
    last_name: str
    gender: Gender
    nationality: str
    job_title: str
    joined_at: date | None
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class MenuCategoryCreate(BaseModel):
    organization_id: str
    name: str = Field(min_length=2, max_length=160)


class MenuCategoryRead(ORMModel):
    id: str
    organization_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class MenuItemCreate(BaseModel):
    category_id: str
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    status: RecordStatus | None = None


class MenuItemRead(ORMModel):
    id: str
    category_id: str
    name: str
    description: str | None
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class MentionedEmployee(BaseModel):
    name: str | None = None
    nationality: str | None = None
    role: str | None = None
    evidence: str | None = None


class EmployeeMatchResult(BaseModel):
    status: Literal["matched", "possible_match", "ambiguous", "unidentified", "not_applicable"]
    employee_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    reason: str = ""
    candidate_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_match(self):
        if self.status in {"matched", "possible_match"} and not self.employee_id:
            raise ValueError("employee_id is required for a matched employee")
        if self.status in {"ambiguous", "unidentified", "not_applicable"} and self.employee_id:
            raise ValueError("employee_id must be empty when the employee is not uniquely matched")
        return self


class MentionedMenuItem(BaseModel):
    name: str
    evidence: str


class RootCause(BaseModel):
    description: str
    confidence: float = Field(ge=0, le=1)
    is_confirmed: bool = False


class AIAnalysisResult(BaseModel):
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    is_issue: bool
    issue_category: str | None = None
    issue_subcategory: str | None = None
    severity: Literal["low", "medium", "high", "critical"]
    urgency: Literal["normal", "soon", "immediate"]
    summary: str
    problem_description: str
    affected_dimensions: list[str]
    key_signals: list[str]
    mentioned_employee: MentionedEmployee | None = None
    employee_match: EmployeeMatchResult
    mentioned_menu_items: list[MentionedMenuItem]
    root_cause: RootCause
    immediate_actions: list[str]
    preventive_actions: list[str]
    suggested_owner_reply: str
    requires_manager_attention: bool


class IssueUpdate(BaseModel):
    status: IssueState | None = None
    assigned_to: str | None = Field(default=None, max_length=200)
    action_taken: str | None = None
    resolution: str | None = None


class IssueRead(ORMModel):
    id: str
    organization_id: str
    branch_id: str
    review_id: str
    category: str
    subcategory: str | None
    severity: Severity
    status: IssueState
    assigned_to: str | None
    summary: str
    action_taken: str | None
    resolution: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IssueNoteCreate(BaseModel):
    note: str = Field(min_length=1)
    author: str | None = Field(default=None, max_length=200)


class RunCreate(BaseModel):
    organization_id: str


class RunRead(ORMModel):
    id: str
    organization_id: str
    status: RunState
    attempts: int
    last_error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    branches_processed: int
    reviews_collected: int
    new_reviews: int
    analyzed_reviews: int
    positive_reviews: int
    negative_reviews: int
    neutral_reviews: int
    issues_generated: int
    created_at: datetime


class ReviewRead(ORMModel):
    id: str
    organization_id: str
    branch_id: str
    external_review_id: str
    reviewer_name: str | None
    rating: float | None
    review_text: str
    published_at: datetime | None
    review_url: str | None
    processing_state: str
    attempts: int
    last_error: str | None


class DashboardFilters(BaseModel):
    organization_id: str
    branch_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None

