---
title: "Probabilistic Argumentation: A Survey"
authors: "Anthony Hunter, Sylwia Polberg, Nico Potyka, Tjitze Rienstra, Matthias Thimm"
year: 2021
venue: "Handbook of Formal Argumentation, Volume 2, Chapter 7"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T08:13:00Z"
---
# Probabilistic Argumentation: A Survey

## One-Sentence Summary
A comprehensive taxonomy of probabilistic argumentation distinguishing epistemic (belief uncertainty over fixed topology) from constellation (topology uncertainty over subgraphs) approaches, with formal definitions of credulous/skeptical acceptance probability, extension probability, and labelling probability under each. *(p.1)*

## Problem Addressed
Argumentation is inherently pervaded by uncertainty: incomplete premises (enthymemes), uncertain argument structure, uncertain attack relations, uncertain degree of belief. This chapter surveys the state of the art in probabilistic argumentation, which quantifies these uncertainties. *(p.1)*

## Key Contributions
- Unified taxonomy of probabilistic argumentation into **epistemic** and **constellation** approaches *(p.6)*
- Formal definitions of rationality postulates for epistemic probability functions (COH, RAT, FOU, TRU, OPT) *(pp.13-14)*
- Formal definitions for three probability types in the constellation approach: labelling probability, acceptance probability, extension probability *(p.23)*
- Survey of PrAF (probabilistic argumentation framework) with independence assumption and its limitations *(pp.25-30)*
- Survey of combinations (epistemic + constellation), learning approaches, dynamics/dialogues, and argumentation for probabilistic models *(pp.30-35)*

## Methodology
Literature survey covering two main families of probabilistic argumentation plus emerging hybrid approaches. Provides formal definitions, worked examples, and cross-referencing between approaches.

## Key Equations / Statistical Models

### Epistemic approach — probability of argument

$$
P(a) = \sum_{Y \in 2^{Ar}: a \in Y} P(Y)
$$
Where: $P$ is a probability function on $2^{Ar}$ (power set of arguments), $P(a)$ is the marginal probability of argument $a$ being in the believed set.
*(p.11, Def 3.2)*

### Epistemic labelling from probability function

$$
\mathcal{L}ab_P(a) = \begin{cases} \texttt{in} & \text{if } P(a) > 0.5 \\ \texttt{out} & \text{if } P(a) < 0.5 \\ \texttt{undec} & \text{if } P(a) = 0.5 \end{cases}
$$
Where: the threshold 0.5 determines epistemic labelling status.
*(p.11, Def 3.3)*

### Congruence between labelling and probability

$$
\mathcal{L}ab \sim P \iff \forall a \in Ar: \mathcal{L}ab(a) = \texttt{in} \Leftrightarrow P(a) = 1, \quad \mathcal{L}ab(a) = \texttt{out} \Leftrightarrow P(a) = 0, \quad \mathcal{L}ab(a) = \texttt{undec} \Leftrightarrow P(a) = 0.5
$$
*(p.12)*

### COH rationality postulate

$$
\forall a, b \in Ar: (a,b) \in att \implies P(a) \leq 1 - P(b)
$$
Where: COH (coherent) ensures that if $a$ attacks $b$, then $P(a) + P(b) \leq 1$.
*(p.13)*

### RAT rationality postulate

$$
\forall a, b \in Ar: (a,b) \in att \implies P(a) > 0.5 \implies P(b) \leq 0.5
$$
Where: RAT (rational) is a weaker continuous version of COH.
*(p.13)*

### FOU (Founded) postulate

$$
\forall a \in Ar: a^- = \emptyset \implies P(a) = 1
$$
Where: unattacked arguments receive maximal degree of belief.
*(p.14)*

### TRU (Trusting) postulate

$$
\forall a \in Ar: (\forall b \in a^-: P(b) \leq 0.5) \implies P(a) \geq 0.5
$$
Where: if all attackers have low belief, the argument should be believed at least moderately.
*(p.14)*

### OPT (Optimistic) postulate

$$
P(a) \geq 1 - \sum_{b \in a^-} P(b)
$$
Where: belief in $a$ is bounded below by 1 minus the sum of beliefs in its attackers.
*(p.14)*

### Entropy of probability function

$$
H(P) = -\sum_{E \subseteq Ar} P(E) \log P(E)
$$
Where: used to select among probability functions satisfying rationality postulates. Grounded labelling corresponds to COH + OPT + max entropy.
*(p.15, footnote 3)*

### Constellation — subgraph distribution

$$
P^c : \wp(AF) \to [0,1], \quad \sum_{AF' \in \wp(AF)} P^c(AF') = 1
$$
Where: $\wp(AF)$ is the set of all subgraphs of $AF$. Full subgraph distribution restricts to full (induced) subgraphs; spanning subgraph distribution restricts to spanning subgraphs.
*(p.22, Def 4.3)*

### Labelling probability under constellation approach

$$
P_\sigma(\mathcal{L}ab) = \sum_{AF' \in \wp(AF) \text{ s.t. } \mathcal{L}ab \in \mathcal{L}_\sigma(AF')} P^c(AF')
$$
Where: $\mathcal{L}_\sigma(AF')$ is the set of all $\sigma$-labellings of subgraph $AF'$.
*(p.23, Def 4.4)*

### Acceptance probability under constellation approach

$$
P_\sigma(a) = \sum_{AF' \in \wp(AF) \text{ s.t. } \mathcal{L}ab \in \mathcal{L}_\sigma(AF') \text{ and } a \in \texttt{in}(\mathcal{L}ab)} P^c(AF')
$$
Where: probability that argument $a$ is labelled $\texttt{in}$ in some $\sigma$-labelling across all possible subgraphs.
*(p.23, Def 4.5)*

### Extension probability under constellation approach

$$
P_\sigma(W) = \sum_{AF' \in \wp(AF) \text{ s.t. } \exists \mathcal{L}ab \in \mathcal{L}_\sigma(AF'): W = \texttt{in}(\mathcal{L}ab)} P^c(AF')
$$
Where: probability that a set $W \subseteq Ar$ is a $\sigma$-extension.
*(p.23, Def 4.6)*

### PrAF — independence-based subgraph probability

$$
P(X) = \prod_{a \in X} P(a) \prod_{a \notin X} (1 - P(a))
$$
Where: $P(a)$ is the probability that argument $a$ is present. Independence between arguments is assumed. $AF \downarrow_X = (X, att \cap (X \times X))$ is the induced subgraph.
*(p.26, from Def 4.8)*

### PrAF — probability of acceptance

$$
P^{\text{PAF}}_{\circ,\sigma}(a) = \sum_{a \in X \subseteq Ar, AF\downarrow_X \models^{\circ}_{\sigma} a} P(X)
$$
Where: $\circ \in \{s, c\}$ for skeptical/credulous, $\sigma$ is a semantics. Sums probabilities of all subsets $X$ where $a$ is accepted under semantics $\sigma$ and inference mode $\circ$.
*(p.26)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Epistemic labelling threshold | - | - | 0.5 | [0,1] | 11 | P(a) > 0.5 => in, < 0.5 => out |
| COH constraint bound | - | - | - | P(a)+P(b) <= 1 for attacks | 13 | Coherence postulate |
| Argument presence probability | P(a) | - | - | [0,1] | 25 | PrAF per-argument probability |

## Methods & Implementation Details

### Three kinds of uncertainty in argumentation (pp.1-5)
1. **Incomplete premises / enthymemes**: Arguments in natural language often have implicit premises; explicit form may yield different attack graphs *(p.3)*
2. **Constellations / topology uncertainty**: Which arguments and attacks actually exist in the graph is uncertain *(p.6)*
3. **Epistemic / belief uncertainty**: The graph topology is fixed but degree of belief in each argument varies *(p.6)*

### Three kinds of uncertainty in attacks specifically (p.20)
1. **Explicit uncertainty of attack**: Explicit qualifier like "possibly" or "I am 90% sure" *(p.20)*
2. **Implicit imprecision of argument**: Natural language imprecision makes it unclear if two arguments conflict *(p.20)*
3. **Incomplete premises/claims**: Enthymemes make it uncertain whether one argument attacks another *(p.20)*

### Epistemic approach key mechanisms (pp.10-17)
- Probability function P on 2^Ar assigns probability to every subset of arguments *(p.10)*
- Epistemic extension = {a | P(a) > 0.5} *(p.12)*
- Congruence Lab ~ P: relates traditional labellings to probability functions *(p.12)*
- Five rationality postulates: COH, RAT, FOU, TRU, OPT *(pp.13-14)*
- Correspondences: admissible labelling <-> P satisfying COH + OPT; grounded labelling <-> COH + OPT + max entropy *(p.15)*
- Extension 3.1: Beliefs in attacks — belief that an attack is effective, not just belief in arguments [Polberg et al. 2015, Thimm et al. 2014] *(p.16)*
- Extension 3.2: Dynamics — update functions for epistemic probability distributions [Hunter and Potyka 2019] *(p.17)*
- Extension 3.3: Epistemic graphs — generalization using ADFs allowing arbitrary constraints between argument beliefs [Hunter et al. 2018b, 2020] *(p.17)*

### Constellation approach key mechanisms (pp.18-25)
- Subgraph distribution P^c over wp(AF) *(p.22)*
- Full subgraphs: remove arguments + induced edges. Spanning subgraphs: keep all arguments, remove some edges *(p.22)*
- Three probability notions: P_sigma(Lab), P_sigma(a), P_sigma(W) *(p.23)*
- PrAF = (Ar, att, P) with independence assumption [Li et al. 2011] *(p.25)*
- Independence limitation: correlated attacks (e.g., both attacks from same source) not correctly modeled *(pp.28-30)*

### Combinations and extensions (pp.30-35)
- Labelling Framework for Probabilistic Argumentation [Riveret et al. 2018]: three representations — PTFs (probability over rules), PGFs (probability over subgraphs), PLFs (probability over labellings). PLF can calculate probability of statement acceptance. *(p.31)*
- Learning: Riveret & Governatori 2018 — learning AF structure from labelling data; Kido & Morimura 2018 — Bayesian network for attack relation inference *(p.32)*
- Dialogues: Hunter 2013 — persuasion dialogues with epistemic probabilistic argumentation. Belief state = P over extensions. Update functions for persuadee feedback. *(p.33)*
- Structured argumentation connection: Timmer et al. 2015 — ASPIC+-based arguments to explain Bayesian network inference *(p.34)*
- Argumentation-based Bayesian fusion: Nielsen & Parsons 2007 *(p.34)*

## Figures of Interest
- **Fig 1 (p.4):** Two possible argument graphs from enthymemes — (a) mutual attack, (b) no attack
- **Fig 2 (p.6):** Attack graphs acquired by two listeners of a vaccine discussion — different topologies from same arguments
- **Fig 3 (p.9):** AF with 5-argument chain a1->a2->a3->a4->a5 with a5->a3 cycle. Table 1 shows all 5 complete labellings
- **Fig 4 (p.12):** Three arguments in a cycle — epistemic extension example
- **Fig 5 (p.15):** AF with 6 arguments and 4 probability functions showing which postulates each satisfies
- **Fig 6 (p.19):** Four subgraphs showing uncertain attack (c attacks b with varying confidence)
- **Fig 7 (p.24):** AF with subgraphs and subgraph distribution for grounded extension probability calculation
- **Fig 8 (p.26):** Chain a->b->c->d for PrAF acceptance probability example
- **Fig 9 (p.28):** Subgraphs of mutual attack AF — independence limitation example
- **Fig 10 (p.29):** Correlated attacks from same source — independence assumption fails

## Limitations
- PrAF independence assumption does not correctly model correlated attacks (e.g., when the same argument is the source of multiple attacks) *(pp.28-30)*
- Structured probabilistic argumentation (Hunter 2003) largely left out of scope *(p.35)*
- Computational complexity of constellation approach is high — exponential in number of arguments for general subgraph distributions *(p.30, referencing Fazzinga et al. 2013-2019)*
- The survey focuses primarily on abstract argumentation; structured argumentation receives limited coverage *(p.35)*

## Arguments Against Prior Work
- Independence assumption in PrAF (Li et al. 2011) is shown to be inadequate when attacks are correlated *(pp.28-30)*
- Standard three-valued labellings insufficient for representing degrees of belief — motivates the epistemic approach *(p.10)*
- Classical semantics cannot capture audience-specific belief differences *(p.12)*

## Design Rationale
- Epistemic approach chosen when topology is known but belief varies per agent *(p.6)*
- Constellation approach chosen when topology itself is uncertain *(p.6)*
- COH postulate as generalization of conflict-freeness to probabilities *(p.13)*
- RAT as weaker continuous version of COH *(p.13)*
- OPT captures the "optimistic" assumption that unattacked belief should be high *(p.14)*
- Entropy maximization selects grounded labelling among probability functions satisfying COH + OPT *(p.15)*

## Testable Properties
- COH: For any attack (a,b), P(a) + P(b) <= 1 *(p.13)*
- RAT: For any attack (a,b), P(a) > 0.5 implies P(b) <= 0.5 *(p.13)*
- FOU: Unattacked arguments have P(a) = 1 *(p.14)*
- TRU: If all attackers have P <= 0.5, then P(a) >= 0.5 *(p.14)*
- OPT: P(a) >= 1 - sum of P(b) for all attackers b *(p.14)*
- Congruence: If Lab is admissible and P satisfies COH + OPT, then Lab ~ P *(p.15)*
- Grounded: If Lab is grounded labelling and P satisfies COH + OPT with max entropy, then Lab ~ P *(p.15)*
- PrAF independence: P(X) = product of P(a) for a in X times product of (1-P(a)) for a not in X, and sum over all X of P(X) = 1 *(p.26)*
- PrAF acceptance probability is between 0 and 1 for any argument *(p.26)*
- Labelling probability + extension probability + acceptance probability are all derivable from subgraph distribution *(p.23)*

## Relevance to Project
This paper provides the authoritative taxonomy that propstore's probabilistic argumentation layer needs. Specifically:
1. **Credulous vs skeptical acceptance probability** (Def 4.5 with inference modes s,c) — this is the taxonomy Q requested
2. **Extension probability** (Def 4.6) — probability that a given set W is a sigma-extension
3. **Labelling probability** (Def 4.4) — probability of a specific labelling
4. The rationality postulates (COH, RAT, FOU, TRU, OPT) provide correctness criteria for propstore's epistemic probability assignments
5. The distinction between epistemic and constellation approaches maps directly to propstore's existing PrAF implementation (constellation) and potential future epistemic extensions
6. The independence limitation analysis (pp.28-30) is relevant to propstore's current PrAF which assumes independence

## Open Questions
- [ ] Should propstore implement epistemic approach alongside constellation PrAF?
- [ ] How to handle correlated attacks (non-independent PrAF) efficiently?
- [ ] Should rationality postulates (COH, OPT) be enforced as constraints on probability assignments?
- [ ] Epistemic graphs (Sec 3.3) — would arbitrary constraints between argument beliefs be useful?

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — foundational AF definition; this survey builds on Dung's semantics throughout
- [[Li_2011_ProbabilisticArgumentationFrameworks]] — original PrAF definition with independence assumption; Sec 4.3 reviews and critiques this approach
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — earlier work by same first author on epistemic probabilistic argumentation; this survey extends and contextualizes it
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — bipolar AFs; constellation approach extended to bipolar in Sec 4.4
- [[Cayrol_2014_ChangeAbstractArgumentationFrameworks]] — AF dynamics; related to Sec 3.2 on epistemic dynamics
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — SCC decomposition; relevant to efficient computation of extension probabilities
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — principle-based evaluation cited in Sec 2 preliminaries
- [[Caminada_2006_IssueReinstatementArgumentation]] — labelling-based semantics; foundation for Sec 2 labellings
- [[Fazzinga_2016_EfficientlyEstimatingProbabilityExtensions]] — complexity results for probabilistic AF computation
- [[Brewka_2010_AbstractDialecticalFrameworks]] — ADFs; Sec 3.3 epistemic graphs generalize via ADFs
- [[Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault]] — assumption-based argumentation
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ framework; Sec 5.4 connects probabilistic argumentation to ASPIC+ via Timmer et al. 2015

### New Leads (Not Yet in Collection)
- Riveret et al. (2018) — "A labelling framework for probabilistic argumentation" — combines epistemic + constellation approaches into unified PTF/PGF/PLF framework
- Fazzinga et al. (2018a) — "Credulous and skeptical acceptability in probabilistic abstract argumentation: complexity results" — direct complexity results for propstore's MC sampling approach
- Potyka (2019) — "A polynomial-time fragment of epistemic probabilistic argumentation" — could inform efficient epistemic implementation
- Timmer et al. (2015) — "Explaining Bayesian networks using argumentation" — ASPIC+-based arguments for Bayesian inference explanation
- Kido and Morimura (2018) — "Bayesian network for attack relation inference" — learning AF structure

### Cited By (in Collection)
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — cites Hunter et al. for probabilistic argumentation context

### Conceptual Links (not citation-based)
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — directly extends this earlier work; the survey provides the broader context and taxonomy for the specific formalization in Hunter & Thimm 2017
- [[Li_2011_ProbabilisticArgumentationFrameworks]] — the PrAF definition reviewed here is propstore's primary probabilistic AF implementation; the independence limitation analysis (pp.28-30) directly applies to propstore's current approach

## Related Work Worth Reading
- Riveret et al. 2018: Labelling Framework for Probabilistic Argumentation — combines epistemic + constellation
- Fazzinga et al. 2013-2019: Computational complexity results for probabilistic abstract argumentation
- Hunter 2013: Epistemic probabilistic argumentation for persuasion dialogues
- Timmer et al. 2015: ASPIC+-based argumentation for explaining Bayesian network inference
- Kido and Morimura 2018: Bayesian network for attack relation inference
- Riveret and Governatori 2018: Learning AF structure from labellings
- Hunter et al. 2018b, 2020: Epistemic graphs
- Dung and Thang 2010: First constellation approach with subgraph probabilities for grounded semantics
- Baroni et al. 2019: Constellation extended to graded semantics via credit sets
