---
title: "Decision-Making with Belief Functions: a Review"
authors: "Thierry Denoeux"
year: 2019
venue: "International Journal of Approximate Reasoning"
doi_url: "https://doi.org/10.1016/j.ijar.2019.10.005"
---

# Decision-Making with Belief Functions: a Review

## One-Sentence Summary
A comprehensive review of decision criteria available when uncertainty is represented by Dempster-Shafer belief functions rather than single probability distributions, covering extensions of classical criteria, imprecise-probability methods, and Shafer's constructive approach, with clear guidance on which criteria suit which decision-making attitudes.

## Problem Addressed
When uncertainty is described by belief functions (mass functions on power sets) rather than precise probabilities, the standard Maximum Expected Utility (MEU) principle does not directly apply because a belief function induces an interval of expected utilities rather than a point value. The paper reviews and organizes the full landscape of decision rules that handle this richer uncertainty representation. *(p.1)*

## Key Contributions
- Systematic taxonomy of decision criteria under DS theory organized into three families: extensions of classical criteria, imprecise-probability criteria, and Shafer's constructive approach *(p.1)*
- Shows all criteria reduce to MEU when belief function is Bayesian (all focal sets are singletons) *(p.33)*
- Demonstrates that classical criteria under ignorance (maximin, maximax, Hurwicz, Laplace, minimax regret) each extend naturally to the belief function setting *(p.15-20)*
- Provides axiomatic foundations distinguishing complete vs. partial preference orderings under belief functions *(p.21-24)*
- Identifies the pignistic transformation as the dominant practical approach, with clear axiomatic justification *(p.17-18)*
- Connects belief function decision-making to the imprecise probability framework (maximality, E-admissibility) *(p.25-28)*

## Methodology
Literature review organizing decision methods into three categories: (1) extensions of classical decision theory criteria to belief functions, (2) approaches from the imprecise probability framework, and (3) Shafer's constructive decision theory. Each approach is illustrated on a running investment example with four acts and three states of nature. *(p.1-2)*

## Key Equations

### Mass function, Belief, and Plausibility

$$
Bel(A) = \sum_{B \subseteq A} m(B)
$$

$$
Pl(A) = 1 - Bel(\overline{A}) = \sum_{B \cap A \neq \emptyset} m(B)
$$

Where: $m$ is a mass function on $2^\Omega \to [0,1]$, $Bel(A)$ is the belief (lower probability bound), $Pl(A)$ is the plausibility (upper probability bound), $A \subseteq \Omega$ is a proposition.
*(p.12)*

### Credal Set (set of compatible probability measures)

$$
\mathcal{P}(m) = \{P \text{ probability measure} : \forall A \subseteq \Omega,\ P(A) \geq Bel(A)\}
$$

Where: $\mathcal{P}(m)$ contains all probability distributions consistent with the belief function. The lower and upper expectations over this set equal the Choquet integrals w.r.t. $Bel$ and $Pl$.
*(p.13)*

### Lower and Upper Expected Utilities

$$
\underline{E}_\mu(u) = \sum_A m(A) \min_{\omega \in A} u(\omega)
$$

$$
\overline{E}_\mu(u) = \sum_A m(A) \max_{\omega \in A} u(\omega)
$$

Where: $m(A)$ is the mass assigned to focal set $A$, $u(\omega)$ is the utility of state $\omega$. These are Choquet integrals w.r.t. $Bel$ and $Pl$ respectively.
*(p.15)*

### Generalized Hurwicz Criterion

$$
E_\alpha(u) = \sum_A m(A) \left[\alpha \min_{\omega \in A} u(\omega) + (1 - \alpha) \max_{\omega \in A} u(\omega)\right]
$$

Where: $\alpha \in [0,1]$ is the pessimism index. $\alpha = 1$ gives lower expected utility (pessimistic), $\alpha = 0$ gives upper (optimistic). Reduces to classical Hurwicz under total ignorance, to MEU when $m$ is Bayesian.
*(p.17)*

### Pignistic Transformation

$$
BetP(\omega) = \sum_{A : \omega \in A} \frac{m(A)}{|A|}
$$

Where: $BetP(\omega)$ is the pignistic probability of state $\omega$, obtained by distributing each focal set's mass equally among its elements. Mathematically identical to the Shapley value in cooperative game theory.
*(p.17-18)*

### Pignistic Expected Utility

$$
E_p(u) = \sum_\omega BetP(\omega) u(\omega) = \sum_A m(A) \frac{\sum_{\omega \in A} u(\omega)}{|A|}
$$

Where: This averages utility within each focal set, then weights by mass. It extends the Laplace criterion to belief functions. The ONLY transformation satisfying linearity + MEU principle.
*(p.18)*

### Generalized OWA Criterion

$$
E_\beta(u) = \sum_A m(A) F_\beta\big(u(\omega) : \omega \in A\big)
$$

Where: $F_\beta$ is the maximum-entropy OWA operator with degree of optimism $\beta \in [0,1]$. $\beta = 0$: lower (pessimistic), $\beta = 0.5$: pignistic, $\beta = 1$: upper (optimistic). Provides a single-parameter family interpolating between all three.
*(p.19)*

### Generalized Minimax Regret

$$
\overline{R}_i = \sum_j m(\{\omega_j\}) r_{ij}
$$

Where: $r_{ij} = \max_k u_{kj} - u_{ij}$ is the regret of choosing act $f_i$ when state $\omega_j$ obtains. When $m$ is Bayesian, this is identical to MEU (the regret term independent of $i$ cancels).
*(p.19-20)*

### Jaffray's Evidential Lottery Utility

$$
U(p) = \sum_l p_l \left[\alpha \cdot U(c_A) + (1-\alpha) \cdot U(c_B)\right]
$$

Where: $p_l$ are lottery probabilities, $c_A$ and $c_B$ are the worst and best consequences in focal set, $\alpha$ is the pessimism/ambiguity aversion parameter. Extends VNM to evidential lotteries.
*(p.21-22)*

### Ambiguity Index (linking Hurwicz to ambiguity attitudes)

$$
\alpha(\sigma) = \frac{U(\sigma) - U(c_A)}{U(c_B) - U(c_A)}
$$

Where: $\sigma$ is an evidential lottery with imprecise outcomes, $c_A$ worst consequence, $c_B$ best. The DM's ambiguity attitude is captured by how $\alpha$ varies with $\sigma$.
*(p.22)*

### Strong Dominance

$$
f_i \succ_{SD} f_k \text{ iff } \underline{E}_\mu(f_i) \geq \underline{E}_\mu(f_k) \text{ and } \overline{E}_\mu(f_i) \geq \overline{E}_\mu(f_k)
$$

Where: At least one inequality is strict. A partial preference relation — does not require completeness.
*(p.23)*

### Interval Bound Dominance

$$
f_i \succ_{IB} f_k \text{ iff } \underline{E}_\mu(f_i) \geq \underline{E}_\mu(f_k) \text{ and } \overline{E}_\mu(f_i) \geq \overline{E}_\mu(f_k)
$$

Formally: $f_i$ is at least as desirable as $f_k$ according to the Hurwicz criterion for ANY value of pessimism index $\alpha$.
*(p.23)*

### Maximality Criterion (Imprecise Probabilities)

$$
X_1 \succ_{max} X_2 \text{ iff } \underline{E}(X_1 - X_2) > 0
$$

Where: $\underline{E}$ is the lower expectation. $X_1$ is strictly preferred iff the lower expectation of the utility difference is positive — i.e., ALL compatible probability measures agree on the preference.
*(p.26)*

### E-admissibility

$$
X_i \text{ is E-admissible iff } \exists P \in \mathcal{P}(m) \text{ such that } E_P(X_i) \geq E_P(X_j) \ \forall j
$$

Where: An act is in the choice set if there EXISTS at least one compatible probability under which it maximizes expected utility. Can be computed via linear programming.
*(p.27-28)*

### Shafer's Constructive Score

$$
U(f) = \sum_{i=1}^n w_i \left(Bel_f(A_i) + Pl_f(A_i)\right)
$$

Where: $A_i$ are goals with weights $w_i$, $Bel_f$ and $Pl_f$ are belief and plausibility induced by act $f$'s mass function. This equals $u^+(f) - u^-(f)$ where $u^+ = \sum w_i Bel_f(A_i)$ (weight achieved) and $u^- = \sum w_i Bel_f(\overline{A_i})$ (weight precluded). Reduces to MEU when $m_f$ is Bayesian.
*(p.30-31)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Pessimism index | $\alpha$ | - | - | [0, 1] | p.4, 17 | 0 = optimistic, 1 = pessimistic; parameterizes Hurwicz criterion |
| Degree of optimism (OWA) | $\beta$ | - | 0.5 | [0, 1] | p.7, 19 | 0 = pessimistic, 0.5 = pignistic/Laplace, 1 = optimistic |
| OWA weights | $w_1, \ldots, w_s$ | - | - | sum to 1 | p.6 | Define aggregation over sorted utilities |
| Goal weights | $w_1, \ldots, w_n$ | - | - | $w_i > 0$ | p.30 | Weights for goals in Shafer's constructive approach |
| Mass function | $m$ | - | - | $m: 2^\Omega \to [0,1]$, sums to 1 | p.11 | Core uncertainty representation |

## Implementation Details

- **Pignistic probability computation**: For each state $\omega$, sum $m(A)/|A|$ over all focal sets $A$ containing $\omega$. Complexity is $O(|focal sets| \times |\Omega|)$. *(p.17)*
- **Lower/upper expected utility computation**: For each focal set, find min/max utility within the set, weight by mass. Complexity is $O(\sum |A_i|)$ over focal sets. *(p.15)*
- **E-admissibility via LP**: For each candidate act $X_i$, solve a linear program: find $P$ in the credal set (constraints: $\sum_{\omega \in A} p(\omega) \geq Bel(A)$ for all $A$, $\sum p(\omega) = 1$, $p(\omega) \geq 0$) such that $E_P(X_i) \geq E_P(X_j)$ for all $j$. If feasible, $X_i$ is E-admissible. *(p.27-28)*
- **Allocation function for E-admissibility**: Variables $a_{jk}$ represent how mass $m(F_j)$ of focal set $F_j$ is allocated to element $\omega_k \in F_j$. Constraints: $a_{jk} \geq 0$, $\sum_k a_{jk} = m(F_j)$, resulting probability $p_k = \sum_j a_{jk}$. *(p.28)*
- **Generalized OWA**: For degree of optimism $\beta$, use max-entropy OWA operator $F_\beta$. At $\beta = 0.5$ recovers pignistic. The weights can be computed from the entropy-maximization problem. *(p.19)*
- **Shafer's constructive approach**: Define goals $A_1, \ldots, A_n$ as subsets of $\Omega$. For each act $f$, compute its induced mass function $m_f$ on $\Omega$. Score = $\sum w_i (Bel_f(A_i) + Pl_f(A_i))$. Reduces to expected utility when $m_f$ is Bayesian. *(p.30-31)*
- **Classification application of Shafer**: Goals = correct classification of each class. Mass function from classifier. Score for selecting class $C$: $U(f_C) = Bel(C) + Pl(C)$. *(p.32)*

## Figures of Interest
- **Fig 1a (p.8):** Aggregated utilities vs. pessimism index $\alpha$ for generalized Hurwicz criterion — shows how preference orderings between acts change as DM attitude varies
- **Fig 1b (p.8):** Aggregated utilities vs. $1-\beta$ for OWA criterion — similar crossover behavior
- **Fig 2a (p.20):** Generalized Hurwicz utilities vs. $\alpha$ under belief functions — shows distinct crossover points from the classical case
- **Fig 2b (p.20):** Generalized OWA utilities vs. $1-\beta$ under belief functions

## Results Summary
All decision criteria reviewed reduce to MEU when the mass function is Bayesian. The most important distinction among criteria is whether they produce a complete preference relation (total ordering of all acts) or a partial one. Complete-preference criteria: generalized Hurwicz, pignistic, generalized OWA, generalized minimax regret. Partial-preference criteria: strong dominance, interval bound dominance, maximality, E-admissibility. *(p.33)*

## Limitations
- The paper does not propose new criteria; it is a review and organization of existing work *(p.1)*
- Extensions to the continuous/real-line DS setting remain largely unexplored *(p.34)*
- The relationship between imprecise probability criteria (maximality, E-admissibility) and the DS-specific criteria (pignistic, Hurwicz) in the continuous setting is an open question *(p.34)*
- Shafer's constructive approach, while novel, needs deeper investigation of its theoretical and practical implications *(p.34)*

## Arguments Against Prior Work
- Against bare probability (Bayesian) approach: belief functions allow representing ignorance and partial information that probability cannot — a uniform probability and total ignorance are different epistemic states but look identical as probability distributions *(p.1, 13)*
- Against the pignistic transformation specifically: the minimax regret criterion violates Axiom $A_1$ (independence of irrelevant alternatives) of Arrow-Hurwicz, making it the "only notable counterexample" to pignistic *(p.5, 33)*
- Against complete preference relations: when information is genuinely imprecise, forcing a total order via pignistic/Hurwicz discards information about the DM's actual ignorance; partial preferences (maximality, E-admissibility) are more honest *(p.23, 33-34)*
- Against plausibility transformation for decision-making: no axiomatic argument has been put forward for using it; its advantage (preserving Dempster's rule) is about inference, not decision *(p.18)*

## Design Rationale
- **Pignistic is dominant in practice** because: (a) avoidance of Dutch books (Smets' argument), (b) linearity property (unique transformation satisfying MEU + linearity), (c) extends Laplace principle of indifference, (d) identical to Shapley value *(p.17-18, 33)*
- **Hurwicz/OWA preferred when**: the DM has a definite attitude toward ambiguity (risk-averse vs risk-seeking) that should be parameterized rather than fixed *(p.17, 19)*
- **Partial preferences preferred when**: one wants to avoid making unjustified commitments — acts that no compatible probability supports should not be chosen, but one need not totally order the remaining acts *(p.23-24)*
- **E-admissibility vs maximality**: E-admissibility is weaker (larger choice set) but computable via LP; maximality is stronger (smaller choice set) but harder to implement *(p.26-27)*
- **Shafer's constructive approach**: rejects the assumption that probabilities and utilities pre-exist — they must be constructed from concrete goals. Appropriate when the decision problem does not come with a natural utility function *(p.29-30)*

## Testable Properties
- For any mass function $m$: $Bel(A) \leq P(A) \leq Pl(A)$ for all $P \in \mathcal{P}(m)$ and all $A$ *(p.12)*
- $\underline{E}_\mu(u) \leq E_{BetP}(u) \leq \overline{E}_\mu(u)$ — pignistic expected utility always falls within the lower/upper bounds *(p.15, 18)*
- When $m$ is Bayesian (all focal sets are singletons): all criteria must reduce to MEU *(p.33)*
- Generalized Hurwicz at $\alpha = 0$: must equal upper expected utility. At $\alpha = 1$: must equal lower expected utility *(p.17)*
- Generalized OWA at $\beta = 0.5$: must equal pignistic expected utility *(p.19)*
- E-admissibility choice set $\supseteq$ maximality choice set $\supseteq$ strong dominance choice set *(p.23, 26-27)*
- Strong dominance: if $f_i \succ_{SD} f_k$ then $f_i \succ_\alpha f_k$ for ALL $\alpha \in [0,1]$ (Hurwicz for any pessimism) *(p.23)*
- Minimax regret criterion violates Axiom $A_1$ (independence of irrelevant alternatives): adding a dominated act can change the preference ordering among remaining acts *(p.5)*
- BetP must sum to 1 over all $\omega \in \Omega$ *(p.17)*

## Relevance to Project
Directly applicable to propstore's render-time decision problem. When the render layer must select among competing claims with uncertain evidence:

1. **Mass functions as claim uncertainty**: Each claim's evidence can be represented as a mass function on a frame of possible values, with focal sets representing imprecise evidence from different sources.

2. **Pignistic for default rendering**: When a single "best estimate" is needed, the pignistic transformation provides a principled default that avoids Dutch books and extends the principle of indifference.

3. **Lower/upper bounds for uncertainty display**: The $[Bel, Pl]$ interval provides natural uncertainty bounds that can be displayed alongside point estimates.

4. **E-admissibility for choice sets**: When multiple claims compete, E-admissibility (computable via LP) gives the set of claims that could reasonably be "the answer" under some compatible probability — directly implementing the non-commitment discipline.

5. **Pessimism parameter for render policies**: Different render policies can use different $\alpha$ values — a conservative policy uses $\alpha = 1$ (lower expected utility), an optimistic policy uses $\alpha = 0$.

6. **Shafer's constructive approach for goal-directed queries**: When the user specifies goals (e.g., "I need the claim most likely to be safe"), the constructive score $Bel(A) + Pl(A)$ provides a principled ranking.

## Open Questions
- [ ] How to construct mass functions from propstore's existing claim/stance/evidence structure [Partially addressed by Josang_2001_LogicUncertainProbabilities — Def 12 provides bijective mapping between opinions (b,d,u,a) and evidence counts (r,s), and the focused BMA (Sec 2.2) shows how to construct mass functions from binary frames; propstore claims could start as vacuous opinions and accumulate evidence via the consensus operator]
- [ ] Whether the LP for E-admissibility is practical at the scale of propstore's claim sets
- [ ] How to handle the continuous case (claim values on the real line, not discrete)
- [ ] Connection to the existing ATMS architecture — can ATMS labels be interpreted as mass functions?
- [ ] Relationship between Shafer's constructive goals and propstore's render-time query context

## Related Work Worth Reading
- Smets, P. "Decision making in the TBM: the necessity of the pignistic transformation." IJAR 38(2-3):133-147, 2005. — Full axiomatic treatment of pignistic transformation *(p.17)*
- Jaffray, J.-Y. "Linear utility theory for belief functions." Operations Research Letters, 8(2):107-112, 1989. — Axiomatic foundation for Hurwicz-style criteria under DS theory *(p.21)*
- Shafer, G. "Constructive decision theory." IJAR 79:45-62, 2016. — Full treatment of the constructive approach *(p.29)*
- Walley, P. "Towards a unified theory of imprecise probability." IJAR 24(2-3):1-18, 2000. — Foundation for maximality and E-admissibility *(p.25)*
- Gilboa, I. and Schmeidler, D. "Maximin expected utility with non-unique prior." J. Mathematical Economics, 18:141-153, 1989. — Axiomatic foundation for lower expected utility (maximin EU) *(p.10)*
- Denoeux, T. and Shenoy, P. "An axiomatic utility theory for DS theory." In Proc. BELIEF 2018, IJCAI-18, pp. 5135-5141, 2018. — Extension of Savage-style utility theory to belief functions *(p.38)*

## Collection Cross-References

### Conceptual Links (not citation-based)
- [[Josang_2001_LogicUncertainProbabilities]] — **Strong.** Josang defines the opinion algebra (b, d, u, a) for representing uncertain probabilities via Dempster-Shafer belief functions, while Denoeux reviews how to make decisions given such representations. Josang's probability expectation E(x) = b + a*u is equivalent to the pignistic transformation that Denoeux treats as one of many decision criteria. Together they form a pipeline: Josang provides the representation and combination algebra, Denoeux provides the decision-theoretic rendering. Denoeux's taxonomy of decision criteria (Hurwicz, E-admissibility, Shafer constructive) maps to propstore render-time policies applied to Josang's opinions.
- [Belief Functions: The Disjunctive Rule of Combination and the Generalized Bayesian Theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) — **Strong.** Smets's GBT is the canonical evidential-classification primitive surveyed here: the four-step ballooning extension + conjunctive combination + Dempster conditioning + marginalization construction (this paper's section on GBT-based classifiers, Vannoorenberghe-Smets credal EM, and Fiche et al.'s alpha-stable BF classifier) is the operational realization of Smets 1993's DRC/GBT pair. The decision-criteria taxonomy in this review applies on top of conditional belief functions produced by GBT.
- [Decision-Making with Belief Functions and Pignistic Probabilities](../Wilson_1993_Decision-MakingBeliefFunctionsPignistic/notes.md) — **Strong.** Wilson (Theorem 5.7) proves that lower/upper expected utility over the set of pignistic transforms induced by *all refinements* of the frame equals lower/upper expected utility over the standard `[Bel, Pl]` envelope. This is precisely the bound `\underline{E}_\mu(u) ≤ E_{BetP}(u) ≤ \overline{E}_\mu(u)` that Denoeux states (p.15, 18) as a property of the pignistic. Wilson's frame-arbitrariness argument also undercuts one of the four reasons Denoeux cites for pignistic dominance: Smets' "linearity" justification holds only after a frame is fixed; refining the frame moves the pignistic but leaves the envelope invariant. Different formalisms (Wilson: theorem-and-proof; Denoeux: criteria review), same empirical convergence on the envelope decision.

---

**See also (conceptual link):** [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — Source of the Dutch-book argument and Theorem 3.1 (axiomatic uniqueness of the pignistic transformation under A1–A4) cited in this review as one of the four reasons the pignistic transformation is dominant in practice. The 1994 paper presents the operational formulation that this review surveys.
