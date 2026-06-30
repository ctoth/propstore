"""Conflict projection charter.

A detected conflict between two claims (rebuttal, overlap, phi-node, parameter
clash, …) is projected into this charter-derived ``conflict`` table. The conflict
*compute* lives in :mod:`propstore.conflict_detector` (it returns
:class:`~propstore.conflict_detector.models.ConflictRecord` values); this charter
is only the queryable projection the world reader selects over — the projection is
the charter, populated with ``session.add_family("conflict", {...})``.

Like :class:`~propstore.families.diagnostics.BuildDiagnostic`, ``ConflictProjection``
is a derived-only family: no ``semantic`` tag and no foreign keys (a conflict may
reference a quarantined or blocked claim and must still record).
"""

from __future__ import annotations

from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field


@charter(
    key="conflict",
    name="conflict",
    contract_version="2026.06.29",
    placement="conflict",
    identity_field="conflict_id",
)
class ConflictProjection(CharterDoc):
    """One detected pairwise conflict between two claims over a concept.

    ``warning_class`` is the conflict class value (``"CONFLICT"`` / ``"OVERLAP"``
    / ``"PHI_NODE"`` / ``"CONTEXT_PHI_NODE"`` / ``"PARAM_CONFLICT"`` / …);
    ``value_a`` / ``value_b`` are the rendered conflicting values.
    """

    conflict_id: Annotated[str, charter_field(primary_key=True)]
    warning_class: str
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    value_a: str
    value_b: str
    derivation_chain: str | None = None
