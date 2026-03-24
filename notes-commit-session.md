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

## OBSERVATIONS
- Commit style: imperative, short first line, explanation body
- .gitignore covers PDFs, pngs, __pycache__, .venv, etc.
- bash.exe.stackdump should NOT be committed
- All diffs read and understood before committing
