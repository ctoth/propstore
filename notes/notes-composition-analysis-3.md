# Composition Analysis — Session 3 Notes

**Date:** 2026-03-18
**Goal:** Read paper notes + code, think about what needs hooking up to make propstore live up to its potential.

## What I've read so far

### Notes files (root)
All 9 notes-*.md files + notes.md read. Key takeaways:

1. **notes-grok-and-integration.md** — Most relevant. Maps the full architecture:
   - Data model: Concepts (YAML) → Claims (5 types) → Forms → Conflicts (Z3-detected)
   - Pipeline: validate → build SQLite sidecar → WorldModel reasoner
   - WorldModel: value_of, derived_value, resolve, bind, hypothetical, chain_query, sensitivity, graph export
   - CEL type system for conditions
   - `pks import-papers` bridge exists but **claims.yaml doesn't exist in any paper dir yet**
   - 5 integration points identified: claims.yaml generator, concept discovery, form-aware extraction, cross-reference→stances, bidirectional FTS index

2. **notes-integration-plan.md** — Phases 0-7 all complete. Generator script + extract-claims skill built in research-papers-plugin.

3. **notes-world-model.md** — WorldModel fully implemented: value_of, derived_value, resolve, bind, hypothetical, chain_query. 39 tests.

4. **notes-modularize-world-model.md** — world/ subpackage extracted: types.py, resolution.py, model.py, bound.py, hypothetical.py. 530 tests.

5. **notes-domain-independence.md** — Removed hardcoded speech domain assumptions. kind field, condition labels, measure types, domain units all generalized.

6. **notes-algorithm-claims.md** — New claim type `algorithm` with AST equivalence checking via ast-equiv. 544 tests.

7. **notes-features-5-7.md** — graph_export, sensitivity analysis, transitive conflicts + recompute_conflicts. 494 tests.

8. **notes.md** — Build history: schema/validation → sidecar compiler → Repository class → knowledge/ layout.

### Code structure (listed, not yet read)
- propstore/ — 31 .py files including world/ subpackage (5 files)
- tests/ — 20 test files
- schema/ — LinkML schemas + generated JSON Schema + Python dataclasses
- scripts/ — rename_package.py, verify_ast_equiv.py

### Papers directory
- 20 paper directories + index.md
- Have NOT yet read papers/index.md or any papers/*/notes.md

## Paper notes read so far (13 of 20)

### TMS lineage
1. **Doyle_1979_TruthMaintenanceSystem** — Original TMS. SL/CP justifications, in/out belief status, dependency-directed backtracking, nogoods, control patterns (defaults, sequences, equivalence classes). Single-context, binary beliefs.
2. **McAllester_1978_ThreeValuedTMS** — (read via index summary) Three-valued (true/false/unknown), clause-based, eliminates non-monotonic deps from Doyle.
3. **deKleer_1984_QualitativePhysicsConfluences** — Qualitative physics: confluences ({+,0,-}), component models, ENVISION. The APPLICATION that motivated the ATMS — multiple interpretations from constraint satisfaction need simultaneous tracking.
4. **deKleer_1986_AssumptionBasedTMS** — The ATMS itself. Labels (minimal env sets per datum), nogoods, contexts. Four invariants: consistency, soundness, completeness, minimality. Bit-vector environments, three-cache optimization. Eliminates backtracking/retraction.
5. **deKleer_1986_ProblemSolvingATMS** — Consumer architecture on top of ATMS. Scheduling (simplest-label-first), constraint language (PLUS/TIMES/AND/OR/ONEOF), control disjunctions for dependency-directed backtracking.
6. **Falkenhainer_1987_BeliefMaintenanceSystem** — BMS: extends TMS to continuous beliefs via Dempster-Shafer intervals [s,p]. Hard/invertible support links. Propagation-delta threshold. Complementary to ATMS (ATMS=multiple contexts, BMS=graded beliefs).

### AGM / belief revision
7. **Alchourron_1985_TheoryChange** — AGM postulates (K-1 through K-8 for contraction, K*1 through K*8 for revision). Partial meet contraction via remainder sets + selection functions. Levi/Harper identities. Representation theorems.
8. **Dixon_1993_ATMSandAGM** — PROVES ATMS context switching is behaviourally equivalent to AGM operations when entrenchment derived from ATMS justifications. 5 entrenchment levels. ATMS_to_AGM translation algorithm. Theorem 1: formal equivalence.
9. **Shapiro_1998_BeliefRevisionTMS** — (read via index summary) Surveys both TMS and AGM traditions, notes their near-complete isolation, proposes AGM-compliant SNeBR.

### Nonmonotonic reasoning / argumentation
10. **Reiter_1980_DefaultReasoning** — (read via index summary) Default logic: prerequisite/justification/consequent rules, extensions as fixed-point belief sets. Normal defaults guaranteed to have extensions.
11. **Dung_1995_AcceptabilityArguments** — Abstract argumentation frameworks (AR, attacks). Hierarchy: admissible → preferred → stable → grounded → complete extensions. Unifies default logic + defeasible reasoning + logic programming as special cases. Meta-interpreter: acc(X) ← ¬defeat(X); defeat(X) ← attack(Y,X), acc(Y).
12. **Pollock_1987_DefeasibleReasoning** — (read via index summary) Prima facie vs conclusive reasons, rebutting vs undercutting defeaters, warrant via iterative defeat levels. OSCAR implementation.

### Scientific communication / provenance
13. **Clark_2014_Micropublications** — Semantic model for claims + evidence + arguments + attribution. OWL ontology. Complexity spectrum from minimal statement+attribution to full cross-publication claim-evidence networks. Supports/challenges relations. Similarity groups + holotypes. Nine use cases across biomedical lifecycle.

### Still need to read
- Ginsberg_1985_Counterfactuals
- Greenberg_2009_CitationDistortions
- Groth_2010_AnatomyNanopublication
- Martins_1983_MultipleBeliefSpaces
- Martins_1988_BeliefRevision
- McDermott_1983_ContextsDataDependencies
- Verheij_2003_ArtificialArgumentAssistants

## Code read
- world/model.py — WorldModel class: lazy Z3 solver, unbound queries (get_concept, claims_for, conflicts, search, stats), parameterization queries, stance graph (explain), bind(), chain_query()
- conflict_detector.py — ConflictClass enum (COMPATIBLE/PHI_NODE/CONFLICT/OVERLAP/PARAM_CONFLICT), Z3-based disjointness testing, algorithm claim AST comparison
- propagation.py — SymPy evaluation for parameterization (bare expr substitution, Eq solving, self-ref handling)
- validate_claims.py — Full claim validation pipeline: JSON Schema + compiler contract checks per type (parameter/equation/observation/model/measurement/algorithm), CEL condition checking, unit dimensional analysis
- build_sidecar.py — SQLite builder: concept/alias/relationship/parameterization/parameterization_group tables + FTS5 + claim/claim_stance/conflicts tables + claim FTS5
- cli/__init__.py — Click entry point with concept/claim/form/validate/build/query/export_aliases/import_papers/init/world commands
- cli/repository.py — Repository class: knowledge/ root, concepts_dir/claims_dir/forms_dir/sidecar_path, find() walks up to knowledge/
- claim.linkml.yaml — Full schema: 6 claim types, 4 stance types, provenance, variable bindings, fit statistics, parameter bindings

## Emerging picture so far
Will complete after reading remaining 7 paper notes.
