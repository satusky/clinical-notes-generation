from pydantic import BaseModel, Field


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
