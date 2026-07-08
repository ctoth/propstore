"""Phase 4 non-commitment: an EXCEPTED lift stays recorded with provenance.

The reference asserted this through the worldline dependency tracker (Phase 7).
The Phase-4 surface contract is the one that must hold now: a lift targeted by
an authored exception is NOT dropped — it is projected into the
``lifting_materialization`` sidecar carrying its exception id and clashing set,
and only the render layer (status filtering) would hide it. Per Bozzato 2018
the exception's effect is resolved in the argumentation framework, so the
decision status is ``EXCEPTED``, not ``BLOCKED``.
"""

from __future__ import annotations

from pathlib import Path

from propstore.context_lifting import LiftingException, LiftingSystem
from propstore.families.contexts import (
    Context,
    ContextRepository,
    LiftingDecisionStatus,
    LiftingRule,
)


def _excepted_system() -> LiftingSystem:
    source = Context(context_id="ctx_source", name="source")
    target = Context(context_id="ctx_target", name="target")
    rule = LiftingRule(
        rule_id="lift-source-target",
        source_context="ctx_source",
        target_context="ctx_target",
    )
    exception = LiftingException(
        id="except-alpha",
        rule_id="lift-source-target",
        target="ctx_target",
        proposition_id="claim-a",
        clashing_set=("claim-b",),
        justification="authored clash",
    )
    return LiftingSystem(
        contexts=(source, target),
        lifting_rules=(rule,),
        lifting_exceptions=(exception,),
    )


def test_excepted_lift_is_recorded_with_provenance_and_not_dropped(
    tmp_path: Path,
) -> None:
    system = _excepted_system()
    decisions = system.lift_decisions_between("ctx_source", "ctx_target", "claim-a")
    assert [d.status for d in decisions] == [LiftingDecisionStatus.EXCEPTED]

    repo = ContextRepository()
    repo.author(Context(context_id="ctx_source", name="source"), message="m")
    repo.author(Context(context_id="ctx_target", name="target"), message="m")
    schema = repo.build_sidecar(tmp_path / "side.db", lifting_decisions=decisions)

    rows = repo.render_materializations(tmp_path / "side.db", schema)
    assert len(rows) == 1
    (row,) = rows
    assert row.status is LiftingDecisionStatus.EXCEPTED
    assert row.exception_id == "except-alpha"
    assert row.clashing_set == ("claim-b",)
    assert row.justification == "authored clash"


def test_lifted_and_excepted_both_land_so_render_can_filter(tmp_path: Path) -> None:
    system = _excepted_system()
    excepted = system.lift_decisions_between("ctx_source", "ctx_target", "claim-a")
    # A different proposition with no exception lifts cleanly.
    lifted = system.lift_decisions_between("ctx_source", "ctx_target", "claim-z")
    assert [d.status for d in lifted] == [LiftingDecisionStatus.LIFTED]

    repo = ContextRepository()
    repo.author(Context(context_id="ctx_source", name="source"), message="m")
    repo.author(Context(context_id="ctx_target", name="target"), message="m")
    schema = repo.build_sidecar(
        tmp_path / "side.db", lifting_decisions=excepted + lifted
    )
    rows = repo.render_materializations(tmp_path / "side.db", schema)
    assert sorted(r.status.value for r in rows) == ["excepted", "lifted"]
