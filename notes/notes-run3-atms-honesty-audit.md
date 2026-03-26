# Run 3 ATMS Honesty Audit — 2026-03-24

## GOAL

Attack the proposed Run 3 design (global justification graph, label propagation, nogood propagation, exact-support queries) from the standpoint of semantic dishonesty and fake ATMS claims.

## WHAT I OBSERVED

### Current codebase state (verified by reading source):

1. **labelled.py** — Correct ATMS label algebra: AssumptionRef, EnvironmentKey, NogoodSet, Label, JustificationRecord, combine_labels (cross-product), merge_labels (union), normalize_environments (antichain minimization + nogood filtering). All operations are mathematically sound.

2. **structured_argument.py** — 1:1 claim-to-argument projection. premise_claim_ids always `()`, subargument_ids always `()`, top_rule_kind always `"claim"`, attackable_kind always `"base_claim"`. Labels come from `_default_support_metadata()` which is a heuristic classifier (context? conditions? → SupportQuality enum), NOT from justification structure.

3. **bound.py** — Labels attached post-hoc at query time via `_attach_value_label`, `_attach_derived_label`, `_attach_resolved_label`. `_claim_support_label()` returns None for context-scoped claims (line 419-420), meaning context claims opt out of the label system entirely. Two parallel filtering mechanisms: context hierarchy visibility vs. label/environment derivability.

4. **semantic-contract.md** — Binding Decision B4 explicitly says: "this phase implements environment-correct semantics only... no implementation in R1-R5 may market itself as a full ATMS layer." The codebase is self-aware about this gap.

5. **dung.py** — Genuinely implemented: all four Dung semantics (grounded/preferred/stable/complete), conflict-free checks, characteristic function, admissibility. This is real.

6. **argumentation.py** — Cayrol 2005 derived defeats (bipolar support chains), Modgil & Prakken 2018 preference filtering. Also real.

### What de Kleer 1986 actually requires (verified against paper notes in papers/deKleer_1986_AssumptionBasedTMS/):

- justify-node with automatic label propagation through dependency network
- Nogood discovery through derivation reaching γ_⊥ (contradiction node)
- Incremental label updates on new justification addition
- Runtime assumption creation
- Context = environment = set of assumptions (ONE mechanism, not two)

### What Run 3 as proposed would NOT fix:

1. **No real justifications** — parameterizations are math formulas, support stances are editorial opinions. Neither are Horn clause derivations.
2. **Nogoods from conflict detector, not from derivation** — reverses de Kleer's dependency direction.
3. **Batch compilation, not incremental** — would compute all labels at once, not update on justification addition.
4. **Context/label split persists** — two independent filtering mechanisms, neither subsuming the other.
5. **1:1 argument projection unchanged** — empty premises and subarguments survive alongside the new graph.
6. **Exact-support queries already exist** — `BoundWorld.claim_support()` does this inline today.

## WHAT I PRODUCED

Three-section audit delivered to Q:
1. **What Would Still Be Fake** — six specific dishonesty points with code-level evidence
2. **What Must Be Proved In Tests** — eight specific test obligations that would distinguish real ATMS from labeled flat store
3. **Minimum Honest Public Wording** — exact text Q could use that describes capabilities without overclaiming

## NEXT STEP

Ball is with Q. The audit identifies the semantic gap between "ATMS-inspired label algebra" (what exists and is honest) and "ATMS" (what would be claimed). Key decision: does Run 3 aim for genuine incremental ATMS semantics (derivation-originated nogoods, retraction, single visibility mechanism), or does it aim for a better-labeled batch store that preserves the algebra without claiming the architecture?
