"""Tests for the Phase 4 ``pks source status <name>`` subcommand.

Closes axis-1 finding 3.3 (promotion visibility) per
``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``: the
new subcommand surfaces per-claim promotion outcome for the named
source branch, joining ``claim_core`` rows whose
``promotion_status IS NOT NULL`` (either promoted or blocked mirror
rows) with the matching ``build_diagnostics`` rows written during
partial promotion.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from quire.documents import convert_document_value

from propstore.cli import cli
from propstore.families.documents.sources import SourceClaimsDocument
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from propstore.source import (
    SourceStatusState,
    finalize_source_branch,
    inspect_source_status,
    normalize_source_claims_payload,
    promote_source_branch,
)
from propstore.source.common import load_source_document
from tests.conftest import TEST_CONTEXT_ID, make_test_context_commit_entry, normalize_concept_payloads


def _init_cli_source(runner: CliRunner, repo: Repository, name: str) -> None:
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
    adds = {
        f"concepts/{name}.yaml": yaml.safe_dump(
            concept, sort_keys=False, allow_unicode=True
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
        message=f"Seed concept {name}",
        branch="master",
    )
    return str(concept["artifact_id"])


def _save_source_claims_directly(
    repo: Repository,
    source_name: str,
    claims_payload: dict,
) -> None:
    source_doc = load_source_document(repo, source_name)
    raw_claims = convert_document_value(
        claims_payload,
        SourceClaimsDocument,
        source=f"source/{source_name}:claims.yaml",
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


@pytest.fixture()
def promoted_partial(tmp_path: Path) -> tuple[Repository, str]:
    """Build + promote a source with 2 valid + 1 blocked claim.

    Mirrors the fixture used by ``tests/test_source_promotion_alignment.py``
    but scoped to the subset needed for the status subcommand. Returns
    ``(repo, source_name)`` with the sidecar already populated with the
    blocked mirror row + diagnostic.
    """
    source_name = "mixed"
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    shared_concept_id = _seed_master_concept_via_git(repo, "shared_concept")
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

    _save_source_claims_directly(
        repo,
        source_name,
        {
            "source": {"paper": source_name},
            "claims": [
                {
                    "id": "valid_a",
                    "type": "observation",
                    "statement": "First valid observation.",
                    "concepts": [shared_concept_id],
                    "provenance": {"page": 1},
                    "context": TEST_CONTEXT_ID,
                },
                {
                    "id": "valid_b",
                    "type": "observation",
                    "statement": "Second valid observation.",
                    "concepts": [shared_concept_id],
                    "provenance": {"page": 2},
                    "context": TEST_CONTEXT_ID,
                },
                {
                    "id": "broken_source",
                    "type": "observation",
                    "statement": "Claim whose concept mapping is missing.",
                    "concepts": ["missing_concept"],
                    "provenance": {"page": 3},
                    "context": TEST_CONTEXT_ID,
                },
            ],
        },
    )

    # Finalize to generate the error report; build the sidecar so promote
    # can write the mirror + diagnostic rows; promote.
    finalize_source_branch(repo, source_name)

    from tests.family_helpers import build_sidecar

    head = repo.snapshot.head_sha()
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=head)
    promote_source_branch(repo, source_name)

    return repo, source_name


# ── Behavioral contract ─────────────────────────────────────────────


def test_source_status_report_lists_blocked_promotion_rows(
    promoted_partial: tuple[Repository, str]
) -> None:
    repo, source_name = promoted_partial

    report = inspect_source_status(repo, source_name)

    assert report.state is SourceStatusState.HAS_ROWS
    assert report.branch == "source/mixed"
    assert len(report.rows) == 1
    row = report.rows[0]
    assert row.promotion_status == "blocked"
    assert row.diagnostics
    assert any(
        diagnostic.kind == "promotion_blocked"
        or "unresolved" in diagnostic.message.lower()
        for diagnostic in row.diagnostics
    )


def test_source_status_report_marks_missing_sidecar(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    report = inspect_source_status(repo, "clean")

    assert report.state is SourceStatusState.SIDECAR_MISSING
    assert report.rows == ()


def test_source_status_lists_blocked_promotion_rows(
    promoted_partial: tuple[Repository, str]
) -> None:
    """``pks source status <name>`` surfaces the promotion-blocked
    claim with its diagnostic message."""
    repo, source_name = promoted_partial

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "status",
            source_name,
        ],
    )
    assert result.exit_code == 0, result.output
    # The blocked claim's mirror row should be present with its
    # artifact_id; correlating with the fixture's local id 'broken_source'
    # is sufficient — the subcommand prints the full id.
    assert "blocked" in result.output.lower()
    # At least one of the diagnostic-kind marker or its message should
    # appear in the rendered output.
    assert (
        "promotion_blocked" in result.output
        or "finalize error" in result.output
        or "unresolved" in result.output.lower()
    )


def test_source_status_excludes_promoted_claims(
    promoted_partial: tuple[Repository, str]
) -> None:
    """``pks source status <name>`` is scoped to the source branch; the
    two successfully-promoted claims (now on master) must NOT appear."""
    repo, source_name = promoted_partial

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "status",
            source_name,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "First valid observation." not in result.output
    assert "Second valid observation." not in result.output


def test_source_status_empty_source_reports_no_rows(tmp_path: Path) -> None:
    """Running against a fresh source with no finalize-error rows should
    succeed and emit a "no rows" indication rather than erroring out."""
    source_name = "clean"
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()
    _init_cli_source(runner, repo, source_name)

    result = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "source",
            "status",
            source_name,
        ],
    )
    assert result.exit_code == 0, result.output
    # Some indication that nothing matched, not a stack trace.
    assert (
        "no" in result.output.lower()
        or result.output.strip() == ""
        or "0" in result.output
    )
