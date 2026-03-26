import json
from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.agents.investigator import (
    InvestigatorAgent,
    _build_allowed_paths,
    _build_tool_executors,
    _is_path_allowed,
)
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


# --- Tool executor tests ---


@pytest.fixture
def tmp_json(tmp_path):
    data = {"400": {"name": "Primary Site", "description": "Topography code"}, "522": "Histologic Type"}
    fp = tmp_path / "naaccr_dict.json"
    fp.write_text(json.dumps(data))
    return fp


@pytest.fixture
def tmp_dir_tree(tmp_path):
    """Create a directory tree for search_files tests."""
    (tmp_path / "histology").mkdir()
    (tmp_path / "histology" / "breast_codes.json").write_text("{}")
    (tmp_path / "histology" / "lung_codes.json").write_text("{}")
    (tmp_path / "histology" / "sub").mkdir()
    (tmp_path / "histology" / "sub" / "breast_staging.json").write_text("{}")
    (tmp_path / "staging" / "tnm.json").parents[0].mkdir(parents=True, exist_ok=True)
    (tmp_path / "staging" / "tnm.json").write_text("{}")
    return tmp_path


@pytest.mark.asyncio
async def test_lookup_json_dict_valid_key(tmp_json):
    allowed = {str(tmp_json.resolve())}
    executors = _build_tool_executors(allowed)
    result = await executors["lookup_json_dict"](file_path=str(tmp_json), key="400")
    parsed = json.loads(result)
    assert parsed["name"] == "Primary Site"


@pytest.mark.asyncio
async def test_lookup_json_dict_missing_key(tmp_json):
    allowed = {str(tmp_json.resolve())}
    executors = _build_tool_executors(allowed)
    result = await executors["lookup_json_dict"](file_path=str(tmp_json), key="999")
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_lookup_json_dict_invalid_path(tmp_json):
    allowed = {"/some/other/path"}
    executors = _build_tool_executors(allowed)
    result = await executors["lookup_json_dict"](file_path=str(tmp_json), key="400")
    assert "not in the allowed sources" in result


@pytest.mark.asyncio
async def test_search_files_finds_matches(tmp_dir_tree):
    histology_dir = str(tmp_dir_tree / "histology")
    allowed = {str((tmp_dir_tree / "histology").resolve())}
    executors = _build_tool_executors(allowed)
    result = await executors["search_files"](directory=histology_dir, pattern="*.json")
    assert "breast_codes.json" in result
    assert "lung_codes.json" in result


@pytest.mark.asyncio
async def test_search_files_recursive(tmp_dir_tree):
    histology_dir = str(tmp_dir_tree / "histology")
    allowed = {str((tmp_dir_tree / "histology").resolve())}
    executors = _build_tool_executors(allowed)
    result = await executors["search_files"](directory=histology_dir, pattern="*breast*")
    assert "breast_codes.json" in result
    assert "breast_staging.json" in result


@pytest.mark.asyncio
async def test_search_files_invalid_directory(tmp_dir_tree):
    allowed = {"/some/other/path"}
    executors = _build_tool_executors(allowed)
    result = await executors["search_files"](
        directory=str(tmp_dir_tree / "histology"), pattern="*.json"
    )
    assert "not in the allowed sources" in result


# --- InvestigatorAgent tests ---


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
async def test_investigator_with_sources_non_anthropic(mock_report):
    """Non-Anthropic model now uses generate_with_tools when sources are available."""
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
    with patch(
        "src.clinical_notes.agents.investigator.generate_with_tools",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = mock_report
        result = await agent.run(assignment, knowledge_sources=sources)

    assert result.variable_name == "Primary Site"
    mock_gen.assert_called_once()
    # Verify tools were passed
    call_args = mock_gen.call_args
    tools = call_args.args[2] if len(call_args.args) > 2 else call_args.kwargs.get("tools", [])
    tool_names = {t["name"] for t in tools} if tools else set()
    assert "lookup_json_dict" in tool_names


@pytest.mark.asyncio
async def test_investigator_with_tools(mock_report):
    """Anthropic model with sources uses generate_with_tools."""
    assignment = VariableAssignment(
        variable_name="Histologic Type",
        investigation_focus="Look up histology/behavior code 8070/3",
        raw_value="8070/3",
        coding_system="NAACCR",
        relevant_sources=[0],
        raw_variables={"400": "C34.1", "522": "8070/3"},
    )
    sources = [
        KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_FILE,
            location="/tmp/naaccr_dict.json",
            description="NAACCR data dictionary",
        ),
    ]
    agent = InvestigatorAgent()
    with patch(
        "src.clinical_notes.agents.investigator.generate_with_tools",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = mock_report
        result = await agent.run(assignment, knowledge_sources=sources)

    assert result.variable_name == "Primary Site"
    mock_gen.assert_called_once()

    # Verify tools and executors were passed
    call_kwargs = mock_gen.call_args
    args = call_kwargs.args if call_kwargs.args else ()
    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}

    # get the tools argument (positional arg 2 or kwarg)
    tools = kwargs.get("tools") or args[2]
    tool_names = {t["name"] for t in tools}
    assert "lookup_json_dict" in tool_names
    assert "search_files" in tool_names

    # Verify NAACCR instructions in system prompt
    system_prompt = kwargs.get("system_prompt") or args[0]
    assert "NAACCR" in system_prompt


@pytest.mark.asyncio
async def test_investigator_fallback_no_tools(assignment, mock_report):
    """Without relevant sources, always falls back to generate_structured."""
    agent = InvestigatorAgent()
    with patch(
        "src.clinical_notes.agents.investigator.generate_structured",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = mock_report
        result = await agent.run(assignment)

    assert result.variable_value == "Upper lobe of lung"
    mock_gen.assert_called_once()


# --- Helper function tests ---


def test_build_allowed_paths():
    sources = [
        KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_FILE, location="/tmp/dict.json"
        ),
        KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_DIRECTORY, location="/tmp/refs/"
        ),
        KnowledgeSource(
            source_type=KnowledgeSourceType.WEB_URL, location="https://example.com"
        ),
    ]
    allowed = _build_allowed_paths(sources, [0, 1, 2])
    # Web URLs should not be in allowed paths
    assert any("dict.json" in p for p in allowed)
    assert any("refs" in p for p in allowed)
    assert not any("example.com" in p for p in allowed)


def test_is_path_allowed(tmp_path):
    allowed = {str(tmp_path.resolve())}
    assert _is_path_allowed(str(tmp_path / "subdir" / "file.json"), allowed)
    assert _is_path_allowed(str(tmp_path), allowed)
    assert not _is_path_allowed("/etc/passwd", allowed)
