# 02 Quire Document And Family Protocol

## Final State

Quire owns generated document structs/codecs, generated mapped family models,
relationship/reference metadata, lifecycle transitions, artifact payload and
dependency metadata, graph projection records, and local-id reservation.
Propstore supplies charters and semantic callbacks only.

`quire/charters.py` does not expose a broad public `**values` construction sink
for generated family model field shape. Generated model construction is typed
or produced by the Quire generator.

## Required Quire Work

1. Generate msgspec document structs from `FamilyCharter` fields.
2. Generate document codecs from the generated document structs.
3. Add document inclusion metadata to charter fields.
4. Add relationship/reference metadata used by generic traversal and lookup.
5. Add lifecycle transition metadata and execution over family records.
6. Add artifact field/dependency metadata and canonical payload generation
   hooks.
7. Add graph projection metadata and generic graph records.
8. Add generic local-id reservation/counter support.
9. Remove or replace the `quire/charters.py:**values` field-shape sink.

## Search Gates

Run from `C:\Users\Q\code\quire`:

```powershell
rg -n -F -- "msgspec.defstruct" quire tests
rg -n -F -- "document=True" quire tests
rg -n -F -- "transition" quire tests
rg -n -F -- "reserve" quire tests
rg -n -F -- "graph_projection" quire tests
rg -n -F -- "**values" quire tests
```

`**values` is a zero-hit gate for generated family model construction sinks.

## Test Gates

Run from `C:\Users\Q\code\quire`:

```powershell
uv run pytest -vv tests/test_documents.py tests/test_family_store.py tests/test_charters_schema_ir.py tests/test_families.py tests/test_references.py tests/test_sqlalchemy_engine.py
uv run pyright
```

## Dependency Gates

Run from `C:\Users\Q\code\quire` before Propstore is pinned:

```powershell
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml uv.lock
rg -n -F -- "workspace = true" pyproject.toml uv.lock
rg -n -F -- "C:" pyproject.toml uv.lock
uv run pytest -vv
uv run pyright
```

Push Quire before editing Propstore dependency metadata.

## Completion

- [ ] Generated documents and codecs exist in Quire.
- [ ] Lifecycle, relationship, graph, artifact, and reservation capabilities
      exist in Quire.
- [ ] Broad model `**values` construction is gone.
- [ ] Quire tests and pyright pass.
- [ ] Quire commit is pushed.
