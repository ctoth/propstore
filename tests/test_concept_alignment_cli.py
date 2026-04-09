from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.cli import cli
from propstore.cli.repository import Repository
from propstore.concept_alignment import build_alignment_artifact


def _init_source(runner: CliRunner, repo: Repository, name: str) -> None:
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
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


def test_source_propose_concept_writes_inventory(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _init_source(runner, repo, "demo")

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "claims_identical",
            "--definition",
            "A weak identity relation between claim assertions.",
            "--form",
            "structural",
        ],
    )
    assert result.exit_code == 0, result.output

    tip = repo.git.branch_sha("source/demo")
    assert tip is not None
    stored = yaml.safe_load(repo.git.read_file("concepts.yaml", commit=tip))
    concept = stored["concepts"][0]
    assert concept["local_name"] == "claims_identical"
    assert concept["proposed_name"] == "claims_identical"


@given(
    definition_a=st.text(min_size=1, max_size=40),
    definition_b=st.text(min_size=1, max_size=40),
)
@settings(deadline=None)
def test_alignment_builder_emits_mutual_attacks_for_same_name_different_definition(
    definition_a: str,
    definition_b: str,
) -> None:
    if definition_a == definition_b:
        return
    artifact = build_alignment_artifact(
        [
            {
                "source": "tag:local@propstore,2026:source/a",
                "local_handle": "local_a",
                "proposed_name": "claims_identical",
                "definition": definition_a,
                "form": "structural",
            },
            {
                "source": "tag:local@propstore,2026:source/b",
                "local_handle": "local_b",
                "proposed_name": "claims_identical",
                "definition": definition_b,
                "form": "structural",
            },
        ]
    )
    attacks = {tuple(pair) for pair in artifact["framework"]["attacks"]}
    assert ("alt_local_a", "alt_local_b") in attacks
    assert ("alt_local_b", "alt_local_a") in attacks


def test_concept_align_creates_proposal_artifact_and_promote(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _init_source(runner, repo, "a")
    _init_source(runner, repo, "b")

    for source_name, local_name, definition in [
        ("a", "claims_identical", "A weak identity relation."),
        ("b", "weak_identity_relation", "A constrained identity relation."),
    ]:
        result = runner.invoke(
            cli,
            [
                "-C",
                str(repo.root),
                "source",
                "propose-concept",
                source_name,
                "--name",
                local_name,
                "--definition",
                definition,
                "--form",
                "structural",
            ],
        )
        assert result.exit_code == 0, result.output

    align_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "concept",
            "align",
            "--sources",
            "source/a",
            "source/b",
        ],
    )
    assert align_result.exit_code == 0, align_result.output
    assert "align:" in align_result.output
    cluster_id = align_result.output.strip().split()[-1]

    proposal_tip = repo.git.branch_sha("proposal/concepts")
    assert proposal_tip is not None
    artifact = yaml.safe_load(
        repo.git.read_file(f"merge/concepts/{cluster_id.split(':', 1)[1]}.yaml", commit=proposal_tip)
    )
    first_arg = artifact["arguments"][0]["id"]

    decide_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "concept",
            "decide",
            cluster_id,
            "--accept",
            first_arg,
        ],
    )
    assert decide_result.exit_code == 0, decide_result.output

    promote_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "concept",
            "promote",
            cluster_id,
        ],
    )
    assert promote_result.exit_code == 0, promote_result.output

    concept_file = repo.root / "concepts" / "claims_identical.yaml"
    assert concept_file.exists()
    concept_data = yaml.safe_load(concept_file.read_text(encoding="utf-8"))
    assert concept_data["canonical_name"] == "claims_identical"
    assert concept_data["status"] == "accepted"
