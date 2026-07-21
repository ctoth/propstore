"""Pustejovsky qualia structures for sense-level semantic content.

A :class:`QualiaStructure` records the four Pustejovsky (1995) qualia roles —
FORMAL, CONSTITUTIVE, TELIC, AGENTIVE — as bundles of provenance-bearing
:class:`QualiaReference` links. Each reference REQUIRES provenance (CLAUDE.md
honest-ignorance discipline): a qualia link asserts a semantic relation and must
say where that assertion came from. Provenance is required at construction but
never enters identity (see :mod:`propstore.provenance`).

Two derived operations matter downstream:

* :func:`coerce_via_qualia` produces an explicit, provenance-tracked *view* of a
  reference under a target type by following a qualia role (default TELIC) — the
  qualia-mediated type coercion Pustejovsky uses for logical metonymy.
* :func:`purposive_chain` follows TELIC links transitively to recover a
  purposive chain (what a thing is *for*, and what that is for, …).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

import msgspec

from propstore.core.lemon.references import OntologyReference
from propstore.provenance import Provenance, compose_provenance


class QualiaRole(StrEnum):
    """The four Pustejovsky qualia roles."""

    FORMAL = "formal"
    CONSTITUTIVE = "constitutive"
    TELIC = "telic"
    AGENTIVE = "agentive"


class TypeConstraint(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A target type a reference may be required to satisfy."""

    reference: OntologyReference


class QualiaReference(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A single qualia link: a reference, its provenance, an optional type.

    ``provenance`` has no default — a qualia link without provenance cannot be
    constructed (the honest-ignorance law; see ``tests/test_lemon_semantics.py``).
    """

    reference: OntologyReference
    provenance: Provenance
    type_constraint: TypeConstraint | None = None


class QualiaStructure(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The four-role Pustejovsky qualia bundle for a sense."""

    formal: tuple[QualiaReference, ...] = ()
    constitutive: tuple[QualiaReference, ...] = ()
    telic: tuple[QualiaReference, ...] = ()
    agentive: tuple[QualiaReference, ...] = ()


class CoercedReference(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """An explicit, provenance-tracked view of a reference under a target type."""

    reference: OntologyReference
    target_type: TypeConstraint
    role_path: tuple[QualiaRole, ...]
    provenance: Provenance


def qualia_references(
    qualia: QualiaStructure, role: QualiaRole
) -> tuple[QualiaReference, ...]:
    """Return the qualia references stored under ``role``."""

    return getattr(qualia, role.value)


def coerce_via_qualia(
    qualia: QualiaStructure,
    target_type: TypeConstraint,
    *,
    preferred_role: QualiaRole = QualiaRole.TELIC,
) -> CoercedReference | None:
    """Return an explicit qualia-mediated view satisfying ``target_type``, or ``None``.

    Searches ``preferred_role`` for a reference whose own ``type_constraint``
    matches ``target_type``; if found, returns a :class:`CoercedReference` whose
    provenance records the coercion step (``qualia_coercion:<role>``).
    """

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
    """Follow TELIC links to recover a Pustejovsky purposive chain from ``start``.

    Stops at ``max_depth``, on a reference with no TELIC link, or on a cycle.
    """

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
