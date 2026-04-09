from pydantic import BaseModel, Field


class PatientDemographics(BaseModel):
    age: int = Field(ge=0, le=120)
    sex: str
    height: str | None = None
    weight: str | None = None


class SymptomState(BaseModel):
    symptom: str
    onset_date: str | None = None
    severity: str | None = None
    trend: str | None = Field(default=None, description="improving | stable | worsening")
    status: str = Field(default="active", description="active | resolved")
    last_observed_visit: int | None = None


class MedicationCourse(BaseModel):
    medication: str
    dose: str | None = None
    frequency: str | None = None
    status: str = Field(default="active", description="active | held | discontinued | completed")
    indication: str | None = None
    start_date: str | None = None
    planned_duration: str | None = None
    planned_end_date: str | None = None
    stop_reason: str | None = None
    adherence_notes: str | None = None
    side_effects: list[str] = Field(default_factory=list)
    last_updated_visit: int | None = None


class DiagnosticWorkup(BaseModel):
    workup_name: str
    status: str = Field(default="ordered", description="ordered | pending | resulted | inconclusive")
    ordered_date: str | None = None
    resulted_date: str | None = None
    key_findings: str | None = None
    certainty: str | None = Field(
        default=None, description="definitive | suggestive | inconclusive | conflicting"
    )
    next_step: str | None = None
    last_updated_visit: int | None = None


class ClinicalQuestion(BaseModel):
    question: str
    status: str = Field(default="open", description="open | resolved | deferred")
    opened_visit: int | None = None
    last_updated_visit: int | None = None
    plan: str | None = None


class FollowUpTask(BaseModel):
    task: str
    status: str = Field(default="pending", description="pending | completed | missed | deferred")
    due_date: str | None = None
    origin_visit: int | None = None
    completion_visit: int | None = None
    notes: str | None = None


class MedicalHistorySummary(BaseModel):
    demographics: PatientDemographics
    known_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    prior_visit_summaries: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)

    # Structured longitudinal state (diagnosis-free)
    active_symptoms: list[SymptomState] = Field(default_factory=list)
    medication_courses: list[MedicationCourse] = Field(default_factory=list)
    diagnostic_workups: list[DiagnosticWorkup] = Field(default_factory=list)
    open_clinical_questions: list[ClinicalQuestion] = Field(default_factory=list)
    follow_up_tasks: list[FollowUpTask] = Field(default_factory=list)
