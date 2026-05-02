from __future__ import annotations

from click.testing import CliRunner

from quire.documents import render_yaml_value
from propstore.cli import cli
from propstore.app.micropubs import (
    MicropubNotFoundError,
    find_micropub,
    inspect_micropub_lift,
    list_micropubs,
    load_micropub_bundle,
)
from propstore.repository import Repository


def _seed_micropub_repo(tmp_path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "contexts/ctx_source.yaml": render_yaml_value(
                {
                    "id": "ctx_source",
                    "name": "Source",
                }
            ).encode("utf-8"),
            "contexts/ctx_target.yaml": render_yaml_value(
                {
                    "id": "ctx_target",
                    "name": "Target",
                    "lifting_rules": [
                        {
                            "id": "lift_source_target",
                            "source": "ctx_source",
                            "target": "ctx_target",
                            "mode": "bridge",
                        }
                    ],
                }
            ).encode("utf-8"),
            "contexts/ctx_other.yaml": render_yaml_value(
                {
                    "id": "ctx_other",
                    "name": "Other",
                }
            ).encode("utf-8"),
            "micropubs/demo.yaml": render_yaml_value(
                {
                    "micropubs": [
                        {
                            "artifact_id": "ps:micropub:test",
                            "context": {"id": "ctx_source"},
                            "claims": ["claim:one"],
                        }
                    ]
                }
            ).encode("utf-8"),
        },
        "Seed micropub fixture",
    )
    repo.git.sync_worktree()
    return repo


def test_micropub_reports_load_find_and_lift(tmp_path) -> None:
    repo = _seed_micropub_repo(tmp_path)

    bundle = load_micropub_bundle(repo, "demo")
    entry = find_micropub(repo, "ps:micropub:test")
    items = list_micropubs(repo)
    lift = inspect_micropub_lift(
        repo,
        "ps:micropub:test",
        target_context="ctx_target",
    )
    reverse = inspect_micropub_lift(
        repo,
        "ps:micropub:test",
        target_context="ctx_other",
    )

    assert bundle.micropubs[0].artifact_id == "ps:micropub:test"
    assert entry.ref.name == "demo"
    assert entry.document.context.id == "ctx_source"
    assert [(item.bundle, item.artifact_id) for item in items] == [("demo", "ps:micropub:test")]
    assert [(decision.proposition_id, decision.status) for decision in lift.decisions] == [
        ("claim:one", "lifted"),
    ]
    assert reverse.decisions == ()


def test_micropub_reports_raise_typed_not_found(tmp_path) -> None:
    repo = _seed_micropub_repo(tmp_path)

    try:
        find_micropub(repo, "ps:micropub:missing")
    except MicropubNotFoundError as exc:
        assert str(exc) == "Micropub 'ps:micropub:missing' not found."
    else:
        raise AssertionError("expected typed missing-micropub failure")


def test_micropub_cli_renders_bundle_show_and_lift(tmp_path) -> None:
    repo = _seed_micropub_repo(tmp_path)
    runner = CliRunner()

    listed = runner.invoke(cli, ["-C", str(repo.root), "micropub", "list"])
    bundle = runner.invoke(cli, ["-C", str(repo.root), "micropub", "bundle", "demo"])
    show = runner.invoke(cli, ["-C", str(repo.root), "micropub", "show", "ps:micropub:test"])
    lift = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "micropub",
            "lift",
            "ps:micropub:test",
            "--target-context",
            "ctx_target",
        ],
    )
    no_lift = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "micropub",
            "lift",
            "ps:micropub:test",
            "--target-context",
            "ctx_other",
        ],
    )

    assert listed.exit_code == 0, listed.output
    assert "ps:micropub:test" in listed.output
    assert bundle.exit_code == 0, bundle.output
    assert "ps:micropub:test" in bundle.output
    assert show.exit_code == 0, show.output
    assert "claims:" in show.output
    assert lift.exit_code == 0, lift.output
    assert "lifting decisions: ps:micropub:test ctx_source -> ctx_target" in lift.output
    assert "claim:one" in lift.output
    assert "lifted" in lift.output
    assert no_lift.exit_code == 1, no_lift.output
    assert "no lifted decision: ps:micropub:test ctx_source -> ctx_other" in no_lift.output
