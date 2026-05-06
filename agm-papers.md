# AGM Paper Artifact Inventory

Checked from `C:\Users\Q\code\propstore` on 2026-05-06.

This inventory is for implementing the missing formal AGM and belief-dynamics
surfaces in `../belief-set`. Per the paper-reading rule, notes can guide
planning, but implementation-critical rereads should use page images directly.

## Minimum Paper Set

### Alchourron, Gärdenfors, Makinson 1985 — Theory Change

Purpose:

- AGM postulates
- partial-meet contraction
- remainder sets
- selection functions
- Levi and Harper identities

Found:

- `../belief-set/papers/Alchourron_1985_TheoryChange/abstract.md`
- `../belief-set/papers/Alchourron_1985_TheoryChange/citations.md`
- `../belief-set/papers/Alchourron_1985_TheoryChange/description.md`
- `../belief-set/papers/Alchourron_1985_TheoryChange/metadata.json`
- `../belief-set/papers/Alchourron_1985_TheoryChange/notes.md`

Missing for rigorous reread:

- `../belief-set/papers/Alchourron_1985_TheoryChange/paper.pdf`
- `../belief-set/papers/Alchourron_1985_TheoryChange/pngs/`
- page-image-backed verification of remainder-set and selection-function definitions

Also seen elsewhere:

- `../mongoose/propstore/papers/Alchourron_1985_TheoryChange/...` notes artifacts only.

### Gärdenfors and Makinson 1988 — Revisions of Knowledge Systems Using Epistemic Entrenchment

Purpose:

- epistemic entrenchment postulates
- contraction from entrenchment
- representation relationship between entrenchment and AGM contraction

Found:

- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/abstract.md`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/citations.md`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/claims.yaml`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/description.md`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/metadata.json`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md`

Missing for rigorous reread:

- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/paper.pdf`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/pngs/`
- page-image-backed verification of EE postulates and contraction bridge

Also seen elsewhere:

- `../mongoose/propstore/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/...` notes artifacts only.

### Grove 1988 — Two Modellings for Theory Change

Purpose:

- systems of spheres
- alternate semantic representation for AGM revision

Found:

- Citation references in:
  - `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/citations.md`
  - `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/citations.md`
- Gap notes in:
  - `docs/belief-set-revision.md`
  - `notes/cluster-c-belief-set-review-2026-04-26.md`

Missing:

- dedicated paper directory in `../belief-set/papers/`
- `paper.pdf`
- `pngs/`
- `abstract.md`
- `citations.md`
- `description.md`
- `metadata.json`
- `notes.md`
- implementation-focused reread of sphere construction and representation theorem

### Hansson 1989 / 1999 — Belief Dynamics And Base Contraction

Purpose:

- recovery critique
- safe contraction
- belief-base contraction families
- non-prioritized and base-revision surfaces

Found:

- Citation references in:
  - `papers/Baumann_2019_AGMContractionDung/citations.md`
  - `../argumentation/papers/Baumann_2019_AGMContractionDung/citations.md`
  - `../belief-set/papers/Alchourron_1985_TheoryChange/notes.md`
  - `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/citations.md`
- Gap notes in:
  - `docs/belief-set-revision.md`
  - `proposals/true-agm-revision-proposal.md`

Missing:

- dedicated Hansson paper directory in `../belief-set/papers/`
- `paper.pdf`
- `pngs/`
- `abstract.md`
- `citations.md`
- `description.md`
- `metadata.json`
- `notes.md`
- page-image-backed extraction of safe/base contraction definitions

### Darwiche and Pearl 1997 — On the Logic of Iterated Belief Revision

Purpose:

- DP iterated revision postulates
- epistemic states rather than belief sets
- revision over rankings/preorders

Found:

- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/abstract.md`
- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/citations.md`
- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/claims.yaml`
- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/description.md`
- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/metadata.json`
- `../gunray/papers/Darwiche_1997_LogicIteratedBeliefRevision/notes.md`
- reports and notes in current propstore, including:
  - `reports/paper-Darwiche_1997_LogicIteratedBeliefRevision.md`
  - `reports/revision-phase2-semantics-literature-check-2026-03-29.md`
  - `notes/paper-darwiche-pearl-1997.md`

Missing in `../belief-set`:

- dedicated `../belief-set/papers/Darwiche_1997_LogicIteratedBeliefRevision/`
- `paper.pdf`
- `pngs/`
- local `abstract.md`
- local `citations.md`
- local `claims.yaml`
- local `description.md`
- local `metadata.json`
- local `notes.md`

Notes:

- `notes/paper-darwiche-pearl-1997.md` says a PDF and page count were verified
  at `papers/Darwiche_1997_LogicIteratedBeliefRevision/paper.pdf`, but that
  path is not present in the current propstore checkout.

### Spohn 1988 — Ordinal Conditional Functions

Purpose:

- OCF/kappa epistemic state
- ranking invariants
- conditionalization dynamics
- concrete state representation for iterated revision

Found:

- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/abstract.md`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/citations.md`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/claims.yaml`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/description.md`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/metadata.json`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md`

Missing for rigorous reread:

- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/paper.pdf`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/pngs/`
- page-image-backed verification of OCF invariants and conditionalization definitions

Also seen elsewhere:

- `../mongoose/propstore/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/...` notes artifacts only.

### Booth and Meyer 2006 — Admissible and Restrained Revision

Purpose:

- admissible revision family
- restrained revision
- lexicographic revision contrast
- iterated-revision operator-selection guidance

Found:

- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/abstract.md`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/citations.md`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/claims.yaml`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/description.md`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/metadata.json`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/notes.md`
- `notes/booth-2006-processing.md`
- `reports/paper-Booth_2006_AdmissibleRestrainedRevision.md`

Missing for rigorous reread:

- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/paper.pdf`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/pngs/`
- page-image-backed verification of admissible-family and restrained-revision definitions

Also seen elsewhere:

- `../mongoose/propstore/papers/Booth_2006_AdmissibleRestrainedRevision/...` notes artifacts only.

### Konieczny and Pino Pérez 2002 — Merging Information Under Constraints

Purpose:

- IC merge postulates
- model-theoretic merge over constraints
- Sigma and arbitration-style operators

Found:

- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/abstract.md`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/citations.md`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/claims.yaml`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/description.md`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/metadata.json`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`

Missing for rigorous reread:

- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/paper.pdf`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/`
- page-image-backed verification of IC postulates and `Delta^Max`

Also seen elsewhere:

- `../mongoose/propstore/papers/Konieczny_2002_MergingInformationUnderConstraints/...` notes artifacts only.

## Supporting Propstore And AF Papers

These are not the core `../belief-set` AGM implementation set, but they are
relevant to propstore integration, ATMS support-incision, and AF revision.

### Dixon 1993 — ATMS and AGM

Purpose:

- ATMS/AGM bridge
- essential support and support-derived entrenchment intuition

Found in current propstore:

- `papers/Dixon_1993_ATMSandAGM/abstract.md`
- `papers/Dixon_1993_ATMSandAGM/citations.md`
- `papers/Dixon_1993_ATMSandAGM/description.md`
- `papers/Dixon_1993_ATMSandAGM/notes.md`
- `papers/Dixon_1993_ATMSandAGM/pngs/`

Missing:

- `papers/Dixon_1993_ATMSandAGM/paper.pdf` was not seen in the checked listing

### Bonanno 2007 — AGM Belief Revision in Temporal Logic

Purpose:

- branching-time / temporal logic framing
- relation between linear history and belief revision

Found in current propstore:

- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/abstract.md`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/citations.md`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/claims.yaml`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/description.md`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/metadata.json`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/notes.md`
- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/paper.pdf`

Missing:

- `papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/pngs/`

### Bonanno 2010 — Belief Change in Branching Time

Purpose:

- branch/history sensitivity
- PLS and branching belief change

Found in current propstore:

- `papers/Bonanno_2010_BeliefChangeBranchingTime/abstract.md`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/citations.md`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/claims.yaml`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/description.md`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/metadata.json`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/notes.md`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/paper.pdf`
- `papers/Bonanno_2010_BeliefChangeBranchingTime/pngs/`

Missing:

- none seen in the checked listing

### Rotstein 2008 — Argument Theory Change

Purpose:

- argumentation-level theory change
- downstream adapter/context for propstore argumentation revision

Found in current propstore:

- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/abstract.md`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/citations.md`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/claims.yaml`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/description.md`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/metadata.json`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/notes.md`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/paper.pdf`

Missing:

- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/pngs/`

### Baumann 2015 — AGM Meets Abstract Argumentation

Purpose:

- formal AF revision/expansion context
- downstream AF revision target in `../argumentation`

Found in `../argumentation`:

- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/abstract.md`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/citations.md`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/claims.yaml`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/description.md`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/metadata.json`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/notes.md`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/paper.pdf`
- `../argumentation/papers/Baumann_2015_AGMMeetsAbstractArgumentation/pngs/`

Missing:

- none seen in the checked listing

### Baumann 2019 — AGM Contraction and Dung

Purpose:

- AF contraction
- recovery critique in AF setting

Found in current propstore:

- `papers/Baumann_2019_AGMContractionDung/abstract.md`
- `papers/Baumann_2019_AGMContractionDung/citations.md`
- `papers/Baumann_2019_AGMContractionDung/claims.yaml`
- `papers/Baumann_2019_AGMContractionDung/description.md`
- `papers/Baumann_2019_AGMContractionDung/metadata.json`
- `papers/Baumann_2019_AGMContractionDung/notes.md`
- `papers/Baumann_2019_AGMContractionDung/provenance.md`

Also found in `../argumentation` with the same artifact shape.

Missing:

- `paper.pdf`
- `pngs/`

### Coste-Marquis et al. 2007 — Merging Dung's Argumentation Systems

Purpose:

- AF merge, separate from propositional IC merge

Found in `../argumentation`:

- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/abstract.md`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/citations.md`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/claims.yaml`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/description.md`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/metadata.json`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/notes.md`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/paper.pdf`
- `../argumentation/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/pngs/`

Missing:

- none seen in the checked listing

### Diller 2015 — Extension-Based Belief Revision

Purpose:

- AF extension revision
- faithful rankings over extensions

Found in `../argumentation`:

- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/abstract.md`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/citations.md`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/claims.yaml`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/description.md`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/Diller_2015_ExtensionBasedBeliefRevision.pdf`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/metadata.json`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/notes.md`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/pages/`
- `../argumentation/papers/Diller_2015_ExtensionBasedBeliefRevision/reports/`

Missing:

- `pngs/` directory was not seen, but `pages/` exists and should be checked
  before deciding whether page-image coverage is sufficient

### Cayrol 2014 — Change in Abstract Argumentation Frameworks

Purpose:

- grounded argument addition classification
- AF dynamics taxonomy

Found in `../argumentation`:

- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/abstract.md`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/citations.md`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/description.md`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/metadata.json`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/notes.md`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/paper.pdf`
- `../argumentation/papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/pngs/`

Missing:

- `claims.yaml` was not seen in the checked listing

## Immediate Retrieval / Repair Queue For `../belief-set`

To make `../belief-set` implementation-ready for full AGM work:

1. Add PDFs and page images for the five existing `../belief-set/papers/*`
   core directories:
   - `Alchourron_1985_TheoryChange`
   - `Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic`
   - `Spohn_1988_OrdinalConditionalFunctionsDynamic`
   - `Booth_2006_AdmissibleRestrainedRevision`
   - `Konieczny_2002_MergingInformationUnderConstraints`
2. Add a full `../belief-set/papers/Darwiche_1997_LogicIteratedBeliefRevision/`
   directory, preferably by retrieving or copying a page-image-backed version
   from a trustworthy local source.
3. Add Grove 1988 as a new `../belief-set/papers/` directory with notes and
   page images.
4. Add Hansson 1989 and/or Hansson 1999 as `../belief-set/papers/` directories
   with notes and page images.
5. For each added or repaired paper, verify that `notes.md` was derived from
   page images, not from text extraction alone.
