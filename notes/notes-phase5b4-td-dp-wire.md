# Phase 5B-4: Wire Verified Labelling into Tree Decomposition DP

## GOAL
Replace compute_exact_dp() internals in praf_treedecomp.py with a real TD DP for grounded semantics.

## DONE
- Read all required files: prompt, toy_dp, praf_treedecomp, praf, test_treedecomp, Popescu notes, research report
- Hand-traced A->B with P_D=0.5 through the nice TD structure
- Verified the TD structure for A->B: leaf({}), introduce A({A}), introduce B({A,B}), forget A({B}), forget B({})

## KEY DESIGN DECISIONS

### Why grounded only
Per Popescu report: P_ext = P_acc for grounded (unique extension per subframework). For preferred/stable/complete, P_acc is #.NP-complete -- fall back to brute force.

### Algorithm design (hand-verified on A->B, P_D=0.5)

**Table row structure:** (partial labelling of bag args -> label in {I, O, U, absent}) + witness set (which O args have confirmed I attackers) + probability

**Leaf:** single row, empty labelling, prob 1.0

**Introduce v:** For each existing row, branch on:
1. v absent: multiply by (1 - P_A(v)). Row unchanged + v absent.
2. v present (multiply by P_A(v)), then for each defeat (a,v) where a is in bag, branch on edge present/absent:
   - v=I: ALL attackers in bag with realized edges must be O. If any I attacker has realized edge -> invalid. If no attackers or all attackers O (with realized edges factored) -> valid.
   - v=O: at least one I attacker with realized edge (WITNESS).
   - v=U: not all attackers O AND no I attacker with realized edge.

CRITICAL DETAIL: When introducing v, we also need to handle defeats FROM v to bag members. If v=I and some bag member b is labelled O, the (v,b) edge factors into b's witness tracking. If v=I and b=I and (v,b) exists and is realized -> CONFLICT, invalid.

**Forget v:** Merge rows that agree on remaining args. When forgetting:
- v=I: verify all attackers-of-v that were in the subtree were O (tracked via witness/running conditions)
- v=O: check witnessed flag. If not witnessed -> discard (prob 0).
- v=U: valid for grounded (arg is undecided in grounded extension)
- v=absent: fine.
- Accumulate P_acc: if v=I, add row prob to acceptance[v].

**Join:** compatible rows (same labelling) -> multiply probabilities, merge witness sets.

### Defeat edge handling
When both endpoints of a defeat are in the bag, we branch on edge present/absent. The P_D factor is applied at introduce time (when the second endpoint enters the bag). This is key: each defeat is factored ONCE, at the introduce node where both endpoints first co-occur.

### Hand trace: A->B, P_D=0.5, all P_A=1.0
- Node 2 (leaf): {() -> 1.0}
- Node 3 (introduce A): {(A:I) -> 1.0} (A has no attackers, must be I in complete labelling)
- Node 4 (introduce B):
  - (A,B) present (0.5): A=I attacks B -> B=O, witnessed. {(A:I, B:O[w]) -> 0.5}
  - (A,B) absent (0.5): no attack -> B=I. {(A:I, B:I) -> 0.5}
- Node 5 (forget A): accumulate P_acc(A) = 0.5 + 0.5 = 1.0. Table: {(B:I)->0.5, (B:O[w])->0.5}
- Node 6 (forget B): accumulate P_acc(B) = 0.5 (from B:I row). Total prob = 1.0.

Result: P(A=in) = 1.0, P(B=in) = 0.5. CORRECT!

## FILES
- `propstore/praf_treedecomp.py` -- main file to edit (compute_exact_dp and new DP functions)
- `propstore/praf.py` -- dispatches to compute_exact_dp, also has _compute_factored_dp to replace
- `tests/test_treedecomp.py` -- existing tests that must pass
- `tests/test_toy_dp.py` -- reference implementation for grounded labelling

## BUG FOUND AND FIX IN PROGRESS

### Root cause of overcounting (attempts 1-2 debugged)

The DP generates ALL locally-consistent labels (I, O, U) for each argument at introduce time. For grounded semantics, each subframework has exactly ONE grounded labelling. But at introduce time, multiple labels may be locally consistent because we haven't seen all attackers yet.

The correct approach: generate all locally-consistent labels, prune invalid ones at forget time. However, **acceptance cannot be accumulated at individual forget nodes** because some rows in the table will later be pruned when OTHER arguments are forgotten.

Example: A->B, P_D=0.5. When forgetting A, rows with B=O (no witness) and B=U (not undefended) still exist. A gets credited from these rows, but they'll be pruned when B is forgotten later. This inflates A's acceptance.

### Fix: deferred acceptance accumulation

Add `accepted: frozenset[str]` to the row key. When forgetting v=I from a valid row, add v to `accepted`. At the ROOT (empty bag), iterate over all surviving rows and accumulate acceptance from their `accepted` sets.

This ensures acceptance is only counted from rows where ALL arguments have been validated.

### Current state

Mid-edit: added `accepted` to row key type and _make_key/_add_to_table. Still need to:
1. Update leaf node to use 4-element key
2. Update introduce handler to pass `accepted` through
3. Update forget handler: don't accumulate acceptance directly, add to `accepted` set instead
4. Update join handler for 4-element keys
5. Update _compute_grounded_dp: accumulate acceptance from root table
6. Test

## BUGS FOUND AND FIXED

### Bug 1: Acceptance accumulated at wrong time
Acceptance was accumulated at individual forget nodes, before all rows were validated.
Fix: deferred accumulation — track `accepted: frozenset[str]` in row key, accumulate at root.

### Bug 2: Witnesses only updated for O-labelled targets
When v=I was introduced, only O-labelled targets got witnessed. But ALL present targets need witnessing (the witness flag means "has I attacker with realized edge" regardless of current label).
Fix: add ALL present targets to witnesses when v=I.

### Bug 3: Self-attacks not handled
Self-attack (v,v) was never branched because introduce looked for attackers/targets in child_bag, but v is not in child_bag.
Fix: detect self-attacks separately and include in edge branching.

### Bug 4: Join double-counting P_A and P_D
In nice TDs with join nodes, the same argument/edge can appear in both subtrees. P_A(v) and P_D(e) were factored in both, causing double-counting.
Fix: Track edge ownership — each edge's P_D is factored at exactly one introduce node. P_A is NOT factored at introduce; instead applied at forget time (each arg forgotten exactly once).

### Current state
All simple tests pass (A->B, A->B->C, cycle, diamond, self-attack, 4-chain, star5).
Now testing the "known example" with uncertain args (P_A < 1.0) and mutual attacks.
P_A moved to forget-time. About to test.

## NEXT
1. Test current state
2. If passes, run full test suite
3. Commit, write report
