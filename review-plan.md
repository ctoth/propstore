# Review Fix Plan

This plan covers the full review set. Larger items are still sequenced in phases,
but nothing from the written review is being treated as intentionally out of scope.

Status: completed in this repository. The remaining integration work is in
`../research-papers-plugin`, which still needs to emit `papers/*/claims.yaml`
for the import contract implemented here.

## Goals

1. Make the documented CLI workflow actually work on a fresh project.
2. Make the checked-in repository validate and build successfully.
3. Fix the highest-signal contract mismatches between docs, schema, code, and data.
4. Improve sidecar fidelity and validator rigor where the current behavior is misleading.
5. Add integration coverage for the real CLI path.

## Work Items

## Phase 1: Bootstrap and CLI coherence

- make `pks init` create a usable starter project, including baseline `forms/`
- make concept ID generation and lookup coherent across the CLI
- add end-to-end tests for `init -> concept add -> concept show/query`

## Phase 2: Repository data and schema coherence

- migrate checked-in sample claims to the active scalar value format
- fix `concepts/task.yaml` to use structured category values
- fix invalid parameterization metadata in checked-in concepts
- verify `pks validate` and `pks build --force` succeed in the repository

## Phase 3: Validator and sidecar rigor

- centralize duplicated helpers used by validators/builders
- tighten claim file typing where runtime expects loaded claim objects
- add unit consistency checks between claims and concept forms
- stop inventing misleading midpoint scalar values for legacy range-only list data
- persist claim stances into the sidecar instead of dropping them
- improve diagnostics around SymPy generation failures
- make description generation more robust for condition formatting

## Phase 4: Conflict classification improvements

- improve condition classification for the numeric subset that can be mechanically compared
- keep conservative fallback behavior when semantic comparison is not possible
- add regression tests proving numeric-overlap scopes are not mislabeled as `PHI_NODE`
- expand conflict detection to cover equation claims where the compiler can compare
  compatible equation structures mechanically

## Phase 5: Form enforcement and rename safety

- consume form file contents where needed instead of treating forms as existence-only markers
- enforce form-driven unit expectations for claim validation
- add rename-time checking or migration behavior for CEL expressions that depend on canonical names

## Phase 6: Query/test coverage and docs

- add a `pks sidecar query` CLI test
- add a full workflow test covering `init -> add concept -> add/build/sidecar query`
- update README examples and contracts to match current behavior
- keep `code-review.md` and this plan as the written record of the review

## Phase 7: Propstore/research-papers integration groundwork

- define and implement a concrete claim artifact handoff compatible with
  `../research-papers-plugin`
- make the integration path mechanical instead of markdown-only where this repository
  can own that part of the contract
- document what is implemented here versus what must land in the plugin repo

## Commit Plan

1. `docs: add review findings and fix plan`
2. `fix(cli): make fresh projects bootstrapable and align concept ids`
3. `fix(data): align checked-in concepts and claims with active schema`
4. `fix(validator): tighten shared validation helpers and unit checks`
5. `fix(sidecar): preserve stances and improve claim fidelity`
6. `fix(conflicts): improve scope classification and broaden coverage`
7. `fix(forms): enforce form-driven constraints and rename safety`
8. `test(cli): cover query and end-to-end workflow`
9. `docs: update README and integration notes`

## Exit Criteria

- `uv run pytest tests -q` passes
- `uv run pks validate` passes in the repository root
- `uv run pks build --force` passes in the repository root
- the fresh-project bootstrap path succeeds through at least one added concept
