from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.families.registry import (
    CanonicalSourceRef,
    ConceptFileRef,
    SOURCE_BRANCH,
    SourceRef,
)
from propstore.cli import cli
from propstore.repository import Repository
from quire.documents import (
    convert_document_value,
    decode_document_batch_bytes,
    encode_yaml_value,
)
from propstore.families.claims.declaration import SOURCE_CLAIM_BATCH_SPEC
from propstore.families.concepts.declaration import SOURCE_CONCEPT_BATCH_SPEC
from propstore.families.identity.concepts import (
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims.lifecycle import normalize_source_claims_payload
from propstore.source import (
    finalize_source_branch,
    initial_source_document,
    promote_source_branch,
)
from propstore.families.sources.declaration import (
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)
from propstore.families.stances.declaration import (
    SourceStanceEntryDocument,
)
from propstore.source.promote import load_finalize_report
from tests.family_helpers import materialized_world_store_path


def _promoted_claims(repo: Repository):
    return [handle.document for handle in repo.families.claims.iter_handles()]


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


def _seed_master_context_via_git(repo: Repository, name: str = "ctx_test") -> None:
    try:
        repo.git.read_file(f"contexts/{name}.yaml")
        return
    except FileNotFoundError:
        pass
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


def _seed_form_via_git(repo: Repository, name: str) -> None:
    try:
        repo.git.read_file(f"forms/{name}.yaml")
        return
    except FileNotFoundError:
        pass
    repo.git.commit_batch(
        adds={
            f"forms/{name}.yaml": yaml.safe_dump(
                {
                    "name": name,
                    "dimensionless": name
                    in {"boolean", "category", "scalar", "structural"},
                },
                sort_keys=False,
            ).encode("utf-8")
        },
        deletes=[],
        message=f"Seed {name} form",
        branch="master",
    )


def _seed_structural_form_via_git(repo: Repository) -> None:
    _seed_form_via_git(repo, "structural")


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

    branch = repo.families.source_stances.address(SourceRef(source_name)).branch
    repo.families.source_stances.save(
        SourceRef(source_name),
        (
            convert_document_value(
                {
                    "source": {"paper": source_name},
                    "source_claim": "broken_source",
                    "type": "rebuts",
                    "target": "missing_source:claim_zzz",
                },
                SourceStanceEntryDocument,
                source=f"{branch}:stances.yaml[1]",
            ),
        ),
        message=f"Write legacy invalid stance for {source_name}",
        branch=branch,
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

    result = promote_source_branch(repo, source_name)
    assert result is not None, "partial promotion should return some marker, not raise"
    assert result.blocked_claims == ()

    promoted_statements = {
        claim.statement for claim in _promoted_claims(repo) if claim.statement
    }
    assert "First valid observation." in promoted_statements
    assert "Second valid observation." in promoted_statements
    assert "Claim whose stance targets a missing ref." in promoted_statements

    store_path = materialized_world_store_path(
        repo,
        force=True,
        commit_hash=repo.git.head_sha(),
    )
    conn = sqlite3.connect(store_path)
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


def test_promote_source_branch_strict_flag_ignores_stance_only_errors(
    tmp_path: Path,
) -> None:
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

    initial_statements = {
        claim.statement for claim in _promoted_claims(repo) if claim.statement
    }
    assert "Claim whose stance targets a missing ref." in initial_statements

    repo.families.source_stances.save(
        SourceRef(source_name),
        (),
        message=f"Remove broken stance from {source_name}",
        branch=repo.families.source_stances.address(SourceRef(source_name)).branch,
    )

    # Re-finalize: now status should be ready.
    finalize_source_branch(repo, source_name)
    promote_source_branch(repo, source_name)

    final_statements = {
        claim.statement for claim in _promoted_claims(repo) if claim.statement
    }
    assert "Claim whose stance targets a missing ref." in final_statements, (
        "claim must remain promoted after its invalid stance metadata is removed"
    )


def test_source_paper_slug_matches_source_branch_stem_for_unicode_name(
    tmp_path: Path,
) -> None:
    """Regression test for Bug 3: source-branch and master-filename consistency.

    When a paper directory name contains non-ASCII characters (e.g.
    U+2010 HYPHEN), ``SOURCE_BRANCH.branch_name`` replaces the
    unsafe char with ``_`` and then appends a sha256 digest so
    different unicode inputs do not collide
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

    from propstore.source.common import source_paper_slug

    unicode_name = "McNeil_2018_EffectAspirinAll‐CauseMortality"  # U+2010

    branch = SOURCE_BRANCH.branch_name(object(), SourceRef(unicode_name))
    assert branch.startswith("source/"), branch
    branch_stem = branch[len("source/") :]

    paper_slug = source_paper_slug(unicode_name)
    assert paper_slug == branch_stem, (
        f"paper_slug and branch stem disagree: paper_slug={paper_slug!r} "
        f"branch_stem={branch_stem!r}"
    )
