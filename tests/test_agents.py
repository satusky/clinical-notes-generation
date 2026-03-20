from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.agents.clinician import ClinicianAgent
from src.clinical_notes.agents.coordinator import CoordinatorAgent
from src.clinical_notes.agents.narrator import NarratorAgent
from src.clinical_notes.agents.orchestrator import OrchestratorAgent
from src.clinical_notes.agents.scribe import ScribeAgent
from src.clinical_notes.models.case import CaseConfig, ClinicalVariables, Difficulty
from src.clinical_notes.models.note import ClinicalNote
from src.clinical_notes.models.patient import MedicalHistorySummary, PatientDemographics
from src.clinical_notes.models.timeline import Timeline, Visit, VisitAssignment


@pytest.fixture
def case_config():
    return CaseConfig(
        case_id="test-1",
        clinical_variables=ClinicalVariables(
            primary_condition="Pneumonia",
            comorbidities=["COPD"],
            age=65,
            sex="M",
            risk_factors=["Smoking"],
        ),
        difficulty=Difficulty.EASY,
    )


@pytest.fixture
def medical_history():
    return MedicalHistorySummary(
        demographics=PatientDemographics(age=65, sex="M"),
        known_conditions=["COPD"],
    )


@pytest.fixture
def rich_visit():
    return Visit(
        visit_number=1,
        visit_date="2025-01-15",
        clinician_specialty="Family Medicine",
        reason_for_visit="Cough and fever",
        is_related_to_main_illness=True,
        patient_age=65,
        patient_sex="M",
        symptoms=["Productive cough", "Fever 38.5C", "Fatigue"],
        vitals={"BP": "130/85", "HR": "92", "Temp": "38.5C", "SpO2": "94%"},
        relevant_history=["COPD", "20 pack-year smoking history"],
        known_conditions=["COPD"],
        current_medications=[],
        allergies=[],
        visit_scenario="Patient presents with 3-day history of productive cough and fever. "
        "Chest X-ray shows right lower lobe infiltrate consistent with pneumonia. "
        "Started on amoxicillin-clavulanate.",
        examination_findings=["Crackles in right lower lobe", "Decreased breath sounds RLL"],
        tests_ordered=["Chest X-ray", "CBC", "Sputum culture"],
        test_results=[],
        treatments_administered=["Amoxicillin-clavulanate 875/125mg"],
        patient_response="",
        disease_progression_notes="Community-acquired pneumonia, right lower lobe",
    )


@pytest.mark.asyncio
async def test_narrator_calls_generate(case_config):
    agent = NarratorAgent()
    with patch("src.clinical_notes.agents.narrator.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "The patient developed a cough..."
        result = await agent.run(case_config)
    assert result == "The patient developed a cough..."
    mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_calls_generate_structured(case_config):
    agent = OrchestratorAgent()
    mock_timeline = Timeline(
        case_id="",
        visits=[
            Visit(
                visit_number=1,
                visit_date="2025-01-15",
                clinician_specialty="Family Medicine",
                reason_for_visit="Cough",
                is_related_to_main_illness=True,
                patient_age=65,
                patient_sex="M",
                symptoms=["Cough"],
                visit_scenario="Patient presents with cough.",
            )
        ],
    )
    with patch(
        "src.clinical_notes.agents.orchestrator.generate_structured", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_timeline
        result = await agent.run(case_config, "narrative text")
    assert result.case_id == "test-1"
    assert len(result.visits) == 1


@pytest.mark.asyncio
async def test_coordinator_strips_diagnosis(case_config, medical_history, rich_visit):
    agent = CoordinatorAgent()
    mock_assignment = VisitAssignment(
        visit_number=1,
        visit_date="2025-01-15",
        clinician_specialty="Family Medicine",
        reason_for_visit="Cough and fever",
        patient_age=65,
        patient_sex="M",
        symptoms=["Productive cough", "Fever 38.5C", "Fatigue"],
        visit_scenario="Patient presents with 3-day history of productive cough and fever. "
        "Chest X-ray shows right lower lobe infiltrate. Started on antibiotics.",
        examination_findings=["Crackles in right lower lobe", "Decreased breath sounds RLL"],
        tests_ordered=["Chest X-ray", "CBC", "Sputum culture"],
        test_results=[],
        treatments_administered=["Amoxicillin-clavulanate 875/125mg"],
    )
    with patch(
        "src.clinical_notes.agents.coordinator.generate_structured", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_assignment
        result = await agent.run("Pneumonia", rich_visit, medical_history)
    # Verify the assignment doesn't contain the diagnosis
    assert "Pneumonia" not in str(result.symptoms)
    assert "Pneumonia" not in result.reason_for_visit
    assert "Pneumonia" not in result.visit_scenario


@pytest.mark.asyncio
async def test_clinician_produces_note(medical_history):
    agent = ClinicianAgent()
    assignment = VisitAssignment(
        visit_number=1,
        visit_date="2025-01-15",
        clinician_specialty="Family Medicine",
        reason_for_visit="Cough and fever",
        patient_age=65,
        patient_sex="M",
        symptoms=["Productive cough", "Fever 38.5C"],
        visit_scenario="Patient presents with productive cough and fever. Exam reveals crackles.",
        examination_findings=["Crackles in right lower lobe"],
        tests_ordered=["Chest X-ray", "CBC"],
        test_results=[],
        treatments_administered=["Amoxicillin-clavulanate 875/125mg"],
    )
    mock_note = ClinicalNote(
        visit_number=1,
        clinician_specialty="Family Medicine",
        note_date="2025-01-15",
        content="Patient presents with productive cough and fever...",
        symptoms_reported=["Productive cough", "Fever"],
        diagnoses_considered=["Community-acquired pneumonia", "Acute bronchitis"],
    )
    with patch(
        "src.clinical_notes.agents.clinician.generate_structured", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_note
        result = await agent.run(assignment, medical_history)
    assert result.content.startswith("Patient presents")
    assert len(result.diagnoses_considered) == 2


@pytest.mark.asyncio
async def test_scribe_updates_history(medical_history):
    agent = ScribeAgent()
    note = ClinicalNote(
        visit_number=1,
        clinician_specialty="Family Medicine",
        note_date="2025-01-15",
        content="Patient presents with productive cough and fever...",
        symptoms_reported=["Productive cough", "Fever"],
        diagnoses_considered=["Community-acquired pneumonia", "Acute bronchitis"],
        medications=["Amoxicillin 500mg TID"],
    )
    visit = Visit(
        visit_number=1,
        visit_date="2025-01-15",
        clinician_specialty="Family Medicine",
        reason_for_visit="Cough and fever",
        is_related_to_main_illness=True,
    )
    updated_history = MedicalHistorySummary(
        demographics=PatientDemographics(age=65, sex="M"),
        known_conditions=["COPD"],
        current_medications=["Amoxicillin 500mg TID"],
        prior_visit_summaries=[
            "Family Medicine visit on 2025-01-15: Cough and fever. "
            "Productive cough, fever noted. Amoxicillin prescribed."
        ],
    )
    with patch(
        "src.clinical_notes.agents.scribe.generate_structured", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = updated_history
        result = await agent.run(medical_history, note, visit)

    # Verify output doesn't contain diagnosis terms
    for summary in result.prior_visit_summaries:
        assert "pneumonia" not in summary.lower()
        assert "bronchitis" not in summary.lower()

    # Verify medications updated
    assert "Amoxicillin 500mg TID" in result.current_medications
