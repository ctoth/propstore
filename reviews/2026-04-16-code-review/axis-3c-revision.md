# Axis 3c — Revision Fidelity

*Returned inline by scout subagent; saved here verbatim.*

## Scope

- Target modules: `propstore/revision/` (10 files, 1663 LOC), `propstore/world/ic_merge.py` (350 LOC), `propstore/repo/merge_*.py` + `paf_merge.py` + `structured_merge.py` (1352 LOC). Total: 3465 LOC.
- Priority papers read: Alchourrón 1985, Darwiche 1997, Booth 2006, Konieczny 2002, Baumann 2015, Diller 2015 (notes.md). Skimmed: Cayrol 2014, Bonanno 2007 (via indirect references).

## Counts

- Tests in scope: `test_revision_operators.py` (13 tests), `test_revision_iterated.py` (~9 tests), `test_revision_iterated_examples.py` (2 tests), `test_revision_entrenchment.py` (3 tests), `test_revision_properties.py` (1 Hypothesis test), `test_ic_merge.py` (~55 tests, heavy Hypothesis coverage), `test_paf_merge.py` (8 tests w/ Hypothesis), `test_merge_classifier.py` (11 tests w/ Hypothesis), `test_worldline_revision.py` (5 tests), `test_revision_af_adapter.py`, `test_revision_explain.py`, `test_revision_projection.py`, `test_revision_bound_world.py`, `test_revision_cli.py`, `test_revision_phase1*.py`, `test_revision_state.py`.
- AGM postulate property tests: **0**. No test file names or contents reference K*1-K*8, K-1-K-8, P*1-P*6, A*1-A*6, IC0-IC8, C1-C4, EE1-EE5, Maj, Arb, or Sym.
- Literature citations in revision module source: **0**. No mention of Alchourrón, Gärdenfors, Darwiche, Pearl, Booth, Baumann, Diller (2015), Cayrol, Doutre, Dixon, Konieczny, Coste-Marquis, Bonanno, Spohn, or Rotstein anywhere in `propstore/revision/*.py`.
- Literature citations elsewhere in scope:
  - `propstore/world/ic_merge.py:8-10,44`: Konieczny 2002 cited (module docstring, `claim_distance` docstring).
  - `propstore/repo/branch.py:6-11`: docstring cites "Bonanno 2007, claim 9" and "Darwiche & Pearl 1997, C1-C4" but nothing in that file implements them.
  - `propstore/repo/branch.py:165`: `merge_base` docstring cites "Konieczny & Pino Pérez 2002" — unrelated to IC merging postulates; just flags merge-base identification.
  - `docs/semantic-merge.md:48-50` cites Coste-Marquis 2007, Konieczny 2002, ASPIC+.

## Audit answers

### 1. AGM operators (`propstore/revision/operators.py`)

- `expand`, `contract`, `revise` exist (lines 90, 111, 127). Docstrings describe operational behavior ("cutting a minimal low-entrenchment support incision set"). No docstring references AGM or Alchourrón 1985.
- `contract` (line 111-124) implements a **support-set incision** algorithm — pick minimum-size combo of assumption IDs that hits every support set of each target, break ties by total entrenchment weakness (`operators.py:254-286`). This is an ATMS-style nogood-minimization, not partial-meet contraction on remainder sets.
- `revise` (line 127-157) is defined as "contract then expand" (operational Levi composition). The only Levi test (`test_revision_operators.py:84-109` `test_revise_matches_operational_levi_identity`) asserts that `revise(base, a) == expand(contract(base, conflicts[a]), a)` — i.e. it verifies the function equals its own internal implementation. No independent Levi check.
- **No K*1-K*8 property tests, and no K-1-K-8 property tests.** The proposal file (`proposals/true-agm-revision-proposal.md:624-625`) lists "Levi identity holds operationally" and "Harper round-trip is consistent with the package semantics" as "success criteria" — the Harper round-trip test does not exist.
- Recovery (K-6: `A ⊆ Cn((A-x) ∪ {x})`) is not verifiable in this code: the operator does not work on deductively closed belief sets — it operates on a tuple of `BeliefAtom` objects with ATMS-style support sets. There is no `Cn` closure anywhere. So the AGM postulates are not **syntactically expressible** against this datatype.

### 2. Darwiche-Pearl iterated postulates (`propstore/revision/iterated.py`)

- `iterated_revise` (line 58-95) takes `operator="restrained"` or `operator="lexicographic"` (line 129-138). These are the names Booth 2006 uses, but nothing in the file cites Booth, Darwiche, or Pearl.
- "Restrained" implementation (`iterated.py:133-136`): survivors first (preserving old order), then new atom, then extras. Booth 2006's restrained revision is defined over total preorders on worlds with a specific marking procedure. The code's "restrained" is a surface-level atom-id rearrangement; the semantic match to Booth 2006's Definition/Theorem 2 is unverified.
- "Lexicographic" implementation (`iterated.py:129-132`): input atom first, then survivors, then extras. Lexicographic revision in the literature (Nayak, Spohn) has a specific preorder-level definition (level re-stacking). Again — no citation, no mapping, no property test.
- **No C1-C4 tests.** `tests/test_repo_branch.py:8-11` lists DP postulates in the docstring, but its actual tests (lines 83-86, 221-223) explicitly say "This test verifies commit isolation, not a formal C1/C2 verification (which requires a revision operator)." So C1-C4 are named in prose and never checked against the revision operator that now exists.
- `test_iterated_revise_is_history_sensitive_even_with_same_current_acceptance` (`test_revision_iterated.py:150-186`) checks that history matters. That is an informal prerequisite for DP — necessary but not sufficient.

### 3. Entrenchment (`propstore/revision/entrenchment.py`)

- `compute_entrenchment` (line 33-73) is a single-pass ranking by `(override_rank, -support_count, atom_id)` tuple. That's a total order by construction.
- The docstring (line 40-43) says: "deterministic V1 entrenchment ordering. Explicit overrides outrank support-derived ordering. Support-derived ranking then falls back to environment coverage and stable atom id ordering." **No reference to Gärdenfors's EE1-EE5 axioms** (dominance, conjunctiveness, minimality, maximality, transitivity). Conjunctiveness cannot even be expressed here because atoms are not formulas (no conjunction operation).
- No test file validates EE1-EE5.
- **Drift:** the name "entrenchment" is used for a total order on atoms that is essentially a weighted support count. Gärdenfors entrenchment is a specific algebraic structure over a belief set; this is not it.

### 4. AF revision (`propstore/revision/af_adapter.py`)

- `af_adapter.py` **does not implement AF revision**. `project_epistemic_state_argumentation_view` (line 112-137) projects active claims from an `EpistemicState` into a read-only store overlay (`RevisionArgumentationStore`, line 44-109). It passes through `stances_between`, `conflicts`, etc. to the backing store but **filters them by which claims survive the epistemic state**. There is no P*1-P*6 (Diller), no A*1-A*6 (Diller), no expansion-as-kernel-union (Baumann 2015), no faithful-assignment revision.
- The one-line description in the proposal (`proposals/true-agm-revision-proposal.md:566-584`) acknowledges this: "the view carries a revision-projected store overlay for claim-graph consumers… merge remains outside this adapter path." So the *adapter* is intentionally not an AF-revision operator. But then **no module in this codebase implements Baumann 2015, Diller 2015, or Cayrol 2014**. The "AF revision" question in the audit prompt has no code to review.

### 5. IC merge (`propstore/world/ic_merge.py`)

- Module docstring (line 1-12) explicitly acknowledges the deviation: "Konieczny 2002 defines merging over propositional belief bases with min-over-models distance and an integrity constraint μ over models. This module preserves the aggregation families (sum/max/leximax) but adapts them to observed concept values rather than full belief-base model semantics."
- Implementation: `solve_ic_merge` (line 312-350) enumerates candidate concept-assignments over the cross-product of observed source values per concept (`enumerate_candidate_assignments`, line 86-111), filters by integrity constraint (range/category/CEL/custom), scores by operator (Σ/Max/GMax).
- Distance is point-wise (line 114-121): absolute-diff for numerics, Hamming for non-numerics.
- **Agreement with IC postulates:** no IC0-IC8 property test. `test_ic_merge.py` has Maj, Arb, Sym-like checks at the *scalar oracle* level only (`_sigma_merge`, `_max_merge`, `_gmax_merge` local test helpers, lines 165-234), not on the production `solve_ic_merge` function.
- `test_ic_merge.py:451-458` (`test_max_duplicate_invariance_exposes_scalar_limit`) explicitly flags the drift in its own docstring: "This is the arbitration-style property the current implementation really enforces. It should not be confused with the paper's full fairness postulates, which require a model-theoretic result space."
- CLAUDE.md claim of "Assignment-level IC merge with CEL/Z3 is implemented" is accurate (`_eval_cel_constraint_z3` at line 170-181, `_compile_cel_constraint` at 184-202, Z3ConditionSolver integration verified). The deviation is openly declared: admissibility is checked by Z3 over declared concept values, not by model-theoretic merge over propositional interpretations.
- **Biggest departure:** the candidate space is `product(observed_source_values_per_concept)` (line 101-111). A true IC merge candidate space is all `μ`-models. Two sources `x=5` and `x=10` will never admit `x=7` as a winner here, even if the integrity constraint μ allows the full interval. This is an assignment-selection operator, not an IC merge operator — closer to majority-vote selection under constraint.

### 6. Repo merge pipeline (`merge_framework.py` + `merge_classifier.py` + `structured_merge.py` + `paf_merge.py`)

- `build_merge_framework` (`merge_classifier.py:275-457`) is end-to-end: find merge-base, load claims from base/left/right, canonicalize groups by shared logical ID, then per-artifact classification:
  - identical → emit once
  - one-sided edit vs base → emit the edited side
  - two-sided edit → emit both, classify pair via `_classify_pair` (line 185-244) as CONFLICT/PHI_NODE/COMPATIBLE
- `_classify_pair` (line 185-244) delegates to `propstore.conflict_detector.detect_conflicts`. Conflict classes: CONFLICT/OVERLAP/PARAM_CONFLICT → attack pair; PHI_NODE/CONTEXT_PHI_NODE → ignorance pair. This is the semantic vs syntactic distinction.
- Output is `PartialArgumentationFramework` (three-way partition of pair space into attack/ignorance/non_attack, `merge_framework.py:27-87`). This matches Coste-Marquis 2007 partial AFs.
- `create_merge_commit` (`merge_commit.py:20-151`) builds a two-parent commit (line 146: `commit.parents = [left_sha.encode('ascii'), right_sha.encode('ascii')]`). CLAUDE.md's "two-parent merge commits" claim holds.
- `paf_merge.py`: `sum_merge_frameworks`, `max_merge_frameworks`, `leximax_merge_frameworks` (lines 84-155) do exact enumeration of all AFs over the shared universe and score by Hamming edit distance on pair labels (line 128-143). For the 2-argument case, this enumerates all 16 possible attack relations. This is *bounded brute force* — correct for tiny `|A|` but explicitly `O(2^{|A|^2})`.
- **Drift vs CLAUDE.md claim of "branch reasoning (ATMS/ASPIC+ bridge)":** `structured_merge.py:256-283` (`build_branch_structured_summary`) builds `StructuredProjection` via `build_structured_projection` from `propstore.structured_projection`. This exists. But there is no "ATMS" link in this merge pipeline — the merge classifier routes through the conflict detector, not through ATMS labels or justifications.
- **Drift:** `structured_merge.py:172-178` (`_summary_relation_surface`) and `:180-188` (`_summary_lossiness`) explicitly document that the branch-local summary loses `subargument_identity`, `justification_identity`, `preference_metadata`, `support_metadata`, `known_non_attack_relations`, `ignorance_relations`. So the structured merge deliberately lossy-projects before merging. This is documented but significant: the "formal merge" at the structured level operates over degraded inputs.

## Biggest drift

**The revision module claims AGM lineage in prose (proposal, CLAUDE.md) but the code does not implement AGM semantics, does not cite any AGM paper, and is not tested against AGM postulates.**

Concretely: `propstore/revision/` has 1663 LOC, zero literature citations in source, zero K*1-K*8 tests, zero C1-C4 tests, zero EE1-EE5 tests, zero P*1-P*6 or A*1-A*6 tests. The only Levi test is a tautology (`revise` equals its own definition). The only operator named after a literature concept ("restrained", "lexicographic", `iterated.py:129-138`) rearranges atom IDs in tuple order without any connection to the preorder-level definitions in Booth 2006 or the DP 1997 representation theorem. The "entrenchment" (`entrenchment.py`) is a weighted-support-count total order, not a Gärdenfors entrenchment.

The proposal file (`proposals/true-agm-revision-proposal.md`, Status: "Implemented through Phase 5") declared these postulates as success criteria for Phase 2 and Phase 3 but the tests that would verify them do not exist.

**Secondary drift:** `world/ic_merge.py` openly renames "IC merge" to an assignment-selection operator over observed source values. The module docstring honestly flags this. CLAUDE.md also flags it ("Full belief-base/model semantics for Konieczny IC0-IC8 … deferred"). The code is internally consistent with its declared scope — but a reader navigating via the Konieczny paper will find no IC0-IC8 postulate check against the current implementation (only scalar-oracle-level sanity checks).

**Tertiary drift:** CLAUDE.md names `aspic_bridge.py`/`aspic.py` as the ATMS/ASPIC+ bridge for branch reasoning. The actual repo merge pipeline (`merge_classifier.py`, `structured_merge.py`) routes through `conflict_detector` and `structured_projection` — not through ATMS label/nogood machinery. The CLAUDE.md phrase "branch reasoning (ATMS/ASPIC+ bridge)" doesn't match what `merge_classifier.py` does at the code level.

## Discipline tag

Postulates status across all six audit questions: **postulate-ignored** for AGM K*1-K*8/K-1-K-8, DP C1-C4, Gärdenfors EE1-EE5, Diller P*1-P*6 + A*1-A*6, Baumann AF revision/expansion; **postulate-declared-in-module-docstring-but-unverified** for Konieczny IC0-IC8 on `ic_merge.py`; **postulate-satisfied-by-paper-oracle** only in the scalar ic_merge helper (`_sigma_merge`/`_max_merge`/`_gmax_merge` in the test file, which are not production code). No Hypothesis property tests map onto any named AGM/DP/IC postulate identifier.
