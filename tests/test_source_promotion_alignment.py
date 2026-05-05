from __future__ import annotations

import sqlite3
import subprocess
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
    SourceStancesDocument,
)
from propstore.source.promote import load_finalize_report


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


def test_promote_source_branch_does_not_expose_native_git_deletions(tmp_path: Path) -> None:
    """After `pks source promote`, native git must not see phantom deletes."""
    repo = Repository.init(tmp_path / "knowledge")

    _save_source(
        repo,
        "clean_index_paper",
        {
            "concepts": [
                {
                    "local_name": "velocity",
                    "proposed_name": "velocity",
                    "definition": "Speed with direction.",
                    "form": "quantity",
                }
            ]
        },
        claims_payload={
            "source": {"paper": "clean_index_paper"},
            "claims": [
                {
                    "id": "velocity_claim_local",
                    "type": "parameter",
                    "context": "ctx_test",
                    "concept": "velocity",
                    "value": 3.0,
                    "unit": "m/s",
                    "provenance": {"paper": "clean_index_paper", "page": 1},
                }
            ],
        },
    )

    result = promote_source_branch(repo, "clean_index_paper")
    assert result.commit_sha

    status = subprocess.run(
        ["git", "-C", str(repo.root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        assert "work tree" in status.stderr
        return
    assert status.stdout == "", (
        f"native git reported phantom worktree changes after promote: {status.stdout}"
    )


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

    result = promote_source_branch(repo, "paper_source")

    assert result.commit_sha
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
    assert claims_file.claims[0].output_concept == derive_concept_artifact_id("propstore", "gravity")
    assert concept_file.artifact_id == derive_concept_artifact_id("propstore", "gravity")


def test_source_promote_rejects_invalid_promoted_claim_before_master_commit(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _save_source(
        repo,
        "invalid_uncertainty",
        {
            "concepts": [
                {
                    "local_name": "hazard_ratio",
                    "proposed_name": "hazard_ratio",
                    "definition": "Ratio of hazard rates.",
                    "form": "ratio",
                }
            ]
        },
        claims_payload={
            "source": {"paper": "invalid_uncertainty"},
            "claims": [
                {
                    "id": "bad_ci",
                    "type": "parameter",
                    "context": "ctx_test",
                    "concept": "hazard_ratio",
                    "value": 0.98,
                    "lower_bound": 0.76,
                    "upper_bound": 1.26,
                    "uncertainty_type": "95% CI",
                    "provenance": {"paper": "invalid_uncertainty", "page": 1},
                }
            ],
        },
    )
    before = repo.snapshot.branch_head("master")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "invalid_uncertainty",
        ],
    )

    assert result.exit_code != 0
    assert "uncertainty_type without uncertainty" in result.output
    assert repo.snapshot.branch_head("master") == before


def test_source_promote_cli_rebuilds_sidecar_for_immediate_claim_list(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _seed_structural_form_via_git(repo)
    shared_concept_id = _seed_master_concept_via_git(repo, "shared_concept")
    _seed_master_context_via_git(repo)
    _init_cli_source(runner, repo, "visible_after_promote")

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "visible_after_promote"},
                "claims": [
                    {
                        "id": "visible_claim",
                        "type": "observation",
                        "context": "ctx_test",
                        "statement": "A visible promoted observation.",
                        "concepts": [shared_concept_id],
                        "provenance": {"page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    add_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "add-claim",
            "visible_after_promote",
            "--batch",
            str(claims_file),
        ],
    )
    assert add_result.exit_code == 0, add_result.output
    finalize_source_branch(repo, "visible_after_promote")

    promote_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "promote",
            "visible_after_promote",
        ],
    )
    assert promote_result.exit_code == 0, promote_result.output

    list_result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "claim",
            "list",
        ],
    )
    assert list_result.exit_code == 0, list_result.output
    assert "A visible promoted observation." in list_result.output


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


def _seed_structural_form_via_git(repo: Repository) -> None:
    repo.git.commit_batch(
        adds={
            "forms/structural.yaml": yaml.safe_dump(
                {"name": "structural", "dimensionless": True},
                sort_keys=False,
            ).encode("utf-8")
        },
        deletes=[],
        message="Seed structural form",
        branch="master",
    )


def _setup_source_with_partial_validity(
    tmp_path: Path, source_name: str = "mixed"
) -> Repository:
    """Build a source branch with valid claims plus legacy invalid stance YAML.

    The broken stance targets a nonexistent ``missing_source:claim_zzz``
    so ``finalize_source_branch`` flags it in ``stance_reference_errors``.
    The stance is written directly to simulate stale data from before
    proposal-time stance target validation existed.
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

    repo.families.source_stances.save(
        SourceRef(source_name),
        convert_document_value(
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
            SourceStancesDocument,
            source=f"{source_branch_name(source_name)}:stances.yaml",
        ),
        message=f"Write legacy invalid stance for {source_name}",
        branch=source_branch_name(source_name),
    )

    return repo


def test_promote_source_branch_does_not_block_claim_for_invalid_stance(
    tmp_path: Path,
) -> None:
    """Invalid stance references are stance errors, not claim blockers."""

    source_name = "mixed"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)

    finalize_source_branch(repo, source_name)
    finalize_report = load_finalize_report(repo, source_name)
    assert finalize_report is not None
    assert finalize_report.status == "blocked"
    assert "missing_source:claim_zzz" in finalize_report.stance_reference_errors

    # Build the primary-branch sidecar BEFORE promote. The sidecar must
    # exist for ``promote_source_branch`` to write mirror rows for blocked
    # claims into it.
    from tests.family_helpers import build_sidecar

    head = repo.snapshot.head_sha()
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=head)

    result = promote_source_branch(repo, source_name)
    assert result is not None, "partial promotion should return some marker, not raise"
    assert result.blocked_claims == ()

    claims_file = repo.families.claims.require(
        ClaimsFileRef(source_name),
    )
    promoted_statements = {
        claim.statement for claim in claims_file.claims if claim.statement
    }
    assert "First valid observation." in promoted_statements
    assert "Second valid observation." in promoted_statements
    assert "Claim whose stance targets a missing ref." in promoted_statements

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        blocked_rows = conn.execute(
            "SELECT id, branch, promotion_status FROM claim_core "
            "WHERE promotion_status = 'blocked'"
        ).fetchall()
        assert blocked_rows == []

        diag_rows = conn.execute(
            "SELECT claim_id, diagnostic_kind, blocking "
            "FROM build_diagnostics "
            "WHERE diagnostic_kind = 'promotion_blocked'"
        ).fetchall()
        assert diag_rows == []
    finally:
        conn.close()


def test_promote_source_branch_strict_flag_ignores_stance_only_errors(tmp_path: Path) -> None:
    """Strict promotion should not treat invalid stance metadata as a claim error."""

    source_name = "mixed_strict"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)

    result = promote_source_branch(repo, source_name, strict=True)
    assert result.blocked_claims == ()


def test_promote_source_branch_re_promote_after_fix(tmp_path: Path) -> None:
    """Re-promoting after fixing a previously-blocked claim lands that claim.

    Start with valid claims plus one invalid stance. First promote:
    claims promote and the invalid stance is skipped. Remove the broken
    stance, re-finalize, re-promote: the claim set remains promoted.
    """

    source_name = "mixed_refix"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    promote_source_branch(repo, source_name)

    claims_file = repo.families.claims.require(
        ClaimsFileRef(source_name),
    )
    initial_statements = {
        claim.statement for claim in claims_file.claims if claim.statement
    }
    assert "Claim whose stance targets a missing ref." in initial_statements

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
        "claim must remain promoted after its invalid stance metadata is removed"
    )


def test_source_paper_slug_matches_source_branch_stem_for_unicode_name(
    tmp_path: Path,
) -> None:
    """Regression test for Bug 3: source-branch and master-filename consistency.

    When a paper directory name contains non-ASCII characters (e.g.
    U+2010 HYPHEN), ``SourceBranchPlacement.branch_name`` replaces the
    unsafe char with ``_`` and then appends a 12-char sha1 digest
    (``--5265a1465b03``) so different unicode inputs do not collide
    after slugging. Meanwhile paper-slug derivation re-used
    ``normalize_source_slug`` which returned just the safe_slug with
    NO digest suffix — so master claim files were written under a
    different stem than the source branch. Depending on caller input
    form, that produced either the wrong master file or a duplicate
    file alongside the intended one.

    The fix: the new ``source_paper_slug`` helper produces the same
    stem as the source branch, and all paper-slug call sites route
    through it — so ``source/<stem>`` and
    ``knowledge/claims/<stem>.yaml`` share one logical id.
    """

    from propstore.source.common import (
        source_branch_name,
        source_paper_slug,
    )

    unicode_name = "McNeil_2018_EffectAspirinAll‐CauseMortality"  # U+2010

    branch = source_branch_name(unicode_name)
    assert branch.startswith("source/"), branch
    branch_stem = branch[len("source/"):]

    paper_slug = source_paper_slug(unicode_name)
    assert paper_slug == branch_stem, (
        f"paper_slug and branch stem disagree: paper_slug={paper_slug!r} "
        f"branch_stem={branch_stem!r}"
    )


def test_promote_source_branch_unicode_name_writes_single_branch_matching_stem(
    tmp_path: Path,
) -> None:
    """End-to-end: a source name with U+2010 HYPHEN promotes to a master
    filename that matches the source branch stem.

    Prior behavior (Bug 3): promote used the non-suffixed slug, so the
    master claim file was written under a different stem than the
    source branch. This test verifies the master claim filename
    equals ``<branch_stem>.yaml``.
    """

    from propstore.source.common import source_branch_name

    unicode_name = "UnicodeHyphen‐2026_paper"
    repo = Repository.init(tmp_path / "knowledge")

    _save_source(
        repo,
        unicode_name,
        {
            "concepts": [
                {
                    "local_name": "velocity",
                    "proposed_name": "velocity",
                    "definition": "Speed with direction.",
                    "form": "quantity",
                }
            ]
        },
        claims_payload={
            "source": {"paper": unicode_name},
            "claims": [
                {
                    "id": "velocity_claim_local",
                    "type": "parameter",
                    "context": "ctx_test",
                    "concept": "velocity",
                    "value": 3.0,
                    "unit": "m/s",
                    "provenance": {"paper": unicode_name, "page": 1},
                }
            ],
        },
    )

    result = promote_source_branch(repo, unicode_name)
    assert result.commit_sha

    branch = source_branch_name(unicode_name)
    assert branch.startswith("source/"), branch
    branch_stem = branch[len("source/"):]

    promoted_claim_refs = sorted(ref.name for ref in repo.families.claims.iter())
    assert promoted_claim_refs == [branch_stem], (
        f"expected single claim artifact {branch_stem}; got {promoted_claim_refs}"
    )


def test_promote_source_branch_does_not_advance_master_when_sidecar_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for Bug 2: promote atomicity.

    Previously, ``promote_source_branch`` committed to master first and
    wrote the blocked-sidecar mirror rows afterward. If the sidecar
    write raised (e.g. Bug 1's UNIQUE-id collision) the git commit was
    already on master — leaving a stacked promote commit with no
    corresponding sidecar row. The aspirin stance-backfill session
    accumulated 15 such tangled commits before anyone noticed.

    After the fix, a sidecar-write failure must NOT advance the master
    ref: either the sidecar is written before the git commit, or the
    two are bound in a single transaction that rolls back on failure.
    """

    source_name = "atomicity_paper"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    raw_claims = convert_document_value(
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
                    "id": "broken_source",
                    "type": "observation",
                    "context": "ctx_test",
                    "statement": "Claim whose concept mapping is missing.",
                    "concepts": ["missing_concept"],
                    "provenance": {"page": 3},
                },
            ],
        },
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
        message=f"Write drifted blocked claim for {source_name}",
        branch=source_branch_name(source_name),
    )
    finalize_source_branch(repo, source_name)

    from tests.family_helpers import build_sidecar

    head_before_build = repo.snapshot.head_sha()
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=head_before_build)

    master_branch = repo.snapshot.primary_branch_name()
    master_head_before = repo.snapshot.branch_head(master_branch)

    # Arrange a mid-flight sidecar failure.
    from propstore.source import promote as promote_module

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated sidecar write failure")

    monkeypatch.setattr(
        promote_module,
        "_write_promotion_blocked_sidecar_rows",
        _boom,
    )

    with pytest.raises(RuntimeError, match="simulated sidecar write failure"):
        promote_source_branch(repo, source_name)

    master_head_after = repo.snapshot.branch_head(master_branch)
    assert master_head_after == master_head_before, (
        "sidecar-write failure must not advance master; atomicity broken"
    )
