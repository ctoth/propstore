"""Tests for first-class contexts and explicit lifting rules."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from quire.documents import DocumentSchemaError, convert_document_value
from propstore.families.contexts.documents import ContextDocument
from propstore.cel_checker import synthetic_category_concept
from propstore.conflict_detector import ConflictClass
from propstore.conflict_detector.context import _classify_pair_context
from propstore.context_lifting import IstProposition, LiftingRule, LiftingSystem
from propstore.core.assertions import ContextReference
from propstore.families.contexts import load_contexts
from propstore.families.contexts.passes import run_context_pipeline
from propstore.families.contexts.stages import (
    LoadedContext,
    loaded_contexts_to_lifting_system,
    parse_context_record,
)
from propstore.sidecar.schema import (
    build_minimal_world_model_schema,
    create_context_tables,
    populate_contexts,
)
from propstore.world.bound import BoundWorld
from propstore.world.types import Environment
from tests.conftest import make_compilation_context


def write_context(ctx_dir: Path, name: str, data: dict) -> Path:
    ctx_dir.mkdir(parents=True, exist_ok=True)
    path = ctx_dir / f"{name}.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


def make_context(
    context_id: str,
    name: str,
    description: str = "",
    *,
    assumptions: list[str] | None = None,
    parameters: dict[str, str] | None = None,
    perspective: str | None = None,
    lifting_rules: list[dict] | None = None,
) -> dict:
    payload: dict = {"id": context_id, "name": name, "description": description}
    structure: dict[str, object] = {}
    if assumptions:
        structure["assumptions"] = assumptions
    if parameters:
        structure["parameters"] = parameters
    if perspective:
        structure["perspective"] = perspective
    if structure:
        payload["structure"] = structure
    if lifting_rules:
        payload["lifting_rules"] = lifting_rules
    return payload


def loaded_context(
    filename: str,
    source_path: Path | None,
    data: dict,
) -> LoadedContext:
    return LoadedContext.from_payload(
        filename=filename,
        source_path=source_path,
        data=data,
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        ({"id": "ctx", "structure": "not-a-mapping"}, "structure"),
        ({"id": "ctx", "assumptions": "not-a-sequence"}, "assumptions"),
        ({"id": "ctx", "structure": {"assumptions": "not-a-sequence"}}, "assumptions"),
        ({"id": "ctx", "structure": {"parameters": "not-a-mapping"}}, "parameters"),
    ),
)
def test_parse_context_record_rejects_malformed_structured_fields(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_context_record(payload)


def insert_claim_row(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    concept_id: str = "c1",
    context_id: str | None = None,
    conditions_cel: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO claim_core (
            id, content_hash, seq, type, target_concept,
            source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, "", 1, "observation", None, "test", 1, None, context_id),
    )
    conn.execute(
        """
        INSERT INTO claim_concept_link (
            claim_id, concept_id, role, ordinal, binding_name
        ) VALUES (?, ?, 'output', 0, NULL)
        """,
        (claim_id, concept_id),
    )
    conn.execute(
        """
        INSERT INTO claim_numeric_payload (
            claim_id, value, lower_bound, upper_bound, uncertainty,
            uncertainty_type, sample_size, unit, value_si, lower_bound_si, upper_bound_si
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, None, None, None, None, None, None, None, None, None, None),
    )
    conn.execute(
        """
        INSERT INTO claim_text_payload (
            claim_id, conditions_cel, statement, expression, sympy_generated,
            sympy_error, name, measure, listener_population, methodology,
            notes, description, auto_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, conditions_cel, None, None, None, None, None, None, None, None, None, None, None),
    )
    conn.execute(
        "INSERT INTO claim_algorithm_payload (claim_id, body, canonical_ast, variables_json, algorithm_stage) VALUES (?, ?, ?, ?, ?)",
        (claim_id, None, None, None, None),
    )


class TestLoadAndValidateContexts:
    def test_load_context_files(self, tmp_path: Path) -> None:
        write_context(tmp_path, "ctx_foo", make_context("ctx_foo", "Foo"))
        write_context(tmp_path, "ctx_bar", make_context("ctx_bar", "Bar"))

        contexts = load_contexts(tmp_path)

        assert len(contexts) == 2
        assert all(isinstance(context, LoadedContext) for context in contexts)
        assert {
            str(context.record.context_id)
            for context in contexts
            if context.record.context_id is not None
        } == {"ctx_foo", "ctx_bar"}

    def test_validate_structured_context_and_lifting_rule(self, tmp_path: Path) -> None:
        contexts = [
            loaded_context("source", tmp_path / "source.yaml", make_context("ctx_source", "Source")),
            loaded_context(
                "target",
                tmp_path / "target.yaml",
                make_context(
                    "ctx_target",
                    "Target",
                    assumptions=["framework == 'target'"],
                    parameters={"domain": "speech"},
                    perspective="experiment",
                    lifting_rules=[{
                        "id": "lift-source-target",
                        "source": "ctx_source",
                        "target": "ctx_target",
                        "conditions": ["variant == 'controlled'"],
                        "mode": "bridge",
                        "justification": "Guha bridge rule",
                    }],
                ),
            ),
        ]

        result = run_context_pipeline(contexts)

        assert result.ok, tuple(error.render() for error in result.errors)

    def test_lifting_rule_must_reference_existing_contexts(self, tmp_path: Path) -> None:
        contexts = [
            loaded_context(
                "target",
                tmp_path / "target.yaml",
                make_context(
                    "ctx_target",
                    "Target",
                    lifting_rules=[{
                        "id": "lift-missing-target",
                        "source": "ctx_missing",
                        "target": "ctx_target",
                    }],
                ),
            ),
        ]

        result = run_context_pipeline(contexts)

        assert not result.ok
        assert any(
            "nonexistent source context" in error.render()
            for error in result.errors
        )

    @pytest.mark.parametrize("field", ["inherits", "excludes"])
    def test_visibility_inheritance_fields_are_rejected_at_document_boundary(self, field: str) -> None:
        payload = make_context("ctx_bad", "Bad")
        payload[field] = "ctx_parent" if field == "inherits" else ["ctx_other"]

        with pytest.raises(DocumentSchemaError):
            convert_document_value(payload, ContextDocument, source="context.yaml")


class TestLiftingSystem:
    def test_lifting_system_has_no_ancestry_visibility(self) -> None:
        system = loaded_contexts_to_lifting_system([
            loaded_context("root", None, make_context("ctx_root", "Root")),
            loaded_context("child", None, make_context("ctx_child", "Child")),
        ])

        assert system.materialize_lifted_assertions(
            (
                IstProposition(
                    context=ContextReference("ctx_root"),
                    proposition_id="claim_root",
                ),
            )
        ) == ()
        assert not system.can_lift("ctx_root", "ctx_child")

    def test_explicit_lifting_rule_controls_visibility(self) -> None:
        system = loaded_contexts_to_lifting_system([
            loaded_context("root", None, make_context("ctx_root", "Root")),
            loaded_context(
                "child",
                None,
                make_context(
                    "ctx_child",
                    "Child",
                    lifting_rules=[{
                        "id": "lift-root-child",
                        "source": "ctx_root",
                        "target": "ctx_child",
                        "conditions": ["audience == 'researcher'"],
                    }],
                ),
            ),
        ])

        materialized = system.materialize_lifted_assertions(
            (
                IstProposition(
                    context=ContextReference("ctx_root"),
                    proposition_id="claim_root",
                ),
            )
        )
        assert {
            (str(item.source_context.id), str(item.target_context.id))
            for item in materialized
        } == {("ctx_root", "ctx_child")}
        assert system.effective_assumptions("ctx_child") == ("audience == 'researcher'",)

    @pytest.mark.property
    @given(
        source_assumptions=st.lists(st.sampled_from([
            "framework == 'general'",
            "variant == 'baseline'",
            "task == 'speech'",
        ]), unique=True),
        target_assumptions=st.lists(st.sampled_from([
            "framework == 'specific'",
            "variant == 'controlled'",
            "task == 'vision'",
        ]), unique=True),
    )
    @settings(deadline=None)
    def test_source_assumptions_do_not_inherit_into_target(
        self,
        source_assumptions: list[str],
        target_assumptions: list[str],
    ) -> None:
        system = loaded_contexts_to_lifting_system([
            loaded_context("source", None, make_context("ctx_source", "Source", assumptions=source_assumptions)),
            loaded_context("target", None, make_context("ctx_target", "Target", assumptions=target_assumptions)),
        ])

        effective = set(system.effective_assumptions("ctx_target"))

        assert set(target_assumptions).issubset(effective)
        assert effective.isdisjoint(set(source_assumptions) - set(target_assumptions))


class TestContextSidecar:
    def test_create_context_tables_uses_lifting_rule_table(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        create_context_tables(conn)

        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        assert {"context", "context_assumption", "context_lifting_rule"}.issubset(tables)
        assert "context_exclusion" not in tables

    def test_populate_contexts_stores_structure_and_lifting_rules(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        create_context_tables(conn)
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
                    lifting_rules=[{
                        "id": "lift-source-target",
                        "source": "ctx_source",
                        "target": "ctx_target",
                        "conditions": ["variant == 'controlled'"],
                        "mode": "specialization",
                    }],
                ),
            ),
        ]

        from propstore.sidecar.passes import compile_context_sidecar_rows

        populate_contexts(conn, compile_context_sidecar_rows(contexts))

        row = conn.execute("SELECT * FROM context WHERE id='ctx_target'").fetchone()
        assert json.loads(row["parameters_json"]) == {"domain": "speech"}
        assert row["perspective"] == "local-model"
        assumption = conn.execute("SELECT assumption_cel FROM context_assumption").fetchone()
        assert assumption["assumption_cel"] == "framework == 'target'"
        rule = conn.execute("SELECT * FROM context_lifting_rule").fetchone()
        assert rule["source_context_id"] == "ctx_source"
        assert rule["target_context_id"] == "ctx_target"
        assert json.loads(rule["conditions_cel"]) == ["variant == 'controlled'"]
        assert rule["mode"] == "specialization"


class TestBoundWorldContextLifting:
    class _Store:
        def __init__(self, claims: list[dict]) -> None:
            from propstore.z3_conditions import Z3ConditionSolver

            self._claims = claims
            self._solver = Z3ConditionSolver({})

        def claims_for(self, concept_id):
            return [
                claim
                for claim in self._claims
                if concept_id is None or claim.get("concept_id") == concept_id
            ]

        def condition_solver(self):
            return self._solver

    def test_bound_world_uses_explicit_lifting_visibility(self) -> None:
        claims = [
            {"id": "claim_root", "concept_id": "c1", "context_id": "ctx_root"},
            {"id": "claim_child", "concept_id": "c1", "context_id": "ctx_child"},
            {"id": "claim_other", "concept_id": "c1", "context_id": "ctx_other"},
            {"id": "claim_unscoped", "concept_id": "c1", "context_id": None},
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

        assert {str(claim.claim_id) for claim in bound.active_claims("c1")} == {
            "claim_root",
            "claim_child",
            "claim_unscoped",
        }

    def test_bound_world_without_lifting_rule_does_not_see_parent_by_name(self) -> None:
        claims = [
            {"id": "claim_root", "concept_id": "c1", "context_id": "ctx_root"},
            {"id": "claim_child", "concept_id": "c1", "context_id": "ctx_child"},
        ]
        system = LiftingSystem(
            contexts=(ContextReference("ctx_root"), ContextReference("ctx_child")),
        )
        bound = BoundWorld(
            self._Store(claims),
            environment=Environment(context_id="ctx_child"),
            lifting_system=system,
        )

        assert {str(claim.claim_id) for claim in bound.active_claims("c1")} == {"claim_child"}


class TestWorldQueryContextLifting:
    def test_world_query_bind_loads_lifting_rules_from_sidecar(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "propstore.sqlite"
        conn = sqlite3.connect(sidecar)
        build_minimal_world_model_schema(conn)
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

        class _Repo:
            sidecar_path = sidecar

        from propstore.world import WorldQuery

        wm = WorldQuery(_Repo())
        try:
            bound = wm.bind(Environment(context_id="ctx_child"))
            assert {str(claim.claim_id) for claim in bound.active_claims("c1")} == {
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

        assert _classify_pair_context("ctx_a", "ctx_b", system) == ConflictClass.CONTEXT_PHI_NODE

    def test_lifted_contexts_use_normal_conflict_classification(self) -> None:
        system = LiftingSystem(
            contexts=(ContextReference("ctx_a"), ContextReference("ctx_b")),
            lifting_rules=(
                LiftingRule("lift-a-b", ContextReference("ctx_a"), ContextReference("ctx_b")),
            ),
        )

        assert _classify_pair_context("ctx_a", "ctx_b", system) is None


class TestContextCLIIntegration:
    def test_context_add_writes_structured_context(self, tmp_path: Path, monkeypatch) -> None:
        from propstore.cli import cli
        from propstore.repository import Repository

        workspace = tmp_path / "knowledge"
        Repository.init(workspace)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(cli, [
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
        ])

        assert result.exit_code == 0, result.output
        repo = Repository.find(workspace)
        assert repo.git is not None
        data = yaml.safe_load(repo.git.read_file("contexts/ctx_test.yaml"))
        assert data["structure"]["assumptions"] == ["framework == 'general'"]
        assert data["structure"]["parameters"] == {"domain": "speech"}
        assert data["structure"]["perspective"] == "local-model"

    def test_context_add_has_no_inherits_flag(self, tmp_path: Path, monkeypatch) -> None:
        from propstore.cli import cli
        from propstore.repository import Repository

        Repository.init(tmp_path / "knowledge")
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(cli, [
            "context",
            "add",
            "--name",
            "ctx_child",
            "--description",
            "A child",
            "--inherits",
            "ctx_parent",
        ])

        assert result.exit_code != 0
        assert "No such option: --inherits" in result.output

    def test_claim_document_requires_explicit_context(self, tmp_path: Path) -> None:
        from propstore.claims import loaded_claim_file_from_payload

        with pytest.raises(DocumentSchemaError, match="context"):
            loaded_claim_file_from_payload(
                filename="claims",
                source_path=tmp_path / "claims.yaml",
                data={
                    "source": {"paper": "test"},
                    "claims": [{
                        "artifact_id": "claim1",
                        "type": "observation",
                        "statement": "Test statement.",
                        "concepts": ["c1"],
                        "provenance": {"paper": "test", "page": 1},
                    }],
                },
            )

    def test_claim_validation_accepts_context_reference_document_shape(self, tmp_path: Path) -> None:
        from propstore.claims import loaded_claim_file_from_payload
        from propstore.families.claims.passes import validate_claims

        claim_file = loaded_claim_file_from_payload(
            filename="claims",
            source_path=tmp_path / "claims.yaml",
            data={
                "source": {"paper": "test"},
                "claims": [{
                    "artifact_id": "claim1",
                    "type": "observation",
                    "statement": "Test statement.",
                    "concepts": ["c1"],
                    "context": {"id": "ctx_atms"},
                    "provenance": {"paper": "test", "page": 1},
                }],
            },
        )
        registry = {
            "c1": {
                "artifact_id": "c1",
                "canonical_name": "c1",
                "status": "accepted",
                "definition": "c1",
                "form": "category",
            },
        }

        result = validate_claims(
            [claim_file],
            make_compilation_context(registry),
            context_ids={"ctx_atms"},
        )
        context_errors = [error for error in result.errors if "context" in error.lower()]

        assert context_errors == []
