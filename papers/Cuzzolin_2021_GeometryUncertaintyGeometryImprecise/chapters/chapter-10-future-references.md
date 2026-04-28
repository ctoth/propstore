# Chunk #10 — Chapter 17 (An agenda for the future) + complete References

**Book pages:** 655 through end of book (last book p. = 850, no indices)
**PDF idx:** 680-863

## Pages read

Read every page-image in range 678-741 (book pp.665-728, end of Ch.17). Bibliography pp.742-863 (book pp.729-850) sampled at: 742, 743, 755, 765, 766, 768, 770, 783, 790, 808, 820, 822, 823, 832, 836, 839, 840, 846, 847, 848, 855, 862, 863. No pages failed.

## Sections covered

- **17.1 A statistical random set theory** — book pp.665-691
  - 17.1.1 Lower and upper likelihoods (binary trial decompositions; Theorem 110, 109; Lemma 22; Cor 25, 26)
  - 17.1.2 Generalised logistic regression — pp.668-671
  - 17.1.3 Total probability theorem for random sets — pp.671-684 (Theorem 111, Lemmas 23-24, Corollary 27, Proposition 67, Definition 138, Proposition 68, Examples 53-54)
  - 17.1.4 Limit theorems for random sets — pp.684-688 (Definition 139, Propositions 69-73)
  - 17.1.5 Frequentist inference with random sets — pp.689-690
  - 17.1.6 Random-set random variables — pp.690-692 (Defs 141-142, Theorem 112)
- **17.2 Developing the geometric approach** — pp.692-710
  - 17.2.1 Geometry of general combination (Definition 143, Theorem 113, Conjecture 2, Yager/Dubois, disjunctive) — pp.693-700
  - 17.2.2 Geometry of general conditioning — p.700
  - 17.2.3 A true geometry of uncertainty (Prop 74, Thm 114, ternary frame, Banach Prop 75, Milman Prop 76) — pp.701-705
  - 17.2.4 Fancier geometries (exterior algebras, capacities as isoperimeters) — pp.705-707
  - 17.2.5 Integral and stochastic geometry (Buffon, Firey, Sylvester, Defs 144-145) — pp.707-710
- **17.3 High-impact developments** — pp.710-728
  - 17.3.1 Climate change (Rougier framework, Axioms 3-6) — pp.710-714
  - 17.3.2 Machine learning (Defs 146-147, Theorem 115 KKT sufficiency, full KKT system) — pp.714-721
  - 17.3.3 Generalising statistical learning theory (PAC, VC, Defs 148-149, Theorems 116-117 credal generalisation) — pp.721-728

## Chapter overview

Chapter 17 is Cuzzolin's research agenda — explicitly forward-looking, structured as a programme of open problems organised under three pillars: (1) developing a full statistical theory of random sets paralleling classical statistics (likelihood, regression, total probability, limit theorems, hypothesis testing, RNDs); (2) extending the geometric approach beyond Dempster combination to all combination rules, all conditioning operators, all uncertainty measures (capacities, gambles, MV-algebras), with potential reformulations via exterior algebras and convex-body projections; (3) high-impact applications to climate change modelling (Rougier-style Bayesian framework re-cast with belief functions), machine learning (generalised maximum-entropy classifiers using 2-monotonicity bracket constraints), and statistical learning theory (credal-realisability PAC bounds for finite hypothesis classes).

The chapter explicitly numbers research questions Q.14 through Q.38 (25 numbered questions) and frames each subsection as "what's missing and how would we attack it." Cuzzolin's stated goal is to lay foundations for an "uncertainty theory that subsumes probability" and to provide robust theoretical foundations for deep learning by replacing single-model selection with credal-set selection.

The bibliography contains **2137 numbered references** (last entry [2137] Zribi-Benjelloun) spanning book pp.729-850 / PDF pp.742-863. There is **no author index, no subject index** — the book ends at the last reference.

## Definitions

### Definition 137 (KKT necessary conditions) *(p.670)*
For nonlinear optimisation problem $\arg\max_x f(x)$ subject to $g_i(x) \leq 0$, $h_j(x) = 0$, at local optimum $x^*$ there exist KKT multipliers $\mu_i, \lambda_j$ satisfying: stationarity $\nabla f(x^*) = \sum \mu_i \nabla g_i(x^*) + \sum \lambda_j \nabla h_j(x^*)$, primal feasibility, dual feasibility $\mu_i \geq 0$, complementary slackness $\mu_i g_i(x^*) = 0$.

### Definition 138 (Class T column substitutions) *(p.682)*
For a candidate minimal-solution column $e$ of the total-belief solution system, the formal-sum transformation $e \mapsto e' = -e + \sum_{i \in C} e_i - \sum_{j \in S} e_j$ where $C$ is a covering set of "companions" of $e$ and $S$ ($|S|=|C|-2$) is a set of "selection" columns chosen to yield an admissible focal element satisfying Proposition 67's structure.

### Definition 139 (Belief measure on Polish space) *(p.685)*
$Bel : \mathcal{B}(\Theta) \to [0,1]$ is a belief measure if $Bel(\emptyset)=0$, $Bel(\Theta)=1$, monotone, continuous from above on decreasing sequences, $Bel(G) = \sup\{Bel(K) : K \subset G, K \in \mathcal{K}(\Theta)\}$ for open $G$, and totally monotone (∞-monotone) by inclusion-exclusion inequality.

### Definition 140 (Weak/strong LLN) *(p.688)*
Weak: $\lim_{n\to\infty} P(|\overline{X}_n - \mu| > \varepsilon) = 0$. Strong: $P(\lim_{n\to\infty} \overline{X}_n = \mu) = 1$.

### Definition 141 (Absolute continuity of capacities) *(p.691)*
Capacity $\nu$ absolutely continuous w.r.t. $\mu$ if for every $A \in \mathcal{F}$, $\nu(A) = 0$ whenever $\mu(A) = 0$.

### Definition 142 (Strong decomposition) *(p.691)*
Pair $(\mu, \nu)$ has strong decomposition if $\forall \alpha \geq 0$ there exists measurable $A_\alpha \in \mathcal{F}$ such that $\alpha(\nu(A) - \nu(B)) \leq \mu(A) - \mu(B)$ for $B \subset A \subset A_\alpha$, and $\alpha(\nu(A) - \nu(A \cap A_\alpha)) \geq \mu(A) - \mu(A \cap A_\alpha)$ for all $A$.

### Definition 143 (Conditional subspace under arbitrary rule ⊙) *(p.693)*
Given $Bel \in \mathcal{B}$ and a combination rule $\odot$, the conditional subspace $\langle Bel \rangle_{\odot} \doteq \{Bel \odot Bel' : Bel' \in \mathcal{B} \text{ s.t. } Bel \odot Bel' \text{ exists}\}$.

### Definition 144 (Point process) *(p.709)*
Measurable map $\eta : (\Omega, \mathcal{F}, P) \to$ locally finite subsets of Polish space $\mathbb{X}$. Intensity measure $\mu(A) = E[\eta(A)]$.

### Definition 145 (Random element) *(p.709)*
Function $X : \Omega \to E$ that is $(\mathcal{F}, \mathcal{E})$-measurable, where $(E, \mathcal{E})$ is a measurable space — generalisation of random variable.

### Definition 146 (Maximum-entropy classifier) *(p.716)*
$p^*(C_k|x) = \arg\max_{p(C_k|x)} H_s(P)$ subject to $\tilde{E}_p[\phi_m] = \hat{E}[\phi_m]$ ∀m. Solution: log-linear model $p^*(C_k|x) = (1/Z_\lambda(x)) \exp(\sum_m \lambda_m \phi_m(x, C_k))$.

### Definition 147 (Maximum random-set entropy classifier) *(p.717)*
$Bel^*(x, C_k) = \arg\max_{Bel(x,C_k)} H(Bel)$ subject to $\sum_{x,k} Bel(x,C_k)\phi_m(x,C_k) \leq \hat{E}[\phi_m] \leq \sum_{x,k} Pl(x,C_k)\phi_m(x,C_k)$ ∀m.

### Definition 148 (PAC algorithm) *(p.722)*
Learning algorithm is probably approximately correct if it finds with probability ≥ $1-\delta$ a hypothesis $\hat{h} \in \mathcal{H}$ "approximately correct," i.e., $P[L(\hat{h}) - L(h^*) > \varepsilon] \leq \delta$ on the difference between ERM loss and minimum theoretical loss for the class.

### Definition 149 (VC dimension) *(p.723)*
The VC dimension of model space $\mathcal{H}$ is the maximum number of points that can be shattered by some $h \in \mathcal{H}$.

## Theorems, propositions, lemmas, corollaries

### Theorem 109 (Disjunctive factorisation, binary frames) *(p.666)*
$Bel_{\mathbb{X}_1 \times \cdots \times \mathbb{X}_n}(\{(x_1,\ldots,x_n)\}^c | \theta) = \prod_{i=1}^n Bel_{\mathbb{X}_i}(\{x_i\}^c | \theta)$.

### Theorem 110 (Cartesian focal-element factorisation, conjunctive) *(p.667)*
For $Bel_{\mathbb{X}_1} \oplus \cdots \oplus Bel_{\mathbb{X}_n}$ on finite spaces $\mathbb{X}_i$, focal elements are Cartesian products $A_1 \times \cdots \times A_n$ with $m(A_1 \times \cdots \times A_n) = \prod m_{\mathbb{X}_i}(A_i)$.

### Theorem 111 (Total belief theorem) *(p.672)*
Given $\rho : 2^\Omega \to 2^\Theta$ refining, $Bel_0$ on $\Omega$, conditional $Bel_i$ on partition classes $\Pi_i = \rho(\{\omega_i\})$. There exists $Bel : 2^\Theta \to [0,1]$ such that (P1) $Bel_0 = Bel \upharpoonright_\Omega$ (marginal) and (P2) $Bel \oplus Bel_{\Pi_i} = Bel_i$ ∀i.

### Theorem 112 (Graf RND for capacities) *(p.692)*
$\nu$ is indefinite integral of $\mu$ iff $(\mu, \nu)$ has strong decomposition and $\nu \ll \mu$.

### Theorem 113 (Disjunctive line geometry on binary frame) *(p.697)*
Lines joining $Bel'$ and $Bel \mathbin{\bigcirc\!\!\!\cup} Bel'$ for any $Bel' \in \mathcal{B}$ all pass through the point $\overline{m(x)} = m'(x)\frac{m(x)-m(y)}{1-m(y)}$, $\overline{m(y)} = 0$.

### Theorem 114 (Convexity of 2-monotone capacity space) *(p.701)*
$\mathcal{M}^2_\Theta$ (space of 2-monotone capacities on $\Theta$) is convex.

### Theorem 115 (KKT sufficiency for generalised max-entropy) *(p.719)*
If $H_t, H_n, H_d, H_{Bel}$, or $H_{Pl}$ is the entropy, the generalised max-entropy classification problem (Definition 147) has concave objective and convex constraints; KKT conditions are sufficient for optimality.

### Theorem 116 (Bound for realisable finite hypothesis classes) *(p.725)*
$L(\hat{h}) \leq (\log|\mathcal{H}| + \log(1/\delta))/n$, hence $n \geq (\log|\mathcal{H}|+\log(1/\delta))/\varepsilon \Rightarrow L(\hat{h}) \leq \varepsilon$, with proof via union bound on bad hypotheses.

### Theorem 117 (Credal generalisation of Theorem 116) *(p.727)*
Let $\mathcal{H}$ finite, $\mathcal{P}$ a credal set, training $\mathcal{D}$ drawn from some $\hat{p} \in \mathcal{P}$, $\hat{h}$ ERM. Under credal realisability $\exists h^* \in \mathcal{H}, p^* \in \mathcal{P} : E_{p^*}[l] = L_{p^*}(h^*) = 0$. Then with prob $\geq 1-\delta$, $P[\max_{p \in \mathcal{P}} L_p(\hat{h}) > \varepsilon] \leq \varepsilon(\mathcal{H}, \mathcal{P}, \delta)$.

### Lemma 22 (Disjunctive focal elements, binary case) *(p.665)*
$Bel_{\mathbb{X}_1} \mathbin{\bigcirc\!\!\!\cup} \cdots \mathbin{\bigcirc\!\!\!\cup} Bel_{\mathbb{X}_n}$, $\mathbb{X}_i = \{T,F\}$, has $2^n+1$ focal elements: the complements of singletons $\{x_1\}^c \times \cdots \times \{x_n\}^c$, plus $\mathbb{X}_1 \times \cdots \times \mathbb{X}_n$ itself.

### Lemmas 23-24 (Total belief existence via embeddings) *(pp.673-674)*
Lemma 23: $\overrightarrow{Bel}$ over $\Theta$ (Dempster combination of conditional embeddings) has focal elements that are unions of one focal element from each $Bel_i$, and its marginal on $\Omega$ is vacuous. Lemma 24: $Bel = Bel_0^{\uparrow\Theta} \oplus \overrightarrow{Bel}$ satisfies (P1) and (P2).

### Corollary 25 (Singleton decomposition under ⊕ or ∩) *(p.667)*
$Bel_{\mathbb{X}_1 \times \cdots \times \mathbb{X}_n}(\{(x_1,\ldots,x_n)\} | \theta) = \prod Bel_{\mathbb{X}_i}(\{x_i\} | \theta)$.

### Corollary 26 (Lower/upper Bernoulli likelihoods) *(p.668)*
$\underline{L}(\mathbf{x}) = p^k q^{n-k}$, $\overline{L}(\mathbf{x}) = (1-q)^k(1-p)^{n-k}$ where $p=m(\{T\})$, $q=m(\{F\})$, $p+q \leq 1$.

### Corollary 27 (Bayesian prior gives unique total belief) *(p.679)*
If $Bel_0$ is Bayesian, the total belief from (17.20) is the unique solution; $m(e) = m_i(e)m_0(\omega_i)$ if $e \in \mathcal{E}_i$ for some $i$, 0 otherwise.

### Corollary 28 (Sylvester expected intersections) *(p.708)*
For piecewise $C^1$ curve $C$ in compact $\Omega$, expected intersections = $2L(C)/L(\partial \Omega)$.

### Proposition 67 (Focal-element structure of total belief) *(p.681)*
Each focal element $e$ of any total belief function meeting Theorem 111's requirements is the union of exactly one focal element from each $Bel_i$ whose domain $\Pi_i \subseteq \rho(E)$, where $E$ is the smallest focal element of $Bel_0$ such that $e \subset \rho(E)$.

### Proposition 68 (Class T reduces most-negative component) *(p.683)*
T-substitutions reduce |most negative solution component|.

### Proposition 69 (Choquet representation) *(p.685)*
$Bel : \mathcal{B}(\Theta) \to [0,1]$ is a belief measure iff there exists probability $P_{Bel}$ on $(\mathcal{K}(\Theta), \mathcal{B}(\mathcal{K}(\Theta)))$ such that $Bel(A) = P_{Bel}(\{K \in \mathcal{K}(\Theta) : K \subset A\})$.

### Proposition 70 (Epstein-Seo CLT for Bernoulli) *(p.686)*
For empirical frequency $\Phi_n(\theta^\infty)$ of outcome T over n Bernoulli trials, $\lim_n Bel^\infty(\{\sqrt{n}(\Phi_n - Pl(T))/\sqrt{Bel(F)(1-Bel(F))} \leq \alpha\}) = \mathcal{N}(\alpha)$ and the dual inequality.

### Proposition 71 (Epstein-Seo expectation bound) *(p.686)*
For bounded quasi-concave upper-semicontinuous $G$, $\int G(\Phi_n) dBel^\infty = E[G(X'_{1n}, X'_{2n})] + O(1/\sqrt{n})$ where the pair is jointly normal with mean $(Bel(T), Pl(T))$.

### Proposition 72 (Shi 2015 generalisation to bounded RVs) *(p.687)*
For i.i.d. $Y_i$ on $(\Theta, \mathcal{B}(\Theta))$ bounded by $M$, $\lim Bel^\infty(\sum X_i/\sqrt{n\underline{\sigma}} \geq \alpha) = 1 - \mathcal{N}(\alpha)$ etc.

### Proposition 73 (Teran 2014 LLN for completely monotone capacities) *(p.688)*
For $\nu$ completely monotone, integrable $X$, $\{X_n\}$ pairwise pre-independent identically distributed, $\nu(E_\nu[X] - \varepsilon < \overline{X}_n < E_{\overline{\nu}}[X] + \varepsilon) \to 1$.

### Proposition 74 (2-monotone Möbius criterion) *(p.701)*
Capacity $\mu$ on $\Theta$ is 2-monotone iff $\sum_{\{x,y\} \subseteq E \subseteq A} m(E) \geq 0$ ∀ $x,y \in \Theta$, $\forall A \ni x,y$.

### Proposition 75 (Banach symmetric convex body) *(p.704)*
Unit ball $B_X$ of Banach space $X = (\mathbb{R}^n, \|\cdot\|)$ is symmetric convex; conversely any symmetric convex $K \subset \mathbb{R}^n$ is the unit ball of $\|x\|_K = \inf\{t > 0 : x/t \in K\}$.

### Proposition 76 (Concentration of measure on random projections) *(p.705)*
For symmetric convex $K \subset \mathbb{R}^n$, with prob $\geq 1 - e^{-k}$, $\text{diam}(P|K) \leq C(M^*(K) + \sqrt{k/n}\,\text{diam}(K))$.

### Proposition 77 (Buffon needle) *(p.707)*
For parallel lines distance $d$ and needle length $l < d$: $P = 2l/(\pi d)$.

### Proposition 78 (Firey colliding dice) *(p.707)*
For two disjoint unit cubes in $\mathbb{R}^3$ in random collision, $P(\text{edge-edge}) \approx 0.54 > P(\text{corner-face}) \approx 0.46$.

### Proposition 79 (Poincaré formula for lines) *(p.708)*
For piecewise $C^1$ curve $C$, $2L(C) = \int_{L: L \cap C \neq \emptyset} n(C \cap L) \, dK(L)$.

### Proposition 80 (Sylvester) *(p.708)*
For bounded convex $\Theta \subset \Omega$, probability random line meeting $\Omega$ also meets $\Theta$ is $L(\partial \Theta)/L(\partial \Omega)$.

### Conjecture 1 (mentioned p.668) — Bel decomposition is valid under conjunctive independence
### Conjecture 2 (Yager's rule constant-mass loci converge to focus on binary) *(p.694)*

## Equations

### Sample of key equations

$$Bel_{\mathbb{X}_1 \times \cdots \times \mathbb{X}_n}(\{(x_1,\ldots,x_n)\} | \theta) = \prod_{i=1}^n Bel_{\mathbb{X}_i}(\{x_i\}|\theta)$$
**(Eq. 17.11, p.667)** Conjunctive singleton decomposition.

$$\underline{L}(\mathbf{x}) = \prod_{i=1}^n Bel_\mathbb{X}(\{x_i\}) = p^k q^{n-k}, \quad \overline{L}(\mathbf{x}) = \prod_{i=1}^n Pl_\mathbb{X}(\{x_i\}) = (1-q)^k(1-p)^{n-k}$$
**(Eq. 17.12, p.668)** Bernoulli lower/upper likelihood. Variables: $p = m(\{T\})$, $q = m(\{F\})$, $p+q \leq 1$, $k$ = successes, $n$ = trials.

$$\underline{L}(\beta|Y) = \prod_{i=1}^n p_i^{Y_i} q_i^{1-Y_i}, \quad \overline{L}(\beta|Y) = \prod_{i=1}^n (1-q_i)^{Y_i}(1-p_i)^{1-Y_i}$$
**(implicit p.669)** Generalised logistic likelihoods.

$$p_i = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_i)}}, \quad q_i = \beta_2 \frac{e^{-(\beta_0+\beta_1 x_i)}}{1 + e^{-(\beta_0+\beta_1 x_i)}}$$
**(Eq. 17.13, 17.14, p.669)** Generalised logit links; $\beta_2 \leq 1$ ensures $p_i + q_i \leq 1$.

$$\arg \max_\beta \underline{L} \mapsto \underline{\beta}_0, \underline{\beta}_1, \underline{\beta}_2, \quad \arg \max_\beta \overline{L} \mapsto \overline{\beta}_0, \overline{\beta}_1, \overline{\beta}_2$$
**(Eq. 17.15, p.669)** Lower/upper parameter estimates yielding interval BFs $Bel_\mathbb{X}(.|\underline{\beta}, x)$ and $Bel_\mathbb{X}(.|\overline{\beta}, x)$.

$$Bel = Bel_0^{\uparrow\Theta} \oplus \overrightarrow{Bel}$$
**(Eq. 17.18, p.673)** Construction of total belief function.

$$Bel(\bigcup_{i=1}^n B_i) \geq \sum_{\emptyset \neq I \subseteq \{1,\ldots,n\}} (-1)^{|I|+1} Bel(\bigcap_{i \in I} B_i)$$
**(p.685)** ∞-monotonicity.

$$Bel^\infty(A) \doteq P^\infty_{Bel}(\{K = K_1 \times K_2 \times \cdots \in (\mathcal{K}(\Theta))^\infty : K \subset A\})$$
**(Eq. 17.31, p.685)** i.i.d. product belief measure.

$$\lim_n Bel^\infty\left(\frac{\Phi_n - Pl(T)}{\sqrt{Bel(F)(1-Bel(F))/n}} \leq \alpha\right) = \mathcal{N}(\alpha)$$
**(Prop 70, p.686)** Bernoulli random-set CLT.

$$\bel = \sum_{A=\{x_1,\ldots,x_k\} \subset \Theta} m(A) \, x_1 \wedge x_2 \wedge \cdots \wedge x_k$$
**(p.706)** Belief function as exterior-algebra sum of decomposable k-vectors.

$$P = 2l/(\pi d), \quad 2L(C) = \int n(C \cap L) \, dK(L)$$
**(Buffon, Poincaré, pp.707-708)**

$$x \to y = g(x)$$
**(Eq. 17.48, p.712)** Climate model maps parameters $x$ to climate vector $y$.

$$p(y_f | z = \tilde{z}) = \int p(y_f | x^*, z = \tilde{z}) p(x^*|z = \tilde{z}) dx^*$$
**(Eq. 17.50, p.713)** Bayesian climate prediction integrating over best-input parameters.

$$p^*(C_k|x) = \frac{1}{Z_\lambda(x)} e^{\sum_m \lambda_m \phi_m(x, C_k)}$$
**(Eq. 17.57, p.716)** Log-linear classifier — solution of standard max-entropy problem.

$$\sum_{(x,C_k)} Bel(x, C_k) \phi_m(x, C_k) \leq \hat{E}[\phi_m] \leq \sum_{(x, C_k)} Pl(x, C_k) \phi_m(x, C_k)$$
**(Eq. 17.58, p.716)** 2-monotonicity bracket constraint for generalised classifier.

$$L(h) \doteq E_{(x,y) \sim p^*}[l((x,y), h)], \quad \hat{L}(h) = \frac{1}{n}\sum_i l((x_i, y_i), h)$$
**(Eqs. 17.65, 17.67, p.721)** Expected risk and empirical risk.

$$L(\hat{h}) \leq \frac{\log|\mathcal{H}| + \log(1/\delta)}{n}$$
**(Eq. 17.70, p.726)** Realisable PAC bound.

$$\exists h^* \in \mathcal{H}, p^* \in \mathcal{P} : E_{p^*}[l] = L_{p^*}(h^*) = 0$$
**(Eq. 17.74, p.727)** Credal realisability.

$$\forall p \in \mathcal{P}, \exists h_p^* \in \mathcal{H} : E_p[l(h_p^*)] = L_p(h_p^*) = 0$$
**(Eq. 17.76, p.728)** Uniform credal realisability — stronger.

## Geometric structures

- **Conditional subspace $\langle Bel \rangle_\odot$**: convex closure of $\{Bel \odot Bel' : Bel'\}$. For Yager rule on binary frame, vertices are $Bel$, $Bel \mathbin{\bigcirc\!\!\!\!Y} Bel_x = [m(x)+m(\Theta), 0, m(y)]'$, $Bel \mathbin{\bigcirc\!\!\!\!Y} Bel_y = [0, m(y)+m(\Theta), m(x)]'$, $Bel \mathbin{\bigcirc\!\!\!\!Y} Bel_\Theta = Bel$. (p.694)
- **Disjunctive conditional subspace on binary**: triangle with vertices $Bel$, $Bel \mathbin{\bigcirc\!\!\!\cup} Bel_x = [m(x), 0, 1-m(x)]'$, $Bel \mathbin{\bigcirc\!\!\!\cup} Bel_y = [0, m(y), 1-m(y)]'$. (p.696)
- **Yager constant-mass loci** (Fig.17.8): parallel lines (do not converge to focus, unlike Dempster).
- **Disjunctive geometric construction** (Fig.17.10): $45°$ projection trick to find $Bel \mathbin{\bigcirc\!\!\!\cup} Bel'$ via orthogonal projections and a reflected line through point 2.
- **2-monotone polytope on ternary frame**: convex closure of $[1,0,0]$, $[0,1,0]$, $[0,0,1]$, $[1,1,-1]$ in $\mathbb{R}^3$ (Fig.17.12 — diamond/pyramid). Has 4 vertices including one with negative mass component for $\Theta$. Strictly contains the belief space simplex.
- **Belief space via exterior algebra**: each focal element of cardinality $k$ encoded as decomposable $k$-vector $x_1 \wedge \cdots \wedge x_k$; belief functions as linear combinations of such $k$-vectors across cardinalities.
- **Capacities as isoperimeters**: $\nu(S)$ = (hyper)volume of orthogonal projection $K|S$ of convex body $K$ onto coordinate subspace $S$; $2^n$ projections per body in $\mathbb{R}^n$.
- **Solution graph for total belief problem**: nodes = candidate solution systems, edges = T-substitutions; group $G = S_{n_1} \times \cdots \times S_{n_N}$ acts via permutations of focal elements within each conditional $Bel_i$. (p.683-684)

## Algorithms / pseudo-code

### Random-set hypothesis testing (p.690)
1. State null $H_0$ and alternative.
2. State assumptions about random-set (mass-assignment) form.
3. State test statistic $T$ over set-valued samples.
4. Derive mass assignment of $T$ under $H_0$.
5. Set significance level $\alpha$.
6. Compute observed value $t_{obs}$ (set-valued).
7. Calculate **conditional belief value** under $H_0$ of sampling $T$ at least as extreme.
8. Reject if conditional belief value < $\alpha$.

### Generalised logistic regression KKT (p.671)
Objective: maximise $\log \underline{L}(\beta)$ subject to $g_0 = \beta_2 - 1 \leq 0$ and $g_i = -\beta_2 - e^{\beta_0+\beta_1 x_i} \leq 0$ ∀i. Lagrangian $\Lambda(\beta) = \log\underline{L}(\beta) + \mu_0(\beta_2-1) - \sum_i \mu_i(\beta_2 + e^{\beta_0+\beta_1 x_i})$, then gradient descent on stationarity equations (17.16) plus complementary slackness (17.17).

### Disjunctive geometric construction (p.697)
1. Project $Bel'$ orthogonally onto horizontal axis — point 1.
2. Draw $45°$ line through point 1 to vertical axis — point 2.
3. Line $l$ through $Bel_y$ and orthogonal projection of $Bel$ onto x-axis; parallel $l'$ through point 2; intersection with x-axis = $m(x)m'(x)$.
4. Symmetric construction in magenta yields $y$-coordinate.

## Parameters / quantities

| Name | Symbol | Domain/Units | Page | Notes |
|------|--------|--------------|------|-------|
| Bernoulli mass | $p, q$ | [0,1], $p+q \leq 1$ | 668 | $p=m(\{T\})$, $q=m(\{F\})$ |
| Logistic params | $\beta_0, \beta_1, \beta_2$ | $\mathbb{R} \times \mathbb{R} \times [0,1]$ | 669 | $\beta_2$ added vs. classical |
| KKT multipliers | $\mu_i, \lambda_j$ | $\mu_i \geq 0$ | 670 | Definition 137 |
| Refining map | $\rho$ | $2^\Omega \to 2^\Theta$ | 672 | Total belief theorem |
| Partition classes | $\Pi_i = \rho(\{\omega_i\})$ | subsets of $\Theta$ | 672 | |
| Solution-system size | $n_{\min}, n_{\max}$ | $n_{\min} = \sum (n_i-1)+1$, $n_{\max} = \prod n_i$ | 682 | Eqs |
| Symmetry group | $G = S_{n_1} \times \cdots \times S_{n_N}$ | permutations | 683 | |
| State space | $\mathbb{X}$ | Polish | 685 | for Choquet construction |
| Compact subsets | $\mathcal{K}(\Theta)$ | with Hausdorff topology | 685 | |
| Capacity | $\mu, \nu$ | monotone, subadditive, continuous from below | 691 | Defs 141-142 |
| Climate vector | $y = (y_h, y_f)$ | $\mathbb{R}^d$ | 711 | hist + future |
| Measurement | $z = y_h + e$ | error $e \sim \mathcal{N}(0, \Sigma^e)$ | 711 | Axiom 4 |
| Best params | $x^*$ | param space, $y = g(x^*) + \epsilon^*$ | 712 | "model discrepancy" |
| Feature maps | $\phi_m(x, C_k)$ | $X \times \mathcal{C} \to \mathbb{R}$ | 715 | |
| Lagrange weights | $\lambda_m$ | $\mathbb{R}$ | 716 | Log-linear classifier |
| Loss function | $l : (\mathcal{X} \times \mathcal{Y}) \times \mathcal{H} \to \mathbb{R}$ | nonneg | 721 | e.g. zero-one |
| PAC tolerance | $\varepsilon, \delta$ | $\in (0,1)$ | 722 | |
| VC dim of SVM | $VC_{\text{SVM}} = \min\{d, 4R^2/m^2\}+1$ | int | 723 | $d$=data dim, $R$=enclosing radius |
| Credal set | $\mathcal{P}$ | convex set of distributions | 727 | |

## Worked examples

### Example 52 (Lower/upper Bernoulli likelihoods, n=10, k=6) *(p.668)*
$\underline{L} = p^6 q^4$, $\overline{L} = (1-q)^6(1-p)^4$. Lower likelihood (a) is most committed BF on $\{T,F\}$ with $m(\{T,F\}) = 0$; achieves max at $p=k/n=0.6$, $q = 1-p = 0.4$. Upper likelihood is vacuous in $p+q=1$ family. Belief functions joining max $\overline{L}$ to max $\underline{L}$ all preserve ratio $p/q = k/(n-k)$.

### Example 53 (Total belief on ternary $\Omega = \{\omega_1, \omega_2, \omega_3\}$) *(p.676)*
Coarsening induces partition $\{\Pi_1, \Pi_2, \Pi_3\}$ of $\Theta$. Conditional $Bel_1$ on $\Pi_1$ has focal elements $e_1^1, e_1^2$; $Bel_2$ on $\Pi_2$ has single focal $e_2^1$; $Bel_3$ on $\Pi_3$ has $e_3^1, e_3^2$. Total belief Dempster combination $\overrightarrow{Bel}$ has 4 focal elements ("elastic bands"): $e_1 \cup e_2 \cup e_3 = e_1^1 \cup e_2^1 \cup e_3^1$, etc. (Fig.17.5).

### Example 54 (Bayesian-prior special case computed numerically) *(p.678)*
$m_1(e_1^1) = 1/2$, $m_2(e_2^1)=1$, $m_3(e_3^1)=1/3$, $m_3(e_3^2)=2/3$, $m_0$ ranging on subsets of $\Omega$. Yields 17 unknowns ($|\mathcal{E}|=17$), 8 independent linear equations ($|G|=8$). Construct one positive solution via (17.20): $m(\{e_1^1, e_2^1, e_3^1\}) = m_0(\Omega) m_1(e_1^1) m_2(e_2^1) m_3(e_3^1) = 1/4 \cdot 1/2 \cdot 1 \cdot 1/3 = 1/24$, etc. Demonstrates non-uniqueness — alternative $m^*$ via Fourier-Motzkin elimination differs from canonical $m$ by $\pm \epsilon$ on two columns.

### Buffon's colliding dice example (p.707)
Edge-edge collision probability ≈0.54; corner-face ≈0.46; small but real bias.

## Figures of interest

- **Fig 17.1** (p.665, prior): focal element diagrams for binary disjunctive combination. Referenced from previous chunk.
- **Fig 17.2** (p.668): 3D plots of lower (p^k q^{n-k}) and upper ((1-p)^k (1-q)^k) likelihood functions over the binary belief simplex; X axis $p$, Y axis $q$, k=6, n=10.
- **Fig 17.3** (p.673): pictorial schematic of total belief theorem — refining map between $\Omega$ and $\Theta$, with $Bel_0$ on $\Omega$ and conditional $Bel_i$ on partition classes.
- **Fig 17.4** (p.676): conditional belief functions in Example 53 — partition $\Pi$ and focal elements $e_i^j$ as ovals.
- **Fig 17.5** (p.677): four candidate focal elements ("elastic bands") of total belief.
- **Fig 17.6** (p.689): describing parameterised families of random sets — Gaussian-induced and Binomial-induced random sets via multivalued mapping.
- **Fig 17.7** (p.694): conditional subspace $\langle Bel \rangle_\odot$ for Yager/Dubois on binary frame as triangular polytope.
- **Fig 17.8** (p.695): Yager constant-mass loci are parallel (not converging to focus, contrast with Dempster Fig.8.5).
- **Fig 17.9** (p.696): conditional subspace for disjunctive combination on binary frame, with $Bel_y = [0,1]'$, $Bel_x = [1,0]'$, and a 1/3-iso-mass line.
- **Fig 17.10** (p.698): geometric construction of $Bel \mathbin{\bigcirc\!\!\!\cup} Bel'$ via $45°$ projection.
- **Fig 17.11** (p.699): conditional subspaces for unnormalised conjunctive ⌒ and disjunctive ⌣ on ternary frame — symmetric arrangement.
- **Fig 17.12** (p.704): geometry of the convex body of 2-monotone capacities in $\mathbb{R}^3$ — pyramid/diamond with vertex $[1,1,-1]$ extending below the simplex.
- **Fig 17.13** (p.705): Minkowski functional and convex-body projections.
- **Fig 17.14** (p.708): Buffon's needle problem.
- **Fig 17.15** (p.710): three point-process examples: grid, Poisson, uniform.
- **Fig 17.16** (p.722): smart vehicles and surgical robots — motivation for robust statistical learning.
- **Fig 17.17** (p.725): credal generalisation programme: (a) credal set of distributions covering both training and test data, (b) convex set of models induced by training data, (c) deep CNN structure with credal extension.

## Criticisms of prior work

- **Bayesian climate modelling** (Rougier-style): "Numerous assumptions are necessary to make calculations practical, which are only weakly related to the actual problem to be solved" — although the prior on climates is reduced to a prior $p(x^*)$ on parameters, "there is no obvious way of picking the latter (confirming our criticism of Bayesian inference in the Introduction). In general, it is far easier to say what choices are definitively wrong (e.g. uniform priors) than to specify 'good' ones." *(p.714)*
- **Vapnik's classical statistical learning theory**: "effectively useless for model selection, as the bounds on generalisation errors that it predicts are too wide to be useful, and rely on the assumption that the training and testing data come from the same (unknown) distribution. As a result, practitioners regularly resort to cross-validation." *(p.721)*
- **Smets's Jeffrey rule** [1690]: depends on probabilities (vs. our framework); his conditional belief function definition differs from Dempster-derived one. *(p.680)*
- **Spies's Jeffrey rule for belief functions** [1749]: framework depends on probabilities; relies on second-order belief function over conditional events. *(p.680)*
- **Ma et al.'s Jeffrey rule** [1227]: conditional constraints not preserved by their total belief functions. *(p.681)*
- **Dempster-Liu Gaussian belief**: "merely transfers normal distributions on the real line by Cartesian product with $\mathbb{R}^m$" — not a true generalisation. *(p.684)*
- **Training sets in machine learning**: "insufficient in quantity (a Google object detector trained on a few million images vs. thousands of billions of images out there) and insufficient in quality (selected based on cost, availability, mental attitudes — biasing the whole learning process)." *(p.724)*

## Design rationale

- **Why generalise logistic regression with parameter $\beta_2$**: because $p_i + q_i \leq 1$ doesn't follow from a single logit if $q_i = 1 - p_i$ in classical case; must add slack so problem is bounded. Constrained (vs. unconstrained classical). *(p.670)*
- **Why use ⊕ on conditional embeddings (Lemma 23) rather than Smets's second-order BF**: avoids dependence on probabilities; stays within propositional/random-set framework. *(p.680)*
- **Why exterior algebras**: belief vector representation makes focal elements of different cardinalities indistinguishable, but they are *qualitatively different objects* (areas vs. lengths vs. volumes); $k$-vectors encode this. *(p.706)*
- **Why credal-set models for ML rather than single-model selection**: (1) training-test distribution shift handled by belonging to same convex set; (2) overfitting reduces to convex-set identification; (3) deep learning lacks theoretical foundations — this provides one. *(pp.724-725)*
- **Why 2-monotonicity bracket constraint in max-entropy classifier**: only need 2-monotonicity (singleton brackets), not full ∞-monotonicity, because feature constraints involve only single $(x, C_k)$ pairs. *(p.716)*

## Open / research questions

Verbatim where space allows; otherwise paraphrased close.

- **Q.14 (p.671)**: "Is there an analytical solution to the generalised logistic regression inference problem, based on the above KKT necessity conditions?"
- **Q.15 (p.671)**: "What other parameterisations can be envisaged for the generalised logistic regression problem, in terms of the logistic links between the data and the belief functions $Bel_i$ on $\{T,F\}$?"
- **Q.16 (p.687)**: "Does there exist a (parameterisable) class of random sets, playing a role similar to that which Gaussian distributions play in standard probability, such that sample averages of (the equivalent of) i.i.d. random sets converge in some sense to an object of such a class?"
- **Q.17 (p.690)**: "What is the analytical form of random sets induced by, say, Gaussian, binomial or exponential families of (source) probability distributions?"
- **Q.18 (p.690)**: "How would results from random-set hypothesis testing relate to classical hypothesis testing applied to parameterised distributions within the assumed random set?"
- **Q.19 (p.691)**: "Can a (generalised) PDF be defined for a random-set random variable as defined above?"
- **Q.20 (p.692)**: "Can the inference problem be posed in a geometric setting too, by representing both data and belief measures in a common geometric space?"
- **Q.21 (p.696)**: "Does disjunctive combination commute with affine combination in general belief spaces?"
- **Q.22 (p.700)**: "What is the general pointwise geometric behaviour of disjunctive combination, in both the normalised and the unnormalised case?"
- **Q.23 (p.700)**: "What is the general pointwise geometric behaviour of conjunctive combination in the unnormalised case?"
- **Q.24 (p.700)**: "What is the geometric behaviour of bold and cautious rules?"
- **Q.25 (p.700)**: "Can any major conditioning operator be interpreted as geometric (in the sense of this book) conditioning, i.e., as producing the belief function within the conditioning simplex at a minimum distance from the original belief function, with respect to an appropriate norm in the belief space?"
- **Q.26 (p.705)**: "What is the most appropriate framework for describing the geometry of monotone capacities?"
- **Q.27 (p.705)**: "Can we provide a representation in the theory of convex bodies of the set of 2-monotone capacities similar to that of the belief space, i.e., by providing an analytical expression for the vertices of this set?"
- **Q.28 (p.706)**: "How can the geometry of monotone capacities be exploited to provide a geometric theory of general random sets?"
- **Q.29 (p.706)**: "How can we frame the geometry of (sets of desirable) gambles and MV algebras in terms of functional spaces?"
- **Q.30 (p.707)**: "Under what conditions is the above [convex-body-projection] capacity monotone?"
- **Q.31 (p.707)**: "Under what conditions is this capacity a belief function (i.e. an infinitely monotone capacity)?"
- **Q.32 (p.709)**: "How does geometric probability generalise when we replace standard probabilities with other uncertainty measures?"
- **Q.33 (p.714)**: "Can a climate model allowing predictions about future climate be formulated in a belief function framework, in order to better describe the huge Knightian uncertainties involved?"
- **Q.34 (p.717)**: "Should constraints of [the bracket] form be enforced on all possible subsets $A \subset X \times \mathcal{C}$, rather than just singleton pairs $(x, C_k)$? This is linked to the question of what information a training set actually carries."
- **Q.35 (p.717)**: "An alternative course of action is to pursue the *least committed*, rather than the maximum-entropy, belief function satisfying the constraints. This is left for future work."
- **Q.36 (p.721)**: "Derive the analytical form of the solution to the above generalised maximum entropy classification problem."
- **Q.37 (p.721)**: "How does this analytical solution compare with the log-linear model solution to the traditional maximum entropy problem?"
- **Q.38 (p.721)**: "Derive and compare the constraints and analytical solutions for the alternative generalised maximum entropy frameworks obtained by plugging in other concave generalised entropy functions."

Plus implicit research questions: connection of total-belief problem with transversal matroids [1374] and positive linear systems [590] (p.684); exploration of marginal extension [1294] vs. law of total belief (p.684); connection of total belief with credal [584], geometric [1788], conjunctive/disjunctive [1690] conditioning (p.684).

## Notable references cited in Chapter 17

- `[1583]` Shafer 1976 — *Mathematical theory of evidence* (foundational text; cited p.694 etc.)
- `[1689]` Smets — generalised Bayesian theorem (cited p.673)
- `[1690]` Smets — generalised Jeffrey's rule (cited p.680)
- `[1749]` Spies — Jeffrey's rule for belief functions (cited p.680)
- `[1227]` Ma et al. — Jeffrey rule via Dempster's rule on power set (cited p.681)
- `[364]` Cuzzolin's own work — focal-element structure of total belief (cited p.681)
- `[576]` Epstein-Seo — central limit theorem for Bernoulli random sets (cited p.685)
- `[1638]` Shi 2015 — generalised CLT for capacities (cited p.687)
- `[400]` de Cooman-Miranda — laws of large numbers for coherent lower previsions (cited p.684)
- `[314]` Choquet capacity LLN (cited p.684)
- `[243]` Chareka — CLT for capacities (cited p.684)
- `[1806]` Teran — CLT (p.684)
- `[1230]` Marinacci/Maccheroni — LLN for monotone measures (p.688)
- `[1807]` Teran 2014 — LLN under complete monotonicity (p.688)
- `[1300]` Molchanov — Glivenko-Cantelli for capacities (p.687)
- `[1304]` Molchanov — *Theory of random sets* (cited pp.691-692)
- `[725]` Graf 1980 — Radon-Nikodym for capacities (cited p.692)
- `[793]` Harding et al. 1997 — RND for set functions (cited p.691)
- `[1467]` Rebille 2009 — RND for capacities (p.691)
- `[283]` Choquet — total belief and seminar paper (cited p.687)
- `[584]` credal conditioning (p.684)
- `[1788]` Suppes-Zanotti geometric conditioning (p.684)
- `[963]` Fourier-Motzkin elimination (p.678)
- `[1855]` Vershynin — *Lectures in geometric functional analysis* (cited pp.704-705)
- `[833], [834]` Geometric functional analysis (cited p.703)
- `[1324]` MV-algebras and rational polyhedra 2016 (p.703)
- `[688]` Diameters under random projections (Prop 76 ref, p.705)
- `[855]` Stochastic geometry text (p.709)
- `[1268]` Polyconvex bodies and Minkowski combinations (p.710)
- `[1507]` Rougier — Bayesian climate modelling (cited extensively pp.711-714)
- `[355]` Maximum entropy on belief functions (p.717)
- `[949]` KKT extension to belief functions (p.718)
- `[1849, 1850, 1851]` Vapnik — statistical learning theory texts (p.722)
- `[671]` autonomous-vehicle robustness motivation (p.722)
- `[2118]` minimax robust learning (p.724)
- `[964]` budgeted adversarial models (p.724)

## Bibliography section (book pp.729-850 / PDF pp.742-863)

- **Numbering scheme**: numeric `[N]` keys, sorted alphabetically by first author surname (verified at start: [1] Abellán, [2] Abellán-Masegosa, [3-7] more Abellán; mid: [413-426] Dempster cluster; [1583-1592] Shafer cluster; [1703-1733] Smets cluster; [1849-1851] Vapnik; [1871-1878] Walley cluster; [1999-2011] Yager cluster).
- **Total reference count: 2137** (last entry [2137] Mourad Zribi & Mohammed Benjelloun, *Parametric estimation of Dempster-Shafer belief functions*, FUSION 2003 — book p.850, PDF p.863). This is consistent with Cuzzolin's claim of having compiled the largest existing bibliography on belief and uncertainty theory.
- **No author or subject index** — book ends at last reference.

### Foundational / highly-impactful references identified

**Foundational evidence theory**
- `[413]` Arthur P. Dempster, *New methods for reasoning towards posterior distributions based on sample data*, Annals of Mathematical Statistics 37 (1966), 355-374. — Predecessor of upper/lower probabilities.
- `[414]` Dempster, *Upper and lower probabilities induced by a multivalued mapping*, Annals of Mathematical Statistics 38 (1967), 325-339. — **The seminal multivalued-mapping paper.**
- `[415]` Dempster, *Upper and lower probability inferences based on a sample from a finite univariate population*, Biometrika 54 (1967), 515-528.
- `[416]` Dempster, *A generalization of Bayesian inference*, JRSS B 30 (1968), 205-247. — Generalised Bayesian inference.
- `[417]` Dempster, *Upper and lower probabilities generated by a random closed interval*, Annals of Mathematical Statistics 39 (1968), 957-966.
- `[1583]` Glenn Shafer, *A mathematical theory of evidence*, Princeton University Press, 1976. — **THE canonical text.**
- `[1584]` Shafer, *A theory of statistical evidence*, Foundations of Probability Theory…, vol. 2, Reidel, 1976, 365-436.
- `[1587]` Shafer, *Allocations of probability*, Annals of Probability 7 (1979), 827-839.
- `[1588]` Shafer, *Jeffrey's rule of conditioning*, Philosophy of Sciences 48 (1981), 337-362.
- `[1589]` Shafer, *Belief functions and parametric models*, JRSS B 44 (1982), 322-339.
- `[1592]` Shafer, *Conditional probability*, International Statistical Review 53 (1985), 261-277.

**Smets / Transferable Belief Model cluster** (refs 1703-1733)
- `[1705-1707]` Smets's late-90s TBM treatise chapters in *Handbook of Defeasible Reasoning* vol. 1.
- `[1714]` Smets, *Belief functions on real numbers*, Int. J. Approx. Reasoning 40 (2005), 181-223.
- `[1715]` Smets, *Decision making in the TBM: necessity of the pignistic transformation*, Int. J. Approx. Reasoning 38 (2005), 133-147.
- `[1718]` Smets, *Bayes' theorem generalized for belief functions*, ECAI-86, 169-171.
- `[1720]` Smets, *The α-junctions: Combination operators applicable to belief functions*, ECSQARU/FAPR 1997.
- `[1722]` Smets, *The application of the matrix calculus to belief functions*, IJAR 31 (2002), 1-30.
- `[1725]` Smets, *Belief functions and generalized Bayes theorem*, IFSA 1987.
- `[1726]` Smets-Cooke, *How to derive belief functions within probabilistic frameworks?*, ECSQARU/FAPR 1997.
- `[1729]` Smets-Hsia-Saffiotti-Kennes-Xu-Umkehren, *The transferable belief model*, ECSQARU 1991.
- `[1730]/[1731]` Smets-Kennes, *The transferable belief model*, Artificial Intelligence 66 (1994), 191-234. — **The canonical TBM paper.**
- `[1733]` Smets-Ristic, *Kalman filter and joint tracking and classification in the TBM framework*, FUSION 2004.

**Walley / imprecise probability**
- `[1873]` Peter Walley, *Belief function representations of statistical evidence*, Annals of Statistics 15 (1987), 1439-1465.
- `[1874]` Walley, *Statistical reasoning with imprecise probabilities*, Chapman and Hall, 1991. — **The canonical IP text.**
- `[1875]` Walley, *Measures of uncertainty in expert systems*, Artificial Intelligence 83 (1996), 1-58.
- `[1877]` Walley, *Towards a unified theory of imprecise probability*, IJAR 24 (2000), 125-148.
- `[1878]` Walley-Fine, *Towards a frequentist theory of upper and lower probability*, Annals of Statistics 10 (1982), 741-761.

**Choquet / capacities**
- `[283]` Gustave Choquet — capacity theory (referenced multiple times).
- `[576]` Epstein-Seo — CLT for Bernoulli random sets via Choquet representation.
- `[725]` Siegfried Graf, *A Radon-Nikodym theorem for capacities*, J. Reine u. Angew. Math. 320 (1980), 192-214.

**Yager rule cluster** (refs 1999-2011)
- `[1999]` Yager, *On a general class of fuzzy connectives*, Fuzzy Sets Syst. 4 (1980), 235-242.
- `[2001]` Yager, *Entropy and specificity in a mathematical theory of evidence*, Int. J. General Syst. 9 (1983), 249-260.
- `[2009]` Yager, *On the Dempster-Shafer framework and new combination rules*, Information Sciences 41 (1987), 93-138.

**Pawlak / rough sets**
- `[1393-1397]` Zdzislaw Pawlak — rough sets (1982-1998).

**Pearl / Bayesian networks / probabilistic reasoning**
- `[1398]` Judea Pearl, *Fusion, propagation, and structuring in belief networks*, AI 29 (1986), 241-288.
- `[1403]` Pearl, *On probability intervals*, IJAR 2 (1988), 211-216.
- `[1405]` Pearl, *Probabilistic reasoning in intelligent systems*, Morgan Kaufmann, 1988. — Bayes-net text.
- `[1407]` Pearl, *Bayesian and belief-functions formalisms for evidential reasoning*, Readings in Uncertain Reasoning, 1990, 540-574.
- `[1411]` Pearl, *The sure-thing principle*, UCLA Tech. Rep. R-466, 2016.

**AGM / belief revision**
- `[26]` Carlos E. Alchourrón, Peter Gärdenfors, David Makinson, *On the logic of theory change: partial meet contraction and revision functions*, in *Readings in Formal Epistemology: Sourcebook* (2016), 195-217 — **The canonical AGM 1985 paper, reprinted edition cited.**

**Carnap**
- `[228]` Rudolf Carnap, *Logical foundations of probability*, University of Chicago Press, 1962.

**Vapnik / statistical learning**
- `[1849]` Vladimir N. Vapnik, *Statistical learning theory*, vol. 1, Wiley, 1998.
- `[1850]` Vapnik, *An overview of statistical learning theory*, IEEE TNN 10 (1999), 988-999.
- `[1851]` Vapnik, *The nature of statistical learning theory*, Springer, 2013.

**Random sets / Polish space machinery**
- `[1304]` Ilya Molchanov, *Theory of random sets*. — Cuzzolin draws on this for measurability and topology.
- `[1300]` Molchanov — Glivenko-Cantelli for capacities.

**Geometric functional analysis**
- `[1855]` Roman Vershynin, *Lectures in geometric functional analysis*, 2011.

**Random sets and statistics**
- `[717]` Goutsias-Mahler-Nguyen, *Random sets: theory and applications*, IMA Vol. 97, Springer, 1997.
- `[719]` Michel Grabisch — fuzzy/k-additive measures (multiple).
- `[720]` Grabisch, *The Möbius transform on symmetric ordered structures and its application to capacities on finite sets*, Discrete Math 287 (2004), 17-34.
- `[721]` Grabisch, *Belief functions on lattices*, Int. J. Intelligent Systems 24 (2009), 76-95.
- `[723]` Grabisch-Nguyen-Walker, *Fundamentals of uncertainty calculi with applications to fuzzy inference*, Springer, 2013.

**Denœux cluster** (refs 456-478): k-NN classifiers, EM algorithm extensions, parametric estimation under belief functions, neural-network function approximation, Möbius-transform fast computation, Dempster-Shafer calculus for statisticians (ref [468] with Dempster).

**Dezert / DSm theory** (refs 490-497): plausible-and-paradoxical reasoning, DSmT, hyper-power sets, generalised pignistic transformation.

**de Cooman cluster** (refs 395-401): vague probability, imprecise probability trees, imprecise Markov chains, weak/strong LLN for coherent lower previsions, updating beliefs under incomplete observations.

## Implementation notes for propstore

This chapter is a goldmine for propstore's forward roadmap. Concrete pointers:

- **`propstore.belief_set` and `propstore.world`**: Theorem 111 (total belief) corresponds to a generalised total-probability operator. The non-uniqueness result (Proposition 67, solution graphs) is the formal grounding for storing **multiple rival total beliefs** as ATMS environments — never collapsing to one. Each minimal solution = one node in a Dung-style merge framework.
- **`propstore.aspic_bridge`**: Theorem 113's binary disjunctive geometric behaviour (lines through fixed point) gives a closed-form for cautious-combination preference orderings.
- **`propstore.world.assignment_selection_merge`**: the column-substitution class T (Definition 138) is exactly the kind of structured incremental update that assignment-selection-merge can codify when sources disagree on focal elements.
- **`propstore.dimensions` / KindType.TIMEPOINT**: Definitions 144-145 (point process, random element) plus the Choquet construction (Definition 139, Proposition 69) give a measure-theoretic foundation for treating sample spaces as Polish-space frames — which is required if we ever extend dimensions beyond finite frames.
- **`propstore.defeasibility`**: Theorem 117's credal realisability bound (eq.17.74 vs. eq.17.76) maps directly onto our defeasibility model — "uniform credal realisability" is equivalent to requiring exception-derived defeats to be valid for *every* source distribution in the credal set, while plain credal realisability is weaker (some source). We should distinguish these two strengths in CKR justifications.
- **Calibration / honest ignorance**: Definition 147's bracket constraints (eq.17.58) directly encode our principle: when training data is insufficient, *don't* commit to a single distribution; carry the lower/upper bracket through. The vacuous belief function over $X \times \mathcal{C}$ corresponds to "I don't know" — Cuzzolin endorses this on p.714 where he explicitly criticises Bayesian uniform priors.
- **Render layer**: Theorem 116/117 give us a principled way to present **render-time confidence intervals** for ML-derived claims: $L(\hat{h}) \in [0, (\log|\mathcal{H}|+\log(1/\delta))/n]$ becomes a render-policy choice.
- **`propstore.world` / ATMS**: 17.3.3 deep-learning programme suggests that the same convex-set-of-models architecture can be implemented as ATMS bundles, each member of the credal set being a context.
- **Geometric conditioning gap (Q.25)**: propstore's geometric/Dempster conditioning split should be revisited; Q.25 asks whether all conditioning operators can be unified under a "minimum-distance projection" view — that's a directly actionable design question.

## Quotes worth preserving

- *"It is far easier to say what choices are definitively wrong (e.g. uniform priors) than to specify 'good' ones."* — p.714 (climate priors, but the principle generalises)
- *"Vapnik's classical statistical learning theory is effectively useless for model selection, as the bounds on generalisation errors that it predicts are too wide to be useful."* — p.721
- *"Imprecise probabilities naturally arise whenever the data are insufficient to allow the estimation of a probability distribution."* — p.724
- *"It would be natural to term such objects random-set random variables."* — p.690
- *"A specific result on the Radon-Nikodym derivative for random (closed) sets is still missing, and with it the possibility of generalising the notion of a PDF to these more complex objects."* — p.692
- *"This new approach to inference with belief functions, based on the notion of the belief likelihood, opens up a number of interesting avenues."* — p.667
- *"Tackling these more general measures requires therefore extending the concept of a geometric belief space in order to encapsulate the most general such representation."* — p.701
- *"In the medium term, the aim is to develop a general geometric theory of imprecise probabilities, encompassing capacities, random sets induced by capacity functionals, and sets of desirable gambles."* — p.701

## Final summary statistics

- Definitions extracted from Ch.17: **13** (Defs 137-149)
- Theorems extracted: **9** (Thms 109-117)
- Propositions: **14** (67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80) — 14 numbered
- Lemmas: 3 (22, 23, 24)
- Corollaries: 4 (25, 26, 27, 28)
- Conjectures: 2 (1, 2)
- Equations annotated/cited: 64+ numbered (17.8 - 17.76)
- Figures referenced: 17.2-17.17
- Numbered research questions: **25** (Q.14 - Q.38)
- Worked examples: 4 (52, 53, 54, plus colliding-dice numerical illustration)
- Total bibliography entries: **2137** (numeric `[N]` keys, alphabetical by author surname, no separate author/subject index)
- Pages with no read failures: all 184 in range
