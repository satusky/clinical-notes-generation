from enum import StrEnum

from pydantic import BaseModel, Field


class KnowledgeSourceType(StrEnum):
    WEB_URL = "web_url"
    LOCAL_FILE = "local_file"
    LOCAL_DIRECTORY = "local_directory"


class KnowledgeSource(BaseModel):
    source_type: KnowledgeSourceType
    location: str = Field(description="URL or file/directory path")
    description: str | None = Field(default=None, description="Optional description of the source")


class CaseSeed(BaseModel):
    """Minimal user input to kick off case construction."""

    raw_variables: dict[str, str] = Field(
        description="Arbitrary variable name/value pairs (e.g. NAACCR codes)"
    )
    coding_system: str | None = Field(
        default=None, description="Label for the coding system (e.g. NAACCR, ICD-10)"
    )
    age: int | None = Field(default=None, ge=0, le=120, description="Patient age (optional)")
    sex: str | None = Field(default=None, description="Patient sex M/F (optional)")
    difficulty: str = Field(default="medium", description="easy, medium, or hard")
    case_type: str = Field(default="acute", description="acute or chronic")
    intended_outcome: str = Field(default="resolved", description="resolved/improving/worsening/undiagnosed")
    knowledge_sources: list[KnowledgeSource] = Field(
        default_factory=list, description="Optional knowledge sources for investigation"
    )


class VariableAssignment(BaseModel):
    """A single variable assigned to an Investigator."""

    variable_name: str = Field(description="Name of the clinical variable to investigate")
    investigation_focus: str = Field(description="What the investigator should focus on")
    raw_value: str = Field(default="", description="The coded value to interpret (e.g. C34.1)")
    coding_system: str | None = Field(
        default=None, description="Coding system label, inherited from seed"
    )
    relevant_sources: list[int] = Field(
        default_factory=list, description="Indices into the seed's knowledge_sources list"
    )
    raw_variables: dict[str, str] | None = Field(
        default=None, description="All raw variables from the seed, for cross-reference"
    )


class InvestigationPlan(BaseModel):
    """The Constructor's plan for decomposing a condition into variables."""

    variables: list[VariableAssignment] = Field(description="Variables to investigate")
    suggested_age: int = Field(ge=0, le=120, description="Suggested patient age")
    suggested_sex: str = Field(description="Suggested patient sex (M/F)")


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InvestigatorReport(BaseModel):
    """Structured output from an Investigator's research."""

    variable_name: str = Field(description="The variable that was investigated")
    variable_value: str = Field(description="The determined value for this variable")
    associated_symptoms: list[str] = Field(default_factory=list)
    associated_comorbidities: list[str] = Field(default_factory=list)
    associated_risk_factors: list[str] = Field(default_factory=list)
    phenotypic_features: list[str] = Field(default_factory=list)
    prognosis_notes: str | None = Field(default=None)
    treatment_considerations: list[str] = Field(default_factory=list)
    clinical_staging: str | None = Field(default=None)
    source_summary: str = Field(default="", description="Summary of sources consulted")
    confidence: Confidence = Confidence.MEDIUM
