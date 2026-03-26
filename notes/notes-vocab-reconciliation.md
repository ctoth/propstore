# Vocabulary Reconciliation Session - 2026-03-21

## GOAL
Normalize concept names across 26 papers' claims.yaml files to a canonical set.

## Key Findings So Far

- **754 unique concept names** found (not 578 as estimated), across **1070 total references** in **26 papers** (not 25)
- Two schema patterns exist:
  1. `concepts:` list (e.g., Doyle, deKleer, Walton, Greenberg, etc.)
  2. `label:` field (e.g., Dung, Modgil_2014, Clark - but Clark also uses `concepts:`)
  3. Some have `parameters.concept` or `variables.concept` fields (equation claims)
- No vocabulary file exists to load - concept registry (knowledge/concepts/) is EMPTY

## Collision Group Analysis Needed

Now I need to run the token-overlap similarity analysis to find collision groups.
Major clusters to look for per the brief:
- "belief" (20 variants)
- "assumption" (14)
- "label" (12)
- "justification" (12)
- "argument" (11)
- "support" (11)
- "context" (10)
- "environment" (9)

## Key Observation
Many concepts with the same root token are NOT duplicates - they're genuinely different sub-concepts.
E.g., "label_completeness", "label_consistency", "label_minimality", "label_soundness" are four distinct ATMS properties.
"belief_interval", "belief_propagation", "belief_threshold" are distinct BMS concepts.

The real duplicates will be things like:
- `argumentation_scheme` vs `argumentation_schemes` (singular vs plural)
- `agm_belief_revision` vs `belief_revision` (prefixed vs unprefixed)
- `three_attack_types` vs `three_attack_types_full` (paper-specific label variants)
- `last_link_ordering` vs `last_link_ordering_full`
- `rebutting_defeat` vs `rebutting_defeater`
- `claim` vs `claim_lineage` vs `claim_lineages` (singular vs plural issue for the last two)
- `weakest_link_ordering` vs `weakest_link_ordering_full`

## DONE
- Extracted 754 unique concepts from 26 papers (1070 total references)
- Ran collision detection: 47 candidate pairs found
- Applied 12 merges across 8 files
- Documented 33 kept-distinct decisions
- Final count: 742 unique concepts
- Report written to reports/vocabulary-reconciliation.md
- All 26 claims.yaml files validate correctly (391 total claims)
