from src.clinical_notes.models.note import ClinicalNote
from src.clinical_notes.models.timeline import Visit, VisitAssignment
from src.clinical_notes.validation import (
    validate_assignment_no_diagnosis,
    validate_final_case,
    validate_note_alignment,
)


def test_validate_assignment_no_diagnosis_detects_leakage():
    assignment = VisitAssignment(
        visit_number=1,
        visit_date="2025-01-01",
        clinician_specialty="Family Medicine",
        reason_for_visit="Follow-up for Lung Cancer symptoms",
        patient_age=67,
        patient_sex="M",
        symptoms=["persistent cough"],
        visit_scenario="Concern for progression of non-small cell lung cancer.",
    )

    issues = validate_assignment_no_diagnosis("Non-Small Cell Lung Cancer", assignment)

    assert len(issues) >= 1
    assert any("Diagnosis leakage" in issue for issue in issues)


def test_validate_note_alignment_detects_metadata_mismatch():
    visit = Visit(
        visit_number=2,
        visit_date="2025-02-01",
        clinician_specialty="Cardiology",
        reason_for_visit="Chest pain",
        is_related_to_main_illness=True,
    )
    note = ClinicalNote(
        visit_number=1,
        clinician_specialty="Emergency Medicine",
        note_date="2025-01-30",
        content="Patient seen for chest pain.",
        medications=["Aspirin"],
        tests_ordered=["ECG"],
    )

    issues = validate_note_alignment(visit, note)

    assert any("visit_number" in issue for issue in issues)
    assert any("Note date" in issue for issue in issues)
    assert any("clinician_specialty" in issue for issue in issues)


def test_validate_final_case_detects_timeline_issues():
    case = {
        "case_id": "abc123",
        "timeline": [
            {"visit_number": 1, "visit_date": "2025-02-01"},
            {"visit_number": 3, "visit_date": "2025-01-15"},
        ],
        "notes": [
            {"visit_number": 1},
        ],
    }

    issues = validate_final_case(case)

    assert any("visit_number mismatch" in issue for issue in issues)
    assert any("Timeline date decreased" in issue for issue in issues)
    assert any("Notes count" in issue for issue in issues)
