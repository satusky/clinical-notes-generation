import json
import logging
from pathlib import Path

from ..knowledge import KnowledgeLoader
from ..llm import generate_structured, generate_with_tools

from ..models.investigation import (
    InvestigatorReport,
    KnowledgeSource,
    KnowledgeSourceType,
    VariableAssignment,
)
from ..prompts.investigator import (
    INVESTIGATOR_SYSTEM,
    investigator_system_prompt,
    investigator_tool_user_prompt,
    investigator_user_prompt,
)
from .base import BaseAgent

logger = logging.getLogger(__name__)

MAX_RESULT_CHARS = 50_000
MAX_SEARCH_RESULTS = 200


def _build_allowed_paths(
    knowledge_sources: list[KnowledgeSource],
    relevant_indices: list[int],
) -> set[str]:
    """Build set of allowed paths from relevant knowledge sources."""
    allowed = set()
    for idx in relevant_indices:
        if 0 <= idx < len(knowledge_sources):
            src = knowledge_sources[idx]
            if src.source_type in (KnowledgeSourceType.LOCAL_FILE, KnowledgeSourceType.LOCAL_DIRECTORY):
                allowed.add(str(Path(src.location).resolve()))
    return allowed


def _is_path_allowed(path: str, allowed_paths: set[str]) -> bool:
    """Check if a path is within the set of allowed paths."""
    resolved = str(Path(path).resolve())
    for allowed in allowed_paths:
        if resolved == allowed or resolved.startswith(allowed + "/"):
            return True
    return False


def _build_tool_schemas() -> list[dict]:
    """Build Anthropic tool schemas for the investigation tools."""
    return [
        {
            "name": "lookup_json_dict",
            "description": (
                "Look up a key in a JSON data dictionary file. "
                "Returns the value for the given key, or an error if not found."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the JSON file to look up",
                    },
                    "key": {
                        "type": "string",
                        "description": "The key to look up in the JSON dictionary",
                    },
                },
                "required": ["file_path", "key"],
            },
        },
        {
            "name": "search_files",
            "description": (
                "Search a directory recursively for files matching a glob pattern. "
                "Returns a list of matching file paths."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path to the directory to search",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match files (e.g., '*breast*', '*.json')",
                    },
                },
                "required": ["directory", "pattern"],
            },
        },
    ]


def _build_tool_executors(allowed_paths: set[str]) -> dict:
    """Build tool executor functions with path validation."""

    async def lookup_json_dict(file_path: str, key: str) -> str:
        if not _is_path_allowed(file_path, allowed_paths):
            return f"Error: path '{file_path}' is not in the allowed sources"
        path = Path(file_path)
        if not path.exists():
            return f"Error: file '{file_path}' does not exist"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return f"Error reading '{file_path}': {exc}"
        if key not in data:
            available = list(data.keys())[:20]
            return f"Key '{key}' not found. Available keys (first 20): {available}"
        result = json.dumps(data[key], indent=2)
        if len(result) > MAX_RESULT_CHARS:
            result = result[:MAX_RESULT_CHARS] + "\n... (truncated)"
        return result

    async def search_files(directory: str, pattern: str) -> str:
        if not _is_path_allowed(directory, allowed_paths):
            return f"Error: directory '{directory}' is not in the allowed sources"
        dir_path = Path(directory)
        if not dir_path.is_dir():
            return f"Error: '{directory}' is not a directory"
        matches = []
        for match in dir_path.rglob(pattern):
            matches.append(str(match))
            if len(matches) >= MAX_SEARCH_RESULTS:
                break
        if not matches:
            return f"No files matching '{pattern}' found in '{directory}'"
        result = "\n".join(matches)
        if len(matches) >= MAX_SEARCH_RESULTS:
            result += f"\n... (capped at {MAX_SEARCH_RESULTS} results)"
        return result

    return {
        "lookup_json_dict": lookup_json_dict,
        "search_files": search_files,
    }


class InvestigatorAgent(BaseAgent):
    agent_name = "investigator"

    async def run(
        self,
        assignment: VariableAssignment,
        knowledge_sources: list[KnowledgeSource] | None = None,
    ) -> InvestigatorReport:
        """Investigate a single clinical variable and return a structured report."""
        logger.info(
            "Investigating variable: %s (raw_value=%s)",
            assignment.variable_name,
            assignment.raw_value,
        )

        has_relevant_sources = bool(
            knowledge_sources and assignment.relevant_sources
        )

        # Use tool-based path when relevant sources are available
        if has_relevant_sources:
            return await self._run_with_tools(assignment, knowledge_sources)

        # Fallback: pre-load sources and use generate_structured
        return await self._run_structured(assignment, knowledge_sources)

    async def _run_with_tools(
        self,
        assignment: VariableAssignment,
        knowledge_sources: list[KnowledgeSource],
    ) -> InvestigatorReport:
        """Tool-use path: let the LLM query sources via tools."""
        allowed_paths = _build_allowed_paths(knowledge_sources, assignment.relevant_sources)
        tools = _build_tool_schemas()
        executors = _build_tool_executors(allowed_paths)

        system = investigator_system_prompt(
            coding_system=assignment.coding_system,
            use_tools=True,
        )
        user = investigator_tool_user_prompt(
            assignment, knowledge_sources, assignment.relevant_sources
        )

        report = await generate_with_tools(
            system, user, tools, executors, InvestigatorReport, model=self.model
        )
        logger.info(
            "Investigation complete (tools): %s -> value=%s, confidence=%s",
            assignment.variable_name,
            report.variable_value,
            report.confidence,
        )
        return report

    async def _run_structured(
        self,
        assignment: VariableAssignment,
        knowledge_sources: list[KnowledgeSource] | None = None,
    ) -> InvestigatorReport:
        """Fallback path: pre-load sources and use generate_structured."""
        source_content = None

        if knowledge_sources and assignment.relevant_sources:
            loader = KnowledgeLoader()
            parts = []
            for idx in assignment.relevant_sources:
                if 0 <= idx < len(knowledge_sources):
                    content = await loader.load(knowledge_sources[idx])
                    if content:
                        parts.append(content)
            if parts:
                source_content = "\n\n".join(parts)
                logger.debug(
                    "Knowledge loaded for %s: %d sources, %d chars",
                    assignment.variable_name,
                    len(parts),
                    len(source_content),
                )

        user_prompt = investigator_user_prompt(assignment, source_content)
        report = await generate_structured(
            INVESTIGATOR_SYSTEM, user_prompt, InvestigatorReport, model=self.model
        )
        logger.info(
            "Investigation complete: %s -> value=%s, confidence=%s",
            assignment.variable_name,
            report.variable_value,
            report.confidence,
        )
        return report
