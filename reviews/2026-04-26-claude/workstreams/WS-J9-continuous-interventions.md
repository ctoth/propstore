# WS-J9: Continuous-Domain Interventions

**Status**: OPEN
**Depends on**: WS-J2
**Blocks**: actual-cause search over continuous variables.

## Scope

Extend intervention and actual-cause reasoning beyond Boolean and finite enumerated domains. WS-J2 intentionally raises or has no alternatives when a variable lacks a finite alternative assignment set; this stream owns the continuous-domain witness formulation and solver-backed search.

## First Tests

- Continuous domains cannot silently fall back to singleton actual-value domains.
- Linear threshold models find symbolic or interval witnesses.
- Nonlinear models return typed undecidable/unsupported results rather than false negatives when the solver cannot prove a witness.
- Finite-domain WS-J2 behavior remains unchanged.

## Done Means Done

Continuous-domain SCM variables have explicit domain objects, actual-cause search is solver-backed or typed-unsupported, and no production path treats absence of finite alternatives as evidence that AC2 failed.
