# Phase 5B-2: PrAF Integration — Session Notes

## GOAL
Integrate ReasoningBackend.PRAF into the resolution pipeline: types, resolution dispatch, worldline policy, CLI flags.

## DONE (reading phase)
- Read all 8 required files: praf.py, argumentation.py, types.py, resolution.py, worldline.py, worldline_runner.py, compiler_cmds.py, phase5b plan
- Understand the full data flow: resolve() in resolution.py dispatches by ReasoningBackend, calls _resolve_* helpers
- build_praf() already exists in argumentation.py (Phase 5B-1 deliverable)
- compute_praf_acceptance() exists in praf.py with strategies: auto, mc, deterministic, exact_enum

## KEY OBSERVATIONS
1. ReasoningBackend enum in types.py has: CLAIM_GRAPH, STRUCTURED_PROJECTION, ATMS — need to add PRAF
2. RenderPolicy is frozen dataclass — need to add praf_* fields with defaults
3. ResolvedResult needs acceptance_probs: dict[str, float] | None = None
4. resolution.py resolve() has elif chain for backends — add PRAF branch
5. WorldlinePolicy in worldline.py has from_dict/to_dict — need praf fields
6. worldline_runner.py builds RenderPolicy from WorldlinePolicy — need to pass praf fields
7. CLI: world_resolve has --strategy but NO --reasoning-backend flag (uses backend directly in world_extensions)
8. CLI: world_extensions has --backend choice — need to add "praf"
9. Per plan: NO acceptance threshold — return full probability map, winner by highest acceptance prob
10. Per plan: dfquad strategy should raise NotImplementedError("DF-QuAD implemented in Phase 5B-3")

## FILES TO MODIFY
- propstore/world/types.py — ReasoningBackend.PRAF, RenderPolicy praf fields, ResolvedResult.acceptance_probs
- propstore/world/resolution.py — _resolve_praf(), PRAF elif in resolve()
- propstore/worldline.py — WorldlinePolicy praf fields, from_dict/to_dict
- propstore/worldline_runner.py — pass praf fields to RenderPolicy
- propstore/cli/compiler_cmds.py — CLI flags for praf

## IMPLEMENTATION PROGRESS
- [x] Tests written (10 tests, all fail as expected — TDD red phase confirmed)
- [x] types.py: ReasoningBackend.PRAF added
- [x] types.py: RenderPolicy praf_* fields added (with defaults)
- [x] types.py: ResolvedResult.acceptance_probs field added
- [x] resolution.py: _resolve_praf() function added (builds PrAF, computes acceptance, picks winner)
- [x] resolution.py: PRAF elif branch added in resolve() dispatch
- [ ] resolution.py: Need to wire _acceptance_probs into ResolvedResult returns (current blocker)
- [ ] worldline.py: praf fields in WorldlinePolicy + from_dict/to_dict
- [ ] worldline_runner.py: pass praf fields to RenderPolicy
- [ ] compiler_cmds.py: CLI flags

## CURRENT STATE
- resolution.py: DONE — _acceptance_probs initialized, wired into both return paths
- worldline.py: DONE — praf fields added, from_dict/to_dict updated
- worldline_runner.py: DONE — passes praf fields to RenderPolicy
- compiler_cmds.py: world_resolve DONE (--reasoning-backend, --praf-strategy, --praf-epsilon, --praf-confidence, --praf-seed flags added, policy-based resolve call)
- compiler_cmds.py: world_extensions — need to add PRAF elif branch (display acceptance probs instead of extensions)

## NEXT
1. Add PRAF branch to world_extensions command
2. Run integration tests
3. Run full suite
4. Precommit + commit
