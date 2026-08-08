"""Typed relation concepts and semantic link role bindings.

Relation identity is a CONCEPT reference, never a bare predicate string — the
same no-string-matching discipline the alignment layer follows (CLAUDE.md:
vocabulary reconciliation uses lemon entry/form/reference identity, not string
tokens). :class:`RelationConceptRef` is keyed by its concept id; lexical-sense
and description-kind ids are grounding metadata that never enter the identity.

Design basis:
    Buitelaar et al. 2011 and Cimiano et al. 2016 separate lexical entries and
    senses from ontology references. Relation identity therefore lives at the
    ontology/concept reference, while lexical senses and description kinds are
    metadata that can change without changing the relation concept.

"""

from __future__ import annotations

import msgspec

from propstore.core.id_types import ConceptId, to_concept_id


class RelationConceptRef(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    order=True,
):
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


class RoleBinding(msgspec.Struct, frozen=True, forbid_unknown_fields=True, order=True):
    """Bind one role name in a relation signature to one value reference."""

    role: str
    value: str

    def __post_init__(self) -> None:
        role = self.role.strip()
        if role == "":
            raise ValueError("role name must be non-empty")
        object.__setattr__(self, "role", role)

    def identity_payload(self) -> tuple[str, str]:
        return (self.role, str(self.value))


class RoleBindingSet(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
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


def _duplicated(values: tuple[str, ...] | list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
