"""Tests for render-time stance filtering — soft epsilon prune.

Verifies that:
- Low-confidence stances now participate in AF construction (no hard gate)
- Only vacuous stances (opinion_uncertainty > 0.99) are pruned
- stance_summary reports opinion-aware statistics
- confidence_threshold has been hard-deleted from all APIs
- No defeat table exists in the sidecar schema

Per Li et al. (2012, Def 2): each stance has existence probability,
not binary include/exclude.
Per CLAUDE.md design checklist: no gates before render time.
"""

from __future__ import annotations

import sqlite3

import pytest

from propstore.argumentation import (
    build_argumentation_framework,
    compute_claim_graph_justified_claims,
    stance_summary,
)
from tests.sqlite_argumentation_store import SQLiteArgumentationStore
from tests.conftest import create_argumentation_schema


def _insert_claim(conn, claim_id, concept_id, value, sample_size=None,
                   uncertainty=None, confidence=None):
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, sample_size, uncertainty, confidence) "
        "VALUES (?, 'parameter', ?, ?, ?, ?, ?)",
        (claim_id, concept_id, value, sample_size, uncertainty, confidence),
    )


def _insert_stance(conn, claim_id, target, stype, confidence=0.9, model=None,
                   opinion_uncertainty=None):
    conn.execute(
        "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, "
        "confidence, resolution_model, opinion_uncertainty) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, target, stype, confidence, model, opinion_uncertainty),
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    create_argumentation_schema(c)
    return c


@pytest.fixture
def mixed_confidence(conn):
    """Scenario with stances at different confidence levels.

    claim_a rebuts claim_b at confidence=0.9 (high)
    claim_c rebuts claim_a at confidence=0.3 (low — previously excluded by threshold)
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


@pytest.fixture
def vacuous_stances(conn):
    """Scenario with vacuous opinion stances (u > 0.99).

    claim_a rebuts claim_b with vacuous opinion (u=1.0)
    claim_c rebuts claim_a with normal opinion (u=0.3)
    """
    _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=100)
    _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=100)
    _insert_claim(conn, "claim_c", "c1", 250.0, sample_size=100)
    _insert_stance(conn, "claim_a", "claim_b", "rebuts", confidence=0.5,
                   opinion_uncertainty=1.0, model="gemini")
    _insert_stance(conn, "claim_c", "claim_a", "rebuts", confidence=0.7,
                   opinion_uncertainty=0.3, model="gpt-4")
    conn.commit()
    return conn


@pytest.fixture
def all_vacuous(conn):
    """Scenario where ALL stances are vacuous."""
    _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=100)
    _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=100)
    _insert_stance(conn, "claim_a", "claim_b", "rebuts", confidence=0.5,
                   opinion_uncertainty=0.995, model="gemini")
    _insert_stance(conn, "claim_b", "claim_a", "rebuts", confidence=0.5,
                   opinion_uncertainty=1.0, model="gpt-4")
    conn.commit()
    return conn


class TestSoftEpsilonPrune:
    """Soft epsilon prune: only vacuous opinions (u > 0.99) are pruned.

    Per Li et al. (2012, Def 2): each stance has existence probability,
    not binary include/exclude. The hard confidence_threshold gate has
    been replaced with a soft prune that only removes stances carrying
    zero information content.
    """

    def test_low_confidence_stances_participate(self, mixed_confidence):
        """A stance with confidence 0.3 now participates in AF construction.

        Per Li et al. (2012, Def 2): each stance has existence probability,
        not binary include/exclude.
        """
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(mixed_confidence), ids,
        )
        # Both rebuts stances participate — the 0.3 confidence stance is
        # no longer excluded by a hard threshold gate
        assert ("claim_a", "claim_b") in af.defeats
        assert ("claim_c", "claim_a") in af.defeats

    def test_vacuous_stances_survive_af(self, vacuous_stances):
        """A stance with opinion_uncertainty > 0.99 survives AF construction.

        Per CLAUDE.md design checklist: no gates before render time.
        Vacuous opinions (Josang 2001, p.8) participate in the AF structure;
        filtering is deferred to render/resolution time.
        """
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(vacuous_stances), ids,
        )
        # claim_a->claim_b has u=1.0 (vacuous) — still in the AF
        assert ("claim_a", "claim_b") in af.attacks
        # claim_c->claim_a has u=0.3 (informative) — participates
        assert ("claim_c", "claim_a") in af.defeats

    def test_high_confidence_stances_unchanged(self, mixed_confidence):
        """Stances with high confidence continue to participate exactly as before."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(mixed_confidence), ids,
        )
        # The 0.9 confidence rebuts stance still produces a defeat
        assert ("claim_a", "claim_b") in af.defeats

    def test_confidence_threshold_removed(self):
        """RenderPolicy no longer has a confidence_threshold field.
        build_argumentation_framework no longer accepts confidence_threshold.
        Hard deleted, not deprecated.
        """
        import inspect
        from propstore.world.types import RenderPolicy

        # RenderPolicy should not have confidence_threshold
        assert not hasattr(RenderPolicy(), "confidence_threshold"), \
            "confidence_threshold should be hard-deleted from RenderPolicy"

        # build_argumentation_framework should not accept confidence_threshold
        sig = inspect.signature(build_argumentation_framework)
        assert "confidence_threshold" not in sig.parameters, \
            "confidence_threshold should be hard-deleted from build_argumentation_framework"

        # compute_claim_graph_justified_claims should not accept it either
        sig2 = inspect.signature(compute_claim_graph_justified_claims)
        assert "confidence_threshold" not in sig2.parameters, \
            "confidence_threshold should be hard-deleted from compute_claim_graph_justified_claims"

        # stance_summary should not accept it either
        sig3 = inspect.signature(stance_summary)
        assert "confidence_threshold" not in sig3.parameters, \
            "confidence_threshold should be hard-deleted from stance_summary"

    def test_stance_summary_reports_uncertainty(self, vacuous_stances):
        """stance_summary() reports opinion statistics: count of vacuous
        stances and mean uncertainty of all included stances."""
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(SQLiteArgumentationStore(vacuous_stances), ids)

        assert summary["total_stances"] == 2
        assert summary["vacuous_count"] == 1  # the u=1.0 stance (counted, not pruned)
        assert summary["included_as_attacks"] == 2  # both stances participate
        assert "mean_uncertainty" in summary
        # mean of [1.0, 0.3] = 0.65
        assert abs(summary["mean_uncertainty"] - 0.65) < 0.01

    def test_af_with_all_vacuous_stances(self, all_vacuous):
        """When ALL stances are vacuous (u > 0.99), they still appear in the AF.

        No build-time gate — vacuous stances participate in AF construction.
        Filtering is deferred to render/resolution time.
        """
        ids = {"claim_a", "claim_b"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(all_vacuous), ids,
        )
        # Both vacuous stances survive into the AF
        assert len(af.attacks) == 2

    def test_af_includes_more_stances_than_before(self, mixed_confidence):
        """The new AF includes stances that the old threshold (0.5) would
        have excluded. The 0.3-confidence stance now participates, resulting
        in more attack edges (and consequently more defeats including Cayrol
        derived defeats from support chains)."""
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(mixed_confidence), ids,
        )
        # Under old behavior with threshold=0.5, only 1 attack edge existed
        # (claim_a rebuts claim_b at 0.9). Now the 0.3-confidence stance
        # (claim_c rebuts claim_a) also participates, giving 2 attack edges.
        assert len(af.attacks) == 2
        # Both direct attacks produce defeats (equal strength claims)
        assert ("claim_a", "claim_b") in af.attacks
        assert ("claim_c", "claim_a") in af.attacks

    def test_epsilon_threshold_very_low(self, conn):
        """Stances with confidence 0.01 (very low but not vacuous) still
        participate. Only truly vacuous stances (opinion-based, u > 0.99)
        are pruned."""
        _insert_claim(conn, "claim_a", "c1", 100.0, sample_size=100)
        _insert_claim(conn, "claim_b", "c1", 200.0, sample_size=100)
        _insert_stance(conn, "claim_a", "claim_b", "rebuts", confidence=0.01,
                       opinion_uncertainty=0.5)
        conn.commit()
        ids = {"claim_a", "claim_b"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(conn), ids,
        )
        # Very low confidence but non-vacuous opinion — still participates
        assert ("claim_a", "claim_b") in af.defeats


class TestStanceSummary:
    """stance_summary returns render explanation metadata with opinion-aware stats."""

    def test_summary_counts(self, mixed_confidence):
        """Summary includes all attack stances (no threshold filtering)."""
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(SQLiteArgumentationStore(mixed_confidence), ids)

        assert summary["total_stances"] == 3
        # Both rebuts stances are now included (0.9 and 0.3)
        assert summary["included_as_attacks"] == 2
        assert summary["excluded_non_attack"] == 1  # the supports
        assert summary["vacuous_count"] == 0  # no vacuous stances

    def test_summary_models(self, mixed_confidence):
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(SQLiteArgumentationStore(mixed_confidence), ids)
        assert "gemini" in summary["models"]
        assert "gpt-4" in summary["models"]

    def test_summary_no_confidence_threshold_key(self, mixed_confidence):
        """Summary dict should NOT contain confidence_threshold key."""
        ids = {"claim_a", "claim_b", "claim_c"}
        summary = stance_summary(SQLiteArgumentationStore(mixed_confidence), ids)
        assert "confidence_threshold" not in summary
        assert "excluded_by_threshold" not in summary


class TestVacuousSurvivesAFConstruction:
    """Vacuous stances must survive into the AF and only be filtered at render time.

    Finding 11 / F14: argumentation.py:137 prunes vacuous opinions (u > 0.99)
    at AF construction time. This is a build-time gate that violates the design
    checklist: "Does this add a gate anywhere before render time? If yes → WRONG."

    Per CLAUDE.md: vacuous stances should flow into storage/AF with provenance
    and only be filtered at render/resolution time.
    """

    def test_vacuous_stance_survives_af_construction(self, vacuous_stances):
        """A stance with opinion_uncertainty > 0.99 MUST be present in the AF.

        The AF is a structural representation of all arguments and attacks.
        Filtering out vacuous stances at construction time is a build-time gate.
        The stance should appear as an attack edge in the AF, even if its
        opinion is vacuous. Render-time filtering (resolution strategies,
        extension computation) will handle it appropriately.

        EXPECTED TO FAIL: current code prunes vacuous stances at line 137.
        """
        ids = {"claim_a", "claim_b", "claim_c"}
        af = build_argumentation_framework(
            SQLiteArgumentationStore(vacuous_stances), ids,
        )
        # claim_a -> claim_b has u=1.0 (vacuous) — should still be in the AF
        # as an attack edge. The AF is structural; filtering is for render time.
        assert ("claim_a", "claim_b") in af.attacks, (
            "Vacuous stance (u=1.0) was pruned at AF construction time. "
            "This is a build-time gate that violates the design checklist."
        )

    def test_vacuous_stance_does_not_win_resolution(self, conn):
        """A vacuous stance should not cause its source to win resolution.

        When claim_v (vacuous attacker, u=1.0) attacks claim_s (strong, no
        vacuous opinion), claim_s should still win in the grounded extension.
        The vacuous attack carries no information and should not eliminate
        the target. This is render-time behavior — the test should PASS.
        """
        # claim_s: strong across all dimensions
        _insert_claim(conn, "claim_s", "c1", 200.0, sample_size=1000, uncertainty=0.05, confidence=0.9)
        # claim_v: weak across all dimensions
        _insert_claim(conn, "claim_v", "c1", 300.0, sample_size=10, uncertainty=0.8, confidence=0.2)
        # claim_v rebuts claim_s with vacuous opinion — should not eliminate claim_s
        _insert_stance(conn, "claim_v", "claim_s", "rebuts", confidence=0.5,
                       opinion_uncertainty=1.0)
        # claim_s rebuts claim_v with strong opinion — should eliminate claim_v
        _insert_stance(conn, "claim_s", "claim_v", "rebuts", confidence=0.9,
                       opinion_uncertainty=0.1)
        conn.commit()

        ids = {"claim_s", "claim_v"}
        result = compute_claim_graph_justified_claims(
            SQLiteArgumentationStore(conn), ids, semantics="grounded",
        )
        # claim_s should survive — it has a strong attack on claim_v,
        # and claim_v's vacuous attack should not eliminate claim_s
        # (either because it's filtered at render time, or because
        # the preference ordering blocks the weak attacker anyway)
        assert "claim_s" in result, (
            "Strong claim was eliminated by a vacuous attacker"
        )


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
