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

    issues.extend(_validate_medication_continuity(timeline))
    issues.extend(_validate_pending_workup_closure(timeline))
    issues.extend(_validate_follow_up_commitments(notes, timeline))
    issues.extend(_validate_specialty_scope(notes))
    issues.extend(_validate_uncertainty_consistency(notes))

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


def _validate_medication_continuity(timeline: list[dict]) -> list[str]:
    issues: list[str] = []
    stopped: set[str] = set()

    for visit in timeline:
        visit_num = visit.get("visit_number")
        changes = visit.get("medication_changes", []) or []

        for change in changes:
            med = (change.get("medication") or "").strip().lower()
            action = (change.get("action") or "").strip().lower()
            if not med:
                continue
            if action in {"start", "continue", "adjust", "restart"}:
                stopped.discard(med)
            elif action in {"stop", "complete", "discontinue", "discontinued", "hold"}:
                stopped.add(med)

        active = {(m or "").strip().lower() for m in (visit.get("current_medications") or []) if m}
        leaked = sorted(med for med in stopped if med in active)
        if leaked:
            issues.append(
                f"Medication continuity issue at visit {visit_num}: stopped/completed meds still active ({', '.join(leaked)})"
            )

    return issues


def _validate_pending_workup_closure(timeline: list[dict]) -> list[str]:
    issues: list[str] = []
    pending: dict[str, int] = {}

    for visit in timeline:
        visit_num = int(visit.get("visit_number") or 0)
        updates = visit.get("diagnostic_workup_updates", []) or []
        for update in updates:
            test_name = (update.get("test_name") or "").strip().lower()
            status = (update.get("status") or "").strip().lower()
            if not test_name:
                continue
            if status in {"ordered", "pending"}:
                pending[test_name] = visit_num
            elif status in {"resulted", "inconclusive"}:
                pending.pop(test_name, None)

    for test_name, opened_visit in sorted(pending.items()):
        issues.append(
            f"Diagnostic workup '{test_name}' ordered/pending since visit {opened_visit} was never closed"
        )

    return issues


def _validate_follow_up_commitments(notes: list[dict], timeline: list[dict]) -> list[str]:
    issues: list[str] = []

    for idx, note in enumerate(notes[:-1]):
        visit_num = note.get("visit_number")
        recs = note.get("follow_up_recommendations", []) or []
        future_visits = timeline[idx + 1 :]
        future_text = "\n".join(
            " ".join(
                [
                    str(v.get("reason_for_visit") or ""),
                    str(v.get("visit_scenario") or ""),
                    " ".join(v.get("must_address_this_visit", []) or []),
                    " ".join(v.get("carry_forward_items", []) or []),
                ]
            ).lower()
            for v in future_visits
        )

        for rec in recs:
            rec_text = (rec or "").strip().lower()
            if not rec_text:
                continue
            if rec_text not in future_text:
                issues.append(
                    f"Follow-up commitment from note visit {visit_num} not reflected later: '{rec}'"
                )

    return issues


def _validate_specialty_scope(notes: list[dict]) -> list[str]:
    issues: list[str] = []
    for note in notes:
        visit_num = note.get("visit_number")
        uncertainty = note.get("diagnostic_uncertainty", []) or []
        scope_stmt = (note.get("specialty_scope_statement") or "").strip()
        if uncertainty and not scope_stmt:
            issues.append(
                f"Specialty scope issue at note visit {visit_num}: uncertainty documented without specialty_scope_statement"
            )
    return issues


def _validate_uncertainty_consistency(notes: list[dict]) -> list[str]:
    issues: list[str] = []
    for note in notes:
        visit_num = note.get("visit_number")
        uncertainty = note.get("diagnostic_uncertainty", []) or []
        follow_up = note.get("follow_up_recommendations", []) or []
        workup_actions = note.get("workup_plan_actions", []) or []

        has_low_or_medium = any(
            (u.get("confidence") or "").strip().lower() in {"low", "medium"} for u in uncertainty
        )
        if has_low_or_medium and not follow_up and not workup_actions:
            issues.append(
                f"Uncertainty consistency issue at note visit {visit_num}: low/medium confidence without follow-up/workup plan"
            )

    return issues


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
