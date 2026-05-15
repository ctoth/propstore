# Repo-Wide Typed Metadata Cleanup Workstream

## Goal

Clean up repeated semantic field declarations, duplicated row/payload shapes,
and raw storage ownership across the repo using a deletion-first workflow.

The target is not "move sidecar code somewhere else." The target is one typed
owner declaration for each durable semantic surface, with generated or derived
storage/search/vector/query shapes where appropriate.

This workstream is documentation-only until Phase 2 and the required
scanner/baseline work are complete. No production code may be edited from this
workstream until the owner ledger, baseline metrics, slice test map, old-path
search gates, and Quire dependency slices are written here and committed.

## Ownership Boundary

Family declarations and field descriptors live in
`propstore/families/<family>/declaration.py` or the family registry only when
the declaration is truly family-wide. The Propstore generator lives under a
dedicated family/declaration generation package. Generated outputs are ordinary
Python modules under family-owned packages: projection declarations, FTS/vector
roles, typed query APIs, and row coercion modules.

Generic schema, SQL, FTS, vector, connection, and derived-store lifecycle
mechanics live in Quire. Identity, reference, FK, version, and content-hash
fields are owned by Quire family/reference metadata and may not be re-declared
inside Propstore as independent semantic fields.

No file outside the declaration/generator owner may declare a
`ProjectionColumn`, a row class for a derived-store row, enum coercion for a
derived-store row, FTS/vector storage policy, or raw SQL literal over a
derived-store table.

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
- `single declaration`: one typed metadata source of truth for a semantic
  surface. Generated row types, generated projection columns, generated query
  inputs, generated FTS/vector declarations, and generated render subsets are
  allowed; handwritten parallel declarations are not.
- `beautiful abstraction`: a declaration that removes a real repeated semantic
  decision. A renamed wrapper, a column constant with flags still repeated
  elsewhere, or a helper that just moves SQL strings into another module is not
  a beautiful abstraction.

## Target Abstraction

The target abstraction is a typed semantic metadata declaration graph:

1. Quire owns generic declaration execution:
   - artifact family/reference mechanics;
   - derived-store lifecycle and cache hashing primitives;
   - projection/FTS/vector declaration primitives;
   - generated SQLite DDL and insert/read plumbing;
   - machine-readable inventory output for gates.

2. Propstore owns semantic declarations:
   - semantic object identity and family membership;
   - field meaning, type, nullability, default, enum/coercion policy, and
     source-local/canonical visibility;
   - semantic references using Quire family reference/FK APIs;
   - semantic extraction from artifacts;
   - FTS and embedding text meaning;
   - query behavior that is genuinely domain reasoning.

3. Generated surfaces may include:
   - projection table/column declarations;
   - FTS/vector declarations;
   - row decoders that preserve existing enum coercion boundaries;
   - typed read-model query inputs/results;
   - app/report field subsets when they are pure views of semantic metadata.

4. Non-target surfaces stay separate:
   - runtime/wire reports;
   - journal/hash/replay codecs;
   - IO/import codecs at repository boundaries;
   - raw sidecar inspection if product policy keeps it as an escape hatch.

The abstraction must delete handwritten duplicate declarations. It must not
collapse source-of-truth artifact identity into derived-store projection shape.

The first real implementation slice must prove the abstraction on one complete
family vertical. It is not acceptable to delete app SQL first and replace it
with a hand-written typed API that will be deleted again when declarations
arrive. The replacement API must be generated from the single declaration, or
import only field descriptors from it while declaring no column/type/role
knowledge of its own.

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

0. Documentation readiness gate:
   - Before any production code edit, this workstream must contain:
     - a committed baseline metrics block;
     - the Phase 2 owner classification ledger;
     - a slice-level focused test map;
     - old-path search gates for every deletion slice;
     - Quire-vs-Propstore dependency split;
     - stop/revert rules.
   - If any of those are missing, implementation is blocked.

1. Mechanical inventory gate:
   - Run `uv run scripts/typed_metadata_inventory.py --format markdown --limit 80`.
   - The current target file or package must appear in the relevant inventory
     section before it is edited.
   - If the scanner misses a surface discovered during manual inspection,
     update the scanner first and commit it.
   - Before implementation, extend the scanner to emit JSON and commit a
     baseline artifact. Markdown is acceptable for planning, not for gates.

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
   - Within a vertical slice, declaration/generator work may be developed in
     the same slice, but the commit that introduces the replacement production
     surface must also delete the old production surface. No completed slice may
     leave both old and new production surfaces present.

8. Kept-reduction gate:
   - A slice completes only if the target metric improves:
     - fewer red storage leaks for SQL slices;
     - fewer projection columns or repeated projection fields for declaration
       slices;
     - fewer removable custom codecs for payload slices;
     - fewer app/CLI semantic row builders for presentation-boundary slices.
   - If a slice cannot keep a reduction, revert that slice before moving on.

9. Old-path absence gate:
   - Every deletion slice must include exact post-change searches proving the
     old surface is gone from the target path.
   - A passing test run does not satisfy this gate.

10. Stop rule:
   - If two consecutive slices on the same target family produce no kept
     reduction, stop the workstream and record the failed gate. Do not widen the
     scope to hide the failure.

11. Quire dependency gate:
   - If a slice requires Quire changes, create and complete the Quire slice
     first.
   - Push Quire before pinning Propstore.
   - Never pin to a local Quire path or local repository.

12. Byte-equivalence gate:
   - Generated projection/schema output must byte-equal the current output
     unless the slice documents an intentional semantic diff.
   - Row coercion from generated row modules must be behavior-equivalent to the
     old `core.row_types` coercion for the fields in the slice.

13. No-new-parallel-type gate:
   - No new `@dataclass`, `msgspec.Struct`, `TypedDict`, or `NamedTuple` may be
     added inside `propstore/app/`, `propstore/world/`, `propstore/heuristic/`,
     `propstore/merge/`, or `propstore/source/` after the family prototype
     begins unless it has a ledger entry classified as `io-boundary-codec` and
     names the boundary file.

14. Yellow sunset gate:
   - Yellow derived-store coupling is not preserved indefinitely.
   - Every yellow hit outside the declaration/generator owner must either move
     behind a generated catalog/API or be explicitly retained as a product
     escape hatch with zero hand-written column/table knowledge.

## Forbidden Patterns

- No compatibility wrapper, alias, fallback reader, dual path, bridge
  normalizer, deprecation shim, or re-export from a deleted module.
- No renamed helper that merely moves an old abstraction.
- No full-column constants that still require callers to restate nullability,
  defaults, FK semantics, check constraints, or role semantics.
- No app/source/heuristic/world/merge SQL replacement that is still hand-coded
  against table names.
- No scanner update in the same commit as the production slice that benefits
  from it.
- If deleting a surface breaks an importer, rewrite the importer in the same
  commit.

## Dependency Order

The execution order is:

1. Complete mechanical inventory coverage.
2. Add machine-readable scanner output and freeze the baseline.
3. Complete the machine-readable owner ledger.
4. Land one complete family vertical prototype on concepts.
5. Land the claims vertical after claim YAML round-trip fixtures exist.
6. Land context, relation, micropublication, source, diagnostic, grounding, and
   rule verticals.
7. Collapse `WorldQuery` direct SQL as the consequence of generated family
   query APIs.
8. Sunset yellow derived-store coupling outside the declaration/generator owner.
9. Rebuild or delete raw sidecar query inspection so it reads the generated
   catalog and owns zero hand-written column names.
10. Final line-count, inventory, pyright, targeted tests, and full-suite gates.

Standalone red-SQL deletion is not a phase. Red SQL is removed inside the
family vertical whose generated typed query surface replaces it. This prevents
deleting SQL into a temporary hand-written API that will be deleted again.

## Phase 1: Inventory Coverage

Status: complete.

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

- Create `workstreams/typed-metadata-owner-ledger-2026-05-15.csv`.
  The ledger date reflects the day the ledger is authored; if authored on a
  later date, use that date consistently in the filename and gate commands.
- After JSON scanner support exists, commit the baseline JSON artifact and link
  it from this phase.
- For every file in the highest declaration-density table, classify each
  repeated declaration family.
- For every red storage leak, choose the typed owner API that should replace
  direct SQL.
- For every runtime/wire codec hit, mark it out of derived-store cleanup unless
  a persisted/materialized path is proven.

Gate:

- Each high-density file has a written target owner and a deletion proof.

### Required Ledger Shape

The owner ledger is machine-readable. Markdown tables in this workstream are
illustrative only. Every ledger row is one `(field x declaring file)` pair, not
one file. Required columns:

- `field_name`
- `declaring_file`
- `declaration_kind`
- `nullability`
- `default`
- `check`
- `fk`
- `enum_coercion`
- `required`
- `current_role`
- `owner_category`
- `target_owner_file`
- `target_descriptor`
- `deletion_proof`
- `pinned_tests`
- `slice_id`
- `status`

Allowed `declaration_kind` values:

- `projection_column`
- `row_class_attr`
- `family_payload_field`
- `request_report_attr`
- `sql_literal`
- `cel_field`
- `fts_source`
- `vector_source`

Allowed `current_role` values:

- `identity`
- `reference`
- `provenance`
- `context`
- `payload_numeric`
- `payload_text`
- `payload_algorithm`
- `diagnostic`
- `search`
- `vector`
- `runtime_report`
- `wire_report`
- `io_boundary`

Allowed `owner_category` values:

- `quire-generic`
- `quire-artifact-family`
- `propstore-semantic-declaration`
- `propstore-derived-store-declaration`
- `typed-row-boundary`
- `typed-query-api`
- `runtime-wire-report`
- `io-boundary-codec`
- `presentation-adapter`
- `delete-without-replacement`

Ledger invariants:

- Every persisted or derived-store `field_name` has exactly one
  `target_owner_file`.
- Every `slice_id` has a non-empty set of rows whose `deletion_proof` count
  drops to one target declaration or zero old declarations.
- Runtime/wire peers are marked separately and never share generated projection
  row types.
- `io-boundary-codec` rows name the actual boundary file.
- Identity/reference/version/content-hash fields are marked
  `quire-artifact-family` unless there is a documented Propstore semantic
  reason.
- Slices do not open until every field in their family is enumerated in the
  CSV.

### Phase-2 Surface Coverage Seed

The CSV ledger required above expands each surface here into per-field rows.
This seed table is not the ledger.

| Surface | Current Owner | Target Owner | Category | Deletion-First Action | Old-Path Search Gate | Focused Tests | Blockers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `propstore/app/concepts/display.py` direct concept FTS SQL | app layer | typed concept search/read-model API | typed-query-api | delete `connect_sidecar_readonly` and direct `conn.execute` use first | `rg -n "connect_sidecar_readonly|conn\\.execute|concept_fts" propstore/app/concepts/display.py` has no red hit | concept search/display CLI and app tests | owner API must exist |
| `propstore/app/concepts/mutation.py` direct concept lookup SQL | app layer | typed concept identity/query API | typed-query-api | delete `connect_sidecar` and direct lookup SQL first | `rg -n "connect_sidecar|conn\\.execute|SELECT .*concept|SELECT .*alias" propstore/app/concepts/mutation.py` has no red hit | concept mutation/search tests | owner API must preserve alias/name/logical-id resolution |
| `propstore/source/status.py` direct sidecar status SQL | source app layer | source status owner API over typed diagnostics/query result | typed-query-api | delete `connect_sidecar` and table checks first | `rg -n "connect_sidecar|sqlite_master|claim_core|build_diagnostics|conn\\.execute" propstore/source/status.py` has no red hit | source status/promotion diagnostic tests | blocked-row semantics must remain |
| `propstore/heuristic/relate.py` direct claim text SQL | heuristic layer | typed claim text/similarity query API | typed-query-api | delete `conn.execute` claim lookups first | `rg -n "conn\\.execute|claim_core|claim_text_payload" propstore/heuristic/relate.py` has no red hit | relate/opinion tests | embedding model contracts |
| `propstore/sidecar/claims.py` projection column duplication | sidecar declarations | `propstore/families/claims/declaration.py` | propstore-derived-store-declaration | delete repeated projection declarations in the claim vertical | `uv run scripts/typed_metadata_inventory.py --format markdown --limit 80` shows lower repeated claim fields | sidecar projection/build/world tests | Quire generator may be required |
| `propstore/sidecar/concepts.py` projection column duplication | sidecar declarations | `propstore/families/concepts/declaration.py` | propstore-derived-store-declaration | delete repeated projection declarations in the concept vertical | scanner shows lower repeated concept fields | concept sidecar/FTS/embedding tests | concept metadata owner first |
| `propstore/core/row_types.py` row coercion boundary | core row type module | `propstore/families/_generated/rows.py` | typed-row-boundary | do not delete until every importer and coercion behavior is proven | `rg -l "propstore.core.row_types|from propstore.core.row_types" propstore` reviewed and updated | world/ASPIC/PRAF/graph/support-revision tests | 36 importers; high risk |
| `propstore/worldline/result_types.py` codecs | worldline runtime layer | runtime/wire report owner | runtime-wire-report | no derived-store deletion by default | N/A unless leak is proven | worldline tests | must not fold into projection metadata |
| `propstore/families/claims/documents.py` custom `to_payload` | family document schema | `propstore/families/claims/declaration.py` | propstore-semantic-declaration | classify each method as semantic transform or removable boilerplate before deletion | `rg -n "def to_payload" propstore/families/claims/documents.py` decreases only for removable boilerplate | claim authoring/roundtrip tests | claim YAML fixtures required |
| `propstore/families/documents/sources.py` source-local payload duplication | source document schema | `propstore/families/sources/declaration.py` | io-boundary-codec | delete only duplicate codecs that do not encode source-local semantics | `rg -n "def to_payload|dict\\[str, Any\\]" propstore/families/documents/sources.py` decreases for boilerplate only | source propose/promote tests | source-local fields are load-bearing |

## Phase 3: Concept Vertical Prototype

Status: pending.

Preconditions:

- Phase 2 ledger CSV enumerates every concept field, declaration site, target
  owner file, deletion proof, and pinned test before this phase begins.
- JSON scanner/baseline gates exist and are committed.

This is the first production implementation slice after documentation,
baseline, and owner-ledger gates. It proves the beautiful abstraction end to
end on one family.

Deliverables in one vertical slice:

- Single typed concept declaration with fields, roles, FTS source, vector
  source, reference policy, and row coercion policy.
- Propstore generator output for concept projection, concept FTS, concept
  vector metadata, typed concept query API, and generated concept row coercion.
- Quire changes first if generic generator/projection mechanics are missing.
- Delete `propstore/sidecar/concepts.py` as a production declaration owner.
- Remove `ConceptRow` declaration from `propstore/core/row_types.py`; concept
  row consumers are rewritten to the generated concept row module.
- Delete concept-shaped direct SQL in:
  - `propstore/app/concepts/display.py`
  - `propstore/app/concepts/mutation.py`
  - `propstore/app/concepts/embedding.py`
  - concept sections of `propstore/world/model.py`
- Delete sidecar concept projection constants outside the generator/catalog.

Gate:

- Per-field declaring-file count for every concept field equals one target
  declaration, ignoring generated output.
- Generated concept DDL byte-equals current concept DDL or records an
  intentional semantic diff.
- Generated concept row coercion is behavior-equivalent to old `ConceptRow`.
- No hand-written concept table SQL remains outside the generator/query owner.

### Slice Test Map

| Slice | Required Focused Tests |
| --- | --- |
| `propstore/app/concepts/display.py` | `tests/test_concept_views.py`, `tests/test_cli.py`, concept FTS/search tests |
| `propstore/app/concepts/mutation.py` | `tests/test_concept_views.py`, `tests/test_cli.py`, `tests/test_source_promotion_alignment.py`, concept mutation tests |
| `propstore/app/concepts/embedding.py` | `tests/test_embed_operational_error.py`, concept embedding/similarity tests |
| `propstore/app/claims.py` | `tests/test_claim_views.py`, `tests/test_relate_opinions.py`, claim embedding/similarity tests |
| `propstore/source/status.py` | `tests/test_cli_source_status.py`, `tests/remediation/phase_7_race_atomicity/test_T7_5c_source_status_like_escape.py`, promotion diagnostic tests |
| `propstore/heuristic/relate.py` | `tests/test_relate_opinions.py`, calibration/opinion tests |
| `propstore/heuristic/calibrate.py` | `tests/test_calibrate.py`, `tests/test_relate_opinions.py` |
| `propstore/heuristic/embed.py` | `tests/test_embed_operational_error.py`, embedding tests |
| `propstore/merge/structured_merge.py` | merge/grounding/structured merge tests |

Before executing each slice, replace broad names above with exact existing test
paths from `rg --files tests`.

### Old-Path Search Gates

Run these after the concept vertical:

```powershell
rg -n "FROM concept\\b|FROM concept_fts\\b|FROM alias\\b|FROM concept_vec\\b" propstore --glob "*.py"
rg -n "canonical_name|kind_type|form_parameters|primary_logical_id" propstore --glob "*.py"
rg -n "class ConceptRow\\b|ConceptRow\\(" propstore --glob "*.py"
rg -n "from propstore\\.sidecar\\.concepts" propstore --glob "*.py"
rg -n "CONCEPT_PROJECTION|CONCEPT_FTS_PROJECTION|CONCEPT_VEC_PROJECTION" propstore --glob "*.py"
rg -n "connect_sidecar_readonly|conn\\.execute|concept_fts" propstore/app/concepts/display.py
rg -n "connect_sidecar|conn\\.execute|SELECT .*concept|SELECT .*alias" propstore/app/concepts/mutation.py
rg -n "connect_sidecar|row_factory" propstore/app/concepts/embedding.py
```

Any red hit outside the generated declaration/catalog/query owner means the
slice is not complete.

## Phase 4: Claim Vertical

Status: pending.

Precondition:

- Add or locate claim YAML round-trip fixtures. The current local `knowledge/`
  checkout does not contain claim YAML files, so flat-vs-proposition claim
  shape cannot be inferred from local sample data.

Target surfaces:

- `propstore/families/registry.py`
- `propstore/families/claims/documents.py`
- `propstore/families/documents/sources.py`
- `propstore/source/claims.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/core/row_types.py` claim surfaces only
- claim FTS and claim embedding text sources
- claim-shaped SQL in app/source/heuristic/world paths

Gate:

- Preserve the load-bearing `claim_core`, numeric payload, text payload, and
  algorithm payload split unless a proof deletes it.
- Single claim declaration drives projection shape, row decoding input, FTS
  source text, vector source text, and app/query/report field subsets.
- `propstore/core/row_types.py` no longer declares `ClaimRow` once generated
  claim row coercion exists and every importer is rewritten.
- Source-local claim fields remain source-owned and do not leak into canonical
  declarations.
- Old paths searched:
  `rg -n "FROM claim_core\\b|FROM claim_text_payload\\b|FROM claim_numeric_payload\\b|FROM claim_algorithm_payload\\b" propstore --glob "*.py"`
  `rg -n "class ClaimRow\\b|class ClaimCoreRow\\b" propstore --glob "*.py"`
  `rg -n "from propstore\\.sidecar\\.claims|from propstore\\.sidecar\\.claim_utils" propstore --glob "*.py"`
  `rg -n "CLAIM_CORE_PROJECTION" propstore --glob "*.py"`
  must show only generated/declaration-owner hits.

## Phase 5: Remaining Family Verticals

Status: pending.

Target surfaces:

- contexts and context lifting;
- relations and opinion fields;
- micropublications;
- canonical sources and source-local source documents;
- diagnostics/quarantine;
- grounded rules and bundle input rows;
- calibration counts.

Gate:

- Each family follows the concept vertical template.
- The family's sidecar declaration module is deleted, not edited into a renamed
  wrapper.
- FTS/vector/query/row coercion roles are declared in the same family
  declaration slice when applicable.

## Phase 6: WorldQuery and Red SQL Consequences

Status: pending.

Tasks:

- Replace `propstore/world/model.py` table SQL one family at a time using the
  generated typed family query APIs.
- Remove red SQL from app/source/heuristic/merge paths as the direct
  consequence of each family vertical.
- Preserve domain reasoning in world/app/heuristic modules; delete storage
  ownership only.

Gate:

- The matching old-path search gate for each family is clean outside the
  generated declaration/catalog/query owner.
- No replacement module hand-codes derived-store table names.

## Phase 7: Yellow Sunset and Raw Query Catalog

Status: pending.

Tasks:

- Move yellow derived-store coupling behind generated catalog/query APIs:
  `materialize_world_sidecar`, `collect_authoring_lints`, projection constants,
  and `WORLD_SIDECAR_SCHEMA` imports outside owner modules.
- Rebuild `propstore/sidecar/query.py` so raw inspection reads table/column
  metadata from the generated catalog at runtime.
- Delete hand-written column knowledge from raw query support, or delete raw
  query support if product policy chooses that.

Gate:

- `propstore/sidecar/query.py` contains zero hand-written derived-store column
  names.
- Yellow hits outside the generator/catalog owner are either gone or documented
  product escape hatches with no table/column declarations.
- Projection compression is not a separate phase. Family declarations generate
  projections; if a separate compression pass is needed, the family vertical is
  incomplete.

## Phase 8: Runtime/Wire Codec Follow-Up

Status: out of scope for this workstream.

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

- This workstream may not edit these files except when a direct dependency is
  required by a completed family vertical and recorded in the owner ledger.
- Runtime/wire cleanup belongs in a separate follow-up workstream.

## Phase 9: Final Gates

Status: pending.

Commands:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
uv run scripts/typed_metadata_inventory.py --format json
uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label typed-metadata-cleanup-targeted tests/test_build_sidecar.py tests/test_world_query.py tests/test_sidecar_projection_contract.py tests/test_sidecar_projection_fts_contract.py tests/test_sidecar_projection_vec_contract.py tests/test_relate_opinions.py
powershell -File scripts/run_logged_pytest.ps1 -Label typed-metadata-cleanup-full
```

Completion requires:

- all phase gates complete;
- no old production path coexists with its replacement;
- scanner metrics show kept reductions for the targets actually changed;
- all ledger gate checks pass;
- every old-path grep gate returns its expected count;
- `propstore/core/row_types.py` is deleted or contains no derived-store row
  class declarations;
- `propstore/sidecar/{concepts,claims,contexts,relations,rules,micropublications,sources,diagnostics,calibration}.py`
  are deleted;
- `propstore/sidecar/query.py` builds table/column listings from the generated
  catalog and contains zero hand-written derived-store column names;
- pyright passes;
- targeted tests pass;
- full suite passes.

## Required Scanner/Baseline Work Before Implementation

The current scanner is enough for planning but not enough for enforcement.
Before production code edits:

1. Add JSON output to `scripts/typed_metadata_inventory.py`.
2. Commit a baseline JSON artifact under `workstreams/` or `reports/` that
   captures:
   - red storage leak scores by file;
   - projection column counts by file;
   - repeated projection field files;
   - declaration-density scores by file;
   - core row-type importers;
   - CLI request/report adapter calls;
   - test pins.
3. Add a comparison command that fails when a completed slice does not improve
   its target metric.

Do not hand-compare markdown tables for implementation gates.
