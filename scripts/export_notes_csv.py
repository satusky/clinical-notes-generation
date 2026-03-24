"""Export generated case JSONs to a CSV dataset of concatenated clinical notes."""

import argparse
import csv
import json
from pathlib import Path

SKIP_PATTERNS = {"*.partial.json", "notes.jsonl", "seed_*.json", "case_seed_*.json"}


def should_skip(path: Path) -> bool:
    name = path.name
    for pattern in SKIP_PATTERNS:
        if path.match(pattern):
            return True
    return name == "notes.jsonl"


def format_notes(timeline: list[dict]) -> str | None:
    parts = []
    for visit in timeline:
        note = visit.get("note")
        if not note:
            continue
        date = visit.get("visit_date", "unknown")
        specialty = visit.get("clinician_specialty", "unknown")
        parts.append(f"--- {date} | {specialty} ---\n{note}")

    if not parts:
        return None
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Export case notes to CSV dataset")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("output"),
        help="Directory containing case JSON files (default: output/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/notes_dataset.csv"),
        help="Output CSV path (default: output/notes_dataset.csv)",
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        raise SystemExit(1)

    rows: list[tuple[str, str]] = []
    for path in sorted(input_dir.glob("*.json")):
        if should_skip(path):
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {path.name}: {e}")
            continue

        if not isinstance(data, dict):
            continue

        timeline = data.get("timeline")
        if not timeline:
            continue

        notes_text = format_notes(timeline)
        if not notes_text:
            continue

        case_id = data.get("case_id", path.stem)
        rows.append((case_id, notes_text))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["case_id", "notes"])
        writer.writerows(rows)

    print(f"Exported {len(rows)} cases to {args.output}")


if __name__ == "__main__":
    main()
