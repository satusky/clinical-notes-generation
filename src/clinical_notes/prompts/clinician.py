CLINICIAN_SYSTEM = """\
You are a clinician writing a clinical note for a patient visit. You have access to:
- The visit assignment (symptoms, vitals, history, test results)
- The visit scenario describing what happened during the encounter
- The patient's medical history summary

Based on this information, write a realistic clinical note. You should:
- Document the encounter as a real clinician would
- Use appropriate medical terminology for your specialty
- Include your clinical reasoning and differential diagnosis
- Order appropriate tests and prescribe medications as needed
- Provide follow-up recommendations

Write the note in a natural clinical style. You do NOT know the patient's underlying diagnosis — \
reason from the evidence presented to you.
"""


def clinician_user_prompt(
    visit_number: int,
    visit_date: str,
    clinician_specialty: str,
    reason_for_visit: str,
    patient_age: int,
    patient_sex: str,
    symptoms: list[str],
    relevant_history: list[str],
    vitals: dict[str, str],
    known_conditions: list[str],
    current_medications: list[str],
    prior_visit_summaries: list[str],
    allergies: list[str],
    visit_scenario: str = "",
    examination_findings: list[str] | None = None,
    tests_ordered: list[str] | None = None,
    test_results: list[str] | None = None,
    treatments_administered: list[str] | None = None,
    patient_response: str = "",
) -> str:
    symptoms_str = "\n".join(f"  - {s}" for s in symptoms) or "  None reported"
    history_str = "\n".join(f"  - {h}" for h in relevant_history) or "  None"
    vitals_str = (
        "\n".join(f"  - {k}: {v}" for k, v in vitals.items()) if vitals else "  Not recorded"
    )
    conditions_str = ", ".join(known_conditions) if known_conditions else "None"
    meds_str = ", ".join(current_medications) if current_medications else "None"
    summaries_str = "\n".join(
        f"  Visit {i + 1}: {s}" for i, s in enumerate(prior_visit_summaries)
    ) or "  None"
    allergies_str = ", ".join(allergies) if allergies else "NKDA"
    exam_str = "\n".join(f"  - {f}" for f in (examination_findings or [])) or "  Not recorded"
    tests_ordered_str = "\n".join(f"  - {t}" for t in (tests_ordered or [])) or "  None"
    test_results_str = "\n".join(f"  - {t}" for t in (test_results or [])) or "  None available"
    treatments_str = (
        "\n".join(f"  - {t}" for t in (treatments_administered or [])) or "  None"
    )
    response_str = patient_response or "N/A"

    parts = [
        "Write a clinical note for this encounter.",
        "",
        f"Visit #{visit_number} — {visit_date}",
        f"Specialty: {clinician_specialty}",
        f"Chief complaint: {reason_for_visit}",
        "",
        f"Patient: {patient_age}-year-old {patient_sex}",
        f"Known conditions: {conditions_str}",
        f"Current medications: {meds_str}",
        f"Allergies: {allergies_str}",
    ]

    if visit_scenario:
        parts.extend([
            "",
            "Visit scenario:",
            f"{visit_scenario}",
        ])

    parts.extend([
        "",
        "Symptoms:",
        f"{symptoms_str}",
        "",
        "Relevant history:",
        f"{history_str}",
        "",
        "Vitals:",
        f"{vitals_str}",
        "",
        "Examination findings:",
        f"{exam_str}",
        "",
        "Tests ordered:",
        f"{tests_ordered_str}",
        "",
        "Test results:",
        f"{test_results_str}",
        "",
        "Treatments administered:",
        f"{treatments_str}",
        "",
        "Patient response to prior treatments:",
        f"{response_str}",
        "",
        "Prior visit summaries:",
        f"{summaries_str}",
        "",
        "Write a complete clinical note including your assessment and plan.",
    ])

    return "\n".join(parts)
