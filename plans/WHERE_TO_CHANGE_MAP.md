# Where to Change What — Codebase Map

## 1) Add/modify data fields
- **Case-level config**: `src/clinical_notes/models/case.py`
- **Visit/timeline schema**: `src/clinical_notes/models/timeline.py`
- **Clinical note schema**: `src/clinical_notes/models/note.py`
- **Medical history schema**: `src/clinical_notes/models/patient.py`
- Also update:
  - prompts using those fields (`src/clinical_notes/prompts/*.py`)
  - serialization/output docs (`src/clinical_notes/README.md`)
  - tests in `tests/test_models.py` + affected agent tests

## 2) Change agent behavior
- Agent logic: `src/clinical_notes/agents/*.py`
  - e.g. coordinator filtering: `agents/coordinator.py`
  - note writing behavior: `agents/clinician.py`
  - longitudinal updates: `agents/scribe.py`
- Prompt instructions: matching file in `src/clinical_notes/prompts/`
- Tests:
  - `tests/test_agents.py`
  - `tests/test_case_runner.py` (pipeline wiring)

## 3) Tune LLM/provider behavior
- Dispatch/selection: `src/clinical_notes/llm/__init__.py`
- OpenAI-compatible calls: `src/clinical_notes/llm/_openai.py`
- Anthropic calls/tool loop: `src/clinical_notes/llm/_anthropic.py`
- Model parsing: `src/clinical_notes/llm/_types.py`
- Settings/env: `src/clinical_notes/config.py`
- Tests: `tests/test_llm.py`

## 4) Change case-building flow (coded variables → case)
- Main logic: `src/clinical_notes/agents/constructor.py`
- Investigator behavior/tools: `src/clinical_notes/agents/investigator.py`
- Knowledge loading: `src/clinical_notes/knowledge.py`
- Seed/investigation models: `src/clinical_notes/models/investigation.py`
- CLI entry for this flow: `scripts/build_case.py`
- Docs: `CASE_BUILDING.md`
- Tests:
  - `tests/test_constructor.py`
  - `tests/test_investigator.py`
  - `tests/test_investigation_models.py`
  - `tests/test_knowledge.py`

## 5) Change generation pipeline flow (case → notes)
- Pipeline orchestration: `src/clinical_notes/case_runner.py`
- I/O persistence: `src/clinical_notes/io.py`
- CLI: `scripts/generate.py`
- Docs: `AGENT_FRAMEWORK.md` + `src/clinical_notes/README.md`
- Tests: `tests/test_case_runner.py`

## 6) Change output formats / exports / viewing
- JSON + JSONL writing: `src/clinical_notes/io.py`
- HTML case report rendering: `src/clinical_notes/viewer/renderer.py`, `template.py`
- CSV export scripts:
  - `scripts/export_notes_csv.py`
  - `scripts/export_ground_truth_for_batch.py`
  - `scripts/strip_jsonl_fields.py`
  - `scripts/view_case.py`

## 7) Add CLI options
- Build CLI: `scripts/build_case.py`
- Generate CLI: `scripts/generate.py`
- Viewer/export CLIs in `scripts/`
- Add tests for parsing/behavior if nontrivial (current suite is mostly unit-level around core logic)
