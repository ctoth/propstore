# Full Suite Failure Inventory

Date: 2026-03-29

Log:
- `logs/test-runs/20260329-204109-full-suite-post-knowledge-path-sidecar.log`

Result:
- `5 failed, 2036 passed`

## Failure 1

Test:
- `tests/test_exception_narrowing_group3.py::TestValueResolverZ3::test_runtime_error_propagates_through_value_resolver`

Symptom:
- `_all_algorithms_equivalent(...)` raised `AttributeError: 'dict' object has no attribute 'body'`

Root cause:
- The typed-claim refactor narrowed the helper to `_ActiveClaimView` objects and stopped normalizing dict inputs at the helper boundary.
- The exception-narrowing test intentionally patches `ast_compare` and calls the helper directly with raw dicts to verify that non-narrowed runtime errors still propagate.

Git-history signal:
- `256717e` `refactor: type value resolver boundaries` introduced `_ActiveClaimView` and the narrower helper contract.
- The test predates that narrowing via `5ae3c66` and is still asserting the older helper behavior.

Literature relevance:
- None directly. This is an internal helper-boundary regression, not a problem-solver/TMS semantics issue.

Fix direction:
- Normalize dict claims to `_ActiveClaimView` inside the helper, so the test still reaches `ast_compare`.

## Failures 2-3

Tests:
- `tests/test_labelled_core.py::test_derived_value_combines_input_labels`
- `tests/test_semantic_core_phase0.py::test_binding_order_does_not_change_active_or_resolved_semantics`

Symptom:
- `KeyError: 'output_concept_id'` from `ParameterizationRow.from_mapping(...)`

Root cause:
- The strict row refactor treated `parameterizations_for(concept_id)` lookup rows as if they were canonical catalog rows.
- Some stores legitimately omit `output_concept_id` from lookup rows because the lookup argument already fixes the output concept.

Git-history signal:
- `f05eab6` `refactor: add typed semantic id boundaries` made `ParameterizationRow` require `output_concept_id` unconditionally.
- The phase-0 and labelled-core tests use minimal semantic stores that expose per-concept lookup rows, not full catalog rows.

Literature relevance:
- Indirectly yes. The relevant principle is de Kleer/Dixon-style contract honesty: the substrate should expose exact justificational structure, and the problem-solver boundary should not pretend two different interfaces are the same.
- This is not a theorem about parameterizations specifically; it is an architectural honesty issue.

Relevant notes:
- `papers/deKleer_1986_AssumptionBasedTMS/notes.md`
- `papers/deKleer_1986_ProblemSolvingATMS/notes.md`
- `papers/Dixon_1993_ATMSandAGM/notes.md`

Fix direction:
- Let lookup coercion supply `output_concept_id` explicitly from the lookup boundary instead of forcing lookup rows to masquerade as catalog rows.

## Failures 4-5

Tests:
- `tests/test_semantic_core_phase0.py::test_empty_hypothetical_overlay_is_identity_transform`
- `tests/test_semantic_core_phase0.py::test_remove_and_add_inverse_overlay_returns_same_semantic_state`

Symptom:
- `HypotheticalWorld` first failed by forcing `build_compiled_world_graph(...)` on a store without `all_concepts()`
- After that was relaxed, it still tried to recompute conflicts through `_concept_registry_for_store(...)`, which also assumes `all_concepts()`

Root cause:
- `HypotheticalWorld` was still assuming that every valid semantic store is also graph-compilable and concept-catalog-capable.
- The phase-0 tests intentionally use a weaker semantic store to assert that empty or inverse overlays preserve semantics even without graph inventory machinery.

Git-history signal:
- `b1e4798` `refactor: adapt hypothetical graph build boundary` improved one graph-build boundary but still left the semantic-only path incomplete.
- `c83a5b0` added the phase-0 tests specifically to lock semantic identity properties.

Literature relevance:
- Yes. This is exactly the problem-solver/substrate separation issue from the ATMS literature.
- The TMS/ATMS substrate should preserve soundness/completeness guarantees, but the problem solver must not smuggle in stronger interface assumptions than the substrate actually provides.
- Relevance and relatedness decisions belong to the problem solver, not the TMS substrate.

Relevant notes:
- `papers/deKleer_1986_AssumptionBasedTMS/notes.md`
- `papers/deKleer_1986_ProblemSolvingATMS/notes.md`
- `papers/Dixon_1993_ATMSandAGM/notes.md`
- `papers/Mason_1989_DATMSFrameworkDistributedAssumption/notes.md`

Fix direction:
- Make `HypotheticalWorld` bifurcate cleanly:
  - graph-delta path when the base store is genuinely graph-capable
  - semantic-overlay fallback when it is not
- Recomputed conflicts should be skipped when the store lacks concept-catalog capability rather than pretending it can support that recomputation.
