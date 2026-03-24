"""Remove specified fields from each line of a JSONL file."""

import argparse
import json
from pathlib import Path

FIELDS_TO_REMOVE = {"difficulty", "case_type", "clinician_specialty"}


def main():
    parser = argparse.ArgumentParser(description="Strip fields from a JSONL file")
    parser.add_argument("input", type=Path, help="Input JSONL file")
    parser.add_argument("--output", type=Path, help="Output JSONL file (default: overwrite input)")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: {args.input} not found")
        raise SystemExit(1)

    output = args.output or args.input
    lines = args.input.read_text().splitlines()
    cleaned = []
    for line in lines:
        if not line.strip():
            continue
        obj = json.loads(line)
        for field in FIELDS_TO_REMOVE:
            obj.pop(field, None)
        cleaned.append(json.dumps(obj))

    output.write_text("\n".join(cleaned) + "\n")
    print(f"Stripped {FIELDS_TO_REMOVE} from {len(cleaned)} lines -> {output}")


if __name__ == "__main__":
    main()
