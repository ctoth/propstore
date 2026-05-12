"""Tests for the predicate-authoring workflow and the ``pks predicate`` CLI."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.app.predicates import (
    PredicateAddRequest,
    PredicateNotFoundError,
    PredicateRemoveRequest,
    PredicateWorkflowError,
    add_predicate,
    list_predicates,
    remove_predicate,
    show_predicate,
)
from propstore.families.registry import PredicateRef
from propstore.repository import Repository


def _read_predicate_artifact(repo: Repository, predicate_id: str) -> dict:
    return yaml.safe_load(repo.git.read_file(f"predicates/{predicate_id}.yaml"))


def test_add_predicate_writes_one_artifact_per_predicate(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    first = add_predicate(
        repo,
        PredicateAddRequest(
            file="ikeda_2014",
            predicate_id="aspirin_user",
            arity=1,
            arg_types=("person",),
            description="Patient takes daily low-dose aspirin.",
        ),
    )
    second = add_predicate(
        repo,
        PredicateAddRequest(
            file="other_authoring_batch",
            predicate_id="reduces_mi",
            arity=1,
            arg_types=("person",),
        ),
    )

    assert first.created is True
    assert second.created is True
    assert not first.filepath.exists()
    first_data = _read_predicate_artifact(repo, "aspirin_user")
    second_data = _read_predicate_artifact(repo, "reduces_mi")
    assert first_data["id"] == "aspirin_user"
    assert first_data["authoring_group"] == "ikeda_2014"
    assert second_data["id"] == "reduces_mi"
    assert repo.families.predicates.require(PredicateRef("aspirin_user")).id == "aspirin_user"


def test_add_predicate_rejects_arity_mismatch(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        add_predicate(
            repo,
            PredicateAddRequest(
                file="foo",
                predicate_id="bad",
                arity=2,
                arg_types=("person",),
            ),
        )
    except PredicateWorkflowError as exc:
        assert "arity" in str(exc)
    else:
        raise AssertionError("expected arity mismatch failure")


def test_add_predicate_rejects_duplicate(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="foo", predicate_id="dup", arity=0),
    )
    try:
        add_predicate(
            repo,
            PredicateAddRequest(file="foo", predicate_id="dup", arity=0),
        )
    except PredicateWorkflowError as exc:
        assert "already declared" in str(exc)
    else:
        raise AssertionError("expected duplicate predicate failure")


def test_predicate_cli_add_creates_file(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "predicate",
            "add",
            "--file",
            "ikeda_2014",
            "--id",
            "aspirin_user",
            "--arity",
            "1",
            "--arg-type",
            "person",
            "--description",
            "Patient takes daily low-dose aspirin.",
        ],
    )

    assert result.exit_code == 0, result.output
    target = repo.root / "predicates" / "aspirin_user.yaml"
    assert not target.exists()
    data = _read_predicate_artifact(repo, "aspirin_user")
    assert data["id"] == "aspirin_user"
    assert data["arity"] == 1
    assert data["arg_types"] == ["person"]
    assert data["authoring_group"] == "ikeda_2014"


def test_predicate_cli_file_option_does_not_determine_storage(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    first = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "predicate",
            "add",
            "--file",
            "ikeda_2014",
            "--id",
            "p1",
            "--arity",
            "0",
        ],
    )
    second = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "predicate",
            "add",
            "--file",
            "ikeda_2014",
            "--id",
            "p2",
            "--arity",
            "1",
            "--arg-type",
            "thing",
        ],
    )

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert _read_predicate_artifact(repo, "p1")["id"] == "p1"
    assert _read_predicate_artifact(repo, "p2")["id"] == "p2"


def test_predicate_owner_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )

    items = list_predicates(repo)
    shown = show_predicate(repo, "p1")

    assert [(item.authoring_group, item.predicate_id) for item in items] == [("ikeda_2014", "p1")]
    assert "id: p1" in shown.rendered

    try:
        show_predicate(repo, "missing")
    except PredicateNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing predicate failure")


def test_predicate_cli_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    runner = CliRunner()

    listed = runner.invoke(cli, ["-C", str(repo.root), "predicate", "list"])
    shown = runner.invoke(cli, ["-C", str(repo.root), "predicate", "show", "p1"])

    assert listed.exit_code == 0, listed.output
    assert "ikeda_2014" in listed.output
    assert "p1" in listed.output
    assert shown.exit_code == 0, shown.output
    assert "id: p1" in shown.output


def test_remove_predicate_rejects_missing_artifact(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        remove_predicate(
            repo,
            PredicateRemoveRequest(predicate_id="p1"),
        )
    except PredicateNotFoundError as exc:
        assert "p1" in str(exc)
    else:
        raise AssertionError("expected missing-artifact failure")


def test_remove_predicate_rejects_unknown_id(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    try:
        remove_predicate(
            repo,
            PredicateRemoveRequest(predicate_id="nope"),
        )
    except PredicateNotFoundError as exc:
        assert "nope" in str(exc)
    else:
        raise AssertionError("expected unknown-id failure")


def test_remove_predicate_removes_and_preserves_others(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p2", arity=1, arg_types=("thing",)),
    )

    report = remove_predicate(
        repo,
        PredicateRemoveRequest(predicate_id="p1"),
    )
    assert report.removed is True
    assert repo.families.predicates.load(PredicateRef("p1")) is None
    assert _read_predicate_artifact(repo, "p2")["id"] == "p2"


def test_predicate_cli_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "predicate",
            "remove",
            "--id",
            "p1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert repo.families.predicates.load(PredicateRef("p1")) is None
