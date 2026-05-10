from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.support_revision.state import (
    AssumptionAtom,
    AssertionAtom,
    BeliefAtom,
    BeliefBase,
    coerce_assumption_ref,
    is_assertion_atom,
    is_assumption_atom,
)


def normalize_revision_input(
    base: BeliefBase,
    revision_input: BeliefAtom | str | Mapping[str, Any],
) -> BeliefAtom:
    """Normalize a user-facing revision input into a belief atom."""
    if isinstance(revision_input, (AssertionAtom, AssumptionAtom)):
        return revision_input

    if isinstance(revision_input, str):
        existing = _find_existing_atom(base, revision_input)
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {revision_input}")

    kind = str(revision_input.get("kind") or "")
    if kind == "assertion":
        assertion_id = revision_input.get("assertion_id") or revision_input.get("id") or revision_input.get("atom_id")
        if not assertion_id:
            raise ValueError("Assertion revision input requires 'assertion_id' or 'id'")
        existing = _find_existing_atom(base, str(assertion_id))
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {assertion_id}")

    if kind == "assumption":
        assumption_id = revision_input.get("assumption_id") or revision_input.get("id")
        if not assumption_id:
            raise ValueError("Assumption revision input requires 'assumption_id' or 'id'")
        atom_id = str(revision_input.get("atom_id") or f"assumption:{assumption_id}")
        return AssumptionAtom(atom_id=atom_id, assumption=coerce_assumption_ref(revision_input))

    raise ValueError("Assertion revision input requires an AssertionAtom")


def _find_existing_atom(base: BeliefBase, revision_input: str) -> BeliefAtom | None:
    for atom in base.atoms:
        if atom.atom_id == revision_input:
            return atom
        if is_assertion_atom(atom) and revision_input in _assertion_input_candidates(atom):
            return atom
        if is_assumption_atom(atom) and atom.assumption.assumption_id == revision_input:
            return atom
    return None


def _assertion_input_candidates(atom: BeliefAtom) -> tuple[str, ...]:
    if not is_assertion_atom(atom):
        return ()
    return (atom.atom_id, str(atom.assertion_id))
