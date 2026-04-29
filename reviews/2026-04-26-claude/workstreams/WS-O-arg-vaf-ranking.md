# WS-O-arg-vaf-ranking: argumentation pkg coverage — Bench-Capon VAF + Bonzon ranking semantics family + Atkinson 2007 AATS slice

**Status**: CLOSED 418d409c
**Depends on**: WS-O-arg-argumentation-pkg (the existing-bugs sub-stream — cluster-P HIGH bugs land first so the kernels we extend are not built atop known-broken substrate)
**Blocks**: WS-O-arg-gradual (consumes `RankingResult` + the harmonized convergence contract this WS lands)
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Authoritative**: `reviews/2026-04-26-claude/DECISIONS.md` D-15 (upstream-only fix policy), D-16 (implement all four coverage groups; this is Group C), Codex round 2 findings 2.22 (ranking convergence ownership) and 2.23 (Atkinson scope honesty)

**Owns** (locked here per Codex 2.22):
- `argumentation/src/argumentation/ranking.py` non-convergence handling
- `RankingResult` typed dataclass (the uniform return type for all ranking semantics)
- All seven ranking semantics — Categoriser, Burden, Discussion-based, Counting, Tuples-based, h-Categoriser, Iterated-graded
- `subjective_aspic.py` rename of `value_based.py`
- `vaf.py` (new Bench-Capon kernel)
- `practical_reasoning.py` (new Atkinson 2007 AS1 + CQ5/6/11 slice — explicitly partial, see scope honesty below)
- `ranking_axioms.py` (Amgoud 2013 axiom predicate suite)

**Reasoning for ownership lock**: ranking semantics are this WS's core scope. WS-O-arg-gradual previously had ambiguous claim on `ranking.py` non-convergence and `RankingResult`; per Codex 2.22 the conflict resolves in favour of this WS because gradual semantics CONSUME the ranking result, they do not own its shape. WS-O-arg-gradual depends on this WS shipping `RankingResult` + `converged: bool` first; that stream then extends the same uniform contract to DF-QuAD and Matt-Toni 2008 without owning the underlying type.

---

## Why this workstream exists

Cluster P's argumentation-package review (`reviews/2026-04-26-claude/cluster-P-argumentation-pkg.md`) inventoried two distinct gaps that share a single fix locus: the package ships strong substrate for abstract Dung AFs and ASPIC+ but has a thin head on top of that substrate where the literature has built its most actionable user-facing semantics.

**Gap 1 — VAF (value-based AFs).** Bench-Capon 2003 introduced argument strength relative to an audience-specific value ordering: an attack succeeds only if the attacker's value is not less preferred than the target's under the audience. This is the formalism the propstore project depends on for *audience-relative* reasoning — the same claim graph yields different acceptances under different value orderings, and propstore's whole "everything is a defeasible claim with provenance" stance (per global memory `feedback_imports_are_opinions`) is hollow without this. The package has a module *named* `value_based.py` (`argumentation/src/argumentation/value_based.py:1-156`) but its implementation is Wallner 2024 ASPIC+ subjective filtering — a different formalism. Cluster P explicitly flags the naming overload at line 156 of that file and at the cluster-P module table. From the perspective of any consumer importing `argumentation.value_based` expecting Bench-Capon, the module silently does the wrong thing. Open question 6 in cluster-P confirms the rename to `subjective_aspic.py` is the resolution; that rename is in scope here.

**Gap 2 — ranking semantics family.** Bonzon 2016 catalogues at least six ranking-based semantics for abstract AFs, of which `argumentation/src/argumentation/ranking.py` ships exactly two: Categoriser (`ranking.py:33`) and Burden numbers (`ranking.py:82`). The propstore project's argumentation-pipeline-replaces-heuristic decision (D-8) puts ranking semantics on the critical path: the planned `prior_base_rate` pipeline takes the kernel's output as a typed Opinion, and the *semantics chosen* materially changes that output. Shipping two semantics out of six is the kind of silent under-coverage that lets unverified design choices propagate downstream — propstore consumers will pick whichever ranking is exposed without knowing the alternatives even exist.

Atkinson 2007 enters as a deliberately scoped *slice*, not a complete implementation — see "Scope honesty" below.

This workstream closes both gaps in `../argumentation` upstream, per D-15 (no propstore-side wraps, no fork — the dep ships, propstore pin-bumps).

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **P-VAF-1** | cluster-P "Bench-Capon 2003 VAF" missing-features bullet | `cluster-P-argumentation-pkg.md:653-657` | No VAF module. `value_based.py` is named misleadingly; implements Wallner 2024 ASPIC+ filtering, not VAFs. |
| **P-VAF-2** | cluster-P naming-overload note | `value_based.py:1-156` | Module name suggests Bench-Capon 2003 VAFs; internals do something else. Open question 6 in cluster-P confirms — rename to `subjective_aspic.py`. |
| **P-RANK-1** | cluster-P "Ranking" subsection | `cluster-P-argumentation-pkg.md:262-283` | Bonzon 2016 catalogues 6+ ranking semantics; only Categoriser + Burden ship. Tuples-based, h-Categoriser, Discussion-based, Counting absent. |
| **P-RANK-2** | cluster-P "Ranking" subsection | `cluster-P-argumentation-pkg.md:271-277` | Amgoud 2013 axioms (Abstraction, Independence, VP, SC, CP, QP, CT, SCT, DP, DDP, +SADB) not exposed as testable predicates. |
| **P-RANK-3** | cluster-P "Ranking" subsection | `ranking.py:65` vs `gradual.py:133` | `categoriser_scores` raises `RuntimeError` after `max_iterations`; `gradual.py` returns `converged=False`. Inconsistent error contracts in the same module group. **Owned here per Codex 2.22.** Uniform contract via `RankingResult.converged`. |
| **D-16 Group C** | `DECISIONS.md:166-170` | n/a | "All four groups — implement everything." This is Group C. |
| **D-15** | `DECISIONS.md:158-162` | n/a | Upstream-only. PRs in `../argumentation`, propstore pin-bumps. |
| **Atkinson 2007 (slice)** | papers retrieval log | `papers/Atkinson_2007_PracticalReasoningPresumptiveArgumentation/notes.md` | Modern algorithmic VAF treatment with action-based alternating transition systems. **Partial implementation only**: AS1 + CQ5 + CQ6 + CQ11. The remaining critical questions (CQ1-4, CQ7-10, CQ12+) are explicitly out of scope here and tracked for a future workstream. See "Scope honesty" below. |
| **Wallner 2024** | papers/notes | `papers/Wallner_2024_ValueBasedReasoningInASPIC/notes.md` | VAF embedded into ASPIC+. The current `value_based.py` partially covers this but under the wrong name; will be `subjective_aspic.py` after rename. |
| **Codex 2.22** | round 2 findings | n/a | Ranking convergence ownership locked here, not in WS-O-arg-gradual. |
| **Codex 2.23** | round 2 findings | n/a | Atkinson 2007 work renamed from "AATS implementation" to "AATS slice"; honest about which CQs are implemented. |

## Code references (verified by direct read of cluster-P; not re-checked here, see verification step below)

### Existing ranking module (where extensions land)
- `argumentation/src/argumentation/ranking.py:33` — `categoriser_scores(framework, *, max_iterations, tolerance)`
- `argumentation/src/argumentation/ranking.py:65` — `RuntimeError` after non-convergence (contract drift point — owned here, deletes in this WS)
- `argumentation/src/argumentation/ranking.py:82` — `burden_numbers(framework, *, depth)`

### Existing module under wrong name (gets renamed in this WS)
- `argumentation/src/argumentation/value_based.py:1-156` — currently a Wallner-2024 ASPIC+ subjective filter, not a VAF

### Existing gradual module (referenced for contract harmonization, not changed by this WS — WS-O-arg-gradual extends it)
- `argumentation/src/argumentation/gradual.py:133` — `converged: bool` return field

### Cross-stream dependency (must land first)
- `WS-O-arg-argumentation-pkg` per D-16 expansion — closes the cluster-P HIGH bugs (e.g., `dung.py:582-585` ideal-extension union, `aspic_encoding.py:165` ASP id scheme). VAF construction sits atop Dung; we don't want to be debugging on a known-broken Dung kernel.

## Papers (read papers/<dir>/notes.md before writing tests)

The first failing tests below pin specific worked-example outputs from these papers. Coders MUST read each `notes.md` before writing tests — per the global feedback policy (`feedback_citations_and_tdd`).

- **Bench-Capon 2003** — `papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/notes.md`. VAF foundations: VAF = ⟨A, R, V, val, ≥⟩ where val: A → V and ≥ is an audience's preference order on V. Defeat under audience: a defeats b iff (a, b) ∈ R AND val(b) ≯ val(a) under the audience. Objective acceptance = accepted under every total ordering on V; subjective acceptance = accepted under some ordering.

- **Atkinson 2007 (slice only)** — `papers/Atkinson_2007_PracticalReasoningPresumptiveArgumentation/notes.md`. Modern algorithmic VAF treatment with action-based alternating transition systems (AATS). Argument scheme AS1 with critical questions, evaluated under value-promoted/demoted action transitions. **Only AS1 + CQ5 + CQ6 + CQ11 are implemented in this WS.** The full AATS framework comprises AS1 plus 17 critical questions; this WS implements 3 of those 17. Remaining CQs are tracked for a future workstream.

- **Amgoud 2014** — `papers/Amgoud_2014_RichPreference-basedArgumentationFrameworks/notes.md`. Rich PAFs unifying VAF-style preferences with structural attack. The substrate against which we test that VAF reduces to PAF-with-singleton-value-classes correctly.

- **Amgoud 2017** — `papers/Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation/notes.md`. Weighted argumentation acceptability axioms. Bridges to the ranking-axiom predicate work (P-RANK-2).

- **Amgoud-Ben Naim 2013** — `papers/Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks/notes.md`. Original axiomatic treatment. Source of the axioms that the predicate suite materializes.

- **Bonzon 2016** — `papers/Bonzon_2016_ComparativeStudyRanking-basedSemantics/notes.md`. **The survey driving the gap inventory.** Worked examples in §3 give expected output rankings on small AFs for every semantics in the family — Categoriser, h-Categoriser, Burden, Discussion-based, Counting, Tuples-based. These are what the first failing tests pin.

- **Baroni 2019** — `papers/Baroni_2019_GradualArgumentationPrinciples/notes.md`. Principles framework. Useful cross-check for the predicate suite.

- **Al-Anaissy 2024** — `papers/AlAnaissy_2024_ImpactMeasuresGradualArgumentation/notes.md`. Already partially implemented in `gradual.py`; cited here for axiom-suite completeness.

- **Wallner 2024** — `papers/Wallner_2024_ValueBasedReasoningInASPIC/notes.md`. VAF embedded into ASPIC+. The current `value_based.py` implements *part* of this but under the wrong file name. After rename, this paper anchors the bridge module that lifts `aspic.py` defeats through a VAF audience filter.

## Scope — what this WS implements

### A. Bench-Capon VAF kernel (new module `argumentation/src/argumentation/vaf.py`)

`VAF` dataclass:
- `arguments: frozenset[str]`
- `attacks: frozenset[tuple[str, str]]`
- `values: frozenset[str]`
- `value_of: Mapping[str, str]` — total function A → V
- `audience: Sequence[str]` — strict total order on V (head = most preferred); represented as a Sequence to keep the audience hashable via tuple-cast

Functions (all paper-faithful to BC03):
- `successful_attacks(vaf: VAF) -> frozenset[tuple[str, str]]` — BC03 Def 5: (a, b) ∈ R survives the audience iff val(b) is not strictly preferred to val(a) under the audience.
- `induced_af(vaf: VAF) -> ArgumentationFramework` — projects a VAF + audience into a Dung AF whose attack set is `successful_attacks(vaf)`. Bridges to existing `dung.py` semantics for free.
- `objectively_acceptable(vaf: VAF, argument: str) -> bool` — accepted under every total ordering on V (BC03 Def 7). Brute over `|V|!` orderings; warn at `|V| > 8` (5040 orderings remains tractable; 9! = 362880 begins to bite).
- `subjectively_acceptable(vaf: VAF, argument: str) -> bool` — accepted under some total ordering (BC03 Def 7).
- `audiences_supporting(vaf: VAF, argument: str) -> Iterator[tuple[str, ...]]` — audiences under which `argument` is in the (preferred) extension. Sized for inspection and worked-example pinning.

### B. Atkinson 2007 AATS slice (new module `argumentation/src/argumentation/practical_reasoning.py`)

This is a deliberate *partial* implementation of Atkinson 2007's practical-reasoning machinery. **Initial and final scope of THIS WS**: AS1 + the value-transition machinery + exactly three critical questions. The full 17 CQs are NOT in scope here; see "What this WS does NOT do" for the explicit out-of-scope list.

Implemented:
- `AlternatingTransitionSystem` dataclass — states, agents, actions, transition relation, value-labelled transitions.
- `AS1Argument` dataclass — current state, action, target state, value promoted.
- `attack_via_critical_question(arg, cq)` — three CQs only:
  - **CQ5**: alternative action promoting same value
  - **CQ6**: action also demotes another value
  - **CQ11**: target state not actually achieved

That is everything `practical_reasoning.py` ships in this WS. The naming convention deliberately uses "AATS slice" rather than "AATS implementation" to make the partiality visible to downstream consumers.

### C. Bonzon ranking semantics family (extend `argumentation/src/argumentation/ranking.py`)

Add five semantics, each as a separately importable function with a uniform return type `RankingResult`:

```python
@dataclass(frozen=True)
class RankingResult:
    scores: Mapping[str, float]   # higher = stronger
    ranking: tuple[frozenset[str], ...]  # equivalence classes, head = top rank
    converged: bool
    iterations: int
    semantics: str  # name of the semantics that produced this result
```

`RankingResult` is owned by THIS WS (per Codex 2.22). Every existing ranking function returns `RankingResult` after this WS — `categoriser_scores` and `burden_numbers` get rewrapped (existing call sites update in the same PR per the no-shims rule, `feedback_no_fallbacks`).

The five new semantics:

1. **Discussion-based (Amgoud-Ben Naim 2013).** `discussion_based(framework) -> RankingResult`. Compares arguments by length-bounded discussion histories: a stronger than b iff a's path tree to direct-attackers is "better" at every depth. Bonzon 2016 §3.4 has the precise comparator.

2. **Counting (Pu et al. 2014).** `counting_scores(framework, *, damping, max_iterations, tolerance) -> RankingResult`. Strength of a = 1 - damping × Σ counting(b) for b attacking a, projected to [0,1]. Iterative.

3. **Tuples-based (Cayrol-Lagasquie-Schiex 2005).** `tuples_ranking(framework) -> RankingResult`. Strength of a is the lex-comparable tuple of (defenders at depth 1, attackers at depth 2, defenders at depth 3, ...). Lex-orders into a ranking.

4. **h-Categoriser (Pu et al.).** `h_categoriser(framework, *, max_iterations, tolerance) -> RankingResult`. Variant where strength(a) = 1 / (1 + Σ strength(b) for b attacker of a) is replaced by an h-aggregation that resolves the discontinuity at unattacked-with-attacked-attackers. Cite Pu et al. exactly.

5. **Iterated graded acceptability (Grossi-Modgil 2015).** `iterated_graded(framework, *, m, n) -> RankingResult`. (m, n)-acceptability: a is (m, n)-defended by S iff every length-m attack chain to a is broken by an S-attack within n steps. Returns the lattice of acceptability pairs each argument satisfies.

### D. Amgoud 2013 ranking-axiom predicate suite (new module `argumentation/src/argumentation/ranking_axioms.py`)

Each axiom from Amgoud 2013 as a predicate `Callable[[Callable[[ArgumentationFramework], RankingResult], ArgumentationFramework], bool]`:
- `abstraction(semantics, af)`
- `independence(semantics, af)`
- `void_precedence(semantics, af)`
- `self_contradiction(semantics, af)`
- `cardinality_precedence(semantics, af)`
- `quality_precedence(semantics, af)`
- `counter_transitivity(semantics, af)`
- `strict_counter_transitivity(semantics, af)`
- `defense_precedence(semantics, af)`
- `distributed_defense_precedence(semantics, af)`
- `strict_addition_of_defense_branch(semantics, af)`

Each predicate is paper-faithful: returns True iff the supplied semantics satisfies the axiom on the supplied AF (or, for axioms quantified universally, returns the relevant counter-example via a sibling `<axiom>_counterexample` function). Used in tests to check that, e.g., Categoriser satisfies Counter-Transitivity but not Cardinality-Precedence (Bonzon 2016 Table 2).

### E. Rename `value_based.py` → `subjective_aspic.py`

Per cluster-P open question 6 and D-15 (no fork, fix upstream). The current contents move verbatim. `argumentation/__init__.py` re-export updates. Any test under `argumentation/tests/` referencing `value_based` updates in the same commit. No alias module, no re-export shim — per `feedback_no_fallbacks`, we update callers in one pass.

### F. Convergence contract for `ranking.py` (P-RANK-3 — owned here per Codex 2.22)

**Boundary (locked per Codex re-review #11):** WS-O-arg-vaf-ranking owns the `RankingResult` type and `ranking.py` module behavior. WS-O-arg-vaf-ranking does **NOT** touch `gradual.py`. `gradual.py` changes — including any kernel changes that return or consume `RankingResult` — are owned entirely by WS-O-arg-gradual.

Every iterative function in `ranking.py` returns `RankingResult.converged` — none raise on non-convergence. Existing `categoriser_scores` `RuntimeError` at `ranking.py:65` deletes; replaced by `converged=False` return. Callers handle the flag.

WS-O-arg-gradual consumes the `RankingResult` type shipped here (one-way handoff at the type boundary) and is responsible for any gradual-kernel work that returns or consumes `RankingResult` values. WS-O-arg-vaf-ranking does not edit `gradual.py`, does not touch `gradual.py:133`, and does not own the `gradual.py` non-convergence contract. If gradual kernels need to populate a `RankingResult`, they do so in WS-O-arg-gradual using the type defined here, without WS-O-arg-vaf-ranking reaching into the gradual module.

## First failing tests (paper-faithful pins; MUST fail on master before any production change in `../argumentation`)

All tests live under `argumentation/tests/`. Per the global TDD discipline (`feedback_citations_and_tdd`, `feedback_tdd_and_paper_checks`), each test cites the exact paper page it pins.

### F1. `tests/test_vaf_bench_capon.py` (new)

- **F1.1** — Build the VAF from BC03 Example 1 (the four-argument AC1 vs AC2 example). Pin `successful_attacks` against the worked example output for two distinct audiences. Must fail today: no `vaf` module exists.
- **F1.2** — Pin `objectively_acceptable(vaf, "AC1")` against BC03 Table 1 row.
- **F1.3** — Pin `subjectively_acceptable(vaf, "AC2")` against BC03 Table 1 row.
- **F1.4** — Reduction sanity: a VAF with `|V| == 1` reduces to its underlying Dung AF (objective acceptance = grounded under the unique trivial audience).
- **F1.5** — Pin `audiences_supporting(vaf, "AC1")` cardinality against BC03's stated count of supporting orderings for the example.

### F2. `tests/test_atkinson_aats_slice.py` (new — note: "slice" in filename per Codex 2.23)

- **F2.1** — Build the AATS from Atkinson 2007's working example (Section 4 — the cake-or-fruit decision). Pin AS1 argument enumeration count.
- **F2.2** — CQ5 attack: an alternative AS1 argument promoting the same value generates an attack edge. Pin one specific edge from the paper.
- **F2.3** — CQ6 attack: an action that promotes value v also demotes value v' generates an attack indexed by both values.
- **F2.4** — CQ11 attack: target state not actually achieved generates an attack.
- **F2.5** — Out-of-scope sentinel: assert that calling `attack_via_critical_question(arg, "CQ1")` (or any CQ outside {CQ5, CQ6, CQ11}) raises `NotImplementedError` with a message naming the missing CQ. This makes the partiality observable to downstream consumers — they cannot accidentally believe a non-implemented CQ silently passes.
- **F2.6** — Round-trip: an AATS yields a VAF when the action set is collapsed to argument names. Verify `induced_af` agrees with `dung.py`'s grounded extension on the projection.

### F3. `tests/test_ranking_bonzon_pins.py` (new)

For each of the seven semantics (Categoriser, Burden, Discussion-based, Counting, Tuples-based, h-Categoriser, Iterated graded), pin the score / ranking output against Bonzon 2016 §3 Example 1 (the standard 5-argument AF the survey uses across every comparison table). One test method per semantics.

- **F3.Cat** — Categoriser scores match Bonzon 2016 Table 1 col 1.
- **F3.Bur** — Burden numbers match col 2.
- **F3.Dis** — Discussion-based ranking matches col 3.
- **F3.Cou** — Counting scores match col 4 (with damping = 0.98 per the survey).
- **F3.Tup** — Tuples ranking matches col 5.
- **F3.hCa** — h-Categoriser scores match col 6.
- **F3.Igr** — Iterated graded (m=2, n=1) matches the (2,1)-acceptability column.

Every method except F3.Cat and F3.Bur fails today (those two rewrap; the wrap itself must produce `RankingResult` output, so even those flip from passing to failing temporarily until rewrap lands).

### F4. `tests/test_ranking_axioms.py` (new)

- **F4.1** — `abstraction(categoriser_scores, af)` returns True for the Bonzon example AF.
- **F4.2** — `cardinality_precedence(categoriser_scores, af)` returns False with a documented counter-example AF (Bonzon 2016 Table 2 row "Categoriser, CP" = NO).
- **F4.3** — `cardinality_precedence(burden_numbers, af)` returns True (Table 2 row "Burden, CP" = YES).
- **F4.4** — Coverage gate: assert that the predicate suite covers all 11 axioms named in Amgoud 2013. AST-walks the module; counts predicates; compares against a hard-coded set of axiom names. Closes P-RANK-2.

### F5. `tests/test_subjective_aspic_rename.py` (new)

- **F5.1** — `from argumentation import subjective_aspic` succeeds.
- **F5.2** — `from argumentation import value_based` raises `ImportError`. Closes P-VAF-2 by deletion (no alias, per `feedback_no_fallbacks`).
- **F5.3** — `from argumentation import vaf` succeeds, and `vaf.VAF` is the Bench-Capon dataclass — i.e., the value-based name now denotes the value-based formalism.

### F6. `tests/test_convergence_contracts_uniform.py` (new — closes P-RANK-3, owned here)

- **F6.1** — Build a non-convergent AF (an odd cycle that drives `categoriser_scores` past `max_iterations=2`). Assert `categoriser_scores(af, max_iterations=2)` returns `RankingResult` with `converged=False` — does NOT raise. Closes the `ranking.py:65` contract drift.
- **F6.2** — All seven ranking semantics share the `RankingResult` shape: a parametrized AST/typing test asserts the return annotation on each.
- **F6.3** — `RankingResult.converged` is a required field for every iterative semantics; non-iterative semantics (Burden, Tuples) hard-code `converged=True`.

(Note: WS-O-arg-gradual owns the `gradual.py`-side convergence assertions; they are not duplicated here.)

### F7. Paired sentinels — upstream + propstore (per Codex 2.18)

Per Codex 2.18 (already applied to WS-O-arg-argumentation-pkg), every upstream WS needs **two** sentinels with explicit closure conditions. A propstore commit cannot flip an upstream test; an upstream commit cannot prove the propstore pin contains the fix. Both directions are required.

**F7a. Upstream sentinel — `argumentation/tests/test_workstream_o_arg_vaf_ranking_done.py`** (new; lives in the **argumentation** repo)

- `xfail` until F1-F6 above are all green in the argumentation repo.
- Asserts the upstream behaviour shipped: `from argumentation import vaf, practical_reasoning, subjective_aspic, ranking_axioms` all succeed; `RankingResult` is importable from `argumentation.ranking`; `ranking.categoriser_scores` returns `RankingResult` with `converged` field; `value_based` is no longer importable.
- **Closure condition**: turns green when the upstream PR for Step 8 (Amgoud axioms) merges to argumentation's default branch. Closes in the **argumentation repo**.
- Independent of any propstore-side change.

**F7b. Propstore sentinel — `propstore/tests/architecture/test_argumentation_pin_vaf_ranking.py`** (new; lives in **propstore**)

- Imports the public API surface from the pinned `argumentation` package: `from argumentation import vaf, practical_reasoning, subjective_aspic, ranking_axioms`; `from argumentation.ranking import RankingResult, categoriser_scores, burden_numbers, discussion_based, counting_scores, tuples_ranking, h_categoriser, iterated_graded`.
- Exercises one paper-faithful behavioural assertion per major addition, observable from propstore (no reaching into argumentation internals):
  - VAF: build a small VAF via the public constructor; assert `successful_attacks` and `objectively_acceptable` produce paper-faithful values for one BC03 fixture.
  - Ranking: call `categoriser_scores(af, max_iterations=2)` on a non-convergent fixture; assert `converged is False` and no `RuntimeError` is raised (the harmonised contract from Codex 2.22).
  - Rename: `import argumentation.value_based` raises `ImportError` (caller-visible deletion).
- Asserts `propstore/pyproject.toml`'s argumentation pin string equals or post-dates the recorded post-Step-8 argumentation commit (resolved via a recorded commit string in this WS or via git metadata).
- **Closure condition**: turns green when `propstore/pyproject.toml`'s argumentation pin advances to a commit that contains all Step 1-8 fixes AND every behavioural assertion above passes against that pinned dependency. Closes in **propstore** when the pin bumps and the propstore suite re-runs clean.

The two-sentinel discipline ensures that a fix is genuinely reflected in propstore behavior, not merely in upstream source. A propstore PR cannot mark this WS closed by editing only the upstream sentinel (which lives in a different repo); the propstore-side pin bump and F7b turning green is the closure event for propstore.

## Production change sequence

This work lands in `../argumentation`, NOT in propstore. Per D-15, each phase ships as a PR upstream; propstore pin-bumps in a follow-up commit per phase. Each step has its own commit message of the form `WS-O-arg-vaf-ranking step N — <slug>`.

### Step 1 — Rename `value_based.py` → `subjective_aspic.py`

Mechanical rope-driven rename. Update `argumentation/__init__.py` re-export. Update every test importing `value_based`. Delete the old name with no alias. F5.1, F5.2 turn green. F5.3 still fails (no `vaf` module yet).

### Step 2 — Implement `vaf.py`

`VAF` dataclass + `successful_attacks` + `induced_af` + `objectively_acceptable` + `subjectively_acceptable` + `audiences_supporting`. Brute over `|V|!` orderings with documented `|V| > 8` warning. F1.1-F1.5, F5.3 turn green.

### Step 3 — Implement `practical_reasoning.py` (AATS slice)

AATS dataclass + AS1 + CQ5/6/11 ONLY. Out-of-scope CQs raise `NotImplementedError`. F2.1-F2.6 turn green. The remaining 14 CQs are explicitly NOT implemented in this WS (see "What this WS does NOT do").

### Step 4 — Refactor `ranking.py` to `RankingResult` (the ownership step)

`RankingResult` dataclass added. `categoriser_scores` and `burden_numbers` rewrapped to return it. `RuntimeError` at line 65 deletes. F6.1-F6.3 turn green. F3.Cat, F3.Bur turn green. **This step is the cross-stream handoff to WS-O-arg-gradual** — once `RankingResult` lands here, that WS can extend the contract pattern to gradual.py without owning the type.

### Step 5 — Implement Discussion-based, Counting

`discussion_based`, `counting_scores`. F3.Dis, F3.Cou turn green.

### Step 6 — Implement Tuples-based, h-Categoriser

`tuples_ranking`, `h_categoriser`. F3.Tup, F3.hCa turn green.

### Step 7 — Implement Iterated graded acceptability

`iterated_graded`. F3.Igr turns green.

### Step 8 — Implement `ranking_axioms.py`

11 predicates per Amgoud 2013. F4.1-F4.4 turn green.

### Step 9 — propstore pin bump

Update `pyproject.toml`'s argumentation dep pin to the released version that includes Steps 1-8. Re-run propstore's argumentation-touching test corpus (everything under `propstore/tests/` that imports `argumentation`). Address any breakage in propstore in a separate WS file if it surfaces (we don't expect any — VAF and ranking are additive — but the rename in Step 1 has propstore implications IF propstore imports `argumentation.value_based`).

Verification: `Grep "from argumentation import value_based" propstore/` should return zero matches before this WS starts. If it returns hits, those callers update in Step 9 along with the pin bump (single commit, no shim).

### Step 10 — Close gaps and gate (both repos, paired sentinels)

Update `propstore/docs/gaps.md` and the cluster-P inventory: remove the five findings (P-VAF-1, P-VAF-2, P-RANK-1, P-RANK-2, P-RANK-3) from the open list, add a `# WS-O-arg-vaf-ranking closed <sha>` line.

Upstream side (argumentation):
- Flip `argumentation/tests/test_workstream_o_arg_vaf_ranking_done.py` (F7a) from `xfail` to `pass`. This test lives in the **argumentation** repo and closes upstream behaviour.

Propstore side:
- Confirm `propstore/pyproject.toml`'s argumentation pin is on the post-Step-8 argumentation commit.
- Flip `propstore/tests/architecture/test_argumentation_pin_vaf_ranking.py` (F7b) from `xfail` to `pass` (or land it green if it was newly written at this step). This test lives in **propstore** and closes the pin / observable-behaviour gate.
- Update this WS file's STATUS line to `CLOSED <propstore-sha>`.

Per Codex 2.18, the propstore commit cannot flip the upstream test (different repo); the upstream commit cannot prove the propstore pin contains the fix. Both directions are required.

## Acceptance gates

Before declaring this WS done, ALL must hold:

- [x] `cd ../argumentation && uv run pytest tests/test_subjective_aspic.py tests/test_vaf.py tests/test_practical_reasoning.py tests/test_ranking.py tests/test_ranking_axioms.py tests/test_docs_surface.py tests/test_workstream_o_arg_vaf_ranking_done.py` passed: `41 passed in 1.03s`.
- [x] `propstore/tests/architecture/test_argumentation_pin_vaf_ranking.py` (F7b) is green in propstore against the bumped pin: `4 passed in 2.86s`, log `logs/test-runs/arg-vaf-ranking-pin-axioms-20260428-182753.log`.
- [x] `cd ../argumentation && uv run pyright src/argumentation` passed with `0 errors`.
- [x] `cd ../argumentation` full suite passed after the final axiom-surface correction: `439 passed in 27.85s`, log `argumentation/logs/post-ws-o-arg-vaf-ranking-axioms.log`.
- [x] `argumentation/src/argumentation/value_based.py` does not exist on disk; `subjective_aspic.py` does.
- [x] `argumentation/src/argumentation/vaf.py`, `practical_reasoning.py`, `ranking_axioms.py` exist with paper-anchored docstrings.
- [x] `practical_reasoning.py` docstring explicitly states "AATS slice - AS1 + CQ5/6/11 only; remaining CQs out of scope."
- [x] `argumentation/__init__.py` re-exports `vaf`, `practical_reasoning`, `subjective_aspic`, `ranking_axioms`.
- [x] `argumentation/README.md` updates: VAF section mentions `vaf` not `value_based`; ranking section lists all seven semantics; Atkinson section explicitly lists which CQs are in scope (CQ5, CQ6, CQ11) and lists missing CQs as out of scope; non-goals list unchanged.
- [x] Pushed argumentation commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908`; `propstore/pyproject.toml` and `uv.lock` pin to that pushed commit; propstore full suite passes against the new pin.
- [x] WS-O-arg-vaf/ranking property-based gates from `PROPERTY-BASED-TDD.md` are included in upstream tests: Bench-Capon Def. 5.3 VAF attack success, Atkinson CQ11 alternative promoted value, and ranking-result order properties.
- [x] `propstore/docs/gaps.md` no longer lists the five closed findings as open; residual non-scope paper surfaces are separately listed as open gaps.
- [x] `reviews/2026-04-26-claude/workstreams/WS-O-arg-vaf-ranking.md` STATUS line is `CLOSED 418d409c`.

## Done means done

Strictly enumerated, per Codex 2.23 honesty requirement:

- VAF (Bench-Capon 2003) is a first-class, paper-faithfully-tested module.
- **Atkinson 2007 AATS slice** ships exactly: AS1, CQ5, CQ6, CQ11. Nothing more from Atkinson 2007 is implemented in this WS. The remaining CQs are explicitly out of scope (see below).
- All seven ranking semantics enumerated by Bonzon 2016 ship under uniform return type `RankingResult` — owned here.
- All 11 Amgoud 2013 axioms ship as testable predicates.
- The `value_based.py` naming overload is gone — value-based now denotes value-based.
- Convergence contracts harmonized in `ranking.py` — no `RuntimeError` on non-convergence; `RankingResult.converged` is the uniform contract (this WS owns that contract; WS-O-arg-gradual extends it to `gradual.py`).
- Every paper-faithful first-failing test is green.
- The gating sentinel test has flipped from `xfail` to `pass`.
- propstore pin bump landed.

If any of the above is not true, this WS stays OPEN. No "we'll add Tuples-based later" — either it's in scope and done, or it's explicitly carved out in this file before declaring done and re-homed to a successor WS.

## Scope honesty (per Codex 2.23)

This WS deliberately implements a *partial* version of Atkinson 2007's AATS framework. The literature defines AS1 with **17 critical questions**; this WS implements **3** of them (CQ5, CQ6, CQ11). That is approximately 18% of the CQ surface. Calling this an "AATS implementation" without qualification would overclaim — the Codex round 2 finding 2.23 flagged exactly this risk.

The honest framing: **AATS slice**. A slice that:
- Demonstrates the AS1 dataclass and value-transition machinery work end-to-end.
- Implements three CQs that exercise the three structurally distinct attack mechanics (alternative-action-same-value, value-tradeoff, target-state-failure).
- Hard-fails (`NotImplementedError`) on every other CQ so consumers cannot silently believe coverage they don't have.

The CQs explicitly **NOT** implemented in this WS are tracked here for a future workstream:
- CQ1 — Are the believed circumstances true?
- CQ2 — Does the action have the stated consequences?
- CQ3 — Does the consequence promote the value?
- CQ4 — Are there alternative actions promoting the same value? (note: distinct from CQ5; CQ4 is alternative-action-existence; CQ5 is alternative-action-as-attacker)
- CQ7 — Does doing the action have side effects?
- CQ8 — Does the action affect different agents differently?
- CQ9 — Are the circumstances as described (skeptical re-asking of CQ1)?
- CQ10 — Is the consequence in fact possible?
- CQ12+ — Remaining CQs about goal-formation, value-rankings under disagreement, action-feasibility under uncertainty, etc.

Total deferred surface: 14 of 17 CQs. A future workstream (working title: WS-O-arg-aats-completion) would close that surface when a propstore consumer demonstrates a need.

The Bonzon ranking work in this WS, by contrast, is **complete coverage**: all six ranking-based semantics enumerated by the Bonzon 2016 survey ship; all 11 Amgoud 2013 axioms ship as predicates. No partiality there.

## Additional paper-derived residuals after image reread

The post-compaction image reread did not reopen this workstream, but it did surface follow-up work that must not be silently claimed here:

- Bench-Capon 2003 pp. 438-447 define argument chains, lines of argument, parity-based objective/subjective/indefensible classifications, two-value cycle corollaries, and fact-as-highest-value uncertainty handling. This WS implements the VAF/AVAF defeat and acceptance kernel, not that later algorithmic layer.
- Oikarinen 2010 remains outside this WS. Its strong/local equivalence kernels (`s`, `a`, `g`, `c`, and `c-local`) and theorem-backed equivalence checks are still tracked as an open gap in `docs/gaps.md`.

Sizing estimate: ~3-6 weeks of focused upstream work, with most time going to:
- Bonzon 2016 careful re-reading and cross-checking the survey's worked examples against the original semantics papers (Cayrol-Lagasquie-Schiex tuples, Pu h-Categoriser, Grossi-Modgil iterated graded — three different paper traditions to align).
- The Amgoud 2013 axiom predicate suite — 11 axioms each requires a careful spec and at least one documented YES and one documented NO test case.
- Atkinson 2007 AATS slice — even the 3-CQ slice is ~250 LOC of careful dataclass construction and value-transition machinery.

The Bench-Capon VAF kernel itself is small (< 200 LOC) — that is not where time goes. The time sink is the comparison-table fidelity in F3 and F4 and the convergence-contract harmonization sweep.

## Cross-stream notes

- **Depends on `WS-O-arg-argumentation-pkg`** — the cluster-P HIGH bugs (e.g., `dung.py:582-585` ideal-extension union, `aspic_encoding.py:165` ASP id scheme, `af_revision.py:60-92` 2^n materialization) land first. VAF construction calls `induced_af -> ArgumentationFramework`; we don't want to be debugging atop a known-broken Dung kernel.

- **Blocks `WS-O-arg-gradual`** — that WS consumes `RankingResult` (owned here) and the convergence-contract pattern (owned here). It cannot start its own changes to `gradual.py` until Step 4 of this WS lands.

- **Does NOT depend on WS-A (schema fidelity)** — this is upstream-package work, no propstore schema interaction. Can run in parallel with WS-A through Step 8. Step 9 (propstore pin bump) only requires propstore to be in a state where adding the new dep version doesn't conflict with WS-A's schema work; in practice these are independent.

- **Feeds into D-8** — once `prior_base_rate` becomes an Opinion produced by the argumentation kernel (per the meta-paper rule pipeline in WS-K), the choice of ranking semantics is a *configurable knob*. This WS makes seven knobs available; WS-K decides which knob propstore turns by default.

- **Feeds into propstore semantic configuration** — propstore's `praf/engine.py:160` consumes ranking output; once seven semantics are available, propstore needs a config knob exposing the choice. That config-knob work is propstore-side (a follow-up WS, NOT this one). This WS only ensures the choices exist upstream.

## What this WS does NOT do

- Does NOT add propstore-side ranking selection UX. Engineering the config knob is a follow-up.
- **Does NOT implement full Atkinson 2007 AATS.** AS1 + CQ5 + CQ6 + CQ11 only. Missing CQs (CQ1, CQ2, CQ3, CQ4, CQ7, CQ8, CQ9, CQ10, CQ12, CQ13, CQ14, CQ15, CQ16, CQ17 — that is, 14 of the 17 critical questions) are explicitly out of scope and tracked for a future workstream. Calling `attack_via_critical_question` with any CQ outside {CQ5, CQ6, CQ11} raises `NotImplementedError`.
- Does NOT implement Walton-Reed 2002 broader argument schemes. Out of cluster P scope.
- Does NOT touch `aspic.py` ASPIC+ kernel. The `subjective_aspic.py` rename is a file move; no logic change.
- Does NOT implement value-based ABA or value-based ADF. ABA/ADF live in WS-O-arg-aba-adf (Group A); cross-pollinating values in is a future direction, not this WS.
- Does NOT delete the existing Categoriser/Burden implementations. They get rewrapped in `RankingResult`; the math is unchanged.
- Does NOT engage with Coste-Marquis weighted preferred/stable (cluster-P weighted gap). Belongs to a separate WS focused on weighted AFs (Dunne α/γ + Coste-Marquis weighted) — flagged here for index updates.
- Does NOT modify `gradual.py`. WS-O-arg-gradual extends the convergence-contract pattern there, consuming `RankingResult` from here. The handoff is one-way.

## Verification before starting work

The coder kicking this WS off MUST verify the cluster-P observations are still accurate at HEAD of `../argumentation` before writing tests:

1. Confirm `argumentation/src/argumentation/ranking.py:33` is `categoriser_scores` and `:82` is `burden_numbers`.
2. Confirm `argumentation/src/argumentation/value_based.py` exists and its content is Wallner 2024 ASPIC+ filtering, not Bench-Capon VAF.
3. Confirm no module named `vaf.py`, `practical_reasoning.py`, or `ranking_axioms.py` exists.
4. Confirm `argumentation/src/argumentation/ranking.py:65` raises `RuntimeError` on non-convergence; confirm `gradual.py:133` returns `converged=False` on non-convergence (the divergent contract).
5. Confirm `RankingResult` does not yet exist in `ranking.py` (the dataclass is owned by this WS and lands new).
6. Run `cd ../argumentation && uv run pytest 2>&1 | tee logs/baseline-pre-ws-o-arg-vaf-ranking.log` and commit the log. This is the regression baseline for the acceptance gate "no NEW failures vs master baseline."

If any of (1)-(5) is no longer accurate (e.g., someone added a `vaf.py` already, or `RankingResult` already exists), the coder pauses and asks Q how to reconcile — per `feedback_friction_not_notes`, do not improvise around the discrepancy. In particular: if `RankingResult` already exists, that means WS-O-arg-gradual or another WS has crossed the ownership boundary; surface this immediately rather than working around it.

## Papers / specs referenced

Direct paper-faithfulness pins (every test must cite):
- Bench-Capon 2003 — VAF foundations, Defs 5-7, worked Example 1
- Atkinson 2007 — AATS, AS1, CQ5/6/11 only (slice)
- Bonzon 2016 — survey, §3 worked examples, Tables 1 and 2
- Amgoud-Ben Naim 2013 — Discussion-based, ranking-axiom set
- Pu et al. 2014 — Counting, h-Categoriser
- Cayrol-Lagasquie-Schiex 2005 — Tuples-based
- Grossi-Modgil 2015 — Iterated graded acceptability
- Amgoud 2017 — weighted argumentation acceptability axioms (cross-reference)
- Baroni 2019 — gradual argumentation principles (cross-reference)
- Al-Anaissy 2024 — impact measures (already partially implemented in `gradual.py`; cross-reference for axiom suite)
- Wallner 2024 — VAF in ASPIC+ (anchors `subjective_aspic.py` after rename)

Cross-cutting:
- D-15, D-16 (DECISIONS.md) — upstream-only fix policy + Group C scope
- Codex round 2 finding 2.22 — ranking convergence ownership locked here
- Codex round 2 finding 2.23 — Atkinson scope honesty (slice not implementation)
- Codex round 2 finding 2.1 — owner line "Codex implementation owner + human reviewer required"
- cluster-P-argumentation-pkg.md — gap inventory, especially §"Ranking" and §"Missing features the literature reaches further on"
- Global memory: `feedback_no_fallbacks` (no shims), `feedback_citations_and_tdd` (cite at docstring + inline + test), `feedback_update_callers` (rename means update callers, not alias), `feedback_imports_are_opinions` (every imported KB row is defeasible — VAF audience choice is a defeasible claim, not truth)
