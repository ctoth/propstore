# 12 Final Gates

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
- `11-concept-local-id-compatibility-fixtures.md`

## Target

Prove the nested family protocol cutover is complete and that the parent
SQLAlchemy charter cutover still has a valid ordered control surface.

## Required Search Gates

Run every search gate in phases 1-11. Production hits in forbidden surfaces are
failures. Workstreams, reports, notes, and generated historical manifests do
not satisfy production gates.

Additional final searches:

```powershell
rg -n -F -- "from propstore.families.documents" propstore tests
rg -n -F -- "DocumentStruct" propstore/families propstore/source propstore/worldline propstore/support_revision propstore/core
rg -n -F -- "metadata={\"payload\"" propstore tests
rg -n -F -- "metadata={\"document\"" propstore tests
rg -n -F -- "metadata={\"artifact\"" propstore tests
rg -n -F -- "payload_rest" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionTable" propstore tests
```

## Order Gates

```powershell
uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md
uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04c-family-protocol-cutover/00-index.md
```

## Type/Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-protocol-cutover-full
uv run pks build
```

## Dependency Gates

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
git ls-remote https://github.com/ctoth/quire <pinned-sha>
```

## Completion

- Quire is pinned to a pushed commit.
- Generated documents, lifecycle transitions, graph/artifact protocols, local
  IDs, and schema lookup are generic family infrastructure.
- Real Propstore knowledge artifacts build through the generated protocol.
- Propstore has no duplicate family document DTO layer, no restored deleted
  modules, no string-key claim metadata helper, and no root helper ownership of
  source/proposal/worldline/graph/artifact mechanics.
