"""Conflict detector package.

Classifies how same-concept claims relate (compatible, conflicting, φ-node,
overlap, parameter conflict, context φ-node) by composing the formal substrates
directly: condition-ir for Z3 condition reasoning, eq-equiv for equation
equivalence, ast-equiv for algorithm equivalence, and value_comparison/dimensions
for unit-aware value comparison. Every relationship is emitted as a
:class:`ConflictRecord` with provenance and never dropped.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from .models import ConflictClass, ConflictRecord

if TYPE_CHECKING:
    from condition_ir import ConceptInfo

    from propstore.context_lifting import LiftingSystem

    from .models import ConflictClaim


def detect_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: Mapping[str, Mapping[str, object]],
    cel_registry: Mapping[str, ConceptInfo],
    lifting_system: LiftingSystem | None = None,
) -> list[ConflictRecord]:
    from .orchestrator import detect_conflicts as _detect_conflicts

    return _detect_conflicts(
        claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )


__all__ = [
    "ConflictClass",
    "ConflictRecord",
    "detect_conflicts",
]
