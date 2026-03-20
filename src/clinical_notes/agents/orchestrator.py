from ..llm import generate_structured
from ..models.case import CaseConfig
from ..models.timeline import Timeline
from ..prompts.orchestrator import ORCHESTRATOR_SYSTEM, orchestrator_user_prompt
from .base import BaseAgent


class _TimelineVisits(Timeline):
    """Internal model — we need case_id set after parsing."""

    pass


class OrchestratorAgent(BaseAgent):
    agent_name = "orchestrator"

    async def run(self, config: CaseConfig, narrative: str) -> Timeline:
        """Generate a visit timeline with rich clinical data from the narrative."""
        cv = config.clinical_variables
        user_prompt = orchestrator_user_prompt(
            narrative=narrative,
            primary_condition=cv.primary_condition,
            age=cv.age,
            sex=cv.sex,
            difficulty=config.difficulty.value,
            comorbidities=cv.comorbidities,
            risk_factors=cv.risk_factors,
            case_type=config.case_type.value,
            intended_outcome=config.intended_outcome.value,
        )
        timeline = await generate_structured(
            ORCHESTRATOR_SYSTEM, user_prompt, Timeline, model=self.model
        )
        timeline.case_id = config.case_id
        return timeline
