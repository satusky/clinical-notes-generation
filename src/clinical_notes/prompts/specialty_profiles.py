SPECIALTY_PROFILES: dict[str, dict[str, str]] = {
    "Emergency Medicine": {
        "focus": "rapid stabilization, high-risk exclusion, and immediate disposition",
        "scope": "acute triage and initial diagnostic workup",
        "outside_scope": "definitive longitudinal specialty management",
    },
    "Family Medicine": {
        "focus": "broad longitudinal assessment and outpatient care continuity",
        "scope": "primary care management and referral coordination",
        "outside_scope": "highly specialized invasive diagnostics or procedures",
    },
    "Internal Medicine": {
        "focus": "multisystem medical evaluation and inpatient/outpatient management",
        "scope": "comprehensive medical assessment and treatment optimization",
        "outside_scope": "organ-specific procedural interventions",
    },
    "Cardiology": {
        "focus": "cardiac symptom assessment, risk stratification, and therapy adjustment",
        "scope": "cardiovascular diagnostics and medical management",
        "outside_scope": "non-cardiac etiologies requiring other specialty expertise",
    },
    "Pulmonology": {
        "focus": "respiratory symptom interpretation and pulmonary diagnostics",
        "scope": "lung-focused workup and treatment",
        "outside_scope": "non-pulmonary primary pathology management",
    },
    "Oncology": {
        "focus": "cancer-directed treatment planning and response monitoring",
        "scope": "oncologic systemic therapy and surveillance planning",
        "outside_scope": "non-oncologic primary disease management",
    },
    "General Surgery": {
        "focus": "operative indications, perioperative risk, and post-op recovery",
        "scope": "surgical decision-making and procedural management",
        "outside_scope": "non-surgical chronic disease management",
    },
    "Radiology": {
        "focus": "imaging interpretation with differential possibilities",
        "scope": "diagnostic imaging findings and recommendations",
        "outside_scope": "direct medication management or bedside treatment decisions",
    },
}


def specialty_guidance_for(specialty: str) -> str:
    profile = SPECIALTY_PROFILES.get(specialty)
    if not profile:
        return (
            "Focus on realistic documentation for the stated specialty, stay within scope, "
            "and recommend referral/workup when uncertainty exceeds your specialty domain."
        )

    return (
        f"Specialty focus: {profile['focus']}. "
        f"In-scope authority: {profile['scope']}. "
        f"Out-of-scope boundary: {profile['outside_scope']}. "
        "If findings are inconclusive or outside scope, explicitly document uncertainty and "
        "recommend next-step follow-up or referral."
    )
