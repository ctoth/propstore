# WS-07: CLI ownership, app requests, and architecture gates

## Review findings covered

- App-layer request objects accept CLI-shaped payloads and parse option syntax.
- Worldline/revision app code exposes CLI option names and parsing responsibilities.
- Owner modules print directly to stdout/stderr or own command parsing.
- Architecture gates are too narrow to enforce package-wide CLI/owner boundaries.

## Dependencies

- Can begin after `ws-02-schema-and-test-infrastructure.md`.
- Should finish after streams 3-6, because owner APIs should target the repaired domain interfaces rather than today’s defective ones.

## First failing tests

1. App request shape gate:
   - AST scan `propstore/app`.
   - Fail if request dataclass fields use CLI-shaped names such as:
     - `*_json`
     - `dimensionless` when it represents a flag rather than a typed domain field
     - comma-separated string collections such as `values: str`
   - Allow explicit exceptions only with local comments and a test explaining why the app boundary truly owns that shape.

2. CLI flag text in app/owner errors:
   - AST or text scan app/owner modules for error messages naming `--flag`.
   - Fail for `--dimensions`, `--common-alternatives`, `--revision-*`, `--atom`, `--target`, `--operation` outside CLI modules.
   - Domain errors should name domain fields: `dimensions`, `revision.atom`, `revision.target`.

3. No process streams in owner modules:
   - AST scan non-CLI packages for:
     - `print(..., file=sys.stderr)`
     - `sys.exit`
     - direct stdout/stderr writes
   - Existing offenders: sidecar build embedding status, provenance unsupported-file print, contracts command entry.

4. Command parser ownership:
   - Fail if owner modules import `argparse` or `click`.
   - `propstore/contracts.py` should expose manifest/report functions only; CLI/script wrappers own argv parsing.

5. Whole-package import boundary:
   - Add import-linter or AST checks for:
     - `propstore.cli` not imported by owner modules
     - no Click imports outside `propstore.cli`
     - CLI modules call app/owner APIs but do not own compiler workflows, repository mutation semantics, source promotion/finalize/status semantics, sidecar SQL policy, or world/revision query semantics.

## Production change sequence

1. Define typed request/report/failure targets:
   - Forms app requests receive parsed dimensions/common alternatives as domain values.
   - Concepts app mutation receives typed enum/list values, not comma strings.
   - Worldline/revision app requests receive typed revision atom/target/operation objects.

2. Move parsing into CLI:
   - CLI modules parse JSON strings, comma lists, flags, and option combinations.
   - CLI then constructs typed app requests.
   - Delete app-layer JSON parsing and CLI flag wording.

3. Move diagnostics to reports/failures:
   - Sidecar build returns embedding snapshot diagnostics in a typed report.
   - Provenance unsupported file type becomes typed diagnostic/failure.
   - CLI renders reports to stderr/stdout.

4. Split command entry from owner modules:
   - Keep contract manifest construction in `propstore/contracts.py`.
   - Move argv parsing and `SystemExit` behavior to `propstore.cli` or a script wrapper.

5. Add broad gates after each migration:
   - Do not wait until all modules are perfect to add gates.
   - Add a gate for each class as it is fixed, then shrink allowlists to zero.

## TDD commit sequence

1. Commit failing gate for one class, preferably CLI flag text in app errors.
2. Move parsing for that class to CLI and commit passing gate.
3. Repeat for request shapes, process streams, parser ownership, and import boundaries.
4. After all classes pass, add a small integration test for one CLI command per migrated family to prove behavior is unchanged at the user boundary.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label cli-architecture tests/test_cli*.py tests/architecture`
- `uv run pyright propstore`
- `uv run lint-imports`

## Done means

- App/owner APIs accept typed domain requests, not CLI payload strings.
- CLI is the only layer that knows option syntax.
- Owner modules return reports/failures instead of printing or exiting.
- Package-wide gates enforce the boundary so new command families cannot drift back.
