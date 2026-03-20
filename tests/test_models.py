import pytest
from pydantic import ValidationError

from src.clinical_notes.models.case import (
    CaseConfig,
    CaseOutcome,
    CaseType,
    ClinicalVariables,
    Difficulty,
)
from src.clinical_notes.models.note import ClinicalNote
from src.clinical_notes.models.patient import MedicalHistorySummary, PatientDemographics
from src.clinical_notes.models.timeline import Timeline, Visit, VisitAssignment


class TestClinicalVariables:
    def test_valid(self):
        cv = ClinicalVariables(
            primary_condition="Pneumonia",
            age=45,
            sex="F",
        )
        assert cv.primary_condition == "Pneumonia"
        assert cv.comorbidities == []
        assert cv.risk_factors == []

    def test_full(self):
        cv = ClinicalVariables(
            primary_condition="Type 2 DM",
            comorbidities=["HTN"],
            age=60,
            sex="M",
            risk_factors=["Obesity"],
        )
        assert len(cv.comorbidities) == 1

    def test_invalid_age(self):
        with pytest.raises(ValidationError):
            ClinicalVariables(primary_condition="X", age=200, sex="M")


class TestCaseConfig:
    def test_defaults(self):
        config = CaseConfig(
            case_id="test-1",
            clinical_variables=ClinicalVariables(
                primary_condition="Asthma", age=30, sex="F"
            ),
        )
        assert config.difficulty == Difficulty.MEDIUM
        assert config.case_type == CaseType.ACUTE
        assert config.intended_outcome == CaseOutcome.RESOLVED
        assert config.narrative is None


class TestVisit:
    def test_valid(self):
        v = Visit(
            visit_number=1,
            visit_date="2025-01-15",
            clinician_specialty="Family Medicine",
            reason_for_visit="Cough and fever",
            is_related_to_main_illness=True,
        )
        assert v.note is None
        # New default fields
        assert v.patient_age == 0
        assert v.patient_sex == ""
        assert v.symptoms == []
        assert v.vitals == {}
        assert v.relevant_history == []
        assert v.known_conditions == []
        assert v.current_medications == []
        assert v.allergies == []
        assert v.visit_scenario == ""
        assert v.examination_findings == []
        assert v.tests_ordered == []
        assert v.test_results == []
        assert v.treatments_administered == []
        assert v.patient_response == ""
        assert v.disease_progression_notes == ""

    def test_rich(self):
        v = Visit(
            visit_number=2,
            visit_date="2025-02-01",
            clinician_specialty="Cardiology",
            reason_for_visit="Follow-up chest pain",
            is_related_to_main_illness=True,
            patient_age=55,
            patient_sex="M",
            symptoms=["Chest pain", "Shortness of breath"],
            vitals={"BP": "140/90", "HR": "88", "SpO2": "96%"},
            relevant_history=["Prior ER visit for chest pain"],
            known_conditions=["Hypertension", "Hyperlipidemia"],
            current_medications=["Lisinopril 10mg", "Atorvastatin 20mg"],
            allergies=["Penicillin"],
            visit_scenario="Patient presents for cardiology follow-up. ECG shows ST changes. Troponin ordered.",
            examination_findings=["S4 gallop", "JVD absent"],
            tests_ordered=["Troponin", "ECG", "Echocardiogram"],
            test_results=["Prior ECG: ST depression in V4-V6"],
            treatments_administered=["Aspirin 325mg", "Nitroglycerin SL"],
            patient_response="Pain improved with nitroglycerin",
            disease_progression_notes="Progressing coronary artery disease with worsening angina",
        )
        assert v.patient_age == 55
        assert len(v.symptoms) == 2
        assert v.vitals["BP"] == "140/90"
        assert len(v.examination_findings) == 2
        assert v.disease_progression_notes != ""

    def test_invalid_visit_number(self):
        with pytest.raises(ValidationError):
            Visit(
                visit_number=0,
                visit_date="2025-01-15",
                clinician_specialty="FM",
                reason_for_visit="Test",
                is_related_to_main_illness=True,
            )


class TestTimeline:
    def test_empty(self):
        t = Timeline(case_id="c1")
        assert t.visits == []


class TestVisitAssignment:
    def test_minimal(self):
        va = VisitAssignment(
            visit_number=1,
            visit_date="2025-01-15",
            clinician_specialty="ER",
            reason_for_visit="Chest pain",
            patient_age=55,
            patient_sex="M",
        )
        assert va.symptoms == []
        assert va.vitals == {}
        assert va.known_conditions == []
        assert va.current_medications == []
        assert va.prior_visit_summaries == []
        assert va.allergies == []
        # New default fields
        assert va.visit_scenario == ""
        assert va.examination_findings == []
        assert va.tests_ordered == []
        assert va.test_results == []
        assert va.treatments_administered == []
        assert va.patient_response == ""

    def test_with_history_fields(self):
        va = VisitAssignment(
            visit_number=2,
            visit_date="2025-02-01",
            clinician_specialty="Cardiology",
            reason_for_visit="Follow-up chest pain",
            patient_age=55,
            patient_sex="M",
            known_conditions=["Hypertension", "Hyperlipidemia"],
            current_medications=["Lisinopril 10mg", "Atorvastatin 20mg"],
            prior_visit_summaries=["ER visit on 2025-01-15: Chest pain evaluation."],
            allergies=["Penicillin"],
            visit_scenario="Patient returns for cardiology follow-up after ER visit.",
            examination_findings=["S4 gallop"],
            tests_ordered=["Echocardiogram"],
            test_results=["Troponin negative"],
            treatments_administered=["Aspirin 81mg daily"],
            patient_response="Chest pain resolved since ER visit",
        )
        assert len(va.known_conditions) == 2
        assert "Lisinopril 10mg" in va.current_medications
        assert len(va.prior_visit_summaries) == 1
        assert va.allergies == ["Penicillin"]
        assert va.visit_scenario != ""
        assert len(va.examination_findings) == 1
        assert len(va.test_results) == 1
        assert va.patient_response != ""


class TestPatientDemographics:
    def test_valid(self):
        pd = PatientDemographics(age=40, sex="F")
        assert pd.height is None


class TestMedicalHistorySummary:
    def test_defaults(self):
        mh = MedicalHistorySummary(
            demographics=PatientDemographics(age=40, sex="F"),
        )
        assert mh.known_conditions == []
        assert mh.allergies == []


class TestClinicalNote:
    def test_valid(self):
        note = ClinicalNote(
            visit_number=1,
            clinician_specialty="Family Medicine",
            note_date="2025-01-15",
            content="Patient presents with...",
        )
        assert note.tests_ordered == []
        assert note.medications == []
