# Synthesis — 2026-04-16 Deep-Dive Code Review

## Executive summary

propstore is a semantic-reasoning system with a **competent core** (high-fidelity ATMS, verified ASPIC+ argument construction, correct post-fix CCF fusion, git-backed non-commitment storage, real datalog grounding) and a **drifted theoretical veneer** (the revision layer claims AGM but has zero postulate tests; the semantic substrate rhetoric cites Fillmore/Pustejovsky/lemon/McCarthy but has zero structural representation; several citations declare formulas that the code does not implement).

The review's nine axes produced **~130 findings across 9 reports**. The findings cluster into **five cross-axis patterns**:

1. **Confidence fabrication at calibration-free defaults.** Same shape in five places (`_DEFAULT_BASE_RATES`, `praf/engine.py` dogmatic_true, `source_calibration` prior=0.5, `fragility_scoring` fabricated dogmatic opinions, `classify.py` invariant-violating `(0,0,0,0.5)`).
2. **Three-valued solver results collapse to two-valued.** Z3 unknown → bool → OVERLAP across `z3_conditions.py`, `condition_classifier.py`, `dung_z3.py`. No `SolverResult` sum type. No timeouts.
3. **Build-time filtering that should be render-time.** `sidecar/build.py` raw-id gate, `compiler/passes.py` draft filter, `source/promote.py` all-or-nothing. Three distinct violations of the same design-checklist item.
4. **Postulate claims without postulate tests.** AGM, DP, EE, IC, Diller P*/A*, Baumann — named in prose, none tested.
5. **Types that cannot label ignorance.** `SourceTrustDocument` has no `status` field; `ResolutionDocument` has four independent scalars permitting `(0,0,0,0.5)` instead of `Opinion | None`.

The good news: every pattern is remediable at this project's one-month-1365-commit cadence. Every finding has a proposed fix. The bad news: the drift is systemic enough that piecemeal fixes will not scale — the project needs type-level and doc-level disciplines that prevent recurrence, not just one-pass cleanups.

## Severity-ordered findings

### CRIT — principle violations + correctness drift
Ordered by blast radius, not report order.

- **`calibrate.py:211-217` — `_DEFAULT_BASE_RATES` fabricates "corpus frequency priors" with no corpus** (axis 1 Finding 2.1). Single highest-leverage fix in the codebase.
- **`praf/engine.py:155-157, 197-199, 252` — defaults to `Opinion.dogmatic_true()` when calibration missing, with a "backward compat" comment** (axis 1 Finding 2.2, axis 5 cat 1). Literal inversion of the honest-ignorance principle.
- **`sidecar/build.py:75-82, 148` — `_raise_on_raw_id_claim_inputs` aborts the entire sidecar build on any raw-id error** (axis 1 Finding 3.1). Hits design-checklist items 1, 2, 3, 4 simultaneously.
- **`condition_classifier.py:32-36` — every Z3 unknown silently becomes `ConflictClass.OVERLAP`** (axis 5 hot site, axis 3e CRIT). Propagates into merge and argumentation.
- **`z3_conditions.py:444, 463, 481, 489` — Z3 `sat|unsat|unknown` collapses to bool; no timeouts anywhere in `propstore/`** (axis 3e CRIT). The root cause of the condition_classifier symptom.
- **`opinion.wbf()` — implements aCBF, not WBF; commit c7a9215 self-acknowledges the open bug** (axis 3b F1 CONFIRMED against paper PNG).
- **`world/types.py:1064-1066` — function labeled `"pignistic"`, cites Denoeux; implements Jøsang's `b + a·u`** (axis 3b F2). Citation-for-authority failure. Denoeux binomial BetP is `b + u/2`.
- **`aspic.py:55, 74, 91-93` — three docstrings cite "Modgil & Prakken 2018 Def 1 (p.8)" for contrariness** (axis 9 worst drift). Paper's Def 1 is p.4 about Dung acceptability; content is Def 2 p.8. Academic-authority claim backing the wrong content.
- **`propstore/revision/` — 1663 LOC, zero literature citations in source, zero K*1-K*8 / C1-C4 / EE1-EE5 / P*1-P*6 / A*1-A*6 tests; "entrenchment" is weighted-support-count, not Gärdenfors** (axis 3c biggest drift). AGM in name only.

### HIGH — structural drift + scope mismatch

- **Phantom pyright strict target** (axis 2 CRIT, filed as HIGH here because scope is tooling-only): `pyproject.toml` lists `aspic_bridge.py` as strict, but `aspic_bridge` is now a package. Strict checking is silently disabled on the most active refactor area.
- **`source/` runtime-imports `cli.repository`** (axis 2 CRIT, HIGH here): eight-layer upward import; root cause is `Repository` living in `cli/` when it is a filesystem primitive.
- **Semantic substrate zero implementation** (axis 3d): Fillmore, Pustejovsky, Buitelaar lemon, McCarthy all cited in CLAUDE.md, none present in code. What exists is a dimensional-quantity ontology + SKOS taxonomy + visibility-tag contexts + token-Jaccard reconciliation.
- **`fragility_scoring.imps_rev` fabricates dogmatic opinions for every argument and defeat** (axis 1 Finding 2.3). Sensitivity analysis built on fabricated certainty.
- **`source_calibration.derive_source_trust` silently defaults `prior_base_rate=0.5` without provenance on the stored payload** (axis 1 Finding 2.4). Stored trust payload indistinguishable between "derived" and "had-nothing."
- **`compiler/passes.py:289-307` drops every `stage: draft` file from the semantic bundle** (axis 1 Finding 3.2). Build-time filter; should be render-time.
- **`praf/treedecomp.py` advertises Popescu & Wallner 2024 `O(2^tw)` complexity; actually delivers `O(2^|defeats| * 2^|args|)`** (axis 3a biggest drift). `praf/engine.py` dispatches on the unreached bound.
- **AF revision (Baumann/Diller/Cayrol) entirely absent** (axis 3c). Cited in lineage, no module.
- **Defeasibility priority information unconditionally empty** (axis 7): `superiority=[]` at `translator.py:171-178`, `rule_order=frozenset()` at `translate.py:275-280`. Whole pipeline drops priorities.
- **`preference.py` uses Pareto-on-3-vector, not Modgil-Prakken Def 22 strict partial order** (axis 3a). Heuristic flows into aspic_bridge unlabeled.
- **44 papers in `papers/` not listed in `papers/index.md`; 25 papers with stub notes** (axis 9). Paper-collection integrity mismatch.
- **Two strict-typed modules fail pyright** (axis 2).
- **Test marker lie: 54 files use `@given`, only 1 carries `property` marker** (axis 4). CI `-m property` runs 6 tests when 365 exist.
- **ATMS/IC-merge mislocated to `propstore/repo/` in CLAUDE.md** (axis 9): actually in `propstore/world/`. Load-bearing architectural claim wrong on file placement.

### MED — smaller structural gaps

- `dedup_pairs` collapses mirror pairs without provenance (axis 1 Finding 1.2).
- `attach_source_artifact_codes` in finalize mutates authored payloads (axis 1 Finding 1.3).
- `SourceTrustQualityDocument` has no `status` field (axis 1 Finding 2.5).
- `promote_source_branch` requires finalize `status=="ready"` — all-or-nothing (axis 1 Finding 3.3).
- `artifacts/` imports `world/` (axis 2).
- `core/literal_keys` imports `aspic` (axis 2).
- `grounding`/`sidecar` import `aspic` (axis 2).
- `fragility` imports `aspic_bridge` (axis 2).
- ATMS invariants 1780 LOC tested without any `@given` (axis 4 runner-up).
- Seven orphan modules, 1506 LOC, zero test references (axis 4): `diagnostics.py`, `fragility_contributors.py`, `fragility_scoring.py`, `fragility_types.py`, `parameterization_walk.py`, `probabilistic_relations.py`, `source_calibration.py`. Plus `conflict_detector/orchestrator.py`.
- Several MED findings in axis 3d (stub papers for foundational semantic-substrate work), axis 3e (temporal ordering string-matched), axis 9 (papers/index orphan counts, Clark_2014 duplicate directory).

### LOW / NOTE

- Positive finding: ATMS is high-fidelity de Kleer 1986 with runtime `verify_labels()` (axis 3e).
- Positive finding: proposal-branch discipline is structurally enforced (axis 1 Finding 1.1).
- Positive finding: heuristic modules never directly mutate source families (axis 1 Finding 4.1).
- Positive finding: CCF Def 5 implementation now correct to paper Table I (recent commit).
- Positive finding: grounding/ is real datalog per Diller 2025, not a mislabeled variable-binder (axis 7).
- Several low/note-level style items across axes.

## Cross-cutting patterns (deeper than individual findings)

### Pattern A — Fabricated certainty as the default

Every point in the system where calibration data is absent has chosen to fabricate a specific number rather than represent ignorance. The numbers differ (`a=0.7` for "strong" in calibrate; `a=0.5` in source_calibration; `b=1, d=0, u=0` in praf/engine; `b=d=u=0, a=0.5` in classify). The pattern is identical: given nothing, output something plausible.

**Root cause (type-level):** the downstream consumers have no type distinguishing "measured Opinion" from "defaulted Opinion from an unknown." If the return type were `Opinion | NoCalibration` (as axis 1 Finding 2.2 recommends), none of the fabrication sites could type-check their current return.

**Remediation:** Z-1 (honest-ignorance types). Adds `CategoryPrior` with provenance, `Opinion.with_provenance(...)`, `SolverResult` sum type. Consumers get compile-time errors at each current fabrication site.

### Pattern B — Three-valued results forced into two

Z3 returns `sat | unsat | unknown`. CEL evaluation can fail. LLM classification can emit "no stance." Each is honestly three-valued; each is collapsed to two-valued (usually by mapping the third to the more convenient of the first two).

**Root cause:** no `SolverResult`-style algebraic type at the boundary. Callers take `bool` and lose the information.

**Remediation:** same as Pattern A — introduces the type, callers must either propagate the third value or explicitly label the collapse.

### Pattern C — Filtering at build instead of render

Three distinct sites filter data at build time that the design checklist explicitly forbids. The common shape: "this data has a problem; refuse to expose it." The correct shape: "this data has a problem; expose it with the problem attached; let render policy decide."

**Root cause:** build-time is where the problems are *detected*, and refusing output is simpler than attaching a diagnostic. The principled path requires a diagnostic-bearing sidecar row.

**Remediation:** Z-2 (build-to-render gate removal). Convert each refusal to a quarantine row; render policy filters on the quarantine flag.

### Pattern D — Postulates declared, never verified

AGM, DP, EE, IC, Modgil-Prakken rationality, Baumann/Diller P*/A* — all mentioned in prose, none property-tested. `@given` strategies exist in the codebase (365 tests); extending them to postulates is incremental, but requires the *operator semantics to be correct* first. The revision module's postulates are currently not even syntactically expressible.

**Root cause:** the revision module operates on `BeliefAtom` tuples with no `Cn` closure. AGM postulates require a belief-set + consequence operator. Until those exist, no postulate is expressible.

**Remediation:** Track B (WS-B-P5). Real belief-set layer with `Cn` closure over typed assignments (or over a logical-formula layer — decision needed upfront).

### Pattern E — Citation-for-authority without verification

Five concrete sites where code cites a paper for a formula or definition that the paper does not actually contain (aspic.py Def 1/Def 2 swap; world/types pignistic→Jøsang; wbf()→aCBF; revision/iterated Booth-names-without-Booth-semantics; revision/entrenchment Gärdenfors-name-without-Gärdenfors-axioms). Several more sites cite papers correctly but for operators that do not flow through the pipeline (defeasible priority).

**Root cause:** citations are comments; comments do not participate in the type system. A citation claim can stay in place through arbitrary refactors of the code it describes.

**Remediation:** a project discipline — every citation in a docstring or CLAUDE.md paragraph is required to be backed by either (a) a property test whose name references the citation, or (b) a code invariant (pyright-strict assertion, runtime `verify_*` function) that the paper's condition holds. Unbacked citations are retracted in the same commit that introduces them, or struck from docstrings in a Z-3 sweep.

## The two kinds of gaps

The review found two distinct kinds of drift. They need different responses.

### Gaps type 1: "code ahead of doc"
Several findings are of the shape "code does X; comment says Y; both are plausible; they just don't agree." Example: `world/types.py` pignistic — the code is a sensible operator (Jøsang's E(ω)); the doc cites the wrong paper (Denoeux). Fix: rename or relabel. Low effort; no behavior change.

### Gaps type 2: "doc ahead of code"
Other findings are of the shape "CLAUDE.md says we have X; we don't have X; X would require significant work." Example: AGM revision; Fillmore frames; `ist(c, p)` contexts. These are aspirational claims in the docs that were never true. Fix requires either building X or retracting the claim.

The review is silent on which should be done, because that's a project-level decision. The recommendation in axis 6 is: retract the claim until X is built; never let the docs lead the code. Axis 8 assumes the decision is to build.

## Recommendations (severity-ordered)

1. **Retract the Known Limitations section in CLAUDE.md and replace with an honest scope paragraph + a living `docs/gaps.md`** (axis 6). Every item in `docs/gaps.md` cites a finding or a workstream. New limitations may only be added when observed; existing limitations may only be removed when a test proves the gap is closed. This is the cheapest intervention with the highest long-term leverage: it is what prevents the other recommendations' fixes from re-opening.
2. **Install the citation-discipline rule** (pattern E above). Every citation needs a test or an invariant. A one-time sweep plus a CI lint that catches unbacked citations in new docstrings.
3. **Build Z-1 (honest-ignorance types)** (closes pattern A, B, partially D). Adds `Provenance`, `CategoryPrior`, `SolverResult`, `Opinion | NoCalibration` at fabrication sites. Agent-day.
4. **Build Z-2 (build-to-render gate removal)** (closes pattern C). Each gate becomes a quarantine row. Agent-day.
5. **Build Z-3 (citation + doc cleanup)** (partially closes pattern E). The one-time sweep. Agent-evening.
6. **Execute Track A (workstreams A-P1..A-P4)** (closes axis 3d gaps; resolves aspirational-claim drift in semantic layer). Weeks. Detailed workstreams in `workstreams/`.
7. **Execute Track B** (closes axis 3c gaps; makes AGM real). Weeks. Sketched in `workstreams/index.md`.
8. **Execute Track C** (closes axis 7 gaps; populates defeasibility priorities). Week. Sketched in `workstreams/index.md`.
9. **Cover the seven orphan modules with real tests** (axis 4). Incremental; bundle with other workstreams touching the modules.

## What this review did not cover

Honest gaps in the review itself:

- **Benchmarks.** No axis measured performance. `praf/treedecomp.py`'s complexity drift is a warning but not benchmarked.
- **Security.** No axis examined CEL injection, Z3 timeout exhaustion as DoS, sidecar integrity under adversarial git commits, or LLM prompt-injection into proposal classifiers.
- **End-to-end workflows.** Each axis is scoped; no subagent walked a complete user story from `pks init` through `pks promote`.
- **Documentation outside code + CLAUDE.md.** `docs/` has a dozen files; axis 9 sampled a few.
- **Plans directory reconciliation.** Several `plans/*.md` files overlap with review findings but are out of scope for this review. Z-3 should include a plans-directory sweep.

## Where this goes next

`workstreams/` contains four Track A workstreams ready to dispatch, a master index, and sketched Tracks B + C + Z-1 + Z-2 + Z-3.

Axis 8 closes with three capability horizons: typed honest ignorance (week), full semantic substrate (month), reference argumentation + revision framework (months).

`principled-path.md` (companion to this synthesis) audits the workstreams themselves for easy-path hedges and commits to the beautiful-path alternatives where the review's principles demand them.
