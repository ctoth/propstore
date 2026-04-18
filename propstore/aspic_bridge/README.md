# propstore.aspic_bridge

`propstore.aspic_bridge` is the propstore adapter from scientific-claim data
into the formal ASPIC+ argumentation kernel.

It owns translation from propstore domain objects:

- active claims
- canonical justifications
- stance rows
- grounded rule bundles
- support metadata
- structured projection records

into formal argumentation objects:

- literals
- knowledge bases
- strict and defeasible rules
- contrariness relations
- preference configurations
- complete structured argumentation frameworks

## Boundary

The bridge is propstore-specific and stays in propstore.

The external `argumentation` package owns finite formal argumentation algorithms
and datatypes. It must not know about propstore claims, stances, sidecars,
contexts, source-local state, worldlines, or CLI policy.

This package is therefore allowed to import propstore domain modules and the
formal kernel. The formal kernel is not allowed to import this package.

## Main Entry Points

- `build_bridge_csaf(...)`
  - compiles active claims, justifications, stances, and grounded bundles into a
    complete ASPIC+ framework plus induced Dung AF.
- `query_claim(...)`
  - runs goal-directed ASPIC+ argument construction for one claim conclusion.
- `build_aspic_projection(...)`
  - maps formal arguments back into propstore structured projection records.
- `grounded_rules_to_rules(...)`
  - converts grounded rule bundles into ASPIC+ rules.

## Related Plan

The argumentation-kernel extraction workstream is:

- `plans/argumentation-package-extraction-workstream-2026-04-18.md`

The propstore-side boundary record is:

- `docs/argumentation-package-boundary.md`
