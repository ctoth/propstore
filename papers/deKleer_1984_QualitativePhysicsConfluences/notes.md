---
title: "A Qualitative Physics Based on Confluences"
authors: "Johan De Kleer, John Seely Brown"
year: 1984
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(84)90002-5"
pages: "7-83"
affiliation: "Xerox PARC, Intelligent Systems Laboratory, Palo Alto, CA"
---

# A Qualitative Physics Based on Confluences

## One-Sentence Summary

This paper provides a complete framework for qualitative reasoning about physical systems using confluences (qualitative differential equations), qualitative states, a qualitative calculus, causal explanation algorithms, and the concept of mythical causality for determining how device behavior arises from component interactions.

## Problem Addressed

Classical physics uses continuous real-valued variables and differential equations to describe physical systems. This level of detail often obscures the essential qualitative distinctions (state, cause, oscillation, gain, momentum) that humans use to reason about physical mechanisms. Expert systems of the era lacked commonsense physical reasoning capabilities. The paper addresses the gap between formal quantitative physics and the qualitative causal reasoning humans actually use to understand devices.

## Key Contributions

- **Confluence**: A qualitative differential equation where variables take values from {+, 0, -} and terms sum to a constant. Central modeling primitive for component behavior.
- **Qualitative state**: Each component's operating range is divided into regions (states), each governed by a different set of confluences. State specifications use inequalities over non-derivative variables.
- **Qualitative calculus**: Qualitative versions of continuity, Rolle's theorem, and the mean value theorem; defines qualitative addition and multiplication tables.
- **ENVISION program**: Implemented system that takes device topology + component library and produces behavioral predictions with causal explanations.
- **No-function-in-structure principle**: Component laws may not presume the functioning of the whole device.
- **Class-wide assumptions**: Explicit assumptions (e.g., quasistatic approximation) that apply to an entire class of devices, not just the one under study.
- **Mythical causality and mythical time**: A new notion of causality based on information-passing between neighboring components in "mythical time" (a partial, not total, ordering).
- **Proof-based explanation**: Device behavior predictions are accompanied by logical proofs; causal explanations differ from logical proofs by following cause-effect order.
- **Episode and state diagrams**: Algorithms for predicting sequences of qualitative states a device may pass through over time.

## Methodology

The paper develops a theoretical framework grounded in several paradigmatic assumptions:

1. **Quasistatic approximation**: Behavior at small time scales is unimportant; the device is always near equilibrium.
2. **Causality as ontological principle**: Device behavior arises from time-ordered cause-effect interactions between neighboring components.
3. **Generalized machines**: Physical situations are modeled as devices (machines) whose behavior is described by variables (force, velocity, pressure, flow, current, voltage).
4. **Locality**: A component's laws can only refer to its immediate neighbors.
5. **Digital physics**: Each component is viewed as a simple information processor; overall behavior emerges from causal interactions between adjacent component processors.

The framework is demonstrated extensively on a pressure-regulator device.

## Key Equations

### Qualitative Addition Table ([X] + [Y])

| [Y]\[X] | - | 0 | + |
|----------|---|---|---|
| -        | - | - | ? |
| 0        | - | 0 | + |
| +        | ? | + | + |

Where `?` indicates ambiguity (result could be -, 0, or +).

### Qualitative Multiplication Table ([X] x [Y])

| [Y]\[X] | - | 0 | + |
|----------|---|---|---|
| -        | + | 0 | - |
| 0        | 0 | 0 | 0 |
| +        | - | 0 | + |

### Confluence Form

$$
\sum T_i = C
$$

Where each term $T_i$ is a variable (attribute), the negation of a variable, or the product of a constant and a variable. All terms sum to a constant $C$ (typically 0).

### Example: Valve Confluence (WORKING state)

$$
\partial P + \partial A - \partial Q = 0
$$

Where $\partial P$ = change in pressure across valve, $\partial A$ = change in area available for flow, $\partial Q$ = change in flow rate.

### Orifice Flow Equation (quantitative basis)

$$
Q = CA\sqrt{2P/\rho}
$$

Where $Q$ = flow rate, $C$ = discharge coefficient, $A$ = area, $P$ = pressure, $\rho$ = mass density.

### Qualitative Transform of Orifice Equation

$$
[Q] = [C][A][\sqrt{2P/\rho}] = [+][+][\sqrt{2P/\rho}] = [P]
$$

### Differentiated Orifice Equation

$$
\frac{dQ}{dt} = C\sqrt{\frac{2P}{\rho}}\frac{dA}{dt} + \frac{CA}{\rho}\sqrt{\frac{\rho}{2P}}\frac{dP}{dt}
$$

### Mean Value Theorem (Qualitative)

If $[X(T_1)] = [X(T_2)]$ where $T_1 < T_2$, then $\partial X(T_i) = 0$ for some $T_1 \leq T_i \leq T_2$. If $T_1 < T_2$ and $\partial X(T) = +$, then $[X(T')] = +$ where $T'$ is immediately after $T$.

## Parameters

This is primarily a theoretical/framework paper; it does not report empirical measurements. The key "parameters" are the qualitative value set and the component models.

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Qualitative value | [x] | - | - | {+, 0, -} | Basic three-valued quantity space |
| Qualitative derivative | dx | - | - | {+, 0, -} | Direction of change |

## Implementation Details

### Data Structures
- **Device topology**: Graph where nodes = components, edges = conduits (pipes, wires, cables). Each component has a type and conduit attachments.
- **Component model**: Set of qualitative states, each with state specifications (inequalities) and confluences.
- **Conduit**: Simple attachment structure with a flowlike attribute per terminal and a pressurelike attribute per conduit.
- **Attribute**: A variable and its derivatives/integrals, each qualitatively valued.
- **Interpretation**: An assignment of qualitative values to all variables that satisfies all confluences.
- **Episode**: A time interval during which all non-derivative variables remain constant.
- **State diagram**: Graph of qualitative states with transitions governed by ordering, equality change, epsilon ordering, contradiction avoidance, and continuity rules.

### Key Algorithms

**Algorithm: Constraint Satisfaction for Confluences**
1. For each component, identify current qualitative state from state specifications.
2. Collect all confluences for that state, plus compatibility and continuity conditions from conduits.
3. Find all consistent assignments of {+, 0, -} to variables using the qualitative addition/multiplication tables.
4. Each consistent assignment is an interpretation; the set of all interpretations characterizes the behavior.

**Algorithm: State Transition Rules**
1. **Ordering rule**: Variables change continuously; state terminates when a variable crosses a boundary.
2. **Equality change rule**: If $\partial X \neq 0$ and $[X] = A$ (a boundary point), the state terminates immediately.
3. **Epsilon ordering rule**: If $[X]$ changes from 0 to + and $[Y]$ is also changing, $[X]$ changes first.
4. **Contradiction avoidance rule**: If confluences are unsatisfiable in a state, no transition to that state is possible.
5. **Continuity rule**: Each variable $[X(T)]$ must be adjacent to $[X(T')]$ in the quantity space.

**Algorithm: Episode Diagram Construction (Appendix B)**
1. Enumerate all possible composite device states.
2. Apply constraint satisfaction to each; rule out contradictory states.
3. For each valid state, determine termination conditions and successor states using the transition rules.
4. Result is a directed graph of episodes.

### Causality Heuristics
1. **Conduit heuristic**: A disturbance propagates along conduits in the direction away from the source.
2. **Confluence heuristic**: Given a confluence, if all but one variable's value is known, propagate as if the unknown is determined by the knowns.
3. These heuristics produce causal accounts that match human explanations of device behavior.

## Figures of Interest

- **Fig. 1 (page 9):** Pressure-regulator physical diagram showing valve, sensor, diaphragm, spring.
- **Fig. 2 (page 10):** ENVISION system architecture: Component Library + Device Topology -> Behavioral Predictions + Causal Explanation.
- **Fig. 3 (page 20):** Device topology graph for the pressure-regulator.
- **Table 1 (page 20):** Icons for valve, sensor, main-sump, terminal components.
- **Table 2 (page 22):** Qualitative addition table for [X] + [Y].
- **Table 3 (page 22):** Qualitative multiplication table for [X] x [Y].
- **Fig. 5 (page 32):** Two-tank example illustrating class-wide assumption violations.
- **Fig. 7 (page 38):** State diagrams for the pressure-regulator.
- **Fig. 9 (page 40):** State diagram with multiple outgoing edges showing ambiguity.
- **Fig. 17 (page 72):** Confluence heuristic illustrated for a component D with three terminals.
- **Fig. 18 (page 82):** Expanded episode diagram for the pressure-regulator.

## Results Summary

- ENVISION has been run successfully on hundreds of examples across electronic, translational, hydraulic, and acoustic device types.
- The qualitative physics correctly predicts that the pressure-regulator achieves homeostasis (negative feedback) and identifies the possibility of oscillation due to phase delay.
- The system produces causal explanations that match engineering intuitions.
- Ambiguity is inherent in the qualitative approach (8 confluences with 8 unknowns in the pressure-regulator yield 4 solutions rather than 1 unique solution as in quantitative analysis, because qualitative addition does not form an algebraic group).

## Limitations

- **Ambiguity**: The qualitative value set {+, 0, -} often produces multiple interpretations where quantitative analysis yields a unique answer. The addition operation is not invertible.
- **No quantitative precision**: Cannot distinguish between different magnitudes of the same sign.
- **Quasistatic assumption required**: The framework cannot handle transient non-equilibrium dynamics without violating its foundational assumptions.
- **No systematic theory of class-wide assumptions**: Determining when to violate class-wide assumptions (e.g., modeling a pipe as a valve) requires external knowledge.
- **Mythical causality limitations**: The causal account depends on canonicality heuristics that, while matching human intuitions, are not provably complete.
- **Finer-grain analysis problems**: Pushing to finer detail (e.g., mixed confluences with momentum and storage capacity) dramatically increases the state space (81 states for two mixed confluences).

## Testable Properties

- Qualitative addition of {+, 0, -} values must satisfy Table 2 exactly.
- Qualitative multiplication of {+, 0, -} values must satisfy Table 3 exactly.
- If $[X(T)] = 0$ and $\partial X(T) = +$, then $[X(T')] = +$ (mean value theorem).
- A confluence $\partial P + \partial A - \partial Q = 0$ with $\partial P = +$ and $\partial A = +$ must yield $\partial Q = +$.
- The valve model must have exactly three states (OPEN, WORKING, CLOSED) with the specified confluences.
- State transitions must obey all five transition rules simultaneously.
- The pressure-regulator must exhibit negative feedback behavior under the WORKING state.
- Causal explanations must not depend on undischarged premises (RAA criterion).

## Relevance to Project

This paper is foundational to the propstore's domain of qualitative reasoning and truth maintenance. De Kleer and Brown's confluence-based qualitative physics is a direct predecessor to the ATMS-based reasoning in de Kleer's later work (1986). The notion of multiple interpretations arising from qualitative constraint satisfaction is closely related to the assumption-based truth maintenance system's management of multiple consistent belief sets. The framework of component models, device topology, and behavioral prediction provides the ontological foundation that the ATMS was later designed to support computationally.

## Open Questions

- [ ] How does the qualitative calculus handle higher-order derivatives beyond the first?
- [ ] Can the framework be extended to handle distributed parameter systems (fields) rather than lumped components?
- [ ] What is the formal relationship between the qualitative value set and interval arithmetic?
- [ ] How do the canonicality heuristics for causality relate to more modern causal reasoning frameworks (e.g., Pearl's do-calculus)?

## Related Work Worth Reading

- Forbus, K.D., "Qualitative process theory", Artificial Intelligence 24 (1984) - companion paper in same volume
- Kuipers, B., "Commonsense reasoning about causality", Artificial Intelligence 24 (1984) - same volume
- de Kleer, J., "An assumption-based TMS", Artificial Intelligence 28 (1986) - the ATMS paper
- de Kleer, J. and Sussman, G.J., "Propagation of constraints applied to circuit synthesis", Circuit Theory and Applications 8 (1980) 127-144
- DiSessa, A.A., "Momentum flow as a world view in elementary mechanics" (1979) - influence on the digital physics perspective

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] — cited in Related Work as the ATMS paper; the qualitative physics framework's need for managing multiple interpretations and component assumptions directly motivated the ATMS design.
- [[deKleer_1986_ProblemSolvingATMS]] — the constraint propagation and consumer architecture in the ATMS problem-solving paper builds on the qualitative constraint satisfaction demonstrated here with confluences.

### New Leads (Not Yet in Collection)
- Forbus, K.D. (1984) — "Qualitative process theory" — companion paper presenting the process-based alternative to component-based qualitative physics
- Kuipers, B. (1984) — "Commonsense reasoning about causality" — complementary approach to deriving behavior from structure

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — this paper predates most collection papers and is referenced implicitly through de Kleer's later work)

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** The qualitative physics framework is the application domain that motivated the ATMS. Multiple interpretations arising from qualitative constraint satisfaction (8 confluences yielding 4 solutions) correspond directly to multiple ATMS environments. The class-wide assumptions and component assumptions in ENVISION became the ATMS's formal assumption management. This paper provides the "why" for the ATMS design.
- [[deKleer_1986_ProblemSolvingATMS]] — **Strong.** The ATMS problem-solving paper's constraint language (PLUS, TIMES, AND, OR, ONEOF) directly generalizes the qualitative constraint satisfaction demonstrated here. The consumer architecture's pattern of modular rules firing based on ATMS label status mirrors ENVISION's component models producing behavioral predictions.
- [[Ginsberg_1985_Counterfactuals]] — **Moderate.** Both papers address reasoning about physical devices under assumptions. De Kleer's class-wide assumptions (quasistatic, locality) parallel Ginsberg's device assumptions in the diagnosis application. Ginsberg's counterfactual framework could formalize the "what if this assumption is violated?" reasoning that de Kleer handles informally.
