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


@dataclass(frozen=True)
class RoleSignature:
    """Required role names for a relation concept."""

    relation: RelationConceptRef
    roles: tuple[str, ...]

    def __post_init__(self) -> None:
        roles = tuple(role.strip() for role in self.roles)
        if not roles:
            raise ValueError("role signature must define at least one role")
        if any(role == "" for role in roles):
            raise ValueError("role name must be non-empty")
        duplicated = _duplicated(roles)
        if duplicated:
            raise ValueError(f"duplicate role in signature: {duplicated}")
        object.__setattr__(self, "roles", roles)

    def validate_bindings(self, bindings: RoleBindingSet) -> None:
        expected = frozenset(self.roles)
        observed = bindings.roles()
        missing = expected.difference(observed)
        if missing:
            raise ValueError(f"missing role binding: {sorted(missing)[0]}")
        unknown = observed.difference(expected)
        if unknown:
            raise ValueError(f"unknown role binding: {sorted(unknown)[0]}")

    def identity_payload(self) -> tuple[tuple[str, str], tuple[str, ...]]:
        return (self.relation.identity_key(), self.roles)


def _duplicated(values: tuple[str, ...] | list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
