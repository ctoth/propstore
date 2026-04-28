from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from tests.builders import (
    SourceClaimSpec,
    SourceJustificationSpec,
    SourceStanceSpec,
    source_claims_document,
    source_justifications_document,
    source_stances_document,
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
    repo.git.commit_batch(
        adds={
            "concepts/claims_identical.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
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
    claim_ids = _add_claims(
        repo,
        runner,
        "demo",
        tmp_path,
        [
            SourceClaimSpec(
                local_id="blocked",
                claim_type="observation",
                statement="Blocked claim.",
                concepts=("claims_identical",),
                page=1,
            ),
            SourceClaimSpec(
                local_id="valid",
                claim_type="observation",
                statement="Valid claim.",
                concepts=("claims_identical",),
                page=2,
            ),
        ],
    )
    stances_file = tmp_path / "demo-stances.yaml"
    _write_yaml(
        stances_file,
        source_stances_document(
            [
                SourceStanceSpec(
                    source_claim="blocked",
                    target="missing_source:claim404",
                    stance_type="rebuts",
                )
            ],
            paper="demo",
        ),
    )
    add_stances = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            "demo",
            "--batch",
            str(stances_file),
        ],
    )
    assert add_stances.exit_code == 0, add_stances.output
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
