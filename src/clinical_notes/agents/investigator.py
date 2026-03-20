import logging

from ..knowledge import KnowledgeLoader
from ..llm import generate_structured
from ..models.investigation import (
    InvestigatorReport,
    KnowledgeSource,
    VariableAssignment,
)
from ..prompts.investigator import INVESTIGATOR_SYSTEM, investigator_user_prompt
from .base import BaseAgent

logger = logging.getLogger(__name__)


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
