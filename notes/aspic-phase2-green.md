# ASPIC+ Phase 2 Green: Transposition Closure

**Date:** 2026-03-25
**Status:** COMPLETE

## GOAL
Implement `transposition_closure()` in `propstore/aspic.py` to make 10 failing tests pass.

## Reading Done
- `prompts/aspic-phase2-green.md` — full prompt with algorithm spec
- `papers/Modgil_2018_*/notes.md` — Def 12 (p.13): transposition closure definition
- `papers/Prakken_2010_*/notes.md` — Defs 5.1-5.2: transposition and closure
- `reports/aspic-phase2-red.md` — 10 new tests, all fail with ImportError
- `tests/test_aspic.py` — 17 tests total (7 Phase 1 + 10 Phase 2)
- `propstore/aspic.py` — has Literal, ContrarinessFn, Rule; no transposition_closure yet

## Key Observations
- `transposition_closure` signature: `(rules: frozenset[Rule], language: frozenset[Literal], contrariness: ContrarinessFn) -> frozenset[Rule]`
- Algorithm: for each strict rule A1,...,An -> C, for each i, create A1,...,~C,...,An -> ~Ai
- Filter: all literals must be in L
- Iterate to fixpoint
- Only strict rules get transposed; defeasible rules pass through untouched
- The test `test_transposition_closure_complete` checks that transposed rules use `r.consequent.contrary` (not cfn) for ~C and `ante_i.contrary` for ~Ai
- The concrete test: married -> ~bachelor produces bachelor -> ~married

## NEXT
- Implement `transposition_closure()` in aspic.py
- Run tests
- Commit
- Write report
