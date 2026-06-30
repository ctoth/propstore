"""Source-branch lifecycle primitives.

Every source-authoring function takes a :class:`~propstore.repository.Repository`
and writes to the source branch ``source/<stem>`` through the bound family
registry (``repo.families.source_*``) or, for the two opaque side files
(``notes.md`` / ``metadata.json``), through a direct git commit on that branch.
Nothing here gates a write: a proposal flows into the source branch with its
provenance and becomes queryable immediately (CLAUDE.md non-commitment).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import msgspec

from quire.git_store import HeadMismatchError

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.registry import SOURCE_BRANCH, SourceRef
from propstore.families.sources import (
    ClaimSourceDocument,
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceMetadataDocument,
    SourceMicropublicationsDocument,
    SourceOriginDocument,
    SourceStancesDocument,
    SourceTrustDocument,
)
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.uri import ni_uri_for_file
from propstore.uri import source_tag_uri as _mint_source_tag_uri

_NOTES_FILENAME = "notes.md"
_METADATA_FILENAME = "metadata.json"


def is_stale_branch_error(exc: ValueError) -> bool:
    """Whether a git write failed because its expected branch head is stale."""

    return isinstance(exc, HeadMismatchError)


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 ``...Z`` timestamp."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_source_slug(name: str) -> str:
    """Reduce *name* to a safe slug (alphanumerics plus ``_-.``).

    Used for the source's logical namespace and concept-slug derivation, where
    ambiguity detection relies on the plain safe-slug collapsing variants to one
    stem. Distinct from :func:`source_paper_slug`, which must match the branch
    stem exactly (including its collision suffix).
    """

    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip()
    )
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_paper_slug(name: str) -> str:
    """Return the paper-scoped filesystem stem for a source name.

    Matches :data:`SOURCE_BRANCH`'s stem so the master-branch artifact filename
    (e.g. ``claims/<stem>.yaml``) shares one logical id with the source branch
    ``source/<stem>``. When the safe-slug transform changes any character, a full
    sha256 digest is appended for disambiguation — the same rule
    :class:`~quire.artifacts.BranchPlacement` applies for ``collision_suffix``.
    """

    stripped = name.strip()
    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in stripped
    )
    cleaned = cleaned.strip("._-")
    if not cleaned:
        return "source"
    if cleaned != stripped:
        digest = hashlib.sha256(stripped.encode("utf-8")).hexdigest()
        return f"{cleaned}--{digest}"
    return cleaned


def source_branch_name(name: str) -> str:
    """Return the source branch name (``source/<stem>``) for *name*."""

    return SOURCE_BRANCH.branch_name(object(), SourceRef(name))


def source_tag_uri(repo: Repository, name: str) -> str:
    """Mint the canonical ``tag:`` URI identifying the source *name*."""

    return _mint_source_tag_uri(name, authority=repo.uri_authority)


def current_source_branch_head(repo: Repository, name: str) -> str | None:
    """Read the live source-branch head sha directly from git.

    ``Repository.snapshot`` is cached per instance, so source-local
    compare-and-swap retries must ask the git backend for the live ref.
    """

    git = repo.git
    if git is None:
        return None
    return git.branch_sha(source_branch_name(name))


def initial_source_document(
    repo: Repository,
    name: str,
    *,
    kind: SourceKind,
    origin_type: SourceOriginType,
    origin_value: str,
    content_file: Path | None = None,
) -> SourceDocument:
    """Build the initial manifest for a new source branch."""

    return SourceDocument(
        id=source_tag_uri(repo, name),
        kind=kind,
        origin=SourceOriginDocument(
            type=origin_type.value,
            value=origin_value,
            retrieved=utc_now(),
            content_ref=(
                ni_uri_for_file(content_file) if content_file is not None else None
            ),
        ),
        trust=SourceTrustDocument(status=ProvenanceStatus.DEFAULTED, derived_from=()),
        metadata=SourceMetadataDocument(name=normalize_source_slug(name)),
    )


def init_source_branch(
    repo: Repository,
    name: str,
    *,
    kind: SourceKind,
    origin_type: SourceOriginType,
    origin_value: str,
    content_file: Path | None = None,
) -> str:
    """Create the source branch (if absent) and write its manifest.

    Returns the branch name. Idempotent on the branch: re-initializing an
    existing source rewrites its ``source.yaml`` manifest.
    """

    branch = source_branch_name(name)
    git = repo.git
    if git is None:
        raise ValueError("source branches require a git-backed repository")
    if git.branch_sha(branch) is None:
        git.create_branch(branch)
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
    """Write a source branch's ``notes.md`` from *notes_file*; return commit sha."""

    branch = source_branch_name(name)
    payload = notes_file.read_text(encoding="utf-8").encode("utf-8")
    return repo.require_git().commit_batch(
        adds={_NOTES_FILENAME: payload},
        deletes=[],
        message=f"Write notes for {normalize_source_slug(name)}",
        branch=branch,
    )


def commit_source_metadata(repo: Repository, name: str, metadata_file: Path) -> str:
    """Write a source branch's ``metadata.json`` from *metadata_file*."""

    branch = source_branch_name(name)
    payload = metadata_file.read_bytes()
    # Validate it is JSON before committing (fail fast, do not store garbage).
    json.loads(payload.decode("utf-8"))
    return repo.require_git().commit_batch(
        adds={_METADATA_FILENAME: payload},
        deletes=[],
        message=f"Write metadata for {normalize_source_slug(name)}",
        branch=branch,
    )


def load_source_metadata(repo: Repository, name: str) -> dict[str, object] | None:
    """Read a source branch's ``metadata.json`` as a dict, or ``None``."""

    git = repo.git
    if git is None:
        return None
    branch_sha = git.branch_sha(source_branch_name(name))
    if branch_sha is None:
        return None
    try:
        payload = git.read_file(_METADATA_FILENAME, commit=branch_sha)
    except FileNotFoundError:
        return None
    return msgspec.json.decode(payload, type=dict[str, object])


def load_source_notes(repo: Repository, name: str) -> str | None:
    """Read a source branch's ``notes.md`` text, or ``None``."""

    git = repo.git
    if git is None:
        return None
    branch_sha = git.branch_sha(source_branch_name(name))
    if branch_sha is None:
        return None
    try:
        payload = git.read_file(_NOTES_FILENAME, commit=branch_sha)
    except FileNotFoundError:
        return None
    return payload.decode("utf-8")


def load_source_document(repo: Repository, name: str) -> SourceDocument:
    """Load a source branch's manifest; raise if the branch does not exist."""

    document = repo.families.source_documents.load(SourceRef(name))
    if document is None:
        raise ValueError(f"Source branch {source_branch_name(name)!r} does not exist")
    return document


def load_source_concepts_document(
    repo: Repository, name: str
) -> SourceConceptsDocument | None:
    return repo.families.source_concepts.load(SourceRef(name))


def load_source_claims_document(
    repo: Repository, name: str
) -> SourceClaimsDocument | None:
    return repo.families.source_claims.load(SourceRef(name))


def load_source_stances_document(
    repo: Repository, name: str
) -> SourceStancesDocument | None:
    return repo.families.source_stances.load(SourceRef(name))


def load_source_justifications_document(
    repo: Repository, name: str
) -> SourceJustificationsDocument | None:
    return repo.families.source_justifications.load(SourceRef(name))


def load_source_micropubs_document(
    repo: Repository, name: str
) -> SourceMicropublicationsDocument | None:
    return repo.families.source_micropubs.load(SourceRef(name))


def load_source_finalize_report(
    repo: Repository, name: str
) -> SourceFinalizeReportDocument | None:
    return repo.families.source_finalize_reports.load(SourceRef(name))


# Re-export so ``ClaimSourceDocument`` (used by source/claims.py and
# source/relations.py to stamp the per-batch ``source.paper``) has one import
# site alongside the other source loaders.
__all__ = [
    "ClaimSourceDocument",
    "commit_source_metadata",
    "commit_source_notes",
    "current_source_branch_head",
    "init_source_branch",
    "initial_source_document",
    "is_stale_branch_error",
    "load_source_claims_document",
    "load_source_concepts_document",
    "load_source_document",
    "load_source_finalize_report",
    "load_source_justifications_document",
    "load_source_metadata",
    "load_source_micropubs_document",
    "load_source_notes",
    "load_source_stances_document",
    "normalize_source_slug",
    "source_branch_name",
    "source_paper_slug",
    "source_tag_uri",
    "utc_now",
]
