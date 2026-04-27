# WS-01: Render policy and read-only boundaries

## Review findings covered

- Direct claim URLs return blocked/draft claim details under the default policy.
- Neighborhood routes leak hidden supporter/attacker IDs and edges.
- Concept pages disclose hidden claim counts and type distribution.
- Malformed concept FTS queries can escape as 500s.
- Sidecar query opens SQLite write-capable and enables WAL before `query_only`.

## Why this comes first

These are externally visible leaks and boundary violations. They can be fixed before schema or semantic work, and their tests will protect later web/app refactors from reintroducing visibility leaks.

## First failing tests

1. Add a web/app fixture with:
   - visible claim `V`
   - blocked or draft claim `B`
   - unique marker text on `B`
   - relation `B supports V`
   - both claims tied to the same concept

2. Prove direct claim default policy:
   - `GET /claim/B.json` without include flags must not return marker text.
   - Choose one target behavior and test it consistently:
     - preferred: `404` for default-hidden claims
     - acceptable: `403` with no claim payload
     - acceptable only if deliberate: redacted response with no statement/value/provenance

3. Prove neighborhood default policy:
   - `GET /claim/V/neighborhood.json` must not contain `B` in `moves.target_ids`, rows, nodes, edges, prose counts, or HTML.
   - Add the include flag case only after the default-hidden test fails for the right reason.

4. Prove concept default policy:
   - `GET /concept/<concept>.json` must report visible-only counts by default.
   - Hidden counts and blocked type distribution must appear only when include flags request them, or be removed entirely if the target design is no hidden-count disclosure.

5. Prove malformed FTS boundary:
   - Build a sidecar with concept FTS.
   - Request `/concepts.json?q=%22unterminated`.
   - Expected result: stable 400/domain error, not 500 or raw `sqlite3.OperationalError`.

6. Prove read-only sidecar query:
   - Copy a sidecar to a temp path without `-wal`/`-shm`.
   - Open through the sidecar query path with `SELECT 1`.
   - Assert no WAL/SHM files are created and sidecar mtime does not change.
   - Also verify the connection fails cleanly on a read-only filesystem/path if feasible.

## Production change sequence

1. Define one app-level visibility rule for entity reads:
   - `claim_view` must treat hidden under policy as not readable by default.
   - Do not rely on the HTML renderer to hide fields; the app report should not contain hidden content.

2. Filter relation surfaces before building neighborhood reports:
   - Load stances only where both endpoints are visible under the effective policy.
   - If include flags are enabled, the policy should explicitly produce the broader visible set.
   - Derive counts from filtered relations, not from raw world rows.

3. Make concept reports policy-relative:
   - Default `total_claim_count` should mean visible total, or rename/report hidden counts only under explicit include flags.
   - Do not compute blocked type distribution unless hidden content is part of the requested policy.

4. Add a typed app error for invalid FTS queries:
   - Catch SQLite FTS grammar errors inside `search_concepts` or the concept search owner module.
   - Map to a stable app exception that the web route already understands, or add it to expected web errors.

5. Split read-write and read-only sidecar connections:
   - Build/publish paths can keep WAL configuration.
   - Query/inspection paths should open SQLite in read-only URI mode and set `query_only` before user SQL.
   - Do not call shared connection setup that mutates journal mode from read-only code.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label render-policy tests/test_web*.py tests/test_*claim*view*.py`
  - Adjust file list to actual tests added.
- `uv run pyright propstore`
- `uv run lint-imports` if app/web module ownership changes.

## Done means

- Hidden default-policy claim details cannot be reached by direct URL, neighborhood relation, concept counts, JSON, or HTML.
- Sidecar query is demonstrably non-mutating.
- FTS syntax errors are user/domain errors, not server errors.
