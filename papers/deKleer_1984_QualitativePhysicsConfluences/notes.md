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

This paper provides a complete framework for qualitative reasoning about physical systems using confluences (qualitative differential equations), qualitative states, a qualitative calculus, causal explanation algorithms, and the concept of mythical causality for determining how device behavior arises from component interactions. *(p.7)*

## Problem Addressed

Classical physics uses continuous real-valued variables and differential equations to describe physical systems. This level of detail often obscures the essential qualitative distinctions (state, cause, oscillation, gain, momentum) that humans use to reason about physical mechanisms. *(p.7)* Expert systems of the era lacked commonsense physical reasoning capabilities; they have no commonsense and cannot solve simpler versions of the problems they are designed to solve. *(p.8)* The paper addresses the gap between formal quantitative physics and the qualitative causal reasoning humans actually use to understand devices. *(p.8)*

## Key Contributions

- **Confluence**: A qualitative differential equation where variables take values from {+, 0, -} and terms sum to a constant. Central modeling primitive for component behavior. *(p.8-9)*
- **Qualitative state**: Each component's operating range is divided into regions (states), each governed by a different set of confluences. State specifications use inequalities over non-derivative variables. *(p.24-25)*
- **Qualitative calculus**: Qualitative versions of continuity, Rolle's theorem, and the mean value theorem; defines qualitative addition and multiplication tables. *(p.23)*
- **ENVISION program**: Implemented system that takes device topology + component library and produces behavioral predictions with causal explanations. *(p.10)*
- **No-function-in-structure principle**: Component laws may not presume the functioning of the whole device. *(p.16)*
- **Class-wide assumptions**: Explicit assumptions (e.g., quasistatic approximation) that apply to an entire class of devices, not just the one under study. *(p.16-17)*
- **Mythical causality and mythical time**: A new notion of causality based on information-passing between neighboring components in "mythical time" (a partial, not total, ordering). *(p.62-63)*
- **Proof-based explanation**: Device behavior predictions are accompanied by logical proofs; causal explanations differ from logical proofs by following cause-effect order. *(p.50)*
- **Episode and state diagrams**: Algorithms for predicting sequences of qualitative states a device may pass through over time. *(p.36-37)*
- **Three canonicality heuristics**: Component, conduit, and confluence heuristics that enable causal accounts matching human explanations. *(p.67, 69, 71, 72)*
- **Feedback detection**: Causal accounts can detect positive and negative feedback as loops in the cause-effect structure, without any explicit notion of feedback in the component models. *(p.73-75)*
- **Digital physics**: The proposal that physical laws can be expressed as constraints on programs, processors, or information-flow among component processors. *(p.13, 76-77)*

## Methodology

The paper develops a theoretical framework grounded in several paradigmatic assumptions:

1. **Quasistatic approximation**: Behavior at small time scales is unimportant; the device is always near equilibrium. This is the classical "lumped circuit" approximation applied across domains. *(p.12, 17)*
2. **Causality as ontological principle**: Device behavior arises from time-ordered cause-effect interactions between neighboring components. *(p.12)*
3. **Generalized machines**: Physical situations are modeled as devices (machines) whose behavior is described by variables (force, velocity, pressure, flow, current, voltage). *(p.12)*
4. **Locality**: A component's laws can only refer to its immediate neighbors. The locality principle also plays a crucial role in the definition of causality, limiting the theory to lumped parameter systems. *(p.18)*
5. **Digital physics**: Each component is viewed as a simple information processor; overall behavior emerges from causal interactions between adjacent component processors. *(p.13)*
6. **No-function-in-structure**: The laws of a device's parts may not presume the functioning of the whole. This is implemented through class-wide assumptions. *(p.16)*
7. **Proof as explanation**: Physical laws, viewed as constraints, are acausal. Explanations are logical proofs expressed in a natural deduction system. *(p.12, 50)*

The framework is demonstrated extensively on a pressure-regulator device. *(p.9)*

## Key Equations

### Qualitative Addition Table ([X] + [Y])

| [Y]\[X] | - | 0 | + |
|----------|---|---|---|
| -        | - | - | ? |
| 0        | - | 0 | + |
| +        | ? | + | + |

Where `?` indicates ambiguity (result could be -, 0, or +). *(p.22)*

### Qualitative Multiplication Table ([X] x [Y])

| [Y]\[X] | - | 0 | + |
|----------|---|---|---|
| -        | + | 0 | - |
| 0        | 0 | 0 | 0 |
| +        | - | 0 | + |

*(p.22)*

Note: [xy] = [x][y], but [x + y] != [x] + [y]. Qualitative multiplication is exact; qualitative addition introduces ambiguity because addition does not form an algebraic group over {+, 0, -}. *(p.22, 80)*

### Confluence Form

$$
\sum T_i = C
$$

Where each term $T_i$ is a variable (attribute), the negation of a variable, or the product of a constant and a variable. All terms sum to a constant $C$ (typically 0). *(p.24)*

### Example: Valve Confluence (WORKING state)

$$
\partial P + \partial A - \partial Q = 0
$$

Where $\partial P$ = change in pressure across valve, $\partial A$ = change in area available for flow, $\partial Q$ = change in flow rate. This is a *pure* confluence (simple sum of derivatives). *(p.8-9, 24)*

The correct *mixed* confluence for the valve is $\partial P + [P]\partial A - \partial Q = 0$, where $[P]$ is the qualitative value of pressure. *(p.25-26)*

### Orifice Flow Equation (quantitative basis)

$$
Q = CA\sqrt{2P/\rho}
$$

Where $Q$ = flow rate, $C$ = discharge coefficient, $A$ = area, $P$ = pressure, $\rho$ = mass density. *(p.26)*

### Qualitative Transform of Orifice Equation

$$
[Q] = [C][A][\sqrt{2P/\rho}] = [+][+][\sqrt{2P/\rho}] = [P]
$$

*(p.26)*

### Differentiated Orifice Equation

$$
\frac{dQ}{dt} = C\sqrt{\frac{2P}{\rho}}\frac{dA}{dt} + \frac{CA}{\rho}\sqrt{\frac{\rho}{2P}}\frac{dP}{dt}
$$

*(p.26)*

### Qualitative Transform of Differentiated Orifice Equation

$$
\partial Q = [P]\partial A + [A][P][P]\partial P
$$

Simplifying (as P > 0 and A > 0): $\partial Q = \partial A + \partial P$. *(p.27)*

### Mean Value Theorem (Qualitative)

$[X(T')] = [X(T)] + \partial X(T)$. If $[X(T)] = 0$ and $\partial X(T) = +$, then $[X(T')] = +$ where $T'$ is the time immediately after $T$. *(p.23-24)*

### Pressure-Sensor Confluence

$$
\partial P = \partial Q
$$

Relates pressure directly to force. The sensor model is extremely simple. *(p.38)*

### Mass (Newton's Second Law) Confluence

$$
[F] = \partial V
$$

Where $\partial V$ is the qualitative derivative of velocity. This is a mixed confluence relating a non-derivative to a derivative. *(p.38)*

### Spring (Hooke's Law) Confluence

$$
\partial F = [V]
$$

Derived from $f = kx$ or $dF/dt = kv$. Also a mixed confluence. *(p.38)*

### Valve with Velocity (Level-2 Model)

$$
\partial P - [V] - \partial Q = 0
$$

The confluence is still mixed because $V$ (velocity) appears as a non-derivative. *(p.39)*

### Wave Equation (Distributed Parameter)

$$
u_{tt} = c^2 u_{xx}
$$

Where $u(x, t)$ is pressure or flow at position $x$ at time $t$. Solutions are of the form $u(x, t) = f(x - ct)$, representing waves. *(p.63)*

## Parameters

This is primarily a theoretical/framework paper; it does not report empirical measurements. The key "parameters" are the qualitative value set and the component models.

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Qualitative value | [x] | - | - | {+, 0, -} | Basic three-valued quantity space | p.21-22 |
| Qualitative derivative | dx | - | - | {+, 0, -} | Direction of change | p.22 |
| Quantity space | [.]_Q | - | - | Disjoint intervals covering reals | General framework for finer distinctions | p.21 |

## Implementation Details

### Data Structures
- **Device topology**: Graph where nodes = components, edges = conduits (pipes, wires, cables). Each component has a type and conduit attachments. *(p.19-20)*
- **Component model**: Set of qualitative states, each with state specifications (inequalities) and confluences. The general form is *state*:[*specifications*], *confluences*. *(p.25)*
- **Conduit**: Simple attachment structure with a flowlike attribute per terminal and a pressurelike attribute per conduit. Conduits transport material but do not process it. *(p.21)*
- **Three kinds of constituents**: Materials (water, air, electrons), components (process/transform material), and conduits (transport material between components). *(p.19)*
- **Attribute**: A variable and its derivatives/integrals, each qualitatively valued. Values [x] and derivatives dx are only instantaneously independent. *(p.22)*
- **Interpretation**: An assignment of qualitative values to all variables that satisfies all confluences. Multiple interpretations represent qualitative ambiguity. *(p.35)*
- **Episode**: A time interval during which all non-derivative variables remain constant and all derivative variables maintain the same qualitative value. *(p.33-34)*
- **State diagram**: Graph of qualitative states with transitions governed by ordering, equality change, epsilon ordering, contradiction avoidance, and continuity rules. *(p.36)*

### Key Algorithms

**Algorithm: Constraint Satisfaction for Confluences** *(p.34-35)*
1. For each component, identify current qualitative state from state specifications.
2. Collect all confluences for that state, plus compatibility and continuity conditions from conduits.
3. Find all consistent assignments of {+, 0, -} to variables using generate-and-test combined with constraint propagation (simple propagation alone is insufficient because the system is inherently simultaneous).
4. Each consistent assignment is an interpretation; the set of all interpretations characterizes the behavior.

**Algorithm: State Transition Rules** *(p.42)*
1. **Ordering rule**: Variables change continuously; state terminates when a variable crosses a boundary. *(p.42)*
2. **Equality change rule**: If $\partial X \neq 0$ and $[X(T)] = A$ (a boundary point interval), the state terminates immediately. *(p.42)*
3. **Epsilon ordering rule**: If $[X]$ changes from 0 to + and $[Y]$ is also changing, $[X]$ changes first (the rationale is that $Y > \epsilon > 0$ takes finite time while $X$ changes instantaneously). *(p.42)*
4. **Contradiction avoidance rule**: If confluences are unsatisfiable in a state, no transition to that state is possible. *(p.42)*
5. **Continuity rule**: Each variable $[X(T)]$ must be adjacent to $[X(T')]$ in the quantity space. *(p.42)*
6. **Mean value rule**: For every variable, $[X(T')] = [X(T)] + \partial X(T)$ must hold. *(p.43)*
7. **Feedback rule**: Knowledge about feedback behavior provides information about transitions. Negative feedback paths cannot overshoot; positive feedback prevents certain transitions. *(p.43)*

**Algorithm: Episode Diagram Construction (Appendix B)** *(p.81-82)*
1. Enumerate all possible composite device states.
2. Apply constraint satisfaction to each; rule out contradictory states (those with no solution to the confluences).
3. For each valid state, determine termination conditions and successor states using the transition rules.
4. Multiple interpretations within a composite state may produce multiple episodes.
5. Result is a directed graph of episodes (expanded episode diagram, Fig. 18).

### Explanation-Proof Structure *(p.50-52)*
- Three kinds of justifications: "Given" (from confluences/input), "Substitution n1,...,nk, m" (value assignments substituted into confluence m), "Premise" (arbitrary unsubstantiated assignment).
- Explanation-proofs are constructed automatically by ENVISION. *(p.51)*
- Lines (1)-(9) form a complete explanation-proof for pressure-regulator behavior. *(p.50)*

### Indirect Proof (RAA) *(p.51-52)*
- Reductio ad absurdum is necessary because some behaviors cannot be explained by direct proof alone (the flow into the valve cannot be shown to be increasing without assuming the contrary leads to contradiction).
- Three new inference rules: "Unique Value" (a variable must have one of +, 0, -), "RAA n, m" (lines n and m contradict), "Discharge n, m1,...,mi" (remove unsubstantiated premises via RAA). *(p.51)*
- A compelling explanation must not depend on any undischarged premises. *(p.52-53)*

### Causality Heuristics *(p.67-73)*
1. **Component heuristic**: A disturbance propagates through a component; if one side is "pushed" or "pulled", the component responds as if the unknown actions are negligible. *(p.69)*
2. **Conduit heuristic**: A disturbance propagates along conduits; if flow changes at one terminal, pressure changes in the conduit are assumed caused by that flow change. *(p.71)*
3. **Confluence heuristic**: Given a confluence, if all but one variable's value is known from the disturbance reaching one terminal, propagate as if the unknown is determined by the knowns. *(p.72)*
- These three heuristics apply across all domains (fluid, electrical, acoustic, rotational, translational). *(p.69)*
- They produce causal accounts matching human explanations of device behavior. *(p.67)*
- The heuristics are abstracted from the kinds of verbal and written explanations human experts give. *(p.67)*

### Digital Physics / Processor Architecture *(p.59, 64, 76-77)*
- Each component is modeled as a simple processor with limited memory that communicates only with neighboring processors.
- Each processor is programmed to satisfy its component's confluences.
- When all but one of a confluence's variables are known, the processor determines the last one.
- The set of variables with new equilibrium values grows monotonically outward from the disturbance source (a "wavefront"). *(p.64)*
- Three computational strategies for processors: (a) chronological backtracking with audit trail, (b) propagate multiple values with no backtracking, (c) negotiation based on local energy minimization (Hopfield networks). *(p.77)*

## Figures of Interest

- **Fig. 1 (p.9):** Pressure-regulator physical diagram showing valve, sensor, diaphragm, spring.
- **Fig. 2 (p.10):** ENVISION system architecture: Component Library + Device Topology -> Behavioral Predictions + Causal Explanation.
- **Fig. 3 (p.20):** Device topology graph for the pressure-regulator.
- **Table 1 (p.20):** Icons for valve, sensor, main-sump, terminal components.
- **Table 2 (p.22):** Qualitative addition table for [X] + [Y].
- **Table 3 (p.22):** Qualitative multiplication table for [X] x [Y].
- **Fig. 4 (p.29):** Variables of the pressure-regulator with conduit/component labels.
- **Fig. 5 (p.32):** Two-tank example illustrating class-wide assumption violations.
- **Fig. 6 (p.32):** Device topology for two-tank example (pipe modeled as valve).
- **Fig. 7 (p.36):** State diagrams for the pressure-regulator (decreasing and increasing input).
- **Fig. 8 (p.40):** Device topology with mass and spring (level-2 model).
- **Fig. 9 (p.41):** State diagram with nine states showing oscillatory behavior (continuing input, mass, spring, no friction).
- **Fig. 10 (p.47):** State diagram with no input signal, no friction (perpetual oscillation).
- **Fig. 11 (p.48):** State diagram with no input signal, with friction (damped oscillation reaching equilibrium).
- **Table 4 (p.34):** Intrastate behavior of the pressure-regulator (8 variables, values and derivatives).
- **Table 5 (p.39):** All pressure-regulator solutions (9 states, 10 variables, level-2 model).
- **Table 6 (p.47):** Solution given no input signal, no friction (10 variables, 9 states).
- **Table 7 (p.49):** Solution given no input signal, with friction (12 variables, 9 states).
- **Table 8 (p.75):** Summary of modeling results: Level 1 acausal = Table 4, Level 2 acausal = Table 5 and Figure 9, causal = Section 7.
- **Table 9 (p.78):** Four interpretations of the pressure-regulator under WORKING-- (reverse operation).
- **Fig. 12 (p.60):** Two narrow pipes (constrictions) in series illustrating RAA necessity.
- **Fig. 13 (p.69):** Component D with three terminals (component heuristic illustration).
- **Fig. 14 (p.70):** Component heuristic applied to valve in pressure-regulator.
- **Fig. 15 (p.71):** Conduit heuristic illustration (three terminals on conduit C).
- **Fig. 16 (p.71):** Conduit heuristic applied to pressure-regulator (conduit OUT with valve and sensor).
- **Fig. 17 (p.72):** Confluence heuristic illustrated for a component D with three terminals.
- **Fig. 18 (p.82):** Expanded episode diagram for the pressure-regulator (with continuing input signal, no friction).

## Results Summary

- ENVISION has been run successfully on hundreds of examples across electronic, translational, hydraulic, and acoustic device types. *(p.10)*
- The qualitative physics correctly predicts that the pressure-regulator achieves homeostasis (negative feedback) and identifies the possibility of oscillation due to phase delay. *(p.10, 45-46)*
- The system produces causal explanations that match engineering intuitions. *(p.67)*
- Ambiguity is inherent in the qualitative approach: 8 confluences with 8 unknowns in the pressure-regulator yield 4 solutions rather than 1 unique solution, because qualitative addition does not form an algebraic group. *(p.78, 80)*
- Level-1 models (without mass/spring) produce simple acausal analysis (Table 4) but cannot explain oscillation or feedback. *(p.75-76)*
- Level-2 models (with mass/spring) produce expanded state diagrams (9 states) that reveal oscillation, ringing, and energy dissipation as identifiable patterns. *(p.39, 47)*
- Causal analysis using mythical causality and the three canonicality heuristics matches the behavioral predictions of the acausal level-2 analysis but additionally reveals feedback loops. *(p.75-76)*
- Any device with feedback necessarily exhibits oscillation when viewed at a lower level, but this oscillation often damps out quickly (quasistatic assumption). *(p.76)*

## Limitations

- **Ambiguity**: The qualitative value set {+, 0, -} often produces multiple interpretations where quantitative analysis yields a unique answer. The addition operation is not invertible. *(p.80)*
- **No quantitative precision**: Cannot distinguish between different magnitudes of the same sign. *(p.15)*
- **Quasistatic assumption required**: The framework cannot handle transient non-equilibrium dynamics without violating its foundational assumptions. *(p.17)*
- **No systematic theory of class-wide assumptions**: Determining when to violate class-wide assumptions (e.g., modeling a pipe as a valve) requires external knowledge. No procedure exists to determine if a topology violates some class-wide assumption. *(p.32)*
- **Mythical causality limitations**: The causal account depends on canonicality heuristics that, while matching human intuitions, are not provably complete. No mechanism exists for how fringe processors decide they are all stuck. Heuristics sometimes produce wrong values requiring backtracking. *(p.65-66)*
- **Finer-grain analysis problems**: Pushing to finer detail (e.g., mixed confluences with momentum and storage capacity) dramatically increases the state space (81 states for two mixed confluences, 4 mixed confluences yield state diagrams with additional unresolvable states and transitions). *(p.62)*
- **Negative resistance**: The heuristics do not work for devices containing negative resistances (e.g., mechanical widgets doing analog multiplication). *(p.69)*
- **Distributed parameter systems**: Conduits are poor for modeling distributed parameter systems (e.g., heat flow in a slab, gravitational fields). *(p.21)*
- **Cannot causally simulate**: It is impossible to "causally simulate" behavior; ENVISION constructs all possible behaviors and all possible causal accounts, then eliminates contradictory ones. *(p.66)*

## Testable Properties

- Qualitative addition of {+, 0, -} values must satisfy Table 2 exactly. *(p.22)*
- Qualitative multiplication of {+, 0, -} values must satisfy Table 3 exactly. *(p.22)*
- If $[X(T)] = 0$ and $\partial X(T) = +$, then $[X(T')] = +$ (mean value theorem). *(p.23-24)*
- A confluence $\partial P + \partial A - \partial Q = 0$ with $\partial P = +$ and $\partial A = +$ must yield $\partial Q = +$. *(p.24)*
- The valve model must have exactly three states (OPEN, WORKING, CLOSED) with the specified confluences. *(p.25)*
- The pure five-state valve model (OPEN, WORKING-+, WORKING-0, WORKING--, CLOSED) is formally equivalent to the mixed three-state model. *(p.26)*
- State transitions must obey all five transition rules simultaneously. *(p.42)*
- The pressure-regulator must exhibit negative feedback behavior under the WORKING state. *(p.74-75)*
- Causal explanations must not depend on undischarged premises (RAA criterion). *(p.52-53)*
- With friction (dissipative law $df/dt = k \cdot dV/dt$), the state diagram must show convergence to equilibrium (Fig. 11). *(p.48)*
- Without friction and no input signal, the state diagram must show perpetual oscillation through states 2-9 (Fig. 10). *(p.47)*
- The continuity condition (Kirchhoff's current law analog) requires that the sum of flowlike variables at a conduit equals zero. *(p.27-28)*
- The compatibility condition (Kirchhoff's voltage law analog) requires that pressurelike variables along structural loops sum to zero. *(p.28)*
- 8 confluences in 8 unknowns for the pressure-regulator yield exactly 4 interpretations. *(p.78)*

## Relevance to Project

This paper is foundational to the propstore's domain of qualitative reasoning and truth maintenance. De Kleer and Brown's confluence-based qualitative physics is a direct predecessor to the ATMS-based reasoning in de Kleer's later work (1986). The notion of multiple interpretations arising from qualitative constraint satisfaction is closely related to the assumption-based truth maintenance system's management of multiple consistent belief sets. The framework of component models, device topology, and behavioral prediction provides the ontological foundation that the ATMS was later designed to support computationally. *(p.7-8)*

## Open Questions

- [ ] How does the qualitative calculus handle higher-order derivatives beyond the first? (Paper notes that $\partial^{n+1}x$ cannot be obtained by differentiating $\partial^n x$ -- one must go back to the quantitative definition.) *(p.22)*
- [ ] Can the framework be extended to handle distributed parameter systems (fields) rather than lumped components? (Paper explicitly notes conduits are poor for this.) *(p.21)*
- [ ] What is the formal relationship between the qualitative value set and interval arithmetic? (Paper mentions connection to catastrophe theory.) *(p.15)*
- [ ] How do the canonicality heuristics for causality relate to more modern causal reasoning frameworks (e.g., Pearl's do-calculus)?
- [ ] Can the Hopfield-network-based local energy minimization approach to processor negotiation be made to work in practice? *(p.77)*

## Related Work Worth Reading

- Forbus, K.D., "Qualitative process theory", Artificial Intelligence 24 (1984) - companion paper in same volume *(p.83)*
- Kuipers, B., "Commonsense reasoning about causality", Artificial Intelligence 24 (1984) - same volume *(p.83)*
- de Kleer, J., "An assumption-based TMS", Artificial Intelligence 28 (1986) - the ATMS paper
- de Kleer, J. and Sussman, G.J., "Propagation of constraints applied to circuit synthesis", Circuit Theory and Applications 8 (1980) 127-144 *(p.83)*
- DiSessa, A.A., "Momentum flow as a world view in elementary mechanics" (1979) - influence on the digital physics perspective *(p.83)*
- Karnopp, D. and Rosenberg, R., "System Dynamics: A Unified Approach" (Wiley, 1975) - the system dynamics methodology underlying device structure *(p.83)*
- Hopfield, J.J., "Neural networks and physical systems with emergent collective computational abilities" (1982) - cited for negotiation-based processor strategy *(p.77, 83)*
- Feynman, Leighton, and Sands, "The Feynman Lectures on Physics" Vol. 1 (1963) - source of the constriction/wave analysis approach *(p.63, 83)*

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] -- cited in Related Work as the ATMS paper; the qualitative physics framework's need for managing multiple interpretations and component assumptions directly motivated the ATMS design.
- [[deKleer_1986_ProblemSolvingATMS]] -- the constraint propagation and consumer architecture in the ATMS problem-solving paper builds on the qualitative constraint satisfaction demonstrated here with confluences.

### New Leads (Not Yet in Collection)
- Forbus, K.D. (1984) -- "Qualitative process theory" -- companion paper presenting the process-based alternative to component-based qualitative physics *(p.83)*
- Kuipers, B. (1984) -- "Commonsense reasoning about causality" -- complementary approach to deriving behavior from structure *(p.83)*

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found -- this paper predates most collection papers and is referenced implicitly through de Kleer's later work)

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] -- **Strong.** The qualitative physics framework is the application domain that motivated the ATMS. Multiple interpretations arising from qualitative constraint satisfaction (8 confluences yielding 4 solutions) correspond directly to multiple ATMS environments. The class-wide assumptions and component assumptions in ENVISION became the ATMS's formal assumption management. This paper provides the "why" for the ATMS design.
- [[deKleer_1986_ProblemSolvingATMS]] -- **Strong.** The ATMS problem-solving paper's constraint language (PLUS, TIMES, AND, OR, ONEOF) directly generalizes the qualitative constraint satisfaction demonstrated here. The consumer architecture's pattern of modular rules firing based on ATMS label status mirrors ENVISION's component models producing behavioral predictions.
- [[Ginsberg_1985_Counterfactuals]] -- **Moderate.** Both papers address reasoning about physical devices under assumptions. De Kleer's class-wide assumptions (quasistatic, locality) parallel Ginsberg's device assumptions in the diagnosis application. Ginsberg's counterfactual framework could formalize the "what if this assumption is violated?" reasoning that de Kleer handles informally.
