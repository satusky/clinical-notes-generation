"""Output JSON schema for a Pydantic model. Usage: uv run python scripts/tools/schema.py <ModelName>"""

import json
import sys

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
        print(json.dumps({"error": f"Usage: schema.py <ModelName>. Available: {available}"}))
        sys.exit(1)

    model = MODELS[sys.argv[1]]
    print(json.dumps(model.model_json_schema(), indent=2))


if __name__ == "__main__":
    main()
