from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import compiler_cmds
from propstore.compiler.workflows import BuildPhiGroup, RepositoryBuildReport


def test_build_renders_phi_group_glosses_once_per_kind(
    monkeypatch,
) -> None:
    report = RepositoryBuildReport(
        concept_count=1,
        claim_count=4,
        conflict_count=0,
        phi_node_count=3,
        warning_count=0,
        rebuilt=True,
        phi_groups=(
            BuildPhiGroup(
                key="PHI_NODE: ps:concept:1",
                claim_ids=("ps:claim:1", "ps:claim:2"),
            ),
            BuildPhiGroup(
                key="PHI_NODE: ps:concept:2",
                claim_ids=("ps:claim:3", "ps:claim:4"),
            ),
            BuildPhiGroup(
                key="CONTEXT_PHI_NODE: ps:concept:3",
                claim_ids=("ps:claim:5", "ps:claim:6"),
            ),
        ),
    )

    monkeypatch.setattr(
        compiler_cmds,
        "build_repository",
        lambda _repo, *, output, force: report,
    )

    result = CliRunner().invoke(
        compiler_cmds.build,
        obj={"repo": object()},
    )

    assert result.exit_code == 0, result.output
    assert (
        result.stderr.count(
            "PHI_NODE — concept slot with multiple competing claim branches "
            "in the same context"
        )
        == 1
    )
    assert (
        "CONTEXT_PHI_NODE — concept slot with competing branches across "
        "different contexts"
    ) in result.stderr
    assert "PHI_NODE: ps:concept:1 — 2 branches: ps:claim:1, ps:claim:2" in result.stderr
    assert "PHI_NODE: ps:concept:2 — 2 branches: ps:claim:3, ps:claim:4" in result.stderr
