"""Mine ground facts from the concept/claim substrate per ``derived_from`` specs.

:func:`extract_facts` walks every registered predicate that declares a
``derived_from`` spec and emits the ground :class:`gunray.GroundAtom` facts the
spec licenses, validating each against the predicate's declaration. The result is
deduplicated and deterministically sorted.

Substrate boundary: facts are ``gunray.GroundAtom`` — gunray's own ground-atom
type — not a propstore mirror. The concept side reads a thin
:class:`ConceptRelations` input rather than a ``relationships`` field on the
``Concept`` charter (relations are not concept identity).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import gunray

from propstore.families.claims import Claim
from propstore.grounding.predicates import (
    DerivedFromSpec,
    PredicateAtom,
    PredicateRegistry,
    parse_derived_from,
)


@dataclass(frozen=True)
class ConceptRelations:
    """A concept's outgoing relations, supplied for fact mining.

    The :class:`~propstore.families.concepts.Concept` charter carries no
    ``relationships`` field (relations are not concept identity), so the
    concept-relation derived-from path reads this thin typed input. Each
    relationship is ``(relationship_type, target)``.
    """

    concept_id: str
    canonical_name: str
    relationships: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class GroundingFactInputs:
    """The substrate facts are mined from: concept relations and claims."""

    concepts: tuple[ConceptRelations, ...] = ()
    claims: tuple[Claim, ...] = ()


def extract_facts(
    inputs: GroundingFactInputs, registry: PredicateRegistry
) -> tuple[gunray.GroundAtom, ...]:
    """Emit every ground fact licensed by the registered predicates' specs.

    A predicate with ``derived_from is None`` contributes nothing. Results are
    deduplicated and sorted by ``(predicate, stringified-arguments)``.
    """

    collected: set[gunray.GroundAtom] = set()
    for predicate in registry.all_predicates():
        if predicate.derived_from is None:
            continue
        spec = parse_derived_from(predicate.derived_from)
        if spec.kind == "concept_relation":
            _collect_concept_relation_facts(
                predicate.predicate_id, spec, inputs.concepts, registry, collected
            )
        else:
            _collect_claim_facts(predicate.predicate_id, spec, inputs.claims, registry, collected)
    return tuple(
        sorted(
            collected,
            key=lambda atom: (atom.predicate, tuple(str(arg) for arg in atom.arguments)),
        )
    )


def _collect_concept_relation_facts(
    predicate_id: str,
    spec: DerivedFromSpec,
    concepts: Iterable[ConceptRelations],
    registry: PredicateRegistry,
    collected: set[gunray.GroundAtom],
) -> None:
    declaration = registry.lookup(predicate_id)
    # A concept-relation predicate must be unary (one concept name argument);
    # validating a probe atom rejects a mis-declared arity before walking concepts.
    registry.validate_atom(
        PredicateAtom(
            predicate_id,
            arguments=("__concept__",),
            argument_types=tuple(declaration.arg_types),
        )
    )
    if spec.relation is None or spec.target is None:
        return
    for concept in concepts:
        for relationship_type, target in concept.relationships:
            if relationship_type != spec.relation:
                continue
            if str(target) != spec.target:
                continue
            collected.add(
                gunray.GroundAtom(predicate=predicate_id, arguments=(concept.canonical_name,))
            )


def _collect_claim_facts(
    predicate_id: str,
    spec: DerivedFromSpec,
    claims: Iterable[Claim],
    registry: PredicateRegistry,
    collected: set[gunray.GroundAtom],
) -> None:
    for claim in claims:
        claim_id = claim.claim_id
        if spec.kind == "claim_attribute" and spec.attribute is not None:
            value = getattr(claim, spec.attribute, None)
            if value is not None:
                _add_claim_scalar_fact(predicate_id, claim_id, value, registry, collected)
        elif spec.kind == "claim_condition" and spec.condition is not None:
            for authored_condition in claim.conditions:
                if authored_condition == spec.condition:
                    _add_claim_scalar_fact(
                        predicate_id, claim_id, authored_condition, registry, collected
                    )
        elif spec.kind == "claim_role" and spec.role is not None:
            for concept_id in _claim_role_bindings(claim, spec.role):
                _add_fact(
                    predicate_id, (claim_id, concept_id), ("Claim", "Concept"), registry, collected
                )
        elif spec.kind == "claim_context":
            if claim.context_id is not None:
                _add_fact(
                    predicate_id,
                    (claim_id, claim.context_id),
                    ("Claim", "Context"),
                    registry,
                    collected,
                )
        elif spec.kind == "claim_provenance" and spec.provenance_field is not None:
            value = getattr(claim, spec.provenance_field, None)
            if value is not None:
                _add_claim_scalar_fact(predicate_id, claim_id, value, registry, collected)


def _claim_role_bindings(claim: Claim, role: str) -> tuple[str, ...]:
    if role == "about":
        return tuple(str(concept) for concept in claim.concepts)
    if role == "output":
        return _optional_singleton(claim.output_concept)
    if role == "target":
        return _optional_singleton(claim.target_concept)
    return ()


def _optional_singleton(value: str | None) -> tuple[str, ...]:
    return () if value is None else (str(value),)


def _add_claim_scalar_fact(
    predicate_id: str,
    claim_id: str,
    value: object,
    registry: PredicateRegistry,
    collected: set[gunray.GroundAtom],
) -> None:
    declaration = registry.lookup(predicate_id)
    if declaration.arity == 1:
        _add_fact(predicate_id, (claim_id,), ("Claim",), registry, collected)
    else:
        _add_fact(
            predicate_id,
            (claim_id, _scalar_value(value)),
            ("Claim", "Scalar"),
            registry,
            collected,
        )


def _scalar_value(value: object) -> gunray.Scalar:
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


def _add_fact(
    predicate_id: str,
    arguments: tuple[gunray.Scalar, ...],
    argument_types: tuple[str, ...],
    registry: PredicateRegistry,
    collected: set[gunray.GroundAtom],
) -> None:
    registry.validate_atom(
        PredicateAtom(predicate_id, arguments=arguments, argument_types=argument_types)
    )
    collected.add(gunray.GroundAtom(predicate=predicate_id, arguments=arguments))
