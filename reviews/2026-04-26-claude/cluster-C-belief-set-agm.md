# Cluster C: belief_set (AGM, iterated, IC merge, AF revision)

Reviewer: analyst (Opus 4.7 1M context), 2026-04-26.
Mandate: find postulate gaps, claim-vs-code mismatches, missing constructions, complexity issues.

## Scope

In-scope source modules (`propstore/belief_set/`): `__init__.py` (36 LOC), `core.py` (115), `language.py` (138), `agm.py` (174), `iterated.py` (100), `entrenchment.py` (36), `ic_merge.py` (203). README in same dir. Total 802 LOC.

In-scope tests:
- `tests/test_belief_set_postulates.py`
- `tests/test_belief_set_iterated_postulates.py`
- `tests/test_af_revision_postulates.py`
- `tests/test_belief_set_docs.py`
- `tests/revision_assertion_helpers.py`

In-scope docs:
- `docs/belief-set-revision.md`
- `docs/af-revision.md`
- `docs/ic-merge.md`

**Important scope correction observed by reading the code (not assumed):**
The task lists `propstore/belief_set/af_revision.py`, but no such source file exists. Only a stale `__pycache__/af_revision.cpython-313.pyc` remains. Commit `ad7a4cdc` ("Move AF revision kernel to argumentation") moved the source to `argumentation.af_revision` (imported by `tests/test_af_revision_postulates.py:8`). I therefore treat AF revision as out-of-package but still review the **tests** and **docs** since they were named in scope.

`tests/revision_assertion_helpers.py` is unrelated to belief_set — it builds `AssertionAtom`s for `support_revision` (a separate package). It does not exercise any AGM-style postulate.

---

## AGM postulate coverage matrix

Notation: AGM 1985 paper uses (-1)..(-8) for contraction (often called K-1..K-8) and (+1)..(+8) for revision (often called K*1..K*8). The propstore tests label the test functions with mixed naming. I use the paper's symbols.

### Revision postulates (K*1 — K*8)

| Postulate | Statement | Coverage |
|---|---|---|
| K*1 (closure) | K*φ is a theory | **Trivially satisfied by construction** — `BeliefSet.__post_init__` (core.py:18-25) and `revise` returns a `BeliefSet`. Not explicitly asserted. |
| K*2 (success) | φ ∈ K*φ | Tested at `tests/test_belief_set_postulates.py:110` (`assert result.belief_set.entails(a)`). **Hidden bug**: when φ is unsatisfiable in the alphabet, `revise` (`agm.py:84-85`) silently returns `working_state` unchanged, so `K*⊥` still entails the original belief set, NOT ⊥. The test escapes this via `assume(_belief(a).is_consistent)` at `test_belief_set_postulates.py:106`. K*2 is therefore **only conditionally tested**. |
| K*3 (expansion inclusion) | K*φ ⊆ K + φ | Tested at line 111 (`theory_subset(result.belief_set, expansion)`). |
| K*4 (preservation) | If ¬φ ∉ K, then K + φ ⊆ K*φ | Tested at line 112-113. |
| K*5 (consistency) | K*φ is consistent unless ⊨¬φ | Tested at line 114 (`assert result.belief_set.is_consistent`) — but again gated by `assume(_belief(a).is_consistent)` so the case ⊨¬φ is never exercised. **Coverage gap**. |
| K*6 (extensionality) | If ⊢φ↔ψ then K*φ = K*ψ | Tested at line 118-120 using a single equivalence pair (`a` vs `conjunction(a, TOP)`). Weak — does not vary over equivalent formula pairs. |
| K*7 (superexpansion) | K*(φ∧ψ) ⊆ (K*φ) + ψ | Tested at line 122-124. |
| K*8 (subexpansion) | If ¬ψ ∉ K*φ then (K*φ)+ψ ⊆ K*(φ∧ψ) | Tested at line 125-126. |

**Verdict:** K*1, K*2 (conditional), K*3, K*4, K*5 (conditional), K*6 (weak), K*7, K*8 all present. None labelled individually — single mega-test means a violation cannot be attributed.

### Contraction postulates (K-1 — K-8)

| Postulate | Statement | Coverage |
|---|---|---|
| K-1 (closure) | K÷φ is a theory | Trivial by construction. |
| K-2 (inclusion) | K÷φ ⊆ K | Tested at `tests/test_belief_set_postulates.py:137`. |
| K-3 (vacuity) | If φ ∉ K then K÷φ = K | Tested at line 138-139. |
| K-4 (success) | If ⊬φ then φ ∉ K÷φ | Tested at line 140-141. |
| K-5 (recovery) | K ⊆ Cn(K÷φ ∪ {φ}) | Tested at line 143-144. |
| K-6 (extensionality) | If ⊢φ↔ψ then K÷φ = K÷ψ | **MISSING.** No assertion that `full_meet_contract(state, a) ≡ full_meet_contract(state, equivalent_a)`. |
| K-7 (conjunction inclusion) | K÷φ ∩ K÷ψ ⊆ K÷(φ∧ψ) | **MISSING.** |
| K-8 (conjunction vacuity) | If φ ∉ K÷(φ∧ψ) then K÷(φ∧ψ) ⊆ K÷φ | **MISSING.** |

Plus Harper identity (Alchourron 1985 p.513, observation 2.3): K÷φ = K ∩ K*¬φ — tested at line 146-147.

**Verdict:** Basic K-1..K-5 + Harper covered. **Supplementary K-6, K-7, K-8 NOT TESTED.** No explicit note that they are skipped.

### Cn properties (consequence operator)

`test_agm_1985_cn_is_inclusive_monotonic_and_idempotent` (line 86-96) checks:
- inclusion: `base.entails(a)` ✓
- idempotence: `cn().equivalent(cn().cn())` ✓ (trivially: `cn()` returns `self`, core.py:58-59)
- some monotonicity-flavored assertion with conjunction, but the actual Tarskian monotonicity (X⊆Y ⇒ Cn(X)⊆Cn(Y)) is not tested.

### Epistemic entrenchment (Gärdenfors-Makinson 1988 EE1-EE5)

| Postulate | Statement (paper, p.89) | Coverage |
|---|---|---|
| EE1 transitivity | A≤B, B≤C ⇒ A≤C | Tested at `test_belief_set_postulates.py:183-184`. |
| EE2 dominance | A⊨B ⇒ A≤B | Tested at line 185-186. |
| EE3 conjunctiveness | A≤A∧B or B≤A∧B | Tested at line 187. |
| EE4 minimality | If K≠Cn(∅), then A∉K iff ∀B A≤B | Tested at line 189-190 over the **finite `FORMULAS` sample**, not over the Lindenbaum algebra. **Severely weak.** |
| EE5 maximality | If ∀B B≤A, then ⊨A | Tested at line 192-193 — same weakness. |

The two bridging conditions (C≤) and (C-) from Gärdenfors-Makinson 1988 (notes.md p.89-90) are **NOT TESTED**. The paper's representation theorem (Theorems 3-6) — that EE1-EE5 generates contraction satisfying K-1..K-8 — is not exercised: there is no test that the entrenchment derived from a Spohn state actually agrees with `full_meet_contract`'s outcomes via (C-).

---

## Iterated revision (DP) coverage

Source: `iterated.py` (100 LOC), `agm.py` `revise` (lines 73-100).

### Darwiche-Pearl 1997 postulates (paper notes.md p.11)

| Postulate | Operator under test | Coverage |
|---|---|---|
| C1 (α⊨μ ⇒ (Ψ°μ)°α ≡ Ψ°α) | `revise` only | `test_belief_set_postulates.py:163-164` |
| C2 (α⊨¬μ ⇒ (Ψ°μ)°α ≡ Ψ°α) | `revise` only | line 165-166 |
| C3 (Ψ°α⊨μ ⇒ (Ψ°μ)°α⊨μ) | `revise` only | line 167-168 |
| C4 (Ψ°α⊬¬μ ⇒ (Ψ°μ)°α⊬¬μ) | `revise` only | line 169-170 |
| C1-C4 for `lexicographic_revise` | — | **NOT TESTED.** Only "places all input worlds first" + internal preorder preservation are checked (`test_belief_set_iterated_postulates.py:43-61`). |
| C1-C4 for `restrained_revise` | — | **NOT TESTED.** |

### Modified AGM postulates (R*1-R*6) — DP §3

The paper's R*4 (`Ψ1=Ψ2 ∧ μ1≡μ2 ⇒ Ψ1°μ1 ≡ Ψ2°μ2`) requires identity of the EPISTEMIC STATE, not just equivalence of belief sets. **No test enforces this distinction.** Two `SpohnEpistemicState`s with different ranks but the same `belief_set` should still revise differently — this property is not exercised, which means a buggy implementation that collapses to belief-set identity would pass all current tests.

### Booth-Meyer 2006 admissibility

| Postulate | Coverage |
|---|---|
| Admissibility (P): if K*α⊬¬μ then (K*μ)*α ⊨ α whenever K*α ⊨ α | `test_belief_set_iterated_postulates.py:84-99` checks ONE direction. |
| AR1, AR2, AR3 / RR-specific axioms (admissible-restrained family) | **NOT TESTED.** Booth's notes.md only mentions the (P) admissibility criterion explicitly; the analyst could not enumerate further postulates from the notes file alone. **Open question for Q below.** |

### Bullet operator faithfulness to DP Theorem 14

DP's bullet operator (notes.md p.15) shifts ¬μ-worlds by `κ(ω) - κ(¬μ) + m` with `m = κ(¬μ) + 1` (i.e., the ¬μ block is rebased and pushed one slot above the new μ block). The implementation in `agm.py:88-94` does:

```python
if formula.evaluate(world):
    revised_ranks[world] = current_rank - min_formula_rank
else:
    revised_ranks[world] = current_rank + 1
```

This is **not** the (μ, m)-conditionalization with `m = κ(¬μ) + 1`. The implementation:
- shifts μ-worlds down by `min_formula_rank` ✓ matches DP
- shifts ¬μ-worlds up by `+1` regardless of `κ(¬μ)` ✗ does NOT match DP (which subtracts `κ(¬μ)` from the ¬μ ranks too)

For initial states where `κ(¬μ) = 0` (the most-plausible block contains a ¬μ world), the two coincide. Otherwise they diverge — and after one revision, the post-state's `κ(¬μ)` is generally not 0, so the second iteration's DP equations produce different rank vectors than this code. **This is a high-severity bug (see Bugs section) — the postulate tests cover C1-C4 only on the resulting belief set, not on conditional belief equivalence, so the divergence is invisible at the postulate gate.**

### CR1-CR4 (representation theorem, DP p.14)

| Condition | Coverage |
|---|---|
| CR1: ω1,ω2⊨μ ⇒ (ω1≤Ψω2 iff ω1≤Ψ°μω2) | **NOT TESTED.** |
| CR2: ω1,ω2⊨¬μ ⇒ (ω1≤Ψω2 iff ω1≤Ψ°μω2) | **NOT TESTED** for `revise`. Tested for `lexicographic_revise` and `restrained_revise` (the "internal preorder preservation" tests). |
| CR3: ω1⊨μ, ω2⊨¬μ, ω1<Ψω2 ⇒ ω1<Ψ°μω2 | **NOT TESTED.** |
| CR4: ω1⊨μ, ω2⊨¬μ, ω1≤Ψω2 ⇒ ω1≤Ψ°μω2 | **NOT TESTED.** |

This is a major gap: CR1-CR4 are the SEMANTIC counterparts of C1-C4 and would catch the bullet-operator bug above directly.

---

## IC merge coverage (Konieczny-Pino-Pérez 2002)

Source: `ic_merge.py`. Tests in `test_belief_set_postulates.py:196-249`.

| Postulate | Statement (notes.md p.4) | Coverage |
|---|---|---|
| IC0 | Δμ(Ψ) ⊨ μ | line 206 ✓ |
| IC1 | μ consistent ⇒ Δμ(Ψ) consistent | line 207 ✓ |
| IC2 | ⋀Ψ ∧ μ consistent ⇒ Δμ(Ψ) ≡ ⋀Ψ ∧ μ | line 209-211 ✓ |
| IC3 | Ψ1≡Ψ2 ⇒ Δμ(Ψ1) ≡ Δμ(Ψ2) | line 213-216 (one syntactic variant only) |
| IC4 (fairness) | φ1⊨μ, φ2⊨μ ⇒ Δμ({φ1,φ2}) ⊬ ¬φ1 | **NOT TESTED.** |
| IC5 | Δμ(Ψ1) ∧ Δμ(Ψ2) ⊨ Δμ(Ψ1⊔Ψ2) | line 247 ✓ |
| IC6 | Δμ(Ψ1) ∧ Δμ(Ψ2) consistent ⇒ Δμ(Ψ1⊔Ψ2) ⊨ Δμ(Ψ1) ∧ Δμ(Ψ2) | line 248-249 ✓ |
| IC7 | Δμ1(Ψ) ∧ μ2 ⊨ Δμ1∧μ2(Ψ) | line 222 ✓ (with `tighter_mu = conjunction(mu, P)`) |
| IC8 | Δμ1(Ψ) ∧ μ2 consistent ⇒ Δμ1∧μ2(Ψ) ⊨ Δμ1(Ψ) | line 223-224 ✓ |
| Maj (majority) | ∃n. Δμ(Ψ1 ⊔ Ψ2^n) ⊨ Δμ(Ψ2) | **NOT TESTED.** Σ is claimed to be a majority operator (Konieczny notes p.13, Theorem 4.2). |
| Arb (arbitration) | (cf. notes.md p.5) | **NOT TESTED.** GMax is claimed to be an arbitration operator (Theorem 4.14). |

**Verdict:** 7 of 9 IC postulates tested (IC0-IC3 partially, IC5-IC8 fully). **IC4 and the operator-class-distinguishing postulates (Maj, Arb) are absent.** Without those, the code cannot claim to implement either a majority or an arbitration operator faithfully, only a "quasi-merging-or-better" operator.

`docs/ic-merge.md` line 16-19 claims SIGMA implements `Σ` and GMAX implements `GMax` from Konieczny-Pino-Pérez. The doc does not say "majority operator" or "arbitration operator" by name, so the gap is one of *under-claim*, but `_score_world` (`ic_merge.py:80-86`) clearly maps SIGMA → sum (Σ) and GMAX → sorted-descending vector with lex compare (GMax) faithfully to the paper's definitions (notes.md p.12, p.17).

---

## AGM-meets-AF coverage

Source: `argumentation.af_revision` (out of this package; tests in `tests/test_af_revision_postulates.py`).

### Baumann-Brewka 2015 (notes.md p.86-105, p.147)

| Postulate / theorem | Coverage |
|---|---|
| K1-K6 expansion postulates for Dung logics | Test `test_baumann_brewka_2015_kernel_union_expansion_success_and_inclusion` (lines 63-77) checks: `base.arguments ≤ expanded.arguments`, `new.arguments ≤ expanded.arguments`, `expanded == stable_kernel(union)`, idempotence on second call. This corresponds to K2 (success) and K3 (inclusion) and a form of idempotence. **K1 (closure), K4 (vacuity), K5 (consistency), K6 (extensionality) NOT EXPLICITLY TESTED.** |
| R1-R8 revision postulates for AFs | **NOT TESTED.** Baumann-Brewka 2015's notes.md p.105 lists R1-R8 for revision. The implementation has no AF revision operator (only kernel-union expansion + Diller-style extension revision, which is not the same surface). |
| Theorem 1 (kernel-union expansion satisfies K1-K6) | Partially tested via the `==` check above. |
| Representation theorem for revision (faithful assignment) | **NOT TESTED.** Per notes.md p.155 the paper itself does not provide a concrete revision operator, so test absence is partly excusable. |

### Diller 2015

| Property | Coverage |
|---|---|
| P*1-P*6 formula revision | The test name says "P*1-P*6" but the body checks ~3 properties: success (`_satisfies(extension, formula)`), syntax-irrelevance via `__top_guard__` projection, and minimality. The label is **misleading** — the 6 individual postulates are not enumerated. |
| A*1-A*6 framework revision | Same situation — name claims 6 postulates, tests check ~3. |

### Cayrol et al. 2014

`test_cayrol_2014_grounded_addition_is_never_restrictive_or_questioning` (line 122-131) tests ONE classification implication. The paper's full taxonomy (decisive/expansive/conservative/altering/destructive/restrictive/questioning) and their characterization conditions are not exhaustively tested.

### Coste-Marquis 2007 merging Dung frameworks

**ZERO coverage.** No source, no tests, no docs mention. This was explicitly listed in the cluster scope.

### Baumann 2010 expansion / enforcement

Only "kernel-union expand" is tested. The paper's enforcement results (Theorems 2-4 in the notes) — conservative/liberal, strong/weak, single-argument enforcement — are NOT implemented or tested. `cayrol_2014_classify_grounded_argument_addition` is adjacent but not the same operator.

### Baumann 2019 AGM contraction for Dung

**ZERO coverage.** No `agm_contract` for AF anywhere. Notes.md correctly observes (p.16-17) that recovery cannot hold and the Harper identity fails for AFs — but the project does not even document this as a known not-yet item in `docs/af-revision.md`.

### Diller 2015 extension-based belief revision (ratio of paper to test)

Diller's framework has many more properties than the single P*-style minimality test. Not exhaustively reviewed here — listing as gap.

### Bonanno 2007 / 2010, Boella 2009, Doutre 2018, Rotstein 2008

No implementation. No tests. The notes files mention them as conceptual links only. These are gaps if propstore intends to claim coverage of "AF dynamics" — but the cluster scope does not state that the project intends to implement them. **Treat as inventory, not bugs.**

---

## Bugs

### HIGH

**HIGH-1: `revise` violates K*2 (success) when φ is unsatisfiable.**
Location: `propstore/belief_set/agm.py:84-95`.

```python
satisfying = tuple(world for world in worlds if formula.evaluate(world))
if not satisfying:
    result_state = working_state          # returns input UNCHANGED
else:
    ...
```

When `formula` is `BOTTOM` (or any contradiction over the alphabet), `revise` returns the original state. The resulting `belief_set` is the input belief set, which (if non-empty) does NOT entail `BOTTOM`. K*2 is violated. The standard AGM treatment for revision by ⊥ is either to define K*⊥ = K_⊥ (the inconsistent theory) or to leave it explicitly undefined. The current implementation silently violates K*2.

The postulate test (`test_belief_set_postulates.py:101-126`) escapes this via `assume(_belief(a).is_consistent)`. Hypothesis therefore never explores the bug.

**HIGH-2: `revise` does not implement DP's bullet operator faithfully.**
Location: `propstore/belief_set/agm.py:88-94`.

The DP bullet operator (`paper/Darwiche_1997.../notes.md` p.15) is `(κ • μ)(ω) = κ(ω) - κ(μ)` if ω⊨μ else `κ(ω) + 1`. This is `(μ, m)`-conditionalization with `m = κ(¬μ) + 1`, which expands to `(κ(ω) - κ(¬μ)) + κ(¬μ) + 1 = κ(ω) + 1` ONLY if you treat the `+1` as the post-shift offset above the new μ-block.

DP's actual definition (notes.md p.15, equation between Theorems 13 and 14, also `paper/Darwiche_1997.../notes.md` line 144-148):

```
(κ ∘ μ)(ω) = κ(ω) - κ(μ)             if ω⊨μ
             κ(ω) - κ(¬μ) + (κ(¬μ)+1)  if ω⊨¬μ
           = κ(ω) + 1                   if ω⊨¬μ      ✓ matches code
```

So the algebra works out and the code IS correct as a one-shot operator. Demoting from HIGH to MED-but-deserves-checking — but only because `min_rank=0` is renormalised on every state construction (`agm.py:38-43`). After renormalisation `κ(¬μ) ∈ {0, ..., max_rank}` and the `+1` shift is always relative to current ranks — i.e., the +1 increment is the "one slot above the previous max" semantic only if we then renormalise. Renormalisation happens in `SpohnEpistemicState.__post_init__`. So the operator is faithful AFTER normalisation.

**Downgrading HIGH-2 to MED**: faithful but very fragile — the +1 step assumes immediate normalisation. Documenting this would prevent the next refactor from breaking it.

**HIGH-3: `full_meet_contract` discards epistemic state.**
Location: `propstore/belief_set/agm.py:117-122`.

```python
contracted = state.belief_set.intersection_theory(revised_by_negation.belief_set)
return RevisionOutcome(
    belief_set=contracted,
    state=SpohnEpistemicState.from_belief_set(contracted),  # rebuild from scratch
    ...
)
```

`SpohnEpistemicState.from_belief_set` (`agm.py:54-62`) assigns rank 0 to all models and rank 1 to all non-models. **All entrenchment information from before contraction is lost.** This means iterated contractions degenerate to a flat 2-level ranking after the first call, which violates DP-style preservation under contract-then-revise sequences. Not detected by any test because no test does iterated contraction.

**HIGH-4: `_distance_to_formula` cache is keyed on `id(formula)`.**
Location: `propstore/belief_set/ic_merge.py:167-193`.

```python
key = (id(formula), signature)
```

The comment at line 190 claims "the entry holds a strong formula reference, so id reuse cannot alias a later formula while the cache entry remains live." This is true for entries that survive — but `popitem(last=False)` at line 192 evicts the OLDEST entry, releasing the formula reference, after which Python may recycle that `id`. The next lookup using the recycled id will hit a *different* cached entry (because the evicted one is gone) and recompute correctly — but the danger sits one step away: any caller holding a non-cached formula whose id matches a cached id will get the wrong cached entry returned (`cached.formula is formula` saves you, but only because of the strong-ref check, which the comment correctly identifies).

The bigger issue: **per-process leak.** With formulas constructed inside loops, `_DISTANCE_FORMULA_CACHE_MAX_SIZE = 128` is reached almost immediately. The key lookup is `(id, frozenset)` so all keys differ; no genuine cache hits. Switch to `(formula, signature)` since `Formula` dataclasses are `frozen=True` and hashable.

### MED

**MED-1: K-6, K-7, K-8 contraction postulates are not tested.**
See matrix above. The supplementary contraction postulates characterise transitively relational partial-meet (Alchourron 1985 Corollary 4.5) and are non-trivial. `full_meet_contract` should satisfy K-7 and K-8 (full-meet is transitively relational by construction — Alchourron 1985 p.525) and K-6 (extensionality). All three should be testable; they are not.

**MED-2: IC4 fairness postulate is not tested.**
See matrix above. Without IC4, the operator could systematically discard one source. Easy to test: `assume φ1⊨μ ∧ φ2⊨μ; assert not result.entails(negate(φ1))`.

**MED-3: CR1-CR4 (DP semantic counterparts) are not tested for `revise`.**
See iterated section. These would directly catch ordering bugs that C1-C4 may miss because C1-C4 only constrain BELIEF SET equivalence on iterated calls, not the underlying ranking.

**MED-4: Test labels claim more than they test.**
- `test_diller_2015_p_star_1_p_star_6_formula_revision` claims 6 postulates, asserts 3 properties.
- `test_diller_2015_a_star_1_a_star_6_framework_revision` similarly.
- `test_konieczny_pino_perez_2002_ic0_ic3_and_ic7_ic8` claims IC0-3 and IC7-8 — actually delivers (IC4 missing).
- `test_alchourron_gardenfors_makinson_1985_revision_k_star_postulates` does NOT enumerate K*1..K*8 individually — combined assertion graveyard.

If any postulate fails, the test report says "this giant test failed" and the bisection cost is paid by Q.

**MED-5: `_score_world` silently strips infinite distances.**
Location: `ic_merge.py:81`.

```python
finite_distances = tuple(distance for distance in distances if not math.isinf(distance))
```

If a profile member is unsatisfiable in `signature` (no models), `_distance_to_formula` returns `math.inf`. The current code drops these from the sum/max, treating an unsatisfiable source as if it contributed 0. Konieczny-Pino-Pérez's IC merging is undefined in this case (see the paper's `mod(φ)` convention — distance from any world to a φ with no models is undefined). Either raise, or document that unsatisfiable profile members are silently dropped.

**MED-6: `EpistemicEntrenchment._negation_rank` returns `inf` for tautologies.**
Location: `entrenchment.py:34-36`.

The countermodels of a tautology are empty, so `min(state.ranks[world] for world in countermodels)` would error; the code returns `float("inf")` instead. EE5 says only tautologies are maximally entrenched; the code's encoding makes tautologies trivially exceed all other formulas in `_negation_rank`. That's correct semantics for EE5, but the test at `test_belief_set_postulates.py:192-193` only asserts the ⇒ direction (max ⇒ tautology). The ⇐ direction (tautology ⇒ max) is not tested explicitly — it follows from `inf > anything`, but a typo replacing `inf` with `max(rank for...)+1` would silently weaken the property.

### LOW

**LOW-1: `equivalent` requires importing `BeliefSet` lazily inside the function.**
Location: `language.py:135-138`. Circular import workaround. Works, but flags an architectural smell — `equivalent` belongs in `core.py` or `language.py` should not need it.

**LOW-2: `BeliefSet.cn()` returns `self`.**
`core.py:58-59`. Models-based representation IS already in Cn-form, so `cn()` is the identity. Test asserts `cn().equivalent(cn().cn())`. Trivially true. No actual closure operator is invoked — fine for finite extensional rep, but a future refactor that distinguishes "syntactic representation" from "Cn closure" would silently break.

**LOW-3: `from_belief_set` makes inconsistent belief sets impossible to lift.**
`agm.py:54-62`. If `belief_set.models` is empty, every world is non-model and gets rank 1. The min_rank in `__post_init__` is then 1, which gets subtracted, producing all-zero ranks — meaning the resulting `belief_set` property returns ALL worlds (the tautology), not the inconsistent theory. This is a representation-theoretic bug for the inconsistent case. Probably never hit in practice (assumes `is_consistent`), but undefended.

**LOW-4: `_format_timestamp` strips sub-second precision.**
`agm.py:140-141`. `strftime("%Y-%m-%dT%H:%M:%SZ")` loses microseconds. Tests that hash provenance might collide if two operations occur within one second. Cosmetic.

**LOW-5: docs string-presence tests do not cover umlauts.**
`tests/test_belief_set_docs.py:11` asserts `"Gardenfors" in text`. The actual paper directory uses "Gärdenfors_1988_..." (with umlaut). A faithful citation in the docs would FAIL this test. The test is enforcing an ASCII-stripped author name — Q should decide whether to change the test or document the convention.

**LOW-6: `revision_assertion_helpers.py` is not a belief-set helper.**
The file's name suggests it's for `tests/test_belief_set_*.py`, but it imports from `propstore.support_revision` and constructs `AssertionAtom` (different concept). No belief-set test imports it. Misnamed or stranded.

---

## Algorithmic concerns

1. **Exponential blow-up in alphabet size.** `BeliefSet.all_worlds(alphabet)` materialises 2^|alphabet| worlds. Every revise/contract/merge call computes this. With ALPHABET = {p,q,r} (size 3) the tests use 8 worlds; an alphabet of size 20 is 1M worlds and would OOM. **No graceful degradation, no warning.** `extend_state` (`agm.py:125-133`) iterates `|old_worlds| × 2^|extras|`. Every call to `revise` with a formula whose `atoms()` contains a new atom triggers exponential extension.

2. **Naïve enumeration in `_distance_to_formula`'s capped path.** `ic_merge.py:148-164` iterates `BeliefSet.all_worlds(signature)` linearly with an early-out at `examined >= max_candidates`. For `signature` of size N it's O(2^N) per call. Cache only helps the uncapped path.

3. **`merge_belief_profile` is O(2^|sig| × |profile|).** No pruning by current best-score, no branch-and-bound, no model-counting tricks. For small alphabets the tests pass quickly, but the operator does not scale.

4. **`_dense_ranks` in `iterated.py:84-89`.** Sorts the value set then maps. Fine for small alphabets, but uses `set(keys.values())` then `sorted(...)`, creating two passes — minor.

5. **`SpohnEpistemicState.__post_init__` rebuilds the entire ranks dict on every construction.** Combined with `from_ranks` returning a new state, every `revise` call does O(2^|sig|) dict construction at least twice (once in `extend_state`, once in `from_ranks`).

6. **No memoisation across calls in `extend_state`.** Same alphabet-extension is recomputed for every revise.

7. **No anytime/budget integration in `agm.py` or `iterated.py`.** Only `ic_merge.py` exposes `EnumerationExceeded`. The whole revision surface lacks a "give up after N worlds" path.

---

## Missing constructions

From Alchourron 1985 (notes.md p.512):

- **Partial-meet contraction** (notes.md "K-x = ∩γ(K⊥x)"): not implemented.
- **Selection function abstraction** (`γ`): not implemented.
- **Maxichoice contraction** (γ singleton): not implemented.
- **Remainder set computation** (`K⊥x`): not implemented.
- **Levi identity** as an explicit composable operator (`revise = expand ∘ contract ∘ negate`): not exposed. The implementation has direct DP bullet revision; if Q wants to swap in a different contraction (e.g. partial-meet), there is no Levi-glue.

From Gärdenfors-Makinson 1988 (notes.md p.89-90):

- **Conditions (C≤) and (C-)** bridging entrenchment to contraction: not implemented as operators. `EpistemicEntrenchment` exposes `leq` only.
- **Contraction derived from entrenchment** (Theorem 5 in Gärdenfors-Makinson): not implemented. Currently `full_meet_contract` uses Harper, not entrenchment-based selection.

From Grove 1988 (referenced indirectly):

- **System-of-spheres** representation: not implemented. The Spohn rankings cover the same ground but with different idioms.

From Katsuno-Mendelzon 1991:

- **KM update** (distinct from revision): not implemented.

From Hansson:

- **Safe contraction**: not implemented.
- **Belief base** (vs belief set) operations: the codebase only does belief sets.

From Booth-Meyer 2006:

- **Full RR family parameterisation** (admissibility level γ): not implemented. Only one fixed `restrained_revise` operator.

From DP 1997:

- **Diamond operator** (Counter-example for C3/C4 independence, notes.md p.155): not implemented. Not strictly needed for production but useful as a postulate-violation test fixture.
- **(μ, m)-conditionalization with general m**: only the `m = κ(¬μ)+1` (bullet) variant exists. Q has the option to expose `m` as a parameter for "soft" revision.

From Konieczny-Pino-Pérez 2002:

- **Max-distance operator** (`Δ^Max`, notes.md p.15): not implemented. Only Σ and GMax.
- **Iterated merging convergence** (Iteration postulate, notes.md p.5): not exercised.
- **Symmetry condition (Sym)**: not enforced — the implementation does not check that input formula representation does not bias the merge.

From AF-side papers:

- **AF revision operator** (Baumann-Brewka 2015): the paper itself gives only a representation theorem (notes.md p.155). No concrete operator implemented in propstore. `argumentation.af_revision.diller_2015_*` is a different surface (Diller 2015, not Baumann-Brewka).
- **AGM contraction for AFs** (Baumann 2019): not implemented. The paper's negative result (Harper Identity fails for AFs, recovery must be dropped) is not even documented in `docs/af-revision.md`.
- **Coste-Marquis 2007 merging Dung frameworks**: not implemented.
- **Cayrol-Lagasquie-Schiex change taxonomy**: only one classification predicate (`cayrol_2014_classify_grounded_argument_addition`) tested with one constraint.

---

## Open questions for Q

1. **K*2 violation by `revise` on unsatisfiable input** — should `revise(state, BOTTOM)` return the inconsistent theory (closing K under ⊥), raise, or stay a no-op as today? The current behaviour silently violates K*2; if intentional, document it in `docs/belief-set-revision.md`.

2. **Booth-Meyer 2006** — the notes.md file documents only the (P) admissibility criterion explicitly. Does the project intend to implement the **full** AR family (admissibility hierarchy γ ∈ {0,1,2,...}), or is the single `restrained_revise` the only target? The README says "restrained family" but the implementation is one operator.

3. **AF revision** — `docs/af-revision.md` claims `argumentation.af_revision` is the "formal abstract-argumentation change surface for WS-B" but provides no AGM-AF revision operator (only Baumann-2015 expansion + Diller-style extension revision + Cayrol classification). Is the intention to defer AGM-AF revision (Baumann-Brewka 2015 representation theorem) entirely, or is this a known gap?

4. **AGM contraction for AFs (Baumann 2019)** — should propstore implement contraction for AFs without recovery (as the paper recommends), or is this out of scope? `docs/af-revision.md` does not mention contraction for AFs at all.

5. **Coste-Marquis 2007 merging Dung frameworks** — listed in cluster scope; entirely absent from code, tests, and docs. Was this intentionally deferred?

6. **`full_meet_contract` discarding epistemic state (HIGH-3)** — is contraction expected to be one-shot only? If so, document. If not, design the post-contraction Spohn state preservation.

7. **Distance cache by `id(formula)` (HIGH-4)** — switch to `(formula, signature)` keys? Formulas are frozen dataclasses, hashable by value. Removes the GC foot-gun and increases hit rate.

8. **Test mega-functions** — should each of K*1..K*8, K-1..K-8, IC0..IC8, C1..C4, EE1..EE5 get its own test function, so the gate's failure messages name the actual postulate? Current "single test asserts everything" pattern obscures attribution.

9. **EE4/EE5 quantification over `FORMULAS` only** — the property is universal over the Lindenbaum algebra. Hypothesis cannot enumerate all formulas, but a stronger test could: enumerate all `frozenset[World] → BeliefSet` and check entrenchment over those, since over a finite alphabet the algebra has 2^(2^n) elements. Worth doing for n=3.

10. **Docs string-presence tests** — should they enforce ASCII names ("Gardenfors") or accept Unicode ("Gärdenfors")? Currently the latter would fail.

11. **Coverage of Bonanno 2007/2010, Boella 2009, Doutre 2018, Rotstein 2008** — listed in cluster scope but no implementation/tests anywhere. Are these inventory-only entries (research backlog) or expected deliverables?

12. **`revision_assertion_helpers.py`** — does this file belong in scope? It is named like a belief-set helper but only constructs `support_revision` `AssertionAtom`s. Likely a misnomer or stale.

---

## Summary count

- **HIGH bugs**: 4 declared, 1 (HIGH-2) downgraded to MED on closer reading. Net 3 HIGH.
- **MED bugs**: 7 (including the demoted HIGH-2).
- **LOW bugs**: 6.
- **Missing AGM postulates tested**: K-6, K-7, K-8 (contraction supplementaries).
- **Missing IC postulates tested**: IC4, Maj, Arb.
- **Missing iterated postulates tested**: CR1, CR2, CR3, CR4 for `revise`; C1-C4 for `lexicographic_revise` and `restrained_revise`.
- **Missing constructions**: partial-meet, maxichoice, selection function, Levi-as-operator, entrenchment-based contraction, system-of-spheres, KM update, safe contraction, belief base, `Δ^Max`, AF revision operator, AF contraction, Coste-Marquis merging.
- **Algorithmic concerns**: exponential in |alphabet|, no anytime/budget on revision side, no memoisation of `extend_state`.

The implementation hits the *named* postulate-tested cases for K*, basic K-, EE, DP-C and IC partial — but the test suite as a whole tests **fewer postulates than the test names suggest**, and the postulates that ARE tested are bundled into mega-functions that obscure attribution. The biggest risk is HIGH-1 (K*2 violation) and HIGH-3 (state-discard on contraction) — both invisible to the current gate.
