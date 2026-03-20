from ..models.investigation import VariableAssignment

INVESTIGATOR_SYSTEM = """\
You are a clinical coding investigator. Your role is to interpret a coded value from a clinical \
coding system by consulting reference documents.

Given a variable name and its raw coded value, look up the code in the provided reference material \
and produce a structured report including:
- The human-readable clinical meaning of the coded value
- Associated symptoms that would present with this finding
- Related comorbidities commonly seen alongside it
- Relevant risk factors
- Phenotypic features observable in the patient
- Prognosis implications
- Treatment considerations
- Clinical staging if applicable

Your confidence level should reflect how the code was resolved:
- high: code was found in the reference material and the meaning is unambiguous
- medium: code was partially matched or the reference material was incomplete
- low: code was not found in the reference material; interpretation relies on general knowledge
"""


def investigator_user_prompt(
    assignment: VariableAssignment,
    source_content: str | None = None,
) -> str:
    raw_value_section = ""
    if assignment.raw_value:
        raw_value_section = f"\nRaw coded value: {assignment.raw_value}"

    coding_system_section = ""
    if assignment.coding_system:
        coding_system_section = f"\nCoding system: {assignment.coding_system}"

    sources_section = ""
    if source_content:
        sources_section = f"""

Reference material:
{source_content}

Look up the coded value in the above reference material. If the code is found, use the \
reference definition. If not found, fall back on general clinical knowledge but set \
confidence to low."""

    return f"""\
Interpret the following coded clinical variable:

Variable: {assignment.variable_name}{raw_value_section}{coding_system_section}
Focus: {assignment.investigation_focus}{sources_section}

Produce a detailed investigation report with the clinical meaning of this code."""
