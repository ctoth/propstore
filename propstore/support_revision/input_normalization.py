from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from condition_ir import to_cel_expr

from propstore.core.environment import AssumptionRef
from propstore.core.id_types import to_assumption_id
from propstore.support_revision.state import (
    AssertionAtom,
    AssumptionAtom,
    BeliefAtom,
    BeliefBase,
    is_assertion_atom,
    is_assumption_atom,
)


def normalize_revision_input(
    base: BeliefBase,
    revision_input: BeliefAtom | str,
) -> BeliefAtom:
    """Resolve a typed revision input against the belief base.

    A :class:`BeliefAtom` passes through unchanged; a string is resolved
    against the base's atom ids, assertion ids, and assumption ids.
    """
    if isinstance(revision_input, AssertionAtom | AssumptionAtom):
        return revision_input

    existing = _find_existing_atom(base, revision_input)
    if existing is not None:
        return existing
    raise ValueError(f"Unknown revision input: {revision_input}")


def parse_revision_atom_payload(payload: Mapping[str, Any]) -> BeliefAtom | str:
    """Parse user-authored revision-atom JSON (the CLI ``--atom`` flag).

    This is the one deserialization boundary for revision atoms: its producer
    is genuinely untyped user input. Assertion payloads resolve to the atom id
    string (the atom must already exist in the base); assumption payloads
    construct a typed :class:`AssumptionAtom`. The ``kind`` key is the payload
    discriminator; an assumption's own ref kind rides the dedicated
    ``assumption_kind`` key so the discriminator never leaks into
    ``AssumptionRef.kind``.
    """
    kind = str(payload.get("kind") or "")
    if kind == "assertion":
        assertion_id = (
            payload.get("assertion_id") or payload.get("id") or payload.get("atom_id")
        )
        if not assertion_id:
            raise ValueError("Assertion revision input requires 'assertion_id' or 'id'")
        return str(assertion_id)

    if kind == "assumption":
        assumption_id = payload.get("assumption_id") or payload.get("id")
        if not assumption_id:
            raise ValueError(
                "Assumption revision input requires 'assumption_id' or 'id'"
            )
        atom_id = str(payload.get("atom_id") or f"assumption:{assumption_id}")
        return AssumptionAtom(
            atom_id=atom_id,
            assumption=AssumptionRef(
                assumption_id=to_assumption_id(assumption_id),
                cel=to_cel_expr(str(payload.get("cel") or "")),
                kind=str(payload.get("assumption_kind") or ""),
                source=str(payload.get("source") or ""),
            ),
        )

    raise ValueError("Revision atom payload requires kind 'assertion' or 'assumption'")


def _find_existing_atom(base: BeliefBase, revision_input: str) -> BeliefAtom | None:
    for atom in base.atoms:
        if atom.atom_id == revision_input:
            return atom
        if is_assertion_atom(atom) and revision_input in _assertion_input_candidates(
            atom
        ):
            return atom
        if is_assumption_atom(atom) and atom.assumption.assumption_id == revision_input:
            return atom
    return None


def _assertion_input_candidates(atom: BeliefAtom) -> tuple[str, ...]:
    if not is_assertion_atom(atom):
        return ()
    return (atom.atom_id, str(atom.assertion_id))
