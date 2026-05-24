# 02 Quire Generated Family Protocols

## Prerequisites

- `01-deleted-file-fallout-repair.md`

## Target

Add the missing Quire generic capabilities before Propstore deletes broad
document, lifecycle, graph, artifact, and local-id surfaces.

## Required Quire Capabilities

- `FamilyCharter` generates strict msgspec document structs from charter fields.
- `CharterField` carries document inclusion metadata. Inclusion is default;
  storage-only fields opt out explicitly.
- `DocumentCodec` and `DocumentFamilyStore` consume generated document types.
- Lifecycle state and transition metadata are declared generically and executed
  over typed generated family documents/models.
- Relationship traversal and graph projection records are generated from
  `CharterRelationship`, reference keys, and field metadata.
- Artifact payload and artifact dependency edges are generated from declared
  artifact-participating fields and relationships, with Propstore semantic
  callbacks only for domain policy.
- Generic local-id reservation exists for monotonic family-local handles.
- FTS and vector caches prove concept FTS, claim FTS, and one vector cache use
  the same generic family metadata path.
- The broad `FamilyModel.__init__(**values)` sink is proved as SQLAlchemy
  instrumentation-only or removed from Quire's authored construction surface.

## Deletion-First Execution

1. Add failing Quire tests for generated document structs/codecs from a small
   charter.
2. Implement generated document structs/codecs in Quire.
3. Add lifecycle tests over two families that are not claims.
4. Implement generic lifecycle transition metadata and execution.
5. Add graph/artifact traversal tests over non-claim relationships.
6. Implement generic graph and artifact protocols.
7. Add local-id reservation tests using generic family metadata.
8. Implement reservation without Propstore concept-specific code.
9. Close the FTS/vector proof gaps.
10. Push Quire before Propstore pins it.

## Quire Gates

```powershell
Set-Location C:\Users\Q\code\quire
rg -n -F -- "msgspec.defstruct" quire tests
rg -n -F -- "document=True" quire tests
rg -n -F -- "transition" quire tests
rg -n -F -- "reserve" quire tests
rg -n -F -- "graph_projection" quire tests
rg -n -F -- "**values" quire tests
uv run pytest -vv tests/test_documents.py tests/test_family_store.py tests/test_charters_schema_ir.py tests/test_sqlalchemy_engine.py tests/test_references.py
uv run pyright
```

## Dependency Gates

```powershell
Set-Location C:\Users\Q\code\quire
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml uv.lock
rg -n -F -- "workspace = true" pyproject.toml uv.lock
rg -n -F -- "C:" pyproject.toml uv.lock
uv run pytest -vv
uv run pyright
```

## Completion

- Quire is pushed.
- Propstore can pin a pushed Quire SHA.
- Propstore does not need a local workaround for generated documents,
  lifecycle, graph/artifacts, local-id reservation, or FTS/vector metadata.
