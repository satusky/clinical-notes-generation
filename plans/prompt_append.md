ADDITIONAL INSTRUCTIONS FOR SYNTHETIC CLINICAL NOTE QUALITY

Apply the following as mandatory quality constraints on top of all prior instructions.

Generate the case and notes exactly as previously instructed, but also satisfy all of the following quality constraints. These constraints override any tendency toward generic, overly polished, or internally inconsistent note generation.

1. GLOBAL CASE CONSISTENCY
- A single source of truth must be maintained across the entire case for:
  - age
  - sex
  - smoking history
  - quit date
  - pack-years
  - comorbidities
  - allergies
  - medication list
  - tumor size
  - diagnosis
  - stage
  - procedure dates
  - treatment regimen
  - follow-up intervals
- Once a fact is established, it must not change unless the note explicitly documents the change and explains why.
- Structured fields and free-text note content must agree with each other.
- Do not allow contradictions such as different smoking histories, conflicting medication lists, inconsistent staging, or mismatched dates across visits. 

2. TIMELINE ACCURACY
- Every note must reflect only the information available at that point in time.
- Do not place POD2 labs, POD5 oxygen-weaning plans, discharge status, and POD0 recovery language in the same note unless the note is explicitly written as a retrospective discharge summary.
- Maintain realistic elapsed time between visits, procedures, recovery milestones, and surveillance imaging.
- Ensure that relative time expressions such as “5 months later” match the actual dates in the case timeline. 

3. SPECIALTY-SPECIFIC VOICE
- Each note must sound like it was written by the listed specialty, not by a generic narrator.
- Pulmonary Medicine notes should focus on respiratory symptoms, inhaler use, pulmonary differentials, and stepwise evaluation.
- Thoracic Oncology notes should focus on staging, pathology interpretation, treatment options, systemic therapy planning, and prognosis discussion.
- Interventional Radiology notes should be concise and procedure-focused, emphasizing indication, consent, technical details, immediate complications, and post-procedure instructions.
- Anesthesiology notes should focus on perioperative risk, airway/pulmonary/cardiac assessment, anesthesia planning, and operative clearance.
- Thoracic Surgery notes should focus on operative course, postoperative recovery, chest tubes or oxygen needs if applicable, complications, pathology review, and surgical follow-up.
- Avoid repeating the same counseling boilerplate across all specialties. 

4. REALISM OVER POLISH
- The notes should feel clinically plausible, not literary.
- Avoid overexplaining obvious findings.
- Avoid excessive narrative prose, dramatic storytelling, or polished “textbook” summaries unless the note type specifically calls for it.
- Prefer realistic clinic-style documentation over elegant prose.
- Include uncertainty where appropriate. Clinicians should sometimes document concern, suspicion, or differential reasoning rather than acting as if the final diagnosis is already known.

5. APPROPRIATE COMPLETENESS
- Include only the sections that would realistically appear in that specialty note.
- Do not automatically include vaccination counseling, smoking cessation counseling, nutrition advice, and broad chronic disease management in every note unless clinically relevant for that encounter.
- Interventional and postoperative notes should not read like primary-care annual wellness visits.
- Follow-up plans should be targeted to the visit purpose.

6. CLINICAL REASONING
- Each note should contain an assessment and plan that logically follow from the symptoms, findings, and tests available at that visit.
- Differential diagnoses should be plausible for that specialty and visit context.
- If a cancer workup is underway, the progression from symptom evaluation to imaging to biopsy to staging to treatment should be clinically coherent.
- Treatment choices should be clinically plausible and consistent with the documented stage and patient status.

7. STRUCTURED-TO-TEXT ALIGNMENT
- The following must match between structured output and free text:
  - medications
  - allergies
  - tests ordered
  - test results
  - diagnoses considered
  - follow-up recommendations
- Do not generate a structured medication list showing active medications while the note text says no medications are listed, or similar mismatches. 

8. LONGITUDINAL STATE TRACKING
- Before writing each note, review all prior visits and maintain continuity of:
  - unresolved symptoms
  - workup already completed
  - pending studies
  - medication changes
  - post-procedure status
  - patient response to treatment
- If a symptom resolves, state that clearly and do not keep documenting it as active without explanation.

9. REQUIRED REALISM ELEMENTS
Where appropriate for the case and specialty, incorporate:
- relevant smoking chronology
- pertinent family/social history
- functional status
- symptom duration and progression
- pertinent negatives
- rationale for next-step testing or treatment
- realistic postoperative milestones if surgery has occurred
These should be included selectively and naturally, not as a checklist dump.

10. SELF-CHECK BEFORE FINALIZING
Before returning the case, silently verify:
- no contradictory smoking history
- no contradictory medication list
- no contradictory stage or diagnosis
- no timeline mismatch
- no note containing future knowledge unavailable at that visit
- no specialty note written in a generic voice
- no unnecessary boilerplate repeated across all notes
If any inconsistency is found, revise the output before returning it.

OUTPUT GOAL
Produce notes that are internally consistent, temporally coherent, specialty-specific, clinically plausible, and suitable for hackathon use in tasks such as summarization, extraction, temporal reasoning, and chart review simulation.