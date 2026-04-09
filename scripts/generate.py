"""CLI entry point for generating clinical cases."""

import argparse
import asyncio
import logging
import sys
import uuid
from pathlib import Path

from src.clinical_notes.case_runner import CaseRunner
from src.clinical_notes.config import settings
from src.clinical_notes.io import save_case_json, save_notes_jsonl
from src.clinical_notes.models.case import (
    CaseConfig,
    CaseOutcome,
    CaseType,
    ClinicalVariables,
    Difficulty,
)

# EXAMPLE_CASE = CaseConfig(
#     case_id=str(uuid.uuid4())[:8],
#     clinical_variables=ClinicalVariables(
#         primary_condition="Type 2 Diabetes Mellitus",
#         comorbidities=["Hypertension", "Obesity"],
#         age=58,
#         sex="M",
#         risk_factors=["Sedentary lifestyle", "Family history of diabetes", "High BMI"],
#     ),
#     difficulty=Difficulty.MEDIUM,
#     case_type=CaseType.CHRONIC,
#     intended_outcome=CaseOutcome.IMPROVING,
# )


EXAMPLE_CASE = CaseConfig(
    case_id=str(uuid.uuid4())[:8],
    clinical_variables=ClinicalVariables(
        primary_condition="Non-Small Cell Lung Cancer",
        comorbidities=["COPD", "Hypertension", "dyslipidemia"],
        age=67,
        sex="M",
        risk_factors=["Former 40 pack-year smoker", "Family history of diabetes", "High BMI"],
    ),
    difficulty=Difficulty.MEDIUM,
    case_type=CaseType.CHRONIC,
    intended_outcome=CaseOutcome.IMPROVING,
)


async def run(seed_file: str | None = None, output: str | None = None):
    logging.basicConfig(level=getattr(logging, settings.log_level))

    runner = CaseRunner()

    if seed_file:
        # Build a CaseConfig from a seed file via the case-building pipeline
        import json

        from src.clinical_notes.case_builder import CaseBuilder
        from src.clinical_notes.models.investigation import CaseSeed

        seed_data = json.loads(Path(seed_file).read_text())
        if "raw_variables" in seed_data:
            seed = CaseSeed(**seed_data)
            config = await CaseBuilder().build_case(seed)
        else:
            config = CaseConfig(**seed_data)
    else:
        config = EXAMPLE_CASE

    # Generate the case
    case = await runner.generate_case(config)

    # Save outputs
    save_case_json(case, output)
    save_notes_jsonl([case], output)

    print(f"Case {case['case_id']} generated with {len(case['notes'])} notes.")


def resolve_seed_files(seed_file: str | None, seed_dir: str | None) -> list[str | None]:
    """Resolve input mode into concrete seed files (or [None] for example case)."""
    if seed_file and seed_dir:
        raise ValueError("Provide either --seed-file or --seed-dir, not both")

    if seed_dir:
        directory = Path(seed_dir)
        if not directory.is_dir():
            raise FileNotFoundError(f"Seed directory not found: {seed_dir}")
        files = sorted(str(path) for path in directory.glob("*_seed*.json"))
        if not files:
            raise FileNotFoundError(f"No seed files matching '*_seed*.json' found in {seed_dir}")
        return files

    if seed_file:
        path = Path(seed_file)
        if not path.is_file():
            raise FileNotFoundError(f"Seed file not found: {seed_file}")
        return [str(path)]

    return [None]


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic clinical notes")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--seed-file", default=None,
                        help="Path to a JSON file containing CaseSeed/CaseConfig fields")
    parser.add_argument("--seed-dir", default=None,
                        help="Path to a directory containing seed files")
    args = parser.parse_args()

    try:
        seed_files = resolve_seed_files(args.seed_file, args.seed_dir)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for seed_file in seed_files:
        asyncio.run(run(seed_file, args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
