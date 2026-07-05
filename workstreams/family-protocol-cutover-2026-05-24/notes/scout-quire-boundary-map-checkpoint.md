# Scout checkpoint — scout-quire-boundary-map

Datestamp: 2026-05-24 (second checkpoint)

## Tree state
- HEAD: e13e302d195ddf38bbde5c965744e992ae57166b
- `git status --short` shows only untracked files; no modified tracked source files.

## Files read (with line counts)
- `pyproject.toml` (97)
- `.venv/Lib/site-packages/quire/__init__.py` (211)
- `.venv/Lib/site-packages/quire/charters.py` (253)
- `.venv/Lib/site-packages/quire/schema_catalog.py` (25)
- `.venv/Lib/site-packages/quire/sqlalchemy_schema.py` (499)
- `.venv/Lib/site-packages/quire/references.py` (partial; ForeignKeySpec at :57)
- `.venv/Lib/site-packages/quire/families.py` (FamilyDefinition at :121)
- `workstreams/family-protocol-cutover-2026-05-24/02-quire-generated-family-protocols.md` (154)
- `reports/charter-cutover-breakdown/quire-prereqs-report.md` (207)
- `propstore/families/sources/declaration.py` (125) — `source_charter()` at :47
- `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut1-slice-a-world-charters-fallout.md` (281) — Slice A draft
- `workstreams/family-protocol-cutover-2026-05-24/notes/world_charters_last_living.py` (931; read 1-120, 430-550)
- `workstreams/family-protocol-cutover-2026-05-24/reports/scout-world-schema-current-owner.md` (326; read 1-80)

## Quire pinning facts
- `pyproject.toml:83`: `quire = { git = "https://github.com/ctoth/quire", rev = "ac05ff5e66d8a744ec0be9406f8912c81dfaa6bd" }`
- Git-rev pin (correct per `feedback_no_local_path_pins`). On-disk: `.venv/Lib/site-packages/quire/`.

## Symbol existence verdicts (Section 4)
- `quire.charters.FamilyCharter` — YES, charters.py:185 (`@dataclass(frozen=True)`)
- `quire.charters.CharterField` — YES, charters.py:39 (`@dataclass(frozen=True)`)
- `quire.charters.FamilyModel` — YES, charters.py:25 (plain class with `__init__(**values)`)
- `quire.charters.charter_catalog` — YES, charters.py:234 (`(*charters, metadata=None) -> SchemaCatalog`)
- `quire.charters.SchemaCatalog` — NOT at `quire.charters.*`; actually at `quire.schema_catalog.SchemaCatalog` (schema_catalog.py:11). Re-exported from `quire.__init__:64`. Slice A prompt's literal `quire.charters.SchemaCatalog` would be wrong; the deleted snapshot imports it correctly from `quire.schema_catalog`.
- `quire.charters.ForeignKeySpec` — NOT at `quire.charters.*`; actually at `quire.references.ForeignKeySpec` (references.py:57). Re-exported from `quire.__init__:70`. Same correction.
- `quire.sqlalchemy_schema.build_sqlalchemy_schema` — YES, sqlalchemy_schema.py:217 (`(SchemaCatalog) -> SqlAlchemySchema`)
- `quire.sqlalchemy_schema.SqlAlchemySchema` — YES, sqlalchemy_schema.py:88 (`@dataclass(frozen=True)`)
- All other charters used by the snapshot exist: `CharterIndex`, `CharterFtsIndex`, `CharterVectorCache`, `CharterRelationship`, `CharterPolymorphicModel`. `ReferenceKey` is at `quire.references`.

## Pipeline trace (Section 5)
- `FamilyCharter(...)` is a frozen dataclass with explicit fields. No factory.
- `charter_catalog(*charters, metadata=None)` is a pure function that calls `to_schema_object()` on each charter and returns a `SchemaCatalog`. No caching, no validation, no ordering — `SchemaCatalog.payload()` sorts at output time but the SchemaObject tuple is built in argument order.
- `build_sqlalchemy_schema(catalog)` (sqlalchemy_schema.py:217) calls `clear_mappers()` first — NOT internally cached. Caller-side `lru_cache` is required.
- `SqlAlchemySchema` exposes `.table(name)`, `.model(name)`, `.polymorphic_model(family,identity)`, `.identity_field(family)`, `.require_reference_id(...)`, `.resolve_reference_id(...)`, `.reference_index_from_records(...)`, `.fts_table(name)`, `.fts_index(name)`, `.vector_cache(name)`, `.has_vector_caches`, `.construct(family, values)`, `.schema_object(name)`. All accessors Slice A's call-site rewrites need are present.

## `source_charter()` reference pattern facts
- Uses `quire.charters.{CharterField, CharterIndex, FamilyCharter, FamilyModel}`, `quire.families.FamilyDefinition`, `quire.artifacts.{ArtifactFamily, FlatYamlPlacement}`, `quire.versions.VersionId`.
- Inline `FamilyCharter(family=FamilyDefinition(...), model=Source, fields=(CharterField(...), ...), indexes=(...), semantic_metadata={"semantic": "propstore.world"})`.
- Matches the last-living `_charter()` helper output exactly — no drift. The deleted helper's `_world_family` is equivalent to the inline `FamilyDefinition(key=..., name=..., contract_version=..., artifact_family=ArtifactFamily(..., placement=FlatYamlPlacement(...)), identity_field=...)` Slice A would author.

## Phase 02 — what Quire is GAINING (Section 7 facts)
From `02-quire-generated-family-protocols.md`:
- `CharterField` must gain: `document`, `document_name`, `document_order`, `states: frozenset[str] | None`, `artifact`, `artifact_name`, `graph_node_label`, `graph_metadata`, `local_id`, `local_id_policy`, `contract_version: VersionId | None`, `parse_boundary` (lines 19-39).
- `CharterRelationship` must gain: `artifact_dependency`, `graph_edge`, `graph_edge_kind`, `states` (lines 41-47).
- `FamilyCharter` must gain: `states: tuple[FamilyState, ...]`, `transitions: tuple[FamilyTransition, ...]`, `local_id_policy: LocalIdPolicy | None`, `batch_specs: tuple[DocumentBatchSpec, ...]`, `document_contract_version: VersionId`, plus `generated_document()`, `document_codec()`, `main_model()`, `identity_field()`, `reference_resolver()` accessor methods (lines 49-62).
- Required new types: `FamilyState`, `FamilyTransition`, `LocalIdPolicy` — confirmed ABSENT in pinned Quire (`DocumentBatchSpec` exists at `quire/documents/batch.py:19`, others do not exist).
- Hard rule (lines 14-17): "Phase 02 does not pass by adding conventions to `metadata: Mapping[str, object]`. The following concepts must be first-class typed charter attributes." — this is critical for Section 9.

## Cross-check current Quire against Phase 02 additions
- `metadata: Mapping[str, object] = field(default_factory=dict)` is present on `CharterField` (charters.py:57), `CharterFtsIndex` (:108), `CharterVectorCache` (:132), `CharterRelationship` (:158), and `FamilyCharter.semantic_metadata` (:198). Phase 02 forbids using these mappings for the named concepts; today the only path TO those concepts is the metadata bag, so the prohibition explicitly says metadata bags are no longer the answer.
- All Phase 02 ADDITIONS are additive (new fields with defaults / new methods). No removals or renames of `FamilyCharter`, `CharterField`, `charter_catalog`, or `build_sqlalchemy_schema` signatures.

## Section 9 (load-bearing answer) — leaning verdict
- **(a) COMPATIBLE.** Slice A authors `FamilyCharter(...)` using the current dataclass fields (family/model/fields/indexes/.../semantic_metadata). Phase 02 ADDS dataclass fields with defaults; it does not rename or remove. The literal `<family>_charter()` function bodies authored in Slice A continue to type-check and run unchanged. Slice A does NOT use the `metadata={"document": True, ...}` anti-pattern (it uses typed `CharterField` kwargs directly).
- One caveat to flag: the prereqs report notes the metadata-bag anti-pattern Phase 02 forbids. If Slice A authors used `CharterField.metadata` for any document/artifact/graph flag (it doesn't — those flags don't exist today and Slice A is a mechanical translation of `_f`/`_i`/`_r`/`_b` which never set `metadata`), they'd need rework. But the last-living `_charter`/`_f` helpers do not touch `metadata=`, so the mechanical translation stays clean.

## Hazards for foreman (Section 10) — preliminary
- Slice A prompt at lines 26, 50, 203 names `quire.charters.SchemaCatalog`, `quire.charters.ForeignKeySpec` — those are at `quire.schema_catalog` and `quire.references` respectively. The deleted snapshot imports them from the correct modules; Slice A code should follow that, not the prompt's prose phrasing.
- H-B's enumeration is correct (those 5 symbols exist).
- Slice A's `world_catalog()` lru_cache IS needed — `build_sqlalchemy_schema` calls `clear_mappers()` and is uncached.

## Current blocker
None. Ready to write the final report.
