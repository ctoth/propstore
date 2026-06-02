"""Tests for first-class contexts and explicit lifting rules."""

from __future__ import annotations

import sqlite3
from sqlite3 import Connection
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from quire.sqlalchemy_store import (
    create_sqlalchemy_store,
    readonly_session,
    writable_session,
)
from quire.documents import DocumentSchemaError, LoadedDocument, convert_document_value
from propstore.families.contexts.declaration import ContextDocument
from propstore.conflict_detector import ConflictClass
from propstore.conflict_detector.context import _classify_pair_context
from propstore.families.contexts.lifting import (
    IstProposition,
    LiftingDecisionStatus,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions.refs import ContextReference
from propstore.families.contexts import load_contexts
from propstore.families.contexts.declaration import (
    CONTEXT_ASSUMPTION_CHARTER,
    CONTEXT_CHARTER,
    CONTEXT_LIFTING_RULE_CHARTER,
)
from propstore.families.contexts.passes import run_context_pipeline
from propstore.families.contexts.stages import (
    loaded_contexts_to_lifting_system,
)
from propstore.families.contexts.declaration import (
    compile_context_models,
)
from propstore.families.registry import world_schema
from propstore.world.bound import BoundWorld
from propstore.world.types import Environment
from tests.claim_model_helpers import make_claim
from tests.family_helpers import world_query_from_sqlite_path
from tests.sidecar_schema_helpers import build_world_projection_schema


def write_context(ctx_dir: Path, name: str, data: dict) -> Path:
    ctx_dir.mkdir(parents=True, exist_ok=True)
    path = ctx_dir / f"{name}.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


class TestLoadAndValidateContexts:
    def test_load_context_files(self, tmp_path: Path) -> None:
        write_context(tmp_path, "ctx_foo", make_context("ctx_foo", "Foo"))
        write_context(tmp_path, "ctx_bar", make_context("ctx_bar", "Bar"))

        contexts = load_contexts(tmp_path)

        assert len(contexts) == 2
        assert all(isinstance(context, LoadedDocument) for context in contexts)
        assert {str(context.document.id) for context in contexts} == {
            "ctx_foo",
            "ctx_bar",
        }

    def test_validate_structured_context_and_lifting_rule(self, tmp_path: Path) -> None:
        contexts = [
            loaded_context(
                "source", tmp_path / "source.yaml", make_context("ctx_source", "Source")
            ),
            loaded_context(
                "target",
                tmp_path / "target.yaml",
                make_context(
                    "ctx_target",
                    "Target",
                    assumptions=["framework == 'target'"],
                    parameters={"domain": "speech"},
                    perspective="experiment",
                    lifting_rules=[
                        {
                            "id": "lift-source-target",
                            "source": "ctx_source",
                            "target": "ctx_target",
                            "conditions": ["variant == 'controlled'"],
                            "mode": "bridge",
                            "justification": "Guha bridge rule",
                        }
                    ],
                ),
            ),
        ]

        result = run_context_pipeline(contexts)

        assert result.ok, tuple(error.render() for error in result.errors)

    def test_lifting_rule_must_reference_existing_contexts(
        self, tmp_path: Path
    ) -> None:
        contexts = [
            loaded_context(
                "target",
                tmp_path / "target.yaml",
                make_context(
                    "ctx_target",
                    "Target",
                    lifting_rules=[
                        {
                            "id": "lift-missing-target",
                            "source": "ctx_missing",
                            "target": "ctx_target",
                        }
                    ],
                ),
            ),
        ]

        result = run_context_pipeline(contexts)

        assert not result.ok
        assert any(
            "nonexistent source context" in error.render() for error in result.errors
        )


class TestLiftingSystem:
    def test_lifting_system_has_no_ancestry_visibility(self) -> None:
        system = loaded_contexts_to_lifting_system(
            [
                loaded_context("root", None, make_context("ctx_root", "Root")),
                loaded_context("child", None, make_context("ctx_child", "Child")),
            ]
        )

        assert (
            system.materialize_lifted_assertions(
                (
                    IstProposition(
                        context=ContextReference("ctx_root"),
                        proposition_id="claim_root",
                    ),
                )
            )
            == ()
        )
        assert (
            system.lift_decisions_between(
                "ctx_root",
                "ctx_child",
                "claim_root",
            )
            == ()
        )

    def test_explicit_lifting_rule_controls_visibility(self) -> None:
        system = loaded_contexts_to_lifting_system(
            [
                loaded_context("root", None, make_context("ctx_root", "Root")),
                loaded_context(
                    "child",
                    None,
                    make_context(
                        "ctx_child",
                        "Child",
                        lifting_rules=[
                            {
                                "id": "lift-root-child",
                                "source": "ctx_root",
                                "target": "ctx_child",
                                "conditions": ["audience == 'researcher'"],
                            }
                        ],
                    ),
                ),
            ]
        )

        assertion = IstProposition(
            context=ContextReference("ctx_root"),
            proposition_id="claim_root",
        )
        decisions = system.lift_decisions_for(assertion)

        assert {
            (str(item.source_context.id), str(item.target_context.id), item.status)
            for item in decisions
        } == {("ctx_root", "ctx_child", LiftingDecisionStatus.UNKNOWN)}
        assert system.materialize_lifted_assertions((assertion,)) == ()
        assert system.effective_assumptions("ctx_child") == ()

    @pytest.mark.property
    @given(
        source_assumptions=st.lists(
            st.sampled_from(
                [
                    "framework == 'general'",
                    "variant == 'baseline'",
                    "task == 'speech'",
                ]
            ),
            unique=True,
        ),
        target_assumptions=st.lists(
            st.sampled_from(
                [
                    "framework == 'specific'",
                    "variant == 'controlled'",
                    "task == 'vision'",
                ]
            ),
            unique=True,
        ),
    )
    @settings(deadline=None)
    def test_source_assumptions_do_not_inherit_into_target(
        self,
        source_assumptions: list[str],
        target_assumptions: list[str],
    ) -> None:
        system = loaded_contexts_to_lifting_system(
            [
                loaded_context(
                    "source",
                    None,
                    make_context(
                        "ctx_source", "Source", assumptions=source_assumptions
                    ),
                ),
                loaded_context(
                    "target",
                    None,
                    make_context(
                        "ctx_target", "Target", assumptions=target_assumptions
                    ),
                ),
            ]
        )

        effective = set(system.effective_assumptions("ctx_target"))

        assert set(target_assumptions).issubset(effective)
        assert effective.isdisjoint(set(source_assumptions) - set(target_assumptions))


class TestContextSidecar:
    def test_context_charter_uses_lifting_rule_table(self, tmp_path: Path) -> None:
        schema = world_schema()
        sidecar_path = tmp_path / "propstore.sqlite"
        create_sqlalchemy_store(sidecar_path, schema)
        conn = sqlite3.connect(sidecar_path)
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        finally:
            conn.close()

        assert {"context", "context_assumption", "context_lifting_rule"}.issubset(
            tables
        )
        assert "context_exclusion" not in tables

    def test_context_models_store_structure_and_lifting_rules(
        self, tmp_path: Path
    ) -> None:
        schema = world_schema()
        contexts = [
            loaded_context("source", None, make_context("ctx_source", "Source")),
            loaded_context(
                "target",
                None,
                make_context(
                    "ctx_target",
                    "Target",
                    assumptions=["framework == 'target'"],
                    parameters={"domain": "speech"},
                    perspective="local-model",
                    lifting_rules=[
                        {
                            "id": "lift-source-target",
                            "source": "ctx_source",
                            "target": "ctx_target",
                            "conditions": ["variant == 'controlled'"],
                            "mode": "specialization",
                        }
                    ],
                ),
            ),
        ]
        compiled = compile_context_models(contexts)
        context_rows, assumption_rows, lifting_rule_rows, _ = compiled
        sidecar_path = tmp_path / "propstore.sqlite"
        create_sqlalchemy_store(sidecar_path, schema)

        with writable_session(sidecar_path, schema) as session:
            session.add_all(context_rows)
            session.add_all(assumption_rows)
            session.add_all(lifting_rule_rows)
            session.commit()

        context_model = schema.model(CONTEXT_CHARTER.family.name)
        assumption_model = schema.model(CONTEXT_ASSUMPTION_CHARTER.family.name)
        rule_model = schema.model(CONTEXT_LIFTING_RULE_CHARTER.family.name)
        with readonly_session(sidecar_path, schema) as session:
            rows = {
                str(row.id): row
                for row in session.execute(select(context_model)).scalars()
            }
            assumption = session.execute(select(assumption_model)).scalars().one()
            rule = session.execute(select(rule_model)).scalars().one()

        row = rows["ctx_target"]
        assert row.parameters_json == {"domain": "speech"}
        assert row.perspective == "local-model"
        assert assumption.assumption_cel == "framework == 'target'"
        assert rule.source_context_id == "ctx_source"
        assert rule.target_context_id == "ctx_target"
        assert tuple(rule.conditions_cel) == ("variant == 'controlled'",)
        assert rule.mode == "specialization"


class TestBoundWorldContextLifting:
    class _Store:
        def __init__(self, claims) -> None:
            from propstore.core.conditions.solver import ConditionSolver
            from propstore.core.conditions.registry import ConditionRegistry

            self._claims = claims
            self._solver = ConditionSolver(ConditionRegistry())

        def claims_for(self, concept_id):
            return [
                claim
                for claim in self._claims
                if concept_id is None or claim.value_concept_id == concept_id
            ]

        def condition_solver(self):
            return self._solver

    def test_bound_world_uses_explicit_lifting_visibility(self) -> None:
        claims = [
            make_claim(claim_id="claim_root", concept_id="c1", context_id="ctx_root"),
            make_claim(claim_id="claim_child", concept_id="c1", context_id="ctx_child"),
            make_claim(claim_id="claim_other", concept_id="c1", context_id="ctx_other"),
            make_claim(claim_id="claim_unscoped", concept_id="c1", context_id=None),
        ]
        system = LiftingSystem(
            contexts=(
                ContextReference("ctx_root"),
                ContextReference("ctx_child"),
                ContextReference("ctx_other"),
            ),
            lifting_rules=(
                LiftingRule(
                    id="lift-root-child",
                    source=ContextReference("ctx_root"),
                    target=ContextReference("ctx_child"),
                ),
            ),
        )
        bound = BoundWorld(
            self._Store(claims),
            environment=Environment(context_id="ctx_child"),
            lifting_system=system,
        )

        assert {str(claim.id) for claim in bound.active_claims("c1")} == {
            "claim_root",
            "claim_child",
            "claim_unscoped",
        }

    def test_bound_world_without_lifting_rule_does_not_see_parent_by_name(self) -> None:
        claims = [
            make_claim(claim_id="claim_root", concept_id="c1", context_id="ctx_root"),
            make_claim(claim_id="claim_child", concept_id="c1", context_id="ctx_child"),
        ]
        system = LiftingSystem(
            contexts=(ContextReference("ctx_root"), ContextReference("ctx_child")),
        )
        bound = BoundWorld(
            self._Store(claims),
            environment=Environment(context_id="ctx_child"),
            lifting_system=system,
        )

        assert {str(claim.id) for claim in bound.active_claims("c1")} == {"claim_child"}


class TestWorldQueryContextLifting:
    def test_world_query_bind_loads_lifting_rules_from_sidecar(
        self, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "propstore.sqlite"
        conn = sqlite3.connect(sidecar)
        build_world_projection_schema(conn)
        conn.execute(
            "INSERT INTO context (id, name, parameters_json, perspective) VALUES (?, ?, ?, ?)",
            ("ctx_root", "Root", "{}", None),
        )
        conn.execute(
            "INSERT INTO context (id, name, parameters_json, perspective) VALUES (?, ?, ?, ?)",
            ("ctx_child", "Child", "{}", None),
        )
        conn.execute(
            "INSERT INTO context_lifting_rule "
            "(id, source_context_id, target_context_id, conditions_cel, mode) "
            "VALUES (?, ?, ?, ?, ?)",
            ("lift-root-child", "ctx_root", "ctx_child", "[]", "bridge"),
        )
        insert_claim_row(conn, "claim_root", context_id="ctx_root")
        insert_claim_row(conn, "claim_child", context_id="ctx_child")
        conn.commit()
        conn.close()

        wm = world_query_from_sqlite_path(sidecar)
        try:
            bound = wm.bind(Environment(context_id="ctx_child"))
            assert {str(claim.id) for claim in bound.active_claims("c1")} == {
                "claim_root",
                "claim_child",
            }
        finally:
            wm.close()


class TestContextAwareConflicts:
    def test_unrelated_contexts_classify_as_context_phi_node(self) -> None:
        system = LiftingSystem(
            contexts=(ContextReference("ctx_a"), ContextReference("ctx_b")),
        )

        assert (
            _classify_pair_context("ctx_a", "ctx_b", system)
            == ConflictClass.CONTEXT_PHI_NODE
        )

    def test_lifted_contexts_use_normal_conflict_classification(self) -> None:
        system = LiftingSystem(
            contexts=(ContextReference("ctx_a"), ContextReference("ctx_b")),
            lifting_rules=(
                LiftingRule(
                    "lift-a-b", ContextReference("ctx_a"), ContextReference("ctx_b")
                ),
            ),
        )

        assert (
            _classify_pair_context(
                "ctx_a",
                "ctx_b",
                system,
                claim_a_id="claim_alpha",
            )
            is None
        )


class TestContextCLIIntegration:
    def test_context_add_writes_structured_context(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from propstore.cli import cli
        from propstore.repository import Repository

        workspace = tmp_path / "knowledge"
        Repository.init(workspace)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(
            cli,
            [
                "context",
                "add",
                "--name",
                "ctx_test",
                "--description",
                "A test context",
                "--assumption",
                "framework == 'general'",
                "--parameter",
                "domain=speech",
                "--perspective",
                "local-model",
            ],
        )

        assert result.exit_code == 0, result.output
        repo = Repository.find(workspace)
        assert repo.git is not None
        data = yaml.safe_load(repo.git.read_file("contexts/ctx_test.yaml"))
        assert data["assumptions"] == ["framework == 'general'"]
        assert data["parameters"] == {"domain": "speech"}
        assert data["perspective"] == "local-model"

    def test_context_add_has_no_inherits_flag(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from propstore.cli import cli
        from propstore.repository import Repository

        Repository.init(tmp_path / "knowledge")
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(
            cli,
            [
                "context",
                "add",
                "--name",
                "ctx_child",
                "--description",
                "A child",
                "--inherits",
                "ctx_parent",
            ],
        )

        assert result.exit_code != 0
        assert "No such option: --inherits" in result.output
