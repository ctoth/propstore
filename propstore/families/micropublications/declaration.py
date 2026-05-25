"""Micropublication model declarations and family-owned compilation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TYPE_CHECKING

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, CharterRelationship, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.references import FamilyReferenceIndex, ForeignKeySpec
from quire.versions import VersionId

from ...core.diagnostics import QuarantineDiagnostic
from ..claims.documents import ProvenanceDocument
from ..contexts.declaration import ContextReferenceDocument

if TYPE_CHECKING:
    from ..claims.references import ClaimReferenceRecord


_MICROPUBLICATION_WORLD_CONTRACT_VERSION = VersionId(
    "2026.05.20",
    allow_placeholder=False,
)


class MicropublicationEvidenceDocument(msgspec.Struct, forbid_unknown_fields=True):
    kind: str
    reference: str


def _micropub_validate_non_empty_claims(document: msgspec.Struct) -> None:
    if not getattr(document, "claims"):
        raise ValueError("claims must contain at least one claim reference")


class Micropublication(FamilyModel):
    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(
            link.claim_id
            for link in sorted(self.claim_links, key=lambda link: (link.seq, link.claim_id))
        )


class MicropublicationClaimLink(FamilyModel):
    pass


MICROPUBLICATION_CHARTER: FamilyCharter = FamilyCharter(
            family=FamilyDefinition(
                key="micropublication",
                name="micropublication",
                contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-micropublication",
                    contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                    doc_type=Micropublication,
                    placement=FlatYamlPlacement(".derived/micropublication", str),
                ),
                identity_field="id",
            ),
            model=Micropublication,
            fields=(
                CharterField(
                    "id",
                    str,
                    primary_key=True,
                    nullable=False,
                    document_name="artifact_id",
                ),
                CharterField(
                    "context_id",
                    ContextReferenceDocument,
                    nullable=False,
                    document_name="context",
                ),
                CharterField(
                    "claims",
                    tuple[str, ...],
                    parse_boundary="json",
                    nullable=False,
                    default=(),
                ),
                CharterField("version_id", str, nullable=True),
                CharterField(
                    "assumptions_json",
                    tuple[str, ...],
                    parse_boundary="json",
                    nullable=False,
                    default=(),
                    default_sql="'[]'",
                    document_name="assumptions",
                ),
                CharterField(
                    "evidence_json",
                    tuple[MicropublicationEvidenceDocument, ...],
                    parse_boundary="json",
                    nullable=False,
                    default=(),
                    default_sql="'[]'",
                    document_name="evidence",
                ),
                CharterField("stance", str, nullable=True),
                CharterField(
                    "provenance_json",
                    ProvenanceDocument,
                    parse_boundary="json",
                    nullable=True,
                    document_name="provenance",
                ),
                CharterField("source_slug", str, nullable=True, document_name="source"),
            ),
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
            semantic_metadata={"semantic": "propstore.world"},
            validators=(_micropub_validate_non_empty_claims,),
        )


MICROPUBLICATION_CLAIM_CHARTER: FamilyCharter = FamilyCharter(
            family=FamilyDefinition(
                key="micropublication_claim",
                name="micropublication_claim",
                contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-micropublication_claim",
                    contract_version=_MICROPUBLICATION_WORLD_CONTRACT_VERSION,
                    doc_type=MicropublicationClaimLink,
                    placement=FlatYamlPlacement(".derived/micropublication_claim", str),
                ),
                identity_field="micropublication_id",
            ),
            model=MicropublicationClaimLink,
            fields=(
                CharterField(
                    "micropublication_id",
                    str,
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
                CharterField(
                    "claim_id",
                    str,
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
                CharterField("seq", int, nullable=False),
            ),
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
            semantic_metadata={"semantic": "propstore.world"},
        )


if TYPE_CHECKING:
    class MicropublicationDocument(msgspec.Struct, forbid_unknown_fields=True):
        artifact_id: str
        context: ContextReferenceDocument
        claims: tuple[str, ...]
        version_id: str | None = None
        assumptions: tuple[str, ...] = ()
        evidence: tuple[MicropublicationEvidenceDocument, ...] = ()
        stance: str | None = None
        provenance: ProvenanceDocument | None = None
        source: str | None = None

else:
    MicropublicationDocument: Any = MICROPUBLICATION_CHARTER.generated_document()


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
