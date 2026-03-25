# Notes: Matt & Toni 2008 — Game-Theoretic Measure of Argument Strength

## Date: 2026-03-24

## Status: Reading complete, writing outputs

## Key Observations

- 13-page paper from JELIA 2008 (LNAI 5293, pp. 285-297)
- Authors: Paul-Amaury Matt and Francesca Toni, Imperial College London
- Core idea: Define argument strength via value of a two-person zero-sum game (game of argumentation strategy)
- Proponent picks opinion supporting argument x, opponent picks opinion against x
- Payoff = degree of acceptability of opinion P vs opinion O
- Game value computed via simplex algorithm (linear programming)
- Strength s_F(x) is in [0, 1], equals game value

## Key Definitions
- Def 1: AF = (Arg, att)
- Def 2: Acceptability (conflict-free + defends all members)
- Def 3: Game of argumentation strategy — proponent plays sets containing x, opponent plays sets attacking x
- Def 4: Degree of acceptability d(P, O) — ratio of attacks from P to O vs total attacks
- Def 5: Payoff matrix r_F(P_i, O_j) for the game
- Def 6: Argument strength s_F(x) = value of (F, x) game
- Def 7: Superfluous argument — adding attack on x is superfluous if proponent can counter

## Key Properties (Section 5)
- Prop 2: Strength bounded in [0, 1]
- Prop 3: Strength is 0 iff x attacked by some unattacked argument (self-confirmation must be satisfied)
- Prop 4: Unattacked arguments are strongest (strength = 1)
- Prop 5: Criticism reduces argument strength (adding attack reduces strength)
- Prop 6: Strict monotonicity — adding attack strictly reduces strength unless superfluous
- Prop 7: Counter-extra-aggressiveness increases strength (adding attack on attacker helps)
- Prop 8: Indirect counter-support brings support
- Prop 9: Insensitivity to irrelevant information — adding disconnected args doesn't change strength

## Computation
- Reduce to LP: maximize x_{m+1} subject to constraints
- Solved with simplex algorithm
- Table 1 shows examples for 8 different frameworks F1-F8

## Next Steps
- Write notes.md, description.md, abstract.md, citations.md
- Update index.md
- Run reconcile skill
