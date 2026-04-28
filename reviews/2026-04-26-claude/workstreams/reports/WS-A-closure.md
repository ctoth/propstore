# WS-A Closure Report

Workstream: WS-A schema fidelity, fixture parity, and identity boundaries
Closing commit: `e75581b9` (`WS-A close sentinel test`)
Status: CLOSED

## Findings Closed

- T0.1 / Codex #7: test fixtures no longer define a hand-written world-model schema; tests use production-owned `build_minimal_world_model_schema`.
- T0.2 / Codex #6: world-model required schema now includes runtime lifecycle columns and `build_diagnostics`.
- Generated schema freshness: generated schema resources are committed and the generator writes bytes without newline churn.
- Property-marker discipline: every collected Hypothesis `@given` test is recursively marked `property`; collection warns on unmarked property tests.
- D-24 T0.3: URI tagging authorities are parsed and validated before tag URI interpolation and repository-config use.
- D-24 T0.4: numeric concept resolution no longer privileges the `propstore` namespace; ambiguous numeric aliases fail unless explicitly disambiguated.
- D-24 T0.5/T0.6: source-local claim namespaces and concept aliases cannot mint or shadow reserved canonical namespaces.

## Tests Written First

- `tests/test_required_schema_completeness.py`: failed while `_REQUIRED_SCHEMA` omitted lifecycle/runtime columns.
- `tests/test_fixture_schema_parity.py`: failed while tests used `tests/conftest.py:create_world_model_schema`.
- `tests/test_generated_schema_freshness.py`: failed while generated package schema resources were absent or stale.
- `tests/test_property_marker_discipline.py`: failed while nested/unmarked Hypothesis tests were not marked `property`.
- `tests/test_uri_authority_validation.py`: failed while malformed tagging authorities passed through `tag_uri` and repository config.
- `tests/test_no_privileged_namespace.py`: failed while numeric concept IDs selected `propstore` by hard-coded preference.
- `tests/test_source_cannot_mint_canonical_ids.py`: failed while source claim namespaces and aliases could use reserved canonical namespaces.
- `tests/test_workstream_a_done.py`: xfailed until all WS-A gates were green; commit `e75581b9` flips it to passing.

## Logged Test Evidence

- Red WS-A gate: `logs/test-runs/WS-A-red-20260427-212247.log`
- Property marker gate: `logs/test-runs/WS-A-property-marker-20260427-213515.log`
- Pre-close targeted gate with sentinel xfail: `logs/test-runs/WS-A-targeted-20260427-214326.log`
- Focused regression fixes: `logs/test-runs/WS-A-failure-fixes-20260427-214948.log`
- Click/schema dependency check: `logs/test-runs/WS-A-click-schema-check-20260427-215220.log`
- Post-close targeted WS-A gate: `logs/test-runs/WS-A-20260427-215819.log` (`30 passed`)
- Pre-close full suite: `logs/test-runs/WS-A-full-preclose-2-20260427-215238.log` (`2998 passed, 1 xfailed, 1 failed`)
- Final full suite after sentinel close: `logs/test-runs/WS-A-full-20260427-215900.log` (`2999 passed, 1 failed`)
- `uv run pyright propstore`: passed with 0 errors, 0 warnings, 0 informations.
- `uv run lint-imports`: passed with 4 contracts kept, 0 broken.

The full-suite failure is `tests/test_repository_artifact_boundary_gates.py::test_current_docs_do_not_name_deleted_repo_storage_surface`, caused by the pre-existing dirty deletion of `CLAUDE.md`. The same failure appears in baseline `logs/test-runs/pytest-20260426-154852.log`, so it is not a WS-A regression.

## Property-Based Tests

- `tests/test_property_marker_discipline.py` now checks every `@given` test under `tests/` recursively.
- `tests/conftest.py` emits a collection warning for unmarked Hypothesis tests.
- `scripts/mark_hypothesis_property_tests.py` preserves existing newline bytes and recursively marks property tests without broad formatting churn.

## Files Changed

- `propstore/uri_authority.py`
- `propstore/uri.py`
- `propstore/repository.py`
- `propstore/canonical_namespaces.py`
- `propstore/source/claims.py`
- `propstore/app/concepts/mutation.py`
- `propstore/concept_ids.py`
- `propstore/sidecar/schema.py`
- `propstore/world/model.py`
- `schema/generate.py`
- `schema/generated/*.schema.json`
- `propstore/_resources/schemas/*.schema.json`
- `tests/conftest.py`
- `tests/test_required_schema_completeness.py`
- `tests/test_fixture_schema_parity.py`
- `tests/test_generated_schema_freshness.py`
- `tests/test_property_marker_discipline.py`
- `tests/test_uri_authority_validation.py`
- `tests/test_no_privileged_namespace.py`
- `tests/test_source_cannot_mint_canonical_ids.py`
- `tests/test_workstream_a_done.py`
- `scripts/mark_hypothesis_property_tests.py`
- `pyproject.toml`
- `uv.lock`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-A-schema-fidelity.md`

## Remaining Risks / Successors

- No WS-A findings are deferred.
- The repo still has unrelated dirty state: tracked `CLAUDE.md` is deleted. That keeps the full suite from returning exit code 0 until the user-owned deletion is resolved.
