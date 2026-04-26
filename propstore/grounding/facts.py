"""Fact extractor for the propstore -> Datalog grounding pipeline.

The fact extractor walks loaded propstore source data and materialises
the Datalog fact base consumed by later grounding stages. It is the
sole bridge between propstore concept relationships, claim structure,
claim context/provenance, and the ground-atom set that the gunray
translator and the sidecar populate stage will read.

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is a
      finite set of ground atoms ``p(c_1,...,c_n)`` whose terms are
      constants drawn from the domain. The extractor produces exactly
      this set from the propstore concept graph.
    - Section 3 (Definition 9): ground substitutions are a function of
      the program and its fact base. The extractor must therefore be a
      pure, total, deterministic function of its inputs so the
      substitution set downstream is stable across runs.
    - Section 4: every emitted ground atom must reference a declared
      predicate and respect its declared arity. The extractor cannot
      invent predicate symbols and cannot emit atoms whose arity
      disagrees with the registry. Section 4 fixes the typed
      ``derived_from`` boundary that propstore extends across concept
      relations and claim structure in WS7.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): the unary ``bird/1`` predicate is the
      canonical defeasible-reasoning toy example; the ground literal
      ``bird(tweety)`` is produced from a fact-base entry asserting
      that the constant ``tweety`` participates in the ``Bird``
      classification. The extractor reproduces exactly this
      derivation: a concept whose ``canonical_name`` is ``tweety`` with
      an outgoing ``is_a`` edge to ``Bird`` produces ``bird(tweety)``.
    - Section 3.1: the ground instances of a program are obtained by
      replacing each variable in a rule head/body with a constant
      drawn from the Herbrand base. Here the Herbrand base for a
      ``concept.relation:<rel>:<target>`` derivation is the set of
      concept canonical names that have a matching outgoing edge.
    - Section 3.2: predicate signatures are a flat function from
      predicate id to arity; rule heads and bodies have term-tuple
      lengths matching the declared arity for grounding to be
      well-defined. WS7 emits concept, claim, context, and scalar terms
      only through registered predicate signatures.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from argumentation.aspic import GroundAtom
from propstore.claims import ClaimFileEntry, claim_file_claims
from propstore.families.claims.documents import ClaimDocument
from propstore.families.concepts.stages import LoadedConcept
from propstore.grounding.predicates import (
    PredicateAtom,
    PredicateRegistry,
    parse_derived_from,
)


@dataclass(frozen=True)
class GroundingFactInputs:
    """Typed source bundle for propstore-to-Datalog fact extraction."""

    concepts: tuple[LoadedConcept, ...] = ()
    claim_files: tuple[ClaimFileEntry, ...] = ()


def extract_facts(
    inputs: GroundingFactInputs,
    registry: PredicateRegistry,
) -> tuple[GroundAtom, ...]:
    """Materialise the Datalog fact base from loaded propstore sources.

    Predicates with ``derived_from`` declarations are materialised from
    the matching source subsystem: concept relations, claim attributes,
    claim conditions, claim roles, claim context, or claim provenance.
    Predicates with ``derived_from is None`` contribute nothing because
    they have no bridge from propstore data.

    The result is a deterministic, duplicate-free tuple. Diller et al.
    2025 §3 (Definition 7) treats the fact base as a *set*, so the
    extractor deduplicates internally before sorting; Garcia & Simari
    2004 §3.1 makes the same point about ground instances. Sorting on
    the natural ``(predicate, arguments)`` key gives a stable order
    independent of dict iteration order or graph-walk order, which
    Diller et al. 2025 §3 Definition 9 requires for the substitution
    set to be a deterministic function of the program and the fact
    base.

    Note: ``ConceptRelationship.relationship_type`` is the parsed
    dataclass field name (the underlying YAML uses ``type``, but
    ``parse_concept_record`` renames it). The extractor reads
    ``rel.relationship_type`` and compares against ``spec.relation``.

    Args:
        inputs: Typed source bundle with concept and claim-family data
            already loaded by the repository pipeline.
        registry: ``PredicateRegistry`` providing predicate
            declarations and their ``derived_from`` DSL strings.

    Returns:
        A deterministic tuple of ``GroundAtom``, sorted on
        ``(predicate, arguments)``, with no duplicates.
    """

    # Collect into a set to enforce the Diller 2025 §3 Definition 7
    # requirement that the fact base is a set, not a multiset. The
    # same (concept, predicate) pair never produces more than one
    # atom, regardless of how the loops below are nested.
    collected: set[GroundAtom] = set()

    for predicate in registry.all_predicates():
        derived_from = predicate.derived_from
        if derived_from is None:
            # No bridge from propstore data: this predicate contributes
            # nothing to the fact base. Diller 2025 §3-§4: derived_from
            # is the only sanctioned source.
            continue

        spec = parse_derived_from(derived_from)
        if spec.kind == "concept_relation":
            _collect_concept_relation_facts(
                collected,
                concepts=inputs.concepts,
                registry=registry,
                predicate_id=predicate.id,
                relation=spec.relation,
                target=spec.target,
            )
            continue

        _collect_claim_facts(
            collected,
            claims=_iter_claims(inputs.claim_files),
            registry=registry,
            predicate_id=predicate.id,
            kind=spec.kind,
            attribute=spec.attribute,
            condition=spec.condition,
            role=spec.role,
            provenance_field=spec.provenance_field,
        )

    # Sort on (predicate, arguments) for a deterministic order
    # independent of dict / set iteration order. Diller et al. 2025
    # §3 Definition 9 requires the ground substitution set to be a
    # deterministic function of its inputs; downstream consumers
    # (the gunray translator, the sidecar populate stage) rely on
    # this stability for reproducible builds.
    return tuple(
        sorted(collected, key=lambda atom: (atom.predicate, atom.arguments))
    )


def _collect_concept_relation_facts(
    collected: set[GroundAtom],
    *,
    concepts: Sequence[LoadedConcept],
    registry: PredicateRegistry,
    predicate_id: str,
    relation: str | None,
    target: str | None,
) -> None:
    registry.validate_atom(
        PredicateAtom(
            predicate_id=predicate_id,
            arguments=("__concept__",),
            argument_types=("Concept",),
        )
    )
    if relation is None or target is None:
        return

    for concept in concepts:
        record = concept.record
        for relationship in record.relationships:
            if relationship.relationship_type != relation:
                continue
            if str(relationship.target) != target:
                continue
            collected.add(
                GroundAtom(
                    predicate=predicate_id,
                    arguments=(record.canonical_name,),
                )
            )


def _collect_claim_facts(
    collected: set[GroundAtom],
    *,
    claims: Sequence[ClaimDocument],
    registry: PredicateRegistry,
    predicate_id: str,
    kind: str,
    attribute: str | None,
    condition: str | None,
    role: str | None,
    provenance_field: str | None,
) -> None:
    for claim in claims:
        claim_id = _claim_fact_id(claim)
        if claim_id is None:
            continue
        if kind == "claim_attribute" and attribute is not None:
            value = getattr(claim, attribute, None)
            if value is not None:
                _add_claim_scalar_fact(
                    collected,
                    registry=registry,
                    predicate_id=predicate_id,
                    claim_id=claim_id,
                    value=value,
                )
            continue
        if kind == "claim_condition" and condition is not None:
            for authored_condition in claim.conditions:
                condition_text = str(authored_condition)
                if condition_text == condition:
                    _add_claim_scalar_fact(
                        collected,
                        registry=registry,
                        predicate_id=predicate_id,
                        claim_id=claim_id,
                        value=condition_text,
                    )
            continue
        if kind == "claim_role" and role is not None:
            for concept_id in _claim_role_bindings(claim, role):
                _add_fact(
                    collected,
                    registry=registry,
                    predicate_id=predicate_id,
                    arguments=(claim_id, concept_id),
                    argument_types=("Claim", "Concept"),
                )
            continue
        if kind == "claim_context":
            context_id = getattr(claim.context, "id", None)
            if context_id is not None:
                _add_fact(
                    collected,
                    registry=registry,
                    predicate_id=predicate_id,
                    arguments=(claim_id, str(context_id)),
                    argument_types=("Claim", "Context"),
                )
            continue
        if kind == "claim_provenance" and provenance_field is not None:
            provenance = claim.provenance
            value = None if provenance is None else getattr(provenance, provenance_field, None)
            if value is not None:
                _add_claim_scalar_fact(
                    collected,
                    registry=registry,
                    predicate_id=predicate_id,
                    claim_id=claim_id,
                    value=value,
                )


def _iter_claims(claim_files: Sequence[ClaimFileEntry]) -> tuple[ClaimDocument, ...]:
    claims: list[ClaimDocument] = []
    for claim_file in claim_files:
        claims.extend(claim_file_claims(claim_file))
    return tuple(claims)


def _claim_fact_id(claim: ClaimDocument) -> str | None:
    return claim.id or claim.artifact_id or claim.primary_logical_id


def _claim_role_bindings(claim: ClaimDocument, role: str) -> tuple[str, ...]:
    if role == "about":
        return tuple(str(concept_id) for concept_id in claim.concepts)
    if role == "output":
        return _optional_singleton(claim.output_concept)
    if role == "target":
        return _optional_singleton(claim.target_concept)
    return ()


def _optional_singleton(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return (str(value),)


def _add_claim_scalar_fact(
    collected: set[GroundAtom],
    *,
    registry: PredicateRegistry,
    predicate_id: str,
    claim_id: str,
    value: object,
) -> None:
    declaration = registry.lookup(predicate_id)
    if declaration.arity == 1:
        _add_fact(
            collected,
            registry=registry,
            predicate_id=predicate_id,
            arguments=(claim_id,),
            argument_types=("Claim",),
        )
        return
    _add_fact(
        collected,
        registry=registry,
        predicate_id=predicate_id,
        arguments=(claim_id, _scalar_value(value)),
        argument_types=("Claim", "Scalar"),
    )


def _scalar_value(value: object) -> str | int | float | bool:
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


def _add_fact(
    collected: set[GroundAtom],
    *,
    registry: PredicateRegistry,
    predicate_id: str,
    arguments: tuple[object, ...],
    argument_types: tuple[str, ...],
) -> None:
    registry.validate_atom(
        PredicateAtom(
            predicate_id=predicate_id,
            arguments=arguments,
            argument_types=argument_types,
        )
    )
    collected.add(GroundAtom(predicate=predicate_id, arguments=arguments))
