from __future__ import annotations

from pathlib import Path

import yaml
import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.test_source_promote_dangling_refs import (
    _init_source,
    _propose_claims_identical,
    _seed_master_concept,
    _write_yaml,
)


def test_finalize_blocks_claim_without_context_before_writing_micropubs(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo)
    _init_source(repo, runner, "demo")
    _propose_claims_identical(repo, runner, "demo")

    claims_file = tmp_path / "claims-without-context.yaml"
    _write_yaml(
        claims_file,
        {
            "source": {"paper": "demo"},
            "claims": [
                {
                    "id": "no_context",
                    "type": "observation",
                    "statement": "A claim without an explicit context.",
                    "concepts": ["claims_identical"],
                    "provenance": {"page": 1},
                }
            ],
        },
    )
    add_claim = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "demo",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_claim.exit_code == 0, add_claim.output

    finalize = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "finalize", "demo"],
    )
    assert finalize.exit_code == 0, finalize.output

    source_head = repo.git.branch_sha("source/demo")
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=source_head))
    assert report["status"] == "blocked"
    assert report["artifact_code_status"] == "incomplete"
    assert report["micropub_coverage_errors"] == ["no_context"]
    with pytest.raises(FileNotFoundError):
        repo.git.read_file("micropubs.yaml", commit=source_head)
