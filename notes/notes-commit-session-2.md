# Commit Session 2 — 2026-03-24

## GOAL
Commit all modified files in logical chunks.

## OBSERVATIONS
- Previous commit session (notes-commit-session.md) already committed 15 chunks
- Current modified files are NEW changes on top of those commits
- `recover_worldline.py` is a one-off utility script (extracts from agent transcript) — skip or separate commit
- `bash.exe.stackdump` — do NOT commit

## LOGICAL CHUNKS IDENTIFIED

### Chunk 1: ATMS labelled kernel (new module + tests)
- `propstore/world/labelled.py` (NEW, 202 lines) — ATMS-style label kernel
- `tests/test_labelled_core.py` (NEW, 338 lines) — tests for labelled kernel

### Chunk 2: Integrate labelled kernel into world layer
- `propstore/world/bound.py` — imports labelled, attaches labels to ValueResult/DerivedResult/ResolvedResult
- `propstore/world/model.py` — compile_environment_assumptions call, pass assumptions to Environment
- `propstore/world/types.py` — add Label field to ValueResult/DerivedResult/ResolvedResult, assumptions to Environment

### Chunk 3: Value resolver — replace eval with ast_compare
- `propstore/world/value_resolver.py` — replace _evaluate_algorithm_claim_value with _algorithm_matches_direct_value using ast_compare, remove _is_safe_algorithm_expression

### Chunk 4: Docstring corrections
- `propstore/world/resolution.py` — fix docstring (3 lines)
- `propstore/world/types.py` — fix ReasoningBackend docstring (already in chunk 2, combine)
- `propstore/worldline.py` — fix WorldlinePolicy docstring + add reasoning_backend validation
- `propstore/worldline_runner.py` — fix module docstring, remove _compute_hash
- `propstore/validate.py` — fix module docstring

### Chunk 5: Tests for new behavior
- `tests/test_semantic_repairs.py` — test mixed direct+multistatement algorithm ast equivalence
- `tests/test_worldline.py` — test unknown reasoning_backend rejection

### Chunk 6: README update
- `README.md` — semantic axes section update for Run 2A labelled core

### Chunk 7: Session notes
- `notes-commit-session.md` — updated with done status

## DECISION POINT
Chunks 2 and 4 overlap on types.py and worldline.py. Need to split carefully.

OPTION A: Merge chunks 2+4 since they touch the same files
OPTION B: Commit types.py label fields with chunk 2, docstring-only files separately
CHOOSING: A — the types.py changes are all one logical unit (label support + docstring fixes both serve the labelled core). Worldline changes (validation + docstring) also serve the same goal.

## REVISED PLAN (5 commits)
1. labelled.py + test_labelled_core.py — new ATMS label kernel
2. bound.py + model.py + types.py + worldline.py + worldline_runner.py + resolution.py + validate.py — integrate labelled kernel + fix docstrings
3. value_resolver.py — replace eval with ast_compare
4. test_semantic_repairs.py + test_worldline.py — tests for chunks 2+3
5. README.md — docs update
6. notes-commit-session.md — session notes

## NEXT
Execute commits in order.
