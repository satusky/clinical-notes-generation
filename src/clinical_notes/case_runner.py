import logging
from datetime import datetime, timezone
from time import perf_counter

from .agents import ClinicianAgent, CoordinatorAgent, NarratorAgent, OrchestratorAgent, ScribeAgent
from .config import settings
from .io import remove_partial, save_partial_case
from .models.case import CaseConfig
from .models.patient import MedicalHistorySummary, PatientDemographics
from .models.timeline import Timeline
from .validation import (
    enforce_validation,
    validate_assignment_no_diagnosis,
    validate_final_case,
    validate_note_alignment,
)

logger = logging.getLogger(__name__)


class CaseRunner:
    """Wires agents together to generate a complete clinical case."""

    def __init__(self):
        self.narrator = NarratorAgent()
        self.orchestrator = OrchestratorAgent()
        self.coordinator = CoordinatorAgent()
        self.clinician = ClinicianAgent()
        self.scribe = ScribeAgent()

    async def generate_case(self, config: CaseConfig, output_dir: str | None = None) -> dict:
        """Run the full pipeline for a single case. Returns serializable dict."""
        cv = config.clinical_variables

        case_start = perf_counter()

        # Step 1: Narrator generates the full disease narrative
        logger.info("Case %s: Generating narrative...", config.case_id)
        step_start = perf_counter()
        narrative = await self.narrator.run(config)
        logger.info(
            "Case %s: Narrative complete in %.2fs",
            config.case_id,
            perf_counter() - step_start,
        )
        config.narrative = narrative

        # Step 2: Orchestrator creates the visit timeline with rich clinical data
        logger.info("Case %s: Creating timeline...", config.case_id)
        step_start = perf_counter()
        timeline = await self.orchestrator.run(config, narrative)
        logger.info(
            "Case %s: Timeline complete in %.2fs (%d visits)",
            config.case_id,
            perf_counter() - step_start,
            len(timeline.visits),
        )

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

            try:
                # Coordinator filters rich visit data (has diagnosis access, strips it)
                step_start = perf_counter()
                assignment = await self.coordinator.run(
                    primary_condition=cv.primary_condition,
                    visit=visit,
                    medical_history=medical_history,
                )
                logger.info(
                    "Case %s visit %d: Coordinator complete in %.2fs",
                    config.case_id,
                    visit.visit_number,
                    perf_counter() - step_start,
                )

                self._enforce_issues(
                    validate_assignment_no_diagnosis(cv.primary_condition, assignment),
                    f"Case {config.case_id} visit {visit.visit_number}: assignment validation",
                )

                # Clinician writes note (no diagnosis access)
                step_start = perf_counter()
                note = await self.clinician.run(assignment, medical_history)
                logger.info(
                    "Case %s visit %d: Clinician complete in %.2fs",
                    config.case_id,
                    visit.visit_number,
                    perf_counter() - step_start,
                )
                note.visit_number = visit.visit_number
                note.clinician_specialty = visit.clinician_specialty
                note.note_date = visit.visit_date

                self._enforce_issues(
                    validate_note_alignment(visit, note),
                    f"Case {config.case_id} visit {visit.visit_number}: note alignment validation",
                )

                # Store note on the visit and collect it
                visit.note = note.content
                notes.append(note)

                # Scribe updates medical history for subsequent visits
                step_start = perf_counter()
                medical_history = await self.scribe.run(medical_history, note, visit)
                logger.info(
                    "Case %s visit %d: Scribe complete in %.2fs",
                    config.case_id,
                    visit.visit_number,
                    perf_counter() - step_start,
                )
            except Exception:
                logger.error(
                    "Case %s: Failed on visit %d/%d. Partial progress saved.",
                    config.case_id,
                    visit.visit_number,
                    len(timeline.visits),
                )
                raise

            # Save progress after each successful visit
            self._save_progress(config, timeline, notes, medical_history, output_dir)

        # All visits complete — remove partial file
        remove_partial(config.case_id, output_dir)

        logger.info(
            "Case %s: Complete (%d visits) in %.2fs",
            config.case_id,
            len(notes),
            perf_counter() - case_start,
        )

        case = _serialize_case(config, timeline, notes, medical_history)
        self._enforce_issues(
            validate_final_case(case),
            f"Case {config.case_id}: final case validation",
        )
        case["generation_metadata"] = self._generation_metadata()
        return case

    def _save_progress(
        self,
        config: CaseConfig,
        timeline: Timeline,
        notes: list,
        medical_history: MedicalHistorySummary,
        output_dir: str | None,
    ) -> None:
        """Write a partial case JSON after each successful visit."""
        case = _serialize_case(config, timeline, notes, medical_history)
        save_partial_case(case, output_dir)

    def _enforce_issues(self, issues: list[str], context: str) -> None:
        enforce_validation(
            issues,
            mode=settings.validation_mode,
            context=context,
            logger=logger,
        )

    def _generation_metadata(self) -> dict:
        generated_at = datetime.now(timezone.utc).isoformat()
        return {
            "generated_at": generated_at,
            "agents": {
                "narrator": {
                    "model": self.narrator.model,
                    "prompt_version": self.narrator.prompt_version,
                },
                "orchestrator": {
                    "model": self.orchestrator.model,
                    "prompt_version": self.orchestrator.prompt_version,
                },
                "coordinator": {
                    "model": self.coordinator.model,
                    "prompt_version": self.coordinator.prompt_version,
                },
                "clinician": {
                    "model": self.clinician.model,
                    "prompt_version": self.clinician.prompt_version,
                },
                "scribe": {
                    "model": self.scribe.model,
                    "prompt_version": self.scribe.prompt_version,
                },
            },
        }


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
