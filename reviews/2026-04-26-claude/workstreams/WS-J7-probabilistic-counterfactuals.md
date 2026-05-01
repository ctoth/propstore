# WS-J7: Probabilistic Counterfactuals and Bayesian Observation

**Status**: OPEN
**Depends on**: WS-J2
**Blocks**: Bayesian observation semantics and probabilistic SCM queries.

## Scope

Extend the deterministic SCM surface from WS-J2 with a probability model over exogenous variables, posterior conditioning for observations, and Pearl-style probabilistic counterfactual queries. WS-J2's `ObservationWorld` deliberately fails closed on deterministic disagreement; this stream owns replacing that narrow observation cut with a real Bayesian observation operator.

## First Tests

- Observing evidence updates the posterior over exogenous assignments without replacing structural equations.
- `do(X=x)` remains surgical and is not implemented as conditioning on `X=x`.
- A twin-network counterfactual query shares exogenous variables between actual and counterfactual copies.
- Deterministic WS-J2 observations remain a special case of probability-one evidence.

## Done Means Done

`ObservationWorld` supports explicit probabilistic evidence and posterior queries, `InterventionWorld` keeps Pearl do-surgery semantics, and tests prove conditioning and intervention produce different answers on generated confounded SCMs.
