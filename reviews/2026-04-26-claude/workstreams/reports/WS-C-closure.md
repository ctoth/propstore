# WS-C Closure Report

Workstream: WS-C, Sidecar atomicity and SQLite discipline
Closed: 2026-04-28
Implementation close commit: `eedfbaa8`

## Findings Closed

- T1.4 / Codex #1: `materialize(force=False)` preflights conflicts before writes and preserves local edits on refusal.
- T1.6 / Claude A H2: promotion writes git first and mirrors blocked sidecar diagnostics after commit.
- Codex #3: micropublication sidecar dedupe consumes WS-CM payload-derived micropub ids.
- Codex #2: claim sidecar dedupe uses `(artifact_id, version_id)` discipline and link PK dedupe.
- T1.7 / Claude N HIGH-1: `build_repository` reports missing sidecars instead of returning silent zero counts.
- Codex #5: sidecar cache keys are derived from source revision, sidecar schema version, generated schema fingerprint, semantic pass versions, family contract versions, relevant dependency pins, and build-time config.
- Adjacent materialize cleanup race: cleanup now collects unlink candidates before deleting.

## TDD Evidence

- `tests/test_T1_4_materialize_atomicity.py` failed first because materialize wrote non-conflicting paths before raising on a later conflict. Green after commits `3b2ec607` and `4fc57df6`. Logs: `logs/test-runs/WS-C-T1-4-red-20260428-021035.log`, `logs/test-runs/WS-C-T1-4-green-20260428-021146.log`.
- `tests/test_promote_atomicity.py` failed first because promote lacked `PromotionResult` and sidecar diagnostics led git state. Green after commits `d01663c4` and `fea35828`. Logs: `logs/test-runs/WS-C-promote-red-20260428-021311.log`, `logs/test-runs/WS-C-promote-green-20260428-021528.log`.
- `tests/test_micropub_identity_dedupe_shape.py` failed first on the old false identity/dedupe contract. Green after commits `9de09633` and `6275a32b`. Logs: `logs/test-runs/WS-C-micropub-red-20260428-021655.log`, `logs/test-runs/WS-C-micropub-green-20260428-021757.log`.
- `tests/test_codex2_claim_dedupe_diverges_on_version.py` failed first because duplicate logical ids with different versions were silently first-writer-wins. Green after commits `6fb2a473`, `03c75dd9`, and `3c5daafd`. Logs: `logs/test-runs/WS-C-claim-dedupe-red-20260428-021940.log`, `logs/test-runs/WS-C-claim-dedupe-green-20260428-022045.log`.
- `tests/test_T1_7_build_repository_propagates_sidecar_errors.py` failed first because missing sidecars were swallowed. Green after commits `912aba09` and `6090cc07`. Logs: `logs/test-runs/WS-C-buildrepo-red-20260428-022246.log`, `logs/test-runs/WS-C-buildrepo-green-20260428-022405.log`.
- `tests/test_codex5_sidecar_cache_derived_invalidation.py` failed first because the cache key ignored derived build inputs; a second red tightened the pass-version and generated-schema requirements. Green after commits through `eedfbaa8`. Logs: `logs/test-runs/WS-C-cache-red-20260428-022639.log`, `logs/test-runs/WS-C-cache-green-20260428-022847.log`, `logs/test-runs/WS-C-cache-pass-version-red-20260428-023739.log`, `logs/test-runs/WS-C-cache-pass-version-green-20260428-024119.log`.
- `tests/test_materialize_clean_unlink_plan.py` failed first because cleanup still unlinked inside the `rglob()` loop. Green after commits `b0909d60` and `0bac2c19`. Logs: `logs/test-runs/WS-C-clean-red-20260428-022957.log`, `logs/test-runs/WS-C-clean-green-20260428-023036.log`.
- `tests/test_workstream_c_done.py` failed first while WS-C was still open. It gates this report, `docs/gaps.md`, the WS status line, and the INDEX row. Red log: `logs/test-runs/WS-C-sentinel-red-20260428-023134.log`.

## Property-Based Coverage

- WS-C includes a Hypothesis property gate in `tests/test_T1_4_materialize_atomicity.py::test_materialize_is_all_or_nothing_for_generated_local_edits`. It generates deleted/conflicting path combinations and asserts materialize is all-or-nothing.
- WS-Q-cas property gates are a hard WS-C dependency and were already closed in WS-Q-cas; WS-C acceptance reruns `tests/test_branch_head_cas_matrix.py` and `tests/test_cas_rejection_no_orphan_rows.py`.
- No WS-C property item was moved to a successor workstream.

## Files Changed

- `propstore/storage/snapshot.py`
- `propstore/source/promote.py`
- `propstore/app/sources.py`
- `propstore/sidecar/micropublications.py`
- `propstore/sidecar/claims.py`
- `propstore/compiler/workflows.py`
- `propstore/cli/compiler_cmds.py`
- `propstore/sidecar/build.py`
- `propstore/families/forms/passes.py`
- `propstore/families/concepts/passes.py`
- `propstore/families/contexts/passes.py`
- `propstore/families/claims/passes/__init__.py`
- `propstore/semantic_passes/types.py`
- WS-C test files listed above
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-C-sidecar-atomicity.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`

## Verification

- `uv run pyright propstore`: passed with 0 errors.
- `uv run lint-imports`: passed.
- Pre-close full suite: `3060 passed, 1 failed`; the single failure was the intentionally red WS-C sentinel before the closeout files were updated. Log: `logs/test-runs/WS-C-full-preclose-20260428-023350.log`.
- Final sentinel, targeted acceptance, and full-suite logs are recorded in the final closeout commit after those commands pass.

## Remaining Risks

- WS-C does not own Trusty URI identity construction; WS-CM owns that and is already closed.
- WS-C does not own concurrent branch-head CAS; WS-Q-cas owns that and is already closed.
- WS-C does not own read-only sidecar open policy; WS-B owns that and is already closed.
