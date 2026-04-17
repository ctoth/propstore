# WS-Z-gates Phase 5 — Documentation Cleanup Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source spec: `prompts/ws-z-gates-05-doc-cleanup.md`
Author: coder subagent

Phase 5 retires the misleading "Known Limitations" paragraph from CLAUDE.md, points readers at a new `docs/gaps.md` source-of-truth file, audits phase-3/4 citation discipline, and closes axis-1 findings 3.1/3.2/3.3 in the gap ledger. Doc-cleanup phase only — no Python source changes.

## Commits

| SHA | Deliverable | Message |
|-----|-------------|---------|
| `12379c7` | 1 | `docs(gaps): create docs/gaps.md as source of truth; close axis-1 findings 3.1/3.2/3.3` |
| `0c56b1b` | 2 | `docs(claude): retire Known Limitations section; point at docs/gaps.md` |

Two commits total. Deliverable 3 (`docs/conflict-detection.md` update) was a no-op — the file does not reference build-time gating sites; per the prompt, no unprompted content was added. Deliverable 4 (citation audit) found every required citation already present from phases 3 and 4; no fix commit was needed.

## Deliverable 1 — `docs/gaps.md`

Created at `C:\Users\Q\code\propstore\docs\gaps.md`. Structure:

- **Discipline** section (4 bullets): observation-driven, severity + citation + plan per entry, atomic closures, workstream-grep workflow.
- **Open gaps** organized by severity:
  - **CRIT / structural (2)**: `_DEFAULT_BASE_RATES` fabrication (axis-1 F2.1), `praf/engine.py` dogmatic fallbacks (axis-1 F2.2 + axis-5 F1.1/1.2/1.5).
  - **HIGH (12)**: `fragility_scoring` fabricated opinions (axis-1 F2.3), `source_calibration` prior=0.5 (axis-1 F2.4), Z3 three-valued collapse (axis-5 F2.1-2.3 + axis-6 #4), `condition_classifier` UNKNOWN→OVERLAP (axis-5 F2.4 most-dangerous), CLAUDE.md Pignistic→Jøsang (axis-6 declared-limit 2), `wbf()` is aCBF (axis-6 declared-limit 4), AGM revision in name only (axis-6 #1), AF revision absent (axis-6 #2), semantic substrate zero impl (axis-6 #3), defeasibility priority dropped (axis-6 #6), LLM "none" stance invalid opinion (axis-5 F1.3), sidecar SI normalization silent fallback (axis-5 F3.1).
  - **MED (10)**: `SourceTrustDocument` no status field (axis-1 F2.5), `dedup_pairs` mirror collapse (axis-1 F1.2), `finalize_source_branch` mutates payloads (axis-1 F1.3), IC-merge `product(observed)` (axis-6 declared-limit 3), PrAF treewidth bound undelivered (axis-6 #5), Modgil-Prakken preference heuristic (axis-6 #11), `pks world chain` lifecycle flags accepted-but-unused (phase-4 flag), CLAUDE.md mislocates ATMS/ASPIC+/IC merge (axis-9 A.2), CLAUDE.md `aspic_bridge.py`-as-file references (axis-9 A.3 + E.2/3/4), `aspic.py` "Def 1 (p.8)" wrong (axis-9 B.1/C.1), `rules.py:120` Def 13 wrong (axis-9 B.2/C.2).
  - **LOW / NOTE (8)**: 10 remaining pyright errors in `propstore/source/common.py` (phase-4 flag 1), test markers lie (axis-6 #13), seven modules zero test references (axis-6 #14), `papers/index.md` 21% incomplete (axis-9 D), CLAUDE.md "Defs 1-22" hand-wave (axis-9 A.4), CLAUDE.md TIMEPOINT pointer (axis-9 A.1), citation-pattern drift cross-cutting (axis-6 #15), `Opinion` invariant vs `ResolutionDocument` shape (axis-1 F2.6 / structural S3).
- **Closed gaps** section captures axis-1 findings 3.1, 3.2, 3.3 with the closing commits (`67fccc1`, `5bb948d`, `8923b9f` + `c263db6`).

Plans cite specific workstreams: WS-Z-types (phases 1-6 for honest-ignorance work), WS-A (semantic substrate + structural S2/S3), WS-B (belief-set / AGM / IC-merge), WS-C (defeasibility / preferences / treewidth), and explicit "not yet scheduled" for the gaps without a current docket.

## Deliverable 2 — CLAUDE.md diff summary

Replaced the four-bullet "## Known Limitations" section (lines 43-51 of the prior file) with a two-paragraph "## Gaps" section pointing at `docs/gaps.md`. Diff: 7 lines removed, 3 lines added. No other CLAUDE.md changes — axis-6's broader rewrite (the section misidentifies `propstore/repo/` as owning ATMS/ASPIC+/IC-merge, references `aspic_bridge.py` as a file, etc.) is captured in `docs/gaps.md` as MED-severity entries with plan "CLAUDE.md rewrite (phase beyond WS-Z-gates)".

## Deliverable 3 — `docs/conflict-detection.md`

**No update required.** Read end-to-end. The doc describes the conflict-class taxonomy, the Z3 condition reasoning machinery, derivation chains, and how conflicts feed into argumentation as defeats. It does NOT discuss the sidecar build-time refusal of raw-id-broken claims, the compiler's draft-claim drop, the source-promote all-or-nothing gate, or how those things surface in the render layer. Per the prompt's instruction ("If it doesn't mention any of the three gate-refactor sites, don't add unprompted content — leave it alone."), no edit was made.

## Deliverable 4 — Citation audit

Grepped `propstore/` for `ws-z-render-gates.md` and for `Finding 3\.[123]`. Returned hits in all eight named files; verified each named function/site has the citation either at module-docstring level, function-docstring level, or inline-comment level:

| File | Site | Citation present? | Where |
|------|------|-------------------|-------|
| `propstore/sidecar/build.py` | `_collect_raw_id_diagnostics` | yes | function docstring (lines 156-157) |
| `propstore/sidecar/build.py` | (also: module docstring) | yes | module docstring (line 4) |
| `propstore/sidecar/claims.py` | `populate_raw_id_quarantine_records` | yes | function docstring (lines 202-203) |
| `propstore/sidecar/claims.py` | `populate_claims` | yes | function docstring (lines 287-289) |
| `propstore/sidecar/claim_utils.py` | `insert_claim_row` | yes | function docstring (lines 229-230) |
| `propstore/compiler/passes.py` | draft-handling site (line 295) | yes | inline comment (line 289) |
| `propstore/source/promote.py` | `_compute_blocked_claim_artifact_ids` | yes | function docstring (lines 214-215) |
| `propstore/source/promote.py` | `_write_promotion_blocked_sidecar_rows` | yes | function docstring (lines 296+) |
| `propstore/source/promote.py` | `promote_source_branch` | yes | module docstring (lines 3-4) + inline comment (line 404) — function itself has no docstring but coverage is upstream |
| `propstore/world/types.py` | RenderPolicy field block | yes | inline docblock (lines 822-836) |
| `propstore/world/model.py` | `_render_policy_predicates` | yes | function docstring (lines 644-645) |
| `propstore/world/model.py` | `claims_with_policy` | yes | function docstring (lines 679-682) |
| `propstore/world/model.py` | `build_diagnostics` | yes | function docstring (lines 705-709) |
| `propstore/cli/source.py` | `source_status` | yes | function docstring (lines 420-421) |
| `propstore/cli/compiler_cmds.py` | `_lifecycle_policy` | yes | function docstring (lines 114-115) |
| `propstore/cli/compiler_cmds.py` | `world_status` | yes | function docstring (lines 556-557) |
| `propstore/cli/compiler_cmds.py` | `world_query` | yes | function docstring (lines 612-613) |
| `propstore/cli/compiler_cmds.py` | `world_derive` | yes | function docstring (lines 1711-1712) |
| `propstore/cli/compiler_cmds.py` | `world_resolve` | yes | function docstring (lines 1809-1810) |
| `propstore/cli/compiler_cmds.py` | `world_chain` | yes | function docstring (lines 2218-2220) |

**Result:** all citations present and pointing at the correct workstream + axis-1 finding number(s). No citation-fix commit needed.

## Deliverable 5 — Final validation

### Pyright

```
$ uv run pyright propstore/
355 errors, 55 warnings, 0 informations
```

This count is unchanged from phase 4's exit state (phase-4 report flag 1 noted 10 remaining errors specifically in `propstore/source/common.py` from the `propstore.artifacts` `__getattr__` lazy-dispatch pattern; the 355 includes those plus pre-existing errors from the broader codebase). Phase 5 changed only markdown files (`docs/gaps.md`, `CLAUDE.md`); markdown cannot affect pyright. **No regression.**

### Pytest

```
$ uv run pytest tests/ -x --timeout=60
1 failed, 251 passed in 85.50s
FAILED tests/test_backward_chaining.py::test_backward_finds_all_goal_conclusions
```

**Investigation.** Re-ran in isolation: `uv run pytest tests/test_backward_chaining.py::test_backward_finds_all_goal_conclusions -x --timeout=120` → 1 failed in 0.96s (deterministic, not a Hypothesis flake). Then stashed phase-5 working changes and re-ran: same 1 failed in 0.95s. **The failure pre-exists on master before any phase-5 change.**

This phase made no Python edits (markdown-only). The failure cannot have been caused by phase-5 work. Recent history on `aspic.py` (most recent commits: `989eaeb` ASPIC cache lifecycle fix, `471f80f` test regression fix, `c17e557` definition-19 lifting/defeat fix) suggests this test relates to a recent ASPIC+ definition-19 change rather than to anything in WS-Z-gates.

**Proposed solution / next step:** This is a pre-existing master failure unrelated to WS-Z-gates. Recommended path: open it as a separate finding for the next phase (phase 6 adversary + verifier) to triage against the recent `aspic.py` commits, or hand off to a coder subagent dispatched to investigate `test_backward_finds_all_goal_conclusions` against `propstore/aspic.py:79` (the line the Hypothesis explanation pinpointed). Phase 5's exit criteria (no regression introduced) are satisfied; the unrelated pre-existing failure is flagged below.

## Flags raised during work

1. **Pre-existing master test failure: `test_backward_chaining.py::test_backward_finds_all_goal_conclusions`.** Deterministic (0.95s), unrelated to phase 5 (markdown-only changes). Likely related to recent `aspic.py` definition-19 work (commits `989eaeb`/`471f80f`/`c17e557`). Recommend phase 6 adversary or a separate coder dispatch triage this against `propstore/aspic.py:79`.

2. **Module-level `RenderPolicy` import in `compiler_cmds.py`.** Phase 4 flag 5 noted this is currently TYPE_CHECKING-only with `_lifecycle_policy` doing a runtime import. Cosmetic; not blocking.

3. **Per phase-4 flag 1: 10 pyright errors remain in `propstore/source/common.py`.** Captured in `docs/gaps.md` LOW section with plan "follow-up typing workstream."

4. **`pks world chain` accepts lifecycle flags but does not behaviorally filter.** Captured as MED in `docs/gaps.md` with plan "future workstream when chain-query materially consumes claim sets."

5. **`docs/gaps.md` deliberately does not exhaustively re-enumerate every axis-5 silent-failure finding.** I included the structurally significant ones (Z3 three-valued collapse, condition_classifier UNKNOWN, sidecar SI normalization, classify.py "none" stance, fragility_scoring fabrications, praf/engine.py dogmatic fallbacks). The remaining axis-5 findings (3.2 embedding-restore swallow, 3.3-3.10 various per-call exception swallowing, Category 5 bool-coercion, Category 6 None-overloading) are referenced by axis-5 itself; future workstreams will add specific entries when picking them up. Per the prompt: "the file captures the review's state, not your own review" — I leaned conservative on per-finding granularity to avoid over-claiming; if the verifier wants per-finding entries, they can be added.

## Out of scope (deferred)

- Broader CLAUDE.md rewrite (axis-6's full recommendation): rephrasing the architecture-layer attribution, fixing `aspic_bridge.py`-as-file references, fixing the "Defs 1-22" hand-wave. Captured in `docs/gaps.md` MED entries with plan "CLAUDE.md rewrite (phase beyond WS-Z-gates)."
- Citation-as-claim CI lint per disciplines.md rule 1 ("a pre-commit or CI job that scans docstrings for citation patterns"). Mentioned in disciplines.md but not part of phase 5.
- Backfilling missing `papers/*/notes.md` files (25 directories) and missing `papers/index.md` entries (44 orphans). Captured in `docs/gaps.md` LOW.

## Citation-as-claim discipline

`docs/gaps.md` itself adheres to discipline rule 2 ("Docs never lead code"): every entry cites either an axis-N finding number or a phase report flag. No entry was added that the 2026-04-16 review did not surface. Rule 1 ("citation-as-claim") is honored by the audit table above — every cited finding number traces to a verified location in the source.

## File path reference (absolute paths)

- `C:\Users\Q\code\propstore\docs\gaps.md` (new)
- `C:\Users\Q\code\propstore\CLAUDE.md` (modified — Known Limitations section replaced)
- `C:\Users\Q\code\propstore\reports\ws-z-gates-05-doc-cleanup.md` (this file)
- `C:\Users\Q\code\propstore\notes\ws-z-gates-05-state.md` (work breadcrumb)
