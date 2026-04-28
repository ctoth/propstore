# Chunk #3 — Chapter 4: Reasoning with belief functions

**Book pages:** 109-236
**PDF idx:** 134-261

## Sections covered

- 4.1 Inference (and 4.1.1 from statistical data, 4.1.2 from qualitative data, 4.1.3 from partial knowledge, 4.1.4 a coin toss example) — pp.109-127
- 4.2 Measuring uncertainty (4.2.1 order relations, 4.2.2 measures of entropy, 4.2.3 principles of uncertainty) — pp.127-132
- 4.3 Combination (Dempster's rule under fire, alternative rules, families) — pp.133-160
- 4.4 Belief vs. Bayesian reasoning: a data fusion example — pp.160-163
- 4.5 Conditional belief functions (Dempster, Suppes-Zanotti, Smets, disjunctive, Spies, others) — pp.163-181
- 4.6 Manipulating (conditional) belief functions (generalised Bayes theorem, total probability, marginalisation) — pp.181-189
- 4.7 Computing — efficient algorithms, transformation approaches, Monte Carlo, local propagation — pp.189-200
- 4.8 Making decisions (utility-based, non-utility-based, multicriteria) — pp.200-216
- 4.9 Continuous formulations (Shafer's allocations, BFs on Borel intervals, random sets, Kramosil's, MV algebras) — pp.216-228
- 4.10 The mathematics of belief functions (distances, algebra, integration, category theory) — pp.228-236

## Chapter overview

Chapter 4 is the operational engine of Cuzzolin's monograph: where Chapter 3 introduced the formal objects (mass, belief, plausibility, commonality), Chapter 4 surveys what one can *do* with them — how to infer them from data, measure their uncertainty, combine them, condition them, propagate them efficiently, and make decisions from them. It is deliberately encyclopaedic: every competing approach in the belief-function literature is given a brief but mathematically precise treatment, with citations. In Cuzzolin's words, the chapter is a "manual for the working scientist."

The chapter argues, implicitly, three theses. First, that belief-function inference is *richer* than Bayesian inference because it does not require a prior — but consequently the literature has fragmented across many incompatible inference recipes (likelihood-based, Dempster's a-equation, fiducial, Martin-Liu inferential models, weak belief, Walley-Fine frequentist envelopes, confidence structures). Second, that combination is the most theoretically contested operation in the whole field: Dempster's rule is *one* answer (under a strong independence assumption), but a long list of alternative rules has been proposed for cases of dependent or unreliable evidence. Third, that conditioning is genuinely plural — Dempster's conditioning, Smets's conjunctive (TBM) conditioning, geometric (Suppes-Zanotti) conditioning, disjunctive conditioning, Spies's equivalence-class conditioning, and others — each with different formal properties and different appropriate applications.

The chapter culminates in §4.10, a roadmap to the *mathematical structures* (distances, algebraic operations, category theory, integration on monotone capacities) that the rest of the book uses to ground its geometric programme. Sections 4.7 (computing) and 4.8 (decision making) are the most directly action-oriented for an implementor: they collect every published algorithm for efficient belief computation and every published decision rule.

## 4.1 Inference

### Setup and likelihood-based inference *(pp.109-114)*

The general inference problem: given i.i.d. observations $x = (x_1,\dots,x_n)$ from a parametric family $\{f(x|\theta), \theta\in\Theta\}$, build a belief function on $\Theta$. Three main routes are surveyed: likelihood-based, Dempster-Shafer (a-equation / fiducial), and partial-knowledge.

**Shafer's likelihood-based BF.** Shafer (1976) proposed that the likelihood induce a *consonant* belief function on $\Theta$ via the contour function $pl(\theta|x) = L(\theta;x)/\sup_{\theta\in\Theta} L(\theta;x)$.

$$
pl(\theta|x) = \frac{L(\theta; x)}{\sup_{\theta \in \Theta} L(\theta; x)}
$$
**(Eq. 4.2, p.112)** Where: $L(\theta;x) = f(x|\theta)$ is the likelihood and the divisor is the maximum-likelihood value (so $pl$ peaks at the MLE).

The associated plausibility function on subsets of $\Theta$ and corresponding multivalued mapping $\Gamma_x:\Omega\to 2^\Theta$:

$$
Pl_\Theta(A|x) = \sup_{\theta\in A} pl(\theta|x), \qquad \Gamma_x(\omega) = \{\theta\in\Theta\,|\,pl(\theta|x)\geq\omega\}
$$
**(p.113)** with $\Omega = [0,1]$ and uniform source probability.

Denoeux argued the method extends to *low-quality data* (partial relevance, imperfect observation) via the evidential EM (E2M) algorithm — a generalised likelihood maximisation for uncertain data ([460], [458]). Zribi and Benjelloun ([2137]) gave an iterative MLE-based BF estimation in this generalised EM framework.

**Example 8 — Bernoulli sample (p.113):** for $x_1,\dots,x_n$ i.i.d. Bernoulli with parameter $\theta\in[0,1]$, $y=\sum x_i$ successes:
$$
pl(\theta|x) = \frac{\theta^y(1-\theta)^{n-y}}{\hat\theta^y(1-\hat\theta)^{n-y}}
$$
where $\hat\theta = y/n$ is the MLE.

**Robust Bayesian inference (Wasserman [1915]).** BFs generate classes of priors (credal sets); each prior is updated by Bayes' rule, giving an envelope $\Pi_x$ on the posterior. Lower/upper expectation formulas:

$$
\inf_{P_x\in\Pi_x} P_x(A) = \frac{E_*(L_A)}{E_*(L_A)+E^*(L_{A^c})}, \qquad \sup_{P_x\in\Pi_x} P_x(A) = \frac{E^*(L_A)}{E^*(L_A)+E_*(L_{A^c})}
$$
**(p.114)** where $E^*(f)=\int f^*(\omega)\mu(d\omega)$, $E_*(f)=\int f_*(\omega)\mu(d\omega)$, $f^*(\omega)=\sup_{\theta\in\Gamma(\omega)} f(\theta)$, $f_*=\inf$, and $L_A(\theta)=L(\theta)I_A(\theta)$.

**Proposition 24 (p.113):** Lets $\Pi$ be the credal set induced by a BF on $\Theta$ via source space $(\Omega,\mathcal{B}(\Omega),\mu)$ and multivalued $\Gamma$; if $L(\theta)$ is bounded then for any $A\in\mathcal{B}(\Theta)$ the inf/sup posteriors are as above.

**Proposition 25 (Wasserman, [1915] Thm 2.1, p.114):** A probability $P$ is consistent with a BF $Bel$ induced by source $(\Omega,\mathcal{B}(\Omega),\mu)$ via $\Gamma$ iff for $\mu$-a.a. $\omega$ there is a probability $P_\omega$ on $\mathcal{B}(\Theta)$ supported by $\Gamma(\omega)$ such that $P(A) = \int_\Omega P_\omega(A)\mu(d\omega)$.

**Dempster's auxiliary-variable inference (a-equation, pp.114-115).** Augment the parametric model $\{f(x|\theta)\}$ with an *a-equation* $X = a(\Theta, U)$ where $U$ is an unobserved auxiliary variable with known distribution $\mu$ independent of $\theta$. Standard CDF inversion is the canonical case: $X = F_\theta^{-1}(U)$ for $U\sim\mathcal{U}([0,1])$. The a-equation defines a multivalued mapping (compatibility relation) $\Gamma:U\to 2^{\mathbb{X}\times\Theta}$ via $\Gamma(u) = \{(x,\theta)\,|\,x = a(\theta,u)\}$. This induces a BF on $\mathbb{X}\times\Theta$. Dempster-conditioning on observed $\theta$ gives sample BF $Bel_\mathbb{X}(A|\theta)$; conditioning on observed $X=x$ gives the *Dempster posterior*:

$$
Bel_\Theta(B|x) = \frac{\mu\{u : M_x(u) \subseteq B\}}{\mu\{u : M_x(u)\neq\emptyset\}}, \quad B\subseteq\Theta
$$
**(Eq. 4.3, p.115)** where $M_x(u) = \{\theta : x=a(\theta,u)\}$.

**Example 9 — Bernoulli sample, Dempster style (p.115):** With pivotal $U=(U_1,\dots,U_n)$ uniform on $[0,1]^n$ and $X_i = 1$ if $U_i\le\theta$ else 0, with $y = \sum x_i$ successes, the BF $Bel_\Theta(\cdot|x)$ is induced by a *random closed interval* $[U_{(y)}, U_{(y+1)})$ on the order statistics. Quantities like $Bel_\Theta([a,b]|x)$ can be readily computed.

**Cuzzolin's critique of Dempster's model (p.115):** Dempster's model is a *posterior without a prior* (good); compatible with Bayesian: $Bel_\Theta(\cdot|x) \subset P(\cdot|x)$ (good); but conditioning often uses Monte Carlo, and analysis depends on auxiliary variable $U$ which is not observable, so the BF is not uniquely identified by the statistical model.

**Almond's BF construction via Dempster's model ([29], p.116)** focused on Bernoulli/Poisson processes.

**Dempster's $(p,q,r)$ semantics ([468], p.116):** every assertion is a triple where $p = Bel(A)$, $q = Bel(A^c)$, $r = 1-p-q$ ('don't know'). Applied to inference and prediction from Poisson counts, with join-tree structure. Concept of a *dull null hypothesis* — one assigning mass 1 to an interval $L_1\le L\le L_2$.

### Fiducial / inferential-model / weak-belief / frequentist *(pp.116-121)*

**Fiducial inference (Fisher 1935, [621], p.116).** Pivotal variable $U$ such that $(X,\Theta,U)$ is uniquely determined by the a-equation given any two. Crucial assumption: *continue to believe* — $U$ retains its prior distribution after observing $X$. This produces a fiducial distribution on $\Theta$.

**Example 10 — fiducial inference (p.117):** Estimate mean of $N(0,1)$ from one observation $X$. The a-equation is $X = \Theta + \Psi^{-1}(U)$ (where $\Psi$ is standard-normal CDF); pivotal $U\sim\mathcal{U}(0,1)$. Events $\{\Theta\le\theta\}$ and $\{U\ge\Psi(X-\theta)\}$ have the same probability, so fiducial probability of $\{\Theta\le\theta\}$ is $\Psi(\theta-X)$, giving fiducial $\Theta\sim N(X,1)$.

**Inferential models / weak belief (Martin & Liu [1258], pp.117-118).** Predict the value $u^*$ of the auxiliary variable *before* conditioning on $X=x$. Use a *predictive random set* $\mathcal{S}:U\to 2^U$ with $u\in\mathcal{S}(u)$ — equivalent to replacing pivot measure $\mu$ with a BF. A BF $Bel^*$ on $\Theta$ is an *inferential model* if $Bel^*(A) \le Bel_\Theta(A)$ for all $A$ — i.e., is dominated by Dempster's posterior. The quantity $\mathcal{S}$ is called a "predictive random set" — a smearing of the pivot. Extended on $U\times\mathbb{X}\times\Theta$ then marginalised:

$$
\Gamma_\mathcal{S}(u) = \bigcup_{u'\in\mathcal{S}(u)} \Gamma(u')
$$
**(p.118)** Maximal-belief and other constructions for $\mathcal{S}$ in [1259]. Ermini's *elastic belief* extension [1108]. WB applied to binomial proportion and outlier counting.

**Walley & Fine's frequentist theory of upper/lower probability ([1878], p.118).** Estimator for lower probability $\underline{P}$ from $\epsilon_1,\dots,\epsilon_n$:
$$
\underline{r}_n(A) = \min\{r_j(A) : k(n)\le j\le n\}, \quad k(n)\to\infty
$$
where $r_j(A)$ is relative frequency of $A$ after $\epsilon_j$. Convergence: $\lim_n \underline{P}^\infty(G_{n,\delta}^c)/\underline{P}^\infty(G_{n,\delta}) = 0$ for $G_{n,\delta} = \{|\underline{r}_n(A) - \underline{P}(A)|<\delta\}$. Lemmers [1132]: BFs from sampling cannot be interpreted as frequency ratios. Fierens & Fine [612] continue with credal sets for long sequences with persistent oscillations.

**Confidence structures (Perrussel et al. [1420], pp.119-120).** Observation-conditional random set $\Gamma(\omega,x)\subset\Theta$:
$$
Bel_{\theta|x}(A) = P_\omega(\{\omega : \Gamma(\omega,x)\subseteq A\})
$$
**Confidence set:** $C: \mathcal{X}\to\mathcal{P}(\Theta)$, $C(x)\subset\Theta$ (Eq. 4.4, p.119). Neyman-Pearson confidence: frequentist probability of drawing $x$ such that $C(x)$ covers true parameter. A *confidence structure* is an observation-conditional random set commensurate with NP confidence:
$$
P_{x|\theta}\!\left(\!\left\{x\in\mathcal{X} : \theta\in\bigcup_{\omega\in A}\Gamma(\omega,x)\right\}\!\right) \ge P_\omega(A)
$$
**(Eq. 4.5, p.119)**

**Shafer's three cases of inference ([1589], pp.120-121).** (i) independent observations for each $f(\cdot|\theta)$ — use Smets' conditional embedding + Dempster's rule; (ii) single empirical frequency distribution — use fiducial inference; (iii) no evidence except conviction of randomness — Bayesian-inspired construction. For case (iii) with $\mathbb{X}=\{1,\dots,k\}$ Bayesian prior $P$ on $\mathbf{X}=(X_1,X_2,\dots)$ that is countably additive, symmetric, and $P(\lim_n f(x,n)\text{ exists})=1$, Shafer constructs a BF with three properties (p.121): $Bel(\lim_n f(x,n)\text{ exists}) = 1$; $Bel(X_1=x_1,\dots,X_n=x_n|\lim_n[f(1,n),\dots,f(k,n)]=\theta) = P_\theta(x_1)\cdots P_\theta(x_n)$; $Bel(\lim_n[f(1,n),\dots,f(k,n)]\in A)=0$ for all proper $A\subsetneq\Theta$. For $\mathbb{X}=\{0,1\}$ the unique solution recovers Dempster's generalised Bayesian solution.

### 4.1.2 From qualitative data *(pp.121-123)*

Key proposals:

- **Wong & Lingras's perceptron model ([1958, 1953], pp.121-122).** Build BF from preference/indifference relations $\cdot >$ and $\sim$ such that $A\cdot>B \iff Bel(A)>Bel(B)$ and $A\sim B \iff Bel(A)=Bel(B)$. Existence: $\cdot >$ a weak order and $\sim$ an equivalence. **Algorithm 1 (p.122):** consider all propositions in preferences as candidate focal elements; eliminate $A$ if $A\sim B$ for some $B\subset A$; perceptron solves the remaining (in)equality system for mass $m$. *Negative feature:* arbitrarily picks one of many admissible solutions; doesn't address inconsistent inputs.
- **Qualitative discrimination processes (Osei-Bryson et al. [198, 1355, 197, 1370], p.122).** Three buckets ('broad'/'intermediate'/'narrow'), then imprecise pairwise comparisons giving mass intervals per focal element, plus consistency check.
- **Ben Yaghlane's constrained optimisation ([111], pp.122-123).** Maximise entropy/uncertainty subject to constraints derived from inputs:
$$
A\cdot > B \iff Bel(A)-Bel(B)\ge\epsilon, \quad A\sim B \iff |Bel(A)-Bel(B)|\le\epsilon
$$
- **Ennaceur et al. [575]:** for incomplete/incomparable preferences.
- **Yang [2048]:** confidence belief function from BF samples taken from a bounded-rationality expert.

### 4.1.3 From partial knowledge *(pp.123-124)*

- **Smets [1695]:** given that random process is governed by some $P\in\mathcal{P}$, ask what beliefs follow. Like Wasserman's robust Bayesian inference.
- **Aregui & Denoeux [55]:** *pl-most committed BPA* in BPAs less committed than all probabilities in $\mathcal{P}$.
- Aregui & Denoeux [58]: lower envelope of pignistic probabilities $\mathcal{P}$ when $\mathcal{P}$ is itself a BF (e.g., a p-box, multinomial confidence region). Most committed consonant BF preferred. Extended to continuous variables [56].
- **Caron et al. [230]:** $n$-dimensional Gaussian betting density partial knowledge — explicit least-committed basic belief density in TBM.
- **Doré et al. [508]:** review eliciting principles, especially pignistic.

**Building complete BFs from partial ones (p.124):**
- Hsia [846]: minimum commitment principle (stronger than minimum specificity).
- Lemmer & Kyburg [1134]: belief-plausibility intervals for singletons → algorithm; result not least-informative in general.
- Moral & Campos [1314]: minimum-commitment + 'focusing' axiom.

**Inference in machine learning (p.124):**
- Bentabet et al. [127]: fuzzy c-means + BPA from grey levels (image processing).
- Matsuyama [1270]: BPA from similarity measures.
- [1089]: SVM + BFs and fuzzy memberships as constraints in convex optimisation, giving fuzzy SVM and belief SVM.

### 4.1.4 Coin-toss example *(pp.124-127)*

Setup: $n=10$ tosses give $X = \{H,H,T,H,T,H,T,H,H,H\}$, $k=7$ successes, $n-k=3$ failures. Parameter $\theta=p=P(H)$.

**General Bayesian inference (p.125).** Likelihood $P(X|p)=p^k(1-p)^{n-k}$ (Eq. 4.6). Posterior $P(p|X) = P(X|p)P(p)/P(X) \propto P(X|p)$ in absence of prior info (Eq. 4.7). MLE $p=k/n=0.7$.

**Frequentist test (p.125).** Null hypothesis $p=k/n$. Compute right-tail p-value at confidence level $\alpha=0.05$. Right-tail $\approx 1/2$ vastly exceeds $\alpha$; hypothesis cannot be rejected.

**Likelihood-based BF inference (p.126).** $Pl_\Theta(A|X) = \sup_{p\in A} \tilde L(p|X)$, $Bel_\Theta(A|X) = 1 - Pl_\Theta(A^c|X)$, where $\tilde L$ is normalised likelihood. Random set $\Gamma_X(\omega) = \{\theta : Pl_\Theta(\{\theta\}|X)\ge\omega\} = \{\theta : \tilde L(p|X)\ge\omega\}$ — an interval centred on MLE. The BF's credal set is "an entire convex envelope of PDFs there".

**On the binary frame $\Omega=\{H,T\}$, applying the procedure to normalised counts $\tilde f(H)=k/n$, $\tilde f(T)=(n-k)/n$** would naively give $Pl(H)=1$, $Pl(T)=3/7$ — but that is unsatisfactory since $p=1$ (always heads) is excluded by the data. So instead use $Pl_{\{T\}}(T)=1$, $Pl_{\{H\}}(H)=3/7$:
$$
m(H) = 4/7, \quad m(T) = 0, \quad m(\Omega) = 3/7
$$
**(p.126)** corresponding to credal set $Bel = \{4/7\le p\le 1\}$. **Note** $p=1$ excluded since $n(T)=3$. So the BF is on $\Omega=\{H,T\}$.

**Cuzzolin's takeaway (p.127):** Bayesian inference on a continuous $\Theta=[0,1]$ produces a continuous distribution; in opposition, MAP/MLE collapse to a single point. *Both likelihood-based and Dempster-Shafer-based BF inference produce a BF on $\Theta$ — corresponding to an entire convex set of second-order distributions* (more cautious than general Bayesian). MLE-based delivery a *single parameter* value, corresponding to a single PDF.

## 4.2 Measuring uncertainty

Two threads: order relations (partial ordering of information content), and entropy generalisations.

### 4.2.1 Order relations *(pp.127-128)*

**Definition 43 (pl-more committed, p.127).** $m_1\sqsubseteq_{pl} m_2$ iff $Pl_1(A)\le Pl_2(A)$ for all $A$.

Weak inclusion $\sqsubseteq_{bel}$ (3.9) is strictly related: $Pl_1\le Pl_2 \iff Bel_2 \le Bel_1$.

**Definition 44 (q-more committed, p.128).** $m_1 \sqsubseteq_q m_2$ iff $Q_1(A)\le Q_2(A)$ for all $A$. Both pl- and q-orderings extend set inclusion: for categorical BFs, $m_A\sqsubseteq_{pl}m_B \iff m_A\sqsubseteq_q m_B \iff A\subseteq B$. Greatest element in both is the vacuous mass.

**Definition 45 (specialisation, p.128).** $m_1\sqsubseteq_S m_2$ if $m_1$ obtainable from $m_2$ by redistributing mass $m_2(B)$ to subsets of $B$:
$$
m_1(A) = \sum_{B\subseteq\Theta} S(A,B)\, m_2(B)
$$
$S = [S(A,B):A,B\subseteq\Theta]$ is the *specialisation matrix*. Implies pl- and q-commitment: $m_1\sqsubseteq_S m_2 \Rightarrow m_1\sqsubseteq_{pl}m_2 \wedge m_1\sqsubseteq_q m_2$.

### 4.2.2 Measures of entropy *(pp.128-131)*

Generalisations of Shannon entropy $H_s[P] = -\sum_x P(x)\log P(x)$ (Eq. 4.8):

| Name | Formula | Eq | Notes |
|------|---------|----|-------|
| Nguyen | $H_n[m] = -\sum_A m(A)\log m(A)$ | 4.9 | Direct Shannon on mass |
| Yager | $H_y[m] = -\sum_A m(A)\log Pl(A)$ | 4.10 | Zero on consonant/consistent BFs |
| Hohle | $H_o[m] = -\sum_A m(A)\log Bel(A)$ | 4.11 | Dual of Yager |
| Dubois-Prade | $H_d[m] = \sum_A m(A)\log|A|$ | 4.12 | Hartley generalisation, non-specificity |
| Pal | $H_a[m] = \sum_A m(A)/|A|$ | — | Pignistic-related |
| Smets (commonality) | $H_t = \sum_A \log(1/Q(A))$ | 4.13 | Q-based |
| Klir-Ramer global | $H_k[m] = D[m] + H_d[m]$ | 4.14 | Discord + non-specificity |
| Pal et al. | $H_p = \sum_A m(A)\log(|A|/m(A))$ | 4.15 | Composite, addresses subadditivity |
| Harmanec-Klir AU | $H_h[m] = \max_{P\in\mathcal{P}[Bel]} H_s(P)$ | 4.16 | Max Shannon over consistent probabilities |
| Maeda-Ichihashi | $H_i[m] = H_h[m] + H_d[m]$ | 4.17 | Aggregated + non-specificity |
| Jousselme ambiguity | $H_j[m] = H_s[BetP[m]]$ | 4.18 | Pignistic Shannon |
| Deng | $H_e[m] = \sum_A m(A)\log\bigl((2^{|A|}-1)/m(A)\bigr)$ | 4.19 | Generalised Shannon |

Discord component:
$$
D(m) = -\sum_A m(A)\log\Bigl[\sum_{B} m(B)\frac{|A\cap B|}{|B|}\Bigr]
$$

**Klir-Ramer critique of Yager:** Yager's $H_y$ takes $A\cap B = \emptyset$ as conflict, but should consider $B\not\subseteq A$. **Vejnarova [1853]:** discord/total uncertainty don't satisfy subadditivity. **Pal et al. [1379]:** composite measures don't admit unique max, no rationale for adding conflict + non-specificity, expensive.

**Jirousek-Shenoy ([909], 2016) summary properties (p.131):** non-negativity, max entropy on vacuous, monotonicity in $|\Theta|$, probability consistency ($H[m]=H_s[p]$ when $m$ is Bayesian), additivity over Dempster sum. Only the **Maeda-Ichihashi proposal (4.17)** satisfies all.

### 4.2.3 Principles of uncertainty *(p.132)*

- **Maximum entropy principle** (Jaynes [888]).
- **Principle of insufficient reason** (PIR, Laplace [1096]): if no info about $k$ alternatives, assign $1/k$.
- **Definition 46 — least commitment principle (p.132):** "When several BFs are compatible with a set of constraints, the least informative (per some informational ordering) should be selected, if such a BF exists."
- Both MEP and least-commitment are *principles of maximum uncertainty* [984].
- **Minimum specificity principle (Dubois-Prade, p.133):** for a focal element $A$ with cardinality $|A|$ or any decreasing $f(|A|)$, the *measure of specificity* is $f(Bel) = \sum_{A\subseteq\Theta} m(A)f(|A|)$ (Eq. 4.20). Min-specificity prescribes selecting the BF with minimal $f(Bel)$ from a candidate collection. It motivates a combination rule that does *not* presuppose source independence.
- **Minimum description length (Rissanen 1978, [1489], p.133):** the best hypothesis (model+parameters) is the one yielding shortest data encoding. MDL is closely related to maximum entropy.

## 4.3 Combination *(pp.133-160)*

§4.3 reviews aggregation operators for BFs, beginning from Dempster's original orthogonal sum and proceeding through every published alternative. A hierarchy from least to most conservative is identified.

### 4.3.1 Dempster's rule under fire *(pp.133-138)*

Several authors have questioned whether Dempster's rule [414] is truly canonical. Smets [1719] tried to formalise *distinct evidence* combined by orthogonal sum. Walley [1873] characterised the class of BFs for which independent statistical observations can be combined by Dempster's rule and those for which it is consistent with Bayes. Cinicioglu and Shenoy [287] gave a comparison. Seidenfeld [1571] objected on statistical-inference grounds, arguing that Dempster's rule is *inferior to conditioning*.

**Example 11 — Zadeh's counter-example *(p.134)*.** $\Theta=\{M,C,T\}$ (meningitis, concussion, tumour); two doctors:
$$
m_1(M)=0.99,\, m_1(C)=0.01; \qquad m_2(T)=0.99,\, m_2(C)=0.01.
$$
**(Eq. 4.21, p.134).** Unnormalised Dempster combination: $m(\emptyset)=0.9999$, $m(C)=0.0001$. After normalisation, $C$ gets *categorical* belief — a strong claim that disagrees with both experts (who allowed only 1% to $C$). **Yager 1983 [2002]** suggested introducing a 'hedging' element. **Haenni [766]** counter-argued the example arises from a poorly defined frame: tumour and meningitis are not exclusive, and a 'frame of discernment' is misleading. The fix: discount each expert's reliability via $\Theta_i = \{R_i, U_i\}\times\Theta$ then marginalise.

**Dubois & Prade's analysis (1985, [525], p.135):** Dempster's rule's behaviour in cases of small conflict can lead to a *zero value* for hypotheses that experts deem 'highly improbable' but not 'impossible'. Translates to a need for discounting. Eventually [532], they concluded the Dempster-pooling justification is problematic and proposed the **minimum-specificity rule** (§4.3.2, Eq. 4.24).

**Example 12 — Lemmer's counter-example *(p.136)*** [1133]. Balls in an urn each with one true label. Sensors $s$ produce BPAs $m_s(A)$ = fraction of balls labelled $A$. *Voorbraak [1860] counter:* DS theory generalises Bayesian probability theory whereas Lemmer's sample-space interpretation generalises classical probability theory — different framings. Voorbraak's own counter-intuitive: $\Theta=\{a,b,c\}$, $m(\{a\})=m(\{b,c\})=m'(\{a,b\})=m'(\{c\})=0.5$ gives $m\oplus m'(\{a\})=m\oplus m'(\{b\})=m\oplus m'(\{c\})=1/3$ — mass to $\{b\}$ which never received explicit support.

**Axiomatic justifications.** Klawonn-Schwecke [974, 975] gave axioms uniquely determining Dempster's rule, and showed Dempster *conditioning* is the least committed specialisation. Dempster *combination* arises from commutativity. Liu [1199] argued counter-intuitive results stem from overlooking different independence conditions. Wilson [1943] gave another axiomatic approach:

### Definition 47 *(p.137)*
A combination rule $\pi: s\mapsto P^s : \Omega^s\to[0,1]$ over collections of random sets *respects contradictions* if $\Gamma(\omega)=\bigcap_i\Gamma_i(\omega_i)=\emptyset \Rightarrow P^s(\omega)=0$.

### Definition 48 *(p.137)*
Combination rule $\pi$ *respects zero probabilities* if $P_i(\omega_i)=0$ for some $i$ implies $P^s(\omega)=0$.

In [1943] Dempster's rule is claimed (without proof) to be the unique combination rule respecting contradictions and zero probabilities under two extra assumptions.

**Example 13 — Dezert-Tchamova paradox (2012, [498], p.138).** $\Theta=\{M,C,T\}$:
$$
m_1(\{M\})=a,\, m_1(\{M,C\})=1-a; \qquad m_2(\{M,C\})=b_1,\, m_2(\Theta)=b_2,\, m_2(\{T\})=1-b_1-b_2.
$$
**(Eq. 4.22, p.138).** Dempster combination yields $m_1\oplus m_2 = m_1$ — Doctor 2's diagnosis is *completely absorbed* by Doctor 1. The 'paradox' is not a conflict consequence — Doctor 2 has no veto power even on compatible events. Cuzzolin reads this as 'absorptive' behaviour requiring further theoretical attention.

**Other criticisms.** Josang & Pope (2012, [923]) showed Dempster's rule is *not* a generalisation of Bayes' rule with simple-example counter; introduced subjective-logic combination. Wang [1891] argued subjective probability functions are special BFs for which Dempster's rule is inconsistent. Smets [1728] argued objections are due to misuse, not to the rule. Liu-Hong [1201] found Dempster's evidence-combination idea richer than the rule itself. Bhattacharya [148] analysed non-hierarchical aggregation. Tchamova et al. [2072] proposed having all experts decide on the same focused collection. Hau et al. [809] showed orthogonal sum is not robust under high conflict; modified rule proposed.

### 4.3.2 Alternative combination rules *(pp.138-149)*

**Yager's rule (1987, [2009]) *(p.139)*.** Conflicting mass $m_\cap(\emptyset)$ is reassigned to $\Theta$:
$$
m_Y(A) = \begin{cases} m_\cap(A) & \emptyset\neq A\subsetneq\Theta\\ m_\cap(\Theta)+m_\cap(\emptyset) & A=\Theta\end{cases}
$$
**(Eq. 4.23, p.139).** Rationale: conflict comes from non-reliable sources, so its mass should reflect ignorance. Yager 1984 [2003] earlier had alternative based on linguistic-quantifier compatibility. Yager [2006] also discussed the *entailment principle* extended to DS-granules (mixtures of possibilistic and probabilistic information).

**Dubois-Prade min-specificity rule [532] *(p.140)*.** When focal elements $B,C$ don't intersect, assign their product mass to $B\cup C$:
$$
m_D(A) = m_\cap(A) + \!\!\!\sum_{\substack{B\cup C=A\\ B\cap C=\emptyset}} m_1(B)m_2(C)
$$
**(Eq. 4.24, p.140).** Resulting BF dominates Yager's.

**Smets's conjunctive rule (TBM) *(p.140)*.** Leave the conflicting mass on $\emptyset$ (open-world):
$$
m_{\,\bigcirc\,}(A) = \begin{cases} m_\cap(A) & \emptyset\neq A\subseteq\Theta\\ m_\cap(\emptyset) & A=\emptyset\end{cases}
$$
**(Eq. 4.25, p.140).** Applicable to *unnormalised* BFs. Same idea predates Smets ([2009] Yager; Hau-Kashyap [808]; Yamada [2034] 'combination by exclusion').

**Disjunctive rule (Smets) *(p.140)*.** Take *union* of supported propositions for consensus:
$$
m_{\,\bigcup\,}(A) = \sum_{B\cup C = A} m_1(B)m_2(C)
$$
**(Eq. 4.26, p.140).** Under disjunctive combination, $Bel_1\,\bigcup\,Bel_2(A) = Bel_1(A)\cdot Bel_2(A)$ — multiplicative on belief. Dual to conjunctive rule (Kramosil [1056]). Yamada [2034] called it 'combination by union'.

**Denoeux's cautious rule [455, 451] *(pp.141-142)*.**

### Definition 49 *(p.141)*
For non-dogmatic BPAs $m_1,m_2$, the *cautious (conjunctive) rule* $m_1\,\,⃝\!\!\wedge\,\,m_2$ is the BPA with weight function
$$
w_{1\,⃝\wedge 2}(A) = w_1(A)\wedge w_2(A) \doteq \min\{w_1(A),w_2(A)\}, \quad A\in 2^\Theta\setminus\{\Theta\}
$$
**(Eq. 4.27, p.141).** The cautious operator is commutative, associative, *idempotent* — suitable for combining reliable but possibly overlapping evidence. Cautious combination yields the $w$-least committed BF in $S_w(m_1)\cap S_w(m_2)$.

A **normalised cautious rule** can be defined by replacing the conjunctive combination by Dempster's rule [455]. Destercke et al. [487] supported a *different* cautious conjunctive rule based on maximising expected cardinality.

**Bold disjunctive rule.** Dual of cautious. For unnormalised BPA $m$, complement $\overline{m}(A)=m(A^c)$ is also non-dogmatic; canonical disjunctive decomposition (Proposition 26):
$$
m = \,\bigcup\,_{A\neq\emptyset} m_{A,v(A)}
$$
**(Eq. 4.28, p.141).** $m_{A,v(A)}$ assigns $v(A)$ to $\emptyset$ and $1-v(A)$ to $A$.

### Definition 50 *(p.142)*
The bold disjunctive combination $m_1\,\,⃝\!\!\vee\,\,m_2$ uses disjunctive weight $v_{1\,⃝\vee 2}(A)=v_1(A)\wedge v_2(A)$:
$$
m_1\,\,⃝\!\!\vee\,\,m_2 = \,\bigcup\,_{A\neq\emptyset} m_{A,v_1(A)\wedge v_2(A)}
$$
**(Eq. 4.29, p.142).** Restricted to unnormalised BFs.

Pichon-Denoeux [1428] noted cautious + unnormalised-Dempster are least-committed members of *triangular-norm* and *uninorm* families respectively. Cuzzolin-Adaptive: cautious-adaptive rule from Florea et al. [600] uses generalised discounting on separable BPAs.

**Josang's consensus operator [915] *(p.142)*.** Operates on *opinion tuples* not on full BFs. Relative atomicity $a(A/B)=|A\cap B|/|B|$.

### Definition 51 *(p.142)*
An *opinion* on $A$ is $o = (b(A)\doteq Bel(A), d(A)\doteq 1-Pl(A), u(A)\doteq Pl(A)-Bel(A), a(A)\doteq a(A/\Theta))$. Consensus combination $o_1\oplus o_2$:
$$
o_1\oplus o_2 = \begin{cases} \bigl(\frac{b_1u_2+b_2u_1}{\kappa},\frac{d_1u_2+d_2u_1}{\kappa},\frac{u_1u_2}{\kappa},\frac{a_1u_2+a_2u_1-(a_1+a_2)u_1u_2}{u_1+u_2-2u_1u_2}\bigr) & \kappa\neq 0\\ \bigl(\frac{\gamma b_1+b_2}{\gamma+1},\frac{\gamma d_1+d_2}{\gamma+1},0,\frac{\gamma a_1+a_2}{\gamma+1}\bigr) & \kappa=0\end{cases}
$$
**(Eq. 4.30, p.143)** with $\kappa = u_1+u_2-u_1u_2$, $\gamma=u_2/u_1$. Derived from posterior combination of beta distributions; $b+d+u=1$. Operates on lower/upper probabilities, not on BFs proper.

**Josang's cumulative and averaging rules [920].** Generalisations of consensus to independent and dependent opinions; bijection with Dirichlet posterior updating / averaging.

**Averaging and distance-based methods.** Murphy [1328]: average masses, then Dempster-combine the average $n$ times. Deng et al. [2071, 1159, 438]: weighted average based on credibility $Crd(m_i) = Sup(m_i)/\sum_j Sup(m_j)$ where $Sup(m_i)=\sum_{j\neq i}1-d(m_i,m_j)$, then Dempster $n-1$ times. Du et al. [516], [2059], [1974], [656] (eigenvector of evidence-support matrix), [655] (conflict-weighted) are similar variants. These dampen Dempster's 'veto' problem heuristically.

**Surveys.** Josang-Daniel [919] compared dogmatic-belief strategies. Wang et al. [1903] proposed 'logically correct' combination optimising normalisation jointly. Yamada [2034] proposed 'combination by compromise'. Yager [2016] proposed *prioritised belief structures* — $m_1$ has priority over $m_2$ if $m_2$ may only enhance, not alter, $m_1$. Janez-Appriou [885, 884] studied combination on *non-exhaustive* frames via *deconditioning*. Dubuisson [2044] introduced *weighted belief distributions* (WBDs). Florea et al. [631] introduced **adaptive combination rules (ACRs)**:
$$
m_{\rm ACR}(A) = \alpha(\kappa) m_{\,\bigcup\,}(A) + \beta(\kappa) m_{\,\bigcirc\,}(A)
$$
**(Eq. 4.31, p.145)** plus the *proportional conflict redistribution (PCR)* family redistributing conflict to non-empty involved sets.

**Idempotent fusion (Destercke-Dubois [484, 483]):** when source dependencies are unknown, idempotence is desirable. They concluded extending possibility theory's 'min' rule to BFs requires accepting that fusion output may be a *family* of BFs.

**Joshi's rule [925] *(p.146)*.**
$$
m(A) = \begin{cases} (1+\kappa)\sum_{B\cap C=A}m_1(B)m_2(C) & A\neq\Theta\\ 1-\sum_{X\subseteq\Theta}m(X) & A=\Theta\end{cases}
$$
**(Eq. 4.32, p.146)** — ignorance proportional to conflict; reduces to Dempster's when $\kappa=0$.

**Logic-based belief revision (Ma et al. [1227, 1226]):** revision is asymmetric; their rule reduces to Dempster's under strong consistency, and generalises Jeffrey's, Dempster's conditioning, and AGM revision [26].

### 4.3.3 Families of combination rules *(pp.147-149)*

**Lefevre family parameterised by weights [1118]:**
$$
m(A) = m_\cap(A) + m^c(A), \quad m^c(A) = \begin{cases} w(A,\mathbf{m})\cdot m_\cap(\emptyset) & A\in\mathcal{P}\\ 0 & \text{otherwise}\end{cases}
$$
**(Eq. 4.33, p.147)** with $\sum w = 1$. Subsumes Smets ($\mathcal{P}=\{\emptyset\}$), Yager ($\mathcal{P}=\{\Theta\}$), Dempster ($\mathcal{P}=2^\Theta\setminus\{\emptyset\}$, weights $m_\cap(A)/(1-m_\cap(\emptyset))$), Dubois-Prade.

**Denoeux's t-norm/t-conorm families [455] *(pp.148-149)*.** A *t-norm* $\top$ is commutative associative monotone with $x\top 1=x$; a *t-conorm* $\perp$ has $x\perp 0=x$. For non-dogmatic BFs, conjunctive combination satisfies $w^c_{1\,\bigcirc\,2}(A) = w_1^c(A)\cdot w_2^c(A)$ (Eq. 4.34, p.148) where $w^c_1(A) = 1\wedge w(A)$. New rules:
$$
m_1\circledast_{\top,\perp} m_2 = \,⃝\!\bigcap_{A\subset\Theta} m_A^{w_1(A)*_{\top,\perp}w_2(A)}
$$
**(Eq. 4.35, p.149)** with $x*_{\top,\perp} y = x\top y$ for $x\vee y\le 1$, $x\wedge y$ if $x\vee y>1, x\wedge y\le 1$, else $(1/x \perp 1/y)^{-1}$. Cautious rule corresponds to $\circledast_{\wedge,\vee}$.

**$\alpha$-junctions (Smets [1720]) *(p.149)*.** Associative, commutative, linear operators with neutral element. Linear stochastic-matrix representation $\mathbf{m}_{12} = K_{m_1}\mathbf{m}_2$, $K_{m_1}=\sum_A m_1(A)K_A$. Smets [1720] proved $K_A$ depends only on $\mathbf{m}_{\rm vac}\in\{\mathbf{m}_\Theta, \mathbf{m}_\emptyset\}$ and $\alpha\in[0,1]$. Pichon [1429] showed $\alpha$-junctions correspond to particular knowledge about source truthfulness.

**Wen [1925]:** unified random-set formulation encompassing all classical rules.

### 4.3.4 Combination of dependent evidence *(p.150)*

Smets [1719] explored 'distinct evidence'. Kramosil [1054] showed Dempster-analogue exists for a class of probability measures without statistical-independence assumption, using non-standard Boolean structures. Cattaneo [236, 1309] proposed least-specific monotone-conflict-minimising rules; later [1309] introduced two rules with no independence assumptions, based on cautious combinations of plausibility and commonality. Yager [2023]: weighted aggregation with weights related to dependence. Fu-Yang [649] *cautious conjunctive rule* (CCR): split canonical decomposition weights into positive/negative, build new partial ordering. Su et al. [1775] used common-information-significance.

### 4.3.5 Combination of conflicting evidence *(pp.151-155)*

**Liu's measure of conflict [1196] *(p.151)*.**
### Definition 52 *(p.151)*
$cf(m_1,m_2) = \langle m_\cap(\emptyset),\, difBetP^{m_2}_{m_1}\rangle$ (Eq. 4.37) where $difBetP^{m_2}_{m_1} = \max_{A\subseteq\Theta}|BetP[m_1](A)-BetP[m_2](A)|$ is the pignistic-betting-commitment distance. $m_1, m_2$ are *in conflict* iff *both* $difBetP > \epsilon$ and $m_\cap(\emptyset)>\epsilon$.

**Conflict as distance.** George-Pal [677] axioms; Martin et al. [1251, 1249] argued against $m_\cap(\emptyset)$ as conflict measure, proposed weighted distance.

**Internal vs external conflict (Daniel [384, 388, 386]).** Internal conflict: between focal elements *of one* BF. External: between BFs. Schubert [1561] decomposed BF into generalised simple support functions (GSSFs) and computed internal conflict as Dempster combination of all GSSFs except $\emptyset$-supporting one.

**Redistribution approaches.** Lefevre et al. [1120]; Daniel's *minC* operator [381]; Martin [1253] proportional-conflict redistribution within Dezert-Smarandache theory; Xu et al. [1981] grey-relational analysis.

**Other conflict resolution.** Sloman [1488] showed normalisation constant ties to prior; Schubert *metaconflict function* [1543, 1546, 1547, 1549]; Ray-Krantz [1465] schemata weighting; Zhang [2109] two algorithms with/without prior; Campos-Cavalcante [217]:
$$
m_1 \Psi m_2 (A) = \frac{Z\cdot \sum_{B\cap C=A}m_1(B)m_2(C)}{1+\log(1/\kappa)}
$$
**(Eq. 4.38, p.153)** with $\kappa = \sum_{B\cap C=\emptyset}m_1m_2$, $Z$ normaliser. Guan [748], Lefevre-Eleouedi [1123, 1122] (preserving conflict via dissimilarity), [2046] coherence-based.

### 4.3.6 Combination of (un)reliable sources: Discounting *(pp.154-155)*

**Discounting (Shafer [1583]) *(p.154)*.** Reserve mass $\alpha$ to $\Theta$, normalise rest:
$$
m^\alpha(\Theta) = \alpha + (1-\alpha)m(\Theta), \qquad m^\alpha(A) = (1-\alpha)m(A) \,\,\forall A\subsetneq\Theta
$$
**(Eq. 4.39, p.154).** Formal alternative [1282]: conjunctive combination with a frame $\mathcal{R}=\{\text{reliable},\text{unreliable}\}$ on $\Theta\times\mathcal{R}$. Note Guan et al. [742] showed discounting does *not* commute with orthogonal sum.

**Reliability assessment.** Elouedi et al. [572]: minimise pignistic-distance between discounted and original BFs. Liu [658] dissimilarity-distance + pignistic-conflict. Klein [976] *dissent measure* — compare each source vs the average. Delmotte et al. [410]: estimate discount factors from inter-source conflict.

**Generalisations of discounting.** *De-discounting* (Denoeux-Smets [475]): inverse of discounting,
$$
m = \frac{m^\alpha - m_\Theta}{1-\alpha}
$$
**(Eq. 4.40, p.155).**

*Contextual discounting* (Mercier et al. [1286, 1287]): discount-rate *vector*, not scalar — different rates conditioned on different hypotheses. Extensions [1284, 1285] link to canonical disjunctive decomposition. Pichon et al. [1252]: correction handling source truthfulness as well as relevance. Smarandache [1666]: *importances* as distinct from reliabilities. Haenni [768]: partially reliable sources. Zhu-Basir [2123]: discount rate outside $[0,1]$ — does both discounting and de-discounting.

## 4.4 Belief versus Bayesian reasoning: A data fusion example *(pp.156-158)*

Classical multi-sensor object-classification setup: train per-feature likelihood $p(x_i|y)$ from data; observe $n$ feature measurements $x_1,\dots,x_n$.

**Bayesian fusion** assumes conditional independence:
$$
p(y|\mathbf{x}) \propto p(\mathbf{x}|y) = \prod_i p(x_i|y)
$$
under uniform priors, applied via Bayes' rule.

**Belief-function fusion.** For each feature $i$, learn a BF $Bel(Y|x_i)$ by likelihood-based method (§4.1.1). Combine via $\,⃝\!\bigcap\,$, $\oplus$, or $\,⃝\!\bigcup\,$:
$$
Bel(Y|\mathbf{x}) = Bel(Y|x_1)\odot\cdots\odot Bel(Y|x_n)
$$

### 4.4.2 Inference under partially reliable data *(pp.157-158)*

Two sensors $x_1, x_2$, sensor 2 wrong (reliable 80% of time): normalised likelihoods $p(x_1|Y)=0.9, p(x_1|N)=0.1, p(x_2|Y)=0.1, p(x_2|N)=0.9$ **(Eq. 4.41, p.157)**.

- *Bayesian fusion:* assuming conditional independence, $p(Y|x_1,x_2)=p(N|x_1,x_2)=1/2$ — **completely uninformative** (Eq. 4.42, p.158).
- *Discounted BFs* with $\alpha=0.2$: $m(Y|x_1)=0.72, m(N|x_1)=0.08, m(\Theta|x_1)=0.2$ etc., then Dempster: $m(Y|x_1,x_2)=0.458, m(N|x_1,x_2)=0.458, m(\Theta|x_1,x_2)=0.084$ **(Eq. 4.43)**.
- *Disjunctive rule (least committed):* $m'(Y)=0.09, m'(N)=0.09, m'(\Theta)=0.82$ **(Eq. 4.44)**.

The credal set induced by $Bel$ is *narrow* (sensor reliability was estimated 80%, half were faulty); disjunctive credal set is wider and more cautious.

## 4.5 Conditioning *(pp.159-164)*

### 4.5.1 Dempster conditioning *(p.159)*

Conditioning by Dempster's rule on a 'logical' BF $Bel_B$ (mass 1 on $B$):
$$
Bel_\oplus(A|B) = \frac{Bel(A\cup\bar B) - Bel(\bar B)}{1-Bel(\bar B)} = \frac{Pl(B)-Pl(B\setminus A)}{Pl(B)}, \quad Pl_\oplus(A|B) = \frac{Pl(A\cap B)}{Pl(B)}
$$
**(Eq. 4.45, p.159).** "Bayes' rule applied to plausibility values rather than probability."

### 4.5.2 Lower and upper conditional envelopes (Fagin-Halpern [584]) *(p.160)*
$$
Bel_{\rm Cr}(A|B) = \inf_{P\in\mathcal{P}[Bel]} P(A|B), \qquad Pl_{\rm Cr}(A|B) = \sup_{P\in\mathcal{P}[Bel]} P(A|B)
$$
**(Eq. 4.46, p.160).** Closed forms:
$$
Bel_{\rm Cr}(A|B) = \frac{Bel(A\cap B)}{Bel(A\cap B)+Pl(\bar A\cap B)}, \qquad Pl_{\rm Cr}(A|B) = \frac{Pl(A\cap B)}{Pl(A\cap B)+Bel(\bar A\cap B)}
$$
**(Eq. 4.47, p.160).** More conservative than Dempster: $Bel_{\rm Cr}\le Bel_\oplus \le Pl_\oplus \le Pl_{\rm Cr}$. Fagin-Halpern argue Dempster behaves unreasonably in three-prisoners example (Diaconis [499]).

### 4.5.3 Suppes-Zanotti geometric conditioning *(p.161)*

Distinguishes *focusing* (no new info; specialise to $B$) from *revision* (new info modifies state). Geometric (focusing):
$$
Bel_{\rm G}(A|B) = \frac{Bel(A\cap B)}{Bel(B)}, \qquad Pl_{\rm G}(A|B) = \frac{Bel(B)-Bel(B\setminus A)}{Bel(B)}
$$
**(Eq. 4.48, p.161).** Smets proved this via Pearl's 'probability of provability' [1405]. Dual to Dempster conditioning: replace probability values with *belief* values in Bayes' rule.

### 4.5.4 Smets's conjunctive (TBM) rule of conditioning *(pp.161-162)*

Belief revision: combine $Bel$ with logical $Bel_B$ via the conjunctive rule:
$$
m_{\,\bigcirc\,}(A|B) = \begin{cases} \sum_{X\subseteq B^c} m(A\cup X) & A\subseteq B\\ 0 & A\not\subseteq B\end{cases}
$$
**(Eq. 4.49, p.162).** Belief and plausibility:
$$
Bel_{\,\bigcirc\,}(A|B) = \begin{cases} Bel(A\cup\bar B) & A\cap B\neq\emptyset\\ 0 & A\cap B=\emptyset\end{cases}, \quad Pl_{\,\bigcirc\,}(A|B) = \begin{cases} Pl(A\cap B) & A\not\supset B\\ 1 & A\supset B\end{cases}
$$
Conjunctive conditioning is *more committal* than Dempster: $Bel_\oplus(A|B)\le Bel_{\,\bigcirc\,}(A|B)\le Pl_{\,\bigcirc\,}(A|B)\le Pl_\oplus(A|B)$. Klawonn [975]: $Bel_{\,\bigcirc\,}$ is the minimum-commitment specialisation of $Bel$ such that $Pl(B^c|B)=0$.

### 4.5.5 Disjunctive rule of conditioning *(p.162)*

Dual:
$$
m_{\,\bigcup\,}(A|B) = \sum_{X\subseteq B} m(A\setminus B\cup X) \quad A\supseteq B
$$
**(p.162).** Belief: $Bel_{\,\bigcup\,}(A|B) = Bel(A)$ if $A\supset B$ else 0. Plausibility: $Pl_{\,\bigcup\,}(A|B) = Pl(A)$ if $A\cap B=\emptyset$ else 1. Disjunctive is *less* committal than Dempster and credal: $Bel_{\,\bigcup\,}\le Bel_{\rm Cr}\le Pl_{\rm Cr}\le Pl_{\,\bigcup\,}$.

### 4.5.6 Spies's equivalence-class conditioning [1749] *(p.163)*

Conditional events $[B|A]$ as sets of equivalent events under conditioning relation: $A\triangle B = (A\cap\bar B)\cup(\bar A\cap B)$ symmetric difference.

**Lemma 1 *(p.163)*.** If $\exists Z$ with $B,C\in Z\triangle\mathcal{N}(P_A)$, then $P(B|A)=P(C|A)$.

### Definition 53 *(p.163)*
$[B|A] = B\triangle\mathcal{N}(P_A) = \{C: A\cap B\subseteq C\subseteq \bar A\cup B\}$.

### Definition 54 *(p.163)*
Conditional BF given $B$:
$$
Bel([C|B]) = P(\{\omega: \Gamma_B(\omega)=[C|B]\}) = \frac{1}{K}\sum_{A\in[C|B]} m(A)
$$
A 'second-order' BF on collections of focal elements. Closed under Dempster's rule. Slobodova [1662, 1661]: multivalued extension; valuation-based systems.

### 4.5.8 Conditioning summary *(p.164)*

**Table 4.1** lists belief/plausibility values for each operator (Dempster, Credal, Geometric, Conjunctive, Disjunctive). They form a **nested family**:
$$
Bel_{\,\bigcup\,}(\cdot|B)\le Bel_{\rm Cr}(\cdot|B)\le Bel_\oplus(\cdot|B)\le Bel_{\,\bigcirc\,}(\cdot|B)\le Pl_{\,\bigcirc\,}(\cdot|B)\le Pl_\oplus(\cdot|B)\le Pl_{\rm Cr}(\cdot|B)\le Pl_{\,\bigcup\,}(\cdot|B)
$$
**(p.164).** This argues for reasoning with *intervals* of BFs.

**Open question (p.164):** Is geometric conditioning induced by some combination rule dual to Dempster's, and how does it fit this picture?

## 4.6 Manipulating (conditional) belief functions *(pp.165-176)*

### 4.6.1 Generalised Bayes Theorem (GBT, Smets [1718, 1725]) *(pp.165-166)*

Input: family of conditional BFs $Bel_\mathbb{X}(X|\theta)$ on $\mathbb{X}$ (one per parameter value $\theta$). Output: $Bel_\Theta(A|X)$ family parameterised by sets $X\subset\mathbb{X}$.

Procedure:
1. $Bel_\mathbb{X}(X|A) = \,⃝\!\bigcup\,_{\theta\in A} Bel_\mathbb{X}(X|\theta) = \prod_{\theta\in A} Bel_\mathbb{X}(X|\theta)$ — disjunctive combination over parameter set $A$ **(Eq. 4.50, p.165)**.
2. $Pl_\Theta(A|X) = Pl_\mathbb{X}(X|A)$, so $Bel_\Theta(A|X) = \prod_{\theta\in\bar A} Bel_\mathbb{X}(\bar X|\theta)$.

**Axiom 1 (p.166):** $Bel_\Theta(A|X,Y) = Bel_\Theta(A|X)\,⃝\!\bigcap\, Bel_\Theta(A|Y)$.
**Axiom 2 (p.166):** $Pl_\mathbb{X}(X|A)$ is a function of $\{Pl_\mathbb{X}(X|\theta), Pl_\mathbb{X}(\bar X|\theta): \theta\in A\}$.

GBT generalises Bayes by replacing $P$ with $Pl$ when priors are uniform. Under Axiom 1, variables are *conditional cognitive independent*. Shafer's likelihood inference $Pl_\Theta(A|x)=\max_{\theta\in A} Pl_\Theta(\theta|x)$ does *not* satisfy Axiom 1.

### 4.6.2 Generalising total probability *(pp.167-169)*

**Law of total probability (Jeffrey's rule):** $P''(A) = \sum_{B\in\mathbb{B}} P(A|B)P'(B)$ **(Eq. 4.51, p.167)** — the unique solution.

**Spies's generalisation.** Partition $\Pi=\{B_1,\dots,B_n\}$, conditional masses $m_1,\dots,m_n$ on each $B_i$, unconditional mass $m$ on coarsening.

**Proposition 27 *(p.167)*.** The BF
$$
Bel_{\rm tot}(A) = \sum_{C\subseteq A}\bigl(m\oplus \bigoplus_i m_{B_i}\bigr)(C)
$$
**(Eq. 4.52, p.167)** has marginals $Bel_{\rm tot}(\cdot|B_i)=Bel_i$ and reduces to Jeffrey when probabilities. Uniqueness discussed in §17.1.3.

**Smets's Jeffrey-like rules.** Let $B(A)$ = smallest element of $\mathbb{B}$ containing $A$, $\mathcal{B}(A)$ = $A$s sharing same $B(A)$. Required:
$$
\frac{Bel''(X)}{Bel''(Y)} = \begin{cases} Bel(X|B)/Bel(Y|B) & Bel(Y|B)>0\\ 0 & Bel(Y|B)=0\end{cases}
$$
**(Eq. 4.53, p.168).** Plug in geometric or Dempster conditioning to get:
- *Jeffrey-Geometric:* $m_{JG}(A) = \frac{m(A)}{\sum_{X\in\mathcal{B}(A)}m(X)} m'(B(A))$.
- *Jeffrey-Dempster:* $m_{JD}(A) = \frac{m(A|B(A))}{\sum_{X\in\mathcal{B}(A)}m(X|B(A))} m'(B(A))$.

Reduces to geometric/Dempster conditioning when $m'(B)=1$ on a single $Bel$.

**Ruspini [1514]:** approximate deduction; conditional knowledge as numeric intervals; integrate unconditional and conditional estimates.

### 4.6.3 Multivariate belief functions *(pp.169-170)*

Cartesian product frames $\Theta_X\otimes\Theta_Y = \Theta_X\times\Theta_Y$. Marginalisation:
$$
m^{XY\downarrow X}(B) = \sum_{\{A\subseteq\Theta_{XY}: A\downarrow\Theta_X = B\}} m^{XY}(A)
$$
**(p.169).** Vacuous extension is the inverse: $m^{X\uparrow XY}(A) = m^X(B)$ if $A=B\times\Omega_Y$, else 0. Closely tied to *graphical models*. **Belief-function factorisation** (Kong [1033] hypergraphs; Shafer-Shenoy-Mellouli local propagation [1611, 1609, 1631]; Almond's BELIEF software [32]; Thoma [1813]; Kong on Markov trees [1987]).

### 4.6.4 Graphical models *(pp.171-176)*

**Probabilistic graphical models** (Pearl [1398], Lauritzen [1101], Spiegelhalter [1410]): DAG, $p_X(x) = \prod_v p(x_v | x_{pa(v)})$ **(Eq. 4.54, p.171).** Belief propagation by message passing.

**Graphical models for BFs.** Hypertrees (Cobb-Shenoy [291]); qualitative Markov trees [1611, 65]; join trees [1628]; valuation networks [1626]. **Evidential networks with conditional BFs (ENCs)** [1995] use Smets's GBT for propagation. **Directed evidential networks (DEVNs)** [116, 113] generalise ENCs to multi-parent relations.

**DEVN propagation (Ben Yaghlane-Mellouli):** for each conditional pair $(v,u)$, compute posterior via disjunctive combination + GBT:
$$
Bel^v = Bel_0^v\oplus Bel_{u\to v}, \quad Bel_{u\to v}(A) = \sum_{B\subseteq\Theta_u} m_0^u(B) Bel^v(A|B)
$$

**Algorithm 2 (DEVN initialisation, p.174)** and **Algorithm 3 (DEVN updating, p.174):** $\pi$ values from parents propagate down, $\lambda$ values from children up; $Bel_v = \pi_v\oplus\lambda_v$.

**Compositional models (Jirousek et al. [911]).** Iterative composition operator.

### Definition 55 *(p.175)*
For BPAs $m_1$ on $\Theta_K$ and $m_2$ on $\Theta_L$:
$$
m_1\triangleright m_2(C) = \begin{cases} \frac{m_1(C^{\downarrow K})m_2(C^{\downarrow L})}{m_2^{\downarrow K\cap L}(C^{\downarrow K\cap L})} & m_2^{\downarrow K\cap L}(C^{\downarrow K\cap L})>0,\, C=C^{\downarrow K}\bowtie C^{\downarrow L}\\ m_1(C^{\downarrow K}) & m_2^{\downarrow K\cap L}(C^{\downarrow K\cap L})=0,\, C=C^{\downarrow K}\times\Theta_{L\setminus K}\\ 0 & \text{otherwise}\end{cases}
$$

### Definition 56 *(p.175)*
$m$ on $\Theta_{K\cup L}$ *factorises* w.r.t. $(K,L)$ if $\exists \phi:2^{\Theta_K}\to[0,+\infty)$, $\psi:2^{\Theta_L}\to[0,+\infty)$ such that $m(A) = \phi(A^{\downarrow K})\psi(A^{\downarrow L})$ if $A^{\downarrow K}\bowtie A^{\downarrow L}$, else 0. Generalises Dempster [414] and Walley-Fine [1878].

### Definition 57 (Jirousek-Vejnar [910]) *(p.176)*
$X_K, X_L$ are conditionally independent given $X_M$ if for any $A\subseteq\Theta_{K\cup L\cup M}$ which is a join $A^{\downarrow K\cup M}\bowtie A^{\downarrow L\cup M}$:
$$
m^{\downarrow K\cup L\cup M}(A) m^{\downarrow M}(A^{\downarrow M}) = m^{\downarrow K\cup M}(A^{\downarrow K\cup M}) m^{\downarrow L\cup M}(A^{\downarrow L\cup M})
$$
0 otherwise.

## 4.7 Computing *(pp.176-196)*

Naive Dempster combination is exponential; the question is *reducible* to NP-completeness for the orthogonal sum (Orponen [1366]).

### 4.7.1 Efficient algorithms *(pp.177-181)*

**Representing focal elements.** Haenni-Lehmann [770]: binary encoding — intersection = bitwise AND, equality test = bit-comparison. Liu [1193] (2014): focal element as integer for bitwise ops. **OBDDs** (ordered binary decision diagrams [196]): polynomial-time intersection/equality/projection.

**Reducing focal-element list.**

**Algorithm 4 — Truncated DS (Valin-Boily, [1838], p.178):** keep BPAs > MAX_BPM, drop < MIN_BPM, retain by cardinality if needed. *Tessem's $m_{klx}$*; Lowrance summarisation [1218]; Harmanec [797]; Petit-Renaud-Denoeux [1424].

**Inner/outer approximations (Denoeux [449]).**
### Definition 58 (strong outer approximation, p.178) [533]
Disjoint partition $\Pi=\{\mathcal{F}_1,\dots,\mathcal{F}_K\}$ of focal sets; $G_k = \bigcup_{F\in\mathcal{F}_k} F$. $Bel_\Pi^+$ has mass
$$
m_\Pi^+(G_k) = \sum_{F\in\mathcal{F}_k} m(F)
$$
**(Eq. 4.55, p.178).** Strong inner: $H_j = \cap_{F\in\mathcal{F}_j} F$. Hierarchical clustering [110, 466] for partitioning.

**Fast Mobius transform (Kennes-Smets [954, 955]) *(pp.179-180)*.** Mass/belief/plausibility as vectors $\mathbf{m}, \mathbf{bel}, \mathbf{pl}$. Negation $\overline{m}=Jm$; implicability $\mathbf{b}=BfrM\,\mathbf{m}$ via recursion $BfrM_{i+1} = \begin{bmatrix}1&0\\1&1\end{bmatrix}\otimes BfrM_i$ (Kronecker). Other inversions: $MfrB(A,B)=(1)^{|A|-|B|}$ if $B\subseteq A$ etc. Then $\mathbf{Bel} = \mathbf{b} - b(\emptyset)\mathbf{1}$, $\mathbf{pl} = \mathbf{1} - J\mathbf{b}$. Decomposition $BfrM = M_3M_2M_1$ with three $8\times 8$ matrices for $|\Omega|=3$ (worked out p.180).

**Computing relative plausibilities (Cuzzolin [89]).** When $Pl(A)=Q(A)$ for atomic hypotheses ($A=\{x\}$):
$$
Pl(A) \approx Q(A) = K\prod_{1\le i\le m} Q_i(A) \propto \prod_i Q_i(A) \propto \prod_i \sum_{B\in\mathcal{E}_i, B\supseteq A} m_i(B)
$$
**(Eq. 4.56, p.181).**

**Mean-variance ranges over credal set (Kreinovich [1072], Langewisch-Choobineh [1095]).** Lower/upper expectation $\underline E = \sum m_i\underline x_i$, $\bar E = \sum m_i\bar x_i$; upper-variance via concave QP $\bar V = \max(\sum m_i(\underline x_i^2+\bar x_i^2)) - (\sum m_i\underline x_i+\bar m_i\bar x_i))^2)$, lower-variance via convex QP solvable in $O(n^2\log n)$, faster $O(n\log n)$.

### 4.7.2 Transformation approaches *(pp.181-188)*

Map BFs to probabilities (or other simpler measures) for efficient computation.

### Probability transform (Cuzzolin [382])
$$
pt: \mathcal{B}\to\mathcal{P}, \quad Bel\mapsto pt[Bel] \quad \text{s.t. } Bel(x)\le pt[Bel](x)\le Pl(x)
$$
**(Eq. 4.57, p.182).** Constraint only on singletons.

### Pignistic transform (Smets [1675])
$$
BetP[Bel](x) = \sum_{A\supseteq\{x\}} \frac{m(A)}{|A|}
$$
**(Eq. 4.58, p.182).** Equal redistribution over focal elements; centre of mass of consistent-probabilities polytope.

### Plausibility transform (Voorbraak [1859])
$$
\tilde{Pl}[Bel](x) = \frac{Pl(x)}{\sum_{y\in\Theta} Pl(y)}
$$
**(Eq. 4.59, p.183).** *Relative plausibility of singletons*. Voorbraak: perfect representative under Dempster combination — $\tilde{Pl}[Bel]\oplus P = Bel\oplus P$ for all $P\in\mathcal{P}$ **(Eq. 4.60).**

### Relative belief transform [337, 341, 765, 382]
$$
\tilde{Bel}[Bel](x) = \frac{Bel(x)}{\sum_{y\in\Theta} Bel(y)}
$$
**(Eq. 4.61, p.183).**

**Sudano's transformations [1778]:** $PrPl, PrBel, PrNPl, PraPl$ — Eqs 4.62-4.65 (pp.183-184). $PrPl(x) = \sum_{A\supseteq\{x\}} m(A)Pl(x)/\sum_{y\in A}Pl(y)$; $PrBel$ analogous with belief; $PrNPl=\tilde{Pl}$; $PraPl(x)=Bel(x)+\epsilon Pl(x)$, $\epsilon=(1-k_{Bel})/k_{Pl}$. *Intersection probability* $p[Bel]=(1-\beta)k_{Bel}\tilde{Bel}+\beta k_{Pl}\tilde{Pl}$ **(Eq. 4.66, p.184)** with $\beta=(1-k_{Bel})/(k_{Pl}-k_{Bel})$.

**Entropy-related transforms.** Meyerowitz [1290]: maximum-entropy probability via *allocation function*
$$
\alpha: \Theta\times 2^\Theta \to [0,1], \quad \alpha(x,A)>0 \text{ only if } x\in A
$$
**(Eq. 4.68, p.185).** Harmanec-Klir [802] uncertainty-invariant transformations. Han et al. [789] questioned entropy-based criteria.

**Pan-Yang PrBP1, PrBP2, PrBP3** (Eqs in pp.185-186). Cuzzolin's *Bayesian approximations from geometry* [333, 334].

**Possibility transformation.** Mapping to consonant BFs (focal elements nested) — only $|\Theta|$ focal elements.

**Outer consonant approximation (Dubois-Prade [533]) *(pp.186-187)*.** Permutation $\rho$ of $\{x_1,\dots,x_n\}$:
$$
S_1^\rho=\{x_{\rho(1)}\},\dots,S_n^\rho=\{x_{\rho(1)},\dots,x_{\rho(n)}\}
$$
Consonant BPA: $m^\rho(S_j^\rho) = \sum_{i:\min\{l: E_i\subseteq S_l^\rho\}=j} m(E_i)$ **(Eq. 4.69, p.187)**. Iterative permutation of focal elements: Eq 4.70.

### Definition 59 (isopignistic approximation [58], p.187)
The unique consonant BF $Co_{\rm iso}$ whose pignistic probability coincides with $Bel$'s. Contour $pl_{\rm iso}(x) = \sum_{x'\in\Theta} \min\{BetP[Bel](x), BetP[Bel](x')\}$. Mass: $m_{\rm iso}(A_i) = i\cdot(BetP[Bel](x_i) - BetP[Bel](x_{i+1}))$.

**Other approximations.** Bauer's *DI algorithm* [101, 100]; Grabisch [719] $k$-additive; Jousselme [935] distance-based; Haenni [769] *incomplete belief potentials*; Antonucci-Cuzzolin [48] outer credal-set lower-probability approximation; Florea [633] possibility-to-random-set.

### 4.7.3 Monte Carlo *(pp.188-190)*

**Wilson's algorithm [1940]:** sample $\omega_i$ from $\Omega_i$ via $P_i$, count fraction with $\Gamma(\omega)\subseteq A$.

**Algorithm 5 (Monte Carlo Dempster, p.189):** $N$ trials, restart on conflict, $T=1$ if $\Gamma(\omega)\subseteq A$. Time $\frac{N}{1-\kappa}m\cdot(K_1+K_2|\Omega|)$; expected accuracy time $(9/(4(1-\kappa)k^2))\cdot m\cdot(K_1+K_3|\Omega|)$.

**Algorithm 6 (Wilson-Moral MCMC, p.190):** non-deterministic $\rm OPERATION_i$ chain.

### Theorem 3 (Wilson-Moral, p.190)
If $\Omega$ connected, then for $\epsilon, \delta$ there exist $K', N'$ such that $K\ge K', N\ge N'\Rightarrow Pr(|BEL_K^N(\omega_0)|<\epsilon)\ge 1-\delta$.

Importance sampling [1318]; Helton et al. [818] sophisticated sampling.

### 4.7.4 Local propagation *(pp.191-196)*

**Barnett's scheme [88, 89] *(p.191)*.** Linear in $|\Theta|$ for simple support functions on singletons/complements. With $\{Bel_\theta : \theta\in\Theta\}$ and only $\{\theta,\bar\theta,\Theta\}$ focal:
$$
Pl(A) = K\Bigl(1 + \sum_{\theta\in A} \frac{Bel_\theta(\theta)}{1-Bel_\theta(\theta)} - \prod_{\theta\in A}\frac{Bel_\theta(\bar\theta)}{1-Bel_\theta(\theta)}\Bigr)
$$
**(p.191).** Linear in $|\Theta|$ but exponential in number of events $A$.

**Gordon-Shortliffe diagnostic trees [710] *(p.192)*.** Hierarchical event tree (e.g., disease taxonomy). Approximation: replace any intersection of focal elements with smallest tree-node containing it.

**Shafer-Logan hierarchical evidence [1608] *(p.192)*.** *Local families* — node + its children. Three stages: up the tree (Algorithm 7), down the tree (Algorithm 8), total beliefs.

**Algorithm 7 (Stage 1, up the tree, p.193):** for non-terminal node $A$, $Bel_A^\downarrow = \oplus\{Bel_B : B\in S_A\}$, $Bel_A^L = Bel_A\oplus Bel_A^\downarrow$.

**Algorithm 8 (Stage 2, down the tree, p.193):** for each child $B\in S_A$, $Bel_B^\downarrow(B) = (Bel_A^U \oplus \{Bel_C^L: C\in S_A, C\neq B\})(B)$.

**Shafer-Shenoy on Qualitative Markov Trees [1611] *(pp.193-196)*.**

### Definition 60 (Qualitative Conditional Independence, p.194)
Partitions $\Psi_1,\dots,\Psi_n$ of $\Theta$ are *QCI* given partition $\Psi$ if $P\cap P_1\cap\dots\cap P_n\neq\emptyset$ whenever $P\in\Psi$, $P_i\in\Psi_i$ and $P\cap P_i\neq\emptyset\,\,\forall i$. Implied by stochastic independence; logical-only, doesn't require probability.

### Definition 61 (Qualitative Markov Tree, p.194)
$QMT=(V,E)$ tree of partitions of base frame $\Theta$, each node $v$ with partition $\Psi_v$, such that for every node $v$, the minimal refinements of partitions in $V_j(v)$ ($j=1,\dots,k$ subtrees) are QCI given $\Psi_v$.

**Algorithm 9 (Shafer-Shenoy propagation on QMTs, p.195):** Each node sends $Bel_v$ to neighbours; on receiving inputs $Bel_u$, computes $(Bel^T)_{\Psi_v} \leftarrow (\oplus\{(Bel_u)_{\Psi_v}: u\in N(v)\}\oplus Bel_v)_{\Psi_v}$; sends $Bel_{v\to w}$ to neighbour $w$.

PULCINELLA [1529] (Saffiotti-Umkehrer); Lauritzen [1102] HUGIN-style; Bissig-Kohlas-Lehmann *fast-division architecture* [161] guarantees BF intermediate results.

## 4.8 Making decisions *(pp.196-213)*

§4.8 places BF decision theory inside Knight's risk-vs-uncertainty distinction (Bewley [140]).

### 4.8.1 Frameworks based on utilities *(pp.197-208)*

**Expected utility (Savage, von Neumann-Morgenstern):**
$$
f\succeq g \Leftrightarrow \mathbb{E}_P(u\circ f) \ge \mathbb{E}_P(u\circ g)
$$
**(Eq. 4.71, p.197).**

### Proposition 28 (von Neumann-Morgenstern [1858], p.197)
$\succeq$ satisfies preorder, continuity, independence iff a utility $u$ exists with (4.71).

**Other criteria.** Maximax (Eq. 4.72), maximin/Wald (Eq. 4.73), Hurwicz (Eq. 4.74), minimax regret (Eqs. 4.75-4.76, p.198).

**BFs and decision making.** Two cases (Denoeux [462]): BF on states; act $f$ as multivalued $\Omega\to 2^\mathcal{X}$ — *credibilistic lottery*.

**Generalised Hurwicz / Jaffray [877, 875] *(p.198)*.**
$$
e_{m,\alpha} = \sum_{A\subset\mathcal{X}} m(A)[\alpha\min_{x\in A}u(x) + (1-\alpha)\max_{x\in A}u(x)] = \alpha\underline{\mathbb{E}}_m(u) + (1-\alpha)\overline{\mathbb{E}}_m(u)
$$
**(Eq. 4.77, p.198).** $\alpha\in[0,1]$ pessimism index. Jaffray-Wakker [883, 1867, 1868] axiomatised: transitivity, completeness, continuity, independence, *neutrality* for ambiguous events ($A\subseteq\Omega$ ambiguous if $\exists$ focal element of $Bel$ intersecting both $A$ and $\bar A$); *weak sure-thing principle*.

**Strat's decision apparatus [1768, 1770, 1771] *(pp.199-200)*.** Decision frame is a set of dollar values. Lower/upper expectations $E_*(\Theta) = \sum \inf(A)m(A)$, $E^*(\Theta)=\sum\sup(A)m(A)$. **Cloaked carnival wheel:** one wheel sector hidden. **Proposition 29 (p.200):** $E(\Theta) = E_*(\Theta) + \rho(E^*(\Theta) - E_*(\Theta))$ **(Eq. 4.78)** — coincides with Jaffray Hurwicz (4.77). $\rho$ = subjective probability that ambiguity will be resolved unfavourably.

**Decision making in TBM (pignistic).** Maximise $E_{BetP}[u] = \sum_\theta u(f,\theta) BetP(\theta)$ **(p.200)**. Linearity-axiom argument (Smets [1678, 1715]). Wilson [1951]: Smets's decision-making framework is *sensitive to choice of frame of discernment* — refinement of frame may change pignistic and hence the decision. → IN COLLECTION: [Decision-Making with Belief Functions and Pignistic Probabilities](../../Wilson_1993_Decision-MakingBeliefFunctionsPignistic/notes.md) (Wilson's Theorem 5.7 strengthens this to: lower/upper expected utility over the set of pignistic transforms induced by *all* refinements equals the standard `[Bel, Pl]` envelope expectation, so once frame-arbitrariness is admitted Smets' single-frame decision is a frame-dependent projection of the envelope decision).

**Decision in valuation-based systems.** Pignistic local computations [2041, 1988]; class-value version [570, 573].

**Choquet expected utility (CEU) [1539, 1540].** Schmeidler axiomatisation: weaker comonotonic-additive axiom yields a (not necessarily additive) *capacity* $\mu$ with utility:
$$
\forall f,g\in\mathcal{F}, \quad f\succeq g \Leftrightarrow C_\mu(u\circ f) \ge C_\mu(u\circ g)
$$
where the **Choquet integral** is
$$
C_\mu(X) = \int_0^{+\infty} \mu(X(\omega)\ge t)\,dt + \int_{-\infty}^0 [\mu(X(\omega)\ge t)-1]\,dt
$$
**(Eq. 4.79, p.202).**

**Lower/upper Choquet utilities.** For finite $\Omega$:
$$
C_{Bel}(u\circ f) = \sum_{B\subseteq\Omega} m(B)\min_{\omega\in B} u(f(\omega)) = \min_{P\in\mathcal{P}(Bel)}\mathbb{E}_P(u\circ f) = \underline{\mathbb{E}}(u\circ f)
$$
and dually $C_{Pl}(u\circ f) = \overline{\mathbb{E}}(u\circ f)$ **(p.202)**. Decision criteria: conservative ($\underline{\mathbb{E}}_f \ge \overline{\mathbb{E}}_g$, partial preorder), pessimistic ($\underline{\mathbb{E}}_f \ge \underline{\mathbb{E}}_g$ — generalises maximin), optimistic, Hurwicz-generalised.

Worked example (Ellsberg's paradox, p.202): with $m(\{R\})=1/3, m(\{B,Y\})=2/3$, lower/upper expectations differ; pessimistic strategy explains $f_1\succeq f_2$ and $f_4\succeq f_3$.

**Related Choquet work.** Nguyen [1352]: Choquet expected utility with BFs gives pessimistic strategy. Ghirardato-Le Breton [682]: characterisation of Choquet-rational decision-makers. Zhang [2105] axiomatisation. Chu-Halpern [285, 284] *generalised expected utility* — universal decision rule. Gajdos et al. [661] credal-set-framework MEU representation linking $\mathcal{P}$ to revealed priors.

### Definition 62 (E-capacity [565], p.204)
For partition $\mathcal{E}=\{E_1,\dots,E_n\}$ of $\Omega$ with probabilities $P(E_i)$, $\beta_i(A)=1$ if $E_i\subseteq A$ else 0, assessment $p\in\Pi(P)$ degree of confidence $\rho\in[0,1]$:
$$
\nu(A|p,\rho) = \sum_{i=1}^n[\rho\cdot p(A\cap E_i) + (1-\rho)\cdot P(E_i)\beta_i(A)]
$$
**(Eq. 4.80, p.204).** Convex combination of additive and capacity components.

**Caselton-Luo (1992) [234] *(pp.204-205)*.** BF mass on intervals $[\underline\omega,\bar\omega]$:
$$
E^*[u(f)] = \int m([\underline\omega,\bar\omega])\sup_\omega u(f,\omega)\,d[\underline\omega,\bar\omega], \qquad E_*[u(f)] = \int m([\underline\omega,\bar\omega])\inf_\omega u(f,\omega)\,d[\underline\omega,\bar\omega]
$$
**(Eq. 4.81, p.204).** For monotone increasing $u$: $E^* = \int u(f,\omega)h(\omega)\,d\omega$ where $h, g$ are marginal densities of upper/lower bounds.

**Generalised minimax regret (Yager [2022, 2028]).** For *subset* $A\subset\Theta$: $r_f(A)=\max_{\omega\in A}r_f(\omega)$, expected max regret $\bar R[f] = \sum m(A) r_f(A)$.

**Aggregation operators.**
### Definition 63 (OWA, [2014, 2029], p.205)
$F(x_1,\dots,x_n) = \sum_{i=1}^n w_i x_{(i)}$ **(Eq. 4.82)** with $x_{(i)}$ = $i$-th largest; weights $w_i$ normalised positive.

OWA over focal set utilities; *COWA-ER* [1795] cautious OWA with evidential reasoning. Casanovas-Merigo [1288] ascending/descending IOWA, fuzzy OWA, BS-LOWA, BS-LHA linguistic.

**Other utility-based frameworks.** Danielson [390], [252] non-ad-hoc rule, Augustin [67] interval-valued expected utility, Bordley [178] fuzzy-utility hybrid, Giang-Shenoy [686, 687] *partially consonant BFs* (PCBs) — preference axiom system, representation theorem.

### 4.8.2 Frameworks not based on utilities *(pp.206-208)*

**Boolean reasoning** (Skowron [1657]): rules $\tau\Rightarrow\tau'$, certainty coefficients as BPAs.

**Rough-set-based.** Wu [1964]: *plausibility reduct* and *belief reduct* of incomplete information system.

### Definition 64 (complete information system, p.207)
$(U,AT)$, $U$ universe, $AT=\{a_1,\dots,a_m\}$ attributes $a:U\to V_a$.

### Definition 65 (consistent sets / reducts, p.207)
$A\subseteq AT$ is:
- *classical consistent* if $R_A=R_{AT}$ (indiscernibility relations agree); minimal such = *classical reduct*.
- *belief consistent* if $Bel_A(X)=Bel_{AT}(X)$ for all $X\in U/R_{AT}$, where $Bel_A(X)=|\underline A(X)|/|U|$; minimal = *belief reduct*.
- *plausibility consistent* with $Pl_A(X)=Pl_{AT}(X)$.

### Proposition 30 ([1964] Theorem 2, p.207)
$A$ is a classical consistent set iff $A$ is a belief consistent set; $A$ is a classical reduct iff $A$ is a belief reduct.

**Other.** Kleyle-Corvin [979] elimination procedure; Sosnowski [1746] fuzzy decision rules; Sabbadin [1518]: representation of decision problems via *assumption-based truth maintenance systems* (ATMS [405]) extended with preference and decision symbols, allowing multiple real/qualitative values for gradual uncertainty/preferences. Peng [1152] grey systems with intuitionistic fuzzy.

### 4.8.3 Multicriteria decision making *(pp.208-213)*

MCDM problem $\max\mathbf{q}, \mathbf{q}\in Q$ **(Eq. 4.83, p.208)**: vector of criterion values, multiple non-dominated solutions.

**Yang's evidential reasoning (ER) [2041] *(pp.209-210)*.** Basic attributes $E=\{e_1,\dots,e_L\}$, weights $w_i$, evaluation grades $H=\{H_1,\dots,H_N\}$. Assessment: $S(e_i) = \{(H_n,\beta_{n,i})\}$ with $\sum_n\beta_{n,i}\le 1$.

### Definition 66 (ER recursive algorithm, p.210)
$$
m_{n,I(i+1)} = K_{I(i+1)}(m_{n,I(i)}m_{n,i+1} + m_{n,I(i)}m_{H,i+1} + m_{H,I(i)}m_{n,i+1}), \quad m_{H,I(i+1)} = K_{I(i+1)}m_{H,I(i)}m_{H,i+1}
$$
**(Eq. 4.84, p.210).** Variants: RIMER [2040] rule-based; IDS software [1975]; *IOWER* [2051]; FIER [754] fuzzy ER; group consensus [646, 645]; ERCM [647, 648] interval-valued; DIER [650] dependence-based.

**DS-AHP [143, 141, 142, 144, 854].** Belief-theoretic extension of Saaty's AHP for group decision-making.

**Other MCDM.** Boujelben [187]; Deng [433] BFs with TOPSIS; Huynh [864]; Sii [1649] synthesis with Zadeh-Bellman.

## 4.9 Continuous formulations *(pp.213-227)*

### 4.9.1 Shafer's allocations of probabilities [1587] *(pp.213-216)*

A BF on a class of events $\mathcal{E}\subseteq 2^{\Theta}$ can be represented as an *allocation of probability* — a $\cap$-homomorphism from $\mathcal{E}$ into a complete probability algebra. Canonical extensions defined on multiplicative subclasses extend uniquely to whole BFs definable on infinitely many compatible frames.

### Definition 67 (multiplicative subclass / BF, p.214)
$\mathcal{E}\subseteq 2^\Theta$ is *multiplicative* if $A\cap B\in\mathcal{E}$ for all $A,B\in\mathcal{E}$. $Bel:\mathcal{E}\to[0,1]$ with $Bel(\emptyset)=0, Bel(\Theta)=1$ and monotone of order $\infty$ is a BF.

### Definition 68 ($n$-alternating capacity, p.214)
$$
\mu(A_1\cap\dots\cap A_n) \le \sum_i\mu(A_i) - \sum_{i<j}\mu(A_i\cup A_j) + \dots + (-1)^{n+1}\mu(A_1\cup\dots\cup A_n)
$$
**(Eq. 4.85, p.214).** Plausibility = $\infty$-alternating; belief = $\infty$-monotone.

### Definition 69 (continuous BF, p.214)
$Bel(\cap_i A_i) = \lim_i Bel(A_i)$ for every decreasing $A_i$.

### Definition 70 (condensable BF, p.214)
$Bel(\cap\mathcal{A}) = \inf_{A\in\mathcal{A}} Bel(A)$ for every downward net $\mathcal{A}$. Required for combining infinitely many BFs.

### Definition 71 ($\cap$-homomorphism, p.214) [283]
$r:\mathcal{E}\to\mathcal{F}$ preserves $\cap$.

### Proposition 31 *(p.215)*
For every BF $Bel$ on multiplicative $\mathcal{E}$, $\exists\mathcal{X}, \mathcal{F}$, finitely additive $\mu$, and $\cap$-homomorphism $r:\mathcal{E}\to\mathcal{F}$ such that $Bel = \mu\circ r$. (Roughly: "rearranging" focal elements preserving intersection.)

### Proposition 32 (Shafer's Theorem 3.1, p.215)
There exists $\rho:\mathcal{E}\to\mathcal{M}$ ($\mathcal{M}$ probability algebra), $Bel = \mu\circ\rho$, called *allocation of probability*. (Reviewed by Kohlas [1018]; argumentation systems [1021, 1020].)

### Proposition 33 (Shafer's Theorem 5.1, canonical extension, p.215)
Any BF on multiplicative $\mathcal{E}\subseteq 2^\Theta$ extends to $2^\Theta$ via canonical extension:
$$
\overline{Bel}(A) = \sup_{\substack{n\ge 1, A_1,\dots,A_n\in\mathcal{E}\\ A_i\subset A\,\forall i}}\Bigl\{\sum (-1)^{|I|+1}Bel\bigl(\cap_{i\in I}A_i\bigr) : \emptyset\neq I\subset\{1,\dots,n\}\Bigr\}
$$
$\overline{Bel}$ is the minimal such extension.

### 4.9.2 Belief functions on random Borel intervals *(pp.216-217)*

**Strat-Smets [1772, 1714].** Take real interval $I=[0,1]$, partition by $N$ subintervals; mass $\sim N^2/2$ over discrete triangle of all sub-intervals. Limit BF lives on intervals of $I$ via integration. For $0\le a\le b\le 1$:
$$
Bel([a,b]) = \int_a^b \int_x^1 m(x,y)\,dy\,dx, \quad Pl([a,b]) = \int_0^b\int_{\max(a,x)}^1 m(x,y)\,dy\,dx
$$
**(p.216).** Dempster combination generalises:
$$
Bel_1\oplus Bel_2([a,b]) = \frac{1}{R}\int_0^a\int_b^1 [m_1(x,y)m_2(a,b)+m_2(x,y)m_1(a,b)+m_1(a,b)m_2(x,y)+m_2(a,b)m_1(x,y)]\,dy\,dx
$$
**(p.217).**

Smets [1714] *continuous pignistic PDF*:
$$
Bet(u) = \lim_{\epsilon\to 0}\int_0^u dx\int_{u+\epsilon}^1 \frac{m(x,y)}{y-x}\,dy
$$
**(Eq. 4.86, p.217).** Generalises to BFs on Borel $\sigma$-algebra with consonant + unimodal pignistic PDFs [1490]: $Bel(y) = -(s-\hat s)\frac{dBet(s)}{ds}$.

### Definition (random closed interval, p.217-218)
$(U,V)$ two-dim random vector on $\mathbb{R}^2$, $\Gamma(\omega)=[U(\omega),V(\omega)]\subset\mathbb{R}$. Induces BF on $\mathbb{R}$. Examples: fuzzy set $\pi(x)$ → consonant random interval (level-set of $\omega$); p-box $F_*, F^*$ — pair of CDFs → family of intervals.

Vannobel [1843]: reconstructs plausibility curve from cross-product of pairs of focal sets from univariate Gaussian PDFs.

### 4.9.3 Random sets *(pp.219-222)*

The most elegant continuous formalism. Probability measures over power sets; classical BFs are special case (Nguyen [1344]). Quinio [1449]: unified topological approach. Joint BFs via copulas [1350]. Kohlas [1019]: graded semilattices.

**Applications.** Vo et al. [1857]: random finite sets for multi-target tracking. Fetz-Oberguggenberger [606] *unknown interaction model* for dependent sources. Alvarez [36]: Monte Carlo for general infinite random sets.

**Random sets and possibility theory.** Dubois-Prade [537]: extension of Zadeh's principle.

**Molchanov's random set theory [1302, 1304] *(pp.220-221)*.** Closed subsets of locally compact Hausdorff second countable $\mathbb{E}$.

### Definition 72 (random closed set, p.220)
$X:\Omega\to\mathcal{C}$ such that $\{\omega: X(\omega)\cap K\neq\emptyset\}\in\mathcal{F}$ for every compact $K$.

### Definition 73 (alternative, Fell topology, p.220)
$X$ measurable w.r.t. Borel $\sigma$-algebra on $\mathcal{C}$ in Fell topology.

**Example 14 (random closed sets, p.220):** random singletons; random rays $X=(-\infty,\xi]$; random triangles; random balls; level sets $\{x:\zeta_x=t\}$ of a stochastic process.

### Definition 74 (capacity functional, p.221)
$T_X:\mathcal{K}\to[0,1]$, $T_X(K) = P(\{X\cap K\neq\emptyset\})$ **(Eq. 4.87)**. $T_X$ is a *capacity*: monotone, upper semicontinuous, $\infty$-alternating.

**CLT for random sets [1304] *(p.222)*.**

### Theorem 4 ([1304] Theorem 2.1, p.222)
For i.i.d. square-integrable random sets $X_1, X_2,\dots$,
$$
\sqrt n \rho_H\Bigl(\frac{X_1+\dots+X_n}{n}, EX\Bigr) \to \sup_{u\in B_1}\|\zeta(u)\|
$$
where $\rho_H$ Hausdorff metric, $\{\zeta(u), u\in B_1\}$ centred Gaussian random function in $C(B_1)$ with covariance $E[\zeta(u)\zeta(v)] = E[h(X,u)h(X,v)] - Eh(X,u)Eh(X,v)$.

### Definition 75 (Gaussian random compact set, p.222)
$X$ in $\mathbb{R}^d$ Gaussian if $g(X)$ Gaussian for each positively-linear Lipschitz $g\in Lip^+(\mathcal{K},\mathbb{R})$.

### 4.9.4 Kramosil's BFs on infinite spaces *(pp.222-224)*

### Definition (set-valued random variable / measure theoretic BF, p.223)
$\Gamma(\omega) = \{\theta\in\Theta: \rho(\omega,\theta)=1\}$ **(Eq. 4.88, p.223)**, $\rho:\Omega\times\Theta\to\{0,1\}$ compatibility relation. $\Gamma$ measurable on $\sigma$-field $\mathcal{S}\subset\mathcal{P}(\mathcal{P}(\Theta))$ — collections, not subsets.

**Existence of belief values.** $S\in\mathcal{S}$ measurable iff $\Gamma^{-1}(S)\in\mathcal{F}$. Then
$$
Bel(A) = P(\{\omega: \emptyset\neq\Gamma(\omega)\subset A\})
$$
**(Eq. 4.89, p.223)** exists iff anti-image of $\mathcal{P}(A)$ is in $\mathcal{F}$ — *$\mathcal{S}$-regular* events.

**Kohlas's simplified model [1027]:** $\Omega$ finite, $\mathcal{F}=\mathcal{P}(\Omega)$. Then mappings are automatically measurable.

### Definition 76 (DS-complete, p.224)
$\mathcal{S}\subset\mathcal{P}(\mathcal{P}(\Theta))$ is *Dempster-Shafer complete* if every $A\subset\Theta$ is $\mathcal{S}$-regular.

### Proposition 34 ([1051] Theorem 9.1, p.224)
If $\mathcal{S}$ is DS-complete, every collection $S\subset\mathcal{P}(\Theta)$ of at most countable cardinality of at-most-countable subsets is measurable.

### Definition 77 (four generalised BF values, p.224)
For $\mathcal{S}$-regular empty-set:
$$
\begin{aligned}
Bel_+(A) &= \sup\{P(\Gamma\in\mathcal{B})/P(\Gamma\neq\emptyset) : \mathcal{B}\subset\mathcal{P}(A)\setminus\{\emptyset\}\}\\
Bel^+(A) &= \inf\{P(\Gamma\in\mathcal{B})/P(\Gamma\neq\emptyset) : \mathcal{B}\supset\mathcal{P}(A)\setminus\{\emptyset\}\}\\
Bel_{++}(A) &= \sup\{Bel(B): B\subset A\}\\
Bel^{++}(A) &= \inf\{Bel(B): A\subset B\subset\Theta\}
\end{aligned}
$$
**(Eq. 4.90, p.224).** Normalised $Bel(A)=P(\emptyset\neq\Gamma\subset A)/P(\Gamma\neq\emptyset)$ **(Eq. 4.91)**. $Bel_+$ supremum over included measurable; $Bel^+$ infimum over containing measurable; $Bel_{++}, Bel^{++}$ over subsets themselves.

### 4.9.5 MV algebras *(pp.225-226)*

Generalises BFs to *many-valued* events (Lukasiewicz logic).

### Definition 78 (MV algebra, p.225)
$\langle M,\oplus,\neg,0\rangle$ Abelian monoid with $\neg\neg f=f$, $f\oplus\neg 0 = \neg 0$, $\neg(\neg f\oplus g)\oplus g = \neg(\neg g\oplus f)\oplus f$. Derived: $1=\neg 0$; $f\odot g=\neg(\neg f\oplus\neg g)$; $f\le g$ iff $\neg f\oplus g=1$. Adjoining $\vee,\wedge$ makes a distributive lattice.

**Example 15 (standard MV algebra, p.226):** $[0,1]$ with $f\oplus g=\min(1,f+g)$, $\neg f=1-f$, $f\odot g=\max(0,f+g-1)$ — Lukasiewicz t-norm/t-conorm.

### Definition 79 (state, p.226)
$s:M\to[0,1]$ with $s(1)=1$, $s(f+g)=s(f)+s(g)$ when $f\odot g=0$. Generalisation of finite probability. On semisimple algebras: $s(f)=\int f\,d\mu$.

### Definition 80 (BF on $[0,1]^X$, p.226)
$Bel:[0,1]^X\to[0,1]$ such that $\exists s$ on $[0,1]^{\mathcal{P}(X)}$ with $s(1_\emptyset)=0$ and $Bel(f) = s(\rho(f))$ where $\rho(f)(B) = \min_{x\in B}f(x)$ if $B\neq\emptyset$ else 1.

State-assignment $s$ corresponds to probability on $\Omega$ in random-set interpretation; integral representation by Choquet integral. The set of BFs on $[0,1]^X$ forms a simplex with categorical-BF-like extreme points.

### 4.9.6 Other approaches *(p.227)*
Guan-Bell [735]: BFs over arbitrary Boolean algebras. Wu et al. [1965]: fuzzy BFs on infinite spaces via fuzzy implication.

## 4.10 The mathematics of belief functions *(pp.227-235)*

### 4.10.1 Distances and dissimilarities *(pp.227-229)*

Norms for BFs serve conflict measurement, approximation, distance-based reasoning. Survey: Jousselme-Maupin [938, 630, 937] identifying four families: metric, pseudo-metric, non-structural, non-metric.

**Jousselme distance [933] *(p.228)*:**
$$
d_J(m_1,m_2) = \sqrt{\frac{1}{2}(\mathbf{m}_1-\mathbf{m}_2)^T D(\mathbf{m}_1-\mathbf{m}_2)}, \quad D(A,B) = |A\cap B|/|A\cup B|
$$
Positive definite (Bouchard et al. [184]); accounts for focal element similarity; $D(A,B)<D(A,C)$ if $C$ closer to $A$.

**Other proposals.**
- Dempster conflict $\kappa$, Ristic *additive global dissimilarity* $-\log(1-\kappa)$ [1491].
- Bhattacharya-extended *fidelity* [149]: $\sqrt{\mathbf{m}_1}^T W \sqrt{\mathbf{m}_2}$.
- Perry-Stephanou [1421]: $d_{PS}(m_1,m_2) = |\mathcal{E}_1\cup\mathcal{E}_2|(1-|\mathcal{E}_1\cap\mathcal{E}_2|/|\mathcal{E}_1\cup\mathcal{E}_2|) + (\mathbf{m}_{12}-\mathbf{m}_1)^T(\mathbf{m}_{12}-\mathbf{m}_2)$.
- Blackman-Popoli *attribute distance* [169]: $d_{BP}(m_1,m_2) = -2\log[(1-\kappa(m_1,m_2))/(1-\max_i\{\kappa(m_i,m_i)\})] + (\mathbf{m}_1+\mathbf{m}_2)^T\mathbf{g}_A - \mathbf{m}_1^T G\mathbf{m}_2$, $G(A,B)=(|A|-1)(|B|-1)/(|\Theta|-1)^2$.
- $L_p$ Minkowski [356, 360, 349, 352]: $d_{L_p}(m_1,m_2) = (\sum_A |Bel_1(A)-Bel_2(A)|^p)^{1/p}$.
- Fixen-Mahler *Bayesian percent attribute miss* [623]: $\mathbf{m}_1' P \mathbf{m}_2$, $P(A,B)=p(A\cap B)/(p(A)p(B))$.
- Zouhal-Denoeux inner product of pignistic.
- Information-based $d_U(m_1,m_2)=|U(m_1)-U(m_2)|$ for uncertainty measure $U$ [449].

### 4.10.2 Algebra *(pp.229-232)*

**Algebra of frames.** Cuzzolin [363, 369, 329]; Kohlas [1027 Ch. 7]; Capotorti-Vantaggi [222].

### Definition 81 (independent frames [1583], p.229)
$\Theta_1,\dots,\Theta_n$ are $\mathcal{IF}$ if $\rho_1(A_1)\cap\dots\cap\rho_n(A_n)\neq\emptyset$ for all $\emptyset\neq A_i\subseteq\Theta_i$, where $\rho_i$ is refining onto minimal refinement.

### Proposition 35 *(p.230)*
$\Theta_1,\dots,\Theta_n$ independent iff *all* possible BFs $Bel_1,\dots,Bel_n$ on them are Dempster-combinable on minimal refinement $\Theta_1\otimes\dots\otimes\Theta_n$.

Order $\Theta_1\le\Theta_2\Leftrightarrow\exists\rho:\Theta_2\to 2^{\Theta_1}$ refining **(Eq. 4.92, p.230)**. Both $(\mathcal{F},\le)$ and $(\mathcal{F},\le^*)$ are lattices.

### Definition 82 (semimodular lattice, p.230)
*Upper*: $x\succ x\wedge y$ implies $x\vee y\succ y$. *Lower*: $x\vee y\succ y$ implies $x\succ x\wedge y$.

### Theorem 5 ([329], p.230)
$(\mathcal{F},\le)$ upper semimodular lattice; $(\mathcal{F},\le^*)$ lower semimodular.

**Lattice independence.** $\mathcal{I}_1: l_j\not\le \bigvee_{i\neq j}l_i$; $\mathcal{I}_2: l_j\wedge\bigvee_{i<j}l_i = 0$; $\mathcal{I}_3: h(\bigvee_i l_i) = \sum h(l_i)$ (rank). Theorem 5 of independence-of-frames vs lattice-independence: $\mathcal{IF}\subset\mathcal{I}_1\cap\mathcal{I}_2\cap\mathcal{I}_3$ (upper) — equivalent to matroidal independence in a generalised sense [1374].

**Algorithm 10 (Generalised Gram-Schmidt, p.232):** project $Bel_1,\dots,Bel_n$ onto independent frames $\Theta_1',\dots,\Theta_m'$ with same minimal refinement, producing surely-combinable equivalents.

**Algebra of belief measures.** Daniel [389].
### Definition 83 (Dempster's semigroup, p.231)
$D=(\mathcal{B}_2^\emptyset,\oplus)$ — set of all BFs on binary frame minus Bayesian ones, with Dempster combination.

### Definition 84 *(p.232)*
$Bel\le Bel'$ on $\Theta=\{x,y\}$ iff $h(Bel)\le h(Bel')$ or $h(Bel)=h(Bel')$ and $Bel(x)\le Bel'(x)$, $h(Bel)\doteq(1-Bel(y))/(2-Bel(x)-Bel(y))$.

### Proposition 36 *(p.232)*
Dempster semigroup with $\le$ is ordered commutative semigroup; neutral element $\mathbf 0=[0,0]'$; only non-zero idempotent $\mathbf 0'=[1/2,1/2]$. Daniel extended to disjunctive rule [378], algebra on three-frame quasi-Bayesian [387]. Brodzik-Enders [194]: semigroup of Bayesian BFs and categorical BFs under Dempster's rule, related by homomorphism.

### 4.10.3 Integration *(p.233)*

Barres [134] integrals w.r.t. basic plausibility:
$$
\int f\otimes_\mu m \doteq \int_\mathcal{F}\Bigl(\int_F f\,d\mu\Bigr)dm(F) = \int(f\cdot Pl)(x)\,d\mu(x)
$$
**(p.233).** Generalised Lebesgue:
$$
\oint f\otimes_\mu m \doteq \int_\mathcal{F}\Bigl(\int_F f\,d\mu_F\Bigr)dm(F)
$$
**(Eq. 4.93, p.233)** with $\mu_F(B)=\mu(B|F)$. Reduces to Lebesgue for probability BPAs. Comparison with Choquet $\int_0^{\sup f} T(\{f>t\})dt$ and Sugeno integrals; bracketed:
$$
\int_0^{\sup f} Bel(\{f>t\})dt = \int(\inf_{x\in F} f(x))dm(F) \le \oint f\otimes_\mu m \le \int_0^{\sup f} Pl(\{f>t\})dt = \int(\sup_{x\in F} f(x))dm(F)
$$

### 4.10.4 Category theory *(pp.233-234)*

Kennes [951]: combination of probability kinematics (Jeffrey) with maximum cross-entropy (Jaynes).

### Definition 85 (category, p.234)
$(V,A)$ directed graph with composition operator $c:A\times A\to A$, $c(a_1,a_2)=a_1.a_2$; associative; identities are neutral.

### Definition 86 (Dempster's category, p.234)
Nodes = mass distributions; arrows $a:m_1\to m_2$ are BPAs with $a\oplus m_1 = m_2$. Composition = Dempster sum. Identity = vacuous BF.

### Definition 87 (product, p.234)
Universal arrow $a:u\to v\times w$ with $a.p_v=a_v$, $a.p_w=a_w$.

For two BFs, product/disjunction $Bel_1\vee Bel_2$ is the most-Dempster-updated BF s.t. both are updates of it. Conjunction dual. *Categorical conjunction* = most cautious — no distinctness assumed (vs Dempster, which assumes distinct evidence).

### 4.10.5 Other mathematical analyses *(pp.234-235)*

- Dubois-Prade [527]: bodies of evidence as generalised sets; algebraic structure via extended union/intersection/complement.
- Roesmer [1494]: connection to non-standard analysis.
- Yager [2005]: combination under arithmetic operations of DS-structure-valued variables; Dempster's rule as special case under intersection.
- Wagner [1866]: BF consensus on $|\Theta|\ge 3$ must be weighted arithmetic mean (and on $|\Theta|\ge 4$ for Bayesian BFs); preserved under low-monotone Choquet.
- Hernandez-Recasens [824]: T-indistinguishability operator from BF — new method for BF approximation via T-preorders.

## Algorithms (compiled list)

| # | Name | Page | Inputs / outputs |
|---|------|------|------------------|
| 1 | Wong-Lingras BF from preferences | 122 | $\cdot>,\sim$ → mass $m$ via perceptron |
| 2 | DEVN initialisation | 174 | DEVN, priors → $\pi, \lambda$ |
| 3 | DEVN updating | 174 | New $Bel$ at node → propagated network |
| 4 | Truncated Dempster-Shafer (Valin-Boily) | 178 | BPM thresholds → reduced focal set |
| 5 | Monte Carlo Dempster | 189 | $Bel_1,\dots,Bel_m$, $A$ → estimate of $Bel(A)$ |
| 6 | MCMC Dempster (Wilson-Moral) | 190 | + $\omega_0$ → $S/Nm$ estimator |
| 7 | Hierarchical evidence Stage 1 | 193 | Tree, BFs at leaves → up-propagation |
| 8 | Hierarchical evidence Stage 2 | 193 | + Stage 1 → down-propagation |
| 9 | Shafer-Shenoy QMT propagation | 195 | QMT, BFs at $V'$ → marginalised BF at each node |
| 10 | Generalised Gram-Schmidt | 232 | $\{Bel_i\}$ → surely combinable equivalents |

## Geometric structures (chapter highlights)

- **Random closed interval (p.217-218):** $\Gamma(\omega) = [U(\omega), V(\omega)]$ on $\mathbb R^2$ probability space; induces BF on $\mathbb R$. Special cases: fuzzy set $\pi(x)$ → consonant random interval; p-box $(F_*, F^*)$ → upper/lower CDF pair.
- **Lattice of frames (p.230):** $(\mathcal{F},\le)$ upper-semimodular lattice; $(\mathcal{F},\le^*)$ lower-semimodular. Theorem 5.
- **Dempster's semigroup (Definition 83, p.231):** $D=(\mathcal{B}_2^\emptyset,\oplus)$ ordered commutative semigroup with neutral $[0,0]$ and unique non-trivial idempotent $[1/2,1/2]$.
- **Simplex of BFs on $[0,1]^X$ (Section 4.9.5):** set of MV-algebra BFs is a simplex whose vertices are categorical-BF generalisations.
- **Polytope of consistent probabilities (Eq. 3.10 referenced in 4.7.2, pignistic discussion):** centre of mass = $BetP$.

## Worked examples (compiled)

- **Example 11 — Zadeh's counter (p.134).** Two doctors, mass on $\{M\}$ vs $\{T\}$ (99% each), tiny mass on $\{C\}$ (1% each). Dempster gives $m(C)=1$ → 'paradox'.
- **Example 12 — Lemmer's urn (p.136).** Sensors labelling balls; Dempster-combined sensor BFs may not match accurate label proportions.
- **Example 13 — Dezert-Tchamova absorption (p.138).** Doctor 1 has $a$ on $\{M\}$ + rest on $\{M,C\}$; Doctor 2 covers $\{M,C\}, \Theta, \{T\}$. Dempster yields $m_1\oplus m_2=m_1$ — Doctor 2 ignored.
- **Voorbraak's three-element example (p.136).** $\Theta=\{a,b,c\}$, $m, m'$ specific masses. $\oplus$ gives uniform $1/3$ each, including to $\{b\}$ which never received explicit support.
- **Strat's cloaked carnival wheel (p.200).** $\Theta=\{1,5,10,20\}$, one sector hidden. $\rho$ = subjective probability the hidden sector is favourable. Generalised Hurwicz / Jaffray.
- **Ellsberg's paradox (p.202).** $m(\{R\})=1/3, m(\{B,Y\})=2/3$. Lower/upper Choquet expectations differ; pessimistic strategy explains observed $f_1\succeq f_2$ and $f_4\succeq f_3$.
- **Object-classification fusion (§4.4.2, p.157).** Two sensors, one wrong; Bayesian fusion hits $1/2-1/2$ deadlock; discounted-DS picks correct decision.

## Figures of interest

- **Fig 4.5 (p.135):** $m_1, m_2$ in Zadeh's paradox over $\Theta=\{M,C,T\}$.
- **Fig 4.6 (p.138):** Belief functions in Dezert-Tchamova example.
- **Fig 4.7-4.8 (p.157):** Bayesian vs belief data fusion pipelines.
- **Fig 4.9 (p.158):** Credal sets associated with $Bel$ (Dempster) and $Bel'$ (disjunctive) vs Bayesian point in fusion-of-unreliable-data example.
- **Fig 4.10 (p.160):** Dempster conditioning illustration.
- **Fig 4.11 (p.170):** Marginalisation vs cylindrical extension of focal elements on product frame.
- **Fig 4.12 (p.172):** Example DAG.
- **Fig 4.13 (p.179):** Strong outer approximation by clustering focal elements.
- **Fig 4.14 (p.180):** Fast Möbius transform recursive computation on $\Omega=\{a,b,c\}$.
- **Fig 4.15 (p.192):** Gordon-Shortliffe diagnostic tree example.
- **Fig 4.16 (p.196):** Local processor in Shenoy-Shafer architecture (3 neighbours).
- **Fig 4.17 (p.200):** Strat's cloaked carnival wheel.
- **Fig 4.18 (p.216):** Strat's BFs on intervals — left/right extrema, integration domain.
- **Fig 4.19 (p.217):** Random closed interval $\Gamma=[U,V]$.
- **Fig 4.20 (p.218):** Consonant random interval (fuzzy α-cuts) and p-box.
- **Fig 4.21 (p.221):** Examples of random closed sets (Molchanov).
- **Fig 4.22 (p.227):** Relationships between classical BFs and BFs on $[0,1]^X$ via $\rho$ and state $s$.
- **Fig 4.23 (p.231):** Lattice-theoretic independence vs frame-independence in upper/lower semimodular lattice cases.

## Additional definitions

(Carried over and supplemented; numbering keeps the book's chapter-local numbers.)

- **Definition 47** *Wilson axioms* — combination rule respects contradictions *(p.137)*.
- **Definition 48** Combination rule respects zero probabilities *(p.137)*.
- **Definition 49** Cautious conjunctive rule *(p.141)*.
- **Definition 50** Bold disjunctive rule *(p.142)*.
- **Definition 51** Josang's opinion / consensus *(p.142)*.
- **Definition 52** Liu's conflict measure *(p.151)*.
- **Definition 53** Conditional event $[B|A]$ *(p.163)*.
- **Definition 54** Spies's conditional BF *(p.163)*.
- **Definition 55** BPA composition $m_1\triangleright m_2$ *(p.175)*.
- **Definition 56** Factorisation of a BPA *(p.175)*.
- **Definition 57** Conditional independence (Jirousek-Vejnar) *(p.176)*.
- **Definition 58** Strong outer approximation *(p.178)*.
- **Definition 59** Isopignistic approximation *(p.187)*.
- **Definition 60** QCI partitions *(p.194)*.
- **Definition 61** Qualitative Markov Tree *(p.194)*.
- **Definition 62** E-capacity *(p.204)*.
- **Definition 63** OWA operator *(p.205)*.
- **Definition 64** Complete information system *(p.207)*.
- **Definition 65** Classical/belief/plausibility consistent set / reduct *(p.207)*.
- **Definition 66** ER recursive aggregation *(p.210)*.
- **Definition 67** Multiplicative subclass / BF on it *(p.214)*.
- **Definition 68** $n$-alternating capacity *(p.214)*.
- **Definition 69** Continuous BF *(p.214)*.
- **Definition 70** Condensable BF *(p.214)*.
- **Definition 71** $\cap$-homomorphism *(p.214)*.
- **Definition 72** Random closed set (Molchanov) *(p.220)*.
- **Definition 73** Random closed set via Fell topology *(p.220)*.
- **Definition 74** Capacity functional $T_X$ *(p.221)*.
- **Definition 75** Gaussian random compact set *(p.222)*.
- **Definition 76** DS-complete $\sigma$-field *(p.224)*.
- **Definition 77** Four generalised BF values $Bel_+, Bel^+, Bel_{++}, Bel^{++}$ *(p.224)*.
- **Definition 78** MV algebra *(p.225)*.
- **Definition 79** State on MV algebra *(p.226)*.
- **Definition 80** BF on $[0,1]^X$ *(p.226)*.
- **Definition 81** Independent frames $\mathcal{IF}$ *(p.229)*.
- **Definition 82** Upper / lower semimodular lattice *(p.230)*.
- **Definition 83** Dempster's semigroup $D=(\mathcal{B}_2^\emptyset,\oplus)$ *(p.231)*.
- **Definition 84** Order $\le$ on Dempster's semigroup *(p.232)*.
- **Definition 85** Category *(p.234)*.
- **Definition 86** Dempster's category *(p.234)*.
- **Definition 87** Product in a category *(p.234)*.

## Theorems / propositions (additional)

- **Proposition 26 ([455] Prop 10, p.141):** every unnormalised BF has unique canonical disjunctive decomposition $m=\,⃝\!\bigcup\,_{A\neq\emptyset} m_{A,v(A)}$.
- **Proposition 27 (Spies, p.167):** total-probability-generalised BF $Bel_{\rm tot}$ exists with $Bel_{\rm tot}(\cdot|B_i)=Bel_i$ and reduces to Jeffrey for probabilities.
- **Proposition 28 (vNM, p.197):** preorder + continuity + independence ⇔ utility function exists.
- **Proposition 29 (Strat, p.200):** $E(\Theta) = E_*(\Theta)+\rho(E^*(\Theta)-E_*(\Theta))$.
- **Proposition 30 (Wu, p.207):** $A$ is a classical reduct iff a belief reduct.
- **Proposition 31 (p.215):** every BF on multiplicative subclass = $\mu\circ r$ for $r$ $\cap$-homomorphism.
- **Proposition 32 (Shafer Thm 3.1, p.215):** every BF has an allocation of probability $\rho:\mathcal E\to\mathcal M$.
- **Proposition 33 (Shafer Thm 5.1, p.215):** canonical extension of a BF on multiplicative $\mathcal E$ to $2^\Theta$ exists; $\overline{Bel}$ is minimal.
- **Theorem 3 (Wilson-Moral MCMC, p.190):** convergence of Monte Carlo Dempster to BF value.
- **Proposition 34 (Kramosil [1051] 9.1, p.224):** DS-complete σ-fields make all countable-cardinality countable collections measurable.
- **Theorem 4 (Molchanov CLT, p.222):** $\sqrt n\rho_H((X_1+\dots+X_n)/n, EX)\to\sup\|\zeta(u)\|$.
- **Theorem 5 (Cuzzolin [329], p.230):** lattice of frames with ordering $\le$ is upper semimodular; with $\le^*$ lower semimodular.
- **Proposition 35 (p.230):** independence of frames ⇔ all BFs on them are Dempster-combinable on minimal refinement.
- **Proposition 36 (Daniel [389], p.232):** Dempster's semigroup with $\le$ is ordered commutative semigroup with neutral $[0,0]$ and unique non-zero idempotent $[1/2,1/2]$.

## Criticisms of prior work (chapter)

- *Bayesian fusion failure under unreliability:* $1/2$-$1/2$ deadlock when sensors equally unreliable but evidence asymmetric (p.158). Discounted DS solves it.
- *Bayesian inference assumes prior:* Dempster's auxiliary-variable model produces posterior without prior (p.115); BF richer than MLE/MAP.
- *Dempster's rule in conflict:* Zadeh, Lemmer, Voorbraak, Dezert-Tchamova all show counter-intuitive behaviour (pp.134-138).
- *Pignistic decision frame-sensitivity:* Wilson [1951] — refining the frame may change pignistic probability and hence the optimal decision (p.201).
- *Uncertainty-measure subadditivity failures:* Vejnarova [1853], Pal [1379] (p.130).
- *Lefevre family:* Haenni [763] criticised; Lefevre replied [1119] (p.148).
- *Frequentist BF interpretation impossible:* Lemmers [1132] showed sample-space-derived BFs cannot be frequency ratios (p.118).
- *Dempster conditioning vs three prisoners:* Fagin-Halpern argue Dempster behaves unreasonably (p.161).

## Design rationale

- *Why not always Dempster:* the "veto power" of a single source over consensus is undesirable when sources are unreliable or conflicting (p.144). Hence averaging, discounting, idempotent rules, $\alpha$-junctions.
- *Open-world (Smets) vs closed-world (Yager):* leaving $m(\emptyset)>0$ admits the frame is not exhaustive; Yager moves it to $\Theta$ as ignorance (Eqs. 4.23, 4.25, p.139-140).
- *Conjunctive vs disjunctive conditioning:* conjunctive is *committal* (one source is right), disjunctive *cautious* (one of them is right) — choice depends on source-reliability assumption (§4.5 nested family).
- *Pignistic transform vs plausibility transform:* pignistic has linearity-axiom justification (Smets); plausibility transform commutes with Dempster's rule (Voorbraak; pp.182-183).
- *Cuzzolin's geometry programme rationale (p.186):* Bayesian approximations from minimum Euclidean distance — geometric ground for probability transformations.

## Open / research questions

- *Geometric conditioning's combination-rule dual* (p.164) — open whether some rule dual to Dempster's induces geometric conditioning.
- *Uniqueness of Spies's total-probability solution* (p.168) — addressed in Ch. 17.
- *Idempotent fusion under unknown dependencies* (p.146) — extension may require multi-BF outputs.
- *Mathematics of allocation of probability extension* of geometric programme to continuous spaces (Choquet representation footnote, p.215).

## Notable references cited (chapter-level keys)

- `[1583]` Shafer 1976 — original BF text, discounting, $\mathcal{IF}$.
- `[1675]`, `[1730]`, `[1718]` Smets — TBM, GBT.
- `[1772]`, `[1714]` Strat / Smets — continuous BFs on intervals.
- `[1304]`, `[1302]` Molchanov — random set theory, CLT.
- `[1051]` Kramosil — measure-theoretic BFs.
- `[1077]`, `[627]` Kroupa, Flaminio — MV-algebraic BFs.
- `[1078]` Kroupa — MV-algebra extension.
- `[1858]` von Neumann-Morgenstern — utility axiomatisation.
- `[140]` Bewley — Knightian uncertainty.
- `[1539]`, `[1540]`, `[689]`, `[692]` Schmeidler / Gilboa — Choquet expected utility, axiomatisation.
- `[877]`, `[875]`, `[883]` Jaffray, Jaffray-Wakker — generalised Hurwicz, BF utility.
- `[1518]` Sabbadin — extended ATMS for decision making with preferences (relevant to propstore.world).
- `[1859]` Voorbraak — plausibility transform.
- `[1860]` Voorbraak — random codes, Lemmer counter.
- `[1587]` Shafer — allocations of probability.
- `[291]` Cobb-Shenoy — plausibility transform commutativity.
- `[1611]` Shafer-Shenoy-Mellouli — local computation on QMT.
- `[1626]` Shenoy — valuation networks.
- `[911]`, `[910]`, `[907]` Jirousek + Shenoy/Vejnar — compositional models, factorisation, conditional independence.
- `[455]`, `[451]` Denoeux — cautious rule, canonical decomposition.
- `[1428]` Pichon-Denoeux — t-norm/uninorm families.
- `[915]`, `[920]` Josang — consensus, cumulative, averaging operators.
- `[1118]`, `[1119]` Lefevre — weight families.
- `[1720]`, `[1429]` Smets, Pichon — $\alpha$-junctions.
- `[1196]`, `[1197]` Liu — conflict measure.
- `[1287]`, `[1286]`, `[1284]`, `[1285]` Mercier — contextual discounting.
- `[1252]` Pichon — correction with metaknowledge.
- `[2041]`, `[2040]`, `[2042]`, `[2038]`, `[2043]`, `[2051]`, `[2122]` Yang and co-authors — ER, RIMER, IDS, IOWER, FIER.
- `[143]`, `[141]`, `[142]`, `[144]` Beynon — DS-AHP.
- `[26]` Alchourrón-Gärdenfors-Makinson — AGM revision (referenced for Ma's logic-based revision).
- `[1318]`, `[1940]` Wilson, Moral — Monte Carlo and importance sampling.
- `[770]`, `[1193]` Haenni-Lehmann, Liu — efficient focal-element representations.
- `[954]`, `[955]` Kennes-Smets — fast Möbius transform.

## Implementation notes for propstore (Chapter 4)

The chapter is a goldmine of **operations** that propstore can plug into existing layers — every conditioning rule, combination rule, transform, decision rule is a candidate adapter for the storage / world / belief_set / aspic_bridge / render layers.

- **`propstore.world` (ATMS) and `propstore.world.assignment_selection_merge`:**
  - The conditioning *family* (Dempster, Credal/Fagin-Halpern, Geometric, Conjunctive, Disjunctive) and their nested inequalities (§4.5.8) are directly applicable as alternative adjudication policies under different ATMS environment assumptions. Per propstore's non-commitment principle, *all five* are legitimate; render policy chooses.
  - Discounting (§4.3.6, Eq. 4.39) and contextual discounting (Mercier) are the formal counterpart of source-reliability metadata on ATMS evidence assumptions.
  - Liu's conflict measure (Definition 52) and the *internal vs external conflict* distinction (Daniel [384]) provide signals for ATMS conflict bookkeeping versus storage merge bookkeeping.
  - Smets's *open-world assumption* via $m(\emptyset)>0$ (§4.3.2) maps onto propstore's stance that the frame may be incomplete — `propstore.world` should preserve unallocated mass rather than normalising it away.

- **`propstore.belief_set.ic_merge` and `propstore.belief_set` AGM:**
  - Conjunctive vs disjunctive conditioning maps to *revision vs focusing* (Suppes-Zanotti, p.161). The AGM revision interface in `propstore.belief_set` should be tagged with the underlying conditioning family.
  - Spies's equivalence-class conditioning (Definition 53, 54, p.163) defines conditional events as second-order BFs on collections — directly applicable to propstore's claim-context machinery if multiple authored claims are equivalent under a conditioning relation.
  - GBT (§4.6.1) generalises Bayes to inference; useful for `propstore.world` posterior updating from evidential parameters when claims act like conditional likelihoods.

- **`propstore.aspic_bridge`:**
  - Yager's, Dubois-Prade's, Dempster's, Smets's, Yager's prioritised combination rules each correspond to a *priority discipline* over rules in ASPIC+ — `propstore.aspic_bridge.translate_priorities` could expose any of these.
  - Combination of *unreliable* sources (discounting, ACR, PCR, Joshi rule) maps to ASPIC+'s undercutting attack types: an undermine of a source's reliability rather than of the conclusion.
  - Cautious rule's idempotence (§4.3.2) is the right semantics for combining redundant evidence — ASPIC+ rule duplication should not strengthen support.

- **`propstore.defeasibility`:**
  - "Veto power" critique of Dempster (p.144) is the same intuition as CKR justifiable exceptions: a single misfiring source should not annihilate downstream belief. Propstore's exception mechanism implements this at the contextual-applicability layer.
  - Strat's Hurwicz-coefficient $\rho$ for unresolved ambiguity (p.200) is a candidate parameter for `propstore.defeasibility` exception-confidence configuration.

- **`propstore.support_revision`:**
  - The Smets *Jeffrey-Geometric* and *Jeffrey-Dempster* rules (Eq. 4.53) generalise the support-incision pattern: when a partition's mass shifts, propagate through the conditional family.
  - Categorical conjunction in Dempster's category (Definition 86): "no distinctness assumed" is the right model for *worldline-scope* combination where shared evidence may be present.

- **Render layer (CLI / decision policy):**
  - Decision rules in §4.8 are render-time policies. Per the architecture, the *same* worldline supports many: pignistic ($BetP$), Choquet lower (pessimist), Choquet upper (optimist), Hurwicz ($\alpha$), generalised regret, OWA. The `RenderPolicy` should expose these as enumerated families (Eqs. 4.71-4.83).
  - Transformation approaches (§4.7.2) — pignistic, plausibility, Sudano $PrPl/PrBel/PrNPl/PraPl$, intersection probability, isopignistic — each is a render-time *probability extraction* with different semantics. Calibration provenance (cf. project CLAUDE.md) tags should distinguish them.
  - The *isopignistic approximation* (Definition 59) is the unique consonant BF whose pignistic = original — useful as a compact summary representation when render needs a possibility-shaped output.

- **`propstore.dimensions` / CEL / Z3:**
  - BFs on random Borel intervals (§4.9.2, Eq. 4.86) connect directly to propstore's QUANTITY / TIMEPOINT typed values: a measurement with uncertainty is a random closed interval, and the continuous pignistic PDF is its render-time deterministic projection. The Strat-Smets formalism is the natural underpinning for QUANTITY-with-uncertainty on the dimensions side.
  - p-boxes (§4.9.2) are pairs $(F_*, F^*)$ of CDFs — exactly the typed provenance shape `calibrated` vs `vacuous` carrier the project design demands.

- **Provenance / honest ignorance (project CLAUDE.md):**
  - "Vacuous BF" $m(\Theta)=1$ is the formal `vacuous` provenance tag.
  - Discounting at rate $\alpha$ (Eq. 4.39) is the formal way to take a `measured` value and downgrade it under known reliability — this implements the `calibrated` stance algebraically.
  - The four Kramosil values $Bel_+, Bel^+, Bel_{++}, Bel^{++}$ (Definition 77) are the formal *non-S-regular* generalisations — applicable to events where the σ-field doesn't capture the event exactly.

- **`propstore.cli` / agent workflow:**
  - The Yang ER recursion (Eq. 4.84, Definition 66) is a directly implementable algorithm for combining multi-criteria attribute assessments — useful for the `adjudicate` agent.
  - DS-AHP (§4.8.3) for pairwise expert preference aggregation — applicable to `reconcile-vocabulary` when multiple experts propose competing concept reconciliations.

- **Computing layer:**
  - Algorithm 4 (truncated DS), Algorithm 5/6 (Monte Carlo), Algorithm 9 (Shafer-Shenoy on QMT) are the implementations of choice when propstore needs to compute world-marginal beliefs over large frames. The fast Möbius transform (Eqs. for `BfrM`) is the bedrock primitive.
  - Strong outer/inner approximations (Definition 58) provide bounded-error approximation algorithms for storage compression of large focal-element collections.

## Quotes worth preserving

- *"Conditioning operators form a nested family, from the most committal to the least: $Bel_{\,\bigcup\,}\le Bel_{\rm Cr}\le Bel_\oplus\le Bel_{\,\bigcirc\,}\le Pl_{\,\bigcirc\,}\le Pl_\oplus\le Pl_{\rm Cr}\le Pl_{\,\bigcup\,}$"* — p.164.
- *"Combinations are performed at the target information level."* — Liu [1199] cited p.137.
- *"Dempster's rule of conditioning corresponds essentially to the least committed specialisation, whereas Dempster's rule of combination results from commutativity requirements."* — Klawonn-Schwecke cited p.137.
- *"Belief functions become a component of a decision problem if either: (1) The decision maker's beliefs are described by a BF rather than a probability, or (2) The decision maker is unable to precisely describe the outcomes of (at least some) acts under each state of nature."* — Denoeux [462] cited p.198.
- *"$\alpha$-junctions correspond to a particular form of knowledge about the truthfulness of the sources generating the BFs to be combined."* — Pichon [1429] cited p.149.
- *"The bottom line of Proposition 27 is that by combining the unconditional, a priori belief function with all the conditionals we get an admissible marginal which generalises total probability."* — p.168.
