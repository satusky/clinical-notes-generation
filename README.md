# clinical-notes-generation

A multi-agent framework for generating synthetic clinical notes datasets. The system uses LLM-powered agents to construct medically plausible patient cases and produce realistic clinical documentation.

## Overview

The project has two phases:

1. **Case Building** — Takes a minimal seed (e.g. a condition name) and constructs a fully populated case configuration by decomposing the condition into clinical variables and researching each one via parallel investigator agents. See [CASE_BUILDING.md](CASE_BUILDING.md).

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

### Build a case from a condition

```bash
uv run python scripts/build_case.py \
  --condition "Stage III Non-Small Cell Lung Cancer" \
  --difficulty hard \
  --case-type chronic \
  --outcome worsening
```

Optional flags: `--age`, `--sex`, `--source` (repeatable — accepts URLs or file/directory paths), `--output`.

### Generate clinical notes from a seed

```bash
uv run python scripts/generate.py --seed "Stage III Non-Small Cell Lung Cancer"
```

### Generate clinical notes from the built-in example case

```bash
uv run python scripts/generate.py
```

## Architecture

### Agents

| Agent | Role |
|-------|------|
| **Constructor** | Decomposes a condition into variables, dispatches investigators, merges results into a `CaseConfig` |
| **Investigator** | Researches a single clinical variable, optionally using knowledge sources |
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
