# propstore.belief_set

`propstore.belief_set` owns propstore's formal belief-revision surfaces:

- AGM-style expansion, contraction, and revision
- iterated revision operators
- epistemic entrenchment
- model-theoretic IC merge

## Boundary

This package is formal-adjacent, but it is not part of the initial
`argumentation` extraction.

The initial `argumentation` package should contain the finite argumentation
kernels only:

- `argumentation.dung`
- `argumentation.aspic`
- `argumentation.bipolar`

`propstore.belief_set` can be reconsidered only after the argumentation package
is external and after any provenance or propstore-specific coupling has been
made explicit.

Belief-set language, revision state, provenance, and propstore world/query
integration remain propstore-owned unless a separate belief-revision package is
defined with its own boundary and tests.

## Main Entry Points

- `agm.py`
  - one-shot belief-set revision operators.
- `iterated.py`
  - iterated revision operators.
- `entrenchment.py`
  - entrenchment ordering helpers.
- `ic_merge.py`
  - IC merge over finite belief sets.

## Related Plan

- `plans/argumentation-package-extraction-workstream-2026-04-18.md`
- `docs/argumentation-package-boundary.md`
