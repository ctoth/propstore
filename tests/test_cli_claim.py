"""CLI adapter tests for the ``pks claim`` read-view family (Phase 10-1).

Exercises the thin Click adapters end-to-end through the root ``cli`` lazy
registry (``-C`` points it at the on-disk demo repo) against the real owner tier
(:mod:`propstore.app.claim_views`, :mod:`propstore.app.claims`,
:mod:`propstore.app.neighborhoods`). The corpus is the shared Phase 10-0 demo
repo, which already exercises every per-field view state plus BLOCKED / DRAFT
render-time filtering.

Ported and adapted from the reference ``test_cli`` claim display cases; cases
whose owner does not exist in the rewrite (``embed`` / ``similar`` / ``relate`` /
``validate`` / ``conflicts``) are deferred and noted in the worker report.
"""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner, Result

from tests.app_render_helpers import build_demo_repo
from propstore.cli import cli
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "claim", *args])


def test_show_renders_fields(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "p_speed"])
    assert result.exit_code == 0, result.output
    assert "Claim p_speed" in result.output
    assert "Value is 3.0 m/s" in result.output
    assert "The claim is about speed." in result.output


def test_show_json_shape(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "p_speed", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["claim_id"] == "p_speed"
    assert data["value"]["value"] == 3.0


def test_show_unknown_claim_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "nope"])
    assert result.exit_code != 0
    assert "Unknown claim: nope" in result.output


def test_show_blocked_claim_is_blocked_by_default(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "p_blocked"])
    assert result.exit_code != 0
    assert "blocked" in result.output.lower()


def test_show_blocked_claim_visible_with_include_blocked(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "p_blocked", "--include-blocked"])
    assert result.exit_code == 0, result.output
    assert "Claim p_blocked" in result.output


def test_list_shows_visible_hides_blocked(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["list"])
    assert result.exit_code == 0, result.output
    assert "p_speed" in result.output
    assert "p_blocked" not in result.output


def test_list_scoped_to_concept(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["list", "--concept", "speed"])
    assert result.exit_code == 0, result.output
    assert "p_speed" in result.output
    assert "p_missingval" not in result.output


def test_search_matches_text(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["search", "Speed"])
    assert result.exit_code == 0, result.output
    assert "p_speed" in result.output


def test_neighborhood_reports_supporters_and_attackers(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["neighborhood", "p_speed"])
    assert result.exit_code == 0, result.output
    assert "1 supporters" in result.output
    assert "1 attackers" in result.output


def test_neighborhood_unknown_claim_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["neighborhood", "nope"])
    assert result.exit_code != 0
    assert "Unknown claim: nope" in result.output


def _algo_repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "A", Concept(concept_id="A", canonical_name="A"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "alg1",
        Claim(
            claim_id="alg1",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="A",
            body="def f(x):\n    return x * 2 + 1\n",
        ),
        message="m",
    )
    repo.families.claim.save(
        "alg2",
        Claim(
            claim_id="alg2",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="A",
            body="def f(x):\n    return 2 * x + 1\n",
        ),
        message="m",
    )
    repo.families.claim.save(
        "p1",
        Claim(
            claim_id="p1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="A",
            value=3.0,
        ),
        message="m",
    )
    return repo


def _invoke_compare(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "claim", "compare", *args])


def test_compare_equivalent_bodies(tmp_path: Path) -> None:
    repo = _algo_repo(tmp_path)
    result = _invoke_compare(repo, ["alg1", "alg2"])
    assert result.exit_code == 0, result.output
    assert "equivalent" in result.output


def test_compare_json_shape(tmp_path: Path) -> None:
    repo = _algo_repo(tmp_path)
    result = _invoke_compare(repo, ["alg1", "alg2", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["equivalent"] is True


def test_compare_unknown_claim_fails(tmp_path: Path) -> None:
    repo = _algo_repo(tmp_path)
    result = _invoke_compare(repo, ["alg1", "nope"])
    assert result.exit_code != 0
    assert "nope" in result.output


def test_compare_non_algorithm_claim_fails(tmp_path: Path) -> None:
    repo = _algo_repo(tmp_path)
    result = _invoke_compare(repo, ["alg1", "p1"])
    assert result.exit_code != 0
    assert "algorithm" in result.output.lower()
