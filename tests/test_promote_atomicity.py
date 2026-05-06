from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.source import finalize_source_branch, promote_source_branch, source_branch_name
from propstore.source.promote import PromotionResult

from tests.family_helpers import build_sidecar
from tests.conftest import make_test_context_commit_entry
from tests.remediation.phase_2_gates.test_T2_2s_source_promote_unresolved_concept_quarantine import (
    _save_source_claims_directly,
)


def _setup_source_with_blocked_claim(
    tmp_path: Path,
    *,
    source_name: str,
):
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    repo.git.commit_batch(
        adds=dict(
            [
                make_test_context_commit_entry(),
                (
                    "forms/structural.yaml",
                    yaml.safe_dump(
                        {"name": "structural", "dimensionless": True},
                        sort_keys=False,
                    ).encode("utf-8"),
                ),
            ]
        ),
        deletes=[],
        message="Seed test context and form",
        branch="master",
    )
    init = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            source_name,
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            source_name,
        ],
    )
    assert init.exit_code == 0, init.output
    propose = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            source_name,
            "--concept-name",
            "known_concept",
            "--definition",
            "known_concept definition",
            "--form",
            "structural",
        ],
    )
    assert propose.exit_code == 0, propose.output
    _save_source_claims_directly(
        repo,
        source_name,
        {
            "source": {"paper": source_name},
            "claims": [
                {
                    "id": "valid_claim",
                    "type": "observation",
                    "statement": "Known concept observation.",
                    "concepts": ["known_concept"],
                    "context": "ctx_test",
                    "provenance": {"page": 1},
                },
                {
                    "id": "unresolved_claim",
                    "type": "observation",
                    "statement": "Unresolved concept observation.",
                    "concepts": ["missing_concept"],
                    "context": "ctx_test",
                    "provenance": {"page": 2},
                },
            ],
        },
    )
    return repo


def test_promote_returns_in_memory_blocked_diagnostics_after_committed_mirror(
    tmp_path: Path,
) -> None:
    source_name = "ws_c_partial"
    repo = _setup_source_with_blocked_claim(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.snapshot.head_sha())

    result = promote_source_branch(repo, source_name)

    assert isinstance(result, PromotionResult)
    assert result.commit_sha
    assert result.sidecar_mirror_ok is True
    assert result.sidecar_mirror_error is None
    assert result.blocked_claims
    assert result.blocked_diagnostics
    blocked_ids = {claim.artifact_id for claim in result.blocked_claims}
    assert set(result.blocked_diagnostics).issubset(blocked_ids)
    assert any(
        "unresolved concept mappings: missing_concept" in detail
        for diagnostics in result.blocked_diagnostics.values()
        for _, detail in diagnostics
    )

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        mirrored_rows = conn.execute(
            "SELECT id FROM claim_core WHERE branch = ? AND promotion_status = 'blocked'",
            (source_branch_name(source_name),),
        ).fetchall()
    finally:
        conn.close()
    assert {row[0] for row in mirrored_rows} == blocked_ids
