# Phase 5B-4: Tree-Decomposition DP for Grounded Semantics

## Summary

Replaced the brute-force internals of `compute_exact_dp()` in `propstore/praf_treedecomp.py` with a real tree-decomposition DP for **grounded semantics only**. Non-grounded semantics fall back to brute-force enumeration.

## How the DP Works

The DP processes a nice tree decomposition bottom-up, tracking subworld configurations (which arguments are present, which defeat edges are realized) factored along the TD structure. At the root, the grounded extension is computed via Dung's fixpoint for each surviving configuration.

### Key design: edge-configuration tracking (not I/O/U labels)

Previous attempts used Popescu & Wallner's I/O/U labelling approach, which enumerates all valid complete labellings. This overcounts for grounded semantics because mutual attacks and even cycles produce multiple complete labellings per subworld, but only one is grounded.

The implemented approach tracks **edge configurations** instead:

- **Row key**: `(bag_state, active_edges, present_forgotten)` where:
  - `bag_state`: which bag arguments are present/absent in this subworld
  - `active_edges`: frozenset of realized defeat edges (accumulated over subtree)
  - `present_forgotten`: frozenset of forgotten arguments that were present

- **Leaf**: single row, empty state, probability 1.0 (Popescu & Wallner 2024, p.6)

- **Introduce v**: branch on v present/absent. For v present, branch on each owned edge's presence/absence (multiply by P_D). P_A is deferred to forget time. (Popescu & Wallner 2024, Algorithm 2, p.6-7)

- **Forget v**: apply P_A(v) — multiply by P_A if present, (1-P_A) if absent. Move v from bag to `present_forgotten`. Each argument is forgotten exactly once. (Popescu & Wallner 2024, Algorithm 3, p.7)

- **Join**: combine rows with matching bag states. Multiply probabilities, union edge sets and forgotten sets. (Popescu & Wallner 2024, p.6)

- **Root**: for each surviving row, run the grounded fixpoint (Dung 1995, Definition 20 + Theorem 25) on `present_forgotten` with `active_edges`. Accumulate acceptance probabilities.

### Edge ownership (preventing double-counting at joins)

In nice TDs with join nodes, the same argument or edge can appear in multiple subtrees. Each edge's P_D factor is assigned to exactly one introduce node (first in post-order to see both endpoints). This prevents double-counting when subtrees merge. P_A is applied at forget time (each argument forgotten exactly once), avoiding the same issue for argument probabilities.

### Connected component decomposition

Per Hunter & Thimm (2017, Prop 18): acceptance probability separates over connected components. The AF is decomposed into components before TD construction, handling disconnected graphs correctly.

### Scope limitation

Per Popescu & Wallner (2024, Theorem 6): P_acc for preferred/stable/complete is #.NP-complete. The DP is scoped to grounded semantics only. Non-grounded semantics fall back to brute-force enumeration. See `reports/research-popescu-pacc-report.md` for analysis.

## Cross-Validation Results

All tests cross-validate DP against brute-force enumeration at 1e-6 tolerance (MANDATORY per prompt).

Topologies tested at multiple P_D values (0.3, 0.5, 0.7, 0.9):
- Chain (4 args): PASS
- Cycle (4 args): PASS
- Diamond (4 args): PASS
- Star (5 args): PASS
- Mutual attacks with uncertain args: PASS
- Self-attacks: PASS

## Test Results

- `tests/test_treedecomp.py`: **27/27 passed** (24.74s)
- `tests/test_toy_dp.py`: **14/14 passed** (64.66s)
- Full suite: **1250/1251 passed** (176.92s)
  - 1 pre-existing failure in `test_form_dimensions.py` (JSON schema validation for dimension keys with newlines — unrelated)

## Files Changed

- `propstore/praf_treedecomp.py` — replaced `compute_exact_dp()` internals and `_compute_factored_dp()` with edge-tracking TD DP
