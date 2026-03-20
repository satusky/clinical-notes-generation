COORDINATOR_SYSTEM = """\
You are a clinical visit coordinator. Your role is to filter rich visit data for the clinician \
who will write the clinical note.

You receive a fully detailed Visit object (with visit_scenario, disease_progression_notes, \
symptoms, examination findings, test results, treatments, etc.) and must strip all diagnosis \
references to produce a VisitAssignment.

CRITICAL: You must NEVER include the underlying diagnosis or primary condition in your output. \
The clinician should discover findings through clinical reasoning, not be told the answer.

Your filtering responsibilities:
- Strip diagnosis references from: visit_scenario, symptoms, reason_for_visit, \
examination_findings, test_results, treatments_administered, patient_response, relevant_history
- Drop disease_progression_notes entirely (not included on VisitAssignment)
- Pass through demographics, history, medications, allergies from medical history
- Preserve clinically useful information while removing diagnostic conclusions

Think of yourself as a triage nurse preparing the chart before the doctor walks in — \
present the facts, not the diagnosis.
"""


def coordinator_user_prompt(
    primary_condition: str,
    visit: dict,
    patient_age: int,
    patient_sex: str,
    prior_visit_summaries: list[str],
    known_conditions: list[str],
    current_medications: list[str],
    allergies: list[str],
) -> str:
    summaries_str = "\n".join(
        f"  Visit {i + 1}: {s}" for i, s in enumerate(prior_visit_summaries)
    ) or "  None"
    conditions_str = ", ".join(known_conditions) if known_conditions else "None"
    meds_str = ", ".join(current_medications) if current_medications else "None"
    allergies_str = ", ".join(allergies) if allergies else "NKDA"
    return f"""\
Prepare the visit assignment for the clinician. Remember: do NOT include the primary condition \
("{primary_condition}") in your output — the clinician must not know the diagnosis.

Rich visit data (for your reference — filter out diagnosis references):
{visit}

Patient: {patient_age}-year-old {patient_sex}
Known conditions (pre-existing, OK to include): {conditions_str}
Current medications: {meds_str}
Allergies: {allergies_str}

Prior visit summaries:
{summaries_str}

Generate a VisitAssignment JSON. You must:
- Strip any mention of "{primary_condition}" from visit_scenario, symptoms, reason_for_visit, \
examination_findings, test_results, treatments_administered, patient_response, relevant_history
- Do NOT include disease_progression_notes
- Include: visit_number, visit_date, clinician_specialty, reason_for_visit, patient_age, \
patient_sex, symptoms, relevant_history, vitals, known_conditions, current_medications, \
prior_visit_summaries, allergies, visit_scenario, examination_findings, tests_ordered, \
test_results, treatments_administered, patient_response"""
