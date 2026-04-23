"""Tests for ``pks source list`` and ``pks source add-claim --context``."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def _init_source(runner: CliRunner, repo_root: Path, name: str) -> None:
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo_root),
            "source",
            "init",
            name,
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            name,
        ],
    )
    assert result.exit_code == 0, result.output


def test_source_list_enumerates_source_branches(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _init_source(runner, repo.root, "Alpha_2024")
    _init_source(runner, repo.root, "Beta_2025")

    result = runner.invoke(cli, ["-C", str(repo.root), "source", "list"])

    assert result.exit_code == 0, result.output
    assert "Alpha_2024" in result.output
    assert "Beta_2025" in result.output
    assert "source/Alpha_2024" in result.output


def test_source_list_emits_no_branches_message(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    result = runner.invoke(cli, ["-C", str(repo.root), "source", "list"])

    assert result.exit_code == 0, result.output
    assert "No source branches" in result.output


def test_source_add_claim_context_flag_injects_default(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    _init_source(runner, repo.root, "Demo_2026")

    # Batch YAML with two claims: one inline-context, one omitting it.
    batch = tmp_path / "claims.yaml"
    batch.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "Demo_2026"},
                "claims": [
                    {
                        "id": "c_with_context",
                        "type": "observation",
                        "statement": "Already has context.",
                        "context": "ctx_inline",
                    },
                    {
                        "id": "c_without_context",
                        "type": "observation",
                        "statement": "No context inline.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "Demo_2026",
            "--batch",
            str(batch),
            "--context",
            "ctx_default",
        ],
    )

    assert result.exit_code == 0, result.output
    branch_tip = repo.git.branch_sha("source/Demo_2026")
    assert branch_tip is not None
    stored = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    by_local_id = {
        claim.get("source_local_id"): claim for claim in stored["claims"]
    }
    assert by_local_id["c_with_context"]["context"] == "ctx_inline"
    assert by_local_id["c_without_context"]["context"] == "ctx_default"
