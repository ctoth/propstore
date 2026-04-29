# WS-G Closure Report

Workstream: WS-G belief revision, IC merge, and AF-revision consumption
Closing propstore commit: `b3b91229`
Upstream dependency fix: `formal-argumentation` pushed commit `de6b66f97eb8208e911cb6686f0c2ea6c5d2c69e`

## Findings Closed

- T2.6: `revise(state, BOTTOM)` now yields an inconsistent belief set instead of returning the input state.
- T2.2 / Codex #23: AGM contraction preserves Spohn/OCF ranking information through Harper-style min ranks.
- Cluster C MED-1/MED-3/MED-4: K-6/K-7/K-8, Harper, C1-C4, CR1-CR4, and EE rows are split into the WS-G audit matrix.
- Cluster C MED-2: IC4, Maj, and Arb are explicitly covered; Arb fixture corrected against Konieczny-Pino-Pérez 2002 p.791.
- Codex #18: IC merge rejects unsatisfiable profile members instead of discarding infinite distances.
- Cluster C HIGH-4: IC distance cache keys by formula value and signature.
- Cluster C exponential gap: AGM revision refuses oversized signatures with `EnumerationExceeded`.
- Codex #19: support-revision projection records branch, commit, and merge-parent evidence from a real repo snapshot.
- Codex #20: upstream AF revision now raises `NoStableExtensionsError` for no-stable targets; propstore pins that pushed commit and the consumer adapter keeps the no-stable/empty-stable distinction.
- Cluster C LOW-5/LOW-6: docs use `Gärdenfors`; revision helper moved under `tests/support_revision/`.
- Missing constructions are documented in `docs/belief-set-revision.md`, `docs/ic-merge.md`, and `docs/af-revision.md`, with propositional items assigned to T6.5 and AGM-AF items to WS-O-arg.

## Red Tests Written First

- `tests/test_agm_K_star_2_inconsistent_input.py`: failed because `revise(state, BOTTOM)` returned the unchanged state.
- `tests/test_agm_contraction_preserves_spohn_state.py`: failed because contraction flattened distinct OCF states.
- `tests/test_ic_merge_infinite_distance_handling.py`: failed because the typed boundary exception did not exist.
- `tests/test_ic_merge_distance_cache_stale_read.py`: failed because equal formula values produced separate cache entries under `id(formula)` keys.
- `tests/test_belief_set_alphabet_growth_budget.py`: failed because `revise` had no explicit alphabet-size budget and enumerated a 21-atom signature.
- `tests/test_worldline_revision_merge_parent_evidence.py`: failed because `RevisionScope` omitted branch, commit, and merge parents.
- `tests/test_af_revision_no_stable_distinct_from_empty_stable.py`: failed because propstore had no public consumer adapter.
- Upstream `argumentation/tests/test_af_revision.py::test_diller_2015_framework_revision_rejects_no_stable_target`: failed at collection before `NoStableExtensionsError` existed.

## Test Evidence

- Red AGM: `logs/test-runs/WS-G-red-agm-20260429-014440.log`
- AGM green: `logs/test-runs/WS-G-agm-green-20260429-014712.log`
- Red IC: `logs/test-runs/WS-G-red-ic-20260429-014844.log`
- IC green: `logs/test-runs/WS-G-ic-green-20260429-015024.log`
- IC coverage green: `logs/test-runs/WS-G-ic-coverage-20260429-015241.log`
- Red budget: `logs/test-runs/WS-G-red-budget-20260429-015408.log`
- Budget green: `logs/test-runs/WS-G-budget-green-20260429-015531.log`
- Red merge-parent: `logs/test-runs/WS-G-red-merge-parent-20260429-015703.log`
- Merge-parent green: `logs/test-runs/WS-G-merge-parent-green-20260429-015742.log`
- Red AF adapter: `logs/test-runs/WS-G-red-af-20260429-015830.log`
- AF adapter green: `logs/test-runs/WS-G-af-green-20260429-015909.log`
- Audit matrix green: `logs/test-runs/WS-G-audit-20260429-020445.log`
- Support-helper move: `logs/test-runs/WS-G-support-helper-20260429-020620.log`
- Docs: `logs/test-runs/WS-G-docs-20260429-020842.log`
- Sentinel: `logs/test-runs/WS-G-sentinel-20260429-021115.log`
- Propstore after dependency pin: `logs/test-runs/WS-G-argumentation-pin-20260429-021729.log`

Upstream dependency evidence:

- `uv run pytest -vv tests/test_af_revision.py`: 14 passed.
- `uv run pyright src/argumentation`: 0 errors.
- `uv run pytest -vv`: 482 passed.

## Property-Based Tests

- `tests/test_agm_postulate_audit.py` adds 100 audit rows spanning K*1-K*8, K-1-K-8 plus Harper, C1-C4, CR1-CR4, IC4/Maj/Arb, EE1-EE5, and AF no-stable distinguishability.
- Existing Hypothesis postulate tests were updated so IC properties assume satisfiable profile members after the production boundary rejects inconsistent profiles.
- The old bundled K*/K-/DP mega-tests were removed from `tests/test_belief_set_postulates.py`.

## Files Changed

- `propstore/belief_set/agm.py`
- `propstore/belief_set/iterated.py`
- `propstore/belief_set/ic_merge.py`
- `propstore/belief_set/af_revision_adapter.py`
- `propstore/support_revision/projection.py`
- `docs/belief-set-revision.md`
- `docs/ic-merge.md`
- `docs/af-revision.md`
- `docs/gaps.md`
- `pyproject.toml`
- `uv.lock`
- WS-G tests under `tests/`
- Moved helper: `tests/support_revision/revision_assertion_helpers.py`
- Upstream dependency: `argumentation/src/argumentation/af_revision.py`, `argumentation/tests/test_af_revision.py`

## Remaining Risks

- The WS-G audit is intentionally finite and representative, not an exhaustive theorem prover.
- Missing constructions remain future work by design: propositional AGM work in T6.5 and AF-kernel work in WS-O-arg.
- No local dependency pin was introduced; propstore points at the pushed remote argumentation commit.
