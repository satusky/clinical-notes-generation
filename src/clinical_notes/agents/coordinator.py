import logging

from ..llm import generate_structured
from ..models.patient import MedicalHistorySummary
from ..models.timeline import Visit, VisitAssignment
from ..prompts.coordinator import PROMPT_VERSION, COORDINATOR_SYSTEM, coordinator_user_prompt
from .base import BaseAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    agent_name = "coordinator"
    prompt_version = PROMPT_VERSION

    async def run(
        self,
        primary_condition: str,
        visit: Visit,
        medical_history: MedicalHistorySummary,
    ) -> VisitAssignment:
        """Filter rich visit data into a diagnosis-free VisitAssignment for the Clinician."""
        user_prompt = coordinator_user_prompt(
            primary_condition=primary_condition,
            visit=visit.model_dump(),
            patient_age=medical_history.demographics.age,
            patient_sex=medical_history.demographics.sex,
            prior_visit_summaries=medical_history.prior_visit_summaries,
            known_conditions=medical_history.known_conditions,
            current_medications=medical_history.current_medications,
            allergies=medical_history.allergies,
            active_symptoms=[s.model_dump() for s in medical_history.active_symptoms],
            medication_courses=[m.model_dump() for m in medical_history.medication_courses],
            diagnostic_workups=[w.model_dump() for w in medical_history.diagnostic_workups],
            open_clinical_questions=[q.model_dump() for q in medical_history.open_clinical_questions],
            follow_up_tasks=[t.model_dump() for t in medical_history.follow_up_tasks],
        )
        self.maybe_log_prompts(logger, COORDINATOR_SYSTEM, user_prompt)
        return await generate_structured(
            COORDINATOR_SYSTEM, user_prompt, VisitAssignment, model=self.model
        )
