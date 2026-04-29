# WS-O-gun Closure Report

Workstream: WS-O-gun gunray fixes and anytime wire-up
Closing gunray tag: `v0.1.0`
Closing gunray commit: `27b0a13`
Propstore metadata closure commit: this report/index update commit

## Findings Closed

- HIGH-1: argument building now uses shared grounding and has explicit budget plumbing through `max_arguments`.
- HIGH-2: disagreement/concordance now uses explicit theory conflicts instead of re-deriving complement checks through repeated grounding.
- HIGH-3: `evaluate_with_trace` carries `grounding_inspection`, so consumers do not need a second `inspect_grounding` pass.
- MED-2: marking memoization now uses a shared table for dialectical subtrees.
- MED-3: private cross-module grounding import pressure is resolved through the shared internal grounder and public `grounding_types` value objects.
- MED-5: strict-only traces now expose arguments, trees, markings, and grounding inspection instead of returning an opaque empty dialectical view.
- MED-6: superiority self-pairs and cycles are rejected at the boundary.
- MED-7: `Policy` was split into `MarkingPolicy` and `ClosurePolicy`, removing the mixed public enum.
- LOW-1: Diller 2025 is now load-bearing in `CITATIONS.md` and cited from the grounding implementation.
- LOW-2 / D-18: `EnumerationExceeded` is now reachable through argument enumeration budgets and carries partial arguments/trace for callers.
- LOW-4: zero-arity atoms are accepted and round-trip through the updated boundary contract.
- LOW-6: `build_arguments(theory, max_arguments=...)` exposes budgeted argument enumeration directly.
- LOW-7: `DefeasibleTrace` is now the canonical inspection surface for arguments and grounding evidence.
- ARCH/BND items: `ARCHITECTURE.md` documents the split policy surface, single-grounder trace contract, superiority validation, strict-only trace shape, and budget-exhaustion behavior.

MED-4 was not in this workstream; it remains in `WS-O-gun-garcia.md` per D-17.

## Red Tests Written First

- `tests/test_inspect_grounding_via_trace.py`: failed because trace evaluation did not expose the grounding inspection and consumers had to ground twice.
- `tests/test_workstream_o_gun_contract.py`: failed because the public boundary still had the mixed `Policy` enum, no real budget exception path, and no strict-only trace payload.
- `tests/test_citations_diller_load_bearing.py`: failed because Diller 2025 was not load-bearing and the implementation did not cite the paper pages.
- `tests/test_anytime_budget_exhausted.py`: added as the named D-18 gate for budget exhaustion and partial-result behavior.

## Test Evidence

Gunray acceptance used the direct commands specified by this sibling-repo workstream; no propstore logged pytest wrapper was involved.

- `cd ../gunray && uv run pyright src`: 0 errors, 0 warnings, 0 informations.
- `cd ../gunray && uv run ruff check src tests examples`: all checks passed.
- `cd ../gunray && uv run ruff check`: all checks passed.
- `cd ../gunray && uv run ruff format --check`: 83 files already formatted after follow-up format commit `27b0a13`.
- `cd ../gunray && uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `cd ../gunray && uv run pytest -m property tests/`: 56 passed, 469 deselected.
- `cd ../gunray && uv run pytest tests/`: 230 passed, 293 skipped, 2 deselected.
- `cd ../gunray && uv run pytest`: 230 passed, 293 skipped, 2 deselected.
- `cd ../gunray && uv run pytest tests/test_dialectic_perf.py`: 5 passed.
- `cd ../gunray && uv run pytest tests/test_anytime_budget_exhausted.py`: 3 passed.

## Property-Based Tests

- The property selector now works through a gunray `property` pytest marker.
- Existing Hypothesis tests are collected under `-m property` by `tests/conftest.py`.
- `tests/test_anytime_budget_exhausted.py` adds a Hypothesis monotonicity check for `max_arguments` budget behavior.
- The WS-O-gun property gates from `PROPERTY-BASED-TDD.md` are represented in the named property run above.

## Files Changed

Gunray production:

- `src/gunray/__init__.py`
- `src/gunray/adapter.py`
- `src/gunray/closure.py`
- `src/gunray/conformance_adapter.py`
- `src/gunray/defeasible.py`
- `src/gunray/grounding.py`
- `src/gunray/grounding_types.py`
- `src/gunray/schema.py`

Gunray tests/docs/config:

- `tests/conftest.py`
- `tests/test_anytime_budget_exhausted.py`
- `tests/test_citations_diller_load_bearing.py`
- `tests/test_dialectic_perf.py`
- `tests/test_inspect_grounding_via_trace.py`
- `tests/test_workstream_o_gun_contract.py`
- existing affected test/example call sites updated for `MarkingPolicy` and `ClosurePolicy`
- `ARCHITECTURE.md`
- `CITATIONS.md`
- `pyproject.toml`

Propstore metadata:

- `reviews/2026-04-26-claude/workstreams/WS-O-gun-gunray.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`
- `reviews/2026-04-26-claude/workstreams/reports/WS-O-gun-closure.md`

## Remaining Risks and Successor Work

- Propstore still intentionally points at its prior gunray dependency until WS-M updates the pin and consumer boundary.
- WS-M owns `propstore/grounding/grounder.py`, `propstore/grounding/explanations.py`, `tests/test_grounder_budget_exceeded.py`, and the `ResultStatus.BUDGET_EXCEEDED` surfacing.
- WS-O-gun-garcia owns the Garcia 2004 generalized-specificity rewrite and the section-projection/not-defeasibly semantics.
- Trace serialization, per-fact provenance accessors, and any `DefeasibleModel.sections` redesign remain out of WS-O-gun scope unless pulled into WS-M or a later explicit workstream.
