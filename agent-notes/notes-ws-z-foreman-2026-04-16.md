# WS-Z Foreman Notes — 2026-04-16 — CLOSED

## Status

**WS-Z-gates: COMPLETED** on 2026-04-16. Six phases dispatched sequentially under the foreman protocol. Adversary + verifier signed off.

**WS-Z-types: NOT STARTED** — Q's instruction was to fully update WS-Z-gates and stop. Will require a fresh dispatch decision.

## Mode
Foreman protocol active (`ward set foreman`). Subagents committed their own work.

## Final WS-Z-gates phase log

| # | Phase | Status | Key commits |
|---|---|---|---|
| 1 | Design scout | DONE | `890347c` |
| 2 | Schema additions + collision rename | DONE | `41541f3`, `a1c20c8`, `77d4748`, `7f3da36`, `53c8acf` |
| 2b | Rename completion verification | DONE | `4dbcd1c` (no fix needed) |
| 3 | Three gate refactors | DONE | `34d2be2`, `67fccc1`, `dd78dfd`, `5bb948d`, `d5b585e`, `8923b9f`, `f594972` |
| 4 | RenderPolicy + CLI flags + `pks source status` | DONE | `cb9a7e1`, `d489635`, `009dda2`, `1c47816`, `74176b1`, `f930d74`, `b48f62d`, `c263db6`, `5a47bfa`, `c37fed5` |
| 5 | Doc cleanup (`docs/gaps.md` + CLAUDE.md) | DONE | `12379c7`, `0c56b1b`, `5451c5e` |
| 6 | Adversary + verifier | DONE | `9698233` |

## Test suite trajectory
- Baseline (before WS-Z-gates): 2524 passing.
- After phase 2: 2529 passing (+5 schema tests).
- After phase 3: 2535 passing (+6 gate-behavior tests).
- After phase 4: 2562 passing (+27 RenderPolicy + CLI tests).
- After phase 6 final: 2561/2562 passing. Sole failure (`test_backward_finds_all_goal_conclusions`) verified pre-existing — traces to ASPIC+ commits `989eaeb`/`471f80f`/`c17e557` from 2026-04-14, two days before WS-Z-gates began. Out of scope.

## Pyright trajectory
- Net new pyright errors from WS-Z-gates: **0** (per phase 6 verification).
- Pre-existing pyright errors documented as gaps in `docs/gaps.md`.

## Concurrent non-foreman work that landed during WS-Z-gates

### Davidsonian → descriptivist event reframe (Q-driven)
- Q rejected Davidsonian event semantics in favor of "events as defeasible coreference" (Hobbs 1985 + Quine 1968 + late-period Putnam).
- WS-A P3 + P4 updated; WS-C composition section added; `semantic-substrate-papers.md` P3 rewritten.
- `docs/event-semantics.md` created by subagent — commits `f25817d` + `546c702`. 1199 words; descriptivist position statement.

### git-notes provenance commitment
- Q's question "we can already use git notes with dulwich no?" → yes; `dulwich.notes` is in `dulwich >= 0.22`; pyproject pins `>= 1.1.0`.
- WS-A P1 scope, exit criteria, red flags, and `semantic-substrate-papers.md` P1 all updated to commit to git-notes (`refs/notes/provenance`) as the storage realization for named-graph provenance payloads.

### Cloudflare Artifacts launch (informational)
- 2026-04-16 architectural validation of propstore's git-backed-storage-as-agent-substrate bet. Not a propstore commitment; not a threat; substrate-independent given git-notes works on any git remote.

## Source-of-truth documents (refreshed and current)
- `reviews/2026-04-16-code-review/workstreams/disciplines.md`
- `reviews/2026-04-16-code-review/workstreams/judgment-rubric.md`
- `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md` — **NOW carries completion summary**
- `reviews/2026-04-16-code-review/workstreams/ws-z-honest-ignorance-types.md`
- `reviews/2026-04-16-code-review/workstreams/ws-a-semantic-substrate.md` — carries event-semantics + git-notes reframes
- `reviews/2026-04-16-code-review/workstreams/ws-b-belief-set-layer.md`
- `reviews/2026-04-16-code-review/workstreams/ws-c-defeasibility.md` — carries WS-A composition section
- `reviews/2026-04-16-code-review/workstreams/README.md` — Z-gates row marked COMPLETED
- `docs/event-semantics.md` — descriptivist position statement
- `docs/gaps.md` — living source of truth for known gaps
- `CLAUDE.md` — old "Known Limitations" retired; "Gaps" section points at docs/gaps.md
- `semantic-substrate-papers.md` — paper-retrieval list with reframes folded in
- `notes-ws-z-foreman-2026-04-16.md` — this file

## Stopped per Q's instruction.

Tasks 16-20 closed. Task 21 (WS-Z-types) remains pending; not auto-dispatched.

Foreman is idle until Q kicks off the next dispatch.
