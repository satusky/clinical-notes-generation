import json
import logging
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)


def save_case_json(case: dict, output_dir: str | None = None) -> Path:
    """Save a completed case as a JSON file."""
    out = Path(output_dir or settings.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{case['case_id']}.json"
    path.write_text(json.dumps(case, indent=2))
    logger.info("Saved case to %s", path)
    return path


def save_partial_case(case: dict, output_dir: str | None = None) -> Path:
    """Save an in-progress case as a partial JSON file."""
    out = Path(output_dir or settings.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{case['case_id']}.partial.json"
    path.write_text(json.dumps(case, indent=2))
    logger.info("Saved partial case to %s", path)
    return path


def remove_partial(case_id: str, output_dir: str | None = None) -> None:
    """Delete the partial JSON file if it exists."""
    out = Path(output_dir or settings.output_dir)
    path = out / f"{case_id}.partial.json"
    if path.exists():
        path.unlink()
        logger.info("Removed partial file %s", path)


def save_notes_jsonl(cases: list[dict], output_dir: str | None = None) -> Path:
    """Save all notes from multiple cases as JSONL (one note per line) for ML pipelines."""
    out = Path(output_dir or settings.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "notes.jsonl"
    with path.open("w") as f:
        for case in cases:
            for note in case.get("notes", []):
                record = {
                    "case_id": case["case_id"],
                    "difficulty": case["difficulty"],
                    "case_type": case["case_type"],
                    **note,
                }
                f.write(json.dumps(record) + "\n")
    logger.info("Saved %d notes to %s", sum(len(c.get("notes", [])) for c in cases), path)
    return path
