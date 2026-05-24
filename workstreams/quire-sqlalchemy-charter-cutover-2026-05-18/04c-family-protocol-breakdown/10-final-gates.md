# 10 Final Gates

## Final State

The 04c family protocol cleanup is complete only after all previous child
workstreams pass their gates and the old-path gates below pass from the current
repo state.

## Order Gate

```powershell
uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md
```

## Dependency Gates

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

All dependency gates are zero-hit gates for local Quire pins.

## Production Old-Path Gates

```powershell
rg -n -F -- "from propstore.families.world_charters" propstore tests
rg -n -F -- "propstore.families.world_charters" propstore tests scripts
rg -n -F -- "claim_metadata_value" propstore tests
rg -n -F -- "from propstore.families.documents" propstore tests
rg -n -F -- "DocumentStruct" propstore/families propstore/source propstore/worldline propstore/support_revision propstore/core
rg -n -F -- "DocumentBatchSpec" propstore/families propstore/source tests
rg -n -F -- 'schema.model("claim_core")' propstore tests
rg -n -F -- 'schema.model("concept")' propstore tests
rg -n -F -- 'schema.model("alias")' propstore tests
rg -n -F -- 'derived.schema.table("claim_core")' propstore tests
rg -n -F -- 'derived.schema.table("build_diagnostics")' propstore tests
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "_from_payload" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- 'claim["' tests/test_world_query.py
rg -n -F -- "propstore.concept_ids" propstore tests
rg -n -F -- "propstore.context_lifting" propstore tests
rg -n -F -- "propstore.worldline.resolution" propstore tests
rg -n -F -- "StanceProposalPromotionPlan" propstore tests
rg -n -F -- "RuleProposalPromotionPlan" propstore tests
rg -n -F -- "PredicateProposalPromotionPlan" propstore tests
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-protocol-breakdown-targeted tests/test_world_query.py tests/test_graph_export.py tests/test_contexts.py tests/test_aspic_bridge.py tests/test_source_claims.py tests/test_source_relations.py tests/test_worldline.py tests/test_contract_manifest.py
powershell -File scripts/run_logged_pytest.ps1 -Label family-protocol-breakdown-full
```

## Parity Gates

Run the parity gates named by the parent workstream files for the touched
owners:

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/world-query-graph-reasoning/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/world-query-graph-reasoning/after.sqlite --owner world-query-graph-reasoning --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/12-world-query-graph-reasoning.md --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning-behavior.json --require-behavior world-query --require-behavior graph-build --require-behavior atms --require-behavior scm-intervention-resolution --require-behavior worldline --require-behavior support-revision --require-behavior aspic
```

## Completion

- [ ] Every child workstream is complete.
- [ ] Order, dependency, production old-path, type, test, and parity gates pass.
- [ ] The parent `04c-family-document-and-relationship-protocol.md` points to
      this breakdown.
