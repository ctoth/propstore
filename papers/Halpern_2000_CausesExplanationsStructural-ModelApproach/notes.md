---
title: "Causes and Explanations: A Structural-Model Approach. Part I: Causes"
authors: "Joseph Y. Halpern, Judea Pearl"
year: 2005
venue: "British Journal for the Philosophy of Science 56(4), 843-887"
doi_url: "https://doi.org/10.1093/bjps/axi147"
---

# Causes and Explanations: A Structural-Model Approach. Part I: Causes

## One-Sentence Summary
Provides a formal definition of actual causation using structural equations and counterfactual reasoning, handling overdetermination, preemption, and other difficult cases that defeat simpler counterfactual accounts.

## Problem Addressed
The traditional counterfactual definition of causation (Hume/Lewis: "A causes B iff B would not have occurred without A") fails on many important cases: overdetermination (two simultaneous sufficient causes), preemption (a backup cause would have produced the same effect), and problems of transitivity. This paper provides a rigorous formal alternative using structural equation models. *(p.1-2)*

## Key Contributions
- A formal definition of actual causation (Definition 3.1, refined in Section 5) using structural causal models *(p.9)*
- Demonstration that the definition correctly handles overdetermination, preemption (early and late), switches, omission, and other notoriously difficult cases *(p.14-30)*
- Extension to handle "allowable settings" to rule out inappropriate counterfactual contingencies *(p.23-24)*
- Proof that the active causal process in recursive models is a minimal set on a path in the causal graph *(p.33)*
- Extension to nonrecursive (cyclic) causal models *(p.36-37)*
- Extension to infinitely many variables *(p.35-36)*

## Methodology
The approach uses structural equation models (SEMs) as the formal framework. A causal model specifies exogenous variables (background context), endogenous variables, and structural equations defining each endogenous variable as a function of others. Counterfactuals are evaluated by interventions: setting variables to specific values and computing the consequences through the structural equations. Causation is then defined as a three-part condition requiring (1) the cause and effect are both true, (2) under some contingency (partition of variables into frozen and free), changing the cause changes the effect while the effect remains robust to other changes, and (3) minimality. *(p.3-9)*

## Key Equations

### Causal Model Structure

A causal model $M$ is a pair $(S, F)$ where: *(p.3-4)*

- $S = (U, V, R)$ is a **signature**
  - $U$ = set of exogenous variables
  - $V$ = set of endogenous variables
  - $R$ = function assigning range $R(X)$ to each variable $X \in U \cup V$
- $F = \{F_X : X \in V\}$ = set of structural equations, one per endogenous variable

$$
F_X : (\times_{U \in \mathcal{U}} R(U)) \times (\times_{Y \in \mathcal{V} \setminus \{X\}} R(Y)) \to R(X)
$$

Where: $F_X$ determines the value of $X$ given the values of all other variables. *(p.4)*

### Counterfactual Evaluation

$$
(M, \vec{u}) \models [\vec{Y} \leftarrow \vec{y}]\varphi
$$

Where: $(M, \vec{u})$ denotes model $M$ with exogenous context $\vec{u}$; $[\vec{Y} \leftarrow \vec{y}]$ is an intervention setting variables $\vec{Y}$ to values $\vec{y}$; $\varphi$ is evaluated in the resulting submodel $M_{\vec{Y} \leftarrow \vec{y}}$. *(p.4)*

### Definition 3.1: Actual Cause (Preliminary)

$\vec{X} = \vec{x}$ is an **actual cause** of $\varphi$ in $(M, \vec{u})$ if: *(p.9)*

**AC1.** $(M, \vec{u}) \models (\vec{X} = \vec{x})$ and $(M, \vec{u}) \models \varphi$. (Both cause and effect hold in the actual world.)

**AC2.** There exists a partition $(\vec{Z}, \vec{W})$ of $\mathcal{V}$ with $\vec{X} \subseteq \vec{Z}$ and some setting $(\vec{x}', \vec{w})$ of the variables in $(\vec{X}, \vec{W})$ such that if $(M, \vec{u}) \models \vec{Z} = \vec{z}^*$, then both:
- (a) $(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}', \vec{W} \leftarrow \vec{w}] \neg \varphi$
- (b) $(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}, \vec{W} \leftarrow \vec{w}, \vec{Z}' \leftarrow \vec{z}^*] \varphi$ for all subsets $\vec{Z}'$ of $\vec{Z}$ and all $\vec{z}^*$

**AC3.** $\vec{X}$ is minimal; no subset of $\vec{X}$ satisfies AC1 and AC2.

### AC2(b) Refined Version

$$
(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}, \vec{W} \leftarrow \vec{w}, \vec{Z}' \leftarrow \vec{z}^*] \varphi
$$

For all subsets $\vec{Z}'$ of $\vec{Z}$ and all values $\vec{z}^*$ of $\vec{Z}'$. *(p.9)*

This ensures the effect $\varphi$ remains robust: changing other variables in $\vec{Z}$ does not affect the effect as long as the cause $\vec{X}$ is held at its actual value. *(p.10)*

### Refined Definition with Allowable Settings (Section 5)

For extended causal models with allowable settings $\mathcal{A}$: *(p.24)*

**AC2(a_m).** $(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}', \vec{W} \leftarrow \vec{w}] \neg \varphi$ where $(\vec{x}', \vec{w})$ is an allowable setting.

Restrict $\vec{W}$ to only take values within the set of allowable settings, preventing "unreasonable" counterfactual contingencies. *(p.23-24)*

### Strong Causality (AC3(s))

$$
(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}, \vec{W} \leftarrow \vec{w}'] \varphi \text{ for all settings } \vec{w}' \text{ of } \vec{W}
$$

Where: strong causality requires the effect to hold under ALL settings of the witness variables, not just the one chosen. *(p.11)*

### Definition A.8: Nonrecursive Models

$\vec{X} = \vec{x}$ is an actual cause of $\varphi$ in $(M, \vec{u})$ if: *(p.37)*

AC1 unchanged. AC2 modified:
- (a) $(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}', \vec{W} \leftarrow \vec{w}] \neg \varphi$
- (b) $(M, \vec{u}) \models [\vec{X} \leftarrow \vec{x}, \vec{W} \leftarrow \vec{w}, \vec{Z}' \leftarrow \vec{z}^*] \varphi$ for all subsets $\vec{Z}'$ of $\vec{Z}$

In (a) only the value of $\varphi$ changes (not the equations); in (b) require $\varphi$ stay true in all solutions to the modified equations. *(p.37)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Exogenous variables | $\mathcal{U}$ | - | - | finite set | 3 | Background context, set externally |
| Endogenous variables | $\mathcal{V}$ | - | - | finite set | 3 | Determined by structural equations |
| Variable range | $R(X)$ | - | - | finite | 4 | Range of possible values for variable X |
| Witness partition (frozen) | $\vec{Z}$ | - | - | subset of $\mathcal{V}$ | 9 | Variables held at actual values |
| Witness partition (free) | $\vec{W}$ | - | - | subset of $\mathcal{V}$ | 9 | Variables allowed to vary |
| Allowable settings | $\mathcal{A}$ | - | - | subset of settings | 24 | Restrict contingencies to "reasonable" ones |

## Implementation Details
- A causal model is a DAG (for recursive models) where nodes are endogenous variables and edges represent functional dependencies *(p.6)*
- Counterfactual evaluation: substitute intervention values into structural equations and solve (unique solution for recursive models) *(p.4)*
- AC2 requires searching over partitions $(\vec{Z}, \vec{W})$ of variables and over settings $(\vec{x}', \vec{w})$ - exponential search space *(p.9)*
- AC3 (minimality) requires checking all subsets of the proposed cause *(p.9)*
- For the "active causal process" in recursive models, the variables in $\vec{Z}$ satisfying AC2 lie on a path from $\vec{X}$ to a variable in the causal graph (Proposition A.1) *(p.33)*
- Nonrecursive models may have multiple solutions to structural equations; the definition requires checking all solutions *(p.36-37)*
- The definition is model-relative: the same scenario modeled differently can yield different causal judgments, reflecting the importance of choosing the right level of abstraction *(p.26-27)*

## Figures of Interest
- **Fig 1 (p.6):** Simple causal network for forest fire example (Lightning L, Match ML, Fire F)
- **Fig 2 (p.12):** Causal network for disjunctive/conjunctive forest fire scenarios (M1, M2 models)
- **Fig 3 (p.17):** Rock-throwing example causal network (ST, BT, BS, SH)
- **Fig 4 (p.18):** Time-invariant rock throwing (with H_i, BS_i variables at each timestep)
- **Fig 5 (p.20):** Billy's medical condition (doctor treatment example)
- **Fig 6-7 (p.23):** Blowing up the target (with SPS variable for Suzy's plan)
- **Fig 8 (p.26):** Flipping the switch (railroad tracks example)
- **Fig 9 (p.28):** Merlin and Morgana (enchantment/preemption)
- **Fig 10-11 (p.29):** Sergeant and major (trumping preemption)
- **Fig 12 (p.34):** Example showing need for AC2(b) - vote counting

## Results Summary
The definition correctly handles: *(p.14-30)*
- **Overdetermination**: Both arsonists are causes of fire in disjunctive scenario *(p.15)*
- **Early preemption**: Suzy's throw is the cause, Billy's is not (rock-throwing) *(p.16-17)*
- **Late preemption**: Handled via structural contingencies *(p.17-18)*
- **Omission/prevention**: Doctor's failure to treat as cause *(p.19-20)*
- **Double prevention**: Suzy's mission in bombing example *(p.22-23)*
- **Switches**: Railroad switch example, shows model choice matters *(p.26)*
- **Trumping preemption**: Merlin/Morgana and sergeant/major examples *(p.27-29)*
- **Bogus prevention**: Handled correctly via allowable settings *(p.30)*

## Limitations
- The definition is model-relative: different (reasonable) models of the same scenario can give different causal verdicts *(p.26-27, 31-32)*
- No general theory for how to choose the "right" model (set of variables, level of granularity) *(p.32)*
- Strong causality (requiring effect under ALL contingencies) is too restrictive for most cases *(p.11)*
- Allowable settings are needed to handle some cases but require additional modeling decisions *(p.23-24)*
- The paper does not treat probabilistic causation *(p.2)*
- Nonrecursive (cyclic) models receive limited treatment *(p.36-37)*

## Arguments Against Prior Work
- **Lewis's counterfactual dependence**: Fails on overdetermination (both causes are genuine causes but neither is counterfactually necessary) *(p.1-2)*
- **Simple but-for test**: Cannot handle preemption, where a backup cause would have produced the same effect *(p.1)*
- **Lewis's influence account**: Adding "would the effect have been slightly different" doesn't solve core problems *(p.2)*
- **Transitivity of causation**: Hall (2004) shows tension between transitivity and the desire to deny causation in some chains; HP definition handles this by not requiring transitivity *(p.21)*
- **Pearl's original definition (1998/2000)**: Too permissive; the refined AC2(b) condition is needed *(p.10, 35)*

## Design Rationale
- **Structural equations over logic**: Structural equations provide a natural language for representing causal mechanisms and evaluating counterfactuals, unlike purely logical approaches *(p.8, 31)*
- **Partition into Z and W**: The partition allows "freezing" some variables at actual values while varying others, capturing the intuition that a cause makes a difference under some contingency *(p.9-10)*
- **AC2(b) robustness condition**: Prevents spurious causes by requiring the effect to be robust when other variables in Z change, as long as the cause is held fixed *(p.9-10)*
- **Minimality (AC3)**: Prevents listing irrelevant conjuncts as part of a cause *(p.9)*
- **Model-relative causation**: Embraced rather than fought; reflects real practice where the choice of variables determines what counts as a cause *(p.31-32)*
- **Allowable settings vs. unrestricted contingencies**: Some cases require restricting which variable settings count as legitimate counterfactual scenarios *(p.23-24)*

## Testable Properties
- For any recursive causal model, the active causal process forms a minimal set on a path in the causal graph from X to the effect variable (Proposition A.1) *(p.33)*
- AC1+AC2+AC3 together imply that the cause is a but-for cause under some contingency (but not necessarily in the actual situation) *(p.9)*
- In the disjunctive scenario with two independent causes, each individual cause satisfies the definition *(p.15)*
- In early preemption (Suzy's rock hits first), Suzy's throw satisfies the definition but Billy's does not *(p.17)*
- Strong causality implies actual causality, but not vice versa *(p.11)*
- The definition reduces to simple counterfactual dependence when the causal model has only two variables *(p.10)*

## Relevance to Project
This paper is foundational for any system that needs to reason about actual causation in structured models. For propstore:
- The structural equation framework provides a formal language for representing causal relationships between claims, which could ground causal argumentation
- The counterfactual evaluation mechanism parallels the ATMS's ability to reason about alternative assumption sets
- The model-relative nature of causation aligns with propstore's non-commitment discipline: different models (perspectives) can yield different causal judgments, and all should be preserved
- The connection to explanation (Part II, not included) would be relevant for the argumentation layer's ability to generate explanations for why certain claims defeat others

## Open Questions
- [ ] How does Part II (Explanations) extend the framework? (Published separately)
- [ ] Can the structural equation approach be integrated with ASPIC+ argumentation?
- [ ] How does the complexity of checking AC2 scale with the number of variables?
- [ ] What is the relationship between HP causation and Dung-style argumentation?
- [ ] Can allowable settings be derived automatically from domain knowledge?

## Related Work Worth Reading
- Halpern and Pearl (2005b) "Causes and Explanations: A Structural-Model Approach. Part II: Explanations" - companion paper on explanation
- Halpern (2000) "Axiomatizing causal reasoning" - axiomatization of the framework
- Pearl (2000) "Causality: Models, Reasoning, and Inference" - comprehensive textbook treatment
- Hitchcock (2001) "The intransitivity of causation revealed in equations and graphs" - related work on causal models
- Chockler and Halpern (2004) "Responsibility and Blame: A structural-model approach" - extends HP causation to degrees of responsibility
- Hall (2004) "Two concepts of causation" - philosophical analysis distinguishing counterfactual dependence from production
