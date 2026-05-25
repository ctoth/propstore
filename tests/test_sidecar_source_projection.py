from __future__ import annotations

from pathlib import Path

from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.documents.sources import (
    SourceDocument,
    SourceOriginDocument,
    SourceTrustDocument,
    SourceTrustQualityDocument,
)
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.families.sources.declaration import (
    Source,
    SourceOrigin,
    SourceQuality,
    SourceTrust,
    compile_source_models,
)
from propstore.families.registry import world_schema


def test_source_models_round_trip_through_charter_session(tmp_path: Path) -> None:
    source = SourceDocument(
        id="source-alpha",
        kind=SourceKind.ACADEMIC_PAPER,
        origin=SourceOriginDocument(
            type=SourceOriginType.DOI,
            value="10.1000/example",
            retrieved="2026-05-14",
            content_ref="sha256:abc",
        ),
        trust=SourceTrustDocument(
            status=ProvenanceStatus.STATED,
            prior_base_rate=Opinion(b=0.2, d=0.1, u=0.7, a=0.5),
            quality=SourceTrustQualityDocument(
                status=ProvenanceStatus.STATED,
                b=0.8,
                d=0.05,
                u=0.15,
                a=0.5,
            ),
            derived_from=("seed-a", "seed-b"),
        ),
        artifact_code="sha256:source-alpha",
    )

    schema = world_schema()
    sources = compile_source_models((("alpha", source),))

    assert len(sources) == 1
    compiled = sources[0]
    assert compiled.slug == "alpha"
    assert compiled.source_id == "source-alpha"
    assert compiled.kind == "academic_paper"
    assert compiled.origin == SourceOrigin(
        type="doi",
        value="10.1000/example",
        retrieved="2026-05-14",
        content_ref="sha256:abc",
    )
    assert compiled.trust == SourceTrust(
        status="stated",
        prior_base_rate={"a": 0.5, "b": 0.2, "d": 0.1, "u": 0.7},
    )
    assert compiled.quality == SourceQuality(
        status="stated",
        b=0.8,
        d=0.05,
        u=0.15,
        a=0.5,
    )
    assert compiled.derived_from == ["seed-a", "seed-b"]
    assert compiled.artifact_code == "sha256:source-alpha"

    db_path = tmp_path / "source.sqlite"
    create_sqlalchemy_store(db_path, schema)

    with writable_session(db_path, schema) as session:
        session.add_all(sources)
        session.commit()

    with readonly_session(db_path, schema) as session:
        stored = session.get(Source, "alpha")

    assert stored is not None
    assert stored.artifact_code == "sha256:source-alpha"
    assert stored.origin == SourceOrigin(
        type="doi",
        value="10.1000/example",
        retrieved="2026-05-14",
        content_ref="sha256:abc",
    )
    assert stored.trust == SourceTrust(
        status="stated",
        prior_base_rate={"a": 0.5, "b": 0.2, "d": 0.1, "u": 0.7},
    )
    assert stored.quality == SourceQuality(
        status="stated",
        b=0.8,
        d=0.05,
        u=0.15,
        a=0.5,
    )
    assert stored.derived_from == ["seed-a", "seed-b"]
