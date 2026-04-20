"""Context authoring workflows used by CLI adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.families.registry import ContextRef
from propstore.families.contexts.documents import ContextDocument
from quire.documents import convert_document_value
from propstore.families.contexts.stages import (
    LoadedContext,
    parse_context_record_document,
)
from propstore.repository import Repository


class ContextWorkflowError(Exception):
    """Raised when a context workflow cannot complete."""


@dataclass(frozen=True)
class ContextAddRequest:
    name: str
    description: str
    assumptions: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    perspective: str | None = None


@dataclass(frozen=True)
class ContextAddReport:
    filepath: Path
    document: ContextDocument
    created: bool


@dataclass(frozen=True)
class ContextListItem:
    context_id: str
    description: str
    perspective: str | None


def _parse_parameters(parameters: tuple[str, ...]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_parameter in parameters:
        key, sep, value = raw_parameter.partition("=")
        if not sep or not key or not value:
            raise ContextWorkflowError(
                f"Context parameter '{raw_parameter}' must be KEY=VALUE"
            )
        parsed[key] = value
    return parsed


def _context_document_payload(request: ContextAddRequest) -> dict[str, object]:
    data: dict[str, object] = {
        "id": request.name,
        "name": request.name,
        "description": request.description,
    }
    structure: dict[str, object] = {}
    if request.assumptions:
        structure["assumptions"] = list(request.assumptions)
    parameters = _parse_parameters(request.parameters)
    if parameters:
        structure["parameters"] = parameters
    if request.perspective:
        structure["perspective"] = request.perspective
    if structure:
        data["structure"] = structure
    return data


def add_context(
    repo: Repository,
    request: ContextAddRequest,
    *,
    dry_run: bool,
) -> ContextAddReport:
    ref = ContextRef(request.name)
    relpath = repo.families.contexts.family.address_for(repo, ref).require_path()
    filepath = repo.root / relpath
    if repo.families.contexts.load(ref) is not None:
        raise ContextWorkflowError(f"Context file '{filepath}' already exists")

    source = (
        f"dry-run:{relpath}"
        if dry_run
        else relpath
    )
    document = convert_document_value(
        _context_document_payload(request),
        ContextDocument,
        source=source,
    )
    if dry_run:
        return ContextAddReport(
            filepath=filepath,
            document=document,
            created=False,
        )

    repo.families.contexts.save(
        ref,
        document,
        message=f"Add context: {request.name}",
    )
    repo.snapshot.sync_worktree()
    return ContextAddReport(
        filepath=filepath,
        document=document,
        created=True,
    )


def list_context_items(repo: Repository) -> tuple[ContextListItem, ...]:
    items: list[ContextListItem] = []
    tree = repo.tree()
    for ref in repo.families.contexts.iter():
        handle = repo.families.contexts.require_handle(ref)
        context = LoadedContext(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_context_record_document(handle.document),
        )
        record = context.record
        context_id = context.filename if record.context_id is None else str(record.context_id)
        items.append(
            ContextListItem(
                context_id=context_id,
                description=record.description or "",
                perspective=record.perspective,
            )
        )
    return tuple(items)
