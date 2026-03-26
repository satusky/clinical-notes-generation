"""Save completed case to disk. Reads full case JSON from stdin.

Usage: echo '{"case_id": "abc", ...}' | uv run python scripts/tools/save_case.py [--output-dir DIR]
"""

import argparse
import json
import sys

from src.clinical_notes.io import save_case_json, save_notes_jsonl


def main():
    parser = argparse.ArgumentParser(description="Save completed case")
    parser.add_argument("--output-dir", "-o", default=None, help="Output directory")
    args = parser.parse_args()

    raw = sys.stdin.read().strip()
    try:
        case = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    if "case_id" not in case:
        print(json.dumps({"error": "Missing required field: case_id"}))
        sys.exit(1)

    case_path = save_case_json(case, args.output_dir)
    notes_path = save_notes_jsonl([case], args.output_dir)

    print(json.dumps({
        "saved": True,
        "case_path": str(case_path),
        "notes_path": str(notes_path),
        "num_notes": len(case.get("notes", [])),
    }))


if __name__ == "__main__":
    main()
