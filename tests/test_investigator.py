from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.agents.investigator import InvestigatorAgent
from src.clinical_notes.models.investigation import (
    Confidence,
    InvestigatorReport,
    KnowledgeSource,
    KnowledgeSourceType,
    VariableAssignment,
)


@pytest.fixture
def assignment():
    return VariableAssignment(
        variable_name="Primary Site",
        investigation_focus="Look up topography code C34.1 in the NAACCR coding manual",
        raw_value="C34.1",
        coding_system="NAACCR",
    )


@pytest.fixture
def mock_report():
    return InvestigatorReport(
        variable_name="Primary Site",
        variable_value="Upper lobe of lung",
        associated_symptoms=["Persistent cough", "Dyspnea"],
        associated_comorbidities=["COPD"],
        associated_risk_factors=["Smoking"],
        confidence=Confidence.HIGH,
    )


@pytest.mark.asyncio
async def test_investigator_without_sources(assignment, mock_report):
    agent = InvestigatorAgent()
    with patch(
        "src.clinical_notes.agents.investigator.generate_structured",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = mock_report
        result = await agent.run(assignment)

    assert result.variable_name == "Primary Site"
    assert result.variable_value == "Upper lobe of lung"
    assert result.confidence == Confidence.HIGH
    mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_investigator_with_sources(mock_report):
    assignment = VariableAssignment(
        variable_name="Histologic Type",
        investigation_focus="Look up histology/behavior code 8070/3",
        raw_value="8070/3",
        coding_system="NAACCR",
        relevant_sources=[0],
    )
    sources = [
        KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_FILE,
            location="/tmp/naaccr_coding_manual.txt",
        ),
    ]
    agent = InvestigatorAgent()
    with (
        patch(
            "src.clinical_notes.agents.investigator.generate_structured",
            new_callable=AsyncMock,
        ) as mock_gen,
        patch(
            "src.clinical_notes.agents.investigator.KnowledgeLoader",
        ) as mock_loader_cls,
    ):
        mock_loader = mock_loader_cls.return_value
        mock_loader.load = AsyncMock(return_value="NAACCR histology codes reference content")
        mock_gen.return_value = mock_report
        result = await agent.run(assignment, knowledge_sources=sources)

    assert result.variable_name == "Primary Site"
    mock_loader.load.assert_called_once_with(sources[0])
