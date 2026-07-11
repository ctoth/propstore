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


@charter(
    key="micropublication",
    name="micropublication",
    contract_version="2026.06.29",
    placement="micropublication",
    identity_field="artifact_id",
)
class Micropublication(CharterDoc):
    """A Clark micropublication bundle authored against a context.

    ``artifact_id`` is the identity. ``context_id`` and the ``claims`` it bundles
    are foreign keys into the context and claim families; the bundle is empty of
    meaning without claims, so a sidecar projection quarantines a bundle whose
    claims do not resolve rather than dropping it silently.
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

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("micropublication artifact_id is required")
        if not self.context_id:
            raise ValueError("micropublication context_id is required")
        if not self.claims:
            raise ValueError("micropublication claims must not be empty")
