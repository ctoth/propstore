from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


PAPER = "Ioannidis_2005_WhyMostPublishedResearch"
FIXTURES = Path(__file__).parent / "fixtures"


def init_repo(tmp_path) -> Repository:
    return Repository.init(tmp_path / "knowledge")


def invoke(repo: Repository, args: list[str]):
    return CliRunner().invoke(cli, ["-C", str(repo.root), *args])


def seed_predicates(repo: Repository) -> None:
    result = invoke(
        repo,
        [
            "proposal",
            "predicates",
            "declare",
            "--paper",
            PAPER,
            "--model",
            "test-model",
            "--mock-llm-fixture",
            str(FIXTURES / "llm_predicate_extraction_ioannidis.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    promoted = invoke(
        repo,
        ["proposal", "predicates", "promote", "--paper", PAPER],
    )
    assert promoted.exit_code == 0, promoted.output


def seed_rule_proposals(repo: Repository) -> None:
    seed_predicates(repo)
    result = invoke(
        repo,
        [
            "proposal",
            "propose-rules",
            "--paper",
            PAPER,
            "--model",
            "test-model",
            "--mock-llm-fixture",
            str(FIXTURES / "llm_rule_extraction_ioannidis.json"),
        ],
    )
    assert result.exit_code == 0, result.output
