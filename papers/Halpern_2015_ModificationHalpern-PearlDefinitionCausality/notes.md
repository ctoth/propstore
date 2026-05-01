---
title: "A Modification of the Halpern-Pearl Definition of Causality"
authors: "Joseph Y. Halpern"
year: 2015
venue: "arXiv preprint"
doi_url: ""
pages: 12
---

# A Modification of the Halpern-Pearl Definition of Causality

## One-Sentence Summary
Halpern replaces the original and updated HP actual-causality AC2 contingency condition with a stricter modified condition that only lets non-causal variables be held fixed at their actual values, yielding simpler definitions, better behavior on standard counterexamples, and lower decision complexity. *(p.1-p.10)*

## Problem Addressed
The but-for test fails in preemption and overdetermination cases, while the original HP and updated HP definitions sometimes classify intuitively irrelevant actions as causes because they allow contingencies where non-causal variables are set to non-actual values. *(p.1-p.2)* The paper asks whether HP-style structural-equation actual causality can be simplified while blocking the Hopkins-Pearl and later counterexamples without relying on normality/defaults or extra variables in every case. *(p.1-p.2)*

## Key Contributions
- Introduces the modified HP definition, where AC2(a) requires a witness set `W` to be fixed at its actual value `w`; there is no separate AC2(b) sufficiency condition because the modified necessity condition plus AC1 implies it. *(p.2-p.3)*
- Proves stringency: if `X = x` is part of a cause according to the modified HP definition, then `X = x` is a cause under both original and updated HP definitions. *(p.3, p.10)*
- Shows the modified definition gives the intended answers for forest fires, rock throwing, Hopkins-Pearl prisoner death, bogus prevention, non-existent threat, lamp-switch, voting, train-switch, and pollutant examples. *(p.3-p.8)*
- Compares the modified definition with Pearl causal beam, Hall H-account, and Hitchcock causal-path accounts, arguing that holding off-path variables at actual values captures the useful intuition without the excessive path restrictions. *(p.8-p.9)*
- Lowers the general decision complexity of causality from `D_2^P` for updated HP and `Sigma_2^P` for original HP to `D_1^P`; for singleton causes the decision problem is NP-complete. *(p.9)*

## Study Design

## Methodology
The paper is a formal-theory paper. It reviews recursive structural causal models and the HP language, isolates the AC2 clause as the source of differences among definitions, defines a modified AC2 condition, then evaluates the modified definition on standard examples and complexity classes. *(p.1-p.3)* It uses model-by-model counterfactual analysis: variables, domains, structural equations, actual contexts, proposed causes, and allowed witness contingencies are made explicit for each example. *(p.3-p.8)* The complexity section gives reductions for the modified decision problem and for the singleton-cause special case. *(p.9)*

## Core Formal Setup

### Causal models and signatures
A causal model is a pair `M = (S, F)`, where `S` is a signature and `F` is a set of modifiable structural equations. *(p.2)* A signature is `S = (U, V, R)`, where `U` is the set of exogenous variables, `V` is the set of endogenous variables, and `R(Y)` gives each variable's nonempty range of possible values. *(p.2)* The paper assumes finite `V` and finite ranges for endogenous variables. *(p.2)*

For each endogenous variable `X`, `F` associates a function:

$$
F_X : \left(\times_{U \in U} R(U)\right) \times \left(\times_{Y \in V-\{X\}} R(Y)\right) \to R(X)
$$

`F_X` determines `X` from all exogenous variables and all endogenous variables except `X`. The paper's example `F_X(u, y, z) = u + y` shows that an argument may syntactically occur without functionally mattering. *(p.2)*

### Interventions and acyclicity
Setting `X` to `x` in `M = (S, F)` produces `M_{X <- x}`, identical to `M` except that the equation for `X` is replaced by `X = x`. *(p.2)* The paper restricts attention to recursive/acyclic models, where there is a total order `<` on endogenous variables such that `X < Y` implies `X` is independent of `Y`. Given a context `u`, an acyclic model has a unique solution. *(p.2)*

### Causal formulas
A primitive event is `X = x` for `X in V` and `x in R(X)`. A causal formula has the form:

$$
[Y_1 \leftarrow y_1, \ldots, Y_k \leftarrow y_k]\varphi
$$

where `varphi` is a Boolean combination of primitive events, the `Y_i` are distinct endogenous variables, and `y_i in R(Y_i)`. The empty intervention is abbreviated `varphi`; `[Y <- y]varphi` says that `varphi` would hold if the variables in `Y` were set to `y`. *(p.2-p.3)*

Truth is written `(M,u) |= psi`. For primitive events, `(M,u) |= X = x` iff `X` has value `x` in the unique solution under context `u`. For interventions, `(M,u) |= [Y <- y]varphi` iff `(M_{Y <- y},u) |= varphi`. *(p.3)*

## Key Equations / Statistical Models

### Original HP AC2(a)

$$
(M,u) \models [X \leftarrow x', W \leftarrow w]\neg \varphi
$$

There is a partition of endogenous variables into disjoint `Z` and `W`, with `X subseteq Z`, and settings `x'` and `w` such that changing `X` to `x'` while setting `W` to `w` makes `varphi` false. This is the necessity/but-for-under-contingency clause. *(p.3)*

### Original HP AC2(b)

$$
(M,u) \models [X \leftarrow x, W \leftarrow w, Z' \leftarrow z]\varphi
$$

If `z` is the actual value of `Z`, then the original sufficiency clause requires `varphi` to remain true for all subsets `Z'` of `Z` when `X` is restored to `x`, `W` is fixed at `w`, and `Z'` is fixed at its actual value. *(p.3)*

### Updated HP AC2(b^u)

$$
(M,u) \models [X \leftarrow x, W' \leftarrow w, Z' \leftarrow z]\varphi
$$

The updated HP definition strengthens sufficiency by quantifying over all subsets `W'` of `W` and all subsets `Z'` of `Z`; `varphi` must remain true if any subset of `W` is set to `w` and any subset of `Z` is set to actual values. *(p.3)*

### Modified HP AC2(a^m)

$$
(M,u) \models [X \leftarrow x', W \leftarrow w]\neg \varphi
$$

Here `W` is a set of variables in `V - X`, `x'` is a setting of `X`, and crucially `(M,u) |= W = w`; `w` must be the actual value of the variables in `W`. No non-actual contingency for `W` is permitted. *(p.4)* Because `w` is actual, AC2(b) and AC2(b^u) follow immediately from AC1 and modified AC2(a), so the modified definition has no separate sufficiency clause. *(p.4)*

### Forest-fire equations

$$
FF = \min(L, MD)
$$

Conjunctive forest fire: both lightning `L = 1` and match dropped `MD = 1` are needed for fire `FF = 1`. All HP variants identify both as causes because each is a but-for cause. *(p.4)*

$$
FF = \max(L, MD)
$$

Disjunctive forest fire: either lightning or match suffices. Original and updated HP call both `L = 1` and `MD = 1` causes, but the modified definition calls each a part of the joint cause rather than an individual cause, because both values must change to change `FF`. *(p.4-p.5)*

### Rock-throwing equations

$$
BS = ST \lor BT
$$

The naive Suzy/Billy model makes bottle shattering depend on either throw and is isomorphic to disjunctive forest fire, so it cannot distinguish Suzy from Billy. *(p.5)*

$$
BS = SH \lor BH
$$

$$
SH = ST
$$

$$
BH = BT \land \neg SH
$$

The richer model encodes Suzy's rock hitting first. In the actual context `ST = SH = 1`, `BT = 1`, `BH = 0`, and `BS = 1`; all definitions say Suzy's throw is a cause and Billy's throw is not. The modified definition proves Billy is not a cause more directly because the only variables allowed to be held fixed already have actual values. *(p.5)*

### Complexity language

$$
D_k^P = \{ L : \exists L_1,L_2 \; (L_1 \in \Sigma_k^P,\ L_2 \in \Pi_k^P,\ L = L_1 \cap L_2) \}
$$

`D_1^P` is the class `D^P`, containing languages expressible as the intersection of an NP language and a co-NP language. *(p.9)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Endogenous variable domain size assumption | `R(Y)` | values | finite | finite for every endogenous `Y` | 2 | Simplifying assumption for model definitions. |
| Modified causality decision complexity | `D_1^P` | complexity class | `D_1^P`-complete | intersection of NP and co-NP | 9 | General modified HP cause decision problem. |
| Singleton-cause decision complexity | NP | complexity class | NP-complete | - | 9 | Applies when proposed causes are single conjuncts and AC3 holds vacuously. |
| Updated HP causality complexity | `D_2^P` | complexity class | `D_2^P`-complete | - | 9 | Cited from Aleksandrowicz et al. 2014. |
| Original HP causality complexity | `Sigma_2^P` | complexity class | `Sigma_2^P`-complete | - | 9 | Cited from Eiter and Lukasiewicz 2002 and Hopkins 2001. |
| Pollution threshold example | `k` | kg | 120, 80, 50 | threshold for fish death | 8 | Used to analyze responsibility/blame and joint causes. |
| Company A pollutant amount | `A` | kg | 100 | example fixed amount | 8 | Company A dumping amount in legal-responsibility example. |
| Company B pollutant amount | `B` | kg | 60 | example fixed amount | 8 | Company B dumping amount in legal-responsibility example. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| General modified HP decision complexity | completeness class | `D_1^P`-complete | - | - | finite recursive structural models | 9 |
| Singleton modified HP decision complexity | completeness class | NP-complete | - | - | causes restricted to single conjuncts | 9 |

## Methods & Implementation Details
- Treat `W` in modified AC2 as a set of variables outside `X` whose values must be their actual values in `(M,u)`; do not permit counterfactual, non-actual settings for `W`. *(p.4)*
- A witness to causality is the tuple `(W, w, x')` in AC2; if `W` is empty, the witness is `(empty, empty, x')`. *(p.4)*
- Each conjunct in `X = x` is called part of a cause in context `(M,u)`, although ordinary-language causes often correspond to parts of causes under the modified definition. *(p.4)*
- For the modified definition, AC3 should be interpreted as no subset of `X` satisfying AC1 and modified AC2(a); the paper does not write separate AC3 versions each time. *(p.4)*
- If a but-for cause has a singleton cause, then all three HP variants agree that it is a cause. *(p.4)*
- Modified HP is more stringent than original or updated HP: it cannot introduce causes that those definitions reject, though it can turn an individual original/updated cause into only part of a modified cause. *(p.4)*
- Adding variables that model mechanism can convert a part of a cause into a cause under the modified definition; model richness matters. *(p.6-p.7)*
- Normality, defaults, responsibility, and blame can be layered on top of modified HP when the base modified definition does not settle an intuitively legal or moral question. *(p.7-p.8, p.10)*
- For general modified HP complexity, split the language into `L_AC2` and `L_AC3`, show `L = L_AC2 intersection L_AC3`, with `L_AC2` NP-complete and `L_AC3` co-NP-complete. *(p.9)*

## Figures of Interest
No figures are present. The paper's examples are textual structural-equation models. *(p.1-p.12)*

## Results Summary
The modified definition handles the Hopkins-Pearl prisoner example by rejecting `A = 1` as a cause when `B` did not shoot, because fixing only `A` to actual value while leaving `B` at its actual value makes death false; no non-actual `B = 1` contingency is permitted. *(p.5-p.6)* It handles bogus prevention and non-existent threat by rejecting prevention events as causes when the relevant threat was not actual, unless normality considerations independently justify a different analysis. *(p.6-p.8)* It blocks voting and train-switch anomalies where original/updated HP create causes by considering non-actual off-path contingencies. *(p.7-p.8)* It does not prove final correctness, but it gives reasonable answers across standard counterexamples and materially lowers complexity. *(p.10)*

## Limitations
The paper explicitly does not prove that the modified definition is the right definition of actual causality; it argues usefulness by examples and formal properties. *(p.4, p.10)* Some intuitions remain model-dependent: adding mechanism variables can change whether something is a cause or only part of a cause. *(p.6-p.7)* Responsibility and blame, especially group/legal responsibility in the pollution example, may require extensions beyond actual causality itself. *(p.8)* Normality/defaults can still be needed for examples such as bogus prevention variants. *(p.7-p.8)* The formal discussion is limited to recursive/acyclic models. *(p.2)*

## Arguments Against Prior Work
- The original HP definition's AC2 allowed contingencies with non-actual variable settings, which can make Billy's throw or other intuitively irrelevant events appear causal. *(p.1-p.5)*
- The updated HP definition strengthens sufficiency but still allows some problematic contingencies; in the Hopkins-Pearl example it avoids one problem but still retains complexity and can produce other unintuitive results. *(p.3-p.5)*
- Normality/default additions can address many examples but do not always seem satisfactory and are orthogonal to the proposed syntactic simplification. *(p.1, p.7-p.8)*
- Pearl's causal beam and Hall's H-account are too strong because they require off-path variables to have no effect along the causal path, excluding cases that should count as causes or parts of causes. *(p.8-p.9)*
- Hitchcock's path-reduction account has similar excessive path restrictions; in a four-variable model with paths `A,B,D` and `A,C,D`, `A = 1` is not a but-for cause in either path-reduced model even though all HP variants count it as a cause. *(p.9)*

## Design Rationale
- The modified definition captures the intuition that, when evaluating whether `X = x` caused `varphi`, the only counterfactual changes should be to the candidate cause and possibly to actual background variables held fixed; arbitrary non-actual off-path values can manufacture causal dependence. *(p.2-p.4)*
- Removing independent AC2(b) makes the definition conceptually simpler: sufficiency follows from AC1 plus the restriction that `W = w` is actual. *(p.4)*
- The definition intentionally becomes more stringent; it may classify a conjunct as part of a cause rather than as a full cause, matching examples where multiple actual factors jointly explain an effect. *(p.4-p.5)*
- Richer models are preferred when intuitions distinguish mechanisms that a coarse model collapses; the modified definition is not intended to replace careful causal modeling. *(p.6-p.7)*

## Testable Properties
- In any implementation of modified HP, `W` in AC2(a^m) must satisfy `(M,u) |= W = w`; any non-actual assignment for `W` is invalid. *(p.4)*
- A proposed cause must satisfy AC1: both `X = x` and `varphi` are true in the actual context. *(p.3)*
- A proposed cause must satisfy AC3 minimality with respect to AC1 and modified AC2(a). *(p.3-p.4)*
- If `X = x` is a but-for cause and AC1 holds, all three HP variants classify it as a cause. *(p.4)*
- If `X = x` is part of a cause under modified HP, it must be a cause under original HP and updated HP. *(p.4, p.10)*
- Under the rich rock-throwing model, `ST = 1` is a cause of `BS = 1`, but `BT = 1` is not. *(p.5)*
- Under the disjunctive forest-fire model without extra mechanism variables, `L = 1` and `MD = 1` are parts of a joint cause under modified HP, not individual causes. *(p.4-p.5)*
- The general modified HP causality decision problem is `D_1^P`-complete. *(p.9)*
- With singleton causes, the modified HP causality decision problem is NP-complete. *(p.9)*

## Relevance to Project
This paper is directly relevant to propstore's causal and counterfactual semantics because it provides a stricter intervention-witness discipline for actual causality over structural equations. The central implementation lesson is to type witnesses so they cannot encode arbitrary non-actual off-path assignments: modified HP witnesses should carry the candidate intervention `X <- x'` plus a set of variables explicitly checked against the actual solution. It also gives test fixtures for causality algorithms and a complexity target for solver-backed cause queries.

## Open Questions
- [ ] Should propstore represent "part of a cause" distinctly from "cause" so modified HP's conjunct-level behavior is not flattened? *(p.4-p.5)*
- [ ] Should normality/defaults and responsibility/blame be separate layers over actual causality rather than fields in the core causality witness? *(p.7-p.8)*
- [ ] How should model richness be exposed to users when adding mechanism variables can change modified-HP cause status? *(p.6-p.7)*
- [ ] Should implementation restrict first to recursive finite models, matching this paper's scope, before supporting cyclic models? *(p.2)*

## Related Work Worth Reading
- Halpern and Pearl 2001/2005 for original and updated structural-model definitions of actual cause. *(p.1-p.3, p.11)*
- Hopkins and Pearl 2003 for examples motivating the updated HP definition. *(p.1, p.5-p.6, p.12)*
- Aleksandrowicz et al. 2014, Eiter and Lukasiewicz 2002, and Hopkins 2001 for complexity results on HP causality. *(p.2, p.9, p.11-p.12)*
- Hitchcock 2001, Hall 2007, Pearl 1998/2000 for path/beam-style alternatives. *(p.8-p.9, p.11-p.12)*
- Halpern and Hitchcock 2015, Chockler and Halpern 2004, Zultan et al. 2012 for normality, responsibility, and blame extensions. *(p.7-p.8, p.11-p.12)*
