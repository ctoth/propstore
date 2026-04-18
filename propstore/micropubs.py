"""Micropublication artifact inspection workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from propstore.artifacts.documents.micropubs import (
    MicropublicationDocument,
    MicropublicationsFileDocument,
)
from propstore.artifacts.families import MICROPUBS_FILE_FAMILY
from propstore.artifacts.refs import MicropubsFileRef
from propstore.context_types import loaded_contexts_to_lifting_system
from propstore.repository import Repository
from propstore.validate_contexts import load_contexts


class MicropubNotFoundError(Exception):
    """Raised when a micropublication bundle or entry is absent."""


@dataclass(frozen=True)
class MicropubEntry:
    ref: MicropubsFileRef
    document: MicropublicationDocument


@dataclass(frozen=True)
class MicropubLiftReport:
    artifact_id: str
    source_context: str
    target_context: str
    liftable: bool


def load_micropub_bundle(repo: Repository, source: str) -> MicropublicationsFileDocument:
    document = repo.artifacts.load(MICROPUBS_FILE_FAMILY, MicropubsFileRef(source))
    if document is None:
        raise MicropubNotFoundError(f"Micropub bundle '{source}' not found.")
    return document


def iter_micropubs(repo: Repository) -> Iterator[MicropubEntry]:
    for ref in repo.artifacts.list(MICROPUBS_FILE_FAMILY):
        document = repo.artifacts.load(MICROPUBS_FILE_FAMILY, ref)
        if document is None:
            continue
        for entry in document.micropubs:
            yield MicropubEntry(ref=ref, document=entry)


def find_micropub(repo: Repository, artifact_id: str) -> MicropubEntry:
    for entry in iter_micropubs(repo):
        if entry.document.artifact_id == artifact_id:
            return entry
    raise MicropubNotFoundError(f"Micropub '{artifact_id}' not found.")


def inspect_micropub_lift(
    repo: Repository,
    artifact_id: str,
    *,
    target_context: str,
) -> MicropubLiftReport:
    entry = find_micropub(repo, artifact_id)
    system = loaded_contexts_to_lifting_system(load_contexts(repo.tree() / "contexts"))
    source_context = entry.document.context.id
    return MicropubLiftReport(
        artifact_id=artifact_id,
        source_context=source_context,
        target_context=target_context,
        liftable=system.can_lift(source_context, target_context),
    )
