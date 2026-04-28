---
title: "Subjective Logic: A Formalism for Reasoning Under Uncertainty"
authors: "Audun Jøsang"
year: 2016
venue: "Springer, Artificial Intelligence: Foundations, Theory, and Algorithms"
doi_url: "https://doi.org/10.1007/978-3-319-42337-1"
pages: "1-326"
produced_by:
  agent: "claude-opus-4-7"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:23:36Z"
---
# Subjective Logic: A Formalism for Reasoning Under Uncertainty

## One-Sentence Summary

A book-length, comprehensive specification of subjective logic — an algebra of opinions over Dirichlet distributions that generalises probabilistic logic by adding an explicit uncertainty mass and a base-rate distribution, providing closed-form operators for addition, subtraction, multiplication, division, deduction, abduction, fusion, unfusion, fission, trust transitivity, trust fusion, trust revision, and Bayesian network reasoning, and providing direct test cases (worked numerical examples) for each operator *(p.1-326)*.

## Problem Addressed

Probability calculus and Boolean logic cannot represent "I don't know" — `p = 0.5` is informative ("equally likely"), not ignorant. Bayesian probability also conflates base rates and posteriors under a single symbol `p`, hiding the prior contribution and breaking iterated Bayes' theorem unless marginal base rates (MBR) are used. Dempster–Shafer belief theory abandons probability additivity but does not include base rates and is famously brittle under high conflict (Zadeh's counterexample). Fuzzy logic and Kleene three-valued logic capture vagueness or unknowns but not vacuity of evidence. The book argues these gaps demand a formal calculus that (1) makes uncertainty mass a first-class quantity, (2) carries a base-rate distribution alongside belief masses, (3) bijects to the Beta and Dirichlet PDFs, (4) provides closed-form operators that are conservative about uncertainty, and (5) applies uniformly across binary, multinomial, and hyper (powerset) domains — including trust networks, reputation systems, and Bayesian networks *(p.1-6)*.

## Key Contributions

- **Opinion 4-tuple** `ω_x = (b, d, u, a)` for binomial and the triplet `ω_X = (b_X, u_X, a_X)` for multinomial, with simplex constraint `b + d + u = 1` (Eq. 3.1) and projected probability `P(x) = b + a·u` (Eq. 3.2) *(p.24)*.
- **Bijection between subjective opinion and Beta/Dirichlet PDFs** with default non-informative prior weight `W = 2` so that the vacuous opinion `(0,0,1,1/2)` corresponds to the uniform Beta(1,1) (Eq. 3.11, Eq. 3.23) *(p.27-28, p.36)*.
- **Hyper-opinions** over the reduced powerset `R(X) = P(X) \ {{X}, {∅}}`, with cardinality `2^k − 2`, supporting vague belief on composite values (Eq. 2.7, Def 3.7) *(p.9-13, p.39)*.
- **Three masses, three concepts of uncertainty**: vacuity of evidence (uncertainty mass `u`), evidential vagueness (vague belief mass `b^V`), and total ignorance (vacuous opinion). Decomposed as `b^S + b^V + u^F = P(x)` (Eq. 4.9) *(p.51-58)*.
- **Master operator catalogue** (Table 5.3, p.92) — addition, subtraction, complement, multiplication, comultiplication, division, codivision, deduction, abduction, Bayes inversion, joint, fusion (BCF/CBF/ABF/WBF/CCF), unfusion, fission, trust discounting — with closed-form formulas and worked numerical examples for each.
- **Five-class fusion taxonomy with selection flowchart** (Fig. 12.2, p.214): Belief Constraint Fusion (preferences), Cumulative Belief Fusion (independent evidence), Averaging Belief Fusion (dependent sources), Weighted Belief Fusion (confidence-weighted experts), Consensus & Compromise Fusion (preserves shared belief, redistributes conflict as vague belief).
- **Subjective Bayes' Theorem with marginal base rate** (Eqs. 9.9, 9.36, 10.27, 10.52) — required for repeated-inversion consistency; uncertainty masses grow under repeated inversion.
- **Computational trust networks** with probability-sensitive trust discounting `⊗`, transitive trust through paths, parallel trust fusion, and conflict-aware trust revision (Ch. 14-15).
- **Subjective Bayesian and subjective networks** — replaces probabilistic conditionals with conditional opinions; chains via deduction `⊙` and abduction `⊙̃`; integrates with subjective trust networks via the two-layer "frame of sources / frame of variables" architecture (Ch. 17, Fig. 17.14).

## Methodology

The book is a formal specification with proofs at the level of "stated, justified, and demonstrated by worked numerical example." Theorems are stated and proved (e.g., Theorem 7.1 on the analytical PDF of a binary uniform product, Theorem 12.1 on equivalence between stochastic and belief constraint fusion, Theorem 12.2 on CBF as evidence parameter addition, Theorem 12.3 on ABF as evidence parameter averaging, Theorem 12.4 on WBF as confidence-weighted evidence averaging). Operator validity is established by showing (a) closed-form formulas for `(b, d, u, a)` of the result, (b) homomorphism to projected probabilities (e.g., `P(x∧y) = P(x)·P(y)` in Eq. 7.2), (c) properties such as commutativity, idempotence, neutral element, and (d) a worked numeric example with the input opinion vectors and the resulting opinion vector. Approximations (e.g., binomial multiplication is exact in projected probability but approximate in variance) are explicitly flagged with comparison to the analytical Beta product PDF `−ln(p)` (Theorem 7.1, Fig. 7.4). Notation is layered: belief notation `(b, d, u, a)`, evidence notation `(r, s, a)`, probabilistic notation `π_x = (P, u, a)` — operators are isomorphic across all three (Sec. 3.7).

## Key Equations / Statistical Models

This book defines hundreds of equations. Below is a representative anchor set, organized by chapter. The complete catalog appears under **Equation Catalog** further below.

### Foundational opinion algebra

$$b_x + d_x + u_x = 1 \quad (3.1)$$
Binomial opinion simplex constraint *(p.24)*.

$$P(x) = b_x + a_x u_x \quad (3.2)$$
Binomial probability projection — the most important formula in subjective logic. Uncertainty mass is partitioned by base rate `a_x` *(p.24)*.

$$\text{Var}(x) = \frac{P(x)(1 - P(x)) u_x}{W + u_x} \quad (3.3, 3.10)$$
Binomial opinion variance, derived from Beta(α, β). At `u = 0` the variance vanishes (Dirac); at `u = 1` it equals `P(1−P)/(W+1)` *(p.27)*.

$$\text{Beta}(p_x, \alpha, \beta) = \frac{\Gamma(\alpha + \beta)}{\Gamma(\alpha)\Gamma(\beta)} p_x^{\alpha - 1}(1 - p_x)^{\beta - 1} \quad (3.6)$$
Beta PDF, with `α = r_x + a_x W`, `β = s_x + (1-a_x) W` *(p.26-27)*.

$$\begin{cases} b_x = r_x / (W + r_x + s_x) \\ d_x = s_x / (W + r_x + s_x) \\ u_x = W / (W + r_x + s_x) \end{cases} \Leftrightarrow \begin{cases} u_x \neq 0: r_x = b_x W / u_x, \; s_x = d_x W / u_x \\ u_x = 0: r_x = b_x \cdot \infty, \; s_x = d_x \cdot \infty \end{cases} \quad (3.11)$$
Bijection between binomial opinion and Beta PDF. Default `W = 2` *(p.28)*.

$$\mathbf{P}_X(x) = \mathbf{b}_X(x) + \mathbf{a}_X(x) u_X \quad (3.12)$$
Multinomial probability projection *(p.30)*.

$$\text{Dir}(p_X, \alpha_X) = \frac{\Gamma(\sum \alpha_X(x))}{\prod \Gamma(\alpha_X(x))} \prod p_X(x)^{\alpha_X(x)-1} \quad (3.14)$$
Dirichlet PDF; `α_X(x) = r_X(x) + a_X(x)·W` (Eq. 3.15) *(p.32)*.

$$\begin{cases} b_X(x) = r_X(x)/(W + \sum r_X(x_i)) \\ u_X = W/(W + \sum r_X(x_i)) \end{cases} \Leftrightarrow \begin{cases} r_X(x) = W b_X(x)/u_X \\ \sum b_X(x_i) + u_X = 1 \end{cases} \quad (3.23)$$
Multinomial opinion ↔ Dirichlet PDF bijection *(p.36)*.

$$\ddot u_X = \min_i \!\left[\frac{P_X(x_i)}{a_X(x_i)}\right] \quad (3.27)$$
Theoretical maximum uncertainty preserving projected probability — used for uncertainty-maximised opinions, IDM, fusion *(p.37-38)*.

$$P_X(x) = \sum_{x_i \in R(X)} a_X(x|x_i)\,b_X(x_i) + a_X(x)\,u_X \quad (3.28)$$
Hyper-opinion projection to singleton probability *(p.40)*.

$$b'_X(x) = \sum_{x' \in R(X)} a_X(x|x')\,b_X(x') \quad (3.30)$$
Hyper-opinion → multinomial projection *(p.40)*.

### Decision making and entropy (Ch. 4)

$$b^S_X(x) = \sum_{x_i \subseteq x} b_X(x_i),\quad b^V_X(x) = \sum_{x_j \in C(X), x_j \not\subseteq x} a_X(x|x_j) b_X(x_j),\quad u^F_X(x) = a_X(x) u_X \quad (4.1, 4.3, 4.8)$$
Sharp, vague, and focal uncertainty mass per value. `b^S + b^V + u^F = P(x)` (Eq. 4.9) *(p.51-58)*.

$$L_X(x) = \lambda_X(x) P_X(x);\quad P^N_X(x) = \frac{\lambda_X(x) P_X(x)}{\lambda^+} \quad (4.13, 4.15)$$
Utility / utility-normalised probability *(p.60)*.

$$H^P(\omega_X) = -\sum P_X(x) \log_2 P_X(x);\quad H^S + H^V + H^U = H^P \quad (4.55, 4.59)$$
Opinion entropy decomposition into sharpness, vagueness, uncertainty *(p.78)*.

$$\mathrm{DC}(\omega^B, \omega^C) = \mathrm{PD} \cdot \mathrm{CC} \quad (4.63)$$
Degree of conflict, with `PD = (1/2)Σ|P^B - P^C|`, `CC = (1-u^B)(1-u^C)` *(p.80)*.

### Operators (Chs. 6-8)

$$b_{x_1 \cup x_2} = b_{x_1} + b_{x_2};\quad u_{x_1 \cup x_2} = (a_{x_1} u_{x_1} + a_{x_2} u_{x_2})/(a_{x_1}+a_{x_2});\quad a_{x_1 \cup x_2} = a_{x_1}+a_{x_2} \quad (6.1)$$
Addition: disjoint subsets, union; `P(x_1∪x_2) = P(x_1)+P(x_2)` *(p.95)*.

$$b_{\bar x} = d_x;\quad d_{\bar x} = b_x;\quad u_{\bar x} = u_x;\quad a_{\bar x} = 1 - a_x \quad (6.6)$$
Complement; `P(¬x) = 1 - P(x)` *(p.99)*.

$$b_{x \wedge y} = b_x b_y + \frac{(1-a_x)a_y b_x u_y + a_x(1-a_y)u_x b_y}{1 - a_x a_y};\;\; d_{x \wedge y} = d_x + d_y - d_x d_y;\;\; u_{x \wedge y} = u_x u_y + \frac{(1-a_y)b_x u_y + (1-a_x)u_x b_y}{1 - a_x a_y};\;\; a_{x \wedge y} = a_x a_y \quad (7.1)$$
Binomial multiplication; `P(x∧y) = P(x)P(y)` (Eq. 7.2) *(p.102)*.

$$b_{x \vee y} = b_x + b_y - b_x b_y;\;\; d_{x \vee y} = d_x d_y + \frac{a_x(1-a_y) d_x u_y + (1-a_x) a_y u_x d_y}{a_x + a_y - a_x a_y};\;\; u_{x \vee y} = u_x u_y + \frac{a_y d_x u_y + a_x u_x d_y}{a_x + a_y - a_x a_y};\;\; a_{x \vee y} = a_x + a_y - a_x a_y \quad (7.3)$$
Binomial comultiplication; `P(x∨y) = P(x) + P(y) - P(x)P(y)` (Eq. 7.4) *(p.103)*.

### Conditional reasoning (Ch. 9-10)

$$a_y = \frac{a_x b_{y|x} + a_{\bar x} b_{y|\bar x}}{1 - a_x u_{y|x} - a_{\bar x} u_{y|\bar x}} \quad (9.36)$$
Binomial Marginal Base Rate (MBR); valid when `u_{y|x} + u_{y|\bar x} < 2` *(p.165)*.

$$\boldsymbol a_Y(y) = \frac{\sum_x \boldsymbol a_X(x) \boldsymbol b_{Y|x}(y)}{1 - \sum_x \boldsymbol a_X(x) u_{Y|x}} \quad (9.57, 9.68)$$
Multinomial MBR *(p.173, 177)*.

$$\omega_{y\|x} = \omega_x \odot (\omega_{y|x}, \omega_{y|\bar x}) \quad (9.27)$$
Binomial deduction (closed-form Definition 9.1, nine cases on K coefficient).

$$\omega_{Y\|X} = \omega_X \odot \boldsymbol \omega_{Y|X} \quad (9.30, 9.79)$$
Multinomial deduction (3-step procedure: MBR, sub-simplex apex, projection).

$$P_{X|y_j}(x) = \frac{a_X(x)\,P_{Y|x}(y_j)}{\sum_i a_X(x_i)\,P_{Y|x_i}(y_j)} \quad (10.36)$$
Multinomial Bayes inversion at projected-probability level *(p.189)*.

$$u_{X|\widetilde{y_j}} = \ddot u_{X|y_j}\bigl(u^{\mathrm w}_{Y|X} + \overline\Psi(y_j|X) - u^{\mathrm w}_{Y|X}\,\overline\Psi(y_j|X)\bigr) \quad (10.50)$$
Inverted multinomial conditional uncertainty: theoretical max times disjunctive coproduct of weighted proportional uncertainty and irrelevance.

$$\omega_{X\|\widetilde Y} = \omega_Y \,\widetilde\odot\, (\boldsymbol \omega_{Y|X}, \boldsymbol a_X) = \omega_Y \odot \widetilde\phi(\boldsymbol \omega_{Y|X}, \boldsymbol a_X) = \omega_Y \odot \boldsymbol \omega_{X|\widetilde Y} \quad (9.31, 10.53-10.56)$$
Multinomial abduction = inversion (Bayes) then deduction.

### Fusion (Ch. 12)

$$b_X^{(A\&B)}(x) = \frac{\mathrm{Har}(x)}{1 - \mathrm{Con}};\quad u_X^{(A\&B)} = \frac{u_X^A u_X^B}{1 - \mathrm{Con}} \quad (12.2)$$
Belief Constraint Fusion (BCF). Undefined when `Con = 1`.

$$b_X^{(A\diamond B)}(x) = \frac{b_X^A(x) u_X^B + b_X^B(x) u_X^A}{u_X^A + u_X^B - u_X^A u_X^B};\quad u_X^{(A\diamond B)} = \frac{u_X^A u_X^B}{u_X^A + u_X^B - u_X^A u_X^B} \quad (12.14)$$
Aleatory Cumulative Belief Fusion (CBF) ⊕. Equivalent to evidence-vector addition `r^{A⋄B}(x) = r^A(x) + r^B(x)` (Theorem 12.2, Eq. 12.17).

$$b_X^{(A\diamond B)}(x) = \frac{b_X^A(x) u_X^B + b_X^B(x) u_X^A}{u_X^A + u_X^B};\quad u_X^{(A\diamond B)} = \frac{2 u_X^A u_X^B}{u_X^A + u_X^B} \quad (12.18)$$
Averaging Belief Fusion (ABF) ⨁. Equivalent to evidence averaging `r^{A⋄B}(x) = (r^A(x) + r^B(x))/2` (Theorem 12.3).

$$\omega_X^{A\hat\diamond B} = \cdots \quad (12.23-12.25)$$
Weighted Belief Fusion (WBF) ⨁̂ — confidence-weighted, three cases (Case I uncertainty mixing, Case II dogmatic limits, Case III double-vacuous).

CCF (Consensus & Compromise Fusion) three-step (Def 12.9): `b_X^{cons}(x) = min(b_X^A(x), b_X^B(x))` (consensus), residue allocation to compromise vague beliefs, normalised merge with whole-frame mass redirected to uncertainty.

### Trust (Ch. 14)

$$b_X^{[A;B]}(x) = P_B^A \cdot b_X^B(x);\quad u_X^{[A;B]} = 1 - P_B^A \cdot \sum_{x \in R(X)} b_X^B(x);\quad a_X^{[A;B]}(x) = a_X^B(x) \quad (14.5-14.6)$$
Probability-sensitive trust discounting (Def 14.6). Multi-edge: `P_{A_n}^{A_1} = \prod P_{A_{i+1}}^{A_i}` (Eq. 14.13).

$$\mathrm{DC} = \mathrm{PD} \cdot \mathrm{CC};\quad \mathrm{UD}(\omega_B^A | \omega_C^A) = \frac{u_B^A}{u_B^A + u_C^A};\quad \mathrm{RF}(\omega_B^A) = \mathrm{UD} \cdot \mathrm{DC} \quad (14.19-14.24)$$
Trust revision factor used in conflict-aware fusion (Eq. 14.27).

### Reputation (Ch. 16)

$$S = \frac{r + W a}{r + s + W} \quad (16.1)$$
Beta reputation score (binomial) *(p.291)*.

$$R_{y,(\tau+1)} = \lambda \cdot R_{y,\tau} + r_{y,(\tau+1)},\;\; 0 \le \lambda \le 1 \quad (16.5)$$
Reputation ageing with longevity factor `λ`. Geometric convergence `R_∞ = e_y / (1-\lambda)` (Eq. 16.8).

### Subjective networks (Ch. 17)

$$\omega_{X_K | X_1} = \mathsf M_{I=2}^K (\omega_{X_I | X_{I-1}}) \quad (17.13)$$
Chained conditional opinions via deduction.

$$\omega_{X_1 \widetilde | X_K} \approx \widetilde\phi\bigl(\mathsf M_{I=2}^K(\omega_{X_I|X_{I-1}}), a_{X_1}\bigr) \quad (17.16)$$
Chained-then-inverted alternative to Eq. 17.15 (invert each then chain). Validation Eq. 17.18: equal projected probabilities, approximately equal uncertainty.

$$\omega_Z^A = (\omega_X^{[A;B]} \odot \omega_{Y|X}^{[A;C]}) \odot \omega_{Z|Y}^{[A;D]} \quad (17.35)$$
Subjective network derivation with trust transitivity and SBN deduction.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Non-informative prior weight | W | — | **2** | W > 0 | 27, 30, 32, 291 | The single most important magic number; W=2 makes Beta(1,1) (uniform) the prior under r=s=0, a=1/2. Larger W desensitises posterior to new evidence. Setting W = k yields uniform PDF on k-domain but is impractical for large k. |
| Default singleton base rate | a_X(x) | — | 1/k | (0,1) | 14, 32 | k = \|X\|. Each singleton equiprobable a priori. |
| Default composite base rate | a_X(x_i) | — | n_i/k | (0,1] | 14 | n_i = number of singletons in composite x_i. Super-additive over R(X). |
| Belief mass (singleton) | b_x | — | — | [0,1] | 13, 24 | |
| Disbelief mass (binomial) | d_x | — | — | [0,1] | 24 | Binomial only; for multinomial there is just the b_X distribution. |
| Uncertainty mass | u_x, u_X | — | — | [0,1] | 13, 24, 30 | u=1 → vacuous (honest ignorance); u=0 → dogmatic (Dirac PDF). |
| Confidence | c_X | — | 1 - u_X | [0,1] | 50 | Eq. 3.43. Meaningful for binomial/multinomial; not directly meaningful for hyper-opinions (vagueness can coexist with low u). |
| Beta strength | α, β | — | 1, 1 (vacuous default) | α>0, β>0 | 26 | α = r_x + a_x W; β = s_x + (1-a_x) W. |
| Evidence counts | r_x, s_x | counts | 0 prior | r ≥ 0 | 27 | Positive / negative observations. |
| Hyperdomain cardinality | κ | — | 2^k - 2 | — | 10, 41 | Excludes ∅ and X. |
| Domain cardinality | k | — | — | k ≥ 1 | 10 | k=1 trivial; k=2 binomial; k≥3 multinomial. |
| Logarithm base for surprisal | — | base | 2 (bits) | — | 76 | Alternatives: nats (e), hartleys (10). |
| Theoretical max uncertainty | ü_X | — | min_i [P_X(x_i)/a_X(x_i)] | [0,1] | 38, 190 | Used in uncertainty-maximisation, IDM upper/lower probability, fusion proportional methods, abduction. |
| Trust path threshold | p_T | — | — | [0,1] | 283 | Used in non-DSPG trust-network synthesis: exclude paths with P-product below threshold. |
| Reputation longevity factor | λ | — | — | [0,1] | 293 | 0 = full forgetting after each period; 1 = never forgotten. Geometric convergence requires λ < 1. |
| Reputation high-longevity factor | λ_H | — | — | (λ, 1] | 295 | Slower decay for base rate than for ratings. |
| Fission parameter | φ | — | — | (0,1) | 240 | φ ∈ {0,1} produces one vacuous and one identity opinion. |
| Default base rate (binary reputation) | a | — | 0.5 | (0,1) | 291 | Bootstrapping bias possible for hostile/friendly market entry. |
| Lung cancer prior (worked ex.) | a(C) | — | 0.01 | — | 306 | Used throughout SBN worked example. |

## Methods & Implementation Details

- **Three notations are isomorphic** (Sec. 3.7): belief notation `(b, d, u, a)`, evidence notation `(r, s, a)`, probabilistic notation `π_x = (P, u, a)`. All operators have isomorphic forms across the three. Pick one (typically belief notation) for storage and convert at the boundary; never mix in algebra.
- **Default `W = 2` is hard-coded throughout**. Changing W changes every operator output. Do not allow W to be a per-opinion parameter; treat it as a system constant.
- **Vacuous opinion construction**: `vacuous(a_X) := (b = 0_⃗, u = 1, a = a_X)`. The base rate is **still required** even when u = 1 — it is what enables `P(x) = a_X(x)` projection.
- **Dogmatic opinion** (`u = 0`) requires a special branch. The bijection in Eq. 3.11/3.23 maps to `r = b·∞` so cannot be used directly. Implementations typically store dogmatic opinions as a flag plus the belief vector.
- **Bijective mapping at endpoints**: at `α < 1` the Beta density blows up at p = 0; at `β < 1` it blows up at p = 1. PDF integration code must handle endpoints carefully.
- **Multinomial multiplication has three methods** (Sec. 8.1): normal (Eq. 8.18-8.19, most conservative, preserves max uncertainty), proportional (Eq. 8.22-8.25, ~50% less uncertainty), projected (Sec. 8.1.5, hardly any uncertainty). All produce identical projected probability `P_{XY} = P_X · P_Y`. Normal is the recommended default; projected is only safe for near-dogmatic factors.
- **Multinomial division has no general analytical solution** (Sec. 8.3). Two partial methods: averaging-proportional (Eq. 8.45-8.55, round-trip lossy) and selective (Eq. 8.57-8.61, requires single observed `y_j`).
- **Binomial deduction is a closed-form 9-case selector on K** (Definition 9.1, Eqs. 9.40-9.51). The cases branch on (a) sign of `b_{y|x} - b_{y|\bar x}` and `d_{y|x} - d_{y|\bar x}`, (b) position of `P(y\|\hat x)` relative to a threshold, and (c) `P(x)` vs `a_x`. Test in order: I, II.A.1, II.A.2, II.B.1, II.B.2, III.A.1, III.A.2, III.B.1, III.B.2.
- **Multinomial deduction is a 3-step algorithm** (Sec. 9.5.4): (1) compute MBR `a_Y` via Eq. 9.68; (2) compute sub-simplex apex opinion `ω_{Y\|\hat X}` via Eqs. 9.69-9.74 enforcing Pearl's plausible-reasoning constraint; (3) project `ω_X` onto the sub-simplex via Eqs. 9.75-9.78.
- **Repeated Bayes inversion only converges with MBR** (Eqs. 9.24, 9.36, 9.57). Without MBR, conditionals drift after multiple inversions. Projected probabilities are stationary under repeated `\widetilde\phi` with MBR; uncertainty masses grow monotonically toward theoretical maxima `\ddot u`.
- **Subjective Bayes' theorem 4-step uncertainty algorithm** (Sec. 10.3.2): theoretical max uncertainties → weighted proportional uncertainty → coproduct with irrelevance `\overline\Psi(y|X)` → multiply.
- **Naïve Bayes assumption** is required when joint conditionals `ω_{Z|XY}` are unavailable; replaced with product `∏ ω_{Z|·}` of single-variable conditionals (Eq. 17.27, 17.33).
- **Subjective conditional independence requires absolute conditioning opinion** (Definition 17.2). With uncertain conditioning, dependencies "reactivate" — do not prune SBN edges based purely on the underlying BN topology when evidence is itself uncertain.
- **Subjective Network = SBN + STN** (Fig. 17.14). Two-layer architecture: frame of sources (agents) modelled as STN; frame of variables (world) modelled as SBN. Conditional and evidence opinions for the SBN flow from fusion+discounting over the STN. Belief fusion operators apply only to source fusion in the STN frame, never to "fuse variables" in the SBN frame.
- **DSPG analysis algorithm** (Sec. 15.3.1, Fig. 15.5): identify each PPS by source-target, compute nesting level, process highest-nesting PPS first by discounting all paths and fusing, then re-evaluate nesting level. Series-only collapses last.
- **Reputation cold start**: use community base rate `a` directly for unrated objects; can bias to negative for harder market entry or positive for easier (Eq. 16.9, two-layered base rate). For ageing, λ ∈ [0,1) for finite convergence.
- **Coproduct operator** `a ⊔ b = a + b - a·b` (used in Eq. 10.23, 10.49, 14.20). Inclusion-exclusion for two events; identity element 0, absorbing element 1.

## Figures of Interest

Illustrations are central to subjective logic — opinion triangles (binomial), tetrahedra (multinomial k=3), and barycentric projector/director geometry. Selected figures:

- **Fig. 1.1 (p.4):** Subjective Logic = Probabilistic Logic + Uncertainty & Subjectivity.
- **Fig. 2.3 (p.9):** Hyperdomain of a ternary domain — Venn-style diagram with three singletons and three pair-composites.
- **Fig. 3.1 (p.25):** Barycentric triangle for binomial opinion; projector line from opinion point parallel to director.
- **Fig. 3.2 (p.29):** Beta(p_x, 3.8, 1.2) PDF plot for example opinion.
- **Fig. 3.3 (p.31):** Tetrahedron for trinomial opinion.
- **Fig. 3.6 (p.38):** Uncertainty-maximised opinion `ω̈` with projector and director lines.
- **Fig. 3.7 (p.46):** Hyper-Dirichlet PDFs; non-Dirichlet shapes.
- **Fig. 4.7 (p.64):** Decision flowchart with four priority levels (probability, sharpness, focal uncertainty, base rate / vagueness).
- **Fig. 4.8-4.10 (p.65-68):** Ellsberg paradox hyperdomain Venn and game mass-sums.
- **Fig. 4.11-4.13:** Decision games 1, 2, 3 mass-sum diagrams.
- **Fig. 5.2 (p.88):** Multiplication of two vacuous opinions.
- **Fig. 6.2-6.5 (p.96-100):** Addition, subtraction, complement examples on opinion triangles.
- **Fig. 7.2-7.8 (p.103-113):** Multiplication, comultiplication, division, codivision examples; reliability network examples (Fig. 7.5-7.6).
- **Fig. 7.4 (p.106):** Beta(p,1/2,3/2) vs `−ln(p)` — SL approximation vs analytical product PDF.
- **Fig. 9.5-9.7 (p.148-149):** Vacuous-antecedent deduction with MBR / upper / lower free base rate.
- **Fig. 9.9 (p.153):** Sub-triangle apex `ω_{y\|\hat x}` projection.
- **Fig. 10.1 (p.176/png 194):** Inversion of binomial conditionals — uncertainty grows.
- **Fig. 10.2 (p.178/png 196):** Dogmatic vs uncertainty-maximised inverted conditional.
- **Fig. 10.4-10.6 (p.184-186):** Medical-test abduction examples — base-rate fallacy made visible.
- **Fig. 10.7 (p.187):** Multinomial abduction with poor-quality test, irrelevance `\overline\Psi(y|X) = 0.80` → resultant uncertainty 0.72.
- **Fig. 11.x:** Joint and marginal opinions for the match-fixing example.
- **Fig. 12.1 (p.208):** Belief fusion process schematic.
- **Fig. 12.2 (p.214):** Fusion operator selection flowchart (BCF/CBF/ABF/WBF/CCF four binary branches).
- **Fig. 12.4 / 12.5 (p.228-229):** Aleatory vs epistemic CBF visual difference.
- **Fig. 13.1 (p.237):** Unfusion principle.
- **Fig. 14.1 (p.246):** Same reliability trust, different decision trust (fire-drill vs real-fire).
- **Fig. 14.2-14.3:** Transitive trust derivation chains.
- **Fig. 14.4 (p.255):** Trust-discounting principle — derived opinion confined to scaled sub-triangle.
- **Fig. 14.5 (p.256):** Probability-sensitive trust discounting on opinion triangle.
- **Fig. 14.6 (p.258):** Restaurant advice screenshot.
- **Fig. 14.10 (p.268):** Trust revision moves opinion toward distrust vertex.
- **Fig. 15.1 (p.272):** Stepwise SP-graph reduction.
- **Fig. 15.2-15.3 (p.274-275):** PPSs and nesting levels.
- **Fig. 15.5 (p.277):** DSPG analysis flowchart algorithm.
- **Fig. 15.6 / 15.7 (p.278-279):** Incorrect vs correct way of receiving advice opinions.
- **Fig. 15.8 (p.280):** Non-DSPG trust network example.
- **Fig. 15.10 (p.283):** DSPG synthesis flowchart.
- **Fig. 16.1 (p.290):** Reputation system architecture.
- **Fig. 16.2 (p.298):** Score polarisation invisible under point estimate.
- **Fig. 16.3 (p.299):** Continuous→discrete fuzzy triangular mapping.
- **Fig. 17.1 (p.304):** Subjective Networks = SBN + STN.
- **Fig. 17.2 (p.305):** Four BN reasoning categories (predictive, diagnostic, intercausal, combined).
- **Fig. 17.3 (p.306):** Lung cancer BN.
- **Fig. 17.5 (p.311):** Three causality topologies — chain, common cause, common effect.
- **Fig. 17.6-17.7 (p.313-314):** Serial chained conditional opinions; chained inverted conditionals.
- **Fig. 17.8-17.11 (p.317-321):** SBN reasoning patterns.
- **Fig. 17.14 (p.325):** Two-layer SN — frame of sources (STN) above frame of variables (SBN). Trust dashed, belief single arrow, conditional double arrow.

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Binomial example projection | P(x) | 0.76 | — | — | ω_x = (0.40, 0.20, 0.40, 0.90), Beta(3.8, 1.2) | 25, 29 |
| Vacuous binomial Beta | Beta(α,β) | (1, 1) | — | — | ω_x = (0,0,1,1/2) under W=2 | 28 |
| Trinomial projection | P_X | (0.50, 0.25, 0.25) | — | — | b=0.20 each, u=0.40, a=(0.75,0.125,0.125) | 31 |
| Lung cancer (single evidence) | p(C\|D) | 0.25 | — | — | Bayes with base rate 0.01 | 307 |
| Lung cancer (joint evidence) | p(C\|D,X) | 0.97 | — | — | Naïve Bayes with both indicators | 307 |
| Match-fixing deduced | b(y_2)=0.728, P(y_2)=0.739 | — | — | — | ω_X (b₁=0.90, u=0.10) and conditionals | 181 |
| Military intelligence abduction | P(x_1)=0.65, b(x_1)=0.00, u=0.93 | — | — | — | Three-plan, three-troop-movement scenario | 198 |
| Cinema fusion (BCF) | P(GM)=1.00 | — | — | — | Zadeh-numerical inputs (Alice/Bob preferences) | 223 |
| Aleatory CBF example | (0.62, 0.11, 0.27, 0.36, P=0.72) | — | — | — | Two opposed sources | 228 |
| Epistemic CBF example | (0.57, 0.00, 0.43, 0.36, P=0.72) | — | — | — | Same sources, uncertainty-maximised | 229 |
| Trust discounting (vacuous) | P(x)=0.88 | — | — | — | Vacuous trust on Bob with high base rate, Bob's strong belief on x | 258 |
| Trust revision example | P → 0.208 (Claire dominant) | — | — | — | Conflicting restaurant recommendations | 270 |
| Subj. Bayes validation Method 1 | u(z_1)=0.205 | — | — | — | Three-variable chain X⇒Y⇒Z | 315 |
| Subj. Bayes validation Method 2 | u(z_1)=0.184 | — | — | — | Same chain via chain-then-invert | 315 |

## Results Summary

The book demonstrates that subjective logic, as a calculus, satisfies the design goals stated in Ch.1: it represents "I don't know" honestly via vacuous opinions, separates base rate from posterior probability, bijects to Beta/Dirichlet PDFs (Defs 3.3, 3.6, 3.9), generalises probabilistic logic so all standard binary operators emerge as homomorphic limits at u=0, provides selectable fusion operators for distinct evidence-combination situations, supports trust networks with conflict-aware revision, and underpins subjective Bayesian networks that allow per-source uncertainty in conditionals and evidence. The book repeatedly demonstrates correctness through worked numerical examples — every operator section ends with a Figure or Table giving input opinions and resulting opinion. The author concedes the formalism contains conservative approximations (binomial multiplication is exact in projected probability but approximate in variance — Theorem 7.1 vs Beta product `−ln(p)`; multinomial division has no general analytical solution — only synthetic methods; trust revision is "ad hoc"), and explicitly frames the book as "not the final word" *(p.viii, 326)*.

## Limitations

- **Multinomial division has no general analytical solution** (Sec. 8.3). The two partial methods (averaging-proportional and selective) lose information; round-trip `(ω_X · ω_Y) / ω_Y ≠ ω_X` in general.
- **Joint opinion uncertainty is approximate** (Sec. 11.2.2). Marginal-on-X of joint = `ω_X` exactly in projected probability, but uncertainty mass `u_X` may shift by ~30% relative on round-trip. "Exact nature of this approximation needs further investigation" (p.206).
- **Binomial multiplication is approximate** (Sec. 7.1.3, Theorem 7.1). The actual product PDF of two binary uniform variables is `−ln(p)` over (0,1); SL approximates as Beta(p, 1/2, 3/2). Projected probabilities are exact, variances are approximate.
- **Trust revision factor is ad hoc** (p.270). Author explicitly invites alternative designs.
- **Hyper-Dirichlet normalisation B(r,a) has no closed form** (Eq. 3.36-3.38). Numerical integration required (Hankin's R package).
- **Hyper-domain cardinality grows as `2^k − 2`** — for `k = 20`, `κ ≈ 10⁶`. Hyper-opinions are exponential in domain size; use multinomial when composite belief is not needed.
- **Multinomial deduction is iterative/algorithmic, not closed-form** — only the binomial 2x2 case admits the closed-form K-coefficient case analysis (Definition 9.1).
- **Subjective conditional independence requires absolute opinion on conditioning variable** (Definition 17.2). Standard BN edge-pruning under independence does not apply when evidence itself is uncertain.
- **Subjective logic operators are not fully distributive**: `ω_{x ∧ (y ∨ z)} ≠ ω_{(x ∧ y) ∨ (x ∧ z)}` in general (Eq. 5.8, 7.7). De Morgan duality and self-duality (b↔d, a↔1-a, ∧↔∨) hold; full distributivity holds only for absolute opinions (Eq. 5.16).
- **WBF does not leverage shared belief on partially overlapping composite values** (p.231) — sometimes a disadvantage.
- **CCF is semi-associative** — three-way CCF requires single multi-input formulation, not chained pairwise.
- **DSPG synthesis heuristic is greedy by certainty** — not guaranteed optimal; an early high-certainty path can exclude multiple low-certainty incompatible paths whose combination would have higher confidence.
- **Repeated Bayes inversion grows uncertainty toward theoretical maxima `\ddot u`** — long inference chains accumulate uncertainty exponentially. Implication for SBN: long subjective chains yield highly vacuous targets.
- **Approximations are conservative but not always equivalent across notations**: SL multiplication of Beta PDFs is simpler than analytical Bayesian convolution but is an approximation, not equivalent.

## Arguments Against Prior Work

- **Bayesian probability** treats base rate and posterior probability with the same symbol p, conflating them. Subjective logic uses `a` for base rate, `P` for projected probability *(p.5, 156, 326)*.
- **Probability calculus alone cannot represent ignorance**: `p = 0.5` is "equally likely," not "I don't know." Forces analysts to "pull probabilities out of thin air" *(p.4, 21)*.
- **Truth tables in binary logic are redundant** — they all derive from probabilistic-logic operators evaluated at p ∈ {0,1}. Maintaining both is "problematic because of the possibility of inconsistency between definitions" *(p.3)*.
- **Dempster–Shafer Theory ignores base rates** *(p.5, 84)*. Belief mass on the powerset is allowed but no base-rate distribution exists. Subjective logic restores base rates while keeping the powerset structure.
- **Dempster's rule is misused as cumulative fusion** *(p.84, 215, 223)*. It is correctly understood as a constraint fusion operator (preference combination). Zadeh's medical-doctors counterexample (b₁=0.99, b₃=0.99 from two independent doctors) produces counter-intuitive results under Dempster's rule because Dempster's rule is a *constraint* operator. Apply CBF or CCF for evidence accumulation, BCF for preference fusion. The Cinema example (Sec. 12.2.4) uses Zadeh's exact same numerical values and produces the intuitive result with BCF.
- **Imprecise Dirichlet Model upper/lower probabilities are not literal bounds** *(p.85)*. 9-red-1-black-bag counterexample: lower probability of black = 1/3 but actual = 0.1. They should be interpreted as a "rough probability interval," not a literal bound.
- **Fuzzy logic handles vague semantic categories**, not vacuity of evidence *(p.86)*. SL handles crisp categories with uncertainty; combinable but distinct.
- **Kleene three-valued logic** allows TRUE/FALSE/UNKNOWN but does not include base rates, so cannot derive a probability projection from UNKNOWN *(p.25, 87)*. SL's vacuous opinion projects to `P = a`. Also: Kleene fails to converge for infinite series of UNKNOWN — produces UNKNOWN rather than the intuitive FALSE for "infinite series of heads"; SL converges via vacuous-product base-rate reduction *(p.87-88)*.
- **Bayesian theory cannot represent epistemic uncertainty separately from aleatory** *(p.23)*. They are syntactically indistinguishable in pure Bayes. SL makes the distinction syntactic via uncertainty maximisation.
- **Choquet capacities** can explain Ellsberg but cannot distinguish sharp belief, vague belief, and focal uncertainty *(p.69)*. SL subsumes Choquet on the Ellsberg paradox.
- **Material implication is inconsistent with probability calculus** *(p.183-186)*. Truth-functional `(x → y) ⇔ (x̄ ∨ y)` ignores relevance and forces F-antecedent to T regardless. Augmented truth table (Table 9.4) replaces F-antecedent cases with vacuous opinion `(0,0,1,1/2)`. Cited approvingly: Nute & Cross (2002) — "neither material implication nor any other truth function can be used by itself to provide an adequate representation of the logical and semantic properties of English conditionals."
- **Pearl-style Bayesian fusion is not belief fusion** *(p.305)*. Fusion operators of Ch. 12 apply to source fusion in STN; using them in SBN where joint conditionals are required is "approximation at best but ... incorrect in general."
- **Bar-Hillel base-rate fallacy [7,66]** and **prosecutor's fallacy [88]**: classical examples of incorrect intuitive abduction. SL's MBR-required Bayes inversion is the correct calculus.
- **"Enemy of my enemy is my friend" distrust transitivity** is rejected *(p.251)*. The conservative discounting operator interprets distrust as reduced confidence (uncertainty), not as flipped belief.
- **Earlier Jøsang work omitted MBR** *(p.165, p.172)* — author criticises his own [62] for missing MBR in Eq. 9.36 and his [44] for less clear multinomial deduction; updated in [38].

## Design Rationale

- **Why uncertainty mass `u`?** Because probability `p = 0.5` is informative ("equally likely"), not ignorant. The framework needs a syntactic carrier for "I don't know" *(p.4)*. propstore implication: `vacuous` provenance status is a first-class signal, not a special case of `defaulted 0.5`.
- **Why base rates `a`?** Because Bayes' theorem requires priors, and conflating priors with posteriors (under one symbol `p`) hides the distinction. Base rates are "non-informative prior probabilities" — what the analyst would assert with no specific evidence *(p.5, 17)*.
- **Why W = 2 default?** So that the vacuous binomial opinion `(0,0,1,1/2)` maps to the uniform Beta(1,1) — the canonical "I don't know" PDF *(p.27-28)*.
- **Why hyperdomain `R(X) = P(X) \ {{X}, {∅}}`?** To distinguish vague belief on composite values (e.g., "rainy or sunny") from vacuous belief on the entire domain. Belief mass on X itself is reserved for uncertainty mass — DST allows it but SL does not, because evidence can support specific values, never the entire domain *(p.84)*.
- **Why three-method multinomial multiplication?** Because the analytical Beta-product PDF (`−ln(p)` for binary uniform, complex hypergeometric for general) is intractable. Normal preserves max uncertainty (conservative); proportional preserves ~50%; projected hardly any. Choose by need: conservative default (normal), aggressive (projected) *(p.124, 127)*.
- **Why MBR in Bayes?** Because repeated inversion with arbitrary `a(y)` produces non-stationary conditionals; only the marginal base rate (Eq. 9.36, 9.57) preserves projected probabilities under iteration *(p.156, 160, 165)*.
- **Why five fusion operators (BCF/CBF/ABF/WBF/CCF) instead of one?** Because different evidence-combination situations require different operators. Dempster's rule is one of these (BCF), not a universal solution. Selection by four binary criteria: defined-on-total-conflict? idempotent? vacuous-neutral? compromise-via-vague-belief or weighted-average? *(p.213-214)*.
- **Why probability-sensitive trust discounting?** Because trust evidence with low projected probability should reduce confidence in the propagated opinion (uncertainty grows). Distrust does not flip belief — it dampens propagation *(p.251)*.
- **Why two-layer Subjective Network (STN + SBN)?** Because the frame of sources (which agents say what about which variable) and the frame of variables (the world structure) have different operators: trust transitivity / fusion in the STN frame; deduction / abduction / joint product in the SBN frame. Mixing the two layers (e.g., applying fusion to fuse Bayesian classifiers) is "incorrect in general" *(p.326)*.
- **Why uncertainty-maximised epistemic opinions?** Because epistemic situations are not governed by frequentist sampling; uncertainty maximisation makes the syntactic difference between aleatory and epistemic explicit *(p.23, 228)*.
- **Why `b^S + b^V + u^F = P(x)`?** To make decision-making transparent. An option's projected probability decomposes into evidence-supported sharp belief, evidence-supported vagueness, and vacuity-of-evidence focal uncertainty. Decisions can prefer sharp over vague over uncertain *(p.74)*.

## Testable Properties

- **Simplex constraint**: `b + d + u = 1` (binomial), `u + Σ b(x) = 1` (multinomial), `u + Σ_{x ∈ R(X)} b(x) = 1` (hyper) *(p.14, 24)*.
- **Probability projection**: `P(x) = b(x) + a(x)·u` for all opinion classes *(p.24, 30, 40)*.
- **Vacuous projection**: `u = 1 ⇒ P(x) = a(x)` *(p.28, 91)*.
- **Dogmatic variance**: `u = 0 ⇒ Var(x) = 0` (Eq. 3.10) *(p.27)*.
- **Beta bijection round-trip**: For any opinion `(b, d, u, a)` with `u > 0`, mapping to `(α, β)` and back via Eqs. 3.7 and 3.11 returns the original opinion exactly *(p.27-28)*.
- **Vacuous Beta**: `(0, 0, 1, a)` ↔ `Beta(p, W·a, W·(1-a))`; default `a=1/2, W=2` ↔ uniform `Beta(1,1)` *(p.28)*.
- **Coarsening preserves projected probability of singletons**: `P_X(x_i)` is invariant under coarsening that aggregates `x_j` and `x_k` into composite `x_{jk}` *(p.34-35)*.
- **Mass-sum decomposition**: `b^S(x) + b^V(x) + u^F(x) = P(x)` (Eq. 4.9) and `b^TS + b^TV + u = 1` (Eq. 4.11) *(p.51-58)*.
- **Entropy decomposition**: `H^S + H^V + H^U = H^P` (Eq. 4.59) *(p.78)*.
- **Opinion entropy invariance**: opinions with identical projected probability have identical opinion entropy regardless of `u` (Proposition 4.1, Eq. 4.55) *(p.78)*.
- **Multiplication homomorphism**: `P(x ∧ y) = P(x)·P(y)` (Eq. 7.2); `P(x ∨ y) = P(x) + P(y) - P(x)P(y)` (Eq. 7.4) *(p.103)*.
- **Multinomial multiplication projected**: `P_{XY}(xy) = P_X(x)·P_Y(y)` (Eq. 8.8) for all three methods (normal, proportional, projected) — only uncertainty differs *(p.117)*.
- **Multinomial multiplication uncertainty ordering**: `u_{XY}^{normal} ≥ u_{XY}^{proportional} ≥ u_{XY}^{projected}` for the same factors *(p.127)*.
- **Complement involution**: `¬¬ω_x = ω_x`; `P(¬x) = 1 - P(x)` (Eq. 6.8) *(p.99)*.
- **De Morgan in SL**: `ω_{¬(x ∧ y)} = ω_{(¬x) ∨ (¬y)}`, `ω_{¬(x ∨ y)} = ω_{(¬x) ∧ (¬y)}` (Eq. 5.12) *(p.93)*.
- **Distributivity of multiplication over addition**: `ω_{x ∧ (y ∪ z)} = ω_{(x ∧ y) ∪ (x ∧ z)}` (Eq. 5.11) *(p.93)*.
- **Distributivity of multiplication over comultiplication does NOT hold**: `ω_{x ∧ (y ∨ z)} ≠ ω_{(x ∧ y) ∨ (x ∧ z)}` in general (Eq. 5.8) *(p.94)*.
- **Repeated Bayes inversion fixed-point** (with MBR): projected probabilities of conditionals are stationary under repeated `\widetilde\phi`; uncertainty masses are monotone non-decreasing and converge to `\ddot u` *(p.165, 199)*.
- **Marginal-on-X round-trip**: `[X]` of joint `ω_{YX}` equals `ω_X` exactly in projected probability and approximately in uncertainty mass (Eq. 11.21 says exact in uncertainty for a particular construction; the broader text notes ~30% drift in some cases) *(p.202, 206)*.
- **CBF as evidence addition** (Theorem 12.2): under bijection (Def 3.9), `ω^A ⊕ ω^B` equals the opinion derived from `r^A + r^B` (Eq. 12.17) *(p.227)*.
- **ABF as evidence averaging** (Theorem 12.3): `r^{A⋄B}(x) = (r^A(x) + r^B(x))/2` (Eq. 12.21) *(p.230)*.
- **WBF as confidence-weighted Dirichlet averaging** (Theorem 12.4) *(p.233)*.
- **BCF idempotence**: BCF is **non-idempotent** — fusing equal opinions can produce different result.
- **CBF idempotence**: **non-idempotent** — fusing two copies of same evidence accumulates.
- **ABF, WBF, CCF**: idempotent (fusing equal opinions yields equal opinion).
- **Vacuous neutral**: BCF vacuous-neutral by Eq. 12.5; ABF NOT vacuous-neutral; WBF, CCF vacuous-neutral.
- **Trust discounting limit cases**: `P_B^A = 1 ⇒ ω_X^{[A;B]} = ω_X^B` (full trust preserves); `P_B^A = 0 ⇒ ω_X^{[A;B]} = vacuous` (full distrust kills propagation) *(p.256)*.
- **Multi-edge trust path projected probability product**: `P_{A_n}^{A_1} = ∏ P_{A_{i+1}}^{A_i}` (Eq. 14.13).
- **Reputation convergence**: `R_∞ = e_y / (1 - λ)` for constant rating `e_y` per period and `λ < 1` (Eq. 16.7-16.8).
- **Subjective Bayes' theorem validation**: chained-then-inverted (Eq. 17.16) and inverted-then-chained (Eq. 17.15) produce equal projected probabilities and approximately equal uncertainty masses (Eq. 17.18, Table 17.2).
- **Subjective conditional independence**: `X ⊥ Z | Y_abs` only when Y carries an absolute opinion. With uncertain `ω_Y`, `X` and `Z` are dependent through SBN deduction (Definition 17.2) *(p.322)*.

## Relevance to Project

This book is the **canonical formal reference** for the honest-ignorance and uncertainty-as-data principles in propstore. Direct mappings:

- **`vacuous` provenance status** = ω with `u = 1`. Carrying a base rate alongside is non-optional — Eq. 3.2 requires `a` for projection. propstore's vacuous-opinion construction must include a base rate (default `1/k`) per the book's Definition (p.28, p.91).
- **`measured` and `calibrated` provenance** correspond to evidence-bearing opinions with `u < 1`, mapped from Beta/Dirichlet posteriors via Eq. 3.11 / 3.23. propstore's calibration step must yield `(b, d, u)` triples with the bijection respected.
- **`stated` provenance** corresponds to author-asserted opinions where evidence may be absent or sparse — typically high-`u` opinions; ASPIC+ assumptions / facts.
- **`defaulted` provenance** must be explicit: a `defaulted 0.5` is not `vacuous` (Foreword principle quote, p.4). propstore must distinguish them in storage and rendering.
- **ATMS environment labels** map to context-conditional opinions: ATMS environments are set-of-assumption labels; SL conditional opinions `ω_{Y|X}` are functionals from contexts (parent values) to child opinions.
- **Fusion taxonomy** is directly applicable to propstore's render-time multi-source aggregation. Choice of operator depends on how sources relate:
  - Independent measurements → CBF (cumulative).
  - Multiple analysts agreeing/disagreeing → ABF (averaging) or WBF (confidence-weighted).
  - Hard preference constraints → BCF.
  - Compromise on conflicting beliefs preserving shared belief → CCF.
  - **Selection flowchart Fig. 12.2 should be implemented as the default fusion-policy chooser.**
- **Subjective Bayes' theorem with MBR** is required for any propstore reasoning that inverts conditionals (e.g., diagnostic queries). Without MBR, repeated inversion drifts.
- **Subjective conditional independence (Def 17.2)** matters: propstore's SBN-style queries with uncertain evidence must NOT prune dependencies based on the underlying graph alone. When `ω_Y` is uncertain, X and Z dependencies through Y are reactivated.
- **Trust networks and discounting `⊗`** map directly onto propstore's source-trust modelling. Reputation system integration (Eq. 16.20-16.21) provides the canonical pattern: trust-in-source ⊗ source's belief-in-thing.
- **Worked numeric examples are direct test cases**: Match-fixing (p.181, 205), Lung cancer (p.306-308), Subjective Bayes' theorem validation (Table 17.2, p.315), Cinema fusion (p.223-225), Trust revision (p.269-270), Aleatory/Epistemic CBF (Fig. 12.4-12.5).
- **Evidence accumulation `α = r + W·a`, `β = s + W·(1-a)`, `W = 2` default** is the Bayesian update rule for propstore's calibration layer.
- **"Honest ignorance"** principle: vacuous opinion `(0,0,1,a)` is the calibrated answer when evidence is absent. The book frames this as the subject's epistemic prerogative ("Analysts are never forced to invent belief where there is none" — p.21). This is a direct match for propstore's vacuous status.
- **Conflict measure `DC = PD·CC`** (Eq. 4.63, 14.19) is the formal carrier of "two sources disagree" used in trust revision; usable for propstore's stance-conflict adjudication.
- **Reputation as Beta evidence accumulation with longevity factor** (Ch. 16) maps onto propstore's source-quality tracking — for sources that produce repeated calibrated outputs over time.

## Open Questions

- [ ] **Joint opinion uncertainty approximation**: marginal-on-X round-trip drift "needs further investigation" (p.206). For propstore: should propstore tolerate the drift or substitute exact marginals where possible?
- [ ] **Trust revision factor design**: author concedes ad hoc (p.270). Alternative designs welcome. propstore could investigate principled designs based on Bayesian update or AGM-style entrenchment.
- [ ] **Subjective Bayes' theorem validation methods produce slightly different uncertainties** (Table 17.2). Which is preferred? The simpler chained-then-invert (Eq. 17.16) is cheaper but may yield different final uncertainty.
- [ ] **CCF semi-associativity**: when more than two sources need CCF, the multi-input formulation differs from chained pairwise. propstore must implement multi-input CCF, not iterate.
- [ ] **DSPG synthesis heuristic optimality**: greedy-by-certainty is not guaranteed optimal. propstore could implement exhaustive variant when graph small.
- [ ] **Hyper-Dirichlet normalisation**: `B(r,a)` has no closed form; numerical integration via Hankin's R package. For propstore's CEL backend, what numerical method?
- [ ] **Naïve Bayes assumption** in SBN (Eq. 17.27, 17.33): when joint conditionals are unavailable, use product. propstore should declare this as an explicit defeasible step.

## Related Work Worth Reading

(Most directly relevant entries from the 102-reference bibliography. Full list in `citations.md`.)

- **Jøsang [42]** — *A logic for uncertain probabilities*, IJUFKBS 2001. Canonical SL paper. Read first.
- **Jøsang [43]** — *The consensus operator for combining beliefs*, AI 2002. Foundational fusion operator (now CBF).
- **Jøsang [44]** — *Conditional reasoning with subjective logic*, JMVL Soft Comp 2008. Foundational deduction/abduction.
- **Jøsang & Hankin [59]** — *Interpretation and fusion of hyper-opinions*, FUSION 2012. Hyper-opinion formalisation.
- **Jøsang & Kaplan [60]** — *Principles of subjective networks*, FUSION 2016. Foundational SN paper.
- **Jøsang & Sambo [63]** — *Inverting conditional opinions in subjective logic*, MENDEL 2014. Subjective Bayes' theorem.
- **Hankin [33]** — *A generalization of the Dirichlet distribution*, J. Stat. Software 2010. Hyper-Dirichlet PDF formalisation; numerical R package.
- **Pearl [81]** — *Probabilistic Reasoning in Intelligent Systems*, Morgan Kaufmann 1988. Foundational BN; SL borrows MBR pattern and conditional-independence semantics.
- **Pearl [82]** — *Reasoning with belief functions*, IJAR 1990. The plausible-reasoning constraint used in Eq. 9.69.
- **Shafer [90]** — *A Mathematical Theory of Evidence*, Princeton 1976. DST baseline.
- **Zadeh [101]** — *Review of Shafer's Evidence Theory*, AI Magazine 1984. Famous counterexample to Dempster's rule; SL's reinterpretation as constraint fusion.
- **Walley [98]** — *Inferences from Multinomial Data*, JRSS 1996. Imprecise Dirichlet Model baseline.
- **Heuer [34]** — *Psychology of Intelligence Analysis*, CIA 1999. Source of the ACH (Analysis of Competing Hypotheses) framework SL extends.
- **Bar-Hillel & Koehler [7, 66]** — base-rate fallacy in medicine and reconsidered.
- **Robertson & Vignaux [88]** — *Interpreting evidence in the courtroom*, Wiley 1995. Prosecutor's fallacy.
- **Marsh [71]** — *Formalising Trust as a Computational Concept*, PhD 1994. Origin of computational trust.
- **Gambetta [29]** — *Can we trust trust?* 1990. Trust definition baseline.
- **Castelfranchi & Falcone [9]** — *Trust Theory: A Socio-cognitive and Computational Model*, Wiley 2010. Trust theory complement.

## Collection Cross-References

### Already in Collection

- [A Logic for Uncertain Probabilities](../Josang_2001_LogicUncertainProbabilities/notes.md) — Cited as book reference [42]; the canonical foundational subjective-logic paper. This 2016 book is the harmonised, corrected, and extended specification of [42]; the 2001 paper is the seed.
- [A Mathematical Theory of Evidence](../Shafer_1976_MathematicalTheoryEvidence/notes.md) — Cited as book reference [90]. The Dempster–Shafer baseline that the book repeatedly contrasts with. Subjective logic mapping to DST in Eq. 5.1 (`m(x) = b_X(x), m(X) = u_X`); the book reinterprets Dempster's rule as belief constraint fusion (BCF), not cumulative.
- [Inferences from Multinomial Data: Learning About a Bag of Marbles](../Walley_1996_InferencesMultinomialDataLearning/notes.md) — Cited as book reference [98]. Imprecise Dirichlet Model baseline. SL bijection to Dirichlet PDFs is conceptually parallel; the book criticises IDM upper/lower probability as not being literal bounds (p.85, 9-red-1-black-bag counterexample).
- [Unreliable probabilities, risk taking, and decision making](../Gardenfors_1982_UnreliableProbabilitiesRiskTaking/notes.md) — Cited as book reference [31]. Second-order probability literature; foundational for the "probability of probabilities" intuition that subjective logic formalises via uncertainty mass.

### New Leads (Not Yet in Collection)

- **Jøsang & Kaplan (2016) — "Principles of subjective networks", FUSION 2016** — Book reference [60]. The companion paper for Chapter 17. Read for the full subjective-network formalism beyond the book chapter.
- **Hankin (2010) — "A generalization of the Dirichlet distribution", J. Stat. Software** — Book reference [33]. Provides the hyper-Dirichlet PDF used in Section 3.6.5 with no closed-form normalisation. Comes with an R package; relevant for any propstore numerical implementation of hyper-opinions.
- **Pearl (1988) — "Probabilistic Reasoning in Intelligent Systems"** — Book reference [81]. Foundational Bayesian network reference that subjective Bayesian networks (Ch. 17) generalise.
- **Pearl (1990) — "Reasoning with belief functions: An analysis of compatibility", IJAR** — Book reference [82]. Source of the plausible-reasoning constraint enforced in multinomial deduction (Eq. 9.69).
- **Jøsang & Hankin (2012) — "Interpretation and fusion of hyper-opinions in subjective logic", FUSION 2012** — Book reference [59]. Foundational hyper-opinion formalisation, used throughout Sec. 3.6 and Ch. 12.
- **Jøsang & McAnally (2004) — "Multiplication and comultiplication of beliefs", IJAR** — Book reference [51]. Foundational paper for Ch. 7 (binomial multiplication) including Theorem 7.1 (analytical PDF of binary uniform product).
- **Jøsang (2008) — "Conditional reasoning with subjective logic", JMVL Soft Comp** — Book reference [44]. Foundational paper for Ch. 9 (deduction) and Ch. 10 (abduction).
- **Jøsang & Pope (2012) — "Dempster's rule as seen by little colored balls", Comp. Intelligence** — Book reference [53]. Critique of misapplication of Dempster's rule as cumulative fusion.
- **Heuer (1999) — "Psychology of Intelligence Analysis"** — Book reference [34]. Source of the ACH (Analysis of Competing Hypotheses) framework SL extends.
- **Marsh (1994) — "Formalising Trust as a Computational Concept", PhD thesis** — Book reference [71]. Origin of computational trust.
- **Zadeh (1984) — "Review of Shafer's Evidence Theory", AI Magazine** — Book reference [101]. Famous counterexample to Dempster's rule that the book reinterprets as misapplication (Cinema example, p.223).
- **Bar-Hillel / Koehler [7, 66]** — Base-rate fallacy in medicine and reconsidered. Used by the book to motivate MBR-required Bayes inversion.

### Cited By (in Collection)

- [Subjective Logic Encodings for Training Neural Networks with Limited Data](../Vasilakes_2025_SubjectiveLogicEncodings/notes.md) — Cites Jøsang 2016 as the comprehensive textbook reference; uses cumulative fusion and trust discounting operators defined in this book.
- [Multi-Source Fusion Operations in Subjective Logic](../vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/notes.md) — Cites Jøsang 2016 as the operator catalogue reference; extends the fusion-operator family of Ch. 12.
- [Subjective logic as a complementary tool to meta-analysis to explicitly address second-order uncertainty in research findings](../Margoni_2024_SubjectiveLogicMetaAnalysis/notes.md) — Cites Jøsang 2016 as the comprehensive reference for all SL operators including WBF.
- [Evidential Deep Learning to Quantify Classification Uncertainty](../Sensoy_2018_EvidentialDeepLearningQuantifyClassification/notes.md) — Cites Jøsang 2016 as the formal framework for subjective opinions (belief, disbelief, uncertainty, base rate) underpinning the entire evidential deep learning approach.

### Supersedes or Recontextualizes

- [A Logic for Uncertain Probabilities](../Josang_2001_LogicUncertainProbabilities/notes.md) — This book harmonises and corrects [42]; in particular, the 2001 paper's deduction operator did not include MBR, which this book restores (p.165, author's self-correction).

### Conceptual Links (not citation-based)

**Belief functions / DST family:**
- [The Transferable Belief Model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — TBM is an alternative reinterpretation of DST without base rates; SL adds base rates and bijects to Dirichlet PDFs. Both formalisms address the gap between Bayesian probability and DST belief, but along different axes (TBM via two-level credal/pignistic; SL via uncertainty mass + base rate).
- [Decision-Making with Belief Functions: a Review](../Denoeux_2018_Decision-MakingBeliefFunctionsReview/notes.md) — Reviews decision-making in DST family; SL's Ch. 4 decision-making framework (mass-sum, utility-normalisation, priority-ordered criteria) is a complementary treatment of the same problem from the SL angle.
- [Geometry of Uncertainty: The Geometry of Imprecise Probabilities](../Cuzzolin_2021_GeometryUncertaintyGeometryImprecise/notes.md) — Geometric perspective on belief-function family; SL's barycentric simplex / tetrahedron geometry (Figs. 3.1, 3.3) is a specific instance of this broader programme.
- [Axioms for Probability and Belief-function Propagation](../Shenoy_1990_AxiomsProbabilityBelief-functionPropagation/notes.md) — Axiomatises propagation in valuation-based systems; SL Ch. 17 SBN is a concrete propagation framework over subjective opinions.
- [Decision-Making with Belief Functions and Pignistic Probabilities](../Wilson_1993_Decision-MakingBeliefFunctionsPignistic/notes.md) — Wilson's Theorem 5.7 proves that lower/upper expected utility over pignistic transforms across all refinements equals the standard `[Bel, Pl]` envelope expectation. A binomial SL opinion `(b, d, u)` is the `[b, b+u] = [Bel, Pl]` envelope on a binary frame; Wilson's frame-arbitrariness critique therefore lands on the projected probability `E(x) = b + a*u` (frame-dependent), justifying SL's preservation of the full opinion at the source layer with the probability projection deferred to render time. SL's vacuous opinion `b=d=0, u=1` instantiates Wilson's vacuous-belief case where the pignistic collapses to the Principle of Insufficient Reason and the envelope is `[0, 1]`.

**Subjective logic family:**
- [Multiplication of Multinomial Subjective Opinions](../Josang_2010_CumulativeAveragingFusionBeliefs/notes.md) — Jøsang & O'Hara 2010 IPMU paper on multinomial multiplication; this book's Ch. 8 harmonises and extends.
- [Partial Observable Update for Subjective Logic and its Application for Trust Estimation](../Kaplan_2015_PartialObservableUpdateSubjectiveLogic/notes.md) — Kaplan, Sensoy, et al. extend SL with partial-observable update; complements the book's Ch. 14-15 trust-network treatment.

**ATMS / belief-maintenance:**
- [Belief Maintenance System](../Falkenhainer_1987_BeliefMaintenanceSystem/notes.md) — Generalises ATMS with belief functions; SL's hyper-opinion treatment (Sec. 3.6) provides a complementary base-rate-aware model.

**Iterated belief revision:**
- [On the Logic of Iterated Belief Revision](../Darwiche_1997_LogicIteratedBeliefRevision/notes.md) — Darwiche-Pearl iterated revision postulates; SL's repeated Bayes inversion (with MBR) is a specific stationary fixpoint that contrasts with AGM-style revision.
- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md) — Foundational AGM revision; SL trust revision (Ch. 14.5) provides an "ad hoc" alternative for the trust-network domain.
- [Ordinal Conditional Functions: A Dynamic Theory of Epistemic States](../Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md) — OCF as another formalism for graded epistemic states; SL's uncertainty mass plays a parallel but distinct role.

**Information & merging:**
- [Merging Information Under Constraints: A Logical Framework](../Konieczny_2002_MergingInformationUnderConstraints/notes.md) — IC merge for belief sets; SL's Ch. 12 fusion taxonomy (BCF/CBF/ABF/WBF/CCF) is a parallel typology of fusion situations specific to subjective opinions.
- [Information Value Theory](../Howard_1966_InformationValueTheory/notes.md) — Decision-theoretic value of information; SL Ch. 4 utility-normalisation and decision criteria draw on this lineage.

**Sensitivity & uncertainty propagation:**
- [A Distance Measure for Bounding Probabilistic Belief Change](../Chan_2005_DistanceMeasureBoundingProbabilistic/notes.md) — Bounds on probabilistic belief change; SL's degree-of-conflict `DC = PD · CC` (Eq. 4.63) is a coarse alternative measure with complementary properties.
- [Properties of Sensitivity Analysis of Bayesian Belief Networks](../Coupé_2002_PropertiesSensitivityAnalysisBayesian/notes.md) — Sensitivity analysis of BNs; SL's free base-rate intervals (Eqs. 9.37-9.38) and theoretical maximum uncertainty `ü` provide a parallel sensitivity framework for SBNs.

**Provenance:**
- [A Characterization of Data Provenance](../Buneman_2001_CharacterizationDataProvenance/notes.md) — Where-provenance vs why-provenance; SL provenance status (`measured/calibrated/stated/defaulted/vacuous`) needs to track which opinion-construction path produced each `(b, d, u, a)` tuple.
- [Anatomy of a Nanopublication](../Groth_2010_AnatomyNanopublication/notes.md) — Nanopublication model for evidence-bundling; SL's subjective network architecture (Fig. 17.14) similarly bundles agent-source opinions with conditional-opinion structures.

---

# Equation Catalog (organized by chapter)

Below is the full ordered equation list as captured from the chunk readers. Each equation cites its book equation number and printed page. Variable definitions are inline or in the section header above.

## Chapter 2: Elements of Subjective Opinions

- (2.1) `R(X) = P(X) \ {{X}, {∅}}` — hyperdomain definition *(p.9)*.
- (2.2) `C(κ, j) = κ! / ((κ-j)! j!)` — choose function for hyperdomain indexing *(p.11)*.
- (2.3) `C(X) = {x ⊂ X : |x| ≥ 2}` — composite set *(p.12)*.
- (2.4) `C(X) = R(X) \ X` *(p.12)*.
- (2.5) `|C(X)| = κ - k` *(p.12)*.
- (2.6) `u_X + Σ_{x ∈ X} b_X(x) = 1` — multinomial belief-mass additivity *(p.14)*.
- (2.7) `u_X + Σ_{x ∈ R(X)} b_X(x) = 1` — hypernomial additivity *(p.14)*.
- (2.8) `Σ_{x ∈ X} a_X(x) = 1` — base rate additivity over domain *(p.15)*.
- (2.9) `a_X(x_i) = Σ_{x_j ∈ X, x_j ⊆ x_i} a_X(x_j)` — composite base rate *(p.16)*. Super-additive over R(X).
- (2.10) `a_X(x | x_i) = a_X(x ∩ x_i) / a_X(x_i)` — relative base rate *(p.17)*.
- (2.11) `Σ_{x ∈ X} p_X(x) = 1` *(p.18)*.
- (2.12) `Σ_{x ∈ R(X)} p_X^H(x) = 1` *(p.18)*.
- (2.13) `p_X(x) = Σ_{x_i ∈ R(X)} a_X(x | x_i) p_X^H(x_i)` — hyper→standard probability *(p.18)*.

## Chapter 3: Opinion Representations

- (3.1) `b_x + d_x + u_x = 1` *(p.24)*.
- (3.2) `P(x) = b_x + a_x u_x` *(p.24)*.
- (3.3) `Var(x) = P(x)(1-P(x)) u_x / (W + u_x)` *(p.24)*.
- (3.4) `∫₀¹ PDF(p(x)) dp(x) = 1` *(p.26)*.
- (3.5) `Beta(p_x, α, β) : [0,1] → ℝ_{≥0}` *(p.26)*.
- (3.6) `Beta(p_x, α, β) = Γ(α+β)/(Γ(α)Γ(β)) p_x^{α-1} (1-p_x)^{β-1}` *(p.26)*.
- (3.7) `α = r_x + a_x W; β = s_x + (1-a_x) W` *(p.27)*.
- (3.8) Evidence-form Beta `Beta^e(p_x, r_x, s_x, a_x) = Γ(r_x+s_x+W)/(Γ(r_x+a_x W)Γ(s_x+(1-a_x)W)) p_x^{r_x+a_x W - 1} (1-p_x)^{s_x+(1-a_x)W - 1}` *(p.27)*.
- (3.9) `E(x) = α/(α+β) = (r_x + a_x W)/(r_x + s_x + W)` *(p.27)*.
- (3.10) Variance multiple forms; opinion form `Var(x) = P(x)(1-P(x)) u_x / (W + u_x)` *(p.27)*.
- (3.11) Bijective binomial-opinion ↔ Beta PDF mapping *(p.28)*.
- (3.12) `P_X(x) = b_X(x) + a_X(x) u_X` — multinomial projection *(p.30)*.
- (3.13) `Var_X(x) = P_X(x)(1-P_X(x)) u_X / (W + u_X)` *(p.30)*.
- (3.14) Dirichlet PDF *(p.32)*.
- (3.15) `α_X(x) = r_X(x) + a_X(x) W` *(p.32)*.
- (3.16) Evidence-form Dirichlet *(p.32)*.
- (3.17) `E_X(x) = (r_X(x) + a_X(x) W) / (W + Σ r_X(x_j))` *(p.32)*.
- (3.18) Dirichlet variance, opinion form *(p.32)*.
- (3.19-3.20) `P_X = E_X` equivalence *(p.32)*.
- (3.21-3.22) `Σ r → ∞ ⇔ Σ b → 1, u → 0` *(p.32)*.
- (3.23) Bijective multinomial-opinion ↔ evidence-Dirichlet mapping *(p.36)*.
- (3.24) `P_X(x_i) = b_X(x_i) + a_X(x_i) u_X` — projector line *(p.37)*.
- (3.25-3.26) Conditions for uncertainty-maximised opinion *(p.37)*.
- (3.27) `ü_X = min_i [P_X(x_i)/a_X(x_i)]` *(p.37)*.
- (3.28) `P_X(x) = Σ_{x_i ∈ R(X)} a_X(x|x_i) b_X(x_i) + a_X(x) u_X` — hyper-opinion projection *(p.40)*.
- (3.29.a/b) Additivity (singletons) / super-additivity (hyper) *(p.40)*.
- (3.30) `b'_X(x) = Σ_{x' ∈ R(X)} a_X(x|x') b_X(x')` — hyper→multinomial *(p.40)*.
- (3.31) Dirichlet HPDF *(p.41)*.
- (3.32) HPDF strength + base rate composite formula *(p.41)*.
- (3.33) Evidence-form HPDF *(p.41)*.
- (3.34) Expected probability from HPDF over singletons *(p.42)*.
- (3.35) Hyper-opinion ↔ Dirichlet HPDF mapping *(p.43)*.
- (3.36-3.38) Hyper-Dirichlet PDF (Hankin) *(p.44)*.
- (3.39) `p_X(x_j) = Σ_{x_i ⊆ x_j} p_X(x_i)` *(p.45)*.
- (3.40) Probabilistic notation constraints *(p.47)*.
- (3.41) `b_X(x) = P_X(x) - a_X(x) u_X` — bijection probabilistic↔belief *(p.47)*.
- (3.42) Binomial probabilistic notation constraint *(p.47)*.
- (3.43) `Confidence(ω_X) = c_X = 1 - u_X` *(p.50)*.

## Chapter 4: Decision Making

- (4.1) `b^S_X(x) = Σ_{x_i ⊆ x} b_X(x_i)` — sharp belief *(p.51)*.
- (4.2) `b^TS_X = Σ_{x_i ∈ X} b_X(x_i)` — total sharp *(p.52)*.
- (4.3) `b^V_X(x) = Σ_{x_j ∈ C(X), x_j ⊄ x} a_X(x|x_j) b_X(x_j)` — vague belief *(p.52)*.
- (4.4) `b^TV_X = Σ_{x ∈ C(X)} b_X(x)` — total vague *(p.53)*.
- (4.8) `u^F_X(x) = a_X(x) u_X` — focal uncertainty *(p.55)*.
- (4.9) `b^S(x) + b^V(x) + u^F(x) = P(x)` *(p.56)*.
- (4.10) `M_X(x) = (b^S, b^V, u^F)` mass-sum *(p.56)*.
- (4.11) `b^TS + b^TV + u = 1` *(p.58)*.
- (4.12) `M^T_X = (b^TS, b^TV, u)` *(p.58)*.
- (4.13-4.14) `L(x) = λ(x) P(x); L^T = Σ λ P` — utilities *(p.60)*.
- (4.15-4.18) Utility-normalised probability and masses *(p.60-61)*.
- (4.19) `b^NS + b^NV + u^NF = P^N` *(p.61)*.
- (4.20) Utility-normalised mass-sum *(p.61)*.
- (4.48-4.49) Surprisal / opinion outcome surprisal *(p.76)*.
- (4.50-4.52) Sharp / vague / focal-uncertainty surprisal *(p.77)*.
- (4.53) `I^S + I^V + I^U = I^P` *(p.77)*.
- (4.54-4.55) Entropy `H(X) = -Σ p log p`, opinion entropy `H^P` *(p.77)*.
- (4.56-4.58) Sharpness, vagueness, uncertainty entropies *(p.78)*.
- (4.59) `H^S + H^V + H^U = H^P` *(p.78)*.
- (4.60) `H^BP(ω_X) = -Σ a_X(x) log_2 P_X(x)` — base-rate cross entropy *(p.79)*.
- (4.61-4.63) `PD = (1/2) Σ |P^B - P^C|`; `CC = (1-u^B)(1-u^C)`; `DC = PD · CC` *(p.80)*.

## Chapter 5: Principles

- (5.1) `m(x) = b_X(x), m(X) = u_X` — DST↔SL mapping *(p.84)*.
- (5.2-5.3) IDM upper/lower probabilities *(p.85)*.
- (5.4) `u_X = E^+(x) - E^-(x)` — uncertainty as IDM gap *(p.85)*.
- (5.5-5.6) Homomorphism / isomorphism *(p.88)*.
- (5.7-5.8) Distributivity does not hold in SL *(p.93)*.
- (5.10) Probability coproduct *(p.93)*.
- (5.11) `ω_{x ∧ (y ∪ z)} = ω_{(x ∧ y) ∪ (x ∧ z)}` — distributivity over addition *(p.93)*.
- (5.12) De Morgan in SL *(p.93)*.
- (5.13) `ω_{¬(x ∧ y)} = ¬ω_{x ∧ y}` *(p.93)*.
- (5.14) `P(ω_{x ∧ y}) = P(ω_x) P(ω_y)` *(p.93)*.
- (5.15-5.16) Absolute case BL homomorphism *(p.94)*.
- (5.17) Probabilistic notation `π_x = (P(x), u_x, a_x)` *(p.94)*.

## Chapter 6: Addition, Subtraction, Complement

- (6.1.a-d) Addition formulas *(p.95)*.
- (6.2) `P(x_1 ∪ x_2) = P(x_1) + P(x_2)` *(p.96)*.
- (6.3.a-d) Subtraction formulas *(p.97)*.
- (6.4) Subtraction constraints *(p.98)*.
- (6.5) `P(x_1) = P(x_1 ∪ x_2) - P(x_2)` *(p.98)*.
- (6.6) Complement formulas *(p.99)*.
- (6.7) `¬ω_x = ω_{x̄}` *(p.99)*.
- (6.8) `P(¬ω_x) = 1 - P(ω_x)` *(p.99)*.

## Chapter 7: Binomial Multiplication and Division

- (7.1.a-d) Binomial multiplication formulas *(p.102)*.
- (7.2) `P(x ∧ y) = P(x) P(y)` *(p.102)*.
- (7.3.a-d) Binomial comultiplication formulas *(p.103)*.
- (7.4) `P(x ∨ y) = P(x) + P(y) - P(x) P(y)` *(p.103)*.
- (7.5-7.6) Variance formulas *(p.105)*.
- (7.7) `ω_{x ∧ (y ∨ z)} ≠ ω_{(x ∧ y) ∨ (x ∧ z)}` *(p.105)*.
- (7.8) `PDF(p(Z = x ∧ y)) = -ln p(Z)`, 0 < p < 1 *(p.106)*.
- (7.9-7.10) Reliability network expression *(p.107-108)*.
- (7.12.a-d) Binomial division formulas *(p.110)*.
- (7.13) Binomial division constraints (a_x < a_y, etc.) *(p.111)*.
- (7.14) `P(x) = P(x ∧ y) / P(y)` *(p.112)*.
- (7.15.a-d) Binomial codivision formulas *(p.112)*.
- (7.16) Codivision constraints (a_x > a_y, etc.) *(p.113)*.
- (7.17) `P(x) = (P(x ∨ y) - P(y)) / (1 - P(y))` *(p.113)*.

## Chapter 8: Multinomial Multiplication and Division

- (8.1) Domains X, Y *(p.115)*.
- (8.2) Cartesian product matrix *(p.116)*.
- (8.3) Singleton belief `b_X(x_i) b_Y(y_j)` *(p.117)*.
- (8.4-8.5) Row/column belief masses *(p.117)*.
- (8.6) `u^Domain_{XY} = u_X u_Y` *(p.117)*.
- (8.7) `a_{XY}(x_i, y_j) = a_X(x_i) a_Y(y_j)` *(p.117)*.
- (8.8) `P_{XY}(xy) = P_X(x) P_Y(y)` *(p.117)*.
- (8.9) Variance *(p.117)*.
- (8.10-8.20) Normal multiplication two-step procedure *(p.118-120)*.
- (8.21) `ω_{XY} = (b_{XY}, u_{XY}, a_{XY})` *(p.120)*.
- (8.22-8.26) Proportional multiplication *(p.120-121)*.
- (8.28-8.33) Hypernomial product belief masses *(p.122)*.
- (8.34) `Dir^e_{XY} = Dir^e_X · Dir^e_Y` *(p.123)*.
- (8.35) Cartesian and projected probability matrix for GE eggs *(p.125)*.
- (8.36) Power-set notation `P*(X × Y)` *(p.127)*.
- (8.37-8.42) Multinomial division setup *(p.128-129)*.
- (8.43-8.44) Limit and condition rules *(p.129)*.
- (8.45-8.49) Averaging proportional division *(p.129-131)*.
- (8.50-8.55) Uncertainty heuristic and clipping *(p.130-131)*.
- (8.56) `ω^Ave_X = ω_{XY} / ω_Y` *(p.131)*.
- (8.57-8.61) Selective division *(p.132-133)*.

## Chapter 9: Conditional Reasoning and Subjective Deduction

- (9.1-9.3) MP, CP, MT principles *(p.151-152)*.
- (9.4) Traditional Bayes *(p.154)*.
- (9.5) Bayes with base rates `p(x|y) = a(x) p(y|x) / a(y)` *(p.155)*.
- (9.6) Conditional probability `p(y|x) = p(x ∧ y)/p(x)` *(p.155)*.
- (9.7) Bayes via base-rate join *(p.155)*.
- (9.8) `p(x|y) = a(x) p(y|x) / a(y)` *(p.155)*.
- (9.9) Bayes with MBR *(p.156)*.
- (9.12) `a(y) = a(x) p(y|x) + a(x̄) p(y|x̄)` *(p.156)*.
- (9.13) Law of total probability *(p.156)*.
- (9.14) Lottery example *(p.156)*.
- (9.15) Binomial probabilistic deduction `p(y\|x)` *(p.157)*.
- (9.16) Binomial probabilistic abduction `p(x̃\|y)` *(p.157)*.
- (9.17-9.21) Multinomial setup, total probability, deduced probability *(p.158-159)*.
- (9.22-9.24) Multinomial Bayes with base rate *(p.159-160)*.
- (9.25) Multinomial probabilistic abduction *(p.160)*.
- (9.27-9.29) Binomial deduction, abduction, subjective Bayes *(p.162)*.
- (9.30-9.32) Multinomial deduction, abduction, subjective Bayes *(p.162-163)*.
- (9.33-9.36) MBR derivation; binomial MBR *(p.165)*.
- (9.37-9.38) Upper/lower free base rate *(p.166)*.
- (9.39) Dogmatic case *(p.167)*.
- (9.40-9.51) Definition 9.1 binomial deduction with 9-case K selector *(p.168-169)*.
- (9.52-...) Sub-triangle examples *(p.170-172)*.
- (9.56-9.60) Multinomial MBR and free intervals *(p.173-174)*.
- (9.61-9.63) Multinomial deduction projected/belief/uncertainty *(p.175)*.
- (9.64) `ω_{Y\|X} = ω_X ⊙ ω_{Y|X}` *(p.176)*.
- (9.65-9.67) Three constraints; vacuous opinion def; apex *(p.176)*.
- (9.68-9.78) Multinomial deduction 3-step (MBR, apex, projection) *(p.177-179)*.
- (9.79) Definition 9.2: `ω_{Y\|X} = ω_X ⊙ ω_{Y|X}` *(p.179)*.
- (9.80-9.81) Match-fixing computed values *(p.180-181)*.
- (9.82-9.83) Material probabilistic implication *(p.183)*.
- (9.84) `Ψ(y|X) = |p(y|x) - p(y|x̄)|` — relevance *(p.185)*.
- (9.85) `ω_{y\|x} = ω_x ⊙ (ω_{y|x}, ω_{y|x̄})` *(p.187)*.

## Chapter 10: Subjective Abduction

- (10.1-10.2) Sensitivity / specificity / unspecificity definitions *(p.190)*.
- (10.3-10.6) Probabilistic and subjective relevance, irrelevance *(p.192)*.
- (10.7-10.8) Dependence / independence *(p.193)*.
- (10.9) `ω_{x\|y} = ω_y ⊙ (ω_{x|y}, ω_{x|ȳ})` *(p.193)*.
- (10.10) Projected probabilities of conditionals *(p.195)*.
- (10.11) Inverted projected probabilities (Bayes with MBR) *(p.195)*.
- (10.12) Dogmatic conditionals *(p.195)*.
- (10.13-10.14) Theoretical max uncertainties *(p.196)*.
- (10.15-10.22) Weighted proportional uncertainty (binomial) *(p.196-197)*.
- (10.23) Relative uncertainty `ũ_{x|y} = u^w_{y|X} ⊔ Ψ̄(y|X)` *(p.197)*.
- (10.24) Inverted binomial uncertainties *(p.198)*.
- (10.25-10.26) Inverted binomial conditionals *(p.198)*.
- (10.27) Definition 10.4: `(ω_{x̃|y}, ω_{x̃|ȳ}) = φ̃(ω_{y|x}, ω_{y|x̄}, a_x)` *(p.199)*.
- (10.28) Double inversion identity *(p.199)*.
- (10.29-10.31) Binomial abduction *(p.183)*.
- (10.32) Sources of uncertainty in abduction *(p.184)*.
- (10.33-10.34) Medical-test conditionals (sensitivity, specificity) *(p.185-186)*.
- (10.35) Inversion arguments *(p.188)*.
- (10.36) `P_{X|y_j}(x) = a_X(x) P_{Y|x}(y_j) / Σ a_X(x_i) P_{Y|x_i}(y_j)` *(p.189)*.
- (10.37) Dogmatic inverted opinion *(p.189)*.
- (10.38) Projector line in inverted opinion simplex *(p.189)*.
- (10.39-10.41) Theoretical max uncertainty for inverted *(p.190)*.
- (10.42-10.43) `u^S, w^u` weights *(p.190)*.
- (10.46) Theoretical max uncertainty for forward conditional *(p.191)*.
- (10.47-10.48) Weighted proportional uncertainty *(p.191)*.
- (10.49) `ũ_{X|y_j} = u^w_{Y|X} ⊔ Ψ̄(y_j|X)` *(p.191)*.
- (10.50) `u_{X|ỹ_j} = ü_{X|y_j} · ũ_{X|y_j}` *(p.192)*.
- (10.51) Inverted conditional opinion `ω_{X|ỹ_j}` *(p.192)*.
- (10.52) Definition 10.6: `ω_{X|Ỹ} = φ̃(ω_{Y|X}, a_X)` *(p.193)*.
- (10.53-10.56) Definition 10.7: `ω_{X\|Ỹ} = ω_Y ⊚̃ (ω_{Y|X}, a_X)` *(p.193-194)*.
- (10.59-10.61) Military intelligence example *(p.195-196)*.
- (10.63-10.67) Subjective-logic version of military intel *(p.197-198)*.

## Chapter 11: Joint and Marginal Opinions

- (11.1) `p(yx) = p(y|x) p(x)` *(p.199)*.
- (11.2) `p(YX) = p(Y|X) · p(X)` *(p.199)*.
- (11.4) `p([Y]) = Σ_x p(yx)` — marginalisation *(p.200)*.
- (11.5) `p([Y]) = p(Y\|X)` — marginal = deduction *(p.200)*.
- (11.6) Joint distribution worked example *(p.200)*.
- (11.7-11.8) Joint base rate `a_{YX}` *(p.201)*.
- (11.10-11.11) Joint base rate via base rate of Y *(p.201)*.
- (11.12) Marginal of X = ω_X exactly; marginal of Y ≈ ω_{Y\|X} *(p.202)*.
- (11.13-11.15) Joint uncertainty proportional formula *(p.203)*.
- (11.16) Joint opinion `ω_{YX}` *(p.203)*.
- (11.17) `ω_{YX} = ω_{Y|X} · ω_X` *(p.203)*.
- (11.18) Marginal projected probabilities *(p.204)*.
- (11.21) `u_{[X]} = u_{[Y]} = u_{YX}` *(p.204)*.
- (11.22-11.23) Marginal conditionals `P_{[Y|x]}` *(p.204)*.
- (11.24-11.25) Match-fixing joint and uncertainty *(p.205-206)*.

## Chapter 12: Belief Fusion

- (12.2) BCF formulas (Har, Con, base rate average) *(p.216)*.
- (12.3) `Har(x) = b^A u^B + b^B u^A + Σ_{x^A ∩ x^B = x} b^A b^B` *(p.216)*.
- (12.4) `Con = Σ_{x^A ∩ x^B = ∅} b^A b^B` *(p.216)*.
- (12.5) Vacuous neutral element *(p.217)*.
- (12.6) Frequentist constraint-fusion limit *(p.218)*.
- (12.9-12.11) Stochastic↔belief constraint fusion equivalence (Theorem 12.1) *(p.219-220)*.
- (12.13) Cinema A&B projected probability calculation *(p.224)*.
- (12.14-12.15) Definition 12.5 aleatory CBF cases I and II *(p.226)*.
- (12.16-12.17) Theorem 12.2: CBF as evidence addition `r^{A⋄B}(x) = r^A(x) + r^B(x)` *(p.227)*.
- (12.18-12.19) Definition 12.7 ABF cases I and II *(p.229)*.
- (12.20-12.21) Theorem 12.3: ABF as evidence averaging `r^{A⋄B}(x) = (r^A(x) + r^B(x))/2` *(p.230)*.
- (12.22-12.25) Definition 12.8 WBF (three cases) *(p.232)*.
- (12.29-12.36) CCF three-step (consensus min, residue, compromise, normalised merge) *(p.234-235)*.

## Chapter 13: Unfusion and Fission

- (13.1) Cumulative unfusion case I *(p.238)*.
- (Definition 13.2) Averaging unfusion *(p.239)*.
- (13.9) Cumulative fission with parameter φ *(p.241)*.

## Chapter 14: Computational Trust

- (14.2-14.3) Notation for transitive trust *(p.252)*.
- (14.4) Compact trust notation *(p.253)*.
- (14.5-14.6) Two-edge probability-sensitive trust discounting (Definition 14.6) *(p.256)*.
- (14.13-14.14) Multi-edge product `P_{A_n}^{A_1} = ∏ P_{A_{i+1}}^{A_i}` (Definition 14.7) *(p.260)*.
- (14.16-14.17) Trust fusion `ω_X^{[A;B]⋄[A;C]} = (ω_B^A ⊗ ω_X^B) ⊕ (ω_C^A ⊗ ω_X^C)` *(p.262)*.
- (14.19-14.22) DC, PD, CC; UD; RF *(p.266)*.
- (14.23-14.24) UD `= u_B^A / (u_B^A + u_C^A)`, RF `= UD · DC` *(p.266-267)*.
- (14.25-14.26) Revised opinions (b̌, ď, ǔ, ǎ) *(p.267)*.
- (14.27) Revised cumulative fusion *(p.267)*.

## Chapter 15: Subjective Trust Networks

- (15.2) Compact expression for example DSPG *(p.275)*.
- (15.3) Perceived topology under bad-receiving *(p.278)*.
- (15.4-15.5) DSPG synthesis path enumeration *(p.285)*.
- (15.6-15.8) DSPG synthesis criteria 1, 2, 3 examples *(p.286-288)*.

## Chapter 16: Bayesian Reputation Systems

- (16.1) `S = (r + Wa) / (r + s + W)` *(p.291)*.
- (16.2) Multinomial reputation score *(p.292)*.
- (16.3-16.4) Aggregate ratings vector *(p.292-293)*.
- (16.5-16.6) Recursive ageing with longevity factor *(p.293)*.
- (16.7-16.8) Geometric convergence *(p.294)*.
- (16.9) Individual base rate from community base rate *(p.294)*.
- (16.10-16.12) Total / sliding-window / high-longevity individual evidence *(p.295)*.
- (16.13-16.14) Aggregate community reputation; community base rate *(p.296)*.
- (16.15-16.18) Multinomial probability score; point estimate *(p.297-298)*.
- (16.19) Multinomial→binomial rating projection *(p.299)*.
- (16.20-16.21) Trust path with reputation system *(p.301)*.

## Chapter 17: Subjective Networks

- (17.1) `p(C|D) = a(C) p(D|C) / [a(C) p(D|C) + a(C̄) p(D|C̄)] = 0.25` *(p.307)*.
- (17.2-17.3) Naïve Bayes for joint evidence *(p.307)*.
- (17.4) Joint variable sets `X̂, Ẑ` *(p.309)*.
- (17.5) Chain rule of conditional probability *(p.309)*.
- (17.6-17.8) Bayes with MBR; Naïve Bayes classifier *(p.310)*.
- (17.9-17.12) Causal chain / common cause / common effect topologies *(p.311-312)*.
- (17.13) `ω_{X_K|X_1} = M_{I=2}^K (ω_{X_I|X_{I-1}})` — chained conditional *(p.312)*.
- (17.14) `ω_{X_K\|X_1} = ω_{X_1} ⊙ ω_{X_K|X_1}` — deduction with serial *(p.313)*.
- (17.15) Chained inverted conditionals (invert each then chain) *(p.313)*.
- (17.16) Simpler inversion (chain then invert) *(p.314)*.
- (17.17) Abduction with serial inverted conditionals *(p.314)*.
- (17.18) Heuristic validation: equal P, approximately equal u *(p.315)*.
- (17.19) Validated base rates *(p.315)*.
- (17.20) Chain rule for joint opinions *(p.316)*.
- (17.23) Subjective predictive deduction *(p.317)*.
- (17.24) Joint cause via product *(p.317)*.
- (17.26-17.27) Subjective Bayes / naïve subjective Bayes classifier *(p.318-319)*.
- (17.28) Diagnostic deduction *(p.319)*.
- (17.30-17.31) Intercausal abduction + division *(p.319-320)*.
- (17.33) Naïve subjective Bayes classifier for combined reasoning *(p.321)*.
- (17.34) I-map for conditional independence *(p.321)*.
- (17.35-17.36) SN derivation (trust transitivity + SBN deduction; trust fusion + SBN) *(p.324-325)*.

---

# Definitions Catalog (numbered, by chapter)

## Chapter 2

- **2.1 Hyperdomain** *(p.9)*: `R(X) = P(X) \ {{X}, {∅}}`.
- **2.2 Composite Set** *(p.12)*: `C(X) = {x ⊂ X : |x| ≥ 2}`.
- **2.3 Hypervariable** *(p.12)*: variable taking values from `R(X)`.
- **2.4 Belief Mass Distribution** *(p.13)*: `b_X : X → [0,1]` with `u + Σb = 1`; hypernomial form over `R(X)`.
- **2.5 Base Rate Distribution** *(p.15)*: `a_X : X → [0,1]` with `Σa = 1`.
- **2.6 Base Rate over Hyperdomain** *(p.16)*: super-additive sum.
- **2.7 Relative Base Rate** *(p.17)*: `a_X(x | x_i) = a_X(x ∩ x_i) / a_X(x_i)`.
- **2.8 Probability Distribution** *(p.17-18)*: standard and hyper.

## Chapter 3

- **3.1 Binomial Opinion** *(p.24)*: `ω_x = (b_x, d_x, u_x, a_x)`.
- **3.2 Beta PDF** *(p.26)*.
- **3.3 Mapping Binomial Opinion ↔ Beta PDF** *(p.28)*: `b = r/(W+r+s); d = s/(W+r+s); u = W/(W+r+s)` and inverse.
- **3.4 Multinomial Opinion** *(p.30)*: `ω_X = (b_X, u_X, a_X)`.
- **3.5 Dirichlet PDF** *(p.32)*.
- **3.6 Mapping Multinomial Opinion ↔ Dirichlet PDF** *(p.36)*.
- **3.7 Hyper-opinion** *(p.39)*: `ω_X = (b_X, u_X, a_X)` with `b_X` over `R(X)`, `a_X` over singletons only.
- **3.8 Dirichlet HPDF** *(p.41)*.
- **3.9 Mapping Hyper-opinion ↔ Dirichlet HPDF** *(p.43)*.
- **3.10 Probabilistic Opinion Notation** *(p.47)*.
- **3.11 Mapping Belief ↔ Probabilistic Opinion** *(p.47)*: `b(x) = P(x) - a(x)·u`.

## Chapter 4

- **4.1 Sharp Belief Mass** *(p.51)*.
- **4.2 Total Sharp Belief Mass** *(p.52)*.
- **4.3 Vague Belief Mass** *(p.52)*.
- **4.4 Total Vague Belief Mass** *(p.53)*.
- **4.5 Focal Uncertainty Mass** *(p.55)*.
- **4.6 Mass-Sum** *(p.56)*.
- **4.7 Total Mass-Sum** *(p.58)*.
- **4.8 Utility-Normalised Probability Vector** *(p.60)*.
- **4.9-4.10 Utility-Normalised Masses, Mass-Sum** *(p.60-61)*.
- **4.11 Surprisal** *(p.76)*.
- **4.12 Opinion Outcome Surprisal** *(p.76)*.
- **4.13 Surprisal of Sharpness/Vagueness/Focal Uncertainty** *(p.77)*.
- **4.14 Entropy** *(p.77)*.
- **4.15 Opinion Entropy** *(p.78)*.
- **4.16-4.18 Sharpness/Vagueness/Uncertainty Entropy** *(p.78)*.
- **4.19 Base-Rate to Projected-Probability Cross Entropy** *(p.79)*.
- **4.20 Degree of Conflict** *(p.80)*.

## Chapter 6

- **6.1 Addition** *(p.95)*: disjoint, proper subset, vacuous if `x_1 ∪ x_2 = X`.
- **6.2 Subtraction** *(p.97)*: subset constraint, removes vagueness.
- **6.3 Complement** *(p.99)*: unary, swaps `b ↔ d`, `a → 1-a`.

## Chapter 7

- **7.1 Binomial Multiplication** *(p.102)*.
- **7.2 Binomial Comultiplication** *(p.103)*.
- **7.3 Binomial Division** *(p.110)*.
- **7.4 Binomial Codivision** *(p.112)*.

## Chapter 9

- **9.1 Conditional Deduction with Binomial Opinions** *(p.168)*: closed-form 9-case selector.
- **9.2 Multinomial Conditional Deduction** *(p.179)*: 3-step procedure.

## Chapter 10

- **10.1 Probabilistic Relevance** *(p.192)*: `Ψ(y_j|X) = max_i p(y_j|x_i) - min_i p(y_j|x_i)`.
- **10.2 Subjective Relevance** *(p.192)*: same form on projected probabilities.
- **10.3 Dependence** *(p.193)*: `δ(Y|X) = max_y Ψ(y|X)`.
- **10.4 Binomial Subjective Bayes' Theorem** *(p.199)*.
- **10.5 Binomial Abduction** *(p.183)*: composition of inversion `φ̃` and deduction `⊙`.
- **10.6 Multinomial Subjective Bayes' Theorem** *(p.193)*.
- **10.7 Multinomial Abduction** *(p.193)*.

## Chapter 12

- **12.1 Correctness of Results** *(p.209)*.
- **12.2 Model Correctness** *(p.211)*.
- **12.3 Constraint Fusion Operator** *(p.216)*.
- **12.4 Stochastic Constraint Opinion** *(p.219)*.
- **12.5 Cumulative Fusion Operator (aleatory)** *(p.226)*.
- **12.6 Epistemic Cumulative Fusion** *(p.228)*.
- **12.7 Averaging Belief Fusion** *(p.229)*.
- **12.8 Weighted Belief Fusion** *(p.231)*.
- **12.9 Consensus & Compromise Fusion** *(p.235)*.

## Chapter 13

- **13.1 Cumulative Unfusion Operator** *(p.238)*.
- **13.2 Averaging Unfusion Operator** *(p.239)*.
- **13.3 Cumulative Fission Operator** *(p.241)*.

## Chapter 14

- **14.1 Reliability Trust** (Gambetta 1988) *(p.244)*.
- **14.2 Decision Trust** (McKnight & Chervany 1996) *(p.247)*.
- **14.3 Reputation** *(p.248)*.
- **14.4 Functional Trust Derivation Criterion** *(p.254)*.
- **14.5 Trust Scope Consistency Criterion** *(p.254)*.
- **14.6 Probability-Sensitive Trust Discounting (Two-Edge Path)** *(p.256)*.
- **14.7 Trust Discounting (Multi-edge Paths)** *(p.260)*.

## Chapter 15

- **15.1 Series-Parallel Graph** *(p.271)*.
- **15.2 Directed Series-Parallel Graph (DSPG)** *(p.272)*.
- **15.3 Outbound-Inbound Set (OIS)** *(p.273)*.
- **15.4 Parallel-Path Subnetwork (PPS)** *(p.274)*.
- **15.5 Nesting Level** *(p.274)*.
- **15.6 Directed Series and Parallel Composition** *(p.282)*.
- **15.7 DSPG-Synthesis Criteria for Sub-Path Addition** *(p.285)*.

## Chapter 16

- **16.1 Community Base Rate** *(p.296)*.

## Chapter 17

- **17.1 Bayesian Conditional Independence** *(p.321)*.
- **17.2 Subjective Conditional Independence** *(p.322)*: requires absolute opinion on conditioning variable.

---

# Theorems / Propositions

- **Theorem 7.1** *(p.106)*: Product of two independent binary uniform variables (Beta(p,1,1)) has PDF `−ln(p)` over (0,1). Used as benchmark for SL multiplication approximation Beta(p, 1/2, 3/2).
- **Theorem 9.1** *(p.155)*: Bayes' theorem with base rates, `p(x|y) = a(x) p(y|x) / a(y)`.
- **Theorem 9.2** *(p.156)*: Bayes with marginal base rate.
- **Theorem 12.1** *(p.219)*: Equivalence between stochastic and belief constraint fusion.
- **Theorem 12.2** *(p.227)*: CBF equivalent to evidence-vector addition (Eq. 12.17).
- **Theorem 12.3** *(p.230)*: ABF equivalent to evidence-vector averaging (Eq. 12.21).
- **Theorem 12.4** *(p.233)*: WBF equivalent to confidence-weighted Dirichlet averaging.
- **Theorem 15.1** *(p.273)*: A pair of nodes in a DSPG is connected iff their OIS is non-empty.
- **Proposition 4.1** *(p.78)*: Opinions with identical projected probability have identical opinion entropy regardless of `u`.

---

# Operator Catalogue (alphabetical by symbol where named)

Each operator entry: symbol; signature (input/output spaces); formula(s) for output `(b, d, u, a)` or `(b⃗, u, a⃗)`; conditions; identity element; properties; key page.

## Addition `+` (Eq. 6.1, p.95)

- **Signature**: binomial × binomial → binomial; disjoint subsets; `x_1 ∪ x_2 ⊂ X` strict.
- **Output**: `b_{x_1 ∪ x_2} = b_{x_1} + b_{x_2}`; `u_{x_1 ∪ x_2} = (a_{x_1} u_{x_1} + a_{x_2} u_{x_2})/(a_{x_1} + a_{x_2})`; `a_{x_1 ∪ x_2} = a_{x_1} + a_{x_2}`.
- **Property**: `P(x_1 ∪ x_2) = P(x_1) + P(x_2)`.
- **Edge case**: if `x_1 ∪ x_2 = X`, addition is undefined (totally vague); treat result as vacuous.

## Subtraction `−` (Eq. 6.3, p.97)

- **Signature**: binomial × binomial → binomial; subset constraint `x_2 ⊆ (x_1 ∪ x_2)`.
- **Constraints (Eq. 6.4)**: `a_{x_2} u_{x_2} ≤ a_{(x_1 ∪ x_2)} u_{(x_1 ∪ x_2)}`; non-negativity.
- **Property**: `P(x_1) = P(x_1 ∪ x_2) - P(x_2)`.

## Complement `¬` (Eq. 6.6, p.99)

- **Signature**: unary on binomial.
- **Output**: `b_{¬x} = d_x`; `d_{¬x} = b_x`; `u_{¬x} = u_x`; `a_{¬x} = 1 - a_x`.
- **Property**: involution `¬¬ω_x = ω_x`; `P(¬x) = 1 - P(x)`.

## Binomial Multiplication `·` (Eq. 7.1, p.102)

- **Signature**: binomial × binomial → binomial.
- **Output**: see equation (7.1.a-d) above.
- **Property**: `P(x ∧ y) = P(x) P(y)`.
- **Edge case**: denominator `(1 - a_x a_y)` — handle `a_x = a_y = 1`.
- **Conservation**: maximises uncertainty given the constraint.

## Binomial Comultiplication `⊔` (Eq. 7.3, p.103)

- **Signature**: binomial × binomial → binomial.
- **Property**: `P(x ∨ y) = P(x) + P(y) - P(x) P(y)`.

## Binomial Division `/` (UN-AND) (Eq. 7.12, p.110)

- **Signature**: binomial × binomial → binomial.
- **Constraints (Eq. 7.13)**: `a_x < a_y`; `d_x ≥ d_y`; plus inequalities on `b_x`, `u_x`.
- **Property**: `P(x) = P(x ∧ y) / P(y)`.

## Binomial Codivision `⊔̃` (UN-OR) (Eq. 7.15, p.112)

- **Signature**: binomial × binomial → binomial.
- **Constraints (Eq. 7.16)**: `a_x > a_y`; `b_x ≥ b_y`; plus inequalities.
- **Property**: `P(x) = (P(x ∨ y) - P(y)) / (1 - P(y))`.

## Multinomial Multiplication (three methods)

### Normal Multiplication (Sec. 8.1.2, Eq. 8.18-8.19, p.118)

- **Signature**: multinomial × multinomial → multinomial.
- **Output**: `u_{XY} = min_{(i,j)} [(P_X(x_i) P_Y(y_j) - b_X(x_i) b_Y(y_j)) / (a_X(x_i) a_Y(y_j))]`; `b_{XY}(xy) = P_X(x) P_Y(y) - a_X(x) a_Y(y) u_{XY}`.
- **Property**: most conservative (preserves max uncertainty); commutative, associative.

### Proportional Multiplication (Sec. 8.1.4, Eq. 8.22-8.26, p.120)

- **Output**: `u_{XY} = ü_{XY} (u_X + u_Y) / (ü_X + ü_Y)`.
- **Property**: ~50% less uncertainty than normal.

### Projected Multiplication (Sec. 8.1.5, p.121)

- Hypernomial product → multinomial via Eq. 3.30.
- Hardly preserves any uncertainty; least conservative.

All three: `P_{XY}(xy) = P_X(x) P_Y(y)` (Eq. 8.8).

## Multinomial Division (two methods, Sec. 8.3)

### Averaging Proportional Division `/` (Eq. 8.45-8.55, p.129)

- Round-trip lossy: `(ω_X · ω_Y) / ω_Y ≠ ω_X` in general.
- 0/0 limit rule (Eq. 8.43).

### Selective Division `‖` (Eq. 8.57-8.61, p.132)

- Requires single observed `y_j`.

## Binomial Deduction `⊙` (Definition 9.1, Eq. 9.40-9.51, p.168)

- **Signature**: binomial × (binomial × binomial) → binomial; `ω_x ⊙ (ω_{y|x}, ω_{y|x̄})`.
- **Closed-form**: 9-case selector for K coefficient. Intermediate `b^I_y, d^I_y, u^I_y` (Eq. 9.41) is the convex combination of conditionals weighted by parent (b, d, u) and parent base rate.
- **MBR base rate** (Eq. 9.36): `a_y = (a_x b_{y|x} + a_{x̄} b_{y|x̄}) / (1 - a_x u_{y|x} - a_{x̄} u_{y|x̄})` if `u_{y|x} + u_{y|x̄} < 2`; free in [0,1] otherwise.

## Multinomial Deduction `⊙` (Definition 9.2, Eq. 9.79, p.179)

- **Signature**: multinomial × set-of-conditionals → multinomial; 3-step algorithmic.
- **Step 1**: MBR via Eq. 9.68.
- **Step 2**: sub-simplex apex `ω_{Y\|X̂}` enforcing Pearl's plausible-reasoning constraint Eq. 9.69.
- **Step 3**: linear projection of `ω_X` onto deduction sub-space.

## Subjective Bayes' Theorem `φ̃` (Definitions 10.4, 10.6)

### Binomial (Eq. 10.27, p.199)

- **Signature**: `(ω_{y|x}, ω_{y|x̄}, a_x) → (ω_{x̃|y}, ω_{x̃|ȳ})`.
- **4-step uncertainty algorithm** (Sec. 10.3.2): theoretical max → weighted proportional → coproduct with irrelevance → multiply.
- **Convergence under iteration** with MBR: projected probabilities stationary; uncertainty monotone non-decreasing.

### Multinomial (Eq. 10.52, p.193)

- **Signature**: `(ω_{Y|X}, a_X) → ω_{X|Ỹ}`.
- **Inverted projected probability**: Eq. 10.36.

## Abduction `⊙̃` / `⊚̃` (Definitions 10.5, 10.7, Eq. 10.29-10.31, 10.53-10.56)

- **Composition**: invert via `φ̃` then deduce via `⊙`.
- **Binomial**: `ω_{x̃\|y} = ω_y ⊙̃ (ω_{y|x}, ω_{y|x̄}, a_x) = ω_y ⊙ φ̃(ω_{y|x}, ω_{y|x̄}, a_x)`.
- **Multinomial**: `ω_{X\|Ỹ} = ω_Y ⊚̃ (ω_{Y|X}, a_X) = ω_Y ⊙ φ̃(ω_{Y|X}, a_X)`.

## Joint Opinion `·` (Eq. 11.17, p.203)

- `ω_{YX} = ω_{Y|X} · ω_X`.
- Marginal-on-X = `ω_X` exactly; marginal-on-Y ≈ `ω_{Y\|X}`.

## Marginalisation `[·]` (Eq. 11.4, p.200)

- `p([Y]) = p(Y\|X)` — marginal equals deduction.

## Belief Constraint Fusion (BCF) `⊙` (Definition 12.3, Eq. 12.2, p.216)

- **Signature**: hyperdomain × hyperdomain → hyperdomain.
- **Output**: `b^{(A&B)} = Har/(1-Con)`; `u^{(A&B)} = u^A u^B / (1-Con)`.
- **Properties**: commutative, **non-idempotent**, associative under equal base rates; vacuous neutral (Eq. 12.5); undefined when `Con = 1`.

## Cumulative Belief Fusion (CBF) `⊕` (Definitions 12.5, 12.6, Eq. 12.14, 12.18, p.226-228)

### Aleatory `⊕` (Def 12.5, Eq. 12.14)

- Case I (not both dogmatic): `b^{(A⋄B)}(x) = (b^A(x) u^B + b^B(x) u^A) / (u^A + u^B - u^A u^B)`; `u^{(A⋄B)} = u^A u^B / (u^A + u^B - u^A u^B)`.
- Case II (both dogmatic): limit weights `γ`.
- **Properties**: commutative, associative, **non-idempotent**, vacuous neutral.
- **Equivalent to evidence addition** (Theorem 12.2): `r^{(A⋄B)} = r^A + r^B`.

### Epistemic `⊕̈` (Def 12.6, p.229)

- Two-step: aleatory CBF then uncertainty-maximise.
- Models contradictory witnesses: equally-trusted contradictions cancel.

## Averaging Belief Fusion (ABF) `⨁` (Definition 12.7, Eq. 12.18, p.229)

- **Output**: `b^{(A⋄B)}(x) = (b^A(x) u^B + b^B(x) u^A) / (u^A + u^B)`; `u^{(A⋄B)} = 2 u^A u^B / (u^A + u^B)`; `a^{(A⋄B)}(x) = (a^A(x) + a^B(x)) / 2`.
- **Properties**: commutative, **idempotent**, **NOT associative**, **NO neutral element** (vacuous still adds weight).
- **Equivalent to evidence averaging** (Theorem 12.3): `r^{(A⋄B)} = (r^A + r^B)/2`.

## Weighted Belief Fusion (WBF) `⨁̂` (Definition 12.8, Eq. 12.22-12.25, p.231-232)

- **Confidence-weighted**: `c_X = 1 - u_X`.
- **Three cases**: I (one not dogmatic, one not vacuous), II (both dogmatic), III (both vacuous).
- **Properties**: commutative, idempotent, semi-associative, vacuous neutral.
- **Equivalent to confidence-weighted Dirichlet averaging** (Theorem 12.4).
- **Limitation**: does not leverage shared belief on partially overlapping composites.

## Consensus & Compromise Fusion (CCF) `⊚` (Definition 12.9, Eq. 12.29-12.36, p.235)

- **Three-step**: consensus = min of belief masses; compromise = redistribute residue into vague beliefs over composites; merge with normalisation.
- **Properties**: commutative, idempotent, semi-associative, vacuous neutral.
- **Whole-frame mass** `b^{comp}(X)` is reassigned to uncertainty.

## Cumulative Unfusion `⊖` (Definition 13.1, Eq. 13.1, p.238)

- **Inverse of CBF**.
- **Properties**: non-commutative, non-associative, non-idempotent.
- **Edge case**: division-by-zero when `u^B - u^C + u^B u^C = 0`.

## Averaging Unfusion `⨸` (Definition 13.2, p.239)

- **Inverse of ABF**.
- **Properties**: idempotent, non-commutative, non-associative.

## Cumulative Fission `ⓘ` (Definition 13.3, Eq. 13.9, p.241)

- **Splits** `ω_X^C` into `ω_X^{C_1}` and `ω_X^{C_2}` using `φ ∈ (0,1)`.
- **Recombines**: `ω_X^{C_1} ⊕ ω_X^{C_2} = ω_X^C`.
- **Edge case**: `φ ∈ {0, 1}` produces one vacuous and one identity opinion.

## Trust Discounting `⊗` (Definition 14.6, 14.7, Eq. 14.5-14.6, 14.13-14.14, p.256-260)

- **Two-edge** (Def 14.6): `ω_X^{[A;B]} = ω_B^A ⊗ ω_X^B`. `b_X^{[A;B]}(x) = P_B^A · b_X^B(x)`; `u_X^{[A;B]} = 1 - P_B^A · Σ b_X^B(x)`; `a_X^{[A;B]}(x) = a_X^B(x)`.
- **Multi-edge** (Def 14.7): `P_{A_n}^{A_1} = ∏ P_{A_{i+1}}^{A_i}`.
- **Edge cases**: `P_B^A = 1` ⇒ derived = received; `P_B^A = 0` ⇒ derived vacuous.
- Probability-sensitive: low projected probability of trust ⇒ high uncertainty in derived opinion.

## Trust Fusion `⋄` (Eq. 14.16-14.17, p.262)

- Combines two trust paths: `ω_X^{[A;B]⋄[A;C]} = (ω_B^A ⊗ ω_X^B) ⊕ (ω_C^A ⊗ ω_X^C)`.
- The `⊕` instance can be CBF or other fusion operator selected per Ch. 12.

## Trust Revision `⊕̌` (Eq. 14.27, p.267)

- Revised cumulative fusion using revised opinions (Eq. 14.25).
- Uses degree of conflict `DC = PD · CC`, uncertainty differential `UD`, revision factor `RF = UD · DC`.
- Author concedes design is "ad hoc."

## Multinomial Subjective Bayes' Inversion `φ̃` and Abduction `⊚̃`

(Already covered above under Subjective Bayes' Theorem.)

## Chained Conditional Operators (Ch. 17)

- **Chain rule** `M_{I=2}^K (ω_{X_I|X_{I-1}})` (Eq. 17.13): nested deduction across K conditionals.
- **Chained inversion** Eq. 17.15 (invert each then chain) vs Eq. 17.16 (chain then invert) — produce equal projected probabilities, approximately equal uncertainty (Eq. 17.18).

## Subjective Network Derivation (Eq. 17.35-17.36)

Standard pattern: trust transitivity `⊗` for each source → trust fusion `⊕` (or product `·`) for multiple sources → SBN deduction `⊙` along chain. Belief fusion only applies in STN frame, never in SBN frame.

---

# Worked Numerical Examples (canonical test cases)

These are direct test cases for any subjective-logic implementation. Each gives input opinions, the operator applied, and the expected output. Page citations point to the worked example in the book.

## Binomial opinion / Beta PDF

- **Example 3.1 (p.25)**: `ω_x = (0.40, 0.20, 0.40, 0.90)` → `P(x) = 0.40 + 0.90·0.40 = 0.76`.
- **Example 3.2 (p.28-29)**: same `ω_x` ↔ Beta(α = 3.8, β = 1.2). E[p] = 3.8/5.0 = 0.76. ✓
- **Vacuous (p.28)**: `(0,0,1,1/2)` ↔ Beta(1,1) = uniform.
- **Trinomial (p.31)**: `b = (0.20,0.20,0.20)`, `u = 0.40`, `a = (0.75, 0.125, 0.125)` → `P_X = (0.50, 0.25, 0.25)`.

## Decision making (Ch. 4)

- **Mass-sum (p.57, Table 4.1)**: ternary, hyperdomain x_1..x_6, `b = (0.10, 0.10, 0.00, 0.20, 0.30, 0.10)`, `u = 0.20`, `a = (0.20, 0.30, 0.50, 0.50, 0.70, 0.80)`.
- **Utility-normalisation urn (p.61, Table 4.2)**: Urn X (70R/10B/20U), Urn Y (40R/20B/40U), bet $1000 on X-black or $500 on Y-black. `λ^+ = 1000`. `P_X(x_2) = 0.2`, `P_Y(y_2) = 0.4`. Utility-normalised probabilities equal. Decide on `b^S_Y(y_2) > b^S_X(x_2)` → choose Y.
- **Ellsberg (p.65)**: 30R / 60(B-or-Y) urn. Game 1 (R vs B): equal projected, sharp belief favours R. Game 2 (R-or-Y vs B-or-Y): equal projected, sharp belief favours B-or-Y. Both rational under sharpness.
- **Decision Game 1 (p.69)**: vacuous urn vs known-ratio urn; `P_X(y) = 1/3`, `P_Y(y) ≈ 0.222`. Choose X (greater projected probability).
- **Decision Game 2 (p.71)**: `P_X(x_3) = P_Y(y_3) = 1/3`. `b^S_X = 0`, `b^S_Y = 1/9`. Choose Y (greater sharpness).
- **Decision Game 3 (p.73)**: same projected probability, same sharp = 0. `b^V_X = 2/9`, `b^V_Y = 0`; `u^F_X = 1/9`, `u^F_Y = 1/3`. Choose X — least focal uncertainty.
- **Conflict (p.80-81)**: both projected = 0.77, base rate 0.90. PD = 0, DC = 0. With base rate 0.10: PD = 0.56, CC = 0.20·0.90 = 0.18, DC = 0.10.

## Operators (Chs. 6-7)

- **Addition (Fig. 6.2, p.96)**: `ω_{x_1} = (0.20, 0.40, 0.40, 0.25)`, `ω_{x_2} = (0.10, 0.50, 0.40, 0.50)`. Sum: `(0.30, 0.30, 0.40, 0.75)`. P = 0.60.
- **Subtraction (Fig. 6.3, p.98)**: `ω_{(x_1 ∪ x_2)} = (0.70, 0.10, 0.20, 0.75)`, `ω_{x_2} = (0.50, 0.30, 0.20, 0.25)`. Diff: `(0.20, 0.60, 0.20, 0.50)`. P = 0.30.
- **Complement (Fig. 6.5, p.100)**: `ω_x = (0.50, 0.10, 0.40, 0.25)`. ¬: `(0.10, 0.50, 0.40, 0.75)`. P = 0.40.
- **Multiplication (Fig. 7.2, p.103)**: `ω_x = (0.75, 0.15, 0.10, 0.50)`, `ω_y = (0.10, 0.00, 0.90, 0.20)`. Product: `(0.15, 0.15, 0.70, 0.10)`. `P(x ∧ y) = 0.80·0.28 = 0.224`.
- **Comultiplication (Fig. 7.3, p.104)**: `ω_x = (0.75, 0.15, 0.10, 0.50)`, `ω_y = (0.35, 0.00, 0.65, 0.20)`. Coproduct: `(0.84, 0.06, 0.10, 0.60)`. `P(x ∨ y) = 0.80 + 0.48 - 0.80·0.48 = 0.896`.
- **Reliability (Table 7.1, p.108)**: components w, x, y, z; system `S = w ∧ (x ∨ y) ∧ z`. Result: `(0.43, 0.10, 0.47, 0.78)`, P = 0.80.
- **Division (Fig. 7.7, p.111)**: `ω_{x ∧ y} = (0.10, 0.80, 0.10, 0.20)`, `ω_y = (0.40, 0.00, 0.60, 0.50)`. Quotient: `(0.15, 0.80, 0.05, 0.40)`. P = 0.12 / 0.70 = 0.171.

## Multinomial multiplication (Sec. 8.2)

- **GE eggs (Table 8.3, p.126)**: gender × mutation. Inputs: `b_X = (0.60, 0.30)`, `u_X = 0.10`, `a_X = (0.50, 0.50)`; `b_Y = (0.70, 0.20)`, `u_Y = 0.10`, `a_Y = (0.50, 0.50)`. P-matrix: `[[0.49, 0.16], [0.26, 0.09]]`. Comparing methods:
  - Normal: `b = (0.460, 0.135, 0.235, 0.060)`, `u = 0.110`.
  - Proportional: `b = (0.473, 0.148, 0.248, 0.073)`, `u = 0.058`.
  - Projected: `b = (0.485, 0.160, 0.260, 0.085)`, `u = 0.010`.

## Conditional reasoning (Ch. 9-10)

- **Lottery (p.156)**: `p(y|x) = 0.001`, `p(x) = p(y) = 1`, `p(y|x̄) = 0`. Eq. 9.4 gives 0.001 (wrong); Bayes with MBR gives `p(x|y) = 1`.
- **Match-fixing (p.180-181, Table 9.1, Eq. 9.81)**:
  - Inputs: `ω_X` with `b(x_1) = 0.90`, `b(x_2) = 0.00`, `u_X = 0.10`, `a_X = (0.1, 0.9)`. `ω_{Y|x_1}` with `b = (0.00, 0.80, 0.10)`, `u = 0.10`. `ω_{Y|x_2}` with `b = (0.70, 0.00, 0.10)`, `u = 0.20`.
  - **Expected**: MBR `a_Y = (0.778, 0.099, 0.123)`. `u_{Y\|X̂} = 0.190`. Deduced: `b(y_1) = 0.063`, `b(y_2) = 0.728`, `b(y_3) = 0.100`, `u = 0.109`. `P = (0.148, 0.739, 0.113)`.
  - **Interpretation**: despite high base rate of Team 1 winning (0.778), match-fixing evidence pushes belief to Team 2 winning (0.739).
- **Vacuous antecedent (Fig. 9.5, p.148)**: `ω_x = (0.00, 0.00, 1.00, 0.80)`, `ω_{y|x} = (0.40, 0.50, 0.10, 0.40)`, `ω_{y|x̄} = (0.00, 0.40, 0.60, 0.40)`. Deduced `ω_y = (0.32, 0.48, 0.20, 0.40)`. P = 0.40.
- **Free base rate (Fig. 9.6-9.7)**: `a_y^+ = 0.52`, `a_y^- = 0.32`.
- **Sub-triangle (Fig. 9.9, p.153)**: `ω_x = (0.00, 0.40, 0.60, 0.50)` → P(x) = 0.30. `ω_{y|x} = (0.55, 0.30, 0.15, 0.38)`, `ω_{y|x̄} = (0.10, 0.75, 0.15, 0.38)`. Apex `ω_{y\|x̂} = (0.19, 0.30, 0.51, 0.38)`. Deduced `ω_{y\|x} = (0.15, 0.48, 0.37, 0.38)`. P = 0.29.
- **Inversion (Fig. 10.1, p.176)**: `ω_{y|x} = (0.80, 0.20, 0.00, 0.50)`, `ω_{y|x̄} = (0.20, 0.80, 0.00, 0.50)`, `a_x = 0.50`. Inverted: `ω_{x̃|y} = (0.72, 0.12, 0.16, 0.50)`, `ω_{x̃|ȳ} = (0.16, 0.72, 0.12, 0.50)`. **Inversion increases uncertainty.**
- **Medical-test abduction (Fig. 10.5, p.185)**: sensitivity / specificity (0.90, 0.05, 0.05). Disease A `a_x = 0.5`. Result: `b = 0.89, d = 0.04, u = 0.07, P = 0.93`.
- **Disease B (Fig. 10.6, p.186)**: same conditionals, `a_x = 0.01`. Result: `b = 0.14, d = 0.53, u = 0.33, P = 0.15` — base-rate fallacy made visible.
- **Military intelligence (p.194-198)**: three plans × three movements. Conditional probabilities Table 10.2; abduced result `P(x_1) = 0.65` but `b(x_1) = 0.00`, `u = 0.93`. Despite x_1 being highest projected, all of its mass is uncertainty — high analytic risk.
- **Joint distribution / weather-umbrella (p.200, Table 11.1)**: P(X) = (0.5, 0.3, 0.2). Conditionals; joint matrix `P_{XY}` summing to 1. Most likely (no umbrella, sunny) at 0.45.
- **Match-fixing joint (p.205, Table 11.3)**: marginal-on-X `b = (0.903, 0.025)`, `u = 0.072` (note: `u_X` was input as 0.10, came out 0.072 after round-trip).

## Fusion (Ch. 12)

- **Cinema First Attempt (Table 12.2, p.223)**: Alice/Bob/Clark on {BD, GM, WP}. Alice b(BD) = 0.99; Bob b(WP) = 0.99; Clark b(GM∪WP) = 1.0. Result A&B = b(GM) = 1.00; A&B&C also b(GM) = 1.00. **They watch Grey Matter.** This uses Zadeh's exact numerical example and shows BCF is the correct operator.
- **Cinema Second Attempt (Table 12.3, p.224)**: with u = 0.01, base rates a(BD) = 0.6, a(GM) = a(WP) = 0.2. A&B: P(BD) = 0.493 > P(WP) = 0.491 — base-rate breaks tie. Choose Black Dust. Adding Clark (against BD): P(WP) = 0.966. **Choose White Powder.**
- **Cinema Conflict (Table 12.4, p.225)**: Alice b(BD) = 1.00, Bob b(WP) = 1.00. **Undefined** (Con = 1) — correctly signals "no compromise possible."
- **Aleatory CBF (Fig. 12.4, p.228)**: `ω^A = (0.00, 0.30, 0.70, 0.70)`, `ω^B = (0.70, 0.00, 0.30, 0.30)`. Result `(A⋄B) = (0.62, 0.11, 0.27, 0.36, P=0.72)`.
- **Epistemic CBF (Fig. 12.5, p.229)**: same inputs, uncertainty-maximised. Result `(0.57, 0.00, 0.43, 0.36, P=0.72)`. Same projected probability as aleatory but higher u.
- **Zadeh Comparison (Tables 12.5/12.6, p.236)**: 𝕏 = {x_1, x_2, x_3}, base rate uniform. Source A: b(x_1) = 0.99, b(x_2) = 0.01. Source B: b(x_2) = 0.01, b(x_3) = 0.99. Compare BCF, A-CBF, E-CBF, ABF, WBF, CCF outputs. CCF gives `b(x_1, x_3) = 0.990` (compromise vague belief), matching intuition for two doctors disagreeing on diagnoses.

## Unfusion / Fission (Ch. 13)

- **Cumulative unfusion (p.240)**: `ω^{A⋄B} = (0.90, 0.05, 0.05, 0.50)`, `ω^B = (0.70, 0.10, 0.20, 0.50)` → `ω^A = (0.91, 0.03, 0.06, 0.50)`.
- **Fission (Table 13.1, p.242)**: ternary X with φ = 0.75. Argument `b = (0.20, 0.30, 0.40)`, `u = 0.10`, `a = (0.10, 0.20, 0.70)`. Result `ω_{C_1}: b = (0.194, 0.290, 0.387)`, `u = 0.129`. Result `ω_{C_2}: b = (0.154, 0.230, 0.308)`, `u = 0.308`. Projected probabilities preserved.

## Trust (Ch. 14)

- **Trust discounting (Eq. 14.8, p.257)**: `ω_B^A = (0.20, 0.40, 0.40, 0.75, P=0.50)`, `ω_X^B = (b(x_1)=0.45, b(x_2)=0.35, u=0.20, a(x_1)=0.25, P(x_1)=0.50)`. Derived `ω_X^{[A;B]}`: `b(x_1) = 0.225`, `b(x_2) = 0.175`, `u = 0.600`, `a(x_1) = 0.250`, `P(x_1) = 0.375`.
- **Restaurant advice (Fig. 14.6, p.258)**: vacuous trust on Bob (b=0, u=1, a=0.90); strong belief on Xylo (b=0.95, u=0.05, a=0.20). Discounted: `b = 0.85, u = 0.15, P = 0.88`. Demonstrates high base rate + vacuous trust still yields strong projected probability.
- **Multi-edge (Table 14.2, p.261)**: path [A;B;C;D,X] with three referrals (each `(0.20, 0.10, 0.70, 0.80, P=0.76)`) and final functional `(0.80, 0.20, 0.0, P=0.80)`. Product `P_D^A = 0.44`. Derived `ω_X^{[A;D]}: b = 0.35, d = 0.09, u = 0.56, a = 0.10, P = 0.41`.
- **Conflicting restaurants (Tables 14.4, 14.5, p.269-270)**: Bob recommends, Claire warns. Without revision: simple fusion → P = 0.465 (counter-intuitive). With revision: PD = 0.763, CC = 0.762, DC = 0.581; UD_B = 0.909, UD_C = 0.091; RF_B = 0.529, RF_C = 0.053. Revised fusion → **P = 0.208** (Claire dominant).

## Reputation (Ch. 16)

- **Polarisation (Fig. 16.2, p.298)**: 10 average ratings on level 3 vs 5 bad + 5 excellent. Both have point estimate σ = 0.5, but multinomial scores expose the difference.

## Subjective networks (Ch. 17)

- **Lung cancer (p.306-308)**: P(C|D) = 0.25 (single evidence). P(C|D,X) ≈ 0.97 (joint via naïve Bayes). Forward base-rate inference yields a(C) = 0.01.
- **Subjective Bayes' validation (Table 17.2, p.315)**: three-variable chain X ⇒ Y ⇒ Z. Method 1 (invert each then chain): `ω_{X̃|z_1}: b = 0.759, 0.036, u = 0.205`; `ω_{X̃|z_2}: b = 0.075, 0.767, u = 0.158`. Method 2 (chain then invert): `ω_{X̃|z_1}: b = 0.774, 0.042, u = 0.184`; `ω_{X̃|z_2}: b = 0.080, 0.769, u = 0.151`. **Equal projected probabilities; approximately equal uncertainty.**

---

# Algorithms / Procedures

## Decision-making (priority-ordered, Fig. 4.7, p.64)

1. Compute mass-sums for all options.
2. Compare utility-normalised probabilities. Different → pick greatest.
3. If tied, compare sharp belief mass. Different → pick greatest.
4. If tied, compare focal uncertainty. Different → pick least.
5. If all tied → "Difficult decision"; consider vague mass or base rates.

## Continuous hyperdomain indexing (p.10-11)

1. Index singletons of X with [1, k].
2. Group remaining R(X) values into cardinality classes j = 2, …, k-1.
3. Within each class, list values in order of lowest-indexed contained singleton, then second-lowest, etc.
4. Assign absolute indices [k+1, κ] sequentially across classes.

## Hyper → Multinomial → Uncertainty-Maximisation (p.37, p.39)

1. Project hyper-opinion → multinomial via Eq. 3.30.
2. Apply Eq. 3.27: `ü_X = min_i [P_X(x_i) / a_X(x_i)]` to project to simplex side.

## Binomial Deduction (Definition 9.1, Eq. 9.40-9.51)

1. Compute MBR `a_y` via Eq. 9.36 (or free in [0,1] if both u sum to 2).
2. Compute intermediate `b^I_y, d^I_y, u^I_y` via Eq. 9.41.
3. Determine selection coefficient K via 9-case analysis. Helpers `P(y\|x̂)` and `P(x)` by Eq. 9.51.
4. Output: `b_{y\|x} = b^I_y - a_y K`; `d_{y\|x} = d^I_y - (1-a_y) K`; `u_{y\|x} = u^I_y + K`.

## Multinomial Deduction (Sec. 9.5.4)

1. **MBR**: `a_Y(y) = Σ a_X(x) b_{Y|x}(y) / (1 - Σ a_X(x) u_{Y|x})` (Eq. 9.68).
2. **Sub-simplex apex** `ω_{Y\|X̂}`: enforce Pearl's plausible-reasoning constraint `b_{Y\|X̂}(y) ≥ min_i b_{Y|x_i}(y)` (Eq. 9.69); compute `u_j = (P_{Y\|X̂}(y) - min_i b_{Y|x_i}(y)) / a_Y(y)`; apex uncertainty `u_{Y\|X̂} = min_j u_j` (Eq. 9.74).
3. **Linear projection**: `u_{Y\|X} = u_X u_{Y\|X̂} + Σ u_{Y|x_i} b_X(x_i)` (Eq. 9.75); `b_{Y\|X}(y) = P_{Y\|X}(y) - a_Y(y) u_{Y\|X}` (Eq. 9.77).

## Subjective Bayes' Theorem 4-step uncertainty (Sec. 10.3.2)

1. Theoretical max uncertainties `ü_{x|y}, ü_{x|ȳ}` (Eq. 10.13-10.14).
2. Weighted proportional uncertainty `u^w_{y|X}` (Eq. 10.15-10.22).
3. Coproduct with irrelevance: `ũ_{x|y} = u^w_{y|X} ⊔ Ψ̄(y|X)` (Eq. 10.23).
4. Multiply: `u_{x\widetilde|y} = ü_{x|y} · ũ_{x|y}` (Eq. 10.24).

## CCF three-step (Def 12.9, p.234-235)

1. **Consensus**: `b_X^{cons}(x) = min(b_X^A(x), b_X^B(x))` over R(X).
2. **Compromise**: redistribute residue into vague beliefs over `P(X)` using base-rate-weighted overlap of residues; whole-frame mass `b^{comp}(X) = 0`.
3. **Merge**: normalise η, `b^{(A♡B)}(x) = b^{cons} + η · b^{comp}`, `u^{(A♡B)} = u^{pre} + η · b^{comp}(X)`.

## DSPG analysis (Sec. 15.3.1, Fig. 15.5)

1. Verify graph is a DSPG.
2. Identify each PPS by source-target pair. Compute nesting level NL of every edge.
3. Select PPS with highest NL. If none, go to step 7.
4. Discount each path in the PPS using two-edge or multi-edge trust discounting.
5. Fuse all paths in the PPS using selected trust-fusion operator (Ch. 12 selection).
6. Recompute NL of replacement edge. Loop to step 3.
7. Series-only: apply two-edge or multi-edge discounting end-to-end.

## DSPG synthesis (Sec. 15.4.1, Fig. 15.10)

1. Set threshold `p_T`. Empty DSPG.
2. Identify each path A→X. Compute product of projected probabilities of referral edges.
3. Rank by product. Initialise DSPG with path 1.
4. For each next ranked path: if product < p_T → stop.
5. Check Definition 15.7 criteria for inclusion.
6. If yes, add new edges. If no, drop.
7. Loop. Final DSPG analysed via Sec. 15.3.

## Trust + Reputation pipeline (p.301)

1. Reputation system publishes `R_B^{RS} = Beta^e(p_x, r_x, s_x, a_x)`.
2. Map to opinion `ω_B^{RS}` via Definition 3.3.
3. A trusts RS: `ω_{RS}^A`. B trusts F: `ω_F^B`.
4. Trust path `[A,F] = [A;RS] : [RS;B] : [B,F]`.
5. Result: `ω_F^A = ω_{RS}^A ⊗ ω_B^{RS} ⊗ ω_F^B`.

---

# Quotes Worth Preserving

(Selected for propstore relevance — full quote list in chunks.)

> "An analyst might for example want to give the input argument 'I don't know', which expresses total ignorance and uncertainty about some statement. However, an argument like that can not be expressed if the formalism only allows input arguments in the form of Booleans or probabilities. The probability p(x) = 0.5 would not be a satisfactory argument because it would mean that x and x̄ are exactly equally likely, which in fact is quite informative, and very different from ignorance." *(p.4)* — **The foundational quote for propstore's vacuous-vs-defaulted distinction.**

> "An analyst who has little or no evidence for providing input probabilities could be tempted or even encouraged to set probabilities with little or no confidence. This practice would generally lead to unreliable conclusions, often described as the problem of 'garbage in, garbage out'. What is needed is a way to express lack of confidence in probabilities. In subjective logic, the lack of confidence in probabilities is expressed as *uncertainty mass*." *(p.4)*

> "Uncertainty mass in the Dirichlet model reflects vacuity of evidence. Interpreting uncertainty mass as vacuity of evidence reflects the property that 'the fewer observations the more uncertainty mass'." *(p.5)*

> "An essential characteristic of subjective logic is thus to include base rates, which also makes it possible to define a bijective mapping between subjective opinions and Dirichlet PDFs." *(p.5)*

> "Initial vacuity of evidence exist *a priori*, as represented by uncertainty mass. Belief mass is then formed *a posteriori* as a function of collected evidence in accordance with the Beta and Dirichlet models." *(p.14)*

> "From a philosophical viewpoint, no one can ever be totally certain about anything in this world. So when the formalism allows explicit expression of uncertainty, as opinions do, it is extreme, and even unrealistic, to express a dogmatic opinion." *(p.20)*

> "Analysts are never forced to invent belief where there is none. In case they are ignorant, they can simply produce a vacuous or highly uncertain opinion. The same can not be said when using probabilities, where analysts sometimes have to 'pull probabilities out of thin air'." *(p.21)* — **Direct support for honest-ignorance principle.**

> "Vagueness is preferable over uncertainty, because vagueness is based on evidence, whereas uncertainty reflects vacuity of evidence." *(p.74)*

> "A fundamental assumption behind subjective logic is that different agents can have different opinions about the same variable. This also reflects the subjective reality of how we perceive the world we live in." *(p.79)*

> "By using beliefs it is possible to provide the argument 'I don't know' as input to a reasoning model, which is not possible with probabilities." *(p.83)*

> "There has been considerable confusion and controversy around the adequacy of belief fusion operators ... There is nothing wrong with Dempster's rule per se; there are situations where it is perfectly appropriate, and there are situations where it is clearly inappropriate. No single belief fusion operator is suitable in every situation." *(p.84)*

> "It is therefore recommended to always use the MBR distribution when applying Bayes' theorem." *(p.160)*

> "With the MBR of Eq.(9.36) it is guaranteed that the projected probabilities of binomial conditional opinions do not change after multiple inversions." *(p.165)*

> "the inherent uncertainty of situations no longer has to be 'hidden under the carpet', which is good news for analysts and decision makers." *(p.316)* — **Honest ignorance argument applied to SBN.**

> "Different people commonly have different opinions about the same evidence variables and conditionals of a model. ... Traditional Bayesian network modelling can not directly be applied to such situations because they assume a single analyst with a complete view of the whole model. In contrast, subjective networks are perfectly suited to model situations where different agents have different opinions about the conditionals and evidence variables of a model." *(p.323)* — **Direct claim about SN > BN for distributed analysis.**

> "Whenever multiple (conflicting) opinions are provided for a specific variable, trust fusion can be applied. In case input opinions are missing for some conditionals or evidence nodes, vacuous opinions can be used as input instead. In this way, the analysis of a model can be done incrementally as more evidence is gathered." *(p.323)*

> "Base rates do not go away just because the analyst derives marginal probabilities for the same variables. This confusion is eliminated in subjective logic by using the symbol `a(x)` for base rates and the symbol `P(x)` for probabilities, which is helpful for learning and practicing Bayesian analysis." *(p.326)*

> "Trust revision must be considered to be an *ad hoc* method, because there is no parallel in physical processes that can be objectively observed and analysed. [...] We invite the reader to reflect on these issues, and maybe come up with an alternative and improved design for the revision factor." *(p.270)* — **Author concedes trust revision is ad hoc.**

---

# End of notes

This concludes the synthesis. Total content: ~1900 lines covering 326 printed pages. For chapter-level detail beyond what is captured here, see the individual chunks in `chunks/chunk-*.md`. Bibliography (102 references) is in `citations.md`. Abstract is in `abstract.md`.

---

**See also (conceptual link):** [Quantifying Beliefs by Belief Functions: An Axiomatic Justification](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) - Smets axiomatically justifies belief functions and derives the pignistic transformation as a credal-to-decision projection. Subjective logic's projected probability E(x)=b(x)+a(x)u(x) plays the same role - both formalisms separate the credal level (where uncertainty is entertained) from the decision level (where a probability is committed). The vacuous opinion in subjective logic corresponds to Smets's I_Omega.
