# Quire Registry Query Helpers Workstream

## Goal

Move generic family-registry query mechanics into `../quire` while keeping
Propstore's semantic family catalog in Propstore.

The target architecture is:

- Quire owns reusable registry selection and lookup utilities over
  `FamilyRegistry` / `FamilyDefinition` metadata and placement contracts.
- Propstore owns `PropstoreFamily`, `PROPSTORE_FAMILY_REGISTRY`, semantic
  metadata values, family names, import ordering, and semantic root policy.
- Propstore's `semantic_*` helpers become thin applications of generic Quire
  registry queries or disappear where the generic query is clearer at the call
  site.
- The kept result should shrink Propstore. If a Propstore helper does not add
  semantic policy after Quire grows the generic query, delete it instead of
  renaming or wrapping it.

This is a two-repository workstream. Quire changes land first. Propstore must
never pin Quire to a local path; pin only to a pushed tag or immutable pushed
commit SHA.

## Non-Goals

Do not move these into Quire:

- `PropstoreFamily`
- `PROPSTORE_FAMILY_REGISTRY`
- any Propstore family name or root such as `claims`, `concepts`, `stances`, or
  `worldlines`
- the meaning of metadata keys such as `semantic`, `importable`,
  `import_order`, `init_directory`, `collection_field`, or `trajectory_field`
- source import normalization, source promotion, proposal promotion, sidecar
  policy, or compiler workflows

Do not add compatibility wrappers. When a Propstore helper is replaced, delete
the old production helper first and use the resulting failures as the caller
work queue.

## Dependency Order

The phases below are topologically ordered.

1. Quire registry query primitives
2. Quire placement namespace/root introspection
3. Propstore dependency pin
4. Propstore semantic helper deletion
5. Contract, docs, and gates

## Phase 1: Quire Registry Query Primitives

Repository: `../quire`

Add generic query helpers for `FamilyRegistry` and `FamilyDefinition`.

Candidate API:

```python
registry.select(lambda family: family.metadata_value("semantic") is True)
registry.select_by_metadata("semantic", True)
registry.by_metadata("root", "claims")
family.metadata_value("import_order", default=100)
```

Acceptable alternative:

- free functions in `quire.families` if they fit the existing module better
- no Propstore vocabulary in names, docs, or tests

Required behavior:

- metadata lookup treats missing metadata as empty
- default values are explicit at the call site
- filtering is lazy or tuple-returning consistently with existing Quire style
- duplicate single-result lookups fail with typed `ValueError` or `KeyError`
  before returning an arbitrary family
- registry contract output is unchanged unless the helper requires new contract
  fields

Tests:

- `../quire/tests/test_families.py`
- use consumer-neutral family names such as `books`, `notes`, or `events`

Required gates:

- `uv run pytest tests/test_families.py`
- `uv run pytest`

## Phase 2: Quire Placement Namespace/Root Introspection

Repository: `../quire`

Add generic placement introspection so callers do not inspect raw
`contract_body()` dictionaries to find roots.

Candidate API:

```python
family.artifact_family.placement.namespace()
family.storage_root()
registry.by_storage_root("books")
registry.family_for_path("books/example.yaml")
```

Requirements:

- namespace-backed placements expose a generic storage root
- non-namespace placements fail clearly when used in root lookup
- root lookup remains placement-driven; do not introduce a second root field
- no Propstore-specific path names or filenames in Quire

Placements to cover:

- `FlatYamlPlacement`
- `HashScatteredYamlPlacement`
- `SubdirFixedFilePlacement`
- `NestedFlatYamlPlacement`
- any existing placement that has a namespace-like root

Required gates:

- `uv run pytest tests/test_artifacts.py tests/test_families.py`
- `uv run pytest`

## Phase 3: Propstore Dependency Pin

Repository: `propstore`

Only start after the Quire changes are pushed to a shared remote.

Before editing dependency files:

- verify the Quire target is a pushed tag or immutable pushed commit SHA
- reject local paths, editable paths, local git paths, Windows drive paths, WSL
  paths, and `file://` URLs

Update:

- `pyproject.toml`
- `uv.lock`

Required gate:

- `uv run pyright propstore`

## Phase 4: Propstore Semantic Helper Deletion

Repository: `propstore`

Before writing replacement code, delete the Propstore helpers that are now
generic registry queries. The goal is net Propstore shrinkage, not a spelling
change.

Delete first from `propstore/families/registry.py` where directly replaced:

- `_metadata`
- `_semantic_root`
- helper-local metadata dispatch that Quire can now express generically

Then update callers and keep only Propstore-semantic policy helpers that still
add domain meaning.

Likely retained helpers:

- `semantic_families()`
- `semantic_import_families()`
- `semantic_foreign_keys()`

Retain these only if they still encode Propstore semantic policy. If they
become one-line aliases over Quire, delete them and update callers directly.

Likely deleted or reduced helpers:

- `semantic_family_by_root`
- `semantic_family_for_path`
- `semantic_root_path`
- raw `placement.contract_body()["namespace"]` access

Known callers:

- `propstore/importing/repository_import.py`
- `propstore/source/passes.py`
- tests in `tests/test_semantic_family_registry.py`

Search gates:

- `rg -F "contract_body()[\"namespace\"]" propstore tests` returns no refs
- `rg -F "placement_body.get(\"namespace\")" propstore tests` returns no refs
- `rg -F "def _semantic_root" propstore/families/registry.py` returns no refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label registry-query-helpers tests/test_semantic_family_registry.py tests/test_import_repo.py tests/test_artifact_store.py`
- `uv run pyright propstore`

## Phase 5: Contract, Docs, and Gates

Repository: both

Docs:

- Quire README: document generic registry metadata/root queries
- Propstore AGENTS or nearby architecture docs: state that family declarations
  remain Propstore-owned while generic registry querying belongs to Quire

Final Quire gates:

- `uv run pytest`

Final Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label registry-query-helpers-full tests/test_semantic_family_registry.py tests/test_import_repo.py tests/test_artifact_store.py tests/test_contract_manifest.py`
- `uv run pyright propstore`

Completion evidence:

- Propstore no longer reaches into placement contract dictionaries for roots
- Quire has no Propstore vocabulary in registry query code
- semantic family declarations remain in `propstore/families/registry.py`
- no dependency metadata points at a local Quire checkout
