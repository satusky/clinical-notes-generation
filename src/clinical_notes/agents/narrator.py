from ..llm import generate
from ..models.case import CaseConfig
from ..prompts.narrator import NARRATOR_SYSTEM, narrator_user_prompt
from .base import BaseAgent


class NarratorAgent(BaseAgent):
    agent_name = "narrator"

    async def run(self, config: CaseConfig) -> str:
        """Generate a full narrative for the case. Returns the narrative string."""
        cv = config.clinical_variables
        user_prompt = narrator_user_prompt(
            primary_condition=cv.primary_condition,
            comorbidities=cv.comorbidities,
            age=cv.age,
            sex=cv.sex,
            risk_factors=cv.risk_factors,
            difficulty=config.difficulty.value,
            case_type=config.case_type.value,
            intended_outcome=config.intended_outcome.value,
        )
        return await generate(NARRATOR_SYSTEM, user_prompt, model=self.model)
