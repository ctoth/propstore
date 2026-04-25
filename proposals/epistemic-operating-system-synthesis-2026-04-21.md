# Proposal: Situated Assertions as the Epistemic Operating System Substrate

**Date:** 2026-04-21
**Status:** Draft synthesis
**Builds on:** `proposals/epistemic-operating-system-roadmap.md`, `reports/research-structural-predicates-cel-frontend.md`, `docs/subjective-logic.md`

---

## Evidence Basis

I read the epistemic operating system roadmap, the structural-predicates/CEL research note, `docs/subjective-logic.md`, `propstore/calibrate.py`, `CLAUDE.md`, the lemon concept/context/provenance surfaces, and the grounding/gunray translator surfaces. I also used prior local inspection from this discussion of `../cel2js`, the attempted Windows build of upstream `cel-expr-python`, and `../gunray`.

I did not reread the scientific paper PDFs page-by-page for this synthesis. Any replication-rate examples below should be treated as local-note-level design anchors, not freshly adjudicated constants.

The first Claude Code architectural critique pass failed with `401 Invalid authentication credentials`. A later retry succeeded; I verified the load-bearing claims against local files before incorporating them.

---

## Thesis

The existing roadmap is right about the operating-system shape: source storage, compiled substrate, epistemic kernel, semantic services, policy, process manager, and public surfaces are the right layers.

The missing piece is the carrier those layers operate on.

Propstore should organize the OS around **situated assertions**:

```text
assertion = (relation, role_bindings, context, condition, provenance_ref)
```

where `relation` is itself a concept-shaped ontology reference, `role_bindings` bind named roles to concepts/entities/literals, `context` scopes applicability through the existing `ist(c, p)` machinery, `condition` controls when the assertion applies, and provenance is linked through the existing JSON-LD/git-notes provenance graph rather than embedded into identity.

Everything else should either be:

- a concept,
- a relation concept,
- a situated assertion using concepts,
- an epistemic state over situated assertions,
- or an operation/materialization/projection over situated assertions.

That gives the "beautiful algebra" the current roadmap is reaching for. It keeps source truth separate from belief state, keeps linguistic authoring separate from structural semantics, keeps backend atoms separate from propstore identity, and gives subjective opinions an actual proposition to attach to.

---

## Non-Commitment Discipline

This proposal must obey propstore's existing non-commitment rule: storage may hold multiple rival normalizations, candidate stances, supersession stories, and render policies. The system should not collapse disagreement merely because one compiler pass or heuristic can produce a plausible normal form.

So "canonical" in this document means one of two narrow things:

- a typed internal representation selected under a named compile/render policy;
- a current runtime projection from richer authored data.

It does not mean storage uniqueness. Authored forms, normalized candidates, and equivalence witnesses must be able to coexist until a render or migration policy chooses among them.

---

## The Atom

The atom of knowledge is not a bare concept, not a claim row, not a predicate string, not a CEL expression, and not a gunray atom.

The atom is a situated assertion:

```text
SituatedAssertion
  id
  relation: RelationConceptRef
  role_bindings: RoleBindingSet
  context: ContextReference
  condition: ConditionIR
  provenance_ref: ProvenanceGraphRef
```

Examples:

```text
published_in(paper: camerer_2018_social_science, venue: nature_human_behaviour)

reports_replication_rate(
  study: open_science_collaboration_2015,
  field: psychology,
  rate_kind: significant_same_direction,
  value: 0.36
)

supports(
  supporter: replication_rate_profile_psychology_2015,
  supported: base_rate_for_social_psychology_claims
)

has_part(
  whole: experimental_design,
  part: randomization_step
)

subtype_of(
  subtype: randomized_controlled_trial,
  supertype: empirical_method
)
```

The key move is that relation identity is no longer a loose string like `"has a"` or `"is a"`. A relation is a constrained view of the existing concept/semantic layer: an `OntologyReference` reached through a `LexicalSense`, where the sense may carry a `DescriptionKind` whose participant slots provide the role signature.

```text
RelationConceptRef
  ontology_reference
  lexical_sense
  description_kind
  role_signature
  property_assertions
  renderings
```

Relation properties such as transitivity, symmetry, functionality, inverse, and defeasibility should be assertions about the relation reference. They should not be hard-coded fields unless the kernel needs them as bootstrap semantics.

`context` should reference propstore's existing first-class context machinery: `ClaimDocument.context`, structured context documents, nested `ist(c, p)` propositions, and authored lifting rules. It should not introduce an opaque second context system.

`provenance_ref` should point into the deterministic JSON-LD named graph stored through `refs/notes/provenance`. Provenance must not contaminate assertion identity.

For example, the English phrase "has a" is not a primitive. It can render multiple structural relations:

- `has_part(whole, part)`
- `has_slot(frame, slot)`
- `fills_role(filler, role, frame)`
- `has_attribute(subject, attribute)`
- `bears_quality(subject, quality)`
- `uses_method(study, method)`

Likewise, "is a" is not one relation:

- `subtype_of(subtype, supertype)`
- `instance_of(instance, type)`
- `plays_role(entity, role, context)`
- `classified_as(subject, class, classifier, context)`

This follows the same lesson as Woods/Brachman/OntoClean/OBO RO: the linguistic link is too overloaded to be the stored structural relation.

---

## The Algebra

A compact way to frame the substrate:

```text
C = concepts
R = relation concepts, R subset C
A = situated assertions over R and C
S = epistemic states over A
O = operations over A and S
P = projections from A/S into backend languages
```

The useful operations are then explicit:

```text
select(A, predicate)       -> A'
project(A, backend)        -> backend_input
join(A1, A2, relation)     -> A3
close(A, rules)            -> A+
revise(S, evidence, policy)-> S'
merge(S1..Sn, policy)      -> S*
fuse(opinions, policy)     -> opinion
render(A/S, surface)       -> text/yaml/api
explain(S, assertion)      -> support/attack/provenance
```

This is not "everything is a triple" in the RDF sense. Role names, contexts, conditions, justification, and provenance are first-class because propstore needs source-local authoring, defeasible support, revision, merge, and audit.

The algebra also explains why the OS roadmap layers belong together:

- source storage stores authored assertions and authored concepts;
- compiled substrate indexes and normalizes assertions;
- the epistemic kernel computes states over assertions;
- semantic services are projections out of assertion state;
- policy governs operations over assertion state;
- the process manager schedules and journals operations;
- public surfaces render or edit the same substrate.

---

## Relations In Propstore

The user's requirement that "everything in propstore should be in propstore" is correct. Relations themselves should be represented as propstore concepts.

That does not mean relations are self-defining magic. The kernel needs a small bootstrap vocabulary whose semantics are implemented by the system. Above that kernel, relation definitions become ordinary propstore content.

Bootstrap primitives should be minimal:

- `concept`
- `relation_concept`
- `role`
- `has_role`
- `role_domain`
- `role_range`
- `subtype_of`
- `instance_of`
- `contextualizes`
- `condition_applies`
- `supports`
- `undercuts`
- `rebuts`
- `base_rate_for`
- `calibrates`
- `published_in`

The bootstrap vocabulary should be small enough to implement rigorously and rich enough to express the rest of the system's own metadata.

For example, `published_in` should not be treated as inert bibliographic metadata. It is a relation concept that can participate in inference:

```text
published_in(paper, venue)
venue_in_field(venue, field)
field_has_replication_profile(field, profile)
base_rate_for(profile, claim_class, base_rate)
```

That chain is exactly how Ioannidis-style prior odds and replication-base-rate information enter subjective opinions without inventing a fake universal `a = 0.5`.

---

## Linguistic Versus Structural Predicates

Propstore should be friendly to linguistic authoring, but structural in the core.

The author should be able to write or see:

```text
randomized controlled trial is an empirical method
trial has a randomization step
paper was published in Nature
```

The core should see:

```text
subtype_of(randomized_controlled_trial, empirical_method)
has_part(trial, randomization_step)
published_in(paper, nature)
```

This makes implicit language explicit. The authoring surface can remain humane, but the structural assertion has typed roles, stable identity, validation, source spans, and backend lowering.

This is the conceptual answer to the earlier "linguistic or structural" question: propstore wants linguistic entry and rendering, but structural storage and reasoning. The work is the compiler from linguistic/convenient authoring into structural assertions.

That also answers the "is all this work to convert linguistic conditions into structural ones?" question: yes, but not only conditions. It is the whole predicate surface. Conditions, relation declarations, source metadata, policy declarations, and reasoning outputs should all converge into structural assertions.

---

## CEL And cel2py

CEL should not be the ontology. CEL should be a condition/query authoring language that compiles into propstore's typed condition IR.

The upstream CEL Python build experiment showed that full upstream runtime conformance is possible on Windows with patches, but it implies a fork and API work. That is not the right center of gravity if propstore needs tree access, source spans, structural relation bindings, and Python-native integration.

The better architecture is:

```text
author text
  -> SurfaceAst with spans
  -> ResolvedAst with concept/relation bindings
  -> ConditionIR with typed operators
  -> CheckedCondition with registry fingerprint
  -> backend artifacts
```

Backends include:

- Z3 constraints,
- Python AST,
- JavaScript ESTree,
- SQL predicates where possible,
- human rendering.

The `../cel2js` design is the right semantic precedent. It is not "compile CEL by pretending it is JavaScript"; it emits backend AST that calls runtime helpers for CEL semantics. A `cel2py` should do the same for Python:

```text
ConditionIR
  -> Python ast.AST
  -> calls _rt helpers for CEL equality, arithmetic, optionals, lists, maps, nulls, errors
```

But `_rt` nodes must never be propstore semantic AST nodes. They belong only in backend IR.

That split should be enforced by types, not convention: `ConditionIR` should be a closed Python sum type that cannot contain backend runtime-helper nodes, while Python/JS backend IR should be a disjoint type family that can contain `_rt` calls.

So the nanopass split should be strict:

- frontend passes preserve source tree, spans, and author-facing syntax;
- middle passes resolve names, macros, types, and structural conditions;
- backend passes introduce runtime helper calls and target-specific evaluation rules.

This likely deserves its own package once it becomes serious, because full CEL conformance, parser tests, Python AST emission, and JS emission are compiler work. Propstore should own the binding layer from CEL identifiers to propstore concepts and relation concepts. The CEL package should own language conformance and backend lowering.

---

## Opinions And Base Rates

A subjective opinion attaches to a situated assertion, not to a relation globally:

```text
opinion_about(assertion_id) = (belief, disbelief, uncertainty, base_rate)
```

For example, the opinion is about:

```text
published_in(paper: P, venue: V)
```

or:

```text
supports(evidence: E, claim: C)
```

or:

```text
base_rate_for(profile: psychology_replication_2015, claim_class: social_psychology_claim)
```

It is not about `published_in` as a universal relation.

The current code and docs still contain the old fallback shape:

- `docs/subjective-logic.md` says base rate `a` defaults to `0.5`;
- `propstore/calibrate.py` uses `0.5` when no category prior is supplied;
- sidecar/test surfaces also preserve `opinion_base_rate REAL DEFAULT 0.5`.

That was a reasonable implementation stepping stone, but it is conceptually wrong for the OS target. Ignorance is not `a = 0.5`. Ignorance is missing evidence, missing prior, or both.

The target distinction should be:

```text
known prior + no direct evidence:
  Opinion.vacuous(a=sourced_base_rate)

unknown prior + no direct evidence:
  UnresolvedOpinion / BaseRateUnknown

known prior + evidence:
  Opinion(b, d, u, a=sourced_base_rate)
```

If an operation requires an expected probability, it must either resolve a prior from propstore assertions or fail with a typed "base rate unresolved" condition. It should not silently insert `0.5`.

`a = 0.5` is still valid when it is itself justified: a symmetric binary frame, a policy assertion, or a calibrated base-rate assertion can produce 0.5. It is not valid as the default representation of ignorance.

There is a recursion hazard here. Base-rate resolution cannot be an unrestricted query over propstore, because the assertions that define a base-rate profile may themselves carry opinions. The resolver needs a stratification rule:

```text
BaseRateProfile can resolve a prior only when its own support is
measured, calibrated, or stated under the selected policy.

Otherwise:
  return BaseRateUnresolved
```

This lines up with the existing `ProvenanceStatus` taxonomy (`measured`, `calibrated`, `stated`, `defaulted`, `vacuous`) and prevents the resolver from looping or falling back to `0.5`.

The current implementation is already partly aimed in this direction: `CategoryPrior` and `CalibrationSource` make priors explicit. The remaining conceptual bug is the silent fallback in `categorical_to_opinion`, where missing category prior becomes `0.5`. The target should be a typed unresolved result or a required prior at the caller boundary.

This is where the local replication-rate material matters. Existing notes point at very different replication profiles:

- psychology replications around 36 percent significant replication overall, with social/cognitive differences;
- experimental economics around 61 percent in one replication project;
- Nature/Science social science around 62 percent in one project;
- preclinical cancer replication success varying radically by criterion.

Those numbers should not become constants in code. They should become propstore assertions about studies, fields, methods, venues, and claim classes. Then base-rate resolution becomes a query over propstore itself.

---

## Gunray

Gunray should not be the kernel. It should be a proof/evaluation backend.

The propstore-to-gunray boundary should look like:

```text
situated assertions + policy + context
  -> projection
  -> Gunray DefeasibleTheory / Datalog program / KLM fragment
  -> evaluation
  -> lifted derived assertions
```

Gunray's `GroundAtom(predicate, arguments)` is a backend encoding. The `predicate` string should eventually be derived from a relation concept id and role signature, not treated as propstore identity.

The current `propstore.grounding.predicates` layer already has a projection DSL with three sanctioned source kinds:

- `concept.relation`
- `claim.attribute`
- `claim.condition`

The situated-assertion plan should extend or replace that deliberately, not invent a second invisible projection system.

Every projection frame must preserve a round-trippable mapping from backend artifacts to originating assertion ids. For gunray that means either:

- include the originating assertion id as a term in every projected atom where that is semantically acceptable; or
- maintain a projection-frame mapping table from emitted atom/rule text back to `SituatedAssertion.id`.

Without that bijection, lifted backend results cannot honestly attach opinions, provenance, or audit explanations to the assertion that produced them.

Gunray outputs should lift back into propstore as assertions such as:

```text
defeasibly_holds(assertion)
definitely_holds(assertion)
not_defeasibly_holds(assertion)
has_acceptability_status(argument, status)
```

That keeps gunray useful without letting it own identity, source truth, belief revision, or policy.

---

## Revised OS Layering

The seven roadmap layers remain right, but each layer should be interpreted through the situated-assertion substrate.

| Roadmap layer | Situated-assertion interpretation |
| --- | --- |
| Source storage | Authored concepts, relation concepts, situated assertions, source spans, provenance |
| Compiled substrate | Canonical assertion indexes, condition IR, relation signatures, sidecar materializations, base-rate profiles |
| Epistemic kernel | States over assertions: support, attack, ranking, opinion, revision, merge, snapshots |
| Argumentation and semantic services | Projections from assertion states into ASPIC/PrAF/gunray/Z3/CEL/Python/JS |
| Policy and governance | Assertions about admissibility, operators, source trust, priors, escalation, approval |
| Process manager | Journaled operations over assertion states: revise, merge, investigate, observe, compare |
| Public surfaces | Linguistic/rendered editing and inspection of the same structural substrate |

The important constraint is ownership:

- CEL does not own condition semantics.
- Gunray does not own propstore identity.
- Argumentation does not own belief change.
- Sidecar rows do not own source truth.
- CLI does not own workflows.
- Policy is not flags scattered through commands.

Each service consumes or produces situated assertions through a typed boundary.

---

## Roadmap Amendment

The current roadmap jumps from formal merge completion into structured consumers and then policy. That sequence needs one explicit substrate phase, but it should not silently collide with the existing Phase 7 label.

Insert:

```text
Phase 6.5: Situated Assertion and Relation-Concept Substrate
```

Goal:

- define the shared semantic carrier and relation vocabulary that revision, merge, policy, CEL, gunray, argumentation, snapshots, and investigation all share.

Deliverables:

- `RelationConceptRef`, `RoleSignature`, `RoleBinding`, `SituatedAssertion`, `ConditionIR`, and `BaseRateProfile` domain objects;
- small bootstrap relation vocabulary;
- identity rules for situated assertions that preserve rival normalized candidates;
- CEL frontend pass that emits `ConditionIR`, not backend helper calls;
- projection boundary from situated assertions to gunray atoms/rules;
- assertion-id round trip for backend projections;
- opinion attachment to assertion identity;
- base-rate resolution from propstore assertions, with explicit unresolved-prior failure;
- conformance tests for relation signatures, condition normalization, backend projection, and round-trip rendering.

Then continue with the existing roadmap labels:

```text
Phase 7: Structured State Semantics
Phase 8: Policy and Governance
Phase 9: Snapshot, Journal, and Diff
Phase 10: Investigation and Intervention Manager
Phase 11: Evaluation and Observatory
Phase 12: Product Surface Unification
```

The numbering matters because other planning artifacts can already refer to Phase 7. The dependency is the point: structured consumers and policy should not grow on top of the current loose predicate/condition surface.

---

## Immediate Execution Slice

The immediate slice should be a design-and-code control surface for Phase 6.5, not another ad hoc CEL parser or another argumentation adapter.

Concrete first slice:

1. Write the situated assertion object spec.
2. Define the bootstrap relation vocabulary.
3. Define assertion identity without collapsing rival normalized candidates.
4. Define `ConditionIR` independent of CEL and independent of `_rt`.
5. Define base-rate resolution as a typed service that can return `BaseRateUnknown`.
6. Update the CEL plan so Lark/CEL parses into `ConditionIR`.
7. Update the gunray boundary so backend predicates are projections from relation concepts.
8. Add assertion-id round-trip requirements to every projection frame.
9. Add conformance tests before broad caller migration.

Success criteria:

- no structural semantic object stores `"is a"` or `"has a"` as an undifferentiated predicate;
- no `ConditionIR` node stores backend `_rt` nodes;
- no backend atom string is treated as propstore identity;
- no scientific assertion gets `a = 0.5` unless a sourced prior or explicit policy produced it;
- relation definitions can themselves be represented as propstore content above the bootstrap kernel.

---

## Non-Negotiable Invariants

1. **The atom is situated.**
   A claim without relation, roles, context, condition, and provenance reference is not a complete semantic object.

2. **Relations are concepts.**
   Relation declarations, role signatures, and relation properties belong in propstore, with a small implemented bootstrap.

3. **Linguistic predicates are authoring/rendering surfaces.**
   "is a" and "has a" must compile into explicit structural relations.

4. **CEL is a frontend and backend compiler target, not the ontology.**
   CEL source trees are useful. CEL runtime helpers are backend artifacts.

5. **Opinions attach to assertions.**
   A Josang opinion is about a proposition in context, not a global relation name.

6. **Base rates are sourced or unresolved.**
   `a = 0.5` is a possible result, not the representation of ignorance.

7. **Backends are projections.**
   Gunray, Z3, Python AST, JavaScript ESTree, SQL, ASPIC, and PrAF consume projections and return lifted results.

8. **Policy is propstore content.**
   Operator choice, admissibility, priors, source trust, and escalation rules should be inspectable assertions, not hidden flags.

9. **Every operation is journalable.**
   Revision, merge, projection, base-rate resolution, opinion fusion, and investigation steps must be reconstructable from state-in, policy, operation, and state-out.

10. **Rival normalizations coexist.**
    Storage keeps authored forms, normalized candidates, and equivalence witnesses. Canonicalization is a render-time or explicit-migration decision, not a side effect of parsing.

11. **Projection must round-trip identity.**
    Backend artifacts must carry or map back to originating situated assertion ids before their results can be lifted into propstore.

---

## Open Questions

- What is the exact bootstrap vocabulary, and what can be represented above it?
- Does `Context` live as a relation concept family, a separate domain object, or both?
- Should `BaseRateUnknown` be a distinct object outside `Opinion`, or should `Opinion` be wrapped in an assessment type that can be unresolved?
- Which relation properties are implemented by the kernel: transitive, symmetric, functional, inverse, defeasible, monotone?
- How much of OBO RO, DOLCE, BFO, SHACL, or Common Logic should be imported as design guidance versus represented as propstore content?
- What is the minimal CEL conformance tranche needed before replacing current CEL paths?
- Should `cel2py` live as `propstore-cel`, `cel2py`, or a package inside propstore until the API stabilizes?
- How are source-local authored relation templates promoted into shared relation concepts under a named policy?
- What equivalence witness links situated assertions whose conditions are syntactically different but semantically equivalent?

---

## Bottom Line

The epistemic operating system becomes coherent when the whole stack has one semantic carrier: situated assertions over relation concepts.

That carrier lets propstore keep the parts that already work: source storage, sidecar compilation, revision, merge, ATMS, argumentation, opinions, worldlines, fragility, and gunray-style reasoning. It also explains how to make the next pieces principled instead of ad hoc: parse linguistic and CEL surfaces into structural assertions, attach opinions to those assertions, resolve base rates from propstore content, project into backends, and journal every transition.

The roadmap should therefore insert the situated-assertion substrate before expanding structured consumers and policy. Without it, the OS grows around loose predicate strings. With it, propstore can make its own relations, priors, policies, and reasoning outputs first-class knowledge inside propstore itself.
