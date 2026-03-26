# CLI Phase 2: world query/bind — show SI values — Session Notes

## GOAL
Add SI-normalized value display to `pks world query` and `pks world bind` CLI commands.

## OBSERVATIONS

### Current state of `world_query` (compiler_cmds.py:579-599)
- Prints: `{c['id']}: {c['type']} value={c.get('value')} conditions={conds}`
- Does NOT show `unit` or `value_si`
- Uses `wm.claims_for(resolved)` which does `SELECT * FROM claim` — so `value_si` and `unit` columns ARE in the dict already

### Current state of `world_bind` (compiler_cmds.py:605-647)
- With concept: prints `{c['id']}: value={c.get('value')} source={c.get('source_paper')}`
- Without concept: prints `{c['id']}: {c.get('concept_id', '?')} value={c.get('value')} conditions={conds}`
- Also does NOT show `unit` or `value_si`

### Sidecar schema (build_sidecar.py:819)
- Claim table has `value_si REAL` column
- 0.2 kHz -> value_si = 200.0
- Canonical unit Hz -> value_si == value
- No unit -> value_si == value

### Test fixture needed
- `freq_workspace` fixture: workspace with a frequency concept + kHz claim + built sidecar
- Existing `workspace` fixture creates concepts but does NOT build sidecar or add claims
- Existing `built_workspace` fixture in TestQueryReadOnly builds sidecar but no claims with unit != canonical

### Claim YAML format (from test_build_with_claims)
```yaml
source: {paper: paper}
claims:
  - id: claim1
    type: parameter
    concept: concept1
    value: 0.2
    unit: kHz
    provenance: {paper: paper, page: 1}
```

## PLAN
1. Create `freq_workspace` fixture with concept1 (frequency) + claim with 0.2 kHz
2. Write RED tests for TestWorldQuerySIValues
3. Run tests, confirm failure
4. Implement SI display in world_query and world_bind
5. Run full suite

## STATUS — checkpoint 3 (DONE)
- Fixture: `freq_workspace` — overwrites frequency form with full SI definition (unit_symbol: Hz, kHz multiplier)
- RED confirmed: both tests failed
- GREEN confirmed: both tests pass (1056 pass, 1 pre-existing failure in test_atms_engine)
- `compiler_cmds.py` staged, `tests/test_cli.py` already committed (from parallel subagent?)
- Key fix: workspace fixture's minimal form YAML had no unit_symbol/common_alternatives, so value_si was never normalized. Fixed by writing full frequency form in freq_workspace fixture.
- Also fixed pre-existing closed-database bug in world_query (used wm outside `with` block)
- Pre-existing failure: test_atms_cli_surfaces_interventions_and_next_queries (missing CLI command)
- NEXT: need to add tests/test_cli.py to staging, commit, write report
