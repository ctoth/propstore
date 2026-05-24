# 03 Generic Family Lookup Cleanup

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`

## Target

Delete direct string table/model lookup from Propstore semantic code. Finding
the main model, identity field, alternate references, or SQLAlchemy table for a
family is generic Quire/family-registry infrastructure.

## Deletion Targets

- `derived.schema.table("claim_core")`
- `derived.schema.table("build_diagnostics")`
- `derived.schema.model("build_diagnostics")`
- `schema.model("claim_core")`
- `schema.model("concept")`
- `schema.model("alias")`
- `schema.model("context")`
- `schema.model("context_assumption")`
- `schema.model("context_lifting_rule")`
- `schema.model("context_lifting_materialization")`

## Required Owners

- Quire schema/catalog APIs expose affirmative generic accessors:
  `main_model(family_name) -> type[Any]`, `table(family_name)`,
  `identity_field(family_name) -> str`, `reference_keys(family_name)`, and
  `reference_resolver(family_name)`.
- Propstore family owners may expose semantic query APIs only when they do more
  than model/table lookup.
- Source status and diagnostics keep report semantics but stop selecting
  hardcoded tables directly.

## Execution

1. Delete one direct string lookup family at a time.
2. Use pyright/test failures as the caller queue.
3. Replace lookup-only code with generic family metadata/session APIs.
4. Keep semantic owner APIs only where they encode source status, diagnostics,
   render policy, or world reasoning behavior.
5. Do not add `resolve_claim`, `resolve_concept`, `claim_model`,
   `concept_model`, or other per-family wrappers over generic model/reference
   lookup.

## Search Gates

```powershell
rg -n -F -- 'derived.schema.table("claim_core")' propstore tests
rg -n -F -- 'derived.schema.table("build_diagnostics")' propstore tests
rg -n -F -- 'derived.schema.model("build_diagnostics")' propstore tests
rg -n -F -- 'schema.model("claim_core")' propstore tests
rg -n -F -- 'schema.model("concept")' propstore tests
rg -n -F -- 'schema.model("alias")' propstore tests
rg -n -F -- 'schema.model("context")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
rg -n -F -- 'schema.model("context_assumption")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
rg -n -F -- 'schema.model("context_lifting_rule")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
rg -n -F -- 'schema.model("context_lifting_materialization")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- "def resolve_concept" propstore tests
rg -n -F -- "def claim_model" propstore tests
rg -n -F -- "def concept_model" propstore tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label generic-family-lookup tests/test_world_query.py tests/test_contexts.py tests/test_sidecar_projection_contract.py tests/test_cli_source_status.py
```

## Completion

- Direct string model/table lookups are zero production hits.
- Per-family lookup wrappers over generic family infrastructure are zero
  production hits.
- Remaining model/reference resolution flows through Quire generic family
  metadata or a semantic owner API backed by that generic path.
