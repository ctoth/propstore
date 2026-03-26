---
title: "Causality: Models, Reasoning, and Inference"
authors: "Judea Pearl"
year: 2000
venue: "Cambridge University Press"
doi_url: "https://doi.org/10.1017/CBO9780511803161"
publisher: "Cambridge University Press"
note: "Second Edition, 2009. ISBN 978-0-521-89560-6"
---

# Causality: Models, Reasoning, and Inference

## One-Sentence Summary
Provides a complete mathematical framework for causal reasoning based on structural causal models (SCMs), the do-calculus for computing interventional distributions from observational data, and a formal semantics for counterfactuals grounded in functional equations.

## Problem Addressed
Before this work, causality lacked clear mathematical semantics; causal claims were either treated as metaphysical or reduced to statistical associations. The book transforms causality from a vague concept into a well-defined mathematical object with graph-based representations, computable identification criteria, and axiomatic foundations for counterfactual reasoning.

## Key Contributions
- **Structural Causal Models (SCMs)**: A triple M = (U, V, F) unifying causal graphs, structural equations, and counterfactual logic into one coherent framework *(p.204)*
- **do-calculus**: Three inference rules (Theorem 3.4.1) that are complete for identifying causal effects from observational data given a causal graph *(p.85-86)*
- **Back-door criterion**: A graphical condition for identifying causal effects by covariate adjustment (Definition 3.3.1) *(p.79)*
- **Front-door criterion**: Identification via mediating variables when back-door is blocked (Section 3.3.2) *(p.81)*
- **Structural counterfactuals**: Counterfactuals defined as submodel evaluations rather than closest-world semantics (Definition 7.1.5) *(p.204)*
- **Axiomatic characterization**: Three properties of counterfactuals -- composition, effectiveness, reversibility -- that hold in all causal models (Section 7.3.1) *(p.229)*
- **Actual causation**: Formal definition via sustenance and causal beams (Definitions 10.3.1, 10.3.3, 10.3.4) *(p.318-319)*
- **Causal hierarchy**: Three-level hierarchy -- association P(y|x), intervention P(y|do(x)), counterfactual P(y_x|x',y') -- each strictly more informative than the one below *(p.38)*

## Methodology

### The Structural Causal Model (SCM) Framework

**Definition 7.1.1 (Causal Model)**: A causal model is a triple M = (U, V, F) where: *(p.204)*
- U is a set of background (exogenous) variables determined by factors outside the model
- V = {V_1, ..., V_n} is a set of endogenous variables determined by variables in the model
- F = {f_1, ..., f_n} is a set of functions, one per endogenous variable, where each f_i maps from (the domains of) U_i union PA_i to V_i, with PA_i a subset of V \ {V_i}

The causal graph G associated with M has nodes V and directed edges from PA_i and U_i to each V_i.

### The do-Operator

The intervention do(X = x) is modeled by replacing the structural equation for X with the constant X = x, deleting all arrows into X in the causal graph, and computing the resulting distribution over the remaining variables. *(p.70-72)*

**Definition 3.2.1 (Causal Effect)**: Given a causal model M, the causal effect of X on Y, denoted P(y|do(x)) or P(y|hat{x}), is the probability of Y = y in the submodel M_x obtained by deleting from M all equations corresponding to variables in X and substituting X = x. *(p.70)*

## Key Equations

$$
P(y | \hat{x}) = \sum_z P(y | x, z) P(z)
$$
Where: y = outcome, x = treatment, z = back-door admissible covariates. This is the adjustment formula (back-door adjustment). *(p.79)*

$$
P(y | \hat{x}) = \sum_z P(z | x) \sum_{x'} P(y | x', z) P(x')
$$
Where: z = mediating variable satisfying front-door criterion. This is the front-door adjustment formula. *(p.81-82)*

### Three Rules of do-Calculus (Theorem 3.4.1)

Let G be the directed acyclic graph associated with a causal model, and P(v) the probability distribution induced by that model. For any disjoint subsets of variables X, Y, Z, and W: *(p.85-86)*

**Rule 1** (Insertion/deletion of observations):

$$
P(y | \hat{x}, z, w) = P(y | \hat{x}, w) \quad \text{if } (Y \perp\!\!\!\perp Z | X, W)_{G_{\overline{X}}}
$$

**Rule 2** (Action/observation exchange):

$$
P(y | \hat{x}, \hat{z}, w) = P(y | \hat{x}, z, w) \quad \text{if } (Y \perp\!\!\!\perp Z | X, W)_{G_{\overline{X}\underline{Z}}}
$$

**Rule 3** (Insertion/deletion of actions):

$$
P(y | \hat{x}, \hat{z}, w) = P(y | \hat{x}, w) \quad \text{if } (Y \perp\!\!\!\perp Z | X, W)_{G_{\overline{X}\overline{Z(S)}}}
$$

where Z(S) is the set of Z-nodes that are not ancestors of any W-node in G_X-bar.

These three rules are complete: any identifiable causal effect can be derived from observational distributions using these rules. *(p.86)*

### Counterfactual Axioms (Section 7.3.1)

**Property 1 (Composition)**: For any three sets of endogenous variables X, Y, W in a causal model: *(p.229)*

$$
W_x(u) = w \implies Y_{xw}(u) = Y_x(u)
$$

**Property 2 (Effectiveness)**: For all sets X and W: *(p.229)*

$$
X_{xw}(u) = x
$$

**Property 3 (Reversibility)**: For any two variables Y and W and any set X: *(p.229)*

$$
(Y_{xw}(u) = y) \wedge (W_{xy}(u) = w) \implies Y_x(u) = y
$$

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Background variables | U | - | - | - | 204 | Exogenous, determined outside model |
| Endogenous variables | V | - | - | - | 204 | Determined by structural equations |
| Structural functions | F | - | - | - | 204 | One per endogenous variable |
| Causal graph | G | - | - | - | 204 | DAG encoding causal structure |

## Implementation Details

### Structural Causal Model (SCM) *(p.204)*
- Data structure: Triple (U, V, F) where F is a set of deterministic functions
- Each f_i: Dom(U_i) x Dom(PA_i) -> Dom(V_i)
- Causal graph G derived from F: edges from PA_i and U_i to V_i
- Exogenous U typically not observed; induces probability P(u) over models

### Computing Interventional Distributions *(p.72)*
1. Start with structural equations: x_i = f_i(pa_i, u_i) for each variable
2. For intervention do(X = x): replace equation for X with constant X = x
3. Truncated factorization: P(v_1, ..., v_n | do(x)) = product of P(v_i | pa_i) for all V_i not in X, evaluated at X = x
4. This is equivalent to removing all incoming edges to X in the graph and computing P(Y) in the mutilated graph

### Identification Algorithm *(p.77-98)*
1. Check if causal effect is identifiable using graphical criteria
2. Try back-door criterion (Definition 3.3.1): find set Z that blocks all back-door paths from X to Y
3. If no back-door set exists, try front-door criterion (Section 3.3.2)
4. General case: apply do-calculus rules iteratively to reduce P(y|do(x)) to observational quantities
5. If no sequence of rules eliminates all do-operators, the effect is not identifiable from the given graph

### Counterfactual Computation (Twin Network Method) *(p.213)*
1. Build twin network: duplicate endogenous variables (actual world + hypothetical world)
2. Shared exogenous variables U connect both copies
3. In hypothetical copy, replace structural equation for intervened variable
4. Condition on evidence in actual-world copy
5. Compute probability of counterfactual outcome in hypothetical copy

### Actual Causation (Causal Beams) *(p.318)*
- Partition PA_k into sustaining set S_k and complement
- Causal beam: submodel where only sustaining paths are active
- Natural beam: "freeze" all variables outside sustaining set at actual values
- Actual cause: X = x is actual cause of Y = y if there exists a natural beam where but-for X, Y would not have occurred (Definition 10.3.3) *(p.319)*

## Figures of Interest
- **Fig 1.1 (p.12)**: A simple Bayesian network with DAG structure
- **Fig 1.3 (p.14)**: Bayesian network example with conditional dependencies
- **Fig 1.7 (p.22)**: Causal Bayesian network vs. standard Bayesian network
- **Fig 3.1 (p.67)**: Causal diagram for fumigation example
- **Fig 3.4 (p.79)**: Back-door criterion diagram
- **Fig 3.5 (p.81)**: Front-door criterion diagram with unobserved confounder
- **Fig 3.6 (p.87)**: Subgraphs used in do-calculus derivations

## Results Summary
- The do-calculus (3 rules) is provably complete for identification of causal effects in semi-Markovian models *(p.86)*
- Back-door and front-door criteria are special cases derivable from the do-calculus *(p.85-86)*
- Structural counterfactuals subsume Lewis's closest-world semantics while avoiding its problems with backtracking and similarity metrics *(p.238-240)*
- The three axioms (composition, effectiveness, reversibility) plus a graphical criterion completely characterize all counterfactual relationships derivable from structural models *(p.228-229)*

## Limitations
- The framework assumes the causal graph is known or can be inferred; graph discovery is treated separately (Chapter 2) *(p.41)*
- Semi-Markovian models (with latent variables) can make some effects non-identifiable; the framework identifies but cannot always compute effects *(p.77)*
- Actual causation definitions (Chapter 10) remain debated; Pearl acknowledges the sustenance account may not capture all intuitions *(p.309)*
- Nonparametric identification requires stronger graphical conditions than parametric (linear) models *(p.149)*

## Arguments Against Prior Work
- **Against purely statistical approaches**: Statistical associations (correlations, regressions) cannot distinguish causal from spurious relationships; the do-operator captures what statistics cannot *(p.38-39)*
- **Against Lewis's closest-world counterfactuals**: Structural counterfactuals avoid the problematic similarity metric and backtracking issues that plague possible-world semantics *(p.238-240)*
- **Against SEM without causal interpretation**: Traditional structural equation modeling in social science obscured causal meaning by focusing on covariance fitting rather than interventional semantics *(p.133-135)*
- **Against the "no causation without manipulation" doctrine**: Causation is a property of the model, not limited to manipulable variables; the do-operator applies to any variable in the structural model *(p.361)*

## Design Rationale
- **Why graphs?** Directed acyclic graphs encode causal assumptions transparently and support algorithmic identification of causal effects via d-separation and path analysis *(p.12-16)*
- **Why structural equations over potential outcomes?** Structural equations encode the full causal mechanism, enabling both interventional and counterfactual reasoning from a single model; potential outcomes are derivable from SCMs but not vice versa *(p.202-204)*
- **Why deterministic functions with stochastic U?** Separating mechanism (f_i) from uncertainty (U_i) allows precise counterfactual evaluation: change the mechanism while holding background factors fixed *(p.27, 204)*
- **Why three levels of causal hierarchy?** Association, intervention, and counterfactual represent strictly increasing information requirements; conflating levels leads to Simpson's paradox and other fallacies *(p.38, 173)*

## Testable Properties
- **Markov condition**: Every variable is independent of its non-descendants given its parents in the causal graph (Theorem 1.4.1) *(p.30)*
- **d-separation implies conditional independence**: If X and Y are d-separated by Z in G, then X is conditionally independent of Y given Z in every distribution compatible with G *(p.16-18)*
- **Truncated factorization**: P(v|do(x)) = product of P(v_i|pa_i) for V_i not in X, only if causal Markov condition holds *(p.72)*
- **Composition axiom**: Setting W to its natural value under do(X=x) should not change Y; testable via nested interventions *(p.229)*
- **Consistency (Corollary 7.3.2)**: If X(u) = x, then Y_x(u) = Y(u); the counterfactual under the actual treatment equals the actual outcome *(p.229)*

## Relevance to Project
Pearl's SCM framework provides the formal foundation for causal reasoning that complements propstore's argumentation layer. Key connections:
1. **Interventions as arguments**: The do-operator formalizes the distinction between observing and intervening -- directly relevant to evaluating the effect of policy changes or hypothetical scenarios in propstore's world queries
2. **Counterfactual reasoning**: Structural counterfactuals enable precise hypothetical reasoning ("what if this claim were false?") aligned with propstore's hypothetical reasoning capabilities
3. **Graph-based identification**: The back-door/front-door criteria and do-calculus provide algorithmic methods for determining which causal effects can be computed from available data
4. **Causal hierarchy**: The three-level hierarchy (association/intervention/counterfactual) maps to different types of queries in propstore's render layer

## Open Questions
- [ ] How does the do-calculus interact with argumentation frameworks (Dung AFs)? Can defeats be modeled as interventions?
- [ ] Can SCMs formalize the notion of "supersession" in propstore's claim management?
- [ ] How do causal beams relate to undercutting defeat in Pollock's framework?
- [ ] Can the identification criteria inform which propstore world queries are answerable?

## Related Work Worth Reading
- Spirtes, Glymour, and Scheines (1993) "Causation, Prediction, and Search" -- alternative framework for causal discovery from data
- Halpern and Pearl (2005) "Causes and Explanations" -- updated definition of actual causation
- Tian and Pearl (2002) -- completeness proof for the do-calculus in semi-Markovian models
- Bareinboim and Pearl (2016) -- causal inference and the data-fusion problem (transportability)
- Robins (1986) -- potential outcomes framework that Pearl's work synthesizes with
