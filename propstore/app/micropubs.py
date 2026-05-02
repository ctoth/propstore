"""Micropublication artifact inspection workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from propstore.families.documents.micropubs import (
    MicropublicationDocument,
    MicropublicationsFileDocument,
)
from propstore.families.registry import MicropubsFileRef
from propstore.families.contexts.stages import (
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
class MicropubLiftDecisionItem:
    proposition_id: str
    rule_id: str
    status: str
    mode: str
    exception_id: str | None = None
    justification: str | None = None


@dataclass(frozen=True)
class MicropubLiftReport:
    artifact_id: str
    source_context: str
    target_context: str
    decisions: tuple[MicropubLiftDecisionItem, ...]


@dataclass(frozen=True)
class MicropubListItem:
    bundle: str
    artifact_id: str
    context_id: str


def load_micropub_bundle(repo: Repository, source: str) -> MicropublicationsFileDocument:
    document = repo.families.micropubs.load(MicropubsFileRef(source))
    if document is None:
        raise MicropubNotFoundError(f"Micropub bundle '{source}' not found.")
    return document


def iter_micropubs(repo: Repository) -> Iterator[MicropubEntry]:
    for handle in repo.families.micropubs.iter_handles():
        document = handle.document
        for entry in document.micropubs:
            yield MicropubEntry(ref=handle.ref, document=entry)


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
            filename=handle.ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_context_record_document(handle.document),
        )
        for handle in repo.families.contexts.iter_handles()
    ]
    system = loaded_contexts_to_lifting_system(contexts)
    source_context = entry.document.context.id
    decisions = tuple(
        MicropubLiftDecisionItem(
            proposition_id=claim_id,
            rule_id=decision.rule_id,
            status=decision.status.value,
            mode=decision.mode.value,
            exception_id=decision.provenance.exception_id,
            justification=decision.provenance.justification,
        )
        for claim_id in entry.document.claims
        for decision in system.lift_decisions_between(
            source_context,
            target_context,
            claim_id,
        )
    )
    return MicropubLiftReport(
        artifact_id=artifact_id,
        source_context=source_context,
        target_context=target_context,
        decisions=decisions,
    )


def list_micropubs(repo: Repository) -> tuple[MicropubListItem, ...]:
    return tuple(
        MicropubListItem(
            bundle=entry.ref.name,
            artifact_id=entry.document.artifact_id,
            context_id=entry.document.context.id,
        )
        for entry in iter_micropubs(repo)
    )
