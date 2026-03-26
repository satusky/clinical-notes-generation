"""Export a flat JSONL file of clinical notes to a JSON file grouped by case_id."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Convert notes JSONL to JSON grouped by case_id"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSONL file of clinical notes",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/notes_by_case.json"),
        help="Output JSON path (default: output/notes_by_case.json)",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"Error: {input_path} does not exist or is not a file")
        sys.exit(1)

    cases: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    with open(input_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed line {line_num}: {e}")
                skipped += 1
                continue

            case_id = record.get("case_id")
            if case_id is None:
                print(f"Warning: skipping line {line_num}: missing case_id")
                skipped += 1
                continue

            visit = {k: v for k, v in record.items() if k != "case_id"}
            cases[str(case_id)].append(visit)

    for visits in cases.values():
        visits.sort(key=lambda v: v.get("visit_number", 0))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        sorted_cases = dict(sorted(cases.items()))
        json.dump(sorted_cases, f, indent=2)

    print(f"Exported {len(cases)} cases to {args.output}")
    if skipped:
        print(f"  ({skipped} lines skipped)")


if __name__ == "__main__":
    main()
