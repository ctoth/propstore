# Workstream B — Belief-Set Layer (Real AGM)

Date: 2026-04-16
Status: active 2026-04-17; finite model-theoretic foundation in progress
Depends on: `disciplines.md`, `judgment-rubric.md`, WS-A phase 1 (provenance)
Blocks: —
Review context: `../axis-3c-revision.md` (primary), `../SYNTHESIS.md` pattern D

## Progress log

- 2026-04-17: Phase B-1/B-2/B-4/B-5 foundation slice started with red property tests for the new `propstore.belief_set` subsystem (`logs\test-runs\ws-b-red-belief-set-20260417-094021.log`, import failure as expected). Implemented a finite propositional model-theoretic core (`Formula`, `World`, `BeliefSet`, truth-table `Cn`), Spohn/Darwiche-Pearl ranking revision with provenance traces, Harper contraction, Gärdenfors-Makinson entrenchment, Konieczny-Pino Pérez model-theoretic IC merge over all `mu`-models, Baumann kernel-union AF expansion, Diller faithful-assignment extension revision, and Cayrol grounded-addition classification. Verification slice passed: `tests/test_belief_set_postulates.py tests/test_af_revision_postulates.py` (`11 passed`, `logs\test-runs\ws-b-belief-set-green-3-20260417-094513.log`) and `uv run pyright propstore/belief_set` (`0 errors`). Architectural critique agreed the existing `propstore/world/ic_merge.py` should be renamed as assignment-selection while true IC merge belongs under `propstore.belief_set`; `propstore/revision/` should be retired or replaced, not shimmed.
- 2026-04-17: Phase B-3 iterated-revision slice completed. Added `propstore.belief_set.iterated` with world-preorder-level `lexicographic_revise` (all input-worlds before all countermodels, preserving internal preorder) and `restrained_revise` (conservative Spohn/DP update), replacing the old atom-id-order interpretation of those names. Verification slice passed: red import gate (`logs\test-runs\ws-b-red-iterated-20260417-094658.log`), focused iterated/DP suite (`4 passed`, `logs\test-runs\ws-b-iterated-green-1-20260417-094737.log`), and `uv run pyright propstore/belief_set` (`0 errors`).
- 2026-04-17: Phase B-4 assignment-selection rename completed. `propstore/world/ic_merge.py` was renamed to `propstore/world/assignment_selection_merge.py`, callers moved to `ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE`, stale test helper names were removed, and `docs/gaps.md` now closes the old "IC merge candidate enumeration uses observed values" gap by distinguishing assignment selection from true `propstore.belief_set.ic_merge`. Verification slice passed: targeted rename suite (`73 passed`, `logs\test-runs\ws-b-assignment-selection-rename-4-20260417-095915.log`) after a caught regression in `logs\test-runs\ws-b-assignment-selection-rename-2-20260417-095614.log`, plus `uv run pyright propstore/world/assignment_selection_merge.py propstore/world/resolution.py propstore/world/types.py` (`0 errors`).
- 2026-04-17: Phase B-6 retirement slice completed for the old import path. Added a red gate proving `propstore.revision` still existed (`logs\test-runs\ws-b-red-revision-retirement-20260417-100244.log`), moved the surviving operational support-incision adapter to `propstore.support_revision`, migrated active callers/tests/docs, and made malformed required snapshot/context structures hard-fail instead of decoding as empty mappings. Verification slice passed: retirement gate (`2 passed`, `logs\test-runs\ws-b-revision-retirement-gate-20260417-100444.log`), moved revision/worldline/context suite (`69 passed`, `logs\test-runs\ws-b-support-revision-move-2-20260417-101109.log`), and `uv run pyright propstore/support_revision propstore/worldline/revision_capture.py propstore/worldline/revision_types.py propstore/context_types.py` (`0 errors`).

## What you're doing

`propstore/revision/` is 1663 lines of code that claims to be AGM belief revision. The 2026-04-16 review found it is not:

> **Axis 3c, biggest drift:** The revision module claims AGM lineage in prose (proposal, CLAUDE.md) but the code does not implement AGM semantics, does not cite any AGM paper, and is not tested against AGM postulates. Concretely: zero literature citations in source, zero K*1-K*8 / K-1-K-8 / C1-C4 / EE1-EE5 / P*1-P*6 / A*1-A*6 tests. The only Levi test is a tautology (revise equals its own definition). The "entrenchment" is a weighted-support-count total order, not Gärdenfors entrenchment. The only operators named after literature concepts ("restrained," "lexicographic") rearrange atom IDs in tuple order without any connection to preorder-level definitions in Booth 2006 or DP 1997.

> **Recovery (K-6) is not verifiable:** the operator does not work on deductively closed belief sets — it operates on a tuple of BeliefAtom objects with ATMS-style support sets. There is no Cn closure anywhere. So AGM postulates are not syntactically expressible against this datatype.

> **AF revision is absent entirely:** `revision/af_adapter.py` does NOT implement AF revision. It projects an active-claim subset of a store. No module in this codebase implements Baumann 2015, Diller 2015, or Cayrol 2014.

> **IC merge is honestly flagged but not tested:** `world/ic_merge.py` correctly documents its deviation from Konieczny but has no IC0-IC8 property tests. The candidate space is `product(observed_source_values_per_concept)`, not `μ`-models. Sources `x=5` and `x=10` will never admit `x=7` as a winner, even when the integrity constraint allows the interval. This is assignment-selection under constraint, not belief-base merge.

Your job: build a real belief-set layer with `Cn` closure over logical formulas, implement AGM operators that satisfy K*1-K*8, Darwiche-Pearl iterated operators that satisfy C1-C4, Gärdenfors entrenchment satisfying EE1-EE5, Konieczny IC merge satisfying IC0-IC8 with real model-theoretic semantics, and AF revision per Baumann 2015 + Diller 2015 + Cayrol 2014. Property-test every postulate.

**The existing `propstore/revision/` module either becomes a wrapper around the real thing (if its ATMS-style nogood minimization is useful as a specific operator with an honest name), or is retired.** You decide during the work which is appropriate. The principled path is "retire if the honest name doesn't add value; wrap if the underlying ATMS-style operator has real use cases once it's stripped of AGM pretense."

## Vision

When this workstream is complete, propstore has:

- **`BeliefSet` as a first-class type** over propstore's claim language. `Cn(B)` is the consequence operator. Property tests verify that `Cn` is monotonic, idempotent, inclusive.
- **`BeliefSetRevision` module** implementing AGM operators: `expand`, `contract`, `revise`. Every AGM postulate (K*1 closure, K*2 success, K*3 inclusion, K*4 vacuity, K*5 consistency, K*6 extensionality, K*7 conjunction, K*8 conjunctive inclusion; K-1 closure, K-2 inclusion, K-3 vacuity, K-4 success, K-5 recovery, K-6 extensionality, K-7 conjunction, K-8 conjunctive inclusion) is a `@given` property test.
- **`IteratedRevision` module** implementing Darwiche-Pearl postulates C1-C4 over sequences of revisions. "Restrained" and "lexicographic" operators are real preorder-level definitions from Booth 2006 and Nayak-Spohn, property-tested against their representation theorems.
- **Gärdenfors entrenchment** as a genuine EE1-EE5-satisfying preorder over the belief set: dominance (EE1), conjunctiveness (EE2), minimality (EE3), maximality (EE4), transitivity (EE5). Not a weighted-support-count total order — the real algebraic structure.
- **Real IC merge** per Konieczny 2002. Candidate space is all `μ`-models, not observed values. IC0-IC8 property-tested. The existing `world/ic_merge.py` either becomes an honestly-named alternative operator (`AssignmentSelectionMerge` or similar) or is retired.
- **AF revision module** implementing Baumann 2015 AGM-meets-abstract-argumentation, Diller 2015 extension-based belief revision (P*1-P*6, A*1-A*6), Cayrol 2014 change operators. Faithful-assignment representation per Diller.
- **Every operator carries provenance** via WS-A phase 1's `Provenance` type. A revision's output carries the revision witness + the pre-image belief set fingerprint.
- **Integration with worldline**: `worldline/revision_capture.py` becomes the tracing layer for real belief revision operators (currently captures operations against the drifted revision module).

## What you are NOT doing

- **Not re-implementing the argumentation surface.** Dung, ASPIC+, bipolar all survive unchanged. Axis 3a verified the recursive argument construction is correct.
- **Not replacing `world/atms.py`.** Axis 3e confirmed it's high-fidelity de Kleer 1986. The new belief-set operators consume ATMS nogoods as useful input but the ATMS is not part of this workstream.
- **Not replacing `world/ic_merge.py` behavior wholesale.** It gets an honest name (if kept) and an honest module docstring. The new Konieczny IC merge lives alongside; both can be useful for different needs.
- **Not touching the defeasibility pipeline.** `grounding/`, `conflict_detector/`, `aspic_bridge/` are WS-C's territory.

## Key design decisions — made

Decisions the principled-path analysis already settled; don't re-debate:

- **Belief sets are over formulas, not typed assignments.** AGM is expressible only over a language with a consequence operator. The typed-assignment approach extends `ic_merge.py`'s existing machinery but cannot express recovery (K-6); formulas are the faithful-to-paper choice. A new `propstore/belief_set/` subsystem is the home.
- **Language:** propstore's existing CEL expressions over typed claims are the formula language. `Cn` is defined modulo CEL-typed equivalence + provenance-preserving equivalence. Z3 integration via `z3_conditions.py` provides decidable subquery routing.
- **No backward compat with existing `revision/`.** Rip out; replace; callers migrate.
- **AF revision** — Baumann 2015 as the primary semantic reference; Diller 2015 for the representation theorem + postulate list; Cayrol 2014 for the change-operator taxonomy.

## Papers

**Priority (read first, notes to non-stub depth):**
- Alchourrón-Gärdenfors-Makinson 1985, *On the Logic of Theory Change*. AGM foundations. K*1-K*8, K-1-K-8, Levi identity, Harper identity.
- Gärdenfors 1988, *Knowledge in Flux* — entrenchment. EE1-EE5 axioms, representation theorem linking entrenchment to contraction.
- Darwiche-Pearl 1997, *On the Logic of Iterated Belief Revision*. C1-C4 postulates + representation theorem.
- Booth 2006, *Admissible and Restrained Revision*. Operational definition of restrained + admissible revision over total preorders.
- Konieczny-Pino Pérez 2002, *Merging Information Under Constraints*. IC0-IC8 postulates, model-theoretic merge operators (Σ, Max, GMax / leximax).
- Baumann 2015, *AGM Meets Abstract Argumentation*. AGM postulates adapted to argumentation frameworks.
- Diller 2015, *An Extension-Based Approach to Belief Revision in Abstract Argumentation*. P*1-P*6, A*1-A*6 postulates; faithful-assignment representation.
- Cayrol 2014, *Change in Abstract Argumentation Frameworks*. Taxonomy of AF change operators.

**Secondary (read for context, cite as needed):**
- Alchourrón-Makinson 1982, *On the Logic of Theory Change: Contraction Functions and their Associated Revision Functions*. Predecessor to 1985.
- Nayak-Spohn — for the literature definition of "lexicographic revision" that Booth 2006 builds on.
- Coste-Marquis 2007, *Merging Dung's Argumentation Systems*. AF-level IC merging. Cross-references with Konieczny at the AF level.
- Bonanno 2007, *AGM Belief Revision in Temporal Logic*. Already cited in `repo/branch.py` docstring without implementation — resolve the citation-as-claim violation while you're here.
- Doyle 1979, *A Truth Maintenance System* and de Kleer 1986, *An Assumption-Based TMS*. Background for the ATMS interaction; `world/atms.py` already implements the latter.

**Cross-reference:**
- `world/ic_merge.py` current implementation — read it before designing the new IC merge. Understand what operator it actually is, whether it has standalone value, and what its honest name should be.

## Phase structure (internal)

### Phase B-1 — Belief-set + Cn foundation
- Design `BeliefSet` type + `Cn` consequence operator over propstore's formula language.
- `Cn` property tests: monotonic, idempotent, inclusive.
- Integration with CEL + Z3 for decidable subqueries.

### Phase B-2 — AGM operators + postulate property tests
- `expand`, `contract`, `revise` operators.
- K*1-K*8 and K-1-K-8 as `@given` property tests over randomly generated `BeliefSet` + input pairs.
- Levi identity (`revise = expand after contract of negation`) property-tested against the actual AGM definition, not a tautology.
- Harper identity (`contract` derivable from `revise`) property-tested.
- Gärdenfors entrenchment as EE1-EE5-satisfying preorder, with the representation theorem verified (entrenchment determines contraction and vice versa).

### Phase B-3 — Iterated revision + DP postulates
- `IteratedRevision` operator.
- C1-C4 as `@given` property tests over revision sequences.
- Booth 2006 restrained revision + Nayak-Spohn lexicographic revision property-tested against their representation theorems.

### Phase B-4 — Real IC merge
- `model_theoretic_ic_merge` operator over belief-base profiles with integrity constraints.
- IC0-IC8 as `@given` property tests.
- `world/ic_merge.py` either gets an honest rename (`assignment_selection_merge` or similar) with a module docstring explaining the deviation from Konieczny, or is retired with callers migrated.

### Phase B-5 — AF revision
- `af_revise`, `af_contract`, `af_expand` operators over argumentation frameworks.
- P*1-P*6, A*1-A*6 as `@given` property tests per Diller 2015.
- Baumann 2015 expansion-as-kernel-union and contraction postulates verified.
- Faithful-assignment representation validated per Diller's representation theorem.
- Cayrol 2014 change-operator taxonomy referenced; where our operators align, citations are backed by tests.

### Phase B-6 — Existing `propstore/revision/` reconciliation
- Decide: retire or wrap with honest name?
  - If wrap: rename operators (`support_set_contract` instead of `contract`; retract all AGM citations; add module docstring explaining what the operator actually is — ATMS-style nogood minimization — and when it's useful).
  - If retire: migrate all callers to the new belief-set operators; delete `propstore/revision/`.
- Either way: `plans/true-agm-revision-*.md` files get honest updates or deletion.
- `CLAUDE.md`'s revision layer paragraph rewritten to match whichever path was taken.

## Red flags — stop if you find yourself

- About to claim "restrained revision" without the preorder-level definition from Booth 2006.
- About to call a weighted total order "entrenchment" without verifying EE1-EE5.
- About to test an AGM postulate with a single example instead of `@given`.
- About to preserve the old revision module's tautological Levi test.
- About to cite Alchourrón without a corresponding property test.
- About to extend the typed-assignment machinery for AGM instead of implementing formulas.
- About to keep the old `world/ic_merge.py` under its misleading name without honest renaming or retirement.
- About to write an AF revision operator without verifying against Diller's representation theorem.

## Exit criteria

- All priority papers at non-stub depth.
- `propstore/belief_set/` subsystem lives. `uv run pyright --strict` green on every file.
- K*1-K*8, K-1-K-8, C1-C4, EE1-EE5, IC0-IC8, P*1-P*6, A*1-A*6 all `@given` property-tested and green.
- Levi + Harper identity tests are non-tautological (test against the real AGM definitions, not against the operator's own internal implementation).
- `world/ic_merge.py` resolution (renamed or retired) complete. `docs/gaps.md` reflects closure.
- AF revision module lives. Faithful-assignment representation verified.
- `propstore/revision/` reconciliation complete (wrapped or retired per Phase B-6).
- CLAUDE.md's "Argumentation layer" + "Known Limitations" sections updated with honest claims backed by tests.
- `docs/belief-set-revision.md`, `docs/ic-merge.md`, `docs/af-revision.md` exist.
- All axis-3c findings marked closed in `docs/gaps.md`.

## On learning

AGM belief revision is one of the cleanest theoretical edifices in knowledge representation. The Alchourrón-Gärdenfors-Makinson 1985 paper is a minor miracle — eight postulates + representation theorem, half a page of proofs, decades of downstream work. Darwiche-Pearl's C1-C4 extends it to iteration with the same crystalline style. Read these papers the way you would read a proof: slowly, verifying each step, reconstructing the author's inferences. When you can sketch the representation theorems from memory, you are ready to implement.

Konieczny on IC merge is more operational — read alongside Coste-Marquis for the AF-level generalization. Baumann and Diller on AF revision are the most recent and the most directly applicable to propstore's shape.

This is the theoretical spine of principled belief dynamics. The code you write here will be read by future agents as the canonical example of "how to bridge AGM to a working system." Write it accordingly.
