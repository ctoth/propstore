# WS-I Closure Report

Workstream: WS-I ATMS / world correctness
Closing commit: `6a6cc9d6`

## Findings Closed

- E.H1a/E.H1b/E.H1c: `is_stable`, `node_relevance`, and `node_interventions` now require explicit keyword-only budgets. `limit=None` is unbounded; finite budget exhaustion raises `BudgetExhausted`.
- E.H2: cyclic support pruned by nogoods is classified as `NOGOOD_PRUNED`, so intervention planning sees the right OUT discriminator.
- E.H3: categorical and boolean parameterization providers now produce visible rejected derived nodes with `PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE`.
- Codex #24: derived-vs-derived parameterization contradictions are collected, surfaced, and fed into ATMS nogoods.
- Codex #25: serialized support environments preserve assumption ids and context ids across core, app, CLI, nogood, and future-report surfaces.
- Codex #26: exact antecedent matching uses canonical CEL equality for supported commutative forms instead of raw spelling.
- E.M1/E.M2/E.M3: ATMS build ceilings return partial state, the dead `consequent_ids` production surface is deleted, and the old stale-nogood propagation ordering is gated.
- E.M4: conflict orchestration fails loudly on synthetic concept collisions, composes returned parameterization records, uses an explicit lifting decision cache, and keys lifted records with derivation provenance.

## Tests Written First

- `tests/test_atms_unbounded_stability_api.py` failed on silent default-budget truncation and missing `BudgetExhausted`.
- `tests/test_atms_was_pruned_by_nogood_cycle.py` failed when cyclic nogood-pruned support was reported as missing support.
- `tests/test_atms_categorical_provider_visibility.py` failed because nonnumeric providers were silently dropped.
- `tests/test_atms_derived_contradictions.py` failed because only the first compatible derived candidate was inspected.
- `tests/test_atms_environment_context_serialisation.py` failed because environment serializers stripped context ids.
- `tests/test_atms_cel_semantic_equality.py` failed because antecedent matching used raw CEL string equality.
- `tests/test_atms_max_iterations_anytime.py`, `tests/test_atms_consequent_field_discipline.py`, and `tests/test_atms_propagation_nogood_interleave.py` failed against the old build ceiling, dead field, and propagation-order surfaces.
- `tests/test_conflict_orchestrator_isolation.py` failed on synthetic concept collisions, mutable record injection, missing cache, and derivation-chain-insensitive lifting keys.
- `tests/test_workstream_i_done.py` is the final pass sentinel.

## Logged Gates

- Red logs: `logs/test-runs/WS-I-step1-red-20260428-050119.log`, `WS-I-step2-red-20260428-052231.log`, `WS-I-step3-red-20260428-052630.log`, `WS-I-step4-red-20260428-053220.log`, `WS-I-step5-red-20260428-053735.log`, `WS-I-step6-red-20260428-054615.log`, `WS-I-step7-red-20260428-055035.log`, `WS-I-step8-red-20260428-055903.log`.
- Step greens: `logs/test-runs/WS-I-step1-stale-tests-20260428-051550.log`, `WS-I-step2-impl-20260428-052417.log`, `WS-I-step3-impl-20260428-053037.log`, `WS-I-step4-atms-20260428-053602.log`, `WS-I-step5-impl-20260428-054452.log`, `WS-I-step5-serializer-complete-20260428-061450.log`, `WS-I-step6-impl-20260428-054834.log`, `WS-I-step7-existing-20260428-055636.log`, `WS-I-step7-split-20260428-061954.log`, `WS-I-step8-impl-20260428-060852.log`, `WS-I-sentinel-20260428-061618.log`.
- Final WS-I gate: `logs/test-runs/WS-I-20260428-062435.log` green, 19 passed.
- Existing companion gate: `logs/test-runs/WS-I-existing-20260428-062524.log` green, 116 passed. No `tests/test_world_atms*.py` files exist in this repo state.
- Full suite: `logs/test-runs/pytest-20260428-062603.log` green, 3166 passed.
- `uv run pyright propstore`: 0 errors.
- `uv run lint-imports`: 4 contracts kept, 0 broken.

## Property Tests

- Added `tests/test_atms_unbounded_stability_api.py::test_ws_i_budgeted_stability_is_monotone_when_a_verdict_is_reached` for the WS-I budget monotonicity property.
- Existing `tests/test_labels_properties.py` was included in the WS-I companion run and covers generated label minimality, nogood exclusion, merge/combination laws, and context ids as part of environment identity.
- No WS-I property gates were moved to a successor workstream.

## Files Changed

- `propstore/world/atms.py`
- `propstore/world/types.py`
- `propstore/world/bound.py`
- `propstore/world/value_resolver.py`
- `propstore/app/world_atms.py`
- `propstore/cli/world/atms.py`
- `propstore/fragility_types.py`
- `propstore/conflict_detector/orchestrator.py`
- `propstore/conflict_detector/parameterization_conflicts.py`
- `docs/atms.md`
- `docs/python-api.md`
- `docs/gaps.md`
- WS-I tests under `tests/`
- Review bookkeeping: this report, `WS-I-atms-world.md`, and `INDEX.md`

## Remaining Risks

- Step 6 uses parser-based canonical equality for supported commutative CEL forms. A full Z3-backed CEL semantic-equivalence service remains WS-P or a future CEL semantics stream.
- WS-J must account for the structured environment shape and the explicit ATMS budget API when it starts.
