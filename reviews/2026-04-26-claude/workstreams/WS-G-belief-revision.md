# WS-G: Belief revision — AGM, iterated, IC merge, AGM-AF postulate coverage

**Status**: CLOSED b3b91229
**Depends on**: WS-A (foundation), WS-D (operator naming), WS-O-arg (upstream owner of Codex #20 fix in `argumentation` package)
**Blocks**: nothing internal. Downstream-of WS-A which is the universal foundation.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Resolved decisions

**D-12** (AGM-AF ownership): AGM-AF kernel stays in `argumentation`; propstore consumes via public API only. **No** `propstore/belief_set/af_revision.py` resurrection. The Codex #20 fix at `af_revision.py:274` lives in **WS-O-arg** (cluster-P bugs); WS-G owns only the consumer-side test, and the propstore `argumentation` pin advances when the upstream release ships.

---

## Why this workstream exists

`propstore/belief_set/` advertises AGM revision/contraction, Spohn-ranking iterated revision, Booth-Meyer restrained revision, KPP IC merging, and (via public API) Baumann-Brewka expansion + Diller revision. Both reviewers found the postulate gates these constructions claim to satisfy are not actually tested: three known violations (K*2 for ⊥, Spohn collapse on contraction, IC merge silently dropping ∞ distances) and twelve unasserted postulates (K-6/K-7/K-8, IC4, Maj, Arb, CR1-CR4, C1-C4 on the iterated operators). WS-G makes the contract testable: every postulate gets one parameterized test; the code either satisfies it or the surface is renamed/withdrawn. Findings in dependency packages: WS-G owns the consumer-side test, the upstream fix lives in `WS-O-*`.

## Review findings covered

This workstream closes ALL of the following. Fix-side and test-side are WS-G unless noted.

| Finding | Citation | Description |
|---|---|---|
| **T2.2** (Claude HIGH-3, RP Tier 2; Codex #23 corroborates) | `propstore/belief_set/agm.py:117-122` | AGM contraction collapses Spohn epistemic state via `SpohnEpistemicState.from_belief_set(contracted)`. |
| **T2.6** (Claude HIGH-1, RP Tier 2) | `propstore/belief_set/agm.py:84-85`; `tests/test_belief_set_postulates.py:106` | `revise(state, ⊥)` returns `working_state` unchanged, violating K*2. Mega-test escapes via `assume(consistent)`. |
| **Cluster C MED-1** | `tests/test_belief_set_postulates.py:137-147` | K-6/K-7/K-8 not asserted for `full_meet_contract`. |
| **Cluster C MED-2** | `tests/test_belief_set_postulates.py:206-249` | IC4 not asserted for `merge_belief_profile`; Maj/Arb absent for SIGMA/GMAX. |
| **Cluster C MED-3** | `tests/test_belief_set_postulates.py:163-170` | CR1-CR4 not asserted for `revise`. |
| **Cluster C MED-4** | `tests/test_belief_set_iterated_postulates.py:43-99` | C1-C4 not asserted for `lexicographic_revise` / `restrained_revise`. |
| **Codex #18** | `propstore/belief_set/ic_merge.py:80-86` | `_score_world` strips `math.inf` from per-source distances before SIGMA/GMAX. |
| **Codex #19** | `propstore/support_revision/projection.py:76-79` vs `state.py:91-104` | `RevisionScope.merge_parent_commits` declared, never populated. |
| **Codex #20** (fix-side **WS-O-arg**, test-side WS-G) | `argumentation/src/argumentation/af_revision.py:274` | `target = tuple(stable_extensions(framework)) or (frozenset(),)` collapses "no stable" and "stable={∅}". |
| **Cluster C HIGH-4** | `propstore/belief_set/ic_merge.py:167-193` | `_distance_to_formula` cache keyed by `(id(formula), signature)`. |
| **Cluster C "exponential"** | `propstore/belief_set/core.py:32-38` | `all_worlds(alphabet)` materialises 2^|alphabet| with no anytime budget. |
| **Missing constructions** (inventory-only here; impl in T6.5 / WS-O-arg) | n/a | Partial-meet, γ, maxichoice, remainder-set, Levi/Harper-as-composer, system-of-spheres, KM update, safe contraction, belief-base ops, Δ^Max, full Booth-Meyer AR, Baumann-Brewka 2015, Baumann 2019, Coste-Marquis 2007. |
| **Test mega-functions** | `tests/test_belief_set_postulates.py:101-126,137-147,163-170,196-249` | Test names claim per-postulate coverage, assert 1-3 properties bundled. |

Adjacent: `tests/test_belief_set_docs.py:11` `"Gardenfors" in text` rejects the umlaut the paper-faithful directory uses (Cluster C LOW-5; same file family).

## Code references (verified by direct read)

Citations in the findings table above already point at exact lines. Concentrated below as the implementer's quick map.

- `propstore/belief_set/agm.py`: `:33-44` `__post_init__` re-normalises min_rank to 0 (DP +1 only correct because of this); `:54-62` `from_belief_set` is the flat 2-level ranking with zero entrenchment information; `:73-100` `revise` is the DP bullet operator with the K*2 short-circuit at `:84-85`; `:103-122` `full_meet_contract` rebuilds via `from_belief_set` at `:120` (T2.2 / Codex #23); `:125-133` `extend_state` is O(|old|·2^|extras|) with no memoisation.
- `propstore/belief_set/iterated.py`: `:12-38` `lexicographic_revise` (Nayak / Spohn); `:41-81` `restrained_revise` (Booth-Meyer 2006). Today's gate covers preorder preservation only; **C1-C4 absent for both**.
- `propstore/belief_set/entrenchment.py:24-36`: `_negation_rank` returns ∞ for tautologies. EE5 ⇐ holds by ∞-totality but is unasserted; (C≤)/(C-) bridging not implemented.
- `propstore/belief_set/core.py`: `:32-38` `all_worlds` is 2^|alphabet| with no anytime hook; `:58-59` `cn()` is the identity.
- `propstore/belief_set/language.py:135-138`: `equivalent` does a lazy `BeliefSet` import (circular workaround; LOW-1).
- `propstore/belief_set/ic_merge.py`: `:39-71` `merge_belief_profile` is faithful to Konieczny-Pino-Pérez 2002 §3 *modulo* `:81` `finite_distances = tuple(d for d in distances if not math.isinf(d))` (Codex #18); `:167-193` `_distance_formula_cache_entry` keys on `(id(formula), signature)` at `:171` (Cluster C HIGH-4); the `:190` comment names the GC foot-gun without fixing it.
- `propstore/support_revision/`: `state.py:91-104` declares `merge_parent_commits` and nothing populates it; `projection.py:76-79` constructs `RevisionScope(bindings, context_id)` only (Codex #19); `iterated.py:108-112` is downstream-of and starved by the projection bug; `operators.py:86-99` does support-graph incision, **not** AGM partial-meet (docs sub-task); `history.py:239-256` `check_replay_determinism` is sound but starved by `projection.py`. `projection.py:174` / `history.py:47` `default=str` is WS-J's, not ours.
- `argumentation` public API (read-only from propstore per D-12): `argumentation.diller_2015_revise_by_framework`, `argumentation.diller_2015_expand_by_framework`, `argumentation.stable_extensions`, AF expansion/revision result types. Codex #20 (`argumentation/src/argumentation/af_revision.py:274`) lives upstream in **WS-O-arg**; propstore tests use only the public API.
- Test current state: `tests/test_belief_set_postulates.py:101-126` K* mega gated by `assume(consistent)`; `:137-147` K- mega without K-6/7/8; `:163-170` DP C1-C4 mega without CR1-CR4 and `revise`-only; `:183-193` EE1-EE5 over a finite `FORMULAS` sample; `:196-249` IC without IC4/Maj/Arb. `tests/test_belief_set_iterated_postulates.py:43-99` preorder surrogates; C1-C4 absent. `tests/test_af_revision_postulates.py` Baumann-Brewka K1-K6 partial; R1-R8/Coste-Marquis 2007 absent. `tests/test_belief_set_docs.py:11` rejects the umlaut.

## First failing tests (write these before any production change)

Per Codex 2.4, tests below are split into two classes. **Test docstrings explicitly state which class each test is.** "Must-fail-today" is reserved for tests with a paper-cited or line-cited known counterexample; everything else is a "coverage gate" — the test must exist because the postulate is unasserted, but the production code may already satisfy the property. Coverage gates that the audit reveals as actually-violated are escalated to known-failing in the workstream log at that point, not pre-emptively here.

### Class A — Must fail today (known counterexamples)

A test in this class is failing on master right now and the workstream proves it. Every entry below cites the source-line or paper-line that constitutes the counterexample.

1. **`tests/test_agm_K_star_2_inconsistent_input.py`** (new; T2.6)
   - Docstring: `"""Class A — must fail today. Counterexample: agm.py:84-85 short-circuits revise(state, ⊥) to working_state, violating K*2."""`
   - Constructs `state` with a non-tautological belief set.
   - Calls `revise(state, BOTTOM)` (or `revise(state, conjunction(p, negate(p)))`).
   - Asserts one of: result.belief_set is the inconsistent theory `BeliefSet.contradiction(signature)`, OR `revise` raises a typed `K2Violation` exception. (Pick during Step 1 below; document.)
   - **Must fail today**: result.belief_set equals the input belief set, no exception.

2. **`tests/test_agm_contraction_preserves_spohn_state.py`** (new; T2.2 / Codex #23)
   - **Per Codex 2.6, the test docstring carries the OCF derivation; it IS the proof. The full derivation is inlined here so a reader of the test alone can verify correctness without consulting Step 2 of the production sequence.** The docstring (verbatim, multi-paragraph) reads:

     > Class A — must fail today. Counterexample: `agm.py:120` rebuilds the Spohn state via `from_belief_set(contracted)`, which assigns rank 0 to models and rank 1 to non-models irrespective of the prior ranking. This collapses any non-flat ranking to the flat 2-level ranking and loses information about prior entrenchment.
     >
     > **Paper-cited OCF derivation.** Spohn 1988 OCF Definition 4 (p.115) defines κ as the disbelief grade with κ(W)=0, κ(∅)=Ω, κ(A) = min{κ(w) | w ∈ A}. Darwiche-Pearl 1997 §6 p.15 gives the Spohn-bullet revision operator:
     >
     >     (κ • μ)(ω) = κ(ω) − κ(μ)              if ω ⊨ μ
     >               = κ(ω) + 1                   if ω ⊨ ¬μ
     >
     > Harper identity (Alchourron-Gärdenfors-Makinson 1985 Observation 2.3) lifted to OCFs: a world is "kept" in a contraction iff it survives in either the original κ or the revision-by-negation κ•¬φ. The minimum is the additive identity for OCF disbelief (rank 0 = "most plausible / kept"). The OCF analogue of Harper is therefore:
     >
     >     (κ ÷ φ)(ω) = min(κ(ω), (κ • ¬φ)(ω))
     >
     > Booth-Meyer 2006 §5 confirms this min-of-prior-and-revised-by-negation construction yields a contraction-OCF when the prior is an OCF.
     >
     > **Worked numerical example (the fixture this test uses).** Alphabet `{p, q}`, four worlds `w0=¬p¬q, w1=¬pq, w2=p¬q, w3=pq`. Two prior states with the same belief set after contracting by `p`:
     >
     > - State A: κ_A = {w3:0, w2:1, w1:2, w0:3}. Bel(κ_A) = {w3} (only pq is rank 0). p ∈ Bel(κ_A); q ∈ Bel(κ_A).
     > - State B: κ_B = {w3:0, w1:1, w2:2, w0:3}. Bel(κ_B) = {w3} (same as A). p ∈ Bel(κ_B); q ∈ Bel(κ_B).
     >
     > Contract both by `p`. State A computation:
     >  1. κ_A(¬p) = min(κ_A(w0), κ_A(w1)) = min(3, 2) = 2.
     >  2. (κ_A • ¬p)(w0)=3−2=1; (w1)=2−2=0; (w2)=1+1=2; (w3)=0+1=1.
     >  3. (κ_A ÷ p)(w0)=min(3,1)=1; (w1)=min(2,0)=0; (w2)=min(1,2)=1; (w3)=min(0,1)=0.
     >  4. Normalised: κ_A÷p = {w0:1, w1:0, w2:1, w3:0}. Bel = {w1, w3}.
     >
     > State B computation:
     >  1. κ_B(¬p) = min(3, 1) = 1.
     >  2. (κ_B • ¬p)(w0)=3−1=2; (w1)=1−1=0; (w2)=2+1=3; (w3)=0+1=1.
     >  3. (κ_B ÷ p)(w0)=min(3,2)=2; (w1)=min(1,0)=0; (w2)=min(2,3)=2; (w3)=min(0,1)=0.
     >  4. Normalised: κ_B÷p = {w0:2, w1:0, w2:2, w3:0}. Bel = {w1, w3} (same belief set as A).
     >
     > The two contraction outputs share a belief set but have distinct rankings. Now revise each by `q`:
     >  - A's contracted state revised by q: κ(q) = min(0,0) = 0. Final: {w0:2, w1:0, w2:2, w3:0}.
     >  - B's contracted state revised by q: κ(q) = min(0,0) = 0. Final: {w0:3, w1:0, w2:3, w3:0}.
     >
     > The two final states differ at w0 (rank 2 vs 3) — exactly what the contraction-preserves-prior-information property requires. The test asserts inequality.
     >
     > **Today's behaviour (the counterexample).** `agm.py:120` calls `from_belief_set(contracted)`, which forces both A and B to {w0:1, w1:0, w2:1, w3:0} after contraction. Both revise by q to identical ranks. The test fails (the two final states are equal); the bug is exposed.

   - Test body: construct the two states from the docstring's worked example, call `full_meet_contract(state, p)` on each, then `revise(result.state, q)` on the contraction outputs.
   - **Assert** the two final Spohn states are NOT equal: revise must remain sensitive to the prior ranking that contraction was supposed to preserve.
   - **Must fail today**: both states get flattened by `from_belief_set` to the same 2-level ranking before the second revise, so the outcomes are equal at w0.
   - The Step 2 production-sequence section reproduces the same derivation as production-side justification and references the test docstring as the canonical proof — the byte-for-byte expected ranks live in the test, not in the spec.

3. **`tests/test_ic_merge_infinite_distance_handling.py`** (new; Codex #18)
   - Docstring: `"""Class A — must fail today. Counterexample: ic_merge.py:81 strips math.inf from per-source distances before SIGMA / GMAX, so a profile with an unsatisfiable member scores identically to one without it."""`
   - Construct a profile with one formula that has zero models in `signature` (e.g. `conjunction(p, negate(p))`).
   - Call `merge_belief_profile` with SIGMA and GMAX.
   - Assert: either the call raises `ICMergeProfileMemberInconsistent`, OR the unsatisfiable formula is preserved through the score with a sentinel that surfaces in `scored_worlds`. Pick during Step 4 below.
   - **Must fail today**: the unsatisfiable distance is silently dropped from `finite_distances`, so SIGMA returns the same score as if the unsatisfiable formula were absent.

4. **`tests/test_ic_merge_distance_cache_stale_read.py`** (new; Cluster C HIGH-4 — deterministic fixture per Codex 2.5)
   - Docstring: `"""Class A — must fail today. Counterexample: ic_merge.py:171 keys _distance_to_formula on (id(formula), signature). Demonstrated deterministically — no reliance on CPython id-recycling timing."""`
   - **Deterministic stale-cache fixture (the primary path; Codex 2.5 option 2).** Monkey-patch the module-level cache (`ic_merge._DISTANCE_CACHE` or its accessor) to expose direct insertion. Construct `formula_a` with a known `signature`; insert a known-bad value `999` under key `(id(formula_a), signature)`. Call `_distance_to_formula(formula_a, world, signature)` and assert it returns `999`, proving the cache is keyed on `id(...)`. Then construct `formula_b` whose `Formula` value is identical to `formula_a` (same operator/atoms, distinct object) and call `_distance_to_formula(formula_b, world, signature)`: under id-keying it computes fresh (cache miss; assertion-A holds); under value-keying it would hit the same entry (assertion-A flips). The two-read contradiction is the violation. After Step 6 (value-keying), the assertion flips to require a single shared cache entry for both objects.
   - Optional companion: a `@pytest.mark.cpython_address_reuse` weakref-based fixture that allocates structurally-different formulas until one lands at the dropped address (bounded `max_attempts`, `pytest.skip` on exhaustion). Supplementary only; never required for CI green.
   - **Must fail today**: the deterministic fixture demonstrates id-keying directly without flake.

5. **`tests/test_worldline_revision_merge_parent_evidence.py`** (new; Codex #19)
   - Docstring: `"""Class A — must fail today. Counterexample: projection.py:76-79 constructs RevisionScope(bindings=..., context_id=...) with no merge-parent threading; downstream entrenchment (iterated.py:108-112) reads an empty merge_parent_commits tuple even when the underlying world has merge history."""`
   - Build a real `BoundWorld` whose underlying world has a merged branch history (use the existing fixture in `tests/test_worldline_revision.py`).
   - Project the belief base via `support_revision.projection.project_belief_base`.
   - Assert `result.scope.merge_parent_commits == (parent_a_commit, parent_b_commit)` — the actual merge parents.
   - **Must fail today**: the field is never populated.

6. **`tests/test_af_revision_no_stable_distinct_from_empty_stable.py`** (new; Codex #20 consumer-side test, public API only)
   - Docstring: `"""Class A — must fail today against the current argumentation pin. Counterexample: argumentation/src/argumentation/af_revision.py:274 substitutes (frozenset(),) when stable_extensions is empty, collapsing 'no stable' and 'stable={∅}' at the public-API surface. Upstream fix lives in WS-O-arg."""`
   - Imports only `argumentation.diller_2015_revise_by_framework`, `argumentation.stable_extensions`, framework constructors. No reaching into `argumentation.af_revision` private module.
   - Build AF-A with no stable extensions (e.g. odd cycle of three mutually attacking arguments). Verify via the public API: `stable_extensions(AF_A) == ()`.
   - Build AF-B with `stable_extensions(AF_B) == (frozenset(),)`.
   - Call `diller_2015_revise_by_framework(state, AF_A)` and `diller_2015_revise_by_framework(state, AF_B)`.
   - Assert the two outcomes differ at the public-API surface — at minimum: AF-A's outcome surfaces "no stable" through a typed error or sentinel; AF-B's outcome reports the empty extension as a real revision target. Exact contract negotiated with WS-O-arg's upstream PR; the propstore test pins the consumer-visible distinction.
   - **Must fail today**: af_revision.py:274 collapses both cases.

### Class B — Coverage gates (no known counterexample)

A test in this class fails because no test exists today; the production code may already be correct. The audit (test 7 below) tells us which Class-B parameters actually-violate when first run. Class B test docstrings carry the line: `"""Class B — coverage gate. The postulate is unasserted today; the audit will tell us whether production satisfies it. Failure here means a real bug; promote to Class A and cite the counterexample."""`

7. **`tests/test_agm_postulate_audit.py`** (new — the parameterized matrix; WS-G headline test)
   - Parametrize over each postulate ID from the matrix below; parameter `= (postulate_id, operator, formal_property, class_letter)`. Each body builds a small Spohn state (alphabet ≤ 3), exercises the property under Hypothesis `@given`, asserts the postulate. `@pytest.mark.property` per WS-A.
   - Enumerates: K*1-K*8, K-1-K-8 (Alchourron-Gärdenfors-Makinson 1985 p.512); IC0-IC8, Maj (Konieczny 2002 Thm 4.2), Arb (Thm 4.14); CR1-CR4 (DP 1997 p.14) for `revise`, `lexicographic_revise`, `restrained_revise`; C1-C4 (DP 1997 p.11) for the same three operators; EE1-EE5 (Gärdenfors-Makinson 1988 p.89).
   - Includes one row exercising the AGM-AF kernel through the `argumentation` public API: **`agm_af_no_stable_distinct_from_empty_stable`** (Class A; same fixture as test 6).
   - **Class A rows in the audit (paper- or line-cited known counterexamples)**: K*2 for φ=⊥ (cites `agm.py:84-85`); the AGM-AF stable-distinguishability row (cites `argumentation/.../af_revision.py:274`). These rows MUST fail on master; CI gating asserts they fail before Step 1 / Step 10 land.
   - **Class B rows**: K-6/K-7/K-8, IC4, Maj, Arb, CR1/CR2/CR3/CR4 for each of the three iterated operators, C1-C4 for `lexicographic_revise` and `restrained_revise`, EE5 reverse direction, alphabet-budget refusal. Each is a coverage gate. The audit run after each gate is added classifies it: pass → unasserted-but-correct, fail → newly-discovered bug logged with a citation in `notes/ws-g-audit-results.md` and the row promoted to Class A.
   - Test `id` is the postulate name — CI says "`K*2` failed" not "the mega-test failed at line 117."

8. **`tests/test_ic_merge_IC4_fairness.py`** (new; Cluster C MED-2 — Class B)
   - Docstring: Class B — coverage gate.
   - Hypothesis `@given` over two formulas φ1, φ2 each with at least one model under the constraint μ.
   - `assume(φ1.entails(μ) and φ2.entails(μ))`.
   - Assert `not result.belief_set.entails(negate(φ1))` and `not result.belief_set.entails(negate(φ2))`.
   - **First-run classification**: TBD. The Konieczny-Pino-Pérez 2002 §3 fairness construction predicts SIGMA satisfies IC4 for non-degenerate profiles; if the audit run shows otherwise, promote to Class A with the failing fixture.

9. **`tests/test_ic_merge_Maj_Arb.py`** (new; Cluster C MED-2 — Class B)
   - Docstring: Class B — coverage gate. Maj is a SIGMA-specific postulate (Konieczny 2002 Thm 4.2); Arb is a GMAX-specific postulate (Thm 4.14).
   - Maj: build a profile `Ψ1, Ψ2` and an `n` such that `Ψ2`-replicated-`n`-times dominates; assert `Δμ(Ψ1 ⊔ Ψ2^n) ⊨ Δμ(Ψ2)` for SIGMA.
   - Arb: pick the profile from Konieczny-Pino-Pérez 2002 Theorem 4.14 example (notes.md p.13); assert GMAX returns the arbitration-correct outcome.
   - **First-run classification**: TBD.

10. **`tests/test_belief_set_alphabet_growth_budget.py`** (new; Cluster C "exponential" concern — Class B)
    - Docstring: Class B — coverage gate; tests presence of the budget hook, not violation of a postulate.
    - Build a Spohn state over alphabet of size 3.
    - Call `revise(state, formula)` where `formula` introduces 18 fresh atoms (signature size 21, world space 2^21).
    - Assert: either the operation refuses with `EnumerationExceeded` or completes within a configured budget.
    - **First-run classification**: gate fails today (no hook present); Step 7 adds the hook so it passes. Not a postulate violation per se — a missing-feature gate.

### Sentinel

11. **`tests/test_workstream_g_done.py`** (new — gating sentinel; same shape as WS-A's sentinel)
    - `xfail` until WS-G closes; flips to `pass` on the final commit.
    - Used by `tests/test_gaps_md_consistency.py` (per REMEDIATION-PLAN Mechanism 2) to verify the `gaps.md` rows for findings T2.2, T2.6, Codex #18, #19, #20 (note: #20 closes via the WS-O-arg release plus this consumer test going green), all Cluster C HIGH/MED items, and the missing-construction inventory entries are closed.

## Postulate matrix (the audit target)

The fixture `tests/test_agm_postulate_audit.py` parametrizes over the IDs below. The row id is the postulate name; the assert template is the textbook statement at the cited page. Coverage column: ✓ asserted, ⚠ partial, ✗ unasserted, ❌ asserted but violated.

**AGM revision K*1-K*8** (Alchourron 1985 p.512). Today: K*1 ✓; K*2 ❌ violated for ⊥; K*3-K*8 ⚠ via mega-test (K*5 escapes via `assume(consistent)`). After WS-G: all ✓ per-postulate, K*6 over Hypothesis-generated equivalence pairs.

**AGM contraction K-1-K-8 + Harper** (same paper). Today: K-1 ✓; K-2-K-5 ⚠; K-6/K-7/K-8 ✗; Harper ⚠. After WS-G: all ✓; Harper kept as separate parameter.

**Iterated revision** (Darwiche-Pearl 1997 p.11, p.14). For each of `revise`, `lexicographic_revise`, `restrained_revise`:
- C1-C4 (p.11): today ⚠ for `revise` (mega-test), ✗ for both `lex`/`restrained`. After WS-G: ✓ for all three.
- CR1-CR4 (p.14, representation-theorem counterparts): today ✗ for `revise`, partial for CR1/CR2 in `lex`/`restrained`, ✗ for CR3/CR4. After WS-G: ✓ for all three operators.
- R*4 (state identity, not belief-set equivalence): today ✗ for all three; After: ✓.
- Booth-Meyer (P) admissibility: today ⚠ one direction `restrained` only; After: ✓ both directions.

**IC merging** (Konieczny-Pino-Pérez 2002 p.4-5, Thms 4.2/4.14). Today: IC0-IC2 ✓; IC3 ⚠; IC4 ✗; IC5-IC8 ✓; Maj ✗; Arb ✗; Inf-distance ❌ silently dropped. After WS-G: all ✓; Inf-distance becomes "raise `ICMergeProfileMemberInconsistent` or sentinel".

**Epistemic entrenchment EE1-EE5** (Gärdenfors-Makinson 1988 p.89). Today: EE1-EE3 ⚠; EE4 ⚠ (finite sample); EE5 ⚠ one direction. After WS-G: ✓ for all; EE4 over all `frozenset[World]`-induced belief sets at |alphabet|=3; EE5 both directions.

**AGM-AF coverage — public-API consumer rows** (Baumann-Brewka 2015; Coste-Marquis 2007). Per D-12, kernel lives upstream in `argumentation`; fix-side is **WS-O-arg** for every row. Today / After-WS-G:
- K1-K6 AF expansion: ⚠ (K2/K3/idempotence covered; K1/K4/K5/K6 absent) → ✓.
- R1-R8 AF revision: ✗ → ✓ or documented-deferred.
- Diller P*1-P*6 / A*1-A*6: ⚠ (label says 6, asserts ~3) → ✓.
- Cayrol 2014 classify (seven extension-family changes): partial one direction → ✓.
- Coste-Marquis 2007 IC-style merging: ✗ no implementation → ✓ or deferred to T6.5.
- AGM contraction for AFs (Baumann 2019): ✗ → documented-deferred to T6.5.
- **Stable-extension distinguishability (no-stable ≠ empty-stable; Codex #20)**: ❌ collapsed → ✓ via public API; upstream fix in WS-O-arg, consumer test in WS-G.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-G step N — <slug>`.

WS-G is **read-only** on production code in the `argumentation` package — no edits to `argumentation/src/argumentation/af_revision.py` or any other upstream module. propstore-side production changes only.

### Step 1 — K*2 fix (T2.6)

`propstore/belief_set/agm.py:73-100`. `revise(state, ⊥)` returns `RevisionOutcome(belief_set=BeliefSet.contradiction(signature), state=...)` — the inconsistent theory is a legitimate AGM result, all worlds rank ∞ explicitly. (Alternative: typed `RevisionInconsistencyError`. Default to the value path; AGM tradition.) Remove `assume(_belief(a).is_consistent)` from `tests/test_belief_set_postulates.py:106`. Acceptance: K*2 audit row passes.

### Step 2 — Spohn state preservation on contraction (T2.2 / Codex #23)

`propstore/belief_set/agm.py:103-122`. Replace `SpohnEpistemicState.from_belief_set(contracted)` with the OCF-Harper construction `(κ ÷ φ)(ω) = min(κ(ω), (κ • ¬φ)(ω))` — paper-cited in Spohn 1988 (OCF Def 4 p.115), Darwiche-Pearl 1997 §6 p.15 (bullet operator), Alchourron 1985 Obs 2.3 (Harper), Booth-Meyer 2006 §5 (OCF-preservation). **Per Codex 2.6, the canonical derivation and byte-for-byte worked example live in the docstring of `tests/test_agm_contraction_preserves_spohn_state.py`** (test 2 above); the test docstring IS the proof. The implementation must match its expected ranks; if the two ever disagree, the test docstring wins. Acceptance: K-* audit rows pass; the contraction test passes; production output matches the test docstring's expected ranks byte-for-byte.

### Step 3 — K-6, K-7, K-8 coverage gates

Class B. Full-meet is transitively relational (Alchourron 1985 Cor 4.5), so K-6/K-7/K-8 are predicted to hold. Apply the **shared first-run protocol** (defined once, below): add the audit rows; on first run, log any actual failure to `notes/ws-g-audit-results.md` with paper citation, promote the row to Class A, fix in production. If all pass, "unasserted-but-correct" is the deliverable.

**Shared first-run protocol (referenced by steps 3, 5, 8).** When a Class-B audit row first runs, capture the result in `notes/ws-g-audit-results.md`. Pass → record "unasserted-but-correct" with the postulate id and paper citation. Fail → record the failing fixture, promote the row to Class A, cite the source line, then implement the fix in the relevant production file before re-running.

### Step 4 — IC merge inf-distance handling (Codex #18)

`propstore/belief_set/ic_merge.py:80-86`. Konieczny-Pino-Pérez does not define merging when a profile member is unsatisfiable (notes p.4 footnote on `mod(φ)`). Raise `ICMergeProfileMemberInconsistent(formula)` at the boundary in `merge_belief_profile` — fail closed. Remove the `finite_distances` line at `:81`. Acceptance: `tests/test_ic_merge_infinite_distance_handling.py` passes; Inf-distance audit row passes.

### Step 5 — IC4, Maj, Arb coverage gates

Class B. KPP 2002 Thm 4.2 / Thm 4.14 predict SIGMA satisfies IC4 + Maj and GMAX satisfies Arb by construction. Add audit rows; apply the shared first-run protocol from Step 3.

### Step 6 — Cache by formula value (Cluster C HIGH-4)

`propstore/belief_set/ic_merge.py:167-193`. Replace `key = (id(formula), signature)` with `key = (formula, signature)`. `Formula` is `frozen=True` and hashable. Drop the strong-ref comment and the cache-eviction warning. Acceptance: `tests/test_ic_merge_distance_cache_stale_read.py` Path 1 flips from "stale read demonstrated under id-keying" to "single shared entry under value-keying"; Path 2 (where it ran) skips or passes consistently because address reuse no longer matters.

### Step 7 — Alphabet-size budget on revision

`propstore/belief_set/agm.py`. Anytime semantics are a downstream feature; the immediate gap is the absence of *any* budget. Reject signatures > `MAX_ALPHABET_SIZE` (default 16 → 65k worlds) at the entry point with a typed error. Acceptance: `tests/test_belief_set_alphabet_growth_budget.py` passes.

### Step 8 — C1-C4 and CR1-CR4 audit rows for all three iterated operators

Class B. Both `lexicographic_revise` and `restrained_revise` claim iterated-revision semantics; CR1-CR4 are the representation-theorem counterparts (DP 1997 Thm 13 p.14). DP literature predicts `lexicographic_revise` satisfies C1-C2 but may violate C3/C4; `restrained_revise` (Booth-Meyer) is purpose-built for all four. Apply the shared first-run protocol from Step 3; fixes (if any) land in `iterated.py`.

### Step 9 — Worldline merge-parent evidence (Codex #19)

`propstore/support_revision/projection.py:76-79`. Thread `branch`, `commit`, `merge_parent_commits` from `BoundWorld._world` into `RevisionScope`. If `World` lacks `merge_parent_commits`, source from `worldline/runner` history. Coordinate with WS-J (worldline / hashing) — the read of merge parents must align with WS-J's canonical worldline projection. Acceptance: `tests/test_worldline_revision_merge_parent_evidence.py` passes; the Bonanno guard exercises real DAG history.

### Step 10 — AF revision: consume the no-stable / empty-stable distinction via public API (Codex #20)

Fix-side: `argumentation/src/argumentation/af_revision.py:274` ships in **WS-O-arg** per D-12 (likely typed `NoStableExtensionError` or discriminated result). WS-G does not edit `argumentation`. Consumer-side: (1) author the consumer test (test 6 above), initially `xfail(strict=True)` against the current pin; (2) author a thin `propstore/belief_set/af_revision_adapter.py` (or fold into `__init__.py` re-exports) that projects public-API results into `BeliefSet`/Opinion-typed surfaces — wrapper only, no kernel resurrection; (3) when the upstream PR ships, advance the `argumentation` pin in `pyproject.toml`, the consumer test flips xfail→pass, the wrapper updates if the public API shape changed. Acceptance: consumer test green on the new pin; audit row passes; no edits under `argumentation/`; `propstore/belief_set/af_revision.py` does not exist.

### Step 11 — Mega-test decomposition

Move every per-postulate assertion from `tests/test_belief_set_postulates.py` and `tests/test_belief_set_iterated_postulates.py` into the parameterized audit. Delete the mega-functions; per Q's no-shims rule, no deprecated wrappers. Acceptance: every audit row has a unique pytest id; `pytest -k K_star_2` selects exactly one test.

### Step 12 — Document missing constructions

`docs/belief-set-revision.md`, `docs/ic-merge.md`, `docs/af-revision.md` each gain a "Not implemented" section listing the deferred items from the findings table (partial-meet, γ, maxichoice, Levi/Harper-as-composer, Grove 1988 spheres, KM 1991 update, Hansson safe contraction, Hansson belief-base ops, Booth-Meyer full AR, KPP Δ^Max, Baumann-Brewka 2015, Baumann 2019, Coste-Marquis 2007) with paper citations. AGM-AF items cross-link to **WS-O-arg**; propositional items roll into **REMEDIATION-PLAN T6.5**. Switch `tests/test_belief_set_docs.py:11` from `"Gardenfors"` to `"Gärdenfors"` (paper-faithful umlaut).

### Step 13 — Close gaps and gate

- Update `docs/gaps.md`: remove the Cluster C HIGH-1, HIGH-3, HIGH-4 rows; remove the Codex #18, #19, #23 rows; for Codex #20, mark "fix-side closed in WS-O-arg <upstream-sha>; consumer-side closed in WS-G <propstore-sha>"; remove the K-6/7/8, IC4, Maj, Arb, CR1-CR4 coverage gaps. Add a `# WS-G closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_g_done.py` from `xfail` to `pass`.
- Update `reviews/2026-04-26-claude/workstreams/WS-G-belief-revision.md` STATUS line to `CLOSED <sha>`.

Acceptance: `tests/test_workstream_g_done.py` passes; `gaps.md` has the new closed entries; the missing-construction list in `docs/` references unrelated future workstreams (T6.5) and WS-O-arg for AGM-AF items.

## Acceptance gates

Before declaring WS-G done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors.
- [x] `uv run lint-imports` — passes.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-G tests/test_agm_postulate_audit.py tests/test_agm_K_star_2_inconsistent_input.py tests/test_agm_contraction_preserves_spohn_state.py tests/test_ic_merge_infinite_distance_handling.py tests/test_ic_merge_IC4_fairness.py tests/test_ic_merge_Maj_Arb.py tests/test_ic_merge_distance_cache_stale_read.py tests/test_belief_set_alphabet_growth_budget.py tests/test_worldline_revision_merge_parent_evidence.py tests/test_af_revision_no_stable_distinct_from_empty_stable.py tests/test_workstream_g_done.py` — all green.
- [x] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs the baseline at `logs/test-runs/pytest-20260426-154852.log` (Codex's recorded baseline; WS-A renormalises, but for WS-G we compare against post-WS-A).
- [x] `tests/test_belief_set_postulates.py` no longer contains the K* mega-function or the K- mega-function (Step 11).
- [x] `tests/revision_assertion_helpers.py` — Cluster C LOW-6 — moved to `tests/support_revision/` or renamed to clarify it is not a belief-set helper.
- [x] `argumentation` pin updated to a release containing the WS-O-arg fix for Codex #20.
- [x] `propstore/belief_set/af_revision.py` does **not** exist (D-12 enforcement).
- [x] Any propstore-side AF-revision wrapper imports only from `argumentation`'s public API surface (verifiable via `lint-imports` contract or grep).
- [x] `docs/gaps.md` has no open rows for the findings listed above.
- [x] `docs/belief-set-revision.md`, `docs/ic-merge.md`, `docs/af-revision.md` all enumerate the missing constructions with paper citations and cite WS-O-arg as the upstream owner for AGM-AF items.
- [x] `reviews/2026-04-26-claude/workstreams/WS-G-belief-revision.md` STATUS line is `CLOSED <sha>`.

## Done means done

WS-G closes only when **every finding in the table at top has a green test in CI**: T2.2, T2.6, Cluster C MED-1/2/3/4 + HIGH-4, Codex #18/#19 (propstore-side); Codex #20 has a green consumer test plus the upstream WS-O-arg PR cited; the audit covers ≥60 parameters spanning K*1-K*8, K-1-K-8 + Harper, IC0-IC8 + Maj + Arb, EE1-EE5, C1-C4 × 3 operators, CR1-CR4 × 3 operators, and the AGM-AF stable-distinguishability row; `gaps.md` updated; sentinel passes; `docs/` missing-constructions inventory is paper-cited and cross-linked to WS-O-arg. If any of those is not true, WS-G stays OPEN. No deferral by side-channel — either in scope and closed, or explicitly moved to a successor WS in this file before declaring done.

## Papers / specs referenced

All retrieved and live at `papers/<dir>/notes.md`. Citations in the matrix above point at exact pages; this list is the bibliography.

- **Alchourron-Gärdenfors-Makinson 1985** — K*/K- (p.512); Harper (p.513 obs 2.3); partial-meet §4.
- **Gärdenfors-Makinson 1988** — EE1-EE5 (p.89); (C≤)/(C-) (p.89-90); Theorem 5. Umlaut in dirname.
- **Spohn 1988** — `SpohnEpistemicState` basis; OCF Definition 4 p.115; α-shift §6.
- **Darwiche-Pearl 1997** — C1-C4 (p.11); CR1-CR4 (p.14); bullet operator (p.15); R*1-R*6 §3.
- **Konieczny-Pino-Pérez 2002** — IC0-IC8 (p.4); Maj/Thm 4.2 (p.13); Arb/Thm 4.14 (p.13); Σ/GMax (p.12, p.17); Δ^Max (p.15).
- **Booth-Meyer 2006** — (P) admissibility; RR Definition 4. Full AR family deferred.
- **Baumann-Brewka 2015** — K1-K6 expansion (p.86-105); R1-R8 revision (p.105); kernel-union (Thm 1). Lives upstream per D-12.
- **Baumann 2019** — Recovery fails; Harper fails for AFs. Deferred to T6.5; upstream WS-O-arg.
- **Diller 2015** — P*1-P*6 / A*1-A*6 — the `diller_2015_*` operators in the `argumentation` public API.
- **Coste-Marquis 2007** — Dung-merging. Zero coverage today; deferred. Upstream WS-O-arg.
- **Bonanno 2007/2010** — Cited by the Codex #19 merge-parent guard.
- **Kraus-Lehmann-Magidor 1990; Lehmann-Magidor 1989** — KLM / rational closure cross-check for entrenchment-derived contraction.
- **Doutre-Mailly 2018, Rotstein 2008, Boella-Kaci-van der Torre 2009, Baumann 2010** — inventory papers; deferred.

## Cross-stream notes

- Depends on **WS-A** (fixtures must match production schema before postulate gates can be measured) and **WS-D** (operator-naming audit may rename Spohn/OCF/DP terminology).
- Depends on **WS-O-arg** for Codex #20 per D-12 — the consumer test `tests/test_af_revision_no_stable_distinct_from_empty_stable.py` is the propstore gate; upstream fix at `argumentation/src/argumentation/af_revision.py:274` lives in WS-O-arg cluster-P. propstore's `argumentation` pin advances on upstream release. **No `propstore/belief_set/af_revision.py` resurrection** — D-12 explicit.
- All other AGM-AF kernel work (Baumann-Brewka R1-R8, Baumann 2019 contraction, Coste-Marquis 2007 merging, Diller P*/A* completion) lives upstream in **WS-O-arg**. propstore's `belief_set` only wraps the public API.
- "Missing constructions" feeds **REMEDIATION-PLAN T6.5** (propositional-AGM gaps); AGM-AF gaps owned by WS-O-arg.
- Coordinate Step 9 with **WS-J**: `support_revision/history.py:47` and `projection.py:174` `default=str` is WS-J's; the Codex #19 fix must not introduce new `default=str` sites.
- Mega-test decomposition pattern (Step 11) is reusable by **WS-F** (ASPIC) and **WS-H** (probabilistic).

## What this WS does NOT do

- Does NOT recreate `propstore/belief_set/af_revision.py` (D-12) or edit any file under `argumentation/` (WS-O-arg owns that).
- Does NOT implement partial-meet, selection-function `γ`, maxichoice, Levi-as-composer, system-of-spheres, KM update, safe contraction, belief-base operations, Coste-Marquis 2007 Dung-merging, Baumann 2019 AGM-AF contraction, or full Booth-Meyer AR — all deferred to T6.5 or WS-O-arg, paper-cited in `docs/`.
- Does NOT change canonical-JSON discipline (WS-J), import-linter contracts (WS-N), or add anytime semantics (Step 7 picks rejection-on-budget; anytime is a separate spike).
- Does NOT touch `praf-paper-td-complete`, DF-QuAD (WS-H), or ASPIC stance asymmetry T2.1 (WS-F).
