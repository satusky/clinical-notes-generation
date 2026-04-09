import logging

from ..llm import generate_structured
from ..models.note import ClinicalNote
from ..models.patient import MedicalHistorySummary
from ..models.timeline import Visit
from ..prompts.scribe import PROMPT_VERSION, SCRIBE_SYSTEM, scribe_user_prompt
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ScribeAgent(BaseAgent):
    agent_name = "scribe"
    prompt_version = PROMPT_VERSION

    async def run(
        self,
        medical_history: MedicalHistorySummary,
        note: ClinicalNote,
        visit: Visit,
    ) -> MedicalHistorySummary:
        """Update the medical history summary based on a completed visit."""
        user_prompt = scribe_user_prompt(
            current_history=medical_history.model_dump(),
            clinical_note=note.model_dump(),
            visit_date=visit.visit_date,
            clinician_specialty=visit.clinician_specialty,
            reason_for_visit=visit.reason_for_visit,
        )
        self.maybe_log_prompts(logger, SCRIBE_SYSTEM, user_prompt)
        return await generate_structured(
            SCRIBE_SYSTEM, user_prompt, MedicalHistorySummary, model=self.model
        )
