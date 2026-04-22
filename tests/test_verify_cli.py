from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.artifact_codes import attach_source_artifact_codes
from tests.family_helpers import build_sidecar
from propstore.cli import cli
from propstore.repository import Repository
from tests.conftest import make_test_context_commit_entry
from tests.test_source_relations import _init_source, _seed_master_concept


def _prepare_promoted_source(tmp_path: Path) -> tuple[Repository, str]:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    content_file = tmp_path / "paper.pdf"
    content_file.write_bytes(b"%PDF-demo\n")
    _seed_master_concept(repo, name="claims_identical")
    context_path, context_body = make_test_context_commit_entry()
    repo.git.commit_batch(
        adds={context_path: context_body},
        deletes=[],
        message="Seed test context",
        branch="master",
    )

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
            "file",
            "--origin-value",
            "paper.pdf",
            "--content-file",
            str(content_file),
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    propose_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--concept-name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert propose_result.exit_code == 0, propose_result.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "claims_identical",
                        "value": 1.0,
                        "unit": "probability",
                        "context": "ctx_test",
                        "provenance": {"page": 1},
                    },
                    {
                        "id": "claim2",
                        "type": "observation",
                        "statement": "A second claim.",
                        "concepts": ["claims_identical"],
                        "context": "ctx_test",
                        "provenance": {"page": 2},
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_claims = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "add-claim", "demo", "--batch", str(claims_file)],
    )
    assert add_claims.exit_code == 0, add_claims.output

    justifications_file = tmp_path / "justifications.yaml"
    justifications_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "justifications": [
                    {
                        "id": "just1",
                        "conclusion": "claim2",
                        "premises": ["claim1"],
                        "rule_kind": "empirical_support",
                        "provenance": {"page": 3},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_justifications = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "add-justification", "demo", "--batch", str(justifications_file)],
    )
    assert add_justifications.exit_code == 0, add_justifications.output

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "stances": [
                    {
                        "source_claim": "claim1",
                        "target": "claim2",
                        "type": "supports",
                        "note": "parameter supports observation",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_stances = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "add-stance", "demo", "--batch", str(stances_file)],
    )
    assert add_stances.exit_code == 0, add_stances.output

    finalize = runner.invoke(cli, ["-C", str(repo.root), "source", "finalize", "demo"])
    assert finalize.exit_code == 0, finalize.output
    promote = runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"])
    assert promote.exit_code == 0, promote.output

    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    claim_id = claims_doc["claims"][1]["artifact_id"]
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.git.head_sha())
    papers_dir = repo.root.parent / "papers" / "demo"
    papers_dir.mkdir(parents=True, exist_ok=True)
    (papers_dir / "paper.pdf").write_bytes(content_file.read_bytes())
    return repo, claim_id


def test_source_finalize_persists_artifact_codes(tmp_path: Path) -> None:
    repo, _claim_id = _prepare_promoted_source(tmp_path)

    source_tip = repo.git.branch_sha("source/demo")
    assert source_tip is not None
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=source_tip))
    claims_doc = yaml.safe_load(repo.git.read_file("claims.yaml", commit=source_tip))
    justifications_doc = yaml.safe_load(repo.git.read_file("justifications.yaml", commit=source_tip))
    stances_doc = yaml.safe_load(repo.git.read_file("stances.yaml", commit=source_tip))

    assert source_doc["artifact_code"].startswith("sha256:")
    assert claims_doc["claims"][0]["artifact_code"].startswith("sha256:")
    assert justifications_doc["justifications"][0]["artifact_code"].startswith("sha256:")
    assert stances_doc["stances"][0]["artifact_code"].startswith("sha256:")


def test_verify_tree_reports_ok_and_origin_match(tmp_path: Path) -> None:
    repo, claim_id = _prepare_promoted_source(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["-C", str(repo.root), "verify", "tree", claim_id])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load(result.output)
    assert report["status"] == "ok"
    assert report["claim"]["status"] == "ok"
    assert report["origin_verification"]["status"] == "matched"
    assert report["atms_label"] == [[]]


def test_verify_tree_reports_claim_mismatch(tmp_path: Path) -> None:
    repo, claim_id = _prepare_promoted_source(tmp_path)
    runner = CliRunner()

    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    claims_doc["claims"][1]["artifact_code"] = "sha256:" + ("0" * 64)
    repo.git.commit_batch(
        adds={
            "claims/demo.yaml": yaml.safe_dump(
                claims_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Corrupt stored artifact code",
        branch="master",
    )
    repo.git.sync_worktree()

    result = runner.invoke(cli, ["-C", str(repo.root), "verify", "tree", claim_id])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load(result.output)
    assert report["status"] == "mismatch"
    assert report["claim"]["status"] == "mismatch"


def test_verify_tree_atms_failure_propagates(tmp_path: Path) -> None:
    repo, claim_id = _prepare_promoted_source(tmp_path)
    runner = CliRunner()

    with patch("propstore.world.WorldModel.bind", side_effect=RuntimeError("atms boom")):
        result = runner.invoke(cli, ["-C", str(repo.root), "verify", "tree", claim_id])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)
    assert "atms boom" in str(result.exception)


@given(order=st.permutations([0, 1]))
@settings(deadline=None)
def test_claim_artifact_codes_ignore_justification_and_stance_order(order: tuple[int, int]) -> None:
    source_doc = {
        "id": "tag:local@propstore,2026:source/demo",
        "kind": "academic_paper",
        "origin": {"type": "file", "value": "paper.pdf", "retrieved": "2026-04-04T00:00:00Z", "content_ref": "ni:///sha-256;abc"},
        "trust": {"prior_base_rate": 0.5, "quality": {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5}, "derived_from": []},
        "metadata": {"name": "demo"},
    }
    claims_doc = {
        "claims": [
            {
                "artifact_id": "ps:claim:a",
                "logical_ids": [{"namespace": "demo", "value": "claim_a"}],
                "version_id": "sha256:" + ("1" * 64),
                "type": "observation",
                "statement": "A",
            },
            {
                "artifact_id": "ps:claim:b",
                "logical_ids": [{"namespace": "demo", "value": "claim_b"}],
                "version_id": "sha256:" + ("2" * 64),
                "type": "observation",
                "statement": "B",
            },
        ]
    }
    justifications = [
        {"id": "j1", "conclusion": "ps:claim:b", "premises": ["ps:claim:a"], "rule_kind": "support"},
        {"id": "j2", "conclusion": "ps:claim:b", "premises": ["ps:claim:a"], "rule_kind": "support_2"},
    ]
    stances = [
        {"source_claim": "ps:claim:b", "target": "ps:claim:a", "type": "supports"},
        {"source_claim": "ps:claim:b", "target": "ps:claim:a", "type": "qualifies"},
    ]

    left = attach_source_artifact_codes(
        source_doc,
        claims_doc,
        {"justifications": [justifications[i] for i in order]},
        {"stances": [stances[i] for i in order]},
    )
    right = attach_source_artifact_codes(
        source_doc,
        claims_doc,
        {"justifications": justifications},
        {"stances": stances},
    )

    left_claim = next(claim for claim in left[1]["claims"] if claim["artifact_id"] == "ps:claim:b")
    right_claim = next(claim for claim in right[1]["claims"] if claim["artifact_id"] == "ps:claim:b")
    assert left_claim["artifact_code"] == right_claim["artifact_code"]

