# Agentic framework for note generation

The purpose of this phase is to design a framework wherein a team of agents can work in concert to build out a clinical case.


## Case construction process

1. A case will begin with a set of clinical variables from which the clinical symptoms and phenotypes will be derived. The case will receive a diagnostic difficulty:
- "easy": the case is straightforward and easily diagnosable
- "medium": can be diagnosed if the right tests are performed, but may take a longer time/more visits. Sometimes, these may go undiagnosed.
- "hard": symptoms may mask as another disease, may be mild or vague, will take a number of visits or may go undiagnosed in the timeframe.
Important note: difficult to diagnose is not the same as difficult to treat. Some easily diagnosed cases might be difficult to treat and vice versa.
2. A timeline of clinical visits is constructed by the Orchestrator, each containing:
    - Date of visit
    - Clinician specialty
    - Reason for visit (e.g. symptoms, phenotypes, follow-ups, prescribed treatments from previous visits, etc.)
    - Rich patient state: symptoms, vitals, medications, known conditions, allergies
    - Visit scenario: a full narrative of what happens during the encounter (exam, tests, results, treatment, patient response)
    - Disease progression notes for internal tracking
3. The Coordinator filters each visit's rich data, stripping diagnosis references to produce a diagnosis-free assignment for the Clinician.
4. The clinician only receives the filtered visit assignment (including the visit scenario) and a summary medical history. They do not receive the underlying disease information.
4. The clinician will write a note that captures the outcomes of the visit and any recommendations for future interventions, if applicable.
5. The Scribe updates the patient's medical history summary after each visit.

Additional information:
- The course of the case should follow the progress of the underlying disease or illness.
- Some cases will involve acute illness that are resolved relatively quickly.
- Chronic cases should progress naturally throughout the timeline.
- Some cases will be successfully resolved through intervention (e.g. medication, treatment, surgery, etc.).
- Some cases will not be successfully treated and will continue to worsen.
- Over the course of a case, not all visits must involve the main illness. This will be especially true for acute illnesses/injuries or chronic diseases that are easily managed, but these visits can also occur for patients with a difficult, chronic illness (e.g. an acute injury)


## Visit scenario concept

The Orchestrator generates a **visit scenario** for each visit — a narrative description of the full encounter including examination, tests ordered, results, treatments administered, and patient response. This scenario contains diagnosis context (the Orchestrator knows the diagnosis).

The Coordinator then filters this scenario to remove diagnosis references before passing it to the Clinician. This gives the Clinician rich encounter context while maintaining the information barrier.

**Information barrier**: `disease_progression_notes` on the Visit are never forwarded to the VisitAssignment or Clinician. The Coordinator explicitly strips diagnosis terms from the visit scenario, symptoms, examination findings, test results, treatments, and patient response.


## Clinical note contents

Each visit note will contain the following information:
- A brief patient history/case summarization
- The patient's current symptoms and/or phenotypes
- Standard vital measurements (if applicable)
- Pertinent diagnostic testing/imaging
- Prior and newly prescribed medications/therapies
- Future care recommendations

Notes should be formatted as follows:
- Notes will be mostly written as free text.
- Some use of lists or other formatting is allowed, but avoid overuse.
- Notes should be written in the voice of the clinician assigned to the visit.


## Agent roles

The agent team will be comprised of the following roles:
- **Narrator**: The Narrator composes the narrative of the clinical timeline.
- **Orchestrator**: The Orchestrator builds the case timeline from the narrative with rich clinical detail. For each visit, it assigns the full patient state (symptoms, vitals, medications, conditions), plans the visit scenario (what happens during the encounter), and tracks disease progression. It maintains medical continuity across visits (e.g., medications prescribed in visit N appear in visit N+1).
- **Scribe**: The Scribe keeps the patient medical history and updates it after each visit. It integrates new findings, medications, and test results while maintaining the information barrier (no differential diagnoses in the history).
- **Coordinator**: The Coordinator filters rich visit data for diagnosis removal. It receives the fully detailed Visit (with visit scenario and disease progression notes) and strips all diagnosis references to produce a clean VisitAssignment for the Clinician.
- **Clinician**: The Clinician conducts the visit and composes the clinical notes. Clinicians are given a specialization by the Coordinator based on the nature of visit (e.g. general practitioner, radiologist, oncologist, surgeon, etc.) They write from the visit scenario and assignment without knowledge of the underlying diagnosis.


## Pipeline flow

```
[NARRATOR] ──→ narrative
[ORCHESTRATOR] ──→ Timeline with rich Visit objects (patient state + visit scenario per visit)

FOR EACH Visit:
  [COORDINATOR] ──→ VisitAssignment (filters diagnosis from rich Visit data)
       │
       ▼
  [CLINICIAN] ──→ ClinicalNote (writes note from visit scenario)
       │
       ▼
  [SCRIBE] ──→ Updated MedicalHistorySummary
```
