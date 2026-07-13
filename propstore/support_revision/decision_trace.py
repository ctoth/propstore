"""What a formal revision decision recorded about how it was reached.

The trace was a bare ``dict[str, Any]``, but it was never a bag: it is a tagged
union whose shape is determined by the operator that produced it. A revision
records its operator and pre-image fingerprint; an IC merge records the profile
it merged, the constraint it merged under, and the worlds it selected; expand and
contract record nothing. Reading it meant ``trace.get(...)`` and hoping.

``ranking_provenance`` did not belong in that bag at all — it is a sibling fact
about *how the ranking was obtained*, present for every operator, and its
``status`` was the string ``"defaulted"``: a second spelling of
:class:`~propstore.provenance.ProvenanceStatus.DEFAULTED`. CLAUDE.md requires
every value that reaches the argumentation layer to carry typed provenance, so it
carries the enum and lives on its own field.
"""

from __future__ import annotations

import msgspec

from propstore.provenance import ProvenanceStatus
from propstore.support_revision.integrity_constraints import IntegrityConstraintSpec


class RankingProvenance(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """How the epistemic ranking a decision used was obtained.

    ``DEFAULTED`` is the honest answer when no authored ranking existed and the
    Hamming-distance fallback supplied one — it is a fallback, not a measurement,
    and the enum says so rather than a bare string.
    """

    status: ProvenanceStatus
    method: str
    input_hash: str


class RevisionTrace(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="kind", tag="revision"
):
    """What an AGM/iterated revision recorded about its outcome."""

    operator: str
    pre_image_fingerprint: str


class ICMergeTrace(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="kind", tag="ic_merge"
):
    """What a Konieczny-style IC merge recorded about its outcome.

    ``integrity_constraint`` is the authored constraint itself, not a lowering of
    it: the merge stores what it merged under. It is ``None`` when the merge was
    driven by a raw ``belief_set`` formula rather than an authored constraint —
    there is then no authored constraint to record, and inventing one would be a
    lie about where the merge came from.
    """

    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    profile_hash: str = ""
    integrity_constraint: IntegrityConstraintSpec | None = None
    merge_operator: str = "sigma"
    selected_worlds_hash: str = ""
    scored_worlds_hash: str = ""


DecisionTrace = RevisionTrace | ICMergeTrace
"""What a decision recorded, discriminated on its ``kind`` tag.

Expand and contract carry no trace (``None``): they have nothing to record beyond
the accepted/rejected formulas the report already holds.
"""


__all__ = [
    "DecisionTrace",
    "ICMergeTrace",
    "RankingProvenance",
    "RevisionTrace",
]
