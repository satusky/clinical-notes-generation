"""Transform a case dict into a self-contained HTML string."""

from html import escape

from .template import TEMPLATE


def render_case(case: dict) -> str:
    """Main entry point: case dict -> complete HTML string."""
    return TEMPLATE.format(
        case_id=escape(case.get("case_id", "unknown")),
        header=_render_header(case),
        narrative=_render_narrative(case.get("narrative")),
        visit_tabs=_render_visit_tabs(case.get("timeline", [])),
        visit_panels=_render_visit_panels(case.get("timeline", [])),
        final_history=_render_final_history(case.get("final_medical_history")),
    )


# -- Header ------------------------------------------------------------------


def _render_header(case: dict) -> str:
    cv = case.get("clinical_variables", {})
    condition = escape(cv.get("primary_condition", "Unknown condition"))
    sex_label = {"M": "Male", "F": "Female"}.get(cv.get("sex", ""), cv.get("sex", ""))
    age = cv.get("age", "?")
    subtitle = f"{condition} | {sex_label}, {age}"

    difficulty = case.get("difficulty", "")
    case_type = case.get("case_type", "")
    outcome = case.get("intended_outcome", "")

    badges = []
    for val in (difficulty, case_type, outcome):
        if val:
            css = f"badge-{escape(val)}"
            badges.append(f'<span class="badge {css}">{escape(val)}</span>')
    badges_html = f'<div class="badges">{"".join(badges)}</div>' if badges else ""

    meta_lines = []
    comorbidities = cv.get("comorbidities", [])
    if comorbidities:
        meta_lines.append(f"Comorbidities: {escape(', '.join(comorbidities))}")
    risk_factors = cv.get("risk_factors", [])
    if risk_factors:
        meta_lines.append(f"Risk Factors: {escape(', '.join(risk_factors))}")
    meta_html = "".join(f'<div class="meta-line">{m}</div>' for m in meta_lines)

    case_id = escape(case.get("case_id", "unknown"))
    return (
        f'<div class="case-header">'
        f"<h1>Case: {case_id}</h1>"
        f'<div class="subtitle">{subtitle}</div>'
        f"{badges_html}"
        f"{meta_html}"
        f"</div>"
    )


# -- Narrative ----------------------------------------------------------------


def _render_narrative(narrative: str | None) -> str:
    if not narrative:
        return ""
    preview = escape(narrative[:120]).replace("\n", " ") + "..."
    body = _paragraphs(narrative)
    return (
        f"<details>"
        f'<summary>Narrative <span class="preview-text">{preview}</span></summary>'
        f'<div class="section-body">{body}</div>'
        f"</details>"
    )


# -- Visit tabs & panels -----------------------------------------------------


def _render_visit_tabs(timeline: list[dict]) -> str:
    if not timeline:
        return ""
    buttons = []
    for i, visit in enumerate(timeline):
        num = visit.get("visit_number", i + 1)
        active = " active" if i == 0 else ""
        buttons.append(f'<button class="{active}">Visit {num}</button>')
    return (
        f'<div class="tab-bar">{"".join(buttons)}</div>'
        f'<div class="keyboard-hint">Use left/right arrow keys to navigate visits</div>'
    )


def _render_visit_panels(timeline: list[dict]) -> str:
    if not timeline:
        return '<div class="visit-panels"><div class="visit-panel active"><span class="na">(no visits)</span></div></div>'
    panels = [_render_visit_panel(v, i) for i, v in enumerate(timeline)]
    return f'<div class="visit-panels">{"".join(panels)}</div>'


def _render_visit_panel(visit: dict, index: int) -> str:
    active = " active" if index == 0 else ""
    num = visit.get("visit_number", index + 1)
    date = escape(visit.get("visit_date", ""))
    specialty = escape(visit.get("clinician_specialty", ""))
    reason = escape(visit.get("reason_for_visit", ""))

    header = f"<h3>Visit {num} &mdash; {date}</h3>"
    meta_parts = []
    if specialty:
        meta_parts.append(specialty)
    if reason:
        meta_parts.append(f"Reason: {reason}")
    meta = f'<div class="visit-meta">{" | ".join(meta_parts)}</div>' if meta_parts else ""

    # Clinical note (expanded by default)
    note = visit.get("note")
    note_html = ""
    if note:
        note_html = (
            f'<details open><summary>Clinical Note</summary>'
            f'<div class="section-body"><div class="clinical-note">{escape(note)}</div></div>'
            f"</details>"
        )
    elif note is None:
        note_html = (
            f'<details><summary>Clinical Note</summary>'
            f'<div class="section-body"><span class="na">(not yet available)</span></div>'
            f"</details>"
        )

    # Sub-sections
    subs = []
    subs.append(_render_subsection("Symptoms", _render_pills(visit.get("symptoms", []))))
    subs.append(_render_subsection("Vitals", _render_vitals_table(visit.get("vitals", {}))))
    subs.append(_render_subsection("Examination Findings", _render_list(visit.get("examination_findings", []))))
    subs.append(_render_subsection("Tests Ordered", _render_list(visit.get("tests_ordered", []))))
    subs.append(_render_subsection("Test Results", _render_list(visit.get("test_results", []))))
    subs.append(_render_subsection("Treatments", _render_list(visit.get("treatments_administered", []))))
    subs.append(_render_subsection("Patient Response", _render_text(visit.get("patient_response", ""))))
    subs.append(_render_subsection("Known Conditions", _render_pills(visit.get("known_conditions", []))))
    subs.append(_render_subsection("Current Medications", _render_list(visit.get("current_medications", []))))
    subs.append(_render_subsection("Relevant History", _render_list(visit.get("relevant_history", []))))
    subs.append(_render_subsection("Visit Scenario", _render_text(visit.get("visit_scenario", ""))))
    subs.append(_render_subsection("Disease Progression", _render_text(visit.get("disease_progression_notes", ""))))

    subs_html = "".join(s for s in subs if s)

    return (
        f'<div class="visit-panel{active}">'
        f"{header}{meta}{note_html}{subs_html}"
        f"</div>"
    )


# -- Final medical history ----------------------------------------------------


def _render_final_history(history: dict | None) -> str:
    if not history:
        return ""

    parts = []

    demo = history.get("demographics", {})
    if demo:
        sex_label = {"M": "Male", "F": "Female"}.get(demo.get("sex", ""), demo.get("sex", ""))
        items = [f"Age: {demo.get('age', '?')}", f"Sex: {sex_label}"]
        if demo.get("height"):
            items.append(f"Height: {escape(demo['height'])}")
        if demo.get("weight"):
            items.append(f"Weight: {escape(demo['weight'])}")
        parts.append(_render_subsection("Demographics", _render_pills(items)))

    parts.append(_render_subsection("Known Conditions", _render_pills(history.get("known_conditions", []))))
    parts.append(_render_subsection("Current Medications", _render_list(history.get("current_medications", []))))
    parts.append(_render_subsection("Allergies", _render_list(history.get("allergies", []))))

    summaries = history.get("prior_visit_summaries", [])
    if summaries:
        items_html = "".join(f"<li>{escape(s)}</li>" for s in summaries)
        parts.append(_render_subsection("Visit Summaries", f'<ul class="summary-list">{items_html}</ul>'))

    body = "".join(p for p in parts if p)
    return (
        f"<details>"
        f"<summary>Final Medical History</summary>"
        f'<div class="section-body">{body}</div>'
        f"</details>"
    )


# -- Helpers ------------------------------------------------------------------


def _render_subsection(title: str, content: str) -> str:
    """Collapsible sub-section. Returns empty string if content is empty."""
    if not content:
        return ""
    return (
        f"<details>"
        f"<summary>{escape(title)}</summary>"
        f'<div class="section-body">{content}</div>'
        f"</details>"
    )


def _render_vitals_table(vitals: dict[str, str]) -> str:
    if not vitals:
        return ""
    rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>" for k, v in vitals.items()
    )
    return f'<table class="vitals-table">{rows}</table>'


def _render_list(items: list[str]) -> str:
    if not items:
        return ""
    li = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="item-list">{li}</ul>'


def _render_pills(items: list[str]) -> str:
    if not items:
        return ""
    pills = "".join(f'<span class="pill">{escape(item)}</span>' for item in items)
    return f'<div class="pill-list">{pills}</div>'


def _render_text(text: str) -> str:
    if not text:
        return ""
    return _paragraphs(text)


def _paragraphs(text: str) -> str:
    """Convert text to HTML paragraphs, splitting on blank lines."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paras:
        return ""
    return "".join(f"<p>{escape(p)}</p>" for p in paras)
