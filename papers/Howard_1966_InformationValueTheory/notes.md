---
title: "Information Value Theory"
authors: "Ronald A. Howard"
year: 1966
venue: "IEEE Transactions on Systems Science and Cybernetics"
doi_url: "https://doi.org/10.1109/TSSC.1966.300074"
pages: "22-26"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-29T00:03:41Z"
---
# Information Value Theory

## One-Sentence Summary

Develops a formal theory for assigning monetary value to the elimination or reduction of uncertainty in decision problems, showing that the value of perfect information (clairvoyance) about a variable serves as an upper bound analogous to the Carnot cycle in thermodynamics. *(p.22)*

## Problem Addressed

Shannon's information theory measures information quantity based solely on probabilistic structure of communication, without considering economic consequences. Attempts to apply Shannon's theory to decision problems failed because the theory does not account for the economic impact of uncertainty on a decision maker. Howard develops a theory that jointly considers probabilistic and economic factors to assign numerical values to information. *(p.22)*

## Key Contributions

- Formal framework for computing the value of eliminating uncertainty about any random variable in a decision problem *(p.22)*
- Concept of "clairvoyance" as perfect information about a variable, with its value serving as an upper bound on the worth of any real information source *(p.24)*
- Demonstration that the joint value of eliminating multiple independent uncertainties can differ from the sum of their individual values — information interactions exist *(p.26)*
- Analogy between clairvoyance as theoretical upper bound and the Carnot engine as thermodynamic upper bound *(p.25)*

## Methodology

Howard develops the theory through a concrete bidding problem. A company bids on a contract with uncertain cost p and uncertain lowest competitor bid l. The framework uses probability distributions conditioned on different states of information (denoted by the "state of information" variable S) to compute expected profits under different information scenarios. The value of information is defined as the difference in expected profit between having and not having that information. *(pp.22-26)*

## Key Equations / Statistical Models

### Notation

$$
x = \text{a random variable}
$$
$$
A = \text{an event}
$$
$$
S = \text{state of information on which probability assignments are made}
$$
$$
\{x|S\} = \text{density function of } x \text{ given state } S
$$
$$
\{A|S\} = \text{probability of event } A \text{ given state } S
$$
$$
\langle x|S \rangle = \text{expectation of } x = \int_x x \{x|S\}
$$
$$
\mathcal{E} = \text{experience (total a priori knowledge)}
$$
$$
\{x|\mathcal{E}\} = \text{prior density of } x
$$
Where: x is a random variable, S is the state of information, E (script E) is total a priori knowledge. The generalized summation symbol (integral/sum) is used for both continuous and discrete cases. *(p.22)*

### Expansion equation (fundamental inferential tool)

$$
\{u|S\} = \int_v \{u|vS\} \{v|S\}
$$
Where: u, v are random variables. This encodes the law of total probability as the key inferential concept for introducing new variables into a problem. *(p.23)*

### Expectation expansion

$$
\langle u|S \rangle = \int_v \langle u|vS \rangle \{v|S\}
$$
Where: this shows that to find the expectation of u, we need only the conditional expectation of u given v, averaged over v. *(p.23, eq.2)*

### Profit definition (bidding problem)

$$
v = \begin{cases} b - p & \text{if } b < \ell \\ 0 & \text{if } b > \ell \end{cases}
$$
Where: v is profit, b is our bid, p is our cost, l is lowest competitor bid. *(p.23, eq.3)*

### Profit distribution given bid and state of knowledge

$$
\{v|b\mathcal{E}\} = \int_{p,\ell} \{v|bp\ell\mathcal{E}\} \{p,\ell|b\mathcal{E}\}
$$
*(p.23, eq.4)*

### Expected profit (conditional on bid)

$$
\langle v|b\mathcal{E} \rangle = \int_{p,\ell} \langle v|bp\ell\mathcal{E} \rangle \{p,\ell|b\mathcal{E}\}
$$
*(p.23, eq.5)*

### Assumptions: cost-bid independence

$$
\{p,\ell|b\mathcal{E}\} = \{p,\ell|\mathcal{E}\}
$$
*(p.23, eq.6)*

$$
\{p,\ell|\mathcal{E}\} = \{p|\mathcal{E}\} \{\ell|\mathcal{E}\}
$$
*(p.23, eq.7)*

### Expected profit given bid (after substitution)

$$
\langle v|b\mathcal{E} \rangle = \int_{p,\ell} \langle v|bp\ell\mathcal{E} \rangle \{p|\mathcal{E}\} \{\ell|\mathcal{E}\}
$$
*(p.23, eq.8)*

### Conditional profit on bid, cost, and lowest competitor bid

$$
\langle v|bp\ell\mathcal{E} \rangle = \begin{cases} b - p & \text{if } b < \ell \\ 0 & \text{if } b > \ell \end{cases}
$$
*(p.23, eq.9)*

### Expected profit under specific priors (uniform p on [0,1], uniform l on [0,2])

$$
\langle v|b\mathcal{E} \rangle = \frac{1}{2}(2-b)(b - \frac{1}{2}) = -\frac{1}{2} + \frac{5}{4}b - \frac{1}{2}b^2 \quad (b \leq 2)
$$
*(p.24, eq. shown in Fig.2)*

### Optimal expected profit (no clairvoyance)

$$
\langle v|\mathcal{E} \rangle = \max_b \langle v|b\mathcal{E} \rangle = \langle v|b=\frac{5}{4}, \mathcal{E} \rangle = \frac{9}{32} = \frac{27}{96}
$$
Where: optimal bid is b* = 5/4. *(p.24, eq.12)*

### Value of clairvoyance about variable x

$$
\langle v_{c_x}|\mathcal{E} \rangle = \langle v|C_x\mathcal{E} \rangle - \langle v|\mathcal{E} \rangle
$$
Where: v_cx is the increase in expected profit from obtaining perfect information (clairvoyance) about x. C_x denotes the clairvoyance state. *(p.24, eq.13)*

### Expected profit given clairvoyance about x

$$
\langle v|C_x\mathcal{E} \rangle = \int_x \langle v|x\mathcal{E} \rangle \{x|\mathcal{E}\}
$$
Where: we evaluate the expected profit for each possible value of x, then average over the prior on x. *(p.24, eq.14)*

### Value of clairvoyance about cost p

$$
\langle v_{c_p}|\mathcal{E} \rangle = \langle v|C_p\mathcal{E} \rangle - \langle v|\mathcal{E} \rangle = \frac{28}{96} - \frac{27}{96} = \frac{1}{96}
$$
*(p.25, eq.22)*

### Expected profit with clairvoyance about l

$$
\langle v|C_\ell\mathcal{E} \rangle = \int_\ell \langle v|\ell\mathcal{E} \rangle \{\ell|\mathcal{E}\} = \frac{54}{96}
$$
*(p.25, eq.29)*

### Value of clairvoyance about lowest competitor bid l

$$
\langle v_{c_\ell}|\mathcal{E} \rangle = \frac{54}{96} - \frac{27}{96} = \frac{27}{96}
$$
*(p.26, eq.30)*

### Optimal bid given knowledge of p (clairvoyance about p)

$$
b = 1 + \frac{p}{2}
$$
*(p.25, eq.19)*

### Expected profit given clairvoyance about p

$$
\langle v|p\mathcal{E} \rangle = \frac{1}{2}\left(1 - \frac{p}{2}\right)^2
$$
*(p.25, eq.20)*

### Expected profit with clairvoyance about p (integrated over prior)

$$
\langle v|C_p\mathcal{E} \rangle = \int_0^1 dp \{p|\mathcal{E}\} \cdot \frac{1}{2}\left(1 - \frac{p}{2}\right)^2 = \frac{7}{24} = \frac{28}{96}
$$
*(p.25, eq.21)*

### Joint clairvoyance about both p and l

$$
\langle v_{c_{p\ell}}|\mathcal{E} \rangle = \langle v|C_{p\ell}\mathcal{E} \rangle - \langle v|\mathcal{E} \rangle = \frac{56}{96} - \frac{27}{96} = \frac{29}{96}
$$
*(p.26, eq.36)*

### Expected profit with joint clairvoyance

$$
\langle v|C_{p\ell}\mathcal{E} \rangle = \frac{1}{2}\int_0^1 dp \int_0^2 d\ell\, \ell(\ell - p) = \frac{7}{12} = \frac{56}{96}
$$
*(p.26, eq.35)*

### Strategy given both p and l known

$$
\langle v|p\ell\mathcal{E} \rangle = \begin{cases} \ell - p & \text{if } \ell > p \\ 0 & \text{if } \ell < p \end{cases}
$$
Where: if l > p, bid just below l and profit is l - p. If l < p, do not bid. *(p.26, eq.34)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Our cost | p | monetary | — | [0, 1] (uniform prior) | 23 | Company's cost of performing contract |
| Our bid | b | monetary | 5/4 (optimal) | [0, 2] | 23 | Decision variable |
| Lowest competitor bid | l (ell) | monetary | — | [0, 2] (uniform prior) | 23 | Uncertain; represents all competition |
| Profit | v | monetary | — | — | 23 | v = b-p if b<l, else 0 |
| Expected profit (no info) | <v\|E> | monetary | 9/32 = 27/96 | — | 24 | Under optimal bidding strategy |
| Value of knowing p | v_cp | monetary | 1/96 | — | 25 | Very small; knowing own cost adds little |
| Value of knowing l | v_cl | monetary | 27/96 | — | 26 | 27x more valuable than knowing p |
| Value of knowing both | v_cpl | monetary | 29/96 | — | 26 | != 1/96 + 27/96 = 28/96; interaction = 1/96 |
| Expected profit knowing p | <v\|C_p,E> | monetary | 28/96 | — | 25 | Optimal bid b = 1+p/2 |
| Expected profit knowing l | <v\|C_l,E> | monetary | 54/96 | — | 26 | Doubled from no-info case |
| Expected profit knowing both | <v\|C_pl,E> | monetary | 56/96 | — | 26 | Highest achievable |

## Methods & Implementation Details

- **Expansion concept (inferential tool):** The law of total probability is used as the core computational technique, treating each new random variable as expanding the information state. This allows sequential introduction of uncertain factors into expected-value calculations. *(p.23)*
- **Optimization:** Expected profit is maximized over the decision variable (bid b) by taking derivative and setting to zero. Optimal bid b* = 5/4 under uniform priors. *(p.24)*
- **Clairvoyance computation procedure:** (1) For each possible realization of the clairvoyant variable x, compute the optimal decision and resulting expected profit. (2) Average these optimal profits over the prior distribution of x. (3) Subtract the no-clairvoyance expected profit. The difference is the value of clairvoyance. *(p.24)*
- **Prior distributions used in example:** p ~ Uniform(0,1), l ~ Uniform(0,2), p and l independent. *(p.23-24)*
- **The prior on x used in the clairvoyance calculation is the prior from total a priori knowledge E, because up to the moment the clairvoyant reveals x, probability assignments are based only on E.** *(p.24)*

## Figures of Interest

- **Fig. 1 (p.24):** Prior density functions for cost p (uniform on [0,1]) and lowest competitor bid l (uniform on [0,2]), plus conditional distributions {p <= p_0 | E} and {l <= l_0 | E}.
- **Fig. 2 (p.24):** Expected profit as function of bid b — parabolic, maximum at b=5/4 yielding profit 9/32.
- **Fig. 3 (p.26):** Expected profit given lowest competitive bid l — linear (l - p-hat)/2 for l > p-hat, zero otherwise. Shows the value region for knowing l.

## Results Summary

The value of clairvoyance about the lowest competitor bid l (27/96) vastly exceeds the value of knowing own cost p (1/96) — by a factor of 27. This is because knowing l allows controlling profitability far more effectively than knowing p. With knowledge of l, the company can bid just under the competitor and never lose money; with knowledge of p alone, it still faces the large uncertainty about whether it will win. *(pp.25-26)*

The joint value of knowing both p and l (29/96) is greater than the sum of individual values (28/96), demonstrating a positive interaction effect of 1/96. This means the variables are not informationally separable — the whole exceeds the sum of parts. *(p.26)*

## Limitations

- The analysis uses "perfect clairvoyance" (complete elimination of uncertainty), which is a theoretical upper bound, not achievable in practice. Real information sources are imperfect. *(p.25)*
- The imperfection of real clairvoyance can arise from statistical effects, incompetence, or mendacity of the information source. *(p.26)*
- The example uses simple uniform priors; real problems would have more complex distributions. *(p.23-24)*

## Arguments Against Prior Work

- Shannon's information theory is criticized as inadequate for decision-making because it only measures probabilistic structure without considering economic consequences. *(p.22)*
- "Attempts to apply Shannon's information theory to problems beyond communications have, in the large, come to grief" because the theory does not consider outcomes or their values. *(p.22)*
- The failure is fundamental: just knowing probabilities of outcomes without considering their consequences cannot describe the importance of uncertainty to a decision maker. *(p.22)*

## Design Rationale

- **Clairvoyance as upper bound:** Chosen because it represents the maximum possible information about a variable, providing a computable ceiling on what any information program could be worth. Analogous to the Carnot cycle providing an upper bound on engine efficiency. *(p.25)*
- **Expansion as inferential tool:** The law of total probability is chosen as the core mechanism because it provides a direct bridge between probability theory and human reasoning about introducing new considerations. *(p.23)*
- **Separation of probabilistic and economic factors:** The framework keeps probability distributions (states of information) separate from value functions (profit), combining them only at the expectation step. This permits modular analysis. *(p.22-23)*

## Testable Properties

- Value of clairvoyance about any variable must be >= 0 (perfect information cannot make you worse off under optimal use). *(p.24)*
- Under the bidding example priors: optimal bid = 5/4, expected profit = 9/32. *(p.24)*
- Value of clairvoyance about independent variables need not be additive: v_c(x,y) != v_cx + v_cy in general. *(p.26)*
- The value of clairvoyance serves as an upper bound on the value of any real (imperfect) information source about the same variable. *(p.25)*
- If l < p (competitor bids less than our cost), optimal action is do not bid. If l > p, bid just below l. *(p.26)*

## Relevance to Project

This paper is foundational for the propstore project's decision-theoretic layer. The value of information framework directly applies to:
1. **Deciding which uncertainties to resolve first** — the clairvoyance value ranking tells us which uncertain parameters in an argumentation framework have the highest decision-theoretic impact.
2. **Bounding the value of experiments** — before running any analysis or gathering evidence, we can compute an upper bound on how much that evidence could improve decisions.
3. **Information interaction effects** — the non-additivity result (joint value != sum of individual values) is critical for understanding which combinations of evidence are worth gathering.
4. **Integration with subjective logic** — the uncertainty parameter u in Josang's opinion algebra maps naturally to the "state of information" concept; value of information tells us which opinions' uncertainty is most worth reducing.

## Open Questions

- [ ] How does value of information interact with ASPIC+ argumentation — can we compute the value of resolving a particular argument?
- [ ] Connection to Denoeux 2019 decision criteria — can clairvoyance values be computed under belief function representations?
- [ ] Extension to non-independent uncertain variables (Howard assumes independence in the bidding example)
- [ ] How to handle imperfect clairvoyance (partial information) — Howard mentions this but does not develop it

## Collection Cross-References

### Already in Collection
- (none — Howard's two references are not in the collection)

### New Leads (Not Yet in Collection)
- Howard (1965a) — "Bayesian decision models for system engineering," IEEE Trans. SSC — foundational decision-theoretic framework this paper builds on
- Howard (1965b) — "Dynamic inference," J. Operations Research — operational inference framework underlying the expansion concept

### Conceptual Links (not citation-based)
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] — Howard's value of clairvoyance framework provides the classical decision-theoretic foundation that Denoeux extends to belief functions. Howard's framework assumes precise probabilities; Denoeux's pignistic/Hurwicz criteria handle imprecise beliefs. The clairvoyance upper bound concept could be extended to belief function representations.
- [[Ballester-Ripoll_2024_GlobalSensitivityAnalysisBayesianNetworks]] — Global sensitivity analysis answers the same question as Howard's value of information: which uncertain parameters matter most? Ballester-Ripoll's Sobol indices over BN parameters are a modern computational approach to what Howard formulated analytically. Howard's non-additivity result (joint value != sum of individual) parallels interaction effects in Sobol decomposition.
- [[Josang_2001_LogicUncertainProbabilities]] — Howard's "state of information" S maps naturally to Josang's uncertainty parameter u in subjective opinions. The value of clairvoyance about a variable x is the expected gain from reducing u to zero for the opinion about x. Howard provides the decision-theoretic rationale for which opinions' uncertainty is most worth reducing.
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] — Sensoy's evidence-to-opinion mapping produces Dirichlet-based uncertainty estimates. Howard's framework provides the decision-theoretic evaluation of whether reducing that uncertainty is worth the computational cost.
- [[Coupé_2002_PropertiesSensitivityAnalysisBayesian]] — Coupe studies sensitivity of BN outputs to parameter variation, which is the computational analogue of Howard's question about which uncertainties have the highest decision-theoretic impact.

### Cited By (in Collection)
- (none found)

## Related Work Worth Reading

- R. A. Howard, "Bayesian decision models for system engineering," IEEE Trans. on Systems Science and Cybernetics, vol. SSC-1, pp. 36-40, November 1965. *(ref [1])*
- R. A. Howard, "Dynamic inference," J. Operations Research, vol. 13, pp. 712-733, September-October 1965. *(ref [2])*
