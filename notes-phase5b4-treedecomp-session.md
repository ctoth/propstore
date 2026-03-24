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

## NEXT
1. Commit test file + notes
2. Implement propstore/praf_treedecomp.py (estimate_treewidth, compute_tree_decomposition, to_nice_tree_decomposition, compute_exact_dp)
3. Wire "exact_dp" strategy into praf.py compute_praf_acceptance()
4. Run tests, fix until all pass
5. Run full suite (must be >= 1210 + 15 new = 1225)
6. Precommit + commit
7. Write report
