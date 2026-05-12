"""Micropublication artifact inspection workflows."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.registry import MicropublicationRef
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
    ref: MicropublicationRef
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
    artifact_id: str
    context_id: str
    source: str | None


def find_micropub(repo: Repository, artifact_id: str) -> MicropubEntry:
    ref = MicropublicationRef(artifact_id)
    document = repo.families.micropubs.load(ref)
    if document is not None:
        return MicropubEntry(ref=ref, document=document)
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
            artifact_id=handle.document.artifact_id,
            context_id=handle.document.context.id,
            source=handle.document.source,
        )
        for handle in repo.families.micropubs.iter_handles()
    )
