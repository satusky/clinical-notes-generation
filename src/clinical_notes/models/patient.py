from pydantic import BaseModel, Field


class PatientDemographics(BaseModel):
    age: int = Field(ge=0, le=120)
    sex: str
    height: str | None = None
    weight: str | None = None


class MedicalHistorySummary(BaseModel):
    demographics: PatientDemographics
    known_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    prior_visit_summaries: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
