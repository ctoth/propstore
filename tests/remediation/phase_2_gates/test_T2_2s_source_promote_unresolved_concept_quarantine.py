from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml
from click.testing import CliRunner
from quire.documents import convert_document_value

from propstore.cli import cli
from propstore.families.documents.sources import SourceClaimsDocument
from propstore.families.registry import ClaimsFileRef, SourceRef
from propstore.repository import Repository
from propstore.source import normalize_source_claims_payload, source_branch_name
from propstore.source.common import load_source_document
from tests.conftest import make_test_context_commit_entry
from tests.family_helpers import build_sidecar


def _save_source_claims_directly(
    repo: Repository,
    source_name: str,
    claims_payload: dict,
) -> None:
    source_doc = load_source_document(repo, source_name)
    raw_claims = convert_document_value(
        claims_payload,
        SourceClaimsDocument,
        source=f"{source_branch_name(source_name)}:claims.yaml",
    )
    normalized_claims, _ = normalize_source_claims_payload(
        raw_claims,
        source_uri=source_doc.id,
        source_namespace=source_name,
    )
    repo.families.source_claims.save(
        SourceRef(source_name),
        normalized_claims,
        message=f"Write drifted claims for {source_name}",
    )


def test_source_promote_unresolved_concept_mapping_quarantines_claim_not_valid_claims(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    repo.git.commit_batch(
        adds=dict(
            [
                make_test_context_commit_entry(),
                (
                    "forms/structural.yaml",
                    b"name: structural\ndimensionless: true\n",
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
            "demo",
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            "demo",
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
            "demo",
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
        "demo",
        {
            "source": {"paper": "demo"},
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

    finalize = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "finalize",
            "demo",
        ],
    )
    assert finalize.exit_code == 0, finalize.output

    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.snapshot.head_sha())

    promote = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "demo",
        ],
    )
    assert promote.exit_code == 0, promote.output

    claims_doc = repo.families.claims.require(ClaimsFileRef("demo"))
    promoted_statements = {claim.statement for claim in claims_doc.claims if claim.statement}
    assert promoted_statements == {"Known concept observation."}

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'promotion_blocked'
            """
        ).fetchall()
        blocked_rows = conn.execute(
            """
            SELECT branch, promotion_status
            FROM claim_core
            WHERE promotion_status = 'blocked'
            """
        ).fetchall()
    finally:
        conn.close()

    assert blocked_rows == [(source_branch_name("demo"), "blocked")]
    assert len(diagnostic_rows) == 1
    assert diagnostic_rows[0][:4] == ("claim", "promotion_blocked", "error", 1)
    assert "unresolved concept mappings: missing_concept" in diagnostic_rows[0][4]
