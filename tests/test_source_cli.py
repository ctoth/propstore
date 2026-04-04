from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.cli.repository import Repository
from propstore.repo.branch import create_branch, list_branches


def test_source_branch_kind_is_detected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files({"seed.txt": b"ok\n"}, "seed")

    create_branch(repo.git, "source/test-source")

    branches = {branch.name: branch for branch in list_branches(repo.git)}
    assert branches["source/test-source"].kind == "source"


def test_source_init_creates_source_branch_and_source_yaml(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "Halpin_2010_OwlSameAsIsntSame",
            "--kind",
            "academic_paper",
            "--origin-type",
            "doi",
            "--origin-value",
            "10.1007/978-3-642-17746-0_20",
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/Halpin_2010_OwlSameAsIsntSame")
    assert branch_tip is not None
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["kind"] == "academic_paper"
    assert source_doc["origin"]["type"] == "doi"
    assert source_doc["origin"]["value"] == "10.1007/978-3-642-17746-0_20"
    assert source_doc["id"].startswith("tag:")


def test_source_init_uses_repo_uri_authority_and_content_file(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.config_path.write_text("uri_authority: example.com,2026\n", encoding="utf-8")
    runner = CliRunner()
    content_file = tmp_path / "paper.pdf"
    content_file.write_bytes(b"%PDF-demo\n")

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo",
            "--kind",
            "academic_paper",
            "--origin-type",
            "file",
            "--origin-value",
            "paper.pdf",
            "--content-file",
            str(content_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["id"] == "tag:example.com,2026:source/demo"
    assert source_doc["origin"]["content_ref"].startswith("ni:///sha-256;")


def test_source_write_notes_commits_only_to_source_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    notes_file = tmp_path / "notes.md"
    notes_file.write_text("# Notes\n\nA source note.\n", encoding="utf-8")

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-notes",
            "demo",
            "--file",
            str(notes_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    stored_notes = repo.git.read_file("notes.md", commit=branch_tip).decode("utf-8").replace("\r\n", "\n")
    assert stored_notes == notes_file.read_text(encoding="utf-8").replace("\r\n", "\n")
    try:
        repo.git.read_file("notes.md")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("notes.md should not be materialized on master")


def test_source_write_metadata_commits_json_to_source_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text(
        json.dumps({"title": "Demo", "authors": ["A"], "year": "2026"}, indent=2),
        encoding="utf-8",
    )

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo-meta",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo-meta",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-metadata",
            "demo-meta",
            "--file",
            str(metadata_file),
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/demo-meta")
    assert branch_tip is not None
    loaded = json.loads(repo.git.read_file("metadata.json", commit=branch_tip))
    assert loaded["title"] == "Demo"
    assert loaded["authors"] == ["A"]


def test_source_sync_materializes_branch_to_papers_workspace(tmp_path: Path) -> None:
    repo_root = tmp_path / "project"
    repo = Repository.init(repo_root / "knowledge")
    runner = CliRunner()
    notes_file = tmp_path / "notes.md"
    notes_file.write_text("# Notes\n", encoding="utf-8")

    init_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            "demo-sync",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo-sync",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    write_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-notes",
            "demo-sync",
            "--file",
            str(notes_file),
        ],
    )
    assert write_result.exit_code == 0, write_result.output

    sync_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "sync",
            "demo-sync",
        ],
    )
    assert sync_result.exit_code == 0, sync_result.output

    synced_notes = repo.root.parent / "papers" / "demo-sync" / "notes.md"
    assert synced_notes.exists()
    assert synced_notes.read_text(encoding="utf-8") == "# Notes\n"
