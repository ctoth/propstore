"""Context authoring workflows used by CLI adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.artifacts.families import CONTEXT_FAMILY
from propstore.artifacts.refs import ContextRef
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES
from quire.documents import convert_document_value
from propstore.repository import Repository
from propstore.validate_contexts import load_contexts


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
    relpath = repo.artifacts.address(CONTEXT_FAMILY, ref).require_path()
    filepath = repo.root / relpath
    if (repo.tree() / relpath).exists():
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

    repo.artifacts.save(
        CONTEXT_FAMILY,
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
    for context in load_contexts(SEMANTIC_FAMILIES.root_path("context", repo.tree())):
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
