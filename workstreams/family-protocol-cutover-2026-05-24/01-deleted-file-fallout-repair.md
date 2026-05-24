# 01 Deleted-File Fallout Repair

## Prerequisites


## Target

Keep these deletions:

- `propstore/families/world_charters.py`
- `propstore/families/claims/metadata.py`

Repair their callers by moving real behavior to its owner.

## Required Moves

World schema fallout:

- Move each old `FamilyCharter` definition from the deleted world-charters
  history into the owning family charter module: claims, concepts, contexts,
  sources, relations, micropublications, rules, calibration, diagnostics,
  embeddings, forms, and derived-store meta.
- Compose the complete Propstore derived-store `SchemaCatalog` through the
  existing family registry/charter owner.
- Expose registry-level schema access for the whole derived store. The access
  point is generic registry composition, not a claim/world-specific wrapper.
- Move `PROPSTORE_WORLD_META_KEY`, `PROPSTORE_WORLD_SCHEMA_VERSION`, and
  `WorldMeta` to a derived-store meta owner or registry-owned meta charter.

Claim metadata fallout:

- Delete imports of `propstore.families.claims.metadata`.
- Replace `claim_metadata_value(claim, key)` in `propstore/preference.py`,
  `propstore/praf/engine.py`, and `propstore/world/resolution.py` with typed
  claim-family/world-analysis behavior.
- PrAF opinion, confidence, sample-size, probability, and source-quality data
  are typed fields/properties or typed analyzer inputs. They are not string-key
  metadata lookups.

## Deletion-First Execution

1. Run the import gates below and record exact hits.
2. Add or move family charter ownership to the exact family owners. Use the
   deleted file only as historical source material for moves, not as a module
   to restore.
3. Update production imports from `propstore.families.world_charters` to the
   registry/charter owner.
4. Update test helpers to use the same public registry/charter owner as
   production.
5. Delete `claim_metadata_value` call sites and repair each failure with typed
   behavior.
6. Run the narrow type gates.

## Search Gates

```powershell
rg -n -F -- "from propstore.families.world_charters" propstore tests
rg -n -F -- "propstore.families.world_charters" propstore tests scripts
rg -n -F -- "from propstore.families.claims.metadata" propstore tests
rg -n -F -- "claim_metadata_value" propstore tests
```

## Type/Test Gates

```powershell
uv run pyright propstore/world/model.py propstore/world/resolution.py propstore/preference.py propstore/praf/engine.py propstore/compiler/workflows.py
powershell -File scripts/run_logged_pytest.ps1 -Label deleted-file-fallout tests/test_world_query.py tests/test_build_sidecar.py tests/test_source_trust.py
```

## Completion

- Deleted modules remain absent.
- No production import mentions either deleted module.
- World schema creation comes from family charter/registry composition.
- Claim metadata access is typed behavior, not a string-key helper.
