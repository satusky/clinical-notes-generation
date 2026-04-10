# Prompt Updates Changelog

Branch: `prompt-updates`

This changelog summarizes the PR-sized implementation chunks completed for longitudinal state tracking, specialty realism, and consistency validation in the note generation pipeline.

## PR1 — Structured Longitudinal State in Medical History
**Commit:** `73dede0`

### What changed
- Added structured longitudinal models in `models/patient.py`:
  - `SymptomState`
  - `MedicationCourse`
  - `DiagnosticWorkup`
  - `ClinicalQuestion`
  - `FollowUpTask`
- Extended `MedicalHistorySummary` with:
  - `active_symptoms`
  - `medication_courses`
  - `diagnostic_workups`
  - `open_clinical_questions`
  - `follow_up_tasks`
- Passed these trackers into coordinator prompt context.
- Updated scribe prompt guidance to preserve structured state.

## PR2 — Medication Lifecycle + Workup Tracking
**Commit:** `345afb8`

### What changed
- Added timeline/assignment structured fields in `models/timeline.py`:
  - `MedicationChange`
  - `DiagnosticWorkupUpdate`
- Added note structured fields in `models/note.py`:
  - `medication_actions`
  - `workup_plan_actions`
- Updated orchestrator/coordinator/clinician prompts and clinician agent wiring to include these fields.

## PR3 — Coordinator Continuity Contract
**Commit:** `60567df`

### What changed
- Added continuity contract fields to `Visit` and `VisitAssignment`:
  - `visit_narrative_anchor`
  - `must_address_this_visit`
  - `new_events_this_visit`
  - `carry_forward_items`
  - `what_changed_since_last_visit`
- Updated prompts and clinician wiring to consume continuity fields.

## PR4 — Specialty Overlays + Structured Uncertainty
**Commit:** `783a94e`

### What changed
- Added specialty guidance profile library:
  - `src/clinical_notes/prompts/specialty_profiles.py`
- Extended uncertainty/scope modeling:
  - Timeline/assignment: `test_result_certainty`, `unresolved_questions`
  - Note model: `diagnostic_uncertainty`, `specialty_scope_statement`
- Updated clinician prompt to inject specialty-specific behavior and require scope/uncertainty handling.
- Added tests for specialty profile behavior.

## PR5 — Longitudinal Validators + QA Coverage
**Commit:** `35b5f49`

### What changed
- Extended `validate_final_case` with new checks:
  - medication continuity (`stop/complete` consistency)
  - pending workup closure
  - follow-up commitment carry-through
  - specialty scope presence with uncertainty
  - uncertainty-to-plan consistency
- Added targeted tests in `tests/test_validation.py`.

## Documentation Updates

### Updated
- `AGENT_FRAMEWORK.md`
  - Added continuity contract, structured state, specialty overlays, uncertainty handling, and expanded validator scope.
- `src/clinical_notes/README.md`
  - Added schema documentation for new `Visit`, `ClinicalNote`, and `MedicalHistorySummary` fields.

## Test status
- Current suite passes after changes: **93 passed**.
