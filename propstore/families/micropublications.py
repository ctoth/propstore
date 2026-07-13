"""The ``Micropublication`` entity — the Clark micropublication bundle charter.

A micropublication (Clark, Ciccarese & Goble 2014) bundles a set of claims with
the evidence, assumptions, stance, provenance, and source that situate them. This
is the bundle used directly by authoring, sidecar reads, and runtime ATMS support.

Substrate boundary: the class IS the document. Its ``context_id`` and ``claims``
references are declared as :class:`~quire.references.ForeignKeySpec` annotations
on the fields, so the family registry's foreign-key graph for this family is
derived (PLAN.md §12.6 names micropublications as one of the two hardest families
the charter→FK derivation must cover). ``stance`` reuses the one
:class:`~propstore.stances.StanceType`; ``provenance`` reuses the one
:class:`~propstore.provenance.Provenance`. There is no ``MicropublicationDocument``
second spelling.
"""

from __future__ import annotations

from typing import Annotated

import msgspec

from quire.charter_class import CharterDoc, charter, charter_field
from quire.references import ForeignKeySpec

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION
from propstore.provenance import Provenance
from propstore.stances import StanceType


class MicropublicationEvidence(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A single piece of evidence backing a micropublication's claims."""

    kind: str
    reference: str


def validate_principal_claim(
    claims: tuple[str, ...],
    principal_claim: str | None,
) -> None:
    """Enforce Clark's principal claim ``c`` over a bundle's claim set.

    The single canonical rule, shared by the charter and by the runtime view
    (:class:`~propstore.core.micropublications.ActiveMicropublication`) — the
    two must never disagree about which claim a bundle is *about*.

    A one-claim bundle's principal is that claim. A multi-claim bundle has no
    distinguished greatest element unless one is authored, and guessing would
    fabricate the bundle's point, so it must be explicit. An authored principal
    must be a member of the bundle.
    """

    if principal_claim is None:
        if len(claims) > 1:
            raise ValueError(
                "a multi-claim micropublication requires an explicit principal "
                "claim: the principal claim is the distinguished greatest element "
                "of the support order and cannot be inferred"
            )
        return
    if principal_claim not in claims:
        raise ValueError(
            f"micropublication principal claim {principal_claim!r} is not one of "
            "its claims"
        )


def principal_claim_id(
    claims: tuple[str, ...],
    principal_claim: str | None,
) -> str:
    """The bundle's principal claim: authored if given, else the sole claim."""

    if principal_claim is not None:
        return principal_claim
    return claims[0]


@charter(
    key="micropublication",
    name="micropublication",
    contract_version="2026.07.13",
    placement="micropublication",
    identity_field="artifact_id",
)
class Micropublication(CharterDoc):
    """A Clark micropublication bundle authored against a context.

    ``artifact_id`` is the identity. ``context_id`` and the ``claims`` it bundles
    are foreign keys into the context and claim families; the bundle is empty of
    meaning without claims, so a sidecar projection quarantines a bundle whose
    claims do not resolve rather than dropping it silently.

    The charter enforces the representable parts of Clark, Ciccarese & Goble
    (2014) ``MP = (A, mp, c, A_c, Φ, R)``: at least one claim, an attribution
    (every element must have one — carried by ``source`` or by ``provenance``),
    and a well-defined principal claim ``c``. ``R``, the support/challenge
    relation, is delegated to the stance layer.
    """

    artifact_id: Annotated[str, charter_field(primary_key=True)]
    context_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="micropublication_context",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="micropublication",
                source_field="context_id",
                target_family="context",
                target_field="context_id",
            )
        ),
    ]
    claims: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            foreign_keys=(
                ForeignKeySpec(
                    name="micropublication_claims",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="micropublication",
                    source_field="claims[]",
                    target_family="claim",
                    target_field="claim_id",
                    many=True,
                ),
            ),
        ),
    ]
    version_id: str | None = None
    evidence: Annotated[
        tuple[MicropublicationEvidence, ...], charter_field(json=True)
    ] = ()
    assumptions: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    stance: StanceType | None = None
    provenance: Annotated[Provenance | None, charter_field(json=True)] = None
    source: str | None = None
    principal_claim: str | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("micropublication artifact_id is required")
        if not self.context_id:
            raise ValueError("micropublication context_id is required")
        if not self.claims:
            raise ValueError("micropublication claims must not be empty")
        if self.source is None and self.provenance is None:
            raise ValueError(
                "micropublication requires an attribution: every element of a "
                "micropublication must have one (Clark 2014) — carry it on "
                "'source' or on 'provenance'"
            )
        validate_principal_claim(self.claims, self.principal_claim)

    @property
    def principal_claim_id(self) -> str:
        """The principal claim ``c`` — the greatest element of the support order."""

        return principal_claim_id(self.claims, self.principal_claim)
