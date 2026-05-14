# Repo-Wide Typed Metadata Cleanup Inventory

## Purpose

This note is the pre-implementation inventory for the next cleanup workstream.
It exists because the sidecar-only cleanup was too narrow: SQL, row shapes,
payload shapes, and semantic field declarations still leak across app, world,
source, heuristic, merge, family, and sidecar layers.

The desired cleanup shape is one typed semantic declaration per durable semantic
surface, with generated or mechanically derived projections, FTS/vector indexes,
row decoders, and query inputs. Repeating the same field names, nullability,
JSON encoding, identity policy, or SQL column shape in multiple places is a code
smell unless the repeated declaration is generated from one owner.

## Current Evidence

Line-count scan of `propstore/` shows the largest cleanup surfaces are not only
`propstore.sidecar`:

| Directory | Lines | Notes |
| --- | ---: | --- |
| `world` | 10255 | read model, direct SQLite, ATMS/world query types |
| `app` | 8861 | request/report types plus direct sidecar reads |
| `core` | 8610 | row/graph/analyzer types and semantic plumbing |
| `families` | 7656 | family declarations, document/payload/stage shapes |
| `cli` | 6820 | presentation layer; must not own reusable semantics |
| `sidecar` | 4711 | projection declarations and materialization mappers |
| `support_revision` | 3695 | mapping-heavy journal/snapshot types |
| `worldline` | 2784 | mapping-heavy result/revision types |
| `source` | 3769 | source-local authoring/promotion/status surfaces |
| `heuristic` | 2231 | direct embedding/similarity SQL and sidecar coupling |
| `merge` | 1297 | grounding/structured merge sidecar coupling |

Direct SQL or sidecar coupling appears outside `propstore.sidecar` in:

- `propstore/app/concepts/mutation.py`
- `propstore/app/concepts/display.py`
- `propstore/app/concepts/embedding.py`
- `propstore/app/claims.py`
- `propstore/app/sources.py`
- `propstore/app/repository_history.py`
- `propstore/compiler/workflows.py`
- `propstore/heuristic/embed.py`
- `propstore/heuristic/relate.py`
- `propstore/heuristic/calibrate.py`
- `propstore/merge/structured_merge.py`
- `propstore/source/promote.py`
- `propstore/source/status.py`
- `propstore/world/model.py`
- `propstore/world/queries.py`

The sidecar custom table DDL is gone, but typed semantic metadata is still not
centralized. `ProjectionColumn(...)` declarations still spell the semantic row
model directly in `propstore/sidecar/*.py`, while app/world/family/source code
also knows field names and row shapes.

## Cleanup Heuristics

Use these searches to find cleanup targets before editing:

- Repeated field declarations:
  - `rg -n -F "ProjectionColumn(" propstore --glob "*.py"`
  - `rg -n "id|content_hash|seq|provenance_json|conditions_cel|conditions_ir|source_slug|context_id" propstore --glob "*.py"`
- Direct storage leaks:
  - `rg -n "sqlite3|connect_sidecar|connect_sidecar_readonly|row_factory|\\.execute\\(" propstore --glob "*.py"`
  - `rg -n "SELECT |INSERT |UPDATE |DELETE |PRAGMA " propstore --glob "*.py"`
- Duplicated mapping boundaries:
  - `rg -n "def (to_payload|from_payload|to_dict|from_dict|from_mapping|to_mapping)" propstore --glob "*.py"`
  - `rg -n "dict\\[str, Any\\]|dict\\[str, object\\]|Mapping\\[str, Any\\]|TypedDict" propstore --glob "*.py"`
- Parallel request/report/view rows that mirror semantic rows:
  - `rg -n "class .*Row|class .*Record|class .*Report|class .*Request|@dataclass" propstore --glob "*.py"`
- Sidecar-specific imports that should become typed query API calls:
  - `rg -n "propstore\\.sidecar|materialize_world_sidecar|WORLD_SIDECAR_SCHEMA|CLAIM_CORE_PROJECTION|CONCEPT_PROJECTION" propstore --glob "*.py"`
- Family declarations that re-express payload fields:
  - `rg -n "to_payload|parse_.*record|normalize_.*payload|document_to_payload|record_payload" propstore/families propstore/source propstore/app --glob "*.py"`

Each hit is not automatically bad. It becomes a cleanup target when one of these
is true:

- the same semantic field is declared in more than one layer;
- SQL column names are visible outside the derived-store/query owner;
- a `dict` or `Mapping[str, Any]` crosses into semantic core code instead of
  stopping at an IO boundary;
- a request/report row manually mirrors fields from a semantic object;
- FTS/vector/search text is assembled separately from the semantic declaration;
- nullability/default/check semantics are repeated outside one declaration;
- source-local fields can reach canonical/master surfaces;
- CLI/app code knows table names, projection names, or row factories.

## Repeated Field Families To Normalize

These field families should become typed declaration fragments or generated
metadata, not repeatedly spelled columns and row attributes:

- Artifact identity: `id`, `primary_logical_id`, `logical_ids_json`,
  `version_id`, `content_hash`, `seq`.
- Source/provenance: `source_slug`, `source_paper`, `provenance_page`,
  `provenance_json`, `source_ref`, `source_kind`, `file`, `detail_json`.
- Context/lifting: `context_id`, `source_context_id`, `target_context_id`,
  `conditions_cel`, `conditions_ir`, `status`, `exception_id`.
- Relation endpoints: `source_kind`, `source_id`, `relation_type`,
  `target_kind`, `target_id`, `concept_id`, `claim_id`, `role`, `ordinal`.
- Claim payload families: numeric value/bounds/unit/SI fields, text
  statement/expression/sympy fields, algorithm body/AST/stage fields.
- Search/index metadata: FTS source fields, embedding `model`,
  `content_hash`, stable row ids, vector dimensions.
- Subjective/opinion fields: `strength`, `confidence`, `opinion_belief`,
  `opinion_disbelief`, `opinion_uncertainty`, `opinion_base_rate`,
  `resolution_method`, `resolution_model`, `embedding_model`,
  `embedding_distance`.
- Diagnostics: `diagnostic_kind`, `severity`, `blocking`, `message`,
  row/source reference, JSON detail.

## Single-Declaration Target Shape

Propstore should own semantic declarations, not storage mechanics. A declaration
should be able to say, in one place:

- semantic object name and owning family;
- typed Python object or record type;
- canonical fields with type, required/optional status, defaults, checks, and
  source-local/canonical visibility;
- identity fields and reference/FK semantics using Quire family references;
- projection participation and generated SQL column shape;
- FTS text fields and tokenizer/search policy;
- vector embedding text source, identity, dimensions, and freshness policy;
- JSON serialization boundaries for fields that are intentionally structured;
- typed query/read-model row decoder;
- CLI/report render field subsets when those are merely views of the semantic
  object.

Quire should own generic execution of that declaration: validation, schema
hashing, generated DDL, insert/read plumbing, FTS/vector table materialization,
and derived-store lifecycle.

Propstore should own semantic extraction from artifacts and semantic query
behavior. It should not own table DDL, generic SQLite row plumbing, generic
projection ordering, or one-off SQL query copies in app/source/heuristic layers.

## Initial Inventory Buckets

1. Projection declaration duplication:
   `propstore/sidecar/claims.py`, `concepts.py`, `contexts.py`,
   `relations.py`, `sources.py`, `diagnostics.py`, `rules.py`,
   `micropublications.py`, `calibration.py`, `schema.py`.

2. Mapper/persistence duplication:
   `propstore/sidecar/passes.py`, `claim_utils.py`, `build.py`,
   `embedding_store.py`, plus insert/read helpers in sidecar submodules.

3. Direct read-model SQL:
   `propstore/world/model.py`, concept/claim app modules, source status,
   heuristic embedding/relate/calibrate, merge structured grounding.

4. Multiple semantic object representations:
   family document/stage payloads, app request/report rows, sidecar projection
   rows, world query rows, source promotion/status rows, CLI render rows.

5. Mapping-heavy non-sidecar surfaces:
   `propstore/worldline/result_types.py`,
   `propstore/worldline/revision_types.py`,
   `propstore/support_revision/history.py`,
   `propstore/support_revision/snapshot_types.py`,
   `propstore/support_revision/explanation_types.py`,
   `propstore/epistemic_process.py`.

6. CLI-owned or app-owned reusable semantics:
   any command/app path that parses semantic payloads, queries sidecar SQL
   directly, or computes owner-layer behavior instead of adapting typed owner
   APIs.

## Evidence Still Needed Before Edits

- A mechanical duplicate-field ledger by field name and declaring file.
- A table mapping every direct SQL query to the typed query API that should own
  it.
- A semantic object representation matrix: canonical artifact object, family
  document, source-local object, projection row, world query row, app report,
  CLI rendering.
- A dependency graph showing which cleanup slices can be deletion-first without
  temporary bridges.
- Test gates per slice, especially for load-bearing source promotion/status,
  world queries, embeddings, FTS, grounding, and render policy.

## Second-Pass Notes

`propstore/core/row_types.py` is a central cleanup target. It calls itself the
typed storage-row boundary and manually mirrors sidecar field names:
`ConceptRow.from_mapping` knows `id`, `canonical_name`, `status`,
`definition`, `kind_type`, `form`, `domain`, `form_parameters`,
`primary_logical_id`, and `logical_ids_json`. Those same names are declared in
`propstore/sidecar/concepts.py`, consumed in `propstore/world/model.py`, and
rendered again in app view/report code. That is exactly the duplicate
single-declaration problem.

`propstore/world/model.py` is the main direct read-model SQL owner today. It
opens the derived store, sets `sqlite3.Row`, validates `meta`, validates
`WORLD_SIDECAR_SCHEMA`, and issues direct SQL such as
`SELECT schema_version FROM meta WHERE key = ?` and
`SELECT id, canonical_name, kind_type, form_parameters FROM concept`. It then
normalizes those rows through `ConceptRow.from_mapping`. The cleanup shape is
not to move those SQL strings elsewhere one by one; it is to make typed query
surfaces generated or owned by the declaration/read-model layer.

`propstore/families/registry.py` already owns important single-declaration
material: family identity policy, placement, FK declarations, source-local
fields, version-excluded fields, and semantic metadata. The missing piece is
that derived-store/read-model/search/vector metadata is not co-located with
that semantic declaration. A likely beautiful abstraction extends the family
declaration with typed projection/search/index metadata rather than maintaining
sidecar projection modules as a parallel declaration system.

The family/document/stage layer has large mapping duplication:

- `propstore/families/concepts/stages.py` has concept document payload,
  record payload, canonical normalization, record parsing, registry loading,
  and `ConceptRecord.to_payload`.
- `propstore/families/claims/documents.py` has many nested `to_payload`
  methods for source, provenance, values, stances, opinion, resolution,
  variables, context, proposition, fit, and full claim documents.
- `propstore/families/documents/sources.py` repeats source-local concept,
  claim, justification, stance, provenance, produced-by, calibration, and
  merge payload shapes.
- `propstore/source/claims.py`, `propstore/source/relations.py`, and
  `propstore/source/registry.py` normalize source-local payloads and then
  convert back to dictionaries.

These may be legitimate IO-boundary codecs, but they become cleanup targets
where the same semantic field is also declared in sidecar projection rows,
core row types, app reports, or identity normalization.

The non-sidecar mapping-heavy surfaces are probably a second workstream, not
the first derived-store workstream:

- `propstore/worldline/result_types.py`
- `propstore/worldline/revision_types.py`
- `propstore/support_revision/history.py`
- `propstore/support_revision/snapshot_types.py`
- `propstore/support_revision/explanation_types.py`
- `propstore/support_revision/state.py`
- `propstore/epistemic_process.py`

Those files use explicit `from_mapping`/`to_dict` codecs. The smell is not
serialization itself; the smell is untyped mapping payloads flowing between
semantic subsystems instead of being converted immediately at the IO boundary.

## Cleanup Slice Candidates

1. Duplicate declaration ledger:
   mechanically list every semantic field declared in projection columns, core
   row types, family document payloads, app reports, and world query rows.
   Gate: each repeated field has one proposed owner declaration or is marked
   deliberate generated output.

2. Read-model SQL boundary:
   inventory every `.execute(...)` and table name outside the derived-store
   owner. Gate: each direct query is assigned to a typed query API owned by
   world/read-model/derived-store code, not app/CLI/source status.

3. Family declaration consolidation:
   start with concepts because `families/registry.py`,
   `families/concepts/stages.py`, `core/row_types.py`,
   `sidecar/concepts.py`, app concept views/mutation, FTS, and embeddings all
   repeat concept fields. Gate: one concept declaration drives projection
   columns, row decoding, FTS text, and vector text.

4. Claims only after concepts:
   claims have more load-bearing split payloads. Gate: preserve the core/text/
   numeric/algorithm split unless a proof shows it can be collapsed.

5. Embedding/FTS declaration consolidation:
   search text and embedding text should be metadata on semantic declarations,
   not independent SQL/index policy in app, heuristic, and sidecar modules.

6. Source-local boundary audit:
   source-local fields should be declared once and rejected by canonical/master
   surfaces. Gate: source-local normalization remains in source subsystem and
   canonical paths hard-fail on source-local-only shape.
