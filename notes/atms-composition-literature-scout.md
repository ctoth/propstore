# ATMS + Argumentation Composition Literature Scout Notes

**Date:** 2026-03-25
**Goal:** Read all papers referenced in the scout prompt, answer every question, write report to `reports/atms-composition-literature-requirements.md`.

## Papers Read

### 1. de Kleer 1986 (ATMS Fundamentals) - READ
- Labels: sets of minimal assumption sets supporting each datum (p.143-145)
- Nogoods: inconsistent assumption sets (p.143)
- Context = consistent environment (set of assumptions with no nogood subset) (p.145)
- Labels have four properties: consistency, soundness, completeness, minimality (pp.144-145)
- Four node categories: true (holds universally), in (holds in some context), out (holds in no known context), false (never holds) (pp.145-146)
- Bit-vector implementation for environments (p.157)

### 2. de Kleer 1986 (Problem Solving) - READ
- Consumer architecture: modular rules attached to ATMS nodes (p.201-202)
- Consumers run exactly once, no internal state (p.202)
- Scheduling: simplest-label-first (p.204)
- Control disjunctions for search partitioning (p.205)
- Constraint language (PLUS, TIMES, AND, OR, ONEOF) (pp.209-213)

### 3. Dixon 1993 (ATMS and AGM) - READ
- ATMS context switching = AGM expansion + contraction (p.534)
- ATMS_to_AGM algorithm translates justificational info to entrenchment (p.537)
- Five entrenchment levels E1-E5 suffice (p.536)
- Theorem 1: ATMS and AGM behaviorally equivalent under right entrenchment (p.538)
- Essential Support ES(p,E) = intersection of all foundational belief sets for p in E (p.537)

### 4. Odekerken 2023 (ASPIC+ Incomplete Info) - READ
- Four justification statuses: unsatisfiable, defended, out, blocked
- Stability: status won't change regardless of how queryables resolve (Def 13)
- Relevance: which queryables could change a literal's status (Def 15)
- Stability is coNP-complete, relevance is Sigma_2^P-complete (Prop 7, Thm 2)
- Grounded semantics only
- Queryables = unsettled literals whose truth value is unknown (Def 11)
- Future AT = possible state after resolving some queryables (Def 12)

### 5. Dung 1995 (AF Fundamentals) - READ
- AF = (AR, attacks) (Def 2, p.326)
- Admissible, preferred, stable, grounded, complete extensions
- Grounded = least fixpoint of characteristic function F_AF (Def 20, p.329)
- Characteristic function F_AF(S) = {A | A acceptable w.r.t. S} (Def 16, p.329)

### 6. ATMSEngine (propstore/world/atms.py) - PARTIALLY READ
- ATMSEngine wraps a BoundWorld, builds nodes/justifications/nogoods
- Key methods: claim_label(), supported_claim_ids(), node_status(), future_environments(), node_future_statuses()
- Has stability analysis and relevance via bounded replay of future bound worlds
- Docstring says: "bounded ATMS-native analysis over rebuilt future bound worlds rather than AGM-style revision"

### 7. resolution.py - READ FULLY
- ATMS backend: _resolve_atms_support() at line 310-326
- Simply checks engine.supported_claim_ids() & target_ids
- Returns winner if exactly one claim is ATMS-supported
- NO argumentation involved - just ATMS label check
- Other backends: claim_graph, structured_projection, praf - all do argumentation but NO ATMS

## Key Observation: The Gap
The ATMS backend and argumentation backends are ALTERNATIVES in resolution.py, not composed. The ATMS backend only checks support labels. The argumentation backends only check defeat/extension membership. Nobody asks "under which assumptions does claim X survive argumentation?"

## Status: COMPLETE

Report written to `reports/atms-composition-literature-requirements.md`.

Key conclusions:
1. No paper explicitly combines ATMS + Dung argumentation -- but formal foundations are complete
2. Recommended architecture: iterated fixpoint (ATMS labels -> per-environment AF -> surviving labels)
3. Current gap: ATMS and argumentation are mutually exclusive backends in resolution.py
4. Tractable engineering task, not research-level problem
5. Odekerken 2023 provides the formal semantics for stability/relevance of composed system
