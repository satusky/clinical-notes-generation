from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.agents.constructor import ConstructorAgent
from src.clinical_notes.models.case import CaseConfig, ClinicalVariables
from src.clinical_notes.models.investigation import (
    CaseSeed,
    Confidence,
    InvestigationPlan,
    InvestigatorReport,
    VariableAssignment,
)


@pytest.fixture
def seed():
    return CaseSeed(
        raw_variables={
            "Primary Site": "C34.1",
            "Histologic Type": "8070/3",
            "Grade": "2",
        },
        coding_system="NAACCR",
        difficulty="hard",
        case_type="chronic",
        intended_outcome="worsening",
    )


@pytest.fixture
def seed_with_demographics():
    return CaseSeed(
        raw_variables={"Primary Site": "C50.9", "Histologic Type": "8500/3"},
        coding_system="NAACCR",
        age=52,
        sex="F",
        difficulty="medium",
    )


@pytest.fixture
def mock_plan():
    return InvestigationPlan(
        variables=[
            VariableAssignment(
                variable_name="Primary Site",
                investigation_focus="Look up topography code C34.1",
                raw_value="C34.1",
                coding_system="NAACCR",
            ),
            VariableAssignment(
                variable_name="Histologic Type",
                investigation_focus="Look up histology/behavior code 8070/3",
                raw_value="8070/3",
                coding_system="NAACCR",
            ),
        ],
        suggested_age=65,
        suggested_sex="M",
    )


@pytest.fixture
def mock_reports():
    return [
        InvestigatorReport(
            variable_name="Primary Site",
            variable_value="Upper lobe of lung",
            associated_symptoms=["Persistent cough", "Dyspnea"],
            associated_comorbidities=["COPD"],
            confidence=Confidence.HIGH,
        ),
        InvestigatorReport(
            variable_name="Histologic Type",
            variable_value="Squamous cell carcinoma (8070/3)",
            associated_risk_factors=["Smoking"],
            clinical_staging="T3N1M0",
            confidence=Confidence.HIGH,
        ),
    ]


@pytest.fixture
def mock_config():
    return CaseConfig(
        case_id="placeholder",
        clinical_variables=ClinicalVariables(
            primary_condition="Squamous Cell Carcinoma of the Upper Lobe of the Lung",
            comorbidities=["COPD", "Hypertension"],
            age=65,
            sex="M",
            risk_factors=["40 pack-year smoking history"],
        ),
    )


@pytest.mark.asyncio
async def test_constructor_full_pipeline(seed, mock_plan, mock_reports, mock_config):
    agent = ConstructorAgent()

    with (
        patch(
            "src.clinical_notes.agents.constructor.generate_structured",
            new_callable=AsyncMock,
        ) as mock_gen,
        patch(
            "src.clinical_notes.agents.constructor.InvestigatorAgent",
        ) as mock_inv_cls,
    ):
        mock_gen.side_effect = [mock_plan, mock_config]
        mock_investigator = mock_inv_cls.return_value
        mock_investigator.run = AsyncMock(side_effect=mock_reports)

        result = await agent.run(seed)

    # Verify case_id is generated
    assert len(result.case_id) == 8

    # Verify seed constraints are enforced
    assert result.difficulty.value == "hard"
    assert result.case_type.value == "chronic"
    assert result.intended_outcome.value == "worsening"

    # Verify generate_structured called twice (plan + merge)
    assert mock_gen.call_count == 2

    # Verify investigators dispatched for each variable
    assert mock_investigator.run.call_count == 2


@pytest.mark.asyncio
async def test_constructor_uses_seed_demographics(
    seed_with_demographics, mock_plan, mock_reports, mock_config
):
    agent = ConstructorAgent()

    with (
        patch(
            "src.clinical_notes.agents.constructor.generate_structured",
            new_callable=AsyncMock,
        ) as mock_gen,
        patch(
            "src.clinical_notes.agents.constructor.InvestigatorAgent",
        ) as mock_inv_cls,
    ):
        mock_gen.side_effect = [mock_plan, mock_config]
        mock_investigator = mock_inv_cls.return_value
        mock_investigator.run = AsyncMock(side_effect=mock_reports)

        result = await agent.run(seed_with_demographics)

    # Seed demographics should override plan suggestions
    assert result.clinical_variables.age == 52
    assert result.clinical_variables.sex == "F"
