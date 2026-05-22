# Wave 1-C Gate Audit: Claim Graph, Relations, Micropublications, Model Cleanup

Date: 2026-05-21

## Files Audited

- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/08a-typed-claim-graph-projection.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/09-relations-stances-conflicts.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/10-micropublications-justifications.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/10a-charter-generated-model-cleanup.md`

## Scope

- Ran only read-only `rg` searches.
- Did not use `git log`.
- Did not run `pyright`.
- Did not run pytest.
- All repository searches were run from `C:\Users\Q\code\propstore`.
- No audited search path targeted `C:\Users\Q\code\quire`, so no Quire-cwd gate was run.

## Result Summary

| Workstream | Result | Notes |
| --- | --- | --- |
| `08a-typed-claim-graph-projection.md` | Pass | Deletion gates are clean. Allowed/false-positive hits remain only for parameterization `conditions_cel` handling and `ATMSClaimNode(`. |
| `09-relations-stances-conflicts.md` | Pass | All required relation old-path searches returned zero hits. |
| `10-micropublications-justifications.md` | Fail | `CanonicalJustification(` still has production and test hits. All other searched old paths returned zero hits. |
| `10a-charter-generated-model-cleanup.md` | Pass | All required model-cleanup searches returned zero hits after rerunning the regex gate with corrected PowerShell quoting. |

## Commands Run

### Extraction Commands

```powershell
rg -n -F -- "rg -n" workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\08a-typed-claim-graph-projection.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\09-relations-stances-conflicts.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10-micropublications-justifications.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10a-charter-generated-model-cleanup.md
rg -n -F -- "zero-hit" workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\08a-typed-claim-graph-projection.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\09-relations-stances-conflicts.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10-micropublications-justifications.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10a-charter-generated-model-cleanup.md
rg -n -F -- "Search Gates" workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\08a-typed-claim-graph-projection.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\09-relations-stances-conflicts.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10-micropublications-justifications.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10a-charter-generated-model-cleanup.md
rg -n -F -- "Required Gates" workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\08a-typed-claim-graph-projection.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\09-relations-stances-conflicts.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10-micropublications-justifications.md workstreams\quire-sqlalchemy-charter-cutover-2026-05-18\10a-charter-generated-model-cleanup.md
```

### `08a` Search Gates

```powershell
rg -n -F -- 'attributes["conditions_cel"]' propstore tests
rg -n -F -- 'attributes["sample_size"]' propstore tests
rg -n -F -- "conditions_cel" propstore/world/overlay.py propstore/core/graph_build.py
rg -n -F -- "sample_size" propstore/world/overlay.py propstore/core/graph_build.py
rg -n -F -- "ClaimNode(" propstore/core propstore/world tests/test_world_query.py
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- ".resolve_claim(" propstore tests
```

### `09` Search Gates

```powershell
rg -n -F -- "propstore.families.relations.projection_model" propstore tests
rg -n -F -- "RelationshipRow" propstore tests
rg -n -F -- "StanceRow" propstore tests
rg -n -F -- "ConflictRow" propstore tests
rg -n -F -- "RELATION_EDGE_TABLE" propstore tests
rg -n -F -- "CLAIM_STANCE_STORAGE_MODEL" propstore tests
rg -n -F -- "CONCEPT_RELATIONSHIP_STORAGE_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "CONFLICT_ROW_MODEL" propstore tests
rg -n -F -- "_optional_numeric" propstore/families/relations tests
rg -n -F -- "compile_authored_stance_sidecar_rows" propstore tests
rg -n -F -- "compile_authored_stance_sidecar_rows_with_diagnostics" propstore tests
rg -n -F -- "select_stances_between" propstore tests
rg -n -F -- "select_conflicts" propstore tests
rg -n -F -- "select_all_relationships" propstore tests
rg -n -F -- "select_all_claim_stances" propstore tests
rg -n -F -- "select_claim_stances_with_policy" propstore tests
rg -n -F -- "select_explanation_stances" propstore tests
rg -n -F -- "count_conflicts" propstore tests
```

### `10` Search Gates

```powershell
rg -n -F -- "MicropublicationProjectionRow" propstore tests
rg -n -F -- "MicropublicationClaimProjectionRow" propstore tests
rg -n -F -- "MicropublicationSidecarRows" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "MICROPUBLICATION_PROJECTION" propstore tests
rg -n -F -- "MICROPUBLICATION_CLAIM_PROJECTION" propstore tests
rg -n -F -- "MICROPUBLICATION_ROW_MODEL" propstore tests
rg -n -F -- "JUSTIFICATION_STORAGE_MODEL" propstore tests
rg -n -F -- "propstore.families.claims.projection_model" propstore tests
rg -n -F -- "ActiveMicropublication.from_mapping" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "compile_micropublication_sidecar_rows" propstore tests
rg -n -F -- "compile_micropublication_sidecar_rows_with_diagnostics" propstore tests
rg -n -F -- "create_micropublication_tables" propstore tests
rg -n -F -- "populate_micropublications" propstore tests
rg -n -F -- "select_all_micropublications" propstore tests
rg -n -F -- "_normalize_attrs" propstore tests
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "from_mapping" propstore/core/justifications.py tests
```

### `10a` Search Gates

```powershell
rg -n -F -- "__init__(self, **values" propstore/families propstore/core propstore/world tests
rg -n -F -- "from_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- ".coerce(" propstore/families propstore/core propstore/world tests
rg -n -F -- "Input = " propstore/families propstore/core propstore/world tests
rg -n -F -- "to_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- "class WorldModel" propstore tests
rg -n -- 'class .*Record\(' propstore/families/world_charters.py propstore tests
rg -n -F -- "coerce_loaded_context" propstore tests
```

The first attempt at the `class .*Record\(` regex was over-escaped for PowerShell and failed before searching:

```powershell
rg -n -- "class .*Record\\(" propstore/families/world_charters.py propstore tests
```

It was rerun with the PowerShell-safe command shown above and returned zero hits.

## Gate Details

### `08a-typed-claim-graph-projection.md`

| Gate | Result | Interpretation |
| --- | --- | --- |
| `attributes["conditions_cel"]` in `propstore tests` | Pass | Zero hits. Absence/deletion gate. |
| `attributes["sample_size"]` in `propstore tests` | Pass | Zero hits. Absence/deletion gate. |
| `conditions_cel` in overlay/graph-build | Pass | Hits are parameterization condition handling, which the workstream allows. |
| `sample_size` in overlay/graph-build | Pass | Zero hits. Absence/deletion gate. |
| `ClaimNode(` in `propstore/core propstore/world tests/test_world_query.py` | Pass | One `ATMSClaimNode(` substring hit, not a `ClaimNode` projection. |
| `def resolve_claim` in `propstore tests` | Pass | Zero hits. Absence/deletion gate from execution record. |
| `.resolve_claim(` in `propstore tests` | Pass | Zero hits. Absence/deletion gate from execution record. |

Allowed/false-positive hits:

```text
propstore/core/graph_build.py:153:    if parameterization.conditions_cel:
propstore/core/graph_build.py:156:            f"{parameterization.output_concept_id} has conditions_cel without "
propstore/core/graph_build.py:195:                    row.conditions_cel,
propstore/core/graph_build.py:340:                            "conditions_cel": parameterization.conditions_cel,
propstore/world\atms.py:1397:            self._nodes[node_id] = ATMSClaimNode(
```

### `09-relations-stances-conflicts.md`

All required `09` old-path searches returned zero hits. These are absence/deletion gates, so zero hits are interpreted as pass.

Passed gates:

```text
propstore.families.relations.projection_model
RelationshipRow
StanceRow
ConflictRow
RELATION_EDGE_TABLE
CLAIM_STANCE_STORAGE_MODEL
CONCEPT_RELATIONSHIP_STORAGE_MODEL
RELATIONSHIP_ROW_MODEL
STANCE_ROW_MODEL
CONFLICT_ROW_MODEL
_optional_numeric
compile_authored_stance_sidecar_rows
compile_authored_stance_sidecar_rows_with_diagnostics
select_stances_between
select_conflicts
select_all_relationships
select_all_claim_stances
select_claim_stances_with_policy
select_explanation_stances
count_conflicts
```

### `10-micropublications-justifications.md`

All searched `10` old paths returned zero hits except `CanonicalJustification(`.

Passed absence/deletion gates:

```text
MicropublicationProjectionRow
MicropublicationClaimProjectionRow
MicropublicationSidecarRows
ActiveMicropublication
ActiveMicropublicationInput
MICROPUBLICATION_PROJECTION
MICROPUBLICATION_CLAIM_PROJECTION
MICROPUBLICATION_ROW_MODEL
JUSTIFICATION_STORAGE_MODEL
propstore.families.claims.projection_model
ActiveMicropublication.from_mapping
coerce_active_micropublication
_parse_string_tuple
compile_micropublication_sidecar_rows
compile_micropublication_sidecar_rows_with_diagnostics
create_micropublication_tables
populate_micropublications
select_all_micropublications
_normalize_attrs
from_mapping
```

Failing gate:

```powershell
rg -n -F -- "CanonicalJustification(" propstore tests
```

Failing hits:

```text
propstore\aspic_bridge\extract.py:67:            CanonicalJustification(
propstore\aspic_bridge\extract.py:80:        CanonicalJustification(
propstore\aspic_bridge\extract.py:91:            CanonicalJustification(
propstore\core\justifications.py:40:        return CanonicalJustification(
propstore\core\justifications.py:116:        CanonicalJustification(
propstore\core\justifications.py:131:            CanonicalJustification(
tests\remediation\phase_4_layers\test_T4_8_exception_defeats_post_preference.py:35:                CanonicalJustification(
tests\remediation\phase_5_bridge\test_T5_1_undermines_preference_sensitive.py:29:    return CanonicalJustification(
tests\remediation\phase_5_bridge\test_T5_11_exception_sibling_survival.py:35:    return CanonicalJustification(
tests\remediation\phase_5_bridge\test_T5_6_bridge_edge_domain_invariant.py:35:                CanonicalJustification(
tests\remediation\phase_5_bridge\test_T5_7_justification_unknown_premise.py:24:                CanonicalJustification(
tests\remediation\phase_5_bridge\test_T5_9_projection_premise_dependency_split.py:25:    return CanonicalJustification(
tests\test_aspic_bridge.py:152:    return CanonicalJustification(
tests\test_aspic_bridge.py:1461:            CanonicalJustification(
tests\test_aspic_bridge.py:1466:            CanonicalJustification(
tests\test_aspic_bridge_review_v2.py:46:    return CanonicalJustification(
tests\test_defeasibility_aspic_integration.py:40:    return CanonicalJustification(
tests\test_projection_boundary_ws6.py:33:            CanonicalJustification(
tests\test_structured_projection.py:376:            CanonicalJustification(
tests\test_structured_projection.py:419:            CanonicalJustification(
tests\test_structured_projection.py:462:            CanonicalJustification(
tests\test_structured_projection.py:469:            CanonicalJustification(
tests\test_ws_f_aspic_bridge.py:83:    return CanonicalJustification(
tests\test_ws_f_aspic_bridge.py:99:    return CanonicalJustification(
```

Interpretation: this is a required zero-hit old-path search in the workstream. The gate fails in current repo state.

### `10a-charter-generated-model-cleanup.md`

All required `10a` searches returned zero hits. These are absence/deletion gates, so zero hits are interpreted as pass. The extra `coerce_loaded_context` search named in the execution log also returned zero hits.

Passed gates:

```text
__init__(self, **values
from_row_mapping
.coerce(
Input = 
to_row_mapping
class WorldModel
class .*Record\(
coerce_loaded_context
```

## Ambiguous Or Uninterpretable Gates

None. The only non-zero `08a` hits are covered by explicit allowed-hit language or are a fixed-string false positive against `ATMSClaimNode(`. The `10` `CanonicalJustification(` gate is not ambiguous because the workstream lists it in the required zero-hit search block.
