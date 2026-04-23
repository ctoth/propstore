from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.app.forms import (
    FormAddRequest,
    FormNotFoundError,
    FormWorkflowError,
    add_form,
    list_form_items,
    remove_form,
    search_form_items,
    validate_forms,
)
from propstore.cli import cli
from propstore.repository import Repository


def test_form_workflows_add_list_validate_and_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    add_report = add_form(
        repo,
        FormAddRequest(
            name="frequency_like",
            unit_symbol="Hz",
            dimensions_json='{"T": -1}',
            note="Frequency-like test form.",
        ),
        dry_run=False,
    )
    items = list_form_items(repo, dims_filter="T:-1")
    validation = validate_forms(repo)
    remove_report = remove_form(repo, "frequency_like", force=False, dry_run=False)

    assert add_report.created is True
    assert add_report.document.dimensionless is False
    assert add_report.document.dimensions == {"T": -1}
    assert [item.name for item in items or ()] == ["frequency_like"]
    assert validation is not None
    assert validation.ok
    assert validation.count == 1
    assert remove_report.removed is True
    assert not (repo.forms_dir / "frequency_like.yaml").exists()


def test_form_workflows_report_json_and_missing_errors(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    try:
        add_form(
            repo,
            FormAddRequest(name="bad_dims", dimensions_json="{not-json"),
            dry_run=True,
        )
    except FormWorkflowError as exc:
        assert "Invalid JSON for --dimensions" in str(exc)
    else:
        raise AssertionError("expected malformed dimensions failure")

    try:
        remove_form(repo, "missing", force=False, dry_run=False)
    except FormNotFoundError as exc:
        assert exc.name == "missing"
    else:
        raise AssertionError("expected missing form failure")


def test_form_search_matches_unit_and_name(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_form(
        repo,
        FormAddRequest(
            name="frequency_like",
            unit_symbol="Hz",
            dimensions_json='{"T": -1}',
        ),
        dry_run=False,
    )

    unit_matches = search_form_items(repo, "hz", limit=10)
    name_matches = search_form_items(repo, "frequency", limit=10)

    assert [item.name for item in unit_matches or ()] == ["frequency_like"]
    assert [item.name for item in name_matches or ()] == ["frequency_like"]


def test_form_cli_add_dry_run_list_validate_and_remove(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    dry_run = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "form",
            "add",
            "--name",
            "dry_form",
            "--dimensionless",
            "true",
            "--dry-run",
        ],
    )
    add = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "form",
            "add",
            "--name",
            "real_form",
            "--unit",
            "Hz",
            "--dimensions",
            '{"T": -1}',
        ],
    )
    listed = runner.invoke(cli, ["-C", str(repo.root), "form", "list", "--show-dims"])
    searched = runner.invoke(cli, ["-C", str(repo.root), "form", "search", "hz"])
    validate = runner.invoke(cli, ["-C", str(repo.root), "form", "validate"])

    assert dry_run.exit_code == 0, dry_run.output
    assert "Would create" in dry_run.output
    assert not (repo.forms_dir / "dry_form.yaml").exists()
    assert add.exit_code == 0, add.output
    data = yaml.safe_load((repo.forms_dir / "real_form.yaml").read_text())
    assert data["dimensions"] == {"T": -1}
    assert listed.exit_code == 0, listed.output
    assert "real_form" in listed.output
    assert searched.exit_code == 0, searched.output
    assert "real_form" in searched.output
    assert validate.exit_code == 0, validate.output
    assert "OK: 1 form(s) valid" in validate.output
    remove = runner.invoke(cli, ["-C", str(repo.root), "form", "remove", "real_form"])
    assert remove.exit_code == 0, remove.output
    assert "Removed" in remove.output
