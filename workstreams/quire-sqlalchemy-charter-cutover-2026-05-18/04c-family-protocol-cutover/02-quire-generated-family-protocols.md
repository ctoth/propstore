# 02 Quire Generated Family Protocols

## Prerequisites

- `01-deleted-file-fallout-repair.md`

## Target

Add the missing Quire generic capabilities before Propstore deletes broad
document, lifecycle, graph, artifact, and local-id surfaces.

## Required Quire API

Phase 02 does not pass by adding conventions to `metadata: Mapping[str,
object]`. The following concepts must be first-class typed charter attributes
or typed charter-owned value objects. A generic metadata bag is not an
acceptable implementation for a concept named here.

`CharterField` must carry:

- `document: bool = True` for generated document inclusion.
- `document_name: str | None = None` when the on-disk document key differs
  from the Python/storage field name.
- `document_order: int | None = None` when stable document ordering matters.
- `states: frozenset[str] | None = None` for source-local, proposal,
  canonical, rejected, promoted, archived, and other state-conditional field
  participation. `source_local_only` and `canonical_only` may remain only as
  shorthand over this typed state set, not as the whole state model.
- `artifact: bool = False` for canonical artifact payload participation.
- `artifact_name: str | None = None` when artifact payload key differs from
  the field name.
- `graph_node_label: bool = False` and `graph_metadata: bool = False` for
  field participation in graph projection output.
- `local_id: bool = False` and `local_id_policy: str | None = None` for fields
  that carry family-local authoring handles.
- `contract_version: VersionId | None = None` or a typed equivalent for
  document/field-level contract version impact.
- `parse_boundary: Literal["yaml", "json", "sqlite"] | None = None` only for
  true IO-boundary parsing. Runtime semantic code must receive typed values.

`CharterRelationship` must carry:

- `artifact_dependency: bool = False` for artifact hash dependency traversal.
- `graph_edge: bool = False` and `graph_edge_kind: str | None = None` for
  graph projection.
- `states: frozenset[str] | None = None` for relationship participation by
  lifecycle state.

`FamilyCharter` must carry:

- `states: tuple[FamilyState, ...]`.
- `transitions: tuple[FamilyTransition, ...]` with source state, target state,
  guard callback id, materializer callback id, and conflict policy.
- `local_id_policy: LocalIdPolicy | None` with prefix, numeric width if any,
  counter scope, and reservation backend.
- `batch_specs: tuple[DocumentBatchSpec, ...]` with generated item document
  type, collection field, inherited fields, and document payload policy.
- `document_contract_version: VersionId`.
- `generated_document(state: str | None = None)`.
- `document_codec(state: str | None = None)`.
- `main_model()`, `identity_field()`, and `reference_resolver()` as generic
  schema/catalog accessors.

Quire must also provide:

- Generated strict msgspec document structs from `FamilyCharter` fields.
- `DocumentCodec` and `DocumentFamilyStore` consumption of generated document
  types.
- Generic lifecycle transition execution where Quire runs the transition
  framework and Propstore callback ids provide semantic guards/materializers.
- Generic relationship traversal from `CharterRelationship` and reference keys.
- Generic artifact payload/dependency traversal from typed field and
  relationship declarations.
- Generic graph projection records from typed graph field/relationship
  declarations. Rendering and display policy remain Propstore/presentation
  behavior.
- Generic local-id reservation for monotonic family-local handles.
- FTS and vector caches proving concept FTS, claim FTS, and one vector cache use
  the same generic family metadata path.
- Removal of broad authored construction through `FamilyModel.__init__(**values)`
  or a proof and gate that it is SQLAlchemy-instrumentation-only and not a
  public construction path.

## Deletion-First Execution

1. Write the Quire API spec into this file's execution record before coding.
   The spec must name exact classes, attributes, and method signatures for the
   API listed above.
2. Add failing Quire tests for generated document structs/codecs from a small
   charter.
3. Add failing Quire tests for state-conditional fields proving one charter can
   generate source/proposal/canonical document shapes without separate
   handwritten document classes.
4. Implement generated document structs/codecs in Quire.
5. Add lifecycle tests over two families that are not claims.
6. Implement generic lifecycle transition metadata and execution.
7. Add graph/artifact traversal tests over non-claim relationships.
8. Implement generic graph and artifact protocols.
9. Add local-id reservation tests using generic family metadata.
10. Implement reservation without Propstore concept-specific code.
11. Close the FTS/vector proof gaps.
12. Add generated-codec roundtrip tests over real Propstore `knowledge/`
    documents before deleting any Propstore document class.
13. Push Quire before Propstore pins it.

## Quire Gates

```powershell
Set-Location C:\Users\Q\code\quire
rg -n -F -- "msgspec.defstruct" quire tests
rg -n -F -- "document=True" quire tests
rg -n -F -- "transition" quire tests
rg -n -F -- "reserve" quire tests
rg -n -F -- "graph_projection" quire tests
rg -n -F -- "**values" quire tests
rg -n -F -- "metadata={\"document\"" quire tests
rg -n -F -- "metadata={\"artifact\"" quire tests
uv run pytest -vv tests/test_documents.py tests/test_family_store.py tests/test_charters_schema_ir.py tests/test_sqlalchemy_engine.py tests/test_references.py
uv run pyright
```

The `transition`, `reserve`, and `graph_projection` searches are not success
gates by themselves. They only prove the named API exists. The test gates must
exercise behavior using the exact API names from this phase.

## Dependency Gates

```powershell
Set-Location C:\Users\Q\code\quire
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml uv.lock
rg -n -F -- "workspace = true" pyproject.toml uv.lock
rg -n -F -- "C:\\" pyproject.toml uv.lock
rg -n -F -- "C:/" pyproject.toml uv.lock
uv run pytest -vv
uv run pyright
```

Before Propstore is pinned, verify the target Quire SHA exists on the remote:

```powershell
git ls-remote origin <sha>
```

## Completion

- Quire is pushed.
- Propstore can pin a pushed Quire SHA.
- The API above is present as typed attributes/value objects, not as ad hoc
  entries in generic metadata mappings.
- Generated codecs can load and roundtrip representative existing Propstore
  YAML/JSON artifacts.
- Propstore does not need a local workaround for generated documents,
  lifecycle, graph/artifacts, local-id reservation, or FTS/vector metadata.
