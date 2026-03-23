# Agentic case-building pipeline

The case building pipeline accepts minimal input (a `CaseSeed`) and constructs a fully populated `CaseConfig` by interpreting raw coded variables via LLM-powered agents. The initial focus is cancer cases using coding systems like NAACCR.

## Flow

```
CaseSeed → Constructor (plan) → [Investigator × N in parallel] → Constructor (merge) → CaseConfig
```

## Case configuration construction

1. The user provides a `CaseSeed` with raw coded variable/value pairs (e.g. NAACCR codes), an optional coding system label, and optional constraints (age, sex, difficulty, case type, intended outcome, knowledge sources).
2. The **Constructor** assigns investigators to interpret each coded variable via an `InvestigationPlan`. Each assignment carries the raw coded value and a focus describing what to look up in the reference material.
3. The Constructor dispatches an **Investigator** for each variable (up to 5 concurrently). Investigators interpret their assigned code by consulting provided knowledge sources (e.g. NAACCR coding manuals) and return an `InvestigatorReport`.
4. The Constructor merges all Investigator reports into a unified `CaseConfig`, deriving a human-readable `primary_condition` from the interpreted codes and ensuring medical plausibility.

## Key components

| Component | Location | Purpose |
|-----------|----------|---------|
| `CaseSeed` | `src/clinical_notes/models/investigation.py` | Raw coded variables + constraints |
| `InvestigationPlan` | `src/clinical_notes/models/investigation.py` | Constructor's variable assignment plan |
| `InvestigatorReport` | `src/clinical_notes/models/investigation.py` | Structured interpretation output |
| `ConstructorAgent` | `src/clinical_notes/agents/constructor.py` | Plans, dispatches, and merges |
| `InvestigatorAgent` | `src/clinical_notes/agents/investigator.py` | Interprets a single coded variable |
| `KnowledgeLoader` | `src/clinical_notes/knowledge.py` | Loads content from knowledge sources |
| `CaseBuilder` | `src/clinical_notes/case_builder.py` | High-level entry point |

## Knowledge sources

Knowledge sources can be provided in the `CaseSeed` to give investigators reference material for interpreting codes:

- **Web URLs**: Fetched via HTTP, HTML tags stripped
- **Local files**: Read directly from disk
- **Local directories**: All `.txt`, `.md`, and `.json` files concatenated

Content is truncated to `knowledge_source_max_chars` (default 10,000) per source.

## Usage

### CLI — standalone case building

```bash
uv run python scripts/build_case.py \
  --var "Primary Site=C34.1" \
  --var "Histologic Type=8070/3" \
  --var "Grade=2" \
  --coding-system NAACCR \
  --source /path/to/naaccr_docs/ \
  --difficulty hard \
  --case-type chronic \
  --outcome worsening
```

Or using a variables file:

```bash
uv run python scripts/build_case.py \
  --variables-file variables.json \
  --coding-system NAACCR \
  --source /path/to/naaccr_docs/
```

Where `variables.json` contains:

```json
{
  "Primary Site": "C34.1",
  "Histologic Type": "8070/3",
  "Grade": "2"
}
```

### CLI — end-to-end (case building + note generation)

```bash
uv run python scripts/generate.py --seed-file seed.json
```

Where `seed.json` contains:

```json
{
  "raw_variables": {"Primary Site": "C34.1", "Histologic Type": "8070/3"},
  "coding_system": "NAACCR",
  "difficulty": "hard",
  "case_type": "chronic",
  "intended_outcome": "worsening"
}
```

### Python API

```python
from src.clinical_notes.case_builder import CaseBuilder
from src.clinical_notes.models.investigation import CaseSeed

seed = CaseSeed(
    raw_variables={"Primary Site": "C34.1", "Histologic Type": "8070/3"},
    coding_system="NAACCR",
)
builder = CaseBuilder()
config = await builder.build_case(seed)

# config is a CaseConfig, ready for CaseRunner
```

## Configuration

Per-agent model overrides in `.env` or environment:

- `CONSTRUCTOR_MODEL` — model for the Constructor agent
- `INVESTIGATOR_MODEL` — model for Investigator agents
- `KNOWLEDGE_SOURCE_MAX_CHARS` — max chars per knowledge source (default 10,000)
