# Pages 50-99 Notes

Note on pagination: PNG file `page-NNN.png` corresponds to printed page `NNN-18` (e.g., page-050.png = printed p.32; page-099.png = printed p.81). Page citations below use printed page numbers (with PNG index in brackets where helpful).

## Chapters/Sections Covered

- §3.5 Multinomial Opinions (continued from earlier chunk) — pp.32–38
  - §3.5.2 Dirichlet PDF (Definition 3.5, evidence form) — p.32
  - §3.5.3 Visualising Dirichlet PDFs — p.34
  - §3.5.4 Coarsening example: ternary→binary — p.34–35
  - §3.5.5 Mapping multinomial opinion ↔ Dirichlet PDF — p.36
  - §3.5.6 Uncertainty-Maximisation — p.37
- §3.6 Hyper-opinions — pp.39–46
  - §3.6.1 Hyper-opinion representation — p.39
  - §3.6.2 Projecting hyper-opinions to multinomial — p.40
  - §3.6.3 Dirichlet model on hyperdomains (HPDF) — p.41
  - §3.6.4 Mapping hyper-opinion ↔ Dirichlet HPDF — p.43
  - §3.6.5 Hyper-Dirichlet PDF — pp.43–46
- §3.7 Alternative Opinion Representations — pp.46–50
  - §3.7.1 Probabilistic notation — p.47
  - §3.7.2 Qualitative opinion representation — p.48
- Chapter 4: Decision Making Under Vagueness and Uncertainty — pp.51–81
  - §4.1 Aspects of belief and uncertainty — p.51
    - §4.1.1 Sharp belief mass; §4.1.2 Vague belief mass; §4.1.3 Dirichlet visualisation of vagueness; §4.1.4 Focal uncertainty mass
  - §4.2 Mass-Sum (per-value and total) — p.56
  - §4.3 Utility and Normalisation — p.59
  - §4.4 Decision Criteria — p.63
  - §4.5 The Ellsberg Paradox — p.65
  - §4.6 Examples of Decision Making — p.69
    - §4.6.1 Difference in projected probability
    - §4.6.2 Difference in sharpness
    - §4.6.3 Difference in vagueness and uncertainty
  - §4.7 Entropy in the Opinion Model — p.75
    - §4.7.1 Outcome surprisal; §4.7.2 Opinion entropy
  - §4.8 Conflict Between Opinions — p.79

## Definitions and Notation

- **Definition 3.5 (Dirichlet PDF)** *(p.32)*: For domain X of cardinality k, strength vector α_X, probability distribution p_X over X,
  Dir(p_X, α_X) = Γ(Σ α_X(x)) / Π Γ(α_X(x)) · Π p_X(x)^(α_X(x)-1), with α_X(x) ≥ 0; restriction p_X(x) ≠ 0 if α_X(x) < 1.

- **Definition 3.6 (Mapping: Multinomial Opinion ↔ Dirichlet PDF)** *(p.36)*: ω_X = (b_X, u_X, a_X) and Dir^e_X(p_X, r_X, a_X) are equivalent through Eq.(3.23). Forward: b_X(x) = r_X(x)/(W + Σ r_X(x_i)); u_X = W/(W + Σ r_X(x_i)). Inverse for u_X ≠ 0: r_X(x) = W·b_X(x)/u_X with 1 = u_X + Σ b_X(x_i). Inverse for u_X = 0 (dogmatic): r_X(x) = b_X(x)·∞ with 1 = Σ b_X(x_i).

- **Definition 3.7 (Hyper-opinion)** *(p.39)*: Domain X of cardinality k>2, hyperdomain R(X). Hypervariable X. Hyper-opinion ω_X = (b_X, u_X, a_X) where b_X is belief mass distribution over R(X) (composite values), u_X uncertainty mass scalar, a_X base rate distribution over X (singletons only). Hypernomial additivity (Eq.2.7) holds: Σ_{x∈R(X)} b_X(x) + u_X = 1.

- **Definition 3.8 (Dirichlet HPDF)** *(p.41)*: Hyperdomain R(X) with κ = 2^k − 2. Strength vector α_X over κ values. Dir^H_X(p^H_X, α_X) = Γ(Σ_{x∈R(X)} α_X(x)) / Π Γ(α_X(x)) · Π p^H_X(x)^(α_X(x)-1).

- **Definition 3.9 (Mapping: Hyper-opinion ↔ Dirichlet HPDF)** *(p.43)*: Eq.(3.35), structurally identical to Eq.(3.23) but indexed over R(X).

- **Definition 3.10 (Probabilistic Opinion Notation)** *(p.47)*: π_X = (P_X, u_X, a_X) with constraints a_X(x)·u_X ≤ P_X(x) ≤ a_X(x)·u_X + 1 − u_X and Σ P_X(x) = 1.

- **Definition 3.11 (Mapping: Belief ↔ Probabilistic Opinion)** *(p.47)*: Eq.(3.41) b_X(x) = P_X(x) − a_X(x)·u_X. Special: u_X=0 → ordinary discrete prob; u_X=1 → P_X = a_X (totally uncertain, defaults to base rate).

- **Definition 4.1 (Sharp Belief Mass)** *(p.51–52)*: b^S_X(x) = Σ_{x_i ⊆ x} b_X(x_i), ∀x ∈ R(X). Sum of belief masses on values that are subsets of x (collapses to b_X(x) for singletons; sums singletons inside a composite for composites).

- **Definition 4.2 (Total Sharp Belief Mass)** *(p.52)*: b^TS_X = Σ_{x_i ∈ X} b_X(x_i) — sum over singletons only.

- **Definition 4.3 (Vague Belief Mass)** *(p.52)*: b^V_X(x) = Σ_{x_j ∈ C(X), x_j ⊄ x} a_X(x|x_j) · b_X(x_j). Weighted (by relative base rate) sum over composite values that contain x. Captures cognitive vagueness — evidence that does not discriminate between singletons.

- **Definition 4.4 (Total Vague Belief Mass)** *(p.53)*: b^TV_X = Σ_{x ∈ C(X)} b_X(x). Sum of belief masses on composites only.

- **Definition 4.5 (Focal Uncertainty Mass)** *(p.55)*: u^F_X(x) = a_X(x) · u_X. Per-value share of total uncertainty distributed by base rate.

- **Definition 4.6 (Mass-Sum)** *(p.56)*: M_X(x) = (b^S_X(x), b^V_X(x), u^F_X(x)). Triplet for value x; satisfies b^S + b^V + u^F = P_X(x) (Eq.4.9).

- **Definition 4.7 (Total Mass-Sum)** *(p.58)*: M^T_X = (b^TS_X, b^TV_X, u_X), with b^TS + b^TV + u = 1 (Eq.4.11).

- **Definition 4.8 (Utility-Normalised Probability Vector)** *(p.60)*: P^N_X(x) = L_X(x)/λ^+ = λ_X(x)·P_X(x)/λ^+, where λ^+ is greatest absolute utility across all utility vectors being compared.

- **Definition 4.9 (Utility-Normalised Masses)** *(p.60)*: b^NS_X(x) = λ_X(x)·b^S_X(x)/λ^+; b^NV_X(x) = λ_X(x)·b^V_X(x)/λ^+; u^NF_X(x) = λ_X(x)·u^F_X(x)/λ^+.

- **Definition 4.10 (Utility-Normalised Mass-Sum)** *(p.61)*: M^N_X(x) = (b^NS_X(x), b^NV_X(x), u^NF_X(x)).

- **Definition 4.11 (Surprisal)** *(p.76)*: I_X(x) = − log_2(p_X(x)) — classical self-information, measured in bits when log base 2.

- **Definition 4.12 (Opinion Outcome Surprisal)** *(p.76)*: I^P_X(x) = − log_2(P_X(x)).

- **Definition 4.13 (Surprisal of Sharpness, Vagueness and Focal Uncertainty)** *(p.77)*:
  - I^S_X(x) = b^S_X(x) · I^P_X(x) / P_X(x)
  - I^V_X(x) = b^V_X(x) · I^P_X(x) / P_X(x)
  - I^U_X(x) = u^F_X(x) · I^P_X(x) / P_X(x)
  Additivity: I^S + I^V + I^U = I^P (Eq.4.53).

- **Definition 4.14 (Entropy)** *(p.77)*: H(X) = Σ p_X(x)·I_X(x) = − Σ p_X(x) log_2 p_X(x).

- **Definition 4.15 (Opinion Entropy)** *(p.78)*: H^P(ω_X) = − Σ_{x∈X} P_X(x) log_2 P_X(x).

- **Proposition 4.1** *(p.78)*: If ω^A_X and ω^B_X have P^A_X = P^B_X (and possibly different uncertainty), then H^P(ω^A) = H^P(ω^B). Proof: H^P depends only on the projected probability distribution.

- **Definition 4.16 (Sharpness Entropy)** *(p.78)*: H^S(ω_X) = − Σ b^S_X(x) log_2(P_X(x)).

- **Definition 4.17 (Vagueness Entropy)** *(p.78)*: H^V(ω_X) = − Σ b^V_X(x) log_2(P_X(x)).

- **Definition 4.18 (Uncertainty Entropy)** *(p.78)*: H^U(ω_X) = − Σ u^F_X(x) log_2(P_X(x)). Additivity: H^S + H^V + H^U = H^P (Eq.4.59).

- **Definition 4.19 (Base-Rate to Projected-Probability Cross Entropy)** *(p.79)*: H^BP(ω_X) = − Σ a_X(x) log_2(P_X(x)). Maximised when P_X = a_X.

- **Definition 4.20 (Degree of Conflict)** *(p.80)*: DC(ω^B_X, ω^C_X) = PD(ω^B_X, ω^C_X) · CC(ω^B_X, ω^C_X) where:
  - Projected Distance: PD(ω^B, ω^C) = Σ_x |P^B_X(x) − P^C_X(x)| / 2 ∈ [0,1]
  - Conjunctive Certainty: CC(ω^B, ω^C) = (1 − u^B_X)(1 − u^C_X) ∈ [0,1]

## Operators Defined / Used in This Range

- **Probability projection (multinomial)** — Eq.(3.28) on hyper-opinions:
  P_X(x) = Σ_{x_i ∈ R(X)} a_X(x|x_i) · b_X(x_i) + a_X(x)·u_X, ∀x ∈ X.
  For singleton-only domains this reduces to P_X(x) = b_X(x) + a_X(x)·u_X.

- **Hyper→Multinomial projection** *(p.40, Eq.3.30)*:
  b'_X(x) = Σ_{x' ∈ R(X)} a_X(x|x') · b_X(x'). Result ω'_X = (b'_X, u_X, a_X) is multinomial with same projected probability as ω_X.

- **Uncertainty-maximisation operator** *(p.37–38)*: Project ω_X = (b_X, u_X, a_X) along director-base-rate line in opinion simplex to side; result ω̈_X = (b̈_X, ü_X, a_X) with same P_X but maximum u. ü_X = min_i [P_X(x_i)/a_X(x_i)]. For hyper-opinions, first project to multinomial (Eq.3.30) then apply Eq.3.27.

- **Coarsening** (informal here, applied via mapping) *(p.34–35)*: Aggregate ternary into binary: domain X={x1,x2,x3} → {x1, x̄1={x2,x3}}. Base rates summed: a(x̄1) = a(x2) + a(x3). Evidence summed similarly. Projected probability of singletons is preserved through coarsening.

## Equations Found (LaTeX)

$$ \mathrm{Dir}(p_X,\alpha_X) = \frac{\Gamma\!\left(\sum_{x\in X}\alpha_X(x)\right)}{\prod_{x\in X}\Gamma(\alpha_X(x))} \prod_{x\in X} p_X(x)^{\alpha_X(x)-1} \quad (3.14) $$
Dirichlet PDF; α_X strength parameters.

$$ \alpha_X(x) = r_X(x) + a_X(x)\,W \quad (3.15) $$
Strength = evidence + non-informative prior weight. W defaults to 2.

$$ \mathrm{Dir}^e_X(p_X,r_X,a_X) = \frac{\Gamma(\sum (r_X(x)+a_X(x)W))}{\prod \Gamma(r_X(x)+a_X(x)W)} \prod p_X(x)^{r_X(x)+a_X(x)W-1} \quad (3.16) $$
Evidence-form Dirichlet PDF.

$$ \mathbf{E}_X(x) = \frac{\alpha_X(x)}{\sum_j \alpha_X(x_j)} = \frac{r_X(x) + a_X(x)\,W}{W + \sum_j r_X(x_j)} \quad (3.17) $$
Expected probability from Dirichlet.

$$ \mathrm{Var}_X(x) = \frac{(b_X(x) + a_X(x)u_X)(1-b_X(x)-a_X(x)u_X)\,u_X}{W + u_X} = \frac{P_X(x)(1-P_X(x))\,u_X}{W+u_X} \quad (3.18) $$
Dirichlet variance, expressed in opinion-space terms.

$$ P_X = E_X \;\Leftrightarrow\; b_X(x) + a_X(x)u_X = \frac{r_X(x) + W a_X(x)}{W + \sum_j r_X(x_j)} \quad (3.19{-}3.20) $$
Projected-probability/expected-probability equality requirement.

$$ \sum_x r_X(x) \to \infty \;\Leftrightarrow\; \sum_x b_X(x) \to 1, \quad u_X \to 0 \quad (3.21{-}3.22) $$
Limit behaviour — infinite evidence yields dogmatic opinion.

$$ \begin{cases} b_X(x) = \dfrac{r_X(x)}{W + \sum_i r_X(x_i)} \\ u_X = \dfrac{W}{W + \sum_i r_X(x_i)} \end{cases} \;\Leftrightarrow\; \begin{cases} r_X(x) = \dfrac{W b_X(x)}{u_X}, & u_X\ne 0 \\ 1 = u_X + \sum_i b_X(x_i) \end{cases} \quad (3.23) $$
Bijective mapping between multinomial opinion and evidence-Dirichlet, with dogmatic limit.

$$ P_X(x_i) = b_X(x_i) + a_X(x_i)\,u_X, \quad i=1\dots k \quad (3.24) $$
Projector line definition for uncertainty-maximisation.

$$ \ddot u_X = \frac{P_X(x_{i_0})}{a_X(x_{i_0})} \;\text{for some }i_0; \quad P_X(x_i) \ge a_X(x_i)\,u_X \;\forall i \quad (3.25{-}3.26) $$
Conditions for uncertainty-maximised opinion.

$$ \ddot u_X = \min_i \!\left[\frac{P_X(x_i)}{a_X(x_i)}\right] \quad (3.27) $$
Theoretical max uncertainty preserving projected probability.

$$ P_X(x) = \sum_{x_i \in R(X)} a_X(x|x_i)\,b_X(x_i) + a_X(x)\,u_X \quad (3.28) $$
Hyper-opinion projected probability over singletons.

$$ \text{Additivity (singletons)}: \sum_{x\in X} P_X(x) = 1; \quad \text{Super-additivity (hyper)}: \sum_{x\in R(X)} P_X(x) \ge 1 \quad (3.29.a,b) $$

$$ b'_X(x) = \sum_{x' \in R(X)} a_X(x|x')\,b_X(x') \quad (3.30) $$
Hyper-to-multinomial projection of belief.

$$ \mathrm{Dir}^H_X(p^H_X, \alpha_X) = \frac{\Gamma(\sum \alpha_X(x))}{\prod \Gamma(\alpha_X(x))} \prod p^H_X(x)^{\alpha_X(x)-1} \quad (3.31) $$
Dirichlet HPDF over hyperdomain (treating composites as if disjoint).

$$ \alpha_X(x) = r_X(x) + a_X(x)W;\; a_X(x) = \sum_{x_j \subseteq x, x_j\in X} a(x_j); W=2 \quad (3.32) $$

$$ \mathrm{Dir}^{eH}_X(p^H_X, r_X, a_X) = \dots \prod p^H_X(x)^{r_X(x)+a_X(x)W-1} \quad (3.33) $$

$$ E_X(x) = \frac{\sum_{x_i\in R(X)} a_X(x|x_i) r(x_i) + W a_X(x)}{W + \sum_{x_i\in R(X)} r(x_i)} \quad (3.34) $$
Expected probability from Dirichlet HPDF over singletons.

$$ \begin{cases} b_X(x) = r_X(x)/(W + \sum r_X(x_i)) \\ u_X = W/(W + \sum r_X(x_i)) \end{cases} \;\Leftrightarrow\; \begin{cases} r_X(x) = W b_X(x)/u_X \\ \sum b_X(x_i) + u_X = 1 \end{cases} \quad (3.35) $$
Hyper-opinion ↔ Dirichlet HPDF mapping (Eq.3.23 generalised to R(X)).

$$ \mathrm{HDir}^e_X(p_X, r_X, a_X) = B(r_X,a_X)^{-1} \left(\prod_{i=1}^k p_X(x_i)^{a_X(x_i)W - 1} \prod_{j=1}^\kappa p_X(x_j)^{r_X(x_j)}\right) \quad (3.36{-}3.37) $$
Hyper-Dirichlet PDF (Hankin 2010); B is normalisation factor (Eq.3.38), no closed form, computed numerically.

$$ p_X(x_j) = \sum_{x_i \subseteq x_j} p_X(x_i), \quad j\in[1,\kappa] \quad (3.39) $$
Composite probability is the sum of constituent singleton probabilities.

$$ \pi_X = (P_X, u_X, a_X), \quad a_X(x)u_X \le P_X(x) \le a_X(x)u_X + (1-u_X) \quad (3.40) $$

$$ b_X(x) = P_X(x) - a_X(x)\,u_X \quad (3.41) $$
Bijection probabilistic-notation ↔ belief-notation.

$$ \pi_x = (P(x), u_x, a_x): a_x u_x \le P(x) \le 1 \quad (3.42) $$
Binomial probabilistic notation.

$$ \mathrm{Confidence}(\omega_X) = c_X = 1 - u_X \quad (3.43) $$
Confidence as complement of uncertainty (binomial/multinomial only).

$$ b^S_X(x) = \sum_{x_i \subseteq x} b_X(x_i) \quad (4.1) $$

$$ b^{TS}_X = \sum_{x_i \in X} b_X(x_i) \quad (4.2) $$

$$ b^V_X(x) = \sum_{x_j \in C(X),\, x_j \not\subseteq x} a_X(x|x_j)\,b_X(x_j) \quad (4.3) $$

$$ b^{TV}_X = \sum_{x \in C(X)} b_X(x) \quad (4.4) $$

$$ u^F_X(x) = a_X(x)\,u_X \quad (4.8) $$

$$ b^S_X(x) + b^V_X(x) + u^F_X(x) = P_X(x) \quad (4.9) $$

$$ M_X(x) = (b^S_X(x), b^V_X(x), u^F_X(x)) \quad (4.10) $$

$$ b^{TS}_X + b^{TV}_X + u_X = 1 \quad (4.11) $$

$$ M^T_X = (b^{TS}_X, b^{TV}_X, u_X) \quad (4.12) $$

$$ L_X(x) = \lambda_X(x)\,P_X(x); \quad L^T_X = \sum_x \lambda_X(x)\,P_X(x) \quad (4.13{-}4.14) $$

$$ P^N_X(x) = \frac{\lambda_X(x)\,P_X(x)}{\lambda^+}; \quad b^{NS}_X = \frac{\lambda_X b^S_X}{\lambda^+}; \quad b^{NV}_X = \frac{\lambda_X b^V_X}{\lambda^+}; \quad u^{NF}_X = \frac{\lambda_X u^F_X}{\lambda^+} \quad (4.15{-}4.18) $$

$$ b^{NS}_X(x) + b^{NV}_X(x) + u^{NF}_X(x) = P^N_X(x) \quad (4.19) $$

$$ M^N_X(x) = (b^{NS}_X(x), b^{NV}_X(x), u^{NF}_X(x)) \quad (4.20) $$

$$ I_X(x) = -\log_2(p_X(x)); \quad I^P_X(x) = -\log_2(P_X(x)) \quad (4.48{-}4.49) $$

$$ I^S_X(x) = \frac{b^S_X(x) I^P_X(x)}{P_X(x)},\; I^V_X(x) = \frac{b^V_X(x) I^P_X(x)}{P_X(x)},\; I^U_X(x) = \frac{u^F_X(x) I^P_X(x)}{P_X(x)} \quad (4.50{-}4.52) $$

$$ I^S_X(x) + I^V_X(x) + I^U_X(x) = I^P_X(x) \quad (4.53) $$

$$ H(X) = -\sum_x p_X(x)\log_2 p_X(x);\; H^P(\omega_X) = -\sum_x P_X(x)\log_2 P_X(x) \quad (4.54{-}4.55) $$

$$ H^S(\omega_X) = -\sum_x b^S_X(x)\log_2 P_X(x);\; H^V(\omega_X) = -\sum_x b^V_X(x)\log_2 P_X(x);\; H^U(\omega_X) = -\sum_x u^F_X(x)\log_2 P_X(x) \quad (4.56{-}4.58) $$

$$ H^S + H^V + H^U = H^P \quad (4.59) $$

$$ H^{BP}(\omega_X) = -\sum_x a_X(x)\log_2 P_X(x) \quad (4.60) $$

$$ \mathrm{PD}(\omega^B,\omega^C) = \frac{\sum_x |P^B_X(x) - P^C_X(x)|}{2}; \;\mathrm{CC}(\omega^B,\omega^C) = (1-u^B_X)(1-u^C_X);\; \mathrm{DC} = \mathrm{PD}\cdot\mathrm{CC} \quad (4.61{-}4.63) $$

## Parameters / Constants / Defaults

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Non-informative prior weight | W | — | 2 | ≥2; equals cardinality if uniform required | 32–34 | W=2 makes binary prior uniform; larger W requires more evidence to influence posterior |
| Default base rate | a_X(x) | prob | 1/k | (0,1) | 32 | k = singleton domain cardinality |
| Hyperdomain cardinality | κ | — | 2^k − 2 | — | 41 | Excludes ∅ and X |
| Belief mass on hyperdomain (parameter count) | b_X | — | 2^k − 2 | — | 40 | Hyper-opinion has (2^k+k−1) parameters; (2^k+k−3) DOF after additivity |
| Logarithm base for surprisal | — | base | 2 | — | 76 | bits; alternatives: nats (e), hartleys (10) |

## Worked Examples and Numerics

- **Ternary urn (p.34):** k=3 markings x1,x2,x3; default a=1/3 each. Observe r(x1)=6, r(x2)=1, r(x3)=1 (with return). E_X(x1) = (6+1·2/3·... actually) = (6+W·a)/(W+Σr) = (6 + 2·1/3)/(2+8) = 6.667/10 ≈ 0.667 = 2/3. Stated: E_X(x1) = 2/3.

- **Coarsening (p.35):** Same urn coarsened to {x1, x̄1={x2,x3}}. a(x1)=1/3, a(x̄1)=2/3. r(x1)=6, r(x̄1)=2. E_X(x1) computed via Eq.3.17 = 2/3 — coarsening preserves projected probability of singletons.

- **Vagueness example (p.54, Eq.4.6–4.7):** Ternary X, hyperdomain has x4={x1,x2}, x5={x1,x3}, x6={x2,x3}. b_X(x6)=0.8; u_X=0.2; uniform a=0.33 each. Then P_X(x1)=0.066, P_X(x2)=0.467, P_X(x3)=0.467. Vague masses: b^V(x1)=0.0, b^V(x2)=0.4, b^V(x3)=0.4. Hyper-Dirichlet PDF visualised in Fig.4.2 — density spread along x2-x3 edge.

- **Mass-sum example (p.57, Table 4.1):** Hyperdomain values x1..x6 (x4..x6 composites). Belief masses b=(0.10,0.10,0.00,0.20,0.30,0.10), u=0.20; base rates (0.20,0.30,0.50,0.50,0.70,0.80). Computed sharp/vague/focal/projected per row tabulated. Projected probabilities increase from 0.30 (x1) to 0.70 (x6).

- **Utility-normalisation urn example (p.61–62, Eqs.4.21–4.22; Table 4.2; Fig.4.6):** Urn X has 70 red, 10 black, 20 unknown → ω_X with b_X(x1=Red)=7/10, b_X(x2=Black)=1/10, u_X=2/10, base rates 1/2 each. Urn Y has 40 red, 20 black, 40 unknown → b_Y(y1)=4/10, b_Y(y2)=2/10, u_Y=4/10. Bet $1000 if Black drawn from X (option X), $500 if Black drawn from Y (option Y). λ^+=1000. P_X(x2)=0.2, P_Y(y2)=0.4. Utility-normalised probabilities are equal (P^N_X(x2)=P^N_Y(y2)). Decide on sharp belief mass: b^S_Y(y2) > b^S_X(x2) → choose option Y.

- **Ellsberg paradox (p.65, Eq.4.24–4.25; Fig.4.8–4.10):** Urn with 30 red, 60 black-or-yellow (90 total). Hyperdomain {x1=R, x2=B, x3=Y, x4={R,B}, x5={R,Y}, x6={B,Y}}. Hyper-opinion: b(x1)=1/3, b(x6)=2/3, all others 0; uniform 1/3 base rates over singletons; u=0. Game 1 (1A=R, 1B=B): P(R)=1·1/3=1/3, P(B)=1/2·2/3=1/3. Equal projected probability, but b^S(R)=1/3, b^V(B)=1/3 — sharp belief favours 1A. Game 2 (2A=R-or-Y, 2B=B-or-Y): P(2A)=2/3, P(2B)=2/3; b^V(2A)=1/3, b^S(2B)=2/3 — sharp belief favours 2B. Both choices rational under sharpness criterion.

- **Decision Game 1 (p.69, Eq.4.33–4.35; Fig.4.11):** Vacuous urn X (all u=1, base rates 1/3 singletons / 2/3 composites) vs urn Y with 40R/30B/20Y. Yellow win: P_X(x3)=1/3, P_Y(y3)=2/9 ≈ 0.222. Choose X (greater projected probability) despite focal uncertainty mass.

- **Decision Game 2 (p.71–72, Eq.4.36–4.41; Fig.4.12):** Urn X 30 R, 60 BY-composite vs urn Y 10R/10B/10Y/60 composite. P_X(x3)=1/3, P_Y(y3)=1/3 equal. Sharp belief mass: b^S_X(x3)=0; b^S_Y(y3)=1/9. Choose Y for greater sharpness.

- **Decision Game 3 (p.73–75, Eq.4.42–4.47; Fig.4.13):** Urn X 20R, 40 BY-composite, 30 RBY-composite vs urn Y entirely RBY-composite (vacuous). Yellow win: P_X(x3)=1/3 = P_Y(y3). Sharp belief masses both 0. Vague masses: b^V_X(x3)=2/9, b^V_Y(y3)=0. Focal uncertainty: u^F_X(x3)=1/9, u^F_Y(y3)=1/3. Choose X — least focal uncertainty (vagueness preferred over uncertainty since vagueness rests on evidence).

- **Conflict examples (p.80–81, Eq.4.64; Fig.4.14–4.15):** ω^B_{X1}=(0.05,0.15,0.80,0.90), ω^C_{X1}=(0.68,0.22,0.10,0.90). Both project to 0.77, so PD=0, hence DC=0. Same belief masses but different base rates (0.10): ω^B_{X2}=(0.05,0.15,0.80,0.10), ω^C_{X2}=(0.68,0.22,0.10,0.10). DC = 0.56·(1−0.80)·(1−0.10) = 0.56·0.20·0.90 = 0.10.

## Algorithms / Procedures

- **Decision-making process (p.63–64, Fig.4.7) — priority-ordered criteria:**
  1. Compute mass-sums for all options.
  2. Compare utility-normalised probabilities. If different → pick greatest.
  3. If tied, compare sharp belief mass. If different → pick greatest.
  4. If tied, compare focal uncertainty. If different → pick least.
  5. If all tied → "Difficult decision"; consider vague-mass composition or base rates.

- **Hyper-to-Multinomial-to-Uncertainty-Maximisation pipeline (p.39, p.37):**
  1. Project hyper-opinion → multinomial via Eq.(3.30).
  2. Apply Eq.(3.27) ü_X = min_i [P_X(x_i)/a_X(x_i)] to project to simplex side.

## Figures and Tables of Interest

- **Fig 3.4 (p.35):** Prior (uniform) and posterior Dirichlet PDFs on ternary domain — uniform flat triangle vs. peaked posterior near x1.
- **Fig 3.5 (p.35):** Beta PDFs after coarsening — uniform → peaked near 0.7.
- **Fig 3.6 (p.38):** Uncertainty-maximised opinion ω̈ in opinion tetrahedron with projector and director lines.
- **Fig 3.7 (p.46):** Hyper-Dirichlet PDFs on ternary domain showing scenarios A and B; non-Dirichlet-shape distributions.
- **Fig 3.8 (p.49):** Qualitative parallelogram-cell mappings to opinion triangle for a=1/3 and a=2/3.
- **Fig 4.1 (p.54):** Ternary hyperdomain Venn diagram with composites x4,x5,x6.
- **Fig 4.2 (p.55):** Hyper-Dirichlet PDF with vague belief — density along an edge.
- **Fig 4.3, 4.4, 4.5 (p.57–59):** Mass-sum diagrams showing per-value and total mass-sum.
- **Fig 4.6 (p.62):** Mass-sum and utility-normalised mass-sum diagrams for urn X vs Y.
- **Fig 4.7 (p.64):** Decision-making flowchart with four priority levels.
- **Fig 4.8 (p.65):** Ellsberg hyperdomain Venn.
- **Figs 4.9–4.10 (p.68):** Ellsberg game 1 and 2 mass-sum diagrams.
- **Figs 4.11–4.13:** Decision games 1, 2, 3 mass-sum diagrams.
- **Fig 4.14–4.15 (p.81):** Visualisation of opinion conflict — opinion triangle plus Beta PDF.
- **Table 3.3 (p.45):** Genetic engineering eggs example — observation counts per scenario and mutation type.
- **Table 3.4 (p.49):** 9-likelihood × 5-confidence qualitative grid (e.g. cells "9E" through "1A").
- **Table 4.1 (p.57):** Mass-sum example numerical breakdown.
- **Table 4.2 (p.62):** Betting options X vs Y utility table.
- **Tables 4.3–4.4 (p.66):** Ellsberg games 1, 2 utility tables.
- **Tables 4.5–4.7:** Decision games 1, 2, 3 utility tables.

## Quotes Worth Preserving

- *(p.34)* "Selecting W > 2 would result in new observation evidence having relatively less influence over the Dirichlet PDF... Note that it would be unnatural to require a uniform probability density over arbitrarily large domains, because it would make the PDF insensitive to new observation evidence."

- *(p.39)* "Belief mass assigned to composite values x ∈ C(X) represents vagueness."

- *(p.50)* "The level of confidence can be expressed as the complement of uncertainty mass... For hyper-opinions, low uncertainty mass does not necessarily indicate high confidence because belief mass can express vagueness."

- *(p.50, citing Brasfield 2009)* "[Analytic confidence] is not the same as using words of estimative probability, which indicate likelihood. It is possible for an analyst to suggest an event is virtually certain based on the available evidence, yet have a low amount of confidence in that forecast due to a variety of factors..."

- *(p.53)* "Uncertainty reflects vacuity of evidence, whereas vagueness results from evidence that fails to discriminate between specific singletons. A vacuous (totally uncertain) opinion — by definition — does not contain any vagueness. Hyper-opinions can contain vagueness, whereas multinomial and binomial opinions never contain vagueness."

- *(p.69)* "The Ellsberg paradox only involves vagueness, not uncertainty. In fact, the Ellsberg paradox is too simplistic for teasing out the whole spectre of sharp belief, vague belief and uncertainty of opinions."

- *(p.74)* "Vagueness is preferable over uncertainty, because vagueness is based on evidence, whereas uncertainty reflects vacuity of evidence."

- *(p.75)* "People tend to be risk-averse, so they prefer to make decisions under low entropy and low surprisal."

- *(p.78)* "Opinion entropy is insensitive to change in the uncertainty mass of an opinion, as long as the projected probability distribution P_X remains the same." (Proposition 4.1.)

- *(p.79)* "A fundamental assumption behind subjective logic is that different agents can have different opinions about the same variable. This also reflects the subjective reality of how we perceive the world we live in."

- *(p.80)* "A large PD does not necessarily indicate conflict, because the potential conflict is defused in case one (or both) opinions have high uncertainty. The more uncertain one or both opinions are, the more tolerance for a large PD should be given."

## Implementation Notes

- **W default = 2** for binary; for k-domain with non-uniform prior, W=2 still typical. Setting W = k yields uniform PDF but desensitises to evidence.
- **Bijection direction matters at u=0 and u=1**: For dogmatic (u=0), evidence is infinite (r=b·∞); store as flag/sentinel. For vacuous (u=1), all r=0 and P=a (defaults to base rate).
- **Hyper-opinion DOF count:** raw parameters = (2^k + k − 1), DOF = (2^k + k − 3) after the two additivity constraints (Eqs.2.7, 2.8).
- **Super-additivity** of hyper-projection on R(X) is expected (Eq.3.29.b) — composite probabilities double-count constituent singletons.
- **Hyper-Dirichlet normalisation factor B(r,a) has no closed form** — numerical integration required (Hankin's R package recommended).
- **Uncertainty-maximisation needs sequential projection for hyper-opinions:** project to multinomial first (Eq.3.30), then maximise (Eq.3.27).
- **Vagueness and uncertainty are different masses with different decisions implications:** vague belief is evidence-based, uncertainty is vacuity-based; ranking precedence is sharp > vague > uncertainty.
- **Confidence(ω) = 1 − u** is only meaningful for binomial/multinomial. For hyper-opinions, low u may co-exist with vagueness so it does not mean high confidence.
- **Mass-sum additivity:** b^S(x) + b^V(x) + u^F(x) = P(x); b^TS + b^TV + u = 1. Use these as invariants/test cases.
- **Decision criteria are priority-ordered, not weighted.** Implement as cascading equality checks, not as a scoring sum.
- **Cross entropy H^BP** is maximised when P_X = a_X (intuition: highest "surprise" of base-rate observer when projection equals base rate).
- **Conflict measure DC = PD · CC** is "coarse" — two opinions with very different PDFs can have DC=0 if both are highly uncertain (CC≈0). Used in trust revision (Section 14.5).

## Criticisms of Prior Work

- *(p.62)* "Note that in classical utility theory, decisions are based on expected utility for possible options. It is also possible to eliminate the notion of utility by integrating it into the probabilities for the various options [8], which produces a utility-normalised probability vector."
- *(p.69)* "Other models of uncertain probabilities are also able to explain the Ellsberg paradox, such as e.g. Choquet capacities (Choquet 1953 [14], Chateauneuf 1991 [11]). However, the Ellsberg paradox only involves vagueness, not uncertainty. In fact, the Ellsberg paradox is too simplistic for teasing out the whole spectre of sharp belief, vague belief and uncertainty of opinions." — claim: the SL framework subsumes Choquet because it can distinguish sharp/vague/focal-uncertainty, which Choquet's capacities cannot.
- *(p.69)* Subjective logic claim: "As far as we are aware, no other model of uncertain reasoning is able to distinguish and correctly rank the described situations in the same way."

## Open Threads / Forward References

- **Section 4.4** for a detailed summary of decision criteria — referenced from §4.0 *(p.51)*.
- **Section 4.5** explicitly forward-references **Chapter 4** for vagueness (already inside ch.4) and discusses Ellsberg paradox.
- **Chapter 16** (Bayesian Reputation Systems) referenced *(p.37)* — collects feedback ratings as evidence-Dirichlet observations.
- **Section 14.5** for trust revision based on degree of conflict *(p.79–81)*.
- **CertainLogic [87]** — equivalent representation of binomial opinions, mentioned at p.46 without details.
- **Chapter 4** also notes Hankin [33] for hyper-Dirichlet definition and software package.
- **Section 3.5.6** notes input opinions to reasoning models: epistemic vs aleatory distinction is significant; uncertainty-maximisation is characteristic of epistemic opinions.

