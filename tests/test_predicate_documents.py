"""Predicate charter tests: ONE Predicate type, author -> store -> sidecar -> render.

Behavioral tests over the real quire substrate (in-memory git store + on-disk
sqlite sidecar). The sidecar columns ARE the charter fields — there is no DTO.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.families.predicates import Predicate, PredicateRepository


@pytest.fixture
def repo() -> PredicateRepository:
    return PredicateRepository()


def test_predicate_columns_fall_out_of_the_charter() -> None:
    schema_object = Predicate.__charter__.to_schema_object()
    column_names = {field.name for field in schema_object.fields}
    assert {
        "predicate_id",
        "arity",
        "arg_types",
        "derived_from",
        "description",
        "authoring_group",
        "promoted_from_sha",
    } <= column_names


def test_author_then_load_round_trips(repo: PredicateRepository) -> None:
    predicate = Predicate(
        predicate_id="bird",
        arity=1,
        arg_types=("Concept",),
        derived_from="concept.relation:is_a:Bird",
        description="x is a bird",
    )
    repo.author(predicate, message="add bird")
    loaded = repo.get("bird")
    assert loaded == predicate


def test_sidecar_round_trips_arg_types_json(
    repo: PredicateRepository, tmp_path: Path
) -> None:
    repo.author(
        Predicate(predicate_id="heavier", arity=2, arg_types=("Concept", "Concept")),
        message="m",
    )
    repo.author(
        Predicate(
            predicate_id="bird",
            arity=1,
            arg_types=("Concept",),
            derived_from="concept.relation:is_a:Bird",
        ),
        message="m",
    )
    schema = repo.build_sidecar(tmp_path / "p.db")
    rendered = {
        p.predicate_id: p for p in repo.render_predicates(tmp_path / "p.db", schema)
    }
    assert rendered["heavier"].arg_types == ("Concept", "Concept")
    assert rendered["bird"].derived_from == "concept.relation:is_a:Bird"
    assert rendered["bird"].arity == 1


def test_build_sidecar_never_filters(repo: PredicateRepository, tmp_path: Path) -> None:
    for i in range(5):
        repo.author(Predicate(predicate_id=f"p{i}", arity=0), message="m")
    schema = repo.build_sidecar(tmp_path / "p.db")
    assert len(repo.render_predicates(tmp_path / "p.db", schema)) == 5
