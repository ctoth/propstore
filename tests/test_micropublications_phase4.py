from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.artifacts.documents.micropubs import MicropublicationDocument
from propstore.artifacts.schema import convert_document_value
from propstore.cli import cli
from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from propstore.world import WorldModel
from propstore.world.types import Environment, ReasoningBackend, RenderPolicy


def test_micropublication_document_requires_claim_bundle() -> None:
    with pytest.raises(ValueError, match="claims"):
        convert_document_value(
            {
                "artifact_id": "ps:micropub:empty",
                "context": {"id": "ctx_test"},
                "claims": [],
                "provenance": {"paper": "demo", "page": 1},
            },
            MicropublicationDocument,
            source="micropubs/empty.yaml",
        )

    micropub = convert_document_value(
        {
            "artifact_id": "ps:micropub:claim1",
            "context": {"id": "ctx_test"},
            "claims": ["ps:claim:claim1"],
            "evidence": [{"kind": "paper_page", "reference": "demo:1"}],
            "assumptions": ["domain == 'argumentation'"],
            "stance": "supports",
            "provenance": {"paper": "demo", "page": 1},
        },
        MicropublicationDocument,
        source="micropubs/claim1.yaml",
    )

    assert micropub.context.id == "ctx_test"
    assert micropub.claims == ("ps:claim:claim1",)
    assert micropub.to_payload()["evidence"][0]["reference"] == "demo:1"


def _init_source_with_claim(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "context": "ctx_test",
                        "statement": "A micropublished claim",
                        "concepts": ["test_concept"],
                        "provenance": {"paper": "demo", "page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
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
    ).exit_code == 0
    assert runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            "demo",
            "--name",
            "test_concept",
            "--definition",
            "A test concept",
            "--form",
            "category",
        ],
    ).exit_code == 0
    result = runner.invoke(
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
    assert result.exit_code == 0, result.output
    return repo


def test_source_finalize_composes_claims_into_micropubs(tmp_path: Path) -> None:
    repo = _init_source_with_claim(tmp_path)

    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    micropubs = yaml.safe_load(repo.git.read_file("micropubs.yaml", commit=branch_tip))
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=branch_tip))

    assert report["micropub_status"] == "complete"
    assert len(micropubs["micropubs"]) == 1
    micropub = micropubs["micropubs"][0]
    assert micropub["claims"][0].startswith("ps:claim:")
    assert micropub["context"] == {"id": "ctx_test"}
    assert micropub["evidence"] == [{"kind": "paper_page", "reference": "demo:1"}]


def test_source_promote_writes_canonical_micropub_bundle(tmp_path: Path) -> None:
    repo = _init_source_with_claim(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"])
    assert result.exit_code == 0, result.output

    master_tip = repo.git.branch_sha("master")
    assert master_tip is not None
    promoted = yaml.safe_load(repo.git.read_file("micropubs/demo.yaml", commit=master_tip))
    promoted_claims = yaml.safe_load(repo.git.read_file("claims/demo.yaml", commit=master_tip))

    assert len(promoted["micropubs"]) == 1
    assert promoted["micropubs"][0]["claims"] == [
        promoted_claims["claims"][0]["artifact_id"]
    ]
    assert promoted_claims["claims"][0]["context"] == {"id": "ctx_test"}


def test_micropub_cli_show_bundle_and_lift(tmp_path: Path) -> None:
    repo = _init_source_with_claim(tmp_path)
    repo.git.commit_batch(
        adds={
            "contexts/ctx_test.yaml": yaml.safe_dump(
                {
                    "id": "ctx_test",
                    "name": "ctx_test",
                    "description": "Source context",
                    "lifting_rules": [
                        {
                            "id": "lift_test_target",
                            "source": "ctx_test",
                            "target": "ctx_target",
                            "mode": "bridge",
                        }
                    ],
                },
                sort_keys=False,
            ).encode("utf-8"),
            "contexts/ctx_target.yaml": yaml.safe_dump(
                {
                    "id": "ctx_target",
                    "name": "ctx_target",
                    "description": "Target context",
                },
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed test contexts",
        branch="master",
    )
    runner = CliRunner()
    promote_result = runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"])
    assert promote_result.exit_code == 0, promote_result.output

    promoted = yaml.safe_load(repo.git.read_file("micropubs/demo.yaml"))
    micropub_id = promoted["micropubs"][0]["artifact_id"]

    bundle_result = runner.invoke(cli, ["-C", str(repo.root), "micropub", "bundle", "demo"])
    assert bundle_result.exit_code == 0, bundle_result.output
    assert "micropubs:" in bundle_result.output
    assert micropub_id in bundle_result.output

    show_result = runner.invoke(cli, ["-C", str(repo.root), "micropub", "show", micropub_id])
    assert show_result.exit_code == 0, show_result.output
    assert "ctx_test" in show_result.output
    assert "ps:claim:" in show_result.output

    lift_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "micropub",
            "lift",
            micropub_id,
            "--target-context",
            "ctx_target",
        ],
    )
    assert lift_result.exit_code == 0, lift_result.output
    assert "liftable" in lift_result.output


def test_promoted_micropub_builds_as_atms_node(tmp_path: Path) -> None:
    repo = _init_source_with_claim(tmp_path)
    repo.git.commit_batch(
        adds={
            "contexts/ctx_test.yaml": yaml.safe_dump(
                {
                    "id": "ctx_test",
                    "name": "ctx_test",
                    "description": "Source context",
                },
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed test context",
        branch="master",
    )
    runner = CliRunner()
    promote_result = runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"])
    assert promote_result.exit_code == 0, promote_result.output

    promoted = yaml.safe_load(repo.git.read_file("micropubs/demo.yaml"))
    micropub_id = promoted["micropubs"][0]["artifact_id"]

    assert build_sidecar(repo.tree(), repo.sidecar_path, force=True) is True
    world = WorldModel(repo)
    assert [entry.artifact_id for entry in world.all_micropublications()] == [micropub_id]

    bound = world.bind(
        Environment(context_id="ctx_test"),
        policy=RenderPolicy(reasoning_backend=ReasoningBackend.ATMS),
    )
    engine = bound.atms_engine()

    assert engine.supported_micropub_ids() == {micropub_id}
    label = engine.micropub_label(micropub_id)
    assert label is not None
    assert label.environments[0].context_ids == ("ctx_test",)
