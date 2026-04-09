# `clinical_notes` — Output Reference

This document describes the structure of the outputs produced by the pipeline.

## Output files

The pipeline writes to the configured output directory (default `output/`):

| File | Format | Description |
|------|--------|-------------|
| `<case_id>.json` | JSON | Complete case record |
| `notes.jsonl` | JSONL | One note per line across all cases, for ML pipelines |
| `<case_id>.partial.json` | JSON | In-progress case saved after each visit; removed on completion |

## Case JSON (`<case_id>.json`)

The complete case record produced by `CaseRunner.generate_case()`.

```json
{
  "case_id": "a1b2c3d4",
  "clinical_variables": {
    "primary_condition": "Non-Small Cell Lung Cancer",
    "comorbidities": ["COPD", "hypertension"],
    "age": 67,
    "sex": "M",
    "risk_factors": ["40 pack-year smoking history"]
  },
  "difficulty": "hard",
  "case_type": "chronic",
  "intended_outcome": "worsening",
  "narrative": "The patient, a 67-year-old male with a history of ...",
  "timeline": [ "..." ],
  "notes": [ "..." ],
  "final_medical_history": { "..." },
  "generation_metadata": {
    "generated_at": "2026-04-09T11:30:00+00:00",
    "agents": {
      "narrator": {"model": "anthropic/claude-sonnet-4-20250514", "prompt_version": "2026-04-09.1"},
      "orchestrator": {"model": "anthropic/claude-sonnet-4-20250514", "prompt_version": "2026-04-09.1"},
      "coordinator": {"model": "anthropic/claude-sonnet-4-20250514", "prompt_version": "2026-04-09.1"},
      "clinician": {"model": "anthropic/claude-sonnet-4-20250514", "prompt_version": "2026-04-09.1"},
      "scribe": {"model": "anthropic/claude-sonnet-4-20250514", "prompt_version": "2026-04-09.1"}
    }
  }
}
```

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Unique identifier for the case |
| `clinical_variables` | object | The clinical parameters that define the case (see below) |
| `difficulty` | string | Diagnostic difficulty: `easy`, `medium`, or `hard` |
| `case_type` | string | `acute` or `chronic` |
| `intended_outcome` | string | `resolved`, `improving`, `worsening`, or `undiagnosed` |
| `narrative` | string | Full disease progression narrative written by the Narrator |
| `timeline` | array | Ordered list of Visit objects (see below) |
| `notes` | array | Ordered list of ClinicalNote objects (see below) |
| `final_medical_history` | object | Patient's medical history after all visits (see below) |
| `generation_metadata` | object | Generation trace metadata including timestamp, model, and prompt version per agent |

### `clinical_variables`

| Field | Type | Description |
|-------|------|-------------|
| `primary_condition` | string | The underlying diagnosis |
| `comorbidities` | string[] | Co-existing conditions |
| `age` | int | Patient age (0–120) |
| `sex` | string | `M` or `F` |
| `risk_factors` | string[] | Relevant risk factors |

### `timeline[n]` — Visit

Each entry represents one clinical visit. Contains both the ground-truth clinical state (used internally) and the generated note.

| Field | Type | Description |
|-------|------|-------------|
| `visit_number` | int | 1-indexed visit sequence number |
| `visit_date` | string | Date of visit (YYYY-MM-DD) |
| `clinician_specialty` | string | Specialty assigned to the visit |
| `reason_for_visit` | string | Chief complaint or reason |
| `is_related_to_main_illness` | bool | Whether the visit relates to the primary condition |
| `note` | string\|null | The clinical note text (populated after the Clinician runs) |
| `patient_age` | int | Patient age at time of visit |
| `patient_sex` | string | Patient sex |
| `symptoms` | string[] | Presenting symptoms |
| `vitals` | object | Vitals at presentation (e.g. `{"BP": "130/85", "HR": "92"}`) |
| `relevant_history` | string[] | History items relevant to this visit |
| `known_conditions` | string[] | Conditions known at time of visit |
| `current_medications` | string[] | Active medications |
| `allergies` | string[] | Known allergies |
| `visit_scenario` | string | Full encounter narrative (contains diagnosis context) |
| `examination_findings` | string[] | Physical exam findings |
| `tests_ordered` | string[] | Labs/imaging ordered |
| `test_results` | string[] | Results available at this visit |
| `treatments_administered` | string[] | Treatments given during visit |
| `patient_response` | string | Response to prior treatments |
| `visit_narrative_anchor` | string | Diagnosis-free timeline anchor for this visit |
| `must_address_this_visit` | string[] | High-priority items expected to be addressed in this encounter |
| `new_events_this_visit` | string[] | New symptoms/findings/events introduced at this visit |
| `carry_forward_items` | string[] | Unresolved items carried forward from prior visits |
| `what_changed_since_last_visit` | string[] | Explicit transitions since previous visit |
| `test_result_certainty` | object | Map of test name → certainty (`definitive`, `suggestive`, `inconclusive`, `conflicting`) |
| `unresolved_questions` | string[] | Open diagnostic/management questions after this visit |
| `medication_changes` | object[] | Structured medication lifecycle events (`start/continue/adjust/hold/stop/complete`) |
| `diagnostic_workup_updates` | object[] | Structured workup status updates (`ordered/pending/resulted/inconclusive`) |
| `disease_progression_notes` | string | Internal disease tracking (never shown to Clinician) |

### `notes[n]` — ClinicalNote

Each entry is a clinical note written by the Clinician agent, who does not know the underlying diagnosis.

| Field | Type | Description |
|-------|------|-------------|
| `visit_number` | int | Corresponding visit number |
| `clinician_specialty` | string | Specialty of the note author |
| `note_date` | string | Date the note was written |
| `content` | string | Free-text clinical note |
| `symptoms_reported` | string[] | Symptoms documented in the note |
| `vitals` | object | Vitals recorded in the note |
| `tests_ordered` | string[] | Tests ordered by the clinician |
| `diagnoses_considered` | string[] | Differential diagnoses the clinician considered |
| `medications` | string[] | Medications prescribed or continued |
| `follow_up_recommendations` | string[] | Recommended follow-up actions |
| `medication_actions` | object[] | Structured medication plan actions captured in the note |
| `workup_plan_actions` | object[] | Structured workup/diagnostic plan actions captured in the note |
| `diagnostic_uncertainty` | object[] | Differential uncertainty with confidence and rationale (`low/medium/high`) |
| `specialty_scope_statement` | string | Explicit statement of specialty scope boundaries/referral need |

### `final_medical_history`

The cumulative patient record after all visits, maintained by the Scribe agent.

| Field | Type | Description |
|-------|------|-------------|
| `demographics` | object | `{"age": int, "sex": string, "height": string|null, "weight": string|null}` |
| `known_conditions` | string[] | All known conditions (does not include the primary diagnosis) |
| `current_medications` | string[] | Active medications after the final visit |
| `prior_visit_summaries` | string[] | One summary string per visit |
| `allergies` | string[] | Known allergies |
| `active_symptoms` | object[] | Structured active symptom tracker with trend/severity/status |
| `medication_courses` | object[] | Structured medication course tracker with status and dates |
| `diagnostic_workups` | object[] | Structured diagnostic workup tracker with status/certainty |
| `open_clinical_questions` | object[] | Open/resolved/deferred clinical questions |
| `follow_up_tasks` | object[] | Pending/completed/deferred follow-up tasks |

## Notes JSONL (`notes.jsonl`)

Each line is a JSON object representing one clinical note, enriched with case-level metadata. Designed for use as training/evaluation data.

```json
{"case_id": "a1b2c3d4", "difficulty": "hard", "case_type": "chronic", "visit_number": 1, "clinician_specialty": "Emergency Medicine", "note_date": "2025-03-01", "content": "...", "symptoms_reported": [...], "vitals": {...}, "tests_ordered": [...], "diagnoses_considered": [...], "medications": [...], "follow_up_recommendations": [...]}
```

Each line contains all `ClinicalNote` fields plus `case_id`, `difficulty`, and `case_type` from the parent case.

## CaseConfig JSON (from `build_case.py`)

The `build_case.py` script outputs a `CaseConfig` as JSON. This is the input to the note generation pipeline, not a final output — it contains no narrative, timeline, or notes yet.

The `primary_condition` field is derived by the Constructor from the interpreted coded variables — it is not provided directly by the user. For example, given NAACCR codes `Primary Site=C34.1` and `Histologic Type=8070/3`, the pipeline might produce:

```json
{
  "case_id": "f9e8d7c6",
  "clinical_variables": {
    "primary_condition": "Squamous Cell Carcinoma of the Upper Lobe of the Lung",
    "comorbidities": ["COPD", "Hypertension"],
    "age": 67,
    "sex": "M",
    "risk_factors": ["40 pack-year smoking history", "Occupational asbestos exposure"]
  },
  "difficulty": "hard",
  "case_type": "chronic",
  "intended_outcome": "worsening",
  "narrative": null
}
```

This can be saved and later fed to `CaseRunner.generate_case()` to produce the full case with notes.
