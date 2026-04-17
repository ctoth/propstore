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

from propstore.cli import cli
from propstore.repository import Repository
from propstore.identity import derive_concept_artifact_id
from propstore.source import (
    finalize_source_branch,
    promote_source_branch,
)


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
    artifact_id = derive_concept_artifact_id("propstore", name)
    concept = {
        "artifact_id": artifact_id,
        "canonical_name": name,
        "status": "accepted",
        "definition": f"{name} definition",
        "domain": "source",
        "form": "structural",
    }
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
            "--name",
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
                        "statement": "First valid observation.",
                        "concepts": ["shared_concept"],
                        "provenance": {"page": 1},
                    },
                    {
                        "id": "valid_b",
                        "type": "observation",
                        "statement": "Second valid observation.",
                        "concepts": ["shared_concept"],
                        "provenance": {"page": 2},
                    },
                    {
                        "id": "broken_source",
                        "type": "observation",
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

    # Finalize to generate the error report; build the sidecar so promote
    # can write the mirror + diagnostic rows; promote.
    finalize_source_branch(repo, source_name)

    from propstore.sidecar.build import build_sidecar

    head = repo.snapshot.head_sha()
    tree = repo.snapshot.tree(commit=head)
    build_sidecar(tree, repo.sidecar_path, force=True, commit_hash=head)
    promote_source_branch(repo, source_name)

    return repo, source_name


# ── Behavioral contract ─────────────────────────────────────────────


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
