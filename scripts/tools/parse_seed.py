"""Parse CLI args into CaseSeed JSON. Outputs JSON to stdout."""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

from src.clinical_notes.models.investigation import CaseSeed, KnowledgeSource, KnowledgeSourceType


def _parse_source(value: str) -> KnowledgeSource:
    """Parse a source string into a KnowledgeSource."""
    if value.startswith("http://") or value.startswith("https://"):
        return KnowledgeSource(source_type=KnowledgeSourceType.WEB_URL, location=value)
    p = Path(value)
    if p.is_dir():
        return KnowledgeSource(source_type=KnowledgeSourceType.LOCAL_DIRECTORY, location=value)
    return KnowledgeSource(source_type=KnowledgeSourceType.LOCAL_FILE, location=value)


def _parse_var(value: str) -> tuple[str, str]:
    """Parse a 'Name=coded_value' string into a (name, value) tuple."""
    parts = value.split("=", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            f"Invalid variable format: {value!r}. Expected 'Name=value'."
        )
    return parts[0].strip(), parts[1].strip()


def load_patients_csv(path: str) -> list[dict[str, str]]:
    """Load patient rows from a CSV where columns are NAACCR variable IDs.

    Column "400" (Primary Site) has the dot inserted at index -2
    (e.g. "C341" becomes "C34.1").
    """
    patients: list[dict[str, str]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            variables: dict[str, str] = {}
            for col, val in row.items():
                val = val.strip()
                if col == "400" and len(val) >= 2:
                    val = val[:-1] + "." + val[-1:]
                variables[col] = val
            patients.append(variables)
    return patients


def get_variables(args: argparse.Namespace) -> list[dict[str, str]]:
    """Build raw_variables list from CLI args."""
    raw_variables: dict[str, str] = {}

    if args.patients_csv:
        patients = load_patients_csv(args.patients_csv)
        if not patients:
            print(json.dumps({"error": "CSV file contains no data rows"}))
            sys.exit(1)

        if args.batch_patients:
            return patients

        row_idx = args.row if args.row is not None else 0
        if args.row is not None and (row_idx < 0 or row_idx >= len(patients)):
            print(json.dumps({
                "error": f"--row {row_idx} out of range (CSV has {len(patients)} rows, 0-indexed)"
            }))
            sys.exit(1)

        raw_variables.update(patients[row_idx])

    if args.variables_file:
        vf = Path(args.variables_file)
        raw_variables.update(json.loads(vf.read_text()))

    if args.var:
        for v in args.var:
            name, val = _parse_var(v)
            raw_variables[name] = val

    if not raw_variables:
        print(json.dumps({"error": "provide variables via --var, --variables-file, or --patients-csv"}))
        sys.exit(1)

    return [raw_variables]


def main():
    parser = argparse.ArgumentParser(description="Parse CLI input into CaseSeed JSON")
    parser.add_argument("--var", "-v", action="append",
                        help="Variable as 'Name=coded_value' (repeatable)")
    parser.add_argument("--variables-file", default=None,
                        help="JSON file with a dict of variable name/value pairs")
    parser.add_argument("--coding-system", default=None,
                        help="Coding system label (e.g. NAACCR, ICD-10)")
    parser.add_argument("--age", type=int, default=None, help="Patient age")
    parser.add_argument("--sex", default=None, help="Patient sex (M/F)")
    parser.add_argument("--difficulty", "-d", default=None,
                        choices=["easy", "medium", "hard"])
    parser.add_argument("--case-type", default=None, choices=["acute", "chronic"])
    parser.add_argument("--outcome", default=None,
                        choices=["resolved", "improving", "worsening", "undiagnosed"])
    parser.add_argument("--source", "-s", action="append",
                        help="Knowledge source (URL or path)")
    parser.add_argument("--patients-csv", default=None,
                        help="CSV file with NAACCR variable IDs as columns")
    parser.add_argument("--row", type=int, default=None,
                        help="0-indexed row to select from --patients-csv (default: 0)")
    parser.add_argument("--batch_patients", action="store_true",
                        help="Process all rows from CSV")
    args = parser.parse_args()

    if args.batch_patients:
        args.row = None

    case_list = get_variables(args)
    sources = [_parse_source(s) for s in args.source] if args.source else []

    difficulty = args.difficulty or random.choice(["easy", "medium", "hard"])
    case_type = args.case_type or random.choice(["acute", "chronic"])
    outcome = args.outcome or random.choice(["resolved", "improving", "worsening", "undiagnosed"])

    seeds = []
    for raw_variables in case_list:
        seed = CaseSeed(
            raw_variables=raw_variables,
            coding_system=args.coding_system,
            age=args.age,
            sex=args.sex,
            difficulty=difficulty,
            case_type=case_type,
            intended_outcome=outcome,
            knowledge_sources=sources,
        )
        seeds.append(json.loads(seed.model_dump_json()))

    if len(seeds) == 1:
        print(json.dumps(seeds[0], indent=2))
    else:
        print(json.dumps(seeds, indent=2))


if __name__ == "__main__":
    main()
