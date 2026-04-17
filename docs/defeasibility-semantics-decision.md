# Defeasibility Semantics Decision

Status: WS-C C-1 decision accepted; C-2 and C-3 implementation underway.

Date: 2026-04-17

## Inputs

This decision is based on the WS-C workstream, the 2026-04-16 axis-7 and axis-3a reviews, `docs/event-semantics.md`, and the processed notes for:

- Bozzato, Serafini, and Eiter 2018, `papers/Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md`
- Bozzato, Eiter, and Serafini 2020, `papers/Bozzato_2020_DatalogDefeasibleDLLite/notes.md`
- Diller, Gaggl, Hanisch, Monterosso, and Rauschenbach 2025, `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md`
- Bondarenko, Dung, Kowalski, and Toni 1997, `papers/Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/notes.md`
- Toni 2014, `papers/Toni_2014_TutorialAssumption-basedArgumentation/notes.md`
- Green, Karvounarakis, and Tannen 2007, `papers/Green_2007_ProvenanceSemirings/notes.md`

I verified that page-image artifacts exist for those five paper directories. I did not independently reread every page image for this decision artifact; it uses the processed notes as the local evidence base.

## Decision

Propstore should implement Bozzato-style contextual justifiable exceptions as the defeasibility semantics over the WS-A context language:

```text
ist(c, p)
```

ASPIC+ remains the structural argument-construction layer. CKR-style justifiable exceptions determine whether a generalization applies in a context, whether an exception is justified, and whether that exception defeats an ASPIC+ argument's use of the generalization in that context.

This is not a DL-Lite implementation, not an ABA implementation, and not a System Z, preferred-subtheories, WFS, or D(1,1) implementation.

## Formal Commitments

### Contexts

`docs/event-semantics.md` commits propstore to events as defeasible coreference, not to a first-class `Event` type. A context in `ist(c, p)` is therefore a description cluster. A justifiable exception in context `c` reads as:

```text
generalization p holds in description cluster c except for instances selected by exception pattern e, when e has supporting justification.
```

This keeps context membership, event identity, temporal anchoring, and provenance in the semantic substrate rather than duplicating them in WS-C.

### Exceptions

The production type should be explicit, not a loose dictionary:

```text
JustifiableException(
    target_claim,
    exception_pattern,
    justification_claims,
    context,
    support,
    decidability_status,
)
```

`target_claim` is the generalization being qualified.

`exception_pattern` is a CEL expression or equivalent typed condition over the instances to which the exception applies.

`justification_claims` is one or more propstore claims that support the exception. An exception with no supporting justification is not applied.

`context` is the description cluster in which the exception is asserted or derived.

`support` is semiring-compatible `SupportEvidence`: a provenance polynomial plus support quality. It records how source claims, rules, lifting rules, measurements, calibration records, and solver witnesses compose to support the exception. This is not a loose provenance dictionary.

`decidability_status` records whether the satisfaction decision used only decidable checks or a sound-but-incomplete path.

### Support provenance

Green 2007 changes the provenance contract. CKR exceptions and CKR-derived defeats must carry support evidence shaped for semiring projection:

```text
SupportEvidence(
    polynomial: ProvenancePolynomial,
    quality: SupportQuality,
)
```

The polynomial is positive support provenance: alternative derivations add, joint derivations multiply. Render/query policies project that support through explicit homomorphisms, for example Boolean presence, why-provenance/ATMS labels, derivation count, or tropical cost.

This does not make the claim content a polynomial. The content remains typed semantic content; the polynomial is its support annotation.

This also does not put Z3 inside the semiring. Solvers inspect claim content and produce nogoods. Current-world support projections must operate on `live(polynomial, nogoods)`, where live filtering removes monomials whose squarefree support contains a nogood. Live filtering is not a generic semiring homomorphism and must not be documented as one.

Support quality is mandatory. If support is only semantic-compatible, context-visible, mixed, or otherwise non-exact, the result must say so instead of fabricating exact polynomial support.

### Justifiability

Bozzato 2018's central requirement is retained: overriding is permitted only when justified by local clashing evidence. In propstore terms, a CKR exception must carry support claims whose content would make unqualified application of the target generalization conflict in the relevant context.

The exception mechanism is instance-level, not blanket rule deletion. If a generalization applies to many instances and only one instance has a justified exception, only that instance is excepted.

### Lifting

Exceptions lift across contexts only through explicit lifting rules from WS-A P4. There is no implicit upward propagation.

If a lifting rule licenses exception propagation from context `c` to context `c2`, the lifted exception keeps its original justification provenance and adds the lifting rule provenance. If no lifting rule licenses the move, the exception remains local.

### Decidability

The implementation should route CEL-expressible exception patterns over typed values through the existing Z3 condition machinery. When the satisfaction question depends on reasoning outside the decidable fragment, the result must be tagged as sound-but-incomplete rather than presented as complete.

Unknown solver results are not conflicts. They are unknowns. WS-C consumes WS-Z's `ConflictClass.UNKNOWN` discipline and must not collapse unknown into `OVERLAP` or into a positive exception.

## What We Drop From CKR

We do not adopt SROIQ-RL, DL-Lite, OWL/RDF vocabulary, named-individual ABox modeling, or CKRev/DLV as propstore's formal substrate.

We do not import Bozzato 2018's restriction that only global axioms can be defeasible as an arbitrary product rule. Propstore's authored claims can create contextual generalizations and contextual exceptions directly, as long as every exception is justified and provenance is explicit.

We do not claim Bozzato 2018 or Bozzato 2020 complexity bounds for the full propstore language. Those bounds belong to their selected DL fragments and datalog translations. Propstore should claim only the decidable subqueries it actually routes through Z3 or other decidable engines.

We do not use CKR's datalog translation as the implementation boundary for all semantics. Datalog grounding remains a separate layer where it is already appropriate.

## What Stays From ASPIC+

ASPIC+ keeps building arguments recursively from knowledge bases, strict rules, defeasible rules, and contrariness. The axis-3a review found the existing recursive construction directionally correct.

ASPIC+ preferences over defeasible rules are strict partial orders over authored rule priority data. WS-C C-2 closed the former empty `superiority=[]` in the grounding translator and empty `rule_order=frozenset()` in the ASPIC bridge.

CKR exceptions should interact with ASPIC+ as defeat information. If an ASPIC+ argument concludes or uses `p` in context `c`, and CKR says `p` is excepted in `c` by a justified exception, then the exception's supporting claims form the defeating argument against that use.

The exception defeat itself carries support evidence composed from exception support, lifting-rule support, and solver-witness support where applicable.

WS-A1 makes this contract executable in `propstore.defeasibility`:

- `JustifiableException.support` is `SupportEvidence`, not a dictionary, source string, or bespoke provenance record.
- `lift_exception(...)` composes support by polynomial multiplication: exception support times lifting-rule support.
- `build_exception_defeat(...)` preserves the exception object while live-filtering support through solver nogoods.
- `exception_defeat_is_live(...)` reads liveness from live why-provenance, keeping the solver/nogood boundary outside the semiring.
- Unsupported exceptions, meaning exceptions without justification claims, have zero live support and are not applied.

The separation is:

- ASPIC+ answers: what structured arguments can be built, and how do preferences affect defeat?
- CKR answers: does this contextual generalization apply here, or is this instance justifiably excepted?
- Datalog grounding answers: which first-order rule substitutions are relevant before ASPIC+ argument construction?

## Why Not ABA

Bondarenko et al. 1997 define ABA as an assumption-based framework over a deductive system with a distinguished assumption set and a contrary mapping. Attack is derived from assumptions proving contraries. Toni 2014 presents the tutorial form as `<L, R, A, contrary>` with attacks directed at assumptions in supports, plus argument-level, assumption-level, and hybrid semantics.

That is the wrong primitive for WS-C. Propstore's immediate defeasibility problem is not how to choose among assumption sets with contraries. It is how to represent context-qualified scientific generalizations with justified exceptions and explicit lifting across description clusters.

ABA remains relevant background for structured argumentation and proof procedures. It should not be implemented in parallel with CKR in WS-C because that would split the defeasibility surface between assumption contrariness and contextual exceptions.

## Implementation Consequences

### C-2 priority pipeline

Rule files need an explicit authored priority/superiority surface. The data must flow:

```text
rule file -> typed rule document -> grounding translator superiority -> aspic_bridge rule_order -> ASPIC+ defeat calculation
```

The priority relation must be validated as a strict partial order:

- irreflexive
- transitive
- asymmetric

Empty priority data is valid only when the author supplied no priority data. If priority data is present and the pipeline drops it, that is a bug.

The current metadata-strength vector in `preference.py` is not a replacement for Modgil-Prakken rule order. It may remain only if explicitly named as heuristic evidence ranking and kept out of authored rule superiority.

### C-3 justifiable exceptions

The CKR module should expose typed domain objects and typed results. It should reject dict-shaped semantic objects after the IO boundary.

This phase depends on WS-A1's semiring provenance substrate for production `SupportEvidence`. If WS-C reaches C-3 before A1 is implemented, stop rather than introducing a parallel support representation.

Core property tests:

- An exception with no justification is not applied.
- A justified exception applies only to instances selected by its pattern.
- Exceptions lift iff an explicit lifting rule licenses the lift.
- Lifted exception support multiplies exception support by lifting-rule support.
- Solver unknown produces `UNKNOWN`/sound-but-incomplete provenance, not a conflict.
- Solver nogoods can kill exception support monomials without deleting the exception object.
- Conflicting exceptions are surfaced for render-time policy rather than silently collapsed.

### C-4 boundary cleanup

The integration should encode CKR-derived exception defeat against ASPIC+ arguments without making ASPIC+ itself responsible for contextual exception semantics.

Tests should show that ASPIC+ rationality postulates survive when defeats include CKR-derived exception defeats.

## Review Gate

This document completed the decision artifact required by WS-C phase C-1. Q accepted the CKR/ASPIC+/grounding boundary in the subsequent execution instructions, so implementation phases C-2 through C-6 are proceeding against this document.
