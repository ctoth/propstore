# Chunk #9 — Chapter 15 (Geometric conditioning) + Chapter 16 (Decision making with epistemic transforms)

**Book pages:** 595-654 (assignment); pages actually present in PDF range 620-679 cover book pp. 606-end of Ch.16 plus Part V opener and start of Ch.17.

**PDF idx:** 620-679 (NOTE: chunk #8 must own pp.595-605, i.e. the start of Ch.15 — sections 15.1, 15.2, and earlier 15.3 material. This chunk picks up at 15.3.2 "L₁ conditioning in B".)

## Sections covered (with book pages observed in this PDF range)

- **15.3.2 L₁ conditioning in B** (p.606)
- **15.3.3 L∞ conditioning in B** (p.607-610) — Example 50 (ternary), Theorem 97, Theorem 98
- **15.4 Mass space versus belief space conditioning** (p.610-612) — 15.4.1 summary; Example 51 (ternary comparison)
- **Fig. 15.2** (p.613)
- **15.5 An outline of future research** (p.613-614) — Questions 10, 11
- **Appendix: Proofs** for Ch.15 (p.614-626) — Lemmas 17, 18, 19; Theorems 90, 91, 92, 94, 95, 97, 98
- **Chapter 16 opener and outline** (p.627-630)
- **16.1 The credal set of probability intervals** (p.630-632) — 16.1.1 lower/upper simplices; 16.1.2 simplicial form (Theorem 99); 16.1.3 lower/upper simplices and probability intervals
- **16.2 Intersection probability and probability intervals** (p.632-634) — Definition 133, Fig. 16.2
- **16.3 Credal interpretation of Bayesian transforms: ternary case** (p.634-636) — Proposition 66, Fig. 16.3
- **16.4 Credal geometry of probability transformations** (p.636-641) — 16.4.1 focus (Definition 134, Theorem 100); 16.4.2 transformations as foci (Theorems 101-106); 16.4.3 semantics and rationality principle; 16.4.4 mapping; 16.4.5 upper/lower simplices as consistent probabilities (Theorem 107)
- **16.5 Decision making with epistemic transforms** (p.642-646) — 16.5.1 Generalisations of TBM (Question 12); 16.5.2 game/utility interpretation (cloaked carnival wheel, minimax/maximin)
- **Appendix proofs Ch.16** (p.646-652) — Lemma 20, proofs of Thm 99-107, Cor 22, 23
- **Part V title page** (p.653)
- **Ch.17 opening** (p.655-656) — falls beyond Ch.16; chunk #10 owns Ch.17

## Chapter 15 overview

Chapter 15 introduces a fundamentally different approach to conditioning belief functions: instead of axiomatic rules (Dempster, Fagin-Halpern, geometric a la Suppes-Zanotti), one **projects** the original BF onto the "conditioning simplex" associated with the conditioning event A, under different L_p norms. The conditioning operation is therefore a geometric/metric construction. Two distinct ambient spaces matter — the **mass space M** (BPAs as vectors in R^{2^Θ}) and the **belief space B** (Bel as vector of belief values). The conditioning simplex M_A (or its image in B) is the set of "candidate" conditional BFs whose mass is concentrated on subsets of A. L₁, L₂ and L∞ conditioning give different projections; some coincide (L₁ and L₂ in M relate via barycentre), some give qualitatively different geometric objects, some yield pseudo-belief functions (negative masses) requiring an "admissible part" intersection with the simplex of valid BFs. Section 15.4 summarises the comparison; 15.5 sketches future research, including the question of whether Dempster conditioning is itself a special case of geometric conditioning (Question 10), and whether one can reverse-engineer combination rules from conditioning operators (Question 11).

The chapter's payoff for the broader book is a **general imaging interpretation** of L₁/L₂ conditioning in M: the mass redistribution induced by L_p projection generalises Lewis-style probabilistic imaging to belief functions. This connects geometric conditioning to the imaging literature (refs [1417, 665]).

## Chapter 16 overview

Chapter 16 reinterprets the "epistemic family" of probability transforms (relative belief Bel̃, relative plausibility Pl̃, intersection probability p[Bel]) through credal sets — convex sets of consistent probabilities — extending the credal interpretation that the pignistic transform BetP[Bel] enjoys (centre of mass of P[Bel]). The central geometric construction is **the focus of a pair of simplices** (Def. 134): the unique point whose lines through corresponding vertex pairs all meet. Each Bayesian transformation is shown to be a special focus of a particular pair of simplices drawn from the triad {P, T¹[Bel], T^{n-1}[Bel]}, where T¹[Bel] (lower simplex) and T^{n-1}[Bel] (upper simplex) embody the lower and upper probability constraints on singletons. This unifies the geometric semantics of all four Bayesian transforms in one diagram.

Section 16.5 then proposes TBM-like decision frameworks built on top of these credal interpretations. Three pairings — {P[Bel], T¹[Bel]} ↔ Bel̃, {P[Bel], T^{n-1}[Bel]} ↔ Pl̃, {T¹[Bel], T^{n-1}[Bel]} ↔ p[Bel] — give three TBM-style "credal-set + summary-probability" pairs. The chapter closes with a game-theoretic ("cloaked carnival wheel") reading: relative belief and plausibility describe maximin/minimax strategies of a decision maker against an adversary who chooses any consistent distribution.

## Definitions

### Definition 133 (intersection probability) *(p.633)*
The intersection probability $p[(l,u)] : \Theta \to [0,1]$ associated with the interval probability system $(6.10)$ is the probability distribution
$$p[(l,u)](x) \doteq \beta[(l,u)] u(x) + (1-\beta[(l,u)]) l(x)$$
with $\beta[(l,u)]$ given by (16.13).

### Definition 134 (focus of a pair of simplices) *(p.636)*
Consider two simplices in $\mathbb{R}^{n-1}$, $S = Cl(s_1,\ldots,s_n)$ and $T = Cl(t_1,\ldots,t_n)$, with the same number of vertices. If there exists a permutation $\rho$ of $\{1,\ldots,n\}$ such that the intersection
$$\bigcap_{i=1}^n a(s_i, t_{\rho(i)})$$
of the lines joining corresponding vertices of the two simplices exists and is unique, then $p = f(S,T) \doteq \bigcap_{i=1}^n a(s_i, t_{\rho(i)})$ is termed the **focus** of the two simplices.

A focus is **special** if the affine coordinates of $f(S,T)$ on the lines $a(s_i, t_{\rho(i)})$ all coincide: $\exists \alpha \in \mathbb{R}$ such that $f(S,T) = \alpha s_i + (1-\alpha) t_{\rho(i)}$ for all $i$ (Eq. 16.21).

### Set definitions in Ch.16

- **Probability interval system / credal set** (Eq. 16.1): $\mathcal{P}[(l,u)] \doteq \{p : l(x) \le p(x) \le u(x), \forall x \in \Theta\}$.
- **Lower simplex** (Eq. 16.3): $T[l] \doteq \{p : p(x) \ge l(x) \,\forall x \in \Theta\}$. **Upper simplex** $T[u] \doteq \{p : p(x) \le u(x) \,\forall x \in \Theta\}$.
- $T^i[Bel] \doteq \{P' \in \mathcal{P}' : P'(A) \ge Bel(A), \forall A : |A|=i\}$ — pseudo-probability sets (Eq. 16.6, 16.7 specialise to $i=1$ and $i=n-1$).
- $\mathcal{P}^i[Bel]$ (Eq. 16.5): probabilities (not pseudo) satisfying lower-bound on size-$i$ events. $\mathcal{P}^n[Bel] = \mathcal{P}$.
- $\mathcal{P}[Bel]$: full credal set of consistent probabilities (Eq. 16.4): $\mathcal{P}[Bel] = \bigcap_{i=1}^{n-1} \mathcal{P}^i[Bel]$.

## Theorems / Propositions / Lemmas

### Lemma 18 (L₁ norm for Bel - Bel_a) *(p.606)*
$$\|Bel - Bel_a\|_{L_1} = \sum_{\emptyset \subsetneq B\cap A \subsetneq A} |\gamma(B\cap A) + Bel(B) - Bel(B\cap A)|$$
where $\gamma(B) = \sum_{C\subseteq B} \beta(C)$ and $\beta(B) = m(B) - m_a(B)$. Hence the L₁ conditional BFs in B solve $\arg\min_\gamma \sum_{\emptyset \subsetneq B\cap A \subsetneq A} |\gamma(B\cap A) + Bel(B) - Bel(B\cap A)|$.

### Theorem 96 (L₂ conditional BF in B is barycentre of L₁ polytope in ternary case) *(p.607)*
For every BF $Bel : 2^{\{x,y,z\}} \to [0,1]$, the unique L₂ conditional BF $Bel_{L_2,\mathcal{B}_3}(\cdot|\{x,y\})$ with respect to $A \subseteq \{x,y,z\}$ in $\mathcal{B}_3$ is the barycentre of the polytope of L₁ conditional belief functions with respect to $A$ in $\mathcal{B}_3$.

### Lemma 19 *(p.609)*
Values $\gamma^*(X)$ minimising (15.23) satisfy, $\forall \emptyset \subsetneq X \subsetneq A$:
$$-(1 - Bel(A)) \le \gamma^*(X) \le (1-Bel(A)) - \sum_{\substack{C\cap A^c \neq \emptyset \\ C\cap A \subseteq X}} m(C). \quad (15.24)$$

### Theorem 97 (L∞ conditional BFs in B) *(p.609)*
Given a BF $Bel$ and arbitrary non-empty focal $\emptyset \subsetneq A \subseteq \Theta$, the set of L∞ conditional BFs $Bel_{L_\infty, \mathcal{B}}(\cdot|A)$ with respect to $A$ in $\mathcal{B}$ is the set of BFs with focal elements in $\{X \subseteq A\}$ satisfying, $\forall \emptyset \subsetneq X \subseteq A$:
$$m(X) + \sum_{\substack{C\cap A^c \neq \emptyset \\ \emptyset \subseteq C\cap A \subseteq X}} m(C) + (2^{|X|}-1)(1-Bel(A)) \le m_a(X)$$
$$\le m(X) + (2^{|X|}-1)(1-Bel(A)) - \sum_{\substack{C\cap A^c \neq \emptyset \\ \emptyset \subseteq C\cap A \subsetneq X}} m(C) - (-1)^{|X|}\sum_{B\subseteq A^c} m(B). \quad (15.25)$$

### Theorem 98 (Barycentre of L∞ in B) *(p.610)*
The centre of mass of the set of L∞ conditional BFs $Bel_{L_\infty,\mathcal{B}}(\cdot|A)$ in B is the unique solution of the system (15.26), with BPA
$$m_{L_\infty,\mathcal{B}}(C|A) = m(C) + \frac{1}{2}\sum_{\emptyset \subsetneq B\subseteq A^c}\Big[m(B\cup C) + (-1)^{|C|+1}m(B)\Big]$$
$$= m(C) + \frac{1}{2}\sum_{\emptyset \subsetneq B\subseteq A^c} m(B+C) + \frac{1}{2}(-1)^{|C|+1}Bel(A^c). \quad (15.27)$$

### Theorem 99 (lower simplex T¹[Bel] is a simplex; upper simplex T^{n-1}[Bel] is too) *(p.631)*
$T^1[Bel] = Cl(t^1_x[Bel], x \in \Theta)$ where
$$t^1_x[Bel] = \sum_{y\neq x} m(y) Bel_y + \Big(1 - \sum_{y\neq x} m(y)\Big) Bel_x \quad (16.9)$$
Dually, $T^{n-1}[Bel] = Cl(t^{n-1}_x[Bel], x \in \Theta)$ with
$$t^{n-1}_x[Bel] = \sum_{y\neq x} Pl(y) Bel_y + \Big(1 - \sum_{y\neq x} Pl(y)\Big) Bel_x. \quad (16.11)$$
$T^1[Bel] = \mathcal{P}^1[Bel]$ (Eq. 16.12) — entirely in the probability simplex. $T^{n-1}[Bel]$ vertices are pseudo-probabilities.

### Proposition 66 (vertices of P[Bel]) *(p.634)*
$\mathcal{P}[Bel] = Cl(P^\rho[Bel], \forall \rho)$ where for permutation $\rho$ the vertex Bayesian BF is $P^\rho[Bel](x_{\rho(i)}) = \sum_{A\ni x_{\rho(i)}, A\not\ni x_{\rho(j)} \forall j<i} m(A)$ (Eq. 16.18).

### Theorem 100 (special focus has same affine coords) *(p.637)*
Any special focus $f(S,T)$ has same affine coordinates in both simplices: $f(S,T) = \sum_i \alpha_i s_i = \sum_j \alpha_j t_{\rho(j)}$, $\sum \alpha_i = 1$.

### Theorem 101 (relative belief is special focus of {P, T¹[Bel]}) *(p.638)*
Bel̃ has same affine coordinates in P and in T¹[Bel].

### Theorem 102 (relative plausibility is special focus of {P, T^{n-1}[Bel]}) *(p.638)*
Pl̃ has same affine coordinates in P and T^{n-1}[Bel].

### Theorem 103 *(p.638)*
The relative belief Bel̃ is the special focus of {P, T¹[Bel]}, with affine coordinate on the corresponding intersecting lines equal to the reciprocal $1/k_{Bel}$ of the total mass of singletons. ($\alpha = (k_{Bel}-1)/k_{Bel}$ in proof, p.649.)

### Theorem 104 *(p.638)*
The relative plausibility Pl̃ is the special focus of {P, T^{n-1}[Bel]}, with affine coordinate $1/k_{Pl}$ on the intersecting lines.

### Theorem 105 *(p.638)*
For each BF Bel, the intersection probability $p[Bel]$ has the same affine coordinates in lower and upper simplices T¹[Bel] and T^{n-1}[Bel] respectively. The common affine coordinates are the relative uncertainty function $R[Bel](x) = (Pl(x) - m(x))/(k_{Pl} - k_{Bel})$ (Eq. 16.27).

### Theorem 106 *(p.639)*
The intersection probability is the special focus of the pair of lower and upper simplices {T¹[Bel], T^{n-1}[Bel]}, with its affine coordinate on the corresponding intersecting lines equal to $\beta[Bel]$ (Eq. 11.10).

### Theorem 107 (lower/upper simplices as consistent probabilities) *(p.641)*
$T^1[Bel] = \mathcal{P}[\overline{Bel}]$ — the simplex associated with the lower probability constraint on singletons is the set of probabilities consistent with the **belief of singletons** $\overline{Bel}$ (the categorical pseudo-belief on singletons).
$T^{n-1}[Bel] = \mathcal{P}[\overline{Pl}]$ — analogously for plausibility of singletons.

### Corollary 22 (barycentres are pignistic transforms of consonant approximations) *(p.642)*
$$t^1[Bel] = BetP[\overline{Bel}], \quad t^{n-1}[Bel] = BetP[\overline{Pl}].$$

### Corollary 23 (intersection probability as convex combination of barycentres) *(p.642)*
$$p[Bel] = \beta[Bel] t^{n-1}[Bel] + (1-\beta[Bel]) t^1[Bel].$$

### Lemma 20 (affine independence) *(p.646)*
Points $\{t^1_x[Bel], x \in \Theta\}$ are affinely independent — needed so that $T^1[Bel]$ is genuinely a simplex.

## Equations (Chapter 15)

$$\|Bel - Bel_a\|_{L_1} = \sum_{\emptyset \subsetneq B\cap A \subsetneq A} |\gamma(B\cap A) + Bel(B) - Bel(B\cap A)|$$
**(p.606)** — Lemma 18.

$$\arg\min_{\gamma(X)} \sum_{B: B\cap A = X} |\gamma(X) + Bel(B) - Bel(X)| \quad \forall \emptyset \subsetneq X \subsetneq A. \quad (15.18)$$

$$Bel(X) - Bel(B^X_{int_1}) \le \gamma(X) \le Bel(X) - Bel(B^X_{int_2}). \quad (15.19)$$
Where $B^X_{int_1}, B^X_{int_2}$ are events corresponding to the two median values of the collection $\{Bel(B), B\cap A = X\}$. Median computation is generally infeasible since BFs live on a partially ordered power set $2^\Theta$.

**Special case** $|A^c| = 1$: $B^X_{int_1} = X + A^c$, $B^X_{int_2} = X$, so $Bel(X) - Bel(X + A^c) \le \gamma(X) \le 0$ for $\emptyset \subsetneq X \subsetneq A$ (p.606).

In ternary: barycentre of L₁ solutions is $\beta(x) = -(m(z)+m(\{x,z\}))/2$, $\beta(y) = -(m(z)+m(\{y,z\}))/2$ — i.e. the L₂ conditional BF Eq. (15.17), p.607.

L₁ conditional BFs (ternary, A={x,y}) satisfy $Bel(B) \le m_{L_1,\mathcal{B}}(B|A) \le Bel(B \cup A^c)$ — they sandwich between Bel and Bel of B-extended-with-A-complement (p.607).

L∞ system (ternary, masses on x,y,{x,y}): Eq. (15.20) and Eq. (15.21) — see ternary worked example below. Barycentre is Eq. (15.22):
$$m_a(x) = m(x) + \frac{m(z) + m(\{x,z\})}{2}, \quad m_a(y) = m(y) + \frac{m(z) + m(\{y,z\})}{2}, \quad m_a(\{x,y\}) = m(\{x,y\}) + m(\Theta) + \frac{m(\{x,z\}) + m(\{y,z\})}{2}.$$

General L∞ in B (Eq. 15.23): $\max_{\emptyset \subsetneq B \subsetneq \Theta} |Bel(B) - Bel_a(B)| = \max\{\ldots, |\gamma(A\cap B) + \sum_{C\subseteq B, C\not\subseteq A} m(C)|, \ldots, |\gamma(A) + \sum_{C\subseteq B, C\not\subseteq A} m(C)|\}$.

System (15.26): $\sum_{\emptyset \subsetneq C\subseteq X} \beta(C) + \frac{1}{2} \sum_{C\cap A^c \neq \emptyset, C\cap A\subseteq X} m(C) = 0$ for all $\emptyset \subsetneq X \subsetneq A$.

L₂ in M, Eq. (15.28): $m_{L_2,\mathcal{M}}(B|A) = m(B) + Pl(A^c)/(2^{|A|}-1)$, redistributing $Pl(A^c)$ uniformly across all $B \subseteq A$.

Comparison of belief-space conditioning formulas (p.611):
$$m_{L_2,\mathcal{B}}(B|A) = m(B) + \sum_{C\subseteq A^c} m(B+C) 2^{-|C|} + (-1)^{|B|+1}\sum_{C\subseteq A^c} m(C) 2^{-|C|}$$
$$m_{\overline{L_\infty},\mathcal{B}}(B|A) = m(B) + \frac{1}{2}\sum_{\emptyset \subsetneq C \subseteq A^c} m(B+C) + \frac{1}{2}(-1)^{|B|+1} Bel(A^c).$$

## Equations (Chapter 16)

$$\mathcal{P}[(l,u)] \doteq \{p : l(x) \le p(x) \le u(x), \forall x \in \Theta\}. \quad (16.1)$$

Lower / upper probabilities induced (16.2):
$$\underline{P}(A) = \max\Big\{\sum_{x\in A} l(x), 1 - \sum_{x\notin A} u(x)\Big\}$$
$$\overline{P}(A) = \min\Big\{\sum_{x\in A} u(x), 1 - \sum_{x\notin A} l(x)\Big\}$$

$$T[l] = \{p : p(x) \ge l(x) \forall x\}, \quad T[u] = \{p : p(x) \le u(x) \forall x\}. \quad (16.3)$$

$$\mathcal{P}[Bel] = \bigcap_{i=1}^{n-1} \mathcal{P}^i[Bel]. \quad (16.4)$$
$$\mathcal{P}^i[Bel] = \{P \in \mathcal{P} : P(A) \ge Bel(A), \forall A: |A|=i\}. \quad (16.5)$$

$$T^1[Bel] = \{p' \in \mathcal{P}' : p'(x) \ge Bel(x) \forall x\}. \quad (16.6)$$
$$T^{n-1}[Bel] = \{p' \in \mathcal{P}' : p'(x) \le Pl(x) \forall x\}. \quad (16.7)$$

Vertices: Eq. (16.8)-(16.11). Vertex masses (p.632):
- Lower vertex $t^1_x[Bel]$: $m(x) = m(x)+1-k_{Bel}$, $m(y) = m(y), \forall y\neq x$. All in P.
- Upper vertex $t^{n-1}_x[Bel]$: $m(x) = Pl(x) + (1 - k_{Pl})$ (can be negative when $k_{Pl} > 1$), $m(y) = Pl(y), \forall y \neq x$.

Where $k_{Bel} = \sum_x m(x)$ (total singleton mass), $k_{Pl} = \sum_x Pl(x)$ (total singleton plausibility).

$$\mathcal{P}[(Bel,Pl)] = T^1[Bel] \cap T^{n-1}[Bel]. \quad (\text{p.632})$$

Intersection probability (Definition 133, Eqs 16.13-16.16):
$$\alpha = \beta[(l,u)] = \frac{1 - \sum_{x\in\Theta} l(x)}{\sum_{x\in\Theta}(u(x) - l(x))} \quad (16.13)$$
$$p[(l,u)](x) = \beta[(l,u)] u(x) + (1 - \beta[(l,u)]) l(x). \quad (16.14)$$
$$p[(l,u)](x) = l(x) + \Big(1 - \sum_x l(x)\Big) R[(l,u)](x). \quad (16.15)$$
$$R[(l,u)](x) = \frac{u(x) - l(x)}{\sum_{y\in\Theta}(u(y) - l(y))} = \frac{\Delta(x)}{\sum_{y\in\Theta} \Delta(y)}. \quad (16.16)$$

Vertices of credal set (Eq. 16.18):
$$P^\rho[Bel](x_{\rho(i)}) = \sum_{A \ni x_{\rho(i)}, A \not\ni x_{\rho(j)} \forall j<i} m(A).$$

Focus / mapping equations:
$$\bigcap_{i=1}^n a(s_i, t_{\rho(i)}). \quad (16.20)$$
$$f(S,T) = \alpha s_i + (1-\alpha) t_{\rho(i)} \forall i. \quad (16.21) \text{ (special focus)}$$
$$\Big\{p \in \mathbb{R}^{n-1} \mid p = \sum_i \alpha_i s_i = \sum_j \alpha_j t_{\rho(j)}, \sum \alpha_i = 1\Big\}. \quad (16.22)$$

Mapping induced by a pair (S,T) (Eq. 16.23):
$$F^\rho_{S,T} : \mathbb{R}^{n-1} \to \mathbb{R}^{n-1}, \quad p = \sum_i \alpha_i s_i \mapsto \sum_i \alpha_i t_{\rho(i)}.$$
The special focus is a fixed point: $F^\rho_{S,T}(f(S,T)) = f(S,T)$.

Maps between probabilities (Eqs 16.24, 16.25):
$$F_{\mathcal{P}, T^1[Bel]}(p) = \sum_x Bel_x [m(x) + p(x)(1 - k_{Bel})]$$
$$F_{\mathcal{P}, T^{n-1}[Bel]}(p) = \sum_x Bel_x [Pl(x) + p(x)(1 - k_{Pl})]$$
Both map relative uncertainty $R[Bel]$ to the intersection probability $p[Bel]$.

Triad of foci (Eq. 16.26, p.643):
$$\{\mathcal{P}, T^1[Bel]\} : f(\mathcal{P}, T^1[Bel]) = \tilde{Bel}$$
$$\{\mathcal{P}, T^{n-1}[Bel]\} : f(\mathcal{P}, T^{n-1}[Bel]) = \tilde{Pl}$$
$$\{T^1[Bel], T^{n-1}[Bel]\} : f(T^1[Bel], T^{n-1}[Bel]) = p[Bel].$$

Relative uncertainty (Eq. 16.27): $R[Bel](x) = (Pl(x) - m(x))/(k_{Pl} - k_{Bel})$.

## Geometric structures

### Conditioning simplex M_A (mass space, recap from earlier 15.x)
- Set of BFs whose focal elements are subsets of A
- Lives in the simplex of all BPAs
- L₁ conditioning chooses vertices satisfying $m_a(B) \ge m(B)$ (mass dominance on subsets of A)
- L₂ conditioning is barycentre of the L₁ polytope; redistributes $Pl(A^c)$ uniformly to all $B\subseteq A$

### Conditioning polytope in B
- L₁ polytope $\mathcal{M}_{L_1,A}[Bel] = Cl(m[Bel]|^B_{L_1}A, \emptyset \subsetneq B \subseteq A)$ with vertices computed via system (15.30)-(15.31)
- L∞ in B: simplex $Cl(m[Bel]|^{L_\infty}_{\bar B}A, \bar B \subseteq A)$ when condition (15.34) holds: $\max_{C\not\subset A} m(C) \ge \frac{1}{2^{|A|}-1}\sum_{C\not\subset A} m(C)$; else the system has unique solution coinciding with L₂

### Triad of simplices (Ch.16, central object, p.643)
{P, T¹[Bel], T^{n-1}[Bel]}
- **P** — full probability simplex, vertices Bel_x (categorical probabilities at singletons)
- **T¹[Bel]** — lower simplex, $n$ vertices $t^1_x[Bel]$, all genuine probabilities; **equals** $\mathcal{P}^1[Bel]$
- **T^{n-1}[Bel]** — upper simplex, $n$ vertices $t^{n-1}_x[Bel]$, possibly pseudo-probabilities (can have negative mass when $k_{Pl} > 1$)
- Pairwise foci of these three simplices yield: Bel̃, Pl̃, p[Bel]
- $\mathcal{P}[Bel] \subseteq T^1[Bel] \cap T^{n-1}[Bel] = \mathcal{P}[(Bel, Pl)]$

### Focus geometry
- $f(S,T)$: unique intersection of $n$ lines $a(s_i, t_{\rho(i)})$ joining corresponding vertices (Def. 134, Fig. 16.1).
- **Special focus** has equal affine coordinate $\alpha$ on every connecting line — the same convex combination $\alpha s_i + (1-\alpha)t_{\rho(i)}$ for all i.
- Barycentre is a special case of a (special) focus, where T is the simplex of midpoint barycentres of S's $(d-1)$-faces (Fig. 16.4).

## Worked examples

### Example 50: ternary L∞ conditioning in B *(p.607-608)*
$\Theta = \{x,y,z\}$, $A = \{x,y\}$. Computes $\|Bel - Bel_a\|_{L_\infty}$ as max over 6 absolute-value terms. Reduces (after change of variable $\beta$) to system (15.20). Solution in masses: Eq. (15.21). Barycentre Eq. (15.22) — coincides with L₂ conditional BF (15.17).

### Example 51: ternary comparison of conditioning approximations *(p.612)*
- $\Theta = \{x,y,z\}$, $A = \{x,y\}$, mass: $m(x) = 0.2$, $m(y) = 0.3$, $m(\{x,z\}) = 0.5$ (per Example 47).
- L₁ vertices in $\mathcal{M}_{L_1,\{x,y\}}[Bel]$: $[m(x)+Pl(z), m(y), m(\{x,y\})]$, $[m(x), m(y)+Pl(z), m(\{x,y\})]$, $[m(x), m(y), m(\{x,y\})+Pl(z)]$ — vertices of conditioning simplex in M.
- L₂ in M: BPA $m'(x) = m(x) + (1-Bel(\{x,y\}))/3 = m(x) + Pl(z)/3$, etc. (lies at barycentre of L₁ M-simplex).
- L₂ in B (the pink square in Fig 15.2) is barycentre of L∞ B polytope (orange rectangle).
- L₁ in B is a line segment whose barycentre is L₂ in B — entirely admissible, entirely contained in L∞ approximations both in B and M, "more conservative".
- Empirical observations: $m_{L_\infty,\mathcal{B}}$ contains $m_{L_1,\mathcal{M}}$; the two L₂ conditional BFs lie on a line joining opposite vertices of $m_{L_\infty,\mathcal{B}}$; $m_{L_\infty,\mathcal{B}}$ and $m_{L_\infty,\mathcal{M}}$ share several vertices.

### Ternary case Ch.16 (Section 16.3, p.634-636)
- $\Theta = \{x,y,z\}$, masses (Eq. 16.17): $m(x)=.2, m(y)=.1, m(z)=.3, m(\{x,y\})=.1, m(\{y,z\})=.2, m(\Theta)=.1$.
- $\mathcal{P}[Bel]$ has 5 vertices $P^{\rho^k}[Bel]$ (Eq. 16.19): purple squares.
- Two purple triangles: $T^1[Bel]$ (light blue), $T^2[Bel]$ (regular triangle in ternary).
- Fig. 16.3 shows: $\mathcal{P}[Bel]$ = $T^1 \cap T^2$. Bel̃ = intersection of lines joining $\mathcal{P}, T^1$ corresponding vertices: $\tilde{Bel}(x) = .2/.6 = 1/3$, $\tilde{Bel}(y) = .1/.6 = 1/6$, $\tilde{Bel}(z) = .3/.6 = 1/2$. Pl̃: $\tilde{Pl}(x) = .4/(.4+.5+.6) = 4/15$, $\tilde{Pl}(y) = .5/1.5 = 1/3$, $\tilde{Pl}(z) = 2/5$. p[Bel]: $p[Bel](x) = m(x) + \beta[Bel](m(\{x,y\})+m(\Theta)) = .2 + (.4*.2)/(1.5-.4) = .27$ (numerically: .27, .245, .485), as intersection of lines joining $T^1, T^2$ corresponding vertices.
- Bel̃, Pl̃ "happen" to lie inside $\mathcal{P}[Bel]$ in this ternary case (artefact); in general only $\mathcal{P}[(Bel, Pl)] = T^1 \cap T^{n-1}$ is guaranteed to contain the epistemic transforms.

### Cloaked carnival wheel *(p.643-646, Fig. 16.5)*
- Carnival wheel sectors {♣, ◇, ♡, ♠} with sectors of areas (probabilities) per "fair" wheel.
- Manager covers (cloaks) part of the wheel — players see uncovered sectors only, but know hidden share is $1 - \sum$ visible.
- Belief function: $m(\{♣, ◇, ♡, ♠\}) = $ mass of hidden sector.
- Player wants to bet single outcome maximising minimum chance.
- Maximin: $x_{maximin} = \arg\max_x Bel(x) = \arg\max_x \tilde{Bel}(x) = \arg\max_x \min_{P \in \mathcal{P}[Bel]} P(x)$.
- Minimax (loss): $x_{minimax} = \arg\min_x \tilde{Pl}(x) = \arg\min_x \max_{P \in \mathcal{P}[Bel]} P(x)$.
- Generalisations with non-constant utility/loss: $x_{maximin} = \arg\max_x \tilde{Bel}(x) u(x)$, $x_{minimax} = \arg\min_x \tilde{Pl}(x) l(x)$.
- Decision-theoretic role: relative belief and plausibility as **safest betting strategies** in modified Wald (adversary picks any consistent distribution).

## Algorithms / procedures

No explicit numbered algorithms; computation is described as systems of constraints / minimisation problems:

- L₁ in M: minimise $\|m - m_a\|_{L_1}$ → mass-dominance constraints $m_a(B) \ge m(B), \forall \emptyset \subsetneq B \subseteq A$. Vertices = each $m_a$ such that one $B^* \subseteq A$ absorbs all mass $1 - Bel(A) = Pl(A^c)$ above $m(B^*)$, others equal $m(B)$.
- L₂ in M: closed form (15.28), $m_{L_2,\mathcal{M}}(B|A) = m(B) + Pl(A^c)/(2^{|A|}-1)$.
- L∞ in M: equal to L₂ if (15.34) holds; else union of vertices each with one B-outside-A "winning" the maximum.
- L∞ in B: solve system (15.25); barycentre via system (15.26), unique solution Eq. (15.27).

## Parameters / quantities

| Name | Symbol | Domain | Page | Notes |
|------|--------|--------|------|-------|
| L_p norm of difference vector | $\|Bel - Bel_a\|_{L_p}$ | $\ge 0$ | 606,607,609 | objective for geometric conditioning |
| Auxiliary mass-difference | $\beta(B) = m(B) - m_a(B)$ | $\mathbb{R}$ | 606,614 | candidate offset on each subset |
| Cumulative offset | $\gamma(B) = \sum_{C\subseteq B} \beta(C) = Bel(B) - Bel_a(B)$ | $\mathbb{R}$ | 606,608 | |
| Lower bound | $l(x)$ | $[0,1]$ | 628 | interval lower probability |
| Upper bound | $u(x)$ | $[0,1]$ | 628 | interval upper probability |
| Total singleton mass | $k_{Bel} = \sum_x m(x)$ | $[0,1]$ | 632,648 | |
| Total singleton plausibility | $k_{Pl} = \sum_x Pl(x)$ | $\ge 1$ when nontrivial | 632,649 | |
| Width of probability interval | $\Delta(x) = u(x) - l(x)$ | $[0,1]$ | 634 | |
| Relative uncertainty | $R[(l,u)](x) = \Delta(x)/\sum_y \Delta(y)$ | $[0,1]$ | 634,649 | |
| Intersection probability coefficient | $\beta[(l,u)] = (1-\sum l)/\sum \Delta$ | $[0,1]$ | 633 | $(16.13)$ |
| Permutation index | $\rho$ | $S_n$ | 634,636 | indexes vertex pairing for foci |
| Special focus shared coordinate | $\alpha$ | $\mathbb{R}$ | 637 | may be $<0$ or $>1$ (focus outside both simplices) |
| Affine coords for special focus Bel̃ | $1/k_{Bel}$ | $(0,\infty)$ | 638,649 | |
| Affine coords for special focus Pl̃ | $1/k_{Pl}$ | $(0,\infty)$ | 638,649 | |
| Affine coords for special focus p[Bel] | $\beta[Bel]$ | $(0,1)$ | 639 | |

## Figures of interest

- **Fig. 15.2 (p.613):** L∞ B-conditional set drawn as orange rectangle (BF with masses 15.12, A={x,y}). Conditioning simplex 2D with vertices $m_x, m_y, m_{\{x,y\}}$. L₁ B set is blue line segment with barycentre at L₂ B (pink square). Visualises how all four geometric conditioning constructions sit in the same low-dimensional picture.
- **Fig. 16.1 (p.629):** Two triangles S, T with each $s_i$ joined by a line to its $t_{\rho(i)}$; lines all meet at the focus $f$ inside both triangles. Illustrates when a focus exists.
- **Fig. 16.2 (p.633):** Three intervals $[l(x), u(x)], [l(y), u(y)], [l(z), u(z)]$ on a number line, with the same fraction $\alpha$ of each interval's length added to its lower bound to land on $p(x), p(y), p(z)$ summing to 1. Defines $\alpha$ uniquely as $\beta[(l,u)]$.
- **Fig. 16.3 (p.635):** The polytope $\mathcal{P}[Bel]$ as intersection of two triangles $T^1[Bel], T^2[Bel]$ in the ternary probability simplex. Shows Bel̃, Pl̃, p[Bel] as foci; dashed lines for {T¹,P}, {P,T²}; solid lines for {T¹,T²}.
- **Fig. 16.4 (p.638):** A 2-simplex S whose barycentre b is the focus of S and the simplex T formed by midpoints of S's edges. Demonstrates "barycentre is a special focus".
- **Fig. 16.5 (p.644):** Carnival wheel with sectors {♣, ◇, ♡, ♠} and a violet "??" cloaked region; visualises the BF $m(\Theta) = $ cloaked area.

## Criticisms of prior work

- **L₁ in B difficult to interpret in mass terms** *(p.607)*: "Not only are the resulting conditional (pseudo-)belief functions not guaranteed to be proper belief functions, but it is also difficult to find straightforward interpretations of these results in terms of degrees of belief. On these grounds, we might be tempted to conclude that the L₁ norm is not suitable for inducing conditioning in belief calculus." — But ternary analysis suggests admissible L₁ part is interesting.
- **L₂ in B hard to interpret generally** *(p.611)*: "For the L₂ case, the result makes a lot of sense in the ternary case, but it is difficult to interpret in its general form. It seems to be related to the process of mass redistribution among all subsets...". Belief-space conditioning generally has "rather less straightforward interpretations than the corresponding quantities in the mass space."
- **Walley's theory (Ch.17 setup)** *(p.655)*: belief theory "does not require one to abandon the notion of an event" — implicit critique of Walley's lower-prevision-only foundation that gives up event probabilities.
- **Ternary credal Bel̃, Pl̃ membership artefact** *(p.636)*: Although Fig. 16.3 suggests Bel̃, Pl̃, p[Bel] are consistent with Bel, this is "a mere artefact of this ternary example, for we proved in Theorem 53 that neither the relative belief of singletons nor the relative plausibility of singletons necessarily belongs to the credal set $\mathcal{P}[Bel]$." Each is consistent with the larger interval system $\mathcal{P}[(Bel, Pl)]$, but not with $\mathcal{P}[Bel]$.

## Design rationale

- **Why M (mass space) vs B (belief space) matters** *(p.611-612)*: Same L_p norm gives different geometric conditioning depending on which space one minimises in. Mass space conditioning is interpretable via mass redistribution / general imaging. Belief-space conditioning is more abstract; L₁ in B can yield admissible-but-pseudo-BFs requiring intersection with the simplex of valid BFs.
- **Why epistemic transforms admit credal interpretation** *(p.627-628, 642-643)*: Pignistic has clear credal semantics (centre of mass of $\mathcal{P}[Bel]$); but Bel̃, Pl̃, p[Bel] needed an analogous explanation. Sec 16.4 supplies it via foci of paired simplices, where each pair encodes a different probability constraint (lower, upper, both).
- **Why intersection probability via "homogeneous behaviour"** *(p.639, "Semantics of foci and a rationality principle")*: Selecting the special focus = adopting the unique probability that satisfies both constraint sets in **exactly the same way** (same convex coordinate $\alpha$ on every connecting line). Thus the rationality principle "homogeneous behaviour in the two constraint sets" → intersection probability uniquely.
- **TBM-like framework as triple {credal set, summary, transformation}** *(p.642-643)*: TBM = pair $\{\mathcal{P}[Bel], BetP[Bel]\}$. The chapter proposes three TBM analogues, one per constraint type:
  - {{P[Bel], T¹[Bel]}, Bel̃} — lower constraint
  - {{P[Bel], T^{n-1}[Bel]}, Pl̃} — upper constraint
  - {{T¹[Bel], T^{n-1}[Bel]}, p[Bel]} — interval constraint

## Open / research questions

### Question 10 *(p.613)*
"What classes of conditioning rules can be generated by a distance minimisation process, such as that introduced here? Do they span all known definitions of conditioning (Section 4.5), once one applies a sufficiently general class of dissimilarity measures?"

In particular: **is Dempster conditioning itself a special case of geometric conditioning?**

### Question 11 *(p.614)*
"Can we imagine reversing this link, and generating combination rules ⊎ as convex combinations of conditioning operators $Bel|^\uplus_A$? That is,
$$Bel \uplus Bel' = \sum_{A\subseteq\Theta} m'(A) Bel \uplus Bel_A = \sum_{A\subseteq\Theta} m'(A) Bel|^\uplus_A.$$
Additional constraints (e.g. commutativity with affine combination, **linearity** in Smets's terminology [1697]) may be needed for uniqueness."

The Dempster decomposition $Bel \oplus Bel' = \sum_{A\subseteq\Theta} \mu(A) Bel \oplus Bel_A$ where $\mu(A) \propto m'(A) Pl(A)$ is the model.

### Question 12 *(p.643)*
"What are the most appropriate elicitation operators for lower, upper and interval probability systems? How are they related to combination rules for belief functions in the case of probability intervals induced by belief functions?"

### Implicit open problem *(p.612)*
"Finding the admissible parts of $m_{L_\infty,\mathcal{B}}(\cdot|A)$ and $m_{L_\infty,\mathcal{M}}(\cdot|A)$, for instance, remains an open problem."

## Notable references cited

- `[1417, 665]` — general imaging interpretation of L_p mass-space conditioning *(p.611)*
- `[1697]` Smets — linearity terminology for combination *(p.614)*
- `[2033]` Dempster, Shafer foreword to "Classic Works of the Dempster-Shafer Theory" *(p.656)*
- `[1730, 1717]` Smets — TBM and pignistic-based decision *(p.627)*
- `[1808, 393]` — probability intervals (Lemmer-Kyburg, de Campos et al.) *(p.627)*
- `[1141]` Levi — credal set terminology *(p.628)*
- `[1827]` Walley / others — multiple optimal decisions issue *(p.628)*
- `[344]` Cuzzolin earlier paper introducing the upper/lower simplex decomposition *(p.628)*
- `[863]` — interval measurements as natural source of probability intervals *(p.628)*
- `[1858, 1768, 1548]` Strat / utility theory references for game-theoretic interpretation *(p.643-644)*
- `[1858, 1769, 883]` — game/utility theory interpretation of relative belief/plausibility *(p.643)*
- `[1689]` Smets TBM combination rules *(p.643)*
- `[1607, 422, 1613]` references on probability semantics in DS agenda *(p.656)*
- `[468]` Shafer on statistical modelling *(p.656)*
- `[1708]` Smets, real-life applications of belief functions *(p.656)*

## Implementation notes for propstore

This pair of chapters connects directly to several propstore layers:

- **`propstore.belief_set` / IC merge** — the credal-set decomposition $\mathcal{P}[Bel] = T^1[Bel] \cap T^{n-1}[Bel]$ supports an interval-bounds-only sidecar that is much cheaper than full credal-vertex enumeration (Eq. 16.18 has factorial vertex count, but Eq. 16.6/16.7 are linear in n). For belief sets stored as $\{(l(x), u(x))\}_{x\in\Theta}$, intersection probability (Eq. 16.14) gives a TBM-compatible point summary that uses both bounds, and is honest-vacuous when $l = 0, u = 1$ throughout: $p[Bel](x) = 1/n$.
- **Render layer / decision** — the maximin/minimax pair $\{x_{maximin} = \arg\max \tilde{Bel}, x_{minimax} = \arg\min \tilde{Pl}\}$ (with utility/loss generalisation $\arg\max \tilde{Bel}(x) u(x)$, $\arg\min \tilde{Pl}(x) l(x)$) gives a natural resolution strategy for argumentation when stances induce belief intervals on outcomes. This is the **adversarial** sibling of the existing recency / sample_size / argumentation strategies.
- **`propstore.aspic_bridge` / Dung defeats from credal evidence** — three TBM-like frameworks (one per constraint pair) suggest pluggable summarisation pipelines: lower (Bel̃, conservative), upper (Pl̃, optimistic), interval (p[Bel], "rationality principle"). Each yields a different Dung defeat structure.
- **`propstore.world` / ATMS** — geometric conditioning can target an ATMS environment $A$ as the "conditioning event": project the global BF onto the simplex of BFs supported on $A$. Lower bound is L₁ (most conservative, mass-dominance), upper bound (L₂ in M) is closed-form $m_a(B) = m(B) + Pl(A^c)/(2^{|A|}-1)$ — straightforward to implement.
- **`propstore.support_revision`** — Question 11 (combination rules from conditioning operators) is exactly the support-incision question in disguise: revision-from-conditioning. Worth flagging in support_revision docstrings.
- **Provenance** — every probability-bearing summary needs a `transform` provenance tag: `pignistic`, `relative_belief`, `relative_plausibility`, `intersection`, with carrier identifying which credal-set / simplex pair was used as the (S,T) focus pair.

## Quotes worth preserving

- *"The set of L₁ conditional belief functions in B is, instead, a line segment whose barycentre is m_{L_2,B}(.|A). Such a set is: entirely included in the set of L∞ approximations in both B and M, thus representing a more conservative approach to conditioning; entirely admissible."* (p.612)
- *"Selecting the special focus of two simplices representing two different constraints (i.e., the point with the same convex coordinates in the two simplices) means adopting the single probability distribution which satisfies both constraints in exactly the same way."* (p.639) — This is the rationality principle for the intersection probability.
- *"Each Bayesian transformation in 1-1 correspondence with a pair of simplices (relative plausibility, relative belief and intersection probability) is therefore associated with a mapping of probabilities to probabilities."* (p.639)
- *"In conclusion, the relative belief and plausibility of singletons play an important role in determining the safest betting strategy in an adversarial scenario in which the decision maker has to minimise their maximum loss or maximise their minimum return."* (p.646)
- *"Their geometric behaviour as described by facts 2, 3 and 4 still holds in the general case."* (p.636) — The credal interpretation generalises beyond ternary.

## Reading status / chunk boundary note

Read all assigned PDF pages 620-679. Pages 620-668 (book pp.606-654) cover end of Ch.15 and all of Ch.16, the actual subject of this chunk. Pages 669-679 (book pp.655-666) are the Part V title page and start of Ch.17 ("An agenda for the future" — research programme, statistical random set theory, lower/upper likelihoods, Definitions 135-136, Lemmas 21-22, Theorems 108-109, Conjecture 1, Question 13). Ch.17 is chunk #10's responsibility per the chunk title; not extracted here.

**Note on chunk-#8 boundary.** This chunk's nominal book-page range (595-654) spans Ch.15 from its start, but the PDF range supplied (620-679) only enters Ch.15 at section 15.3.2 (book p.606). Pages 595-605 (sections 15.1, 15.2, and 15.3 / 15.3.1) must therefore be covered by chunk #8, and the synthesis step should be aware of that.

No pages failed to read. All Ch.15 and Ch.16 formal content (definitions 133-134, theorems 96-107, lemmas 17-20, corollaries 22-23, proposition 66, equations 15.18-15.47 and 16.1-16.27, the ternary examples 50 and 51 plus the §16.3 worked ternary, future-research Questions 10-12) is captured above.
