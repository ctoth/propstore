from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

from propstore.cel_types import to_cel_expr
from propstore.core.id_types import AssumptionId
from propstore.core.labels import AssumptionRef
from propstore.support_revision.state import (
    AssumptionAtom,
    AssertionAtom,
    BeliefAtom,
    BeliefBase,
    is_assertion_atom,
    is_assumption_atom,
)

RevisionInput: TypeAlias = BeliefAtom | str | Mapping[str, object]


def normalize_revision_input(
    base: BeliefBase,
    revision_input: RevisionInput,
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
        assertion_id = (
            revision_input.get("assertion_id")
            or revision_input.get("id")
            or revision_input.get("atom_id")
        )
        if not assertion_id:
            raise ValueError("Assertion revision input requires 'assertion_id' or 'id'")
        existing = _find_existing_atom(base, str(assertion_id))
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {assertion_id}")

    if kind == "assumption":
        assumption_id = revision_input.get("assumption_id") or revision_input.get("id")
        if not assumption_id:
            raise ValueError(
                "Assumption revision input requires 'assumption_id' or 'id'"
            )
        assumption_id_text = str(assumption_id)
        atom_id = str(revision_input.get("atom_id") or f"assumption:{assumption_id}")
        return AssumptionAtom(
            atom_id=atom_id,
            assumption=AssumptionRef(
                assumption_id=AssumptionId(assumption_id_text),
                cel=to_cel_expr(str(revision_input.get("cel") or "")),
                kind=str(revision_input.get("kind") or ""),
                source=str(revision_input.get("source") or ""),
            ),
        )

    raise ValueError("Assertion revision input requires an AssertionAtom")


def normalize_revision_targets(
    base: BeliefBase,
    targets: RevisionInput | Sequence[RevisionInput],
) -> tuple[str, ...]:
    if isinstance(targets, (str, Mapping, AssertionAtom, AssumptionAtom)):
        return (normalize_revision_input(base, targets).atom_id,)
    return tuple(normalize_revision_input(base, target).atom_id for target in targets)


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
