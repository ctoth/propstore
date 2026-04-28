# WS-CM Closure Report

Workstream: WS-CM micropub canonical payload and Trusty URI identity
Closing commit: `526cf53b` (`WS-CM add closure sentinel`)
Spec status commit: `d0ebdda9`
Date: 2026-04-27

## Findings Closed

- D-7: micropublication artifact ids are content-derived from the full canonical micropub payload.
- D-29: canonical micropub payload and Trusty URI identity now have one prerequisite owner consumed by WS-C, WS-E, and WS-M.
- Codex re-review: no placeholder micropub hash path was added; the old `(source_id, claim_id)` production identity surface was deleted.

## Tests Written First

- `tests/test_micropub_identity_trusty_uri.py`: failed because `propstore.families.identity.micropubs` did not exist and finalization still emitted `ps:micropub:<truncated-hash>` ids.
- `tests/test_micropub_identity_not_logical_handle.py`: failed because the old source finalization identity surface existed and could not distinguish authored payload changes under the same source and claim handle.
- `tests/test_micropub_trusty_verification.py`: failed because no `verify_ni_uri` helper existed for checking the canonical payload bytes against the generated URI.
- `tests/test_workstream_cm_done.py`: added only after the identity, verification, docs, and acceptance gates were in place.

## Property-Based Tests

- `test_micropub_id_is_deterministic_for_same_canonical_payload` asserts generated equivalent canonical payloads produce the same `ni:///sha-256;...` id even when recursive identity fields differ.
- `test_micropub_canonical_payload_ignores_nonsemantic_claim_order` asserts non-semantic claim ordering does not change canonical bytes or identity.
- `test_generated_micropub_trusty_uri_verification_round_trips` asserts generated canonical bytes verify and mutated generated payload bytes fail verification.
- No WS-CM property tests were moved to successor workstreams.

## Commands And Logs

- Red gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM-red tests/test_micropub_identity_trusty_uri.py tests/test_micropub_identity_not_logical_handle.py tests/test_micropub_trusty_verification.py`; log `logs/test-runs/WS-CM-red-20260427-232300.log`.
- Implementation gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM-impl tests/test_micropub_identity_trusty_uri.py tests/test_micropub_identity_not_logical_handle.py tests/test_micropub_trusty_verification.py`; log `logs/test-runs/WS-CM-impl-20260427-232449.log`.
- Final targeted gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM-targeted tests/test_micropub_identity_trusty_uri.py tests/test_micropub_identity_not_logical_handle.py tests/test_micropub_trusty_verification.py`; log `logs/test-runs/WS-CM-targeted-20260427-232527.log`.
- Nearby sweep: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM-sweep tests/test_uri.py tests/test_micropublications_phase4.py tests/test_source_cli.py tests/test_verify_cli.py`; log `logs/test-runs/WS-CM-sweep-20260427-232616.log`.
- Exact workstream acceptance: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM tests/test_micropub_identity_trusty_uri.py tests/test_micropub_identity_not_logical_handle.py tests/test_micropub_trusty_verification.py tests/test_workstream_cm_done.py`; log `logs/test-runs/WS-CM-20260427-232718.log`.
- Full suite: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM-full`; log `logs/test-runs/WS-CM-full-20260427-232811.log`; result was `3029 passed, 1 failed`, with the only failure the pre-existing deleted `CLAUDE.md` docs-boundary test.
- Type gate: `uv run pyright propstore`; result `0 errors, 0 warnings, 0 informations`.
- Import contract gate: `uv run lint-imports`; result `Contracts: 4 kept, 0 broken`.

## Files Changed

- Production: `propstore/families/identity/micropubs.py`, `propstore/source/finalize.py`, `propstore/uri.py`.
- Tests: `tests/test_micropub_identity_trusty_uri.py`, `tests/test_micropub_identity_not_logical_handle.py`, `tests/test_micropub_trusty_verification.py`, `tests/test_workstream_cm_done.py`.
- Docs and tracking: `docs/gaps.md`, `reviews/2026-04-26-claude/workstreams/WS-CM-micropub-identity.md`, `reviews/2026-04-26-claude/workstreams/reports/WS-CM-closure.md`.

## Audits

- `rg -n -F "_stable_micropub_artifact_id(source_id, claim_id)" propstore tests` returned no matches.
- `rg -n -F "_stable_micropub_artifact_id" propstore tests` returned only the deletion assertion in `tests/test_micropub_identity_not_logical_handle.py`.
- `rg -n -F "ps:micropub:" propstore/source propstore/families/identity propstore/uri.py` returned no production source/family identity emitters.
- Placeholder/TODO identity search found only WS-CM spec prose describing the rejected placeholder path, not a production or test helper.

## Remaining Risk

No WS-CM finding is deferred. Broader provenance export and old `ni:///sha-1;...` provenance text remain owned by WS-M. Sidecar dedupe-shape behavior that consumes this identity remains owned by WS-C.

The residual full-suite failure is unrelated to WS-CM: `tests/test_repository_artifact_boundary_gates.py::test_current_docs_do_not_name_deleted_repo_storage_surface` fails because tracked `CLAUDE.md` is deleted in the current worktree. That failure was present before WS-CM execution and was not changed here.
