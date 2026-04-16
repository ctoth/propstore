# WS-Z-gates Phase 2 — Schema Migration Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-02-schema.md`
Author: coder subagent

## Commits

Three deliverables, four commits (TDD red commit + impl commit for deliverable 2):

| SHA | Deliverable | Message |
|-----|-------------|---------|
| `41541f3` | 1 | `refactor(sidecar): rename claim_algorithm_payload.stage -> algorithm_stage to clear name for file-lifecycle column` |
| `a1c20c8` | 2 (red) | `test(sidecar): assert build_diagnostics table and claim_core lifecycle columns exist (failing)` |
| `77d4748` | 2 (green) | `feat(sidecar): add build_diagnostics table + claim_core lifecycle columns (schema v3)` |
| `7f3da36` | 3 | `docs(sidecar): document v3 schema additions and lifecycle dimensions` |

## Final test status

```
tests\test_worldline_error_visibility.py ..                              [ 97%]
tests\test_worldline_praf.py ..                                          [ 97%]
tests\test_worldline_properties.py ....................                  [ 97%]
tests\test_worldline_revision.py ......                                  [ 98%]
tests\test_z3_conditions.py ............................................ [ 99%]
...                                                                      [100%]

====================== 2529 passed in 476.38s (0:07:56) =======================
```

Baseline at the start of this phase was 2524 passing. Net delta: +5 tests (the new TestSchemaV3 class), all passing.

## Surface area

```
 docs/algorithm-comparison.md          |  2 +-
 propstore/cli/compiler_cmds.py        |  6 ++-
 propstore/core/graph_build.py         |  2 +-
 propstore/core/row_types.py           | 16 +++---
 propstore/sidecar/claim_utils.py      | 14 +++---
 propstore/sidecar/schema.py           | 95 +++++++++++++++++++++++++++++++++--
 propstore/world/model.py              |  4 +-
 tests/conftest.py                     |  4 +-
 tests/test_algorithm_stage_types.py   |  6 +--
 tests/test_build_sidecar.py           | 85 +++++++++++++++++++++++++++++--
 tests/test_contexts.py                |  6 +--
 tests/test_embed_operational_error.py |  2 +-
 tests/test_graph_build.py             |  4 +-
 tests/test_graph_export.py            |  2 +-
 tests/test_world_model.py             |  4 +-
 15 files changed, 213 insertions(+), 39 deletions(-)
```

## Deliverable 1 — Rename surface

The scout report flagged the column-name collision between `claim_algorithm_payload.stage` (algorithm sub-phase, e.g. "excitation") and the new `claim_core.stage` (file-level lifecycle: `'draft' | 'final' | NULL`). I renamed the existing column to `algorithm_stage` and propagated the rename through every Python identifier on the storage path:

- SQL: `propstore/sidecar/schema.py` — column + index target.
- Populator: `propstore/sidecar/claim_utils.py` — INSERT column list, the row dict key, the local variable name, and the `resolve_algorithm_storage` return path.
- World model: `propstore/world/model.py` — the `_REQUIRED_SCHEMA` set entry and the `_claim_select_sql` projection.
- ClaimRow: `propstore/core/row_types.py` — dataclass attribute, `__post_init__` coercion, the known-keys set, `from_mapping` reader, `to_dict` writer.
- Graph build: `propstore/core/graph_build.py` — the dict construction now reads `row.algorithm_stage` while still writing `"stage"` as the YAML output key (downstream consumers like `_describe_algorithm` read the YAML field).
- CLI: `propstore/cli/compiler_cmds.py` — the `--stage` filter on the algorithm-list command.
- Documentation: `docs/algorithm-comparison.md` — the schema example, with an inline note distinguishing it from `claim_core.stage`.
- Test fixtures: `tests/conftest.py` (two CREATE TABLE blocks), and the test files that hand-roll INSERTs/SELECTs for `claim_algorithm_payload`: `test_contexts.py`, `test_world_model.py`, `test_graph_export.py`, `test_graph_build.py`, `test_embed_operational_error.py`, plus the schema-shape assertion in `test_build_sidecar.py:1531`.
- The `test_algorithm_stage_types.py` postulate test was updated: `ClaimRow.algorithm_stage` is the new attribute name, while `ClaimDocument.stage`, `SourceClaimDocument.stage`, and `ClaimsFileDocument.stage` keep their original names because those are the user-facing YAML field names and were not in scope for the rename.

The boundary stays clean: YAML field `stage` (algorithm) → Python `algorithm_stage` at the populator (`resolve_algorithm_storage`); YAML field `stage` (file-level) → Python `stage` on `claim_core` once phase 3 wires the populator.

## Deliverable 2 — Schema additions

Implemented exactly as the scout proposed:

- `SCHEMA_VERSION` bumped from 2 to 3.
- `claim_core` grew three columns:
  - `build_status TEXT NOT NULL DEFAULT 'ingested'`
  - `stage TEXT`
  - `promotion_status TEXT`
- New `build_diagnostics` table with all 10 scout-spec columns (`id`, `claim_id`, `source_kind`, `source_ref`, `diagnostic_kind`, `severity`, `blocking`, `message`, `file`, `detail_json`).
- Three new indexes on `claim_core` (one per new column).
- Three new indexes on `build_diagnostics` (`claim`, `kind`, `source`-pair).

TDD discipline was honored: the failing test (`a1c20c8`) was committed before any production code changed. All five `TestSchemaV3` tests failed against schema v2 with the expected error messages (e.g. `assert 2 == 3` for `test_schema_version_is_three`); they all passed against schema v3.

## Deliverable 3 — Documentation

- Module docstring on `propstore/sidecar/schema.py` cites `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`, names findings 3.1/3.2/3.3, and explains the orthogonality argument for keeping `build_status`, `stage`, and `promotion_status` as separate columns rather than a single collapsed `status`.
- Function docstring on `create_claim_tables` describes each new column's domain and the `build_diagnostics` quarantine surface, citing the same workstream reference.
- The discipline cited (`reviews/2026-04-16-code-review/workstreams/disciplines.md` rule 5: "Filter at render, not at build") is the project-level grounding that makes the column choices coherent.

## Deviations from scout proposal

None of substance. Two minor choices:

1. **Rename also extended to the Python attribute on `ClaimRow`.** The scout noted the rename "likely" needed to extend to Python identifiers; I confirmed it did (the row dict key was being read directly into `claim_algorithm_payload.stage` insert, which would have collided with the new file-lifecycle column once phase 3 adds `claim_core.stage` to the same row dict). The rename was extended cleanly through `ClaimRow.algorithm_stage`, with the YAML field `stage` preserved on the document-side classes per the existing `test_algorithm_stage_types.py` postulates.

2. **Index name `idx_claim_algorithm_stage` retained.** It already names the algorithm payload's stage column unambiguously; renaming the index would have been churn without semantic gain.

## Flags raised during work

1. **Hypothesis flake on full-suite run.** `tests/test_form_dimensions.py::TestDimensionsPropertyBased::test_forms_with_same_dimensions_compatible` hit a Hypothesis internal `DeadlineExceeded` (200ms) on one of the two intermediate full-suite runs. Verified the test passes in isolation in 2.28s and that schema-shape changes cannot cause a property test about form dimensions to slow down. Re-ran the full suite to a clean 2529 passing. Flag for the next coder if this surfaces in CI.

2. **Pre-existing unrelated changes in working tree.** The git status snapshot at the start of this dispatch carried numerous modified `papers/` files, untracked notebook artifacts, and `pyghidra_mcp_projects/`. None of these are part of WS-Z-gates phase 2. I added only the files I edited; the unrelated changes remain untouched in the working tree.

3. **`docs/algorithm-comparison.md` updated.** The scout report did not list this file. It contained an out-of-date schema snippet referencing the old column name; updating it preserved doc-vs-code consistency per `disciplines.md` rule 2 ("Docs never lead code"). Flagging because it was outside the scout's enumerated surface.

## Out of scope (deferred to later phases)

Per the prompt:
- Populating the new columns from build code (phase 3).
- Refactoring `_raise_on_raw_id_claim_inputs`, `compiler/passes.py:289-307`, or `source/promote.py` (phase 3).
- Adding `RenderPolicy` fields or CLI flags (phase 4).
- Documentation updates beyond the schema docstring (phase 5).
