# WS-B Closure Report

Workstream: WS-B render policy and web data leak
Closing commit: `bb0bf7fe` (`WS-B close sentinel test`)
Spec status commit: `1fbc36de`
Date: 2026-04-27

## Findings Closed

- T1.1 / Codex #8: direct blocked claim views now hard-fail before report construction and render a generic 404.
- T1.2 / Codex #9: claim-neighborhood focus and edge queries now apply render policy before graph construction.
- T1.3 / Codex #10: concept reports default to policy-relative claim totals and do not expose hidden counts unless the policy explicitly includes blocked claims.
- T1.5 / Codex #4: sidecar query paths and `WorldModel` open SQLite through a read-only `mode=ro` URI and no longer issue write pragmas.
- T1.8: web float parameters reject non-finite, negative, and out-of-range query values at the request boundary.
- T1.9: `pks web --host 0.0.0.0` and other non-loopback binds require explicit `--insecure`; the insecure path emits a warning.
- Codex #11: malformed concept FTS queries now raise `ConceptSearchSyntaxError` and map to HTTP 400 instead of leaking a 500 traceback.

## Tests Written First

- `tests/test_render_policy_direct_claim.py`: proved blocked direct claim access returned claim payloads instead of hard-failing.
- `tests/test_render_policy_neighborhood.py`: proved blocked focus claims and blocked relationship edges were included in neighborhood reports.
- `tests/test_render_policy_concepts.py`: proved default concept reports exposed all-claim and hidden-claim counts.
- `tests/test_concept_fts_malformed_query.py`: proved malformed FTS input raised raw SQLite operational errors through the web layer.
- `tests/test_sidecar_query_read_only.py`: proved read paths could mutate the sidecar or open it with writable pragmas.
- `tests/test_web_request_float_boundary.py`: proved non-finite and invalid render-policy floats were accepted.
- `tests/test_pks_web_insecure_flag.py`: proved public web binds required no explicit insecure acknowledgement.
- `tests/test_workstream_ws_b_closure.py`: closure sentinel stayed xfailed until all WS-B evidence files and gates were present.

## Property-Based Tests

- Added malformed concept FTS Hypothesis coverage in `tests/test_concept_fts_malformed_query.py`; generated malformed query strings are asserted to become typed syntax failures, and valid smoke queries continue to return typed results.
- Added render-policy float boundary Hypothesis coverage in `tests/test_web_request_float_boundary.py`; generated finite values are checked against the accepted interval contracts and non-finite values are rejected.
- No WS-B property tests were moved to successor workstreams.

## Commands And Logs

- Red gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-red ...`; log `logs/test-runs/WS-B-red-20260427-223956.log`.
- Targeted green with closure sentinel still xfailed: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-targeted-2 ...`; log `logs/test-runs/WS-B-targeted-2-20260427-224749.log`.
- Exact WS-B acceptance after sentinel close: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B ...`; log `logs/test-runs/WS-B-20260427-224955.log`.
- Web sweep first exposed stale error-page assertions: log `logs/test-runs/WS-B-web-sweep-20260427-225037.log`.
- Web sweep after assertion updates: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-web-sweep-2 ...`; log `logs/test-runs/WS-B-web-sweep-2-20260427-225148.log`.
- Focused stale-test fixes: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-failure-fixes ...`; log `logs/test-runs/WS-B-failure-fixes-20260427-225551.log`.
- Final exact WS-B targeted gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-final-targeted ...`; log `logs/test-runs/WS-B-final-targeted-20260427-225610.log`.
- Full suite: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B-full-2`; log `logs/test-runs/WS-B-full-2-20260427-225655.log`; result was `3020 passed, 1 failed`, with the only failure the pre-existing deleted `CLAUDE.md` docs-boundary test.
- Type gate: `uv run pyright propstore`; result `0 errors, 0 warnings, 0 informations`.
- Import contract gate: `uv run lint-imports`; result `Contracts: 4 kept, 0 broken`.

## Files Changed

- Production: `propstore/app/claim_views.py`, `propstore/app/concepts/__init__.py`, `propstore/app/concepts/display.py`, `propstore/app/concept_views.py`, `propstore/app/neighborhoods.py`, `propstore/cli/web.py`, `propstore/sidecar/query.py`, `propstore/sidecar/sqlite.py`, `propstore/web/html.py`, `propstore/web/requests.py`, `propstore/web/routing.py`, `propstore/world/model.py`.
- Tests: `tests/test_concept_fts_malformed_query.py`, `tests/test_concept_search.py`, `tests/test_concept_view_policy_counts.py`, `tests/test_concept_views.py`, `tests/test_pks_web_insecure_flag.py`, `tests/test_render_policy_concepts.py`, `tests/test_render_policy_direct_claim.py`, `tests/test_render_policy_neighborhood.py`, `tests/test_sidecar_query_read_only.py`, `tests/test_web_error_pages.py`, `tests/test_web_request_float_boundary.py`, `tests/test_workstream_ws_b_closure.py`.
- Docs and tracking: `docs/gaps.md`, `docs/render-policy.md`, `reviews/2026-04-26-claude/workstreams/WS-B-render-policy.md`, `reviews/2026-04-26-claude/workstreams/reports/WS-B-closure.md`.

## Audits

- `rg -n -F "all_claim_stances" propstore/app propstore/web` returned no app/web callers.
- `rg -n -F "connect_sidecar(" propstore/sidecar/query.py` returned no writable sidecar query opens.
- `rg -n -F "ClaimViewBlockedError" propstore/web/routing.py` confirmed the web mapping to 404.
- `rg -n -F "ConceptSearchSyntaxError" propstore/web/routing.py` confirmed the web mapping to 400.
- `rg -n -i "redacted|redaction" propstore/web propstore/app/claim_views.py` returned no redacted-page production path.
- `rg -n -i "render policy|blocked claim|sidecar.*read|fts|float|0\\.0\\.0\\.0|public-bind|public bind|web" docs/gaps.md` showed WS-B items only in the closed section, plus the unrelated `pks world chain` lifecycle-policy gap.

## Remaining Risk

No WS-B finding is deferred. The residual full-suite failure is unrelated to WS-B: `tests/test_repository_artifact_boundary_gates.py::test_current_docs_do_not_name_deleted_repo_storage_surface` fails because tracked `CLAUDE.md` is deleted in the current worktree. That failure was present before WS-B closure and was not changed here.
