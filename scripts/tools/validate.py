"""Validate JSON against a Pydantic model. Reads JSON from stdin.

Usage: echo '{"visits": []}' | uv run python scripts/tools/validate.py Timeline
"""

import json
import sys

from pydantic import ValidationError

from src.clinical_notes.models import (
    CaseConfig,
    CaseSeed,
    ClinicalNote,
    InvestigationPlan,
    InvestigatorReport,
    MedicalHistorySummary,
    Timeline,
    VisitAssignment,
)

MODELS = {
    "CaseConfig": CaseConfig,
    "CaseSeed": CaseSeed,
    "ClinicalNote": ClinicalNote,
    "InvestigationPlan": InvestigationPlan,
    "InvestigatorReport": InvestigatorReport,
    "MedicalHistorySummary": MedicalHistorySummary,
    "Timeline": Timeline,
    "VisitAssignment": VisitAssignment,
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in MODELS:
        available = ", ".join(sorted(MODELS))
        print(json.dumps({"error": f"Usage: validate.py <ModelName>. Available: {available}"}))
        sys.exit(1)

    model = MODELS[sys.argv[1]]
    raw = sys.stdin.read().strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"valid": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        instance = model.model_validate(data)
        print(instance.model_dump_json(indent=2))
    except ValidationError as e:
        print(json.dumps({"valid": False, "errors": e.errors()}, indent=2, default=str))
        sys.exit(1)


if __name__ == "__main__":
    main()
