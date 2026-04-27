# WS-03: Storage, sidecar identity, and atomicity

## Review findings covered

- `materialize` partially overwrites files before reporting conflicts.
- Duplicate claim handling assumes artifact IDs are content-derived when they are logical-handle-derived.
- Duplicate claim child rows can still violate sidecar constraints.
- Micropublication IDs are not content-derived while sidecar dedupe assumes they are.
- Sidecar cache hash ignores compiler/pass/family semantic versions.
- Import/finalize/promote commits are not bound to branch heads read during planning.
- Embedding model keys collide after lossy sanitization.
- Short 16-hex identity/content hashes are used on canonical identities and worldline hashes.

## Dependencies

- Depends on `ws-02-schema-and-test-infrastructure.md`.
- Can run partly in parallel with `ws-04`, but do not merge sidecar identity changes before tests use production schema.

## First failing tests

1. Materialize atomicity:
   - Build a repo snapshot with at least two semantic files.
   - Locally modify one destination file to conflict.
   - Run `materialize(force=False)`.
   - Assert no other destination file was overwritten.
   - Assert the conflict report names the conflicting path.

2. Claim logical/content collision:
   - Create two claim rows/files with the same logical ID/artifact ID but different content/version IDs.
   - Build sidecar.
   - Expected: hard version-conflict diagnostic, not first-writer-wins.

3. Duplicate identical claim rows:
   - Create the known duplicate input with concept links.
   - Expected: idempotent parent and child rows, no PK violation.
   - This must run against production schema, not a hand-written fixture schema.

4. Micropublication identity:
   - Same `source_id` and `claim_id`, changed evidence/context/provenance payload.
   - Expected: either different micropub artifact ID if content-derived, or same logical ID plus distinct `version_id` with hard conflict on divergent duplicate sidecar rows.

5. Branch-head compare-and-swap:
   - For repository import, source finalize, and promote:
     - plan from branch head `H1`
     - mutate target branch to `H2`
     - attempt commit using stale plan
     - expected: stale-head failure, no stale deletes/promotions committed.

6. Sidecar cache semantic invalidation:
   - Change a compiler/pass/family contract version marker without changing source revision.
   - Expected: build does not reuse existing `.hash`.
   - The test can monkeypatch a semantic build version constant if a durable version surface is introduced first.

7. Embedding model key collision:
   - Use model names `a/b` and `a-b` or equivalent collision pair.
   - Expected: distinct model records/vector tables or hard collision error before overwrite.

8. Hash length policy:
   - Add a policy test that canonical identity/content hashes use full SHA-256 or a project-approved collision budget.
   - If short handles remain for display, assert they are display-only and never database/content identity.

## Production change sequence

1. `materialize`:
   - Split conflict detection from writes.
   - Collect all conflicts first.
   - If any conflict and not forced, raise before writing.
   - Then write files and optionally clean.

2. Branch mutations:
   - Thread `expected_head` through repository import, source finalize, and promote.
   - Use the merge path pattern as the target: capture read head, pass to transact/commit, fail on mismatch.

3. Claim identity:
   - Make names explicit:
     - logical artifact ID
     - content version ID
   - Delete comments and code paths that call logical artifact IDs content-derived.
   - On same logical ID/different version/content, emit a typed build conflict.
   - On same logical ID/same version/content, dedupe parent and child rows idempotently.

4. Micropublication identity:
   - Pick one target architecture:
     - content-derived micropub artifact IDs, or
     - stable logical micropub IDs plus required version/content conflict checks.
   - Update sidecar schema/insertion to store enough version information to enforce the target.
   - Delete first-writer-wins dedupe for divergent content.

5. Sidecar cache key:
   - Introduce a semantic compiler/build version surface covering schema, passes, family contracts, and dependency interpretation inputs.
   - Include it in `_sidecar_content_hash`.

6. Embeddings:
   - Replace lossy sanitized keys with collision-free identifiers.
   - Either hash the full model name for table suffixes or store a generated model ID.
   - Keep original model name as data, not as SQL identifier.

7. Hash policy:
   - Replace production identity hashes that use `hexdigest()[:16]` where collision resistance matters.
   - If short IDs are required for readability, derive them as labels from full IDs and detect ambiguity.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label storage-identity tests/test_git_backend.py tests/test_import_repo.py tests/test_source_relations.py tests/test_build_sidecar.py`
  - Add new focused tests for materialize, duplicate claim, micropub identity, CAS, embeddings, and cache invalidation.
- `uv run pyright propstore`
- `uv run lint-imports` if storage/sidecar ownership imports change.

## Done means

- No refused materialize leaves partial writes.
- Branch mutations fail on stale planning heads.
- Logical identity and content identity are separate, enforced surfaces.
- Sidecar cache reuse is invalidated by semantic compiler changes.
- Embedding table/status identity cannot collide through model-name punctuation.
