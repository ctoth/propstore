"""Application-layer context workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from propstore.families.contexts.documents import ContextDocument
from propstore.families.contexts.stages import LoadedContext, parse_context_record_document
from propstore.families.registry import ContextRef
from propstore.repository import Repository
from quire.documents import convert_document_value, encode_document


class ContextWorkflowError(Exception):
    """Raised when a context workflow cannot complete."""


class ContextNotFoundError(ContextWorkflowError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Context '{name}' not found")
        self.name = name


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


@dataclass(frozen=True)
class ContextShowReport:
    filepath: Path
    rendered: str


@dataclass(frozen=True)
class ContextSearchRequest:
    query: str
    limit: int = 20


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


def _validate_context_assumption_cel(
    repo: Repository,
    request: ContextAddRequest,
) -> None:
    """Reject assumptions referencing structural concepts before any write."""
    if not request.assumptions:
        return
    from propstore.cel_validation import (
        CelIngestValidationError,
        iter_context_assumption_expressions,
        validate_cel_expressions,
    )
    from propstore.compiler.context import build_compilation_context_from_repo

    registry = build_compilation_context_from_repo(repo).cel_registry
    if not registry:
        return
    try:
        validate_cel_expressions(
            iter_context_assumption_expressions(
                list(request.assumptions),
                artifact_label=f"context '{request.name}'",
            ),
            registry,
        )
    except CelIngestValidationError as exc:
        raise ContextWorkflowError(str(exc)) from exc


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

    _validate_context_assumption_cel(repo, request)

    source = f"dry-run:{relpath}" if dry_run else relpath
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
    items = [
        ContextListItem(
            context_id=_context_display_id(context),
            description=context.record.description or "",
            perspective=context.record.perspective,
        )
        for context in _loaded_contexts(repo)
    ]
    return tuple(items)


def search_context_items(
    repo: Repository,
    request: ContextSearchRequest,
) -> tuple[ContextListItem, ...]:
    items: list[ContextListItem] = []
    query = request.query.casefold()
    for item in list_context_items(repo):
        if query and not any(
            query in candidate.casefold()
            for candidate in (
                item.context_id,
                item.description,
                "" if item.perspective is None else item.perspective,
            )
        ):
            continue
        items.append(item)
        if len(items) >= request.limit:
            break
    return tuple(items)


def show_context(repo: Repository, name: str) -> ContextShowReport:
    ref, _loaded = _require_context(repo, name)
    filepath = repo.root / repo.families.contexts.address(ref).require_path()
    document = repo.families.contexts.require(ref)
    return ContextShowReport(
        filepath=filepath,
        rendered=encode_document(document).decode("utf-8"),
    )


def _loaded_contexts(repo: Repository) -> tuple[LoadedContext, ...]:
    items: list[LoadedContext] = []
    tree = repo.tree()
    for ref in repo.families.contexts.iter():
        handle = repo.families.contexts.require_handle(ref)
        items.append(
            LoadedContext(
                filename=ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
        )
    return tuple(items)


def _context_display_id(context: LoadedContext) -> str:
    return (
        context.filename
        if context.record.context_id is None
        else str(context.record.context_id)
    )


def _require_context(
    repo: Repository,
    name: str,
) -> tuple[ContextRef, LoadedContext]:
    for context in _loaded_contexts(repo):
        display_id = _context_display_id(context)
        if name not in {context.filename, display_id}:
            continue
        ref = ContextRef(context.filename)
        return ref, context
    raise ContextNotFoundError(name)
