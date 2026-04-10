"""Tests for context loading, validation, hierarchy, and sidecar integration."""

import json
import sqlite3
from pathlib import Path

import pytest
import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.context_types import LoadedContext
from propstore.loaded import LoadedEntry
from propstore.context_hierarchy import ContextHierarchy
from propstore.validate_contexts import (
    load_contexts,
    validate_contexts,
)
from propstore.value_comparison import DEFAULT_TOLERANCE
from tests.conftest import (
    create_world_model_schema,
    normalize_claims_payload,
    normalize_concept_payloads,
)


# ── Helpers ──────────────────────────────────────────────────────────


def write_context(ctx_dir, name, data):
    ctx_dir.mkdir(parents=True, exist_ok=True)
    path = ctx_dir / f"{name}.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


def make_context(id, name, description="", **kwargs):
    d = {"id": id, "name": name, "description": description}
    d.update(kwargs)
    return d


def _runtime_claim_id_set(claims) -> set[str]:
    return {str(claim.claim_id) for claim in claims}


def insert_claim_row(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    concept_id: str | None = None,
    conditions_cel: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO claim_core (
            id, content_hash, seq, type, concept_id, target_concept,
            source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (claim_id, "", 1, "observation", concept_id, None, "test", 1, None, None),
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
        "INSERT INTO claim_algorithm_payload (claim_id, body, canonical_ast, variables_json, stage) VALUES (?, ?, ?, ?, ?)",
        (claim_id, None, None, None, None),
    )


_ASSUMPTION_POOL = [
    "framework == 'general'",
    "framework == 'specialized'",
    "variant == 'baseline'",
    "variant == 'specific'",
    "task == 'speech'",
]


# ── Step 1: Loading ──────────────────────────────────────────────────


class TestLoadContexts:
    def test_load_context_files(self, tmp_path):
        """Load context YAML files from a directory, returns list of LoadedContext."""
        write_context(tmp_path, "ctx_foo", make_context("ctx_foo", "Foo"))
        write_context(tmp_path, "ctx_bar", make_context("ctx_bar", "Bar"))
        contexts = load_contexts(tmp_path)
        assert len(contexts) == 2
        assert all(isinstance(c, LoadedContext) for c in contexts)
        ids = {
            str(c.record.context_id)
            for c in contexts
            if c.record.context_id is not None
        }
        assert ids == {"ctx_foo", "ctx_bar"}

    def test_load_empty_dir(self, tmp_path):
        """Empty directory returns empty list."""
        tmp_path.mkdir(exist_ok=True)
        assert load_contexts(tmp_path) == []

    def test_load_skips_non_yaml(self, tmp_path):
        """Non-YAML files are ignored."""
        write_context(tmp_path, "ctx_ok", make_context("ctx_ok", "OK"))
        (tmp_path / "README.md").write_text("not a context")
        contexts = load_contexts(tmp_path)
        assert len(contexts) == 1


# ── Step 1: Validation ──────────────────────────────────────────────


class TestValidateContexts:
    def test_valid_context_passes(self, tmp_path):
        """A well-formed context validates clean."""
        contexts = [LoadedEntry("ctx_foo", tmp_path / "ctx_foo.yaml",
                                 make_context("ctx_foo", "Foo", "A test context"))]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_missing_id_errors(self, tmp_path):
        """Context without id is an error."""
        contexts = [LoadedEntry("ctx_bad", tmp_path / "ctx_bad.yaml",
                                 {"name": "Bad"})]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("id" in e.lower() for e in result.errors)

    def test_missing_name_errors(self, tmp_path):
        """Context without name is an error."""
        contexts = [LoadedEntry("ctx_bad", tmp_path / "ctx_bad.yaml",
                                 {"id": "ctx_bad"})]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("name" in e.lower() for e in result.errors)

    def test_inherits_must_exist(self, tmp_path):
        """Validation error if inherits references nonexistent context."""
        contexts = [LoadedEntry("ctx_child", tmp_path / "ctx_child.yaml",
                                 make_context("ctx_child", "Child", inherits="ctx_nonexistent"))]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("nonexistent" in e.lower() or "inherits" in e.lower() for e in result.errors)

    def test_inherits_valid_reference(self, tmp_path):
        """No error when inherits references an existing context."""
        contexts = [
            LoadedEntry("ctx_parent", tmp_path / "a.yaml",
                         make_context("ctx_parent", "Parent")),
            LoadedEntry("ctx_child", tmp_path / "b.yaml",
                         make_context("ctx_child", "Child", inherits="ctx_parent")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_excludes_must_exist(self, tmp_path):
        """Validation error if excludes references nonexistent context."""
        contexts = [LoadedEntry("ctx_a", tmp_path / "a.yaml",
                                 make_context("ctx_a", "A", excludes=["ctx_nonexistent"]))]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("nonexistent" in e.lower() or "excludes" in e.lower() for e in result.errors)

    def test_excludes_valid_reference(self, tmp_path):
        """No error when excludes references an existing context."""
        contexts = [
            LoadedEntry("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A", excludes=["ctx_b"])),
            LoadedEntry("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_no_inheritance_cycles(self, tmp_path):
        """Validation error if inheritance forms A->B->A cycle."""
        contexts = [
            LoadedEntry("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A", inherits="ctx_b")),
            LoadedEntry("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B", inherits="ctx_a")),
        ]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("cycle" in e.lower() for e in result.errors)

    def test_deep_inheritance_ok(self, tmp_path):
        """A->B->C inheritance chain is valid."""
        contexts = [
            LoadedEntry("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A")),
            LoadedEntry("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B", inherits="ctx_a")),
            LoadedEntry("ctx_c", tmp_path / "c.yaml",
                         make_context("ctx_c", "C", inherits="ctx_b")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_duplicate_context_id_errors(self, tmp_path):
        """Two context files with same id is an error."""
        contexts = [
            LoadedEntry("file1", tmp_path / "file1.yaml",
                         make_context("ctx_dup", "Dup 1")),
            LoadedEntry("file2", tmp_path / "file2.yaml",
                         make_context("ctx_dup", "Dup 2")),
        ]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("duplicate" in e.lower() for e in result.errors)


# ── Step 1: Hierarchy ───────────────────────────────────────────────


class TestContextHierarchy:
    def _make_hierarchy(self):
        """Build a test hierarchy: root -> mid -> leaf, plus unrelated."""
        contexts = [
            LoadedEntry("root", None, make_context("ctx_root", "Root")),
            LoadedEntry("mid", None, make_context("ctx_mid", "Mid", inherits="ctx_root")),
            LoadedEntry("leaf", None, make_context("ctx_leaf", "Leaf", inherits="ctx_mid")),
            LoadedEntry("other", None, make_context("ctx_other", "Other", excludes=["ctx_root"])),
        ]
        return ContextHierarchy(contexts)

    def test_ancestors(self):
        h = self._make_hierarchy()
        assert h.ancestors("ctx_leaf") == ["ctx_mid", "ctx_root"]

    def test_ancestors_of_mid(self):
        h = self._make_hierarchy()
        assert h.ancestors("ctx_mid") == ["ctx_root"]

    def test_root_has_no_ancestors(self):
        h = self._make_hierarchy()
        assert h.ancestors("ctx_root") == []

    def test_effective_assumptions(self):
        """Child context's effective assumptions include parent's."""
        contexts = [
            LoadedEntry("root", None, make_context("ctx_root", "Root",
                                                     assumptions=["framework == 'general'"])),
            LoadedEntry("child", None, make_context("ctx_child", "Child",
                                                      inherits="ctx_root",
                                                      assumptions=["variant == 'specific'"])),
        ]
        h = ContextHierarchy(contexts)
        effective = h.effective_assumptions("ctx_child")
        assert "variant == 'specific'" in effective
        assert "framework == 'general'" in effective

    def test_are_excluded(self):
        h = self._make_hierarchy()
        assert h.are_excluded("ctx_other", "ctx_root")
        assert h.are_excluded("ctx_root", "ctx_other")  # symmetric

    def test_non_excluded_contexts(self):
        h = self._make_hierarchy()
        assert not h.are_excluded("ctx_root", "ctx_mid")
        assert not h.are_excluded("ctx_leaf", "ctx_other")

    def test_is_visible(self):
        """A context can see itself, its ancestors, but not unrelated."""
        h = self._make_hierarchy()
        assert h.is_visible("ctx_leaf", "ctx_leaf")   # self
        assert h.is_visible("ctx_leaf", "ctx_mid")     # parent
        assert h.is_visible("ctx_leaf", "ctx_root")    # grandparent
        assert not h.is_visible("ctx_leaf", "ctx_other")  # unrelated
        assert not h.is_visible("ctx_root", "ctx_leaf")   # child not visible from parent


class TestContextProperties:
    @given(
        parent_assumptions=st.lists(st.sampled_from(_ASSUMPTION_POOL), unique=True, max_size=3),
        child_assumptions=st.lists(st.sampled_from(_ASSUMPTION_POOL), unique=True, max_size=3),
    )
    @settings()
    def test_effective_assumptions_monotone_under_inheritance(
        self,
        parent_assumptions,
        child_assumptions,
    ):
        hierarchy = ContextHierarchy([
            LoadedEntry(
                "root",
                None,
                make_context("ctx_root", "Root", assumptions=parent_assumptions),
            ),
            LoadedEntry(
                "child",
                None,
                make_context(
                    "ctx_child",
                    "Child",
                    inherits="ctx_root",
                    assumptions=child_assumptions,
                ),
            ),
        ])

        effective = hierarchy.effective_assumptions("ctx_child")
        assert set(parent_assumptions).issubset(set(effective))
        assert set(child_assumptions).issubset(set(effective))

    @given(
        effective_assumptions=st.lists(
            st.sampled_from(_ASSUMPTION_POOL),
            unique=True,
            max_size=len(_ASSUMPTION_POOL),
        )
    )
    @settings(deadline=None)
    def test_visibility_depends_on_effective_assumptions_not_context_identity(
        self,
        effective_assumptions,
    ):
        from propstore.world.bound import BoundWorld
        from propstore.world.types import Environment
        from propstore.z3_conditions import Z3ConditionSolver

        class _Store:
            def __init__(self, claims):
                self._claims = claims
                self._solver = Z3ConditionSolver({})

            def claims_for(self, concept_id):
                return [
                    claim for claim in self._claims
                    if concept_id is None or claim.get("concept_id") == concept_id
                ]

            def condition_solver(self):
                return self._solver

        claims = [
            {
                "id": "claim_universal",
                "concept_id": "concept1",
                "conditions_cel": None,
                "context_id": None,
            }
        ]
        for index, assumption in enumerate(_ASSUMPTION_POOL, start=1):
            claims.append({
                "id": f"claim_{index}",
                "concept_id": "concept1",
                "conditions_cel": json.dumps([assumption]),
                "context_id": None,
            })

        hierarchy = ContextHierarchy([
            LoadedEntry("a", None, make_context("ctx_a", "A")),
            LoadedEntry("b", None, make_context("ctx_b", "B")),
        ])
        store = _Store(claims)

        bound_a = BoundWorld(
            store,
            environment=Environment(
                context_id="ctx_a",
                effective_assumptions=tuple(effective_assumptions),
            ),
            context_hierarchy=hierarchy,
        )
        bound_b = BoundWorld(
            store,
            environment=Environment(
                context_id="ctx_b",
                effective_assumptions=tuple(effective_assumptions),
            ),
            context_hierarchy=hierarchy,
        )

        active_a = _runtime_claim_id_set(bound_a.active_claims("concept1"))
        active_b = _runtime_claim_id_set(bound_b.active_claims("concept1"))
        assert active_a == active_b


# ── Step 2: Context tables in sidecar ────────────────────────────────

import sqlite3
from propstore.sidecar.schema import (
    create_context_tables,
    populate_contexts,
)


class TestContextSidecar:
    def _make_conn(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn

    def test_create_context_tables(self):
        """_create_context_tables creates all three tables."""
        conn = self._make_conn()
        create_context_tables(conn)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "context" in tables
        assert "context_assumption" in tables
        assert "context_exclusion" in tables

    def test_populate_contexts(self):
        """Contexts from LoadedEntry list appear in context table."""
        conn = self._make_conn()
        create_context_tables(conn)
        contexts = [
            LoadedEntry("a", None, make_context("ctx_a", "A", "Desc A")),
            LoadedEntry("b", None, make_context("ctx_b", "B", "Desc B")),
        ]
        populate_contexts(conn, contexts)
        rows = conn.execute("SELECT * FROM context").fetchall()
        assert len(rows) == 2
        ids = {r["id"] for r in rows}
        assert ids == {"ctx_a", "ctx_b"}

    def test_populate_assumptions(self):
        """Context assumptions appear in context_assumption table in order."""
        conn = self._make_conn()
        create_context_tables(conn)
        contexts = [
            LoadedEntry("a", None, make_context("ctx_a", "A",
                         assumptions=["x == 1", "y == 2"])),
        ]
        populate_contexts(conn, contexts)
        rows = conn.execute(
            "SELECT * FROM context_assumption WHERE context_id='ctx_a' ORDER BY seq"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["assumption_cel"] == "x == 1"
        assert rows[1]["assumption_cel"] == "y == 2"

    def test_populate_exclusions(self):
        """Exclusion pairs appear in context_exclusion table."""
        conn = self._make_conn()
        create_context_tables(conn)
        contexts = [
            LoadedEntry("a", None, make_context("ctx_a", "A", excludes=["ctx_b"])),
            LoadedEntry("b", None, make_context("ctx_b", "B")),
        ]
        populate_contexts(conn, contexts)
        rows = conn.execute("SELECT * FROM context_exclusion").fetchall()
        assert len(rows) == 1
        assert rows[0]["context_a"] == "ctx_a"
        assert rows[0]["context_b"] == "ctx_b"

    def test_populate_inherits(self):
        """Parent reference is stored in context.inherits column."""
        conn = self._make_conn()
        create_context_tables(conn)
        contexts = [
            LoadedEntry("p", None, make_context("ctx_parent", "Parent")),
            LoadedEntry("c", None, make_context("ctx_child", "Child", inherits="ctx_parent")),
        ]
        populate_contexts(conn, contexts)
        row = conn.execute("SELECT inherits FROM context WHERE id='ctx_child'").fetchone()
        assert row["inherits"] == "ctx_parent"

    def test_empty_contexts_ok(self):
        """Build succeeds with no contexts."""
        conn = self._make_conn()
        create_context_tables(conn)
        populate_contexts(conn, [])
        assert conn.execute("SELECT COUNT(*) FROM context").fetchone()[0] == 0


# ── Step 3: Claim context_id ────────────────────────────────────────


class TestClaimContextId:
    def test_claim_context_must_exist(self, tmp_path):
        """Validation error if claim references nonexistent context."""
        from propstore.compiler.passes import validate_claims

        claim_file = LoadedEntry("test", tmp_path / "test.yaml", normalize_claims_payload({
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "context": "ctx_nonexistent",
                "provenance": {"paper": "test", "page": 1},
            }],
        }))
        registry = {
            "fundamental_frequency": {
                "id": "concept1", "canonical_name": "fundamental_frequency",
                "form": "frequency", "status": "accepted", "definition": "F0",
            },
        }
        result = validate_claims([claim_file], registry, context_ids=set())
        assert not result.ok
        assert any("ctx_nonexistent" in e for e in result.errors)

    def test_claim_context_valid_reference(self, tmp_path):
        """No error when claim references an existing context."""
        from propstore.compiler.passes import validate_claims

        claim_file = LoadedEntry("test", tmp_path / "test.yaml", normalize_claims_payload({
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "context": "ctx_atms",
                "provenance": {"paper": "test", "page": 1},
            }],
        }))
        registry = {
            "fundamental_frequency": {
                "id": "concept1", "canonical_name": "fundamental_frequency",
                "form": "frequency", "status": "accepted", "definition": "F0",
            },
        }
        result = validate_claims([claim_file], registry, context_ids={"ctx_atms"})
        id_errors = [e for e in result.errors if "ctx_" in e]
        assert not id_errors, f"Context ref rejected: {id_errors}"

    def test_claim_without_context_ok(self, tmp_path):
        """A claim without context field validates fine."""
        from propstore.compiler.passes import validate_claims

        claim_file = LoadedEntry("test", tmp_path / "test.yaml", normalize_claims_payload({
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "test", "page": 1},
            }],
        }))
        registry = {
            "fundamental_frequency": {
                "id": "concept1", "canonical_name": "fundamental_frequency",
                "form": "frequency", "status": "accepted", "definition": "F0",
            },
        }
        result = validate_claims([claim_file], registry, context_ids=set())
        ctx_errors = [e for e in result.errors if "context" in e.lower()]
        assert not ctx_errors, f"No-context claim rejected: {ctx_errors}"


# ── Step 4: BoundWorld context filtering ─────────────────────────────


class TestBoundWorldContext:
    """Test context filtering in BoundWorld.

    These tests build a minimal sidecar in-memory with contexts and claims,
    then query through WorldModel + BoundWorld.
    """

    def _build_test_world(self):
        """Build a test sidecar with contexts and claims, return (conn, hierarchy)."""
        from propstore.sidecar.schema import (
            create_claim_tables,
            create_context_tables,
            create_tables,
        )

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        create_tables(conn)
        create_claim_tables(conn)
        create_context_tables(conn)

        # Contexts: root -> child, plus unrelated (excludes root)
        conn.execute("INSERT INTO context VALUES ('ctx_root', 'Root', 'Root ctx', NULL)")
        conn.execute("INSERT INTO context VALUES ('ctx_child', 'Child', 'Child ctx', 'ctx_root')")
        conn.execute("INSERT INTO context VALUES ('ctx_other', 'Other', 'Other ctx', NULL)")
        conn.execute("INSERT INTO context_exclusion VALUES ('ctx_other', 'ctx_root')")

        # Concepts
        conn.execute(
            "INSERT INTO concept (id, content_hash, seq, canonical_name, status, domain, "
            "definition, kind_type, form, is_dimensionless) VALUES "
            "('c1', 'h1', 1, 'test_concept', 'accepted', 'test', 'A test', 'structural', 'structural', 1)"
        )

        # Claims in different contexts
        for claim_id, context_id, statement, paper, page in (
            ("claim1", "ctx_root", "Root claim", "paper1", 1),
            ("claim2", "ctx_child", "Child claim", "paper2", 2),
            ("claim3", "ctx_other", "Other claim", "paper3", 3),
            ("claim4", None, "Universal claim", "paper4", 4),
        ):
            conn.execute(
                """
                INSERT INTO claim_core (
                    id, content_hash, seq, type, concept_id, target_concept,
                    source_paper, provenance_page, provenance_json, context_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (claim_id, f"h{page}", page, "observation", "c1", None, paper, page, "{}", context_id),
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
                (claim_id, None, statement, None, None, None, None, None, None, None, None, None, None),
            )
            conn.execute(
                "INSERT INTO claim_algorithm_payload (claim_id, body, canonical_ast, variables_json, stage) VALUES (?, ?, ?, ?, ?)",
                (claim_id, None, None, None, None),
            )

        conn.commit()

        hierarchy = ContextHierarchy([
            LoadedEntry("root", None, make_context("ctx_root", "Root")),
            LoadedEntry("child", None, make_context("ctx_child", "Child", inherits="ctx_root")),
            LoadedEntry("other", None, make_context("ctx_other", "Other", excludes=["ctx_root"])),
        ])

        return conn, hierarchy

    def test_bind_with_context_filters_unrelated(self):
        """Claims in unrelated context are not active."""
        conn, hierarchy = self._build_test_world()
        from propstore.world.bound import BoundWorld

        wm = self._make_wm(conn)
        bound = BoundWorld(wm, {}, context_id="ctx_root", context_hierarchy=hierarchy)
        active = bound.active_claims("c1")
        active_ids = _runtime_claim_id_set(active)

        assert "claim1" in active_ids    # root's own claim
        assert "claim4" in active_ids    # universal
        assert "claim3" not in active_ids  # other context — filtered out
        conn.close()

    def _make_wm(self, conn):
        """Build a minimal mock WorldModel with a live connection."""
        class FakeWM:
            def __init__(self, c):
                self._conn = c
                self._solver = None
                self._registry = None
            def claims_for(self, cid):
                return [
                    dict(r)
                    for r in self._conn.execute(
                        """
                        SELECT
                            core.id, core.content_hash, core.seq, core.type, core.concept_id,
                            num.value, num.lower_bound, num.upper_bound, num.uncertainty,
                            num.uncertainty_type, num.sample_size, num.unit,
                            txt.conditions_cel, txt.statement, txt.expression,
                            txt.sympy_generated, txt.sympy_error, txt.name,
                            core.target_concept, txt.measure, txt.listener_population,
                            txt.methodology, txt.notes, txt.description, txt.auto_summary,
                            alg.body, alg.canonical_ast, alg.variables_json, alg.stage,
                            core.source_paper, core.provenance_page, core.provenance_json,
                            num.value_si, num.lower_bound_si, num.upper_bound_si, core.context_id
                        FROM claim_core AS core
                        LEFT JOIN claim_numeric_payload AS num ON num.claim_id = core.id
                        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
                        LEFT JOIN claim_algorithm_payload AS alg ON alg.claim_id = core.id
                        WHERE core.concept_id = ?
                        """,
                        (cid,),
                    ).fetchall()
                ]
            def _has_table(self, name):
                return True
            def _ensure_solver(self):
                return None
        return FakeWM(conn)

    def test_bind_with_context_sees_parent(self):
        """Claims in parent context are visible when querying child."""
        conn, hierarchy = self._build_test_world()
        from propstore.world.bound import BoundWorld

        wm = self._make_wm(conn)
        bound = BoundWorld(wm, {}, context_id="ctx_child", context_hierarchy=hierarchy)
        active = bound.active_claims("c1")
        active_ids = _runtime_claim_id_set(active)

        assert "claim1" in active_ids    # parent's claim — visible via inheritance
        assert "claim2" in active_ids    # child's own
        assert "claim4" in active_ids    # universal
        assert "claim3" not in active_ids  # other — not visible
        conn.close()

    def test_universal_claims_visible_in_all_contexts(self):
        """Claims with no context are visible everywhere."""
        conn, hierarchy = self._build_test_world()
        from propstore.world.bound import BoundWorld

        wm = self._make_wm(conn)
        for ctx in ["ctx_root", "ctx_child", "ctx_other"]:
            bound = BoundWorld(wm, {}, context_id=ctx, context_hierarchy=hierarchy)
            active = bound.active_claims("c1")
            active_ids = _runtime_claim_id_set(active)
            assert "claim4" in active_ids, f"Universal claim not visible in {ctx}"
        conn.close()

    def test_bind_without_context_sees_everything(self):
        """bind() without context= behaves exactly as before."""
        conn, hierarchy = self._build_test_world()
        from propstore.world.bound import BoundWorld

        wm = self._make_wm(conn)
        bound = BoundWorld(wm, {})  # no context
        active = bound.active_claims("c1")
        assert len(active) == 4  # all four claims visible
        conn.close()

    def test_world_model_bind_uses_sidecar_context_hierarchy(self, tmp_path):
        """WorldModel.bind() should load and apply context hierarchy from sidecar tables."""
        sidecar = tmp_path / "propstore.sqlite"
        conn = sqlite3.connect(sidecar)
        create_world_model_schema(conn)
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_root', 'Root', NULL)")
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_child', 'Child', 'ctx_root')")
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_other', 'Other', NULL)")
        insert_claim_row(conn, "claim_root", concept_id="c1")
        insert_claim_row(conn, "claim_child", concept_id="c1")
        insert_claim_row(conn, "claim_other", concept_id="c1")
        insert_claim_row(conn, "claim_universal", concept_id="c1")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_root' WHERE id = 'claim_root'")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_child' WHERE id = 'claim_child'")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_other' WHERE id = 'claim_other'")
        conn.commit()
        conn.close()

        class _Repo:
            sidecar_path = sidecar

        from propstore.world import WorldModel
        from propstore.world.types import Environment

        wm = WorldModel(_Repo())
        try:
            bound = wm.bind(Environment(context_id="ctx_root"))
            active_ids = _runtime_claim_id_set(bound.active_claims("c1"))
            assert active_ids == {"claim_root", "claim_universal"}
        finally:
            wm.close()

    def test_world_model_bind_exposes_effective_assumptions_and_uses_them(self, tmp_path):
        """Binding through a sidecar context should expose and apply effective assumptions."""
        sidecar = tmp_path / "propstore.sqlite"
        conn = sqlite3.connect(sidecar)
        create_world_model_schema(conn)
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_root', 'Root', NULL)")
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_child', 'Child', 'ctx_root')")
        conn.execute(
            "INSERT INTO context_assumption (context_id, assumption_cel, seq) VALUES (?, ?, ?)",
            ("ctx_root", "framework == 'general'", 1),
        )
        conn.execute(
            "INSERT INTO context_assumption (context_id, assumption_cel, seq) VALUES (?, ?, ?)",
            ("ctx_child", "variant == 'specific'", 1),
        )
        insert_claim_row(conn, "claim_general", concept_id="c1", conditions_cel="[\"framework == 'general'\"]")
        insert_claim_row(conn, "claim_specific", concept_id="c1", conditions_cel="[\"variant == 'specific'\"]")
        insert_claim_row(conn, "claim_other", concept_id="c1", conditions_cel="[\"framework == 'other'\"]")
        conn.commit()
        conn.close()

        class _Repo:
            sidecar_path = sidecar

        from propstore.world import WorldModel
        from propstore.world.types import Environment

        wm = WorldModel(_Repo())
        try:
            bound = wm.bind(Environment(context_id="ctx_child"))
            assert set(bound._environment.effective_assumptions) == {
                "framework == 'general'",
                "variant == 'specific'",
            }
            active_ids = _runtime_claim_id_set(bound.active_claims("c1"))
            assert "claim_general" in active_ids
            assert "claim_specific" in active_ids
            assert "claim_other" not in active_ids
        finally:
            wm.close()

    def test_world_model_bind_active_graph_matches_context_visibility(self, tmp_path):
        """The active graph produced by bind() must match current context-filtered visibility."""
        sidecar = tmp_path / "propstore.sqlite"
        conn = sqlite3.connect(sidecar)
        create_world_model_schema(conn)
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_root', 'Root', NULL)")
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_child', 'Child', 'ctx_root')")
        conn.execute("INSERT INTO context (id, name, inherits) VALUES ('ctx_other', 'Other', NULL)")
        insert_claim_row(conn, "claim_root", concept_id="c1")
        insert_claim_row(conn, "claim_child", concept_id="c1")
        insert_claim_row(conn, "claim_other", concept_id="c1")
        insert_claim_row(conn, "claim_universal", concept_id="c1")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_root' WHERE id = 'claim_root'")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_child' WHERE id = 'claim_child'")
        conn.execute("UPDATE claim_core SET context_id = 'ctx_other' WHERE id = 'claim_other'")
        conn.commit()
        conn.close()

        class _Repo:
            sidecar_path = sidecar

        from propstore.world import WorldModel
        from propstore.world.types import Environment

        wm = WorldModel(_Repo())
        try:
            bound = wm.bind(Environment(context_id="ctx_child"))
            assert tuple(sorted(str(c.claim_id) for c in bound.active_claims())) == (
                bound._active_graph.active_claim_ids
            )
            assert tuple(sorted(str(c.claim_id) for c in bound.inactive_claims())) == (
                bound._active_graph.inactive_claim_ids
            )
        finally:
            wm.close()


# ── Step 5: Context-aware conflict detection ─────────────────────────


from propstore.conflict_detector import ConflictClass, _classify_pair_context


class TestContextAwareConflicts:
    def test_different_unrelated_context_is_context_phi_node(self):
        """Different unrelated contexts = None (let condition analysis decide)."""
        result = _classify_pair_context(
            context_a="ctx_atms", context_b="ctx_jtms",
            hierarchy=ContextHierarchy([
                LoadedEntry("a", None, make_context("ctx_atms", "ATMS")),
                LoadedEntry("b", None, make_context("ctx_jtms", "JTMS")),
            ]),
        )
        assert result is None

    def test_same_context_returns_none(self):
        """Same context → None (let normal classification proceed)."""
        result = _classify_pair_context(
            context_a="ctx_atms", context_b="ctx_atms",
            hierarchy=ContextHierarchy([
                LoadedEntry("a", None, make_context("ctx_atms", "ATMS")),
            ]),
        )
        assert result is None

    def test_ancestor_descendant_returns_none(self):
        """Parent/child contexts → None (both visible, normal classification)."""
        h = ContextHierarchy([
            LoadedEntry("p", None, make_context("ctx_parent", "Parent")),
            LoadedEntry("c", None, make_context("ctx_child", "Child", inherits="ctx_parent")),
        ])
        result = _classify_pair_context(
            context_a="ctx_parent", context_b="ctx_child", hierarchy=h,
        )
        assert result is None

    def test_excluded_contexts_return_context_phi_node(self):
        """Mutually excluded contexts classify as CONTEXT_PHI_NODE."""
        h = ContextHierarchy([
            LoadedEntry("root", None, make_context("ctx_root", "Root")),
            LoadedEntry(
                "other",
                None,
                make_context("ctx_other", "Other", excludes=["ctx_root"]),
            ),
        ])
        result = _classify_pair_context(
            context_a="ctx_root",
            context_b="ctx_other",
            hierarchy=h,
        )
        assert result == ConflictClass.CONTEXT_PHI_NODE

    def test_no_context_returns_none(self):
        """One or both claims with no context → None (universal, normal classification)."""
        h = ContextHierarchy([
            LoadedEntry("a", None, make_context("ctx_atms", "ATMS")),
        ])
        assert _classify_pair_context("ctx_atms", None, h) is None
        assert _classify_pair_context(None, "ctx_atms", h) is None
        assert _classify_pair_context(None, None, h) is None

    def test_both_none_hierarchy_returns_none(self):
        """No hierarchy at all → None (backward compatible)."""
        assert _classify_pair_context("ctx_a", "ctx_b", None) is None

    def test_detect_conflicts_unrelated_contexts_not_suppressed(self):
        """Unrelated-context claims go through normal condition analysis, not CONTEXT_PHI_NODE."""
        from propstore.conflict_detector import detect_conflicts
        
        cf = LoadedEntry(
            filename="test",
            source_path=Path("test.yaml"),
            data={"claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 1.0,
                    "unit": "Hz",
                    "context": "ctx_root",
                    "provenance": {"paper": "test", "page": 1},
                },
                {
                    "id": "claim2",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 2.0,
                    "unit": "Hz",
                    "context": "ctx_other",
                    "provenance": {"paper": "test", "page": 1},
                },
            ]},
        )
        hierarchy = ContextHierarchy([
            LoadedEntry("root", None, make_context("ctx_root", "Root")),
            LoadedEntry("other", None, make_context("ctx_other", "Other")),
        ])
        registry = {
            "concept1": {
                "id": "concept1",
                "canonical_name": "concept1",
                "form": "frequency",
                "status": "accepted",
                "definition": "test concept",
            },
        }

        records = detect_conflicts([cf], registry, context_hierarchy=hierarchy)
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    @given(
        value_a=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        value_b=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings()
    def test_unrelated_context_conflicts_not_suppressed(
        self,
        value_a,
        value_b,
    ):
        """Unrelated contexts let condition analysis decide — never CONTEXT_PHI_NODE."""
        from propstore.conflict_detector import detect_conflicts
        
        assume(abs(value_a - value_b) > DEFAULT_TOLERANCE)

        cf = LoadedEntry(
            filename="test",
            source_path=Path("test.yaml"),
            data={"claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": value_a,
                    "unit": "Hz",
                    "context": "ctx_root",
                    "provenance": {"paper": "test", "page": 1},
                },
                {
                    "id": "claim2",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": value_b,
                    "unit": "Hz",
                    "context": "ctx_other",
                    "provenance": {"paper": "test", "page": 1},
                },
            ]},
        )
        hierarchy = ContextHierarchy([
            LoadedEntry("root", None, make_context("ctx_root", "Root")),
            LoadedEntry("other", None, make_context("ctx_other", "Other")),
        ])
        registry = {
            "concept1": {
                "id": "concept1",
                "canonical_name": "concept1",
                "form": "frequency",
                "status": "accepted",
                "definition": "test concept",
            },
        }

        records = detect_conflicts([cf], registry, context_hierarchy=hierarchy)
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT


# ── Step 6: CLI + Repository integration ─────────────────────────────


from click.testing import CliRunner
from propstore.cli import cli


class TestContextCLIIntegration:
    @staticmethod
    def _make_workspace(tmp_path):
        """Create a minimal workspace with concepts, forms, and contexts."""
        from propstore.cli.repository import Repository

        knowledge = tmp_path / "knowledge"
        repo = Repository.init(knowledge)
        concepts = knowledge / "concepts"
        forms = knowledge / "forms"

        # Write a form
        (forms / "structural.yaml").write_text(yaml.dump(
            {"name": "structural", "dimensionless": True}, default_flow_style=False))

        # Write a concept
        counters = concepts / ".counters"
        (counters / "global.next").write_text("2\n")
        concept_payload = normalize_concept_payloads([{
            "id": "concept1",
            "canonical_name": "test_concept",
            "status": "accepted",
            "definition": "A test concept",
            "domain": "test",
            "form": "structural",
            "created_date": "2026-03-22",
        }], default_domain="test")[0]
        (concepts / "test_concept.yaml").write_text(
            yaml.dump(concept_payload, default_flow_style=False)
        )

        repo.git.commit_files(
            {
                "forms/structural.yaml": (forms / "structural.yaml").read_bytes(),
                "concepts/test_concept.yaml": (concepts / "test_concept.yaml").read_bytes(),
            },
            "Seed context CLI workspace",
        )
        repo.git.sync_worktree()
        return tmp_path

    @staticmethod
    def _commit_workspace_paths(workspace, relpaths, message):
        from propstore.repo import KnowledgeRepo

        root = workspace / "knowledge"
        repo = KnowledgeRepo.open(root)
        repo.commit_files(
            {
                relpath: (root / relpath).read_bytes()
                for relpath in relpaths
            },
            message,
        )
        repo.sync_worktree()

    def test_build_with_contexts(self, tmp_path, monkeypatch):
        """pks build processes context files and creates sidecar tables."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        ctx_dir = ws / "knowledge" / "contexts"
        write_context(ctx_dir, "ctx_test", make_context("ctx_test", "Test", "A test context"))
        self._commit_workspace_paths(ws, ["contexts/ctx_test.yaml"], "Seed committed context")

        runner = CliRunner()
        result = runner.invoke(cli, ["build"])
        assert result.exit_code == 0, f"Build failed: {result.output}"

        # Verify context table exists and is populated
        import sqlite3
        conn = sqlite3.connect(ws / "knowledge" / "sidecar" / "propstore.sqlite")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM context").fetchall()
        assert len(rows) == 1
        assert rows[0]["id"] == "ctx_test"
        conn.close()

    def test_build_without_contexts_backward_compatible(self, tmp_path, monkeypatch):
        """pks build with no contexts/ dir still works."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        # Remove contexts dir
        import shutil
        shutil.rmtree(ws / "knowledge" / "contexts")

        runner = CliRunner()
        result = runner.invoke(cli, ["build"])
        assert result.exit_code == 0, f"Build failed: {result.output}"

    def test_context_add_creates_file(self, tmp_path, monkeypatch):
        """pks context add creates a YAML file."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        runner = CliRunner()
        result = runner.invoke(cli, [
            "context", "add",
            "--name", "ctx_test",
            "--description", "A test context",
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        path = ws / "knowledge" / "contexts" / "ctx_test.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert data["id"] == "ctx_test"
        assert data["name"] == "ctx_test"
        assert data["description"] == "A test context"

    def test_context_add_with_inherits(self, tmp_path, monkeypatch):
        """pks context add --inherits works."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        ctx_dir = ws / "knowledge" / "contexts"
        write_context(ctx_dir, "ctx_parent", make_context("ctx_parent", "Parent"))
        self._commit_workspace_paths(ws, ["contexts/ctx_parent.yaml"], "Seed committed parent context")
        runner = CliRunner()
        result = runner.invoke(cli, [
            "context", "add",
            "--name", "ctx_child",
            "--description", "A child",
            "--inherits", "ctx_parent",
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = yaml.safe_load((ctx_dir / "ctx_child.yaml").read_text())
        assert data["inherits"] == "ctx_parent"

    def test_context_add_duplicate_errors(self, tmp_path, monkeypatch):
        """Error if context already exists."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        ctx_dir = ws / "knowledge" / "contexts"
        write_context(ctx_dir, "ctx_dup", make_context("ctx_dup", "Dup"))
        self._commit_workspace_paths(ws, ["contexts/ctx_dup.yaml"], "Seed committed duplicate context")
        runner = CliRunner()
        result = runner.invoke(cli, [
            "context", "add", "--name", "ctx_dup", "--description", "Dup",
        ])
        assert result.exit_code != 0

    def test_context_list(self, tmp_path, monkeypatch):
        """pks context list shows registered contexts."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        ctx_dir = ws / "knowledge" / "contexts"
        write_context(ctx_dir, "ctx_a", make_context("ctx_a", "A"))
        write_context(ctx_dir, "ctx_b", make_context("ctx_b", "B"))
        self._commit_workspace_paths(
            ws,
            ["contexts/ctx_a.yaml", "contexts/ctx_b.yaml"],
            "Seed committed context list fixtures",
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["context", "list"])
        assert result.exit_code == 0
        assert "ctx_a" in result.output
        assert "ctx_b" in result.output

    def test_build_with_context_on_claim(self, tmp_path, monkeypatch):
        """A claim with context field gets context_id in sidecar."""
        ws = self._make_workspace(tmp_path)
        monkeypatch.chdir(ws)
        ctx_dir = ws / "knowledge" / "contexts"
        write_context(ctx_dir, "ctx_atms", make_context("ctx_atms", "ATMS"))

        claims_dir = ws / "knowledge" / "claims"
        (claims_dir / "test.yaml").write_text(yaml.dump(normalize_claims_payload({
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test in ATMS context",
                "concepts": ["test_concept"],
                "context": "ctx_atms",
                "provenance": {"paper": "test", "page": 1},
            }],
        }), default_flow_style=False))
        self._commit_workspace_paths(
            ws,
            ["contexts/ctx_atms.yaml", "claims/test.yaml"],
            "Seed committed contextual claim fixtures",
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["build"])
        assert result.exit_code == 0, f"Build failed: {result.output}"

        import sqlite3
        conn = sqlite3.connect(ws / "knowledge" / "sidecar" / "propstore.sqlite")
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT context_id FROM claim_core WHERE primary_logical_id = 'test:claim1'"
        ).fetchone()
        assert row["context_id"] == "ctx_atms"
        conn.close()
