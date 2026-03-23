"""Open a Case JSON in the browser as a rendered HTML report.

Usage:
    uv run python scripts/view_case.py output/b68a5cc2.json
    uv run python scripts/view_case.py b68a5cc2
    uv run python scripts/view_case.py b68a5cc2 --save report.html
    uv run python scripts/view_case.py b68a5cc2 --no-open
"""

import argparse
import json
import shutil
import webbrowser
from pathlib import Path

from src.clinical_notes.viewer.renderer import render_case


def resolve_case(case_arg: str, output_dir: Path) -> Path:
    """Resolve a case argument to a JSON path (accepts a path or a case_id)."""
    p = Path(case_arg)
    if p.exists():
        return p
    # Try output_dir / {case_id}.json
    candidate = output_dir / f"{case_arg}.json"
    if candidate.exists():
        return candidate
    # Try partial
    partial = output_dir / f"{case_arg}.partial.json"
    if partial.exists():
        return partial
    raise FileNotFoundError(f"Cannot find case: {case_arg} (checked {p} and {candidate})")


def main() -> None:
    parser = argparse.ArgumentParser(description="View a case JSON in the browser")
    parser.add_argument("case", help="Path to a case JSON or a case_id")
    parser.add_argument("--output-dir", default="output", help="Directory containing case JSONs")
    parser.add_argument("--save", metavar="PATH", help="Save HTML to a specific path")
    parser.add_argument("--no-open", action="store_true", help="Don't open the browser")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    case_path = resolve_case(args.case, output_dir)
    case = json.loads(case_path.read_text())

    html = render_case(case)

    if args.save:
        dest = Path(args.save)
    else:
        dest = case_path.with_suffix(".html")

    dest.write_text(html)
    print(f"Wrote {dest} ({len(html):,} bytes)")

    if not args.no_open:
        webbrowser.open(dest.resolve().as_uri())


if __name__ == "__main__":
    main()
