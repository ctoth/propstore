from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st
from quire.documents import convert_document_value
from sqlalchemy import select

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.registry import world_schema
from propstore.families.registry import ClaimRef
from propstore.opinion import Opinion
from propstore.praf import NoCalibration, p_arg_from_claim
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.source.common import initial_source_document
from tests.family_helpers import materialized_world_store_path
from propstore.cli import cli
from propstore.repository import Repository
from propstore.world import WorldQuery
from tests.conftest import (
    normalize_claims_payload,
    normalize_concept_payloads,
    make_test_context_commit_entry,
)


def _test_provenance(operation: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(),
        operations=(operation,),
    )


def test_p_arg_from_claim_requires_prior_for_claim_evidence() -> None:
    result = p_arg_from_claim(
        _claim_with_metadata(claim_probability=0.8, effective_sample_size=10)
    )

    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_base_rate"
    assert "source_prior_base_rate" in result.missing_fields


def test_initial_source_document_does_not_fabricate_default_prior(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    source_doc = initial_source_document(
        repo,
        "demo",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="demo",
    )

    assert source_doc.trust.prior_base_rate is None
    assert source_doc.trust.quality is None


def test_p_arg_from_claim_invalid_typed_input_propagates() -> None:
    with pytest.raises((TypeError, AttributeError)):
        p_arg_from_claim(object())


def _seed_ratio_form(repo: Repository) -> None:
    repo.git.commit_files(
        {
            "forms/ratio.yaml": yaml.safe_dump(
                {"name": "ratio", "dimensionless": True},
                sort_keys=False,
            ).encode("utf-8")
        },
        "Seed ratio form",
    )


def test_source_finalize_leaves_defaulted_trust_for_argumentation_pipeline(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_calibration_claim(repo)
    runner = CliRunner()
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text('{"domain":"psychology"}', encoding="utf-8")

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
            "manual",
            "--origin-value",
            "demo",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    metadata_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "write-metadata",
            "demo",
            "--file",
            str(metadata_file),
        ],
    )
    assert metadata_result.exit_code == 0, metadata_result.output

    finalize_result = runner.invoke(
        cli, ["-C", str(repo.root), "source", "finalize", "demo"]
    )
    assert finalize_result.exit_code == 0, finalize_result.output

    branch_tip = repo.git.branch_sha("source/demo")
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["trust"]["status"] == "defaulted"
    assert "prior_base_rate" not in source_doc["trust"]
    assert source_doc["trust"]["derived_from"] == []


def test_world_query_claim_source_does_not_fabricate_source_prior(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_batch(
        adds={
            "forms/ratio.yaml": yaml.safe_dump(
                {"name": "ratio", "dimensionless": True},
                sort_keys=False,
            ).encode("utf-8"),
            "contexts/ctx_test.yaml": yaml.safe_dump(
                {"id": "ctx_test", "name": "ctx_test"},
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed source promotion dependencies",
        branch="master",
    )
    _seed_calibration_claim(repo)
    runner = CliRunner()
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text('{"domain":"psychology"}', encoding="utf-8")

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
            "manual",
            "--origin-value",
            "demo",
        ],
    )
    assert init_result.exit_code == 0, init_result.output
    assert (
        runner.invoke(
            cli,
            [
                "-C",
                str(repo.root),
                "source",
                "write-metadata",
                "demo",
                "--file",
                str(metadata_file),
            ],
        ).exit_code
        == 0
    )

    assert (
        runner.invoke(
            cli,
            [
                "-C",
                str(repo.root),
                "source",
                "propose-concept",
                "demo",
                "--concept-name",
                "base_replication_rate",
                "--definition",
                "Field-specific replication prior.",
                "--form",
                "ratio",
            ],
        ).exit_code
        == 0
    )

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "parameter",
                        "concept": "base_replication_rate",
                        "value": 0.4,
                        "unit": "probability",
                        "context": "ctx_test",
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    assert (
        runner.invoke(
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
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            cli, ["-C", str(repo.root), "source", "finalize", "demo"]
        ).exit_code
        == 0
    )
    promote_result = runner.invoke(
        cli, ["-C", str(repo.root), "source", "promote", "demo"]
    )
    assert promote_result.exit_code == 0, promote_result.output

    materialized_world_store_path(
        repo,
        force=True,
        commit_hash=repo.git.head_sha(),
    )
    claim_id = next(repo.families.claims.iter_handles()).ref.artifact_id
    wm = WorldQuery(repo)
    try:
        claim = wm.get_claim(claim_id)
        schema = world_schema()
        source_model = schema.model("source")
        with wm._derived_store.readonly_session(schema) as derived:
            source = derived.execute(
                select(source_model).where(source_model.slug == "demo")
            ).scalar_one()
    finally:
        wm.close()

    assert claim is not None
    assert source.trust.prior_base_rate is None
    result = p_arg_from_claim(
        _claim_with_metadata(
            source={"trust": {"prior_base_rate": source.trust.prior_base_rate}}
        )
    )
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_claim_calibration"
