from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

from propstore.artifacts import (
    SOURCE_CLAIMS_FAMILY,
    SOURCE_CONCEPTS_FAMILY,
    SOURCE_DOCUMENT_FAMILY,
    SOURCE_FINALIZE_REPORT_FAMILY,
    SOURCE_JUSTIFICATIONS_FAMILY,
    SOURCE_STANCES_FAMILY,
    SourceRef,
)

# Imported directly from ``propstore.artifacts.refs`` rather than via
# ``propstore.artifacts`` so pyright can statically resolve the
# re-exports in ``propstore.source.__init__``. ``propstore.artifacts``
# exposes these names through a lazy ``__getattr__`` dispatch table,
# which pyright types as ``object`` — transitive re-exports then fail
# analysis even though the runtime binding is correct (WS-Z-gates
# Phase 4 Deliverable 5: pyright cleanup).
from propstore.artifacts.refs import (
    normalize_source_slug,
    source_branch_name,
)
from propstore.artifacts.families import SOURCE_METADATA_FAMILY, SOURCE_NOTES_FAMILY
from propstore.repo.repository import Repository
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.provenance import ProvenanceStatus
from propstore.uri import ni_uri_for_file, source_tag_uri as mint_source_tag_uri

from propstore.artifacts.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceMetadataDocument,
    SourceOriginDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
    SourceTrustDocument,
    SourceTrustQualityDocument,
)

TDocument = TypeVar("TDocument")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def source_tag_uri(repo: Repository, name: str) -> str:
    return mint_source_tag_uri(name, authority=repo.uri_authority)


def initial_source_document(
    repo: Repository,
    name: str,
    *,
    kind: SourceKind,
    origin_type: SourceOriginType,
    origin_value: str,
    content_file: Path | None = None,
) -> SourceDocument:
    return SourceDocument(
        id=source_tag_uri(repo, name),
        kind=kind,
        origin=SourceOriginDocument(
            type=origin_type,
            value=origin_value,
            retrieved=utc_now(),
            content_ref=ni_uri_for_file(content_file) if content_file is not None else None,
        ),
        trust=SourceTrustDocument(
            status=ProvenanceStatus.DEFAULTED,
            prior_base_rate=0.5,
            quality=SourceTrustQualityDocument(
                status=ProvenanceStatus.VACUOUS,
                b=0.0,
                d=0.0,
                u=1.0,
                a=0.5,
            ),
            derived_from=(),
        ),
        metadata=SourceMetadataDocument(name=normalize_source_slug(name)),
    )


def load_document_from_branch(
    repo: Repository,
    branch: str,
    relpath: str,
    document_type: type[TDocument],
) -> TDocument | None:
    return repo.snapshot.read_document(relpath, document_type, branch=branch)


def init_source_branch(
    repo: Repository,
    name: str,
    *,
    kind: SourceKind,
    origin_type: SourceOriginType,
    origin_value: str,
    content_file: Path | None = None,
) -> str:
    branch = source_branch_name(name)
    repo.snapshot.ensure_branch(branch)
    source_doc = initial_source_document(
        repo,
        name,
        kind=kind,
        origin_type=origin_type,
        origin_value=origin_value,
        content_file=content_file,
    )
    repo.artifacts.save(
        SOURCE_DOCUMENT_FAMILY,
        SourceRef(name),
        source_doc,
        message=f"Initialize source {normalize_source_slug(name)}",
    )
    return branch


def commit_source_notes(repo: Repository, name: str, notes_file: Path) -> str:
    return repo.artifacts.save(
        SOURCE_NOTES_FAMILY,
        SourceRef(name),
        notes_file.read_text(encoding="utf-8"),
        message=f"Write notes for {normalize_source_slug(name)}",
    )


def commit_source_metadata(repo: Repository, name: str, metadata_file: Path) -> str:
    loaded = json.loads(metadata_file.read_text(encoding="utf-8"))
    return repo.artifacts.save(
        SOURCE_METADATA_FAMILY,
        SourceRef(name),
        loaded,
        message=f"Write metadata for {normalize_source_slug(name)}",
    )


def load_source_metadata(repo: Repository, name: str) -> dict[str, object] | None:
    return repo.artifacts.load(SOURCE_METADATA_FAMILY, SourceRef(name))


def load_source_document(repo: Repository, name: str) -> SourceDocument:
    branch = source_branch_name(name)
    document = repo.artifacts.load(SOURCE_DOCUMENT_FAMILY, SourceRef(name))
    if document is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    return document


def load_source_concepts_document(repo: Repository, name: str) -> SourceConceptsDocument | None:
    return repo.artifacts.load(SOURCE_CONCEPTS_FAMILY, SourceRef(name))


def load_source_claims_document(repo: Repository, name: str) -> SourceClaimsDocument | None:
    return repo.artifacts.load(SOURCE_CLAIMS_FAMILY, SourceRef(name))


def load_source_justifications_document(repo: Repository, name: str) -> SourceJustificationsDocument | None:
    return repo.artifacts.load(SOURCE_JUSTIFICATIONS_FAMILY, SourceRef(name))


def load_source_stances_document(repo: Repository, name: str) -> SourceStancesDocument | None:
    return repo.artifacts.load(SOURCE_STANCES_FAMILY, SourceRef(name))


def load_source_finalize_report(repo: Repository, name: str) -> SourceFinalizeReportDocument | None:
    return repo.artifacts.load(SOURCE_FINALIZE_REPORT_FAMILY, SourceRef(name))
