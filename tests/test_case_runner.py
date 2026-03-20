from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.case_runner import CaseRunner
from src.clinical_notes.models.case import CaseConfig, ClinicalVariables, Difficulty
from src.clinical_notes.models.note import ClinicalNote
from src.clinical_notes.models.patient import MedicalHistorySummary, PatientDemographics
from src.clinical_notes.models.timeline import Timeline, Visit, VisitAssignment


@pytest.fixture
def case_config():
    return CaseConfig(
        case_id="orch-test",
        clinical_variables=ClinicalVariables(
            primary_condition="Appendicitis",
            comorbidities=[],
            age=25,
            sex="F",
            risk_factors=[],
        ),
        difficulty=Difficulty.EASY,
    )


@pytest.mark.asyncio
async def test_generate_case_end_to_end(case_config):
    """Integration test with mocked LLM calls — verifies the pipeline wiring."""
    mock_narrative = "The patient developed acute abdominal pain..."

    mock_timeline = Timeline(
        case_id="",
        visits=[
            Visit(
                visit_number=1,
                visit_date="2025-03-01",
                clinician_specialty="Emergency Medicine",
                reason_for_visit="Severe abdominal pain",
                is_related_to_main_illness=True,
                patient_age=25,
                patient_sex="F",
                symptoms=["RLQ pain", "Nausea", "Low-grade fever"],
                vitals={"Temp": "38.1C", "HR": "95", "BP": "120/78"},
                visit_scenario="Patient presents to ER with acute onset RLQ pain. "
                "CT abdomen shows inflamed appendix. Surgical consult obtained.",
                examination_findings=["RLQ tenderness", "Rebound tenderness", "Guarding"],
                tests_ordered=["CT abdomen", "CBC", "BMP"],
                test_results=[],
                treatments_administered=["IV Morphine", "IV fluids"],
                disease_progression_notes="Acute appendicitis, surgical candidate",
            ),
            Visit(
                visit_number=2,
                visit_date="2025-03-02",
                clinician_specialty="General Surgery",
                reason_for_visit="Surgical follow-up",
                is_related_to_main_illness=True,
                patient_age=25,
                patient_sex="F",
                symptoms=["Mild incisional pain"],
                vitals={"Temp": "37.2C", "HR": "78", "BP": "118/72"},
                current_medications=["IV Morphine", "Cefazolin"],
                visit_scenario="Post-appendectomy day 1. Patient recovering well. "
                "Wound check shows clean incision. Advancing diet.",
                examination_findings=["Clean surgical incision", "Soft abdomen"],
                tests_ordered=["CBC"],
                test_results=["CT: inflamed appendix", "CBC: WBC 14.2"],
                treatments_administered=["Cefazolin", "Acetaminophen"],
                patient_response="Pain well controlled with current regimen",
                disease_progression_notes="Post-appendectomy, recovering well",
            ),
        ],
    )

    mock_assignment = VisitAssignment(
        visit_number=1,
        visit_date="2025-03-01",
        clinician_specialty="Emergency Medicine",
        reason_for_visit="Severe abdominal pain",
        patient_age=25,
        patient_sex="F",
        symptoms=["RLQ pain", "Nausea", "Low-grade fever"],
        visit_scenario="Patient presents to ER with acute onset RLQ pain. "
        "CT abdomen ordered. Surgical consult obtained.",
        examination_findings=["RLQ tenderness", "Rebound tenderness", "Guarding"],
        tests_ordered=["CT abdomen", "CBC", "BMP"],
        treatments_administered=["IV Morphine", "IV fluids"],
    )

    mock_note = ClinicalNote(
        visit_number=1,
        clinician_specialty="Emergency Medicine",
        note_date="2025-03-01",
        content="25F presents with acute onset RLQ pain...",
        symptoms_reported=["RLQ pain", "Nausea"],
        diagnoses_considered=["Appendicitis", "Ovarian cyst"],
        medications=["IV Morphine"],
    )

    # Progressive history objects returned by the scribe
    history_after_visit_1 = MedicalHistorySummary(
        demographics=PatientDemographics(age=25, sex="F"),
        current_medications=["IV Morphine"],
        prior_visit_summaries=[
            "Emergency Medicine visit on 2025-03-01: Severe abdominal pain. "
            "RLQ tenderness, nausea, low-grade fever. IV Morphine administered."
        ],
    )
    history_after_visit_2 = MedicalHistorySummary(
        demographics=PatientDemographics(age=25, sex="F"),
        current_medications=["IV Morphine", "Cefazolin"],
        prior_visit_summaries=[
            "Emergency Medicine visit on 2025-03-01: Severe abdominal pain. "
            "RLQ tenderness, nausea, low-grade fever. IV Morphine administered.",
            "General Surgery visit on 2025-03-02: Surgical follow-up. "
            "Post-operative recovery, wound check.",
        ],
    )

    runner = CaseRunner()

    with (
        patch.object(runner.narrator, "run", new_callable=AsyncMock) as mock_narrator,
        patch.object(runner.orchestrator, "run", new_callable=AsyncMock) as mock_orchestrator,
        patch.object(
            runner.coordinator, "run", new_callable=AsyncMock
        ) as mock_coordinator,
        patch.object(runner.clinician, "run", new_callable=AsyncMock) as mock_clinician,
        patch.object(runner.scribe, "run", new_callable=AsyncMock) as mock_scribe,
    ):
        mock_narrator.return_value = mock_narrative
        mock_orchestrator.return_value = mock_timeline
        mock_coordinator.return_value = mock_assignment
        mock_clinician.return_value = mock_note
        mock_scribe.side_effect = [history_after_visit_1, history_after_visit_2]

        result = await runner.generate_case(case_config)

    assert result["case_id"] == "orch-test"
    assert result["narrative"] == mock_narrative
    assert len(result["timeline"]) == 2
    assert len(result["notes"]) == 2

    # Verify sequential processing — coordinator/clinician/scribe called once per visit
    assert mock_coordinator.call_count == 2
    assert mock_clinician.call_count == 2
    assert mock_scribe.call_count == 2

    # Verify coordinator called without narrative param
    for call in mock_coordinator.call_args_list:
        # Should be called with primary_condition, visit, medical_history (no narrative)
        assert "narrative" not in call.kwargs

    # Verify medical history reflects scribe output
    final_history = result["final_medical_history"]
    assert len(final_history["prior_visit_summaries"]) == 2
    assert "IV Morphine" in final_history["current_medications"]
