"""Source family declarative charter classes, documents, and helpers.

Each charter is a declarative ``@charter`` class: the class IS the typed
document, and ``@charter`` derives the :class:`~quire.charters.FamilyCharter`
plus the SQLAlchemy model from it. Nested embedded documents are declared
before their containers (``SourceTrustQualityDocument`` before
``SourceTrustDocument`` before ``SourceDocument``;
``SourceFinalizeCalibrationDocument`` and
``SourceParameterizationGroupMergeDocument`` before
``SourceFinalizeReportDocument``).

``compile_source_models`` stays as the module-level source model compiler.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated

from quire.charter_class import CharterDoc, charter, charter_field, column
from quire.charters import CharterIndex, FamilyCharter, FamilyModel

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus


_SOURCE_CONTRACT_VERSION = "2026.05.25"


if TYPE_CHECKING:
    # ``@charter`` generates this SQLAlchemy-mappable model at runtime (via
    # ``model_name="Source"``) and binds it into this module's namespace. The
    # static stub lets ``compile_source_models`` type-check ``Source(...)``
    # construction and attribute access; the runtime class replaces it.
    class Source(FamilyModel): ...


@charter(
    key="source-origin",
    name="source-origin",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-origin",
    identity_field="value",
    semantic="propstore.source",
    artifact_family_name="propstore-source-origin",
    model_name="SourceOrigin",
)
class SourceOriginDocument(CharterDoc):
    type: Annotated[SourceOriginType, charter_field(enum_type=SourceOriginType)]
    value: str
    retrieved: str | None = None
    content_ref: str | None = None


@charter(
    key="source-trust-quality",
    name="source-trust-quality",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-trust-quality",
    identity_field="status",
    semantic="propstore.source",
    artifact_family_name="propstore-source-trust-quality",
    model_name="SourceTrustQuality",
)
class SourceTrustQualityDocument(CharterDoc):
    status: Annotated[ProvenanceStatus, charter_field(enum_type=ProvenanceStatus)]
    b: float | int
    d: float | int
    u: float | int
    a: float | int


@charter(
    key="source-trust",
    name="source-trust",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-trust",
    identity_field="status",
    semantic="propstore.source",
    artifact_family_name="propstore-source-trust",
    model_name="SourceTrust",
)
class SourceTrustDocument(CharterDoc):
    status: Annotated[ProvenanceStatus, charter_field(enum_type=ProvenanceStatus)]
    prior_base_rate: Opinion | None = None
    quality: SourceTrustQualityDocument | None = None
    derived_from: Annotated[tuple[str, ...], charter_field(nullable=True)] = ()


@charter(
    key="source-metadata",
    name="source-metadata",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-metadata",
    identity_field="name",
    semantic="propstore.source",
    artifact_family_name="propstore-source-metadata",
    model_name="SourceMetadata",
)
class SourceMetadataDocument(CharterDoc):
    name: str


@charter(
    key="source-parameterization-group-merge",
    name="source-parameterization-group-merge",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-parameterization-group-merge",
    identity_field="merged_group",
    semantic="propstore.source",
    artifact_family_name="propstore-source-parameterization-group-merge",
    model_name="SourceParameterizationGroupMerge",
)
class SourceParameterizationGroupMergeDocument(CharterDoc):
    merged_group: tuple[str, ...]
    previous_groups: tuple[tuple[str, ...], ...]
    introduced_by: tuple[str, ...]


@charter(
    key="source-finalize-calibration",
    name="source-finalize-calibration",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-finalize-calibration",
    identity_field="prior_base_rate_status",
    semantic="propstore.source",
    artifact_family_name="propstore-source-finalize-calibration",
    model_name="SourceFinalizeCalibration",
)
class SourceFinalizeCalibrationDocument(CharterDoc):
    prior_base_rate_status: str
    source_quality_status: str
    fallback_to_default_base_rate: bool


@charter(
    key="source-finalize-report",
    name="source-finalize-report",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source-finalize-report",
    identity_field="source",
    semantic="propstore.source",
    artifact_family_name="propstore-source-finalize-report",
    model_name="SourceFinalizeReport",
)
class SourceFinalizeReportDocument(CharterDoc):
    kind: str
    source: str
    status: str
    artifact_code_status: str
    calibration: SourceFinalizeCalibrationDocument
    micropub_status: Annotated[str, charter_field(nullable=True)] = "not_composed"
    claim_reference_errors: Annotated[
        tuple[str, ...], charter_field(nullable=True)
    ] = ()
    micropub_coverage_errors: Annotated[
        tuple[str, ...], charter_field(nullable=True)
    ] = ()
    justification_reference_errors: Annotated[
        tuple[str, ...], charter_field(nullable=True)
    ] = ()
    stance_reference_errors: Annotated[
        tuple[str, ...], charter_field(nullable=True)
    ] = ()
    concept_alignment_candidates: Annotated[
        tuple[str, ...], charter_field(nullable=True)
    ] = ()
    parameterization_group_merges: Annotated[
        tuple[SourceParameterizationGroupMergeDocument, ...],
        charter_field(nullable=True),
    ] = ()


@charter(
    key="source",
    name="source",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=".derived/source",
    identity_field="slug",
    semantic="propstore.world",
    artifact_family_name="propstore-world-source",
    model_name="Source",
    indexes=(CharterIndex("idx_source_source_id", ("source_id",)),),
    extra_columns=(
        column("slug", str, primary_key=True),
        column("quality", SourceTrustQualityDocument, json=True, nullable=True),
        column("derived_from", list, json=True, nullable=True),
    ),
)
class SourceDocument(CharterDoc):
    id: Annotated[str, charter_field(column_name="source_id")]
    kind: SourceKind
    origin: Annotated[SourceOriginDocument, charter_field(json=True, nullable=True)]
    trust: Annotated[SourceTrustDocument, charter_field(json=True, nullable=True)]
    metadata: Annotated[SourceMetadataDocument | None, charter_field(json=True)] = None
    artifact_code: Annotated[str | None, charter_field(artifact=True)] = None


SOURCE_ORIGIN_CHARTER: FamilyCharter = SourceOriginDocument.__charter__
SOURCE_TRUST_QUALITY_CHARTER: FamilyCharter = SourceTrustQualityDocument.__charter__
SOURCE_TRUST_CHARTER: FamilyCharter = SourceTrustDocument.__charter__
SOURCE_METADATA_CHARTER: FamilyCharter = SourceMetadataDocument.__charter__
SOURCE_PARAMETERIZATION_GROUP_MERGE_CHARTER: FamilyCharter = (
    SourceParameterizationGroupMergeDocument.__charter__
)
SOURCE_FINALIZE_CALIBRATION_CHARTER: FamilyCharter = (
    SourceFinalizeCalibrationDocument.__charter__
)
SOURCE_FINALIZE_REPORT_CHARTER: FamilyCharter = SourceFinalizeReportDocument.__charter__
SOURCE_CHARTER: FamilyCharter = SourceDocument.__charter__


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
                quality=(None if trust.quality is None else trust.quality),
                derived_from=list(trust.derived_from) if trust.derived_from else None,
                artifact_code=source_doc.artifact_code,
            )
        )
    return tuple(source_models)
