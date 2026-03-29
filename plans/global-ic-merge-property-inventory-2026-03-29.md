# Global IC-Merge Property Inventory

Date: 2026-03-29

Goal: turn the Konieczny 2002 literature into an explicit test inventory for the
global IC-merge follow-on plan.

Primary source:
- `papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`

Paper pages reread directly from PNGs for this inventory:
- postulates: `page-004.png`, `page-005.png`
- representation conditions: `page-006.png`, `page-007.png`, `page-009.png`, `page-010.png`
- operator families: `page-012.png`, `page-013.png`, `page-015.png`, `page-017.png`, `page-018.png`

## Verdict

We have enough literature-grounded properties to drive TDD for the global merge
solver.

The important split is:

- properties we can assert directly on the finite assignment-level adaptation
- properties that only become honest once production callers really construct one
  global merge problem instead of solving concepts independently
- properties that remain paper-level only unless we model full propositional
  belief bases and logical equivalence, not just concrete assignments

## Direct Solver Properties

These are the properties we should encode as tests for the assignment-level
solver itself.

### Core admissibility and minimality

1. `mu` is a hard filter, not a tie-breaker.
   Literature: IC0, Theorem 3.7, operator definitions on pp. 4, 7, 12, 15, 17.
   Test shape:
   - every winning assignment satisfies every integrity constraint
   - if no assignment satisfies `mu`, the winner set is empty

2. If admissible candidates exist, winners are exactly the admissible minima
   under the operator preorder.
   Literature: `mod(Delta_mu(Psi)) = min(mod(mu), <=_Psi)`.
   Test shape:
   - every non-winner admissible assignment has score not better than the winner
   - every winner has score equal to the best admissible score

3. Winner closure over the candidate domain.
   Literature: the merge result is chosen from admissible interpretations/models.
   Test shape:
   - every winner belongs to the enumerated candidate assignment set

### Constraint postulate adaptations

4. Constraint consistency adaptation.
   Literature: IC1.
   Honest assignment-level version:
   - if the candidate domain contains at least one `mu`-admissible assignment,
     the result is non-empty

5. Consensus exactness adaptation.
   Literature: IC2.
   Honest assignment-level version:
   - if every source contributes the same complete assignment and that assignment
     satisfies `mu`, it is the unique winner
   - more generally, if the conjunction of all source assignments determines one
     admissible merged assignment, that assignment is the unique winner

6. Constraint strengthening monotonicity.
   Literature: IC7 and IC8.
   Test shape:
   - adding an extra constraint can only keep or shrink the winner set
   - if all winners under `mu1` also satisfy `mu2`, then the winners under
     `mu1 ∧ mu2` are a subset of the winners under `mu1`

### Invariance properties

7. Source-order permutation invariance.
   Literature anchor: multiset semantics and syntax independence direction of IC3.
   Honest assignment-level version:
   - permuting source order does not change scored candidates or winners

8. Source renaming invariance.
   Literature anchor: names are not semantic content.
   Test shape:
   - renaming `source_id`s does not change winner assignments

9. Candidate-order invariance.
   Literature anchor: total preorder over interpretations, not enumeration order.
   Test shape:
   - enumeration order changes do not affect winners

### Operator-family properties

10. Sigma majority sensitivity.
    Literature: Theorem 4.2 and `(Maj)` on pp. 5 and 13.
    Test shape:
    - sufficiently duplicating one subgroup can force Sigma to select that
      subgroup's preferred admissible assignment

11. Max arbitration-style duplicate insensitivity.
    Literature: Theorem 4.6 on p.15.
    Test shape:
    - duplicating an identical source assignment does not change Max winners

12. GMax arbitration-style duplicate insensitivity.
    Literature: Theorem 4.14 and fair-assignment conditions.
    Test shape:
    - duplicating an identical source assignment does not change GMax winners

13. GMax refines Max.
    Literature: Remark 4.10 on p.17.
    Test shape:
    - every GMax winner is also a Max winner on the same admissible domain

14. Sigma is multiplicity-sensitive; Max and GMax are not.
    Literature: multisets matter for majority operators; Max/GMax are tied to
    arbitration behavior.
    Test shape:
    - a duplicate can change Sigma winners
    - the same duplicate does not change Max/GMax winners

## Global-Only Properties

These become meaningful only once production callers solve one joint merge
problem across multiple concepts.

15. Cross-concept `mu` can reject locally admissible but jointly impossible
    choices.
    Literature anchor: `mu` constrains whole interpretations.
    Test shape:
    - independent per-concept winners exist, but the global winner set changes
      once a cross-concept constraint is enforced

16. Factorization sanity when `mu` does not couple subproblems and the source
    multiset itself factorizes.
    Literature anchor: the preorder is over whole interpretations, but uncoupled
    domains should not introduce fake interactions.
    Test shape:
    - if concepts are independent, the source multiset is the Cartesian product
      of per-concept source choices, and `mu` is separable, the global winners
      are the product of the per-concept winners

17. Branch-filter and branch-weight effects only act through the formal source
    multiset.
    Literature anchor: belief multiset semantics.
    Test shape:
    - changing branch selection changes winners only because the source multiset
      changed, not through ad hoc downstream filtering

## Paper-Level Properties We Should Treat Carefully

These belong in the inventory, but they should not be claimed as fully proved by
our assignment adaptation without additional formal machinery.

18. Full IC3 syntax independence.
    Why careful:
    - the paper quantifies over logically equivalent belief bases
    - our current solver works over concrete source assignments, not arbitrary
      propositional formulas

19. IC4 fairness in entailment form.
    Why careful:
    - the paper states this using base formulas and entailment
    - we can approximate fairness on bounded assignment instances, but not claim
      the full logical postulate without richer source semantics

20. IC5 and IC6 group-composition postulates in full generality.
    Why careful:
    - these are meaningful at the level of whole merged formulas / model sets
    - we can test finite winner-set analogues, but should label them as
      assignment-level adaptations unless we prove the equivalence carefully

21. Singleton reduction to KM revision.
    Why careful:
    - the paper's theorem is about revision operators on belief bases
    - our assignment solver can test the degenerate one-source behavior, but that
      is not yet a full KM representation theorem

## Property-Based Testing Set

These are the Hypothesis properties worth keeping as the core battery.

### Phase 1

- source-order permutation invariance
- source renaming invariance
- winner closure over candidate domain
- best-score minimality

### Phase 2

- every winner satisfies `mu`
- unconstrained one-concept problems match scalar kernels
- cross-concept constraints can strictly shrink winners
- separable `mu` preserves factorization

### Phase 3

- always-true CEL constraints do not change winners
- unsatisfiable CEL constraints yield no winners
- logically equivalent simple CEL constraints produce the same winners on bounded
  cases

### Phase 4

- Z3-pruned and brute-force winner sets agree on bounded inputs
- Z3 failure falls back without semantic drift

## Immediate Takeaway For Phase 1

Phase 1 does not need the full postulate battery yet. The minimum literature-led
property set for Phase 1 is:

1. multi-concept assignments are first-class objects
2. source order and source names do not affect winners
3. winners are drawn from the candidate assignment domain
4. winner scoring is a preorder over assignments, not a scalar-only shortcut

That is enough to start formalizing the global problem type without overclaiming
postulates that only become honest in later phases.
