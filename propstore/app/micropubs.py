"""Micropublication artifact inspection workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from propstore.families.documents.micropubs import (
    MicropublicationDocument,
    MicropublicationsFileDocument,
)
from propstore.families.registry import MicropubsFileRef
from propstore.context_types import (
    LoadedContext,
    loaded_contexts_to_lifting_system,
    parse_context_record_document,
)
from propstore.repository import Repository


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
    document = repo.families.micropubs.load(MicropubsFileRef(source))
    if document is None:
        raise MicropubNotFoundError(f"Micropub bundle '{source}' not found.")
    return document


def iter_micropubs(repo: Repository) -> Iterator[MicropubEntry]:
    for ref in repo.families.micropubs.iter():
        document = repo.families.micropubs.load(ref)
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
    tree = repo.tree()
    contexts = [
        LoadedContext(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_context_record_document(handle.document),
        )
        for ref in repo.families.contexts.iter()
        for handle in (repo.families.contexts.require_handle(ref),)
    ]
    system = loaded_contexts_to_lifting_system(contexts)
    source_context = entry.document.context.id
    return MicropubLiftReport(
        artifact_id=artifact_id,
        source_context=source_context,
        target_context=target_context,
        liftable=system.can_lift(source_context, target_context),
    )
