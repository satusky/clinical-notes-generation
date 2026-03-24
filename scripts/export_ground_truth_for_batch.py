"""Insert case_id values from case_seed JSON files into a batch CSV."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Add case_id column to a batch CSV using case_seed JSON files"
    )
    parser.add_argument("--batch_file", required=True, type=Path, help="Input CSV file")
    parser.add_argument("--output_dir", required=True, type=Path, help="Directory containing case_seed_*.json files")
    parser.add_argument("--output_file", type=Path, default="ground_truth.csv", help="Output file name")
    args = parser.parse_args()

    if not args.batch_file.is_file():
        print(f"Error: {args.batch_file} not found")
        raise SystemExit(1)
    if not args.output_dir.is_dir():
        print(f"Error: {args.output_dir} is not a directory")
        raise SystemExit(1)

    # Build mapping: row number -> case_id from case_seed files
    case_ids: dict[int, str] = {}
    for path in args.output_dir.glob("case_seed_*.json"):
        stem = path.stem  # e.g. "case_seed_0"
        try:
            row_num = int(stem.split("_")[-1])
        except ValueError:
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {path.name}: {e}")
            continue
        case_id = data.get("case_id")
        if case_id:
            case_ids[row_num] = case_id

    # Read CSV, insert case_id column
    with open(args.batch_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    header.insert(0, "case_id")
    for i, row in enumerate(rows):
        row.insert(0, case_ids.get(i, ""))

    # Write back
    with open(args.output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    matched = sum(1 for cid in case_ids if cid < len(rows))
    print(f"Inserted {matched} case_ids into {args.batch_file} ({len(rows)} data rows)")


if __name__ == "__main__":
    main()
