# Commit Session Notes

## GOAL
Commit all modified and untracked files in logical thematic chunks.

## DONE
1. ✅ Commit 1: `propstore/world/types.py`, `propstore/world/__init__.py` — ReasoningBackend enum + RenderPolicy
2. ✅ Commit 2: `propstore/argumentation.py` — claim-graph backend rename

## REMAINING COMMITS
3. `propstore/world/resolution.py` — whole-belief-space argumentation + reasoning_backend
4. `propstore/world/value_resolver.py` — extract derivation, algorithm eval, safe expressions
5. `propstore/build_sidecar.py` — concept canonicalization, content hash fix, connection leak
6. `propstore/worldline.py`, `propstore/worldline_runner.py` — reasoning_backend in policy
7. `tests/test_world_model.py`, `tests/test_render_contracts.py` — modified test files
8. `tests/test_worldline.py` — worldline failure mode tests
9. `tests/test_param_conflicts.py`, `tests/test_semantic_repairs.py` — new test files
10. `README.md` — clarify argumentation semantics
11. `scripts/` — utility scripts
12. `papers/` — paper directories (PDFs/pngs gitignored)
13. `notes-*.md` — session notes
14. `review-v1.md`, `review-v1-response.md`, `propstore-narrative-review.md`, `aspic.md` — review docs
15. `.ward/`, `.claude_*`, `propstore.txt` — misc (skip bash.exe.stackdump)

## DONE (all 15 commits)
1. ✅ types.py, __init__.py — ReasoningBackend enum
2. ✅ argumentation.py — claim-graph rename (still has compat alias)
3. ✅ resolution.py — whole-belief-space argumentation
4. ✅ value_resolver.py — extract derivation, algo eval
5. ✅ build_sidecar.py — canonicalization, hash fix, conn leak
6. ✅ worldline.py, worldline_runner.py — reasoning_backend
7. ✅ test_render_contracts.py, test_world_model.py — modified tests
8. ✅ test_worldline.py — failure mode tests
9. ✅ test_param_conflicts.py, test_semantic_repairs.py — new tests
10. ✅ README.md — semantic axes docs
11. ✅ scripts/ — utility scripts
12. ✅ papers/ — 6 paper directories
13. ✅ notes-*.md — session notes
14. ✅ review docs, aspic.md, propstore.txt
15. ✅ .ward/, .claude_* artifacts

## NEXT
Q asked to remove the backward-compatible alias in argumentation.py and migrate
all callers to compute_claim_graph_justified_claims. Callers found in:
- propstore/world/resolution.py (import + call)
- propstore/cli/compiler_cmds.py (import + call)
- propstore/worldline_runner.py (import + call)
- tests/test_semantic_repairs.py (import + call)
- tests/test_render_time_filtering.py (import + call)
- tests/test_bipolar_argumentation.py (import + calls)
- tests/test_argumentation_integration.py (import + calls)
- tests/test_worldline.py (mock target)
- notes files (just text references, don't need updating)

bash.exe.stackdump left uncommitted intentionally.
