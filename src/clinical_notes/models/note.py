from pydantic import BaseModel, Field


class MedicationAction(BaseModel):
    action: str = Field(description="start | continue | adjust | hold | stop | complete")
    medication: str
    dose: str | None = None
    frequency: str | None = None
    indication: str | None = None
    planned_duration: str | None = None
    planned_end_date: str | None = None
    stop_reason: str | None = None


class WorkupPlanAction(BaseModel):
    test_name: str
    status: str = Field(description="ordered | pending | resulted | inconclusive")
    certainty: str | None = Field(
        default=None, description="definitive | suggestive | inconclusive | conflicting"
    )
    interpretation: str | None = None
    next_step: str | None = None


class DiagnosticUncertainty(BaseModel):
    diagnosis: str
    confidence: str = Field(description="low | medium | high")
    rationale: str
    within_specialty_scope: bool = True
    recommended_referral: str | None = None


class ClinicalNote(BaseModel):
    visit_number: int = Field(ge=1)
    clinician_specialty: str
    note_date: str
    content: str = Field(description="Free-text clinical note")
    symptoms_reported: list[str] = Field(default_factory=list)
    vitals: dict[str, str] = Field(default_factory=dict)
    tests_ordered: list[str] = Field(default_factory=list)
    diagnoses_considered: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    follow_up_recommendations: list[str] = Field(default_factory=list)

    # Structured care-continuity outputs
    medication_actions: list[MedicationAction] = Field(default_factory=list)
    workup_plan_actions: list[WorkupPlanAction] = Field(default_factory=list)

    # Structured uncertainty/scope outputs
    diagnostic_uncertainty: list[DiagnosticUncertainty] = Field(default_factory=list)
    specialty_scope_statement: str = Field(default="")
