# WS-L Closure

Workstream: WS-L merge non-commitment and sameAs discipline
Closing implementation commit: `e69f1d09`

## Findings Closed

- T3.3 / HIGH-1: cross-paper corroboration no longer collapses into one assertion; assertion identity now includes provenance.
- HIGH-2: regime-split claims with different `conditions` remain distinct and produce explicit ignorance.
- T3.4 / HIGH-3: logical-id aliasing no longer performs unconditional union-find collapse; graded sameAs has its own semantic family.
- HIGH-4: `_classify_pair` no longer guesses compatible/conflict from concept fallthrough when the detector has no record.
- MED-1: `Z3TranslationError` is surfaced as untranslatable, not mislabeled as a phi node.
- MED-2 and MED-3: merge materialization preserves canonical artifact IDs, version IDs, source paper provenance, and branch origin.
- MED-4: missing comparison provenance is a typed error; no synthetic `merge_comparison` paper is emitted.
- MED-5: non-claim path conflicts are surfaced instead of silently left-winning.
- MED-6: tests that pinned collapse behavior were removed or updated with WS-L semantics.
- Missing-feature gates: IC constraint pruning, n-ary branch profiles, graded sameAs vocabulary, witness basis, schema conflict surfacing, and preferred/stable structured evidence are now covered.

## Red Tests First

- `tests/test_merge_assertion_id_includes_provenance.py` failed first because `_semantic_payload` stripped provenance.
- `tests/test_merge_corroboration_preserved.py` failed first because duplicate assertions collapsed to one argument.
- `tests/test_merge_regime_split_preserved.py` failed first because `conditions` were stripped from assertion identity.
- `tests/test_canonical_claim_groups_no_union_find.py` failed first because logical-id aliases were unioned unconditionally.
- `tests/test_classify_pair_no_concept_fallthrough.py`, `tests/test_z3_translation_error_surfaced.py`, and `tests/test_comparison_source_no_synthetic_paper.py` failed first on the classifier fallthrough/error handling.
- `tests/test_materialized_claim_provenance_preserved.py` and `tests/test_merge_symmetry_non_claim_files.py` failed first on merge commit materialization and non-claim overwrite behavior.
- `tests/test_ic_postulate_coverage.py`, `tests/test_structured_merge_supports_preferred_stable.py`, `tests/test_merge_witness_basis.py`, `tests/test_schema_versioning_conflict.py`, `tests/test_sameas_family_schema.py`, and `tests/test_workstream_l_done.py` failed first on missing WS-L surfaces or closure state.

## Logged Gates

- `logs/test-runs/WS-L-red-20260430-004540.log`
- `logs/test-runs/WS-L-assertion-id-20260430-004626.log`
- `logs/test-runs/WS-L-classifier-20260430-005044.log`
- `logs/test-runs/WS-L-commit-20260430-005407.log`
- `logs/test-runs/WS-L-structured-20260430-005508.log`
- `logs/test-runs/WS-L-sameas-red-20260430-005554.log`
- `logs/test-runs/WS-L-sameas-20260430-005708.log`
- `logs/test-runs/WS-L-existing-merge-updated-20260430-010044.log`
- `logs/test-runs/WS-L-docs-20260430-010337.log`
- `logs/test-runs/WS-L-20260430-010418.log`
- `logs/test-runs/WS-L-full-20260430-010517.log` — exposed stale full-suite expectations and contract bumps.
- `logs/test-runs/WS-L-full-failures-20260430-011229.log`
- `logs/test-runs/WS-L-full-failures-rerun-20260430-011345.log`
- `logs/test-runs/WS-L-final-20260430-011453.log` — 16 passed.
- `logs/test-runs/WS-L-full-rerun-20260430-011618.log` — 3446 passed, 2 skipped.

Additional gates:
- `uv run pyright propstore` — 0 errors, 0 warnings, 0 informations.
- `uv run lint-imports` — 445 files, 3031 dependencies, 5 contracts kept, 0 broken.
- `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py` — `INDEX.md dependency order OK (32 rows checked)`.

## Property Gates

- `tests/test_ic_postulate_coverage.py` covers integrity-constraint pruning and n-ary branch profile behavior.
- `tests/remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py` remains a Hypothesis gate for rival body preservation, now asserting distinct versions rather than artifact forks.
- Existing merge determinism/symmetry/property tests stayed green under the new non-collapse semantics.

## Files Changed

- Merge core: `propstore/merge/merge_claims.py`, `propstore/merge/merge_classifier.py`, `propstore/merge/merge_commit.py`, `propstore/merge/structured_merge.py`, `propstore/merge/witness.py`.
- Family/schema surfaces: `propstore/families/sameas/`, `propstore/families/registry.py`, `propstore/families/claims/documents.py`, `propstore/families/documents/merge.py`, `propstore/contracts.py`, `propstore/contract_manifests/semantic-contracts.yaml`.
- Tests: WS-L tests listed above, plus updated merge CLI/remediation expectations and removed collapse-pinning tests.
- Docs: `docs/gaps.md`, `docs/semantic-merge.md`, `reviews/2026-04-26-claude/workstreams/WS-L-merge.md`, this report, and the index status row.

## Remaining Risks

Booth 2006 admissible/restrained revision remains explicitly out of WS-L and belongs to WS-L.2 or a successor research stream. The sameAs family now exists with graded vocabulary, but identity-link quality production and multicut repair policy remain future heuristic-layer work rather than merge-owned automatic collapse.
