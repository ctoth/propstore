"""Tests for propose-claim, propose-justification, propose-stance CLI commands."""
from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.cli.repository import Repository


def _init_source(runner: CliRunner, repo: Repository, name: str = "demo"):
    """Helper: init a source branch and return the result."""
    return runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "init", name,
            "--kind", "academic_paper",
            "--origin-type", "manual",
            "--origin-value", name,
        ],
    )


def _seed_forms(repo: Repository, form_names: list[str]) -> None:
    """Commit minimal form YAML files to master so form validation passes."""
    adds = {}
    for form_name in form_names:
        adds[f"forms/{form_name}.yaml"] = yaml.safe_dump(
            {"name": form_name}, sort_keys=False, allow_unicode=True,
        ).encode("utf-8")
    repo.git.commit_batch(
        adds=adds, deletes=[], message="Seed forms", branch="master",
    )


def _add_concepts(runner: CliRunner, repo: Repository, name: str, concepts: list[dict]) -> None:
    """Helper: add concepts via batch file."""
    concepts_file = repo.root.parent / "concepts_batch.yaml"
    concepts_file.write_text(
        yaml.safe_dump({"concepts": concepts}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "add-concepts", name,
            "--batch", str(concepts_file),
        ],
    )
    assert result.exit_code == 0, result.output


def test_propose_claim_observation(tmp_path: Path) -> None:
    """propose-claim with observation type should assign artifact_id."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "test_concept", "definition": "A test concept.", "form": "structural"},
    ])

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-claim", "demo",
            "--id", "claim1",
            "--type", "observation",
            "--statement", "Water boils at 100C.",
            "--page", "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "claim1" in result.output
    assert "observation" in result.output
    assert "artifact" in result.output.lower() or "ps:claim:" in result.output


def test_propose_claim_parameter(tmp_path: Path) -> None:
    """propose-claim with parameter type should include concept/value/unit."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["scalar"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "boiling_point", "definition": "Temperature at which water boils.", "form": "scalar"},
    ])

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-claim", "demo",
            "--id", "param1",
            "--type", "parameter",
            "--concept", "boiling_point",
            "--value", "100.0",
            "--unit", "celsius",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "param1" in result.output
    assert "parameter" in result.output

    # Verify the claim is stored on the branch
    branch_tip = repo.git.branch_sha("source/demo")
    claims_doc = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    claims = claims_doc["claims"]
    assert len(claims) == 1
    claim = claims[0]
    assert claim["source_local_id"] == "param1"
    assert claim["concept"] == "boiling_point"
    assert claim["value"] == 100.0
    assert claim["unit"] == "celsius"
    assert "artifact_id" in claim


def test_propose_claim_dedup(tmp_path: Path) -> None:
    """Proposing same claim id twice should result in only one entry."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "tc", "definition": "Test concept.", "form": "structural"},
    ])

    # First proposal
    result1 = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-claim", "demo",
            "--id", "claim1",
            "--type", "observation",
            "--statement", "First version.",
        ],
    )
    assert result1.exit_code == 0, result1.output

    # Second proposal with same id
    result2 = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-claim", "demo",
            "--id", "claim1",
            "--type", "observation",
            "--statement", "Updated version.",
        ],
    )
    assert result2.exit_code == 0, result2.output

    # Verify only one claim with this local id
    branch_tip = repo.git.branch_sha("source/demo")
    claims_doc = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    claims = claims_doc["claims"]
    local_ids = [c.get("source_local_id") for c in claims if isinstance(c, dict)]
    assert local_ids.count("claim1") == 1
    # Verify it's the updated version
    claim = [c for c in claims if c.get("source_local_id") == "claim1"][0]
    assert claim["statement"] == "Updated version."


def test_propose_justification(tmp_path: Path) -> None:
    """propose-justification should link two claims and resolve refs."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "tc", "definition": "Test concept.", "form": "structural"},
    ])

    # Add two claims first
    for claim_id, statement in [("c1", "Premise claim."), ("c2", "Conclusion claim.")]:
        r = runner.invoke(
            cli,
            [
                "-C", str(repo.root),
                "source", "propose-claim", "demo",
                "--id", claim_id,
                "--type", "observation",
                "--statement", statement,
            ],
        )
        assert r.exit_code == 0, r.output

    # Propose justification
    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-justification", "demo",
            "--id", "just1",
            "--conclusion", "c2",
            "--premises", "c1",
            "--rule-kind", "empirical_support",
            "--page", "3",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "just1" in result.output
    assert "empirical_support" in result.output

    # Verify stored justification has resolved artifact ids
    branch_tip = repo.git.branch_sha("source/demo")
    just_doc = yaml.safe_load(repo.git.read_file("justifications.yaml", commit=branch_tip))
    justs = just_doc["justifications"]
    assert len(justs) == 1
    j = justs[0]
    assert j["conclusion"].startswith("ps:claim:")
    assert all(p.startswith("ps:claim:") for p in j["premises"])


def test_propose_justification_bad_ref(tmp_path: Path) -> None:
    """propose-justification referencing nonexistent claim should error."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-justification", "demo",
            "--id", "just1",
            "--conclusion", "nonexistent",
            "--premises", "also_nonexistent",
            "--rule-kind", "empirical_support",
        ],
    )

    assert result.exit_code != 0, result.output
    assert "unresolved" in result.output.lower() or "error" in result.output.lower()


def test_propose_stance_local(tmp_path: Path) -> None:
    """propose-stance between two local claims should resolve refs."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "tc", "definition": "Test concept.", "form": "structural"},
    ])

    # Add two claims
    for claim_id, statement in [("c1", "First claim."), ("c2", "Second claim.")]:
        r = runner.invoke(
            cli,
            [
                "-C", str(repo.root),
                "source", "propose-claim", "demo",
                "--id", claim_id,
                "--type", "observation",
                "--statement", statement,
            ],
        )
        assert r.exit_code == 0, r.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-stance", "demo",
            "--source-claim", "c1",
            "--target", "c2",
            "--type", "supports",
            "--strength", "strong",
            "--note", "Supporting evidence.",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "c1" in result.output
    assert "supports" in result.output
    assert "c2" in result.output

    # Verify stored stance has resolved source_claim
    branch_tip = repo.git.branch_sha("source/demo")
    stances_doc = yaml.safe_load(repo.git.read_file("stances.yaml", commit=branch_tip))
    stances = stances_doc["stances"]
    assert len(stances) == 1
    s = stances[0]
    assert s["source_claim"].startswith("ps:claim:")


def test_propose_stance_cross_source(tmp_path: Path) -> None:
    """propose-stance with cross-source target should preserve it as-is."""
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_forms(repo, ["structural"])

    init_result = _init_source(runner, repo)
    assert init_result.exit_code == 0, init_result.output

    _add_concepts(runner, repo, "demo", [
        {"local_name": "tc", "definition": "Test concept.", "form": "structural"},
    ])

    # Add one claim
    r = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-claim", "demo",
            "--id", "c1",
            "--type", "observation",
            "--statement", "A claim.",
        ],
    )
    assert r.exit_code == 0, r.output

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "propose-stance", "demo",
            "--source-claim", "c1",
            "--target", "other_source:claim9",
            "--type", "rebuts",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "rebuts" in result.output

    # Verify cross-source target is preserved
    branch_tip = repo.git.branch_sha("source/demo")
    stances_doc = yaml.safe_load(repo.git.read_file("stances.yaml", commit=branch_tip))
    stances = stances_doc["stances"]
    assert len(stances) == 1
    assert stances[0]["target"] == "other_source:claim9"
