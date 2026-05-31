# Relations unification design proposal

## Position

The unification is viable only as a typed relation-instance substrate, not as a
promise that every current claim payload is relation-shaped. The current code has
three representations of "predicate/relation applied to arguments":

- `RoleBinding.value: object` in `propstore/core/relations.py:91-106`, consumed by
  `SituatedAssertion` identity in `propstore/core/assertions/situated.py:39-52`.
- `GroundAtom(predicate, tuple[Scalar, ...])`, with `Scalar = str | int | float |
  bool`, in `C:/Users/Q/code/argumentation/src/argumentation/structured/aspic/aspic.py:22-39`,
  mirrored by `GroundLiteralKey` in `propstore/core/literal_keys.py:47-58`.
- `SlotBinding(slot, value: OntologyReference, value_type: OntologyReference,
  provenance)` in `propstore/core/lemon/description_kinds.py:29-33`.

They differ in filler type and validation vocabulary. The replacement should be a
single relation instance with tagged values. It must also keep the Clark split
already implemented by `SituatedAssertion`: `provenance_ref` is excluded from
identity (`propstore/core/assertions/situated.py:22-33`) and the hash is derived
only from relation, bindings, context, and condition (`propstore/core/assertions/situated.py:47-63`).

## 1. Unified Value Type

Add a core value module, for example `propstore/core/relation_values.py`, with
these closed dataclasses:

```python
RelationValue = (
    ConceptValue
    | FamilyRefValue
    | ScalarValue
    | CelValue
    | TimepointValue
    | ListValue
    | RelationInstanceValue
)

@dataclass(frozen=True, slots=True)
class ConceptValue:
    reference: OntologyReference

@dataclass(frozen=True, slots=True)
class FamilyRefValue:
    family: Literal["claim", "context", "condition", "assumption", "policy"]
    id: str

@dataclass(frozen=True, slots=True)
class ScalarValue:
    value: str | int | float | bool

@dataclass(frozen=True, slots=True)
class CelValue:
    expression: CelExpr

@dataclass(frozen=True, slots=True)
class TimepointValue:
    lexical: str

@dataclass(frozen=True, slots=True)
class ListValue:
    items: tuple[RelationValue, ...]
    ordered: bool

@dataclass(frozen=True, slots=True)
class RelationInstanceValue:
    instance: RelationInstance
```

`ConceptValue` is not a scalar string. It uses `OntologyReference`, whose current
payload is only `uri` plus optional `label` (`propstore/core/lemon/references.py:8-18`).
The canonical identity uses the URI only; label is render metadata.

`FamilyRefValue` is required because the grounding path has declared term types
such as `"Claim"` and `"Context"` in `propstore/grounding/facts.py:235-252`. Treating
those ids as bare `ScalarValue(str)` would collapse a claim id, context id, and
free-text string with the same spelling.

`ScalarValue` is exactly the ASPIC scalar vocabulary: `str | int | float | bool`
from the argumentation package (`aspic.py:22`) and `GroundLiteralKey.arguments`
(`propstore/core/literal_keys.py:55-57`). It is not the catch-all for concepts,
claim ids, context ids, CEL, or time.

`CelValue` wraps `CelExpr`, the existing branded CEL source string
(`propstore/cel_types.py:9-17`). CEL source remains source text at storage
identity. Type checking and normalization stay in the condition/CEL owner path.

`TimepointValue` is separate even though `KindType.TIMEPOINT` exists beside
`QUANTITY` (`propstore/core/conditions/registry.py:17-23`). `CLAUDE.md:35` says
TIMEPOINT maps to Z3 Real but is semantically distinct and not dimensional
quantity. A timepoint cannot be stored as `ScalarValue(float)` without losing
that distinction. The payload is an authored lexical value until a time owner
normalizes it for reasoning.

`ListValue` handles repeated fillers without bringing back duplicate role
bindings. `ordered=True` preserves lists like variable order. `ordered=False`
canonicalizes item payloads by their canonical JSON so set-valued roles do not
depend on input order. Nested structured fillers use `RelationInstanceValue`, not
JSON blobs. The recursion must reject cycles at construction time.

## 2. Relation Instance and Binding Type

Replace `RelationConceptRef + RoleBindingSet`, `GroundAtom`, and lemon
`SlotBinding` at the Propstore boundary with:

```python
@dataclass(frozen=True, slots=True)
class RelationInstance:
    relation: RelationConceptRef
    bindings: tuple[RelationBinding, ...]

@dataclass(frozen=True, slots=True)
class RelationBinding:
    role: str
    value: RelationValue
```

`RelationConceptRef` still identifies the relation by concept id. Today its
identity is `("relation_concept", concept_id)` (`propstore/core/relations.py:84-87`),
and that stays true. The later FK work should make `concept_id` a real concepts
family reference, as the decided proposal requires.

`RoleBindingSet` currently sorts by role and rejects duplicate roles
(`propstore/core/relations.py:115-131`). `RelationInstance` keeps that behavior:
one binding per role. Repetition belongs inside `ListValue`.

The lemon signature becomes the relation signature:

```python
SlotValueConstraint = (
    ConceptConstraint
    | FamilyRefConstraint
    | ScalarConstraint
    | KindConstraint
    | CelConstraint
    | TimepointConstraint
    | ListConstraint
    | RelationInstanceConstraint
)

@dataclass(frozen=True, slots=True)
class ParticipantSlot:
    name: str
    value_constraint: SlotValueConstraint
    proto_role_bundle: ProtoRoleBundle | None = None
```

This generalizes the current `ParticipantSlot.type_constraint:
OntologyReference` (`propstore/core/lemon/description_kinds.py:12-15`). The old
validator compares only `binding.value_type.uri` to `slot.type_constraint.uri`
(`propstore/core/lemon/description_kinds.py:45-61`). The new validator checks the
tagged value:

- `ConceptConstraint(type_ref)` accepts `ConceptValue` whose resolved concept is
  of that ontology/reference type. Early implementation can require exact
  `reference.uri` equality, matching the current URI check; richer subtype checks
  belong behind an explicit concept owner API.
- `FamilyRefConstraint("claim")` accepts only `FamilyRefValue("claim", id)`.
- `ScalarConstraint("string" | "int" | "float" | "bool")` accepts the matching
  `ScalarValue` payload. `bool` must be checked before `int`.
- `KindConstraint(KindType.QUANTITY)` accepts numeric `ScalarValue` values;
  `KindType.BOOLEAN` accepts boolean scalar values; `KindType.CATEGORY` accepts
  string scalar values plus an optional category vocabulary check from
  `ConceptInfo.category_values` (`propstore/core/conditions/registry.py:25-34`);
  `KindType.STRUCTURAL` accepts `RelationInstanceValue`; `KindType.TIMEPOINT`
  accepts `TimepointValue`.
- `CelConstraint` accepts `CelValue`.
- `ListConstraint(element_constraint, ordered)` accepts `ListValue` and validates
  every item against `element_constraint`.
- `RelationInstanceConstraint(relation_ref)` accepts `RelationInstanceValue` with
  that relation id and recursively validates its bindings.

`SlotBinding.provenance` should be deleted from the binding type. It is set in
the lemon type (`propstore/core/lemon/description_kinds.py:29-33`) but the reports
found no reader. Instance or assertion provenance remains on the enclosing claim,
description claim, import metadata, or `SituatedAssertion.provenance_ref`.

## 3. Convergence at the Current Construction Sites

### Situated Assertions

`SituatedAssertion` should hold `RelationInstance`:

```python
class SituatedAssertion:
    relation_instance: RelationInstance
    context: ContextReference
    condition: ConditionRef
    provenance_ref: ProvenanceGraphRef = field(compare=False)
```

This replaces separate `relation` and `role_bindings` fields currently declared
at `propstore/core/assertions/situated.py:29-33`. `AssertionCanonicalRecord` must
serialize tagged values instead of stringifying each binding as it does now
(`propstore/core/assertions/codec.py:75-82`). The current codec loses types by
writing `{"role": binding.role, "value": str(binding.value)}`; that cannot
survive this unification.

### `merge/merge_claims.py`

The synthetic relation string at `propstore/merge/merge_claims.py:83` dies. The
`subject`/`content` pair at `propstore/merge/merge_claims.py:84-88` becomes a
call to a claim relation projector:

```python
instance = relation_instance_from_claim_document(self.document)
```

The projector resolves the relation concept by claim semantics, not by
`f"ps:relation:claim:{claim_type}"`. The subject becomes
`ConceptValue(OntologyReference(self.value_concept_id))` only when a real concept
id exists. The existing `ps:concept:unscoped` fallback at
`propstore/merge/merge_claims.py:86` fabricates scope as a concept-shaped value;
the replacement is either no `subject` binding for relation signatures where
subject is optional, or a diagnostic-bearing `FamilyRefValue` to the source claim
where the subject is unknown. It must not mint an unscoped concept filler.

The `content` JSON string at `merge_claims.py:87` is not kept as a relation
filler. `_semantic_payload` keeps heterogeneous claim content
(`propstore/merge/merge_claims.py:134-146`), and the claim document fields include
free text, CEL, expressions, nested fit/parameter/variable documents, and numeric
values (`propstore/families/claims/declaration.py:407-434`). Relation-shaped
claim types project to typed roles. Equation/model/algorithm parameterization
content routes to the parameterization owner path; it is not forced into
relation fillers.

### `support_revision/projection.py`

`_relation_ref` currently creates the same synthetic string
(`propstore/support_revision/projection.py:156-158`), and `_role_bindings` creates
`subject` plus opaque JSON `content` (`propstore/support_revision/projection.py:161-189`).
Replace both with the same owner projector used by merge:

```python
projection = project_claim_to_semantic_atom(claim)
```

For relation-shaped claims, `projection.assertion` contains a `RelationInstance`.
For non-relation claims, the result is a typed parameterization/support atom or a
diagnostic. `project_belief_base` already deduplicates by `assertion.assertion_id`
and merges source claims at `propstore/support_revision/projection.py:81-108`; that
many-to-one behavior stays.

The support-revision payload producer `Claim.to_source_claim_payload()` confirms
the current blob is heterogeneous: it emits ids/type/context/provenance at
`propstore/families/claims/declaration.py:798-811`, numeric fields at
`declaration.py:822-831`, text/CEL/expression fields at `declaration.py:832-845`,
and algorithm body/variables at `declaration.py:846-854`. The new projector must
be per claim family, not a generic dict flattener.

### `importing/machinery.py`

`SurfaceRoleBinding` is only `(role: str, value: str)` today
(`propstore/importing/machinery.py:34-43`). `ImportAuthoredFormLens.get` wraps
each value in `RoleBinding(binding.role, binding.value)` at
`propstore/importing/machinery.py:387-393`. That surface must become typed:

```python
class SurfaceRelationBinding:
    role: str
    value: RelationValuePayload
```

`RelationValuePayload` is the JSON form of the tagged union. The import lens
decodes it to `RelationValue`. A bare string import value is rejected with a
diagnostic at the import boundary because the current surface cannot distinguish
a concept URI from free text or a scalar.

Import provenance remains assertion-wide. `ImportCompiler.compile` sets a
single `provenance_ref` from import metadata at
`propstore/importing/machinery.py:448-458`; the binding value should not grow
per-binding provenance.

### `policies.py`

Policy assertions are already relation-shaped. `_policy_assertion` wraps
hard-coded relation ids and config scalars at `propstore/policies.py:416-432`.
The conversion is direct:

- `relation_id="ps:concept:policy-profile"` and the other ids at
  `propstore/policies.py:348-412` become `RelationConceptRef` concept FKs.
- `profile.profile_id`, `content_hash`, operators, strategy names, and enum
  values become `ScalarValue(str)`.
- Booleans and numbers in future profile fields become `ScalarValue(bool/int/float)`.

No policy value is a `ConceptValue` unless the policy schema says it references a
concept. The current code treats every value as `object`, so the new code has to
make that distinction at construction.

### Grounding Builders

Do not replace the external `argumentation.aspic.GroundAtom` API. It is owned by
the `argumentation` package and admits only `Scalar` terms (`aspic.py:22-39`).
Propstore should add adapters:

```python
def relation_instance_to_ground_atom(instance: RelationInstance) -> GroundAtom
def ground_atom_to_relation_instance(atom: GroundAtom, registry: PredicateRegistry) -> RelationInstance
```

The adapter succeeds only when every filler is representable as a ground scalar
or declared family id. `ConceptValue`, `FamilyRefValue`, and `ScalarValue` encode
to scalar terms with type supplied by the predicate registry. `CelValue`,
`TimepointValue`, `ListValue`, and nested `RelationInstanceValue` do not silently
encode to strings.

The grounding fact extractor currently adds `GroundAtom(predicate=predicate_id,
arguments=arguments)` at `propstore/grounding/facts.py:327-342`. It validates a
parallel observed type vector (`"Claim"`, `"Concept"`, `"Context"`, `"Scalar"`)
against `PredicateRegistry.validate_atom` (`propstore/grounding/predicates.py:166-177`,
`propstore/grounding/predicates.py:410-460`). That registry should become the
grounding view of the same `SlotValueConstraint` vocabulary. `_scalar_value`
currently stringifies non-scalar values (`propstore/grounding/facts.py:321-324`);
that fallback must be deleted because it fabricates a scalar representation.

## 4. Identity Canonicalization

The new assertion identity payload is:

```python
(
    instance.relation.identity_key(),
    tuple((binding.role, canonical_value(binding.value))
          for binding in sorted(instance.bindings, key=lambda b: b.role)),
    context.identity_payload(),
    condition.identity_payload(),
)
```

`canonical_value` is tagged:

```python
ConceptValue(ref)          -> ("concept", ref.uri)
FamilyRefValue(family, id) -> ("ref", family, id)
ScalarValue(str_value)     -> ("scalar", "str", str_value)
ScalarValue(bool_value)    -> ("scalar", "bool", bool_value)
ScalarValue(int_value)     -> ("scalar", "int", decimal_text)
ScalarValue(float_value)   -> ("scalar", "float", rfc8785_number_text)
CelValue(expr)             -> ("cel", str(expr))
TimepointValue(lexical)    -> ("timepoint", lexical)
ListValue(items, True)     -> ("list", "ordered", tuple(canonical_value(i) for i in items))
ListValue(items, False)    -> ("list", "set", tuple(sorted(canonical_value(i) for i in items)))
RelationInstanceValue(i)   -> ("relation_instance", canonical_instance(i))
```

Float canonicalization rejects NaN and Infinity. `bool` is checked before `int`.
This prevents collisions that the current `RoleBinding.identity_payload()` allows
by using `str(self.value)` (`propstore/core/relations.py:105-106`): `"1"` versus
`1`, `"True"` versus `True`, and a concept id string versus a free-text string no
longer collide.

The merge behavior is preserved at the semantic level: two different claims with
the same relation instance, context, and condition produce the same assertion id.
Claim id and provenance remain outside the hash. The current code already does
this deliberately: `provenance_ref` is excluded from `SituatedAssertion.identity_payload`
(`propstore/core/assertions/situated.py:33-52`), and support revision merges
colliding claims into one atom with multiple `source_claims`
(`propstore/support_revision/projection.py:102-108`).

This is still a data migration. `AssertionCanonicalRecord.__post_init__`
recomputes the id and raises on mismatch (`propstore/core/assertions/codec.py:34-39`),
and the current payload serializes `assertion_id` (`propstore/core/assertions/codec.py:75-91`).
The migration must rewrite persisted canonical assertion records and merge-commit
materializations that store assertion ids. There should be one post-migration
identity scheme, not old/new readers in production.

## 5. Honesty and Non-Commitment Checkpoints

- Do not create `ps:concept:unscoped` as a fake subject. Current code does that
  in `merge_claims.py:86` and `support_revision/projection.py:176`. Unknown
  subject is absence plus diagnostic, or a reference to the source claim, not a
  fabricated concept.
- Do not convert bare import strings by guessing. `SurfaceRoleBinding.value` is
  only `str` (`propstore/importing/machinery.py:34-43`), so the importer needs a
  typed value payload. Guessing concept-vs-text-vs-number from shape violates
  non-commitment.
- Do not store equation, parameter, variable, and fit structures as relation
  JSON blobs. The claim fields at `declaration.py:407-434` include structures
  that belong to parameterization or typed subdocuments. A JSON fallback would
  preserve bytes while losing semantic ownership.
- Do not pre-merge storage distinctions. The decided context says
  measurement/observation/parameter must not be collapsed in storage absent an
  explicit migration request. They can share validators and render policy, but
  their authored relation concepts remain distinct.
- Do not normalize timepoints to quantities in storage. `KindType.TIMEPOINT` and
  `KindType.QUANTITY` are distinct in `registry.py:17-23`, and the project
  principles state that TIMEPOINT is not dimensional quantity.
- Do not let grounding stringify unsupported values. The current `_scalar_value`
  fallback (`propstore/grounding/facts.py:321-324`) should become an error at the
  grounding boundary.

## 6. Risks and Objections

The strongest objection: this unification is bigger than a type cleanup. It
changes persisted assertion identity. The codec currently rejects mismatched
derived ids (`propstore/core/assertions/codec.py:34-39`), so stored snapshots and
merge artifacts require a real migration. A compatibility reader would violate
the deletion-first rule after migration.

Second objection: not every `ClaimType` is relation-shaped. `ClaimType.EQUATION`
has `expression` plus variable bindings and dimensional checks in the claim type
contract (`propstore/families/claims/declaration.py:225-231`). Treating that as a
relation instance would either create a fake `content` role or duplicate the
parameterization subsystem. The design must allow the claim projector to return a
non-relation semantic atom for those claims.

Third objection: the grounding backend cannot carry the full value union.
`GroundAtom` is scalar-only by definition (`aspic.py:22-39`). The honest design is
an adapter with a strict representability check. A direct replacement of
`GroundAtom.arguments` with `RelationValue` is infeasible without changing the
external `argumentation` package and Gunray-facing code paths.

Fourth objection: `KindType.CATEGORY` is not the same thing as free text. The
claim schema has prose fields such as `statement`, `body`, `notes`, `methodology`,
and `listener_population` (`propstore/families/claims/declaration.py:409-431`).
Encoding all strings as categories would fabricate ontology-level category
semantics. Free text remains `ScalarValue(str)` under a scalar/string constraint,
or it belongs to a text/document owner outside relation semantics.

Fifth objection: recursive relation values are powerful enough to become a new
JSON blob. The guardrail is that every nested structure must name a relation
concept and pass a `DescriptionKind` signature. There is no untyped map/list
variant.

My adversarial conclusion: the substrate unification is sound, but only with
strict typed payloads, no scalar fallback, no fake unscoped concept, and an
explicit identity migration. The infeasible part is "make every current claim
content blob a relation filler." The feasible part is "replace the three
relation/predicate argument carriers with one typed relation-instance model and
use adapters at owner boundaries."
