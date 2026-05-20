"""Source charter and derived-store model helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter
from quire.families import FamilyDefinition
from quire.versions import VersionId

from propstore.families.documents.sources import SourceDocument


_SOURCE_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


@dataclass(frozen=True)
class SourceOrigin:
    type: str
    value: str
    retrieved: str | None = None
    content_ref: str | None = None


@dataclass(frozen=True)
class SourceTrust:
    status: str
    prior_base_rate: dict[str, float] | None = None


@dataclass(frozen=True)
class SourceQuality:
    status: str
    b: float
    d: float
    u: float
    a: float


class Source:
    def __init__(self, **values: object) -> None:
        for key, value in values.items():
            setattr(self, key, value)


def source_charter() -> FamilyCharter:
    return FamilyCharter(
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
            CharterField("slug", str, primary_key=True, nullable=False),
            CharterField("source_id", str, nullable=False),
            CharterField("kind", str, nullable=False),
            CharterField("origin", SourceOrigin, json_value_object=True),
            CharterField("trust", SourceTrust, json_value_object=True),
            CharterField("quality", SourceQuality, json_value_object=True),
            CharterField("derived_from", list, json_value_object=True),
            CharterField("artifact_code", str),
        ),
        indexes=(CharterIndex("idx_source_source_id", ("source_id",)),),
        semantic_metadata={"semantic": "propstore.world"},
    )


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
                origin=SourceOrigin(
                    type=origin.type.value,
                    value=origin.value,
                    retrieved=origin.retrieved,
                    content_ref=origin.content_ref,
                ),
                trust=SourceTrust(
                    status=trust.status.value,
                    prior_base_rate=_opinion_payload(trust.prior_base_rate),
                ),
                quality=(
                    None
                    if trust.quality is None
                    else SourceQuality(
                        status=trust.quality.status.value,
                        b=float(trust.quality.b),
                        d=float(trust.quality.d),
                        u=float(trust.quality.u),
                        a=float(trust.quality.a),
                    )
                ),
                derived_from=list(trust.derived_from) if trust.derived_from else None,
                artifact_code=source_doc.artifact_code,
            )
        )
    return tuple(source_models)


def _opinion_payload(opinion: Any) -> dict[str, float] | None:
    if opinion is None:
        return None
    return {
        "b": float(opinion.b),
        "d": float(opinion.d),
        "u": float(opinion.u),
        "a": float(opinion.a),
    }
