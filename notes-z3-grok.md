# Z3/Constraint Grok Session — 2026-03-22

## Phase 1: Scout Report Summary

Full report: `reports/scout-z3-usage-report.md`

### Current state
- **One core module**: `propstore/z3_conditions.py` — translates CEL AST → z3 expressions
- **Two queries**: `are_disjoint()` and `are_equivalent()` — both satisfiability checks
- **Three consumers**:
  - `conflict_detector.py` — classifies claim pairs as CONFLICT/PHI_NODE/OVERLAP
  - `world/model.py` — lazy solver setup from SQLite registry
  - `world/bound.py` — filters active claims when conditions are bound
- **Types**: z3.Real (quantities), z3.Bool (booleans), z3.EnumSort (categories)
- **Graceful degradation**: Falls back to interval arithmetic if z3 unavailable
- **No CLI exposure**: z3 is invisible to users
- **Test coverage**: 29 tests across 8 classes, gaps in ternary, numeric `in`, error paths

### Identified unused potential
1. Unit dimension consistency checking
2. Parameterization equation/range validation
3. Context hierarchy reasoning
4. Claim value/condition consistency
5. Transitive conflict detection (currently sympy)
6. Equivalence class clustering

## Phase 2: Research — DONE
Full report: `reports/research-smt-constraint-argumentation.md`

Key findings:
- SAT-based extension computation is mature (ICCMA competition, 5 editions)
- MaxSMT (z3 Optimize + soft constraints) is highest-impact/lowest-effort extension for propstore
- SAT encoding of Dung semantics is well-documented: one Boolean var per argument, standard constraint patterns
- IDP-Z3 and InfOCF are existing z3-based knowledge reasoning systems worth studying
- EZSMT combines ASP + z3 for hybrid reasoning

## Phase 3: Paper Processing — IN PROGRESS

### Paper 1: Mahmood_2025_Structure-AwareEncodingsArgumentationProperties — DONE
- Retrieved from arxiv, 33 pages, all read
- Provides complete SAT/QSAT encodings for ALL Dung semantics
- Tight complexity bounds: 2^O(k)·poly(s) for stable/admissible/complete, 2^O(k²)·poly(s) for preferred/semi-stable/stage
- 15 claims extracted, 6 new concepts registered
- Reconciled with Dung_1995 (bidirectional)
- Key practical takeaway: the SIMPLE flat encoding (one var per argument, not the DDG approach) is directly implementable in z3

### Papers 2-8: Batch dispatch — 7 subagents launched in parallel
All running in background, processing via paper-process skill.

**Agents dispatched (all background):**
1. paper-charwat2015 — Charwat et al. 2015, Methods survey (DOI: 10.1016/j.artint.2014.11.008)
2. paper-bjorner2014 — Bjørner & Phan 2014, νZ MaxSMT (MS Research PDF)
3. paper-niskanen2020 — Niskanen & Järvisalo 2020, µ-toksia solver
4. paper-dvorak2012 — Dvořák et al. 2012, FPT algorithms (DOI: 10.1016/j.artint.2012.07.002)
5. paper-encoding-afs — arxiv 2503.07351, Encoding AFs to propositional logic
6. paper-fichte2021 — Fichte et al. 2021, DDG reductions (IJCAI)
7. paper-iccma2023 — Järvisalo et al. 2025, ICCMA 2023 competition

**Status as of notes update (2nd):**

Completed agents:
- paper-niskanen2020 (µ-toksia) — DONE. 16 claims, 3 concepts, high usefulness. Practical SAT encodings.
- paper-encoding-afs (Tang 2025) — DONE. 19 claims, 8 concepts, high usefulness. 3-valued/fuzzy logic encodings.
- paper-bjorner2014 (νZ MaxSMT) — DONE (index updated). Optimization module for z3.

ALL 7 AGENTS COMPLETE:

| # | Paper | Claims | Concepts | Usefulness |
|---|-------|--------|----------|------------|
| 1 | Niskanen 2020 (µ-toksia) | 16 | 3 | High — practical SAT encodings, ICCMA winner |
| 2 | Tang 2025 (Encoding AFs) | 19 | 8 | High — 3-valued/fuzzy logic encodings |
| 3 | Bjørner 2014 (νZ MaxSMT) | 14 | 9 | Low-Med — z3 optimization infrastructure |
| 4 | Järvisalo 2025 (ICCMA 2023) | 18 | 4 | High — competition benchmarks, SAT dominance |
| 5 | Charwat 2015 (Methods Survey) | 23 | 5 | High — definitive survey, 5 papers cite it |
| 6 | Fichte 2021 (DG Reductions) | 16 | 6 | High — treewidth encodings, predecessor to Mahmood |
| 7 | Dvořák 2012 (FPT Algorithms) | 16 | 5 | High — DP algorithms for all semantics |

**Totals across batch: 122 claims, 40 new concepts registered**
Plus the Mahmood 2025 paper I processed directly: 15 claims, 6 concepts.
**Grand total: 137 new claims, 46 new concepts from 8 papers.**

**What worked:**
- Template prompt pattern: one `prompts/paper-process-batch.md`, 7 agents referencing it
- Updated subagent.md protocol with batch dispatch rule per Q's feedback
- Saved feedback memory about template pattern

**What's next:**
- Wait for all 7 agents to complete
- Read their reports from `reports/paper-process-batch-*-report.md`
- Update notes with results
- Proceed to Phase 4: Plan mode — design z3 improvements using hypothesis-driven TDD

## Phase 4: Plan — APPROVED

Plan at: `~/.claude/plans/ancient-strolling-phoenix.md`
4 phases: batch equivalence → z3 SAT extensions → credulous/skeptical → MaxSMT

## Implementation — Phase 1: Batch Equivalence Classes

### Current blocker: circular import
`condition_classifier.py` ↔ `conflict_detector.py` circular import.
- `condition_classifier.py:16` imports `ConflictClass` from `conflict_detector`
- `conflict_detector.py:89` imports `classify_conditions` from `condition_classifier`
- This breaks `test_z3_conditions.py` (cannot collect)

**Approach:** Lazy import of ConflictClass in condition_classifier.py via `_ensure_conflict_class()` + global variable. Pyright complains about `None` type but runtime works. Need to call `_ensure_conflict_class()` at the top of each function that uses `ConflictClass`.

### Baseline
- test_conflict_detector.py: 36 passed
- test_dung.py: 42 passed
- test_z3_conditions.py: IMPORT ERROR (the circular import)

## Implementation — ALL PHASES COMPLETE

### Phase 1: Batch Equivalence Classes — DONE (commit 43a396c)
- Added `partition_equivalence_classes()` to `z3_conditions.py`
- Wired into `conflict_detector.py` for O(n*k) instead of O(n²)
- 7 new tests, all passing
- Fixed circular import between condition_classifier.py ↔ conflict_detector.py

### Phase 2: z3 SAT-Backed Extension Computation — DONE (commit 29ec8e0)
- Created `propstore/dung_z3.py` with SAT encodings for stable/complete/preferred
- Added `backend="z3"` parameter to `dung.py` functions
- 21 new tests including Hypothesis property tests (100 random AFs per semantics)
- Hard instances: symmetric chain of 10, odd cycle of 7

### Phase 3: Credulous/Skeptical Acceptance — DONE (included in Phase 2)
- `credulously_accepted()` and `skeptically_accepted()` in `dung_z3.py`
- 6 acceptance tests (credulous/skeptical under stable and complete)

### Phase 4: MaxSMT Conflict Resolution — DONE (commit 9fbbd6d)
- Created `propstore/maxsat_resolver.py` using `z3.Optimize()` with soft constraints
- `resolve_conflicts()` finds maximally consistent claim subset weighted by `claim_strength`
- Added `compute_consistent_beliefs()` to `argumentation.py`
- 11 new tests, tiebreak test at 0.0001 difference passes

### Final verification: 161 tests passed across all z3-related suites
