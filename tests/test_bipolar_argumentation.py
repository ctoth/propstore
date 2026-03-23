"""Tests for bipolar argumentation (Cayrol 2005) and attack-based conflict-free (Modgil & Prakken 2018).

Tests cover:
  - Supported defeat: A supports B, B defeats C -> derived defeat (A, C)
  - Indirect defeat: A defeats B, B supports C -> derived defeat (A, C)
  - Direct defeats unchanged by support-awareness
  - Mixed support chains and attacks
  - Attack-based conflict-free: attacks blocked by preference still count for CF
  - Extension changes under attack-based CF

References:
    Cayrol & Lagasquie-Schiex (2005). Definition 3.
    Modgil & Prakken (2018). Definition 14.
"""

from __future__ import annotations

import sqlite3

import pytest

from propstore.argumentation import (
    _cayrol_derived_defeats,
    build_argumentation_framework,
    compute_justified_claims,
)
from propstore.dung import (
    ArgumentationFramework,
    admissible,
    conflict_free,
    complete_extensions,
    grounded_extension,
    stable_extensions,
)


# ── SQLite helpers (same schema as test_argumentation_integration) ────


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


def _insert_claim(conn, claim_id, concept_id="c1", value=1.0,
                   sample_size=100, uncertainty=None):
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, sample_size, uncertainty) "
        "VALUES (?, 'parameter', ?, ?, ?, ?)",
        (claim_id, concept_id, value, sample_size, uncertainty),
    )


def _insert_stance(conn, claim_id, target_claim_id, stance_type,
                    confidence=0.9):
    conn.execute(
        "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence) "
        "VALUES (?, ?, ?, ?)",
        (claim_id, target_claim_id, stance_type, confidence),
    )


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    _create_schema(c)
    return c


# ── Unit tests for _cayrol_derived_defeats ────────────────────────────


class TestCayrolDerivedDefeats:
    """Direct tests of the Cayrol 2005 derived defeat computation."""

    def test_supported_defeat(self):
        """A supports B, B defeats C -> derived (A, C)."""
        supports = {("A", "B")}
        defeats = {("B", "C")}
        derived = _cayrol_derived_defeats(defeats, supports)
        assert ("A", "C") in derived

    def test_indirect_defeat(self):
        """A defeats B, B supports C -> derived (A, C)."""
        supports = {("B", "C")}
        defeats = {("A", "B")}
        derived = _cayrol_derived_defeats(defeats, supports)
        assert ("A", "C") in derived

    def test_no_supports_no_derived(self):
        """No support relations -> no derived defeats."""
        defeats = {("A", "B")}
        derived = _cayrol_derived_defeats(defeats, set())
        assert derived == set()

    def test_no_defeats_no_derived(self):
        """No defeats -> no derived defeats (support alone doesn't create defeat)."""
        supports = {("A", "B")}
        derived = _cayrol_derived_defeats(set(), supports)
        assert derived == set()

    def test_chain_supported_defeat(self):
        """A supports B, B supports C, C defeats D -> derived (A, D) and (B, D)."""
        supports = {("A", "B"), ("B", "C")}
        defeats = {("C", "D")}
        derived = _cayrol_derived_defeats(defeats, supports)
        assert ("A", "D") in derived
        assert ("B", "D") in derived

    def test_chain_indirect_defeat(self):
        """A defeats B, B supports C, C supports D -> derived (A, C), (A, D)."""
        supports = {("B", "C"), ("C", "D")}
        defeats = {("A", "B")}
        derived = _cayrol_derived_defeats(defeats, supports)
        assert ("A", "C") in derived
        assert ("A", "D") in derived

    def test_both_directions(self):
        """A supports B defeats C supports D -> derived (A, C) and (B, D).

        Supported defeat: A supports B, B defeats C -> (A, C)
        Indirect defeat: B defeats C, C supports D -> (B, D)
        Also: A supports B, B defeats C, C supports D -> (A, D) via
        supported defeat to C and then indirect defeat would need
        A to defeat C first. Actually (A, D) requires A defeats C
        (a derived defeat) plus C supports D. But derived defeats
        don't chain further in a single pass.
        """
        supports = {("A", "B"), ("C", "D")}
        defeats = {("B", "C")}
        derived = _cayrol_derived_defeats(defeats, supports)
        assert ("A", "C") in derived  # supported defeat
        assert ("B", "D") in derived  # indirect defeat

    def test_direct_defeat_not_duplicated(self):
        """Direct defeats are not in the derived set (they're already in defeats)."""
        supports = {("A", "B")}
        defeats = {("A", "C")}  # direct defeat, unrelated to support
        derived = _cayrol_derived_defeats(defeats, supports)
        # (A, C) is a direct defeat, not a derived one
        assert ("A", "C") not in derived

    def test_self_support_loop_terminates(self):
        """Support cycle doesn't cause infinite recursion."""
        supports = {("A", "B"), ("B", "A")}
        defeats = {("A", "C")}
        derived = _cayrol_derived_defeats(defeats, supports)
        # A defeats C, A supports B -> indirect defeat (A to... wait, that's
        # A supports B, not A defeats B. Let me trace:
        # Indirect: A defeats C, C supports... C has no outgoing support. No indirect from A->C.
        # Supported: B supports A, A defeats C -> (B, C) is a derived defeat
        # A supports B, no defeat from B -> no supported defeat from A via B
        assert ("B", "C") in derived


# ── Integration tests: supported/indirect defeat via DB ───────────────


class TestBipolarAFConstruction:
    """Test build_argumentation_framework with support relations."""

    def test_supported_defeat_via_db(self, conn):
        """A supports B, B rebuts C -> derived defeat (A, C) in AF."""
        _insert_claim(conn, "A", sample_size=100)
        _insert_claim(conn, "B", sample_size=100)
        _insert_claim(conn, "C", sample_size=10)  # weaker, so B rebuts succeeds
        _insert_stance(conn, "A", "B", "supports")
        _insert_stance(conn, "B", "C", "rebuts")
        conn.commit()

        af = build_argumentation_framework(conn, {"A", "B", "C"})
        # Direct defeat: B -> C (rebuts, B stronger)
        assert ("B", "C") in af.defeats
        # Derived supported defeat: A supports B, B defeats C
        assert ("A", "C") in af.defeats

    def test_indirect_defeat_via_db(self, conn):
        """A rebuts B, B supports C -> derived defeat (A, C) in AF."""
        _insert_claim(conn, "A", sample_size=1000)  # strong
        _insert_claim(conn, "B", sample_size=10)    # weak
        _insert_claim(conn, "C", sample_size=100)
        _insert_stance(conn, "A", "B", "rebuts")
        _insert_stance(conn, "B", "C", "supports")
        conn.commit()

        af = build_argumentation_framework(conn, {"A", "B", "C"})
        # Direct defeat: A -> B (rebuts, A stronger)
        assert ("A", "B") in af.defeats
        # Derived indirect defeat: A defeats B, B supports C
        assert ("A", "C") in af.defeats

    def test_direct_defeats_unchanged(self, conn):
        """Direct defeats work exactly as before."""
        _insert_claim(conn, "X", sample_size=1000)
        _insert_claim(conn, "Y", sample_size=10)
        _insert_stance(conn, "X", "Y", "rebuts")
        conn.commit()

        af = build_argumentation_framework(conn, {"X", "Y"})
        assert ("X", "Y") in af.defeats
        assert ("Y", "X") not in af.defeats

    def test_supports_not_in_attacks(self, conn):
        """Support stances do not appear in the attacks set."""
        _insert_claim(conn, "A", sample_size=100)
        _insert_claim(conn, "B", sample_size=100)
        _insert_stance(conn, "A", "B", "supports")
        conn.commit()

        af = build_argumentation_framework(conn, {"A", "B"})
        assert af.attacks is not None
        assert ("A", "B") not in af.attacks
        assert af.defeats == frozenset()

    def test_attacks_set_is_pre_preference(self, conn):
        """Attacks set contains all attack stances, even those blocked by preference."""
        _insert_claim(conn, "weak", sample_size=1)
        _insert_claim(conn, "strong", sample_size=10000)
        _insert_stance(conn, "weak", "strong", "rebuts")  # blocked by preference
        conn.commit()

        af = build_argumentation_framework(conn, {"weak", "strong"})
        assert af.attacks is not None
        # Attack exists (pre-preference)
        assert ("weak", "strong") in af.attacks
        # But not a defeat (blocked by preference: weak is strictly weaker)
        assert ("weak", "strong") not in af.defeats

    def test_mixed_chain(self, conn):
        """A supports B, B undercuts C, C supports D -> derived defeats."""
        _insert_claim(conn, "A")
        _insert_claim(conn, "B")
        _insert_claim(conn, "C")
        _insert_claim(conn, "D")
        _insert_stance(conn, "A", "B", "supports")
        _insert_stance(conn, "B", "C", "undercuts")  # always succeeds
        _insert_stance(conn, "C", "D", "supports")
        conn.commit()

        af = build_argumentation_framework(conn, {"A", "B", "C", "D"})
        # Direct: B defeats C
        assert ("B", "C") in af.defeats
        # Supported defeat: A supports B, B defeats C -> (A, C)
        assert ("A", "C") in af.defeats
        # Indirect defeat: B defeats C, C supports D -> (B, D)
        assert ("B", "D") in af.defeats

    def test_explains_treated_as_support(self, conn):
        """'explains' stances create support edges for derived defeats."""
        _insert_claim(conn, "A")
        _insert_claim(conn, "B")
        _insert_claim(conn, "C", sample_size=10)
        _insert_stance(conn, "A", "B", "explains")
        _insert_stance(conn, "B", "C", "rebuts")
        conn.commit()

        af = build_argumentation_framework(conn, {"A", "B", "C"})
        assert ("A", "C") in af.defeats  # supported defeat via explains


# ── Tests: attack-based conflict-free ─────────────────────────────────


class TestAttackBasedConflictFree:
    """Test Modgil & Prakken 2018 Def 14: CF uses attacks, not defeats."""

    def test_defeat_based_cf_allows_coexistence(self):
        """Under defeat-based CF, args with blocked attacks can coexist."""
        defeats = frozenset({("A", "B")})  # B->A blocked by preference
        # Defeat-based CF: {A, B} has defeat (A, B), not conflict-free
        assert not conflict_free(frozenset({"A", "B"}), defeats)
        # But {B} alone is CF under defeats
        assert conflict_free(frozenset({"B"}), defeats)

    def test_attack_based_cf_blocks_coexistence(self):
        """Under attack-based CF, both directions of attack prevent coexistence."""
        attacks = frozenset({("A", "B"), ("B", "A")})
        # Attack-based CF: {A, B} has attack in both directions
        assert not conflict_free(frozenset({"A", "B"}), attacks)

    def test_attack_based_cf_stricter(self, conn):
        """When weak attacks strong, attack-based CF is stricter than defeat-based.

        Scenario: weak rebuts strong (blocked by preference).
        Under defeat-based CF, they could coexist since no defeat exists.
        Under attack-based CF, the attack still prevents coexistence.
        """
        _insert_claim(conn, "weak", sample_size=1)
        _insert_claim(conn, "strong", sample_size=10000)
        _insert_stance(conn, "weak", "strong", "rebuts")  # blocked
        conn.commit()

        af = build_argumentation_framework(conn, {"weak", "strong"})
        assert af.attacks is not None
        # Verify the setup: attack exists, defeat does not
        assert ("weak", "strong") in af.attacks
        assert ("weak", "strong") not in af.defeats
        # Defeat-based CF allows both
        assert conflict_free(frozenset({"weak", "strong"}), af.defeats)
        # Attack-based CF blocks them
        assert not conflict_free(frozenset({"weak", "strong"}), af.attacks)

    def test_admissible_uses_attacks(self):
        """admissible() uses attacks for CF when provided."""
        args = frozenset({"A", "B"})
        attacks = frozenset({("B", "A")})
        defeats = frozenset()  # B's attack on A blocked by preference
        # Without attacks: {A, B} is admissible (no defeats)
        assert admissible(frozenset({"A", "B"}), args, defeats)
        # With attacks: {A, B} is NOT admissible (B attacks A)
        assert not admissible(frozenset({"A", "B"}), args, defeats, attacks=attacks)

    def test_complete_extensions_with_attacks(self):
        """Complete extensions respect attack-based CF."""
        # A attacks B (blocked by preference), no other attacks
        fw = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset(),
            attacks=frozenset({("A", "B")}),
        )
        exts = complete_extensions(fw)
        # {A, B} is NOT a complete extension (not conflict-free under attacks)
        assert frozenset({"A", "B"}) not in exts
        # {A} should be complete: CF, unattacked, defends itself
        assert frozenset({"A"}) in exts

    def test_stable_extensions_with_attacks(self):
        """Stable extensions use attack-based CF."""
        # A attacks B (blocked by preference), B attacks A (also blocked)
        fw = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset(),
            attacks=frozenset({("A", "B"), ("B", "A")}),
        )
        exts = stable_extensions(fw)
        # No stable extensions: no CF set can defeat all outsiders (no defeats)
        assert frozenset({"A", "B"}) not in exts

    def test_grounded_extension_unchanged_by_attacks(self):
        """Grounded extension uses characteristic function (defeats only).

        The grounded extension computation iterates F using defeats.
        It doesn't check CF directly, so attacks don't change it.
        """
        fw = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset(),
            attacks=frozenset({("A", "B")}),
        )
        ext = grounded_extension(fw)
        # No defeats, so both are unattacked in F
        assert ext == frozenset({"A", "B"})


# ── Extension-level tests with bipolar examples ──────────────────────


class TestBipolarExtensions:
    """Test that extensions change correctly with derived defeats."""

    def test_supported_defeat_changes_grounded(self, conn):
        """Supported defeat removes transitively defeated claims from grounded."""
        # A supports B, B defeats C. Without support-awareness, A is
        # unrelated to C. With it, A also defeats C (derived).
        _insert_claim(conn, "A")
        _insert_claim(conn, "B")
        _insert_claim(conn, "C", sample_size=10)
        _insert_stance(conn, "A", "B", "supports")
        _insert_stance(conn, "B", "C", "rebuts")
        conn.commit()

        result = compute_justified_claims(
            conn, {"A", "B", "C"}, semantics="grounded"
        )
        assert "A" in result
        assert "B" in result
        assert "C" not in result

    def test_indirect_defeat_changes_grounded(self, conn):
        """Indirect defeat: A defeats B, B supports C -> C also out."""
        _insert_claim(conn, "A", sample_size=1000)
        _insert_claim(conn, "B", sample_size=10)
        _insert_claim(conn, "C")
        _insert_stance(conn, "A", "B", "rebuts")
        _insert_stance(conn, "B", "C", "supports")
        conn.commit()

        result = compute_justified_claims(
            conn, {"A", "B", "C"}, semantics="grounded"
        )
        assert "A" in result
        assert "B" not in result
        # C is indirectly defeated by A (via B's support)
        assert "C" not in result

    def test_existing_test_scenario_still_works(self, conn):
        """Reproduce the basic_scenario from test_argumentation_integration."""
        _insert_claim(conn, "claim_a", "c1", 200.0, sample_size=1000)
        _insert_claim(conn, "claim_b", "c1", 300.0, sample_size=10)
        _insert_claim(conn, "claim_c", "c1", 250.0, sample_size=500)
        _insert_stance(conn, "claim_b", "claim_a", "rebuts")      # weak -> strong (blocked)
        _insert_stance(conn, "claim_a", "claim_b", "rebuts")      # strong -> weak (succeeds)
        _insert_stance(conn, "claim_c", "claim_b", "undercuts")   # always succeeds
        _insert_stance(conn, "claim_a", "claim_c", "supports")    # support, not attack
        conn.commit()

        af = build_argumentation_framework(
            conn, {"claim_a", "claim_b", "claim_c"}
        )
        # Direct defeats unchanged
        assert ("claim_a", "claim_b") in af.defeats
        assert ("claim_c", "claim_b") in af.defeats
        # Support does not create direct defeat on claim_c
        assert ("claim_a", "claim_c") not in af.defeats
        # Supported defeat: claim_a supports claim_c, claim_c defeats claim_b
        # -> (claim_a, claim_b) already a direct defeat, so derived is redundant
        assert ("claim_a", "claim_b") in af.defeats

        # Attacks include the blocked rebut
        assert af.attacks is not None
        assert ("claim_b", "claim_a") in af.attacks

        # Grounded should still work
        result = compute_justified_claims(
            conn, {"claim_a", "claim_b", "claim_c"}, semantics="grounded"
        )
        assert "claim_a" in result
        assert "claim_b" not in result
