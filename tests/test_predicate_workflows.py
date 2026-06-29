"""Owner-layer predicate authoring workflows: add / list / show / remove."""

from __future__ import annotations

import pytest

from propstore.families.predicates import PredicateRepository
from propstore.grounding.authoring import (
    PredicateAddRequest,
    PredicateNotFoundError,
    PredicateRemoveRequest,
    PredicateWorkflowError,
    add_predicate,
    list_predicates,
    remove_predicate,
    show_predicate,
)


@pytest.fixture
def repo() -> PredicateRepository:
    return PredicateRepository()


def test_add_predicate_stores_and_reports_created(repo: PredicateRepository) -> None:
    report = add_predicate(
        repo, PredicateAddRequest(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    assert report.created is True
    assert repo.get("bird") is not None


def test_add_predicate_empty_id_rejected(repo: PredicateRepository) -> None:
    with pytest.raises(PredicateWorkflowError):
        add_predicate(repo, PredicateAddRequest(predicate_id="", arity=0))


def test_add_predicate_arity_mismatch_message(repo: PredicateRepository) -> None:
    with pytest.raises(PredicateWorkflowError, match="arity"):
        add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=2, arg_types=("Concept",)))


def test_add_predicate_negative_arity_message(repo: PredicateRepository) -> None:
    with pytest.raises(PredicateWorkflowError, match="arity"):
        add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=-1))


def test_add_predicate_duplicate_rejected(repo: PredicateRepository) -> None:
    add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=0))
    with pytest.raises(PredicateWorkflowError, match="already declared"):
        add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=0))


def test_list_predicates_sorted_by_id(repo: PredicateRepository) -> None:
    add_predicate(repo, PredicateAddRequest(predicate_id="zebra", arity=0))
    add_predicate(repo, PredicateAddRequest(predicate_id="ant", arity=0))
    assert [item.predicate_id for item in list_predicates(repo)] == ["ant", "zebra"]


def test_show_predicate_returns_declaration(repo: PredicateRepository) -> None:
    add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=1, arg_types=("Concept",)))
    report = show_predicate(repo, "bird")
    assert report.predicate.arity == 1
    assert report.predicate.arg_types == ("Concept",)


def test_show_missing_predicate_raises_with_id(repo: PredicateRepository) -> None:
    with pytest.raises(PredicateNotFoundError, match="ghost"):
        show_predicate(repo, "ghost")


def test_remove_predicate(repo: PredicateRepository) -> None:
    add_predicate(repo, PredicateAddRequest(predicate_id="bird", arity=0))
    report = remove_predicate(repo, PredicateRemoveRequest(predicate_id="bird"))
    assert report.removed is True
    assert repo.get("bird") is None


def test_remove_missing_predicate_raises_with_id(repo: PredicateRepository) -> None:
    with pytest.raises(PredicateNotFoundError, match="ghost"):
        remove_predicate(repo, PredicateRemoveRequest(predicate_id="ghost"))
