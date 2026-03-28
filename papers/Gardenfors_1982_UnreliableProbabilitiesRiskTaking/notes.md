---
title: "Unreliable probabilities, risk taking, and decision making"
authors: "Peter Gardenfors, Nils-Eric Sahlin"
year: 1982
venue: "Synthese"
doi_url: "https://doi.org/10.1007/BF00486156"
pages: "361-386"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:05:04Z"
---
# Unreliable probabilities, risk taking, and decision making

## One-Sentence Summary
Introduces epistemic reliability as a second-order measure over sets of probability distributions, yielding a decision theory (MMEU) that generalizes both strict Bayesianism and classical maximin by filtering distributions by reliability before maximizing minimal expected utility.

## Problem Addressed
Strict Bayesianism assumes a decision maker's beliefs can be represented by a *unique* subjective probability measure. This is unrealistic: in practice, the amount and quality of information backing different probability estimates varies enormously. The paper addresses how to incorporate the *reliability* of probability estimates into decision making. *(p.361)*

## Key Contributions
- Introduces the concept of **epistemic reliability** (rho) as a real-valued measure over a set of epistemically possible probability distributions P, capturing how well-backed each distribution is by available information *(p.366)*
- Proposes a two-step decision procedure: (1) select the subset P/rho_0 of distributions meeting a desired reliability threshold rho_0, then (2) choose the alternative with the largest **minimal expected utility** (MMEU) relative to P/rho_0 *(p.370-371)*
- Shows that the MMEU criterion generalizes both strict Bayesian expected utility maximization (when full information yields a single distribution) and classical maximin (when no information makes all distributions equally unreliable) *(p.373)*
- Applies the theory to resolve the Ellsberg paradox and Popper's paradox of ideal evidence *(p.367-368, 374-376)*
- Compares favorably against Levi's theory, showing MMEU satisfies independence of irrelevant alternatives while Levi's S-admissibility does not *(p.377-380)*
- Defines a formal measure of epistemic risk: R(P/rho_0) = 1 - rho(P/rho_0)/rho(P), connecting risk-taking to the selection of the reliability threshold *(p.383)*

## Methodology
Analytical/philosophical framework paper. The authors build a formal decision theory by:
1. Replacing the single probability measure of strict Bayesianism with a *set* P of epistemically possible probability distributions *(p.365)*
2. Adding a reliability measure rho that orders distributions in P *(p.366)*
3. Defining a two-step decision procedure using reliability thresholds and maximin over expected utilities *(p.370-371)*
4. Illustrating with examples (tennis matches, Ellsberg's urn, Popper's coin) and comparing with Wald, Hurwicz, Hodges-Lehmann, Ellsberg, and Levi *(p.373-380)*

## Key Equations / Statistical Models

### Decision situation components
A decision situation consists of:
- A finite set of alternatives A = {a_1, a_2, ..., a_n} *(p.364)*
- A finite set of states of nature {s_1, s_2, ..., s_m} *(p.364)*
- Outcomes o_ij (choosing a_i when state is s_j), with utilities u_ij *(p.364)*
- A set P of epistemically possible probability measures over states *(p.365)*
- A measure rho of epistemic reliability over P *(p.366)*

### Convexity condition for P
$$
\alpha \cdot P + (1 - \alpha) \cdot P' \in \mathscr{P}, \quad \text{for any } \alpha \in [0,1], \text{ if } P, P' \in \mathscr{P}
$$
Where: P, P' are probability measures in the epistemically possible set, alpha is a mixing weight.
*(p.365)*

### Expected utility for alternative a_i under distribution P
$$
e_{ik} = \sum_j P(s_j) \cdot u_{ij}
$$
Where: e_ik is the expected utility of alternative a_i under distribution P_k, P(s_j) is the probability of state s_j, u_ij is the utility of outcome o_ij.
*(p.371)*

### Minimal expected utility of alternative a_i relative to P/rho_0
$$
\min_{P \in \mathscr{P}/\rho_0} e_{ik}
$$
Where: the minimum is taken over all distributions P in the reliability-filtered set P/rho_0.
*(p.371)*

### MMEU decision criterion
$$
\text{Choose } a_i \text{ such that } \min_{P \in \mathscr{P}/\rho_0} e_{ik} \text{ is maximal}
$$
The alternative with the largest minimal expected utility ought to be chosen.
*(p.371)*

### Epistemic risk measure
$$
R(\mathscr{P}/\rho_0) = 1 - \frac{\rho(\mathscr{P}/\rho_0)}{\rho(\mathscr{P})}
$$
Where: rho(P/rho_0) is the sum of epistemic reliability over the restricted set, rho(P) is the sum over the full set, and R measures how much of the total epistemic mass is being ignored.
*(p.383)*

### Popper's ideal evidence equations
Before statistical evidence e:
$$
P(a) = 1/2
$$
After ideally favourable evidence e:
$$
P(a, e) = 1/2
$$
But the epistemic reliability of P(a,e) is much higher than that of P(a) alone.
*(p.367-368)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Desired reliability level | rho_0 | - | - | [0, max(rho)] | 370 | Agent-chosen threshold; higher = more risk averse |
| Epistemic reliability measure | rho | - | - | [lower bound, upper bound] | 366 | Orders distributions; bounded above (full info) and below (no info) |
| Epistemic risk | R | - | - | [0, 1] | 383 | 0 = no risk (all distributions considered), 1 = maximal risk |
| Number of alternatives | n | - | - | >= 2 | 364 | Finite set A |
| Number of states | m | - | - | >= 2 | 364 | Finite set of states of nature |

## Methods & Implementation Details
- The set P of epistemically possible probability measures replaces a single subjective probability. P is epistemically possible if it does not contradict the decision maker's knowledge. *(p.365)*
- If P is assumed convex (Levi's assumption), then probabilities per state form intervals, but convex sets of measures are more general than interval assignments. *(p.365-366)*
- The reliability measure rho need only provide an ordering over distributions in P (not necessarily a numerical value), though if rho is a second-order probability measure, this works. *(p.366-367, note 13 on p.382)*
- Less information about states implies lower epistemic reliability for all distributions; when well-informed, some distributions have much higher reliability than others. *(p.367)*
- The MMEU procedure: Step 1 - select P/rho_0 (distributions with reliability >= rho_0). Step 2 - for each alternative, compute expected utility under each P in P/rho_0, take the minimum. Step 3 - choose the alternative with the largest minimum. *(p.370-371)*
- After restricting P to P/rho_0, the remaining information about states is of the same type as for strict Bayesianism (a unique measure may emerge), but the situation arises for different reasons. *(p.371)*
- The P(o_ij) = P(s_j) simplification assumes outcome probabilities are independent of which alternative is chosen. *(p.365)*

## Figures of Interest
- **Fig 1 (p.367):** Three diagrams showing epistemic reliability rho as a function of P(s_1) for tennis matches A, B, C. Match A has a peaked distribution (high reliability at P=0.5), Match B has a flat/low distribution (low reliability everywhere), Match C has a bimodal distribution (high reliability at extremes).
- **Fig 2 (p.372):** Same three matches but with a dashed horizontal line showing the desired reliability level rho_0. Shows how filtering by rho_0 restricts the distributions differently in each case.

## Results Summary
- In the limiting case of no information, all distributions have equal epistemic reliability, and MMEU reduces to classical maximin (decision making under ignorance). *(p.373)*
- In the limiting case of full information, only one distribution is epistemically possible (or has maximal reliability), and MMEU reduces to strict Bayesian expected utility maximization (decision making under risk). *(p.373)*
- The Ellsberg paradox is resolved: the MMEU criterion recommends a_1 preferred to a_2 and a_4 preferred to a_3, matching empirical findings, because alternatives involving the ambiguous black/yellow distribution are epistemically riskier. *(p.375-376)*
- Popper's paradox of ideal evidence is resolved: before and after evidence e, P(a) = 1/2, but the reliability of the estimate is much higher after evidence, which the standard Bayesian framework cannot capture but the P + rho model can. *(p.367-368)*
- Levi's theory violates independence of irrelevant alternatives; the MMEU criterion does not. *(p.379)*
- The Goldsmith-Sahlin experiments provide empirical support: subjects prefer lottery tickets with more reliable probability estimates, explained by the MMEU criterion. *(p.362-363, 372)*

## Limitations
- The authors do not provide a full axiomatic characterization of the measure rho; they only require that it provide an ordering over distributions. *(p.367)*
- The MMEU criterion is generally applicable only when outcomes are non-negative from the decision maker's perspective; for negative outcomes, the 'reflection effect' and 'isolation effect' from Kahneman and Tversky's prospect theory cannot be captured. *(p.380)*
- The theory does not incorporate 'levels of aspiration' which would be needed for a more comprehensive account. *(p.380-381)*
- The paper uses traditional utility measures; the agent's values are not completely described by a utility measure alone. *(p.383, note 20)*
- The convexity requirement for P (Levi's assumption) may not always be realistic, as shown by the match C example where P/rho_0 can consist of disconnected intervals. *(p.383-384)*

## Arguments Against Prior Work
- **Against strict Bayesianism:** The assumption that beliefs can be represented by a *unique* probability measure is unrealistic. Dutch book arguments presuppose willingness to bet, which is too strong an assumption. People often refuse to bet precisely because probabilities are unreliable. *(p.364-365)*
- **Against Wald's statistical decision theory:** Wald does not introduce any factor corresponding to epistemic reliability rho, nor does he associate the choice of the distribution set Omega with risk taking. *(p.374)*
- **Against Hurwicz:** Like Wald, Hurwicz does not give an account of how the subset Omega_0 is determined, and does not introduce a measure corresponding to rho. *(p.374)*
- **Against Ellsberg's theory:** Ellsberg's confidence measure rho_e is defined for only one distribution y^0 (the estimated distribution), whereas the present theory defines rho for all distributions in P. Once P/rho_0 is selected, y^0 plays no outstanding role. *(p.376-377)*
- **Against Levi's theory:** Levi's S-admissibility criterion violates independence of irrelevant alternatives (adding a_1 to a decision between a_2 and a_3 can change which is preferred). The MMEU criterion satisfies this condition. *(p.379)*

## Design Rationale
- Using a *set* of probability measures P rather than a single measure allows the framework to honestly represent partial information about states of nature. *(p.365)*
- The reliability measure rho is kept as an ordering rather than a specific function to maintain generality. It can be interpreted as a second-order probability, but need not be. *(p.366-367)*
- The two-step procedure (filter by reliability, then maximin) separates the epistemic dimension (what do I know?) from the decision dimension (what should I do?), linking them through the risk parameter rho_0. *(p.370)*
- Choosing rho_0 is explicitly a risk-taking decision: higher rho_0 means more conservative (fewer distributions considered), lower means more risk-tolerant. *(p.370)*
- The MMEU criterion is chosen because it generalizes both classical maximin and Bayesian expected utility as limiting cases. *(p.373)*

## Testable Properties
- When rho_0 = 0 (all distributions in P are considered), MMEU should reduce to classical maximin over all possible states. *(p.373)*
- When P contains exactly one distribution (full information), MMEU should equal standard Bayesian expected utility maximization. *(p.373)*
- In the Ellsberg urn problem, MMEU should recommend a_1 > a_2 and a_4 > a_3 (matching empirical data). *(p.375-376)*
- Epistemic risk R(P/rho_0) = 0 when P/rho_0 = P (all distributions considered), and R approaches 1 when P/rho_0 contains only the single most reliable distribution. *(p.383)*
- MMEU should satisfy independence of irrelevant alternatives: adding or removing a non-optimal alternative should not change the ordering among remaining alternatives. *(p.379)*

## Relevance to Project
This paper is directly relevant to propstore's uncertainty representation architecture. The two-component belief model (P, rho) -- a set of epistemically possible probability distributions plus a reliability measure -- provides theoretical grounding for:
1. **Jøsang's uncertainty parameter u in Subjective Logic:** The epistemic reliability rho maps conceptually to the uncertainty mass u in a Subjective Logic opinion. Low reliability corresponds to high uncertainty. The relationship is: vacuous opinions (u=1) correspond to the limiting case where all distributions have equal (low) reliability.
2. **The MMEU criterion as a decision criterion:** This is closely related to the Hurwicz criterion already implemented in `world/types.py:apply_decision_criterion`, with alpha=0 (pure pessimism). The reliability filtering step adds a layer not currently implemented.
3. **Second-order probability:** Note 13 (p.382) explicitly discusses taking rho as a second-order probability measure, which connects to the broader literature on higher-order uncertainty that propstore's calibration pipeline addresses.
4. **Non-commitment discipline:** The core idea -- maintain a *set* of possible distributions rather than collapsing to one -- directly aligns with propstore's principle of never collapsing disagreement in storage.

## Open Questions
- [ ] How does the reliability measure rho relate formally to Jøsang's uncertainty mass u? Is rho = 1 - u a valid mapping?
- [ ] Can the MMEU criterion be implemented alongside the existing Hurwicz criterion as a new decision criterion that incorporates reliability filtering?
- [ ] The paper's note 13 suggests rho could be a second-order probability. How does this relate to Sensoy et al.'s evidential deep learning (Dirichlet-based uncertainty)?

## Related Work Worth Reading
- Levi, I.: 1974, 'On Indeterminate Probabilities', Journal of Philosophy 71, 391-418. [26] -- Most developed alternative theory using convex sets of probability measures
- Levi, I.: 1980, The Enterprise of Knowledge, MIT Press [27] -- Full theory of E-admissibility and S-admissibility
- Ellsberg, D.: 1961, 'Risk, Ambiguity, and the Savage Axioms', Quarterly Journal of Economics 75, 643-669 [8] -- Source of the Ellsberg paradox
- Keynes, J. M.: 1921, A Treatise on Probability [25] -- Original concept of 'weight of evidence' which parallels epistemic reliability
- Sahlin, N-E.: 1980, 'Level of Aspiration and Risk' [34] -- Connects risk-taking to levels of aspiration
- Goldsmith, R. W. and Sahlin, N-E.: 1982, 'The Role of Second-order Probabilities in Decision Making' [15] -- Empirical evidence for second-order probability effects

## Collection Cross-References

### Already in Collection
- [[Josang_2001_LogicUncertainProbabilities]] — Josang's Subjective Logic opinions (b,d,u,a) provide a concrete implementation of the two-component belief model (probability + uncertainty) that Gardenfors & Sahlin motivate philosophically. Josang 2001 cites Gardenfors.
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] — Reviews decision criteria under belief functions including Hurwicz and pignistic, directly comparable to the MMEU criterion proposed here.
- [[Shafer_1976_MathematicalTheoryEvidence]] — Dempster-Shafer belief functions formalize imprecise probabilities; Dempster [5] is cited in this paper.
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — BMS using Dempster-Shafer for graded beliefs, related to the epistemic reliability concept.
- [[Alchourron_1985_TheoryChange]] — AGM postulates for belief revision; Gardenfors is a co-author of AGM (different paper from same author).
- [[Dixon_1993_ATMSandAGM]] — Connects ATMS to AGM; cites Gardenfors's AGM work.

### New Leads (Not Yet in Collection)
- Ellsberg (1961) — "Risk, Ambiguity, and the Savage Axioms" — foundational paper on ambiguity aversion; the Ellsberg paradox is a key test case for the MMEU criterion
- Levi (1974) — "On Indeterminate Probabilities" — most developed alternative theory using convex sets of permissible probability measures
- Levi (1980) — The Enterprise of Knowledge — full theory of E-admissibility and S-admissibility
- Keynes (1921) — A Treatise on Probability — original concept of 'weight of evidence' paralleling epistemic reliability
- Kahneman & Tversky (1979) — "Prospect Theory" — the reflection and isolation effects that MMEU cannot capture
