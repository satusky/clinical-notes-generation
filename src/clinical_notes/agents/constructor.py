import asyncio
import logging
import uuid

from ..llm import generate_structured
from ..models.case import CaseConfig, CaseOutcome, CaseType, Difficulty
from ..models.investigation import CaseSeed, InvestigationPlan, InvestigatorReport
from ..prompts.constructor import (
    CONSTRUCTOR_MERGE_SYSTEM,
    CONSTRUCTOR_PLAN_SYSTEM,
    constructor_merge_prompt,
    constructor_plan_prompt,
)
from .base import BaseAgent
from .investigator import InvestigatorAgent

logger = logging.getLogger(__name__)


class ConstructorAgent(BaseAgent):
    agent_name = "constructor"

    async def run(self, seed: CaseSeed) -> CaseConfig:
        """Decompose a condition, investigate variables, and merge into a CaseConfig."""
        # Step 1: Plan — decompose condition into variables
        logger.info(
            "Plan phase start: %d raw variables",
            len(seed.raw_variables) if seed.raw_variables else 0,
        )
        plan_prompt = constructor_plan_prompt(seed)
        plan = await generate_structured(
            CONSTRUCTOR_PLAN_SYSTEM, plan_prompt, InvestigationPlan, model=self.model
        )
        logger.info(
            "Plan received: %d variables, suggested demographics: age=%s sex=%s",
            len(plan.variables),
            plan.suggested_age,
            plan.suggested_sex,
        )

        # Inject raw_variables into each assignment for cross-reference
        for var in plan.variables:
            var.raw_variables = seed.raw_variables

        # Step 2: Investigate — fan out investigators concurrently
        investigator = InvestigatorAgent()
        semaphore = asyncio.Semaphore(5)
        total = len(plan.variables)
        completed = 0

        async def _investigate(assignment):
            nonlocal completed
            async with semaphore:
                report = await investigator.run(
                    assignment,
                    knowledge_sources=seed.knowledge_sources or None,
                )
                completed += 1
                logger.info(
                    "Investigation %d/%d complete: %s (confidence=%s)",
                    completed,
                    total,
                    assignment.variable_name,
                    report.confidence,
                )
                return report

        reports: list[InvestigatorReport] = await asyncio.gather(
            *[_investigate(var) for var in plan.variables]
        )

        # Step 3: Merge — synthesize reports into a CaseConfig
        logger.info("Merge phase start: %d reports", len(reports))
        merge_prompt = constructor_merge_prompt(seed, plan, reports)
        config = await generate_structured(
            CONSTRUCTOR_MERGE_SYSTEM, merge_prompt, CaseConfig, model=self.model
        )

        # Set case_id and ensure seed constraints are respected
        config.case_id = str(uuid.uuid4())[:8]
        logger.info("Case constructed: case_id=%s", config.case_id)
        config.difficulty = Difficulty(seed.difficulty)
        config.case_type = CaseType(seed.case_type)
        config.intended_outcome = CaseOutcome(seed.intended_outcome)

        # Use seed demographics if provided, otherwise use plan suggestions
        if seed.age is not None:
            config.clinical_variables.age = seed.age
        if seed.sex is not None:
            config.clinical_variables.sex = seed.sex

        return config
