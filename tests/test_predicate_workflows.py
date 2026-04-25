"""Tests for the predicate-authoring workflow and the ``pks predicate`` CLI."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.app.predicates import (
    PredicateAddRequest,
    PredicateFileNotFoundError,
    PredicateNotFoundError,
    PredicateRemoveRequest,
    PredicateWorkflowError,
    add_predicate,
    list_predicates,
    remove_predicate,
    show_predicate_file,
)
from propstore.repository import Repository


def test_add_predicate_creates_file_and_appends(tmp_path) -> None:
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
            file="ikeda_2014",
            predicate_id="reduces_mi",
            arity=1,
            arg_types=("person",),
        ),
    )

    assert first.created is True
    assert second.created is False
    assert first.filepath.exists()
    data = yaml.safe_load(first.filepath.read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in data["predicates"]]
    assert ids == ["aspirin_user", "reduces_mi"]


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
    target = repo.root / "predicates" / "ikeda_2014.yaml"
    assert target.exists()
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["predicates"][0]["id"] == "aspirin_user"
    assert data["predicates"][0]["arity"] == 1
    assert data["predicates"][0]["arg_types"] == ["person"]


def test_predicate_cli_appends_to_existing_file(tmp_path) -> None:
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
    target = repo.root / "predicates" / "ikeda_2014.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in data["predicates"]]
    assert ids == ["p1", "p2"]


def test_predicate_owner_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )

    items = list_predicates(repo)
    shown = show_predicate_file(repo, "ikeda_2014")

    assert [(item.file, item.predicate_id) for item in items] == [("ikeda_2014", "p1")]
    assert "predicates:" in shown.rendered

    try:
        show_predicate_file(repo, "missing")
    except PredicateFileNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing predicate file failure")


def test_predicate_cli_list_and_show(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    runner = CliRunner()

    listed = runner.invoke(cli, ["-C", str(repo.root), "predicate", "list"])
    shown = runner.invoke(cli, ["-C", str(repo.root), "predicate", "show", "ikeda_2014"])

    assert listed.exit_code == 0, listed.output
    assert "ikeda_2014" in listed.output
    assert "p1" in listed.output
    assert shown.exit_code == 0, shown.output
    assert "predicates:" in shown.output


def test_remove_predicate_rejects_missing_file(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    try:
        remove_predicate(
            repo,
            PredicateRemoveRequest(file="missing", predicate_id="p1"),
        )
    except PredicateFileNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing-file failure")


def test_remove_predicate_rejects_unknown_id(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(file="ikeda_2014", predicate_id="p1", arity=0),
    )
    try:
        remove_predicate(
            repo,
            PredicateRemoveRequest(file="ikeda_2014", predicate_id="nope"),
        )
    except PredicateNotFoundError as exc:
        assert "nope" in str(exc)
        assert "ikeda_2014" in str(exc)
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
        PredicateRemoveRequest(file="ikeda_2014", predicate_id="p1"),
    )
    assert report.removed is True
    data = yaml.safe_load(report.filepath.read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in data["predicates"]]
    assert ids == ["p2"]


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
            "--file",
            "ikeda_2014",
            "--id",
            "p1",
        ],
    )

    assert result.exit_code == 0, result.output
    data = yaml.safe_load((repo.root / "predicates" / "ikeda_2014.yaml").read_text(encoding="utf-8"))
    assert data.get("predicates") in (None, [])
