# Reviewer Response to Analysis (2026-03-22)

This is the reviewer's response after seeing the analysis of review-v1.md grounded in the paper collection.

## What the reviewer validated

- The ATMS framing is stronger than the reviewer's generic "non-collapsing ledger" language
- The point about support relations being thrown away is exactly the kind of concrete correctness hole the reviewer likes to see
- The analysis correctly identified the sharpest flaw: relate.py writes probabilistic LLM stance guesses into source YAML, and downstream machinery treats them as symbolic facts

## Reviewer's updated framing

The system is trying to be:

**a typed claim repository whose semantic core should probably be ATMS-style assumption-labeled environments, with argumentation as one derived analysis layer rather than the sole truth engine.**

Three theoretical layers:
1. **Assumption/context maintenance** — ATMS / belief revision / non-premature commitment
2. **Argumentation layer** — Dung / Pollock / ASPIC+ / bipolar support / defeat semantics
3. **Workflow and ingestion hygiene** — LLM extraction, stance proposals, reconciliation, review, source mutation discipline

## Reviewer's two pushbacks

### 1. Entrenchment cannot be reduced to justification structure alone

Empirical science has evidential quality not captured by graph topology: study design, measurement validity, instrument reliability, sample bias, preregistration, replication quality, fraud/retraction risk. The right design is: **graph-derived structural entrenchment + declared external quality signals, combined transparently at render time.** Neither subsumes the other.

### 2. "Already computes correctly" is conditional

The grounded extension computation in dung.py correctly implements Dung Definition 20. But "correct semantics on a correct input graph" is the full claim. The input graph depends on attack/support extraction being right, attack graph construction being right, premises being typed/scoped correctly, and source relations not being contaminated. The semantics may be right conditional on the input graph being right.

## Five-tranche ordering

Each depends on the one before it.

### Tranche 1: Stop poisoning source truth ✅ DONE (merged 1fa1f21)
- Removed materialized defeat table (build-time collapse)
- Exposed --confidence-threshold at CLI
- Added stance_summary() render explanations
- 8 new tests

### Tranche 2: Fix argumentation semantic correctness
- Support-aware AF construction (Cayrol 2005): implement supported defeat and indirect defeat in argumentation.py so support relations contribute to the Dung AF
- Attack-based conflict-free (Modgil & Prakken 2018 Def 14): upgrade dung.py from defeat-based to attack-based conflict-free, enabling all four rationality postulates
- Tests on small canonical examples demonstrating changed extension behavior

### Tranche 3: Make non-commitment the core model
- ATMS-style environment labels (de Kleer 1986)
- Explicit assumption sets / environment selection / render profiles
- Stable interface between assumption maintenance and argumentation layer
- Dixon 1993 proves ATMS context switching = AGM expansion + contraction

### Tranche 4: Deepen the type/comparability story
- Local theories + views/morphisms + coercions
- Replace naive concept identity with structured comparability
- New YAML types: equivalence_edge, coercion, view, preserves, loses

### Tranche 5: Incomplete information and entrenchment
- Stability/relevance under partial corpus (Odekerken 2023)
- Entrenchment from justification structure (Dixon 1993) PLUS declared external quality signals
- Render-time weighting discipline

## Reviewer's one-paragraph synthesis

"Your response substantially strengthens the original review. The review's main critique — premature canonicalization through heuristic source mutation — still stands, but your analysis identifies a more precise formal remedy: an ATMS-style non-commitment core, with argumentation and revision operating over assumption-labeled environments rather than prematurely hardened source facts. The immediate priority should therefore be to convert heuristic relation extraction into proposal artifacts, then repair the current argumentation semantics by incorporating support-derived defeat and attack-based conflict-freeness. After that, the architectural center should shift from global canonicalization to explicit environments, local theories, and views. My one substantive caution is that empirical scientific preference cannot be reduced entirely to justification topology; render-time epistemic preference should likely combine graph-derived entrenchment with explicit external quality signals rather than pretending one subsumes the other."

## The load-bearing sentence

**The system needs a formal non-commitment discipline at the semantic core.**
