# 01 Deleted File Fallout

## Final State

`propstore/families/world_charters.py` and
`propstore/families/claims/metadata.py` remain deleted. No replacement module,
alias, wrapper, adapter, fallback reader, or compatibility function is created.

World schema/catalog access comes from the existing family registry and Quire
charter/schema catalog owner. Claim metadata access comes from typed claim,
world, preference, and PrAF domain behavior.

## Delete First

Delete every production import and use of the deleted modules:

- `from propstore.families.world_charters ...`
- `propstore.families.world_charters`
- `from propstore.families.claims.metadata ...`
- `claim_metadata_value`

## Repair Owners

- `propstore/world/model.py`, compiler workflows, source status, sidecar
  runtime, contexts, embeddings, and tests obtain schema/catalog data through
  the family registry/Quire charter catalog.
- `propstore/world/resolution.py`, `propstore/preference.py`, and
  `propstore/praf/engine.py` obtain opinion/confidence/preference inputs from
  typed claim/world/analyzer objects or claim-family behavior.

## Search Gates

```powershell
rg -n -F -- "from propstore.families.world_charters" propstore tests
rg -n -F -- "propstore.families.world_charters" propstore tests scripts
rg -n -F -- "from propstore.families.claims.metadata" propstore tests
rg -n -F -- "claim_metadata_value" propstore tests
```

All four gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore/world/model.py propstore/world/resolution.py propstore/preference.py propstore/praf/engine.py propstore/source/status.py
powershell -File scripts/run_logged_pytest.ps1 -Label deleted-file-fallout tests/test_world_query.py tests/test_worldline.py tests/test_praf.py tests/test_preference.py tests/test_cli_source_status.py
```

## Completion

- [ ] Deleted modules still absent.
- [ ] All import/use gates above are zero-hit.
- [ ] No new world-charter or claim-metadata helper module exists.
- [ ] Type and test gates pass.
