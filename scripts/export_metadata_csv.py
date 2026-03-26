"""Export case metadata (age, sex, optional location) to a CSV from a JSONL of clinical notes."""

import argparse
import csv
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export case metadata to CSV")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSONL file of clinical notes",
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=Path("output/cases"),
        help="Directory containing <case_id>.json files (default: output/cases)",
    )
    parser.add_argument(
        "--locations",
        type=Path,
        default=None,
        help="Path to two-column CSV with 'city' and 'state' headers",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/case_metadata.csv"),
        help="Output CSV path (default: output/case_metadata.csv)",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"Error: {input_path} does not exist")
        raise SystemExit(1)

    # Collect unique case_ids preserving insertion order
    case_ids = list(
        dict.fromkeys(
            entry["case_id"]
            for line in input_path.read_text().splitlines()
            if line.strip()
            for entry in [json.loads(line)]
            if "case_id" in entry
        )
    )

    # Load locations if provided (two-column CSV: city, state)
    locations: list[tuple[str, str]] | None = None
    if args.locations:
        with open(args.locations, newline="") as f:
            reader = csv.DictReader(f)
            # Normalize headers to lowercase for flexible matching
            reader.fieldnames = [name.lower() for name in reader.fieldnames]
            locations = [(row["city"], row["state"]) for row in reader]

    case_dir: Path = args.case_dir
    rows: list[list[str]] = []
    for case_id in case_ids:
        case_path = case_dir / f"{case_id}.json"
        try:
            data = json.loads(case_path.read_text())
        except FileNotFoundError:
            print(f"Warning: skipping {case_id}: {case_path} not found")
            continue
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {case_id}: {e}")
            continue

        clinical_vars = data.get("clinical_variables", {})
        age = str(clinical_vars.get("age", ""))
        sex = str(clinical_vars.get("sex", ""))

        row = [case_id, age, sex]
        if locations is not None:
            city, state = random.choice(locations)
            row.extend([city, state])
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        header = ["case_id", "age", "sex"]
        if locations is not None:
            header.extend(["city", "state"])
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Exported {len(rows)} cases to {args.output}")


if __name__ == "__main__":
    main()
