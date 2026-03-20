from ..models.investigation import CaseSeed, InvestigationPlan, InvestigatorReport

CONSTRUCTOR_PLAN_SYSTEM = """\
You are a clinical case construction planner specializing in oncology and complex medical cases.

Given a set of raw coded variables from a clinical coding system, plan how to interpret each code \
and build a realistic, detailed patient case. Your job is to assign investigators to look up what \
each coded value means using the provided reference documents.

For each coded variable:
- Assign an investigator to interpret the code using the reference material
- Specify the raw coded value so the investigator knows exactly what to look up
- Focus the investigation on translating the code into clinical meaning

If demographic variables are present in the raw variables (e.g. "Age at Diagnosis", "Sex"), \
extract them directly rather than spawning investigators for them.

If knowledge sources are provided, assign relevant source indices to variables that would benefit \
from them. Investigators should prioritize reference documents over general knowledge.

If the seed does not specify age or sex (either directly or via raw variables), suggest realistic \
demographics for the clinical context implied by the codes.
"""


def constructor_plan_prompt(seed: CaseSeed) -> str:
    variables_str = "\n".join(
        f"  {name}: {value}" for name, value in seed.raw_variables.items()
    )

    coding_system_str = ""
    if seed.coding_system:
        coding_system_str = f"\nCoding system: {seed.coding_system}"

    sources_str = ""
    if seed.knowledge_sources:
        source_lines = []
        for i, src in enumerate(seed.knowledge_sources):
            desc = src.description or src.location
            source_lines.append(f"  [{i}] {src.source_type.value}: {desc}")
        sources_str = "\nKnowledge sources:\n" + "\n".join(source_lines)

    demographics = ""
    if seed.age is not None:
        demographics += f"\nAge: {seed.age}"
    if seed.sex is not None:
        demographics += f"\nSex: {seed.sex}"

    return f"""\
Assign investigators to interpret the following raw coded variables and build a clinical case.

Raw variables:
{variables_str}{coding_system_str}
Difficulty: {seed.difficulty}
Case type: {seed.case_type}
Intended outcome: {seed.intended_outcome}{demographics}{sources_str}

For each variable, create a VariableAssignment with the variable name, the raw coded value, \
an investigation focus describing what to look up, and relevant knowledge source indices. \
The investigator should interpret what each code means clinically using the reference documents."""


CONSTRUCTOR_MERGE_SYSTEM = """\
You are a clinical case synthesizer. Given investigator reports that interpret raw coded variables, \
merge them into a single coherent CaseConfig.

You must:
- Derive a human-readable primary_condition from the interpreted codes (e.g. if investigators \
report that C34.1 means "upper lobe of lung" and 8070/3 means "squamous cell carcinoma", \
synthesize "Squamous Cell Carcinoma of the Upper Lobe of the Lung")
- Select medically plausible combinations of variables
- Resolve any conflicts between investigator findings
- Ensure the final case matches the specified difficulty, case type, and intended outcome
- Produce realistic comorbidities and risk factors appropriate for the demographics

The output must be a valid CaseConfig with all required fields populated.
"""


def constructor_merge_prompt(
    seed: CaseSeed,
    plan: InvestigationPlan,
    reports: list[InvestigatorReport],
) -> str:
    age = seed.age if seed.age is not None else plan.suggested_age
    sex = seed.sex if seed.sex is not None else plan.suggested_sex

    variables_str = "\n".join(
        f"  {name}: {value}" for name, value in seed.raw_variables.items()
    )

    coding_system_str = ""
    if seed.coding_system:
        coding_system_str = f"\nCoding system: {seed.coding_system}"

    reports_str = ""
    for report in reports:
        reports_str += f"\n--- {report.variable_name} ---\n"
        reports_str += f"Value: {report.variable_value}\n"
        reports_str += f"Confidence: {report.confidence.value}\n"
        if report.associated_symptoms:
            reports_str += f"Symptoms: {', '.join(report.associated_symptoms)}\n"
        if report.associated_comorbidities:
            reports_str += f"Comorbidities: {', '.join(report.associated_comorbidities)}\n"
        if report.associated_risk_factors:
            reports_str += f"Risk factors: {', '.join(report.associated_risk_factors)}\n"
        if report.phenotypic_features:
            reports_str += f"Phenotypic features: {', '.join(report.phenotypic_features)}\n"
        if report.prognosis_notes:
            reports_str += f"Prognosis: {report.prognosis_notes}\n"
        if report.treatment_considerations:
            reports_str += f"Treatment: {', '.join(report.treatment_considerations)}\n"
        if report.clinical_staging:
            reports_str += f"Staging: {report.clinical_staging}\n"
        if report.source_summary:
            reports_str += f"Sources: {report.source_summary}\n"

    return f"""\
Synthesize the following investigator reports into a unified CaseConfig.

Raw variables:
{variables_str}{coding_system_str}
Patient: {age}-year-old {sex}
Difficulty: {seed.difficulty}
Case type: {seed.case_type}
Intended outcome: {seed.intended_outcome}

Investigator Reports:
{reports_str}

Derive a human-readable primary_condition from the interpreted codes. Merge these findings \
into a coherent patient case. Select medically plausible combinations, resolve any conflicts, \
and ensure the case matches the specified constraints."""
