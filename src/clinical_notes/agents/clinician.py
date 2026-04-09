import logging

from ..llm import generate_structured
from ..models.note import ClinicalNote
from ..models.patient import MedicalHistorySummary
from ..models.timeline import VisitAssignment
from ..prompts.clinician import PROMPT_VERSION, CLINICIAN_SYSTEM, clinician_user_prompt
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ClinicianAgent(BaseAgent):
    agent_name = "clinician"
    prompt_version = PROMPT_VERSION

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
            visit_narrative_anchor=assignment.visit_narrative_anchor,
            must_address_this_visit=assignment.must_address_this_visit,
            new_events_this_visit=assignment.new_events_this_visit,
            carry_forward_items=assignment.carry_forward_items,
            what_changed_since_last_visit=assignment.what_changed_since_last_visit,
            medication_changes=[m.model_dump() for m in assignment.medication_changes],
            diagnostic_workup_updates=[w.model_dump() for w in assignment.diagnostic_workup_updates],
        )
        self.maybe_log_prompts(logger, CLINICIAN_SYSTEM, user_prompt)
        return await generate_structured(
            CLINICIAN_SYSTEM, user_prompt, ClinicalNote, model=self.model
        )
