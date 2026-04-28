# Decisions log — 2026-04-27

Decisions made by Q on the open questions surfaced across all 20 workstreams. Authoritative when the WS files conflict with this document.

Decisions in order asked.

---

## Math / operator naming

### D-1 — `opinion.wbf()` math

**Question**: rename to acbf (lazy fix) or implement true van der Heijden 2018 Definition 4 (paper-faithful)?
**Q's pushback**: "What do those callers actually expect? if they expect WBF, give them WBF, don't just do the easy thing."
**Decision**: **Fix to true WBF** per vdH 2018 Def 4.

**Reasoning**: docstring at `opinion.py:432-441` already promised vdH 2018 Def 4 verbatim. Three call sites total (`fragility_scoring.py:359` + two internal in `opinion.py:693, 698`). Caller intent and docstring contract both demand WBF. Renaming would be deceiving the docstring instead of fixing the code.

**Affects**: WS-D
**Action**: replace numerator math at `opinion.py:475-478` so terms are `b_i / u_i × prod_except_i` not `b_i × prod_except_i`. Re-validate fragility_scoring.py expected outputs.

### D-2 — `decision_criterion="pignistic"` math

**Question**: rename to projected_probability (lazy fix), or implement true Smets/Denoeux BetP, or add separate flags?
**Q's pushback**: "what do the callers actually think they are getting again? why is this such a weird/hard concept? What does the paper say?"
**Decision**: **Fix to true BetP under 'pignistic'** (b + u/2 distributed by base rate). Add `projected_probability` as a new flag value covering the current Jøsang formula.

**Reasoning**: CLI exposes `pignistic / lower_bound / upper_bound / hurwicz` as coordinated decision criteria. Users selecting "pignistic" expect *the* Smets/Denoeux pignistic transformation. The Vasilakes_2025 notes confirm `b + a·u` is "Projected Probability" in the Jøsang lineage, not pignistic. Two transformations are real and distinct; both must be reachable under their correct names.

**Affects**: WS-D
**Action**: at `world/types.py:1257-1259`, change formula to BetP and update Smets_Kennes_1994 citation. Add `projected_probability` flag value to the CLI Choice list and consumer dispatch. Re-validate every test corpus exercising the flag.

---

## Architecture / naming

### D-3 — Old-data shims

**Question**: keep, document, or delete entirely?
**Decision**: **Delete all, no carve-out**.

**Affects**: WS-N
**Action**: rip in one pass — `_CONCEPT_STATUS_ALIASES`, `DecisionValueSource.CONFIDENCE_FALLBACK` (enum value + path), `world/types.py:1275` old-data fallback path, `classify.py:389` "fallback to whole response as forward", `grounding/grounder.py:141-149` "backwards compatibility" block, `pyproject.toml:65` dead `aspic_bridge.py` strict entry. Update callers; no aliases.

### D-4 — `WorldModel` rename

**Decision**: **Rename to `WorldQuery`** via rope.

**Affects**: WS-N (and every consumer). Q noted "we have rope" — use it for the mechanical refactor.
**Action**: `from propstore import WorldModel` → `WorldQuery` everywhere. Several hundred call sites. Single PR via rope-driven rename. No legacy alias.

### D-5 — `Verdict` rename

**Decision**: **Rename to `GroundedClassification`**.

**Affects**: WS-N
**Action**: `grounding/grounder.py:42, 102` and `sidecar/rules.py:20, 129, 243` rename via rope.

---

## Storage / atomicity / lifecycle

### D-6 — Promote ordering (sidecar vs git)

**Decision**: **Reorder — git transaction first, sidecar mirror after**.

**Affects**: WS-C, WS-E
**Action**: at `source/promote.py`, move sidecar mirror writes (currently lines :518-548, :573, :840-851) to AFTER `repo.families.transact(...)` succeeds. If git fails, no sidecar mutation. If sidecar fails after git, sidecar can be rebuilt from git state. Diagnostics that were on the sidecar-leads-git path become return values from the promote function instead of persisted state.

### D-7 — Micropub identity

**Decision**: **Content-derive: hash full canonical payload** per Kuhn 2014 Trusty URI.

**Affects**: WS-CM, WS-C, WS-M
**Action**: create **WS-CM-micropub-identity.md** as the shared prerequisite workstream for the canonical micropub payload and Trusty URI identity. At `source/finalize.py:38-40` (`_stable_micropub_artifact_id`), replace `(source_id, claim_id)` hash with a Trusty URI over the full canonical micropub payload. Sidecar dedupe (`sidecar/micropublications.py:17-57`) becomes safe. Modified micropubs get new IDs (which is correct per Kuhn 2014 — they're new versions). No placeholder hash, no temporary production identity surface, and no WS-C/WS-M cycle: WS-C and WS-M both consume WS-CM.

### D-8 — Trust calibration as argumentation

**Question**: should trust calibration be a Layer-3 heuristic, a Layer-4 argumentation pipeline, or authored-only?
**Q's framing**: "how do we get trust coming from within the system? like: I want Ioannidis 2005 to be ingested then everything use it and so on?"
**Decision**: **Argumentation pipeline replaces the heuristic.**

**Mechanism**:
1. Meta-papers (Ioannidis_2005, Begley_2012, Aarts_2015, Errington_2021, Camerer_2016/2018, Klein_2018, Border_2019, Horowitz_2021, etc.) ingest via existing `paper-process`.
2. Their propositions extract to ordinary claims.
3. Those claims author **rules** — predicates over paper metadata (sample_size, replication_status, field_heat, effect_size_z, etc.).
4. Trust calibration runs the argumentation kernel (DeLP/ASPIC) for each source: rules + source metadata + world's claim graph → Opinion-typed `prior_base_rate` with full Provenance referencing every meta-claim and rule that fired.
5. Output is persisted on the source branch as **authored content**, but the author is the argumentation kernel itself (Layer 4), not a Layer 3 heuristic.
6. Propagation everywhere else is automatic — every downstream consumer that already takes an Opinion gets the calibrated value.

**Affects**: WS-K (replaces the proposal_source_trust family design — calibration is no longer a heuristic, so no proposal gate is needed; the output is first-class authored content).

**Action**:
- Delete `derive_source_document_trust` from `propstore/heuristic/source_trust.py`.
- New pipeline: `propstore.source_trust_argumentation` (or similar) consuming meta-paper rules and producing Opinion outputs.
- Lift `prior_base_rate` from float to Opinion across `core/row_types.py`, `praf/engine.py:160`, `sidecar/passes.py:112`, every consumer.
- The argumentation pipeline runs at promote time; output is persisted on the source branch with explicit provenance.

### D-9 — Meta-paper rule extraction

**Question**: hand-author per paper, or LLM-extract with iteration?
**Q's framing**: "if we can't trust the system, then we can't trust the system. If LLM extraction fails, then we need to iterate until it succeeds."
**Decision**: **LLM-extraction pass with proposal-review gate; iterate the prompt until extraction produces rules that survive promotion.**

**Affects**: WS-K + new sub-stream (call it WS-K2 — meta-rule extraction pipeline).
**Action**:
- Use the existing classify/extract pipeline against meta-papers.
- Surface proposed rules as proposals on a new `proposal_rules` family, parallel to `proposal_stances`.
- Human reviews, promotes selectively.
- Iterate the extraction prompt until extraction produces high-quality rules that survive promotion at scale.
- This is the system's own discipline applied to itself.

### D-10 — Meta-paper rule layout in knowledge tree

**Decision**: **`knowledge/rules/<paper-name>/` per source** — mirrors the claims layout.

**Affects**: WS-K2
**Action**: rule_id includes source paper name. Each meta-paper authors its own rule corpus. Provenance is structural.

---

## Semantic-scope decisions

### D-11 — `HypotheticalWorld` rename + Pearl do()

**Decision**: **Both — rename to `OverlayWorld` AND add separate `InterventionWorld` that does Pearl do()**.

**Affects**: split into two workstreams.
- **WS-J (existing)**: determinism + hashing + multi-extension + rename to OverlayWorld. Stays a determinism/hashing review. No Pearl semantics yet.
- **WS-J2 (new)**: implement `InterventionWorld` per Pearl 2000 / Halpern 2015 HP-modified actual cause. Sever parameterization edges feeding intervened concepts. Build SCM data structure. AC1/AC2/AC3 actual-cause definition.

### D-12 — AGM-AF revision ownership

**Decision**: **Keep AGM-AF revision in `argumentation` package; propstore consumes via public API only**.

**Affects**: WS-G, WS-O-arg
**Action**: Codex finding #20 (`af_revision.py:274` empty-vs-no-stable conflation) becomes a fix in the argumentation package as part of WS-O-arg. propstore's belief_set wraps for projection into propstore data shapes. No `propstore/belief_set/af_revision.py` resurrection.

### D-13 — `verify_equation` (bridgman)

**Decision**: **Demote `verify_equation`; route everything to symbolic API**.

**Affects**: WS-O-bri, WS-P
**Action**: mark `verify_equation` deprecated in bridgman, then delete in next minor version. Move propstore callers to `verify_expr` (which handles Pow/Add/transcendentals once HIGH-2 lands). One canonical dim-checking entry point.

### D-14 — Bytecode tier (ast-equiv)

**Decision**: **Delete now, preserve git history for resurrection** if a future use case appears.

**Affects**: WS-O-ast, WS-P
**Action**: remove `_compile_to_bytecode` and `Tier.BYTECODE` enum value. The surviving enum is exactly `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`. `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL` are proof-strength equivalence tiers; `NONE` is the undecided fallback and must not suppress conflicts. Notes confirm zero corpus loss. Document recovery path in deletion commit message.

---

## Dependency-package policy

### D-15 — `argumentation` upstream policy

**Decision**: **Fix in argumentation upstream; propstore pin updates after each**.

**Affects**: WS-O-arg
**Action**: each cluster-P HIGH bug becomes a PR in `../argumentation` with its own first-failing test in `argumentation/tests/`. propstore pin bumps when the dep ships. propstore-side test corpus re-runs against the new pin. No wraps. No fork.

### D-16 — `argumentation` coverage gaps

**Decision**: **All four groups — implement everything**.

**Affects**: WS-O-arg expands significantly. Likely needs to split into:
- **WS-O-arg-bugs** (the existing HIGH bugs)
- **WS-O-arg-aba-adf** (Group A: Cyras 2016 ABA+ + Polberg 2017 ADF)
- **WS-O-arg-dung-extensions** (Group B: eager, stage2, prudent, semi-stable, bipolar grounded/complete, Caminada labelling-as-semantics operational)
- **WS-O-arg-vaf-ranking** (Group C: Bench-Capon VAF + Bonzon ranking family)
- **WS-O-arg-gradual** (Group D: DF-QuAD discontinuity-free + Matt-Toni 2008 game-theoretic)

These run in parallel since they're independent kernels. All papers retrieved.

**Scope honesty**: this is months of work, not weeks. Acknowledge scope in the workstream files; let timeline emerge from sequencing.

### D-17 — gunray `not_defeasibly` semantics

**Decision**: **Replace with Garcia 2004 generalized specificity properly**.

**Affects**: WS-O-gun expands significantly.
**Action**: major rewrite of gunray's grounding/defeasibility module to implement Garcia 2004 with full generalized specificity, proper-vs-blocking defeaters. Highest-fidelity path to the cluster-B preferred reference. Probably warrants a sub-stream WS-O-gun-garcia separated from the existing-bugs WS-O-gun.

### D-18 — gunray `anytime.EnumerationExceeded`

**Decision**: **Wire it up — callers handle as budget-exhaustion signal**.

**Affects**: WS-O-gun
**Action**: gunray.evaluate gains `max_arguments` parameter; raises EnumerationExceeded with partial result on overflow. propstore/grounding/grounder.py catches and surfaces ResultStatus.BUDGET_EXCEEDED. Useful when cluster-R HIGH-1 (exponential build_arguments) fires.

---

## Scope changes resulting from decisions

The decisions add or split workstreams:

- **WS-J split**: WS-J (determinism + rename) and **NEW WS-J2** (InterventionWorld / Pearl do() / Halpern HP-modified).
- **WS-K + NEW WS-K2** (meta-rule extraction pipeline). WS-K loses the `proposal_source_trust` family design and gains the argumentation-pipeline replacement design.
- **WS-O-arg split** into 5 sub-streams for the coverage-gaps work plus WS-O-arg-bugs.
- **WS-O-gun split** likely into WS-O-gun (existing bugs + anytime wire-up) and WS-O-gun-garcia (the major rewrite).

Updated workstream count: 20 → ~28 streams. Most of the new ones are independent and parallelizable.

## Workstream files needing updates

These need their text revised to reflect the decisions:

| WS file | Updates |
|---|---|
| WS-D-math-naming.md | D-1 (wbf fix), D-2 (pignistic fix + new flag) |
| WS-N-architecture.md | D-3 (delete all shims), D-4 (rename WorldModel → WorldQuery), D-5 (Verdict → GroundedClassification) |
| WS-CM-micropub-identity.md | D-7 (canonical micropub payload + Trusty URI identity prerequisite) |
| WS-C-sidecar-atomicity.md | D-6 (reorder), consumes D-7 via WS-CM |
| WS-K-heuristic-discipline.md | D-8 (delete derive_source_document_trust; argumentation pipeline replaces it) — drop the proposal_source_trust family design |
| WS-J-worldline-causal.md | D-11 (Path A — rename to OverlayWorld; defer Pearl to WS-J2) |
| WS-G-belief-revision.md | D-12 (AGM-AF stays in argumentation pkg) |
| WS-O-bri-bridgman.md | D-13 (demote verify_equation) |
| WS-O-ast-ast-equiv.md | D-14 (delete bytecode tier) |
| WS-O-arg-argumentation-pkg.md | D-15 (upstream policy), D-16 (split into 5 sub-streams) |
| WS-O-gun-gunray.md | D-17 (Garcia rewrite as separate sub-stream), D-18 (wire EnumerationExceeded) |
| INDEX.md | Update count and dependency graph |

New files needed:
- `WS-J2-intervention-world.md`
- `WS-K2-meta-rule-extraction.md`
- `WS-O-arg-aba-adf.md`
- `WS-O-arg-dung-extensions.md`
- `WS-O-arg-vaf-ranking.md`
- `WS-O-arg-gradual.md`
- `WS-O-gun-garcia.md`

---

## Round 2 — decisions from Codex's workstream review (2026-04-27)

Codex reviewed the 28 expanded workstream specs and surfaced 47 findings. These decisions resolve the findings that needed Q input.

### D-19 — Embedding model-key collisions ownership

**Question**: `_sanitize_model_key` collapses distinct model names. No WS owned the fix.
**Decision**: **Fold into WS-K**.
**Action**: extend WS-K's scope to replace sanitized model keys with collision-proof identity tuple `(provider, model_name, model_version, content_digest)`. First failing test: register four colliding model names, assert distinct sidecar identities.

### D-20 — Truncated-hash policy ownership

**Question**: `[:16]`, `[:24]` used as identity in production. No single WS owned "no production identity is a truncated hash."
**Decision**: **Fold into WS-M**.
**Action**: WS-M expands to audit every short-hash identity surface in propstore + dependencies, convert to full content-hash identity, with truncation as display-only. Coordinates with the Trusty URI work already in WS-M.

### D-21 — WS-B blocked-claim behavior

**Question**: hard error vs redacted page with a11y markers?
**Decision**: **Hard error — 403/404, no page rendered**.
**Action**: WS-B's `ClaimViewBlockedError` maps to 403 (identifiable user) or 404 (anonymous). A11y tests assert the error page has useful title/message, not that redacted claim content is present. Redacted-page logic deletes from WS-B.

### D-22 — WS-J2 framing

**Question**: feature/research vs remediation blocker?
**Decision**: **Feature now, remediation later**. Open as feature; if any user/test discovers reliance on Pearl semantics, escalate to remediation blocker.
**Action**: WS-J2 STATUS line documents "feature/research stream — not on critical bug-fix path." Critical path is A/B/C/D/E/K/L/M/N + dependency streams.

### D-23 — Branch-head CAS at propstore call sites

**Question**: WS-O-qui specifies expected-head semantics; no propstore-side WS gates the read-then-commit discipline.
**Decision**: **New compact CAS-discipline workstream — WS-Q-cas**.
**Action**: new file `WS-Q-cas-branch-head-discipline.md`. Test matrix: concurrent source finalize, source promote, repository import, materialize/build all lose a race and fail without writing sidecar state. Asserts expected head is captured before mutation and threaded to quire, not merely that quire can reject a stale head.

### D-24 — URI authority + privileged namespace validation

**Question**: `uri.py` authority unsanitized, `concept_ids.py` privileges `propstore` namespace. No owner.
**Decision**: **Expand WS-A** with an identity-boundary section.
**Action**: WS-A adds: source-local input cannot mint canonical `ps:`/privileged IDs; aliases cannot collide with reserved canonical namespaces; invalid authorities hard-fail at the IO boundary. Cohesive with WS-A's substrate-truthfulness theme.

### D-25 — ADF acceptance-condition representation

**Question**: callable vs AST?
**Decision**: **AST representation**.
**Action**: WS-O-arg-aba-adf locks AST: typed AST over parent labels. Serializable for ICCMA I/O. Inspectable by structural-link classifier. Polberg 2017 thesis convention.

### D-26 — WS-N split

**Question**: WS-N over-dependent on WS-K. Split?
**Decision**: **Split into WS-N1 (immediate) + WS-N2 (post-K)**.
**Action**:
- WS-N1: shim deletion (D-3), WorldModel→WorldQuery rename (D-4), Verdict rename (D-5), CLI ownership extraction (Codex #38-#40), pyproject dead entry, doc-drift sweep, three duplicate `_canonical_json` collapse to `quire.hashing`. Lands without waiting on WS-K.
- WS-N2: final six-layer `layered` import-linter contract over the README layers. Depends on WS-K's heuristic relocation. Includes the negative-violation test (T0.3).

---

## Codex findings being applied uniformly without dedicated decision

Real defects in spec text. Will be fixed by re-dispatching agents to revise affected WS files. Categorized by Codex finding number:

- **1.3 WS-C/WS-M micropub identity conflict**: WS-M is single authority. WS-C defers.
- **1.4 WS-M migration command**: delete per D-3 no-old-data rule.
- **1.5 WS-M optional PROV-O dual-path**: commit to one path (PROV-O canonical for export only, generated from one internal domain model).
- **1.9 WS-P references Tier.BYTECODE**: remove per D-14.
- **1.10 WS-P FreshConst-for-division**: replace with definedness predicate `(value, defined)`.
- **1.11 WS-P log(xy)=log(x)+log(y)**: every test includes domain assumptions in name + assertion.
- **1.13 WS-M default `return_arguments=True`**: depends on WS-O-gun budget wiring (D-18).
- **1.14 WS-E dangling-justification rule**: must accept valid master refs. Test matrix distinguishes invalid (source-local-not-promoted) from valid (canonical/master).
- **1.15 WS-C cache invalidation**: derive from sidecar schema version + pass names/versions + generated schema version + dependency pins + config. Manual override exists but not primary.
- **1.16 WS-K H10/H11**: take ownership in WS-K. No deferral. First failing tests prove forward and reverse can disagree independently.
- **2.2 WS-F projection test**: assert both relations preserved without silent loss, NOT attacks iff defeats.
- **2.3 WS-F undeclared WS-O-arg dependency**: declare upstream-blocked steps.
- **2.4 WS-G coverage-gates vs must-fail**: relabel coverage-only tests; reserve "must fail" for known counterexamples.
- **2.5 WS-G id() recycling**: deterministic stale-cache fixture.
- **2.6 WS-G OCF formula**: paper-derived worked example with expected ranks.
- **2.7 WS-H DF-QuAD**: decide paper contract first, then write test.
- **2.8 WS-I/WS-J ordering**: WS-J depends on WS-I, OR WS-J explicitly avoids ATMS-derived state. Pick one.
- **2.9 WS-I rename**: interface replacement, not rename. Old bounded `is_stable` is deleted; new unbounded API has different semantics.
- **2.10 WS-J hash tests**: compare two equivalent failures with different reprs (not failure-vs-success); assert typed failure on unknown objects (not stable hashing).
- **2.11 WS-J budget API**: required keyword argument, no default.
- **2.12 WS-J replay storage**: journal entries store typed operator name + input + version/policy + normalized state. Then replay tests are meaningful.
- **2.13 WS-K2 missing skill**: write predicate-registration step explicitly; don't reference unavailable skill.
- **2.14 WS-K2 CLI tests**: add logged CLI tests for help/dry-run/propose/promote/unknown id/no-commit-review.
- **2.15 WS-O-arg "blocks nothing"**: declare WS-O-arg-bugs explicit prerequisite for sub-streams.
- **2.16 WS-O-arg ideal-extension proof**: replace with paper construction; defense not downward-closed.
- **2.17 WS-O-arg-Dung Z3 path**: deletion-first per Q rule. Pick one architecture; delete the other.
- **2.18 WS-O-arg sentinels**: separate upstream sentinel (closes in dep repo) from propstore sentinel (asserts pinned dep version contains fix and behavior is observable from propstore).
- **2.20 WS-O-arg-ABA non-flat overclaim**: scope to flat ABA. `NotImplementedError` for non-flat, marked feature.
- **2.21 WS-O-arg-gradual old paths**: deletion-first. Delete `compute_dfquad_strengths`; update every caller; default-on continuous integration; no `strict=True` compat.
- **2.22 WS-O-arg-gradual + VAF ranking convergence**: assigned to WS-O-arg-vaf-ranking. WS-O-arg-gradual consumes.
- **2.23 WS-O-arg-VAF Atkinson overclaim**: rename to "Atkinson slice"; honest about missing CQs.
- **2.24 WS-O-gun-garcia TDD**: remove "do not run tests during rewrite." TDD means failing test first, passing test on each step.
- **2.25 WS-O-gun-garcia type-shape**: align fast-path invariant with new field names (`yes/no/undecided/definitely`).
- **2.26 WS-O-gun-garcia schema closure**: explicit propstore-side coordinated step OR move the finding out of WS-O-gun-garcia.
- **2.27 WS-O-bri verify_equation**: delete now (D-3 no-old-repos rule). No deprecation period.
- **2.28 WS-O-bri tooling**: replace bare `python -c` with `uv run` scripts.
- **2.29 WS-O-ast decisions open**: resolve real-domain assumptions, `extract_names` API, git-hash pinning before scheduling implementation steps.
- **2.30 WS-O-ast error handling**: pick one. If `compare()` catches and returns typed `UNKNOWN`, delete external `AstToSympyError` catches.
- **2.1 Owner: TBD**: replace each with "Codex implementation owner + human reviewer required" or named owner where decided.

## Updated workstream count

Round 1: 28 streams. Round 2: 28 + 1 (WS-Q-cas) + 1 (WS-N split into N1+N2 from N) = 30 streams. INDEX.md needs another update.

---

---

## Round 3 — decisions from Codex's re-review of round-2 work (2026-04-27 evening)

Codex re-reviewed the 30 round-2-revised workstream specs and surfaced 19 narrower findings + 4 stale-text issues. These decisions resolve the ones that needed Q input.

### D-13 — SUPERSEDED by Codex 2.27

D-13 said `verify_equation` is "demoted/deprecated." Codex 2.27 said delete now per Q's no-old-repos rule, and WS-O-bri implements deletion. D-13 is superseded — verify_equation is **deleted in the same PR as the propstore caller migration**, no deprecation period. The text under D-13 above is preserved for git history but the decision IS deletion.

### D-27 — WS-N2 closure language

**Question**: Codex re-review #7 — current "Done means done" allows soft-gate allowlist for residual layered-contract violations. Not true closure.
**Decision**: **Hard-fail clean only — no soft-gate.**
**Action**: WS-N2 closes only when `lint-imports` passes the layered six-contract with zero residual violations. No allowlist. If WS-K's heuristic relocation surfaces a violation needing design, WS-N2 stays OPEN until resolved. Per `feedback_no_fallbacks.md`.

### D-28 — CEL spec ordering

**Question**: Codex re-review #14 — WS-P CEL string-escape work in done-gates while spec retrieval pending. External unresolved source in close-out.
**Q's pushback**: "why are you so freaking out about CEL what is the big deal here jesus christ who cares about CEL for what reasons what is the dealeo here?"
**Decision**: **Drop the spec-retrieval ceremony.** No Step 0. No paper-reader pass. No prerequisite spec-ingestion stream.

**Reasoning**: CEL is Google's typed expression language for condition expressions on claims/stances. Not a research paper — a language reference doc. The cel-spec/langdef.md is ~30 KB of grammar and well-defined. The WS-P engineer reads it while writing the parser fix. That's not a workstream — it's normal engineering with a reference open.

**Action**: WS-P drops "CEL spec retrieval pending" framing; treats cel-spec/langdef.md as an ordinary reference. Bug-fixes for escapes, float-exponents, ternary unsoundness, Z3 division-guards, equation-comparison orientation become normal engineering work.

### D-29 — Micropub identity cycle break

**Question**: Codex latest re-review — WS-C and WS-M still cyclically own micropub payload shape and Trusty URI identity, and WS-C's placeholder hash path violates the no-placeholder rule.
**Decision**: **Split out a prerequisite WS-CM.**
**Action**: WS-CM owns the canonical micropub payload constructor and the Trusty URI artifact id over that payload. WS-C consumes WS-CM for sidecar dedupe-shape correctness. WS-M consumes WS-CM for provenance/Trusty URI verification and for reusing the same hash primitive. WS-C does not install a placeholder identity function; WS-M does not define the micropub payload shape.

---

## What was decided to NOT do

- No naming-only fixes for math bugs (caller intent demands math fixes).
- No old-data carve-outs (rule remains: no old repos, iterating to perfection).
- No backward-compat aliases for the renames (rope handles call-site updates in one pass).
- No fork of the argumentation package.
- No human-only meta-rule authoring (LLM extraction iterated until reliable, with proposal-review gate).
- No proposal_source_trust family — superseded by argumentation-pipeline-replaces-heuristic decision.
- No deferred Pearl do() — gets its own workstream (WS-J2) so it ships when it ships, not when WS-J ships.
