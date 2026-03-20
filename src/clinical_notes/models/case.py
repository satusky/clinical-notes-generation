from enum import StrEnum

from pydantic import BaseModel, Field


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CaseOutcome(StrEnum):
    RESOLVED = "resolved"
    IMPROVING = "improving"
    WORSENING = "worsening"
    UNDIAGNOSED = "undiagnosed"


class CaseType(StrEnum):
    ACUTE = "acute"
    CHRONIC = "chronic"


class ClinicalVariables(BaseModel):
    primary_condition: str = Field(description="The underlying diagnosis / primary condition")
    comorbidities: list[str] = Field(default_factory=list, description="Co-existing conditions")
    age: int = Field(ge=0, le=120, description="Patient age in years")
    sex: str = Field(description="Patient sex (M/F)")
    risk_factors: list[str] = Field(default_factory=list, description="Relevant risk factors")


class CaseConfig(BaseModel):
    case_id: str = Field(description="Unique case identifier")
    clinical_variables: ClinicalVariables
    difficulty: Difficulty = Difficulty.MEDIUM
    case_type: CaseType = CaseType.ACUTE
    intended_outcome: CaseOutcome = CaseOutcome.RESOLVED
    narrative: str | None = Field(default=None, description="Full narrative (set by Narrator)")
