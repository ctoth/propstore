---
title: "A distance measure for bounding probabilistic belief change"
authors: "Hei Chan, Adnan Darwiche"
year: 2005
venue: "International Journal of Approximate Reasoning"
doi_url: "https://doi.org/10.1016/j.ijar.2004.07.001"
pages: "149-174"
---

# A distance measure for bounding probabilistic belief change

## One-Sentence Summary

Proposes the CD-distance (Chan-Darwiche distance) between two probability distributions, which provides tight worst-case bounds on how much any belief (odds ratio) can change when one distribution is replaced by another — with applications to sensitivity analysis in belief networks and probabilistic belief revision.

## Problem Addressed

When a probability distribution is perturbed (e.g., a local conditional probability in a Bayesian network changes, or soft evidence is incorporated), how much can any downstream query belief change? Existing measures (KL-divergence, Euclidean distance) cannot provide tight worst-case bounds on individual belief changes — KL-divergence is asymmetric, incomparable with the CD-distance, and only provides average-case guarantees; Euclidean distance cannot bound belief changes at all without supplementary information. *(p.1-2)*

## Key Contributions

- Definition of the CD-distance D(Pr, Pr') = ln max_w Pr'(w)/Pr(w) - ln min_w Pr'(w)/Pr(w), a true metric (positive, symmetric, triangle inequality) over distributions with the same support *(p.2-3)*
- Theorem 2.2: tight bounds on odds change — for any events alpha, beta: e^{-D} <= O'(alpha|beta)/O(alpha|beta) <= e^D *(p.2-3)*
- Demonstrated that KL-divergence and Euclidean distance cannot bound belief changes in the same way *(p.4-6)*
- Relationship between CD-distance and KL-divergence via Bayes factor (CD-distance = ln of max Bayes factor), with upper bound on KL given CD-distance (Thm 3.4) *(p.7-9)*
- Application to sensitivity analysis in belief networks: CD-distance from local CPT perturbation equals the local parameter log-odds change, computable in constant time *(p.9-11)*
- Application to belief revision: Jeffrey's rule and Pearl's virtual evidence method both minimize CD-distance (Thms 5.2, 5.3), making them optimal from the CD-distance viewpoint *(p.12-15)*
- Proportional covariation scheme for multi-valued variables minimizes CD-distance (Thm 4.2) *(p.11-12)*

## Study Design

*Non-empirical: pure theory with worked examples.*

## Methodology

The paper defines a distance measure on probability distributions based on the log of the ratio of probability ratios (max and min over all worlds). It proves metric properties, derives tight bounds on odds/probability changes, then applies the measure to two domains: (1) sensitivity analysis in Bayesian networks, where local parameter perturbation induces a known CD-distance, and (2) probabilistic belief revision, where Jeffrey's rule and Pearl's virtual evidence are shown to minimize the CD-distance subject to constraints.

## Key Equations / Statistical Models

### Definition 2.1: CD-Distance

$$
D(Pr, Pr') \stackrel{\text{def}}{=} \ln \max_w \frac{Pr'(w)}{Pr(w)} - \ln \min_w \frac{Pr'(w)}{Pr(w)}
$$

Where: Pr, Pr' are two probability distributions over the same set of worlds w. Convention: 0/0 = 1 and infinity/infinity = 1. If Pr and Pr' do not have the same support, D(Pr, Pr') = infinity.
*(p.2)*

### Theorem 2.2: Odds Bounding (main result)

$$
e^{-D(Pr,Pr')} \leq \frac{O'(\alpha|\beta)}{O(\alpha|\beta)} \leq e^{D(Pr,Pr')}
$$

Where: O(alpha|beta) = Pr(alpha|beta)/Pr(not-alpha|beta) is the odds of event alpha given beta w.r.t. Pr, and O'(alpha|beta) is the same w.r.t. Pr'. The bound is tight — for every pair of distributions, there exist events alpha, beta that achieve equality.
*(p.2-3)*

### Corollary: Log-odds form (Inequality 1)

$$
|\ln O'(\alpha|\beta) - \ln O(\alpha|\beta)| \leq D(Pr, Pr')
$$

*(p.3)*

### Inequality 2: Probability bounding form

$$
\frac{p \cdot e^{-d}}{p(e^{-d} - 1) + 1} \leq Pr'(\alpha|\beta) \leq \frac{p \cdot e^{d}}{p(e^{d} - 1) + 1}
$$

Where: p = Pr(alpha|beta) is the initial belief, d = D(Pr, Pr') is the distance.
*(p.3-4)*

### Definition 3.1: KL-Divergence

$$
KL(Pr, Pr') \stackrel{\text{def}}{=} -\sum_w Pr(w) \ln \frac{Pr'(w)}{Pr(w)}
$$

*(p.4)*

### Definition 3.3: Bayes Factor

$$
F_{Pr',Pr}(\alpha : \beta) \stackrel{\text{def}}{=} \frac{Pr'(\alpha)/Pr'(\beta)}{Pr(\alpha)/Pr(\beta)}
$$

The CD-distance equals the log of the maximum Bayes factor over all pairs of worlds:
$$
D(Pr, Pr') = \ln \max_{w_i, w_j} F_{Pr',Pr}(w_i : w_j)
$$

*(p.7-8)*

### Theorem 3.1: KL-divergence average-case bound

$$
KL(Pr, Pr') \geq -Pr(\beta) \left( Pr(\alpha|\beta) \ln \frac{Pr'(\alpha|\beta)}{Pr(\alpha|\beta)} + (1 - Pr(\alpha|\beta)) \ln \frac{1 - Pr'(\alpha|\beta)}{1 - Pr(\alpha|\beta)} \right)
$$

Or equivalently in odds:
$$
KL(Pr, Pr') \geq Pr(\beta) \left( \ln \frac{O'(\alpha|\beta) + 1}{O(\alpha|\beta) + 1} - \frac{O(\alpha|\beta)}{O(\alpha|\beta) + 1} \ln \frac{O'(\alpha|\beta)}{O(\alpha|\beta)} \right)
$$

*(p.6)*

### Theorem 3.3: KL-divergence decomposition via Bayes factors

$$
0 \leq \sum_i Pr(\gamma_i) \ln F_{Pr',Pr}(\alpha : \gamma_i) - \ln \frac{Pr'(\alpha)}{Pr(\alpha)} \leq KL(Pr, Pr')
$$

And as equality when gamma_1, ..., gamma_n partition the set of worlds:
$$
KL(Pr, Pr') = \sum_w Pr(w) \ln F_{Pr',Pr}(\alpha : w) - \ln \frac{Pr'(\alpha)}{Pr(\alpha)}
$$

*(p.8-9)*

### Theorem 3.4: Upper bound on KL given CD-distance

$$
KL(Pr, Pr') \leq -1 - \ln \frac{d}{e^d - 1} + \frac{d}{e^d - 1}
$$

Where: d = D(Pr, Pr') > 0.
*(p.8-9)*

### Theorem 4.1: CD-distance for belief network sensitivity

$$
D(Pr, Pr') = D(\Theta_{X|\mathbf{u}}, \Theta'_{X|\mathbf{u}})
$$

Where: Pr is the global distribution induced by belief network N, Pr' is the global distribution induced by N' (which differs from N only in the conditional probability table for variable X given parents u). The global distance equals the local CPT distance.
*(p.10)*

### Definition 5.1: Jeffrey's Rule

$$
Pr'(w) \stackrel{\text{def}}{=} Pr(w) \frac{q_i}{p_i}, \quad \text{if } w \models \gamma_i
$$

Where: gamma_1, ..., gamma_n are mutually exclusive and exhaustive events with original probabilities p_1, ..., p_n changed to q_1, ..., q_n.
*(p.12)*

### Theorem 5.1: CD-distance under Jeffrey's rule

$$
D(Pr, Pr') = \ln \max_i \frac{q_i}{p_i} - \ln \min_i \frac{q_i}{p_i}
$$

*(p.12)*

### Definition 5.2: Pearl's Method of Virtual Evidence

$$
Pr'(w) \stackrel{\text{def}}{=} Pr(w) \frac{\lambda_i}{\sum_j p_j \lambda_j}, \quad \text{if } w \models \gamma_i
$$

Where: lambda_i = Pr(eta|gamma_i)/Pr(eta|gamma_1) are likelihood ratios, with lambda_1 = 1.
*(p.14)*

### Theorem 5.3: CD-distance under Pearl's method

$$
D(Pr, Pr') = \ln \max_i \lambda_i - \ln \min_i \lambda_i
$$

*(p.14)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| CD-distance | D(Pr,Pr') | nats (log-odds) | — | [0, infinity) | 2 | 0 iff Pr = Pr'; infinity if different support |
| KL-divergence | KL(Pr,Pr') | nats | — | [0, infinity) | 4 | Asymmetric, not a true distance |
| Bayes factor | F_{Pr',Pr}(alpha:beta) | dimensionless | — | (0, infinity) | 7 | Ratio of new-to-old likelihood ratios |
| Odds | O(alpha\|beta) | dimensionless | — | [0, infinity) | 2 | Pr(alpha\|beta)/Pr(not-alpha\|beta) |

## Methods & Implementation Details

- CD-distance computable as max minus min of log probability ratios over all worlds *(p.2)*
- For belief network sensitivity: distance between global distributions equals distance between local CPT distributions — computable in constant time without global inference *(p.10)*
- For multi-valued variables with n values: when changing one parameter theta_{x|u} from its original value, the proportional covariation scheme (adjusting other parameters proportionally) minimizes CD-distance among all valid re-parameterizations *(p.11-12)*
- Proportional scheme: theta'_{x_i|u} = theta_{x_i|u} * (1 - theta'_{x|u})/(1 - theta_{x|u}) for x_i != x. This produces CD-distance = |ln(theta'_{x|u}/theta_{x|u}) - ln((1-theta'_{x|u})/(1-theta_{x|u}))| *(p.12, 23)*
- Jeffrey's rule minimizes CD-distance among all distributions satisfying the new probability constraints (Thm 5.2) *(p.13-14)*
- Pearl's virtual evidence method also minimizes CD-distance subject to likelihood ratio constraints (Thm 5.3) *(p.14-15)*
- Example 5.1: Holmes/burglary scenario demonstrates practical use — given initial probability Pr(burglary) = 0.214 and evidence with CD-distance d, use Inequality 2 to bound the posterior *(p.13-14)*
- Example 5.3: Constraining evidence strength to keep posterior within bounds — find maximum d such that Pr'(c_g|s) <= 0.3 *(p.15-16)*

## Figures of Interest

- **Fig 1 (p.3):** Bounds of Pr'(alpha|beta) from Inequality 2 plotted against initial belief p = Pr(alpha|beta) for distance values d = 0.1, 1, 2, 3. Shows tighter bounds for extreme initial beliefs.
- **Fig 2 (p.7):** Bounds from KL-divergence (Theorem 3.1) plotted against initial belief for different KL and Pr(beta) values. Shows how KL bounds degrade as Pr(beta) decreases.
- **Fig 3 (p.8):** Upper bound on KL-divergence as a function of CD-distance d (Theorem 3.4). Shows KL bounded by a function that grows roughly linearly for small d.

## Results Summary

The CD-distance provides tight worst-case bounds on belief change (odds ratios), unlike KL-divergence (average-case only, incomparable ordering) and Euclidean distance (no belief bounds without additional information). The distance is a true metric. For Bayesian networks, the global CD-distance from a single CPT change equals the local CPT distance. Jeffrey's rule and Pearl's virtual evidence method are optimal in the sense of minimizing CD-distance. *(p.1-16)*

## Limitations

- The distance requires same support (becomes infinity otherwise) *(p.2)*
- Bounds are in terms of odds ratios, which become less informative when initial belief is near 0 or 1 (though tighter in probability terms) *(p.3-4)*
- The sensitivity analysis result (Thm 4.1) applies to single-parameter perturbation; multi-parameter changes require bounding via triangle inequality *(p.10)*
- KL-divergence provides better average-case bounds; CD-distance is worst-case *(p.8-9)*

## Arguments Against Prior Work

- KL-divergence is incomparable with CD-distance for bounding belief changes: Example 3.1 shows distributions where KL and CD-distance rank differently *(p.4-5)*
- KL-divergence can be made arbitrarily close to 0 while keeping odds ratios arbitrarily far from 1 (Example 3.2), so KL cannot bound worst-case belief change *(p.4-5)*
- Euclidean distance has the same problem: large Euclidean difference between pairs of probability values may not translate to large belief changes, because it doesn't account for the base probability *(p.5-6)*
- Both KL-divergence and Euclidean distance cannot provide exact bounds on individual query beliefs without additional global computation *(p.5-6)*

## Design Rationale

- Distance defined on log-odds scale rather than probability scale because odds ratios capture the multiplicative nature of belief change *(p.2-3)*
- Using max/min of log probability ratios gives a symmetric measure (unlike KL) that is a true metric *(p.2-3)*
- The measure is designed specifically for the purpose of bounding, hence the focus on worst-case (max Bayes factor) rather than average-case (KL) *(p.7-8)*
- The connection to Bayes factors provides interpretive clarity: CD-distance is the log of the most extreme evidence ratio possible between any two worlds *(p.7-8)*

## Testable Properties

- D(Pr, Pr') >= 0, with equality iff Pr = Pr' (positiveness) *(p.2)*
- D(Pr, Pr') = D(Pr', Pr) (symmetry) *(p.2)*
- D(Pr, Pr') + D(Pr', Pr'') >= D(Pr, Pr'') (triangle inequality) *(p.2)*
- For any alpha, beta: e^{-D} <= O'(alpha|beta)/O(alpha|beta) <= e^D (Theorem 2.2, tight) *(p.2-3)*
- For any alpha, beta: |ln O'(alpha|beta) - ln O(alpha|beta)| <= D(Pr, Pr') *(p.3)*
- Under Jeffrey's rule: D(Pr, Pr') = ln max_i(q_i/p_i) - ln min_i(q_i/p_i) *(p.12)*
- Under Pearl's virtual evidence: D(Pr, Pr') = ln max_i(lambda_i) - ln min_i(lambda_i) *(p.14)*
- Jeffrey's rule produces the distribution Pr' minimizing D(Pr, Pr') subject to Pr'(gamma_i) = q_i *(p.13-14)*
- For belief networks: D(Pr_N, Pr_{N'}) = D(Theta_{X|u}, Theta'_{X|u}) when only one CPT changes *(p.10)*
- KL(Pr, Pr') <= -1 - ln(d/(e^d - 1)) + d/(e^d - 1) for d = D(Pr, Pr') > 0 *(p.8)*

## Relevance to Project

The CD-distance is directly relevant to propstore's probabilistic argumentation layer. When opinions (Subjective Logic) or probabilistic AFs undergo parameter perturbation — e.g., updating a single argument's base score or strength — the CD-distance provides tight bounds on how much any downstream belief can change. This enables:
1. **Sensitivity analysis for argumentation:** bound the impact of changing a single argument's probability on extension membership
2. **Belief revision bounds:** when incorporating new evidence via Jeffrey's rule (which is connected to SL's belief update), know the maximum belief distortion
3. **Stability guarantees:** verify that small parameter changes produce small output changes, relevant to Odekerken 2023's stability concept

## Open Questions

- [ ] How does CD-distance compose under multiple simultaneous CPT changes? (triangle inequality gives an upper bound, but is it tight?)
- [ ] Can CD-distance be adapted to bound changes in Dung AF extensions when argument probabilities change?
- [ ] Relationship to Jøsang's Subjective Logic uncertainty: can CD-distance bound opinion change under fusion operators?

## Related Work Worth Reading

- Chan & Darwiche, "When do numbers really matter?" UAI 2001 [2] — earlier version of the distance measure concept
- Darwiche, "A differential approach to inference in Bayesian networks" UAI 2000 [4] — differential sensitivity analysis framework
- Castillo et al., "Sensitivity analysis in discrete Bayesian networks" IEEE Trans SMC 1997 [1] — prior sensitivity analysis approach
- Kjærulff & van der Gaag, "Making sensitivity analysis computationally efficient" UAI 2000 [12] — computational aspects of sensitivity
- Pearl, "Probabilistic Reasoning in Intelligent Systems" 1988 [15] — virtual evidence method
- Jeffrey, "The Logic of Decision" 1965 [9] — Jeffrey's rule for belief revision
