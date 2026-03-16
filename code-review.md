# Propstore Code Review

This review consolidates two passes:

- a behavioral/end-to-end review of the current repository state
- a code-level review of implementation details and design gaps

The goal is to distinguish what the project claims to do, what it actually does,
and what should be fixed first.

## Verification Baseline

Observed from the current repository before fixes:

- `uv run pytest tests -q` passed with `253 passed`
- `uv run pks validate` failed on checked-in sample claims
- `uv run pks build --force` failed on checked-in sample claims
- a fresh `pks init` project could not successfully `pks concept add --form pressure ...`
- `pks concept add` could emit `concept1`, but `pks concept show concept1` failed
- `pks claim conflicts` classified semantically overlapping numeric scopes as `PHI_NODE`

## Critical

### 1. Freshly initialized projects are not bootstrapable

`pks init` creates `concepts/`, `claims/`, and `sidecar/`, but it does not create
`forms/`. `pks concept add` requires a form, and concept validation fails if
`forms/<name>.yaml` does not exist.

Consequence:

- the documented bootstrap workflow fails immediately on a fresh project

### 2. The CLI creates concept IDs it cannot reliably look up

`concept add` currently generates IDs like `concept1`, but concept lookup logic
is still biased toward the older `speech_0001` style.

Consequence:

- the CLI can create a concept and then fail to show, rename, alias, or deprecate
  it by the ID it just printed

### 3. The checked-in repository does not satisfy its active claim schema

The current claim schema expects scalar numeric `value` fields, but checked-in
sample claims still use the legacy list form like `value: [200.0]`.

Consequence:

- `pks validate` fails on the repository as checked in
- `pks build` aborts on the repository as checked in
- the project is not self-hosting its advertised pipeline

### 4. Conflict classification is syntactic, not semantic

Condition comparison is done by set equality/intersection over CEL strings,
not by reasoning about their meaning. For example:

- `fundamental_frequency > 100`
- `fundamental_frequency > 200`

These scopes overlap semantically, but are treated as disjoint if their strings
do not match.

Consequence:

- `PHI_NODE`, `OVERLAP`, and `CONFLICT` classifications are only partially
  trustworthy
- the core "same scope vs different scope" claim is overstated

## High

### 5. The `task` concept's category values are not structured

`concepts/task.yaml` stores category metadata as a note string instead of
structured `values` and `extensible` fields.

Consequence:

- CEL checking cannot validate task values correctly
- every `task == '...'` condition produces spurious warnings instead of real checks
- tests pass because fixtures use the structured form, while real repository data does not

### 6. Stance links exist in schema but are dropped by the compiler

The claim schema supports `stances`, but the SQLite sidecar does not persist them.

Consequence:

- support, contradiction, supersession, and mechanism links cannot survive compilation
- the current sidecar is not yet the reconciled proposition graph described in the design doc

### 7. No unit consistency checking exists between claims and concepts

A claim can bind to a concept with an obviously incompatible unit string and still validate.

Consequence:

- the compiler accepts materially invalid quantitative claims
- forms currently act mostly as labels, not enforceable constraints

### 8. The form system is barely enforced

The compiler checks only that `forms/<name>.yaml` exists. It does not consume
form file contents to validate claims or concept semantics beyond broad kind mapping.

Consequence:

- the implemented system falls well short of the design doc's form-driven type model

## Medium

### 9. Sidecar storage for legacy range values invents midpoints

When a legacy list value has two or more numbers, the sidecar stores the midpoint
in the scalar `value` column while also storing bounds.

Consequence:

- downstream consumers may read a value that never appeared in source data
- range semantics are partially preserved and partially distorted

### 10. `concept add` validates by writing first and checking the whole registry

The current flow writes the file, reloads all concepts, validates everything,
and then rolls back on failure.

Consequence:

- it is more fragile than necessary
- the operation is more expensive than necessary
- rollback logic is exposed to partial-failure edges

### 11. `open_quotient.yaml` includes itself as a parameterization input

The concept appears in its own `inputs` list even though the RHS does not require it.

Consequence:

- the parameterization graph contains a semantically wrong self-edge
- PARAM_CONFLICT derivation can become circular or misleading

### 12. Equation claims are ignored by conflict detection

Only parameter and measurement claims are compared for conflicts.

Consequence:

- contradictory equations for the same phenomenon are invisible to the current detector

### 13. Renaming a concept silently risks breaking CEL conditions

Claims use concept IDs, while CEL expressions use canonical names.

Consequence:

- changing a canonical name can invalidate CEL expressions without a migration path

## Low

### 14. Shared logic is duplicated

Duplicated helpers exist for:

- `_json_safe`
- form-to-kind mapping

Consequence:

- drift risk
- unnecessary maintenance overhead

### 15. Typing around claim files is weaker than the code assumes

Some functions operate on loaded claim file objects but are typed as bare `list`.

Consequence:

- type hints under-document the actual contract

### 16. Description generation is brittle for condition formatting

The human-readable condition summarizer only recognizes a narrow equality pattern.

Consequence:

- generated descriptions are inconsistent across equivalent CEL expressions

### 17. SymPy generation loses failure diagnostics

Expression parsing failures collapse to `None` with no stored reason.

Consequence:

- sidecar consumers cannot tell why a generated SymPy expression is missing

### 18. Missing full CLI workflow coverage

The test suite is strong in isolated modules, but weak on the full workflow:

- `pks init`
- add concepts
- add claims
- `pks build`
- `pks query`

Consequence:

- regressions in the real user path can survive while unit-level tests remain green

## Summary

What is already real:

- concept and claim validation
- CEL parsing/type checking
- SQLite sidecar generation
- FTS-backed local querying
- conflict detection for a narrow subset of claim types
- a substantial isolated test suite

What is not yet real enough:

- clean bootstrap
- coherent ID and schema contracts
- reliable scope reasoning
- stance persistence
- form-driven quantitative enforcement
- end-to-end integration with the paper-processing pipeline
