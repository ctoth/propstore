"""Source charter and derived-store model helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeAlias

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter, FamilyModel
from quire.documents import document_to_payload
from quire.families import FamilyDefinition
from quire.versions import VersionId

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus


_SOURCE_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)


class Source(FamilyModel):
    pass


class SourceOrigin(FamilyModel):
    pass


SOURCE_ORIGIN_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-origin",
        name="source-origin",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-origin",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceOrigin,
            placement=FlatYamlPlacement(".derived/source-origin", str),
        ),
        identity_field="value",
    ),
    model=SourceOrigin,
    fields=(
        CharterField("type", SourceOriginType, nullable=False, enum_type=SourceOriginType),
        CharterField("value", str, nullable=False),
        CharterField("retrieved", str, nullable=True),
        CharterField("content_ref", str, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceOriginDocument: TypeAlias = Any
else:
    SourceOriginDocument: Any = SOURCE_ORIGIN_CHARTER.generated_document()
    SourceOriginDocument.__name__ = "SourceOriginDocument"
    SourceOriginDocument.__qualname__ = "SourceOriginDocument"
    SourceOriginDocument.__module__ = __name__


class SourceTrustQuality(FamilyModel):
    pass


SOURCE_TRUST_QUALITY_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-trust-quality",
        name="source-trust-quality",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-trust-quality",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceTrustQuality,
            placement=FlatYamlPlacement(".derived/source-trust-quality", str),
        ),
        identity_field="status",
    ),
    model=SourceTrustQuality,
    fields=(
        CharterField("status", ProvenanceStatus, nullable=False, enum_type=ProvenanceStatus),
        CharterField("b", float | int, nullable=False),
        CharterField("d", float | int, nullable=False),
        CharterField("u", float | int, nullable=False),
        CharterField("a", float | int, nullable=False),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceTrustQualityDocument: TypeAlias = Any
else:
    SourceTrustQualityDocument: Any = SOURCE_TRUST_QUALITY_CHARTER.generated_document()
    SourceTrustQualityDocument.__name__ = "SourceTrustQualityDocument"
    SourceTrustQualityDocument.__qualname__ = "SourceTrustQualityDocument"
    SourceTrustQualityDocument.__module__ = __name__


class SourceTrust(FamilyModel):
    pass


SOURCE_TRUST_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-trust",
        name="source-trust",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-trust",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceTrust,
            placement=FlatYamlPlacement(".derived/source-trust", str),
        ),
        identity_field="status",
    ),
    model=SourceTrust,
    fields=(
        CharterField("status", ProvenanceStatus, nullable=False, enum_type=ProvenanceStatus),
        CharterField("prior_base_rate", Opinion, nullable=True),
        CharterField("quality", SourceTrustQualityDocument, nullable=True),
        CharterField("derived_from", tuple[str, ...], default=()),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceTrustDocument: TypeAlias = Any
else:
    SourceTrustDocument: Any = SOURCE_TRUST_CHARTER.generated_document()
    SourceTrustDocument.__name__ = "SourceTrustDocument"
    SourceTrustDocument.__qualname__ = "SourceTrustDocument"
    SourceTrustDocument.__module__ = __name__


class SourceMetadata(FamilyModel):
    pass


SOURCE_METADATA_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-metadata",
        name="source-metadata",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-metadata",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceMetadata,
            placement=FlatYamlPlacement(".derived/source-metadata", str),
        ),
        identity_field="name",
    ),
    model=SourceMetadata,
    fields=(CharterField("name", str, nullable=False),),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceMetadataDocument: TypeAlias = Any
else:
    SourceMetadataDocument: Any = SOURCE_METADATA_CHARTER.generated_document()
    SourceMetadataDocument.__name__ = "SourceMetadataDocument"
    SourceMetadataDocument.__qualname__ = "SourceMetadataDocument"
    SourceMetadataDocument.__module__ = __name__


class SourceParameterizationGroupMerge(FamilyModel):
    pass


SOURCE_PARAMETERIZATION_GROUP_MERGE_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-parameterization-group-merge",
        name="source-parameterization-group-merge",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-parameterization-group-merge",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceParameterizationGroupMerge,
            placement=FlatYamlPlacement(".derived/source-parameterization-group-merge", str),
        ),
        identity_field="merged_group",
    ),
    model=SourceParameterizationGroupMerge,
    fields=(
        CharterField("merged_group", tuple[str, ...], nullable=False),
        CharterField("previous_groups", tuple[tuple[str, ...], ...], nullable=False),
        CharterField("introduced_by", tuple[str, ...], nullable=False),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceParameterizationGroupMergeDocument: TypeAlias = Any
else:
    SourceParameterizationGroupMergeDocument: Any = (
        SOURCE_PARAMETERIZATION_GROUP_MERGE_CHARTER.generated_document()
    )
    SourceParameterizationGroupMergeDocument.__name__ = "SourceParameterizationGroupMergeDocument"
    SourceParameterizationGroupMergeDocument.__qualname__ = (
        "SourceParameterizationGroupMergeDocument"
    )
    SourceParameterizationGroupMergeDocument.__module__ = __name__


class SourceFinalizeCalibration(FamilyModel):
    pass


SOURCE_FINALIZE_CALIBRATION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-finalize-calibration",
        name="source-finalize-calibration",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-finalize-calibration",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceFinalizeCalibration,
            placement=FlatYamlPlacement(".derived/source-finalize-calibration", str),
        ),
        identity_field="prior_base_rate_status",
    ),
    model=SourceFinalizeCalibration,
    fields=(
        CharterField("prior_base_rate_status", str, nullable=False),
        CharterField("source_quality_status", str, nullable=False),
        CharterField("fallback_to_default_base_rate", bool, nullable=False),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceFinalizeCalibrationDocument: TypeAlias = Any
else:
    SourceFinalizeCalibrationDocument: Any = (
        SOURCE_FINALIZE_CALIBRATION_CHARTER.generated_document()
    )
    SourceFinalizeCalibrationDocument.__name__ = "SourceFinalizeCalibrationDocument"
    SourceFinalizeCalibrationDocument.__qualname__ = "SourceFinalizeCalibrationDocument"
    SourceFinalizeCalibrationDocument.__module__ = __name__


class SourceFinalizeReport(FamilyModel):
    pass


SOURCE_FINALIZE_REPORT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="source-finalize-report",
        name="source-finalize-report",
        contract_version=_SOURCE_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-source-finalize-report",
            contract_version=_SOURCE_CONTRACT_VERSION,
            doc_type=SourceFinalizeReport,
            placement=FlatYamlPlacement(".derived/source-finalize-report", str),
        ),
        identity_field="source",
    ),
    model=SourceFinalizeReport,
    fields=(
        CharterField("kind", str, nullable=False),
        CharterField("source", str, nullable=False),
        CharterField("status", str, nullable=False),
        CharterField("artifact_code_status", str, nullable=False),
        CharterField("calibration", SourceFinalizeCalibrationDocument, nullable=False),
        CharterField("micropub_status", str, default="not_composed"),
        CharterField("claim_reference_errors", tuple[str, ...], default=()),
        CharterField("micropub_coverage_errors", tuple[str, ...], default=()),
        CharterField("justification_reference_errors", tuple[str, ...], default=()),
        CharterField("stance_reference_errors", tuple[str, ...], default=()),
        CharterField("concept_alignment_candidates", tuple[str, ...], default=()),
        CharterField(
            "parameterization_group_merges",
            tuple[SourceParameterizationGroupMergeDocument, ...],
            default=(),
        ),
    ),
    semantic_metadata={"semantic": "propstore.source"},
)
if TYPE_CHECKING:
    SourceFinalizeReportDocument: TypeAlias = Any
else:
    SourceFinalizeReportDocument: Any = SOURCE_FINALIZE_REPORT_CHARTER.generated_document()
    SourceFinalizeReportDocument.__name__ = "SourceFinalizeReportDocument"
    SourceFinalizeReportDocument.__qualname__ = "SourceFinalizeReportDocument"
    SourceFinalizeReportDocument.__module__ = __name__


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
        origin: Any
        trust: Any
        metadata: Any | None = None
        artifact_code: str | None = None

else:
    SourceDocument: Any = SOURCE_CHARTER.generated_document()
    SourceDocument.__module__ = __name__


def source_document_payload(source_doc: SourceDocument) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": source_doc.id,
        "kind": source_doc.kind.value,
        "origin": document_to_payload(source_doc.origin),
        "trust": document_to_payload(source_doc.trust),
    }
    if source_doc.metadata is not None:
        payload["metadata"] = document_to_payload(source_doc.metadata)
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
