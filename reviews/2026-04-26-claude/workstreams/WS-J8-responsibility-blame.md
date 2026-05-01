# WS-J8: Responsibility and Blame

**Status**: OPEN
**Depends on**: WS-J2
**Blocks**: degree-of-responsibility and blame reports.

## Scope

Layer Chockler-Halpern-style responsibility and blame metrics on top of the modified-HP actual-cause evaluator from WS-J2. This is not part of actual-cause truth itself; it quantifies how much contingency change is needed and, for blame, how agent epistemic state affects attribution.

## First Tests

- Singleton but-for causes receive maximal responsibility.
- Overdetermined examples receive lower responsibility than but-for examples.
- Non-causes receive zero responsibility.
- Blame depends on an explicit epistemic/probability model rather than using actual-world truth alone.

## Done Means Done

The public responsibility/blame surface consumes `ActualCauseVerdict` and explicit epistemic inputs, never fabricates probabilities, and has paper-derived examples plus generated monotonicity and zero-for-noncause gates.
