import logging

from .agents import ClinicianAgent, CoordinatorAgent, NarratorAgent, OrchestratorAgent, ScribeAgent
from .models.case import CaseConfig
from .models.patient import MedicalHistorySummary, PatientDemographics
from .models.timeline import Timeline

logger = logging.getLogger(__name__)


class CaseRunner:
    """Wires agents together to generate a complete clinical case."""

    def __init__(self):
        self.narrator = NarratorAgent()
        self.orchestrator = OrchestratorAgent()
        self.coordinator = CoordinatorAgent()
        self.clinician = ClinicianAgent()
        self.scribe = ScribeAgent()

    async def generate_case(self, config: CaseConfig) -> dict:
        """Run the full pipeline for a single case. Returns serializable dict."""
        cv = config.clinical_variables

        # Step 1: Narrator generates the full disease narrative
        logger.info("Case %s: Generating narrative...", config.case_id)
        narrative = await self.narrator.run(config)
        config.narrative = narrative

        # Step 2: Orchestrator creates the visit timeline with rich clinical data
        logger.info("Case %s: Creating timeline...", config.case_id)
        timeline = await self.orchestrator.run(config, narrative)

        # Step 3: Initialize medical history
        medical_history = MedicalHistorySummary(
            demographics=PatientDemographics(age=cv.age, sex=cv.sex),
            known_conditions=list(cv.comorbidities),
        )

        # Step 4: Process each visit sequentially
        notes = []
        for visit in timeline.visits:
            logger.info(
                "Case %s: Processing visit %d/%d...",
                config.case_id,
                visit.visit_number,
                len(timeline.visits),
            )

            # Coordinator filters rich visit data (has diagnosis access, strips it)
            assignment = await self.coordinator.run(
                primary_condition=cv.primary_condition,
                visit=visit,
                medical_history=medical_history,
            )

            # Clinician writes note (no diagnosis access)
            note = await self.clinician.run(assignment, medical_history)
            note.visit_number = visit.visit_number
            note.clinician_specialty = visit.clinician_specialty
            note.note_date = visit.visit_date

            # Store note on the visit and collect it
            visit.note = note.content
            notes.append(note)

            # Scribe updates medical history for subsequent visits
            medical_history = await self.scribe.run(medical_history, note, visit)

        logger.info("Case %s: Complete (%d visits)", config.case_id, len(notes))

        return _serialize_case(config, timeline, notes, medical_history)


def _serialize_case(
    config: CaseConfig,
    timeline: Timeline,
    notes: list,
    medical_history: MedicalHistorySummary,
) -> dict:
    return {
        "case_id": config.case_id,
        "clinical_variables": config.clinical_variables.model_dump(),
        "difficulty": config.difficulty.value,
        "case_type": config.case_type.value,
        "intended_outcome": config.intended_outcome.value,
        "narrative": config.narrative,
        "timeline": [v.model_dump() for v in timeline.visits],
        "notes": [n.model_dump() for n in notes],
        "final_medical_history": medical_history.model_dump(),
    }
