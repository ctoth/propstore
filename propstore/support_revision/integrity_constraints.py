"""The authored integrity constraint an IC merge is performed under.

Konieczny-style IC merge selects the models of a profile that satisfy an
*integrity constraint*. The constraint is a tagged union of three authored
shapes, and it was carried as a bare mapping whose ``"kind"`` key was read by
hand at ``belief_set_adapter._integrity_constraint_formula`` — a discriminated
union with the discrimination done manually, and its grammar documented only in
the ``ValueError`` raised when the hand-rolled parse fell through. Tagging the
union puts that grammar in the type, so a malformed constraint fails when the
document is decoded rather than deep inside a replay.

This module is deliberately free of ``belief_set``: what is *stored* is the
authored constraint, and the ``Formula`` it compiles to is the compute form, so
the crossing is a call at the boundary (``belief_set_adapter``), not a mirror
type. Keeping the import out also keeps the module storage-pure, which the
worldline charter needs — it persists one of these on its revision query.
"""

from __future__ import annotations

import msgspec


class TopConstraint(msgspec.Struct, frozen=True, tag_field="kind", tag="top"):
    """The trivial constraint: every model satisfies it."""


class AtomConstraint(msgspec.Struct, frozen=True, tag_field="kind", tag="atom"):
    """The merged result must entail this one atom."""

    atom_id: str

    def __post_init__(self) -> None:
        if not self.atom_id:
            raise ValueError("atom integrity constraint requires an atom_id")


class LiteralsConstraint(msgspec.Struct, frozen=True, tag_field="kind", tag="literals"):
    """The merged result must entail every required atom and no forbidden one.

    An atom appearing in both ``required`` and ``forbidden`` is *representable*
    on purpose. Such a constraint is unsatisfiable, but that is a semantic fact
    the merge discovers and reports as a typed
    ``RevisionMergeRequiredFailure(reason="unsatisfiable_integrity_constraint")``
    — rejecting it at construction would turn a reasoned outcome into a syntax
    error and delete the failure path that reports it.
    """

    required: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "required", tuple(str(item) for item in self.required))
        object.__setattr__(self, "forbidden", tuple(str(item) for item in self.forbidden))


IntegrityConstraintSpec = TopConstraint | AtomConstraint | LiteralsConstraint
"""The authored integrity constraint, discriminated on its ``kind`` tag."""


__all__ = [
    "AtomConstraint",
    "IntegrityConstraintSpec",
    "LiteralsConstraint",
    "TopConstraint",
]
