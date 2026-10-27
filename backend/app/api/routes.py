from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import (
    Branch,
    BusinessType,
    CollectionRun,
    Employee,
    Issue,
    IssueNote,
    IssueState,
    IssueStatusHistory,
    MenuCategory,
    MenuItem,
    Organization,
    RecordStatus,
    Review,
    ReviewAnalysis,
    ReviewSource,
    RunState,
    utcnow,
)
from app.schemas import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    IssueNoteCreate,
    IssueRead,
    IssueUpdate,
    MenuCategoryCreate,
    MenuCategoryRead,
    MenuItemCreate,
    MenuItemRead,
    MenuItemUpdate,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    ReviewRead,
    RunCreate,
    RunRead,
)
from app.services.metrics import branch_performance, dashboard_summary


router = APIRouter()


def not_found(entity: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{entity} not found")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "reachable"}


@router.post("/organizations", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"logo_url"})
    organization = Organization(**data, logo_url=str(payload.logo_url) if payload.logo_url else None)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)):
    return db.scalars(select(Organization).order_by(Organization.name)).all()


@router.get("/organizations/{organization_id}", response_model=OrganizationRead)
def get_organization(organization_id: str, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if not organization:
        raise not_found("Organization")
    return organization


@router.patch("/organizations/{organization_id}", response_model=OrganizationRead)
def update_organization(organization_id: str, payload: OrganizationUpdate, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if not organization:
        raise not_found("Organization")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(organization, key, str(value) if key == "logo_url" and value else value)
    db.commit()
    db.refresh(organization)
    return organization


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(organization_id: str, db: Session = Depends(get_db)):
    organization = db.get(Organization, organization_id)
    if not organization:
        raise not_found("Organization")
    db.delete(organization)
    db.commit()


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db)):
    if not db.get(Organization, payload.organization_id):
        raise not_found("Organization")
    data = payload.model_dump(exclude={"google_maps_url"})
    url = str(payload.google_maps_url)
    branch = Branch(**data, google_maps_url=url)
    db.add(branch)
    db.flush()
    db.add(ReviewSource(branch_id=branch.id, provider="google_maps", source_url=url))
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/branches", response_model=list[BranchRead])
def list_branches(organization_id: str, status_filter: RecordStatus | None = Query(default=None, alias="status"), db: Session = Depends(get_db)):
    query = select(Branch).where(Branch.organization_id == organization_id)
    if status_filter:
        query = query.where(Branch.status == status_filter)
    return db.scalars(query.order_by(Branch.name)).all()


@router.get("/branches/{branch_id}", response_model=BranchRead)
def get_branch(branch_id: str, db: Session = Depends(get_db)):
    branch = db.get(Branch, branch_id)
    if not branch:
        raise not_found("Branch")
    return branch


@router.patch("/branches/{branch_id}", response_model=BranchRead)
def update_branch(branch_id: str, payload: BranchUpdate, db: Session = Depends(get_db)):
    branch = db.get(Branch, branch_id)
    if not branch:
        raise not_found("Branch")
    values = payload.model_dump(exclude_unset=True)
    if values.get("google_maps_url"):
        values["google_maps_url"] = str(values["google_maps_url"])
    for key, value in values.items():
        setattr(branch, key, value)
    if "google_maps_url" in values:
        source = db.scalar(select(ReviewSource).where(ReviewSource.branch_id == branch.id, ReviewSource.provider == "google_maps"))
        if source:
            source.source_url = values["google_maps_url"]
        else:
            db.add(ReviewSource(branch_id=branch.id, provider="google_maps", source_url=values["google_maps_url"]))
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(branch_id: str, db: Session = Depends(get_db)):
    branch = db.get(Branch, branch_id)
    if not branch:
        raise not_found("Branch")
    db.delete(branch)
    db.commit()


def refresh_employee_count(db: Session, branch_id: str) -> None:
    branch = db.get(Branch, branch_id)
    if branch:
        branch.employee_count = db.scalar(select(func.count(Employee.id)).where(Employee.branch_id == branch_id)) or 0


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    branch = db.get(Branch, payload.branch_id)
    if not branch or branch.organization_id != payload.organization_id:
        raise HTTPException(status_code=422, detail="Branch does not belong to the organization")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.flush()
    refresh_employee_count(db, employee.branch_id)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/employees", response_model=list[EmployeeRead])
def list_employees(
    organization_id: str,
    branch_id: str | None = None,
    gender: str | None = None,
    status_filter: RecordStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = select(Employee).where(Employee.organization_id == organization_id)
    if branch_id:
        query = query.where(Employee.branch_id == branch_id)
    if gender:
        query = query.where(Employee.gender == gender)
    if status_filter:
        query = query.where(Employee.status == status_filter)
    return db.scalars(query.order_by(Employee.first_name, Employee.last_name)).all()


@router.patch("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: str, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise not_found("Employee")
    old_branch_id = employee.branch_id
    values = payload.model_dump(exclude_unset=True)
    if values.get("branch_id"):
        branch = db.get(Branch, values["branch_id"])
        if not branch or branch.organization_id != employee.organization_id:
            raise HTTPException(status_code=422, detail="Branch does not belong to the organization")
    for key, value in values.items():
        setattr(employee, key, value)
    db.flush()
    refresh_employee_count(db, old_branch_id)
    refresh_employee_count(db, employee.branch_id)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise not_found("Employee")
    branch_id = employee.branch_id
    db.delete(employee)
    db.flush()
    refresh_employee_count(db, branch_id)
    db.commit()


@router.post("/menu/categories", response_model=MenuCategoryRead, status_code=status.HTTP_201_CREATED)
def create_menu_category(payload: MenuCategoryCreate, db: Session = Depends(get_db)):
    organization = db.get(Organization, payload.organization_id)
    if not organization:
        raise not_found("Organization")
    if organization.business_type not in {BusinessType.RESTAURANT, BusinessType.CAFE}:
        raise HTTPException(status_code=422, detail="Menu management is available only for restaurants and cafes")
    category = MenuCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/menu/categories", response_model=list[MenuCategoryRead])
def list_menu_categories(organization_id: str, db: Session = Depends(get_db)):
    return db.scalars(select(MenuCategory).where(MenuCategory.organization_id == organization_id).order_by(MenuCategory.name)).all()


@router.post("/menu/items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_menu_item(payload: MenuItemCreate, db: Session = Depends(get_db)):
    if not db.get(MenuCategory, payload.category_id):
        raise not_found("Menu category")
    item = MenuItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/menu/items", response_model=list[MenuItemRead])
def list_menu_items(organization_id: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(MenuItem).join(MenuCategory).where(MenuCategory.organization_id == organization_id).order_by(MenuItem.name)
    ).all()


@router.patch("/menu/items/{item_id}", response_model=MenuItemRead)
def update_menu_item(item_id: str, payload: MenuItemUpdate, db: Session = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item:
        raise not_found("Menu item")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/menu/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item:
        raise not_found("Menu item")
    db.delete(item)
    db.commit()


@router.get("/reviews")
def list_reviews(
    organization_id: str,
    branch_id: str | None = None,
    sentiment: str | None = None,
    rating: float | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Review, ReviewAnalysis).outerjoin(ReviewAnalysis, ReviewAnalysis.review_id == Review.id).where(Review.organization_id == organization_id)
    if branch_id:
        query = query.where(Review.branch_id == branch_id)
    if sentiment:
        query = query.where(ReviewAnalysis.sentiment == sentiment)
    if rating is not None:
        query = query.where(Review.rating == rating)
    if search:
        query = query.where(or_(Review.review_text.ilike(f"%{search}%"), Review.reviewer_name.ilike(f"%{search}%")))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(Review.published_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [
            {
                **ReviewRead.model_validate(review).model_dump(mode="json"),
                "analysis": {
                    "sentiment": analysis.sentiment.value,
                    "is_issue": analysis.is_issue,
                    "category": analysis.issue_category,
                    "severity": analysis.severity.value,
                    "summary": analysis.summary,
                } if analysis else None,
            }
            for review, analysis in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/issues", response_model=list[IssueRead])
def list_issues(
    organization_id: str,
    branch_id: str | None = None,
    issue_status: IssueState | None = Query(default=None, alias="status"),
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Issue).where(Issue.organization_id == organization_id)
    if branch_id:
        query = query.where(Issue.branch_id == branch_id)
    if issue_status:
        query = query.where(Issue.status == issue_status)
    if severity:
        query = query.where(Issue.severity == severity)
    return db.scalars(query.order_by(Issue.created_at.desc())).all()


@router.get("/issues/{issue_id}")
def get_issue(issue_id: str, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue:
        raise not_found("Issue")
    review = db.get(Review, issue.review_id)
    analysis = db.scalar(select(ReviewAnalysis).where(ReviewAnalysis.review_id == issue.review_id))
    notes = db.scalars(select(IssueNote).where(IssueNote.issue_id == issue.id).order_by(IssueNote.created_at)).all()
    return {
        "issue": IssueRead.model_validate(issue).model_dump(mode="json"),
        "review": ReviewRead.model_validate(review).model_dump(mode="json"),
        "analysis": analysis.raw_analysis if analysis else None,
        "notes": [{"id": note.id, "note": note.note, "author": note.author, "created_at": note.created_at} for note in notes],
    }


@router.patch("/issues/{issue_id}", response_model=IssueRead)
def update_issue(issue_id: str, payload: IssueUpdate, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue:
        raise not_found("Issue")
    old_status = issue.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(issue, key, value)
    if payload.status and payload.status != old_status:
        db.add(IssueStatusHistory(issue_id=issue.id, from_status=old_status.value, to_status=payload.status.value))
        if payload.status == IssueState.RESOLVED:
            issue.resolved_at = utcnow()
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/issues/{issue_id}/notes", status_code=status.HTTP_201_CREATED)
def add_issue_note(issue_id: str, payload: IssueNoteCreate, db: Session = Depends(get_db)):
    if not db.get(Issue, issue_id):
        raise not_found("Issue")
    note = IssueNote(issue_id=issue_id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "created_at": note.created_at}


@router.post("/runs", response_model=RunRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_run(payload: RunCreate, db: Session = Depends(get_db)):
    if not db.get(Organization, payload.organization_id):
        raise not_found("Organization")
    active = db.scalar(
        select(CollectionRun).where(
            CollectionRun.organization_id == payload.organization_id,
            CollectionRun.status.notin_([RunState.COMPLETED, RunState.FAILED]),
        )
    )
    if active:
        raise HTTPException(status_code=409, detail=f"Run {active.id} is already active")
    run = CollectionRun(organization_id=payload.organization_id)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=list[RunRead])
def list_runs(organization_id: str, db: Session = Depends(get_db)):
    return db.scalars(select(CollectionRun).where(CollectionRun.organization_id == organization_id).order_by(CollectionRun.created_at.desc())).all()


@router.post("/runs/{run_id}/retry", response_model=RunRead, status_code=status.HTTP_202_ACCEPTED)
def retry_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(CollectionRun, run_id)
    if not run:
        raise not_found("Run")
    if run.status != RunState.FAILED:
        raise HTTPException(status_code=409, detail="Only failed runs can be retried")
    run.status = RunState.STARTED
    run.last_error = None
    db.commit()
    db.refresh(run)
    return run


@router.get("/dashboard/summary")
def get_dashboard_summary(
    organization_id: str,
    branch_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return dashboard_summary(db, organization_id, branch_id, start_date, end_date)


@router.get("/dashboard/branches")
def get_branch_performance(
    organization_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return branch_performance(db, organization_id, start_date, end_date)

