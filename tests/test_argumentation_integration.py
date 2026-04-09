"""Integration tests for ASPIC+ argumentation bridge.

Tests the full pipeline: stance graph → preference filter → Dung AF → extensions.
Uses in-memory SQLite with direct inserts for speed.
"""

from __future__ import annotations

import sqlite3

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.claim_graph import (
    build_argumentation_framework,
    compute_claim_graph_justified_claims,
)
from propstore.dung import conflict_free, grounded_extension
from propstore.praf import build_praf
from propstore.preference import claim_strength
from tests.sqlite_argumentation_store import SQLiteArgumentationStore
from tests.conftest import (
    create_argumentation_schema,
    insert_claim,
    insert_conflict,
    insert_stance,
)


# ── SQLite fixture ──────────────────────────────────────────────────


def _insert_claim(conn: sqlite3.Connection, claim_id: str, concept_id: str,
                   value: float, sample_size: int | None = None,
                   uncertainty: float | None = None,
                   confidence: float | None = None) -> None:
    insert_claim(
        conn,
        claim_id,
        claim_type="parameter",
        concept_id=concept_id,
        value=value,
        sample_size=sample_size,
        uncertainty=uncertainty,
        confidence=confidence,
    )


def _insert_stance(conn: sqlite3.Connection, claim_id: str,
                     target_claim_id: str, stance_type: str,
                     confidence: float = 0.9) -> None:
    insert_stance(
        conn,
        claim_id,
        target_claim_id,
        stance_type,
        confidence=confidence,
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
      - claim_a: value=200, sample_size=1000, uncertainty=0.05, confidence=0.9 (strong)
      - claim_b: value=300, sample_size=10, uncertainty=0.8, confidence=0.2 (weak)
      - claim_c: value=250, sample_size=500, uncertainty=0.2, confidence=0.7 (medium)

    With fixed-length 3-element vectors (Phase 3), all three dimensions must
    differ for elitist comparison (Modgil & Prakken 2018 Def 19) to distinguish
    weak from strong claims. Vectors:
      - claim_a: [log1p(1000)=6.91, 1/0.05=20.0, 0.9]
      - claim_b: [log1p(10)=2.40, 1/0.8=1.25, 0.2]  — min(0.2) < min(claim_a=0.9)
      - claim_c: [log1p(500)=6.22, 1/0.2=5.0, 0.7]

    Stances:
      - claim_b rebuts claim_a (weak attacks strong → blocked by preference)
      - claim_a rebuts claim_b (strong attacks weak → succeeds)
      - claim_c undercuts claim_b (always succeeds)
      - claim_a supports claim_c (NOT a defeat — excluded)
    """
    _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=1000, uncertainty=0.05, confidence=0.9)
    _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=10, uncertainty=0.8, confidence=0.2)
    _insert_claim(conn, "claim_c", "c1", 250.0, sample_size=500, uncertainty=0.2, confidence=0.7)
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
def vacuous_opinion_scenario(conn):
    """Stances with vacuous opinion (u > 0.99) survive AF construction.

    claim_x rebuts claim_y with vacuous opinion (opinion_uncertainty=1.0).
    Per CLAUDE.md design checklist: no gates before render time.
    Vacuous opinions (Josang 2001, p.8) are counted but not pruned.
    """
    _insert_claim(conn, "claim_x", "c1", 100.0, sample_size=100)
    _insert_claim(conn, "claim_y", "c1", 200.0, sample_size=100)
    insert_stance(
        conn,
        "claim_x",
        "claim_y",
        "rebuts",
        confidence=0.3,
        opinion_uncertainty=1.0,
    )
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

    def test_vacuous_opinion_survives_af(self, vacuous_opinion_scenario):
        """Stances with vacuous opinion (u > 0.99) survive AF construction.

        Per CLAUDE.md design checklist: no gates before render time.
        Vacuous opinions (Josang 2001, p.8) are counted but not pruned —
        filtering is deferred to render/resolution time.
        Per Li et al. (2012, Def 2): stances participate with their
        existence probability, not binary gated.
        """
        af = build_argumentation_framework(
            SQLiteArgumentationStore(vacuous_opinion_scenario), {"claim_x", "claim_y"},
        )
        assert ("claim_x", "claim_y") in af.defeats

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


# ── Tests: compute_claim_graph_justified_claims ─────────────────────────────────


class TestComputeJustified:
    def test_grounded(self, basic_scenario):
        """Grounded returns the canonical Dung-grounded survivors."""
        result = compute_claim_graph_justified_claims(
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
        result = compute_claim_graph_justified_claims(
            SQLiteArgumentationStore(basic_scenario),
            {"claim_a", "claim_b", "claim_c"},
            semantics="preferred",
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_stable(self, basic_scenario):
        """Stable returns list of extensions (may be empty)."""
        result = compute_claim_graph_justified_claims(
            SQLiteArgumentationStore(basic_scenario),
            {"claim_a", "claim_b", "claim_c"},
            semantics="stable",
        )
        assert isinstance(result, list)

    def test_supersedes_eliminates_old(self, supersedes_scenario):
        """Superseded claim is not in grounded extension."""
        result = compute_claim_graph_justified_claims(
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
        result = compute_claim_graph_justified_claims(SQLiteArgumentationStore(conn), {"c1", "c2"}, semantics="grounded")
        assert result == frozenset({"c1", "c2"})


# ── Property tests ──────────────────────────────────────────────────


_PROP_SETTINGS = settings(deadline=None)


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
            if t in ("supports", "explains"):
                support_only_pairs.add((a, b))
        for a, b, t, conf in stances:
            if t not in ("supports", "explains"):
                support_only_pairs.discard((a, b))
        # Pairs that ONLY have support/explains stances should not be attacks.
        # They may still show up in defeats through support-aware derivation.
        for pair in support_only_pairs:
            assert pair not in af.attacks

    @given(stance_scenarios())
    @_PROP_SETTINGS
    def test_grounded_is_conflict_free(self, scenario):
        """P3: Grounded computation is conflict-free with respect to defeats."""
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
        """Grounded survivors stay inside the provided active set."""
        claim_ids, stances, sample_sizes = scenario
        conn = _build_scenario_db(claim_ids, stances, sample_sizes)
        result = compute_claim_graph_justified_claims(
            SQLiteArgumentationStore(conn),
            set(claim_ids),
            semantics="grounded",
        )
        assert result <= frozenset(claim_ids)


# ── Helpers for conflict tests ───────────────────────────────────────


def _insert_conflict(
    conn: sqlite3.Connection,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    warning_class: str,
    *,
    value_a: str | None = None,
    value_b: str | None = None,
) -> None:
    insert_conflict(
        conn,
        concept_id=concept_id,
        claim_a_id=claim_a_id,
        claim_b_id=claim_b_id,
        warning_class=warning_class,
        value_a=value_a,
        value_b=value_b,
    )


# ── Tests: conflict-derived defeats ─────────────────────────────────


class TestConflictDerivedDefeats:
    """Tests for wiring conflicts into the argumentation framework.

    The gap: _collect_claim_graph_relations() only reads stances from
    store.stances_between(). It never reads conflicts from store.conflicts().
    Two claims that disagree on value but have no LLM-classified stance
    produce zero defeats in the AF. These tests encode the correct behavior
    that should hold after the green-phase fix.

    References:
    - Dung 1995, Def 6 (p.326): conflict-free sets
    - Dung 1995, Def 8: admissibility requires defending against all attacks
    - Josang 2001, p.8: vacuous opinions for honest ignorance
    """

    def test_conflict_generates_defeats_without_stance(self, conn):
        """A CONFLICT row between two claims (no stance) should produce defeats.

        Two claims for the same concept with different values and a CONFLICT
        record but no LLM-classified stance. The AF should contain mutual
        defeats (symmetric rebuts) because a genuine value conflict exists.
        Currently fails: _collect_claim_graph_relations ignores conflicts.
        """
        _insert_claim(conn, "alpha", "c1", 100.0, sample_size=50)
        _insert_claim(conn, "beta", "c1", 200.0, sample_size=50)
        _insert_conflict(conn, "c1", "alpha", "beta", "CONFLICT",
                         value_a="100.0", value_b="200.0")
        conn.commit()

        af = build_argumentation_framework(
            SQLiteArgumentationStore(conn), {"alpha", "beta"}
        )
        # A genuine conflict should produce at least one defeat direction
        has_defeat = (
            ("alpha", "beta") in af.defeats
            or ("beta", "alpha") in af.defeats
        )
        assert has_defeat, (
            "CONFLICT record between alpha and beta should generate defeats, "
            f"but af.defeats = {af.defeats}"
        )

    def test_phi_node_does_not_generate_defeats(self, conn):
        """PHI_NODE means disjoint conditions — no actual conflict, no defeats.

        PHI_NODE indicates the two claims operate under mutually exclusive
        conditions and can never co-occur. No defeat should be generated.
        """
        _insert_claim(conn, "phi_a", "c1", 100.0, sample_size=50)
        _insert_claim(conn, "phi_b", "c1", 200.0, sample_size=50)
        _insert_conflict(conn, "c1", "phi_a", "phi_b", "PHI_NODE",
                         value_a="100.0", value_b="200.0")
        conn.commit()

        af = build_argumentation_framework(
            SQLiteArgumentationStore(conn), {"phi_a", "phi_b"}
        )
        assert ("phi_a", "phi_b") not in af.defeats
        assert ("phi_b", "phi_a") not in af.defeats

    def test_real_stance_takes_precedence_over_conflict(self, conn):
        """When both a stance and a CONFLICT exist, the stance semantics win.

        If an LLM-classified stance says 'supports', a synthetic rebuts from
        the CONFLICT record should not override it. The real stance's
        classification takes precedence.
        """
        _insert_claim(conn, "prec_a", "c1", 100.0, sample_size=100)
        _insert_claim(conn, "prec_b", "c1", 200.0, sample_size=100)
        _insert_stance(conn, "prec_a", "prec_b", "supports")
        _insert_conflict(conn, "c1", "prec_a", "prec_b", "CONFLICT",
                         value_a="100.0", value_b="200.0")
        conn.commit()

        af = build_argumentation_framework(
            SQLiteArgumentationStore(conn), {"prec_a", "prec_b"}
        )
        # The real stance is "supports", so no defeat from prec_a → prec_b
        assert ("prec_a", "prec_b") not in af.defeats
        # The conflict should still produce a defeat in the reverse direction
        # (prec_b → prec_a), since the "supports" stance only covers a→b
        assert ("prec_b", "prec_a") in af.defeats, (
            "CONFLICT should still produce defeat prec_b→prec_a even when "
            f"a real 'supports' stance covers a→b, but af.defeats = {af.defeats}"
        )

    def test_conflict_synthetic_stances_have_vacuous_opinions(self, conn):
        """Synthetic stances from conflicts must carry vacuous opinions.

        Per Josang 2001 (p.8): when the system lacks evidence for the
        direction/strength of a relation, it must express total ignorance
        via opinion_uncertainty >= 0.99 rather than fabricating confidence.
        """
        _insert_claim(conn, "vac_a", "c1", 100.0, sample_size=50)
        _insert_claim(conn, "vac_b", "c1", 200.0, sample_size=50)
        _insert_conflict(conn, "c1", "vac_a", "vac_b", "CONFLICT",
                         value_a="100.0", value_b="200.0")
        conn.commit()

        store = SQLiteArgumentationStore(conn)
        praf = build_praf(store, {"vac_a", "vac_b"})

        # First, defeats must exist (prerequisite)
        has_defeat = (
            ("vac_a", "vac_b") in praf.framework.defeats
            or ("vac_b", "vac_a") in praf.framework.defeats
        )
        assert has_defeat, (
            "CONFLICT should generate defeats before we can inspect opinions"
        )

        # The PrAF attack relations for conflict-derived defeats should
        # carry vacuous opinions (uncertainty >= 0.99)
        conflict_pairs = {("vac_a", "vac_b"), ("vac_b", "vac_a")}
        for rel in praf.attack_relations:
            if (rel.source, rel.target) in conflict_pairs:
                assert rel.opinion.uncertainty >= 0.99, (
                    f"Conflict-derived relation {rel.source}→{rel.target} "
                    f"has opinion uncertainty {rel.opinion.uncertainty}, "
                    f"expected >= 0.99 (vacuous per Josang 2001)"
                )

    def test_overlap_conflict_generates_defeats(self, conn):
        """OVERLAP is a real value conflict — should generate defeats.

        OVERLAP means overlapping conditions with different values. Like
        CONFLICT, this represents a genuine disagreement that should
        produce defeats in the AF.
        """
        _insert_claim(conn, "ov_a", "c1", 100.0, sample_size=50)
        _insert_claim(conn, "ov_b", "c1", 200.0, sample_size=50)
        _insert_conflict(conn, "c1", "ov_a", "ov_b", "OVERLAP",
                         value_a="100.0", value_b="200.0")
        conn.commit()

        af = build_argumentation_framework(
            SQLiteArgumentationStore(conn), {"ov_a", "ov_b"}
        )
        has_defeat = (
            ("ov_a", "ov_b") in af.defeats
            or ("ov_b", "ov_a") in af.defeats
        )
        assert has_defeat, (
            "OVERLAP conflict between ov_a and ov_b should generate defeats, "
            f"but af.defeats = {af.defeats}"
        )
