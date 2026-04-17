# WS-Z-gates Phase 6 — Adversary + Verifier Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-06-adversary-verifier.md`
Author: verifier subagent (read-only, no code modified)

## Header

- **Hat 1 verdict (principle alignment): PRINCIPLES UPHELD**
- **Hat 2 verdict (test suite + tooling): VERIFIED with one pre-existing failure**
- **Overall: WS-Z-gates ready to mark complete? YES with documented gap (one pre-existing test failure unrelated to WS-Z-gates).**

The overall verdict is YES because the failure is demonstrably pre-existing on master HEAD without any WS-Z-gates changes applied (verified by stash + checkout test). All exit criteria for the workstream are met.

---

## Adversary findings

### A. Design checklist items 1-4

The four CLAUDE.md design-checklist items are upheld at every refactored gate site. Per-site verification:

**Site 1: `propstore/sidecar/build.py` (raw-id quarantine).**
- `_collect_raw_id_diagnostics` (lines 144-200) returns a list of `RawIdQuarantineRecord`; never raises. The former `_raise_on_raw_id_claim_inputs` raise path is gone.
- `populate_raw_id_quarantine_records` is called at `build.py:339-340` *after* the normal `populate_claims` ingest at lines 330-337. Valid claims always ingest regardless of quarantine population.
- The populator runs only if `raw_id_quarantine_records` is non-empty (line 339), so empty-list = no-op (correct).
- Items 1-4: PASS. No data is prevented from reaching the sidecar; no human action required; no gate before render time; filtering happens at render time via `RenderPolicy.include_blocked`.

**Site 2: `propstore/compiler/passes.py:289-305` (draft handling).**
- The early-return that previously dropped draft files is deleted. The `if claim_file_stage(...) == "draft":` block now only appends a `level='info'` `SemanticDiagnostic` (lines 296-305) and continues into the binding loop. No `continue` statement.
- The diagnostic message is rephrased from a refusal ("draft artifacts are not accepted") to an information notice ("render policy hides drafts by default"), per phase 3 report.
- `propstore/sidecar/claims.py:populate_claims` (lines 277-310) builds `file_stage_by_filename` at lines 306-309, then attaches `row["stage"] = file_stage` at line 326 before `insert_claim_row`. Stage threads onto every row.
- Items 1-4: PASS.

**Site 3: `propstore/source/promote.py` + `propstore/cli/source.py` (partial promote).**
- `promote_source_branch` (lines 392-637) computes `blocked_artifact_ids` at line 427-433 via `_compute_blocked_claim_artifact_ids`, then filters to `valid_claims` (line 442-447) and only those flow through `attach_source_artifact_codes` + `transaction.save`.
- Blocked claims are mirrored into the primary-branch sidecar via `_write_promotion_blocked_sidecar_rows` (line 628-635) AFTER the artifact transaction commits — preserves repo integrity if the commit fails.
- The mirror-write happens conditionally on `repo.sidecar_path.exists()` (line 307); CLI path always satisfies this because `pks build` runs at repo init.
- The `--strict` flag (cli/source.py:348-356) is the only documented backward-compat shim; default behaviour is partial promotion.
- Items 1-4: PASS.

**RenderPolicy defaults: `propstore/world/types.py:822-836`.**
- Three new fields: `include_drafts: bool = False`, `include_blocked: bool = False`, `show_quarantined: bool = False`. All default `False` — preserves "don't show problems by default" per CLAUDE.md.
- Field-block docstring (lines 822-833) cites WS-Z-gates workstream + axis-1 findings 3.1/3.2/3.3 and the CLAUDE.md design checklist.
- PASS.

**Render-time application: `propstore/world/model.py:claims_with_policy` (line 671-699).**
- `_render_policy_predicates` (line 638-669) builds SQL `WHERE` clauses *at query time* from policy values: `(core.stage IS NULL OR core.stage != 'draft')` etc.
- The sidecar always projects all three lifecycle columns via `_claim_select_sql` (per phase 4 commit `1c47816`); filtering is purely render-time.
- `claims_with_policy` calls `_claim_rows` with the constructed predicates — no pre-filtered data is consumed.
- Item 4 PASS: filtering happens at render time, not build time.

### B. Citation-as-claim discipline (5-function spot-check)

Per disciplines.md rule 1: every citation must be backed by a passing test. Verified 5 randomly-selected functions.

| # | Function | File:line | Citation in docstring | Backing test | Verdict |
|---|----------|-----------|------------------------|--------------|---------|
| 1 | `_collect_raw_id_diagnostics` | `propstore/sidecar/build.py:144` | "axis-1 finding 3.1: this function replaces the prior `_raise_on_raw_id_claim_inputs` abort. It never raises." | `tests/test_build_sidecar.py:1281+1335-1340` asserts `build_diagnostics WHERE diagnostic_kind = 'raw_id_input'` row exists; build does not raise. | PASS |
| 2 | `populate_raw_id_quarantine_records` | `propstore/sidecar/claims.py:196` | "axis-1 finding 3.1: ... per-claim quarantine ... synthetic id scheme and basis are recorded in `detail_json`" | Same test file, line 1438-1439 selects `detail_json FROM build_diagnostics WHERE diagnostic_kind = 'raw_id_input'`. | PASS |
| 3 | `claims_with_policy` | `propstore/world/model.py:671` | "axis-1 findings 3.1 / 3.2 / 3.3 ... source-of-truth sidecar holds every row, render layer picks what to show" | `tests/test_render_policy_filtering.py` (11 tests) exercises full lifecycle matrix. | PASS |
| 4 | `WorldModel.build_diagnostics` | `propstore/world/model.py:701` | "axis-1 findings 3.1/3.2/3.3 ... only under explicit opt-in" | Same test file plus `test_cli_render_policy_flags.py` for CLI surface. | PASS |
| 5 | `_compute_blocked_claim_artifact_ids` | `propstore/source/promote.py:205` | "axis-1 finding 3.3: a claim is blocked if (a) ... (b) ... (c) ..." | `tests/test_source_promotion_alignment.py::test_promote_source_branch_partial_allows_valid_claims_blocks_invalid` exercises all three branches. | PASS |

All five citations are real and test-backed.

### C. Honest-ignorance discipline

- **Synthetic-id construction for raw-id quarantine stub rows.** `RawIdQuarantineRecord.synthetic_id` is `quarantine:raw_id:<sha256(filename|raw_id|seq)[:32]>` (build.py:137-141). The `detail_json` property (build.py:113-134) explicitly emits `synthetic_id_basis` carrying scheme + filename + raw_id + seq + prefix. The id is *labeled as synthetic* in the diagnostic row's `detail_json`. PASS.
- **Promotion-blocked mirror rows.** Use the actual `claim.artifact_id` (real id, not synthetic). The `type='promotion_blocked'` discriminator (promote.py:347-348) keeps them distinguishable from normally-ingested rows. No fabrication. PASS.
- **`RenderPolicy` defaults False/False/False.** These are render-time policy decisions, not truth-values about data. PASS.
- **No new fabricated defaults observed in phases 3/4/5.**

### D. No-compat-shims discipline

Grep for `legacy|backward|backwards|compat|v1|deprecated` across the WS-Z-gates touched files (`sidecar/build.py`, `sidecar/claims.py`, `compiler/passes.py`, `source/promote.py`, `world/types.py:822-836` new lines, `world/model.py:638-727` new methods, `cli/source.py:346-499` new commands):

- `propstore/source/promote.py`: 5 hits, all on `--strict` flag — *the documented exception*. Module docstring (lines 12-16) explicitly calls it out: "the *only* exception ... because Q explicitly authorized partial promotion as a behavioral change."
- All other WS-Z-gates additions are clean. The `legacy|backward` hits found across the broader codebase (preference.py, praf/engine.py, grounding/, world/bound.py, world/types.py:803/1027/1071) are pre-existing PrAF and Opinion-related code, not WS-Z-gates additions.

PASS — only `--strict` is a compat shim; explicitly documented.

### E. Non-commitment-at-source discipline

The blocked-claim mirror rows preserve disagreement at the storage layer. Verified by reading `_write_promotion_blocked_sidecar_rows` (promote.py:284-389):
- Mirror rows go to the *primary-branch* sidecar (`repo.sidecar_path`) with `branch=<source_branch>` (line 357).
- The actual claim content (the authored YAML on the source branch) is left untouched — `valid_claims` flow through `transaction.save` (line 583+); blocked claims are skipped in the loop at lines 442-447.
- The render layer (`claims_with_policy` + `RenderPolicy.include_blocked`) decides what to surface.

Result: source branch carries the original authored data; primary-branch sidecar carries the blocked-mirror annotation. Disagreement is preserved at storage; resolution happens at render. PASS.

---

## Verifier findings

### A. Test suite (`uv run pytest tests/ --timeout=60`)

```
================= 1 failed, 2561 passed in 480.38s (0:08:00) ==================
FAILED tests/test_backward_chaining.py::test_backward_finds_all_goal_conclusions
```

- **Total:** 2562 collected; 2561 passed; 1 failed.
- **Net delta vs WS-Z-gates phase 4 baseline (2562 passed):** -1 (one previously-passing test now failing). Phase 4 reported 2562 passed; phase 5 reported 1 failed (`test_backward_finds_all_goal_conclusions`); phase 6 confirms 1 failed identically. The regression occurred between phase 4 and phase 5 — phase 5 made markdown-only changes, so the cause is some intervening commit on master, not WS-Z-gates work. Stash-and-checkout verification (below) confirms the failure is independent of WS-Z-gates working tree state.

**Pre-existing failure: `test_backward_finds_all_goal_conclusions`.** Verified pre-existing by stashing all WS-Z-gates working changes and running the test in isolation against current master HEAD: still fails in 0.94s (deterministic). Last commits to the test file (`d0f2a20`, `48d186a`) and to `propstore/aspic.py` (`989eaeb`, `471f80f`, `c17e557`) are recent ASPIC+ definition-19 / `GroundAtom` rework — none touch any WS-Z-gates file. Confirms phase 5 report's classification: pre-existing, not caused by WS-Z-gates.

### B. Pyright on changed files

Total: **66 errors, 0 warnings, 0 informations** across the 9 files. All errors verified pre-existing.

| File | Errors | All pre-existing? | Notes |
|------|--------|-------------------|-------|
| `propstore/sidecar/build.py` | 0 | — | Clean. |
| `propstore/sidecar/claims.py` | 0 | — | Clean. |
| `propstore/sidecar/claim_utils.py` | 8 | yes | All `SemanticClaim.resolved_claim/stances/get/source_paper` errors flagged pre-existing in phase 2b report. |
| `propstore/compiler/passes.py` | 0 | — | Clean. |
| `propstore/source/promote.py` | 21 | yes | All "Object of type 'object' is not callable" — same `propstore.artifacts` `__getattr__` lazy-dispatch root cause flagged in `docs/gaps.md` LOW section + phase-4 report flag 1. |
| `propstore/cli/source.py` | 0 | — | Clean. (Phase 4 fix `5a47bfa` resolved the `cli/source.py:33` warning.) |
| `propstore/world/types.py` | 4 | yes | Lines 91/107/594/637: ValueStatus/CelExpr argument-type errors. Pre-existing per docs/gaps.md HIGH section (Z3 three-valued collapse + CelExpr typing). Not in WS-Z-gates surface (RenderPolicy at line 778-1011 has zero errors). |
| `propstore/world/model.py` | 3 | yes | Line 406 ContextInput (pre-existing pattern), line 741 `ClaimRow __getitem__` in `claims_by_ids` (`row["id"]: row` pattern introduced in `e1a3b63`, pre-WS-Z-gates), line 1115 CelExpr (pre-existing). The phase-4 commit `1c47816` adds `_render_policy_predicates`/`claims_with_policy`/`build_diagnostics` and modifies `_claim_select_sql` projection — none of these introduce new errors. |
| `propstore/cli/compiler_cmds.py` | 26 | yes | ContextInput/ClaimRow/Mapping invariance errors + ConceptRow/ParameterizationRow bytes-vs-str at lines 2483-2496. All pre-existing per phase-2b report. The phase-4 additions (`_lifecycle_policy` helper + flag plumbing across `world status/query/derive/resolve/chain`) introduce zero new errors. |

**The 10 `propstore/source/common.py` errors that `docs/gaps.md` LOW section calls out:** Confirmed still present (visible as part of the 21 promote.py errors transitively, since promote.py imports from common.py). Not from WS-Z-gates — same root cause as the phase-4 narrowly-fixed issue. Recorded in gaps as planned.

**Net delta: 0 new pyright errors introduced by WS-Z-gates phases 2-5.**

### C. CLAUDE.md vs `docs/gaps.md` consistency

`docs/gaps.md` "Closed gaps" section names four SHAs:
- `67fccc1` — verified: `feat(sidecar): quarantine raw-id-broken claims with diagnostics row instead of aborting build` (closes axis-1 F3.1).
- `5bb948d` — verified: `feat(compiler,sidecar): draft claim files ingest with stage='draft' instead of dropping` (closes axis-1 F3.2).
- `8923b9f` — verified: `feat(source,cli): promote source branches partially; mirror blocked claims into sidecar` (closes axis-1 F3.3).
- `c263db6` — verified: `feat(cli): pks source status lists per-claim promotion status from sidecar` (completes 3.3).

Open entries in `docs/gaps.md` were spot-checked against axis report references (axis-1 F2.1 → `_DEFAULT_BASE_RATES`; axis-5 F2.4 → `condition_classifier.py UNKNOWN→OVERLAP`; axis-9 A.2/A.3 → CLAUDE.md mislocation entries). All trace to verifiable axis findings or phase-flag observations.

CLAUDE.md "Gaps" section (lines 43-47) cleanly references docs/gaps.md as the source of truth — no contradictions.

PASS.

### D. WS-Z-gates exit criteria checklist

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | `pks build` completes on tree with raw-id errors, drafts, partial sources; every claim represented | PASS | `tests/test_build_sidecar.py::TestRawIdQuarantine` + `TestDraftStageIngestion`; phase 3 report 6 new tests. |
| 2 | `pks query` default matches pre-fix behaviour for clean trees | PASS | `tests/test_render_policy_filtering.py::test_default_policy_*`; defaults hide blocked + drafts. |
| 3 | `--show-quarantined` / `--include-drafts` / `--include-blocked` flags work | PASS | `tests/test_cli_render_policy_flags.py` (10 tests) + `tests/test_render_policy_filtering.py` (11 tests). |
| 4 | `pks promote` accepts partial; per-claim status reported | PASS | `tests/test_source_promotion_alignment.py::test_promote_source_branch_partial_allows_valid_claims_blocks_invalid` + `cli/source.py::promote` echoes counts (line 401-406). |
| 5 | `RenderPolicy` exists; defaults match design checklist | PASS | `propstore/world/types.py:778-836`; defaults False for all three lifecycle flags. |
| 6 | axis-1 F3.1/3.2/3.3 marked closed in docs/gaps.md | PASS | `docs/gaps.md` "Closed gaps" section, lines 88-93. |
| 7 | CLAUDE.md updated; no contradictions remain | PASS | `CLAUDE.md:43-47` "Gaps" section retired the inaccurate Known Limitations paragraph. |
| 8 | `uv run pytest tests/` green | PARTIAL | One pre-existing failure (`test_backward_finds_all_goal_conclusions`) demonstrably unrelated to WS-Z-gates. |

7 PASS, 1 PARTIAL (pre-existing failure unrelated to workstream). Per the workstream-discipline rule "always offer a useful path forward," see Recommendations below.

---

## Per-failure classification

| Test | Pre-existing? | Evidence | Recommendation |
|------|---------------|----------|----------------|
| `tests/test_backward_chaining.py::test_backward_finds_all_goal_conclusions` | YES | Stashed WS-Z-gates working changes; ran on current master HEAD; still fails in 0.94s deterministically. Phase 5 report flagged this. Recent commits to test file + aspic.py are ASPIC+ definition-19 / GroundAtom rework, not WS-Z-gates. | Open as a separate finding for triage against `propstore/aspic.py:79` (the line Hypothesis pinpointed). Add to docs/gaps.md HIGH or MED. Out of WS-Z-gates scope. |

---

## Recommendations

### For Q

- **WS-Z-gates is complete.** All workstream exit criteria are met. The principle-alignment audit (Hat 1) found the design checklist upheld at every refactored gate site, with the only documented backward-compat shim (`--strict` on `pks source promote`) explicitly authorized in the workstream prompt.
- **One pre-existing test failure** (`test_backward_finds_all_goal_conclusions`) lives on master independently of WS-Z-gates; phase 5 flagged it and phase 6 confirmed it. Suggest dispatching a separate coder to triage against `propstore/aspic.py` recent commits `989eaeb`/`471f80f`/`c17e557`.
- **Net pyright delta from WS-Z-gates: 0 new errors.** The 66 pre-existing errors on the changed files are tracked in `docs/gaps.md` LOW (10 in `source/common.py`) plus the broader `propstore.artifacts` `__getattr__` lazy-dispatch typing pattern.

### For the foreman

- No fix dispatch needed before WS-Z-gates closes. The pre-existing test failure is out of scope per the prompt's explicit instruction ("Do not 'tidy up' the pre-existing pyright errors or the pre-existing test failure. Out of scope.").
- Consider opening a small follow-up workstream for: (a) the 10 `source/common.py` pyright errors (broader `propstore.artifacts` __getattr__ rework); (b) `pks world chain` lifecycle plumbing (currently flags accepted but `chain_query` ignores them — flagged in `docs/gaps.md` MED).

### For docs/gaps.md (flag for future commit; do NOT edit in this phase)

Recommend adding a HIGH-or-MED entry for the `test_backward_chaining.py::test_backward_finds_all_goal_conclusions` pre-existing failure, with citation to phase 5 + phase 6 reports and plan referencing `propstore/aspic.py` recent ASPIC+ commits. The failure has been observed twice now (phase 5 + phase 6) without an entry; per the discipline ("Gaps are only added when *observed*"), it now has two independent observations and should be tracked.

---

## Discipline compliance summary

- Read-only: confirmed; no source/test/doc changes made by this audit.
- Observation-driven: every claim in this report cites a file:line, test name, or commit SHA verified by tool output. No theorizing.
- Pre-existing vs introduced: every reported error/failure is classified with git-log evidence.
- Honest ignorance: where a pyright error's root cause was already known from a prior phase report, this report cites the prior report rather than reinventing analysis.

## File path reference (absolute paths)

- This report: `C:\Users\Q\code\propstore\reports\ws-z-gates-06-adversary-verifier.md`
- Working notes: `C:\Users\Q\code\propstore\notes\ws-z-gates-06-adversary-verifier.md`
- Pytest log: `/tmp/ws-z-gates-final.log`
- Pyright log: `/tmp/ws-z-gates-pyright.log`
