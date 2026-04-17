# Workstream Z-gates — Build-to-Render Gate Removal

## Completion summary (2026-04-16)

This workstream landed in six phases coordinated under the foreman protocol on 2026-04-16. Adversary review confirmed principles upheld; verifier confirmed 2561/2562 tests pass with the sole failure (`test_backward_finds_all_goal_conclusions`) verified pre-existing and unrelated to this workstream (traces to recent ASPIC+ commits 2026-04-14, two days before WS-Z-gates began).

**Phase-by-phase commit register:**

| Phase | Subagent role | Commits | Outcome |
|---|---|---|---|
| 1 — Design scout | scout | `890347c` | Scout report `reports/ws-z-gates-01-design.md` |
| 2 — Schema migration + collision rename | coder | `41541f3`, `a1c20c8`, `77d4748`, `7f3da36`, `53c8acf` | SCHEMA_VERSION 2→3; `build_diagnostics` table; `claim_core` gains `build_status`/`stage`/`promotion_status`; `claim_algorithm_payload.stage` → `algorithm_stage` (Rope-scope); +5 TestSchemaV3, 2529 passing |
| 2b — Rename verification | coder | `4dbcd1c` | Pyright snapshot was stale; rename was complete in `41541f3`; report-only |
| 3 — Three gate refactors | coder | `34d2be2`, `67fccc1`, `dd78dfd`, `5bb948d`, `d5b585e`, `8923b9f`, `f594972` | `_collect_raw_id_diagnostics` quarantine; draft files traverse with `stage='draft'`; partial promote with `--strict` opt-in; +6 net new tests, 2535 passing |
| 4 — RenderPolicy + CLI flags + `pks source status` | coder | `cb9a7e1`, `d489635`, `009dda2`, `1c47816`, `74176b1`, `f930d74`, `b48f62d`, `c263db6`, `5a47bfa`, `c37fed5` | `include_drafts`/`include_blocked`/`show_quarantined` fields; `claims_with_policy` projection; CLI flags on `pks world {status,query,resolve,chain,derive}`; new `pks source status` subcommand; +27 net tests, 2562 passing |
| 5 — Doc cleanup | coder | `12379c7`, `0c56b1b`, `5451c5e` | Created `docs/gaps.md` (32 open + 3 closed entries); CLAUDE.md "Known Limitations" replaced with "Gaps" section pointing at `docs/gaps.md`; citation-as-claim audit clean |
| 6 — Adversary + verifier | general-purpose | `9698233` | All five principle checks pass; 7/8 exit criteria pass (one PARTIAL due to pre-existing failure); 0 new pyright errors from this workstream |

**Closed axis findings (registered in `docs/gaps.md`):**
- axis-1 Finding 3.1 — sidecar build raw-id gate. Closed by commit `67fccc1`.
- axis-1 Finding 3.2 — compiler draft filter. Closed by commit `5bb948d`.
- axis-1 Finding 3.3 — source promote all-or-nothing. Closed by commits `8923b9f` + `c263db6`.

**Surface area (cumulative, phases 2-5 only — non-doc):** ~3000 insertions across `propstore/sidecar/`, `propstore/compiler/`, `propstore/source/`, `propstore/cli/`, `propstore/world/`, plus four new test files (`tests/test_render_policy_filtering.py`, `tests/test_cli_render_policy_flags.py`, `tests/test_cli_source_status.py`, plus the new schema/quarantine/draft/partial-promote tests appended to existing files).

**Documented gaps surfaced during the workstream (open in `docs/gaps.md`):**
- MED — `pks world chain` accepts the lifecycle flags for CLI symmetry but does not behaviorally filter (chain_query reads parameterizations, not filtered claim sets). Future workstream.
- LOW — 10 pyright errors remain in `propstore/source/common.py` from `propstore.artifacts.__getattr__` lazy-dispatch limitation. Follow-up typing workstream.
- Pre-existing — `tests/test_backward_chaining.py::test_backward_finds_all_goal_conclusions` failure traces to recent ASPIC+ commits (`989eaeb`, `471f80f`, `c17e557`, all 2026-04-14). Out of scope; recommend separate triage.

**Foreman coordination artifacts:**
- `prompts/ws-z-gates-{01-design-scout,02-schema,02b-rename-fix,03-gate-refactors,04-renderpolicy-cli,05-doc-cleanup,06-adversary-verifier}.md`
- `reports/ws-z-gates-{01-design,02-schema,02b-rename-fix,03-gate-refactors,04-renderpolicy-cli,05-doc-cleanup,06-adversary-verifier}.md`
- `notes-ws-z-foreman-2026-04-16.md` — running foreman log

---

## (Original workstream spec follows for reference.)


Date: 2026-04-16
Status: **COMPLETED 2026-04-16** (foreman-coordinated; six phases; adversary + verifier signed off)
Depends on: `disciplines.md`, `judgment-rubric.md`. No paper dependency, no other workstream dependency.
Blocks: —
Review context: `../axis-1-principle-adherence.md` (Findings 3.1, 3.2, 3.3), `../SYNTHESIS.md` pattern C

## What you're doing

The 2026-04-16 review found three places where build-time machinery refuses or drops data that should reach the sidecar with diagnostics attached. Each one violates CLAUDE.md's design checklist directly:

> **Design checklist (every data-flow decision):**
> 1. Does this prevent ANY data from reaching the sidecar? → WRONG.
> 2. Does this require human action before data becomes queryable? → WRONG.
> 3. Does this add a gate anywhere before render time? → WRONG.
> 4. Is filtering happening at build time or render time? Build → WRONG.

The three sites:

- **`propstore/sidecar/build.py:75-82, 148`** — `_raise_on_raw_id_claim_inputs` aborts the entire sidecar build on any claim with a raw-id error. One bad claim file makes the entire knowledge tree unqueryable until a human fixes the offender. (Hits checklist items 1, 2, 3, AND 4.)
- **`propstore/compiler/passes.py:289-307`** — drops every `stage: draft` claim file from the semantic bundle by emitting a diagnostic and replacing the claims with an empty tuple. Drafts never reach the sidecar; users querying for "what drafts am I working on?" get nothing.
- **`propstore/source/promote.py:186-188`** — refuses to promote a source branch unless `report.status == "ready"`. A source with even one broken stance reference cannot promote any of its valid claims; the data is invisible from the primary-branch sidecar until a human resolves every error.

Your job: convert each gate into a render-time policy filter with a quarantine row. The data reaches the sidecar; diagnostics ride alongside; the render layer chooses what to show under user-supplied policy.

This is the smallest workstream in the set and has no dependencies. It is the recommended starting point for Q whenever you have an evening — closes three crit/high findings, no theoretical decisions required, mostly disciplined plumbing.

## Vision

When this workstream is complete:

- **`pks build` always populates the sidecar with everything it has.** A claim with a raw-id error becomes a row with `build_status='blocked'` and a `build_diagnostics` row attached; the rest of the build proceeds normally. The user sees the diagnostic via `pks query` (filtered out by default render policy; visible under `--show-quarantined`).
- **`stage: draft` claims populate normally** with a `stage='draft'` annotation. The render layer's default policy hides drafts; users can opt in via `pks query --include-drafts`. Drafts are queryable, listable, and discoverable — they just aren't shown in the default view.
- **`pks promote` accepts partial promotion.** Valid claims promote; claims with finalize errors stay on the source branch with a `promotion_status='blocked'` annotation in the sidecar. The user sees the blocked items via `pks source status`; they can promote those individually after fixing the underlying errors.
- **A `build_diagnostics` sidecar table** holds per-claim diagnostic information: kind, severity, message, source location, blocking-vs-warning flag.
- **A `RenderPolicy` configuration object** controls default visibility per category (drafts, blocked, quarantined, errored, deprecated). The render layer consults policy before filtering output.

## What you are NOT doing

- **Not redesigning the sidecar schema beyond adding the diagnostics + status fields.** Keep the change minimal.
- **Not designing CKR exception semantics or context-with-exceptions structure.** That's WS-C. Render-time filtering by policy is simpler — it's "don't show drafts by default" not "this exception is justified in this context."
- **Not building a new CLI surface beyond what these changes require.** `pks query --show-quarantined`, `pks query --include-drafts`, `pks source status` (or extension thereof) are minimal additions.
- **Not migrating proposal-branch heuristic outputs.** Those are already on a separate branch and gated by explicit promote; no behavior change here.
- **Not changing what counts as a build error.** A genuinely malformed YAML file (parse error) still aborts that file's processing — but only that file, and the sidecar row records the parse failure rather than aborting the batch.

## Phase structure

This workstream is small enough to be one phase, but logically splits into three near-independent fixes plus a shared diagnostics table. Order doesn't matter much; do them in whichever order is convenient.

### Phase Z-gates-1 — Sidecar build raw-id quarantine

- Add a `build_diagnostics` table to the sidecar schema (per `propstore/sidecar/schema.py`).
- Refactor `propstore/sidecar/build.py:75-82, 148`: `_raise_on_raw_id_claim_inputs` becomes `_collect_raw_id_diagnostics` that returns a list of diagnostic rows. Build proceeds; per-claim status reflects whether the claim was successfully ingested or quarantined.
- Each claim row in the sidecar grows a `build_status: Literal["ingested", "blocked"]` field plus a foreign key to its diagnostics.
- Property tests: a build with N valid claims and 1 raw-id-broken claim produces N+1 sidecar rows (the broken one with `build_status='blocked'` plus its diagnostic); none of the valid claims are missing.

### Phase Z-gates-2 — Compiler draft visibility

- `propstore/compiler/passes.py:289-307`: stop replacing draft claims with an empty tuple. Emit them with `stage='draft'` annotation; the SemanticDiagnostic survives but downgrades from `error` to `info` (the draft status is informative, not a problem).
- The semantic-bundle output for draft files is the actual claims, not an empty tuple.
- Sidecar populates draft claims with `stage='draft'` field on the claim row.
- `propstore/_resources/schemas/claim.schema.json` — the schema description currently says drafts are "rejected"; update to "marked for render-policy filtering."
- Property tests: a build with M non-draft claims and K draft claims produces M+K queryable rows; the default render policy returns only the M; `--include-drafts` returns all M+K.

### Phase Z-gates-3 — Promote partial

- `propstore/source/promote.py:186-188`: drop the all-or-nothing gate. Promote each claim individually based on its own validity.
- Claims that pass finalize promote normally.
- Claims that fail finalize stay on the source branch with `promotion_status='blocked'` annotation in the sidecar (visible via the new diagnostics machinery).
- The promote command output reports both success and blocked counts; CLI exit code reflects whether anything was promoted (success) vs. all blocked (failure).
- `pks source status` (or an extended existing command) lists the per-claim promotion status with the diagnostics.
- Property tests: a source with P valid + Q invalid claims promotes P; the Q remain on source with blocked annotations; subsequent re-promote after fixing one of the Q promotes that one.

### Phase Z-gates-4 — `RenderPolicy` configuration

- Add `RenderPolicy` to `propstore/world/types.py` (the existing module that has `RenderPolicy` per `propstore/__init__.py` re-exports — verify what's there and extend rather than parallel-invent).
- Default policy: hide `build_status='blocked'`, hide `stage='draft'`, hide `promotion_status='blocked'` (these stay queryable via flags but are not in the default view).
- Per-flag CLI options on `pks query`: `--include-drafts`, `--include-blocked`, `--show-quarantined`, etc.
- Render policy is *render-time*. It does not affect storage. The same sidecar serves different policies to different views.
- Property tests: identical build state, two policy configurations, two distinct render outputs — and the underlying sidecar rows are identical.

### Phase Z-gates-5 — Document + remediate

- Update CLAUDE.md to remove any "Known Limitations" that referenced these gate behaviors as expected.
- Update `docs/gaps.md` to reflect the closures.
- Update `docs/conflict-detection.md` if it discussed the build-time gating (it likely does given the design checklist's prominence).
- Citation-as-claim discipline: make sure the design-checklist clauses in CLAUDE.md are referenced from the new code paths so a future review sees the discipline being honored.

## Red flags — stop if you find yourself

- About to keep `_raise_on_raw_id_claim_inputs` "for safety."
- About to silently drop drafts from the bundle but emit a warning.
- About to make promote refuse partial work because "it's cleaner."
- About to filter at build time but call it a "policy" — policies are render-time; build-time filtering is the antipattern.
- About to design a complex policy DSL — start with simple boolean flags; richer policies can come later if needed.
- About to change proposal-branch promotion behavior — that's a separate concern; proposal branches stay gated by explicit user-initiated `promote`.

## Exit criteria

- `pks build` completes successfully on a knowledge tree containing raw-id errors, draft claims, and partially-broken sources. Every claim is represented in the sidecar (either ingested or quarantined).
- `pks query` default output matches pre-fix behavior for clean trees (no regression in the happy path).
- `pks query --show-quarantined`, `--include-drafts`, `--include-blocked` flags work.
- `pks promote` accepts partial promotion; per-claim status reported.
- `RenderPolicy` exists; default values match design-checklist intent (don't show problems by default; allow opt-in for diagnostic views).
- All axis-1 findings 3.1-3.3 marked closed in `docs/gaps.md`.
- CLAUDE.md updated; no contradictions remain between the doc's design-checklist claims and the code's behavior.
- `uv run pytest tests/` green.

## On learning

This workstream is the cleanest illustration of CLAUDE.md's design checklist in action. The principle — "data flows in with provenance; render filters per policy" — is at its most concrete here. There's no theoretical sophistication needed; just disciplined application of the principle to three sites that violated it.

The lesson generalizes: every time the system refuses to ingest something, ask whether the user can ever recover from that refusal without leaving propstore. If the answer is "they have to fix it and re-build," that's a build-time gate that should become a render-time policy. The user can always opt to *not see* a problematic row; they cannot opt to *recover a row the build refused to materialize*.

This is small. Do it as a starter workstream if you want to get oriented in the codebase before tackling the larger ones.
