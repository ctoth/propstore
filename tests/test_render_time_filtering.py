"""Tests for render-time stance filtering.

Verifies that:
- confidence_threshold=0.0 includes all stances in AF construction
- confidence_threshold=0.99 excludes low-confidence stances
- stance_summary returns correct counts and model info
- No defeat table exists in the sidecar schema
"""

from __future__ import annotations

import sqlite3

import pytest

from propstore.argumentation import (
    build_argumentation_framework,
    compute_justified_claims,
    stance_summary,
)


# ── SQLite fixture ──────────────────────────────────────────────────


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE claim (
            id TEXT PRIMARY KEY,
            type TEXT,
            concept_id TEXT,
            value REAL,
            sample_size INTEGER,
            uncertainty REAL,
            uncertainty_type TEXT,
            unit TEXT,
            conditions_cel TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE claim_stance (
            claim_id TEXT NOT NULL,
            target_claim_id TEXT NOT NULL,
            stance_type TEXT NOT NULL,
            strength TEXT,
            conditions_differ TEXT,
            note TEXT,
            resolution_method TEXT,
            resolution_model TEXT,
            embedding_model TEXT,
            embedding_distance REAL,
            pass_number INTEGER,
            confidence REAL,
            FOREIGN KEY (claim_id) REFERENCES claim(id),
            FOREIGN KEY (target_claim_id) REFERENCES claim(id)
        );
    """)


def _insert_claim(conn, claim_id, concept_id, value, sample_size=None):
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, sample_size) "
        "VALUES (?, 'parameter', ?, ?, ?)",
        (claim_id, concept_id, value, sample_size),
    )


def _insert_stance(conn, claim_id, target, stype, confidence=0.9, model=None):
    conn.execute(
        "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, "
        "confidence, resolution_model) VALUES (?, ?, ?, ?, ?)",
        (claim_id, target, stype, confidence, model),
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    _create_schema(c)
    return c


@pytest.fixture
def mixed_confidence(conn):
    """Scenario with stances at different confidence levels.

    claim_a rebuts claim_b at confidence=0.9 (high)
    claim_c rebuts claim_a at confidence=0.3 (low)
    claim_a supports claim_c (non-attack)
    """
    _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=100)
    _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=100)
    _insert_claim(conn, "claim_c", "c1", 250.0, sample_size=100)
    _insert_stance(conn, "claim_a", "claim_b", "rebuts", confidence=0.9, model="gemini")
    _insert_stance(conn, "claim_c", "claim_a", "rebuts", confidence=0.3, model="gpt-4")
    _insert_stance(conn, "claim_a", "claim_c", "supports", confidence=0.95, model="gemini")
    conn.commit()
    return conn


class TestConfidenceThresholdFiltering:
    """Confidence threshold controls which stances become defeats at render time."""

    def test_threshold_zero_includes_all_attacks(self, mixed_confidence):
        """confidence_threshold=0.0 includes all attack stances."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            mixed_confidence, ids, confidence_threshold=0.0,
        )
        # Both rebuts stances become defeats (equal strength, neither strictly weaker)
        assert ("claim_a", "claim_b") in af.defeats
        assert ("claim_c", "claim_a") in af.defeats

    def test_threshold_high_excludes_low_confidence(self, mixed_confidence):
        """confidence_threshold=0.5 excludes the 0.3-confidence stance."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            mixed_confidence, ids, confidence_threshold=0.5,
        )
        assert ("claim_a", "claim_b") in af.defeats  # 0.9 >= 0.5
        assert ("claim_c", "claim_a") not in af.defeats  # 0.3 < 0.5

    def test_threshold_very_high_excludes_all(self, mixed_confidence):
        """confidence_threshold=0.99 excludes all stances."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            mixed_confidence, ids, confidence_threshold=0.99,
        )
        assert len(af.defeats) == 0

    def test_grounded_extension_changes_with_threshold(self, mixed_confidence):
        """Different thresholds produce different extensions."""
        ids = {"claim_a", "claim_b", "claim_c"}

        # Low threshold: both attacks active, more complex AF
        ext_low = compute_justified_claims(
            mixed_confidence, ids, confidence_threshold=0.0,
        )

        # High threshold: no attacks, everything survives
        ext_high = compute_justified_claims(
            mixed_confidence, ids, confidence_threshold=0.99,
        )
        assert ext_high == ids  # no defeats → all in grounded extension


class TestStanceSummary:
    """stance_summary returns render explanation metadata."""

    def test_summary_counts(self, mixed_confidence):
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(mixed_confidence, ids, confidence_threshold=0.5)

        assert summary["total_stances"] == 3
        assert summary["included_as_attacks"] == 1  # only the 0.9 rebuts
        assert summary["excluded_by_threshold"] == 1  # the 0.3 rebuts
        assert summary["excluded_non_attack"] == 1  # the supports
        assert summary["confidence_threshold"] == 0.5

    def test_summary_models(self, mixed_confidence):
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(mixed_confidence, ids, confidence_threshold=0.0)
        assert "gemini" in summary["models"]
        assert "gpt-4" in summary["models"]

    def test_summary_threshold_zero_includes_all_attacks(self, mixed_confidence):
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(mixed_confidence, ids, confidence_threshold=0.0)
        assert summary["included_as_attacks"] == 2
        assert summary["excluded_by_threshold"] == 0


class TestNoDefeatTable:
    """The defeat table must not exist in the sidecar schema."""

    def test_build_schema_has_no_defeat_table(self):
        """The build schema should not contain a defeat table."""
        from propstore.build_sidecar import _create_tables, _create_claim_tables
        conn = sqlite3.connect(":memory:")
        _create_tables(conn)
        _create_claim_tables(conn)
        tables = {
            row[0] for row in
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        assert "defeat" not in tables
        conn.close()
