from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner
from quire.documents import convert_document_value

from propstore.cli import cli
from propstore.families.documents.sources import SourceClaimsDocument
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from propstore.source import normalize_source_claims_payload, source_branch_name
from propstore.source.common import load_source_document
from tests.builders import (
    SourceClaimSpec,
    SourceJustificationSpec,
    source_claims_document,
    source_justifications_document,
)
from tests.conftest import make_test_context_commit_entry, normalize_concept_payloads


def _seed_context(repo: Repository) -> None:
    context_path, context_body = make_test_context_commit_entry()
    try:
        repo.git.read_file(context_path)
    except FileNotFoundError:
        repo.git.commit_batch(
            adds={context_path: context_body},
            deletes=[],
            message="Seed test context",
            branch="master",
        )


def _seed_master_concept(repo: Repository) -> None:
    concept = normalize_concept_payloads(
        [
            {
                "id": "claims_identical",
                "canonical_name": "claims_identical",
                "status": "accepted",
                "definition": "A weak identity relation.",
                "domain": "source",
                "form": "structural",
            }
        ],
        default_domain="source",
    )[0]
    adds = {
        "concepts/claims_identical.yaml": yaml.safe_dump(
            concept,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
    }
    try:
        repo.git.read_file("forms/structural.yaml")
    except FileNotFoundError:
        adds["forms/structural.yaml"] = yaml.safe_dump(
            {"name": "structural", "dimensionless": True},
            sort_keys=False,
        ).encode("utf-8")
    repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message="Seed claims_identical concept",
        branch="master",
    )


def _init_source(repo: Repository, runner: CliRunner, name: str) -> None:
    _seed_context(repo)
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "init",
            name,
            "--kind",
            "academic_paper",
            "--origin-type",
            "manual",
            "--origin-value",
            name,
        ],
    )
    assert result.exit_code == 0, result.output


def _propose_claims_identical(repo: Repository, runner: CliRunner, source_name: str) -> None:
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            source_name,
            "--concept-name",
            "claims_identical",
            "--definition",
            "A weak identity relation.",
            "--form",
            "structural",
        ],
    )
    assert result.exit_code == 0, result.output


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _add_claims(
    repo: Repository,
    runner: CliRunner,
    source_name: str,
    tmp_path: Path,
    claims: list[SourceClaimSpec],
) -> dict[str, str]:
    claims_file = tmp_path / f"{source_name}-claims.yaml"
    _write_yaml(claims_file, source_claims_document(claims, paper=source_name))
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            source_name,
            "--batch",
            str(claims_file),
        ],
    )
    assert result.exit_code == 0, result.output
    source_head = repo.git.branch_sha(f"source/{source_name}")
    stored = yaml.safe_load(repo.git.read_file("claims.yaml", commit=source_head))
    return {claim["source_local_id"]: claim["artifact_id"] for claim in stored["claims"]}


def _save_claims_directly(
    repo: Repository,
    source_name: str,
    claims_payload: dict,
) -> dict[str, str]:
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
        branch=source_branch_name(source_name),
    )
    return {
        claim.source_local_id: claim.artifact_id
        for claim in normalized_claims.claims
        if claim.source_local_id is not None
    }


def _add_justification(
    repo: Repository,
    runner: CliRunner,
    source_name: str,
    tmp_path: Path,
    justification: SourceJustificationSpec,
) -> None:
    justifications_file = tmp_path / f"{source_name}-justifications.yaml"
    _write_yaml(
        justifications_file,
        source_justifications_document([justification], paper=source_name),
    )
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-justification",
            source_name,
            "--batch",
            str(justifications_file),
        ],
    )
    assert result.exit_code == 0, result.output


def _finalize_and_promote(repo: Repository, runner: CliRunner, source_name: str) -> None:
    finalize = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "finalize", source_name],
    )
    assert finalize.exit_code == 0, finalize.output
    promote = runner.invoke(
        cli,
        ["-C", str(repo.root), "source", "promote", source_name],
    )
    assert promote.exit_code == 0, promote.output


def _read_promoted_justifications(repo: Repository, source_name: str) -> list[dict[str, object]]:
    try:
        stored = yaml.safe_load(repo.git.read_file(f"justifications/{source_name}.yaml"))
    except FileNotFoundError:
        return []
    return list(stored.get("justifications") or [])


def test_promote_rejects_justification_reference_to_unpromoted_source_claim(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo)
    _init_source(repo, runner, "demo")
    _propose_claims_identical(repo, runner, "demo")
    claim_ids = _save_claims_directly(
        repo,
        "demo",
        {
            "source": {"paper": "demo"},
            "claims": [
                {
                    "id": "blocked",
                    "type": "observation",
                    "statement": "Blocked claim.",
                    "concepts": ["missing_concept"],
                    "context": "ctx_test",
                    "provenance": {"page": 1},
                },
                {
                    "id": "valid",
                    "type": "observation",
                    "statement": "Valid claim.",
                    "concepts": ["claims_identical"],
                    "context": "ctx_test",
                    "provenance": {"page": 2},
                },
            ],
        },
    )
    _add_justification(
        repo,
        runner,
        "demo",
        tmp_path,
        SourceJustificationSpec(
            local_id="j1",
            conclusion="valid",
            premises=("blocked",),
            rule_kind="empirical_support",
            page=3,
        ),
    )

    _finalize_and_promote(repo, runner, "demo")

    justifications = _read_promoted_justifications(repo, "demo")
    assert all(claim_ids["blocked"] not in item.get("premises", ()) for item in justifications)


def test_promote_accepts_justification_reference_to_master_claim(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_concept(repo)
    _init_source(repo, runner, "base")
    _propose_claims_identical(repo, runner, "base")
    _add_claims(
        repo,
        runner,
        "base",
        tmp_path,
        [
            SourceClaimSpec(
                local_id="master_premise",
                claim_type="observation",
                statement="Master premise.",
                concepts=("claims_identical",),
                page=1,
            )
        ],
    )
    _finalize_and_promote(repo, runner, "base")
    master_claims = yaml.safe_load(repo.git.read_file("claims/base.yaml"))
    master_claim_id = master_claims["claims"][0]["artifact_id"]

    _init_source(repo, runner, "demo")
    _propose_claims_identical(repo, runner, "demo")
    _add_claims(
        repo,
        runner,
        "demo",
        tmp_path,
        [
            SourceClaimSpec(
                local_id="new_conclusion",
                claim_type="observation",
                statement="New conclusion.",
                concepts=("claims_identical",),
                page=2,
            )
        ],
    )
    _add_justification(
        repo,
        runner,
        "demo",
        tmp_path,
        SourceJustificationSpec(
            local_id="j_master",
            conclusion="new_conclusion",
            premises=(master_claim_id,),
            rule_kind="empirical_support",
            page=3,
        ),
    )

    _finalize_and_promote(repo, runner, "demo")

    justifications = _read_promoted_justifications(repo, "demo")
    assert len(justifications) == 1
    assert justifications[0]["premises"] == [master_claim_id]
