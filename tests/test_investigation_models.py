import pytest
from pydantic import ValidationError

from src.clinical_notes.models.investigation import (
    CaseSeed,
    Confidence,
    InvestigationPlan,
    InvestigatorReport,
    KnowledgeSource,
    KnowledgeSourceType,
    VariableAssignment,
)


class TestKnowledgeSource:
    def test_web_url(self):
        ks = KnowledgeSource(
            source_type=KnowledgeSourceType.WEB_URL,
            location="https://example.com/guidelines",
            description="NCCN guidelines",
        )
        assert ks.source_type == KnowledgeSourceType.WEB_URL
        assert ks.description == "NCCN guidelines"

    def test_local_file(self):
        ks = KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_FILE,
            location="/data/study.pdf",
        )
        assert ks.source_type == KnowledgeSourceType.LOCAL_FILE
        assert ks.description is None

    def test_local_directory(self):
        ks = KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_DIRECTORY,
            location="/data/references/",
        )
        assert ks.source_type == KnowledgeSourceType.LOCAL_DIRECTORY


class TestCaseSeed:
    def test_minimal(self):
        seed = CaseSeed(raw_variables={"Primary Site": "C34.1"})
        assert seed.raw_variables == {"Primary Site": "C34.1"}
        assert seed.coding_system is None
        assert seed.age is None
        assert seed.sex is None
        assert seed.difficulty == "medium"
        assert seed.case_type == "acute"
        assert seed.intended_outcome == "resolved"
        assert seed.knowledge_sources == []

    def test_full(self):
        seed = CaseSeed(
            raw_variables={
                "Primary Site": "C34.1",
                "Histologic Type": "8070/3",
                "Grade": "2",
            },
            coding_system="NAACCR",
            age=65,
            sex="M",
            difficulty="hard",
            case_type="chronic",
            intended_outcome="worsening",
            knowledge_sources=[
                KnowledgeSource(
                    source_type=KnowledgeSourceType.WEB_URL,
                    location="https://example.com",
                ),
            ],
        )
        assert seed.age == 65
        assert seed.sex == "M"
        assert seed.coding_system == "NAACCR"
        assert len(seed.raw_variables) == 3
        assert len(seed.knowledge_sources) == 1

    def test_invalid_age(self):
        with pytest.raises(ValidationError):
            CaseSeed(raw_variables={"Primary Site": "C34.1"}, age=200)


class TestVariableAssignment:
    def test_basic(self):
        va = VariableAssignment(
            variable_name="Primary Site",
            investigation_focus="Look up the ICD-O-3 topography code",
            raw_value="C34.1",
        )
        assert va.variable_name == "Primary Site"
        assert va.raw_value == "C34.1"
        assert va.coding_system is None
        assert va.relevant_sources == []

    def test_with_sources_and_coding_system(self):
        va = VariableAssignment(
            variable_name="Histologic Type",
            investigation_focus="Look up the histology/behavior code",
            raw_value="8070/3",
            coding_system="NAACCR",
            relevant_sources=[0, 2],
        )
        assert va.relevant_sources == [0, 2]
        assert va.coding_system == "NAACCR"

    def test_default_raw_value(self):
        va = VariableAssignment(
            variable_name="staging",
            investigation_focus="Determine TNM staging",
        )
        assert va.raw_value == ""


class TestInvestigationPlan:
    def test_with_variables(self):
        plan = InvestigationPlan(
            variables=[
                VariableAssignment(
                    variable_name="Primary Site",
                    investigation_focus="Look up topography code",
                    raw_value="C34.1",
                ),
                VariableAssignment(
                    variable_name="Histologic Type",
                    investigation_focus="Look up histology code",
                    raw_value="8070/3",
                ),
            ],
            suggested_age=62,
            suggested_sex="F",
        )
        assert len(plan.variables) == 2
        assert plan.suggested_age == 62
        assert plan.suggested_sex == "F"


class TestInvestigatorReport:
    def test_minimal(self):
        report = InvestigatorReport(
            variable_name="Primary Site",
            variable_value="Upper lobe of lung",
        )
        assert report.variable_name == "Primary Site"
        assert report.confidence == Confidence.MEDIUM
        assert report.associated_symptoms == []
        assert report.prognosis_notes is None
        assert report.clinical_staging is None

    def test_full(self):
        report = InvestigatorReport(
            variable_name="Histologic Type",
            variable_value="Squamous cell carcinoma, keratinizing (8070/3)",
            associated_symptoms=["Persistent cough", "Dyspnea", "Chest pain"],
            associated_comorbidities=["COPD", "Pulmonary fibrosis"],
            associated_risk_factors=["Smoking history", "Asbestos exposure"],
            phenotypic_features=["Cachexia", "Clubbing"],
            prognosis_notes="5-year survival ~36% for Stage IIIA NSCLC",
            treatment_considerations=["Concurrent chemoradiation", "Surgical resection if operable"],
            clinical_staging="T3N1M0",
            source_summary="Based on NAACCR coding manual and NCCN guidelines",
            confidence=Confidence.HIGH,
        )
        assert len(report.associated_symptoms) == 3
        assert report.confidence == Confidence.HIGH
        assert report.clinical_staging == "T3N1M0"
