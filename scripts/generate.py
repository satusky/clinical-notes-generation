"""CLI entry point for generating clinical cases."""

import argparse
import asyncio
import logging
import sys
import uuid

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

EXAMPLE_CASE = CaseConfig(
    case_id=str(uuid.uuid4())[:8],
    clinical_variables=ClinicalVariables(
        primary_condition="Type 2 Diabetes Mellitus",
        comorbidities=["Hypertension", "Obesity"],
        age=58,
        sex="M",
        risk_factors=["Sedentary lifestyle", "Family history of diabetes", "High BMI"],
    ),
    difficulty=Difficulty.MEDIUM,
    case_type=CaseType.CHRONIC,
    intended_outcome=CaseOutcome.IMPROVING,
)


async def run(args: argparse.Namespace):
    logging.basicConfig(level=getattr(logging, settings.log_level))

    runner = CaseRunner()

    # Generate the case
    case = await runner.generate_case(EXAMPLE_CASE)

    # Save outputs
    save_case_json(case, args.output)
    save_notes_jsonl([case], args.output)

    print(f"Case {case['case_id']} generated with {len(case['notes'])} notes.")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic clinical notes")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main() or 0)
