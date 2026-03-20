NARRATOR_SYSTEM = """\
You are a medical narrative writer. Given clinical variables describing a patient case, \
you create a detailed, realistic narrative of the patient's disease course.

Your narrative should:
- Describe how the condition develops and manifests over time
- Include realistic symptom progression aligned with the primary condition
- Incorporate the patient's comorbidities and risk factors naturally
- Match the specified difficulty level (easy = textbook presentation, hard = atypical/subtle)
- Match the intended outcome (resolved, improving, worsening, or undiagnosed)
- Be medically accurate and plausible
- Include enough detail that a timeline of clinical visits can be derived from it

Do NOT write clinical notes — write a narrative story of the disease course.
"""


def narrator_user_prompt(
    primary_condition: str,
    comorbidities: list[str],
    age: int,
    sex: str,
    risk_factors: list[str],
    difficulty: str,
    case_type: str,
    intended_outcome: str,
) -> str:
    comorbidities_str = ", ".join(comorbidities) if comorbidities else "None"
    risk_factors_str = ", ".join(risk_factors) if risk_factors else "None"
    return f"""\
Create a clinical narrative for the following case:

Primary condition: {primary_condition}
Comorbidities: {comorbidities_str}
Patient: {age}-year-old {sex}
Risk factors: {risk_factors_str}
Difficulty: {difficulty}
Case type: {case_type}
Intended outcome: {intended_outcome}

Write a detailed narrative of this patient's disease course, from initial symptoms through \
the progression of care. Include realistic timing, symptom evolution, and clinical decision points."""
