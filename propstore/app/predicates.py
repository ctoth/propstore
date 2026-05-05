"""Predicate authoring workflows used by CLI adapters.

Declares DeLP/Datalog predicates into ``knowledge/predicates/<name>.yaml``
files. Mirrors the context-authoring workflow pattern
(``propstore.app.contexts``) and uses the existing
``PREDICATE_FILE_FAMILY`` plumbing so predicates appear on the primary
branch alongside other canonical artifacts.

Theoretical source:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog. §3-4: a Datalog schema is a set of
    declared predicates indexed by id; each predicate fixes its arity
    and per-position argument type.

    Garcia & Simari 2004 §3 p.3-4: predicate symbols have a fixed
    arity; ground literals substitute variables with constants of
    matching sort.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from quire.documents import convert_document_value, encode_document

from propstore.families.documents.predicates import (
    PredicateDocument,
    PredicatesFileDocument,
)
from propstore.families.registry import PredicateFileRef
from propstore.repository import Repository


class PredicateWorkflowError(Exception):
    """Raised when a predicate workflow cannot complete."""


_PREDICATE_MUTATION_LOCK = Lock()


class PredicateFileNotFoundError(PredicateWorkflowError):
    def __init__(self, file: str) -> None:
        super().__init__(f"Predicate file '{file}' not found")
        self.file = file


class PredicateNotFoundError(PredicateWorkflowError):
    """Raised when a named predicate id is absent from a predicates file."""

    def __init__(self, file: str, predicate_id: str) -> None:
        super().__init__(
            f"Predicate '{predicate_id}' not found in predicates file '{file}'"
        )
        self.file = file
        self.predicate_id = predicate_id


@dataclass(frozen=True)
class PredicateAddRequest:
    """CLI request to declare a predicate in ``predicates/<file>.yaml``.

    The authored YAML is a ``PredicatesFileDocument`` envelope with a
    flat, ordered tuple of ``PredicateDocument`` entries. Authoring order
    is preserved because Diller, Borg, Bex 2025 §3 builds the Datalog
    schema in declaration order.

    Attributes:
        file: File stem (e.g. ``"ikeda_2014"``) — determines the target
            YAML path ``predicates/<file>.yaml``.
        predicate_id: The predicate name (e.g. ``"aspirin_user"``).
        arity: Non-negative integer number of argument positions.
        arg_types: Tuple of length ``arity`` declaring per-position
            sorts.
        derived_from: Optional ``derived_from`` DSL string describing how
            propstore data materialises this predicate's ground atoms.
        description: Optional human-readable explanation.
    """

    file: str
    predicate_id: str
    arity: int
    arg_types: tuple[str, ...] = ()
    derived_from: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class PredicateAddReport:
    filepath: Path
    document: PredicatesFileDocument
    created: bool
    """``True`` when the file was newly created; ``False`` when an
    existing predicates file was extended with an additional entry."""


@dataclass(frozen=True)
class PredicateRemoveRequest:
    """CLI request to remove a predicate from ``predicates/<file>.yaml``.

    Attributes:
        file: File stem (e.g. ``"ikeda_2014"``).
        predicate_id: Predicate name to remove.
    """

    file: str
    predicate_id: str


@dataclass(frozen=True)
class PredicateRemoveReport:
    filepath: Path
    predicate_id: str
    removed: bool


@dataclass(frozen=True)
class PredicateListItem:
    file: str
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
    return data


def _predicate_files_by_ref_at_head(
    repo: Repository,
    commit: str | None,
) -> dict[PredicateFileRef, PredicatesFileDocument]:
    return {
        handle.ref: handle.document
        for handle in repo.families.predicates.iter_handles(commit=commit)
    }


def _reject_global_duplicate_predicate_id(
    files: dict[PredicateFileRef, PredicatesFileDocument],
    *,
    target_ref: PredicateFileRef,
    predicate_id: str,
) -> None:
    for ref, document in files.items():
        if ref == target_ref:
            continue
        for entry in document.predicates:
            if entry.id == predicate_id:
                relpath = f"predicates/{ref.name}.yaml"
                raise PredicateWorkflowError(
                    f"predicate {predicate_id!r} already declared in {relpath}"
                )


def reject_predicate_document_conflicts(
    repo: Repository,
    *,
    commit: str | None,
    target_ref: PredicateFileRef,
    document: PredicatesFileDocument,
) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for entry in document.predicates:
        if entry.id in seen:
            duplicates.add(entry.id)
        seen.add(entry.id)
    if duplicates:
        formatted = ", ".join(sorted(duplicates))
        raise PredicateWorkflowError(
            f"predicate file predicates/{target_ref.name}.yaml declares duplicate id(s): {formatted}"
        )

    predicate_files = _predicate_files_by_ref_at_head(repo, commit)
    for entry in document.predicates:
        _reject_global_duplicate_predicate_id(
            predicate_files,
            target_ref=target_ref,
            predicate_id=entry.id,
        )


def add_predicate(
    repo: Repository,
    request: PredicateAddRequest,
) -> PredicateAddReport:
    """Declare a predicate in ``predicates/<file>.yaml``.

    Creates the file if absent, or appends to the existing envelope
    otherwise. Raises ``PredicateWorkflowError`` on arity/arg_types
    mismatch, empty id, or duplicate predicate id in the same file.
    """
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

    ref = PredicateFileRef(request.file)
    relpath = repo.families.predicates.address(ref).require_path()
    filepath = repo.root / relpath

    with _PREDICATE_MUTATION_LOCK, repo.head_bound_transaction(
        repo.snapshot.primary_branch_name(),
        path="predicate.add",
    ) as head_txn:
        predicate_files = _predicate_files_by_ref_at_head(repo, head_txn.expected_head)

        existing = predicate_files.get(ref)
        entries: list[PredicateDocument] = []
        created = True
        if existing is not None:
            for entry in existing.predicates:
                if entry.id == request.predicate_id:
                    raise PredicateWorkflowError(
                        f"predicate {request.predicate_id!r} already declared in {relpath}"
                    )
                entries.append(entry)
            created = False

        new_entry = convert_document_value(
            _predicate_document_payload(request),
            PredicateDocument,
            source=f"{relpath}:{request.predicate_id}",
        )
        entries.append(new_entry)

        document = PredicatesFileDocument(predicates=tuple(entries))
        reject_predicate_document_conflicts(
            repo,
            commit=head_txn.expected_head,
            target_ref=ref,
            document=document,
        )

        with head_txn.families_transact(
            message=(
                f"Add predicate {request.predicate_id} to {request.file}"
                if not created
                else f"Declare predicates for {request.file}"
            ),
        ) as transaction:
            transaction.predicates.save(ref, document)

    return PredicateAddReport(
        filepath=filepath,
        document=document,
        created=created,
    )


def list_predicates(repo: Repository) -> tuple[PredicateListItem, ...]:
    items: list[PredicateListItem] = []
    for handle in repo.families.predicates.iter_handles():
        document = handle.document
        for predicate in document.predicates:
            items.append(
                PredicateListItem(
                    file=handle.ref.name,
                    predicate_id=predicate.id,
                    arity=predicate.arity,
                    arg_types=tuple(predicate.arg_types),
                )
            )
    return tuple(items)


def show_predicate_file(
    repo: Repository,
    file: str,
) -> PredicateShowReport:
    ref = PredicateFileRef(file)
    document = repo.families.predicates.load(ref)
    if document is None:
        raise PredicateFileNotFoundError(file)
    filepath = repo.root / repo.families.predicates.address(ref).require_path()
    return PredicateShowReport(
        filepath=filepath,
        rendered=encode_document(document).decode("utf-8"),
    )


def remove_predicate(
    repo: Repository,
    request: PredicateRemoveRequest,
) -> PredicateRemoveReport:
    """Remove a predicate from ``predicates/<file>.yaml``.

    Raises ``PredicateFileNotFoundError`` if the file does not exist or
    ``PredicateNotFoundError`` if the predicate id is absent. On success
    the file is rewritten via the family ``save`` path (same commit
    pattern as ``add_predicate``); if the removal leaves zero
    predicates the file is kept as a stub so downstream tooling can
    continue to observe the envelope, matching
    ``remove_context_lifting_rule``'s behaviour for emptied
    lifting-rule blocks.
    """
    if not isinstance(request.predicate_id, str) or not request.predicate_id:
        raise PredicateWorkflowError("predicate id must be a non-empty string")

    ref = PredicateFileRef(request.file)
    with _PREDICATE_MUTATION_LOCK, repo.mutation_guard():
        existing = repo.families.predicates.load(ref)
        if existing is None:
            raise PredicateFileNotFoundError(request.file)

        relpath = repo.families.predicates.address(ref).require_path()
        filepath = repo.root / relpath

        if not any(entry.id == request.predicate_id for entry in existing.predicates):
            raise PredicateNotFoundError(request.file, request.predicate_id)

        remaining = tuple(
            entry for entry in existing.predicates if entry.id != request.predicate_id
        )
        document = PredicatesFileDocument(predicates=remaining)

        repo.families.predicates.save(
            ref,
            document,
            message=f"Remove predicate {request.predicate_id} from {request.file}",
        )

    return PredicateRemoveReport(
        filepath=filepath,
        predicate_id=request.predicate_id,
        removed=True,
    )
