"""Runtime validation checks for generated assignments, notes, and final cases."""

from __future__ import annotations

import re
from datetime import date
from logging import Logger

from .models.note import ClinicalNote
from .models.timeline import Visit, VisitAssignment


class CaseValidationError(Exception):
    """Raised when validation issues are found in strict mode."""

    def __init__(self, message: str, issues: list[str]):
        super().__init__(message)
        self.issues = issues


def enforce_validation(
    issues: list[str],
    *,
    mode: str,
    context: str,
    logger: Logger,
) -> None:
    """Apply validation mode to issues (warn or strict)."""
    if not issues:
        return

    message = f"{context}: " + " | ".join(issues)
    if mode == "strict":
        raise CaseValidationError(message, issues)
    logger.warning(message)


def validate_assignment_no_diagnosis(
    primary_condition: str,
    assignment: VisitAssignment,
) -> list[str]:
    """Ensure diagnosis terms are not leaked into clinician assignment fields."""
    issues: list[str] = []
    terms = _diagnosis_terms(primary_condition)

    fields: list[tuple[str, str]] = [
        ("reason_for_visit", assignment.reason_for_visit),
        ("visit_scenario", assignment.visit_scenario),
        ("patient_response", assignment.patient_response),
    ]
    fields.extend(("symptoms", s) for s in assignment.symptoms)
    fields.extend(("relevant_history", s) for s in assignment.relevant_history)
    fields.extend(("examination_findings", s) for s in assignment.examination_findings)
    fields.extend(("test_results", s) for s in assignment.test_results)
    fields.extend(("treatments_administered", s) for s in assignment.treatments_administered)

    for field, value in fields:
        if _contains_any_term(value, terms):
            issues.append(f"Diagnosis leakage detected in assignment.{field}")

    return issues


def validate_note_alignment(visit: Visit, note: ClinicalNote) -> list[str]:
    """Validate basic alignment between Visit and ClinicalNote."""
    issues: list[str] = []

    if note.visit_number != visit.visit_number:
        issues.append(
            f"Note visit_number ({note.visit_number}) does not match visit ({visit.visit_number})"
        )
    if note.note_date != visit.visit_date:
        issues.append(f"Note date ({note.note_date}) does not match visit date ({visit.visit_date})")
    if note.clinician_specialty != visit.clinician_specialty:
        issues.append(
            "Note clinician_specialty "
            f"({note.clinician_specialty}) does not match visit ({visit.clinician_specialty})"
        )

    content = (note.content or "").lower()
    if not content.strip():
        issues.append("Clinical note content is empty")

    for med in note.medications:
        if med and med.lower() not in content:
            issues.append(f"Medication '{med}' is in structured fields but not in note content")

    for test in note.tests_ordered:
        if test and test.lower() not in content:
            issues.append(f"Test '{test}' is in structured fields but not in note content")

    return issues


def validate_final_case(case: dict) -> list[str]:
    """Validate serialized case-level consistency checks."""
    issues: list[str] = []

    timeline = case.get("timeline", []) or []
    notes = case.get("notes", []) or []

    previous_date: date | None = None
    visit_numbers: set[int] = set()

    for idx, visit in enumerate(timeline):
        expected_num = idx + 1
        visit_num = visit.get("visit_number")
        if visit_num != expected_num:
            issues.append(
                f"Timeline visit_number mismatch at index {idx}: expected {expected_num}, got {visit_num}"
            )

        visit_date = visit.get("visit_date")
        parsed = _parse_iso_date(visit_date)
        if parsed is None:
            issues.append(f"Invalid visit_date format at visit {visit_num}: {visit_date}")
        else:
            if previous_date and parsed < previous_date:
                issues.append(
                    f"Timeline date decreased at visit {visit_num}: {visit_date} < {previous_date.isoformat()}"
                )
            previous_date = parsed

        if isinstance(visit_num, int):
            visit_numbers.add(visit_num)

    if len(notes) != len(timeline):
        issues.append(f"Notes count ({len(notes)}) does not match timeline visits ({len(timeline)})")

    for note in notes:
        note_visit = note.get("visit_number")
        if note_visit not in visit_numbers:
            issues.append(f"Note references unknown visit_number: {note_visit}")

    return issues


def _diagnosis_terms(primary_condition: str) -> set[str]:
    normalized = (primary_condition or "").strip().lower()
    terms = {normalized} if normalized else set()

    # Add key tokens to catch partial leakage while avoiding very short/common words.
    for token in re.findall(r"[a-z0-9]+", normalized):
        if len(token) >= 5:
            terms.add(token)
    return terms


def _contains_any_term(text: str, terms: set[str]) -> bool:
    haystack = (text or "").lower()
    return any(term and term in haystack for term in terms)


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
