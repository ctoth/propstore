# Notes: Fix ATMS Interventions CLI

## GOAL
Add `atms-interventions` and `atms-next-query` CLI commands to `compiler_cmds.py`.

## DONE
- Read prompt file
- Read test at line 1520 of test_atms_engine.py — defines exact expected CLI and output
- Read backend methods: `BoundWorld.claim_interventions` and `BoundWorld.claim_next_queryables`
- Read return dict structure from `_node_intervention_plan` (keys: queryable_cels, target_status, result_status)
- Read `_next_queryables_from_plans` return structure (keys: queryable_cel, plan_count aka coverage, smallest_plan_size)
- Read existing similar commands (atms-stability, atms-relevance) for pattern
- Read helper functions: `_parse_queryables`, `_format_assumption_ids`, `_bind_atms_world`

## FILES
- `propstore/cli/compiler_cmds.py` — where commands go (after line ~1109, before `derive`)
- `tests/test_atms_engine.py:1520` — the test
- `propstore/world/bound.py:414-466` — backend methods
- `propstore/world/atms.py:1509-1590` — return dict structures

## KEY OBSERVATIONS
- Test expects: `--target-status IN` option (required), `--queryable` (multiple)
- Test CLI: `["world", "atms-interventions", "claim_future", "x=1", "--target-status", "IN", "--queryable", "y=2", "--queryable", "z=3"]`
- Interventions output must contain: "bounded additive plans over declared queryables", "not revision/contraction", "plan [y == '2'] -> IN"
- Next-query output must contain: "derived from bounded additive intervention plans", "y == '2': coverage=1 smallest_plan_size=1"
- Plan dict has: queryable_cels, result_status (ATMSNodeStatus enum with .value)
- Next-query dict has: queryable_cel, plan_count, smallest_plan_size
- Pattern: first arg is target (claim_id), rest are bindings via nargs=-1 args

## NEXT
- Confirm RED (test fails)
- Implement two commands in compiler_cmds.py
- Confirm GREEN
- Run full suite
- Commit
