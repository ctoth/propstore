# 03 Generic Family Model Lookup

## Final State

No production code asks for tables or models through string literals such as
`schema.model("claim_core")` or `derived.schema.table("claim_core")`.

Family model/table/reference lookup is generic Quire/family metadata behavior.
Propstore family owners declare reference keys and semantic behavior; callers
use the generic lookup API or a true owner API whose implementation uses that
generic path.

## Delete First

Delete production direct string lookup for:

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

Use the resulting failures as the work queue.

## Repair Owners

- Claim lookup and claim table/model access: claim family owner plus Quire
  family metadata.
- Concept and alias lookup: concept family reference metadata plus generic
  Quire reference lookup.
- Context and lifting lookup: context family metadata plus generic Quire model
  lookup.
- Diagnostics lookup: diagnostics family metadata plus source/diagnostic owner
  query APIs.
- App presentation modules call owner APIs; they do not open family models.

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
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label generic-family-model-lookup tests/test_world_query.py tests/test_contexts.py tests/test_concept_workflows.py tests/test_cli_source_status.py tests/test_required_schema_completeness.py
```

## Completion

- [ ] Every direct string model/table lookup gate is zero-hit.
- [ ] Claim/concept/context/diagnostic lookup behavior still passes tests.
- [ ] No per-family wrapper replaces the deleted string lookup.
