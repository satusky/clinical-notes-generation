from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.case_builder import CaseBuilder
from src.clinical_notes.models.case import (
    CaseConfig,
    CaseOutcome,
    CaseType,
    ClinicalVariables,
    Difficulty,
)
from src.clinical_notes.models.investigation import CaseSeed


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
def mock_config():
    return CaseConfig(
        case_id="abc12345",
        clinical_variables=ClinicalVariables(
            primary_condition="Squamous Cell Carcinoma of the Upper Lobe of the Lung",
            comorbidities=["COPD", "Hypertension"],
            age=67,
            sex="M",
            risk_factors=["40 pack-year smoking history", "Occupational exposure"],
        ),
        difficulty=Difficulty.HARD,
        case_type=CaseType.CHRONIC,
        intended_outcome=CaseOutcome.WORSENING,
    )


@pytest.mark.asyncio
async def test_case_builder_end_to_end(seed, mock_config):
    """CaseBuilder produces a CaseConfig from a CaseSeed."""
    builder = CaseBuilder()

    with patch.object(
        builder.constructor, "run", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = mock_config
        result = await builder.build_case(seed)

    assert isinstance(result, CaseConfig)
    assert result.case_id == "abc12345"
    assert "Squamous Cell Carcinoma" in result.clinical_variables.primary_condition
    assert result.difficulty == Difficulty.HARD
    mock_run.assert_called_once_with(seed)


@pytest.mark.asyncio
async def test_case_builder_output_compatible_with_case_runner(seed, mock_config):
    """CaseBuilder output can be passed to CaseRunner.generate_case()."""
    builder = CaseBuilder()

    with patch.object(
        builder.constructor, "run", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = mock_config
        config = await builder.build_case(seed)

    # Verify the config has all fields CaseRunner needs
    assert config.case_id
    assert config.clinical_variables.primary_condition
    assert config.clinical_variables.age >= 0
    assert config.clinical_variables.sex in ("M", "F")
    assert isinstance(config.difficulty, Difficulty)
    assert isinstance(config.case_type, CaseType)
    assert isinstance(config.intended_outcome, CaseOutcome)
