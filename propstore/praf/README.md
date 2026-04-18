# propstore.praf

`propstore.praf` is propstore's probabilistic argumentation adapter surface.

It stays in propstore because it owns propstore-specific inputs and metadata:

- claim rows
- stance rows
- calibrated opinions
- provenance-bearing probabilistic relations
- support/attack/defeat projections from the active claim graph
- world and CLI strategy policy

## Boundary

The external `argumentation.probabilistic` package owns the reusable
float-valued PrAF and quantitative AF kernels: deterministic fallback, exact
enumeration, Monte Carlo sampling, connected-component decomposition,
tree-decomposition DP, and DF-QuAD / QBAF gradual semantics.

`propstore.praf` consumes those kernels after converting propstore opinions to
float expectations. Propstore row, provenance, opinion, stance, and analyzer
surfaces stay here.

## Main Entry Points

- `build_praf(...)`
  - store-facing construction of a probabilistic argumentation framework from
    the active claim graph.
- `compute_probabilistic_acceptance(...)`
  - imported from `argumentation.probabilistic` and used after propstore
    adapter construction.
- `enforce_coh(...)`
  - applies the COH rationality constraint to probabilistic argument
    existence opinions.
- `p_arg_from_claim(...)`, `p_relation_from_stance(...)`
  - propstore-specific mappings from claim/stance payloads into opinions.

## Extraction Rule

Store-facing construction, provenance, stance mapping, opinion calibration, and
CLI/worldline strategy policy stay in propstore. Formal algorithms that import
no propstore modules belong in `argumentation`.

## Related Plan

- `plans/argumentation-package-extraction-workstream-2026-04-18.md`
- `docs/argumentation-package-boundary.md`
