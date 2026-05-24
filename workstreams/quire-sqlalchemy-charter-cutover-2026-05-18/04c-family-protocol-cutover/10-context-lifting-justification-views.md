# 10 Context Lifting Justification Views

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`
- `06-source-lifecycle-state-machines.md`
- `07-proposal-lifecycle-state-machines.md`
- `08-artifact-graph-verification-export.md`
- `09-worldline-resolution-protocol.md`

## Target

Context lifting semantics live under the context family owner. Justification
semantic views are named views over typed graph/justification models, not a
duplicate schema/conversion path.

## Deletion Targets

- root `propstore.context_lifting` persisted-shape ownership
- `filter_invalid_context_lifting_rows`
- `compile_context_sidecar_rows`
- `compile_context_lifting_materialization_rows`
- raw context table selectors for context/lifting records
- `CanonicalJustification` duplicate schema/conversion role
- broad `CanonicalJustification(` construction outside the final named
  semantic-view owner
- `_claim_algorithm_variable_from_payload` unless renamed as an explicit claim
  algorithm IO/parser boundary

## Kept Behavior

- Lifting rules, exceptions, decisions, provenance, condition evaluation, and
  `LiftingSystem` behavior.
- Active-graph-derived justification view behavior.
- Claim algorithm variable parsing as a claim algorithm boundary parser.

## Execution

1. Move context lifting semantic types and algorithms under the context family
   owner.
2. Keep persisted context/lifting document shape in generated context charter
   documents.
3. Delete duplicated context row/materialization helper paths.
4. Delete duplicate `CanonicalJustification` construction/schema paths.
5. Keep one named typed justification semantic view owner.
6. Rename or delete broad `_from_payload` algorithm parser helper.

## Search Gates

```powershell
rg -n -F -- "propstore.context_lifting" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_TABLE" propstore tests
rg -n -F -- "FROM context_lifting_rule" propstore tests
rg -n -F -- "FROM context_lifting_materialization" propstore tests
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "_from_payload" propstore/families/claims propstore/core tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label context-justification-views tests/test_contexts.py tests/test_context_lifting_ws5.py tests/test_aspic_bridge.py tests/test_world_query.py
```

## Completion

- Context lifting semantics have a context-family owner.
- Persisted context/lifting document shape comes from context charter fields.
- Justification view construction is not a second schema layer.
