"""Predicate authoring workflows used by CLI adapters.

Each canonical predicate declaration is one ``PredicateDocument`` artifact
under ``predicates/<predicate-id>.yaml``. The optional ``--file`` CLI input is
retained only as authoring-group metadata; it does not determine canonical
storage identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from quire.documents import convert_document_value, encode_document

from propstore.families.documents.predicates import PredicateDocument
from propstore.families.registry import PredicateRef
from propstore.repository import Repository


class PredicateWorkflowError(Exception):
    """Raised when a predicate workflow cannot complete."""


_PREDICATE_MUTATION_LOCK = Lock()


class PredicateNotFoundError(PredicateWorkflowError):
    """Raised when a named predicate artifact is absent."""

    def __init__(self, predicate_id: str) -> None:
        super().__init__(f"Predicate '{predicate_id}' not found")
        self.predicate_id = predicate_id


@dataclass(frozen=True)
class PredicateAddRequest:
    """CLI request to declare a predicate artifact.

    Attributes:
        file: Optional authoring group carried into metadata. It never
            determines the canonical storage path.
        predicate_id: The predicate name (e.g. ``"aspirin_user"``).
        arity: Non-negative integer number of argument positions.
        arg_types: Tuple of length ``arity`` declaring per-position sorts.
        derived_from: Optional ``derived_from`` DSL string describing how
            propstore data materialises this predicate's ground atoms.
        description: Optional human-readable explanation.
    """

    file: str | None
    predicate_id: str
    arity: int
    arg_types: tuple[str, ...] = ()
    derived_from: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class PredicateAddReport:
    filepath: Path
    document: PredicateDocument
    created: bool


@dataclass(frozen=True)
class PredicateRemoveRequest:
    predicate_id: str


@dataclass(frozen=True)
class PredicateRemoveReport:
    filepath: Path
    predicate_id: str
    removed: bool


@dataclass(frozen=True)
class PredicateListItem:
    authoring_group: str | None
    predicate_id: str
    arity: int
    arg_types: tuple[str, ...]


@dataclass(frozen=True)
class PredicateShowReport:
    filepath: Path
    rendered: str


def _predicate_document_payload(request: PredicateAddRequest) -> dict[str, object]:
    data: dict[str, object] = {
        "id": request.predicate_id,
        "arity": request.arity,
    }
    if request.arg_types:
        data["arg_types"] = list(request.arg_types)
    if request.derived_from is not None:
        data["derived_from"] = request.derived_from
    if request.description is not None:
        data["description"] = request.description
    if request.file:
        data["authoring_group"] = request.file
    return data


def reject_predicate_document_conflicts(
    repo: Repository,
    *,
    commit: str | None,
    target_ref: PredicateRef,
    document: PredicateDocument,
) -> None:
    if document.id != target_ref.predicate_id:
        raise PredicateWorkflowError(
            f"predicate artifact id {target_ref.predicate_id!r} must match document id {document.id!r}"
        )

    existing = repo.families.predicates.load(target_ref, commit=commit)
    if existing is not None and existing.promoted_from_sha != document.promoted_from_sha:
        relpath = repo.families.predicates.address(target_ref).require_path()
        raise PredicateWorkflowError(
            f"predicate {document.id!r} already declared in {relpath}"
        )

    for handle in repo.families.predicates.iter_handles(commit=commit):
        if handle.ref == target_ref:
            continue
        if handle.document.id == document.id:
            relpath = handle.address.require_path()
            raise PredicateWorkflowError(
                f"predicate {document.id!r} already declared in {relpath}"
            )


def add_predicate(
    repo: Repository,
    request: PredicateAddRequest,
) -> PredicateAddReport:
    """Declare a predicate as ``predicates/<predicate-id>.yaml``."""

    if not isinstance(request.predicate_id, str) or not request.predicate_id:
        raise PredicateWorkflowError("predicate id must be a non-empty string")
    if request.arity < 0:
        raise PredicateWorkflowError(
            f"predicate {request.predicate_id!r}: arity must be >= 0, got {request.arity}"
        )
    if request.arg_types and len(request.arg_types) != request.arity:
        raise PredicateWorkflowError(
            f"predicate {request.predicate_id!r}: arg_types length "
            f"{len(request.arg_types)} does not match arity {request.arity}"
        )

    ref = PredicateRef(request.predicate_id)
    relpath = repo.families.predicates.address(ref).require_path()
    filepath = repo.root / relpath

    with _PREDICATE_MUTATION_LOCK, repo.head_bound_transaction(
        repo.snapshot.primary_branch_name(),
        path="predicate.add",
    ) as head_txn:
        if repo.families.predicates.load(ref, commit=head_txn.expected_head) is not None:
            raise PredicateWorkflowError(
                f"predicate {request.predicate_id!r} already declared in {relpath}"
            )

        document = convert_document_value(
            _predicate_document_payload(request),
            PredicateDocument,
            source=relpath,
        )
        reject_predicate_document_conflicts(
            repo,
            commit=head_txn.expected_head,
            target_ref=ref,
            document=document,
        )

        with head_txn.families_transact(
            message=f"Declare predicate {request.predicate_id}",
        ) as transaction:
            transaction.predicates.save(ref, document)

    return PredicateAddReport(
        filepath=filepath,
        document=document,
        created=True,
    )


def list_predicates(repo: Repository) -> tuple[PredicateListItem, ...]:
    items: list[PredicateListItem] = []
    for handle in repo.families.predicates.iter_handles():
        predicate = handle.document
        items.append(
            PredicateListItem(
                authoring_group=predicate.authoring_group,
                predicate_id=predicate.id,
                arity=predicate.arity,
                arg_types=tuple(predicate.arg_types),
            )
        )
    return tuple(sorted(items, key=lambda item: item.predicate_id))


def show_predicate(
    repo: Repository,
    predicate_id: str,
) -> PredicateShowReport:
    ref = PredicateRef(predicate_id)
    document = repo.families.predicates.load(ref)
    if document is None:
        raise PredicateNotFoundError(predicate_id)
    filepath = repo.root / repo.families.predicates.address(ref).require_path()
    return PredicateShowReport(
        filepath=filepath,
        rendered=encode_document(document).decode("utf-8"),
    )


def remove_predicate(
    repo: Repository,
    request: PredicateRemoveRequest,
) -> PredicateRemoveReport:
    """Remove a predicate artifact."""

    if not isinstance(request.predicate_id, str) or not request.predicate_id:
        raise PredicateWorkflowError("predicate id must be a non-empty string")

    ref = PredicateRef(request.predicate_id)
    with _PREDICATE_MUTATION_LOCK, repo.mutation_guard():
        existing = repo.families.predicates.load(ref)
        if existing is None:
            raise PredicateNotFoundError(request.predicate_id)

        filepath = repo.root / repo.families.predicates.address(ref).require_path()
        repo.families.predicates.delete(
            ref,
            message=f"Remove predicate {request.predicate_id}",
        )

    return PredicateRemoveReport(
        filepath=filepath,
        predicate_id=request.predicate_id,
        removed=True,
    )
