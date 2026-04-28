from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.builders import SourceClaimSpec
from tests.test_source_promote_dangling_refs import (
    _add_claims,
    _init_source,
    _propose_claims_identical,
    _seed_master_concept,
)


def test_source_justification_proposal_rejects_unknown_rule_kind(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo)
    _init_source(repo, runner, "demo")
    _propose_claims_identical(repo, runner, "demo")
    _add_claims(
        repo,
        runner,
        "demo",
        tmp_path,
        [
            SourceClaimSpec(
                local_id="c1",
                claim_type="observation",
                statement="First claim.",
                concepts=("claims_identical",),
                page=1,
            ),
            SourceClaimSpec(
                local_id="c2",
                claim_type="observation",
                statement="Second claim.",
                concepts=("claims_identical",),
                page=2,
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-justification",
            "demo",
            "--id",
            "j_bad",
            "--conclusion",
            "c2",
            "--premises",
            "c1",
            "--rule-kind",
            "bogus",
        ],
    )

    assert result.exit_code != 0
    assert "rule_kind" in result.output
