"""Create a ground truth CSV for all cases, merging cancer ground truth where available."""

import argparse
import csv
import json
from pathlib import Path

TISSUE_MAP = {
    "C17": "small intestine",
    "C18": "colon",
    "C22": "liver",
    "C25": "pancreas",
    "C34": "lung",
    "C50": "breast",
    "C54": "uterus",
    "C55": "uterus",
    "C56": "ovary",
    "C61": "prostate",
}


def main():
    parser = argparse.ArgumentParser(
        description="Create ground truth CSV for all cases"
    )
    parser.add_argument(
        "--notes-json",
        type=Path,
        default=Path("output/notes_by_case.json"),
        help="Notes JSON grouped by case_id (default: output/notes_by_case.json)",
    )
    parser.add_argument(
        "--cancer-csv",
        type=Path,
        default=Path("output/cancer_notes_ground_truth.csv"),
        help="Cancer ground truth CSV (default: output/cancer_notes_ground_truth.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/ground_truth.csv"),
        help="Output CSV path (default: output/ground_truth.csv)",
    )
    args = parser.parse_args()

    # Get all unique case_ids
    with open(args.notes_json) as f:
        all_case_ids = sorted(json.load(f).keys())

    # Read cancer ground truth
    cancer_rows = {}
    with open(args.cancer_csv, newline="") as f:
        reader = csv.DictReader(f)
        cancer_columns = list(reader.fieldnames)
        for row in reader:
            cancer_rows[row["case_id"]] = row

    # Output columns: case_id, has_cancer, tissue, then remaining cancer columns
    remaining = [c for c in cancer_columns if c != "case_id"]
    out_columns = ["case_id", "has_cancer", "tissue"] + remaining

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_columns)
        writer.writeheader()

        for case_id in all_case_ids:
            if case_id in cancer_rows:
                row = dict(cancer_rows[case_id])
                row["has_cancer"] = 1
                code_400 = row.get("400", "")
                row["tissue"] = TISSUE_MAP.get(code_400[:3], "")
            else:
                row = {col: "" for col in cancer_columns}
                row["case_id"] = case_id
                row["has_cancer"] = 0
                row["tissue"] = ""

            writer.writerow(row)

    cancer_count = sum(1 for cid in all_case_ids if cid in cancer_rows)
    print(f"Wrote {len(all_case_ids)} cases to {args.output} ({cancer_count} cancer, {len(all_case_ids) - cancer_count} non-cancer)")


if __name__ == "__main__":
    main()
