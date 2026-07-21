"""CLI adapter smoke tests for ``pks event`` (render-time coreference).

Drives the whole production path end to end through the CLI: author rival
merge-argument proposals, record their mutual attack, then render the
policy-dependent clusters — empty under grounded, rival clusters under preferred.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from propstore.cli import cli
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "event", *args])


def _propose(repo: Repository, supports: str) -> str:
    result = _invoke(repo, ["propose", "--supports", supports])
    assert result.exit_code == 0, result.output
    return result.output.strip()


def test_propose_attack_and_policy_dependent_clusters(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    first = _propose(repo, "claim_a,claim_b")
    second = _propose(repo, "claim_b,claim_c")
    assert first.startswith("cma:")

    for attacker, target in ((first, second), (second, first)):
        result = _invoke(repo, ["attack", attacker, target])
        assert result.exit_code == 0, result.output

    grounded = _invoke(repo, ["list", "--semantics", "grounded"])
    assert grounded.exit_code == 0, grounded.output
    assert "No coreference clusters." in grounded.output

    preferred = _invoke(repo, ["list", "--semantics", "preferred"])
    assert preferred.exit_code == 0, preferred.output
    assert "claim_a, claim_b" in preferred.output
    assert "claim_b, claim_c" in preferred.output


def test_show_claim_scoped_returns_rival_clusters(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    first = _propose(repo, "claim_a,claim_b")
    second = _propose(repo, "claim_b,claim_c")
    for attacker, target in ((first, second), (second, first)):
        assert _invoke(repo, ["attack", attacker, target]).exit_code == 0

    shown = _invoke(repo, ["show", "claim_b", "--semantics", "preferred"])
    assert shown.exit_code == 0, shown.output
    assert "claim_a, claim_b" in shown.output
    assert "claim_b, claim_c" in shown.output


def test_attack_unknown_argument_exits_nonzero(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    known = _propose(repo, "claim_a,claim_b")
    result = _invoke(repo, ["attack", known, "cma:missing"])
    assert result.exit_code != 0
    assert "cma:missing" in result.output
