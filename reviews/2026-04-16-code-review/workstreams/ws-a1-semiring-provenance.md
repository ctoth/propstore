# Workstream A1 - Semiring Provenance Substrate

Date: 2026-04-17
Status: complete - WS-A1 exit criteria met; WS-C C-3 support contract unblocked
Depends on: `disciplines.md`, `judgment-rubric.md`, WS-A source/artifact boundaries
Blocks: WS-C C-3 support contract, ATMS label collapse, support-bearing fragility rewrite
Review context: `../axis-3d-semantic.md` section 6, `../axis-3e-reasoning-infra.md`, `../axis-4-test-adequacy.md`
Design review: drafted with Claude CLI; adversarial pass incorporated before implementation.

## Progress

- 2026-04-17: Added implementation-grade execution map with exact API, file-level phase plan, importer audit, test map, grep/type gates, and minimal WS-C C-3 unblock gate.
- 2026-04-17: Converted `propstore.provenance` from a single module into a package while preserving the existing named-graph/stamping public API.
- 2026-04-17: Implemented A1-1/A1-2 substrate files: `variables.py`, `polynomial.py`, `homomorphism.py`, `support.py`, `projections.py`, `nogoods.py`, and `derivative.py`.
- 2026-04-17: Added property tests for polynomial laws, projection homomorphisms before live filtering, nogood live filtering, non-commutation canary, and derivative laws. Verification passed: `23 passed`, `logs\test-runs\provenance-core-20260417-144423.log`.
- 2026-04-17: Verified legacy provenance imports and named-graph/stamping behavior after the package move. Verification passed: `29 passed`, `logs\test-runs\provenance-legacy-20260417-144509.log`.
- 2026-04-17: Collapsed `core.labels.Label` onto `SupportEvidence`/`ProvenancePolynomial`; `EnvironmentKey`, `combine_labels`, and `merge_labels` now operate as ATMS/why-provenance projections instead of storing independent support truth.
- 2026-04-17: Collapsed `NogoodSet` onto `ProvenanceNogood` and `live(...)`; empty-environment nogoods are represented as empty provenance nogoods and kill every monomial.
- 2026-04-17: Added ATMS equivalence properties proving label-polynomial round trips, assumption/context separation, multiplication/addition projection, and `NogoodSet` live-filter projection. Verification passed: `77 passed`, `logs\test-runs\provenance-atms-20260417-145336.log`.
- 2026-04-17: Re-ran core provenance property gate after the collapse and empty-nogood correction. Verification passed: `24 passed`, `logs\test-runs\provenance-core-20260417-145538.log`; Pyright was clean for `propstore/provenance`, `propstore/core/labels.py`, and the new provenance tests.
- 2026-04-17: Ran A1 static gates. Remaining `combine_labels`/`merge_labels`/`NogoodSet` production hits route through polynomial-backed projection APIs. Float hits are confined to documented tropical-cost code, not confidence/probability; dict hits are named-graph IO, with projection `Mapping` inputs used for source-variable maps and cost maps.
- 2026-04-17: Routed ATMS assumption fragility through live provenance support derivatives: status-flip witnesses are support monomials, queryable relevance is partial derivative support, and intervention provenance now carries `SupportEvidence`. Discovery, conflict, grounding, and bridge families keep their existing semantics rather than returning fabricated derivative results.
- 2026-04-17: Added fragility tests for live derivative scoring and derivative-backed assumption intervention support. Verification passed: `37 passed`, `logs\test-runs\provenance-fragility-20260417-150228.log`; production Pyright was clean for fragility files.
- 2026-04-17: Added the executable WS-C C-3 support contract in `propstore.defeasibility`: `JustifiableException`, `LiftingRuleSupport`, `ExceptionDefeat`, live support checks, lifting support multiplication, and exception-defeat liveness via live why-provenance.
- 2026-04-17: Updated WS-C docs to point at the executable support contract and added property tests for unsupported exceptions, lifting support composition, solver nogood live filtering, Boolean/why liveness agreement, and support-quality preservation. Verification passed: `5 passed`, `logs\test-runs\defeasibility-support-20260417-150458.log`; Pyright was clean for `propstore/defeasibility.py` and its tests.
- 2026-04-17: Ran `uv sync --upgrade`; the environment resolved and audited cleanly with no lockfile changes.
- 2026-04-17: Stabilized the expensive ASPIC bridge rationality property gate by bounding generated examples for that rationality-postulate class, after the exact xdist-crashed tests passed in isolation and a serial run showed unbounded generation could exceed the suite timeout.
- 2026-04-17: Final full-suite gate passed. Verification passed: `2709 passed, 16 warnings`, `logs\test-runs\full-a1-final-20260417-152636.log`.

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

## Implementation-grade execution map

### Exact initial API

Create `propstore/provenance/variables.py`:

```python
class SourceRole(StrEnum):
    CLAIM = "claim"
    RULE = "rule"
    MEASUREMENT = "measurement"
    CALIBRATION = "calibration"
    LIFTING_RULE = "lifting_rule"
    SOLVER_WITNESS = "solver_witness"
    ASSUMPTION = "assumption"
    CONTEXT = "context"

SourceVariableId = NewType("SourceVariableId", str)

@dataclass(frozen=True)
class SourceVariable:
    id: SourceVariableId
    role: SourceRole
    artifact_id: str
    canonical_body_hash: str
    provenance: ProvenanceRecord

def derive_source_variable_id(
    role: SourceRole,
    artifact_id: str,
    canonical_body_hash: str,
) -> SourceVariableId: ...
```

Create `propstore/provenance/polynomial.py`:

```python
@dataclass(frozen=True, order=True)
class VariablePower:
    variable: SourceVariableId
    exponent: int

@dataclass(frozen=True)
class PolynomialTerm:
    coefficient: int
    powers: tuple[VariablePower, ...]

@dataclass(frozen=True)
class ProvenancePolynomial:
    terms: tuple[PolynomialTerm, ...] = ()

    @classmethod
    def zero(cls) -> ProvenancePolynomial: ...
    @classmethod
    def one(cls) -> ProvenancePolynomial: ...
    @classmethod
    def variable(cls, variable: SourceVariableId) -> ProvenancePolynomial: ...

    def __add__(self, other: ProvenancePolynomial) -> ProvenancePolynomial: ...
    def __mul__(self, other: ProvenancePolynomial) -> ProvenancePolynomial: ...
    def squarefree_supports(self) -> tuple[frozenset[SourceVariableId], ...]: ...
```

Create `propstore/provenance/homomorphism.py`:

```python
class Homomorphism(Protocol[K]):
    @property
    def zero(self) -> K: ...
    @property
    def one(self) -> K: ...
    def add(self, left: K, right: K) -> K: ...
    def mul(self, left: K, right: K) -> K: ...
    def variable(self, variable: SourceVariableId) -> K: ...

def evaluate(poly: ProvenancePolynomial, hom: Homomorphism[K]) -> K: ...
```

Create `propstore/provenance/nogoods.py`:

```python
@dataclass(frozen=True)
class NogoodWitness:
    source: str
    detail: str

@dataclass(frozen=True)
class ProvenanceNogood:
    variables: frozenset[SourceVariableId]
    witness: NogoodWitness
    provenance: ProvenanceRecord

def live(
    poly: ProvenancePolynomial,
    nogoods: Iterable[ProvenanceNogood],
) -> ProvenancePolynomial: ...
```

Create `propstore/provenance/support.py`:

```python
class SupportQuality(StrEnum):
    EXACT = "exact"
    SEMANTIC_COMPATIBLE = "semantic_compatible"
    CONTEXT_VISIBLE_ONLY = "context_visible_only"
    MIXED = "mixed"

@dataclass(frozen=True)
class SupportEvidence:
    polynomial: ProvenancePolynomial
    quality: SupportQuality
```

The new `SupportQuality` replaces `propstore.core.labels.SupportQuality` after the collapse gate. Until then, `core.labels.SupportQuality` may import/re-export this enum, but it must not define a competing enum.

Create `propstore/provenance/projections.py`:

```python
def boolean_presence(poly: ProvenancePolynomial, trusted: Container[SourceVariableId]) -> bool: ...
def derivation_count(poly: ProvenancePolynomial) -> int: ...
def why_provenance(poly: ProvenancePolynomial) -> tuple[WhySupport, ...]: ...
def tropical_cost(poly: ProvenancePolynomial, costs: Mapping[SourceVariableId, float]) -> float: ...
```

`WhySupport` must preserve the current assumption/context split:

```python
@dataclass(frozen=True)
class WhySupport:
    assumption_ids: tuple[AssumptionId, ...] = ()
    context_ids: tuple[ContextId, ...] = ()
    other_variables: tuple[SourceVariableId, ...] = ()
```

Create `propstore/provenance/derivative.py`:

```python
def partial_derivative(
    poly: ProvenancePolynomial,
    variable: SourceVariableId,
) -> ProvenancePolynomial: ...
```

### File-by-file phase plan

Phase A1-1 writes:

- `propstore/provenance/__init__.py`
- `propstore/provenance/variables.py`
- `propstore/provenance/polynomial.py`
- `propstore/provenance/homomorphism.py`
- `propstore/provenance/support.py`
- `tests/test_provenance_polynomial_properties.py`

Phase A1-2 writes:

- `propstore/provenance/nogoods.py`
- `propstore/provenance/projections.py`
- `tests/test_provenance_projection_properties.py`
- `tests/test_provenance_nogoods_properties.py`

Phase A1-3 edits:

- `propstore/core/labels.py`
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- `propstore/world/types.py`
- `propstore/worldline/result_types.py`
- `propstore/core/graph_types.py`
- `propstore/core/results.py`
- `tests/test_labels_properties.py`
- `tests/test_labelled_core.py`
- `tests/test_atms_engine.py`
- `tests/test_provenance_atms_equivalence.py`

Phase A1-4 edits:

- `propstore/provenance/derivative.py`
- `propstore/fragility_types.py`
- `propstore/fragility_contributors.py`
- `propstore/fragility_scoring.py`
- `propstore/fragility.py`
- `tests/test_provenance_derivative_properties.py`
- `tests/test_fragility.py`

Phase A1-5 edits:

- `docs/defeasibility-semantics-decision.md`
- `reviews/2026-04-16-code-review/workstreams/ws-c-defeasibility.md`
- WS-C implementation files when C-3 starts.

Do not add production database tables, sidecar indexes, compatibility shims, or backfill commands.

### Current label importer audit

Production consumers that must be redirected or proven projection-only during A1-3:

- `propstore/aspic_bridge/projection.py`
- `propstore/artifacts/codes.py`
- `propstore/cli/compiler_cmds.py`
- `propstore/core/activation.py`
- `propstore/core/environment.py`
- `propstore/core/graph_types.py`
- `propstore/core/results.py`
- `propstore/structured_projection.py`
- `propstore/support_revision/af_adapter.py`
- `propstore/support_revision/projection.py`
- `propstore/support_revision/snapshot_types.py`
- `propstore/support_revision/state.py`
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- `propstore/world/model.py`
- `propstore/world/resolution.py`
- `propstore/world/types.py`
- `propstore/worldline/argumentation.py`

Tests that must be ported or extended:

- `tests/test_labels_properties.py`
- `tests/test_labelled_core.py`
- `tests/test_atms_engine.py`
- `tests/test_aspic_bridge.py`
- `tests/test_core_graph_types.py`
- `tests/test_core_justifications.py`
- `tests/test_revision_entrenchment.py`
- `tests/test_revision_phase1.py`
- `tests/test_semantic_core_phase0.py`
- `tests/test_structured_projection.py`

Use this command as a gate after A1-3:

```powershell
rg -n "Label\\(|EnvironmentKey\\(|NogoodSet\\(|combine_labels\\(|merge_labels\\(|normalize_environments\\(" propstore tests
```

After collapse, hits are allowed only in `propstore/core/labels.py`, provenance projection tests, and compatibility-facing tests that assert the names are projection views. Any production hit that constructs independent label truth is a blocker.

### Test map

New tests:

- `tests/test_provenance_polynomial_properties.py`: algebra laws and canonicalization.
- `tests/test_provenance_projection_properties.py`: homomorphism laws before live filtering, Boolean/count/why/tropical projections.
- `tests/test_provenance_nogoods_properties.py`: live filtering, non-commutation canary for non-idempotent projections.
- `tests/test_provenance_atms_equivalence.py`: generated and fixture-backed equivalence between polynomial why-provenance and current labels.
- `tests/test_provenance_derivative_properties.py`: formal derivative laws and live-support derivative behavior.

Existing targeted tests to run after each affected phase:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label provenance-core tests/test_provenance_polynomial_properties.py
powershell -File scripts/run_logged_pytest.ps1 -Label provenance-projections tests/test_provenance_projection_properties.py tests/test_provenance_nogoods_properties.py
powershell -File scripts/run_logged_pytest.ps1 -Label provenance-atms tests/test_labels_properties.py tests/test_labelled_core.py tests/test_atms_engine.py tests/test_provenance_atms_equivalence.py
powershell -File scripts/run_logged_pytest.ps1 -Label provenance-fragility tests/test_provenance_derivative_properties.py tests/test_fragility.py
```

Run the full suite before any deletion commit and after the final A1 commit.

### Grep/type gates

No naked float confidence from provenance:

```powershell
rg -n "->\\s*float|:\\s*float" propstore/provenance
```

Allowed float hits must be limited to tropical cost and documented as cost, not confidence/probability.

No dict-shaped polynomial/support objects outside IO:

```powershell
rg -n "dict\\[|Mapping\\[|Any" propstore/provenance
```

Allowed hits must be in serialization/IO helpers only. Core polynomial, nogood, support, and homomorphism types must remain typed domain objects.

No parallel support truth after A1-3:

```powershell
rg -n "label=Label\\(|self\\.nogoods\\s*=\\s*NogoodSet|combine_labels\\(|merge_labels\\(" propstore
```

Every remaining hit must route through polynomial projection APIs.

### Minimal WS-C C-3 unblock gate

WS-C C-3 may start after A1-1 and A1-2 if these concrete APIs exist and are property-tested:

- `SupportEvidence`
- `SupportQuality`
- `ProvenancePolynomial`
- `SourceVariableId`
- `ProvenanceNogood`
- `live`
- Boolean projection
- why-provenance projection

WS-C C-3 must not wait for the full ATMS collapse if it only consumes support evidence. It also must not invent its own support representation while waiting for A1.

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
