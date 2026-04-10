# Plan: Improve Longitudinal Case State Tracking for More Realistic, Consistent Notes

## Goal
Reduce visit-to-visit inconsistencies and improve realism by introducing structured longitudinal state that all note-generation agents can use safely (without breaking the diagnosis information barrier).

---

## Current Gaps in the Pipeline

Based on the current implementation (`case_runner -> orchestrator -> coordinator -> clinician -> scribe`):

1. **History is too coarse**
   - `MedicalHistorySummary` stores only broad lists (`known_conditions`, `current_medications`, `prior_visit_summaries`, `allergies`).
   - There is no explicit state for symptom trajectory, pending tests, treatment course timing, or unresolved problems.

2. **Medication continuity is weakly represented**
   - Medications are mostly string lists in visit/note/history.
   - No explicit start/stop dates, status (`active`, `completed`, `held`, `discontinued`), intended duration, indication, or reason for changes.

3. **Narrative continuity is mostly prompt-driven**
   - Orchestrator is instructed to maintain continuity, but there is no hard schema requiring carry-forward of open items.
   - Coordinator/Clinician receive narrative text, but not a structured "open loop" list to close in future visits.

4. **Specialty behavior is under-specified**
   - Specialty is passed as text, but the prompts do not strongly constrain specialty-specific lens, diagnostic scope, and documentation style.

5. **Uncertainty handling is implicit**
   - Inconclusive findings and confidence levels are not first-class fields.
   - Differential uncertainty exists in free text but is not tracked longitudinally.

6. **Validation checks are mostly structural**
   - Existing validation checks alignment/leakage/date ordering.
   - No automated checks for continuity of meds/symptoms/tests across visits.

---

## 1) Information that should be available to clinicians

Provide a diagnosis-free but structured **Clinician Context Packet** on each visit:

1. **Active symptom ledger (diagnosis-free)**
   - symptom, onset, severity, trend (`improving/stable/worsening`), last observed visit.

2. **Medication ledger**
   - medication name, dose/frequency (if known), status, indication (symptom/problem oriented), start date, planned end date, adherence notes, adverse effects.

3. **Diagnostic workup tracker**
   - tests with status (`ordered`, `pending`, `resulted`, `inconclusive`), key finding summary, next-step recommendation.

4. **Open clinical questions / unresolved issues**
   - e.g., "persistent cough etiology unresolved", "repeat imaging due in 6 weeks".

5. **Prior care actions and follow-up commitments**
   - what was recommended last visit and whether it was completed.

6. **Specialty-specific handoff notes**
   - concise, diagnosis-free context relevant to the current specialty.

> This keeps clinicians grounded in continuity without exposing the hidden ground-truth diagnosis.

---

## 2) Handling prescription treatment courses (start/finish/changes)

Adopt explicit medication lifecycle events instead of plain strings.

### Proposed medication event model
- `action`: `start | continue | adjust | hold | stop | complete`
- `medication`: name
- `dose` / `frequency` (optional)
- `indication`: symptom/problem-oriented reason
- `effective_date`
- `planned_duration`
- `planned_end_date` (if known)
- `stop_reason` (if stopped/completed)
- `response` and `side_effects`

### Pipeline behavior
1. **Orchestrator** seeds treatment plans with expected durations and intended checkpoints.
2. **Coordinator** includes active courses + upcoming milestones in assignment.
3. **Clinician** must reconcile medication plan changes in note A/P.
4. **Scribe** converts note content into lifecycle updates and recomputes active meds.
5. **Validator** checks lifecycle consistency (e.g., completed meds no longer appear active unless restarted).

---

## 3) Coordinator controls to preserve case narrative (overall + visit-specific)

Coordinator should enforce a structured continuity contract for each visit assignment.

### Required assignment sections
1. `visit_narrative_anchor`
   - one paragraph describing where this visit sits in the timeline (diagnosis-free).
2. `must_address_this_visit`
   - list of problems/tests/follow-ups that must be touched in this note.
3. `new_events_this_visit`
   - truly new symptoms/findings/events.
4. `carry_forward_items`
   - unresolved items from previous visits.
5. `what_changed_since_last_visit`
   - meds adjusted, symptom trend shifts, new test results.

### Coordinator quality rules
- Every unresolved item from prior visit must be either:
  - addressed this visit, or
  - explicitly deferred with rationale and target follow-up.
- Visit scenario and structured fields must agree (no contradictory actions/results).
- Assignment should include expected note intent by visit type (initial eval, follow-up, treatment check, post-procedure, etc.).

---

## 4) Better use of clinician specialty for realistic notes

Introduce specialty-specific prompt overlays + scoped authority.

### Specialty profile should define
- typical history/exam focus,
- typical tests/interventions ordered by that specialty,
- expected language/style,
- what is **inside** vs **outside** specialty scope,
- referral/escalation norms.

### Implementation pattern
- Keep base clinician prompt, then inject a specialty block (e.g., Pulmonology, Oncology, PCP, ED, Surgery, Radiology).
- Require explicit **scope statement** in note assessment:
  - what this clinician can conclude,
  - what requires another specialty.

This improves realism and reduces implausible cross-specialty overreach.

---

## 5) Incorporating clinician uncertainty

Track uncertainty as structured data and narrative language expectations.

### Add explicit uncertainty constructs
1. **Test result certainty**
   - `definitive | suggestive | inconclusive | conflicting`
2. **Assessment confidence**
   - per diagnosis considered: `low/medium/high` confidence
3. **Unresolved diagnostic questions**
   - explicit list with planned next steps.
4. **Scope uncertainty**
   - field noting when issue is beyond current specialty.

### Prompt expectations
- Encourage clinically realistic language: "findings are nonspecific", "cannot exclude", "recommend repeat imaging".
- Require contingency plans when uncertainty is high.

---

## Proposed Data Model Enhancements

### `models/patient.py`
Add structured longitudinal trackers, e.g.:
- `active_symptoms: list[SymptomState]`
- `medication_courses: list[MedicationCourse]`
- `diagnostic_workups: list[DiagnosticWorkup]`
- `open_clinical_questions: list[ClinicalQuestion]`
- `follow_up_tasks: list[FollowUpTask]`

### `models/timeline.py`
Extend `Visit`/`VisitAssignment` with:
- `continuity_focus` / `must_address_this_visit`
- `carry_forward_items`
- `medication_changes` (structured events)
- `test_result_certainty`
- `unresolved_questions`

### `models/note.py`
Add optional structured outputs for:
- `medication_actions`
- `diagnostic_uncertainty`
- `resolved_items` / `deferred_items`

---

## Validation Enhancements

Add longitudinal validators in `validation.py`:

1. **Medication continuity validator**
   - detects impossible transitions (stopped med later active without restart).
2. **Symptom trajectory validator**
   - checks trend plausibility and contradiction detection.
3. **Pending test closure validator**
   - ensures ordered tests eventually become resulted/inconclusive/deferred.
4. **Follow-up commitment validator**
   - ensures recommended follow-up appears in later timeline or explicitly missed.
5. **Specialty scope validator**
   - soft warnings for implausible actions by specialty.
6. **Uncertainty consistency validator**
   - high uncertainty should map to cautious plan and additional workup.

---

## Implementation Plan (PR-sized)

### PR 1 — Add state schema + minimally invasive prompt support
- Add new state models and fields (optional defaults to preserve compatibility).
- Update orchestrator/coordinator/clinician/scribe prompts to mention new fields.
- Keep existing fields for backward compatibility.

### PR 2 — Medication lifecycle + test/workup trackers
- Implement structured medication events and diagnostic workup statuses.
- Update scribe update logic to maintain active courses correctly.

### PR 3 — Coordinator continuity contract
- Add mandatory assignment sections (`must_address_this_visit`, `carry_forward_items`, etc.).
- Enforce in prompt and post-generation validation.

### PR 4 — Specialty overlays + uncertainty framework
- Add specialty profile library and prompt injection.
- Add uncertainty/confidence fields and note requirements.

### PR 5 — Longitudinal validators + QA fixtures
- Extend validators and tests for med/symptom/test continuity.
- Add fixture cases for common failure modes (med drop, unresolved pending tests, specialty overreach).

---

## Where to Change (Code Map)

- Models:
  - `src/clinical_notes/models/patient.py`
  - `src/clinical_notes/models/timeline.py`
  - `src/clinical_notes/models/note.py`
- Agent prompt contracts:
  - `src/clinical_notes/prompts/orchestrator.py`
  - `src/clinical_notes/prompts/coordinator.py`
  - `src/clinical_notes/prompts/clinician.py`
  - `src/clinical_notes/prompts/scribe.py`
- Agent wiring:
  - `src/clinical_notes/agents/coordinator.py`
  - `src/clinical_notes/agents/clinician.py`
  - `src/clinical_notes/agents/scribe.py`
- Runtime checks:
  - `src/clinical_notes/validation.py`
- Docs/output schema:
  - `AGENT_FRAMEWORK.md`
  - `src/clinical_notes/README.md`
- Tests:
  - `tests/test_models.py`
  - `tests/test_agents.py`
  - `tests/test_validation.py`
  - `tests/test_case_runner.py`

---

## Success Criteria

1. Fewer contradictions across visits (meds, symptoms, test follow-up).
2. Notes clearly reflect prior plan and current trajectory.
3. Specialty voice and scope look clinically plausible.
4. Uncertainty appears naturally and drives realistic follow-up decisions.
5. Validation catches continuity failures before final case output.
