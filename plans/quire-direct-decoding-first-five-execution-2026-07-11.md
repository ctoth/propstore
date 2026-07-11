# Quire direct-decoding cleanup: first five A2 files

Date: 2026-07-11

Status: execution started 2026-07-11. No production code had been changed at
the execution baseline (`dfcb160cd79d38af9d7462f4e10d2e5f13093390`).

Active control surface: `protocols:cleanup-refactor`.

## Scope and ordering

This plan covers the first five files in the lexically sorted A2 inventory:

1. `propstore/core/assertions/codec.py`
2. `propstore/core/assertions/conversion.py`
3. `propstore/core/environment.py`
4. `propstore/core/graph_types.py`
5. `propstore/core/micropublications.py`

“Mapping surface” means the entire representation family, not only the four
generic predicates that exposed it. The cleanup therefore includes
`from_dict`, `from_mapping`, `from_payload`, `to_dict`, `to_payload`, mapping
input aliases, mapping coercers, semantic attribute/extras/details bags, and
per-field parsing functions.

The five-file inventory contains 29 named conversion entry points:

| File | Conversion entry points |
| --- | --- |
| `assertions/codec.py` | `from_assertion`, `from_payload`, `to_assertion`, `to_payload` |
| `assertions/conversion.py` | `from_payload`, `assertion_source_record_from_payload`, `to_situated_assertion` |
| `environment.py` | `AssumptionRef.to_dict`, `Environment.from_dict`, `Environment.to_dict` |
| `graph_types.py` | seven `from_dict`, one `from_mapping`, and eight `to_dict` methods |
| `micropublications.py` | `from_mapping`, `_parse_string_tuple`, `coerce_active_micropublication` |

The count is an inventory aid, not the completion gate. The bags, input unions,
and per-field readers listed below must also be gone.

Execution order should follow dependency risk rather than filename order:

1. delete `assertions/conversion.py`;
2. delete `core/micropublications.py` and use the charter directly;
3. converge `core/graph_types.py` on canonical owners;
4. make `Environment` and worldline inputs typed Quire documents;
5. delete `assertions/codec.py` after the support-revision snapshot is typed.

Each numbered item is one Git slice. A slice must end as either a committed
kept change or a complete tracked-file restore before the next slice starts.

## Target architecture

- Quire decodes and encodes typed document graphs from charter/document field
  declarations. Propstore does not parse those graphs field by field.
- Quire owns document schema, field metadata, strict decoding, storage,
  placement, registry, and reference mechanics.
- Propstore's existing family charters and semantic objects remain the direct
  semantic owners. Callers receive those types, not Propstore-owned wire DTOs.
- A runtime-only graph object that is never a stored document does not acquire
  a Quire wrapper merely to remove a mapping method. Its mapping method is
  deleted.
- IO boundaries may call Quire's existing document codec. Loose mappings do
  not cross into semantic code.
- Unknown fields, wrong tags, wrong member types, and old shapes fail at the
  Quire boundary. There is no compatibility reader.

Current Quire already provides the required generic machinery at the pinned
revision (`95a268c68556160b52fe065ae59f1de2b750f9e3`):

- `quire.documents.schema.DocumentStruct`;
- strict `decode_document_bytes`/document codecs;
- `document_to_payload` at IO boundaries;
- nested typed document decoding;
- tagged-union decoding, including the recursive shape covered by
  `quire/tests/test_charter_class_recursive.py` specifically for the
  claims/worldlines migration.

No Quire change is planned for these five files. If implementation proves a
generic capability genuinely absent, stop the Propstore slice. Add the generic
capability and a generic Quire test in Quire, commit and push Quire, update
Propstore's immutable Quire pin, and only then resume. A Propstore custom codec,
family codec override, fallback parser, or local normalization layer is not an
allowed substitute.

## Forbidden replacement surfaces

The following must not appear as fallout from these deletions:

- replacement `*Record`, `*Payload`, `*DTO`, `*Adapter`, `*Codec`, or
  `*Serializer` types that mirror a domain object;
- aliases or forwarding methods preserving a deleted name;
- `Mapping[str, Any]`, `dict[str, Any]`, or `object` semantic carriers;
- `from_*`/`to_*` methods whose only purpose is rebuilding a typed document;
- custom per-family decode/encode callbacks for an ordinary typed document;
- mapping-or-domain unions and `coerce_*` functions;
- repeated field-name lists, kwargs builders, fallback readers, and
  type-narrowing blocks that reproduce schema knowledge;
- old and new representations accepted concurrently.

## Inventory and disposition

### 1. `core/assertions/conversion.py`: delete the file

Current surface:

- `AssertionSourceRecord` duplicates the fields of `SituatedAssertion`;
- `AssertionSourceRecord.from_payload` manually parses a semantic mapping;
- `to_situated_assertion` reconstructs the real domain object;
- `_is_mapping`, `_is_sequence`, `_required`, and the relation, role,
  context, condition, graph, and text field readers duplicate schema work;
- the package `__init__.py` re-exports the duplicate type;
- only `tests/test_structural_assertion_conversion.py` consumes it.

Broken-edge classification and disposition:

- the record and all parser functions: **deleted old surface** -> delete;
- the package export: **wrong caller that exists only for the old surface** ->
  delete;
- payload-conversion tests: **dead/test/scaffold surface** -> delete;
- any unique role-signature invariant in those tests: **already-owned
  capability** -> assert it directly against `SituatedAssertion` /
  `RoleBindingSet` in the existing situated-assertion tests.

There is no production capability to move and no Quire API to add.

Slice gate:

- the file and export are absent;
- repository search has zero `AssertionSourceRecord`,
  `assertion_source_record_from_payload`, `to_situated_assertion`, or imports
  of `assertions.conversion`;
- focused situated-assertion tests pass through the logged pytest wrapper;
- `uv run pyright propstore` passes.

### 2. `core/micropublications.py`: delete the duplicate runtime model

Current surface:

- `ActiveMicropublication` duplicates a subset of the canonical
  `families.micropublications.Micropublication` charter;
- `from_mapping` and `_is_mapping` manually decode it;
- `_is_str_collection` additionally accepts JSON strings as collections;
- `ActiveMicropublicationInput` admits either the duplicate object or a
  mapping;
- `coerce_active_micropublication` preserves that dual representation;
- world/ATMS and overlay paths consume the coercer;
- environment protocols expose the mapping-or-object input alias.

True owner: `propstore.families.micropublications.Micropublication`.

Broken-edge classification and disposition:

- duplicate model, mapping parser, JSON-string parser, alias, and coercer:
  **deleted old surface** -> delete the entire file;
- ATMS/overlay coercer calls: **already-owned capability that must use its true
  owner directly** -> accept `Sequence[Micropublication]` and read charter
  fields directly (`claims`, `context_id`, evidence, assumptions, stance);
- protocols parameterized by `ActiveMicropublicationInput`: **valid capability
  with wrong representation** -> type them to canonical `Micropublication`;
- tests of mapping coercion: **dead/test/scaffold surface** -> delete;
- semantic invariant tests: **already-owned capability** -> keep them only at
  the charter owner.

Do not add an `ActiveMicropublication` property, conversion method, adapter, or
constructor wrapper to the charter. Quire already returns the charter.

Slice gate:

- repository search has zero `ActiveMicropublication`,
  `ActiveMicropublicationInput`, `coerce_active_micropublication`, or imports
  of `core.micropublications`;
- production ATMS/overlay tests exercise canonical `Micropublication` objects;
- the user's currently untracked `tests/test_micropub_clark_charter.py` is not
  edited, staged, or used as permission to absorb unrelated work;
- focused tests and `uv run pyright propstore` pass.

### 3. `core/graph_types.py`: remove serialization and duplicate semantic views

Current mapping surface:

- `_is_mapping`, `_is_sequence`, `_optional_mapping`;
- `_freeze_value`, `_normalize_pairs`;
- `_condition_set_to_json`, `_condition_set_from_json`;
- `ConceptNode.from_dict` / `to_dict` and its `attributes` bag;
- `ProvenanceRecord.from_mapping` / `to_dict` and its `extras` bag;
- `ClaimNode.from_dict` / `to_dict` and its `attributes` bag;
- `RelationEdge.from_dict` / `to_dict` and its `attributes` bag;
- `ParameterizationEdge.from_dict` / `to_dict`;
- `ConflictWitness.from_dict` / `to_dict` and its `details` bag;
- `CompiledWorldGraph.from_dict` / `to_dict`;
- `ActiveWorldGraph.from_dict` / `to_dict`.

The `from_*` call graph is internal to this file or test-only. No production IO
boundary needs this runtime graph serialized as a loose mapping. Therefore the
serialization methods and their parsing/freezing helpers are **deleted old
surface**, not capabilities to move to Quire.

Several types also copy semantic facts from their real owners:

| Current copy | True owner | Disposition |
| --- | --- | --- |
| `ConceptNode` plus attributes | `families.concepts.Concept` | Replace graph membership with the charter directly; delete the node copy. |
| `ClaimNode` plus attributes | `families.claims.Claim` | Replace graph membership with the charter directly; delete the node copy. |
| stance-derived relation attributes | `families.relations.Stance` | Put the charter directly in the compiled graph; do not flatten it into an edge attribute bag. |
| `ConflictWitness.details` | `conflict_detector.models.ConflictRecord` | Put the record directly in the compiled graph; delete the details bag and witness copy. |
| `ProvenanceRecord` | No graph owner: its only production construction is synthetic stance-edge metadata | Delete it. The stance charter already owns identity and calibration; tests are the only claim provenance constructor. |

The valid graph mechanics are `RelationEdge`, `ParameterizationEdge`,
`CompiledWorldGraph`, `GraphDelta`, and `ActiveWorldGraph`. Keep those only to
the extent they express graph topology or runtime state. `CompiledWorldGraph`
holds `tuple[Concept, ...]`, `tuple[Claim, ...]`, `tuple[Stance, ...]`, and
`tuple[ConflictRecord, ...]` directly. `relations` remains only the already
graph-native relationship edges; authored stances no longer masquerade as
those edges. Sort canonical members with explicit identity keys rather than
adding ordering wrappers. Drop `provenance` and `attributes` from
`RelationEdge`; drop the unused `provenance` field from `ParameterizationEdge`.
Delete all mapping round trips from the kept types.

Caller rewrite classification:

- `graph_build.py` construction of claim/concept/stance/conflict bags:
  **valid capability with wrong representation** -> build the graph with true
  owner objects;
- `graph_build.py`'s local `conditions_ir` JSON narrowing: **already-owned
  capability** -> use `claim_conditions.compile_checked_conditions` at the
  behavior point that needs checked conditions; do not copy the compiled value
  into a graph node;
- activation, analyzers, assertion projection, value resolution, worldline,
  and support-revision reads of node/relation attributes: **already-owned
  capability that must use its true owner directly** -> use the charter/domain
  field;
- tests that only prove dict round trips: **dead/test/scaffold surface** ->
  delete;
- sorting, delta, topology, activation, and conflict behavior tests:
  **valid capability** -> rewrite inputs to canonical objects and keep.

Before editing each exposed caller, record its exact field and classify the
dependency edge. If a field has no typed owner, the slice stops for owner
design; it must not be hidden in a new `metadata`, `extras`, or `attributes`
container.

Slice gate:

- zero `ConceptNode`, `ClaimNode`, `ConflictWitness`, and `ProvenanceRecord`;
- zero `.attribute_mapping()`, `.attribute_value(`, semantic `.attributes`,
  `.extras`, and `.details` reads on graph objects;
- zero `from_dict`, `from_mapping`, `to_dict`, or mapping helper definitions in
  `core/graph_types.py`;
- graph behavior tests pass through the logged wrapper;
- `uv run pyright propstore` passes.

### 4. `core/environment.py`: make nested worldline input a typed Quire graph

Current surface:

- `_is_mapping`, `_empty_bindings`, `_optional_mapping`;
- `AssumptionRef.to_dict`;
- `Environment.from_dict` / `to_dict`;
- `Environment.bindings: Mapping[str, Any]`;
- `from_dict` silently drops invalid assumptions;
- `WorldlineInputs.from_dict` and `WorldlineDefinition.inputs` repeat the
  mapping representation downstream.

True owners:

- `AssumptionRef` and `Environment` own the semantic meaning of an environment;
- `WorldlineInputs` owns the typed input aggregate;
- Quire owns decoding and encoding their declared nested fields.

Disposition:

- keep `AssumptionRef` and `Environment`, converting the existing classes in
  place to Quire `DocumentStruct`-compatible typed domain documents;
- type bindings directly as `dict[str, str | int | float | bool]`; do not add a
  local scalar wrapper or `Any` alias;
- delete every helper and `from_dict`/`to_dict` method;
- convert the existing `WorldlineInputs` in place to a typed nested document;
- change `WorldlineDefinition.inputs` from a mapping to `WorldlineInputs` and
  remove only the old input decoding branch in this slice;
- callers construct typed values or receive them from Quire. They do not call
  a conversion function.

Other still-untyped `WorldlineDefinition` fields are separate later A2
families. Leaving those distinct fields for later is not permission to keep
both old and new representations for `inputs`: the `inputs` field accepts only
the typed form after this slice.

Slice gate:

- zero environment/worldline-input `from_dict`, `to_dict`, `_is_mapping`,
  `_optional_mapping`, or `_empty_bindings`;
- zero `Mapping[str, Any]` environment bindings;
- `WorldlineDefinition.inputs` is typed and strict;
- invalid nested members fail at Quire decode rather than being filtered;
- focused Quire round-trip tests cover `WorldlineInputs` with assumptions and
  bindings, and worldline behavior tests consume typed inputs;
- `uv run pyright propstore` passes.

### 5. `core/assertions/codec.py`: delete the canonical-record mirror

Current surface:

- `AssertionCanonicalRecord` duplicates every `SituatedAssertion` field and
  also stores the computed `assertion_id`;
- `from_assertion`, `from_payload`, `to_assertion`, and `to_payload` implement a
  complete parallel representation lifecycle;
- `_is_mapping`, `_is_sequence`, `_required`, `_has_old_claim_shape`, and the
  relation, role, context, condition, graph, and text readers duplicate field
  declarations;
- `support_revision/snapshot_types.py` is the production caller;
- the package `__init__.py` re-exports the mirror type.

True owners:

- `SituatedAssertion`, its reference/role/value objects, and assertion identity
  own assertion semantics;
- `AssertionAtom` / `AssumptionAtom` own support-revision atom semantics;
- Quire owns strict decoding of their nested tagged document graph.

Disposition:

- convert the existing situated-assertion component classes in place to typed
  Quire-compatible document structs where needed; do not introduce wire twins;
- make the existing assertion/assumption atom alternatives explicitly tagged
  so Quire can decode their union;
- have the snapshot document contain those typed atoms directly;
- derive assertion identity from the typed assertion and validate it against
  the atom identifier; do not persist the redundant codec record merely to
  carry `assertion_id`;
- delete `codec.py` and its package export;
- delete all support-revision field-by-field assertion parsing and emission;
- old claim shapes fail at the boundary; `_has_old_claim_shape` is deleted, not
  converted into a compatibility rejection helper.

Broken-edge classification:

- snapshot calls to `from_payload(...).to_assertion()` and
  `from_assertion(...).to_payload()`: **valid capability with wrong
  representation** -> snapshot field is the typed assertion/atom graph;
- import/export of the record: **deleted old surface** -> delete;
- hand-decoding tests: **dead/test/scaffold surface** -> delete;
- identity, role, context, condition, provenance, and snapshot integrity tests:
  **valid capability** -> test the typed owner and strict Quire boundary.

Slice gate:

- `codec.py` is absent;
- zero `AssertionCanonicalRecord`, `from_payload`, `to_payload`, or imports of
  `assertions.codec`;
- zero assertion field-name parsing in support-revision snapshot code;
- snapshot bytes round-trip a typed tagged atom union through Quire;
- malformed/unknown/old assertion shapes fail strictly;
- focused assertion and support-revision tests pass through the logged wrapper;
- `uv run pyright propstore` passes.

## Per-slice execution protocol

For each of the five slices:

1. Record branch, HEAD, and tracked-file status. Do not absorb the pre-existing
   untracked files.
2. Add the slice's exact symbol/caller inventory to the execution log below.
3. Delete the named old production surface first.
4. For every resulting import, type, or test failure, record the broken
   dependency edge and one allowed classification before editing it.
5. Apply the disposition. A missing name is never restored to make imports or
   tests green.
6. Run the focused production-path test through
   `powershell -File scripts/run_logged_pytest.ps1 ...`.
7. Run `uv run pyright propstore`.
8. Run the slice's zero-surface searches.
9. If kept, commit the complete slice and append the commit SHA here. If
   rejected, restore the complete tracked slice and record why.
10. Only after the slice is committed or restored may the next slice begin.

After all five committed slices, run the full logged test suite and
`uv run pyright propstore`, then repeat the combined repository search for all
deleted symbols and mapping surfaces. Passing tests do not override a nonzero
forbidden-surface search.

## Execution log

### Slice 1: assertion source conversion

- Baseline: `010e42be`; tracked files clean. Untracked
  `pyghidra_mcp_projects/`, `reviews/2026-07-11-propstore-deep-review.md`, and
  `tests/test_micropub_clark_charter.py` excluded.
- Deleted old surface: `core/assertions/conversion.py`,
  `AssertionSourceRecord`, `assertion_source_record_from_payload`, and the
  package exports.
- Deleted scaffold: `tests/test_structural_assertion_conversion.py`.
- Retained owner behavior: role-signature acceptance and rejection now exercise
  `RoleSignature.validate_bindings` directly in `test_situated_assertions.py`.
- Zero-surface search: no deleted conversion symbols or imports under
  `propstore` or `tests`.
- Focused gate: logged `tests/test_situated_assertions.py` — 7 passed.
- Type gate: `uv run pyright propstore` — 0 errors.
- Commit: pending this slice commit.

Each later entry must contain: baseline HEAD/status, exact deleted symbols,
dependency-edge classifications and dispositions, focused/full gate commands
and results, zero-surface search results, and the kept commit SHA or
full-revert result.
