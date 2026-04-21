from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.families.registry import ClaimsFileRef
from propstore.repository import Repository
from propstore.source import source_branch_name
from tests.conftest import normalize_concept_payloads
from tests.family_helpers import build_sidecar


def _seed_master_concept(repo: Repository, *, name: str) -> str:
    concept = normalize_concept_payloads(
        [
            {
                "id": name,
                "canonical_name": name,
                "status": "accepted",
                "definition": f"{name} definition",
                "domain": "source",
                "form": "structural",
            }
        ],
        default_domain="source",
    )[0]
    repo.git.commit_batch(
        adds={
            f"concepts/{name}.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed concept {name}",
        branch="master",
    )
    return str(concept["artifact_id"])


def test_source_promote_ambiguous_concept_quarantines_claim_not_valid_claims(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    known_artifact_id = _seed_master_concept(repo, name="known_concept")
    _seed_master_concept(repo, name="novel_concept")

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

    for concept_name in ("known_concept", "novel concept"):
        propose = runner.invoke(
            cli,
            [
                "-C",
                str(repo.root),
                "source",
                "propose-concept",
                "demo",
                "--name",
                concept_name,
                "--definition",
                f"{concept_name} definition",
                "--form",
                "structural",
            ],
        )
        assert propose.exit_code == 0, propose.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
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
                        "id": "ambiguous_claim",
                        "type": "observation",
                        "statement": "Ambiguous concept observation.",
                        "concepts": ["novel concept"],
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
    assert add_claims.exit_code == 0, add_claims.output

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
    assert claims_doc.claims[0].concepts == (known_artifact_id,)

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
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
    assert diagnostic_rows[0][0] == "claim"
    assert diagnostic_rows[0][2:5] == ("promotion_blocked", "error", 1)
    assert "ambiguous concept mappings: novel concept" in diagnostic_rows[0][5]
