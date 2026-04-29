# Workstreams index — 2026-04-26 deep review (round 3)

Current workstream specifications after the Codex round-3 review. Plus this INDEX, the `workstreams/` directory holds the individual WS files, including the new WS-CM prerequisite.

Each WS file is a self-contained spec: STATUS line, findings table, file:line citations, first failing tests, production change sequence, acceptance gates, "Done means done = all findings closed" criterion, papers/specs referenced, cross-stream notes. The required cross-workstream property-based test matrix lives at `../PROPERTY-BASED-TDD.md`.

This file is the navigation page.

---

## Decision log link

Q resolved the framing/scoping questions across three rounds. Round 1 (2026-04-27) resolved D-1 through D-18. Round 2 resolved D-19 through D-26. Round 3 resolved D-27 through D-29 and added the property-based TDD matrix. Authoritative decisions live at `../DECISIONS.md`. Where this index summarizes a decision, the `../DECISIONS.md` text governs. Where a workstream file conflicts with `../DECISIONS.md`, the decision text wins until the WS file is rewritten to match.

---

## Execution checklist

This index is the control surface for execution. Do not treat the individual WS
files as "done" until this table is updated.

Checklist protocol:

0. Before selecting the next row, run `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py`.
   If it fails, repair this index before executing any workstream.
1. Pick exactly one unchecked WS row from the table below.
2. Execute that WS to completion under its own TDD sequence.
3. Run every acceptance gate listed in the WS file, including the relevant
   property-based gates from `../PROPERTY-BASED-TDD.md`.
4. Write a closure report under
   `reviews/2026-04-26-claude/workstreams/reports/<WS-ID>-closure.md`.
5. Only after the report exists, update this INDEX row. The `Status` cell is
   the checklist checkbox: `OPEN` means unchecked; `CLOSED <sha>` means checked
   off.
   - change Status from `OPEN` to `CLOSED <sha>`;
   - add the closure report path to the Decisions/notes cell;
   - keep any partial/deferred work named explicitly in the report, not hidden
     in prose.

Closure report minimum contents:

- Workstream id and closing commit.
- Findings closed, one line each.
- Tests written first and why they failed before the fix.
- Logged test commands and log paths.
- Property-based tests added or explicitly moved to a successor WS.
- Files changed.
- Remaining risks or successor workstreams, if any.

If a WS is not fully closed, do not check it off here. Passing tests alone is not
closure; the row changes only after the WS file, tests, gaps update, property
gates, and closure report all agree.

## Status board

WS-N is preserved as a SUPERSEDED redirect into WS-N1 + WS-N2.

| ID | Title | Status | Deps | Blocks | Findings | Decisions applied |
|---|---|---|---|---|---|---|
| **WS-A** | Schema fidelity, fixture parity, identity boundary | CLOSED e75581b9 | — | everything | 4 + URI-authority + privileged-namespace section | **D-24 (URI authority + reserved namespace)**; report: `reviews/2026-04-26-claude/workstreams/reports/WS-A-closure.md` |
| WS-B | Render policy & web data leak | CLOSED bb0bf7fe | A | — | 11 (T1.1-T1.3, T1.5, T1.8-T1.9, Codex #4, #8-#11) | **D-21 (hard 403/404 on blocked claim; redacted-page logic deleted)**; report: `reviews/2026-04-26-claude/workstreams/reports/WS-B-closure.md` |
| **WS-CM** | Micropub canonical payload + Trusty URI identity | CLOSED 526cf53b | A | C, M, E | D-7/D-29 cycle break | **D-7, D-29** — one prerequisite owns canonical micropub payload and `ni:///sha-256` id; no placeholder hash; report: `reviews/2026-04-26-claude/workstreams/reports/WS-CM-closure.md` |
| WS-D | Subjective-logic operator naming | CLOSED ea232e21 | — | F, G, H, I, J, J2 | ~12 (T2.7-T2.8, T2.13 + cluster F HIGH/MED) | **D-1 (true WBF), D-2 (true BetP + new flag)**; corrected WBF base-rate reading from vdH 2018 p.5; report: `reviews/2026-04-26-claude/workstreams/reports/WS-D-closure.md` |
| WS-O-qui | quire fixes | CLOSED a27b3cbc | — | **Q-cas**, (informal upstream of N1 step `_canonical_json` collapse) | 12 (cluster S HIGH/MED + boundary) | shipped quire `v0.2.0` at `23bbac2`; propstore pin `a27b3cbc`; full suite `3031 passed` |
| **WS-Q-cas** | Branch-head CAS discipline at propstore call sites | CLOSED 645df92f | A, O-qui | C, E | new spec; concurrent-finalize / concurrent-promote / concurrent-import / concurrent-materialize race tests | **D-23** — captures expected head before mutation, threads it to quire, fails without writing sidecar state on lost race; report: `reviews/2026-04-26-claude/workstreams/reports/WS-Q-cas-closure.md` |
| WS-C | Sidecar atomicity & SQLite discipline | CLOSED eedfbaa8 | A, **CM**, **Q-cas** | E | 7 (T1.4, T1.6, T1.7, Codex #1-#3, #5) | **D-6 (reorder)**; consumes micropub identity from WS-CM; cache-key derivation rule (Codex 1.15); branch-head CAS via WS-Q-cas; report: `reviews/2026-04-26-claude/workstreams/reports/WS-C-closure.md` |
| WS-E | Source-promote correctness | CLOSED 152818da | A, C, **CM**, **Q-cas** | K, L, M | 12 (T3.5-T3.8 + cluster A HIGH/MED) | inherits D-6; consumes D-7 through WS-CM; master-ref allowance for valid canonical/master refs (Codex 1.14); branch-head CAS via WS-Q-cas; report: `reviews/2026-04-26-claude/workstreams/reports/WS-E-closure.md` |
| WS-I | ATMS / world correctness | CLOSED 6a6cc9d6 | D | F, J, J2, K, M | 7 (cluster E HIGH/MED + Codex #24-#26) | interface replacement — bounded `is_stable` deleted; new unbounded API has different semantics (Codex 2.9); report: `reviews/2026-04-26-claude/workstreams/reports/WS-I-closure.md` |
| WS-J | Worldline determinism, hashing, OverlayWorld rename | CLOSED 9eefe5ce | D, **I** | J2 | 13 (cluster J HIGH/MED) | **D-11 path A (rename, no Pearl here)**; depends on WS-I (Codex 2.8 ordering fix); typed canonical encoding — equivalent failures different reprs, typed failure on unknown (Codex 2.10); kw-only budget, no default (Codex 2.11); journal contract — typed operator/input/version/policy/normalized state (Codex 2.12); report: `reviews/2026-04-26-claude/workstreams/reports/WS-J-closure.md` |
| WS-O-arg | argumentation package — HIGH bugs (kernel) | CLOSED a2f41029 | — | F, G, **O-arg-aba-adf**, **O-arg-dung-extensions**, **O-arg-vaf-ranking**, **O-arg-gradual** | 8 (T2.10-T2.11 + cluster P HIGH) | **D-15 (upstream policy), D-16 (split)**; sub-streams now declared as explicit downstream (Codex 2.15); ideal-extension proof replaced with paper construction, defense not downward-closed (Codex 2.16); upstream-sentinel and propstore-sentinel separated (Codex 2.18); report: `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-closure.md` |
| **WS-O-arg-aba-adf** | ABA+ (Cyras 2016) flat-only + ADF (Polberg 2017) AST | CLOSED 58bbae38 | O-arg | F | new spec | **D-16 group A**; **D-25 (AST representation for ADF acceptance conditions; serializable for ICCMA, inspectable by structural-link classifier)**; non-flat ABA scoped out with hard `NotFlatABAError`; report: `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-aba-adf-closure.md` |
| **WS-O-arg-dung-extensions** | Eager, stage2, prudent, semi-stable, bipolar grounded/complete, Caminada labelling-as-semantics operational | CLOSED 00076004 | O-arg | F | new spec | Closed by upstream `argumentation` commits `c267c2b`, `c941fe4`, and prudent correction `98a7325`; propstore pin/sentinel commit `00076004`; Z3 Dung backend deleted; evidence in `tests/architecture/test_argumentation_pin_dung_extensions.py` and `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-dung-extensions-closure.md`. |
| **WS-O-arg-vaf-ranking** | Bench-Capon VAF (Atkinson AATS slice) + Bonzon ranking + ranking-convergence | CLOSED 418d409c | O-arg | F, **O-arg-gradual** | new spec | **D-16 group C**; ranking-convergence ownership locked here, `RankingResult` exported (Codex 2.22); Atkinson scoped to "AATS slice" — honest about missing CQs (Codex 2.23); closed by pushed argumentation commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908` and propstore pin `418d409c`; report: `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-vaf-ranking-closure.md` |
| **WS-O-arg-gradual** | DF-QuAD discontinuity-free + Matt-Toni 2008 game-theoretic | CLOSED fcbc77b1 | O-arg, **O-arg-vaf-ranking** | H | new spec | **D-16 group D**; deletion-first — `compute_dfquad_strengths` deleted, every caller updated, no `strict=True` compat (Codex 2.21); consumes `RankingResult` from VAF/ranking (Codex 2.22); closed by pushed argumentation commit `dbb036b9968b370856c22cb2ebf6157a72587956`, propstore pin `fcbc77b1`, and property/relation gates for DF-QuAD, Matt-Toni, Potyka, and Gabbay; report: `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-gradual-closure.md` |
| **WS-O-arg-vaf-completion** | Bench-Capon pp. 438-447 line-of-argument + fact-uncertainty VAF completion | CLOSED d993b1cdc255837c25fca02456cdc56adfb4e8e8 | **O-arg-vaf-ranking** | — | new spec | Closed by pushed argumentation commit `0d036dfef91e8c47ed47e5b030fe9d510bc53295`; propstore pin/sentinel keeps remote-Git dependency shape and removes exact-SHA tests; report: `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-vaf-completion-closure.md` |
| WS-F | ASPIC+ bridge fidelity | CLOSED e89cc387 | D, **O-arg** | — | 14 (T2.1, T2.9, T5.7 + cluster D HIGH 1-7 + Codex #12-#13, #21-#22, #36) | projection invariant fix closed — both relations preserved without silent loss, NOT attacks-iff-defeats (Codex 2.2); WS-O-arg dependency consumed through pushed argumentation commit `bbfa7ef`; behavior sentinel `tests/test_workstream_f_done.py`; report: `reviews/2026-04-26-claude/workstreams/reports/WS-F-closure.md` |
| WS-G | AGM/iterated/IC postulate coverage | CLOSED b3b91229 | D, O-arg | — | 11 (T2.2, T2.6 + cluster C HIGH/MED + Codex #18-#20, #23) | **D-12 (AGM-AF stays in argumentation pkg)**; coverage-only labels separated from must-fail (Codex 2.4); deterministic stale-cache fixture (Codex 2.5); paper-derived OCF worked example (Codex 2.6); upstream argumentation no-stable fix `de6b66f`; report: `reviews/2026-04-26-claude/workstreams/reports/WS-G-closure.md` |
| WS-O-gun | gunray fixes + anytime wire-up | OPEN | — | M, H | 17 (cluster R HIGH/MED/LOW + ARCH/BND) | **D-17 (Garcia rewrite split off), D-18 (EnumerationExceeded wired)** |
| WS-H | Probabilistic argumentation | OPEN | D, **O-gun**, **O-arg-gradual** | — | 9 (Codex #14-#17 + cluster F HIGH/MED) | DF-QuAD: paper contract decided first then test (Codex 2.7); WS-O-gun dependency for budget wiring (Codex 1.13) |
| **WS-O-gun-garcia** | gunray Garcia 2004 generalized specificity rewrite | OPEN | O-gun | M | new spec; replaces `not_defeasibly` semantics | **D-17 path**; TDD discipline — failing test first, passing test on each step (Codex 2.24); Garcia surface is exactly `yes/no/undecided/unknown`; two-PR scope — gunray-side rewrite + propstore-side coordinated step explicit (Codex 2.26) |
| WS-K | Heuristic discipline, layer-3 boundary, embedding identity | OPEN | E | N2 | 18 (T3.1, T5.1-T5.2 + cluster H HIGH/MED + cluster U layering) + H10/H11 + embedding identity | **D-8 (proposal_source_trust DROPPED; argumentation pipeline replaces)**; **D-19 (embedding model-key collisions — typed `EmbeddingModelIdentity` tuple)**; H10/H11 in-scope, no deferral (Codex 1.16) |
| **WS-K2** | Meta-rule extraction pipeline | OPEN | K | — | new spec; LLM extract → `proposal_rules` → human gate | **D-9 (LLM + proposal gate), D-10 (`knowledge/rules/<paper-name>/`)**; predicate-registration step explicit, no missing-skill reference (Codex 2.13); CLI tests for help/dry-run/propose/promote/unknown-id/no-commit-review (Codex 2.14) |
| WS-L | Merge non-commitment & sameAs | OPEN | E | — | 10 (T3.3-T3.4 + cluster I HIGH/MED) | — |
| WS-M | Provenance — Trusty URI / PROV-O / gunray boundary / truncated-hash audit | OPEN | E, **CM**, **O-gun** | — | 12 (T4.1-T4.7, Codex #27 + cluster M HIGH/MED) + truncated-hash sweep | consumes D-7 through WS-CM; **D-20 (truncated-hash audit — full content-hash identity, truncation display-only)**; migration command deleted per D-3 (Codex 1.4); single PROV-O path generated from one internal domain model (Codex 1.5); `return_arguments=True` default depends on WS-O-gun budget wiring (Codex 1.13) |
| ~~WS-N~~ | ~~Architecture / import-linter / contract enforcement~~ | **SUPERSEDED** | — | — | redirected | **D-26 split into WS-N1 + WS-N2.** Original D-3, D-4, D-5 land in WS-N1; layered-contract work lands in WS-N2. |
| **WS-N1** | Architecture immediate (no WS-K dependency) | OPEN | — | — | 5 (T0.3 partial, Codex #38-#40 CLI extraction, doc-drift, dead pyproject entry, `_canonical_json` collapse) | **D-3 (delete all shims), D-4 (WorldModel→WorldQuery via rope), D-5 (Verdict→GroundedClassification)**; **D-26 immediate side** — CLI ownership extraction, shim deletion, two renames, three duplicate `_canonical_json` collapse to `quire.hashing`, doc-drift sweep |
| **WS-N2** | Architecture layered (final six-layer contract) | OPEN | K, N1 | — | 3 (T5.3-T5.6, T5.8 final layered-contract enforcement; T0.3 negative-violation test) | **D-26 layered side** — `layered` import-linter contract over README's six layers; depends on WS-K's heuristic relocation finishing |
| WS-O-bri | bridgman fixes — `verify_equation` deleted | OPEN | — | P | 8 (cluster Q HIGH/MED + missing) | **D-13 (route to symbolic)**; deletion now, no deprecation period (Codex 2.27); `uv run` scripts replace bare `python -c` (Codex 2.28) |
| WS-O-ast | ast-equiv fixes | OPEN | — | (informal upstream of P) | 13 minus bytecode tier | **D-14 (delete bytecode tier)**; RD-1 through RD-4 resolved — real-domain assumptions, `extract_names` API, SymPy version-independent cache key (Codex 2.29); error handling locked — single typed `UNKNOWN` from `compare()` (Codex 2.30) |
| WS-P | CEL / units / equations | OPEN | O-bri, O-ast | — | 12 (T2.4, T2.12-T2.13, Codex #28-#34 + cluster G HIGH/MED) | inherits D-13; D-28 drops CEL spec ceremony; BYTECODE references removed per D-14 (Codex 1.9); definedness predicate `(value, defined)` replaces FreshConst-for-division (Codex 1.10); domain-aware test names + assertions for `log(xy)=log(x)+log(y)` etc. (Codex 1.11) |
| **WS-J2** | InterventionWorld (Pearl do, Halpern HP-modified) | OPEN (feature/research) | D, J | — | new spec; AC1/AC2/AC3 + SCM data structure | **D-11 path B**; **D-22** — feature/research stream, not on critical bug-fix path; escalates if downstream reliance discovered |

**Total findings closed when all WSes ship**: ~210 plus the WS-CM cycle-break and the property-based TDD gates. INDEX file does not count.

---

## Dependency graph

```
WS-A (foundation: schema parity + URI authority + reserved namespace)
 │
 ├── WS-CM (micropub canonical payload + Trusty URI identity)
 │    ├── WS-C
 │    ├── WS-E
 │    └── WS-M
 │
 ├── WS-B (render policy; D-21 hard error)
 │
 ├── WS-Q-cas (branch-head CAS) ◀── WS-O-qui
 │    ├── WS-C (sidecar atomicity; A + CM + Q-cas)
 │    │    └── WS-E (source/promote; A + C + CM + Q-cas)
 │    │         ├── WS-K (heuristic + arg-pipe + embed-identity)
 │    │         │    ├── WS-K2 (meta-rule extraction pipeline)
 │    │         │    └── WS-N2 (final layered contract; needs K + N1)
 │    │         ├── WS-L (merge)
 │    │         └── WS-M (provenance + truncated-hash sweep) ◀── WS-O-gun
 │    │                                                          └── WS-O-gun-garcia
 │    └── WS-E ──────────────────────┘
 │
 └── WS-N1 (immediate: shim delete, renames, CLI extract, _canonical_json collapse, doc-drift)
       (independent of WS-K — does NOT block on E/K)

WS-D (math naming: D-1 wbf, D-2 BetP)
 ├── WS-F (ASPIC bridge) ◀── WS-O-arg
 ├── WS-G (belief revision) ◀── WS-O-arg
 ├── WS-H (probabilistic) ◀── WS-O-gun, WS-O-arg-gradual
 ├── WS-I (ATMS)
 │    └── WS-J (overlay/hash; depends on I per Codex 2.8)
 │         └── WS-J2 (Pearl do; feature/research per D-22)
 │
WS-O-arg (HIGH bugs / kernel) ─── blocks ──┐
 ├── WS-O-arg-aba-adf (ABA+ flat / ADF AST)│
 ├── WS-O-arg-dung-extensions              │
 ├── WS-O-arg-vaf-ranking ──┐              │
 │    └── WS-O-arg-gradual ◀┘ (consumes RankingResult)
 │                                          ▼
 │                                         WS-F, WS-G
 │
WS-O-bri (bridgman) ─┐
WS-O-ast (ast-equiv) ┤
                     └── WS-P (CEL/units/equations)

WS-O-qui (quire) ── feeds → WS-Q-cas
                  → upstream of WS-N1's `_canonical_json` collapse step
```

**Critical-path chain (longest)**: A → Q-cas → C → E → K → N2. Six-deep (was five — added Q-cas and split N).

**Maximum concurrency at start**: about six truly independent streams once the foundation is staged: WS-A, WS-D, WS-O-qui, WS-O-arg, WS-O-bri, WS-O-ast. WS-Q-cas opens as soon as WS-A and WS-O-qui ship the primitives it consumes. WS-N1 is independent of WS-K and can run concurrently with the entire A/C/E chain — it just touches different code areas. Sub-streams (WS-J2, WS-K2, WS-O-arg-*, WS-O-gun-garcia) wait for their parent's API/contract to settle, but each is independent thereafter.

**Informal dependency arrows** (worth knowing):
- WS-I now formally unblocks WS-J (Codex 2.8); the old "informal" arrow upgraded to a hard dep.
- WS-O-arg explicitly blocks all four sub-streams (Codex 2.15).
- WS-O-arg-vaf-ranking explicitly blocks WS-O-arg-gradual on the ranking-convergence consumer/owner split (Codex 2.22).
- WS-O-gun blocks WS-M (Codex 1.13 — `return_arguments=True` default depends on budget wiring) and WS-H (probabilistic argumentation budget wiring).
- WS-O-gun HIGH bugs land before WS-O-gun-garcia rewrites grounding/defeasibility.
- WS-Q-cas's contract is the read-then-commit protocol — every WS that mutates branch state through propstore must conform; primary consumers are WS-C, WS-E, and (transitively) WS-M.

---

## What to read in what order

If you have ten minutes:
1. `../DECISIONS.md` — the 26 decisions that scope these workstreams.
2. `WS-A-schema-fidelity.md` — foundation; everything blocks on it (now also covers identity boundary per D-24).
3. `INDEX.md` (this file) — dependency graph.

If you have an hour:
1. WS-A
2. WS-B (privacy-class data leak; D-21 hard error)
3. WS-D (math naming; D-1, D-2; unblocks five downstream)
4. WS-N1 (independent quick wins: shims, renames, CLI extraction)
5. The cross-cutting `../REMEDIATION-PLAN.md`

If you're picking what to ship this week:
1. WS-A (foundation; expanded with D-24 identity-boundary section)
2. Then in parallel: WS-B, WS-D, WS-N1, WS-O-arg HIGH bugs, WS-O-bri, WS-O-ast, WS-O-qui
3. WS-Q-cas opens as soon as WS-A and WS-O-qui surface their primitives
4. WS-C + WS-E then proceed with branch-head CAS discipline in place

If you're an engineer about to start a fix:
1. Read the WS file your fix touches.
2. Read `../DECISIONS.md` for any decisions affecting that WS (status board's "Decisions applied" column points at the relevant D-numbers and Codex finding numbers).
3. Verify file:line citations are current — WS files were authored 2026-04-26 then revised in round 2; production may have advanced.
4. For new sub-streams (WS-J2, WS-K2, WS-N1, WS-N2, WS-Q-cas, WS-O-arg-*, WS-O-gun-garcia): if the spec text is thin, your first task is to fill it from the parent WS file plus the relevant decision text — not to start coding.
5. Write the failing test first.
6. Land each commit citing the finding ID.

---

## Q-decisions outstanding

All 26 decisions resolved; see `../DECISIONS.md` (D-1 through D-26).

---

## Outstanding external dependencies (not papers — specs, books, infrastructure)

Unchanged by round 2.

Direct-download (free, half-day to retrieve all four):
- **RFC 6920** "Naming Things with Hashes" (`ni://` URI scheme) — required for WS-M Step 1 finalization.
- **W3C PROV-O / PROV-DM / PROV-N** specifications — required for WS-M's single PROV-O path (Codex 1.5).
- **W3C OntoLex-Lemon** module specs (synsem, decomp, vartrans, lime) — needed for cluster L Lemon coverage but not required by any WS-A through WS-P spec text.
- **Google CEL specification** (`~/src/cel-spec`) — required for WS-P escape-sequence subset and operational semantics.

Books (purchase needed):
- **Walton, Reed, Macagno (2008) Argumentation Schemes** — for WS-F argument schemes / critical questions.
- **Pearl & Mackenzie (2018) Book of Why** — for WS-J2 (Pearl `do()` / Halpern HP-modified).
- **Spirtes, Glymour, Scheines (2000) SGS** — same context as WS-J2.

Paper-reader passes needed (papers retrieved, `notes.md` not yet authored):
- **Jøsang_2016 Subjective Logic** book — required for WS-D's parameterized operator audit and validates D-1, D-2.
- **Smets_Kennes_1994** TBM paper — required for WS-D pignistic resolution under D-2.
- **Cyras_2016 ABA+** — required for WS-O-arg-aba-adf flat ABA scope (Codex 2.20).
- **Polberg_2017 ADF thesis** — required for WS-O-arg-aba-adf AST representation lock (D-25).

---

## How "done means done" works (per WS, uniformly)

A workstream stays OPEN until:

1. Every finding row in its findings table has either (a) a green test in CI gating it, or (b) a `gaps.md` row removed.
2. The workstream's own gating sentinel test (`test_workstream_<id>_done.py`) flips from `xfail` to `pass`. For upstream-fix WSes (O-arg, O-gun, O-qui, O-bri, O-ast), upstream-sentinel and propstore-sentinel are separated per Codex 2.18 — both must flip.
3. The relevant Hypothesis/property-based gates from `../PROPERTY-BASED-TDD.md` are implemented or explicitly moved to a successor workstream with a named reason.
4. The STATUS line at the top of the WS file flips from `OPEN` to `CLOSED <sha>`.
5. `docs/gaps.md` records the closure under "Closed gaps" with the sha.

If any condition is false, the WS stays OPEN. There is no "we'll get to the property markers later." Either it's in scope and closed, or it's explicitly removed from the WS in the WS file (and moved to a successor) before declaring done.

---

## Coordination matrix (which WSes touch the same code area)

| Code area | Owning WS | Adjacent WSes that read/depend |
|---|---|---|
| `propstore/sidecar/schema.py` | A | C, every test |
| `propstore/uri.py` authority validation + `concept_ids.py` reserved namespace registry | A (D-24) | K, M, every IO boundary |
| `propstore/repository.py` branch-head-bound transaction (CAS primitive) | Q-cas (D-23) | C, E, M (all consumers of expected-head-threading) |
| `propstore/source/promote.py` | E | C (atomicity, D-6 reorder), L (merge), M (provenance shape), Q-cas (CAS discipline) |
| `propstore/source/finalize.py` | E indirectly | A, C, K — coordinate merge order; D-7 lives in WS-M now (Codex 1.3) |
| `propstore/web/*` | B | N1 (no CLI in app/owner) |
| `propstore/aspic_bridge/*` | F | D, O-arg, O-arg-aba-adf, O-arg-dung-extensions |
| `propstore/belief_set/*` | G | D, J; D-12 — wraps argumentation pkg, no resurrection |
| `propstore/world/atms.py` | I | F, J (now hard dep, Codex 2.8), J2, K, M |
| `propstore/world/hypothetical.py` → `overlay.py` | J | I (env serialization), G (revision), J2 (sibling, not subclass) |
| (new) `propstore/world/intervention.py` | J2 | J (shares overlay scaffolding), I (ATMS env severance), G |
| `propstore/heuristic/*` + heuristic-out-of-package | K | E, N1 (no relocation needed), N2 (relocation gate); D-8 deletes `derive_source_document_trust` |
| (new) `propstore/source_trust_argumentation/*` + `proposal_rules` family | K + K2 | both touch `core/row_types.py` (Opinion-typed `prior_base_rate`), `praf/engine.py:160`, `sidecar/passes.py:112` |
| `EmbeddingModelIdentity` typed tuple `(provider, model_name, model_version, content_digest)` | K (D-19) | `embed.py`, sidecar embedding registry |
| `proposal_predicates` family (predicate registration first-class) | K2 (Codex 2.13) | K argumentation pipeline consumers |
| `knowledge/rules/<paper-name>/` | K2 | mirrors claims layout (D-10); K consumes |
| `propstore/merge/*` | L | E, M |
| `propstore/provenance/*` + truncated-hash audit surfaces | M | A, E, O-gun (boundary), O-gun-garcia (defeasibility provenance shape); D-20 audit covers every short-hash identity site |
| `propstore/cel_*`, `dimensions`, `equation_*` | P | O-bri (D-13 routed to `verify_expr`), O-ast (D-14, BYTECODE removed) |
| `propstore/.importlinter` + `contracts.py` | N2 (final layered) | N1 (immediate), K (heuristic relocation gate), every WS |
| CLI ownership extraction (Codex #38-#40) + dead pyproject entries + doc-drift sweep | N1 | B (web has no CLI), every consumer |
| `propstore/opinion.py` | D | F, H, J, J2; D-1 numerator at `:475-478`; D-2 BetP at `world/types.py:1257-1259` |
| `RankingResult` / ranking-convergence proof harness | O-arg-vaf-ranking (Codex 2.22) | O-arg-gradual (consumer) |
| `../argumentation/` (external pin) | O-arg | F, G, H, four sub-streams; D-15 ship-as-PR, propstore re-pins |
| `../gunray/` (external pin) | O-gun | M, H, O-gun-garcia (Garcia rewrite ships as upstream PRs, pin bumps) |

Three WSes touch `propstore/source/finalize.py` (A indirectly, C, E, K). Coordinate the merge order. Micropub identity moved out (Codex 1.3) — WS-M is sole authority.

WS-D and WS-N1 both touch `propstore/world/types.py:1206`, `:1239`, `:1275-1281` — D for math under D-2, N1 for shim deletion under D-3. Coordinate.

Four sub-streams (WS-O-arg-aba-adf, WS-O-arg-dung-extensions, WS-O-arg-vaf-ranking, WS-O-arg-gradual) all live in `../argumentation` and coordinate at the dep-pin level — each ships as upstream PRs against the same baseline pin set by WS-O-arg HIGH bugs; propstore re-pins after each ships; downstream sub-streams rebase. D-15 governs the upstream policy; D-16 governs the split. WS-O-arg-vaf-ranking ships before WS-O-arg-gradual because gradual consumes `RankingResult` (Codex 2.22).

WS-K and WS-K2 share the source-trust + argumentation-pipeline boundary. K owns the kernel that produces calibrated Opinion-typed `prior_base_rate`; K2 owns the LLM-extraction → `proposal_rules` → human-promote path. Both touch `core/row_types.py` to lift `prior_base_rate` from float to Opinion (D-8). Land K's type lift first; K2's extraction pipeline writes against the lifted shape.

WS-N is split — WS-N1 lands the immediate work (shim deletion, renames, CLI extraction, `_canonical_json` collapse, doc-drift) without waiting on WS-K. WS-N2 lands the final six-layer `layered` import-linter contract after WS-K relocates the heuristic out of the package.

---

## What this index does NOT do

- It does not list every finding inside every WS — that's in the WS files themselves.
- It does not assign owners — that's a project-management decision. (Codex 2.1: each WS file replaces `Owner: TBD` with named owner or "Codex implementation owner + human reviewer required.")
- It does not promise dates — every WS lists "Done means done" but not "Done by when." D-16 explicitly notes the four argumentation sub-streams are "months of work, not weeks."
- It does not propose the order findings within a single WS should land — see each WS's "Production change sequence."
- It does not duplicate decision text from `../DECISIONS.md` — only the affected-WS column references decision IDs and Codex finding numbers.
- It does not duplicate the cross-check synthesis (`../CROSS-CHECK-vs-codex.md`) — that's the reviewer-vs-reviewer view; this is the workstream-vs-workstream view.

For the review behind these workstreams: `../INDEX.md` (cluster reports) and `../REMEDIATION-PLAN.md` (the synthesis that begat these workstream files).

For Codex's parallel review: `../../2026-04-26-codex/README.md` and `../../2026-04-26-codex/workstreams/`.
