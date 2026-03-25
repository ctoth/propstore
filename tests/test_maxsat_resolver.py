"""Tests for MaxSMT-based conflict resolution.

Verifies that z3.Optimize with soft constraints produces maximally
consistent claim subsets weighted by claim_strength.
"""
import pytest
import z3
from propstore.maxsat_resolver import resolve_conflicts


class TestMaxSATBasic:
    def test_two_conflicting_stronger_wins(self):
        """Two conflicting claims, stronger one should be kept."""
        conflicts = [("c1", "c2")]  # c1 conflicts with c2
        strengths = {"c1": 5.0, "c2": 2.0}
        result = resolve_conflicts(conflicts, strengths)
        assert "c1" in result
        assert "c2" not in result

    def test_two_conflicting_weaker_loses(self):
        """Symmetric check — weaker claim is excluded."""
        conflicts = [("c1", "c2")]
        strengths = {"c1": 1.0, "c2": 10.0}
        result = resolve_conflicts(conflicts, strengths)
        assert "c2" in result
        assert "c1" not in result

    def test_three_claims_chain_conflict(self):
        """A-B conflict, B-C conflict, A-C compatible → keeps A+C."""
        conflicts = [("c1", "c2"), ("c2", "c3")]
        strengths = {"c1": 3.0, "c2": 5.0, "c3": 3.0}
        result = resolve_conflicts(conflicts, strengths)
        # Can keep c1+c3 (weight 6) or just c2 (weight 5)
        # MaxSMT should pick c1+c3
        assert result == frozenset({"c1", "c3"})

    def test_no_conflicts_keeps_all(self):
        """No conflicts → all claims kept."""
        conflicts = []
        strengths = {"c1": 1.0, "c2": 2.0, "c3": 3.0}
        result = resolve_conflicts(conflicts, strengths)
        assert result == frozenset({"c1", "c2", "c3"})

    def test_equal_weight_conflict_free(self):
        """Equal weight conflict — either solution valid, must be conflict-free."""
        conflicts = [("c1", "c2")]
        strengths = {"c1": 1.0, "c2": 1.0}
        result = resolve_conflicts(conflicts, strengths)
        # Either {c1} or {c2} is valid
        assert len(result) == 1
        assert result.issubset({"c1", "c2"})

    def test_tiebreak_at_small_difference(self):
        """Claims differing by 0.0001 in strength — tiebreak resolves correctly."""
        conflicts = [("c1", "c2")]
        strengths = {"c1": 1.0001, "c2": 1.0}
        result = resolve_conflicts(conflicts, strengths)
        assert "c1" in result
        assert "c2" not in result

    def test_empty_claims(self):
        """No claims → empty result."""
        result = resolve_conflicts([], {})
        assert result == frozenset()

    def test_single_claim_no_conflict(self):
        """Single claim with no conflicts → kept."""
        result = resolve_conflicts([], {"c1": 1.0})
        assert result == frozenset({"c1"})

    def test_triangle_conflict(self):
        """Three mutual conflicts — keep the strongest."""
        conflicts = [("c1", "c2"), ("c2", "c3"), ("c1", "c3")]
        strengths = {"c1": 1.0, "c2": 2.0, "c3": 3.0}
        result = resolve_conflicts(conflicts, strengths)
        assert "c3" in result
        assert len(result) == 1


class TestMaxSATConflictFree:
    """Property: result must always be conflict-free."""

    def test_result_is_conflict_free(self):
        """For any conflict graph, the result has no conflicting pairs."""
        conflicts = [("c1", "c2"), ("c2", "c3"), ("c3", "c4"), ("c1", "c4")]
        strengths = {"c1": 1.0, "c2": 2.0, "c3": 3.0, "c4": 4.0}
        result = resolve_conflicts(conflicts, strengths)
        # Verify no pair in result is in conflicts
        for a, b in conflicts:
            assert not (a in result and b in result), f"Conflict pair ({a}, {b}) both in result"

    def test_result_nonempty_when_claims_exist(self):
        """At least one claim is always kept if claims exist."""
        conflicts = [("c1", "c2")]
        strengths = {"c1": 1.0, "c2": 1.0}
        result = resolve_conflicts(conflicts, strengths)
        assert len(result) >= 1


class TestMaxSATBoolRefSafety:
    """Verify MaxSAT resolver uses z3.is_true() instead of Python truthiness.

    Finding C3 (audit-z3-cel-conflict.md): model.evaluate() returns z3.BoolRef,
    not Python bool. Using BoolRef in a Python boolean context is
    version-dependent: some z3 versions raise Z3Exception, others always return
    True regardless of the logical value. The safe pattern is z3.is_true().

    The current code at maxsat_resolver.py:45 uses:
        if model.evaluate(var, model_completion=True)
    instead of:
        if z3.is_true(model.evaluate(var, model_completion=True))

    This test inspects the source code to verify z3.is_true() is used.
    """

    def test_resolver_uses_is_true_not_bool_context(self):
        """The resolver must use z3.is_true() to check model evaluation results.

        Inspects the source code of resolve_conflicts to verify it does not
        use model.evaluate() in a bare boolean context. The safe pattern is
        z3.is_true(model.evaluate(...)). Using `if model.evaluate(...)` is
        fragile because BoolRef.__bool__ behavior is z3-version-dependent.
        """
        import inspect
        import textwrap

        source = inspect.getsource(resolve_conflicts)

        # The code must use z3.is_true() to check model evaluation results
        assert "is_true" in source, (
            "resolve_conflicts uses model.evaluate() in a boolean context "
            "without z3.is_true(). This is version-dependent and fragile. "
            "Replace `if model.evaluate(var, model_completion=True)` with "
            "`if z3.is_true(model.evaluate(var, model_completion=True))`"
        )

    def test_excluded_claim_not_in_result(self):
        """MaxSAT with conflicting soft constraints must exclude the weaker claim.

        Sets up 3 claims where c1 conflicts with both c2 and c3.
        c2+c3 together (weight 6) beat c1 alone (weight 5), so c1 must be
        excluded — model.evaluate(keep_c1) should be z3.BoolVal(False).
        """
        conflicts = [("c1", "c2"), ("c1", "c3")]
        strengths = {"c1": 5.0, "c2": 3.0, "c3": 3.0}
        result = resolve_conflicts(conflicts, strengths)
        # c2+c3 (weight 6) beats c1 (weight 5)
        assert "c1" not in result, (
            "c1 should be excluded but was kept — "
            "model.evaluate() BoolRef used in boolean context without z3.is_true()"
        )
        assert result == frozenset({"c2", "c3"})
