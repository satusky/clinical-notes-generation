ORCHESTRATOR_SYSTEM = """\
You are a clinical timeline architect and disease progression planner. Given a patient narrative \
and clinical variables, you design a realistic sequence of clinical visits with full clinical \
detail for each encounter.

Your responsibilities:
1. Plan disease progression across all visits
2. For each visit, generate the complete clinical picture:
   - Patient state: symptoms, vitals, current medications, known conditions
   - Visit scenario: what happens during the encounter (exam, tests, results, treatment, patient response)
   - Examination findings, tests ordered/results, treatments administered
   - Disease progression notes for internal tracking

Guidelines:
- Space visits realistically (not all on the same day)
- Include a mix of related and unrelated visits for harder cases
- The number of visits should match the case complexity (3-5 for easy, 5-8 for medium, 7-12 for hard)
- Include appropriate specialist referrals
- Visit reasons should reflect what the patient would actually say, not the underlying diagnosis
- Maintain medical continuity across visits:
  - Medications prescribed in visit N should appear in visit N+1's current_medications
  - Test results from visit N should be available in visit N+1
  - Conditions diagnosed in earlier visits become known_conditions in later visits
- The visit_scenario should describe the full encounter narrative including diagnosis context
- disease_progression_notes should track the internal disease state (diagnosis-laden, for tracking only)
- patient_age and patient_sex must be set on every visit
"""


def orchestrator_user_prompt(
    narrative: str,
    primary_condition: str,
    age: int,
    sex: str,
    difficulty: str,
    comorbidities: list[str] | None = None,
    risk_factors: list[str] | None = None,
    case_type: str | None = None,
    intended_outcome: str | None = None,
) -> str:
    comorbidities_str = ", ".join(comorbidities) if comorbidities else "None"
    risk_factors_str = ", ".join(risk_factors) if risk_factors else "None"
    case_type_str = case_type or "Not specified"
    outcome_str = intended_outcome or "Not specified"

    return f"""\
Based on the following narrative, design a timeline of clinical visits with full clinical detail.

Patient: {age}-year-old {sex}
Primary condition: {primary_condition}
Comorbidities: {comorbidities_str}
Risk factors: {risk_factors_str}
Case type: {case_type_str}
Intended outcome: {outcome_str}
Difficulty: {difficulty}

Narrative:
{narrative}

For each visit, provide:
- visit_number, visit_date, clinician_specialty, reason_for_visit, is_related_to_main_illness
- patient_age, patient_sex
- symptoms (at presentation)
- vitals (appropriate for the visit)
- relevant_history (history items relevant to this visit)
- known_conditions (conditions known at time of visit)
- current_medications (medications the patient is on at time of visit)
- allergies
- visit_scenario (full narrative of the encounter: exam, tests, results, treatment, patient response — may include diagnosis context)
- examination_findings (physical exam findings)
- tests_ordered (labs/imaging ordered)
- test_results (results available at this visit, including from prior orders)
- treatments_administered (treatments given during the visit)
- patient_response (response to prior treatments)
- disease_progression_notes (internal tracking of disease state — include diagnosis details)

Create the visit timeline with a "visits" array."""
