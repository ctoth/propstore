# Phase 5B-4 Redo: Tree Decomposition DP

## GOAL
Replace the brute-force inner DP in praf_treedecomp.py with the real I/O/U table DP with witness mechanism from Popescu & Wallner (2024).

## DONE
1. Read Popescu 2024 notes (full paper extraction at papers/Popescu_2024_.../notes.md)
2. Read existing praf_treedecomp.py — confirmed current `compute_exact_dp` is just brute-force enumeration
3. Read praf.py — interface for `_compute_exact_dp` calls `praf_treedecomp.compute_exact_dp`
4. Read dung.py — grounded_extension, complete_extensions, preferred_extensions, stable_extensions
5. Read tests/test_treedecomp.py — existing cross-validation tests
6. Added 4 new witness mechanism tests to test_treedecomp.py:
   - test_witness_mechanism_required (A→B, P_D=0.5)
   - test_witness_mechanism_multiple_attackers (A→C, B→C)
   - test_dp_table_row_count
   - test_dp_vs_brute_force_all_topologies (chain4, cycle4, diamond, star5 x 4 P_D values)

## KEY OBSERVATIONS
- Current compute_exact_dp is literally brute-force: enumerates 2^(|A|+|D|) worlds, evaluates semantics on each
- The TD infrastructure (TreeDecomposition, NiceTDNode, NiceTreeDecomposition, compute_tree_decomposition, to_nice_tree_decomposition) is correct and should be KEPT
- The nice TD introduces arguments one at a time (introduce nodes), removes them one at a time (forget nodes)
- The nice TD has 4 node types matching Popescu: leaf (empty bag), introduce, forget, join
- Current tests should all still pass since brute-force gives correct results

## ALGORITHM DESIGN (from Popescu 2024 notes)
Each DP table row: (labelling: dict[arg, Label], witnessed: dict[arg, bool], probability: float)
- Label = I (in), O (out), U (undecided)
- witnessed[a] = True if arg a labelled O has a confirmed I-labelled attacker with realized attack

Node handlers:
- **Leaf**: single row, empty labelling, prob=1.0
- **Introduce(v)**: for each row, try v=I, v=O, v=U, v=absent:
  - v=I: no I-labelled attacker in bag; multiply by P_A(v)
  - v=O: must have I-labelled attacker with attack edge; multiply by P_A(v) * attack probs; set witness
  - v=U: multiply by P_A(v)
  - v absent: multiply by (1-P_A(v))
- **Forget(v)**: remove v from labelling, merge rows with same remaining labelling by summing probs
  - If v=O and not witnessed → discard row (prob 0)
  - For stable: v=U → discard
- **Join**: for compatible rows (same labelling), multiply probs; combine witnesses (OR)

## FILES
- propstore/praf_treedecomp.py — REPLACE inner DP, KEEP TD infrastructure
- propstore/praf.py — interface, no changes needed
- tests/test_treedecomp.py — added 4 new tests

## NEXT
1. Run new tests to verify they pass with current brute-force implementation
2. Implement real I/O/U table DP
3. Run tests, cross-validate at 1e-9
4. Full test suite >= 1233 passing
5. Commit
6. Write report
