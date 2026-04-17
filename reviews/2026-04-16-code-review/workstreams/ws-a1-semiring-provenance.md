# Workstream A1 - Semiring Provenance Substrate

Date: 2026-04-17
Status: proposed - inserted because axis 3d found Green-style provenance absent
Depends on: `disciplines.md`, `judgment-rubric.md`, WS-A source/artifact boundaries
Blocks: WS-C C-3 support contract, ATMS label collapse, support-bearing fragility rewrite
Review context: `../axis-3d-semantic.md` section 6, `../axis-3e-reasoning-infra.md`, `../axis-4-test-adequacy.md`
Design review: drafted with Claude CLI; adversarial pass incorporated before implementation.

## Why this exists

The 2026-04-16 semantic review already found the gap:

> What Green 2007 formalizes: K-annotated tuples where K is a commutative semiring, subsuming bag/set/why-provenance/lineage. No K-annotation anywhere in `propstore/`.

WS-A listed Green 2007 only as optional background for phase 1 provenance. There is no executable workstream that turns Green 2007 into propstore's support substrate. WS-C exposed that absence because justifiable exceptions need compositional support provenance, not a generic source blob.

This workstream supplies the missing substrate. It does not replace CKR, ASPIC+, Dung, ATMS behavior, or Z3. It gives them one shared support algebra.

## Core decision

Claims remain typed semantic content. Support becomes a provenance polynomial.

```text
AnnotatedClaim(
    content: ClaimContent,
    support: SupportEvidence,
)

SupportEvidence(
    polynomial: ProvenancePolynomial,
    quality: SupportQuality,
)
```

The polynomial is Green 2007's positive provenance object: alternative derivations add, joint derivations multiply, and projections are explicit semiring homomorphisms. The proposition and its support are different objects.

`SupportQuality` is mandatory. The current system has honest non-exact states such as `EXACT`, `SEMANTIC_COMPATIBLE`, `CONTEXT_VISIBLE_ONLY`, and `MIXED`. A1 must preserve that honesty. Do not fabricate an exact support polynomial when support is only semantic-compatible or context-visible.

## Existing repo fit

The current ATMS code is already close to a why-provenance projection:

- `propstore/core/labels.py::EnvironmentKey` is a support monomial with two distinct dimensions: `assumption_ids` and `context_ids`.
- `Label.environments` is an antichain of support monomials.
- `combine_labels` is multiplication projected to why-provenance.
- `merge_labels` is addition projected to why-provenance.
- `NogoodSet.excludes` is support-set pruning.
- `propstore/world/atms.py` is the operational engine that consumes those labels for environments, replay, intervention planning, and explanation.

The new substrate must fit that architecture before it subsumes it. The first deletion target is not ASPIC or Dung. It is duplicated support truth.

## Target architecture

Storage holds three orthogonal things:

- typed claim content;
- support evidence as a provenance polynomial plus support quality;
- content-level nogoods emitted by solvers.

Everything else is a view:

```text
support polynomial + projection policy -> Boolean trust / why-provenance / counts / cost / fragility input
claim content + solvers -> nogoods and witnesses
polynomials + nogoods + directional rules -> derived argumentation view
```

### Source variables

Every primitive support-bearing artifact receives a stable source variable:

```text
SourceVariable(
    id: SourceVariableId,
    role: SourceRole,
    artifact_id: str,
    canonical_body_hash: str,
    provenance: ProvenanceRecord,
)
```

Required roles:

- `CLAIM`
- `RULE`
- `MEASUREMENT`
- `CALIBRATION`
- `LIFTING_RULE`
- `SOLVER_WITNESS`
- `ASSUMPTION`
- `CONTEXT`

`ASSUMPTION` and `CONTEXT` are separate roles because current `EnvironmentKey` separates `assumption_ids` from `context_ids`. A projection that collapses them is wrong.

`SourceVariable.id` must be content-addressed from `(role, artifact_id, canonical_body_hash)`. It must not depend on load order, in-memory iteration order, or mutable post-finalize payloads. If artifact promotion still mutates payloads at the variable boundary, stop and fix that boundary first.

### Polynomial

The core representation is a canonical sparse polynomial:

```text
ProvenancePolynomial(
    terms: tuple[PolynomialTerm, ...]
)

PolynomialTerm(
    coefficient: PositiveInt,
    powers: tuple[VariablePower, ...]
)

VariablePower(
    variable: SourceVariableId,
    exponent: PositiveInt,
)
```

Canonicalization requirements:

- variables inside a monomial are sorted by stable id;
- identical monomials are combined by coefficient addition;
- zero coefficients are rejected;
- the zero polynomial is explicit;
- addition canonicalizes;
- multiplication distributes and canonicalizes;
- multiplicity is preserved for projections that care about derivation counts.

ATMS-style support uses the squarefree support set of a monomial. That is a projection. `x * x` and `x` are different in `N[X]`, but they map to the same why-provenance support set. This must be explicit in code and tests.

### Homomorphic evaluation

Expose one typed evaluator:

```text
evaluate(poly, homomorphism) -> K
```

The homomorphism supplies:

- zero and one;
- add and multiply;
- a variable mapping `SourceVariableId -> K`.

Initial projections:

- Boolean presence/trust;
- natural-number derivation count;
- why-provenance / ATMS support environments;
- tropical cost for preferred single derivation.

Probability-like projections are out of scope for A1. A future probability projection must return a typed result that carries independence assumptions or interval/bound semantics. A naked confidence float is forbidden.

### Nogoods and live support

Z3, CEL, CKR, and conflict detection sit outside the semiring. They inspect claim content and produce nogoods:

```text
ProvenanceNogood(
    variables: frozenset[SourceVariableId],
    witness: NogoodWitness,
    provenance: ProvenanceRecord,
)
```

A monomial is dead when its squarefree support set contains a nogood variable set. The live support for current-world projections is:

```text
live(poly, nogoods)
```

Important: `live` is filtering by a monomial ideal, not a semiring homomorphism. Do not claim that `project(live(poly)) == live(project(poly))` for every projection. Some idempotent projections can commute with live filtering; non-idempotent counting and cost projections generally do not.

All current-world fragility and support projections must operate on `live(poly, nogoods)`, not raw support.

### Argumentation view

Do not delete AF/Dung/ASPIC concepts in A1.

Nogoods alone give symmetric inconsistency. They do not capture directional undercut, rebut, preference-sensitive defeat, or CKR exception defeat. The correct boundary is:

```text
polynomials + nogoods + directed contrary/exception/preference rules
    -> derived attack/defeat graph
    -> Dung/ASPIC+ semantics
```

ASPIC+ arguments gain support annotations. Their directed attack/defeat semantics remain in `aspic.py`, `aspic_bridge/*`, and `dung.py`.

## Deletion and subsumption plan

This workstream is allowed to subsume existing support machinery, but only through proof, not parallel truth.

### Keep as consumers/views

- `propstore/aspic.py`
- `propstore/aspic_bridge/*`
- `propstore/dung.py`
- `propstore/dung_z3.py`
- `propstore/praf/*`
- `propstore/world/atms.py` environment/replay/explanation behavior
- `propstore/core/micropublications.py`
- `propstore/core/justifications.py`

### Collapse after equivalence gates

- `propstore/core/labels.py::Label`
- `EnvironmentKey`
- `NogoodSet`
- `combine_labels`
- `merge_labels`
- `normalize_environments`

At the end of the collapse phase, these names may remain only as thin projection/view names over the polynomial substrate. They must not store an independent support truth.

### Do not delete in A1

- Directional attack/defeat construction.
- Non-support intervention discovery in fragility.
- CKR exception semantics.
- Negation-as-failure reasoning.

### Delete only after stronger gates

Support-reconstruction code inside `fragility_contributors.py` may be deleted only for intervention kinds whose support is actually covered by derivative-over-live-support. Derivative fragility is one input, not a replacement for every intervention family. `MISSING_MEASUREMENT`, `CONFLICT`, and `BRIDGE_UNDERCUT` require their own semantics and must not silently become empty derivative outputs.

## Module design

Create a package:

```text
propstore/provenance/
    variables.py
    polynomial.py
    homomorphism.py
    nogoods.py
    projections.py
    derivative.py
    support.py
```

Expected public types:

- `SourceVariable`
- `SourceVariableId`
- `SourceRole`
- `ProvenancePolynomial`
- `PolynomialTerm`
- `VariablePower`
- `Homomorphism`
- `ProvenanceNogood`
- `NogoodWitness`
- `SupportEvidence`
- `SupportQuality`

Do not pass dict-shaped provenance polynomial objects through the semantic pipeline. Dicts may exist only at IO boundaries.

## Phase structure

### Phase A1-1 - Core algebra

- Implement source variables with stable ids.
- Implement polynomial terms and canonicalization.
- Implement addition, multiplication, zero, one.
- Implement typed homomorphism evaluation.
- Implement support quality types.

Property tests:

- addition is associative and commutative;
- multiplication is associative and commutative;
- multiplication distributes over addition;
- zero and one identities hold;
- canonicalization is idempotent;
- multiplication of sums preserves multiplicity;
- why-provenance projection is invariant under `x^k -> x`.

### Phase A1-2 - Projections and live filtering

- Implement Boolean projection.
- Implement derivation-count projection.
- Implement why-provenance / ATMS-environment projection.
- Implement tropical-cost projection.
- Implement provenance nogoods.
- Implement live-polynomial filtering.

Property tests:

- Green 2007 homomorphism law holds for implemented homomorphisms before live filtering;
- every monomial of `live(poly, nogoods)` contains no nogood support subset;
- every monomial of `poly` not killed by a nogood survives with its coefficient;
- context-only variables project to labels with empty assumptions and non-empty contexts;
- assumption-only variables project to labels with non-empty assumptions and empty contexts;
- tests explicitly demonstrate that live filtering does not commute with non-idempotent projections, so nobody can accidentally claim it does.

### Phase A1-3 - ATMS collapse gate

- Build a read-only equivalence harness between current labels and polynomial projections.
- Port all existing label property tests to the polynomial substrate.
- Exercise real ATMS paths, not only generated positive DAGs.
- Preserve `SupportQuality` states in `claim_support`.

Required gates before collapsing `core/labels.py`:

- `Label -> polynomial -> Label` round-trips every environment shape currently emitted by `compile_environment_assumptions`.
- `EnvironmentKey.assumption_ids` and `EnvironmentKey.context_ids` survive separately.
- Current `tests/test_labels_properties.py`, `tests/test_labelled_core.py`, and relevant `tests/test_atms_engine.py` behavior pass against polynomial-backed labels.
- `claim_support` reproduces `EXACT`, `SEMANTIC_COMPATIBLE`, `CONTEXT_VISIBLE_ONLY`, and `MIXED`.
- Pyright is clean after redirecting all importers of `core.labels`.
- No production code constructs independent label truth after collapse.

Only after those gates pass may `Label`, `EnvironmentKey`, `NogoodSet`, `combine_labels`, `merge_labels`, and `normalize_environments` become projection/view APIs over polynomial support.

### Phase A1-4 - Support-bearing fragility

- Add derivative operations over polynomials.
- Add derivative operations over live support.
- Route support-bearing fragility inputs through derivative/live support where the intervention kind is covered.
- Keep intervention family discovery and ranking policy surfaces.

Property tests:

- derivative of a sum is the sum of derivatives;
- derivative of a product follows the polynomial product rule;
- dead monomials do not contribute to derivative fragility;
- source removal affects exactly the monomials containing that source variable;
- support-bearing intervention kinds have parity with the old path before deletion;
- unsupported intervention kinds raise or keep their existing semantics, never silently return empty derivative results.

### Phase A1-5 - WS-C contract

Update WS-C types and docs to use semiring-shaped support:

```text
JustifiableException(
    target_claim,
    exception_pattern,
    justification_claims,
    context,
    support: SupportEvidence,
    decidability_status,
)
```

CKR-derived exception defeats also carry support evidence:

```text
ExceptionDefeat(
    defeated_use,
    exception,
    support: SupportEvidence,
    solver_witness,
)
```

Property tests:

- unsupported exception has zero live support and is not applied;
- lifted exception support multiplies exception support by lifting-rule support;
- a solver nogood kills an exception support monomial without deleting the exception object;
- Boolean projection says an exception defeat is live iff why-provenance after live filtering is non-empty;
- support quality is preserved across exception defeat construction.

## Tests that must catch lying

- A grep or type gate rejects new functions in `propstore/provenance/` returning naked `float` confidence.
- A property test proves why-provenance projection preserves the assumption/context split.
- A property test proves `live` does not get documented or implemented as a generic homomorphism.
- A snapshot test proves `SourceVariable.id` remains stable across artifact finalization/promotion cycles.
- A test proves every production label construction after A1-3 goes through the polynomial projection path.
- A test proves unsupported or non-exact support stays marked non-exact rather than becoming fabricated polynomial support.

## Red flags - stop if you find yourself

- About to store claim support as a loose provenance dict.
- About to treat a polynomial as claim content.
- About to return a naked probability or confidence float.
- About to put subjective-logic discount inside semiring multiplication.
- About to claim Green 2007 handles negation-as-failure.
- About to erase directed attack/defeat because a nogood relation exists.
- About to compute current-world fragility from raw support rather than live support.
- About to preserve a parallel ATMS label truth after polynomial-backed labels are available.
- About to introduce a `SourceVariable` whose id depends on load order or mutable payload state.
- About to delete fragility intervention families that derivative support does not model.

## Exit criteria

- `propstore/provenance/` exists with typed variables, polynomials, homomorphisms, nogoods, projections, derivatives, and support quality.
- Core semiring laws are property-tested.
- Green 2007 homomorphic projection is property-tested for implemented projections before live filtering.
- Live filtering is first-class, property-tested, and documented as non-homomorphic in general.
- Why-provenance projection matches current ATMS label behavior across assumption and context dimensions.
- `core/labels.py` no longer stores independent support truth after the collapse gate.
- Support-bearing fragility uses derivative over live support where applicable, with uncovered intervention kinds honestly preserved.
- WS-C exception/defeat contracts use `SupportEvidence`, not generic provenance blobs.
- Documentation states the limits: positive provenance is implemented; negation-as-failure provenance is not claimed.

## Papers

Primary:

- Green, Karvounarakis, Tannen 2007, *Provenance Semirings*.
- de Kleer 1986, *An Assumption-Based TMS*.

Secondary before extending scope:

- Buneman 2001, *Why and Where: A Characterization of Data Provenance*.
- Carroll 2005, *Named Graphs, Provenance and Trust*.
- Geerts/Poggi on K-relations and negation only if scope moves beyond positive provenance.
- Amsterdamer/Deutch/Tannen on aggregate provenance only if aggregate derivations become implementation scope.
