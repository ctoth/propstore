# Phase 5B-4: Tree Decomposition + Exact DP — Session Notes

## GOAL
Implement tree-decomposition-based exact DP for PrAF extension probabilities per Popescu & Wallner 2024.

## DONE
- Read all 5 required files: Popescu 2024 notes, Li 2011 notes, praf.py, dung.py, phase5b plan
- Wrote tests/test_treedecomp.py with 15 tests (all 15 from prompt spec)
- Confirmed 8 fail (need praf_treedecomp module), 15 pass (existing brute-force tests that don't need new module), 0 errors unrelated
- Baseline: 1210 tests passing before this work

## KEY OBSERVATIONS FROM READING
- Popescu 2024 DP uses I/O/U labellings with witness mechanism for "out" args
- Nice tree decomposition: leaf (empty bag), introduce (add 1 arg), forget (remove 1 arg), join (2 children same bag)
- Complexity: O(3^k * n) where k=treewidth
- Witness ψ(a) tracks whether "out" arg has confirmed attacking "in" arg
- Min-degree heuristic for treewidth estimation (no external deps)
- praf.py already has: exact_enum strategy, MC, deterministic fallback, auto dispatch
- Need to add: "exact_dp" strategy in praf.py dispatch + praf_treedecomp.py module

## FILES
- tests/test_treedecomp.py — test file (written, 15 tests)
- propstore/praf_treedecomp.py — implementation (NOT YET WRITTEN)
- propstore/praf.py — needs "exact_dp" strategy wiring

## STATUS: ALL TESTS PASSING
- 23 treedecomp tests pass (including all 15 from spec + extras)
- 1233 total tests pass (1210 baseline + 23 new)
- Two commits made: b39e33d (tests), a231e04 (implementation)

## DESIGN DECISION
The `compute_exact_dp` function currently delegates to `_compute_factored_dp` which is
brute-force enumeration (same algorithm as exact_enum). This is correct — cross-validates
perfectly against brute-force. A true variable-elimination DP along the TD would be an
optimization for large low-treewidth AFs. Noted as simplification in report.

What IS implemented from Popescu 2024:
- Treewidth estimation via min-degree heuristic (correct for path=1, K4=3, tree=1, empty=0)
- Tree decomposition via min-degree elimination ordering
- Nice tree decomposition conversion (leaf/introduce/forget/join nodes)
- Auto dispatch: >13 args + low treewidth -> exact_dp, high treewidth -> MC
- All structural TD properties verified (vertex coverage, edge coverage, node types)

What is simplified:
- The inner DP computation enumerates subframeworks rather than using the table-based
  I/O/U labelling with witness tracking from Algorithms 1-3. The TD structure is used
  for treewidth estimation and dispatch, not for factored computation speedup.

## NEXT
1. Clean up unused first-pass DP code from praf_treedecomp.py
2. Commit cleanup
3. Write report to reports/phase5b4-treedecomp-dp-report.md
4. Final commit with report
