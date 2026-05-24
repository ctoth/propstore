# 11 Concept Local ID Compatibility Fixtures

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`
- `06-source-lifecycle-state-machines.md`
- `07-proposal-lifecycle-state-machines.md`
- `08-artifact-graph-verification-export.md`
- `09-worldline-resolution-protocol.md`
- `10-context-lifting-justification-views.md`

## Target

Numeric concept handles are concept-family identity behavior backed by generic
Quire local-id reservation. Compatibility, fallback, broad coercion, and dict
fixtures do not preserve old shapes.

## Deletion Targets

- root `propstore/concept_ids.py`
- concept document scanning for numeric handles
- git counter mechanics owned by a concept-specific root module
- compatibility shims and fallback readers not classified as IO boundaries
- broad `coerce_*` paths that repair old shapes or duplicate type-system work
- `tests/test_world_query.py` dict-shaped `claim["..."]` mutations

## Required Owners

- Concept family identity owns numeric local-id policy.
- Quire owns generic local-id reservation mechanics.
- IO boundaries parse YAML/JSON/SQLite rows once into typed records.
- Tests construct typed domain/family objects, not dict-shaped claim payloads
  past IO.

## Execution

1. Move concept numeric reservation policy under concept family identity.
2. Replace root concept-id callers with concept-family identity API backed by
   generic Quire reservation.
3. Delete `propstore/concept_ids.py`.
4. Classify every compatibility/fallback/coercer hit as `io-boundary`,
   `semantic-owner`, or `delete`.
5. Delete illegal compatibility/fallback/coercer hits.
6. Replace dict-shaped world-query claim fixture mutation with typed fixtures.

## Search Gates

```powershell
rg -n -F -- "propstore.concept_ids" propstore tests
rg -n -F -- "candidate_concept_id_for_repo" propstore tests
rg -n -F -- "reserve_concept_id_candidate" propstore tests
rg -n -F -- 'claim["' tests/test_world_query.py
rg -n -F -- "legacy" propstore tests
rg -n -F -- "backward compat" propstore tests
rg -n -F -- "backwards compat" propstore tests
rg -n -F -- "compat shim" propstore tests
rg -n -F -- "fallback" propstore tests
rg -n -- "\bcoerce_[A-Za-z0-9_]+" propstore tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label concept-local-id-compat tests/test_T7_4_concept_id_counter.py tests/test_git_backend.py tests/test_no_privileged_namespace.py tests/test_world_query.py
```

## Completion

- Root concept-id module is gone.
- Compatibility/fallback/coercer inventory is resolved by owner.
- World-query tests no longer preserve dict-shaped claim assumptions.
