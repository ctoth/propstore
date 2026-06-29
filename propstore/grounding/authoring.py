"""Owner-layer predicate authoring workflows (no Click, no stdout).

These are the reusable predicate add/list/show/remove operations the CLI adapter
calls. They own the mutation semantics — non-empty id and arity/arg_types
agreement validation, duplicate-id rejection, and storage keyed by predicate id
(never by authoring group or file). Mutations are serialized through a
module-level lock so two concurrent same-id adds resolve to exactly one survivor
(the loser sees :class:`PredicateWorkflowError`).
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from propstore.families.predicates import Predicate, PredicateRepository

_PREDICATE_MUTATION_LOCK = Lock()


class PredicateWorkflowError(Exception):
    """A predicate authoring operation was rejected."""


class PredicateNotFoundError(PredicateWorkflowError):
    """A predicate referenced by id does not exist."""

    def __init__(self, predicate_id: str) -> None:
        super().__init__(f"predicate {predicate_id!r} not found")
        self.predicate_id = predicate_id


@dataclass(frozen=True)
class PredicateAddRequest:
    """A request to declare a new predicate."""

    predicate_id: str
    arity: int
    arg_types: tuple[str, ...] = ()
    derived_from: str | None = None
    description: str | None = None
    authoring_group: str | None = None


@dataclass(frozen=True)
class PredicateAddReport:
    """The result of adding a predicate."""

    predicate: Predicate
    created: bool


@dataclass(frozen=True)
class PredicateRemoveRequest:
    """A request to remove a declared predicate by id."""

    predicate_id: str


@dataclass(frozen=True)
class PredicateRemoveReport:
    """The result of removing a predicate."""

    predicate_id: str
    removed: bool


@dataclass(frozen=True)
class PredicateListItem:
    """A summary row for a declared predicate."""

    predicate_id: str
    arity: int
    arg_types: tuple[str, ...]
    authoring_group: str | None


@dataclass(frozen=True)
class PredicateShowReport:
    """The full declaration for one predicate."""

    predicate: Predicate


def add_predicate(
    repo: PredicateRepository,
    request: PredicateAddRequest,
    *,
    message: str = "add predicate",
) -> PredicateAddReport:
    """Declare a new predicate, rejecting an empty id, bad arity, or a duplicate."""

    if request.predicate_id == "":
        raise PredicateWorkflowError("predicate id must be a non-empty string")
    if request.arity < 0:
        raise PredicateWorkflowError(
            f"predicate {request.predicate_id!r}: arity must be >= 0, got {request.arity}"
        )
    if len(request.arg_types) != request.arity:
        raise PredicateWorkflowError(
            f"predicate {request.predicate_id!r}: arg_types length "
            f"{len(request.arg_types)} does not match arity {request.arity}"
        )
    predicate = Predicate(
        predicate_id=request.predicate_id,
        arity=request.arity,
        arg_types=request.arg_types,
        derived_from=request.derived_from,
        description=request.description,
        authoring_group=request.authoring_group,
    )
    with _PREDICATE_MUTATION_LOCK:
        if repo.exists(request.predicate_id):
            raise PredicateWorkflowError(
                f"predicate {request.predicate_id!r} already declared"
            )
        repo.author(predicate, message=message)
    return PredicateAddReport(predicate=predicate, created=True)


def list_predicates(repo: PredicateRepository) -> tuple[PredicateListItem, ...]:
    """Every declared predicate, summarized and sorted by id."""

    items = [
        PredicateListItem(
            predicate_id=predicate.predicate_id,
            arity=predicate.arity,
            arg_types=predicate.arg_types,
            authoring_group=predicate.authoring_group,
        )
        for predicate in repo.iter_predicates()
    ]
    return tuple(sorted(items, key=lambda item: item.predicate_id))


def show_predicate(repo: PredicateRepository, predicate_id: str) -> PredicateShowReport:
    """The full declaration for ``predicate_id`` or raise :class:`PredicateNotFoundError`."""

    predicate = repo.get(predicate_id)
    if predicate is None:
        raise PredicateNotFoundError(predicate_id)
    return PredicateShowReport(predicate=predicate)


def remove_predicate(
    repo: PredicateRepository,
    request: PredicateRemoveRequest,
    *,
    message: str = "remove predicate",
) -> PredicateRemoveReport:
    """Remove a declared predicate, or raise if it does not exist."""

    if request.predicate_id == "":
        raise PredicateWorkflowError("predicate id must be a non-empty string")
    with _PREDICATE_MUTATION_LOCK:
        if not repo.exists(request.predicate_id):
            raise PredicateNotFoundError(request.predicate_id)
        repo.delete(request.predicate_id, message=message)
    return PredicateRemoveReport(predicate_id=request.predicate_id, removed=True)
