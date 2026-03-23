"""Integration tests for ASPIC+ argumentation bridge.

Tests the full pipeline: stance graph → preference filter → Dung AF → extensions.
Uses in-memory SQLite with direct inserts for speed.
"""

from __future__ import annotations

import sqlite3

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.argumentation import (
    build_argumentation_framework,
    compute_justified_claims,
)
from propstore.dung import conflict_free, grounded_extension
from propstore.preference import claim_strength
from tests.sqlite_argumentation_store import SQLiteArgumentationStore
from tests.conftest import create_argumentation_schema


# ── SQLite fixture ──────────────────────────────────────────────────


def _insert_claim(conn: sqlite3.Connection, claim_id: str, concept_id: str,
                   value: float, sample_size: int | None = None,
                   uncertainty: float | None = None) -> None:
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, sample_size, uncertainty) "
        "VALUES (?, 'parameter', ?, ?, ?, ?)",
        (claim_id, concept_id, value, sample_size, uncertainty),
    )


def _insert_stance(conn: sqlite3.Connection, claim_id: str,
                    target_claim_id: str, stance_type: str,
                    confidence: float = 0.9) -> None:
    conn.execute(
        "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence) "
        "VALUES (?, ?, ?, ?)",
        (claim_id, target_claim_id, stance_type, confidence),
    )


@pytest.fixture
def conn():
    """In-memory SQLite with schema."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    create_argumentation_schema(c)
    return c


@pytest.fixture
def basic_scenario(conn):
    """Set up a basic scenario with known defeats.

    Claims for concept "c1":
      - claim_a: value=200, sample_size=1000 (strong)
      - claim_b: value=300, sample_size=10 (weak)
      - claim_c: value=250, sample_size=500 (medium)

    Stances:
      - claim_b rebuts claim_a (weak attacks strong → blocked by preference)
      - claim_a rebuts claim_b (strong attacks weak → succeeds)
      - claim_c undercuts claim_b (always succeeds)
      - claim_a supports claim_c (NOT a defeat — excluded)
    """
    _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=1000)
    _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=10)
    _insert_claim(conn, "claim_c", "c1", 250.0, sample_size=500)
    _insert_stance(conn, "claim_b", "claim_a", "rebuts")      # weak → strong (blocked)
    _insert_stance(conn, "claim_a", "claim_b", "rebuts")      # strong → weak (succeeds)
    _insert_stance(conn, "claim_c", "claim_b", "undercuts")   # always succeeds
    _insert_stance(conn, "claim_a", "claim_c", "supports")    # not a defeat
    conn.commit()
    return conn


@pytest.fixture
def supersedes_scenario(conn):
    """Scenario with supersession.

    Claims:
      - old_claim: value=100, sample_size=50
      - new_claim: value=200, sample_size=100

    Stances:
      - new_claim supersedes old_claim (always succeeds)
    """
    _insert_claim(conn, "old_claim", "c1", 100.0, sample_size=50)
    _insert_claim(conn, "new_claim", "c1", 200.0, sample_size=100)
    _insert_stance(conn, "new_claim", "old_claim", "supersedes")
    conn.commit()
    return conn


@pytest.fixture
def low_confidence_scenario(conn):
    """Stances below confidence threshold should be excluded.

    claim_x rebuts claim_y with confidence 0.3 (below 0.5 threshold).
    """
    _insert_claim(conn, "claim_x", "c1", 100.0, sample_size=100)
    _insert_claim(conn, "claim_y", "c1", 200.0, sample_size=100)
    _insert_stance(conn, "claim_x", "claim_y", "rebuts", confidence=0.3)
    conn.commit()
    return conn


# ── Tests: build_argumentation_framework ────────────────────────────


class TestBuildAF:
    def test_excludes_supports(self, basic_scenario):
        """Supports/explains stances do NOT appear in defeat relation."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(basic_scenario), {"claim_a", "claim_b", "claim_c"}
        )
        # claim_a supports claim_c should not be a defeat
        assert ("claim_a", "claim_c") not in af.defeats

    def test_includes_undercuts(self, basic_scenario):
        """Undercutting always produces defeat regardless of strength."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(basic_scenario), {"claim_a", "claim_b", "claim_c"}
        )
        assert ("claim_c", "claim_b") in af.defeats

    def test_includes_supersedes(self, supersedes_scenario):
        """Supersedes always produces defeat."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(supersedes_scenario), {"old_claim", "new_claim"}
        )
        assert ("new_claim", "old_claim") in af.defeats

    def test_rebut_blocked_when_weaker(self, basic_scenario):
        """Weak claim rebuting strong claim is blocked by preference."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(basic_scenario), {"claim_a", "claim_b", "claim_c"}
        )
        # claim_b (sample=10) rebuts claim_a (sample=1000) → blocked
        assert ("claim_b", "claim_a") not in af.defeats

    def test_rebut_succeeds_when_stronger(self, basic_scenario):
        """Strong claim rebuting weak claim succeeds."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(basic_scenario), {"claim_a", "claim_b", "claim_c"}
        )
        # claim_a (sample=1000) rebuts claim_b (sample=10) → succeeds
        assert ("claim_a", "claim_b") in af.defeats

    def test_confidence_threshold(self, low_confidence_scenario):
        """Stances below confidence threshold are excluded."""
        af = build_argumentation_framework(
            SQLiteArgumentationStore(low_confidence_scenario), {"claim_x", "claim_y"},
            confidence_threshold=0.5,
        )
        assert ("claim_x", "claim_y") not in af.defeats

    def test_arguments_match_input(self, basic_scenario):
        """AF arguments match the active claim IDs passed in."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(SQLiteArgumentationStore(basic_scenario), ids)
        assert af.arguments == frozenset(ids)

    def test_stances_referencing_inactive_claims_skipped(self, conn):
        """Stances whose source or target is not in active_claim_ids are silently skipped.

        Regression: .get(id, {}) created phantom attackers with neutral strength
        instead of skipping stale references.
        """
        _insert_claim(conn, "active_a", "c1", 100.0, sample_size=100)
        _insert_claim(conn, "active_b", "c1", 200.0, sample_size=100)
        _insert_claim(conn, "inactive_c", "c1", 300.0, sample_size=100)
        # Stances referencing inactive_c (not in active set)
        _insert_stance(conn, "inactive_c", "active_a", "rebuts")   # source inactive
        _insert_stance(conn, "active_b", "inactive_c", "rebuts")   # target inactive
        _insert_stance(conn, "inactive_c", "active_b", "supports") # support, source inactive
        # One valid stance between active claims
        _insert_stance(conn, "active_a", "active_b", "rebuts")
        conn.commit()

        active_ids = {"active_a", "active_b"}
        af = build_argumentation_framework(SQLiteArgumentationStore(conn), active_ids)

        # Only the valid stance between active claims should appear
        assert af.arguments == frozenset(active_ids)
        # Stances involving inactive_c must not appear anywhere
        for src, tgt in af.attacks:
            assert src in active_ids and tgt in active_ids
        for src, tgt in af.defeats:
            assert src in active_ids and tgt in active_ids


# ── Tests: compute_justified_claims ─────────────────────────────────


class TestComputeJustified:
    def test_grounded(self, basic_scenario):
        """Grounded extension: strong claims survive, weak ones eliminated."""
        result = compute_justified_claims(
            SQLiteArgumentationStore(basic_scenario),
            {"claim_a", "claim_b", "claim_c"},
            semantics="grounded",
        )
        # claim_a defeats claim_b, claim_c undercuts claim_b
        # claim_b is defeated, claim_a and claim_c are undefeated
        assert isinstance(result, frozenset)
        assert "claim_b" not in result
        assert "claim_a" in result

    def test_preferred(self, basic_scenario):
        """Preferred returns list of extensions."""
        result = compute_justified_claims(
            SQLiteArgumentationStore(basic_scenario),
            {"claim_a", "claim_b", "claim_c"},
            semantics="preferred",
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_stable(self, basic_scenario):
        """Stable returns list of extensions (may be empty)."""
        result = compute_justified_claims(
            SQLiteArgumentationStore(basic_scenario),
            {"claim_a", "claim_b", "claim_c"},
            semantics="stable",
        )
        assert isinstance(result, list)

    def test_supersedes_eliminates_old(self, supersedes_scenario):
        """Superseded claim is not in grounded extension."""
        result = compute_justified_claims(
            SQLiteArgumentationStore(supersedes_scenario),
            {"old_claim", "new_claim"},
            semantics="grounded",
        )
        assert "new_claim" in result
        assert "old_claim" not in result

    def test_no_stances_all_survive(self, conn):
        """No stances → empty defeat relation → all in grounded extension."""
        _insert_claim(conn, "c1", "x", 1.0)
        _insert_claim(conn, "c2", "x", 2.0)
        conn.commit()
        result = compute_justified_claims(SQLiteArgumentationStore(conn), {"c1", "c2"}, semantics="grounded")
        assert result == frozenset({"c1", "c2"})


# ── Property tests ──────────────────────────────────────────────────


_PROP_SETTINGS = settings(max_examples=100, deadline=None)


@st.composite
def stance_scenarios(draw):
    """Generate random stance scenarios for property testing."""
    n = draw(st.integers(2, 5))
    claim_ids = [f"c{i}" for i in range(n)]
    attack_types = ["rebuts", "undercuts", "undermines", "supports", "explains", "supersedes"]
    n_stances = draw(st.integers(0, n * 2))
    stances = []
    for _ in range(n_stances):
        a = draw(st.sampled_from(claim_ids))
        b = draw(st.sampled_from(claim_ids))
        t = draw(st.sampled_from(attack_types))
        conf = draw(st.floats(0.0, 1.0, allow_nan=False))
        if a != b:
            stances.append((a, b, t, conf))
    sample_sizes = {cid: draw(st.integers(1, 10000)) for cid in claim_ids}
    return claim_ids, stances, sample_sizes


@st.composite
def active_stance_scenarios(draw):
    claim_ids, stances, sample_sizes = draw(stance_scenarios())
    active_ids = set(draw(
        st.lists(
            st.sampled_from(claim_ids),
            unique=True,
            min_size=0,
            max_size=len(claim_ids),
        )
    ))
    return claim_ids, stances, sample_sizes, active_ids


def _build_scenario_db(claim_ids, stances, sample_sizes):
    """Build an in-memory SQLite from generated scenario."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_argumentation_schema(conn)
    for cid in claim_ids:
        _insert_claim(conn, cid, "concept", float(hash(cid) % 1000),
                       sample_size=sample_sizes[cid])
    for a, b, t, conf in stances:
        _insert_stance(conn, a, b, t, confidence=conf)
    conn.commit()
    return conn


class TestAFProperties:
    @given(stance_scenarios())
    @_PROP_SETTINGS
    def test_no_supports_in_defeats(self, scenario):
        """P1: Support/explain stances never appear as direct attacks.

        In the bipolar AF, support edges can still induce derived defeats via
        Cayrol supported/indirect defeat. The invariant we can enforce here is
        that support/explain pairs are excluded from the direct attack layer.
        """
        claim_ids, stances, sample_sizes = scenario
        conn = _build_scenario_db(claim_ids, stances, sample_sizes)
        af = build_argumentation_framework(SQLiteArgumentationStore(conn), set(claim_ids))
        support_only_pairs = set()
        for a, b, t, conf in stances:
            if t in ("supports", "explains") and conf >= 0.5:
                support_only_pairs.add((a, b))
        for a, b, t, conf in stances:
            if t not in ("supports", "explains") and conf >= 0.5:
                support_only_pairs.discard((a, b))
        # Pairs that ONLY have support/explains stances should not be attacks.
        # They may still show up in defeats through support-aware derivation.
        for pair in support_only_pairs:
            assert pair not in af.attacks

    @given(stance_scenarios())
    @_PROP_SETTINGS
    def test_grounded_is_conflict_free(self, scenario):
        """P3: Grounded extension of constructed AF is conflict-free."""
        claim_ids, stances, sample_sizes = scenario
        conn = _build_scenario_db(claim_ids, stances, sample_sizes)
        af = build_argumentation_framework(SQLiteArgumentationStore(conn), set(claim_ids))
        ext = grounded_extension(af)
        assert conflict_free(ext, af.defeats)

    @given(active_stance_scenarios())
    @_PROP_SETTINGS
    def test_af_arguments_never_introduce_claims_outside_active_set(self, scenario):
        """AF construction is closed over the provided active set."""
        claim_ids, stances, sample_sizes, active_ids = scenario
        conn = _build_scenario_db(claim_ids, stances, sample_sizes)
        af = build_argumentation_framework(SQLiteArgumentationStore(conn), active_ids)
        assert af.arguments == frozenset(active_ids)
        assert af.defeats <= {
            (source, target)
            for source in active_ids
            for target in active_ids
        }

    @given(stance_scenarios())
    @_PROP_SETTINGS
    def test_justified_subset_of_input(self, scenario):
        """Justified claims are always a subset of input claim IDs."""
        claim_ids, stances, sample_sizes = scenario
        conn = _build_scenario_db(claim_ids, stances, sample_sizes)
        result = compute_justified_claims(SQLiteArgumentationStore(conn), set(claim_ids), semantics="grounded")
        assert result <= frozenset(claim_ids)
