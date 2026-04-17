# Workstream C — Defeasibility (CKR Justifiable Exceptions + ASPIC+ Coexistence)

Date: 2026-04-16
Status: complete - WS-C exit criteria met
Depends on: `disciplines.md`, `judgment-rubric.md`, WS-A phase 4 (contexts + lifting rules), WS-A1 semiring provenance for C-3 support evidence
Blocks: —
Review context: `../axis-7-defeasible-datalog.md` (primary), `../axis-3a-argumentation.md`

## Progress

- 2026-04-17: Verified local artifacts for the three primary papers and the two ABA comparison papers, including processed notes and page-image directories.
- 2026-04-17: Drafted `docs/defeasibility-semantics-decision.md` for C-1, selecting Bozzato-style CKR justifiable exceptions over WS-A `ist(c, p)` contexts, preserving ASPIC+ as the structural argument layer, preserving Diller-style datalog grounding as grounding only, and rejecting ABA as the production semantics for WS-C.
- 2026-04-17: Stopped at the explicit C-1 Q review gate before C-2 implementation.
- 2026-04-17: Inserted WS-A1 semiring provenance as the missing substrate workstream after reading Green 2007 notes and running design/adversarial review with Claude CLI. WS-C C-3 now depends on `SupportEvidence` rather than generic provenance blobs.
- 2026-04-17: WS-A1 added the executable C-3 support contract in `propstore.defeasibility`: `JustifiableException`, `LiftingRuleSupport`, and `ExceptionDefeat` all carry `SupportEvidence`; lifted support multiplies by lifting-rule support; solver nogoods live-filter support without deleting the exception object.
- 2026-04-17: C-2 priority pipeline repaired. `RulesFileDocument` now carries explicit authored `superiority` pairs, the grounding translator emits those pairs into gunray as a validated strict partial order, and the ASPIC bridge projects schematic superiority onto grounded `PreferenceConfig.rule_order` pairs. Verification passed: `91 passed`, `logs\test-runs\ws-c2-runtime-20260417-153640.log`; production Pyright was clean for changed C-2 files. Grep gates found no production `superiority=[]`, no production `rule_order=frozenset()`, and no bridge `del defeasible_rules`.
- 2026-04-17: C-3 justifiable-exception satisfaction implemented. `ContextualClaimUse`, typed `CelBinding`s, `ClaimApplicability`, policy issues, and `evaluate_contextual_claim(...)` now decide local/lifted exception applicability over live support; CEL patterns route through a supplied Z3-compatible solver, missing bindings and solver unknowns become `UNKNOWN` with `INCOMPLETE_SOUND`, and multiple applicable exceptions are surfaced rather than collapsed. Verification passed: `10 passed`, `logs\test-runs\ws-c3-satisfaction-20260417-154226.log`; Pyright was clean for `propstore/defeasibility.py` and C-3 tests.
- 2026-04-17: C-4 ASPIC+/CKR boundary integrated. `apply_exception_defeats_to_csaf(...)` injects CKR-derived exception defeats into the Dung layer using ASPIC arguments for exception justification claims as attackers and excepted target-claim arguments as targets; it fails loudly if an applied exception cannot be represented structurally. Added `docs/justifiable-exceptions.md` for the implemented boundary. Verification passed: `18 passed`, `logs\test-runs\ws-c3-c4-20260417-154647.log`; Pyright was clean for C-3/C-4 files and tests.
- 2026-04-17: C-5 was already satisfied by WS-Z-types in the current repo state. `condition_classifier.py` returns `ConflictClass.UNKNOWN` for solver unknowns, parameter conflict records preserve UNKNOWN, and repository merge maps UNKNOWN to ignorance rather than attacks. Verification passed: `8 passed`, `logs\test-runs\ws-c5-unknown-20260417-154850.log`.
- 2026-04-17: C-6 documentation cleanup completed before the final suite: `CLAUDE.md` now describes the CKR/ASPIC+ boundary, `docs/structured-argumentation.md` no longer claims rule ordering is empty or references `aspic_bridge.py` as a live file, `docs/gaps.md` closes the priority-drop gap while preserving the narrowed premise-ordering caveat, and `docs/justifiable-exceptions.md` describes the implemented exception semantics. Grep gates passed for the stale live-doc phrases `aspic_bridge.py` and `Rule ordering always empty`.
- 2026-04-17: Final WS-C gate passed after `uv sync --upgrade` completed with no tracked lockfile changes. The first full-suite attempt hit an xdist worker crash on `tests/test_aspic.py::TestRationalityPostulates::test_indirect_consistency` after `2724 passed`; the exact focused rerun passed (`1 passed`, `logs\test-runs\ws-c-final-aspic-indirect-20260417-155931.log`), and the full-suite rerun passed: `2725 passed, 16 warnings`, `logs\test-runs\full-ws-c-final-rerun-20260417-155953.log`.

## What you're doing

The 2026-04-16 review found that propstore's defeasibility pipeline drops priority information unconditionally and that the "structural" defeasibility surface in ASPIC+ is undercut by a hard-coded empty `superiority` and `rule_order`:

> **Axis 7, biggest drift:** unconditional empty `superiority=[]` (`grounding/translator.py:171-178`) plus empty `rule_order=frozenset()` (`aspic_bridge/translate.py:275-280`) silently drops all priority information across the full defeasible pipeline.

> **Axis 7 verdict:** `propstore/grounding/` IS a real datalog layer (Diller 2025 §3 Def 7/9 via delegation to the external `gunray` package), NOT a label. The "grounding" terminology is clean — datalog substitution lives here, Dung grounded-extension lives in `aspic.py/dung.py`. However, the defeasibility surface is narrow: only 4 of the 14 cluster-7 papers have meaningful implementation traces. ABA (Bondarenko/Toni) absent, LLM-ASPIC (Fang 2025) absent — LLM classifies stances for Dung attacks, never rules for defeasible grounding. Antoniou WFS, Bozzato CKR/DL-Lite, Brewka preferred subtheories, Maher D(1,1), Morris closure — all absent.

> **Cross-ref Axis 5 + Axis 3e:** `condition_classifier.py:32-36` silently maps Z3 unknown → `ConflictClass.OVERLAP` in the conflict_detector pipeline, which feeds defeasibility decisions. WS-Z-types fixes the unknown-collapse; WS-C consumes the corrected solver result.

Your job: pick a defeasibility semantics, then implement it. Q has chosen **Bozzato-style CKR justifiable exceptions on top of WS-A P4's `ist(c, p)` + lifting rules**, with **ASPIC+ surviving as the structural argument-construction layer** — the two coexist; ASPIC+ builds arguments from non-defeasible rules + assumptions, CKR tells you which exceptions qualify which generalizations in which contexts.

This is the smallest-scope of the major workstreams but the highest decision-density. The decisions are upfront; the implementation is mostly disciplined plumbing.

## Composition with WS-A's descriptivist event semantics

WS-A phase 3 commits to **events as defeasible coreference** (see `docs/event-semantics.md`): there is no `Event` type; what we informally call "an event" is a cluster of description-claims under a merge-hypothesis resolved at render time by Dung argumentation. WS-C's CKR justifiable exceptions compose cleanly with this:

- A "context" in `ist(c, p)` is interpretable as a description-cluster.
- A justifiable exception in cluster c reads as "this generalization holds across cluster c, except in the cases described by these other description-claims (which themselves form an exception-cluster)."
- The exception's *justification* is itself a description-claim (an `Assertion` or similar) with its own provenance and defeasibility.
- Lifting rules (per Guha 1991 + Bozzato) govern when an exception in cluster A applies in cluster B. A specific lifting rule may say "exceptions about measurement-instrument calibration lift from per-experiment cluster to per-laboratory cluster"; another may say they don't.
- Coreference between description-claims (the merge-question) is itself a Dung argument resolvable by the existing argumentation layer. WS-C's defeasibility semantics consume those merge arguments without re-implementing them.

This means WS-C builds on a substrate where claims are already description-grade (with provenance, with temporal anchoring, with defeasible coreference). Don't re-invent any of that machinery in WS-C; consume it.

## Vision

When this workstream is complete, propstore has:

- **Justifiable exceptions per Bozzato 2018 CKR.** A claim of the form "in context `c`, generalization `g` holds **except in cases where `e_1`, `e_2`, ..." is first-class. The exceptions `e_i` are themselves claims that can be non-committal, merged, revised through the existing pipeline.
- **Semiring-shaped support for exceptions and defeats.** Exceptions and CKR-derived defeats carry WS-A1 `SupportEvidence`: positive provenance polynomial plus support quality. This keeps Green 2007 support accounting separate from CKR applicability and ASPIC+ directionality.
- **No DL-Lite commitment.** CKR's *structure* over propstore's richer claim language. Decidable subqueries (interval reasoning, value-equality, range checks) route through `z3_conditions.py`. The remainder is sound-but-incomplete reasoning — explicitly so, with provenance recording when a conclusion depends on an undecidable inference.
- **Lifting rules from WS-A P4 are reused as the upward-propagation channel for exceptions.** A justifiable exception in context `c` lifts to context `c'` if and only if a lifting rule licenses it; otherwise it stays bounded.
- **ASPIC+ as the evidence layer.** When a claim is challenged, the ASPIC+ recursive-argument construction (already verified in `aspic.py:664-964`) builds an argument from the underlying non-defeasible rules + assumptions. The argument doesn't encode defeasibility — the context's exception structure does. This separates *structural* argument from *defeasibility-bearing* exception, which the existing code conflates by leaving priorities empty.
- **Real priority data flows end to end.** The empty `superiority=[]` and `rule_order=frozenset()` are populated from rule-file metadata (entered by users; promoted through proposal branch like everything else). The aspic_bridge consumes them as Modgil-Prakken Def 22 strict partial orders, not as Pareto-on-3-vector heuristics (which is `preference.py`'s current shape per axis 3a).
- **`grounding/` continues to delegate to `gunray` for datalog substitution per Diller 2025.** That part is correct. The defeasibility extensions sit on top, not inside.
- **Property tests for the defeasibility semantics.** Not just "this rule fires"; postulates of CKR (justifiability, exception-consistency, lifting-soundness) become `@given` strategies.

## Key design decisions — made

Decisions Q has already settled; don't relitigate:

- **Bozzato CKR style, not ABA.** ABA (Bondarenko/Toni) is formally beautiful but solves a different problem — assumption-based contrariness, not context-with-exceptions. propstore's use case is scientific argumentation with context-qualified generalizations; CKR is the natural framing.
- **CKR coexists with ASPIC+, doesn't replace it.** ASPIC+ stays as the structural argument-construction layer. CKR is the defeasibility semantics on top.
- **Drop DL-Lite commitment.** Use CKR's structure over propstore's richer claim language; route decidable subqueries to Z3; accept sound-but-incomplete elsewhere with explicit provenance.
- **No System Z, no preferred subtheories, no Antoniou WFS as primary.** They're alternative defeasibility semantics with different commitments. They get read so we know what we're not doing; we don't implement them in this workstream.

## What you are NOT doing

- **Not retiring or rewriting `aspic.py` or the recursive-argument construction.** Axis 3a verified those are paper-correct. They consume the populated priorities; they don't change.
- **Not retiring `grounding/`.** Datalog grounding via `gunray` is correct (Diller 2025). CKR sits on top.
- **Not committing to a single causal semantics.** Causation in propstore lives in WS-A P3's event layer with a `causal_account` discriminator; WS-C's defeasibility is orthogonal.
- **Not building LLM-driven exception classifiers.** Like other heuristics, those land on proposal branches in a separate workstream. WS-C is the formal layer.
- **Not implementing ABA, Antoniou WFS, Brewka preferred subtheories, Goldszmidt System Z, or Maher D(1,1) as production semantics.** Read for context; do not implement.

## Papers

**Primary (read fully, notes to non-stub depth):**

- **Bozzato, Serafini, Eiter 2018**, *Reasoning with Justifiable Exceptions in Contextual Hierarchies*. The defeasibility semantics target. CKR's justifiable-exception machinery: how exceptions are scoped to contexts, how they lift, what makes an exception "justifiable."
- **Bozzato, Eiter, Serafini 2020**, *Enhancing Context Knowledge Repositories with Justifiable Exceptions* (or whatever the closest 2020 follow-up is). The decidable fragment over DL-Lite — read to understand what we are NOT committing to, but understand the *structure* so the propstore-richer-language version stays sound.
- **Diller 2025**, *Grounding Rule-Based Argumentation in Datalog*. The grounding side — already in code via `gunray`. Re-read to verify the boundary between datalog grounding (their job) and ASPIC+ argument construction (our job).

**Secondary (read for comparison, understand why we chose against):**

- **Bondarenko, Dung, Kowalski, Toni 1997**, *An Abstract, Argumentation-Theoretic Approach to Default Reasoning*. ABA. Read to know what we're not doing.
- **Toni 2014**, *A Tutorial on Assumption-Based Argumentation*. ABA tutorial. Same purpose.
- **Antoniou 2007**, *Defeasible Reasoning on the Semantic Web*. Antoniou's defeasible logic style. Read to know what we're not doing.

**Background (read if needed for specific questions):**

- **Brewka 1989**, *Preferred Subtheories: An Extended Logical Framework for Default Reasoning*. Background; preferred-subtheories style.
- **Goldszmidt, Pearl 1992 (or near)**, System Z and rank-based default reasoning. The paper manifest anchors System Z to `conflict_detector/` despite no implementation; understand the framework if the conflict-detector orchestration choices need re-examining.
- **Modgil, Prakken 2018**, the canonical ASPIC+ paper — primarily relevant for the priority-population work, since Def 22 is the strict-partial-order shape that `preference.py`'s Pareto-on-3-vector currently approximates.
- **Maher 2002 / 2013** on D(1,1) and other defeasible-logic variants — context for the broader landscape.
- **Fang 2025**, *LLM-ASPIC: A Neuro-Symbolic Framework for Defeasible Reasoning*. Cited in CLAUDE.md but absent from code. Read to know what an LLM-ASPIC integration could look like; this is *not* a build target for WS-C but informs how a future heuristic-classifier workstream could feed into the defeasibility layer.

## Phase structure

### Phase C-1 — Read + decide

- Process all primary papers + at least Bondarenko or Toni for the why-not-ABA understanding.
- Write `docs/defeasibility-semantics-decision.md` capturing: what CKR commits us to, what we drop from CKR (DL-Lite), what stays from ASPIC+, what the boundary between the two layers is. This document is the input to the implementation phases — get it reviewed by Q (and ideally by an adversary subagent against the principles) before proceeding.

### Phase C-2 — Priority pipeline repair

The smallest, most concrete fix. Closes axis 7's biggest finding without waiting for any new semantics.

- Audit how rule-file metadata flows from `predicate_files.py` / `rule_files.py` into `grounding/translator.py` and onward to `aspic_bridge/translate.py`.
- Identify the data shape that should populate `superiority` and `rule_order`. This is going to involve a rule-file schema decision — do users author priorities directly, or are they derived from other metadata? Check existing rule files in `knowledge/` (Q's own repos) to see what's already there.
- Wire the data through. `superiority=[]` becomes the populated list; `rule_order=frozenset()` becomes the populated set.
- Update `preference.py` to produce Modgil-Prakken Def 22 strict partial orders rather than Pareto-on-3-vector heuristics. Property test: the resulting preference is transitive, irreflexive, antisymmetric (the strict partial order axioms).
- Property test: priorities round-trip through the pipeline (rule file → translator → aspic_bridge → ASPIC+ argument construction) without information loss.

### Phase C-3 — CKR justifiable exceptions

- Design `JustifiableException(target_claim, exception_pattern, justification_claims, context, support, decidability_status)`. The `exception_pattern` is a CEL expression (reusing existing CEL infrastructure) that picks out which instances of `target_claim` are excepted. The `justification_claims` are claims supporting the exception. The `support` is WS-A1 `SupportEvidence`, not a loose provenance dictionary.
- Design how exceptions compose with `ist(c, p)` from WS-A P4. A justifiable exception lives in a context; it qualifies generalizations that hold in that context.
- Design how exceptions lift across contexts via WS-A P4 lifting rules. A specific lifting rule may say "exceptions about `valid_until` lift from clinical-context to general-medicine context"; another may say they don't.
- Implement the satisfaction algorithm: given a context `c`, a claim `p`, and a set of justifiable exceptions, decide whether `ist(c, p)` holds. For decidable subqueries (CEL-expressible exception patterns over Z3-typed values), route through `z3_conditions.py`; for the remainder, do sound-but-incomplete inference and tag the conclusion's provenance with `decidability_status: "decidable" | "incomplete-sound"`.
- Property tests:
  - Justifiability: an exception with no supporting justification is not applied. (CKR's central postulate.)
  - Exception-consistency: a context's set of justifiable exceptions does not contain mutually-defeating pairs (or, if it does, both are flagged for render-time policy choice — non-commitment again).
  - Lifting-soundness: an exception lifts to a context iff a lifting rule licenses the lift; otherwise it stays bounded.
  - Support-composition: lifted exception support multiplies exception support by lifting-rule support; solver nogoods can kill support monomials without deleting the exception object.
  - Decidability-status correctness: every conclusion's provenance reflects whether the inference was decidable.

### Phase C-4 — ASPIC+ ↔ CKR boundary cleanup

- Document explicitly what each layer does. ASPIC+: structural recursive arguments from rules + assumptions, with priorities (now populated). CKR: which generalizations hold in which contexts, with justifiable exceptions.
- Verify they don't conflict. An ASPIC+ argument concluding `p` in context `c` is undermined if `p` is excepted in `c` per CKR — encode this as a defeat in the ASPIC+ framework, with the exception's justification as the defeating argument.
- Property tests for the integrated semantics: ASPIC+ rationality postulates (consistency, closure) survive when defeats include CKR-derived exception defeats.

### Phase C-5 — `condition_classifier.py` interaction

- Once WS-Z-types lands `ConflictClass.UNKNOWN`, update `condition_classifier.py:32-36` to propagate Z3 unknowns as `UNKNOWN`, not silently as `OVERLAP`.
- The conflict_detector orchestrator should produce conflict records that distinguish `OVERLAP` from `UNKNOWN`; downstream merge classification handles them differently (an `UNKNOWN` is not evidence of conflict, just absence of decidable evidence).
- Coordinate with WS-Z-types on the type rollout; this is the consumer side.

### Phase C-6 — Documentation + CLAUDE.md update

- Update CLAUDE.md's "Argumentation layer" paragraph to describe the CKR + ASPIC+ split honestly.
- Update CLAUDE.md's "Known Limitations" — most of axis 7's findings are now resolvable; remove them as the workstream progresses, replacing with `docs/gaps.md` entries pointing at this workstream's exit state.
- `docs/defeasibility-semantics-decision.md` (from C-1) lives.
- `docs/justifiable-exceptions.md` describes the implemented semantics with examples.
- Citation-as-claim discipline: every reference to Bozzato in docstrings has a backing test.

## Red flags — stop if you find yourself

- About to commit to DL-Lite as the formal substrate.
- About to implement ABA in parallel with CKR.
- About to silently extend `superiority` with empty defaults rather than treat empty-priorities-when-data-present as a bug.
- About to populate `superiority` without verifying the strict-partial-order axioms hold for the result.
- About to map Z3 unknown to a definite conflict class without going through `ConflictClass.UNKNOWN`.
- About to retrofit ASPIC+ to encode defeasibility itself — the principle is *separation of concerns*, ASPIC+ stays structural, CKR holds the defeasibility.
- About to cite Bozzato without a backing test.
- About to write a heuristic LLM-ASPIC bridge inside this workstream — that's a separate proposal-branch heuristic workstream.
- About to implement exception provenance as a dict, source string, or bespoke support record instead of WS-A1 `SupportEvidence`.

## Exit criteria

- All primary papers + at least one ABA reference processed at non-stub depth.
- `docs/defeasibility-semantics-decision.md`, `docs/justifiable-exceptions.md` exist.
- `superiority` and `rule_order` populated from rule-file data; `preference.py` produces Modgil-Prakken Def 22 strict partial orders; property tests for strict-partial-order axioms green.
- `JustifiableException` type lives; CKR satisfaction algorithm implemented with explicit decidability-status tracking.
- Justifiable exceptions and CKR-derived defeats carry `SupportEvidence`; no parallel support/provenance representation is introduced.
- `condition_classifier.py` propagates `ConflictClass.UNKNOWN` (depends on WS-Z-types); merge classifier handles UNKNOWN as not-evidence-of-conflict.
- ASPIC+ rationality postulates survive integration with CKR exception defeats — verified by property test.
- All axis-7 findings resolved or moved to `docs/gaps.md` with a successor workstream.
- CLAUDE.md updated; `docs/gaps.md` reflects the closures.

## On learning

The defeasibility literature is sprawling — ABA, ASPIC+, defeasible logic, default logic, preferred subtheories, System Z, CKR, justifiable exceptions, prioritized propositional logics. Each has trade-offs: expressiveness vs. decidability, rule-priority vs. assumption-contrariness, single-extension vs. multi-extension semantics. Reading even just the primary papers gives you an operational understanding of why this is one of the harder areas of nonmonotonic reasoning.

CKR is the relatively young entry; it's specifically designed for *contextualized* defeasibility, which is propstore's use case. Bozzout 2018 and 2020 read together give you the full picture: 2018 introduces the framework, 2020 details the decidable fragment.

The work itself is not large in lines of code. The work is large in *clarity of thinking* — separating ASPIC+'s structural job from CKR's defeasibility job, separating the decidable fragment from the sound-but-incomplete remainder, separating populated priority data from heuristic inference. Get those separations right; the implementation follows.
