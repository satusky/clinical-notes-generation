"""Initialize MedicalHistorySummary from CaseConfig JSON. Reads from stdin.

Usage: echo '{"case_id": "...", "clinical_variables": {...}}' | uv run python scripts/tools/init_history.py
"""

import json
import sys

from src.clinical_notes.models.case import CaseConfig
from src.clinical_notes.models.patient import MedicalHistorySummary, PatientDemographics


def main():
    raw = sys.stdin.read().strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        config = CaseConfig.model_validate(data)
    except Exception as e:
        print(json.dumps({"error": f"Invalid CaseConfig: {e}"}))
        sys.exit(1)

    cv = config.clinical_variables
    history = MedicalHistorySummary(
        demographics=PatientDemographics(age=cv.age, sex=cv.sex),
        known_conditions=list(cv.comorbidities),
    )

    print(history.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
