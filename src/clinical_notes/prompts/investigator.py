from ..models.investigation import KnowledgeSource, VariableAssignment

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


def naaccr_tool_instructions() -> str:
    """Return NAACCR-specific instructions for tool use."""
    return """\

NAACCR Investigation Instructions:
You have tools to look up information from reference sources. Use them strategically:

1. For JSON data dictionaries (LOCAL_FILE sources ending in .json):
   - Use `lookup_json_dict` to look up NAACCR items by their item number (e.g., key "400" \
for Primary Site, "522" for Histologic Type).
   - The key is the NAACCR item number as a string.

2. If the variable you are investigating depends on anatomical site (e.g., histology, staging, \
grade), first look up the primary site code from raw_variables in the data dictionary to \
determine the tissue type, then use that context to narrow your search.

3. For directory sources (LOCAL_DIRECTORY):
   - Use `search_files` to find relevant reference files.
   - Search for patterns related to the tissue type or variable (e.g., "*breast*" in a \
histology subdirectory when the primary site maps to breast tissue).
   - Then use `lookup_json_dict` on any JSON files you discover.

4. Always prefer tool lookups over general knowledge. Set confidence to "high" only when the \
code is found and unambiguous in reference material."""


def coding_system_instructions(coding_system: str | None) -> str:
    """Return coding-system-specific tool instructions."""
    if coding_system == "NAACCR":
        return naaccr_tool_instructions()
    return ""


def investigator_system_prompt(
    coding_system: str | None = None,
    use_tools: bool = False,
) -> str:
    """Build the investigator system prompt, optionally with tool instructions."""
    base = INVESTIGATOR_SYSTEM
    if use_tools:
        base += coding_system_instructions(coding_system)
    return base


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


def investigator_tool_user_prompt(
    assignment: VariableAssignment,
    knowledge_sources: list[KnowledgeSource],
    relevant_indices: list[int],
) -> str:
    """Build user prompt for tool-use path (sources listed, not embedded)."""
    raw_value_section = ""
    if assignment.raw_value:
        raw_value_section = f"\nRaw coded value: {assignment.raw_value}"

    coding_system_section = ""
    if assignment.coding_system:
        coding_system_section = f"\nCoding system: {assignment.coding_system}"

    raw_vars_section = ""
    if assignment.raw_variables:
        raw_vars_section = "\n\nAll raw variables from this case (for cross-reference):"
        for key, val in assignment.raw_variables.items():
            raw_vars_section += f"\n  {key}: {val}"

    sources_section = ""
    source_lines = []
    for idx in relevant_indices:
        if 0 <= idx < len(knowledge_sources):
            src = knowledge_sources[idx]
            desc = f" — {src.description}" if src.description else ""
            source_lines.append(f"  [{src.source_type.value}] {src.location}{desc}")
    if source_lines:
        sources_section = "\n\nAvailable reference sources (use tools to query them):\n"
        sources_section += "\n".join(source_lines)
        sources_section += "\n\nUse the lookup_json_dict and search_files tools to find "
        sources_section += "the information you need from these sources."

    return f"""\
Interpret the following coded clinical variable:

Variable: {assignment.variable_name}{raw_value_section}{coding_system_section}
Focus: {assignment.investigation_focus}{raw_vars_section}{sources_section}

Produce a detailed investigation report with the clinical meaning of this code."""
