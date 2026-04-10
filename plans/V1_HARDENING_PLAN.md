# V1 Hardening Plan (PR-Sized, in Recommended Order)

This plan focuses on reliability, reproducibility, and maintainability without large architectural changes.

---

## PR 1 — Deterministic Model Defaults + Controlled Randomization

### Goal
Remove surprising randomness from core models and make generation behavior reproducible.

### Changes
- In `src/clinical_notes/models/case.py`:
  - Replace randomized field defaults in `CaseConfig` with deterministic defaults:
    - `difficulty=Difficulty.MEDIUM`
    - `case_type=CaseType.ACUTE`
    - `intended_outcome=CaseOutcome.RESOLVED`
- Move random selection to CLI/service entry points:
  - `scripts/build_case.py`
  - any other place where a case is created without explicit values
- Add optional reproducibility controls:
  - CLI flag: `--seed` (int)
  - env fallback: `CASE_RANDOM_SEED`

### Tests
- Update model tests to assert deterministic defaults.
- Add CLI tests (or unit tests for helper functions) validating seeded reproducibility.

### Acceptance Criteria
- `CaseConfig()` defaults are deterministic.
- Running build/generate with same seed yields same setting selections.

---

## PR 2 — Strongly Typed CaseSeed Inputs (Enums + Validation)

### Goal
Catch invalid input values early and simplify downstream conversion logic.

### Changes
- In `src/clinical_notes/models/investigation.py`:
  - Change `CaseSeed` fields from `str` to enums:
    - `difficulty: Difficulty`
    - `case_type: CaseType`
    - `intended_outcome: CaseOutcome`
  - Import enums from `models/case.py`.
- In `scripts/build_case.py`:
  - Remove manual enum coercion where no longer needed.
  - Keep CLI choices aligned with enum values.
- In `src/clinical_notes/agents/constructor.py`:
  - Remove or simplify `Difficulty(seed.difficulty)` style conversion.

### Tests
- Update `tests/test_investigation_models.py` and constructor tests.
- Add negative tests for invalid enum values in seed JSON/JSONL.

### Acceptance Criteria
- Invalid seed values fail fast with clear validation errors.
- Constructor no longer needs defensive enum casting from strings.

---

## PR 3 — Consistency Pass + Leakage Guardrails Before Save

### Goal
Add non-LLM safeguards to catch common quality failures and diagnosis leakage.

### Changes
- Add `src/clinical_notes/validation.py` with checks such as:
  - timeline date ordering and continuity
  - note-to-visit alignment basics (visit number/date consistency)
  - structured/text alignment checks where feasible (meds/tests present in both)
  - coordinator leakage checks for primary condition terms in assignment fields
- Hook checks into `CaseRunner.generate_case()`:
  - per-visit checks after coordinator and clinician
  - final case-level validation before `save_case_json`
- Add strict/lenient mode:
  - env or CLI: `VALIDATION_MODE=strict|warn`

### Tests
- New `tests/test_validation.py` with representative pass/fail cases.
- Update case runner tests to verify validation invocation behavior.

### Acceptance Criteria
- Obvious leakage/consistency issues are detected automatically.
- Strict mode fails fast; warn mode logs issues and continues.

---

## PR 4 — Prompt Governance + Run Traceability

### Goal
Make runs auditable and prompt changes trackable.

### Changes
- Add prompt version constants in each prompt module, e.g.:
  - `PROMPT_VERSION = "2026-04-09.1"`
- Record per-agent run metadata in output case JSON:
  - model used
  - prompt version
  - timestamp
- Extend output schema docs in `src/clinical_notes/README.md`.
- Add optional prompt logging toggle:
  - env: `LOG_PROMPTS=true|false` (default false)

### Tests
- Add assertions in runner tests that metadata is present.
- Add tests for prompt version fields being included.

### Acceptance Criteria
- Every generated case includes enough metadata to reproduce/analyze generation choices.
- Prompt revisions are explicit and visible.

---

## PR 5 — CLI/Script Cleanup + Naming Standardization

### Goal
Reduce operational confusion and improve DX.

### Changes
- Standardize naming across scripts and docs:
  - always use `intended_outcome` internally
  - support legacy alias `outcome` only as backward-compatible input
- Clean up `scripts/generate.py`:
  - clearer behavior for `--seed-file` vs `--seed-dir`
  - explicit error when both are provided
  - robust handling when no seeds found
- Ensure all scripts use consistent output naming and path handling.
- Document all script flags in `README.md`.

### Tests
- Add focused tests around seed file parsing and alias handling.
- Add a smoke test for seed directory batch behavior.

### Acceptance Criteria
- Scripts behave consistently with clear errors.
- Docs match actual CLI behavior.

---

## Suggested Rollout Order Rationale

1. **PR 1** stabilizes behavior and test expectations.
2. **PR 2** strengthens data contracts.
3. **PR 3** adds runtime safeguards against bad outputs.
4. **PR 4** improves observability/auditability.
5. **PR 5** polishes usability and removes edge-case confusion.

---

## Non-Goals for V1 Hardening

- Full refactor of agent architecture
- Provider-agnostic tool-use loop redesign
- Large prompt rewrites for style/medical policy
- Dataset-level scoring/benchmarking framework

These can be V2 once V1 reliability is locked in.
