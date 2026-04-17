# Axis 3b — Uncertainty & Opinion Fidelity

## Summary

Reviewing the post-fix state after commits 34d0074 and c7a9215. Those commits
eliminated the silent `__bool__` bypass, a real hash-contract bug, and the
fake-consensus `_ccf_average` simplification that produced dogmatic output on
dogmatic disagreement. The remaining open drift is significant:
`wbf()` is self-declared aCBF and CONFIRMED against van der Heijden 2018
Def 4 Case 1 (PNG p.4); `apply_decision_criterion`'s "pignistic" label is
Jøsang projected probability, not Denoeux/Smets BetP (diverges when `a ≠ 0.5`);
and Opinion construction has no provenance-enforcing type boundary, so raw
number → Opinion coercion sites remain throughout. Several already-known
vacuous-hostile code paths persist, plus one new one in
`summarize_defeat_relations` that fabricates dogmatic certainty from a MC
marginal.

## Post-fix posture

The two recent commits delivered real theoretical fixes. For synthesis:

- `__eq__`/`__hash__` now share a single `_TOL` quantization grid — hash
  contract is now honored.
- `__bool__` raises `TypeError` — `if op` and `op and other` no longer
  short-circuit around subjective-logic conjunction.
- `&` / `|` are explicit aliases for `conjunction` / `disjunction`;
  docstrings flag binomial-only scope.
- `consensus_pair` base-rate fusion is in cancellation-free `v = 1 - u` form
  — verified algebraically equivalent to Jøsang 2001 Theorem 7 denominator
  `u^A + u^B − 2·u^A·u^B`, just ULP-stable.
- `_ccf_average` deleted. `_ccf_binomial` implements van der Heijden 2018
  Def 5 Eqs. 6–12 for binomial-reduced frames, handling dogmatic
  disagreement by returning vacuous (honest ignorance restored).
- `_BASE_RATE_CLAMP = (0.01, 0.99)` promoted to a named constant with
  paper-deviation docstring.
- `maximize_uncertainty` preconditions and `discount` uncertainty identity
  are now spelled out.

Everything below treats that state as the baseline.

## Fidelity verdict per paper (priority papers)

| Paper | Verdict | Key evidence |
|-------|---------|--------------|
| van der Heijden 2018 (WBF, Def 4 Case 1) | **DRIFT** — `wbf()` is aCBF | `opinion.py:419-422, 430`; paper PNG p.4 has `(1 − u^A_X)` factor missing in code; `kappa` uses `(N−1)` where paper has `|A|` |
| van der Heijden 2018 (CCF, Def 5) | FAITHFUL | `opinion.py:490-611` implements Eqs 6–12 binomial reduction; docstring derivation is correct |
| van der Heijden 2018 (base-rate handling) | DEVIATION (documented) | `opinion.py:31, 446-458, 600-609`; paper requires shared base rates as precondition, propstore confidence-weights and clamps to `[0.01, 0.99]` |
| Jøsang 2001 (consensus Theorem 7) | FAITHFUL | `opinion.py:330-351` matches PNG p.24-25 after algebraic `v = 1 - u` substitution |
| Jøsang 2001 (discount Def 14) | FAITHFUL | `opinion.py:383-387` matches PNG p.23 element-wise |
| Jøsang 2001 (conjunction Theorem 3, disjunction Theorem 4, negation Theorem 6) | FAITHFUL | `opinion.py:114-155`, formulas match verbatim |
| Jøsang 2001 (uncertainty maximization Def 16) | FAITHFUL | `opinion.py:239-273` with `a ∈ (0,1)` precondition documented |
| Jøsang 2001 (BetaEvidence bijection Def 12) | FAITHFUL | `opinion.py:101-110, 295-301`, W=2 |
| Jøsang 2001 (division / "un-consensus", §6.4) | MISSING | no `division` / `reverse_consensus` operator; CLAUDE.md calls core complete — ambiguous whether §6.4 division counts as core |
| Denoeux 2018 (pignistic Eq 30b) | **DRIFT** — terminology vs. formula | `world/types.py:1064-1066` labels `b + a·u` "pignistic" citing Denoeux p.17-18; actual Denoeux BetP(x) for binomial is `b + u/2`; diverges whenever `a ≠ 0.5` |
| Denoeux 2018 (Hurwicz Eq 27) | FAITHFUL | `world/types.py:1073-1077`, α=1 pessimistic / α=0 optimistic convention matches |
| Denoeux 2018 (lower/upper) | FAITHFUL | `world/types.py:1067-1072`, matches Bel/Pl |
| Denoeux 2018 (interval dominance, E-admissibility, maximality) | MISSING (CLAUDE.md acknowledged) | no code paths |
| Amgoud 2017 / Baroni 2019 (DFQuAD principles) | PARTIAL | `tests/test_dfquad.py` covers Freedman 2025 Props 3–4 (monotonicity, contestability, bounds) and Baroni GP1–GP3; **no tests** for GP4/GP5 (completeness), GP6 (isomorphism), GP7–GP11 (franchise / independence / stability / reinforcement / weakening soundness / strengthening soundness); no Amgoud 2017 principle names appear in tests |
| Chan 2005 (probabilistic distance) | NOT USED HERE | not referenced by `opinion.py`, `calibrate.py`, or praf modules |

## Findings

### F1 — wbf() is aCBF (self-declared; CONFIRMED against paper PNG)

File: `propstore/opinion.py:419-442`
Paper: van der Heijden 2018 Def 4 Case 1 (pngs/page-004.png)

The belief numerator in code is missing the per-source `(1 − u^A_X)` factor
the paper requires:

```python
# opinion.py:419-422
num_b = sum(
    op.b * prod_except[i]
    for i, op in enumerate(opinions)
)
```

Paper formula:
```
b^{A∪}_X(x) = Σ_A [ b^A_X(x) · (1 − u^A_X) · Π_{A'≠A} u^{A'}_X ]
              / [ Σ_A Π_{A'≠A} u^A_X − |A| · Π_A u^A_X ]
```

Three divergences:
1. Belief numerator lacks `(1 − u^A_X)` on every term.
2. Denominator `opinion.py:430`: `kappa = sum(prod_except) - (N - 1) * total_prod`. Paper has `|A|` (= N), not `N − 1`.
3. Uncertainty numerator `opinion.py:427`: `num_u = total_prod`. Paper has `(|A| − Σ u^A) · Π u^A`, missing `(|A| − Σ u^A)` factor.

Net: the code reduces to the aCBF (averaging cumulative belief fusion) form
rather than WBF. See §"wbf() vs aCBF" below for the numerical divergence.

### F2 — Pignistic label, Jøsang formula

File: `propstore/world/types.py:1064-1066` and `types.py:793-794`
Paper: Denoeux 2018 Eq 30b (pngs/page-017.png)

```python
if criterion == "pignistic":
    # Jøsang (2001, p.5, Def 6): E(ω) = b + a·u
    value = opinion_b + opinion_a * opinion_u
```

`RenderPolicy.decision_criterion` default `"pignistic"` with docstring citing
Denoeux (2019, p.17-18). Actual Denoeux BetP (Smets) formula for binomial
`{x, ¬x}`: `BetP(x) = b + u/2` — uniform split of ignorance mass, base-rate
independent. Code uses Jøsang E(ω) = `b + a·u` — collapses to BetP only when
`a = 0.5`.

Impact: any claim with a non-0.5 calibrated base rate (corpus frequency prior,
per-category base rate in `calibrate.py:212-217`) gets a rendered decision
value that drifts from the paper the docstring cites. For `a=0.7, u=0.3`
delta is 0.06 (0.21 vs 0.15 on the ignorance contribution).

Either the formula should change to `b + u/2` (Denoeux) or the label should
change to `"projected_probability"` / the docstring should cite Jøsang Def 6
rather than Denoeux.

### F3 — No provenance-enforcing type boundary for Opinion

File: `propstore/opinion.py:40-51`, `probabilistic_relations.py:50-51`

`Opinion` is a plain frozen dataclass of `(b, d, u, a)` floats. No provenance
field. `ProbabilisticRelation` carries a separate `provenance:
RelationProvenance | None = None` that is not attached to the Opinion
itself.

Raw `Opinion(b, d, u, a)` coercion sites found with no enforced provenance:
- `praf/engine.py:216-222` — `omega_source_quality = Opinion(float(q["b"]), ...)` from payload dict.
- `praf/engine.py:241` — `Opinion(b, d, u, a)` from stance row columns.
- `praf/engine.py:1366` — `Opinion(acceptance[edge], 1.0 - acceptance[edge], 0.0, 0.5)` from MC marginal.
- `core/claim_values.py:60-65` — `Opinion(float(payload["b"]), ...)` from persisted JSON.
- `fragility_scoring.py:301` — `Opinion(b_new, d_new, u_new, a)` from synthetic perturbation.

CLAUDE.md principle ("Every probability that enters the argumentation layer
must carry provenance") — not enforced mechanically. Passes through pure
discipline that is violated at least at the payload-rehydration sites.

### F4 — `summarize_defeat_relations` fabricates dogmatic opinions

File: `propstore/praf/engine.py:1318-1372`

```python
# engine.py:1366
opinion=Opinion(acceptance[edge], 1.0 - acceptance[edge], 0.0, 0.5)
```

A sampled / enumerated marginal probability is packaged as an opinion with
`u = 0` — dogmatic. This is a vacuous-principle violation of the same shape
as the old `_ccf_average` bug: presents a point estimate as absolute
certainty. The function is documented as diagnostic-only, but the record
type is the same `ProbabilisticRelation` used everywhere else; nothing
prevents downstream code from consuming it.

A correct encoding would use Jøsang's `from_probability(p, n_eff)` with
`n_eff` reflecting the sample count (for MC) or 1 / enumeration-scale (for
exact), leaving `u > 0` commensurate with the estimator's standard error.

### F5 — `enforce_coh` silently relaxes dogmatic inputs

File: `propstore/praf/engine.py:283-289, 320-332`

When rebuilding evidence counts for COH scaling:

```python
# engine.py:287-289
if op.u > 1e-9:
    evidence_n[arg] = W * (1.0 / op.u - 1.0)
else:
    evidence_n[arg] = 10.0  # default for dogmatic opinions
```

A dogmatic input `(1, 0, 0, a)` becomes a new opinion with `n=10` evidence —
no longer dogmatic. Round-trip is not identity. Also, the "default for
dogmatic opinions" has no paper citation; `n=10` is a magic number.

### F6 — `p_relation_from_stance` sharp dogmatic thresholds

File: `propstore/praf/engine.py:243-250`

```python
if confidence >= 1.0 - 1e-12:
    return Opinion.dogmatic_true(a)
if confidence <= 1e-12:
    return Opinion.dogmatic_false(a)
return from_probability(confidence, 1)
```

A confidence of `0.9999999999999` (13 nines) becomes dogmatic_true; one of
`0.9999999999` (10 nines) becomes `from_probability(0.9999999999, 1)` →
`u = 2/3`, strong but non-dogmatic. Discontinuity is 13 orders of magnitude
on the input, two orders of magnitude on the u output. No paper citation for
the threshold choice.

Also, `from_probability(p, n=1)` for any `0 < p < 1` gives:
`u = W / (p·1 + (1-p)·1 + W) = 2/3`. Every non-dogmatic confidence gets the
same uncertainty regardless of how "confident" the classifier was. The
caller is not conveying sample-size information and probably should.

### F7 — `classify.py` writes invariant-violating opinion when None

File: `propstore/classify.py:148-161`

When `opinion is None`:
```python
"opinion_belief": 0.0,
"opinion_disbelief": 0.0,
"opinion_uncertainty": 0.0,
"opinion_base_rate": 0.5,
```

`b + d + u = 0`, fails Opinion's `|b+d+u - 1| < _TOL` post-init invariant.
Round-trip through `Opinion(0, 0, 0, 0.5)` raises `ValueError`. Axis 5
already flagged this; remains open.

Correct value should be `(0, 0, 1, 0.5)` (vacuous) or the column should be
a distinguishable "no-opinion" sentinel (`NULL` in SQL).

### F8 — DFQuAD cycle handling swallows non-convergence

File: `propstore/praf/dfquad.py:174-188`

```python
if remaining:
    for _iteration in range(100):
        max_delta = 0.0
        for arg in remaining:
            ...
            strengths[arg] = new_strength
        if max_delta < 1e-9:
            break
```

If the fixpoint does not converge in 100 iterations, the loop exits
silently with the last-computed strengths. No warning, no exception, no
return-value flag. Freedman 2025 assumes acyclic QBAFs; when the assumption
is violated and the fixpoint diverges, the downstream DecisionValue carries
no indication that the strength is un-converged.

### F9 — Principle coverage holes in DFQuAD tests

Paper: Baroni 2019 GP1–GP11 enumerated in notes.md lines 35-70+
Tests: `tests/test_dfquad.py`

Tested (Freedman 2025-centric):
- GP1 Neutrality / Vacuity (TestNoAttackersNoSupporters)
- GP2 Weakening (TestSingleAttacker)
- GP3 Strengthening (TestSingleSupporter)
- GP7 Weakening Soundness — partial via TestMonotonicityAttacker (Prop 3)
- GP8 Strengthening Soundness — partial via TestMonotonicitySupporter (Prop 3)
- Contestability (Freedman 2025 Prop 4)
- Boundedness (via Hypothesis `test_attack_bounded`)

Not tested (by name or by structure):
- GP4 Weakening Completeness (biconditional)
- GP5 Strengthening Completeness (biconditional)
- GP6 Isomorphism / Equivalence
- GP9 Reinforcement
- GP10 / GP11 (paper-specific higher-order principles)
- Amgoud 2017 principles: anonymity, independence, directionality, equivalence, stability, neutrality, reinforcement, maximality, weakening, counting — grep for these keywords in `tests/` returns zero DFQuAD-relevant hits.

### F10 — Jøsang division / "un-consensus" absent

File: `propstore/opinion.py`

Jøsang 2001 §6.4 defines a division operator (inverse of consensus). Not
implemented. CLAUDE.md says "Core 2001 operators are complete" — this is
either a definitional choice about what counts as "core" (reasonable;
division is hard to define uniquely) or a mild over-claim. Worth flagging
since the text reads as exhaustive.

## wbf() vs aCBF — confirmed discrepancy

**Paper formula** (van der Heijden 2018 Def 4 Case 1, PNG page-004.png):

```
b^{A∪}_X(x) = Σ_{A∈A} [ b^A_X(x) · (1 − u^A_X) · Π_{A'≠A} u^{A'}_X ]
              ───────────────────────────────────────────────────────
              [ Σ_{A∈A} Π_{A'≠A} u^A_X ] − |A| · Π_{A∈A} u^A_X

u^{A∪}_X = [ (|A| − Σ_A u^A_X) · Π_A u^A_X ]
           ────────────────────────────────────────────────────
           [ Σ_A Π_{A'≠A} u^A_X ] − |A| · Π_A u^A_X

a^{A∪}_X(x) = [ Σ_A a^A_X(x) · (1 − u^A_X) ] / [ |A| − Σ_A u^A_X ]
```

**Code formula** (`propstore/opinion.py:413-454`):

```python
total_prod = math.prod(op.u for op in opinions)
prod_except = [total_prod / op.u for op in opinions]

num_b = sum(op.b * prod_except[i] for i, op in enumerate(opinions))
num_d = sum(op.d * prod_except[i] for i, op in enumerate(opinions))
num_u = total_prod

kappa = sum(prod_except) - (N - 1) * total_prod

b_fused = num_b / kappa
u_fused = num_u / kappa
```

**Three divergences:**

1. **Belief numerator** lacks the per-source `(1 − u^A)` factor.
2. **Denominator** uses `(N − 1)` where paper uses `|A| = N`.
3. **Uncertainty numerator** lacks the `(|A| − Σ u^A)` factor.

**Example divergence** — three sources, all with `a = 0.5`:

| Source | b | d | u |
|---|---|---|---|
| A₁ | 0.6 | 0.1 | 0.3 |
| A₂ | 0.5 | 0.2 | 0.3 |
| A₃ | 0.4 | 0.3 | 0.3 |

- `total_prod = 0.027`
- `prod_except = [0.09, 0.09, 0.09]`
- `sum(prod_except) = 0.27`

Code:
- `num_b = 0.09·(0.6+0.5+0.4) = 0.135`
- `kappa = 0.27 - 2·0.027 = 0.216`
- `b_fused = 0.625`
- `num_u = 0.027`
- `u_fused = 0.027 / 0.216 = 0.125`

Paper (WBF):
- `num_b = Σ b·(1-u)·prod_except = 0.09·(0.6·0.7 + 0.5·0.7 + 0.4·0.7) = 0.09·1.05 = 0.0945`
- `kappa_paper = 0.27 - 3·0.027 = 0.189`
- `b_fused_paper = 0.0945 / 0.189 = 0.500`
- `u_num_paper = (3 - 0.9)·0.027 = 2.1·0.027 = 0.0567`
- `u_fused_paper = 0.0567 / 0.189 = 0.300`

Delta on belief: 0.625 vs 0.500 = 0.125 absolute.
Delta on uncertainty: 0.125 vs 0.300 = 0.175 absolute. Non-trivial drift;
the paper-correct fusion preserves much more uncertainty than the code.

The shape of the code formula matches the aCBF (averaging cumulative belief
fusion) family that Jøsang 2016 defines and van der Heijden 2018 corrects
(see notes.md "Corrected Cumulative Belief Fusion"). Commit c7a9215 message
self-declares this as a known bug.

## Secondary papers — cite-check table

| Paper | Cited where | Faithful? |
|-------|-------------|-----------|
| Jøsang 2001 Def 6 (E(ω)) | opinion.py:92, 215, 253; world/types.py:1065 (as "pignistic") | Yes for projected probability; NO as "pignistic" citation |
| Jøsang 2001 Def 10 (ordering) | opinion.py:208 | Yes |
| Jøsang 2001 Def 12 (opinion ↔ evidence) | opinion.py:102, calibrate.py:198-200, 259-260, 309 | Yes, W=2 consistent |
| Jøsang 2001 Def 14 (discount) | opinion.py:365 | Yes — verified against PNG p.23 |
| Jøsang 2001 Def 16 (uncertainty max) | opinion.py:239-242 | Yes |
| Jøsang 2001 Theorem 3/4/6 (conjunction/disjunction/negation) | opinion.py:119, 139, 115 | Yes |
| Jøsang 2001 Theorem 7 (consensus) | opinion.py:321 | Yes — verified against PNG p.24-25 |
| van der Heijden 2018 Def 4 (WBF) | opinion.py:391 | **NO — drift documented in F1** |
| van der Heijden 2018 Def 5 (CCF) | opinion.py:464 | Yes — matches paper PNG p.5 (binomial reduction) |
| van der Heijden 2018 base-rate handling | opinion.py:20-30, 456-458 | Documented deviation |
| Denoeux 2019 p.17-18 (pignistic) | world/types.py:793-794 | **NO — code is Jøsang E(ω), not BetP** |
| Denoeux 2019 p.17 (Hurwicz) | world/types.py:795-798, 1073-1074 | Yes |
| Guo 2017 (temperature scaling) | calibrate.py:39, 60 | Appears correct (golden-section NLL minimization); not deeply audited |
| Guo 2017 (ECE) | calibrate.py:337 | Appears correct |
| Sensoy 2018 (evidence → Dirichlet) | calibrate.py:118, 164, 198, 310 | Uses `r = p·n`, `s = (1-p)·n` — reasonable evidential framing |
| Hunter & Thimm 2017 (COH postulate) | praf/engine.py:262-273 | Enforcement algorithm plausible; silent `n=10` default is drift (F5) |
| Li 2012 (MC Agresti-Coull) | praf/engine.py:1000+ | Appears correct |
| Freedman 2025 (DFQuAD) | praf/dfquad.py:22, 45, 104, 168 | Aggregation and combine formulas match; cycle handling is lax (F8) |

## Open questions

1. **Is the "pignistic" formula in `apply_decision_criterion` supposed to be
   Denoeux BetP or Jøsang E(ω)?** The cite says Denoeux; the formula is
   Jøsang. Picking one resolves the drift but changes observed behavior for
   callers with non-0.5 base rates.

2. **Does `summarize_defeat_relations` (F4) have any callers that feed its
   dogmatic output back into the argumentation engine?** If yes, this is a
   load-bearing vacuous-principle violation; if strictly diagnostic, the fix
   is scoped to its own record type.

3. **Is Jøsang 2001 §6.4 division considered "core"?** CLAUDE.md says core
   is complete; division is absent. Intentional scope decision or
   over-claim?

4. **Does the propstore test suite verify `_ccf_binomial` reproduces Table
   I's `(0.629, 0.182, 0.189)` exactly at runtime?** The docstring asserts
   it; commit c7a9215 adds Hypothesis properties but the Table I
   numerical-regression test was not verified by this scout. Worth
   confirming in CI.

5. **Does `ccf()` preserve base-rate invariance when all sources share
   `a_X`?** Paper Def 5 treats `a_X` as a shared precondition. propstore's
   confidence-weighted blend could drift `a_fused` slightly even when all
   inputs share `a` due to the `_BASE_RATE_CLAMP`. Not verified.

6. **Is there any non-binomial / k-nomial / multinomial code path?** Grep
   found zero uses of "hyper" or "multinomial" outside the
   binomial-only-scope disclaimers in opinion.py. Safe.

---

**Finding counts**: 10 findings (F1–F10). Biggest drift: F1 (`wbf()` is
aCBF — self-declared by commit, CONFIRMED against PNG p.4) and F2
(pignistic label with Jøsang formula).

**Confirmation on `wbf()` divergence**: confirmed against van der Heijden
2018 Def 4 Case 1 (PNG p.4). Three explicit structural divergences with
worked numerical example showing ≥0.125 absolute drift on belief and ≥0.175
on uncertainty for three non-dogmatic sources at `a=0.5`. Code shape
matches aCBF family from Jøsang 2016 that the paper corrects.
