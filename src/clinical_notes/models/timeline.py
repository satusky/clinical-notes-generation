from pydantic import BaseModel, Field


class Visit(BaseModel):
    visit_number: int = Field(ge=1)
    visit_date: str = Field(description="Date of the visit (YYYY-MM-DD)")
    clinician_specialty: str = Field(description="Specialty of the clinician for this visit")
    reason_for_visit: str = Field(description="Chief complaint / reason for visit")
    is_related_to_main_illness: bool = Field(
        description="Whether this visit is related to the primary condition"
    )
    note: str | None = Field(default=None, description="Clinical note (populated by Clinician)")

    # Rich clinical fields (populated by Orchestrator)
    patient_age: int = Field(default=0, description="Age at time of visit")
    patient_sex: str = Field(default="", description="Patient sex")
    symptoms: list[str] = Field(default_factory=list, description="Symptoms at presentation")
    vitals: dict[str, str] = Field(default_factory=dict, description="Vitals at presentation")
    relevant_history: list[str] = Field(
        default_factory=list, description="History items relevant to this visit"
    )
    known_conditions: list[str] = Field(
        default_factory=list, description="Conditions known at time of visit"
    )
    current_medications: list[str] = Field(
        default_factory=list, description="Medications at time of visit"
    )
    allergies: list[str] = Field(default_factory=list)
    visit_scenario: str = Field(
        default="",
        description="Narrative description of the encounter (exam, tests, results, treatment, patient response). Contains diagnosis context.",
    )
    examination_findings: list[str] = Field(
        default_factory=list, description="Physical exam findings"
    )
    tests_ordered: list[str] = Field(
        default_factory=list, description="Labs/imaging ordered during visit"
    )
    test_results: list[str] = Field(
        default_factory=list, description="Results available at this visit"
    )
    treatments_administered: list[str] = Field(
        default_factory=list, description="Treatments given during visit"
    )
    patient_response: str = Field(default="", description="Response to prior treatments")
    disease_progression_notes: str = Field(
        default="",
        description="Internal disease state tracking (diagnosis-laden, never sent to Clinician)",
    )


class Timeline(BaseModel):
    case_id: str
    visits: list[Visit] = Field(default_factory=list)


class VisitAssignment(BaseModel):
    """Filtered visit info sent to the Clinician — no diagnosis included."""

    visit_number: int
    visit_date: str
    clinician_specialty: str
    reason_for_visit: str
    patient_age: int
    patient_sex: str
    symptoms: list[str] = Field(default_factory=list)
    relevant_history: list[str] = Field(default_factory=list)
    vitals: dict[str, str] = Field(default_factory=dict)
    known_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    prior_visit_summaries: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)

    # Visit scenario fields (populated by Coordinator from rich Visit data)
    visit_scenario: str = Field(default="", description="Diagnosis-free encounter script")
    examination_findings: list[str] = Field(default_factory=list)
    tests_ordered: list[str] = Field(default_factory=list)
    test_results: list[str] = Field(default_factory=list)
    treatments_administered: list[str] = Field(default_factory=list)
    patient_response: str = Field(default="")
