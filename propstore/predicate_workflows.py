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

from quire.documents import convert_document_value, encode_document

from propstore.families.documents.predicates import (
    PredicateDocument,
    PredicatesFileDocument,
)
from propstore.families.registry import PredicateFileRef
from propstore.repository import Repository


class PredicateWorkflowError(Exception):
    """Raised when a predicate workflow cannot complete."""


class PredicateFileNotFoundError(PredicateWorkflowError):
    def __init__(self, file: str) -> None:
        super().__init__(f"Predicate file '{file}' not found")
        self.file = file


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

    existing = repo.families.predicates.load(ref)
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

    repo.families.predicates.save(
        ref,
        document,
        message=(
            f"Add predicate {request.predicate_id} to {request.file}"
            if not created
            else f"Declare predicates for {request.file}"
        ),
    )
    repo.snapshot.sync_worktree()

    return PredicateAddReport(
        filepath=filepath,
        document=document,
        created=created,
    )


def list_predicates(repo: Repository) -> tuple[PredicateListItem, ...]:
    items: list[PredicateListItem] = []
    for ref in repo.families.predicates.iter():
        document = repo.families.predicates.require(ref)
        for predicate in document.predicates:
            items.append(
                PredicateListItem(
                    file=ref.name,
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
