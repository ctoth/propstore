# Remediation plan — propstore 2026-04-26

Source: Claude review (21 cluster reports) + Codex review (40 numbered findings, 7 workstreams) + cross-check synthesis.

This is the answer to four questions:
1. **Order**: in what sequence do we fix things, and why?
2. **Enforcement**: how do we ensure they get fixed, not just talked about?
3. **Resources**: what else (beyond papers) is missing?
4. **Workstreams**: yes — 16 of them, listed below.

---

## Part 1 — Fix order

The order is dictated by *what unblocks what* and *what hides bugs*. Three principles:

- **Test infrastructure must be true before any fix is verifiable.** If the test schema diverges from production, every "passing test" is a lie. Fix this first.
- **Privacy/security/data-leak before correctness, because the cost of delay is asymmetric.** A render-policy bypass leaking hidden claims has no good day-one mitigation.
- **Math/naming bugs before missing features.** A correct cite is worth more than a new operator built atop wrong primitives.

### Tier 0 — foundation (do these before anything else)

| # | Item | Reason | Source |
|---|---|---|---|
| T0.1 | **Test fixtures match production schema.** `tests/conftest.py:386 create_world_model_schema` must use `propstore/sidecar/schema.py` builders, not a hand-written copy. | Until this lands, every other "test passes" claim is unverifiable. | Codex #7 |
| T0.2 | **`_REQUIRED_SCHEMA["claim_core"]` includes runtime columns** (`build_status`, `stage`, `promotion_status`, `build_diagnostics`). | `WorldModel` selects on them; missing the columns is a latent runtime crash. | Codex #6 |
| T0.3 | **Negative test for import-linter.** Add `tests/architecture/test_import_linter_negative.py` that injects a known violation and asserts `lint-imports` rejects. | Currently the contracts catch nothing because they're vacuously satisfied; the test asserts only return-code 0. | Claude U |
| T0.4 | **Convert each high-finding into a failing test BEFORE the fix.** Per Codex's TDD shape: "First failing tests → production change → acceptance gate → done means." | A test is the only contract that survives memory loss. | Both reviews |

### Tier 1 — privacy / data-leak / atomicity

| # | Item | Reason | Source |
|---|---|---|---|
| T1.1 | **Render-policy enforcement on direct claim URL.** `/claim/{id}` returns 404/403/redacted when `visible_under_policy` is false. | Most urgent: if propstore is ever exposed beyond a single user, this leaks hidden draft/blocked claims. | Codex #8 |
| T1.2 | **Render-policy enforcement on neighborhood routes.** Filter `world.all_claim_stances()` through render policy. | Same class as T1.1; leaks supporter/attacker IDs and edges. | Codex #9 |
| T1.3 | **Render-policy enforcement on concept pages.** Don't disclose hidden claim counts or per-type blocked counts. | Same class. | Codex #10 |
| T1.4 | **`materialize` preflight conflict pass.** `storage/snapshot.py:201-216` accumulates conflicts but already wrote non-conflicting files. Either preflight, or write to a temp tree and atomic-rename. | Worktree corruption on conflict. | Codex #1 |
| T1.5 | **Read-only sidecar opens in read-only mode from the start.** `connect_sidecar` should accept a `read_only=True` flag; `query.py:21-30` passes it. | "Read-only" path currently creates WAL/SHM. | Codex #4 |
| T1.6 | **SQLite-before-git in `source/promote.py`.** Reorder so git commit precedes sidecar mirror writes, or scope `claim_core` PK by `(artifact_id, branch)`. | Failed promote can poison subsequent successful ones. | Claude A H2, Claude N |
| T1.7 | **`build_repository` re-raises sidecar errors.** Stop swallowing `FileNotFoundError`. | Reports success indistinguishable from "empty repo". | Claude N |
| T1.8 | **Web request-boundary float validation.** Reject NaN/inf/out-of-range at `web/requests.py:58-69`. | Bad floats reach app layer. | Claude K |
| T1.9 | **`pks web --host 0.0.0.0` requires `--insecure` flag.** Print a security warning. | No-auth knowledge browser exposed to LAN currently. | Claude K |

### Tier 2 — math / semantics correctness (corroborated)

These were caught by both reviews independently OR have explicit paper-citation evidence.

| # | Item | Reason | Source |
|---|---|---|---|
| T2.1 | **Asymmetric stance via symmetric contradiction.** `aspic_bridge/translate.py:139-193` maps `supersedes`/`undermines` to contradictory pairs, losing direction. | Both caught. Modgil/Prakken distinguish symmetric contradictories from asymmetric contraries. | Both, C1 |
| T2.2 | **AGM contraction collapses Spohn epistemic state.** `belief_set/agm.py:116-120` rebuilds via `from_belief_set`. | Both caught. Iterated revision should preserve ranking. | Both, C2 |
| T2.3 | **Micropub IDs content-derived.** `source/finalize.py:39-40` hashes only `(source_id, claim_id)`. | Both caught. Trusty/nanopub require content immutability. | Both, C3 |
| T2.4 | **CEL ternary type-rule.** Enforce boolean condition + branch-type unification. | Both caught. | Both, C4 |
| T2.5 | **Nested `ist`/`proposition` claims reach the pipeline.** Validation, sidecar, FTS must read nested propositions, not only top-level type. | Both caught. McCarthy/Guha context logic centers `ist(c,p)`. | Both, C5 |
| T2.6 | **AGM `K*2` for ⊥.** `revise(state, ⊥)` must signal inconsistency, not return original. Remove `assume(_belief(a).is_consistent)` test escape. | Claude only. K*2 is a foundational AGM postulate. | Claude C |
| T2.7 | **`opinion.wbf` rename or fix.** Pick one: implement van der Heijden 2018 WBF correctly, or rename to `acbf`. | Claude only + gaps.md HIGH. Worked example drifts 0.175. | Claude F |
| T2.8 | **`decision_criterion="pignistic"` rename.** Currently formula is Jøsang projected probability. Rename flag to `projected_probability`, or implement Smets/Denoeux BetP. | Claude only + gaps.md HIGH. | Claude F |
| T2.9 | **ASPIC grounded conflict-free.** `structured_projection.py:253` delegates to `argumentation.dung.grounded_extension` which ignores attacks. Fix delegation or change semantics. | Codex only. | Codex #12 |
| T2.10 | **`ideal_extension` correct semantics.** File upstream in `argumentation` pkg; admissibility isn't closed under union. | Claude only. | Claude P |
| T2.11 | **`aspic_encoding._literal_id` produces valid ASP identifiers.** `repr(literal)` produces `~p` and `p(1, 2)` which clingo rejects. | Claude only. | Claude P |
| T2.12 | **Z3 division guards scoped per-subexpression**, not conjoined globally. `core/conditions/z3_backend.py:121` and `z3_conditions.py:252,410`. | Codex only. Boolean semantics are wrong. | Codex #29 |
| T2.13 | **CEL float exponent + escape sequences.** `propstore/cel_*` parser gaps. | Claude only. | Claude G |

### Tier 3 — non-commitment / disagreement-collapse

| # | Item | Source |
|---|---|---|
| T3.1 | `relate.dedup_pairs` collapses bidirectional embedding distance | Claude H, gaps.md |
| T3.2 | `source/finalize.py` rewrites authored payloads in place | Claude A, gaps.md |
| T3.3 | `merge/_semantic_payload` strips provenance from assertion-id hash | Claude I |
| T3.4 | Union-find sameAs collapse with no quality filter | Claude I |
| T3.5 | `source/promote.py:711-727` justification filter admits dangling refs | Claude A |
| T3.6 | `source/alignment.py:96-98` defaults to `non_attack` | Claude A |
| T3.7 | `source/registry.py:42-47` alias collisions silently merge | Claude A |
| T3.8 | Micropubs silently dropped for context-less claims | Claude A |
| T3.9 | `worldline/argumentation.py:107-111` silently discards multi-extension | Claude J |
| T3.10 | `aspic_bridge` rules with inactive premise/conclusion silently dropped | Claude D, U |
| T3.11 | `classify.py:389` whole-response-as-forward fallback | Claude H |

### Tier 4 — provenance gaps

| # | Item | Source |
|---|---|---|
| T4.1 | gunray boundary preserves `DefeasibleTrace` and rule-id back-pointers | Claude B, D, M, R |
| T4.2 | Trusty URI verification implemented (Kuhn 2014) | Claude M |
| T4.3 | PROV-O serializer (Moreau 2013) | Claude M |
| T4.4 | `storage/repository_import.py` annotates imported rows with provenance | Claude U |
| T4.5 | `compose_provenance` preserves causal order, drops alphabetical sort | Claude M |
| T4.6 | `WhySupport.subsumes` rename or fix to match behavior | Claude M |
| T4.7 | Semiring polynomial provenance not collapsed to ATMS why-labels prematurely | Codex #27 |

### Tier 5 — architecture decoration

| # | Item | Source |
|---|---|---|
| T5.1 | Heuristic logic moves into `propstore/heuristic/` (or rename Layer 3) | Claude U |
| T5.2 | `derive_source_document_trust` routed through proposal/promote gate | Claude H, U |
| T5.3 | Replace four `forbidden` import-linter contracts with `layered` | Claude U |
| T5.4 | App-layer request objects don't accept CLI-shaped payloads | Codex #38, #39 |
| T5.5 | Owner modules don't write to stderr or own argv parsing | Codex #40 |
| T5.6 | Three duplicate `_canonical_json` implementations collapse to one | Claude S |
| T5.7 | `aspic_bridge/query.py:13` stops importing `_contraries_of` private | Claude D |
| T5.8 | Delete every shim per "no old repos" rule (CONFIDENCE_FALLBACK, _CONCEPT_STATUS_ALIASES, etc.) | Claude U |

### Tier 6 — research/spec spikes (need design before patch)

| # | Item | Why design first |
|---|---|---|
| T6.1 | Pearl SCM / `do()` operator (cluster J) | `HypotheticalWorld` is named like one but isn't; either rename or implement. Needs Pearl_Mackenzie_2018 or SGS_2000 first. |
| T6.2 | CEL operational semantics + soundness theorem (cluster G) | Pierce-style small-step rules document; without it, type-system patches are guessed. Needs CEL spec. |
| T6.3 | Forbus incremental ATMS (cluster E) | Multi-week rewrite of `world/atms.py`; current global-rebuild has known perf cost. |
| T6.4 | DeLP generalized specificity / Bozzato CKR (cluster B) | Algorithmic content of papers (Garcia 2004, Bozzato 2018) to lift in. We have both. |
| T6.5 | AGM-AF revision integration (cluster C) | `belief_set/af_revision.py` is gone; ownership question. |
| T6.6 | ABA / ADF coverage in argumentation pkg (cluster P) | Cyras_Toni_2016 (retrieved) and Polberg_2017 (retrieved) are now on disk. |
| T6.7 | Subjective-logic operator-name ↔ formula full audit (cluster F) | Half-day with Jøsang_2016 (on disk). |

### Tier 7 — coverage / feature gaps (lowest urgency, highest scope)

These are paper-implements gaps the codebase hasn't even tried. Don't start until Tiers 0-3 are clear.

- ABA implementation
- ADF implementation
- Bench-Capon VAF
- Caminada semi-stable
- Reiter default logic
- McCarthy circumscription
- Brewka ADF (some overlap with ADF above)
- PROV-O full serializer (overlaps T4.3)
- Replication-comparison data structure for Border 2019 / Horowitz 2021 case studies

---

## Part 2 — How we make sure things get fixed (not just talked about)

Reviews die in markdown unless three mechanisms are in place. All three exist in propstore already; none are wired up to absorb this review.

### Mechanism 1: TDD-first per finding

**Rule**: every numbered finding above gets a failing test BEFORE the fix.

The test is the contract. If the test isn't written first, the fix can't be verified, and "we already fixed that" becomes folk memory.

Codex's workstream files use this shape exactly: every workstream has a "First failing tests" section. Adopt that for *every* finding, not just the seven Codex picked.

**Concrete**: each finding ID (T0.1, T1.1, etc.) becomes a single failing test, named `test_T<n>_<m>_<short_name>`. The test file references the cluster report and Codex finding number in its docstring. The commit that lands the fix references the test name and finding ID.

This pattern already exists in `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py`. Extend the convention.

### Mechanism 2: `gaps.md` is the single source of open-state truth

`docs/gaps.md` already tracks open gaps. Extend it to absorb the new findings:

- Each Tier 0–7 item gets a `gaps.md` entry with: ID, severity, file:line, "first failing test" path, plan reference (workstream below), status (open/in-progress/closed).
- A `tests/test_gaps_md_consistency.py` (new) parses `gaps.md`, walks each "first failing test" path, asserts the test exists. So `gaps.md` can't lie about what's tested.
- When a fix lands, the workstream PR does three things in one commit: makes the failing test pass, removes the entry from `gaps.md`, updates the workstream's "Done means" line.
- A weekly self-review (Q + agent) reads the open `gaps.md` rows and decides "still open" or "stale, close." This prevents drift.

### Mechanism 3: workstream files in `reviews/` rot if not updated

Codex's workstream files are *plans*, not status documents. They will rot once the plans are followed. To avoid this:

- Workstream files become read-only once the workstream is opened.
- Per-workstream progress lives in `gaps.md` (per Mechanism 2) or in commit messages.
- A workstream is "complete" when every finding it covers is closed in `gaps.md` AND the corresponding tests are green AND a final commit on the workstream branch flips a `STATUS:` line at the top of the workstream file from `OPEN` to `CLOSED <sha>`.
- `tests/test_workstream_consistency.py` (new) asserts every CLOSED workstream's findings are also closed in `gaps.md`. So a CLOSED workstream can't have lingering open findings.

### Anti-patterns to avoid

- **"I'll get to it"** — every item not landed within 4 weeks of file-time should be re-triaged. If still not landed at 8 weeks, it gets demoted to Tier 7 (low priority) explicitly.
- **"Refactor this whole module"** — every workstream change is the *minimum* change to flip its tests green. Refactor lives in a separate workstream.
- **"Add a comment / TODO"** — TODO is a four-letter word in this codebase. AGENTS.md already says no comments-as-process. The fix lands or it doesn't.
- **Compatibility shims** — Q's "no old repos, iterating to perfection" rule means every shim (`CONFIDENCE_FALLBACK`, `_CONCEPT_STATUS_ALIASES`, etc.) gets ripped out, callers updated in the same PR.

---

## Part 3 — What other resources are missing (beyond papers)

The papers list was in `papers-2026-04-26.md`; 16 of 20 retrieved. Other resources we lack:

### Test infrastructure

- **Property-marker discipline**: Codex flagged that many Hypothesis tests aren't `@pytest.mark.property`. `pytest -m property` underselects. Fix: a `tests/test_marker_discipline.py` that walks every `@given(...)` and asserts `pytest.mark.property` is on the same function.
- **Schema generation pipeline**: `propstore/_resources/schemas` is absent; tests tolerate conditional copying. Fix: make `schema/generate.py` idempotent and CI-required.
- **Negative tests for `lint-imports`** (mentioned in Tier 0).
- **Determinism corpus for content-hashing**: a fixture pack that exercises every error path of `worldline/runner` to ensure hashes don't flip on transient errors.
- **Performance benchmarks**: gunray exponential, ic_merge O(2^n), quadratic concept matching — none measured. Add `tests/perf/` with budget assertions.
- **a11y test suite**: Q is blind; cluster K listed gaps but no automated suite. `pa11y` or `axe-core` against the web routes.

### Architectural artifacts

- **Diagrams that match reality**: README's six-layer diagram is materially false on Layer 3 location. Either move modules or redraw.
- **Public API surfaces explicit per dep**: quire `__init__.__all__` doesn't expose `quire.artifacts.*` etc. that propstore uses — promote those, or refactor consumers.
- **Pre-promote dry-run mode**: `pks source promote --dry-run` showing the planned diff would catch SQLite-before-git issues at author time.
- **Render-policy enforcement helper**: a single function `enforce_render_policy(world_query_result, policy)` that every web route MUST call. Currently each route filters ad-hoc.
- **A `proposal_source_trust` family**: parallel to `proposal_stances`, gates `derive_source_document_trust` writes (Tier 5.2).

### Documentation that doesn't lie

- `algorithms.md` and `aspic.md` reference modules that don't exist (Claude U). Move to `docs/historical/` or delete.
- `docs/application-layer-and-undo.md` describes a package that doesn't exist (Claude K). Same.
- `docs/structured-argumentation.md:26` honestly admits "rules silently dropped" — fix the behavior, not the doc.
- `gaps.md` has stale line numbers (Claude U). Auto-regenerate from a script that walks the citations.

### Tooling

- **Citation-as-claim CI lint**: gaps.md mentions this as planned. Implement: a script that walks every `#` comment and docstring citing a paper, verifies the citation matches the bibtex key in `papers/<dir>/`, fails CI on mismatch.
- **Cross-repo regression suite**: when `argumentation`, `gunray`, `quire`, `bridgman`, or `ast-equiv` upgrade, propstore tests must run against the new pin first. A `scripts/upgrade_dep.py` automates.
- **PROV-O fixture corpus**: zero PROV-O instances exist; need fixtures before serializer.
- **A "vapor" detector**: walk `pyproject.toml` strict list, README links, doc references — flag anything pointing at a path that doesn't exist. `pyproject.toml:65 propstore/aspic_bridge.py` would have caught itself.

### Ongoing review cadence

- **Quarterly multi-reviewer check**: every quarter, run a Codex+Claude review like this one against current master. Drift catches itself.
- **Per-merge architecture-gate**: `lint-imports` with the layered contract from T0.3 + T5.3.
- **Memory file freshness**: project-memory entries decay. A `notes/memory-audit-YYYY-MM-DD.md` per quarter.

---

## Part 4 — Workstreams

Yes, this becomes workstreams. Codex started 7; Claude's findings extend that to 16. The shape: each workstream has an ID, the findings it covers, dependencies, first failing test, production change sequence, acceptance gate, "Done means."

### WS-B: Render-policy / web data-leak (Codex ws-01 absorbed)
- **Findings**: T1.1, T1.2, T1.3, T1.5, T1.8, T1.9, Codex #11
- **Depends on**: WS-A (schema parity)
- **First failing test**: `tests/test_render_policy_direct_url.py` asserts hidden claim returns 403.
- **Done means**: every web route filters through `enforce_render_policy` helper; integration tests cover hidden/visible/blocked across `/claim`, `/concept`, `/neighborhood`, `/search`.

### WS-C: Sidecar atomicity & SQLite discipline (Codex ws-03 absorbed)
- **Findings**: T1.4, T1.5, T1.6, T1.7, Codex #1, #2, #3 (overlap T2.3), #4, #5
- **Depends on**: WS-A
- **First failing test**: `tests/test_promote_atomicity.py` simulates git failure, asserts no orphan sidecar rows.
- **Done means**: promote is atomic across git+sidecar; materialize is preflight-or-temp; read-only paths can't create WAL.

### WS-A: Schema fidelity & test-fixture parity (Codex ws-02 absorbed) — **FOUNDATION**
- **Findings**: T0.1, T0.2, Codex #6, #7
- **Depends on**: nothing
- **First failing test**: `tests/test_schema_parity.py` asserts `tests/conftest.py:create_world_model_schema` outputs identical SQL to `propstore/sidecar/schema.py`.
- **Done means**: `_REQUIRED_SCHEMA` covers every column production uses; test fixtures call production schema builders directly; CI fails on divergence.
- **NOTE**: nothing else lands until this workstream completes. Foundation.

### WS-E: Source-promote and finalize correctness
- **Findings**: T1.6, T3.5, T3.6, T3.7, T3.8, Claude A H1/H3/H4/H5
- **Depends on**: WS-C, WS-A
- **First failing test**: `tests/test_source_promote_dangling_refs.py` asserts justification with cross-batch conclusion is rejected, not promoted.
- **Done means**: every Cluster A HIGH closed; gaps.md axis-1 findings 1.2 and 1.3 closed.

### WS-D: Math/operator naming and correctness
- **Findings**: T2.7, T2.8, gaps.md WS-Z-types continuation
- **Depends on**: nothing
- **First failing test**: `tests/test_subjective_logic_operator_audit.py` asserts every operator's name matches Jøsang_2016 chapter and the worked example matches the book's value to ≤1e-6.
- **Done means**: `opinion.py` operator names + formulas are line-by-line traceable to Jøsang_2016 with citations; pignistic/projected_probability disambiguated.

### WS-F: ASPIC bridge fidelity
- **Findings**: T2.1, T2.9, T2.11, Claude D HIGH 1/2/3/4/5/6/7, T5.7
- **Depends on**: WS-D (preference operator naming may overlap)
- **First failing test**: `tests/test_aspic_grounded_conflict_free.py` pins the test Codex flagged at `test_structured_projection.py:688` and asserts grounded extension is conflict-free over attacks.
- **Done means**: Modgil 2014 §4.2 indirect consistency theorem holds; well-formedness preflight in place.

### WS-G: Belief-revision postulate coverage
- **Findings**: T2.2, T2.6, all Claude C HIGH/MED postulate gaps, Codex #18, #19, #20
- **Depends on**: WS-D (Spohn vs ranking representations may overlap)
- **First failing test**: `tests/test_agm_K_star_2_inconsistent_input.py` asserts `revise(state, ⊥)` signals inconsistency, not return original.
- **Done means**: K*1-K*8, K-1 through K-8, IC0-IC8, CR1-CR4, C1-C4 all tested for `revise`/`contract`/`merge`; AF revision distinguishes "no stable" from "empty stable."

### WS-H: Probabilistic argumentation
- **Findings**: Codex #14, #15, #16, #17, Claude F HIGH (defeat-summary, OAT, no Brier)
- **Depends on**: WS-D (operator naming)
- **First failing test**: `tests/test_praf_uncalibrated_explicit.py` asserts uncalibrated arguments are surfaced as ignorance, not silently dropped.
- **Done means**: PrAF backends route per advertised semantics; raw confidence ≠ dogmatic; DF-QuAD support/attack symmetric.

### WS-I: ATMS / world correctness
- **Findings**: Claude E HIGH (≤8 subsets, _was_pruned cycles, non-numeric drop), Codex #24, #25, #26
- **Depends on**: WS-D (CEL semantic equality may overlap)
- **First failing test**: `tests/test_atms_derived_contradictions.py` asserts derived-vs-derived contradictions become nogoods.
- **Done means**: context-bearing envs serialized fully; CEL support uses semantic equality; bounded-replay claims stop overstating.

### WS-J: Worldline / causal / hashing
- **Findings**: Claude J HIGH (hashing repr, HypotheticalWorld, multi-extension, replay determinism overstatement)
- **Depends on**: WS-D (subjective logic and Spohn integration)
- **First failing test**: `tests/test_worldline_hash_stability.py` injects transient errors and asserts content hash is stable.
- **Done means**: strict canonical JSON (no `default=str`); HypotheticalWorld either renamed or implements do(); multi-extension preserved.

### WS-K: Heuristic discipline & layer-3 boundary
- **Findings**: T3.1, T5.1, T5.2, all Claude H HIGH, Claude U layering finding
- **Depends on**: WS-E (proposal lifecycle infrastructure)
- **First failing test**: `tests/test_layered_import_contract.py` asserts heuristic modules can't import Layer 1 storage writers.
- **Done means**: heuristic logic lives under `propstore/heuristic/`; `derive_source_document_trust` goes through `proposal_source_trust` family; `dedup_pairs` keeps both directions.

### WS-L: Merge non-commitment
- **Findings**: T3.3, T3.4, all Claude I HIGH/MED
- **Depends on**: WS-E (provenance-in-assertion-id requires source/promote provenance)
- **First failing test**: `tests/test_merge_corroboration_preserved.py` asserts two papers asserting the same statement produce two arguments, not one.
- **Done means**: assertion-id includes provenance; sameAs is graded not transitive-closure; structured merge has IC4 fairness test.

### WS-M: Provenance — Trusty URI / PROV-O / gunray boundary
- **Findings**: T4.1, T4.2, T4.3, T4.4, T4.5, T4.6, T4.7, Codex #27
- **Depends on**: WS-E, RFC 6920 + W3C PROV specs (need to retrieve; in `papers-2026-04-26.md` pending list)
- **First failing test**: `tests/test_trusty_uri_verification.py` asserts every emitted `ni:///sha-1;...` URI's hash matches the content.
- **Done means**: Trusty URI verification on; PROV-O serializer emits Activity/Entity/Agent; gunray boundary preserves DefeasibleTrace; semiring polynomial provenance kept distinct from ATMS labels.

### WS-N: Architecture / import-linter / contract enforcement (Codex ws-07 absorbed)
- **Findings**: T0.3, T5.3, T5.4, T5.5, T5.6, T5.8, Codex #38, #39, #40
- **Depends on**: WS-K (heuristic location)
- **First failing test**: `tests/test_import_linter_negative.py` (T0.3) plus `tests/test_app_layer_no_cli_payloads.py`.
- **Done means**: layered contract over six README layers with negative test; app modules don't accept CLI shapes; owner modules don't write to stderr; shims deleted.

### WS-O: Dependency package fixes
This is actually 5 sub-streams — one per dep. Run in parallel.
- **WS-O-arg**: argumentation pkg (Claude P findings; T2.10, T2.11)
- **WS-O-gun**: gunray (Claude R findings; T4.1 cross-link)
- **WS-O-qui**: quire (Claude S findings; T5.6 cross-link)
- **WS-O-bri**: bridgman (Claude Q findings; T2.5 cross-link via dims_of_expr)
- **WS-O-ast**: ast-equiv (Claude T findings; Codex #33 cross-link)
- **Depends on**: nothing internal; each dep is independent.
- **First failing test**: per-dep test suite in each repo.
- **Done means**: every Claude finding under cluster P/Q/R/S/T closed in the respective repo; propstore pin updated.

### WS-P: CEL / units / equations (Codex ws-04 absorbed)
- **Findings**: T2.4, T2.12, T2.13, Claude G HIGH (affine temp, equation comparison), Codex #28, #31, #32, #33, #34
- **Depends on**: local CEL spec reference at `~/src/cel-spec` (ordinary implementation reference, not a workstream)
- **First failing test**: `tests/test_cel_ternary_unification.py`.
- **Done means**: CEL has explicit operational semantics doc; ternary unsoundness fixed; equation comparison orientation-insensitive; Z3 guards scoped per-subexpression.

### Workstream dependency graph

```
WS-A (foundation)
 ├── WS-B (render policy)
 ├── WS-C (sidecar atomicity)
 │    └── WS-E (source/promote)
 │         ├── WS-K (heuristic)
 │         ├── WS-L (merge)
 │         └── WS-M (provenance)
 ├── WS-D (math naming)
 │    ├── WS-F (ASPIC)
 │    ├── WS-G (belief revision)
 │    ├── WS-H (probabilistic)
 │    ├── WS-I (ATMS)
 │    └── WS-J (worldline)
 ├── WS-N (architecture) -- depends on WS-K
 ├── WS-O-{arg,gun,qui,bri,ast} (deps, parallel, no internal deps)
 └── WS-P (CEL, reads local spec at ~/src/cel-spec)
```

WS-A ships before anything else. Then WS-B, WS-C, WS-D ship in parallel. Everything else is gated on those three.

---

## Part 5 — The actually-concrete next step

This week, in order:

1. **Land WS-A** (schema parity). Two days. Foundation for the rest.
2. **Open `gaps.md` rows** for every Tier 0–3 item above with the first-failing-test path filled in. One day.
3. **Land WS-B's first finding (T1.1, direct claim URL leak)**. Half day. Use as the template for every subsequent fix: failing test in commit 1, fix in commit 2, gaps.md row removed in commit 3.
4. **Retrieve the four pending specs** (RFC 6920, W3C OntoLex modules, W3C PROV, Google CEL spec). They unblock WS-M and WS-P and aren't books-to-buy. Half day.
5. **Open WS-B, WS-C, WS-D, WS-O-arg in parallel branches.** Each gets a worktree, a workstream tracker file, and a target merge date.
6. **Memory entry**: add a feedback memory `feedback_workstream_discipline.md` capturing the rules in Part 2 (TDD-first, gaps.md as truth, workstream files become read-only).

The strongest signal that this plan is working: in two weeks, `gaps.md` has more closed items than it had open items today, and the line-numbers in the open items are still accurate.

The strongest signal that this plan is failing: in two weeks, this file is being re-read instead of executed, and the cross-check has produced more workstreams than fixes.
