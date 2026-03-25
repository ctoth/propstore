# Paper: Doutre & Mailly 2018 — Constraints and Changes

## 2026-03-24

**GOAL:** Retrieve, read, and process "Constraints and changes: A survey of abstract argumentation dynamics" (Doutre & Mailly, 2018, DOI: 10.3233/AAC-180425).

**STATUS:** Step 3 — Writing output files (all pages read)

**DONE:**
- Step 1 complete: Paper retrieved via sci-hub (DDoS-Guard required browser download)
- PDF verified: 22 pages (26 page images), 254983 bytes, PDF 1.4
- Converted to 26 page images in pngs/
- All 26 pages read

**KEY OBSERVATIONS:**
- Survey paper on dynamics of abstract argumentation frameworks
- Three-component model: (1) AF structure, (2) semantics, (3) evaluation result
- Typology of constraints: structural, semantic, acceptability
- Typology of changes: structural (add/remove args/attacks), semantic (change semantics)
- Quality criteria for enforcement: minimality (structural, semantic, acceptability), postulates
- Covers: elementary changes (Cayrol/Lagasquie-Schiex), extension enforcement (Baumann, Wallner, Coste-Marquis), belief update/revision approaches, acceptability constraints, semantic constraints
- Tables 3-7 summarize all existing approaches across constraint/change/quality dimensions
- Key definitions: refinement/abstraction (Def 6), change operations (Def 7), enforcement operators
- Identifies gaps: semantic change quality understudied, combination of constraints underexplored, ranking-based semantics dynamics not studied
- Highly relevant to propstore: the constraint enforcement framework maps directly to how propstore handles competing extensions and policy enforcement

**FILES:**
- papers/Doutre_2018_ConstraintsChangesSurveyAbstract/paper.pdf
- papers/Doutre_2018_ConstraintsChangesSurveyAbstract/metadata.json
- papers/Doutre_2018_ConstraintsChangesSurveyAbstract/pngs/ — 26 page images

**DONE (continued):**
- notes.md, description.md, abstract.md, citations.md all written
- Reconciliation complete: 11 papers already in collection, 5 new leads, 3 conceptual links
- Backward annotation added to Cayrol_2014 notes
- index.md updated
- Two commits made

**NEXT:**
- Extract claims (Step 4 of paper-process) — create mode since no claims.yaml exists
- Write report (Step 5)
- This is a survey paper so claims will be mainly observations, mechanisms, comparisons, and limitations rather than parameters/equations
