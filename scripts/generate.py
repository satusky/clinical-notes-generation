"""CLI entry point for generating clinical cases."""

import argparse
import asyncio
import logging
import sys
import uuid
import os
import glob

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
        from pathlib import Path

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


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic clinical notes")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--seed-file", default=None,
                        help="Path to a JSON file containing CaseSeed fields")
    parser.add_argument("--seed-dir", default=None,
                        help="Path to a directory containing seed files")
    args = parser.parse_args()
    output_dir = args.output

    if args.seed_dir is not None:
        seed_files = glob.glob(os.path.join(args.seed_dir, "*_seed*.json"))
    else:
        seed_files = [args.seed_file]
    
    for seed_file in seed_files:
        asyncio.run(run(seed_file, output_dir))


if __name__ == "__main__":
    sys.exit(main() or 0)
