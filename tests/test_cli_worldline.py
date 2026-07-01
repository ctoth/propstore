"""CLI adapter tests for the ``pks worldline`` command family (slice W3).

Drives the whole subcommand surface (``create`` / ``run`` / ``show`` / ``list`` /
``diff`` / ``delete`` / ``build-journal`` / ``at-step``) through the root ``pks``
group with Click's :class:`CliRunner`, so the lazy registry entry
(``propstore.cli.worldline``) is exercised end to end. The adapters are thin: the
behaviour lives in :mod:`propstore.app.worldlines`; here we assert exit codes and
rendered output, and that expected owner failures (missing worldline, duplicate
create) map to non-zero exits with a helpful message.
"""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner, Result

from propstore.cli import cli
from propstore.core.environment import Environment
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.world import WorldQuery
from tests.app_render_helpers import build_demo_repo


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "worldline", *args])


def _repo_with_one_atom(tmp_path: Path) -> tuple[Repository, str]:
    """A repo with one parameter claim; returns (repo, its projected atom id)."""
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=10.0,
        ),
        message="m",
    )
    world = WorldQuery(repo)
    try:
        atoms = world.bind(Environment()).epistemic_state().base.atoms
    finally:
        world.close()
    assert atoms, "expected the single parameter claim to project to one atom"
    return repo, atoms[0].atom_id


# ── help / registry resolution ─────────────────────────────────────────────────


def test_worldline_help_lists_subcommands() -> None:
    result = CliRunner().invoke(cli, ["worldline", "--help"])
    assert result.exit_code == 0, result.output
    for name in ("create", "run", "show", "list", "diff", "delete", "build-journal", "at-step"):
        assert name in result.output


# ── create / show / list ───────────────────────────────────────────────────────


def test_create_then_show(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    created = _invoke(repo, ["create", "wl", "--target", "Speed"])
    assert created.exit_code == 0, created.output
    assert "Created worldline 'wl'" in created.output

    shown = _invoke(repo, ["show", "wl"])
    assert shown.exit_code == 0, shown.output
    assert "Worldline: wl" in shown.output
    assert "Speed" in shown.output
    assert "not yet materialized" in shown.output


def test_create_duplicate_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "wl", "--target", "Speed"]).exit_code == 0
    dup = _invoke(repo, ["create", "wl", "--target", "Speed"])
    assert dup.exit_code != 0
    assert "already exists" in dup.output


def test_show_missing_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_list_reports_pending_and_materialized(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "pending_wl", "--target", "Speed"]).exit_code == 0
    empty = _invoke(repo, ["list"])
    assert empty.exit_code == 0, empty.output
    assert "pending_wl" in empty.output
    assert "pending" in empty.output


# ── run / staleness ─────────────────────────────────────────────────────────────


def test_run_materializes(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["run", "wl", "--target", "Speed"])
    assert result.exit_code == 0, result.output
    assert "materialized" in result.output

    shown = _invoke(repo, ["show", "wl", "--check"])
    assert shown.exit_code == 0, shown.output
    assert "Computed:" in shown.output


def test_run_new_without_target_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["run", "wl"])
    assert result.exit_code != 0
    assert "target" in result.output.lower()


# ── diff ────────────────────────────────────────────────────────────────────────


def test_diff_two_materialized_worldlines(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["run", "wl_a", "--target", "Speed"]).exit_code == 0
    assert _invoke(repo, ["run", "wl_b", "--target", "Speed"]).exit_code == 0
    result = _invoke(repo, ["diff", "wl_a", "wl_b"])
    assert result.exit_code == 0, result.output
    assert "Comparing:" in result.output


def test_diff_unmaterialized_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "wl_a", "--target", "Speed"]).exit_code == 0
    assert _invoke(repo, ["create", "wl_b", "--target", "Speed"]).exit_code == 0
    result = _invoke(repo, ["diff", "wl_a", "wl_b"])
    assert result.exit_code != 0
    assert "materialized" in result.output.lower()


# ── delete ──────────────────────────────────────────────────────────────────────


def test_delete_then_missing(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "wl", "--target", "Speed"]).exit_code == 0
    deleted = _invoke(repo, ["delete", "wl"])
    assert deleted.exit_code == 0, deleted.output
    assert "Deleted worldline 'wl'" in deleted.output

    again = _invoke(repo, ["delete", "wl"])
    assert again.exit_code != 0
    assert "not found" in again.output.lower()


# ── journal: build-journal / at-step ────────────────────────────────────────────


def test_build_journal_and_at_step(tmp_path: Path) -> None:
    repo, atom_id = _repo_with_one_atom(tmp_path)
    atom = json.dumps({"kind": "assertion", "id": atom_id})
    created = _invoke(
        repo,
        [
            "create",
            "wl",
            "--target",
            "Speed",
            "--revision-operation",
            "revise",
            "--revision-atom",
            atom,
        ],
    )
    assert created.exit_code == 0, created.output

    built = _invoke(repo, ["build-journal", "wl"])
    assert built.exit_code == 0, built.output
    assert "Built journal for worldline 'wl'" in built.output
    assert "1 steps" in built.output

    at_step = _invoke(repo, ["at-step", "wl", "0"])
    assert at_step.exit_code == 0, at_step.output
    assert "cl1" in at_step.output


def test_build_journal_without_revision_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "wl", "--target", "Speed"]).exit_code == 0
    result = _invoke(repo, ["build-journal", "wl"])
    assert result.exit_code != 0
    assert "revision" in result.output.lower()


def test_at_step_without_journal_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    assert _invoke(repo, ["create", "wl", "--target", "Speed"]).exit_code == 0
    result = _invoke(repo, ["at-step", "wl", "0"])
    assert result.exit_code != 0
    assert "journal" in result.output.lower()
