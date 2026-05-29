"""Micropublication model declarations and family-owned compilation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Annotated, TYPE_CHECKING

import msgspec
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import CharterIndex, CharterRelationship, FamilyCharter, FamilyModel
from quire.documents import DocumentBatchSpec
from quire.references import FamilyReferenceIndex, ForeignKeySpec
from quire.versions import VersionId

from ...core.diagnostics import QuarantineDiagnostic
from ..claims.declaration import ProvenanceDocument
from ..contexts.declaration import ContextReferenceDocument

if TYPE_CHECKING:
    from ..claims.references import ClaimReferenceRecord


_MICROPUBLICATION_WORLD_CONTRACT_VERSION = VersionId(
    "2026.05.20",
    allow_placeholder=False,
)
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


class MicropublicationEvidenceDocument(CharterDoc):
    kind: str
    reference: str


def _micropub_validate_non_empty_claims(document: msgspec.Struct) -> None:
    if not getattr(document, "claims"):
        raise ValueError("claims must contain at least one claim reference")


class MicropublicationBehavior:
    """Row behaviour for the micropublication model.

    ``@charter(model_mixin=...)`` makes the generated SQLAlchemy model inherit
    this, so the micropublication row keeps its ``claim_ids`` accessor that reads
    the ordered ``claim_links`` association rows.
    """

    claim_links: Sequence[MicropublicationClaimLink]

    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(
            link.claim_id
            for link in sorted(self.claim_links, key=lambda link: (link.seq, link.claim_id))
        )


if TYPE_CHECKING:
    # ``@charter`` generates these SQLAlchemy-mappable models at runtime (via
    # ``model_name=``) and binds them into this module's namespace; the static
    # stubs keep model construction/attribute access type-checking.
    class Micropublication(MicropublicationBehavior, FamilyModel): ...

    class MicropublicationClaimLink(FamilyModel): ...


@charter(
    key="micropublication",
    name="micropublication",
    contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
    placement=".derived/micropublication",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-micropublication",
    model_name="Micropublication",
    model_mixin=MicropublicationBehavior,
    indexes=(CharterIndex("idx_micropub_context", ("context_id",)),),
    relationships=(
        CharterRelationship(
            "claim_links",
            target_family="micropublication_claim",
            foreign_key="micropublication_id",
            back_populates="micropublication",
            association_object=True,
            order_by=("seq",),
        ),
    ),
    validators=(_micropub_validate_non_empty_claims,),
)
class MicropublicationDocument(CharterDoc):
    artifact_id: Annotated[
        str,
        charter_field(column_name="id", primary_key=True, nullable=False),
    ]
    context: Annotated[
        ContextReferenceDocument,
        charter_field(
            column_name="context_id",
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="micropub_context",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="micropubs",
                source_field="context.id",
                target_family="contexts",
            ),
        ),
    ]
    claims: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="micropub_claims",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="micropubs",
                source_field="claims[]",
                target_family="claims",
                many=True,
            ),
        ),
    ] = ()
    version_id: str | None = None
    assumptions: Annotated[
        tuple[str, ...],
        charter_field(
            column_name="assumptions_json",
            json=True,
            nullable=False,
            default_sql="'[]'",
        ),
    ] = ()
    evidence: Annotated[
        tuple[MicropublicationEvidenceDocument, ...],
        charter_field(
            column_name="evidence_json",
            json=True,
            nullable=False,
            default_sql="'[]'",
        ),
    ] = ()
    stance: str | None = None
    provenance: Annotated[
        ProvenanceDocument | None,
        charter_field(column_name="provenance_json", json=True, nullable=True),
    ] = None
    source: Annotated[str | None, charter_field(column_name="source_slug", nullable=True)] = None


MICROPUBLICATION_CHARTER: FamilyCharter = MicropublicationDocument.__charter__


@charter(
    key="micropublication_claim",
    name="micropublication_claim",
    contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
    placement=".derived/micropublication_claim",
    identity_field="micropublication_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-micropublication_claim",
    model_name="MicropublicationClaimLink",
    indexes=(CharterIndex("idx_micropub_claim", ("claim_id",)),),
    relationships=(
        CharterRelationship(
            "micropublication",
            target_family="micropublication",
            foreign_key="micropublication_id",
            back_populates="claim_links",
            uselist=False,
        ),
    ),
)
class Micropublication_claimDocument(CharterDoc):
    micropublication_id: Annotated[
        str,
        charter_field(
            primary_key=True,
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="micropublication_claim_micropublication",
                contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                source_family="micropublication_claim",
                source_field="micropublication_id",
                target_family="micropublication",
                target_field="id",
                required=True,
            ),
        ),
    ]
    claim_id: Annotated[
        str,
        charter_field(
            primary_key=True,
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="micropublication_claim_claim",
                contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                source_family="micropublication_claim",
                source_field="claim_id",
                target_family="claim_core",
                target_field="id",
                required=True,
            ),
        ),
    ]
    seq: Annotated[int, charter_field(nullable=False)]


MICROPUBLICATION_CLAIM_CHARTER: FamilyCharter = Micropublication_claimDocument.__charter__


SOURCE_MICROPUBLICATION_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-micropublications",
    item_type=MicropublicationDocument,
    items_field="micropublications",
    inherited_item_fields=("source",),
)
object.__setattr__(
    MICROPUBLICATION_CHARTER,
    "batch_specs",
    (SOURCE_MICROPUBLICATION_BATCH_SPEC,),
)


MICROPUBLICATION_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (
    MICROPUBLICATION_CHARTER,
    MICROPUBLICATION_CLAIM_CHARTER,
)


MicropublicationModelBatches = tuple[
    tuple[Micropublication, ...],
    tuple[MicropublicationClaimLink, ...],
]


def compile_micropublication_models_with_diagnostics(
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[MicropublicationModelBatches, tuple[QuarantineDiagnostic, ...]]:
    valid_claim_ids = set(claim_index.ids())
    micropublications: dict[str, Micropublication] = {}
    claim_links: dict[tuple[str, str], MicropublicationClaimLink] = {}
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, micropub in sorted(micropub_entries, key=lambda item: item[0]):
        resolved_claims: list[str] = []
        missing_claim_ref: str | None = None
        for claim_id in micropub.claims:
            resolved_claim = claim_index.resolve_id(claim_id)
            if (
                not isinstance(resolved_claim, str)
                or resolved_claim not in valid_claim_ids
            ):
                if isinstance(resolved_claim, str) and resolved_claim:
                    missing_claim_ref = resolved_claim
                elif isinstance(claim_id, str) and claim_id:
                    missing_claim_ref = claim_id
                else:
                    missing_claim_ref = micropub.artifact_id
                break
            resolved_claims.append(resolved_claim)
        if missing_claim_ref is not None:
            message = (
                f"micropublication artifact {micropub.artifact_id} references "
                f"nonexistent claim '{missing_claim_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_claim_ref,
                    kind="micropublication",
                    diagnostic_kind="micropublication_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        micropublications.setdefault(
            micropub.artifact_id,
            Micropublication(
                id=micropub.artifact_id,
                context_id=str(micropub.context.id),
                assumptions_json=micropub.assumptions,
                evidence_json=micropub.evidence,
                stance=None if micropub.stance is None else str(micropub.stance),
                provenance_json=(
                    None
                    if micropub.provenance is None
                    else micropub.provenance
                ),
                source_slug=micropub.source,
            )
        )
        for seq, claim_id in enumerate(resolved_claims, start=1):
            claim_links.setdefault(
                (micropub.artifact_id, claim_id),
                MicropublicationClaimLink(
                    micropublication_id=micropub.artifact_id,
                    claim_id=claim_id,
                    seq=seq,
                )
            )

    return (
        (tuple(micropublications.values()), tuple(claim_links.values())),
        tuple(diagnostics),
    )
