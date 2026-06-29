"""The ``SameAs`` entity — a graded, defeasible identity assertion between artifacts.

An ``owl:sameAs`` edge says two identifiers denote the same thing. Taken as hard
truth it is notoriously over-asserted: the linked-data literature documents how
naive ``sameAs`` closure conflates distinct entities (Halpin et al. 2010; Beek et
al. 2018; Raad et al. 2018; De Melo 2013). propstore therefore treats every
imported identity edge as a **defeasible claim with provenance**, never a source
truth (CLAUDE.md: every imported row is a defeasible claim with provenance). The
graded ``sim:`` relation vocabulary records *how strong* the asserted identity is,
and an optional Jøsang opinion carries the calibrated strength — both honest
signals, never a gate.

Charter discipline (PLAN.md §12, CLAUDE.md): ONE canonical ``SameAs`` charter. The
git document, the sidecar ``same_as_assertion`` columns, and the serialized
contract all fall out of these field annotations. There is no ``SameAsDocument`` /
``SameAsRecord`` / ``SameAsRow`` second spelling and no ``to_payload`` /
``from_payload``. The opinion is stored as the four Jøsang components and rebuilt as
``doxa``'s canonical :class:`doxa.Opinion`, never re-spelled.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from doxa import Opinion
from quire.charter_class import CharterDoc, charter, charter_field

_DOGMATIC_TOL = 1e-9


class SameAsRelation(StrEnum):
    """Graded identity vocabulary, strongest to weakest.

    ``sim:sameIndividual`` asserts the two artifacts denote the same individual;
    ``sim:claimsIdentical`` that they make the identical claim; ``sim:almostSameAs``
    a near-identity that explicitly stops short of full ``owl:sameAs`` (Beek et al.
    2018's ``almostSameAs`` link, motivated by the unreliability of asserted
    ``owl:sameAs`` at web scale).
    """

    SAME_INDIVIDUAL = "sim:sameIndividual"
    CLAIMS_IDENTICAL = "sim:claimsIdentical"
    ALMOST_SAME_AS = "sim:almostSameAs"


@charter(
    key="same_as_assertion",
    name="same_as_assertion",
    contract_version="2026.06.29",
    placement="same_as_assertion",
    identity_field="sameas_id",
    semantic="propstore.same_as_assertion",
)
class SameAs(CharterDoc):
    """A defeasible graded-identity assertion between two artifacts.

    The class *is* the document: ``sameas_id`` is the edge identity; the four
    ``opinion_*`` columns are nullable (honest absence of a calibrated strength, not
    a fabricated default). ``evidence_source`` records where the edge came from —
    the assertion is a claim, never a privileged truth.
    """

    sameas_id: Annotated[str, charter_field(primary_key=True)]
    left_artifact_id: str
    right_artifact_id: str
    relation: SameAsRelation = SameAsRelation.ALMOST_SAME_AS
    evidence_source: str | None = None
    confidence: float | None = None
    opinion_belief: float | None = None
    opinion_disbelief: float | None = None
    opinion_uncertainty: float | None = None
    opinion_base_rate: float | None = None

    def opinion(self) -> Opinion | None:
        """Rebuild the calibrated identity strength as ``doxa.Opinion``, or ``None``.

        Returns ``None`` unless all four Jøsang components are present — a partial
        opinion is treated as no opinion, never completed with a fabricated mass.
        """

        b = self.opinion_belief
        d = self.opinion_disbelief
        u = self.opinion_uncertainty
        a = self.opinion_base_rate
        if b is None or d is None or u is None or a is None:
            return None
        return Opinion(b, d, u, a, allow_dogmatic=u < _DOGMATIC_TOL)
