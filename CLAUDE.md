# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clinical notes generation — a multi-agent framework for generating synthetic clinical notes datasets. Licensed under MIT.

Claude Code **is** the orchestrator. There is no Python orchestration layer — Claude Code reads prompt files for each role, calls Python tool scripts for data I/O and validation, and spawns sub-agents for parallel work and information isolation.

## Development Setup

- Python 3.11+ required
- Package manager: `uv`
- Install: `uv sync`
- Run tool scripts: `uv run python scripts/tools/<script>.py`

## Architecture

```
User → Claude Code (reads CLAUDE.md + prompts/*.md)
         │
         ├── Bash: scripts/tools/parse_seed.py   (parse CLI input → CaseSeed JSON)
         ├── Bash: scripts/tools/schema.py        (get JSON schema for any model)
         ├── Bash: scripts/tools/validate.py       (validate JSON against model)
         ├── Bash: scripts/tools/load_knowledge.py (load URLs/files/dirs)
         ├── Bash: scripts/tools/save_case.py      (save final case output)
         ├── Bash: scripts/tools/init_history.py   (initialize MedicalHistorySummary)
         │
         ├── Agent: Investigator sub-agents (parallel, with file tool access)
         ├── Agent: Clinician sub-agents (info barrier — no diagnosis in context)
         │
         └── Read: prompts/*.md (role instructions for each pipeline step)
```

**Claude Code handles**: all reasoning, structured output generation, pipeline orchestration
**Scripts handle**: parsing, validation, I/O, knowledge loading (no LLM calls)
**Sub-agents handle**: parallel investigation, information-isolated clinician work

## Tool Scripts

All scripts live in `scripts/tools/` and communicate via JSON stdin/stdout.

| Script | Purpose | Usage |
|--------|---------|-------|
| `parse_seed.py` | Parse CLI args → CaseSeed JSON | `uv run python scripts/tools/parse_seed.py --var "Primary Site=C34.1" --coding-system NAACCR` |
| `schema.py` | Get JSON schema for a model | `uv run python scripts/tools/schema.py InvestigationPlan` |
| `validate.py` | Validate JSON against a model | `echo '<json>' \| uv run python scripts/tools/validate.py Timeline` |
| `load_knowledge.py` | Load knowledge source content | `echo '<sources_json>' \| uv run python scripts/tools/load_knowledge.py` |
| `save_case.py` | Save completed case to disk | `echo '<case_json>' \| uv run python scripts/tools/save_case.py --output-dir output/` |
| `init_history.py` | Initialize MedicalHistorySummary | `echo '<config_json>' \| uv run python scripts/tools/init_history.py` |

Available models for `schema.py` and `validate.py`: `CaseConfig`, `CaseSeed`, `ClinicalNote`, `InvestigationPlan`, `InvestigatorReport`, `MedicalHistorySummary`, `Timeline`, `VisitAssignment`

## Prompt Files

Role-specific instructions live in `prompts/*.md`. Read the relevant file before each pipeline step.

| File | Role |
|------|------|
| `prompts/constructor_plan.md` | Plan variable investigation |
| `prompts/constructor_merge.md` | Merge reports into CaseConfig |
| `prompts/investigator.md` | Investigate a coded variable |
| `prompts/narrator.md` | Write disease progression narrative |
| `prompts/orchestrator.md` | Build visit timeline |
| `prompts/coordinator.md` | Strip diagnosis from visit data |
| `prompts/clinician.md` | Write clinical note (no diagnosis) |
| `prompts/scribe.md` | Update medical history |

---

## Pipeline 1: Case Building

Converts raw coded variables into a structured `CaseConfig`.

### Steps

1. **Parse input**: Run `scripts/tools/parse_seed.py` with the user's CLI args to get a `CaseSeed` JSON.

2. **Get schema**: Run `scripts/tools/schema.py InvestigationPlan` to learn the output format.

3. **Plan investigations** (Constructor — Plan phase):
   - Read `prompts/constructor_plan.md` for role instructions.
   - Given the CaseSeed, produce an `InvestigationPlan` JSON that assigns each raw variable to an investigator.
   - Include all raw variables, knowledge source indices, and coding system info in each assignment.
   - Validate output: pipe result through `scripts/tools/validate.py InvestigationPlan`.

4. **Run investigators** (parallel sub-agents, up to 5 concurrent):
   - Read `prompts/investigator.md` for role instructions.
   - For each `VariableAssignment` in the plan, spawn a sub-agent with:
     - The investigator prompt content
     - The VariableAssignment JSON
     - The `InvestigatorReport` schema (from `scripts/tools/schema.py InvestigatorReport`)
     - For local file/directory sources: give the sub-agent access to those paths so it can use Read/Glob/Grep tools to query reference materials
   - Each sub-agent returns an `InvestigatorReport` JSON.
   - Validate each report: pipe through `scripts/tools/validate.py InvestigatorReport`.

5. **Merge reports** (Constructor — Merge phase):
   - Read `prompts/constructor_merge.md` for role instructions.
   - Get schema: `scripts/tools/schema.py CaseConfig`.
   - Given the CaseSeed, InvestigationPlan, and all InvestigatorReports, produce a `CaseConfig`.
   - Validate: pipe through `scripts/tools/validate.py CaseConfig`.

### Example

```
User: "Build a case with Primary Site=C34.1, coding system NAACCR, source /path/to/docs/"
```

Claude Code runs:
```bash
uv run python scripts/tools/parse_seed.py --var "Primary Site=C34.1" --coding-system NAACCR --source /path/to/docs/
```
Then orchestrates the Constructor → Investigators → Constructor merge pipeline.

---

## Pipeline 2: Note Generation

Converts a `CaseConfig` into a full set of clinical notes.

### Steps

1. **Initialize history**: Pipe the CaseConfig JSON through `scripts/tools/init_history.py` to get the initial `MedicalHistorySummary`.

2. **Generate narrative** (Narrator):
   - Read `prompts/narrator.md` for role instructions.
   - Given the CaseConfig, write a disease progression narrative (plain text, not JSON).

3. **Build timeline** (Orchestrator):
   - Read `prompts/orchestrator.md` for role instructions.
   - Get schema: `scripts/tools/schema.py Timeline`.
   - Given the narrative and CaseConfig, produce a `Timeline` JSON with fully detailed Visit objects.
   - Validate: pipe through `scripts/tools/validate.py Timeline`.

4. **Process each visit sequentially**:

   For each visit in the timeline:

   a. **Coordinator** (main context — has diagnosis access):
      - Read `prompts/coordinator.md` for role instructions.
      - Get schema: `scripts/tools/schema.py VisitAssignment`.
      - Given the primary condition, the full Visit object, and the current MedicalHistorySummary, produce a `VisitAssignment` with all diagnosis references stripped.
      - Validate: pipe through `scripts/tools/validate.py VisitAssignment`.

   b. **Clinician** (spawned sub-agent — NO diagnosis access):
      - **CRITICAL**: Spawn as a separate sub-agent. The sub-agent receives ONLY:
        - The clinician prompt content (from `prompts/clinician.md`)
        - The `VisitAssignment` JSON (already diagnosis-free)
        - The `MedicalHistorySummary` JSON (also diagnosis-free)
        - The `ClinicalNote` schema (from `scripts/tools/schema.py ClinicalNote`)
      - The sub-agent must NEVER receive: the primary_condition, disease_progression_notes, the full Visit object, or the Narrator's narrative.
      - The sub-agent returns a `ClinicalNote` JSON.
      - Validate: pipe through `scripts/tools/validate.py ClinicalNote`.

   c. **Scribe** (main context):
      - Read `prompts/scribe.md` for role instructions.
      - Get schema: `scripts/tools/schema.py MedicalHistorySummary`.
      - Given the current MedicalHistorySummary, the ClinicalNote, and visit details, produce an updated `MedicalHistorySummary`.
      - **Do NOT include `diagnoses_considered`** from the clinical note.
      - Validate: pipe through `scripts/tools/validate.py MedicalHistorySummary`.

5. **Save case**: Pipe the complete case JSON through `scripts/tools/save_case.py --output-dir output/`.

### Case JSON Structure

The final case JSON (for `save_case.py`) should be:
```json
{
  "case_id": "...",
  "clinical_variables": {
    "primary_condition": "...",
    "comorbidities": [],
    "age": 67,
    "sex": "M",
    "risk_factors": []
  },
  "difficulty": "medium",
  "case_type": "chronic",
  "intended_outcome": "improving",
  "narrative": "...",
  "timeline": [ { visit objects... } ],
  "notes": [ { note objects... } ],
  "final_medical_history": { ... }
}
```

---

## Information Barrier Rules

The information barrier ensures clinicians reason independently without knowing the diagnosis.

### What the Clinician sub-agent NEVER receives:
- `primary_condition` from CaseConfig
- `disease_progression_notes` from Visit
- The full Visit object (only the filtered VisitAssignment)
- The Narrator's narrative
- Any text containing the diagnosis name

### How the barrier is enforced:
1. **Coordinator** (main context): Has full diagnosis access. Produces a `VisitAssignment` with diagnosis stripped from all fields.
2. **Clinician** (sub-agent): Spawned with ONLY the VisitAssignment, MedicalHistorySummary, and clinician prompt. No other context.
3. **Scribe** (main context): Updates medical history but excludes `diagnoses_considered` from the clinical note.

---

## Post-Processing Tools

These scripts are not part of the pipeline but useful for working with outputs:

- **View a case**: `uv run python scripts/view_case.py output/<case_id>.json`
- **Export to CSV**: `uv run python scripts/export_notes_csv.py --input-dir output/ --output notes.csv`

---

## Example Workflows

### Build a case from coded variables
```
"Build a case with Primary Site=C34.1, Histologic Type=8070/3, Grade=2, coding system NAACCR, source /path/to/naaccr_docs/"
```

### Generate notes from a seed file
```
"Generate clinical notes from this seed file: output/case_seed.json"
```

### Build cases from CSV
```
"Build cases from patients.csv using NAACCR coding system"
```

### End-to-end
```
"Build a case and generate clinical notes for Primary Site=C34.1 with NAACCR coding, difficulty hard"
```

Claude Code will run Pipeline 1 (case building) followed by Pipeline 2 (note generation).
