"""Small bootstrap vocabulary for relation concepts.

The kernel intentionally owns only the circular minimum: relation concepts,
role names, role bindings, and validation of complete binding sets. Higher
relation definitions can then be represented as ordinary propstore content.

Design basis:
    Buitelaar et al. 2011 and Cimiano et al. 2016 separate lexical entries and
    senses from ontology references. Relation identity therefore lives at the
    ontology/concept reference, while lexical senses and description kinds are
    metadata that can change without changing the relation concept.

    Fillmore 1982, Baker et al. 1998, and Dowty 1991 motivate role signatures
    as structured participant slots rather than loose linguistic labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from propstore.core.id_types import ConceptId, to_concept_id


BOOTSTRAP_RELATION_IDS: frozenset[str] = frozenset({
    "relation_concept",
    "role",
    "has_role",
    "role_domain",
    "role_range",
    "subtype_of",
    "instance_of",
    "contextualizes",
    "condition_applies",
    "supports",
    "undercuts",
    "rebuts",
    "base_rate_for",
    "calibrates",
    "published_in",
})


@dataclass(frozen=True, order=True)
class RelationConceptRef:
    """Reference to a relation represented as a propstore concept.

    The stable identity is the concept id. Lexical-sense and description-kind
    ids are retained as grounding metadata, following the OntoLex-Lemon split
    between ontology reference and lexicalization (Buitelaar 2011; Cimiano
    2016).
    """

    concept_id: ConceptId | str
    lexical_sense_id: str | None = None
    description_kind_id: str | None = None

    def __post_init__(self) -> None:
        concept_id = to_concept_id(self.concept_id)
        if str(concept_id) == "":
            raise ValueError("relation concept id must be non-empty")
        object.__setattr__(self, "concept_id", concept_id)
        if self.lexical_sense_id == "":
            raise ValueError("lexical sense id must be non-empty when provided")
        if self.description_kind_id == "":
            raise ValueError("description kind id must be non-empty when provided")

    def identity_key(self) -> tuple[str, str]:
        """Return the relation identity payload used by later assertions."""

        return ("relation_concept", str(self.concept_id))


@dataclass(frozen=True, order=True)
class RoleBinding:
    """Bind one role name in a relation signature to one value reference."""

    role: str
    value: object

    def __post_init__(self) -> None:
        role = self.role.strip()
        if role == "":
            raise ValueError("role name must be non-empty")
        object.__setattr__(self, "role", role)
        if self.value is None:
            raise ValueError("role value must be present")

    def identity_payload(self) -> tuple[str, str]:
        return (self.role, str(self.value))


@dataclass(frozen=True)
class RoleBindingSet:
    """Canonical, duplicate-free role bindings for one relation assertion."""

    bindings: tuple[RoleBinding, ...]

    def __post_init__(self) -> None:
        bindings = tuple(self.bindings)
        role_names = [binding.role for binding in bindings]
        duplicated = _duplicated(role_names)
        if duplicated:
            raise ValueError(f"duplicate role binding: {duplicated}")
        object.__setattr__(
            self,
            "bindings",
            tuple(sorted(bindings, key=lambda binding: binding.role)),
        )

    def roles(self) -> frozenset[str]:
        return frozenset(binding.role for binding in self.bindings)

    def identity_payload(self) -> tuple[tuple[str, str], ...]:
        return tuple(binding.identity_payload() for binding in self.bindings)


@dataclass(frozen=True, order=True)
class RoleDefinition:
    """Role slot with explicit domain and range concepts.

    FrameNet-style frame elements are useful only when their participant slot
    is tied to the kind of event/frame that owns the slot and to the kind of
    value that may fill it (Baker et al. 1998). The domain/range pair keeps
    that slot identity explicit in the kernel.
    """

    role: str
    domain: ConceptId | str
    range: ConceptId | str

    def __post_init__(self) -> None:
        role = self.role.strip()
        if role == "":
            raise ValueError("role name must be non-empty")
        domain = to_concept_id(self.domain)
        if str(domain) == "":
            raise ValueError("role domain must be non-empty")
        range_id = to_concept_id(self.range)
        if str(range_id) == "":
            raise ValueError("role range must be non-empty")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "range", range_id)

    def identity_payload(self) -> tuple[str, str, str]:
        return (self.role, str(self.domain), str(self.range))


@dataclass(frozen=True)
class RoleSignature:
    """Required domain/range-bearing role slots for a relation concept."""

    relation: RelationConceptRef
    role_definitions: tuple[RoleDefinition, ...]

    def __post_init__(self) -> None:
        role_definitions = tuple(
            sorted(self.role_definitions, key=lambda definition: definition.role)
        )
        if not role_definitions:
            raise ValueError("role signature must define at least one role")
        role_names = [definition.role for definition in role_definitions]
        duplicated = _duplicated(role_names)
        if duplicated:
            raise ValueError(f"duplicate role in signature: {duplicated}")
        object.__setattr__(self, "role_definitions", role_definitions)

    def role_names(self) -> frozenset[str]:
        return frozenset(definition.role for definition in self.role_definitions)

    def validate_bindings(self, bindings: RoleBindingSet) -> None:
        expected = self.role_names()
        observed = bindings.roles()
        missing = expected.difference(observed)
        if missing:
            raise ValueError(f"missing role binding: {sorted(missing)[0]}")
        unknown = observed.difference(expected)
        if unknown:
            raise ValueError(f"unknown role binding: {sorted(unknown)[0]}")

    def identity_payload(
        self,
    ) -> tuple[tuple[str, str], tuple[tuple[str, str, str], ...]]:
        return (
            self.relation.identity_key(),
            tuple(
                definition.identity_payload()
                for definition in self.role_definitions
            ),
        )


class RelationPropertyKind(StrEnum):
    """Implemented relation properties in the bootstrap kernel."""

    FUNCTIONAL = "functional"
    INVERSE_OF = "inverse_of"
    SYMMETRIC = "symmetric"
    TRANSITIVE = "transitive"


@dataclass(frozen=True, order=True)
class RelationPropertyAssertion:
    """A kernel-recognized property asserted about a relation concept."""

    relation: RelationConceptRef
    kind: RelationPropertyKind
    target: RelationConceptRef | None = None

    def __post_init__(self) -> None:
        kind = RelationPropertyKind(self.kind)
        object.__setattr__(self, "kind", kind)
        if kind == RelationPropertyKind.INVERSE_OF:
            if self.target is None:
                raise ValueError("inverse target relation is required")
        elif self.target is not None:
            raise ValueError(f"{kind.value} must not carry a target relation")

    def inverse(self) -> RelationPropertyAssertion:
        if self.kind != RelationPropertyKind.INVERSE_OF:
            return self
        if self.target is None:
            raise ValueError("inverse target relation is required")
        return RelationPropertyAssertion(
            relation=self.target,
            kind=RelationPropertyKind.INVERSE_OF,
            target=self.relation,
        )

    def identity_payload(self) -> tuple[tuple[str, str], str, tuple[str, str] | None]:
        target_payload = None if self.target is None else self.target.identity_key()
        return (self.relation.identity_key(), self.kind.value, target_payload)


@dataclass(frozen=True)
class RelationPropertySet:
    """Immutable property assertions with small kernel algorithms."""

    assertions: tuple[RelationPropertyAssertion, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assertions", tuple(self.assertions))

    def has(
        self,
        relation: RelationConceptRef,
        kind: RelationPropertyKind,
    ) -> bool:
        return any(
            assertion.relation.identity_key() == relation.identity_key()
            and assertion.kind == kind
            for assertion in self.assertions
        )

    def canonicalize_binary_values(
        self,
        relation: RelationConceptRef,
        left: object,
        right: object,
    ) -> tuple[str, str]:
        left_text = str(left)
        right_text = str(right)
        if self.has(relation, RelationPropertyKind.SYMMETRIC):
            ordered = sorted((left_text, right_text))
            return (ordered[0], ordered[1])
        return (left_text, right_text)

    def transitive_closure(
        self,
        relation: RelationConceptRef,
        edges: frozenset[tuple[str, str]],
    ) -> frozenset[tuple[str, str]]:
        if not self.has(relation, RelationPropertyKind.TRANSITIVE):
            return edges

        closure = set(edges)
        changed = True
        while changed:
            changed = False
            additions = {
                (left, right_next)
                for left, right in closure
                for left_next, right_next in closure
                if right == left_next and (left, right_next) not in closure
            }
            if additions:
                closure.update(additions)
                changed = True
        return frozenset(closure)


def _duplicated(values: tuple[str, ...] | list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
