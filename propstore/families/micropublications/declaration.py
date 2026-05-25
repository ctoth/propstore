"""Micropublication model declarations and family-owned compilation."""

from __future__ import annotations

import json
from collections.abc import Iterable

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, CharterRelationship, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.references import FamilyReferenceIndex, ForeignKeySpec

from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION


class Micropublication(FamilyModel):
    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(
            link.claim_id
            for link in sorted(self.claim_links, key=lambda link: (link.seq, link.claim_id))
        )


class MicropublicationClaimLink(FamilyModel):
    pass


def micropublication_charters() -> tuple[FamilyCharter, FamilyCharter]:
    return (
        FamilyCharter(
            family=FamilyDefinition(
                key="micropublication",
                name="micropublication",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-micropublication",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=Micropublication,
                    placement=FlatYamlPlacement(".derived/micropublication", str),
                ),
                identity_field="id",
            ),
            model=Micropublication,
            fields=(
                CharterField("id", str, primary_key=True, nullable=False),
                CharterField("context_id", str, nullable=False),
                CharterField("assumptions_json", str, nullable=False, default_sql="'[]'"),
                CharterField("evidence_json", str, nullable=False, default_sql="'[]'"),
                CharterField("stance", str),
                CharterField("provenance_json", str),
                CharterField("source_slug", str),
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
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="micropublication_claim",
                name="micropublication_claim",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-micropublication_claim",
                    contract_version=_WORLD_CONTRACT_VERSION,
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
                        contract_version=_WORLD_CONTRACT_VERSION,
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
                        contract_version=_WORLD_CONTRACT_VERSION,
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
        ),
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
                assumptions_json=json.dumps(
                    list(micropub.assumptions),
                    sort_keys=True,
                ),
                evidence_json=json.dumps(
                    [item.to_payload() for item in micropub.evidence],
                    sort_keys=True,
                ),
                stance=None if micropub.stance is None else micropub.stance.value,
                provenance_json=(
                    None
                    if micropub.provenance is None
                    else json.dumps(
                        micropub.provenance.to_payload(),
                        sort_keys=True,
                    )
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
