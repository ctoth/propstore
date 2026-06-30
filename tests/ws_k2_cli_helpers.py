"""Shared helpers for the rule-proposal CLI tests (``proposal propose/promote-rules``).

These build a repository, seed the canonical predicates a rule references, and
drive the CLI through :class:`click.testing.CliRunner`. The LLM is never called:
``propose-rules`` reads its response from a fixture file, and the seed helper
feeds the rule-extraction owner a deterministic JSON payload.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from click.testing import Result

from propstore.cli import cli
from propstore.families.predicates import Predicate
from propstore.repository import Repository

PAPER = "Ioannidis_2005_WhyMostPublishedResearch"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ws_k2"


def init_repo(tmp_path: Path) -> Repository:
    return Repository.init(tmp_path / "knowledge")


def invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), *args])


def seed_predicates(repo: Repository) -> None:
    for predicate in (
        Predicate(
            predicate_id="sample_size",
            arity=2,
            arg_types=("paper_id", "int"),
            description="Paper-level sample size.",
            authoring_group=PAPER,
        ),
        Predicate(
            predicate_id="bias",
            arity=2,
            arg_types=("paper_id", "float"),
            description="Study-setting bias.",
            authoring_group=PAPER,
        ),
        Predicate(
            predicate_id="low_trust",
            arity=1,
            arg_types=("paper_id",),
            description="Low trust classification.",
            authoring_group=PAPER,
        ),
        Predicate(
            predicate_id="high_trust",
            arity=1,
            arg_types=("paper_id",),
            description="High trust classification.",
            authoring_group=PAPER,
        ),
    ):
        repo.families.predicate.save(
            predicate.predicate_id,
            predicate,
            message=f"Seed predicate {predicate.predicate_id}",
        )


def _three_rule_fixture() -> str:
    return json.dumps(
        {
            "rules": [
                {
                    "rule_id": "rule-001",
                    "rule_type": "defeasible",
                    "head": "low_trust(P)",
                    "body": ["sample_size(P, 30)", "bias(P, 0.8)"],
                    "predicates_referenced": ["sample_size/2", "bias/2"],
                    "page_reference": "Ioannidis 2005 p. 0697",
                },
                {
                    "rule_id": "rule-002",
                    "rule_type": "defeasible",
                    "head": "low_trust(P)",
                    "body": ["bias(P, 0.5)"],
                    "predicates_referenced": ["bias/2"],
                    "page_reference": "Ioannidis 2005 p. 0698",
                },
                {
                    "rule_id": "rule-003",
                    "rule_type": "defeasible",
                    "head": "high_trust(P)",
                    "body": ["sample_size(P, 500)"],
                    "predicates_referenced": ["sample_size/2"],
                    "page_reference": "Ioannidis 2005 p. 0699",
                },
            ]
        }
    )


def seed_rule_proposals(repo: Repository) -> str:
    """Seed three recorded rule proposals (rule-001, rule-002, rule-003)."""

    from propstore.heuristic import rule_extraction

    seed_predicates(repo)
    result = rule_extraction.propose_rules_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
        llm_response=_three_rule_fixture(),
    )
    assert result.commit_sha is not None
    return result.commit_sha
