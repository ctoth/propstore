---
title: "Epistemic Graphs for Representing and Reasoning with Positive and Negative Influences of Arguments"
authors: "Anthony Hunter, Sylwia Polberg, Matthias Thimm"
year: 2018
venue: "arXiv preprint; published version in Artificial Intelligence"
doi_url: "https://doi.org/10.1016/j.artint.2020.103236"
pages: 66
produced_by:
  agent: "GPT-5 Codex"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T18:44:13Z"
---
# Epistemic Graphs for Representing and Reasoning with Positive and Negative Influences of Arguments

## One-Sentence Summary
The paper defines epistemic graphs: labelled argument graphs equipped with probabilistic epistemic constraints, proof rules, entailment relations, coverage conditions, and graph-coherence checks for modelling fine-grained belief, disbelief, support, attack, dependency, context-sensitivity, incomplete graph knowledge, and imperfect agents. *(pp.1-66)*

## Problem Addressed
Classical Dung-style argumentation and many bipolar/weighted/ranking formalisms often force coarse accepted/rejected statuses, fixed interpretations of attack/support, or graph-global semantics that are too rigid for applications where agents hold degrees of belief, decode enthymemes differently, possess incomplete information, or use context-dependent relations between arguments. *(pp.3-8)*

The authors target monological and dialogical settings where a modeller may need to estimate another agent's belief in arguments and reasons for that belief, then choose a next dialogue move or evaluate a scenario despite uncertainty about the agent's private knowledge and rationality. *(p.3)*

## Key Contributions
- Introduces epistemic graphs as a generalization of the epistemic approach to probabilistic argumentation: a labelled graph plus a set of epistemic constraints over argument probabilities. *(pp.8, 19-20)*
- Provides an epistemic language of Boolean combinations of inequalities over probabilities of argument terms, including operational formulae over sums/differences of term probabilities. *(pp.9-11)*
- Defines a restricted epistemic language over finite rational value sets, designed for cases such as Likert-style belief data and for automated reasoning via constraint solving. *(pp.11-13, 19)*
- Defines epistemic entailment, restricted epistemic entailment, a proof-theoretic consequence relation, soundness, completeness, proof by contradiction, and an equivalence with classical propositional reasoning for the restricted case. *(pp.15-19)*
- Defines epistemic graph consistency, relation coverage, labelling coverage, internal graph coherence, epistemic semantics, and practical modelling examples. *(pp.19-21 and later sections)*

## Study Design (empirical papers)

## Methodology
The paper is formal and constructive. It first motivates requirements by examples, then defines a probability-based language over argument terms and distributions. It restricts that language to finite value sets for implementability, introduces a proof system for the restricted fragment, proves soundness and completeness, and then lifts the language to labelled graphs with constraints that explain or check edge labels. *(pp.3-21)*

## Key Equations / Statistical Models

$$
P(\alpha)=\sum_{\Gamma \subseteq Nodes(G)\ \mathrm{s.t.}\ \Gamma \models \alpha} P(\Gamma)
$$
Where: `G` is the directed argument graph; `Nodes(G)` is the set of arguments; `P` is a belief distribution over subsets of `Nodes(G)`; `alpha` is a term, i.e. a Boolean formula over arguments; and `Gamma models alpha` is classical satisfaction. This defines the probability of a term as the sum of the probabilities of its models. *(p.11)*

$$
Sat(\varphi)=\{P \in Dist(G)\mid P(\alpha_1) *_{1}\cdots *_{k-1} P(\alpha_k)\ \#\ b\}
$$
Where: `varphi` is an epistemic atom of the form `p(alpha_1) *1 ... *k-1 p(alpha_k) # b`; each `alpha_i` is a term; each arithmetic operator is `+` or `-`; `#` is one of `=, !=, >=, <=, >, <`; and `b` is in `[0,1]`. *(p.11)*

$$
Sat(\phi \wedge \psi)=Sat(\phi)\cap Sat(\psi)
$$
$$
Sat(\phi \vee \psi)=Sat(\phi)\cup Sat(\psi)
$$
$$
Sat(\neg \phi)=Sat(\top)\setminus Sat(\phi)
$$
Where: satisfaction for compound epistemic formulae is set-theoretic over satisfying belief distributions. *(p.11)*

$$
Sat(\psi,\Pi)=Sat(\psi)\cap Dist(G,\Pi)
$$
Where: `Pi` is a restricted value set and `Dist(G, Pi)` is the set of distributions whose set and argument probabilities all lie in `Pi`. *(p.12)*

$$
\{\phi_1,\ldots,\phi_n\}\models \psi \quad\mathrm{iff}\quad Sat(\{\phi_1,\ldots,\phi_n\})\subseteq Sat(\psi)
$$
Where: this is unrestricted epistemic entailment. *(p.15)*

$$
\{\phi_1,\ldots,\phi_n\}\models_{\Pi}\psi \quad\mathrm{iff}\quad Sat(\{\phi_1,\ldots,\phi_n\},\Pi)\subseteq Sat(\psi,\Pi)
$$
Where: this is restricted epistemic entailment with respect to a finite restricted value set `Pi`. *(p.15)*

$$
p(\alpha\vee\beta)-p(\alpha)-p(\beta)+p(\alpha\wedge\beta)=0
$$
Where: this proof rule captures the probabilistic inclusion-exclusion identity for two argument terms. *(p.17)*

$$
Closure(\Phi)=\{\psi\mid \Phi\models\psi\}
$$
Where: unrestricted epistemic closure returns every formula entailed by a formula set. *(p.19)*

$$
Closure(\Phi,\Pi)=\{\psi\mid \Phi\models_{\Pi}\psi\}
$$
Where: restricted epistemic closure returns every formula entailed under restricted distributions over `Pi`. *(p.19)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Belief probability for a distribution state | `P(Gamma)` | - | - | `[0,1]` | 11 | Distribution over subsets of graph nodes. |
| Belief/disbelief threshold | `P(alpha)` | - | `0.5` | `[0,1]` | 11 | The authors say an agent believes a term when probability is greater than 0.5, disbelieves when below 0.5, and neither believes nor disbelieves when equal to 0.5. |
| Restricted value set examples | `Pi_1`, `Pi_2`, `Pi_3`, `Pi_4` | - | - | finite subsets of `[0,1]` | 12 | Examples include `{0,0.5,0.75,1}` as non-restricted because `0.75-0.5=0.25` is missing, `{0,0.25,0.5,0.75,1}`, `{0,1/3,2/3,1}`, and `{0,1/5,2/5,3/5,4/5,1}`. |
| Likert-style restricted scale | `Pi` | - | - | often 5 to 11 response options | 11, 13, 19 | Motivation for restricting probability values to finite sets. |
| Example restricted value set for consequence relation | `Pi` | - | `{0,0.2,0.4,0.6,0.8,1.0}` | finite subset of `[0,1]` | 17 | Used in examples of restricted consequence. |
| Example restricted value set for closure | `Pi` | - | `{0,0.1,0.2,...,0.9,1}` | finite subset of `[0,1]` | 19 | Used to illustrate restricted closure. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Not empirical | - | - | - | - | The paper is formal; quantitative values are formal thresholds and finite value-set examples, captured under Parameters and Equations. | 1-21 |

## Methods & Implementation Details
- Represent an argument graph as a directed graph `G=(V,A)` where nodes are arguments and arcs are relations. A labelling function maps each arc to a nonempty subset of label set `Omega`, initially `{+,-,*}` for support, attack, and dependency. *(p.9)*
- Treat a single arc as possibly multi-labelled, because two arguments can be connected in more than one way. *(p.9)*
- `Nodes(G)` denotes `V`; `Arcs(G)` denotes arcs; `Parents(B)` are nodes with arcs into `B`; `Parent^x(B)` filters parents by edge label `x`; `L^x(G)` filters arcs labelled `x`. *(p.9)*
- Use terms as Boolean combinations of arguments, with `not`, `and`, `or`, and derived implication. `Terms(G)` is the set of all terms. *(p.10)*
- Use operational formulae of the form `p(alpha_1) *1 ... *k-1 p(alpha_k)`, where each `alpha_i` is a term and each arithmetic operator is `+` or `-`. *(p.10)*
- Use epistemic atoms by comparing an operational formula with a numeric value using `=`, `!=`, `>=`, `<=`, `>`, or `<`. *(p.10)*
- Use epistemic formulae as Boolean combinations of epistemic atoms; `EFormulae(G)` is the set of all epistemic formulae. *(p.10)*
- Use `Args(alpha)`, `FArgs(psi)`, `FTerms(psi)`, `Num(psi)`, and `AOp(psi)` to extract arguments, terms, numeric constants, and arithmetic operator sequences from formulae. *(p.10)*
- Use a belief distribution `P: 2^{Nodes(G)} -> [0,1]` with total mass `1`; `Dist(G)` is the set of such distributions. *(p.11)*
- Encode a model as a binary number once an argument ordering is fixed: the ith digit is 1 iff the ith argument is in the model. *(p.11)*
- Define restricted value sets as finite rational subsets of `[0,1]` closed under addition and subtraction when results remain in `[0,1]`. *(pp.11-12)*
- A distribution is restricted with respect to `Pi` iff all set probabilities and all argument probabilities lie in `Pi`. *(p.12)*
- A restricted value set is reasonable iff every nonempty finite graph has at least one restricted distribution over that set; the paper observes `{0,0.9}` can fail this condition. *(p.12)*
- Use argument-complete terms to describe exact subsets of argument nodes, then define a formula associated with a distribution by assigning probabilities to every complete term. *(pp.13-14)*
- Transform restricted formulae into distribution disjunctive normal form (DDNF), a disjunction of formulae associated with exactly the restricted distributions satisfying the formula. *(p.14)*
- Implement restricted reasoning as a proof system over basic probability bounds, inclusion-exclusion, subject weakening/strengthening, enumeration rules over restricted combination sets, and propositional rules. *(pp.16-17)*
- The restricted language can be implemented using constraint satisfaction techniques because inequalities can be rewritten as disjunctions of equalities over finite values. *(p.19)*

## Figures of Interest
- **Fig. 1 (p.5):** Jack and Jill have structurally similar train-arrival graphs but decode enthymemes and trust live travel information differently; this motivates context-sensitive and agent-relative interpretation of influences.
- **Fig. 2 (p.6):** Smoking-cessation persuasion graph where different users select different counterarguments and respond differently to proposed remedies; motivates modelling hidden user beliefs and imperfect/incomplete graph knowledge.
- **Fig. 3 (p.10):** Tripolar team-formation graph with positive, negative, and dependency labels; dependency is used where an influence cannot be classified as strictly support or attack.
- **Fig. 4 (p.20):** Party-organization graph with support and attack labels, used to show how explicit constraints can encode support, budget attack, and conflict between arguments.
- **Fig. 5 (p.21):** University-choice graph where one relation is supporting at some belief levels and attacking/dependency-like at others, motivating nonmonotone relation classifications.

## Results Summary
By page 21, the paper has established the formal language and proof machinery needed for epistemic graphs. It shows that the restricted epistemic consequence relation is sound and complete with respect to restricted epistemic entailment, supports proof by contradiction, and is equivalent in expressivity and inference power to classical propositional consequence when finite restricted value sets are used. *(pp.18-19)*

## Limitations
- The paper does not address how to learn probability distributions or constraints from data; it points to crowdsourced-data work and leaves machine learning of constraints for future work. *(p.8)*
- At the implementation level, the paper says it stays conceptual and leaves deeper CSP implementation details for future work. *(p.20)*
- Restricted entailment does not generally imply unrestricted entailment because the finite value set contains extra domain assumptions; the appropriate value set must be chosen for each property. *(p.15)*

## Arguments Against Prior Work
- Two-valued extension/labelling semantics can be insufficient for modelling degrees of belief and disagreement in practical applications. *(pp.3, 9)*
- Existing weighted, ranking, probabilistic, and belief-postulate approaches offer fine-grained alternatives but often have influence aggregation methods that make context-sensitivity, different perspectives, and incomplete graphs difficult. *(p.7)*
- Abstract dialectical frameworks can express local acceptance conditions and incoming influence flexibly, but the paper argues their common two/three-valued semantics and restrictions still leave the targeted modelling problems insufficiently handled. *(p.7)*

## Design Rationale
- Use probabilities of argument terms rather than binary acceptance labels so the system can express belief, disbelief, neutrality, and graded influence. *(pp.8-11)*
- Keep the graph labels separate from constraints because constraints should not be treated as syntactic cues that fully induce graph direction or labelling. *(p.20)*
- Add a restricted language because many practical sources of belief data use finite scales and because finite values make automated reasoning via CSP practical. *(pp.11-13, 19)*
- Include dependency `*` in addition to support and attack because some relations are neither strictly positive nor strictly negative and may change role depending on other accepted arguments. *(pp.9-10, 21)*

## Testable Properties
- A labelled graph is fully labelled iff every arc has at least one label; it is uni-labelled iff every arc has exactly one label. *(p.9)*
- If `P(alpha)>0.5`, the agent believes `alpha`; if `P(alpha)<0.5`, the agent disbelieves `alpha`; if `P(alpha)=0.5`, the agent neither believes nor disbelieves it. *(p.11)*
- Any nonempty restricted value set contains `0`; any reasonable restricted value set contains `0` and `1`; a restricted value set is reasonable iff `1` is included. *(pp.12-13)*
- For any distribution `P`, the formula associated with `P` has exactly `{P}` as its satisfying set. *(p.14)*
- For a reasonable restricted value set, a restricted formula and its DDNF have the same restricted satisfying distributions. *(p.14)*
- Restricted consequence is sound and complete with respect to restricted entailment. *(pp.18-19)*
- Restricted epistemic consequence supports proof by contradiction: `Phi entails_Pi psi` iff `Phi union {not psi}` entails_Pi contradiction. *(p.18)*
- Restricted epistemic language with restricted consequence is equivalent to classical propositional language with classical consequence. *(p.19)*

## Relevance to Project
This paper is directly relevant to a propstore-style system that needs canonical claims, stances, justifications, source-local readings, and argument relations with uncertainty. Its main implementation value is a precise separation between graph structure, relation labels, and source-local epistemic constraints over belief distributions, plus a finite-value restricted fragment that could map naturally to validated enum/rational domains and solver-backed consistency checks.

## Open Questions
- [ ] How should propstore represent belief distributions over argument subsets without exponential blowup?
- [ ] Should restricted value sets be global per source, per graph, or per reasoning context?
- [ ] Can relation coverage and internal graph coherence be checked incrementally as sources are imported?
- [ ] How should source-local user/modeller belief constraints be kept out of canonical identity surfaces while still supporting canonical query projections?

## Related Work Worth Reading
- Abstract dialectical frameworks and bipolar argumentation papers cited by the authors as the closest comparison class. *(pp.7-8)*
- Work on probabilistic argumentation and the epistemic approach, which this paper explicitly generalizes. *(p.8)*
- Constraint satisfaction literature used for implementing restricted reasoning. *(pp.19-20)*

## Detailed Extraction: Epistemic Graph Coverage, Relation Types, Coherence, and Semantics

### Epistemic Graphs and Coverage
An epistemic graph is a labelled graph equipped with a set of epistemic constraints that contain at least one argument. Constraints that operate only on truth values are excluded as redundant, though this restriction is optional. Formally, an epistemic constraint is an epistemic formula `psi in EFormulae(G)` with `FArgs(psi) != empty`; an epistemic graph is `(G,L,C)`, where `(G,L)` is a labelled graph and `C` is a set of epistemic constraints. *(p.20)*

The graph is consistent iff its set of constraints is consistent. The authors stress that graph structure and labels are not necessarily induced by constraints: the constraint `p(A)<0.5 or p(B)<0.5` does not determine the direction of an edge between `A` and `B`. For readability, constraints may reflect edge direction, but they should not generally be treated as syntactic cues for graph structure. *(p.20)*

Coverage measures whether constraints account for arguments and relations. A useful graph need not have constraints covering all possible scenarios, but coverage information helps distinguish limited knowledge from under-specified or ineffective relations. *(p.22)*

#### Constraint Combinations
Definition 5.2 introduces exact and soft constraint combinations for a set of arguments `F={A_1,...,A_m}`. *(p.22)*

$$
CC^F=\{p(A_1)=x_1,\ldots,p(A_m)=x_m\}
$$
Where: an exact constraint combination assigns exact probabilities to every argument in `F`, with each `x_i in [0,1]`. *(p.22)*

$$
CC^F=\{p(A_1)\#_1x_1,\ldots,p(A_m)\#_mx_m\}
$$
Where: a soft constraint combination allows inequalities `#_i in {=, !=, >=, <=, >, <}`. *(p.22)*

For `G subseteq Nodes(G)`, `CC^F|_G` denotes the subset of a combination containing only constraints for arguments in `F cap G`. *(p.22)*

#### Argument Coverage
Default coverage: an argument `A` in a consistent epistemic graph `X=(G,L,C)` is default covered iff there is a value `x in [0,1]` such that `C entails p(A) != x`. This means the constraints alone rule out at least one belief value for `A`. *(p.22)*

Partial coverage by a set `F`: `A` is partially covered by `F` iff there exists a constraint combination `CC^F` and a value `x` such that `CC^F union C` is consistent and `CC^F union C entails p(A) != x`. *(p.23)*

Full coverage by `F`: `A` is fully covered by `F` iff for every constraint combination `CC^F` consistent with `C`, there exists a value `x` such that `CC^F union C entails p(A) != x`. *(p.23)*

Arbitrary partial/full coverage: `A` has arbitrary full or partial coverage iff there exists some `F subseteq Nodes(G)\{A}` such that `A` is fully or partially covered with respect to `F`. *(p.24)*

Coverage relationships: default coverage implies both partial and full coverage with respect to any argument set, but not conversely; full coverage implies partial coverage with respect to the same `F`, but not conversely. If two consistent epistemic graphs have constraint sets with the same satisfying distributions, coverage analysis gives the same results. *(p.24)*

### Relation Coverage and Effectiveness
Relation coverage checks whether a source argument can change restrictions on the target argument, including implicit relations not explicitly present in `Arcs(G)`. *(pp.24-25)*

Definition 5.8 defines a relation `(A,B)` as effective with respect to `F` when there exists a constraint combination over `F` and values `x,y` such that the base constraints remain consistent, adding `p(A)=y` remains consistent, and changing the source `A` changes whether `p(B) != x` is entailed. It is strongly effective when that can be witnessed for every consistent constraint combination over `F`. *(p.25)*

Definition 5.9 weakens effectiveness to semi-effectiveness by testing against any consistent set `Z` drawn from `Closure(C)` rather than all constraints `C`. This allows detection of relations whose local effect is hidden by other constraints. Strong semi-effectiveness requires the witness condition for every consistent combination. *(p.26)*

Effectiveness relationships include: strong effectiveness implies effectiveness; strong semi-effectiveness implies semi-effectiveness; effectiveness with respect to `F` is equivalent to semi-effectiveness with respect to `(C,F)`; strong effectiveness is equivalent to strong semi-effectiveness with respect to `(C,F)`; if `Z != C`, semi-effectiveness need not imply effectiveness and strong semi-effectiveness need not imply strong effectiveness. *(p.26)*

### Relation Types
The paper distinguishes relation labels supplied during graph instantiation from labels derived from constraints. Local edge labelling can miss global or contextual effects. For example, a local supporter of `B` may indirectly attack `B` by supporting an attacker of `B`. *(p.27)*

Definitions 5.11 and 5.12 classify semi-effective relations with respect to `(Z,F)`:

- Attacking: when the source being believed preserves or causes target disbelief, avoiding cases where believing the source would lead to believing the target. *(pp.28-29)*
- Supporting: when the source being believed preserves or causes target belief. *(p.29)*
- Dependent: semi-effective but neither attacking nor supporting. *(p.29)*
- Subtle: both attacking and supporting. *(p.29)*
- Unspecified: not semi-effective. *(p.29)*
- Strong supporting/attacking/dependent/subtle: strengthened versions requiring the relevant witness conditions across all consistent combinations and at least one combination where the source is believed, disbelieved, or both as appropriate. *(p.29)*

Definition 5.13 adds monotonic relation types. `(A,B)` is positive monotonic with respect to `(Z,F)` iff, for all satisfying distributions `P,P'`, if `P(A)>P'(A)` and all other arguments in `F` except `A,B` are fixed, then `P(B)>P'(B)`. Negative monotonic reverses the target inequality. Non-monotonic dependent means neither positive nor negative monotonic. *(pp.29-30)*

The authors emphasize that epistemic graphs remain standard directed graphs rather than hypergraphs, but relation-specific notions can still capture non-binary effects because definitions quantify over parameter sets `F`. Forcing support to always have a positive effect would impose a binary interpretation the framework deliberately avoids. *(p.30)*

### Internal Graph Coherence
Internal graph coherence compares information extracted from constraints with information presented by graph structure. Definition 5.14 introduces several quality/coherence properties: *(p.31)*

- Bounded: every argument is default covered or arbitrary fully covered. *(p.31)*
- Entry-bounded: every argument is default or arbitrary fully covered except possibly arguments with no parents. *(p.31)*
- Directly connected: every explicit relation in `Arcs(G)` is arbitrary semi-effective. *(p.31)*
- Indirectly connected: every pair connected by an undirected path is arbitrary semi-effective. *(p.31)*
- Hidden connected: there exists an arbitrary semi-effective relation not reflected by any undirected path in the graph. *(p.31)*
- Locally connected: for every argument `A`, there exists a consistent `Z subseteq Closure(C)` such that `A` is fully covered with respect to the directly connected arguments around `A`, and every direct relation around `A` is semi-effective under that same local context. *(p.31)*

Definition 5.15 defines label consistency. A labelling is consistent when every `+` edge is arbitrary supporting, every `-` edge is arbitrary attacking, every `*` edge is arbitrary dependent, and an unlabelled edge is arbitrary unspecified. Strong consistency uses strong relation types. Monotonic consistency maps `+` to arbitrary positive monotonic, `-` to arbitrary negative monotonic, and `*` to arbitrary non-monotonic dependent. *(pp.31-32)*

The authors explicitly do not solve consistency repair. Possible strategies include overriding graph labels, deleting constraints, deleting graph structure, preserving both and treating inconsistency as evidence, or choosing by accuracy/popularity of extraction methods. They leave consistency-retrieval strategies for future work. *(p.32)*

### Epistemic Semantics
Definition 5.16: an epistemic semantics associates an epistemic graph `X=(G,L,C)` with a set `R subseteq Dist(G)` of belief distributions. *(p.33)*

Definition 5.17: satisfaction semantics returns distributions satisfying the graph constraints: `P in Sat(C)`. The authors note inconsistent graphs may arise when trying to emulate stable semantics, because restrictive graph-based semantics may not always produce extensions; inconsistency does not necessarily mean irrational constraints. *(p.33)*

Definition 5.18 introduces distribution orderings:

- Acceptance ordering `P <=_A P'` iff every argument believed by `P` is believed by `P'`.
- Rejection ordering `P <=_R P'` iff every argument disbelieved by `P` is disbelieved by `P'`.
- Undecided ordering `P <=_U P'` iff every argument undecided under `P` is undecided under `P'`.
- Information ordering `P <=_I P'` iff every believed argument under `P` is believed under `P'` and every disbelieved argument under `P` is disbelieved under `P'`.
*(p.33)*

Definition 5.19 gives entropy for a distribution:

$$
H(P)=-\sum_{\Gamma\subseteq Nodes(G)}P(\Gamma)\log P(\Gamma)
$$
Where: `0 log 0 = 0`; entropy measures indeterminateness, with absolute certainty giving entropy `0` and the uniform distribution giving maximal entropy. *(p.33)*

Definition 5.20 defines belief ordering by entropy: `P <=_B P'` iff `H(P') <= H(P)`, so lower entropy is considered greater belief/information concentration. *(p.34)*

Definition 5.21 parameterizes maximizing/minimizing semantics over acceptance, rejection, undecided, information, and belief orderings. Given an existing semantics `sigma` producing `R`, a distribution meets `sigma-v` maximizing/minimizing semantics iff it is maximal/minimal with respect to the chosen ordering among elements of `R`. *(p.34)*

Definition 5.22 defines optional distribution properties: minimal iff every argument has probability `0`; maximal iff every argument has probability `1`; neutral iff every argument has probability `0.5`; ternary iff every argument has probability in `{0,0.5,1}`; non-neutral iff every argument avoids `0.5`; `n`-valued iff exactly `n` distinct argument probability values occur. *(p.34)*

### Persuasive Dialogue Case Study
The case study models automated persuasion systems with two coupled components: a domain model containing arguments available to the system and arguments the user may entertain, and a user model containing the system's current beliefs about the user and their likely argument beliefs as dialogue proceeds. *(p.36)*

The dental-checkup domain model contains target argument `A` ("I should book regular dental check-ups"), supporters/attackers such as `B` regular check-ups help teeth, `C` lack of money, `D` check-ups painful, `E` daily brushing/flossing, `F` liking to be healthy, `G` free care for low income, `H` untreated dental problem becomes painful, and `I` check-ups painful because teeth/gums are in bad shape. *(p.36)*

The user-profile constraints include: `(p(B)>0.5 or p(C)<0.5 or p(D)<0.5) <-> p(A)>0.5`; `(p(B)>0.65 -> p(A)>0.8) and (p(B)>0.8 -> p(A)=1)`; `p(D)<0.2 -> p(A)>0.65`; `(p(F)>0.5 -> p(B)>0.65) and (p(F)<0.5 -> p(B)<0.5)`; and `p(G)+p(C)<=1`. *(p.37)*

The case study compares dialogue routes:

- **Option B:** increasing belief in `B` appears graphically related to increasing `F` or decreasing `E`, but constraint analysis says `E` is unspecified and the labelling is inconsistent; increasing `B` can only be done through `F`. An optimistic system may trust the learned constraints and choose `F`; a pessimistic system may treat `E` as a potential attacker because learned data may be incomplete. *(pp.37-38)*
- **Option D:** making `D` disbelieved can make `A` believed; graph labels suggest increasing `H` or `I`, but constraint analysis makes both relations unspecified. Optimistic and pessimistic strategies may diverge again. *(p.38)*
- **Option C:** increasing belief in `G` decreases belief in `C` and yields the smallest gain in `A`, but graph and constraints agree, making it the safest route. *(p.38)*

The case study does not specify how exact update values are chosen. It points to work on updates in epistemic graphs and querying users during dialogue. *(p.38)*

### Related-Work Comparisons Read So Far
Weighted/ranking semantics often assign numbers to arguments, but those values are interpreted as abstract weights/strengths rather than belief. Many weighted postulates are counterintuitive for epistemic graphs because hidden connections can matter, parent values may be forced into global patterns, and requiring one global specificity level would be unrealistic when constraints are mined with varying quality. *(pp.39-40)*

ADFs and epistemic graphs both support positive, negative, and neutral/dependency-like relations. ADFs use per-argument acceptance conditions and often three-valued labellings, while epistemic graphs use graph-level probabilistic constraints over belief degrees. The authors argue epistemic graphs are more fine-grained, can encode ranges of acceptable values, can model dependencies beyond parents, and need not require completeness of per-argument acceptance conditions. *(pp.40-41)*

### Remaining Related Work
The paper shows how ADF acceptance conditions can be translated into epistemic constraints by replacing positive literals with belief atoms such as `p(Z)>0.5` and negative literals with disbelief atoms such as `p(Z)<0.5`. Complete ADF labellings can be retrieved by transforming ternary satisfying distributions: arguments believed map to `t`, disbelieved to `f`, and neither to `u`; preferred or grounded labellings can be retrieved by adding information maximizing/minimizing. *(pp.41-42)*

Probabilistic ADFs are distinguished because they use constellation probabilities rather than epistemic probabilities, producing a different modelling interpretation. Weighted ADFs overlap partly but enforce condition completeness, parent-only dependence, and precise outcomes for combinations of parent values, while epistemic graphs allow constraints such as "if the attacker is believed, the attackee should be disbelieved" without forcing target belief to be a function only of source belief. Weighted ADFs can also use an undefined value with a different meaning from epistemic neutrality. *(p.42)*

Constrained argumentation frameworks impose external propositional constraints over argument extensions and can be mapped into epistemic constraints, but they are mainly two-valued and do not address fine-grained acceptability. Example 40 shows a conflict-based graph augmented with `PC = not A or D`; after translating the graph and the external constraint into epistemic constraints, adding `p(A)<=0.5 or p(D)>0.5` excludes distributions corresponding to disallowed extensions, and information maximality retrieves the desired preferred extensions. *(pp.42-43)*

Constraint programming is presented as an implementation path: epistemic graphs can be treated as CSPs over probabilistic and argumentative constraints, using existing solvers. The authors say their proposal is the first to turn reasoning with beliefs in arguments into a CSP-style problem that includes entailment, consequence, and epistemic semantics; they mention current work on linear-optimization formulations for updates in subclasses of epistemic graphs. *(p.44)*

Bayesian networks differ in motivation and representation. Bayesian networks are acyclic graphs over random variables and causal influences, using one probability distribution and conditioning-based updates; epistemic graphs allow multiple satisfying belief distributions, uncertain belief updates to arbitrary degrees, and rich constraints between argument variables rather than fixed conditional-probability propagation. Bayesian networks target normative reasoning; epistemic graphs target non-normative modelling of how people may reason with uncertainty about arguments. *(pp.44-45)*

### Discussion and Future Work
The discussion states that the proposal meets the initial requirements:

- Fine-grained acceptability: belief degrees are explicit and constrained by epistemic constraints, with clearer semantics than abstract scores/ranks. *(p.45)*
- Positive and negative relations: epistemic graphs can model positive, negative, mixed, binary, and group relations, and can distinguish local from global influence. *(p.45)*
- Context-sensitivity: structurally similar graphs can receive different constraint sets, so equivalent formal graph structures need not have the same epistemic semantics. *(p.45)*
- Different perspectives: agents can perceive arguments and relations differently and assign different beliefs in the same situation. *(p.45)*
- Imperfect agents: constraints can capture irrationality, cognitive bias, or non-standard semantics rather than forcing normative rationality. *(pp.45-46)*
- Incomplete graphs: arguments can be believed/disbelieved without visible graph justification; constraints can represent hidden knowledge, or absence of constraints can represent no known interaction. *(p.46)*

Future-work directions include coverage-based semantics, methods for obtaining constraints from crowdsourcing and machine learning, practical computational-persuasion applications, belief-update methods during dialogue, efficient representation and reasoning with probabilistic user models, uncertainty in belief distributions, learning distributions, decision rules for selecting arguments, constellation probabilities over possible graphs, SMT/constraint-logic implementations, and translations to propositional logic. *(p.46)*

### Proof Appendix
The appendix provides proof details for the main formal results. Lemma 3.8 proves that nonempty restricted value sets contain `0`, reasonable restricted value sets contain `0`, and a restricted value set is reasonable iff it contains `1`. The proof constructs zero by closure under subtraction and constructs a trivial distribution assigning probability `1` to the empty set and `0` elsewhere when `1 in Pi`. *(p.52)*

Proposition 3.9 characterizes when restricted value subsets and restricted combination sets are empty. It handles equality/inequality cases, maximal values, zero, the singleton `{0}`, operator sequences containing only addition or only subtraction, and `!=`. The proof analyzes each inequality and arithmetic-operator case to show emptiness occurs exactly under the listed conditions. *(pp.52-53)*

Proposition 3.12 proves that the epistemic formula associated with a probability distribution has exactly that distribution as its satisfying set. The proof relies on argument-complete terms encoding exactly one subset of arguments and the atom for that term requiring the value assigned by the distribution. *(pp.53-54)*

Proposition 3.14 proves that for a reasonable restricted value set, a restricted formula and its distribution disjunctive normal form have the same restricted satisfying distributions. If the satisfying set is empty, DDNF is contradiction; otherwise, the DDNF is the disjunction of the formulae associated with the satisfying restricted distributions. *(p.54)*

Proposition 4.3 proves unrestricted entailment implies restricted entailment by intersecting satisfaction sets with `Dist(G,Pi)`. *(p.54)*

Proposition 4.4 proves monotonicity in restricted value sets: if `Pi_1 subseteq Pi_2` and entailment holds under `Pi_2`, then it also holds under `Pi_1`. *(p.54)*

Proposition 4.6 proves the subject weakening/strengthening relationships between epistemic atoms by showing that replacing an argument term with a logically weaker or stronger term monotonically changes the possible probability expression and therefore the satisfaction-set inclusion direction. *(p.54)*

Proposition 9.1 derives useful proof rules from the base rules, including bounds, truth/falsehood probabilities, comparison via negated inequalities, equivalence of equality under mutual subject relations, contradiction for incompatible equalities, and inclusion-exclusion conversions for conjunction/disjunction. *(pp.55-56)*

Proposition 4.8 proves soundness of the restricted consequence relation. The proof checks basic rules, enumeration rules, subject rules, the probabilistic rule, and propositional rules, showing each preserves restricted satisfaction. *(pp.56-58)*

Proposition 9.2 gives intermediate completeness machinery: disjunctions of mutually inconsistent complete terms can be represented as disjunctions over tuples of values from the restricted set whose sums match the target value; and the disjunction over all complete terms is tautological. *(pp.58-60)*

Proposition 4.9 proves equivalence between a restricted formula and its DDNF at the proof-theory level. It first handles atoms of the form `p(alpha)=x` by converting terms to complete-term disjunctions and enumerating restricted distributions, then extends to arbitrary formulae by negation normal form, replacement of negated atoms, conversion to equality atoms or contradiction, and propositional DNF. *(pp.60-62)*

Proposition 4.10 proves completeness of the restricted proof system using DDNFs for the premise conjunction and the conclusion. If the DDNF satisfaction set of the premises is included in the conclusion's DDNF satisfaction set, propositional rule P1 plus Proposition 4.9 yields the consequence. *(pp.62-63)*

Proposition 4.11 proves the contradiction property: `Phi entails_Pi psi` iff `Phi union {not psi}` entails_Pi contradiction. The proof uses DDNF forms and shows that premise DDNF minus conclusion DDNF entails contradiction exactly when all premise-distribution clauses are contained in the conclusion. *(pp.63-64)*

Lemma 4.12 translates restricted epistemic consequence into propositional consequence by creating one propositional atom for each restricted distribution and mapping each epistemic formula to the disjunction of atoms for the distributions satisfying it, plus rules enforcing incompatibility of distinct distributions and coverage of all distributions. *(p.64)*

Lemma 4.13 translates classical propositional consequence into restricted epistemic consequence with `Pi={0,1}` by mapping propositional atoms to `p(alpha)=1`, negation to epistemic negation, and conjunction/disjunction homomorphically. *(pp.64-65)*

Proposition 4.14 follows from Lemmas 4.12 and 4.13: restricted epistemic language with restricted epistemic consequence is equivalent to classical propositional language with classical propositional consequence. *(p.65)*

Propositions 5.6, 5.7, and 5.10 prove the basic relationships among coverage and effectiveness notions. The proofs are mostly direct from definitions, with one-way failures witnessed by earlier examples. *(pp.65-66)*

### Additional Figures and Tables
- **Table 1 (p.30):** Relation analysis for Examples 28 and 31, showing how the same labelled relation can be strongly supporting, unspecified, strongly attacking, supporting, or subtle depending on `Z` and `F`.
- **Fig. 10 (p.34):** Labelled graph used for distribution-ordering examples.
- **Table 2 (p.35):** Ternary satisfying distributions for Example 34 and whether they maximize/minimize acceptance, rejection, information, undecidedness, and belief.
- **Fig. 11 (p.35):** Conflict-based argument graph used in Example 35.
- **Fig. 12 (p.35):** Small graph distinguishing undecided-minimizing from belief-maximizing.
- **Fig. 13 (p.36):** Dental-checkup persuasive-dialogue domain graph.
- **Table on Option B (p.38):** Initial, optimistic, and pessimistic predicted distributions for the route using argument `F` to increase belief in `B`.
- **Table on Option D (p.38):** Initial, optimistic, and pessimistic predicted distributions for the route using argument `I` to decrease belief in `D`.
- **Table on Option C (p.38):** Initial, optimistic, and pessimistic predicted distributions for the route using argument `G` to reduce belief in `C`.
- **Fig. 14 (p.40):** Example ADF and its complete, preferred, and grounded labellings.
- **Table 3 (p.42):** Ternary satisfying and information maximizing/minimizing distributions for the ADF translation in Example 39.
- **Fig. 15 (p.43):** Conflict-based argument graph for constrained-argumentation comparison.
- **Table 4 (p.43):** Ternary satisfying and information-maximizing distributions associated with constraints `C` and `C'` in Example 40.

### Key Citations For Follow-up
- Hunter, Polberg, and Potyka, "Updating Belief in Arguments in Epistemic Graphs" is the direct follow-up on belief updates. *(p.49, ref.41)*
- Polberg and Hunter, "Empirical evaluation of abstract argumentation: Supporting the need for bipolar and probabilistic approaches" motivates the need for bipolar/probabilistic modelling. *(p.50, ref.58)*
- Polberg, Hunter, and Thimm, "Belief in attacks in epistemic probabilistic argumentation" is an immediate precursor. *(p.50, ref.59)*
- Brewka et al., "Abstract dialectical frameworks revisited" is the core ADF comparison target. *(p.47, ref.14)*
- Coste-Marquis et al., "Constrained argumentation frameworks" is the constrained-AF comparison target. *(p.48, ref.28)*
- Dechter, Rossi et al., and Tsang are the constraint-programming references. *(pp.48, 50-51, refs.30,68,75)*

## Collection Cross-References

### Already in Collection
- [On the Acceptability of Arguments and its Fundamental Role in Nonmonotonic Reasoning, Logic Programming and n-Person Games](../Dung_1995_AcceptabilityArguments/notes.md) is the foundational abstract-argumentation semantics target that epistemic graphs generalize from two-valued extensions into belief distributions over arguments. *(ref.31)*
- [Probabilistic Reasoning with Abstract Argumentation Frameworks](../Hunter_2017_ProbabilisticReasoningAbstractArgumentation/notes.md) is the direct epistemic-probability predecessor: it constrains probability functions over sets of arguments for ordinary abstract argumentation, while this paper adds labelled positive/negative influences and arbitrary epistemic constraints. *(refs.36, 59-related context)*
- [Abstract Dialectical Frameworks](../Brewka_2010_AbstractDialecticalFrameworks/notes.md) and [Abstract Dialectical Frameworks Revisited](../Brewka_2013_AbstractDialecticalFrameworksRevisited/notes.md) are the core ADF comparison targets; this paper translates ADF acceptance conditions into epistemic constraints and then recovers complete, preferred, and grounded labellings by distribution selection. *(refs.17, 14; pp.40-42)*
- [Developing the Abstract Dialectical Framework](../Polberg_2017_DevelopingAbstractDialecticalFramework/notes.md) is Polberg's extended ADF background, including the three-valued ADF semantics that this paper compares against. *(ref.54; pp.40-42)*
- [On the Acceptability of Arguments in Bipolar Argumentation Frameworks](../Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/notes.md) is the bipolar argumentation ancestor for modelling support and attack in one graph; epistemic graphs retain positive and negative influence labels but interpret them through belief constraints rather than extension rules. *(refs.20-22; pp.1-2, 20-24)*
- [On the Merging of Dung's Argumentation Systems](../Coste-Marquis_2007_MergingDung'sArgumentationSystems/notes.md) is adjacent to the paper's discussion of multi-agent and partial/incomplete views of argument graphs, although the direct constrained-AF comparison target is Coste-Marquis et al. 2006 rather than this 2007 merging paper. *(refs.27-28; pp.42-43)*
- [Prudent Semantics for Argumentation Frameworks](../Coste-Marquis_2005_PrudentSemantics/notes.md) is cited as part of the abstract-argumentation semantics lineage; it handles negative influence conservatively by excluding co-accepted arguments connected by odd-length indirect attack paths. *(ref.27-adjacent semantics context)*

### Conceptual Links
- [A Polynomial-time Fragment of Epistemic Probabilistic Argumentation](../Potyka_2019_PolynomialTimeEpistemicProbabilistic/notes.md) is a strong downstream link: Potyka explicitly positions the 2019 fragment as a tractable linear-constraint subset of the richer epistemic-graph language developed here.
- [A Labelling Framework for Probabilistic Argumentation](../Riveret_2017_LabellingFrameworkProbabilisticArgumentation/notes.md) is a strong sibling approach to probabilistic argumentation through labellings rather than arbitrary epistemic constraints over graph relations.
- [Equational approach to argumentation networks](../Gabbay_2012_EquationalApproachArgumentationNetworks/notes.md) is a moderate numeric-semantics cousin: both attach values to arguments, but Gabbay uses equation systems over argument strength whereas this paper uses probability distributions and logical constraints over belief.
- [Probabilistic Argumentation Frameworks](../Li_2011_ProbabilisticArgumentationFrameworks/notes.md) is a moderate contrast case for constellation-style probability over argument frameworks, which this paper distinguishes from epistemic probability over argument acceptability.
- [Discontinuity-Free Decision Support with Quantitative Argumentation Debates](../Rago_2016_DiscontinuityFreeQuAD/notes.md) and [Adapting the DF-QuAD Algorithm to Bipolar Argumentation](../Rago_2016_AdaptingDFQuADBipolarArgumentation/notes.md) are moderate links for bipolar quantitative argumentation; they aggregate support and attack strengths, while epistemic graphs specify constraint satisfaction over belief distributions.
- [Prudent Semantics for Argumentation Frameworks](../Coste-Marquis_2005_PrudentSemantics/notes.md) is a moderate conceptual contrast: prudent semantics stays extension-based and treats odd-length negative paths as exclusion constraints, while epistemic graphs keep positive/negative influences as graded belief constraints over probability distributions.

### New Leads
- Hunter, Polberg, and Potyka, "Updating Belief in Arguments in Epistemic Graphs" (KR 2018). Direct follow-up on belief updates for epistemic graphs. *(ref.41)*
- Polberg and Hunter, "Empirical evaluation of abstract argumentation: Supporting the need for bipolar and probabilistic approaches" (IJAR 2018). Empirical motivation for bipolar/probabilistic modelling. *(ref.58)*
- Polberg, Hunter, and Thimm, "Belief in attacks in epistemic probabilistic argumentation" (NMR 2016). Immediate precursor on belief in attack relations. *(ref.59)*
- Coste-Marquis, Devred, and Marquis, "Constrained argumentation frameworks" (KR 2006). Direct constrained-AF comparison target. *(ref.28)*
