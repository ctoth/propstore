from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.row_types import coerce_claim_row
from propstore.opinion import Opinion, discount, from_probability
from propstore.praf import NoCalibration, p_arg_from_claim
from tests.family_helpers import build_sidecar
from propstore.cli import cli
from propstore.repository import Repository
from propstore.world import WorldModel
from tests.conftest import normalize_claims_payload, normalize_concept_payloads, make_test_context_commit_entry


def test_p_arg_from_claim_uses_prior_base_rate_when_no_claim_evidence() -> None:
    opinion = p_arg_from_claim({"source_prior_base_rate": 0.62})
    assert isinstance(opinion, Opinion)
    assert opinion == Opinion.vacuous(a=0.62)
    assert opinion.provenance is not None


def test_p_arg_from_claim_builds_claim_evidence_opinion() -> None:
    opinion = p_arg_from_claim(
        {
            "source_prior_base_rate": 0.62,
            "claim_probability": 0.8,
            "effective_sample_size": 10,
        }
    )
    assert isinstance(opinion, Opinion)
    assert opinion == from_probability(0.8, 10, 0.62)
    assert opinion.provenance is not None


def test_p_arg_from_claim_discounts_claim_by_source_quality() -> None:
    claim = {
        "source_prior_base_rate": 0.62,
        "claim_probability": 0.8,
        "effective_sample_size": 10,
        "source_quality_opinion": {
            "b": 0.7,
            "d": 0.1,
            "u": 0.2,
            "a": 0.5,
        },
    }
    expected_claim = from_probability(0.8, 10, 0.62)
    expected = discount(Opinion(0.7, 0.1, 0.2, 0.5), expected_claim)
    actual = p_arg_from_claim(claim)
    assert isinstance(actual, Opinion)
    assert actual == expected
    assert actual.provenance is not None


def test_p_arg_from_claim_accepts_typed_claim_rows() -> None:
    claim = coerce_claim_row(
        {
            "id": "claim-1",
            "artifact_id": "claim-1",
            "source": {
                "trust": {
                    "prior_base_rate": 0.62,
                    "quality": {
                        "b": 0.7,
                        "d": 0.1,
                        "u": 0.2,
                        "a": 0.5,
                    },
                }
            },
            "claim_probability": 0.8,
            "effective_sample_size": 10,
        }
    )
    expected_claim = from_probability(0.8, 10, 0.62)
    expected = discount(Opinion(0.7, 0.1, 0.2, 0.5), expected_claim)
    actual = p_arg_from_claim(claim)
    assert isinstance(actual, Opinion)
    assert actual == expected
    assert actual.provenance is not None


def test_p_arg_from_claim_invalid_typed_input_propagates() -> None:
    with pytest.raises((TypeError, AttributeError)):
        p_arg_from_claim(object())


def test_p_arg_from_claim_ignores_sample_size_without_calibration_payload() -> None:
    result = p_arg_from_claim({"sample_size": 50})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_claim_calibration"


@given(
    prior=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
    probability=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    n_eff=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_p_arg_from_claim_expectation_stays_in_unit_interval(
    prior: float,
    probability: float,
    n_eff: float,
) -> None:
    opinion = p_arg_from_claim(
        {
            "source_prior_base_rate": prior,
            "claim_probability": probability,
            "effective_sample_size": n_eff,
        }
    )
    assert isinstance(opinion, Opinion)
    assert 0.0 <= opinion.expectation() <= 1.0


def test_p_arg_from_claim_rejects_invalid_source_quality_shape() -> None:
    with pytest.raises(ValueError):
        p_arg_from_claim(
            {
                "source_prior_base_rate": 0.62,
                "source_quality_opinion": {"b": 0.7},
            }
        )


def _seed_ratio_form(repo: Repository) -> None:
    repo.forms_dir.mkdir(parents=True, exist_ok=True)
    (repo.forms_dir / "ratio.yaml").write_text(
        yaml.safe_dump({"name": "ratio", "dimensionless": True}, sort_keys=False),
        encoding="utf-8",
    )


def _seed_calibration_claim(repo: Repository) -> None:
    _seed_ratio_form(repo)
    concept = normalize_concept_payloads(
        [
            {
                "id": "base_replication_rate",
                "canonical_name": "base_replication_rate",
                "status": "accepted",
                "definition": "Field-specific replication prior.",
                "domain": "meta",
                "form": "ratio",
            }
        ],
        default_domain="meta",
    )[0]
    context_path, context_body = make_test_context_commit_entry()
    repo.git.commit_batch(
        adds={
            context_path: context_body,
            "concepts/base_replication_rate.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Seed calibration concept",
        branch="master",
    )

    claims = normalize_claims_payload(
        {
            "source": {"paper": "calibration"},
            "claims": [
                {
                    "id": "replication_rate_psychology",
                    "type": "parameter",
                    "concept": concept["artifact_id"],
                    "value": 0.36,
                    "unit": "probability",
                    "conditions": ["domain == 'psychology'"],
                    "provenance": {"page": 1},
                }
            ],
        },
        default_namespace="calibration",
    )
    repo.git.commit_batch(
        adds={
            "claims/calibration.yaml": yaml.safe_dump(
                claims,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message="Seed calibration claims",
        branch="master",
    )
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.git.head_sha())


def test_source_finalize_derives_prior_base_rate_from_calibration_claims(tmp_path: Path) -> None:
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
        ["-C", str(repo.root), "source", "write-metadata", "demo", "--file", str(metadata_file)],
    )
    assert metadata_result.exit_code == 0, metadata_result.output

    finalize_result = runner.invoke(cli, ["-C", str(repo.root), "source", "finalize", "demo"])
    assert finalize_result.exit_code == 0, finalize_result.output

    branch_tip = repo.git.branch_sha("source/demo")
    source_doc = yaml.safe_load(repo.git.read_file("source.yaml", commit=branch_tip))
    assert source_doc["trust"]["prior_base_rate"] == pytest.approx(0.36)
    assert source_doc["trust"]["derived_from"]


def test_world_model_claim_rows_include_calibrated_source_prior(tmp_path: Path) -> None:
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
    assert runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "write-metadata", "demo", "--file", str(metadata_file)],
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
            "base_replication_rate",
            "--definition",
            "Field-specific replication prior.",
            "--form",
            "ratio",
        ],
    ).exit_code == 0

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
    assert runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "add-claim", "demo", "--batch", str(claims_file)],
    ).exit_code == 0
    assert runner.invoke(cli, ["-C", str(repo.root), "source", "finalize", "demo"]).exit_code == 0
    assert runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"]).exit_code == 0

    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.git.head_sha())
    claims_doc = yaml.safe_load(repo.git.read_file("claims/demo.yaml"))
    claim_id = claims_doc["claims"][0]["artifact_id"]
    wm = WorldModel(repo)
    try:
        claim = wm.get_claim(claim_id)
    finally:
        wm.close()

    assert claim is not None
    claim_data = coerce_claim_row(claim).to_dict()
    assert claim_data["source"]["trust"]["prior_base_rate"] == pytest.approx(0.36)
    opinion = p_arg_from_claim(claim_data)
    assert isinstance(opinion, Opinion)
    assert opinion == Opinion.vacuous(a=0.36)
    assert opinion.provenance is not None
