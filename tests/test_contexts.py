"""Tests for context loading, validation, hierarchy, and sidecar integration."""

import pytest
import yaml

from propstore.validate_contexts import (
    ContextHierarchy,
    LoadedContext,
    load_contexts,
    validate_contexts,
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


# ── Step 1: Loading ──────────────────────────────────────────────────


class TestLoadContexts:
    def test_load_context_files(self, tmp_path):
        """Load context YAML files from a directory, returns list of LoadedContext."""
        write_context(tmp_path, "ctx_foo", make_context("ctx_foo", "Foo"))
        write_context(tmp_path, "ctx_bar", make_context("ctx_bar", "Bar"))
        contexts = load_contexts(tmp_path)
        assert len(contexts) == 2
        assert all(isinstance(c, LoadedContext) for c in contexts)
        ids = {c.data["id"] for c in contexts}
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
        contexts = [LoadedContext("ctx_foo", tmp_path / "ctx_foo.yaml",
                                 make_context("ctx_foo", "Foo", "A test context"))]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_missing_id_errors(self, tmp_path):
        """Context without id is an error."""
        contexts = [LoadedContext("ctx_bad", tmp_path / "ctx_bad.yaml",
                                 {"name": "Bad"})]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("id" in e.lower() for e in result.errors)

    def test_missing_name_errors(self, tmp_path):
        """Context without name is an error."""
        contexts = [LoadedContext("ctx_bad", tmp_path / "ctx_bad.yaml",
                                 {"id": "ctx_bad"})]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("name" in e.lower() for e in result.errors)

    def test_inherits_must_exist(self, tmp_path):
        """Validation error if inherits references nonexistent context."""
        contexts = [LoadedContext("ctx_child", tmp_path / "ctx_child.yaml",
                                 make_context("ctx_child", "Child", inherits="ctx_nonexistent"))]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("nonexistent" in e.lower() or "inherits" in e.lower() for e in result.errors)

    def test_inherits_valid_reference(self, tmp_path):
        """No error when inherits references an existing context."""
        contexts = [
            LoadedContext("ctx_parent", tmp_path / "a.yaml",
                         make_context("ctx_parent", "Parent")),
            LoadedContext("ctx_child", tmp_path / "b.yaml",
                         make_context("ctx_child", "Child", inherits="ctx_parent")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_excludes_must_exist(self, tmp_path):
        """Validation error if excludes references nonexistent context."""
        contexts = [LoadedContext("ctx_a", tmp_path / "a.yaml",
                                 make_context("ctx_a", "A", excludes=["ctx_nonexistent"]))]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("nonexistent" in e.lower() or "excludes" in e.lower() for e in result.errors)

    def test_excludes_valid_reference(self, tmp_path):
        """No error when excludes references an existing context."""
        contexts = [
            LoadedContext("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A", excludes=["ctx_b"])),
            LoadedContext("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_no_inheritance_cycles(self, tmp_path):
        """Validation error if inheritance forms A->B->A cycle."""
        contexts = [
            LoadedContext("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A", inherits="ctx_b")),
            LoadedContext("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B", inherits="ctx_a")),
        ]
        result = validate_contexts(contexts)
        assert not result.ok
        assert any("cycle" in e.lower() for e in result.errors)

    def test_deep_inheritance_ok(self, tmp_path):
        """A->B->C inheritance chain is valid."""
        contexts = [
            LoadedContext("ctx_a", tmp_path / "a.yaml",
                         make_context("ctx_a", "A")),
            LoadedContext("ctx_b", tmp_path / "b.yaml",
                         make_context("ctx_b", "B", inherits="ctx_a")),
            LoadedContext("ctx_c", tmp_path / "c.yaml",
                         make_context("ctx_c", "C", inherits="ctx_b")),
        ]
        result = validate_contexts(contexts)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_duplicate_context_id_errors(self, tmp_path):
        """Two context files with same id is an error."""
        contexts = [
            LoadedContext("file1", tmp_path / "file1.yaml",
                         make_context("ctx_dup", "Dup 1")),
            LoadedContext("file2", tmp_path / "file2.yaml",
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
            LoadedContext("root", None, make_context("ctx_root", "Root")),
            LoadedContext("mid", None, make_context("ctx_mid", "Mid", inherits="ctx_root")),
            LoadedContext("leaf", None, make_context("ctx_leaf", "Leaf", inherits="ctx_mid")),
            LoadedContext("other", None, make_context("ctx_other", "Other", excludes=["ctx_root"])),
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
            LoadedContext("root", None, make_context("ctx_root", "Root",
                                                     assumptions=["framework == 'general'"])),
            LoadedContext("child", None, make_context("ctx_child", "Child",
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


# ── Step 2: Context tables in sidecar ────────────────────────────────

import sqlite3
from propstore.build_sidecar import (
    _create_context_tables,
    _populate_contexts,
)


class TestContextSidecar:
    def _make_conn(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn

    def test_create_context_tables(self):
        """_create_context_tables creates all three tables."""
        conn = self._make_conn()
        _create_context_tables(conn)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "context" in tables
        assert "context_assumption" in tables
        assert "context_exclusion" in tables

    def test_populate_contexts(self):
        """Contexts from LoadedContext list appear in context table."""
        conn = self._make_conn()
        _create_context_tables(conn)
        contexts = [
            LoadedContext("a", None, make_context("ctx_a", "A", "Desc A")),
            LoadedContext("b", None, make_context("ctx_b", "B", "Desc B")),
        ]
        _populate_contexts(conn, contexts)
        rows = conn.execute("SELECT * FROM context").fetchall()
        assert len(rows) == 2
        ids = {r["id"] for r in rows}
        assert ids == {"ctx_a", "ctx_b"}

    def test_populate_assumptions(self):
        """Context assumptions appear in context_assumption table in order."""
        conn = self._make_conn()
        _create_context_tables(conn)
        contexts = [
            LoadedContext("a", None, make_context("ctx_a", "A",
                         assumptions=["x == 1", "y == 2"])),
        ]
        _populate_contexts(conn, contexts)
        rows = conn.execute(
            "SELECT * FROM context_assumption WHERE context_id='ctx_a' ORDER BY seq"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["assumption_cel"] == "x == 1"
        assert rows[1]["assumption_cel"] == "y == 2"

    def test_populate_exclusions(self):
        """Exclusion pairs appear in context_exclusion table."""
        conn = self._make_conn()
        _create_context_tables(conn)
        contexts = [
            LoadedContext("a", None, make_context("ctx_a", "A", excludes=["ctx_b"])),
            LoadedContext("b", None, make_context("ctx_b", "B")),
        ]
        _populate_contexts(conn, contexts)
        rows = conn.execute("SELECT * FROM context_exclusion").fetchall()
        assert len(rows) == 1
        assert rows[0]["context_a"] == "ctx_a"
        assert rows[0]["context_b"] == "ctx_b"

    def test_populate_inherits(self):
        """Parent reference is stored in context.inherits column."""
        conn = self._make_conn()
        _create_context_tables(conn)
        contexts = [
            LoadedContext("p", None, make_context("ctx_parent", "Parent")),
            LoadedContext("c", None, make_context("ctx_child", "Child", inherits="ctx_parent")),
        ]
        _populate_contexts(conn, contexts)
        row = conn.execute("SELECT inherits FROM context WHERE id='ctx_child'").fetchone()
        assert row["inherits"] == "ctx_parent"

    def test_empty_contexts_ok(self):
        """Build succeeds with no contexts."""
        conn = self._make_conn()
        _create_context_tables(conn)
        _populate_contexts(conn, [])
        assert conn.execute("SELECT COUNT(*) FROM context").fetchone()[0] == 0


# ── Step 3: Claim context_id ────────────────────────────────────────


class TestClaimContextId:
    def test_claim_context_must_exist(self, tmp_path):
        """Validation error if claim references nonexistent context."""
        from propstore.validate_claims import LoadedClaimFile, validate_claims

        claim_file = LoadedClaimFile("test", tmp_path / "test.yaml", {
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "context": "ctx_nonexistent",
                "provenance": {"paper": "test", "page": 1},
            }],
        })
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
        from propstore.validate_claims import LoadedClaimFile, validate_claims

        claim_file = LoadedClaimFile("test", tmp_path / "test.yaml", {
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "context": "ctx_atms",
                "provenance": {"paper": "test", "page": 1},
            }],
        })
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
        from propstore.validate_claims import LoadedClaimFile, validate_claims

        claim_file = LoadedClaimFile("test", tmp_path / "test.yaml", {
            "source": {"paper": "test"},
            "claims": [{
                "id": "claim1",
                "type": "observation",
                "statement": "Test statement.",
                "concepts": ["fundamental_frequency"],
                "provenance": {"paper": "test", "page": 1},
            }],
        })
        registry = {
            "fundamental_frequency": {
                "id": "concept1", "canonical_name": "fundamental_frequency",
                "form": "frequency", "status": "accepted", "definition": "F0",
            },
        }
        result = validate_claims([claim_file], registry, context_ids=set())
        ctx_errors = [e for e in result.errors if "context" in e.lower()]
        assert not ctx_errors, f"No-context claim rejected: {ctx_errors}"
