from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar, cast

from propstore.families.registry import SOURCE_DOCUMENT_FAMILY, SourceRef
from propstore.repository import Repository
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.provenance import ProvenanceStatus
from propstore.uri import ni_uri_for_file, source_tag_uri as mint_source_tag_uri

from propstore.families.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceMetadataDocument,
    SourceOriginDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
    SourceTrustDocument,
)
from propstore.families.documents.micropubs import MicropublicationsFileDocument

TDocument = TypeVar("TDocument")


def normalize_source_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_paper_slug(name: str) -> str:
    """Return the paper-scoped filesystem stem for a source name.

    Must match ``SourceBranchPlacement.branch_name``'s stem
    (``propstore/families/registry.py::SourceBranchPlacement``) so that
    the master-branch artifact filename (e.g. ``claims/<stem>.yaml``)
    shares one logical id with the source branch ``source/<stem>``.
    When the safe-slug transform changes any character, the branch
    placement appends a 12-char sha1 digest for disambiguation; this
    helper does the same.

    Distinct from ``normalize_source_slug``: the latter is also used
    for concept-slug derivation where ambiguity detection relies on
    the plain safe-slug collapsing non-ascii variants to one stem
    (e.g. ``"novel concept"`` → ``"novel_concept"`` must collide with
    a pre-existing master ``novel_concept`` concept).

    Prior behavior re-used ``normalize_source_slug`` for paper slugs,
    which disagreed with the branch stem whenever the input had
    characters like U+2010 HYPHEN — producing duplicate master files
    under two different stems. See ``tests/test_source_promotion_alignment.py::
    test_normalize_source_slug_matches_source_branch_stem_for_unicode_name``.
    """

    stripped = name.strip()
    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in stripped
    )
    cleaned = cleaned.strip("._-")
    if not cleaned:
        return "source"
    if cleaned != stripped:
        digest = hashlib.sha1(stripped.encode("utf-8")).hexdigest()[:12]
        return f"{cleaned}--{digest}"
    return cleaned


def source_branch_name(name: str) -> str:
    return SOURCE_DOCUMENT_FAMILY.address_for(cast(Repository, object()), SourceRef(name)).branch


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
    repo.families.source_documents.save(
        SourceRef(name),
        source_doc,
        message=f"Initialize source {normalize_source_slug(name)}",
    )
    return branch


def commit_source_notes(repo: Repository, name: str, notes_file: Path) -> str:
    return repo.families.source_notes.save(
        SourceRef(name),
        notes_file.read_text(encoding="utf-8"),
        message=f"Write notes for {normalize_source_slug(name)}",
    )


def commit_source_metadata(repo: Repository, name: str, metadata_file: Path) -> str:
    loaded = json.loads(metadata_file.read_text(encoding="utf-8"))
    return repo.families.source_metadata.save(
        SourceRef(name),
        loaded,
        message=f"Write metadata for {normalize_source_slug(name)}",
    )


def load_source_metadata(repo: Repository, name: str) -> dict[str, object] | None:
    return repo.families.source_metadata.load(SourceRef(name))


def load_source_document(repo: Repository, name: str) -> SourceDocument:
    branch = source_branch_name(name)
    document = repo.families.source_documents.load(SourceRef(name))
    if document is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    return document


def load_source_concepts_document(repo: Repository, name: str) -> SourceConceptsDocument | None:
    return repo.families.source_concepts.load(SourceRef(name))


def load_source_claims_document(repo: Repository, name: str) -> SourceClaimsDocument | None:
    return repo.families.source_claims.load(SourceRef(name))


def load_source_micropubs_document(repo: Repository, name: str) -> MicropublicationsFileDocument | None:
    return repo.families.source_micropubs.load(SourceRef(name))


def load_source_justifications_document(repo: Repository, name: str) -> SourceJustificationsDocument | None:
    return repo.families.source_justifications.load(SourceRef(name))


def load_source_stances_document(repo: Repository, name: str) -> SourceStancesDocument | None:
    return repo.families.source_stances.load(SourceRef(name))


def load_source_finalize_report(repo: Repository, name: str) -> SourceFinalizeReportDocument | None:
    return repo.families.source_finalize_reports.load(SourceRef(name))
