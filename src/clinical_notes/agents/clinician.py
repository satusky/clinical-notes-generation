from ..llm import generate_structured
from ..models.note import ClinicalNote
from ..models.patient import MedicalHistorySummary
from ..models.timeline import VisitAssignment
from ..prompts.clinician import CLINICIAN_SYSTEM, clinician_user_prompt
from .base import BaseAgent


class ClinicianAgent(BaseAgent):
    agent_name = "clinician"

    async def run(
        self,
        assignment: VisitAssignment,
        medical_history: MedicalHistorySummary,
    ) -> ClinicalNote:
        """Write a clinical note from the visit assignment. No diagnosis access."""
        user_prompt = clinician_user_prompt(
            visit_number=assignment.visit_number,
            visit_date=assignment.visit_date,
            clinician_specialty=assignment.clinician_specialty,
            reason_for_visit=assignment.reason_for_visit,
            patient_age=assignment.patient_age,
            patient_sex=assignment.patient_sex,
            symptoms=assignment.symptoms,
            relevant_history=assignment.relevant_history,
            vitals=assignment.vitals,
            known_conditions=assignment.known_conditions or medical_history.known_conditions,
            current_medications=assignment.current_medications or medical_history.current_medications,
            prior_visit_summaries=assignment.prior_visit_summaries or medical_history.prior_visit_summaries,
            allergies=assignment.allergies or medical_history.allergies,
            visit_scenario=assignment.visit_scenario,
            examination_findings=assignment.examination_findings,
            tests_ordered=assignment.tests_ordered,
            test_results=assignment.test_results,
            treatments_administered=assignment.treatments_administered,
            patient_response=assignment.patient_response,
        )
        return await generate_structured(
            CLINICIAN_SYSTEM, user_prompt, ClinicalNote, model=self.model
        )
