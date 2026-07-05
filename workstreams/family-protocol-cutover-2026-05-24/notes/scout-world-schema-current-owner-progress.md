# Scout progress — world schema current owner

Date: 2026-05-24

## What I know (cumulative)

### Tree state
- HEAD = `e13e302d195ddf38bbde5c965744e992ae57166b`. No tracked-file modifications. No agent collisions.

### Deletion provenance
- `propstore/families/world_charters.py` was deleted in commit `30e7d242666536d5fabc305b4cc548cf8d25c628` ("Delete duplicated world charter surface"), 2026-05-24 15:25 -0600.
- Last living revision saved as `notes/world_charters_last_living.py` (931 lines).

### Pyright log evidence (notes/scout-pyright-20260524T230935Z.log)
- ALL EIGHT `world_charters` imports fail to resolve today (`reportMissingImports`). Exact file:col for each is in the log. The three `claim_metadata_value` imports also unresolved (out of scope here).

### Symbols the deleted module exposed (top-level, public)
From last-living file head + grep:
- Constants: `PROPSTORE_WORLD_SCHEMA_VERSION = 6` (line 62), `PROPSTORE_WORLD_META_KEY = "sidecar"` (line 63), `_WORLD_CONTRACT_VERSION` (line 64, private).
- Class: `WorldMeta(FamilyModel)` (line 67).
- Functions: `world_charter_catalog() -> SchemaCatalog` (line 72, lru_cache), `world_sqlalchemy_schema() -> SqlAlchemySchema` (line 444, lru_cache).
- Private helpers: `_charter`, `_world_family`, `_f`, `_i`, `_r`, `_b`, `_fk`, `_claim_models`, `_claim_core_charter`, `_claim_payload_charters`, `_claim_source_assertion_charter`, `_support_charters`, plus `_CONCEPT_FTS_SOURCE_QUERY`, `_CLAIM_FTS_SOURCE_QUERY` module-level string constants.

### Per-site imports confirmed (HEAD)
1. `propstore/app/concepts/display.py:30` — `from propstore.families.world_charters import world_sqlalchemy_schema`. Usage: `:50` `schema = world_sqlalchemy_schema()` then `:51` `concept = schema.model("concept")`.
2. `propstore/compiler/workflows.py:88-93` — imports `PROPSTORE_WORLD_META_KEY, PROPSTORE_WORLD_SCHEMA_VERSION, WorldMeta, world_sqlalchemy_schema`. Usage at `:288, :294, :595, :609-611`.
3. `propstore/source/status.py:18` — imports `world_sqlalchemy_schema`. Usage at `:54`.
4. `propstore/families/claims/sidecar_runtime.py:11` — imports `world_sqlalchemy_schema`. Usage at `:77, :115`.
5. `propstore/families/contexts/declaration.py:188` — imports `world_sqlalchemy_schema` (inside function `load_lifting_system`). Usage at `:190-193`.
6. `propstore/families/concepts/sidecar_runtime.py:9` — imports `world_sqlalchemy_schema`. Usage at `:32`.
7. `propstore/families/embeddings/declaration.py:39` — NOT YET READ (still to read).
8. `propstore/world/model.py:53` — NOT YET READ.

## Still to do

1. Read `propstore/families/embeddings/declaration.py` import block + usages of imported symbol.
2. Read `propstore/world/model.py` import block + usages of imported symbol.
3. Read all of `propstore/families/registry.py` to enumerate schema/catalog access surface.
4. Grep `propstore/` for `PROPSTORE_WORLD_META_KEY`, `PROPSTORE_WORLD_SCHEMA_VERSION`, `WorldMeta`, `world_charter_catalog`, `world_sqlalchemy_schema` to locate current homes (or confirm ORPHAN).
5. Identify the current composition site for the world-level SchemaCatalog (may be `propstore/families/registry.py`, may be nowhere).
6. Write deliverable.

## Observations to thread into the deliverable
- Several sites use `world_sqlalchemy_schema()` ONLY to then call `.model("X")` or `.table("X")` — those are also V005-V009 (separate slice). Slice A only needs to re-route the import; semantic cleanup of `.model("X")` is Slice B.
- `propstore/compiler/workflows.py` is the heaviest consumer: it both BUILDS the schema (`:288, :595`) AND writes meta rows (`:609-611`) using `WorldMeta(key=..., schema_version=...)`. This is the one that proves whether `PROPSTORE_WORLD_META_KEY`/`WorldMeta`/`PROPSTORE_WORLD_SCHEMA_VERSION` need first-class re-exposure or whether the registry can offer a single `world_meta_row()` builder.
- `propstore/families/contexts/declaration.py:188` does the import INSIDE the function (deferred), suggesting circular-import concern; this is a HAZARD for Slice C in section 9.

## Blockers
None.
