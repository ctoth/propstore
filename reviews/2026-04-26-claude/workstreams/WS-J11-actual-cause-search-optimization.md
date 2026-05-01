# WS-J11: Actual-Cause Search Optimization

**Status**: OPEN
**Depends on**: WS-J2
**Blocks**: large finite-SCM actual-cause queries.

## Scope

Replace WS-J2's naive exponential AC2 witness enumeration with a principled optimized search path, such as SAT/SMT-backed witness discovery or another paper-grounded pruning strategy. WS-J2 keeps `max_witnesses` as the safety valve; this stream owns performance without changing the modified-HP semantics.

## First Tests

- Optimized search returns the same verdict and witness class as exhaustive search on generated small finite SCMs.
- Search respects `max_witnesses` and reports budget exhaustion without false negatives.
- Large voting-style examples avoid enumerating the full powerset when a proof of no singleton cause is available.
- Optimization never holds non-actual witness variables at non-actual values.

## Done Means Done

The optimized evaluator is semantically equivalent to exhaustive modified-HP search on the generated comparison suite, exposes typed budget/proof metadata, and keeps the exhaustive implementation only as a test oracle or explicitly named fallback.
