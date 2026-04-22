from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.families.registry import (
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptAlignmentRef,
    ConceptFileRef,
    SourceRef,
)
from propstore.cli import cli
from propstore.repository import Repository
from quire.documents import convert_document_value
from propstore.families.identity.concepts import (
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.source import (
    align_sources,
    concept_proposal_branch,
    decide_alignment,
    finalize_source_branch,
    initial_source_document,
    load_alignment_artifact,
    normalize_source_claims_payload,
    promote_alignment,
    promote_source_branch,
    source_branch_name,
)
from propstore.families.documents.sources import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)


def _save_source(repo: Repository, source_name: str, concepts_payload: dict, claims_payload: dict | None = None) -> None:
    branch = source_branch_name(source_name)
    repo.snapshot.ensure_branch(branch)

    source_doc = initial_source_document(
        repo,
        source_name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=source_name,
    )
    repo.families.source_documents.save(
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
    )

    concepts_doc = convert_document_value(
        concepts_payload,
        SourceConceptsDocument,
        source=f"{branch}:concepts.yaml",
    )
    repo.families.source_concepts.save(
        SourceRef(source_name),
        concepts_doc,
        message=f"Write concepts for {source_name}",
    )

    if claims_payload is None:
        return

    raw_claims = convert_document_value(
        claims_payload,
        SourceClaimsDocument,
        source=f"{branch}:claims.yaml",
    )
    normalized_claims, _ = normalize_source_claims_payload(
        raw_claims,
        source_uri=source_doc.id,
        source_namespace=source_name,
    )
    repo.families.source_claims.save(
        SourceRef(source_name),
        normalized_claims,
        message=f"Write claims for {source_name}",
    )

    report = SourceFinalizeReportDocument(
        kind="source_finalize_report",
        source=str(source_doc.id),
        status="ready",
        claim_reference_errors=(),
        justification_reference_errors=(),
        stance_reference_errors=(),
        concept_alignment_candidates=(),
        parameterization_group_merges=(),
        artifact_code_status="incomplete",
        calibration=SourceFinalizeCalibrationDocument(
            prior_base_rate_status="fallback",
            source_quality_status="vacuous",
            fallback_to_default_base_rate=True,
        ),
    )
    repo.families.source_finalize_reports.save(
        SourceRef(source_name),
        report,
        message=f"Finalize {source_name}",
    )


def test_align_and_promote_alignment_use_artifact_store(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.snapshot.ensure_branch(concept_proposal_branch(repo))

    _save_source(
        repo,
        "paper_a",
        {
            "concepts": [
                {
                    "local_name": "gravity",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
    )
    _save_source(
        repo,
        "paper_b",
        {
            "concepts": [
                {
                    "local_name": "gravity_constant",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
    )

    artifact = align_sources(
        repo,
        [source_branch_name("paper_a"), source_branch_name("paper_b")],
    )
    slug = artifact.id.split(":", 1)[1]
    stored = repo.families.concept_alignments.require(
        ConceptAlignmentRef(slug),
    )
    assert stored.to_payload() == artifact.to_payload()

    decided = decide_alignment(repo, artifact.id, accept=[artifact.arguments[0].id], reject=[])
    assert decided.decision.status == "decided"

    promoted = promote_alignment(repo, artifact.id)
    promoted_concept = repo.families.concepts.require(
        ConceptFileRef("gravity"),
    )
    reloaded_alignment = load_alignment_artifact(repo, artifact.id)[1]

    assert promoted.decision.status == "promoted"
    assert promoted_concept.lexical_entry.canonical_form.written_rep == "gravity"
    assert reloaded_alignment.decision.status == "promoted"


def test_promote_source_branch_writes_canonical_artifact_families(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    _save_source(
        repo,
        "paper_source",
        {
            "concepts": [
                {
                    "local_name": "gravity",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
        claims_payload={
            "source": {"paper": "paper_source"},
            "claims": [
                {
                    "id": "gravity_claim_local",
                    "type": "parameter",
                    "context": "ctx_test",
                    "concept": "gravity",
                    "value": 9.81,
                    "unit": "m/s^2",
                    "provenance": {"paper": "paper_source", "page": 1},
                }
            ],
        },
    )

    commit_sha = promote_source_branch(repo, "paper_source")

    assert commit_sha
    canonical_source = repo.families.sources.require(
        CanonicalSourceRef("paper_source"),
    )
    claims_file = repo.families.claims.require(
        ClaimsFileRef("paper_source"),
    )
    concept_file = repo.families.concepts.require(
        ConceptFileRef("gravity"),
    )

    assert canonical_source.metadata is not None
    assert claims_file.claims[0].concept == derive_concept_artifact_id("propstore", "gravity")
    assert concept_file.artifact_id == derive_concept_artifact_id("propstore", "gravity")


def _init_cli_source(runner: CliRunner, repo: Repository, name: str) -> None:
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


def _seed_master_concept_via_git(repo: Repository, name: str) -> str:
    """Seed a canonical concept on master so source claims can resolve to it."""

    concept = normalize_canonical_concept_payload(
        {
            "canonical_name": name,
            "status": "accepted",
            "definition": f"{name} definition",
            "domain": "propstore",
            "form": "structural",
        },
        local_handle=name,
    )
    artifact_id = derive_concept_artifact_id("propstore", name)
    repo.git.commit_batch(
        adds={
            f"concepts/{name}.yaml": yaml.safe_dump(
                concept, sort_keys=False, allow_unicode=True
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed concept {name}",
        branch="master",
    )
    return artifact_id


def _seed_master_context_via_git(repo: Repository, name: str = "ctx_test") -> None:
    repo.git.commit_batch(
        adds={
            f"contexts/{name}.yaml": yaml.safe_dump(
                {
                    "id": name,
                    "name": name,
                    "description": "Test context",
                },
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed context {name}",
        branch="master",
    )


def _setup_source_with_partial_validity(
    tmp_path: Path, source_name: str = "mixed"
) -> Repository:
    """Build a source branch with 2 valid claims + 1 broken-stance claim.

    The broken stance targets a nonexistent ``missing_source:claim_zzz``
    so ``finalize_source_branch`` flags it in ``stance_reference_errors``
    and the report status is ``'blocked'``. The finalize error is
    per-stance (not per-claim), so the finalize machinery still resolves
    the claim artifact_ids; the block is at promote time for the
    broken-stance claim only.
    """

    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_master_context_via_git(repo)
    _seed_master_concept_via_git(repo, "shared_concept")
    _init_cli_source(runner, repo, source_name)

    runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "propose-concept",
            source_name,
            "--concept-name",
            "shared_concept",
            "--definition",
            "A shared concept definition.",
            "--form",
            "structural",
        ],
    )

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": source_name},
                "claims": [
                        {
                            "id": "valid_a",
                            "type": "observation",
                            "context": "ctx_test",
                            "statement": "First valid observation.",
                        "concepts": ["shared_concept"],
                        "provenance": {"page": 1},
                    },
                        {
                            "id": "valid_b",
                            "type": "observation",
                            "context": "ctx_test",
                            "statement": "Second valid observation.",
                        "concepts": ["shared_concept"],
                        "provenance": {"page": 2},
                    },
                        {
                            "id": "broken_source",
                            "type": "observation",
                            "context": "ctx_test",
                            "statement": "Claim whose stance targets a missing ref.",
                        "concepts": ["shared_concept"],
                        "provenance": {"page": 3},
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
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

    stances_file = tmp_path / "stances.yaml"
    stances_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": source_name},
                "stances": [
                    {
                        "source_claim": "broken_source",
                        "type": "rebuts",
                        "target": "missing_source:claim_zzz",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-stance",
            source_name,
            "--batch",
            str(stances_file),
        ],
    )
    assert result.exit_code == 0, result.output

    return repo


def test_promote_source_branch_partial_allows_valid_claims_blocks_invalid(
    tmp_path: Path,
) -> None:
    """Partial promotion lands valid claims; invalid ones stay with blocked marker.

    Per ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    axis-1 finding 3.3: the former all-or-nothing gate
    (``report.status != 'ready'`` raised ValueError) becomes a
    per-item filter. Valid claims promote to the primary branch; claims
    with per-item finalize errors stay on the source branch with a
    ``promotion_status='blocked'`` sidecar mirror row and a
    ``build_diagnostics`` row (``diagnostic_kind='promotion_blocked'``,
    ``blocking=1``).
    """

    source_name = "mixed"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)

    # Finalize first — must report blocked status (broken stance).
    finalize_source_branch(repo, source_name)

    # Build the primary-branch sidecar BEFORE promote. The sidecar must
    # exist for ``promote_source_branch`` to write mirror rows for blocked
    # claims into it.
    from tests.family_helpers import build_sidecar

    head = repo.snapshot.head_sha()
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=head)

    # Promote must NOT raise under the new gate behavior.
    result = promote_source_branch(repo, source_name)
    assert result is not None, "partial promotion should return some marker, not raise"

    # Valid claims land on primary branch via CLAIMS_FILE_FAMILY.
    # Correlate by statement text since source_local_id is stripped on promote.
    claims_file = repo.families.claims.require(
        ClaimsFileRef(source_name),
    )
    promoted_statements = {
        claim.statement for claim in claims_file.claims if claim.statement
    }
    assert "First valid observation." in promoted_statements
    assert "Second valid observation." in promoted_statements
    assert "Claim whose stance targets a missing ref." not in promoted_statements, (
        "claim with broken stance must stay on source branch, not promote"
    )

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        blocked_rows = conn.execute(
            "SELECT id, branch, promotion_status FROM claim_core "
            "WHERE promotion_status = 'blocked'"
        ).fetchall()
        assert len(blocked_rows) >= 1, (
            "expected at least one claim_core row with promotion_status='blocked'"
        )
        for row in blocked_rows:
            _, branch, promotion_status = row
            assert promotion_status == "blocked"
            assert branch == source_branch_name(source_name)

        diag_rows = conn.execute(
            "SELECT claim_id, diagnostic_kind, blocking "
            "FROM build_diagnostics "
            "WHERE diagnostic_kind = 'promotion_blocked'"
        ).fetchall()
        assert len(diag_rows) >= 1, (
            "expected at least one build_diagnostics row for promotion_blocked"
        )
        for row in diag_rows:
            _, kind, blocking = row
            assert kind == "promotion_blocked"
            assert blocking == 1
    finally:
        conn.close()


def test_promote_source_branch_strict_flag_raises_on_partial(tmp_path: Path) -> None:
    """--strict flag preserves all-or-nothing behavior for callers that want it.

    Per the prompt (Q explicitly authorized partial promotion as the
    default; ``--strict`` is the opt-in for the old abort).
    """

    source_name = "mixed_strict"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)

    with pytest.raises(ValueError, match="strict"):
        promote_source_branch(repo, source_name, strict=True)


def test_promote_source_branch_re_promote_after_fix(tmp_path: Path) -> None:
    """Re-promoting after fixing a previously-blocked claim lands that claim.

    Start with 2 valid + 1 broken-stance claim. First promote:
    2 promoted, 1 blocked. Remove the broken stance, re-finalize,
    re-promote: the previously-blocked claim now promotes.
    """

    source_name = "mixed_refix"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    promote_source_branch(repo, source_name)

    # Verify initial state: broken_source not yet promoted.
    claims_file = repo.families.claims.require(
        ClaimsFileRef(source_name),
    )
    initial_statements = {
        claim.statement for claim in claims_file.claims if claim.statement
    }
    assert "Claim whose stance targets a missing ref." not in initial_statements

    # Fix: remove the broken stance by overwriting source stances with empty set.
    from propstore.families.documents.sources import SourceStancesDocument
    from propstore.source.common import source_branch_name as _branch_name

    repo.families.source_stances.save(
        SourceRef(source_name),
        SourceStancesDocument(stances=()),
        message=f"Remove broken stance from {source_name}",
        branch=_branch_name(source_name),
    )

    # Re-finalize: now status should be ready.
    finalize_source_branch(repo, source_name)
    promote_source_branch(repo, source_name)

    claims_file = repo.families.claims.require(
        ClaimsFileRef(source_name),
    )
    final_statements = {
        claim.statement for claim in claims_file.claims if claim.statement
    }
    assert "Claim whose stance targets a missing ref." in final_statements, (
        "previously-blocked claim must promote once its finalize error is fixed"
    )
