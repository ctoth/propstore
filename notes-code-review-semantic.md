# Semantic Code Review — 2026-03-23

## GOAL
Deep review of Python code for semantic bugs, architectural mismatches, and paper conflicts.

## FILES READ (all)
- CLAUDE.md — core principle: non-commitment, lazy-until-render, 6-layer arch
- propstore/dung.py — Dung AF (grounded, preferred, stable, complete)
- propstore/argumentation.py — stances → AF, Cayrol bipolar derived defeats
- propstore/preference.py — ASPIC+ preference ordering (elitist/democratic)
- propstore/world/model.py — WorldModel read-only reasoner
- propstore/world/resolution.py — resolution strategies
- propstore/world/types.py — data classes, enums, protocols
- propstore/world/bound.py — BoundWorld condition-bound view
- propstore/world/value_resolver.py — ActiveClaimResolver
- propstore/world/hypothetical.py — HypotheticalWorld overlay
- propstore/build_sidecar.py (lines 1-200) — sidecar builder, stance loading
- propstore/stances.py — stance type vocabulary
- propstore/z3_conditions.py — CEL→Z3 translation, disjointness/equivalence
- propstore/validate_claims.py — claim file validation
- propstore/conflict_detector/__init__.py, models.py, orchestrator.py, algorithms.py
- propstore/value_comparison.py — numeric value comparison
- propstore/parameterization_walk.py — graph walk utilities
- propstore/maxsat_resolver.py — MaxSMT conflict resolution

## CRITICAL SEMANTIC BUGS

### 1. preference.py:27-28 — Elitist comparison definition
Modgil & Prakken 2018 Def 19: set_a <_e set_b iff ∃x∈set_b ∀y∈set_a: y<x
Code: `any(all(x < y for y in set_b) for x in set_a)` = ∃x∈A ∀y∈B: x<y
This reads "some element of A is strictly less than every element of B" which is STRONGER than required.
Actually wait — re-reading: the paper says A is weaker if some element of B dominates all of A. The code says A is weaker if some element of A is dominated by all of B. For singleton sets these are equivalent. For multi-element sets they diverge. NEED TO VERIFY against exact paper formulation.

### 2. argumentation.py:146-153 — Cayrol derived defeats missing from attacks
Derived defeats from support chains added to `defeats` but NOT to `attacks`. The AF is built with attacks=frozenset(attacks) containing only original stances. In dung.py:97, conflict_free uses `attacks` relation. Two arguments connected only by a Cayrol derived defeat can both be in a "conflict-free" set — this violates Cayrol 2005 which says derived defeats ARE attacks in the flattened framework.

### 3. maxsat_resolver.py:45 — z3 model.evaluate returns BoolRef not bool
`model.evaluate(var, model_completion=True)` returns a z3.BoolRef, not a Python bool. The `if` truthiness check works for z3.BoolVal(True) but this is fragile. Should use `z3.is_true(model.evaluate(...))`.

### 4. argumentation.py:109-115 — confidence threshold silently drops stances
Stances with confidence < threshold are silently dropped before AF construction. The non-commitment principle says filtering before render is WRONG. This is build-time filtering of stance data.

### 5. value_resolver.py:106-107 — conflicted inputs short-circuit derivation
If ANY input to a parameterization is conflicted, the entire derivation returns "conflicted" immediately without trying other parameterizations. This prevents derivation chains from using alternative paths.

## ARCHITECTURAL MISMATCHES

### 1. WorldModel implements ArtifactStore protocol but also has chain_query
chain_query (model.py:466-549) does resolution (render-layer logic) inside what the architecture describes as a storage-layer object. ArtifactStore protocol (types.py:124-129) includes chain_query, so the protocol itself violates the layering.

### 2. BoundWorld.conflicts() recomputes at render time — good
But BoundWorld calls _recomputed_conflicts which imports detect_conflicts from conflict_detector (the heuristic analysis layer). This means the render layer depends on the heuristic analysis layer, violating one-way dependencies (render should be above analysis in the stack).

### 3. build_sidecar.py:158-161 — stance loading rejects nonexistent claims
Stances referencing claims not in the DB are rejected with IntegrityError. Per the design checklist: "Does this prevent ANY data from reaching the sidecar? If yes → WRONG." Invalid stance references should be stored with a warning, not blocked.

### 4. validate_claims.py:140-145 — draft stage claims are hard-rejected
Draft artifacts are blocked with an error. The non-commitment principle says data should flow into storage regardless. Draft claims should reach the sidecar and be filtered at render time by policy.

### 5. HypotheticalWorld._base._store and _base._policy — reaching through abstraction
hypothetical.py:28 and :87 reach into BoundWorld's private _store and _policy attributes, coupling tightly to implementation.

## PAPER CONFLICTS

### 1. Cayrol 2005 — Derived defeats not in attack relation (SEE BUG #2)
The flattened AF per Cayrol should include derived defeats in the attack relation. The code maintains separate attacks (original only) and defeats (original + derived), but the ASPIC+ conflict-free check uses attacks. This means the AF is neither a proper bipolar AF (which needs explicit support/attack) nor a properly flattened Dung AF.

### 2. de Kleer 1986 ATMS — No assumption labeling
The CLAUDE.md cites de Kleer's ATMS: "label every datum with minimal assumption sets, never commit to one context." Claims have conditions (CEL expressions), but these are not ATMS-style assumption labels. There is no minimal environment computation, no dependency-directed backtracking. The Z3 condition solver checks disjointness/equivalence but doesn't compute minimal nogood sets or track justifications. The ATMS grounding is aspirational, not implemented.

### 3. Pollock 1987 — No undercutting defeat distinction in AF construction
Pollock distinguishes rebutting from undercutting defeat semantically: undercutting attacks the inference step, not the conclusion. In argumentation.py:135, both "undercuts" and "supersedes" are treated as unconditional (preference-independent) defeats, which is correct per ASPIC+. But the AF itself doesn't model inference steps — it's argument-level, not sub-argument-level. An undercutting defeater that attacks a specific inference step is represented as attacking the entire argument, which may be overly aggressive.

### 4. Odekerken 2023 — No incomplete information handling
The CLAUDE.md cites Odekerken 2023 for "ASPIC+ with incomplete information: stability and relevance." The code has no stability analysis (checking whether new information could change the extension) or relevance computation. The argumentation layer computes extensions but doesn't track which are stable under information growth.

## HIGHEST-LEVERAGE IMPROVEMENTS

### 1. Fix Cayrol derived defeats in attacks relation (Bug #2)
Add derived defeats to the `attacks` set in argumentation.py so conflict_free checks correctly identify conflicts through support chains. Single-line fix with significant semantic impact.

### 2. Move confidence threshold filtering to render policy
Currently argumentation.py:115 filters stances by confidence at AF-build time. This should be policy-driven at the render layer, matching the non-commitment principle.

### 3. Allow draft claims into the sidecar
validate_claims.py:140-145 rejects drafts. These should flow through to the sidecar and be filtered at render time via a stage-aware policy.

### 4. Add stability analysis for argumentation extensions
Per Odekerken 2023: after computing an extension, check if adding plausible new arguments could change it. This gives the render layer a "stability" confidence metric.

## STILL TO READ
- build_sidecar.py lines 200+ (remaining build logic)
- propstore/worldline.py, worldline_runner.py
- propstore/propagation.py
- propstore/condition_classifier.py, equation_comparison.py
- conflict_detector/parameters.py, equations.py, measurements.py, collectors.py, context.py
- propstore/dung_z3.py
