"""Source charter and derived-store model helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus


_SOURCE_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)


class Source(FamilyModel):
    pass


class SourceOriginDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    type: SourceOriginType
    value: str
    retrieved: str | None = None
    content_ref: str | None = None


class SourceTrustQualityDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    status: ProvenanceStatus
    b: float | int
    d: float | int
    u: float | int
    a: float | int


class SourceTrustDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    status: ProvenanceStatus
    prior_base_rate: Opinion | None = None
    quality: SourceTrustQualityDocument | None = None
    derived_from: tuple[str, ...] = ()


class SourceMetadataDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    name: str


class SourceParameterizationGroupMergeDocument(
    msgspec.Struct,
    kw_only=True,
    forbid_unknown_fields=True,
):
    merged_group: tuple[str, ...]
    previous_groups: tuple[tuple[str, ...], ...]
    introduced_by: tuple[str, ...]


class SourceFinalizeCalibrationDocument(
    msgspec.Struct,
    kw_only=True,
    forbid_unknown_fields=True,
):
    prior_base_rate_status: str
    source_quality_status: str
    fallback_to_default_base_rate: bool


class SourceFinalizeReportDocument(
    msgspec.Struct,
    kw_only=True,
    forbid_unknown_fields=True,
):
    kind: str
    source: str
    status: str
    artifact_code_status: str
    calibration: SourceFinalizeCalibrationDocument
    micropub_status: str = "not_composed"
    claim_reference_errors: tuple[str, ...] = ()
    micropub_coverage_errors: tuple[str, ...] = ()
    justification_reference_errors: tuple[str, ...] = ()
    stance_reference_errors: tuple[str, ...] = ()
    concept_alignment_candidates: tuple[str, ...] = ()
    parameterization_group_merges: tuple[SourceParameterizationGroupMergeDocument, ...] = ()


SOURCE_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="source",
            name="source",
            contract_version=_SOURCE_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-source",
                contract_version=_SOURCE_CONTRACT_VERSION,
                doc_type=Source,
                placement=FlatYamlPlacement(".derived/source", str),
            ),
            identity_field="slug",
        ),
        model=Source,
        fields=(
            CharterField("slug", str, primary_key=True, nullable=False, document=False),
            CharterField("source_id", str, nullable=False, document_name="id"),
            CharterField("kind", SourceKind, nullable=False),
            CharterField("origin", SourceOriginDocument, parse_boundary="json"),
            CharterField("trust", SourceTrustDocument, parse_boundary="json"),
            CharterField(
                "metadata",
                SourceMetadataDocument,
                parse_boundary="json",
                nullable=True,
            ),
            CharterField(
                "quality",
                SourceTrustQualityDocument,
                parse_boundary="json",
                nullable=True,
                document=False,
            ),
            CharterField(
                "derived_from",
                list,
                parse_boundary="json",
                nullable=True,
                document=False,
            ),
            CharterField("artifact_code", str, artifact=True, nullable=True),
        ),
        indexes=(CharterIndex("idx_source_source_id", ("source_id",)),),
        semantic_metadata={"semantic": "propstore.world"},
    )

if TYPE_CHECKING:

    class SourceDocument(msgspec.Struct, forbid_unknown_fields=True):
        id: str
        kind: SourceKind
        origin: SourceOriginDocument
        trust: SourceTrustDocument
        metadata: SourceMetadataDocument | None = None
        artifact_code: str | None = None

else:
    SourceDocument: Any = SOURCE_CHARTER.generated_document()
    SourceDocument.__module__ = __name__


def source_document_payload(source_doc: SourceDocument) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": source_doc.id,
        "kind": source_doc.kind.value,
        "origin": source_doc.origin.to_payload(),
        "trust": source_doc.trust.to_payload(),
    }
    if source_doc.metadata is not None:
        payload["metadata"] = source_doc.metadata.to_payload()
    if source_doc.artifact_code is not None:
        payload["artifact_code"] = source_doc.artifact_code
    return payload


def encode_source_document(source_doc: SourceDocument) -> bytes:
    return msgspec.yaml.encode(source_document_payload(source_doc))


def render_source_document(source_doc: SourceDocument) -> str:
    return encode_source_document(source_doc).decode("utf-8").rstrip()


def compile_source_models(
    sources: Iterable[tuple[str, SourceDocument]],
) -> tuple[Source, ...]:
    source_models: list[Source] = []
    for slug, source_doc in sources:
        origin = source_doc.origin
        trust = source_doc.trust
        source_models.append(
            Source(
                slug=slug,
                source_id=str(source_doc.id or slug),
                kind=source_doc.kind.value,
                origin=origin,
                trust=trust,
                metadata=source_doc.metadata,
                quality=(
                    None
                    if trust.quality is None
                    else trust.quality
                ),
                derived_from=list(trust.derived_from) if trust.derived_from else None,
                artifact_code=source_doc.artifact_code,
            )
        )
    return tuple(source_models)
