from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st
from quire.documents import convert_document_value
from sqlalchemy import select

from propstore.families.claims.types import ClaimType
from propstore.core.graph_types import ClaimNode
from propstore.core.id_types import ClaimId
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims.documents import ClaimDocument
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
from tests.conftest import normalize_claims_payload, normalize_concept_payloads, make_test_context_commit_entry


def _prior_payload(a: float = 0.62) -> dict[str, float]:
    return {"b": 0.0, "d": 0.0, "u": 1.0, "a": a}


def _test_provenance(operation: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(),
        operations=(operation,),
    )


def _opinion_from_payload(payload: object, operation: str) -> Opinion:
    if isinstance(payload, Opinion):
        return payload
    if not isinstance(payload, dict):
        raise ValueError(f"{operation} must be an opinion mapping")
    required = {"b", "d", "u", "a"}
    if not required.issubset(payload):
        raise ValueError(f"{operation} must contain b, d, u, and a")
    return Opinion(
        float(payload["b"]),
        float(payload["d"]),
        float(payload["u"]),
        float(payload["a"]),
        _test_provenance(operation),
    )


def _claim_with_metadata(**metadata: object) -> ClaimNode:
    typed_keys = {
        "source_prior_base_rate",
        "source_quality_opinion",
        "claim_probability",
        "effective_sample_size",
        "confidence",
        "sample_size",
    }
    return ClaimNode(
        claim_id=ClaimId("test_claim"),
        claim_type=ClaimType.OBSERVATION,
        source_prior_opinion=(
            _opinion_from_payload(metadata["source_prior_base_rate"], "source_prior_base_rate")
            if "source_prior_base_rate" in metadata
            else None
        ),
        source_quality_opinion=(
            _opinion_from_payload(metadata["source_quality_opinion"], "source_quality_opinion")
            if "source_quality_opinion" in metadata
            else None
        ),
        claim_probability=metadata.get("claim_probability"),
        effective_sample_size=metadata.get("effective_sample_size"),
        confidence=metadata.get("confidence"),
        sample_size=metadata.get("sample_size"),
        attributes=tuple(
            (key, value) for key, value in metadata.items() if key not in typed_keys
        ),
    )


def test_p_arg_from_claim_uses_prior_base_rate_when_no_claim_evidence() -> None:
    prior = _prior_payload(0.62)
    opinion = p_arg_from_claim(_claim_with_metadata(source_prior_base_rate=prior))
    assert isinstance(opinion, Opinion)
    assert opinion == Opinion(**prior)
    assert opinion.provenance is not None


def test_p_arg_from_claim_builds_claim_evidence_opinion() -> None:
    opinion = p_arg_from_claim(
        _claim_with_metadata(
            source_prior_base_rate=_prior_payload(0.62),
            claim_probability=0.8,
            effective_sample_size=10,
        )
    )
    assert isinstance(opinion, Opinion)
    assert opinion == Opinion.from_probability(0.8, 10, 0.62)
    assert opinion.provenance is not None


def test_p_arg_from_claim_requires_prior_for_claim_evidence() -> None:
    result = p_arg_from_claim(
        _claim_with_metadata(claim_probability=0.8, effective_sample_size=10)
    )

    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_base_rate"
    assert "source_prior_base_rate" in result.missing_fields


def test_initial_source_document_does_not_fabricate_default_prior(tmp_path: Path) -> None:
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


def test_p_arg_from_claim_discounts_claim_by_source_quality() -> None:
    claim = _claim_with_metadata(
        source_prior_base_rate=_prior_payload(0.62),
        claim_probability=0.8,
        effective_sample_size=10,
        source_quality_opinion={
            "b": 0.7,
            "d": 0.1,
            "u": 0.2,
            "a": 0.5,
        },
    )
    expected_claim = Opinion.from_probability(0.8, 10, 0.62)
    expected = Opinion(0.7, 0.1, 0.2, 0.5).discount(expected_claim)
    actual = p_arg_from_claim(claim)
    assert isinstance(actual, Opinion)
    assert actual == expected
    assert actual.provenance is not None


def test_p_arg_from_claim_ignores_source_trust_mapping() -> None:
    claim = _claim_with_metadata(
        source={
            "trust": {
                "prior_base_rate": _prior_payload(0.62),
                "quality": {
                    "b": 0.7,
                    "d": 0.1,
                    "u": 0.2,
                    "a": 0.5,
                },
            },
        },
        claim_probability=0.8,
        effective_sample_size=10,
    )
    actual = p_arg_from_claim(claim)
    assert isinstance(actual, NoCalibration)
    assert actual.reason == "missing_base_rate"


def test_p_arg_from_claim_invalid_typed_input_propagates() -> None:
    with pytest.raises((TypeError, AttributeError)):
        p_arg_from_claim(object())


def test_p_arg_from_claim_ignores_sample_size_without_calibration_payload() -> None:
    result = p_arg_from_claim(_claim_with_metadata(sample_size=50))
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_claim_calibration"


@pytest.mark.property
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
        _claim_with_metadata(
            source_prior_base_rate=_prior_payload(prior),
            claim_probability=probability,
            effective_sample_size=n_eff,
        )
    )
    assert isinstance(opinion, Opinion)
    assert 0.0 <= opinion.expectation() <= 1.0


def test_p_arg_from_claim_rejects_invalid_source_quality_shape() -> None:
    with pytest.raises(ValueError):
        p_arg_from_claim(
            _claim_with_metadata(
                source_prior_base_rate=_prior_payload(0.62),
                source_quality_opinion={"b": 0.7},
            )
        )


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
                    "provenance": {"paper": "calibration", "page": 1},
                }
            ],
        },
        default_namespace="calibration",
    )
    claim_adds: dict[str, bytes] = {}
    for claim in claims["claims"]:
        claim_payload = {**claim, "source": claims["source"]}
        claim_doc = convert_document_value(
            claim_payload,
            ClaimDocument,
            source="test:calibration-claim",
        )
        assert claim_doc.artifact_id is not None
        ref = ClaimRef(claim_doc.artifact_id)
        claim_adds[repo.families.claims.address(ref).require_path()] = (
            repo.families.claims.render(claim_doc).encode("utf-8")
        )
    repo.git.commit_batch(
        adds=claim_adds,
        deletes=[],
        message="Seed calibration claims",
        branch="master",
    )
    materialized_world_store_path(
        repo,
        force=True,
        commit_hash=repo.git.head_sha(),
    )


def test_source_finalize_leaves_defaulted_trust_for_argumentation_pipeline(tmp_path: Path) -> None:
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
    assert source_doc["trust"]["status"] == "defaulted"
    assert "prior_base_rate" not in source_doc["trust"]
    assert "derived_from" not in source_doc["trust"]


def test_world_query_claim_source_does_not_fabricate_source_prior(tmp_path: Path) -> None:
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
            "--concept-name",
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
    promote_result = runner.invoke(cli, ["-C", str(repo.root), "source", "promote", "demo"])
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
