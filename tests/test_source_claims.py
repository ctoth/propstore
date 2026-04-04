from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.cli import cli
from propstore.cli.repository import Repository
from propstore.source_ops import normalize_source_claims_payload


@given(
    local_id_a=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=12,
    ),
    local_id_b=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=12,
    ),
)
@settings(max_examples=40, deadline=None)
def test_normalized_source_claim_ids_are_content_stable(local_id_a: str, local_id_b: str) -> None:
    claim_a = {
        "id": local_id_a,
        "type": "observation",
        "statement": "same semantic content",
        "provenance": {"page": 1},
    }
    claim_b = {
        "id": local_id_b,
        "type": "observation",
        "statement": "same semantic content",
        "provenance": {"page": 1},
    }

    payload_a = {"source": {"paper": "demo"}, "claims": [claim_a]}
    payload_b = {"source": {"paper": "demo"}, "claims": [claim_b]}

    normalized_a, _ = normalize_source_claims_payload(
        payload_a,
        source_uri="tag:local@propstore,2026:source/demo",
        source_namespace="demo",
    )
    normalized_b, _ = normalize_source_claims_payload(
        payload_b,
        source_uri="tag:local@propstore,2026:source/demo",
        source_namespace="demo",
    )

    first_a = normalized_a["claims"][0]
    first_b = normalized_b["claims"][0]
    assert first_a["artifact_id"] == first_b["artifact_id"]
    assert first_a["logical_ids"][0] == first_b["logical_ids"][0]
    assert first_a["source_local_id"] == local_id_a
    assert first_b["source_local_id"] == local_id_b


def test_source_add_claim_batch_normalizes_claims(tmp_path: Path) -> None:
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
                        "statement": "A claim",
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
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
            "manual",
            "--origin-value",
            "demo",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

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

    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    stored = yaml.safe_load(repo.git.read_file("claims.yaml", commit=branch_tip))
    claim = stored["claims"][0]
    assert claim["source_local_id"] == "claim1"
    assert claim["id"].startswith("claim_")
    assert claim["artifact_id"].startswith("ps:claim:")
    assert claim["version_id"].startswith("sha256:")


def test_source_finalize_writes_report(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

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

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert result.exit_code == 0, result.output

    branch_tip = repo.git.branch_sha("source/demo")
    assert branch_tip is not None
    report = yaml.safe_load(repo.git.read_file("merge/finalize/demo.yaml", commit=branch_tip))
    assert report["kind"] == "source_finalize_report"
    assert report["status"] == "ready"
    assert report["calibration"]["fallback_to_default_base_rate"] is True
