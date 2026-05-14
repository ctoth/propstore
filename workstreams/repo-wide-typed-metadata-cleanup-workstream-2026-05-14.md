# Repo-Wide Typed Metadata Cleanup Workstream

## Goal

Clean up repeated semantic field declarations, duplicated row/payload shapes,
and raw storage ownership across the repo using a deletion-first workflow.

The target is not "move sidecar code somewhere else." The target is one typed
owner declaration for each durable semantic surface, with generated or derived
storage/search/vector/query shapes where appropriate.

## Control Documents

- Inventory notes:
  `workstreams/repo-wide-typed-metadata-cleanup-inventory-2026-05-14.md`
- Mechanical scanner:
  `uv run scripts/typed_metadata_inventory.py --format markdown --limit 80`

Before every implementation commit, reread this workstream and the inventory
notes. After every commit, rerun or reread the mechanical inventory for the
current target and update the next unchecked item.

## Definitions

- `red storage leak`: raw storage mechanics outside the storage/query owner:
  `sqlite3`, `connect_sidecar`, `connect_sidecar_readonly`, `row_factory`, or
  direct `.execute("SELECT ...")` over projection tables outside
  `propstore/sidecar` or the future owner module.
- `yellow derived-store coupling`: typed calls to current sidecar APIs such as
  `materialize_world_sidecar`, `collect_authoring_lints`, or projection
  constants used for diagnostics. Yellow hits are not deletion targets until
  ownership is explicitly reassigned.
- `repeated declaration`: the same semantic field, nullability/default/check,
  JSON shape, enum coercion, FTS text source, vector text source, or query row
  shape spelled by more than one owner.
- `typed owner`: exactly one of Quire artifact/family metadata, Propstore
  semantic artifact metadata, Propstore derived-store projection metadata,
  runtime/wire report metadata, or IO-boundary codec metadata.

## Current Mechanical Inventory

Last observed command:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
```

Top package metrics from that run:

| Package | Lines | Projection Columns | Raw SQL Score | Codec Methods | Mapping Hints | Row Classes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `world` | 11654 | 0 | 85 | 2 | 27 | 29 |
| `app` | 10536 | 0 | 54 | 5 | 52 | 172 |
| `core` | 10061 | 0 | 0 | 59 | 39 | 12 |
| `families` | 8797 | 0 | 0 | 57 | 70 | 4 |
| `cli` | 7784 | 0 | 0 | 0 | 2 | 0 |
| `sidecar` | 5273 | 208 | 142 | 0 | 2 | 9 |
| `source` | 4227 | 0 | 14 | 0 | 14 | 2 |
| `support_revision` | 4225 | 0 | 0 | 28 | 41 | 6 |
| `worldline` | 3131 | 0 | 0 | 33 | 31 | 1 |
| `heuristic` | 2657 | 0 | 33 | 0 | 2 | 1 |
| `grounding` | 2284 | 0 | 0 | 0 | 2 | 5 |
| `conflict_detector` | 1977 | 0 | 0 | 3 | 3 | 1 |
| `aspic_bridge` | 1711 | 0 | 0 | 0 | 2 | 1 |
| `merge` | 1515 | 0 | 2 | 2 | 4 | 0 |
| `provenance` | 1408 | 0 | 0 | 8 | 8 | 6 |
| `web` | 1396 | 0 | 0 | 0 | 0 | 1 |
| `compiler` | 1110 | 0 | 0 | 0 | 8 | 2 |
| `opinion.py` | 768 | 0 | 0 | 0 | 0 | 0 |

Highest declaration-density files:

| Path | Score | Reason |
| --- | ---: | --- |
| `propstore/sidecar/claims.py` | 71 | projection columns |
| `propstore/sidecar/concepts.py` | 48 | projection columns |
| `propstore/families/documents/sources.py` | 40 | codecs and mapping hints |
| `propstore/worldline/result_types.py` | 38 | runtime/wire codecs |
| `propstore/app/concepts/mutation.py` | 34 | request/report rows and mappings |
| `propstore/core/row_types.py` | 34 | row coercion boundary |
| `propstore/world/queries.py` | 24 | request/report rows |
| `propstore/families/claims/documents.py` | 24 | document codecs |
| `propstore/core/graph_types.py` | 24 | graph codecs |
| `propstore/support_revision/history.py` | 23 | journal codecs |

Red storage leaks outside sidecar:

| Path | Score | Tables/Surfaces |
| --- | ---: | --- |
| `propstore/world/model.py` | 82 | world read model over most projection tables |
| `propstore/app/concepts/mutation.py` | 23 | concept, alias, FTS lookup |
| `propstore/heuristic/embed.py` | 16 | embedding store connection plumbing |
| `propstore/source/status.py` | 14 | `claim_core`, `build_diagnostics` |
| `propstore/heuristic/relate.py` | 13 | `claim_core`, `claim_text_payload` |
| `propstore/app/claims.py` | 12 | embedding/similarity connection plumbing |
| `propstore/app/concepts/display.py` | 10 | concept FTS display query |
| `propstore/app/concepts/embedding.py` | 9 | concept embedding connection plumbing |
| `propstore/heuristic/calibrate.py` | 4 | calibration projection |
| `propstore/world/queries.py` | 3 | sqlite error coupling |
| `propstore/merge/structured_merge.py` | 2 | grounding sidecar coupling |

Repeated projection field files:

| Field | File Count |
| --- | ---: |
| `id` | 6 |
| `conditions_cel` | 4 |
| `seq` | 4 |
| `claim_id` | 3 |
| `context_id` | 3 |
| `kind` | 3 |
| `name` | 3 |
| `provenance_json` | 3 |
| `source_id` | 3 |
| `concept_id` | 2 |
| `conditions_ir` | 2 |
| `content_hash` | 2 |
| `logical_ids_json` | 2 |
| `primary_logical_id` | 2 |
| `source_kind` | 2 |
| `source_slug` | 2 |
| `status` | 2 |
| `target_id` | 2 |
| `type` | 2 |
| `version_id` | 2 |

Core row-type blast radius:

- `propstore/core/row_types.py` is imported by world, app, ASPIC bridge, PRAF,
  graph export/build, support revision, worldline, merge, relation analysis,
  sensitivity, and sidecar embedding code.
- It is not a deletion target until a generated or explicit typed boundary
  preserves enum coercion and required-field behavior.

Top test pins:

- `tests/test_build_sidecar.py`
- `tests/test_graph_build.py`
- `tests/conftest.py`
- `tests/remediation/phase_7_race_atomicity/test_T7_5e_promotion_blocked_fk_payload.py`
- `tests/web_demo_fixture.py`
- `tests/test_relate_opinions.py`
- `tests/test_codex2_claim_dedupe_diverges_on_version.py`
- `tests/test_world_query.py`
- `tests/test_render_policy_filtering.py`
- `tests/test_cli_render_policy_flags.py`

CLI request/report adapter hotspots:

| Path | Request/Report Calls | Interpretation |
| --- | ---: | --- |
| `propstore/cli/world/revision.py` | 13 | CLI presentation adapter over app revision APIs |
| `propstore/cli/concept/mutation.py` | 9 | CLI presentation adapter over concept mutation APIs |
| `propstore/cli/world/atms.py` | 7 | CLI presentation adapter over ATMS app APIs |
| `propstore/cli/world/analysis.py` | 7 | CLI presentation adapter over world analysis app APIs |
| `propstore/cli/world/query.py` | 6 | CLI presentation adapter over world query app APIs |
| `propstore/cli/source/lifecycle.py` | 6 | CLI presentation adapter over source lifecycle APIs |
| `propstore/cli/world/reasoning.py` | 5 | CLI presentation adapter over world reasoning APIs |
| `propstore/cli/source/proposal.py` | 4 | CLI presentation adapter over source proposal APIs |
| `propstore/cli/source/batch.py` | 4 | CLI presentation adapter over source batch APIs |
| `propstore/cli/rule/mutation.py` | 4 | CLI presentation adapter over rule mutation APIs |

Additional surface classifications:

| Surface | Current Classification | Cleanup Rule |
| --- | --- | --- |
| `propstore/grounding/` | reasoning/runtime domain logic | Do not fold into derived-store metadata unless it declares persisted row shape. |
| `propstore/conflict_detector/` | semantic detector models and outputs | Inventory field duplication, but preserve detector semantics. |
| `propstore/aspic_bridge/` | argumentation bridge over typed rows | Preserve `core.row_types` coercion inputs. |
| `propstore/provenance/` | provenance codecs and records | Treat as semantic/wire metadata, not sidecar metadata by default. |
| `propstore/web/` | presentation surface | Only clean if it builds semantic rows or owns storage/query behavior. |
| `propstore/compiler/` | workflow orchestration and typed reports | Yellow sidecar coupling is allowed until owner API is reassigned. |
| `propstore/importing/` | IO/import boundary | Mapping codecs are expected; keep them at the boundary. |
| `propstore/opinion.py` | subjective-logic semantic owner | Opinion projection fields should reference this semantic owner. |
| `propstore/sidecar/quarantine.py` | current derived-store diagnostic writer | In-owner SQL until diagnostic writer is moved/generated. |
| `propstore/sidecar/sqlite.py` | current SQLite connection owner | In-owner SQL until Quire fully owns connection policy. |
| `propstore/sidecar/query.py` | explicit raw sidecar inspection command backend | Keep as deliberate escape hatch unless product policy deletes raw SQL query. |

`propstore/core/row_types.py` importer count: 36 files. This is the blast
radius gate for any row-type consolidation.

## Hard Gates

1. Mechanical inventory gate:
   - Run `uv run scripts/typed_metadata_inventory.py --format markdown --limit 80`.
   - The current target file or package must appear in the relevant inventory
     section before it is edited.
   - If the scanner misses a surface discovered during manual inspection,
     update the scanner first and commit it.

2. Ownership classification gate:
   - Every candidate field/type/query/codec in the current slice is classified
     as one of:
     - Quire artifact/family metadata
     - Propstore semantic artifact metadata
     - Propstore derived-store projection metadata
     - runtime/wire report metadata
     - IO-boundary codec metadata
   - No slice may consolidate across these categories without a written reason.

3. Runtime-vs-persisted gate:
   - Before deleting or generating a dataclass/codec, prove whether it is a
     persisted artifact, derived-store row, runtime report, wire report, or
     IO-boundary codec.
   - Runtime reports are not folded into projection declarations.

4. Enum-coercion gate:
   - If a row type currently calls a `coerce_*` function or enforces required
     fields, the replacement must preserve that behavior at the same boundary.

5. Source-local gate:
   - Before hard-failing source-local shape, inspect
     `propstore/source/promote.py` blocked-row and `sidecar_mirror_ok`
     behavior.
   - The workstream may delete diagnostic mirroring only with a replacement
     source promotion contract and tests.

6. Test-pinning gate:
   - Each slice names the tests that pin the old surface.
   - Update tests only after deleting the old production surface and replacing
     callers.

7. Deletion-first gate:
   - Delete the old production surface for the current target first.
   - Use type, test, and search failures as the work queue.
   - Do not add wrappers, aliases, fallback readers, bridge normalizers, dual
     paths, or compatibility shims.

8. Kept-reduction gate:
   - A slice completes only if the target metric improves:
     - fewer red storage leaks for SQL slices;
     - fewer projection columns or repeated projection fields for declaration
       slices;
     - fewer removable custom codecs for payload slices;
     - fewer app/CLI semantic row builders for presentation-boundary slices.
   - If a slice cannot keep a reduction, revert that slice before moving on.

## Dependency Order

The execution order is:

1. Complete mechanical inventory coverage.
2. Classify owner categories for all high-density surfaces.
3. Remove red storage leaks from app/source/heuristic before compressing
   `WorldQuery`.
4. Consolidate concept declaration metadata before claim metadata.
5. Consolidate claim metadata only after claim YAML fixtures or equivalent
   round-trip tests exist.
6. Consolidate FTS/vector metadata after concept/claim declarations own their
   search and embedding text sources.
7. Compress sidecar projection declarations after typed metadata exists.
8. Compress `core/row_types.py` only after typed row generation/coercion is
   proven and every importer is accounted for.
9. Audit runtime/wire codecs separately from derived-store metadata.
10. Final line-count, inventory, pyright, targeted tests, and full-suite gates.

## Phase 1: Inventory Coverage

Status: completed for planning.

Completed evidence:

- Scanner run with limit 80.
- Scanner covers package metrics, repeated projection fields, declaration
  density, red storage leaks, yellow sidecar API coupling, core row-type
  importers, CLI request/report adapter calls, and test pins.
- CLI module rows are inventoried as presentation adapters.
- Previously missing surfaces are classified in this workstream.
- `propstore/core/row_types.py` has 36 importing files.
- Test-pin table is generated mechanically by the scanner.

Gate result:

- There are no unclassified missing inventory surfaces in this workstream.
- If a future slice discovers a missed category, update the scanner first,
  commit it, rerun the scanner, and update this workstream before editing
  production code.

## Phase 2: Owner Classification Ledger

Status: pending.

Tasks:

- For every file in the highest declaration-density table, classify each
  repeated declaration family.
- For every red storage leak, choose the typed owner API that should replace
  direct SQL.
- For every runtime/wire codec hit, mark it out of derived-store cleanup unless
  a persisted/materialized path is proven.

Gate:

- Each high-density file has a written target owner and a deletion proof.

## Phase 3: Red Storage Leak Removal

Status: pending.

Ordered slices:

1. `propstore/app/concepts/display.py`
2. `propstore/app/concepts/mutation.py`
3. `propstore/app/concepts/embedding.py`
4. `propstore/app/claims.py`
5. `propstore/source/status.py`
6. `propstore/heuristic/relate.py`
7. `propstore/heuristic/calibrate.py`
8. `propstore/heuristic/embed.py`
9. `propstore/merge/structured_merge.py`

Gate per slice:

- Delete direct SQL or direct sidecar connection use from the target.
- Replace with a typed owner-layer API.
- Rerun scanner and prove the target's red storage leak score decreased.
- Run focused tests for the target path.
- Commit atomically.

## Phase 4: Concept Metadata Consolidation

Status: pending.

Target surfaces:

- `propstore/families/registry.py`
- `propstore/families/concepts/stages.py`
- `propstore/families/concepts/passes.py`
- `propstore/sidecar/concepts.py`
- `propstore/core/row_types.py` concept surfaces only
- app concept view/mutation reports
- concept FTS and concept embedding text sources

Gate:

- One concept metadata owner drives projection shape, row decoding input,
  FTS source text, vector source text, and app query/report field subsets.
- Existing `ConceptRow` coercion behavior remains available to all importers.

## Phase 5: Claim Metadata Consolidation

Status: pending.

Precondition:

- Add or locate claim YAML round-trip fixtures. The current local `knowledge/`
  checkout does not contain claim YAML files, so flat-vs-proposition claim
  shape cannot be inferred from local sample data.

Target surfaces:

- `propstore/families/claims/documents.py`
- `propstore/families/documents/sources.py`
- `propstore/source/claims.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/core/row_types.py` claim surfaces only
- claim FTS and claim embedding text sources

Gate:

- Preserve the load-bearing `claim_core`, numeric payload, text payload, and
  algorithm payload split unless a proof deletes it.
- Remove only duplicated Python declaration/codecs that can be generated or
  owned once.

## Phase 6: FTS and Vector Metadata

Status: pending.

Tasks:

- Move FTS field selection into semantic metadata for concepts and claims.
- Move embedding text source and freshness metadata into semantic metadata.
- Keep Quire owning generic FTS/vector table mechanics.

Gate:

- `propstore/sidecar/embedding_store.py` no longer owns generic sqlite-vec
  declaration mechanics.
- App/heuristic code no longer assembles table-specific search/vector storage
  policy directly.

## Phase 7: Sidecar Projection Compression

Status: pending.

Tasks:

- Replace repeated `ProjectionColumn(...)` declarations with typed metadata
  generation.
- Keep per-role nullability/default/FK/check semantics explicit in the metadata.
- Do not replace repeated fields with naive full-column constants.

Gate:

- Repeated projection field count decreases.
- Projection tests still pass.

## Phase 8: Runtime/Wire Codec Audit

Status: pending.

Targets:

- `propstore/worldline/result_types.py`
- `propstore/worldline/revision_types.py`
- `propstore/support_revision/history.py`
- `propstore/support_revision/snapshot_types.py`
- `propstore/support_revision/explanation_types.py`
- `propstore/support_revision/state.py`
- `propstore/core/graph_types.py`
- `propstore/epistemic_process.py`

Gate:

- Runtime/wire reports are classified and left alone unless they leak semantic
  mappings across subsystem boundaries.
- Any deletion preserves journal/hash/replay semantics.

## Phase 9: Final Gates

Status: pending.

Commands:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label typed-metadata-cleanup-targeted tests/test_build_sidecar.py tests/test_world_query.py tests/test_sidecar_projection_contract.py tests/test_sidecar_projection_fts_contract.py tests/test_sidecar_projection_vec_contract.py tests/test_relate_opinions.py
powershell -File scripts/run_logged_pytest.ps1 -Label typed-metadata-cleanup-full
```

Completion requires:

- all phase gates complete;
- no old production path coexists with its replacement;
- scanner metrics show kept reductions for the targets actually changed;
- pyright passes;
- targeted tests pass;
- full suite passes.
