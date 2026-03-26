# Phase 6 Red: PRAF Worldline State Capture

## 2026-03-25

### GOAL
Write failing tests that assert PRAF argumentation state is captured during worldline materialization.

### Observations

1. **worldline_runner.py lines 190-257**: The argumentation state capture block has branches for:
   - `claim_graph` (line 196)
   - `structured_projection` (line 213)
   - `atms` (line 250)
   - **No branch for `praf`** -- this is the gap we're testing

2. **ReasoningBackend enum** (`propstore/world/types.py` line 133): `PRAF = "praf"` exists as a valid backend value.

3. **WorldlinePolicy** (`propstore/worldline.py`): Already has praf-specific fields (praf_strategy, praf_mc_epsilon, praf_mc_confidence, praf_treewidth_cutoff, praf_mc_seed).

4. **Existing test pattern** (`tests/test_worldline.py` line 729): `test_argumentation_worldline_records_stance_dependencies_and_detects_staleness` uses:
   - FakeBound class with value_of, derived_value, active_claims methods
   - FakeWorld class with bind, resolve_concept, get_concept, get_claim, has_table, claims_by_ids, stances_between methods
   - monkeypatch to mock `propstore.argumentation.compute_claim_graph_justified_claims`
   - WorldlineDefinition with `policy: {strategy: "argumentation"}`

5. **What the tests should assert**: When `reasoning_backend="praf"` and `strategy="argumentation"`, the result's `argumentation` field should contain:
   - `"backend"` key = `"praf"`
   - `"acceptance_probs"` dict mapping claim IDs to floats in [0.0, 1.0]
   - `"strategy_used"` string
   - `"semantics"` string

6. **Li et al. 2011 notes**: PrAF = (A, P_A, D, P_D). Acceptance probability is computed by marginalizing over all inducible sub-DAFs. MC approximation with Agresti-Coull stopping.

### Plan
- Write two tests in `tests/test_worldline_praf.py`:
  1. `test_praf_argumentation_state_captured` - basic structure assertions
  2. `test_praf_argumentation_state_has_acceptance_probs` - two conflicting claims, acceptance probs in [0,1]
- Use FakeWorld/FakeBound pattern from existing tests
- Tests should FAIL because worldline_runner.py has no praf branch

### NEXT
Write the test file.
