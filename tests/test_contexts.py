"""Phase 4 first-class ``ist(c, p)`` contexts + lifting algebra.

Contexts are flat first-class qualifiers: structured assumptions / parameters /
perspective, NO visibility hierarchy, NO ancestry. Cross-context flow exists only
through authored lifting rules. These prove the charter, the no-ancestry / no-leak
invariants, the LIFTED/BLOCKED/UNKNOWN decision algebra (condition-ir gated), and
the non-filtering sidecar projection.
"""

from __future__ import annotations

from pathlib import Path

import msgspec
import pytest
from condition_ir import ConceptInfo, ConditionSolver, KindType

from propstore.context_lifting import (
    IstProposition,
    LiftingException,
    LiftingSystem,
)
from propstore.families.contexts import (
    Context,
    ContextRepository,
    LiftingDecisionStatus,
    LiftingMode,
    LiftingRule,
)


def _category_solver(name: str, values: tuple[str, ...]) -> ConditionSolver:
    registry = {
        name: ConceptInfo(
            id=name,
            canonical_name=name,
            kind=KindType.CATEGORY,
            category_values=list(values),
            category_extensible=True,
        )
    }
    return ConditionSolver(registry)


def test_context_charter_carries_structured_assumptions_parameters_perspective() -> (
    None
):
    context = msgspec.convert(
        {
            "context_id": "ctx_a",
            "name": "Trial A",
            "assumptions": ["task == 'speech'"],
            "parameters": {"speaker": "speaker_a"},
            "perspective": "analyst",
        },
        Context,
    )
    assert context.assumptions == ("task == 'speech'",)
    assert context.parameters == {"speaker": "speaker_a"}
    assert context.perspective == "analyst"


@pytest.mark.parametrize("banned", ["inherits", "excludes"])
def test_context_document_rejects_visibility_hierarchy_fields(banned: str) -> None:
    with pytest.raises(msgspec.ValidationError, match=banned):
        msgspec.convert({"context_id": "c", "name": "n", banned: ["x"]}, Context)


def test_lifting_system_has_no_ancestry_visibility() -> None:
    root = Context(context_id="ctx_root", name="root")
    child = Context(context_id="ctx_child", name="child")
    system = LiftingSystem(contexts=(root, child))
    assert (
        system.materialize_lifted_assertions((IstProposition("ctx_root", "p"),)) == ()
    )
    assert system.lift_decisions_between("ctx_root", "ctx_child", "p") == ()


def test_source_assumptions_never_leak_into_target() -> None:
    source = Context(context_id="ctx_src", name="src", assumptions=("a == 1",))
    target = Context(context_id="ctx_tgt", name="tgt", assumptions=("b == 2",))
    rule = LiftingRule(rule_id="r", source_context="ctx_src", target_context="ctx_tgt")
    system = LiftingSystem(contexts=(source, target), lifting_rules=(rule,))
    assert system.effective_assumptions("ctx_tgt") == ("b == 2",)
    assert "a == 1" not in system.effective_assumptions("ctx_tgt")


def test_lifting_rule_with_unknown_context_is_rejected() -> None:
    only = Context(context_id="ctx_only", name="only")
    rule = LiftingRule(
        rule_id="r", source_context="ctx_missing", target_context="ctx_only"
    )
    with pytest.raises(ValueError, match="unknown source context"):
        LiftingSystem(contexts=(only,), lifting_rules=(rule,))


def test_lifting_decision_statuses_lifted_blocked_unknown() -> None:
    src = Context(context_id="ctx_src", name="src")
    tgt = Context(context_id="ctx_tgt", name="tgt")
    solver = _category_solver("task", ("speech", "text"))
    rule = LiftingRule(
        rule_id="r",
        source_context="ctx_src",
        target_context="ctx_tgt",
        conditions=('task == "speech"',),
    )
    system = LiftingSystem(contexts=(src, tgt), lifting_rules=(rule,))

    lifted = system.lift_decisions_between(
        "ctx_src", "ctx_tgt", "p", solver=solver, bindings={"task": "speech"}
    )
    assert [d.status for d in lifted] == [LiftingDecisionStatus.LIFTED]

    blocked = system.lift_decisions_between(
        "ctx_src", "ctx_tgt", "p", solver=solver, bindings={"task": "text"}
    )
    assert [d.status for d in blocked] == [LiftingDecisionStatus.BLOCKED]

    unknown = system.lift_decisions_between("ctx_src", "ctx_tgt", "p")
    assert [d.status for d in unknown] == [LiftingDecisionStatus.UNKNOWN]


def test_exception_marks_an_otherwise_lifted_decision_excepted_with_provenance() -> (
    None
):
    src = Context(context_id="ctx_src", name="src")
    tgt = Context(context_id="ctx_tgt", name="tgt")
    rule = LiftingRule(rule_id="r", source_context="ctx_src", target_context="ctx_tgt")
    exception = LiftingException(
        id="except-alpha",
        rule_id="r",
        target="ctx_tgt",
        proposition_id="p",
        clashing_set=("claim-x",),
        justification="known clash",
    )
    system = LiftingSystem(
        contexts=(src, tgt), lifting_rules=(rule,), lifting_exceptions=(exception,)
    )
    (decision,) = system.lift_decisions_between("ctx_src", "ctx_tgt", "p")
    assert decision.status is LiftingDecisionStatus.EXCEPTED
    assert decision.exception_id == "except-alpha"
    assert decision.clashing_set == ("claim-x",)
    assert decision.exception is not None


def test_sidecar_has_context_lifting_tables_and_no_exclusion_table(
    tmp_path: Path,
) -> None:
    repo = ContextRepository()
    repo.author(
        Context(context_id="c1", name="n", assumptions=("a == 1",)), message="m"
    )
    repo.author_lifting_rule(
        LiftingRule(
            rule_id="r1",
            source_context="c1",
            target_context="c1",
            mode=LiftingMode.BRIDGE,
        ),
        message="m",
    )
    schema = repo.build_sidecar(tmp_path / "side.db")
    tables = set(schema.tables)
    assert {"context", "lifting_rule", "lifting_materialization"} <= tables
    assert not any("exclusion" in table for table in tables)


def test_sidecar_round_trips_context_and_lifting_rule(tmp_path: Path) -> None:
    repo = ContextRepository()
    repo.author(
        Context(
            context_id="c1",
            name="n",
            assumptions=("a == 1",),
            parameters={"speaker": "x"},
            perspective="analyst",
        ),
        message="m",
    )
    repo.author_lifting_rule(
        LiftingRule(
            rule_id="r1",
            source_context="c1",
            target_context="c1",
            conditions=('task == "speech"',),
        ),
        message="m",
    )
    schema = repo.build_sidecar(tmp_path / "side.db")
    (context,) = repo.render_contexts(tmp_path / "side.db", schema)
    assert context.parameters == {"speaker": "x"}
    assert context.perspective == "analyst"
    assert context.assumptions == ("a == 1",)
    (rule,) = repo.render_lifting_rules(tmp_path / "side.db", schema)
    assert rule.conditions == ('task == "speech"',)
