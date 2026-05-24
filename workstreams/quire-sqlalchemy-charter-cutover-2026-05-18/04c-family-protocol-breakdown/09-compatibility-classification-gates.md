# 09 Compatibility Classification Gates

## Final State

Every production `legacy`, compatibility, fallback, and broad `coerce_*` hit is
classified as one of:

- `io-boundary`: request, CLI, file, journal, JSON, YAML, or external-row
  parsing before semantic code.
- `semantic-owner`: domain canonicalization owned by the module's semantic
  type system.
- `delete`: illegal compatibility, shim, fallback reader, old/new dual path, or
  helper-shaped coercion.

Every `delete` hit is then removed. No generic exception category exists.

## Delete First

Delete illegal compatibility hits as they are found. Do not rename them into a
new helper-shaped spelling.

## Search Gates

```powershell
rg -n -F -- "legacy" propstore tests
rg -n -F -- "backward compat" propstore tests
rg -n -F -- "backwards compat" propstore tests
rg -n -F -- "compat shim" propstore tests
rg -n -F -- "fallback" propstore tests
rg -n -- "\bcoerce_[A-Za-z0-9_]+" propstore tests
```

These are classification gates first. After classification, every production
`delete` hit becomes a zero-hit gate.

## Required Output During Execution

Each production hit is recorded in this file under one table:

| Surface | Classification | Owner or deletion target |
| --- | --- | --- |

The table is updated before moving to `10-final-gates.md`.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label compatibility-classification tests/test_world_query.py tests/test_worldline.py tests/test_praf.py tests/test_source_claims.py tests/test_source_relations.py
```

## Completion

- [ ] Every production hit is classified.
- [ ] Every `delete` hit is removed.
- [ ] No compatibility shim, fallback reader, alias, adapter, or old/new dual
      path remains.
- [ ] Search, type, and test gates pass.
