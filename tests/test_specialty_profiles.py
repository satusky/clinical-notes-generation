from src.clinical_notes.prompts.specialty_profiles import specialty_guidance_for


def test_specialty_guidance_known_specialty():
    guidance = specialty_guidance_for("Emergency Medicine")
    assert "rapid stabilization" in guidance
    assert "Out-of-scope boundary" in guidance


def test_specialty_guidance_unknown_specialty():
    guidance = specialty_guidance_for("Unknown Specialty")
    assert "stay within scope" in guidance
