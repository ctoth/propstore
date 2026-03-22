# Entailment Session Notes — 2026-03-21

## Goal
Refine propstore's stance taxonomy to distinguish rebutting vs undercutting defeat,
support vs justification, and other relations that propagate differently.
Then use the refined taxonomy as foundation for entailment reasoning.

## Current state
- StanceType has 4 values: supported_by, contradicted_by, superseded_by, mechanism_for
- These conflate rebutting/undercutting defeat (Pollock distinction)
- superseded_by does double duty (undercutting defeater vs refinement)
- mechanism_for is really a justification, not a stance

## Paper processing progress
1. Modgil & Prakken 2014 (ASPIC+) — DONE. 13 claims.
2. Cayrol & Lagasquie-Schiex 2005 (bipolar argumentation) — DONE. 17 claims.
3. Walton & Macagno 2015 (argumentation schemes) — DONE. 15 claims.
4. Mayer, Cabrio & Villata 2020 (argument mining) — DONE. 18 claims.
5. Prakken & Horty 2012 (Pollock appreciation) — DONE. 10 claims.

## Literature gaps identified
1. Rebutting vs undercutting formalization beyond Pollock 1987
2. Argumentation scheme taxonomies (Walton?)
3. Bipolar argumentation (support + attack)
4. Structured argumentation (ASPIC+, ABA)
5. Applied defeater classification in scientific literature

## Implementation — stance taxonomy refactor

### Baseline: 529 passed, 1 pre-existing failure (test_missing_claims_key_errors)

### What I've observed in the code:
- Schema enum (claim.linkml.yaml:35-47): supported_by, contradicted_by, superseded_by, mechanism_for
- Test data uses DIFFERENT strings: "contradicts", "supports" (not the schema values!)
- Resolution code (resolution.py:68-70) checks for "supports" and "contradicts"
- Sidecar DDL stores stance_type as TEXT — no enum constraint
- Only 3 files have stances: Martins_1983 (contradicted_by), fant_1985 (mechanism_for), henrich_2003 (mechanism_for)
- validate_claims.py does NOT validate stance types at all
- No data migration needed — Q says knowledge stores will be recreated

### TDD progress:
- Step 2 (RED → passed): fixture "contradicts"→"rebuts", assertion updated, test renamed. Committed fada564.
- Step 4 (RED confirmed): Added test_paper_gamma with claims 12-15 using undercuts/undermines/explains/supersedes.
  - 3 new tests all fail as expected: supersedes, undercuts, weights_asymmetric
  - BUT: adding 4 new claims broke 11 existing tests that have hardcoded counts/assumptions:
    - test_claims_for: expects concept1 claims = {claim1,claim2,claim3,claim7,claim9}, now also has claim15
    - test_stats: expects 11 claims, now 15
    - test_speech_no_conflicts_concept2: concept2 now has conflicts (was only claim4+claim6, now also claim12-14)
    - test_empty_bind_all_active: count changed
    - test_resolve_recency: claim15 has date 2025-01-01, now wins recency for concept1
    - Various hypothetical/chain tests affected by new concept2 claims

  CURRENT TASK: Fixing 11 existing tests. Progress:

  Key facts about new claims:
  - claim12: concept2, value=900, undercuts claim6
  - claim13: concept2, value=850, undermines claim4
  - claim14: concept2, value=810, explains claim6
  - claim15: concept1, value=205, supersedes claim1

  Fixed so far:
  - test_claims_for: added claim15 to expected set ✓
  - test_stats: 11→15 ✓
  - test_empty_bind_all_active: 11→15 ✓
  - test_speech_no_conflicts_concept2: renamed, assert >=1 ✓
  - test_resolves_conflict: also remove claim15 ✓
  - test_cascading_to_derived: also remove claim15 ✓
  - test_diff_shows_changes: also remove claim15 ✓

  All 11 existing tests fixed and passing. Committed e979d2b.

  Now implementing resolution logic (Step 3+5):
  - Replaced _resolve_stance() in resolution.py with:
    - _STANCE_WEIGHTS dict: supports=+1, explains=+0.5, rebuts=-1, undercuts=-1, undermines=-0.5
    - supersedes check first (short-circuits, winner takes all)
    - float-based weighted scoring for remaining types
  - Need to run tests to verify GREEN

### Plan file: C:\Users\Q\.claude\plans\jiggly-skipping-chipmunk.md
