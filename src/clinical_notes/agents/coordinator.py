from ..llm import generate_structured
from ..models.patient import MedicalHistorySummary
from ..models.timeline import Visit, VisitAssignment
from ..prompts.coordinator import COORDINATOR_SYSTEM, coordinator_user_prompt
from .base import BaseAgent


class CoordinatorAgent(BaseAgent):
    agent_name = "coordinator"

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
        )
        return await generate_structured(
            COORDINATOR_SYSTEM, user_prompt, VisitAssignment, model=self.model
        )
