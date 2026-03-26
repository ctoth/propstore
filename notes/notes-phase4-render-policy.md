# Phase 4: Render Policy Extensions — Session Notes

## GOAL
Add decision criterion selection (pignistic, lower_bound, upper_bound, hurwicz) to RenderPolicy so render layer can interpret opinion data differently per policy.

## DONE
- Read all 7 required files from the prompt
- Understand RenderPolicy (frozen dataclass, types.py:180-196) — 7 fields, all with defaults
- Understand WorldlinePolicy (worldline.py:52-115) — parallel structure, from_dict/to_dict serialization
- Understand resolve() dispatch (resolution.py:210-341) — extracts policy fields at lines 241-262
- Understand Opinion class (opinion.py) — expectation() = b + a*u, uncertainty_interval() = (b, 1-d)
- Read impact analysis Change 7 section — LOW risk, add fields with defaults
- Read Denoeux 2019 notes — pignistic is default, Hurwicz = α·Bel + (1-α)·Pl
- Read Jøsang 2001 notes — E(ω) = b + a·u, Bel = b, Pl = 1-d

## FILES TO MODIFY
1. `propstore/world/types.py` — Add 3 fields to RenderPolicy + apply_decision_criterion function
2. `propstore/worldline.py` — Add 3 fields to WorldlinePolicy, update from_dict/to_dict
3. `propstore/world/resolution.py` — Extract new fields from policy (around line 252)
4. `propstore/cli/compiler_cmds.py` — Add --decision-criterion and --pessimism-index CLI options
5. `tests/test_render_policy_opinions.py` — NEW test file (10 tests, write FIRST)

## KEY OBSERVATIONS
- RenderPolicy is frozen=True dataclass — adding fields with defaults is safe
- WorldlinePolicy.from_dict uses .get() with defaults — backward compatible
- worldline_runner.py:70-76 constructs RenderPolicy explicitly — needs new fields passed through
- CLI world_resolve at compiler_cmds.py:1242-1289 — add options after --confidence-threshold
- resolve() function doesn't directly use opinion data yet — the prompt says to extract new fields and use apply_decision_criterion when argumentation backends return stance data with opinion columns

## IMPLEMENTATION STATUS
- [x] tests/test_render_policy_opinions.py — 12 tests written, confirmed ImportError (red phase)
- [x] propstore/world/types.py — Added 3 fields to RenderPolicy + apply_decision_criterion function
- [x] propstore/worldline.py — Added 3 fields to WorldlinePolicy, updated from_dict/to_dict
- [x] propstore/world/resolution.py — Extract new fields from policy (lines 254-258)
- [x] propstore/worldline_runner.py — Pass new fields when constructing RenderPolicy (line 70-78)
- [x] propstore/cli/compiler_cmds.py — Added --decision-criterion and --pessimism-index to world_resolve

## NEXT
1. Run tests/test_render_policy_opinions.py — should pass now
2. Run full test suite — must be >= 1144 passing
3. Precommit + commit
4. Write report
