from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from propstore.artifacts.schema import DocumentStruct
from propstore.core.lemon.references import OntologyReference
from propstore.provenance import Provenance, compose_provenance


class QualiaRole(StrEnum):
    FORMAL = "formal"
    CONSTITUTIVE = "constitutive"
    TELIC = "telic"
    AGENTIVE = "agentive"


class TypeConstraint(DocumentStruct):
    reference: OntologyReference


class QualiaReference(DocumentStruct):
    reference: OntologyReference
    provenance: Provenance
    type_constraint: TypeConstraint | None = None


class QualiaStructure(DocumentStruct):
    formal: tuple[QualiaReference, ...] = ()
    constitutive: tuple[QualiaReference, ...] = ()
    telic: tuple[QualiaReference, ...] = ()
    agentive: tuple[QualiaReference, ...] = ()


@dataclass(frozen=True, slots=True)
class CoercedReference:
    reference: OntologyReference
    target_type: TypeConstraint
    role_path: tuple[QualiaRole, ...]
    provenance: Provenance


def qualia_references(qualia: QualiaStructure, role: QualiaRole) -> tuple[QualiaReference, ...]:
    return getattr(qualia, role.value)


def coerce_via_qualia(
    qualia: QualiaStructure,
    target_type: TypeConstraint,
    *,
    preferred_role: QualiaRole = QualiaRole.TELIC,
) -> CoercedReference | None:
    """Return an explicit qualia-mediated view satisfying ``target_type``."""

    for candidate in qualia_references(qualia, preferred_role):
        if candidate.type_constraint is None:
            continue
        if candidate.type_constraint.reference.uri != target_type.reference.uri:
            continue
        return CoercedReference(
            reference=candidate.reference,
            target_type=target_type,
            role_path=(preferred_role,),
            provenance=compose_provenance(
                candidate.provenance,
                operation=f"qualia_coercion:{preferred_role.value}",
            ),
        )
    return None


def purposive_chain(
    start: OntologyReference,
    qualia_by_reference: Mapping[str, QualiaStructure],
    *,
    max_depth: int = 8,
) -> tuple[OntologyReference, ...]:
    """Follow TELIC links to recover Pustejovsky-style purposive chains."""

    if max_depth < 1:
        return ()
    chain: list[OntologyReference] = []
    seen = {start.uri}
    current = start
    for _ in range(max_depth):
        qualia = qualia_by_reference.get(current.uri)
        if qualia is None or not qualia.telic:
            break
        next_ref = qualia.telic[0].reference
        if next_ref.uri in seen:
            break
        seen.add(next_ref.uri)
        chain.append(next_ref)
        current = next_ref
    return tuple(chain)
