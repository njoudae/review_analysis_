import re
import unicodedata
from difflib import SequenceMatcher

from app.models import Employee, MenuItem
from app.schemas import EmployeeMatchResult, MentionedEmployee, MentionedMenuItem


ARABIC_MARKS = re.compile(r"[\u064b-\u065f\u0670]")


def normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold().strip()
    text = ARABIC_MARKS.sub("", text)
    return re.sub(r"[^\w\u0600-\u06ff]+", " ", text).strip()


def match_employee(mention: MentionedEmployee | None, employees: list[Employee]) -> EmployeeMatchResult:
    if not mention or not any((mention.name, mention.role, mention.nationality)):
        return EmployeeMatchResult(status="not_applicable", confidence=0, reason="No employee was mentioned")

    name = normalize_text(mention.name)
    role = normalize_text(mention.role)
    nationality = normalize_text(mention.nationality)
    scored: list[tuple[Employee, float, bool, bool]] = []

    for employee in employees:
        full_name = normalize_text(f"{employee.first_name} {employee.last_name}")
        first_name = normalize_text(employee.first_name)
        employee_role = normalize_text(employee.job_title)
        employee_nationality = normalize_text(employee.nationality)
        name_match = bool(name and (name == full_name or name == first_name or name in full_name))
        role_match = bool(role and (role == employee_role or role in employee_role or employee_role in role))
        nationality_match = bool(nationality and nationality == employee_nationality)
        if not name_match and not role_match:
            continue
        score = (0.65 if name_match else 0) + (0.25 if role_match else 0) + (0.1 if nationality_match else 0)
        scored.append((employee, min(score, 1.0), name_match, role_match))

    if not scored:
        reason = "Nationality alone is never used to assign an employee" if nationality else "No eligible employee matched the evidence"
        return EmployeeMatchResult(status="unidentified", confidence=0, reason=reason)

    scored.sort(key=lambda row: row[1], reverse=True)
    top_score = scored[0][1]
    top = [row for row in scored if abs(row[1] - top_score) < 0.05]
    if len(top) > 1:
        return EmployeeMatchResult(
            status="ambiguous",
            confidence=top_score,
            reason="Several branch employees match the supplied name/role evidence",
            candidate_count=len(top),
        )

    employee, score, name_match, role_match = top[0]
    status = "matched" if name_match and role_match and score >= 0.85 else "possible_match"
    return EmployeeMatchResult(
        status=status,
        employee_id=employee.id,
        confidence=score,
        reason="Unique name and role match" if status == "matched" else "Unique partial evidence match; requires confirmation",
        candidate_count=1,
    )


def match_menu_items(mentions: list[MentionedMenuItem], items: list[MenuItem]) -> list[tuple[MentionedMenuItem, MenuItem | None, float]]:
    output: list[tuple[MentionedMenuItem, MenuItem | None, float]] = []
    for mention in mentions:
        needle = normalize_text(mention.name)
        best_item: MenuItem | None = None
        best_score = 0.0
        for item in items:
            candidate = normalize_text(item.name)
            score = 0.98 if needle and (needle in candidate or candidate in needle) else SequenceMatcher(None, needle, candidate).ratio()
            if score > best_score:
                best_item, best_score = item, score
        output.append((mention, best_item if best_score >= 0.78 else None, best_score))
    return output

