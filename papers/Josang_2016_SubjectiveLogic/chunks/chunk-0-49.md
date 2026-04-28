# Pages 0-49 Notes

PNG file indices 000-049. The book printed pages start at p.vii (Foreword) on PNG 005 and run through printed page 31 on PNG 049. Front matter (cover, ISBN, dedication) on PNGs 000-004; Foreword on PNGs 005-006; Preface on PNGs 007-008; Acknowledgements on PNGs 009-010; Contents on PNGs 011-015; Chapter 1 (Introduction) on PNGs 016-021 (printed pp.1-6); Chapter 2 (Elements of Subjective Opinions) on PNGs 022-031 (printed pp.7-18); Chapter 3 (Opinion Representations) starts on PNG 032 and pages 3.5.2 on PNG 049 ends mid-section. Page numbering throughout these notes uses the **printed page** when visible.

## Chapters/Sections Covered

- Front matter, dedication, Foreword (Lance Kaplan, Adelphi MD, March 2016) *(p.vii-viii)*
- Preface (Audun Jøsang, Oslo, March 2016) *(p.ix-x)*
- Acknowledgements *(p.xi-xiii)*
- Contents (full TOC; chs. 1-17, References, Acronyms, Index) *(p.xv-xxi)*
- **Chapter 1 — Introduction** *(p.1-6)*
- **Chapter 2 — Elements of Subjective Opinions** *(p.7-18)*
  - 2.1 Motivation for the Opinion Representation *(p.7)*
  - 2.2 Flexibility of Representation *(p.8)*
  - 2.3 Domains and Hyperdomains *(p.8-12)*
  - 2.4 Random Variables and Hypervariables *(p.12)*
  - 2.5 Belief Mass Distribution and Uncertainty Mass *(p.13-14)*
  - 2.6 Base Rate Distributions *(p.14-17)*
  - 2.7 Probability Distributions *(p.17-18)*
- **Chapter 3 — Opinion Representations** *(starts p.19; chunk ends mid-3.5.2 on p.31)*
  - 3.1 Belief and Trust Relationships *(p.19-20)*
  - 3.2 Opinion Classes *(p.20-21)*
  - 3.3 Aleatory and Epistemic Opinions *(p.22-23)*
  - 3.4 Binomial Opinions *(p.24-29)*
    - 3.4.1 Binomial Opinion Representation *(p.24-25)*
    - 3.4.2 The Beta Binomial Model *(p.26-28)*
    - 3.4.3 Mapping Between a Binomial Opinion and a Beta PDF *(p.28-29)*
  - 3.5 Multinomial Opinions *(p.30-...)*
    - 3.5.1 The Multinomial Opinion Representation *(p.30-31)*
    - 3.5.2 The Dirichlet Multinomial Model — section header only on p.31 (continues into next chunk)

## Definitions and Notation

### Symbols and Conventions
- Domains denoted by **blackboard bold capitals**: 𝕏, 𝕐, ℤ. Variables denoted by italic capitals: X, Y, Z. *(p.12)*
- Binary domain: 𝕏 = {x, x̄}, where x̄ is the complement (negation) of x. *(p.8)*
- Cardinality of domain: k = |𝕏|. Cardinality of hyperdomain: κ = |𝓡(𝕏)| = 2^k − 2. *(p.10)*
- Powerset 𝓟(𝕏); reduced powerset (hyperdomain) 𝓡(𝕏); composite set 𝓒(𝕏).
- Opinion notation: ω_X^A = (b_X, u_X, a_X) — superscript A is the belief owner agent; subscript X is the target variable. *(p.19, 20)*
- Trust relationship: [A, E] = directed trust from agent A to entity E; belief relationship [A, X]. *(p.19)*
- Probability: lower-case p or capital P; base rate: a (NOT p). *(p.5)* This is a deliberate departure from Bayesian convention to distinguish base rates from posterior probabilities.
- Belief mass distribution: bold ***b***_X. Uncertainty mass: scalar u_X. Base rate distribution: bold ***a***_X. Probability distribution: bold ***p***_X. Hyper-probability distribution: ***p***_X^H.
- Opinion class shorthand glyphs introduced p.24: ω̈_x = uncertainty-maximised (epistemic) opinion (b=0 or d=0); ω̲_x = dogmatic opinion (u=0); ω̂_x = vacuous opinion (u=1).

### Definition 2.1 (Hyperdomain) *(p.9)*
Let 𝕏 be a domain, 𝓟(𝕏) its powerset. The hyperdomain 𝓡(𝕏) is the reduced powerset excluding the empty set {∅} and the domain itself {𝕏}:
$$\mathcal{R}(\mathbb{X}) = \mathcal{P}(\mathbb{X}) \setminus \{\{\mathbb{X}\}, \{\emptyset\}\} \quad (2.1)$$

### Definition 2.2 (Composite Set) *(p.12)*
Let 𝕏 be a domain of cardinality k, hyperdomain 𝓡(𝕏) of cardinality κ. Every proper subset x ⊂ 𝕏 with |x| ≥ 2 is a composite value. The composite set 𝓒(𝕏):
$$\mathcal{C}(\mathbb{X}) = \{x \subset \mathbb{X} \text{ where } |x| \geq 2\} \quad (2.3)$$
Equivalences:
$$\mathcal{C}(\mathbb{X}) = \mathcal{R}(\mathbb{X}) \setminus \mathbb{X} \quad (2.4)$$
$$|\mathcal{C}(\mathbb{X})| = \kappa - k \quad (2.5)$$

### Definition 2.3 (Hypervariable) *(p.12)*
A variable X taking values from the hyperdomain 𝓡(𝕏). A hypervariable can be constrained to a random variable by restricting it to the domain 𝕏 only.

### Definition 2.4 (Belief Mass Distribution) *(p.13-14)*
Multinomial belief mass distribution: ***b***_X : 𝕏 → [0,1], with additivity requirement:
$$u_X + \sum_{x \in \mathbb{X}} \mathbf{b}_X(x) = 1 \quad (2.6)$$
Hypernomial belief mass distribution: ***b***_X : 𝓡(𝕏) → [0,1], with additivity requirement:
$$u_X + \sum_{x \in \mathcal{R}(\mathbb{X})} \mathbf{b}_X(x) = 1 \quad (2.7)$$

### Definition 2.5 (Base Rate Distribution) *(p.15)*
***a***_X : 𝕏 → [0,1], with:
$$\sum_{x \in \mathbb{X}} \mathbf{a}_X(x) = 1 \quad (2.8)$$

### Definition 2.6 (Base Rate Distribution over Hyperdomain) *(p.16)*
For a composite x_i ∈ 𝓡(𝕏):
$$\mathbf{a}_X(x_i) = \sum_{\substack{x_j \in \mathbb{X} \\ x_j \subseteq x_i}} \mathbf{a}_X(x_j), \quad \forall x_i \in \mathcal{R}(\mathbb{X}) \quad (2.9)$$
The base rate of a composite is the **sum of base rates of singletons it contains**. NOTE this is super-additive over 𝓡(𝕏) — singletons are counted multiple times — so it is not itself a probability distribution.

### Definition 2.7 (Relative Base Rate) *(p.17)*
$$\mathbf{a}_X(x \mid x_i) = \frac{\mathbf{a}_X(x \cap x_i)}{\mathbf{a}_X(x_i)}, \quad \forall x, x_i \in \mathcal{R}(\mathbb{X}), \text{ where } \mathbf{a}_X(x_i) \neq 0 \quad (2.10)$$
If a_X(x_i) = 0 then a_X(x|x_i) = 0; the author recommends always assuming a_X(x_i) > 0 for every singleton.

### Definition 2.8 (Probability Distribution) *(p.17-18)*
Standard: ***p***_X : 𝕏 → [0,1] with $\sum_{x \in \mathbb{X}} \mathbf{p}_X(x) = 1$ (Eq. 2.11).
Hyper-probability: ***p***_X^H : 𝓡(𝕏) → [0,1] with $\sum_{x \in \mathcal{R}(\mathbb{X})} \mathbf{p}_X^H(x) = 1$ (Eq. 2.12).
Hyper-probability projects onto standard probability via:
$$\mathbf{p}_X(x) = \sum_{x_i \in \mathcal{R}(\mathbb{X})} \mathbf{a}_X(x \mid x_i) \, \mathbf{p}_X^H(x_i), \quad \forall x \in \mathbb{X} \quad (2.13)$$

### Definition 3.1 (Binomial Opinion) *(p.24)*
Let 𝕏 = {x, x̄}, X ∈ 𝕏. A binomial opinion about value x is the ordered **quadruplet**:
$$\omega_x = (b_x, d_x, u_x, a_x) \text{ with } b_x + d_x + u_x = 1 \quad (3.1)$$
where:
- b_x: belief mass for x = TRUE
- d_x: disbelief mass for x = FALSE (i.e. X = x̄)
- u_x: uncertainty mass (vacuity of evidence)
- a_x: base rate (prior probability of x without evidence)

### Definition 3.2 (Beta Probability Density Function) *(p.26)*
Beta(p_x, α, β) : [0,1] → ℝ_≥0,
$$\text{Beta}(p_x, \alpha, \beta) = \frac{\Gamma(\alpha + \beta)}{\Gamma(\alpha)\Gamma(\beta)} p_x^{\alpha - 1}(1 - p_x)^{\beta - 1}, \quad \alpha > 0, \beta > 0 \quad (3.6)$$
Restrictions: p_x ≠ 0 if α < 1; p_x ≠ 1 if β < 1.

### Definition 3.3 (Mapping: Binomial Opinion ↔ Beta PDF) *(p.28)*
The bijection that anchors the entire theory:
$$\begin{cases} b_x = r_x / (W + r_x + s_x) \\ d_x = s_x / (W + r_x + s_x) \\ u_x = W / (W + r_x + s_x) \end{cases} \Leftrightarrow \begin{cases} \text{For } u \neq 0: r_x = b_x W / u_x, \; s_x = d_x W / u_x, \; 1 = b_x + d_x + u_x \\ \text{For } u_x = 0: r_x = b_x \cdot \infty, \; s_x = d_x \cdot \infty, \; 1 = b_x + d_x \end{cases} \quad (3.11)$$
Default non-informative prior weight **W = 2**, chosen so a vacuous opinion (r=s=0) with default base rate a_x = 1/2 maps to the **uniform Beta PDF** Beta(p_x, 1, 1).

The vacuous binomial opinion is ω_x = (0, 0, 1, 1/2) and corresponds to Beta(p_x, 1, 1) under default base rate. *(p.28)*

### Definition 3.4 (Multinomial Opinion) *(p.30)*
For domain 𝕏 with k = |𝕏| > 2 and random variable X ∈ 𝕏, a multinomial opinion is the ordered triplet:
$$\omega_X = (\mathbf{b}_X, u_X, \mathbf{a}_X)$$
satisfying additivity Eq.(2.6). Multinomial has 2k+1 parameters; with the two additivity constraints, 2k−1 degrees of freedom.

## Theorems / Lemmas / Propositions / Corollaries

No numbered theorems/lemmas in this range; all results are stated as definitions and equations. Notable algebraic facts proved or asserted:
- Sub-additivity of belief mass: ∑ b ≤ 1, with deficit absorbed by u_X. *(p.13)*
- Eq.(2.4): 𝓒(𝕏) = 𝓡(𝕏) \ 𝕏 (composite set is hyperdomain minus singletons). *(p.12)*
- Cardinality identity: |𝓡(𝕏)| = 2^k − 2. *(p.10)*
- Beta PDF additivity: $\int_0^1 \text{Beta}(p_x, \alpha, \beta) dp_x = 1$. *(p.27)*
- Uniform PDF emerges from r_x = s_x = 0, a_x = 1/2, W = 2 → α = β = 1, Var = 1/12. *(p.28)*

## Operators Defined / Used in This Range

The introduction Table 1.1 *(p.2)* lists probabilistic-logic operator analogues (foreshadowing later subjective-logic chapters):

| Binary | Probabilistic Logic | Equation # |
|--------|---------------------|------------|
| AND (x∧y) | Product: p(x∧y) = p(x)p(y) | (I) |
| OR (x∨y) | Coproduct: p(x∨y) = p(x) + p(y) − p(x)p(y) | (II) |
| XOR (x≢y) | Inequivalence: p(x≢y) = p(x)(1−p(y)) + (1−p(x))p(y) | (III) |
| EQU (x≡y) | Equivalence: p(x≡y) = 1 − p(x≢y) | (IV) |
| MP {(x→y), x} ⊢ y | Deduction: p(y‖x) = p(x)p(y\|x) + p(x̄)p(y\|x̄) | (V) |
| MT {(x→y), ȳ} ⊢ x̄ | Abduction: p(x\|y) = a(x)p(y\|x) / [a(x)p(y\|x) + a(x̄)p(y\|x̄)] | (VI) |
| (same) | p(x\|ȳ) = a(x)p(ȳ\|x) / [a(x)p(ȳ\|x) + a(x̄)p(ȳ\|x̄)] | (VII) |
| (same) | p(x∼‖y) = p(y)p(x\|y) + p(ȳ)p(x\|ȳ) | (VIII) |
| CP (x→y) ⇔ (ȳ→x̄) | Bayes' theorem: p(x̄\|ȳ) = 1 − a(x)p(ȳ\|x) / [a(x)p(ȳ\|x) + a(x̄)p(ȳ\|x̄)] | (IX) |

These are stated as **probabilistic logic** (PL) generalising binary logic. Subjective logic, defined in later chapters (outside this chunk), generalises PL further by adding uncertainty mass.

The notation `p(y‖x)` (double bar) means probability of child y is **derived as a function** of conditionals p(y|x), p(y|x̄) and evidence probability p(x) — i.e. the deduction operator. Symmetrically `p(x∼‖y)` (with tilde) denotes conditional **abduction** — derived target from input conditionals and evidence on child. *(p.3)*

## Equations Found (LaTeX)

$$\mathcal{R}(\mathbb{X}) = \mathcal{P}(\mathbb{X}) \setminus \{\{\mathbb{X}\}, \{\emptyset\}\} \quad (2.1)$$
Hyperdomain definition. *(p.9)*

$$C(\kappa, j) = \binom{\kappa}{j} = \frac{\kappa!}{(\kappa - j)! \, j!} \quad (2.2)$$
Choose function (binomial coefficient) for cardinality-class indexing of hyperdomain. *(p.11)*

$$\mathcal{C}(\mathbb{X}) = \{x \subset \mathbb{X} \text{ where } |x| \geq 2\} \quad (2.3)$$
*(p.12)*

$$\mathcal{C}(\mathbb{X}) = \mathcal{R}(\mathbb{X}) \setminus \mathbb{X} \quad (2.4)$$
*(p.12)*

$$|\mathcal{C}(\mathbb{X})| = \kappa - k \quad (2.5)$$
*(p.12)*

$$u_X + \sum_{x \in \mathbb{X}} \mathbf{b}_X(x) = 1 \quad (2.6)$$
Multinomial belief-mass additivity. *(p.14)*

$$u_X + \sum_{x \in \mathcal{R}(\mathbb{X})} \mathbf{b}_X(x) = 1 \quad (2.7)$$
Hypernomial belief-mass additivity. *(p.14)*

$$\sum_{x \in \mathbb{X}} \mathbf{a}_X(x) = 1 \quad (2.8)$$
Base rate distribution additivity over the **domain**. *(p.15)*

$$\mathbf{a}_X(x_i) = \sum_{\substack{x_j \in \mathbb{X} \\ x_j \subseteq x_i}} \mathbf{a}_X(x_j) \quad (2.9)$$
Base rate of composite = sum of base rates of contained singletons. Super-additive over 𝓡(𝕏). *(p.16)*

$$\mathbf{a}_X(x \mid x_i) = \frac{\mathbf{a}_X(x \cap x_i)}{\mathbf{a}_X(x_i)} \quad (2.10)$$
Relative base rate. *(p.17)*

$$\sum_{x \in \mathbb{X}} \mathbf{p}_X(x) = 1 \quad (2.11)$$
$$\sum_{x \in \mathcal{R}(\mathbb{X})} \mathbf{p}_X^H(x) = 1 \quad (2.12)$$
Probability and hyper-probability additivity. *(p.18)*

$$\mathbf{p}_X(x) = \sum_{x_i \in \mathcal{R}(\mathbb{X})} \mathbf{a}_X(x \mid x_i) \, \mathbf{p}_X^H(x_i) \quad (2.13)$$
Hyper-probability → standard probability projection via relative base rates. *(p.18)*

$$b_x + d_x + u_x = 1 \quad (3.1)$$
Binomial opinion additivity (simplex constraint). *(p.24)*

$$P(x) = b_x + a_x u_x \quad (3.2)$$
**Binomial probability projection** — the most important formula in subjective logic for this range. The fraction a_x of uncertainty mass u_x contributes to the projected probability of x. *(p.24)*

$$\text{Var}(x) = \frac{P(x)(1 - P(x)) u_x}{W + u_x} \quad (3.3)$$
Binomial opinion variance, derived from Beta PDF variance. *(p.24)*

$$\text{PDF}(p(x)) : [0,1] \to \mathbb{R}_{\geq 0}, \quad \int_0^1 \text{PDF}(p(x)) \, dp(x) = 1 \quad (3.4)$$
General PDF axiom over the probability variable. *(p.26)*

$$\text{Beta}(p_x, \alpha, \beta) : [0,1] \to \mathbb{R}_{\geq 0} \quad (3.5)$$
$$\text{Beta}(p_x, \alpha, \beta) = \frac{\Gamma(\alpha + \beta)}{\Gamma(\alpha)\Gamma(\beta)} p_x^{\alpha - 1} (1 - p_x)^{\beta - 1} \quad (3.6)$$
Beta PDF. *(p.26)*

$$\begin{cases} \alpha = r_x + a_x W \\ \beta = s_x + (1 - a_x) W \end{cases} \quad (3.7)$$
Mapping evidence + base rate to Beta strength parameters. *(p.27)*

$$\text{Beta}^e(p_x, r_x, s_x, a_x) = \frac{\Gamma(r_x + s_x + W)}{\Gamma(r_x + a_x W)\Gamma(s_x + (1-a_x)W)} p_x^{r_x + a_x W - 1}(1-p_x)^{s_x + (1-a_x)W - 1} \quad (3.8)$$
Evidence-notation Beta PDF. *(p.27)* Restrictions: p_x ≠ 0 if (r_x + a_x W) < 1; p_x ≠ 1 if (s_x + (1−a_x)W) < 1.

$$E(x) = \frac{\alpha}{\alpha + \beta} = \frac{r_x + a_x W}{r_x + s_x + W} \quad (3.9)$$
Expected probability of Beta PDF (= projected probability under the bijection). *(p.27)*

$$\text{Var}(x) = \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)} = \frac{(r_x + a_x W)(s_x + (1-a_x)W)}{(r_x + s_x + W)^2 (r_x + s_x + W + 1)} = \frac{(b_x + a_x u_x)(d_x + (1-a_x)u_x)u_x}{W + u_x} = \frac{P(x)(1-P(x))u_x}{W + u_x} \quad (3.10)$$
Beta variance, multiple equivalent forms. The opinion form makes plain that **as u_x → 0, Var → 0**: dogmatic opinions are zero-variance Dirac-like. *(p.27)*

$$\begin{cases} b_x = r_x / (W + r_x + s_x) \\ d_x = s_x / (W + r_x + s_x) \\ u_x = W / (W + r_x + s_x) \end{cases} \Leftrightarrow \begin{cases} u_x \neq 0: \; r_x = b_x W / u_x, \; s_x = d_x W / u_x \\ u_x = 0: \; r_x = b_x \cdot \infty, \; s_x = d_x \cdot \infty, \; 1 = b_x + d_x \end{cases} \quad (3.11)$$
**The bijective binomial-opinion ↔ Beta PDF mapping.** Default W=2. *(p.28)*

$$\mathbf{P}_X(x) = \mathbf{b}_X(x) + \mathbf{a}_X(x) u_X, \quad \forall x \in \mathbb{X} \quad (3.12)$$
**Multinomial probability projection.** Direct generalisation of (3.2). *(p.30)*

$$\text{Var}_X(x) = \frac{\mathbf{P}_X(x)(1 - \mathbf{P}_X(x)) u_X}{W + u_X} \quad (3.13)$$
Multinomial variance. *(p.30)*

## Parameters / Constants / Defaults

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Non-informative prior weight | W | — | **2** | W > 0 | p.27, p.30 | Set so Beta(p_x, 1, 1) (uniform) is the prior under r=s=0, a=1/2. The single most important magic number in the framework. |
| Default singleton base rate | a_X(x) | — | 1/k | (0,1) | p.14 | Where k = \|𝕏\|. |
| Default composite base rate | a_X(x) | — | n/k | (0,1] | p.14 | n = number of singletons in the composite. Also called "relative atomicity". |
| Belief mass | b_x | — | — | [0,1] | p.13, p.24 | |
| Disbelief mass | d_x | — | — | [0,1] | p.24 | Binomial only |
| Uncertainty mass | u_x, u_X | — | — | [0,1] | p.13, p.24 | u=1 → vacuous; u=0 → dogmatic |
| Beta strength | α, β | — | (1,1) when r=s=0, a=1/2, W=2 | α>0, β>0 | p.26 | α = positive evidence + a_x W; β = negative evidence + (1−a_x) W |
| Evidence counts | r_x, s_x | counts | 0 prior | r_x ≥ 0, s_x ≥ 0 | p.27 | Positive (heads) and negative (tails) observations |
| Hyperdomain cardinality | κ | — | 2^k − 2 | — | p.10 | k = singletons, κ = hyperdomain values |

## Worked Examples and Numerics

**Example 3.1: Binomial opinion in Figure 3.1** *(p.25)*
ω_x = (b_x = 0.40, d_x = 0.20, u_x = 0.40, a_x = 0.90).
Projected probability: P(x) = 0.40 + 0.90 × 0.40 = **0.76**. Visualised on a barycentric triangle with the opinion point inside.

**Example 3.2: Beta PDF equivalent** *(p.28-29, Figure 3.2)*
Same opinion ω_x = (0.40, 0.20, 0.40, 0.90) maps to Beta^e(p_x, r_x=2.0, s_x=1.0, a_x=0.9), which under (3.7) yields α = 2.0 + 0.9·2 = 3.8 and β = 1.0 + 0.1·2 = 1.2. Equivalent PDF: **Beta(p_x, 3.8, 1.2)**. Expected probability E(x) = 3.8/5.0 = **0.76**. Matches projected probability ✓.

Verify mapping (3.11): with W=2 and u_x=0.40, r_x = 0.40·2/0.40 = 2.0, s_x = 0.20·2/0.40 = 1.0. ✓

**Vacuous binomial example** *(p.28)*
ω_x = (0, 0, 1, 1/2) ↔ Beta(p_x, 1, 1) — the **uniform PDF**. This is the canonical "I don't know" opinion. The unique fixed point of the W=2 default. propstore's `vacuous` provenance status corresponds to this.

**Trinomial opinion (Figure 3.3, p.31)**
Domain 𝕏 = {x_1, x_2, x_3}, k = 3.
ω_X with belief masses ***b***_X = {0.20, 0.20, 0.20}, uncertainty u_X = 0.40, base rate ***a***_X = {0.750, 0.125, 0.125}.
Projected probability via (3.12):
- P(x_1) = 0.20 + 0.750·0.40 = 0.50
- P(x_2) = 0.20 + 0.125·0.40 = 0.25
- P(x_3) = 0.20 + 0.125·0.40 = 0.25
**P_X = {0.50, 0.25, 0.25}.** ✓ (sums to 1).

**Indexing example (Table 2.2, p.11)**
Domain k=4, hyperdomain cardinality κ = 2^4 − 2 = 14. Cardinality classes: class 1 has 4 values (singletons x_1..x_4); class 2 has C(4,2)=6 values; class 3 has C(4,3)=4 values. Class-by-class indexing: indices 1-4 are singletons, 5-10 are pairs, 11-14 are triples. Example: x_12 = {x_1, x_2, x_4} (second relative-index value of cardinality class 3, absolute index 10+2 = 12). Total values 4+6+4 = 14 = κ. ✓

**Quaternary domain (Fig 2.2, p.9)** 𝕐 = {y_1, y_2, y_3, y_4}, hyperdomain cardinality 2^4 − 2 = 14.

**WEATHER ternary example** *(p.13)* 𝕏 = {rainy, sunny, overcast}. Composite e.g. {rainy, sunny} interpreted as "exactly one of rainy/sunny is TRUE — but not both." If real-world 'rainy AND sunny' is desired, must extend domain with a singleton {rainy&sunny}.

## Algorithms / Procedures

No numbered algorithms in this range. The key procedural content:

**Continuous indexing of hyperdomain** *(p.10-11)*
1. Index singletons of 𝕏 with [1, k].
2. Group remaining hyperdomain values into cardinality classes j = 2, 3, …, k−1.
3. For each cardinality class, list values in order of their lowest-indexed contained singleton, then second-lowest, etc.
4. Assign absolute indices [k+1, κ] sequentially across classes.
This produces a deterministic numbering of all 2^k − 2 hyperdomain values.

## Figures and Tables of Interest

- **Fig. 1.1 (p.4):** Diagram showing Subjective Logic = Probabilistic Logic + Uncertainty & Subjectivity.
- **Fig. 2.1 (p.8):** Binary domain diagram.
- **Fig. 2.2 (p.9):** Quaternary domain diagram.
- **Fig. 2.3 (p.9):** Hyperdomain of a ternary domain — three singletons and three pair-composites in a Venn-style diagram.
- **Fig. 2.4 (p.10):** Same hyperdomain with continuous indexing (x_1..x_3 for singletons, x_4, x_5, x_6 for composites).
- **Fig. 3.1 (p.25):** Barycentric triangle visualisation of binomial opinion. Three vertices: x (belief), x̄ (disbelief), uncertainty (top). Shows projector line from opinion point parallel to director (line from u-vertex to base-rate point on baseline).
- **Fig. 3.2 (p.29):** Beta(p_x, 3.8, 1.2) PDF plot, demonstrating equivalence with example opinion.
- **Fig. 3.3 (p.31):** Tetrahedron (3D simplex) for trinomial opinion, with vertices x_1, x_2, x_3 (belief faces) and uncertainty top.
- **Table 1.1 (p.2):** Binary↔Probabilistic logic operator correspondence (9 rows).
- **Table 2.1 (p.11):** Number of values per cardinality class for k=4: {1:4, 2:6, 3:4}.
- **Table 2.2 (p.11):** Index and cardinality class of all 14 values of 𝓡(𝕏) for k=4.
- **Table 3.1 (p.19):** Belief and trust relationship notation. Belief = [A,X] ; Trust = [A,E].
- **Table 3.2 (p.21):** **The 12-cell opinion class taxonomy.** Rows: confidence levels (Vacuous u=1, Uncertain 0<u<1, Dogmatic u=0, Absolute b(x)=1). Columns: Binomial / Multinomial / Hyper. Entries give probabilistic equivalents (Uniform Beta, Beta PDF, Dirichlet PDF, Dirichlet HPDF, Probability on x, Boolean TRUE/FALSE, etc.).

## Quotes Worth Preserving

> "We can assume that an objective reality exists but our perception of it will always be subjective. This idea is articulated by the concept of *das Ding an sich* (the thing-in-itself) in the philosophy of Kant." *(p.1)*

> "An analyst might for example want to give the input argument 'I don't know', which expresses total ignorance and uncertainty about some statement. However, an argument like that can not be expressed if the formalism only allows input arguments in the form of Booleans or probabilities. The probability p(x) = 0.5 would not be a satisfactory argument because it would mean that x and x̄ are exactly equally likely, which in fact is quite informative, and very different from ignorance." *(p.4)*  
> **— THIS is the foundational quote for propstore's `vacuous` vs `defaulted 0.5` distinction.**

> "An analyst who has little or no evidence for providing input probabilities could be tempted or even encouraged to set probabilities with little or no confidence. This practice would generally lead to unreliable conclusions, often described as the problem of 'garbage in, garbage out'. What is needed is a way to express lack of confidence in probabilities. In subjective logic, the lack of confidence in probabilities is expressed as *uncertainty mass*." *(p.4)*

> "Uncertainty mass in the Dirichlet model reflects vacuity of evidence. Interpreting uncertainty mass as vacuity of evidence reflects the property that 'the fewer observations the more uncertainty mass'." *(p.5)*

> "An essential characteristic of subjective logic is thus to include base rates, which also makes it possible to define a bijective mapping between subjective opinions and Dirichlet PDFs." *(p.5)*

> "Initial vacuity of evidence exist *a priori*, as represented by uncertainty mass. Belief mass is then formed *a posteriori* as a function of collected evidence in accordance with the Beta and Dirichlet models." *(p.14)*

> "Belief mass assigned to a singleton value x_i ∈ 𝕏 represents *sharp belief* because it sharply supports the truth of that specific value only. Belief mass assigned to a composite value x_j ∈ 𝓒(𝕏) represents *vague belief* because it supports the truth of a set of singleton values x ∈ {x_j} but not which singleton value in particular." *(p.14)*

> "Base rates are non-informative prior probabilities … 'non-informative' is used to express that no specific evidence is available for determining the probability of a specific event other than the general background information for that class of events." *(p.17)*

> "From a philosophical viewpoint, no one can ever be totally certain about anything in this world. So when the formalism allows explicit expression of uncertainty, as opinions do, it is extreme, and even unrealistic, to express a dogmatic opinion. The rationale for this interpretation is that a dogmatic opinion has an equivalent Dirichlet probability density function in the form of a Dirac delta function which is infinitely high and infinitesimally thin. It would require an infinite amount of evidence to produce a Dirichlet PDF equal to a Dirac delta function." *(p.20)*

> "Analysts are never forced to invent belief where there is none. In case they are ignorant, they can simply produce a vacuous or highly uncertain opinion. The same can not be said when using probabilities, where analysts sometimes have to 'pull probabilities out of thin air'." *(p.21)* **— Direct support for honest-ignorance principle.**

> Foreword (Kaplan, p.viii): "I am personally intrigued by subjective logic because it provides a principled way to connect beliefs to Dirichlet distributions. Furthermore, subjective logic offers computationally efficient operators that approximate second-order Bayesian reasoning."

## Implementation Notes

1. **W = 2 is the default prior weight** (p.27, p.30). Hardcode unless the user explicitly overrides. Changing W changes the bijection (3.11) and so changes every numerical operator output.
2. **Opinion 4-tuple invariant**: For binomials, `b + d + u = 1` exactly. For multinomial, `u + Σb(x) = 1`. Implementations should validate on construction; floating-point drift requires tolerance (no specific tolerance given by the book, but Var(x) at u=0 is exactly 0 so ε around 1e-9 is reasonable).
3. **Vacuous opinion: ω_x = (0, 0, 1, a_x)**. The base rate a_x is **still required** even when u=1 — this is what distinguishes a vacuous opinion from "no opinion at all" and what enables probability projection (P = a_x when u=1). propstore's `vacuous` provenance value should still carry a base rate. Default: 1/k for singleton in domain of size k.
4. **Dogmatic opinion: u_x = 0**. Maps to a Dirac delta Beta PDF — finite-evidence interpretation is **infinite evidence**. Mapping (3.11) becomes r = b·∞, s = d·∞, with 1 = b + d. Numerical implementations need a special branch for u_x = 0; do not use (3.11) directly. Projected probability simplifies to P(x) = b_x.
5. **Absolute opinion: b_X(x) = 1** for some single x. This subsumes Boolean TRUE/FALSE (b_x = 1 → TRUE; d_x = 1 ≡ b_x̄ = 1 → FALSE). All other belief masses 0, u_X = 0.
6. **Relative base rate (2.10) requires nonzero denominators**; treat a(x|x_i) = 0 as the convention when a(x_i) = 0, OR enforce a(x_i) > 0 for every singleton.
7. **Composite base rates (2.9) are super-additive over 𝓡(𝕏)** — they are NOT a probability distribution. Do not normalise. Use only as input to (2.10) for relative base rates and to (2.13) for hyper-probability → probability projection.
8. **Hyperdomain cardinality grows as 2^k − 2** — for k=10, κ = 1022. For k=20, κ ≈ 10^6. Hyper-opinions are exponential in domain size; use multinomial (k-cardinality, not κ) when composite belief is not needed.
9. **Beta PDF restrictions**: at α<1 the density blows up at p_x = 0; at β<1 it blows up at p_x = 1. Sampling and integration code must handle these endpoints carefully.
10. **Continuous hyperdomain indexing (p.10-11)** is the canonical way to enumerate composite values. Use a stable algorithm (cardinality-class-then-lowest-singleton-first); document it because Tables/Figures elsewhere in the book reference these indices.
11. **Aleatory vs epistemic distinction is syntactically explicit in subjective logic.** Epistemic opinions must be uncertainty-maximised (per §3.5.6, deferred to next chunk). Aleatory opinions can have any u_X. propstore needs a flag or kind for this if the framework wants epistemic vs aleatory provenance.
12. **Variance formula (3.10)** in opinion form is monotone in u_x: at u_x=0, Var=0 (Dirac); larger u → larger variance. This gives a principled way to derive a confidence interval from an opinion without re-deriving the Beta directly.
13. **Probability projection (3.2) and (3.12)** are the canonical conversion from opinion → probability for downstream (non-subjective) consumers. The contribution of base rate to projection scales linearly with u: P = b + a·u. propstore's render layer should expose this as the standard scalar export.

## Criticisms of Prior Work

1. **Bayesian probability** treats base rate and posterior probability with the same symbol p, conflating them. Subjective logic distinguishes them: a for base rate, p (or P) for projected probability. *(p.5)*
2. **Probability calculus and binary logic both fail** to express "I don't know" — p=0.5 is informative ("equally likely"), not ignorant. *(p.4)* This drives the need for explicit uncertainty mass.
3. **Truth tables in binary logic are redundant axioms**: when binary logic is a special case of probabilistic logic with p ∈ {0,1}, AND/OR/XOR/EQU/MP/MT all derive from the algebraic operators in Table 1.1; truth tables are superfluous. Maintaining both is "problematic because of the possibility of inconsistency between definitions." *(p.3)*
4. **Belief functions (Dempster 1960, Shafer 1976) ignore base rates.** Dempster-Shafer theory abandons probability additivity (allowing belief mass on the powerset) but does not include base rates. Subjective logic restores base rates while keeping the powerset structure. *(p.5)*
5. **Bayesian theory cannot represent epistemic uncertainty separately from aleatory.** They are formally and syntactically indistinguishable in pure Bayes, with a "mostly philosophical" difference. Subjective logic makes the difference syntactic via uncertainty maximisation. *(p.23)*
6. **Kleene three-valued logic [25]** allows TRUE/FALSE/UNKNOWN but does not include base rates, so it cannot derive a probability projection from UNKNOWN. Subjective logic's vacuous opinion does derive a projection (P = a) using the base rate. *(p.25)*
7. **Anecdotal vs statistical justification**: Foreword (Kaplan, p.viii) notes that belief theories are "typically justified by anecdotal examples, which is one reason why ideas within the theories are disputed" — suggests subjective logic needs more statistical verification.

## Open Threads / Forward References

Forward references explicitly mentioned in this chunk:
- §3.5.6 — Uncertainty-maximisation (referenced p.23, p.24).
- §3.5.5 — Detailed mapping description for multinomial ↔ Dirichlet (referenced p.28, p.30).
- §3.6.3 — Hyperprobability and Dirichlet model on hyperdomains (referenced p.18).
- Chapter 4 — Belief mass distribution detail (referenced p.14).
- Chapter 14 — Trust opinions, [A,E] semantics (referenced p.20).
- §14.1, Table 14.1 — Referral trust relationship (referenced p.19).
- §16.3.5 — Bayesian reputation systems base rates (referenced p.15).
- §17.5 — Subjective Bayesian networks (referenced p.23).
- §9.2.1, §9.2.3 — Bayes' theorem and law of total probability (referenced p.3).
- §9.1, §9.7 — MP, MT, material implication interpretation (referenced p.3).
- §5.1.4 — Comparison with Kleene three-valued logic (referenced p.25).
- Reference [33] = "hyper-Dirichlet model" (p.10) — Hankin's hyper-Dirichlet PDF, used as basis for hyperdomain belief models.
- Reference [78] — Probabilistic logic survey (p.1).
- References [31, 95] — Second-order probability literature (p.5).
- Reference [76] — Barycentric coordinate system reference (p.25).

Backward references — none (this is the start of the book).

Internal threads/loose ends to stitch:
- The bijection (3.11) only handles the binomial case; the multinomial generalisation is deferred to §3.5.5.
- The "uncertainty-maximised" concept appears (p.22-23) but its formal mechanics are in §3.5.6.
- The relationship between hyper-opinions and the hyper-Dirichlet PDF [33] is announced (p.10) but the formal model is in §3.6 (next chunk).
- Operator algebra introduced in Table 1.1 *(p.2)* sets up later chapters 5–13 but no subjective-logic operator is defined in this range.
- Ellsberg paradox (§4.5), entropy (§4.7), and conflict (§4.8) — all in next chunk.
