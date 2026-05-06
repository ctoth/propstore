from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def _seed_forms(repo: Repository) -> None:
    repo.git.commit_batch(
        adds={
            "forms/structural.yaml": yaml.safe_dump(
                {"name": "structural", "dimensionless": True},
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed structural form",
        branch="master",
    )


def _seed_context(repo: Repository) -> None:
    repo.git.commit_batch(
        adds={
            "contexts/ctx_test.yaml": yaml.safe_dump(
                {
                    "id": "ctx_test",
                    "name": "ctx_test",
                    "description": "Test context",
                },
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed test context",
        branch="master",
    )


def _seed_concept(repo: Repository) -> str:
    concept = normalize_concept_payloads(
        [
            {
                "id": "roundtrip_topic",
                "canonical_name": "roundtrip_topic",
                "status": "accepted",
                "definition": "Concept used by the authoring round-trip test.",
                "domain": "test",
                "form": "structural",
            }
        ],
        default_domain="test",
    )[0]
    repo.git.commit_batch(
        adds={
            "concepts/roundtrip_topic.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
            ).encode("utf-8"),
            "concepts/.counters/global.next": b"2\n",
        },
        deletes=[],
        message="Seed round-trip concept",
        branch="master",
    )
    artifact_id = concept.get("artifact_id")
    assert isinstance(artifact_id, str)
    return artifact_id


def _run(runner: CliRunner, repo: Repository, args: list[str]) -> None:
    result = runner.invoke(cli, ["-C", str(repo.root), *args])
    assert result.exit_code == 0, result.output


def _init_source(runner: CliRunner, repo: Repository, name: str) -> None:
    _run(
        runner,
        repo,
        [
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


def _propose_observation(
    runner: CliRunner,
    repo: Repository,
    source: str,
    claim_id: str,
    statement: str,
    concept_ref: str,
) -> None:
    _run(
        runner,
        repo,
        [
            "source",
            "propose-claim",
            source,
            "--id",
            claim_id,
            "--type",
            "observation",
            "--statement",
            statement,
            "--concept-ref",
            concept_ref,
            "--context",
            "ctx_test",
            "--page",
            "2",
        ],
    )


def _propose_support(
    runner: CliRunner,
    repo: Repository,
    source: str,
    justification_id: str,
    *,
    rule_kind: str,
) -> None:
    _run(
        runner,
        repo,
        [
            "source",
            "propose-justification",
            source,
            "--id",
            justification_id,
            "--conclusion",
            "target_a",
            "--premises",
            "premise_a",
            "--rule-kind",
            rule_kind,
            "--rule-strength",
            "defeasible",
            "--page",
            "3",
        ],
    )


def _finalize_and_promote(runner: CliRunner, repo: Repository, source: str) -> None:
    _run(runner, repo, ["source", "finalize", source])
    _run(runner, repo, ["source", "promote", source])


def _promoted_claim_artifact_id(repo: Repository, source: str, local_id: str) -> str:
    claims_doc = yaml.safe_load(repo.git.read_file(f"claims/{source}.yaml"))
    for claim in claims_doc["claims"]:
        logical_ids = claim.get("logical_ids") or ()
        if any(
            item.get("namespace") == source and item.get("value") == local_id
            for item in logical_ids
            if isinstance(item, dict)
        ):
            artifact_id = claim.get("artifact_id")
            assert isinstance(artifact_id, str)
            return artifact_id
    raise AssertionError(f"promoted claim {source}:{local_id} not found")


def test_source_authoring_to_aspic_extensions_round_trip(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo)
    _seed_context(repo)
    concept_ref = _seed_concept(repo)

    _init_source(runner, repo, "paper_a")
    _propose_observation(
        runner,
        repo,
        "paper_a",
        "premise_a",
        "Paper A reports the observed premise.",
        concept_ref,
    )
    _propose_observation(
        runner,
        repo,
        "paper_a",
        "target_a",
        "Paper A concludes the target claim.",
        concept_ref,
    )
    _propose_support(
        runner,
        repo,
        "paper_a",
        "support_j",
        rule_kind="supports",
    )
    _propose_support(
        runner,
        repo,
        "paper_a",
        "alt_support_j",
        rule_kind="empirical_support",
    )
    _finalize_and_promote(runner, repo, "paper_a")
    target_a = _promoted_claim_artifact_id(repo, "paper_a", "target_a")

    _init_source(runner, repo, "paper_b")
    _propose_observation(
        runner,
        repo,
        "paper_b",
        "undercutter_b",
        "Paper B reports a methodological objection.",
        concept_ref,
    )
    _run(
        runner,
        repo,
        [
            "source",
            "propose-justification",
            "paper_b",
            "--id",
            "undercut_support_j",
            "--conclusion",
            "undercutter_b",
            "--premises",
            "undercutter_b",
            "--rule-kind",
            "methodological_inference",
            "--rule-strength",
            "defeasible",
            "--attack-target-claim",
            target_a,
            "--attack-target-justification-id",
            "support_j",
            "--page",
            "4",
        ],
    )
    _finalize_and_promote(runner, repo, "paper_b")

    build = runner.invoke(cli, ["-C", str(repo.root), "build", "--force"])
    assert build.exit_code == 0, build.output

    extensions = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "world",
            "extensions",
            "--backend",
            "aspic",
            "--format",
            "json",
        ],
    )
    assert extensions.exit_code == 0, extensions.output
    report = json.loads(extensions.output)
    assert report["backend"] == "aspic"
    assert report["semantics"] == "grounded"
    assert report["active_claims"]
