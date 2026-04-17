# WS-Z-gates Phase 3 — Three Gate Refactors Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-03-gate-refactors.md`
Author: coder subagent

Converts three build-time data-blocking gates into render-time policy filters per axis-1 findings 3.1 (raw-id quarantine), 3.2 (draft visibility), and 3.3 (partial source promotion).

## Commits

Six commits, one red + one green per gate. Commit order: gate 1 first (diagnostics-attached pattern sets the template reused by gates 2 and 3).

| SHA | Gate | Phase | Message |
|-----|------|-------|---------|
| `34d2be2` | 1 | red | `test(sidecar): raw-id-broken claims quarantine instead of aborting (failing)` |
| `67fccc1` | 1 | green | `feat(sidecar): quarantine raw-id-broken claims with diagnostics row instead of aborting build` |
| `dd78dfd` | 2 | red | `test(compiler,sidecar): draft claims traverse binding and ingest with stage='draft' (failing)` |
| `5bb948d` | 2 | green | `feat(compiler,sidecar): draft claim files ingest with stage='draft' instead of dropping` |
| `d5b585e` | 3 | red | `test(source): promote partial allows valid + blocks invalid items with sidecar mirror (failing)` |
| `8923b9f` | 3 | green | `feat(source,cli): promote source branches partially; mirror blocked claims into sidecar` |

No refactor-only commits were needed — the green commits land cohesive changes (helper extraction happens in the same commit as the primary behavior change).

## Final test status

```
====================== 2535 passed in 547.23s (0:09:07) =======================
```

(Full-suite run, `--timeout=180`.) Phase 2 baseline was 2529. Net delta: **+6 tests**:

- `TestClaimStanceTable::test_raw_inline_stance_targets_are_quarantined_not_rejected` — inversion of the prior `test_raw_inline_stance_targets_are_rejected_at_compile_boundary` (net 0 in count).
- `TestClaimStanceTable::test_raw_id_claim_quarantine_preserves_other_claims` — new (+1).
- `TestDraftArtifactBoundary::test_draft_claim_file_traverses_binding_with_info_diagnostic` — inversion of `test_draft_claim_file_rejected_from_final_validation` (net 0).
- `TestDraftArtifactBoundary::test_draft_claim_file_surfaces_in_compilation_bundle` — new (+1).
- `TestDraftStageIngestion::test_draft_and_final_claims_both_populate` — new (+1).
- `test_promote_source_branch_partial_allows_valid_claims_blocks_invalid` — new (+1).
- `test_promote_source_branch_strict_flag_raises_on_partial` — new (+1).
- `test_promote_source_branch_re_promote_after_fix` — new (+1).

6 net new + 2 inversions = consistent with 2535 − 2529 = 6.

### Flake flag

`tests/test_aspic_bridge.py::TestBridgeRationalityPostulates::test_direct_consistency` (a Hypothesis property test with `@settings(deadline=None)`) times out on full-suite runs at `--timeout=60` and occasionally `--timeout=180`, but passes in `~2s` in isolation and in `~17s` as a targeted file run at `--timeout=600`. Phase 2's report flagged the same Hypothesis-deadline-style flake for `test_form_dimensions.py`; the current occurrence is a different test but the same general pattern — Hypothesis search state on Windows occasionally pushes a single shrink over the pytest thread timeout. Not caused by phase-3 changes (the aspic bridge does not read or write `claim_core.build_status`/`stage`/`promotion_status`, nor does it read `build_diagnostics`). Flagged for CI triage.

## Surface area (`git diff --stat 34d2be2^..HEAD -- propstore/ tests/`)

```
 propstore/_resources/schemas/claim.schema.json | 350 ++++++++++++-------------
 propstore/cli/source.py                        |  57 +++-
 propstore/compiler/passes.py                   |  20 +-
 propstore/sidecar/build.py                     | 140 +++++++++-
 propstore/sidecar/claim_utils.py               |  18 +-
 propstore/sidecar/claims.py                    | 126 ++++++++-
 propstore/source/promote.py                    | 330 ++++++++++++++++++++++-
 tests/test_build_sidecar.py                    | 240 ++++++++++++++++-
 tests/test_source_promotion_alignment.py       | 316 ++++++++++++++++++++++
 tests/test_validate_claims.py                  |  84 +++++-
 10 files changed, 1462 insertions(+), 219 deletions(-)
```

Note: `claim.schema.json` shows 350/350 churn because of a whole-file reformat (property key reordering). The semantic change is a single-line description update at the `stage` property (see Gate 2 below).

## Gate 1 — Raw-id quarantine (`sidecar/build.py`)

**Behavior before:** `_raise_on_raw_id_claim_inputs` at `propstore/sidecar/build.py:75-82` walked the compile bundle's diagnostics and raised `ValueError` on any diagnostic whose message contained `"raw 'id' input"`. The entire sidecar build aborted; every other valid claim in the knowledge tree became unqueryable until a human fixed the offender.

**Behavior after:** `_collect_raw_id_diagnostics` replaces the raise with typed `RawIdQuarantineRecord` output. Each record carries:

- `filename` — the claim-file stem.
- `source_paper` — the paper slug from the file's `source.paper`.
- `raw_id` — the offending claim's `id` field.
- `seq` — the within-file sequence number of the offending claim.
- `synthetic_id` — `quarantine:raw_id:<sha256(filename|raw_id|seq)[:32]>`.
- `message` — the exact diagnostic text preserved from `compiler/passes.py`.

`populate_raw_id_quarantine_records` writes a stub row into `claim_core` with `id=<synthetic>`, `build_status='blocked'`, and a companion row into `build_diagnostics` with `diagnostic_kind='raw_id_input'`, `blocking=1`, `severity='error'`, plus `detail_json` carrying the synthetic-id basis (scheme + filename + raw_id + seq + prefix) per the honest-ignorance discipline: the id is synthetic, and the storage must say so.

The per-file compile diagnostic at `compiler/passes.py:326-339` was left alone — the build-side quarantine reads its emission but does not depend on it structurally; the test at `tests/test_claim_compiler.py:233` continues to pass unchanged.

## Gate 2 — Draft visibility (`compiler/passes.py`)

**Behavior before:** The block at `propstore/compiler/passes.py:289-307` substituted `SemanticClaimFile(..., claims=tuple())` for any file with `stage='draft'` and emitted a `level='error'` diagnostic. Draft claims never reached the sidecar; users asking "what drafts am I working on?" got nothing.

**Behavior after:** Early-return deleted. Drafts traverse the normal binding path. The diagnostic is retained but downgraded to `level='info'` with a new message ("claim file is marked stage='draft'; render policy hides drafts by default") that describes *what will happen at render time* rather than *why the file is being refused*.

The populator in `propstore/sidecar/claims.py:populate_claims` now threads the file-level stage marker onto every `claim_core` row by building a `{filename: stage}` map from `claim_bundle.normalized_claim_files` and attaching it to each row before `insert_claim_row`. `insert_claim_row` in `propstore/sidecar/claim_utils.py` grew three new columns in its `INSERT` list — `build_status`, `stage`, `promotion_status` — with schema-default fallback semantics (`'ingested'`, `NULL`, `NULL`).

Schema description at `propstore/_resources/schemas/claim.schema.json` updated in the same commit from:

> Optional file-level processing stage marker used to reject draft claim files from the canonical validation path.

to:

> Optional file-level processing stage marker used for render-policy filtering (drafts hidden by default).

Per the "docs never lead code" discipline (rule 2): the schema description changed in the same commit that changed the code.

## Gate 3 — Partial promotion (`source/promote.py`, `cli/source.py`)

**Behavior before:** `promote_source_branch` at `propstore/source/promote.py:186-188` raised `ValueError` whenever the finalize report's `status != "ready"`. A single broken stance reference kept every other valid claim on the source branch invisible from the primary-branch sidecar.

**Behavior after:** The all-or-nothing gate is replaced with a per-claim blocked-set computation (`_compute_blocked_claim_artifact_ids`). A claim is blocked if:

1. Its `artifact_id` is not a canonical string.
2. It has a stance whose `source_claim` doesn't resolve on the source index, or whose `target` doesn't resolve on either the source or primary resolvers.
3. It's the `conclusion` (or a `premise`) of a justification whose referenced items don't all resolve.

`promote_source_branch` iterates per-claim/stance/justification, filters to the valid subset, and promotes that subset via the existing `attach_source_artifact_codes` + `transaction.save` path. Blocked claims stay on the source branch.

After the artifact transaction commits, `_write_promotion_blocked_sidecar_rows` mirrors the blocked claims into the primary-branch sidecar (`repo.sidecar_path`) as `claim_core` rows with:

- `id=<blocked claim's artifact_id>`
- `branch=<source_branch_name>`
- `promotion_status='blocked'`
- `type='promotion_blocked'` (synthetic type — keeps the row distinguishable from a normally-ingested row)

and one `build_diagnostics` row per reason with:

- `diagnostic_kind='promotion_blocked'`
- `blocking=1`
- `source_kind='claim'`
- `source_ref=<source_branch>:<artifact_id>`
- `detail_json={"reason_kind": ..., "source_branch": ...}`

The mirror write is conditional on `repo.sidecar_path.exists()` — no-op if the sidecar hasn't been built yet. The CLI build flow builds the sidecar at repo init, so the normal user path hits the write.

**`--strict` flag:** Preserves the old abort-on-any-error behavior for explicit opt-in. Per the prompt: this is the *only* backward-compat shim in the phase. Every other gate is ripped out.

**CLI output (`pks source promote`):**
- Clean success → `Promoted <branch> to master`
- Partial success → `Promoted N of M claims to master (K blocked; see build_diagnostics).`
- All blocked (or `--strict`-triggered finalize block) → `ValueError` → ClickException → exit code 1.

## Deviations from the scout's proposed shape

1. **Gate 3 mirror-write location.** Scout B.3 proposed "a `claim_core` mirror row with `promotion_status='blocked'`, `branch=<source_branch_name>`" without specifying *when* in the promote flow the write happens. I placed it **after** the artifact transaction commit and **conditionally** on sidecar existence. Rationale: the artifact transaction commits to the primary branch's git refs; the sidecar is a derivative artifact. Writing the mirror rows into the sidecar before the transaction commit would leave the repo inconsistent if the commit fails. Writing unconditionally (without the `.exists()` guard) would force `promote_source_branch` to create the sidecar on-demand, which is out of scope for this phase's scope of gate removal.

2. **Gate 3 blocked-claim identification.** The scout said `finalize_source_branch` "already produces `claim_reference_errors`, etc." — these flat lists conflate the error type with the offending reference. For a stance with a broken target, `stance_reference_errors` contains the *target* string (`"missing_source:claim_zzz"`), not the stance's source_claim (which is the claim we need to block from promotion). I re-derived the blocked set by re-walking stances/justifications per-item against the source index and resolver, rather than consuming the flat report lists. This preserves the `finalize` report shape unchanged and avoids a second pass of join-logic on strings.

3. **Gate 3 test-fixture shape.** The prompt suggested asserting on `source_local_id` to correlate promoted claims. Primary-branch `ClaimDocument` strips `source_local_id` during promote (via `normalize_canonical_claim_payload(..., strip_source_local=True)` at `propstore/source/promote.py:524`). I correlated on `statement` text instead. The test still proves the identity-preservation property.

4. **Gate 2 test-fixture shape.** The prompt's draft tests used a raw-id claim (`id: "draft_claim_1"`, no `artifact_id`). With gate 1 in effect the raw-id claim skip at `compiler/passes.py:326-339` still fires, causing the claim to be skipped even when draft files traverse the path. I switched the fixture to `make_observation_claim(...)` so the claim canonicalizes properly and the draft-visibility property is actually being tested.

## Flags raised during work

1. **Pre-existing aspic_bridge flake (same pattern as phase 2).** Full-suite runs with `--timeout=120` or `--timeout=180` can time out on `test_direct_consistency`. In isolation the test passes in 2s; as a targeted file run at `--timeout=600` the whole file (51 tests) passes in 17s. Not caused by phase-3 changes. Phase 2's report flagged the same Hypothesis-state-dependent timing pattern for `test_form_dimensions.py`. Suggest CI pinning `deadline=None` + per-class `--timeout=600` for these property tests.

2. **`_DEFAULT_BASE_RATES` in `calibrate.py` (axis-1 finding 2.1) unchanged.** Not in scope for this phase but observed while reading around promote; fairness call-out.

3. **Event-semantics commit (`f25817d`) landed between gate-1 red and gate-1 green on master.** Unrelated to WS-Z-gates. Phase-3 diff-stat `34d2be2^..HEAD` is clean with respect to `propstore/` and `tests/` paths — no cross-contamination with the event-semantics docs work.

## Out of scope (deferred to later phases)

- `RenderPolicy` extension with `include_drafts`, `include_blocked`, `show_quarantined` boolean fields — phase 4.
- CLI filter flags on `pks world status`/`pks world query`/etc. — phase 4.
- `pks source status` subcommand listing blocked mirror rows — phase 4.
- `docs/gaps.md` closure records — phase 5.
- `CLAUDE.md` "Known Limitations" updates — phase 5.
- Deduplication of the two synthetic-id stub schemes (raw-id quarantine vs promotion-blocked mirror both write minimal `claim_core` rows via direct SQL; could factor into a shared helper). Cosmetic; deferred.

## Citation-as-claim discipline

Per discipline rule 1: citations in docstrings must be backed by tests. The new module docstrings (`propstore/sidecar/build.py`, `propstore/sidecar/claims.py`, `propstore/source/promote.py`) and function docstrings (`_collect_raw_id_diagnostics`, `populate_raw_id_quarantine_records`, `promote_source_branch`, `_compute_blocked_claim_artifact_ids`, `_write_promotion_blocked_sidecar_rows`, `populate_claims`, `insert_claim_row`) all cite `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md` plus the specific axis-1 finding number (3.1, 3.2, or 3.3). Each is backed by at least one of the new or inverted tests enumerated under "Final test status".

## File path reference (absolute paths)

- Source:
  - `C:\Users\Q\code\propstore\propstore\sidecar\build.py`
  - `C:\Users\Q\code\propstore\propstore\sidecar\claims.py`
  - `C:\Users\Q\code\propstore\propstore\sidecar\claim_utils.py`
  - `C:\Users\Q\code\propstore\propstore\compiler\passes.py`
  - `C:\Users\Q\code\propstore\propstore\source\promote.py`
  - `C:\Users\Q\code\propstore\propstore\cli\source.py`
  - `C:\Users\Q\code\propstore\propstore\_resources\schemas\claim.schema.json`
- Tests:
  - `C:\Users\Q\code\propstore\tests\test_build_sidecar.py`
  - `C:\Users\Q\code\propstore\tests\test_validate_claims.py`
  - `C:\Users\Q\code\propstore\tests\test_source_promotion_alignment.py`
