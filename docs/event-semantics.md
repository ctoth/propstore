# Event Semantics — Position Statement

Grounds WS-A phase 3 (`reviews/2026-04-16-code-review/workstreams/ws-a-semantic-substrate.md`); composes with WS-C (`reviews/2026-04-16-code-review/workstreams/ws-c-defeasibility.md`).

## 1. Position

**Events as defeasible coreference.** propstore does not treat events as individuals with pre-descriptive identity conditions. There are description-claims — observation-descriptions, measurement-descriptions, assertion-descriptions, decision-descriptions — each with provenance, participant slots, and temporal anchoring. What we informally call "an event" is a render-time inference: a cluster of description-claims under an explicit merge-hypothesis whose justification is itself a defeasible argument resolvable by Dung semantics over the existing argumentation layer. Coreference is never a fact about the world; it is the conclusion of an argument that survives attack under some assumption-set, queryable at render time and revisable in principle.

This commits us against Davidsonian (1969 / 1985) event identity, neo-Davidsonian event reification (Parsons 1990), Kripkean rigid designation across worlds, and Lewisian counterpart theory. It commits us toward Hobbs (1985) ontological promiscuity treated as posits-not-discoveries, Quine (1968) ontological relativity, and late-period Putnam internal realism. Practically it commits us to: no `Event` type; no event-individuation primitives; coreference resolved by argumentation-over-merge-proposals; `worldline/` as an agent's own description-trajectory; contexts (per WS-A P4) interpretable as description-clusters; causation as a description-level claim with its own defeasibility, not a relation between determinate underlying entities.

## 2. Why this matters

The architectural payoff of propstore's non-commitment discipline extended into the temporal domain:

- **Federation.** Two contributors never disagree about "what the event was" because there is no event to disagree about. They contribute different description-claims; the merge question is explicit and argumentation-mediated rather than hidden in an entity-identity fact one pipeline silently decided.
- **Non-commitment all the way down.** Storage already holds rival normalizations, stances, supersession stories without collapsing at write time. The same discipline extends to event-coreference: merge proposals live on proposal branches with provenance, survive as rival cluster-hypotheses, resolve per render policy.
- **Composition with existing machinery.** PAF, ATMS labels, and Dung extensions are the tools for "are these the same event?" — no parallel event-individuation infrastructure is invented.

## 3. Philosophical lineage

- **Hobbs 1985, *Ontological Promiscuity*.** The licensing-to-posit move: AI/NLP may freely posit entities (events, situations, abstract kinds) because they serve inferential roles. propstore's taken-seriously version: posit them, but as *posits* — artefacts of a description scheme — not discoveries about the world.
- **Quine 1968, *Ontological Relativity*.** Reference is inscrutable; what exists is relative to a translation manual. Translated: there is no fact-of-the-matter about which underlying entities our descriptions refer to, so the system refuses to stake a metaphysical claim it cannot cash out.
- **Late-period Putnam, internal realism.** Truth and reference are internal to a conceptual scheme, not correspondence to mind-independent objects. Putnam eventually backed away; we inherit the earlier spirit — no view-from-nowhere that adjudicates event-individuation.

## 4. What we are explicitly NOT doing

- **Davidsonian event identity (1969 causal, 1985 spatiotemporal).** Both presuppose events are individuals whose identity is a fact about the world. No such metaphysical commitment.
- **Neo-Davidsonian event reification (Parsons 1990).** The cleanest version of the position we considered and rejected; read for contrast.
- **Kripkean rigid designation across worlds.** Presupposes pre-descriptive individuation. Not needed.
- **Lewisian counterpart theory.** Same.
- **The whole transworld-identity apparatus.** Same — no metaphysical event-individuation problem because no metaphysical events.
- **An `Event` type peer to `OntologyReference`.** No event individual; what would the type refer to?
- **`causes(e1, e2)` as a primitive between determinate event individuals.** Causal connection is itself a *description-kind* — a claim with its own provenance and defeasibility over two other description-claims.
- **Frames-as-individuated-categorical-types.** Already dropped (WS-A P3 first reframe).

## 5. Practical commitments

- **Description-kinds are concepts** (lemon `LexicalEntry` + `LexicalSense`): `Observation`, `Measurement`, `Assertion`, `Decision`, `Reaction`.
- **Particular descriptions are claims** (in `claim_core`) whose predicate is a description-kind concept and whose bindings fill the kind's participant slots.
- **Pustejovsky qualia + Dowty proto-roles decorate description-kind senses** — qualia license type coercion across kinds; proto-roles carry graded entailments on participant slots.
- **Temporal anchoring uses `KindType.TIMEPOINT`** plus `ConditionSolver` providing Allen-1983 interval reasoning. Description-claims locate in time via TIMEPOINT-valued slot bindings; `DescriptionTemporalAnchor` and `description_temporal_relation` are a thin Allen-relation layer over `propstore.core.conditions`, not a second temporal system.
- **Coreference is a Dung argument resolved at render time.** `MergedDescriptionCluster` is a query-time view over merge proposals; acceptance is policy-dependent; rival cluster-hypotheses survive in storage.
- **Causation is a description-kind.** `CausalConnectionAssertion(target_descriptions, account, provenance)` where `account ∈ {stated, counterfactual, statistical, mechanistic}`. Transitivity is conditional on the account, not a unified causal closure.
- **Contexts are interpretable as description-clusters** (WS-A P4). `ist(c, p)` reads as "p is true in the cluster I am calling c." Composes with WS-C CKR exceptions: "this generalization holds across cluster c, except in the cases described by these other description-claims."
- **`worldline/` is an agent's own description-trajectory.** The physics metaphor fits — a worldline is relative to a frame.

## 6. Pushback acknowledged

**Description quality as first-class.** Some descriptions *do* have privileged status — a video recording, a lab instrument readout, a preregistered protocol. Not because they are metaphysically "closer to the event," but because the argumentative machinery gives them lower attack-surface (chain-of-custody auditable, medium harder to forge, temporal anchoring automatic). Opinion algebra + provenance + fragility scoring already represent description-quality without sneaking metaphysical privilege back in. Stay vigilant: never introduce a `description_quality_truth_factor` that re-imports realism through the side door.

**UI cooperation with the surface ontology.** Users will talk as if events are individuals ("tell me about the Camerer replication"). The render layer cooperates: `pks event "X"` returns the current-best description-cluster with the merge-argument inspectable on drill-down. Internals stay descriptivist; the cluster rendered for a user is a momentary inference under that user's render policy, not a stored fact.

## 7. References

Per `disciplines.md` rule 1: every paper resolves to a `papers/<dir>/` location or is tagged `to fetch` against `semantic-substrate-papers.md`. Code citations must come with a backing test, runtime invariant check, or linked `xfail`.

- **Hobbs 1985, *Ontological Promiscuity*** — `to fetch` (P3-primary). Ontological-promiscuity argument.
- **Quine 1968, *Ontological Relativity*** — `to fetch` (P3-primary). Translation-manual / inscrutability-of-reference argument.
- **Putnam, late-period internal-realism essays** — `to fetch` (P3-secondary; *Realism with a Human Face*). Earlier spirit, not the late retraction.
- **Davidson 1967, *The Logical Form of Action Sentences*** — `to fetch` (read-for-rejection). Position considered and rejected.
- **Davidson 1969, *The Individuation of Events*; 1985, *Reply to Quine on Events*** — `to fetch` (read-for-rejection). Causal identity (1969, abandoned as circular); spatiotemporal identity (1985, contested).
- **Parsons 1990, *Events in the Semantics of English*** — `to fetch` (read-for-rejection). Maximally-developed neo-Davidsonian reference.
- **Pustejovsky 1991, *The Generative Lexicon*** — `papers/Pustejovsky_1991_GenerativeLexicon/`. Qualia and type coercion.
- **Dowty 1991, *Thematic Proto-Roles*** — `papers/Dowty_1991_ThematicProtoRoles/`. Proto-agent / proto-patient graded entailments.
- **Fillmore 1982, *Frame Semantics*** — `papers/Fillmore_1982_FrameSemantics/`. Cognitive-frame motivation; not an implementation target.
- **Allen 1983, *Maintaining Knowledge About Temporal Intervals*** — interval relations over `KindType.TIMEPOINT` via `ConditionSolver`; already consumed.

## 8. Cross-references within propstore

- `reviews/2026-04-16-code-review/workstreams/ws-a-semantic-substrate.md` — WS-A phase 3 implements this position; its second reframe note motivates the descriptivist turn.
- `reviews/2026-04-16-code-review/workstreams/ws-c-defeasibility.md` — "Composition with WS-A's descriptivist event semantics" explains how CKR justifiable exceptions compose with description-clusters.
- `semantic-substrate-papers.md` — P3 section and paper retrieval list; `to fetch` tags resolve here.
- `reviews/2026-04-16-code-review/workstreams/disciplines.md` — citation-as-claim, papers-first, no-backward-compat disciplines apply.
- `CLAUDE.md` — Literature Grounding should be updated to reference this doc once canonical; see report companion for flagged cross-refs.
