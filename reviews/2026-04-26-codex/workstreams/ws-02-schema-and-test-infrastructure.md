# WS-02: Schema and test infrastructure truthfulness

## Review findings covered

- Required schema validation omits lifecycle/quarantine columns runtime code selects.
- Tests use a hand-written "canonical" world-model schema that diverges from production.
- Generated schema freshness and package-resource coverage are not enforced.
- Architecture gates are mostly selected-file/string checks.
- Hypothesis/property test selection is unreliable because many `@given` tests are unmarked.

## Why this comes before most fixes

If fixtures do not match production, regression tests can prove the wrong thing. This stream makes the test substrate trustworthy before identity, sidecar, reasoning, and publication repairs depend on it.

## First failing tests

1. Required schema completeness:
   - Create a production sidecar schema in a temp database.
   - Mutate/drop or simulate absence of each runtime-required lifecycle surface:
     - `claim_core.build_status`
     - `claim_core.stage`
     - `claim_core.promotion_status`
     - `build_diagnostics`
   - Assert `WorldModel` rejects the sidecar at open/validation time before a query crashes.

2. Fixture schema drift:
   - Build one database with production schema builders.
   - Build one with `tests/conftest.py:create_world_model_schema`.
   - Compare `PRAGMA table_info`, PKs, not-null constraints, and key indexes for tables used by `WorldModel`.
   - This test should fail immediately, proving the duplicate schema is lying.

3. Generated schema freshness:
   - Run the schema generator into a temp output directory, not into the repo.
   - Byte-compare generated output against committed `schema/generated/*`.
   - If package resources are expected, assert committed `propstore/_resources/schemas/*` exists and matches.

4. Property marker integrity:
   - AST scan `tests/`.
   - Any function decorated with `@given` must also have `@pytest.mark.property`, or the project must stop relying on the `property` marker.
   - Test should fail on currently unmarked Hypothesis tests.

5. Architecture gate broadening:
   - Add a first package-wide ownership test for one high-value boundary:
     - no `propstore.cli` imports from app/owner modules
     - no `click` imports outside CLI
     - no `sys.exit`/stdout/stderr writes in owner modules
   - Start with a failing gate tied to an existing finding, not a giant policy rewrite.

## Production/test change sequence

1. Expand `_REQUIRED_SCHEMA` to include every column/table runtime queries require.

2. Replace duplicate test schema construction:
   - Prefer production schema builders in fixtures.
   - If tests need minimal fixtures, derive them from production DDL and insert only necessary rows.
   - Delete or quarantine the hand-written "canonical" schema once callers are moved.

3. Add schema drift checks:
   - One test for runtime required schema vs production schema.
   - One test for generated artifacts vs generator output.

4. Normalize property markers:
   - Mark existing Hypothesis tests or remove the marker from the workflow.
   - Add the AST gate so future property tests cannot be invisible.

5. Convert brittle string/path architecture tests into package-level gates incrementally:
   - Use AST where practical.
   - Use import-linter for package dependencies.
   - Keep specific string tests only for truly intentional exact source shapes.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label schema-gates tests/test_required_schema_completeness.py tests/architecture`
  - Add any new schema drift/property marker tests.
- `uv run pyright propstore`
- `uv run lint-imports`

## Done means

- World-model tests run against production-compatible schema.
- Runtime-required sidecar columns are validated before use.
- Generated schema resources cannot silently drift or disappear.
- Property and ownership gates select the tests they claim to select.
