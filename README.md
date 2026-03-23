# clinical-notes-generation

A multi-agent framework for generating synthetic clinical notes datasets. The system uses LLM-powered agents to construct medically plausible patient cases and produce realistic clinical documentation.

## Overview

The project has two phases:

1. **Case Building** — Takes raw coded variables (e.g. NAACCR codes) and knowledge source documents (e.g. coding manuals), interprets each code via parallel investigator agents, and synthesizes a fully populated case configuration. See [CASE_BUILDING.md](CASE_BUILDING.md).

2. **Note Generation** — Takes a case configuration and generates a series of clinical notes through a multi-agent pipeline that maintains an information barrier (the note-writing clinician does not know the diagnosis). See [AGENT_FRAMEWORK.md](AGENT_FRAMEWORK.md).

```
CaseSeed → Constructor → [Investigator × N] → CaseConfig → Narrator → Orchestrator → [Coordinator → Clinician → Scribe] × visits → Clinical Notes
```

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Configure API keys in a `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

## Usage

### Build a case from coded variables

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

Optional flags: `--age`, `--sex`, `--variables-file` (JSON dict), `--source` (repeatable — accepts URLs or file/directory paths), `--output`.

### Generate clinical notes from a seed file

```bash
uv run python scripts/generate.py --seed-file seed.json
```

### Generate clinical notes from the built-in example case

```bash
uv run python scripts/generate.py
```

## Architecture

### Agents

| Agent | Role |
|-------|------|
| **Constructor** | Assigns investigators to interpret coded variables, dispatches them, merges results into a `CaseConfig` |
| **Investigator** | Interprets a single coded variable, consulting knowledge sources |
| **Narrator** | Writes a disease progression narrative from clinical variables |
| **Orchestrator** | Builds a visit timeline with rich clinical detail |
| **Coordinator** | Strips diagnosis references from visit data before passing to the Clinician |
| **Clinician** | Writes clinical notes without knowledge of the underlying diagnosis |
| **Scribe** | Updates the patient's medical history after each visit |

### Model support

Supports multiple LLM providers via a `provider/model` string format:

- `anthropic/claude-sonnet-4-20250514` (default)
- `openai/gpt-4o`
- `ollama/llama3`
- `vllm/model-name`

Per-agent model overrides can be set via environment variables (e.g. `CONSTRUCTOR_MODEL`, `NARRATOR_MODEL`).

## Development

```bash
uv run pytest               # run tests
uv run ruff check src/ tests/  # lint
```

## License

MIT
