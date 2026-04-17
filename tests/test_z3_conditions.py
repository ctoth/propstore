"""Tests for Z3-based condition reasoning."""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts as _detect_conflicts,
)
from propstore.conflict_detector.collectors import conflict_claim_from_payload
from propstore.conflict_detector.models import ConflictClaim
from tests.conftest import make_cel_registry, make_concept_registry


# ── Helpers ──────────────────────────────────────────────────────────


def make_parameter_claim(id, concept_id, value, unit="Hz", conditions=None):
    return {
        "id": id,
        "type": "parameter",
        "concept": concept_id,
        "value": value if isinstance(value, list) else [value],
        "unit": unit,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }


def make_claim_file(claims, filename="test_paper"):
    records = []
    for claim_payload in claims:
        claim = conflict_claim_from_payload(claim_payload, source_paper=filename)
        assert claim is not None
        records.append(claim)
    return records


def flatten_claims(claims_or_files):
    flattened = []
    for item in claims_or_files:
        if isinstance(item, ConflictClaim):
            flattened.append(item)
        else:
            flattened.extend(item)
    return flattened


def detect_conflicts(claim_files, registry, lifting_system=None):
    return _detect_conflicts(
        flatten_claims(claim_files),
        registry,
        make_cel_registry(registry),
        lifting_system=lifting_system,
    )


# ── Strict Z3 requirements ──────────────────────────────────────────


class TestStrictZ3Requirements:
    """Condition classification should require the canonical Z3 path."""

    def test_classify_conditions_requires_registry(self):
        with pytest.raises(ValueError, match="requires a CEL registry"):
            _classify_conditions(
                ["F1/F0 > 3.0"],
                ["F1/F0 > 2.0"],
            )

    def test_open_category_undeclared_literals_do_not_raise(self):
        from propstore.z3_conditions import Z3ConditionSolver

        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        result = _classify_conditions(
            ["task == 'dancing'"],
            ["task == 'speech'"],
            registry,
            solver=solver,
        )
        assert result == ConflictClass.PHI_NODE


# ── Z3 module tests ──────────────────────────────────────────────────

from typing import TYPE_CHECKING

from propstore.cel_checker import ConceptInfo, KindType

try:
    import z3 as _z3  # noqa: F401
    from propstore.z3_conditions import Z3ConditionSolver as Z3ConditionSolver
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver as Z3ConditionSolver

z3_only = pytest.mark.skipif(not HAS_Z3, reason="z3-solver not installed")


def _make_cel_registry():
    """Build a ConceptInfo registry for Z3 tests."""
    return {
        "fundamental_frequency": ConceptInfo(
            id="concept1",
            canonical_name="fundamental_frequency",
            kind=KindType.QUANTITY,
        ),
        "subglottal_pressure": ConceptInfo(
            id="concept2",
            canonical_name="subglottal_pressure",
            kind=KindType.QUANTITY,
        ),
        "task": ConceptInfo(
            id="concept3",
            canonical_name="task",
            kind=KindType.CATEGORY,
            category_values=["speech", "singing", "whisper"],
            category_extensible=True,
        ),
        "voiced": ConceptInfo(
            id="concept4",
            canonical_name="voiced",
            kind=KindType.BOOLEAN,
        ),
    }


@z3_only
class TestZ3Disjointness:
    """Test that Z3 correctly determines disjointness of condition sets."""

    def test_simple_numeric_disjoint(self):
        """F0 < 100 vs F0 > 200 are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency < 100"],
            ["fundamental_frequency > 200"],
        )

    def test_simple_numeric_overlapping(self):
        """F0 > 100 vs F0 > 200 overlap (everything > 200 satisfies both)."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
        )

    def test_category_disjoint(self):
        """task == 'speech' vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'"],
            ["task == 'singing'"],
        )

    def test_category_same_value_not_disjoint(self):
        """task == 'speech' vs task == 'speech' are not disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task == 'speech'"],
            ["task == 'speech'"],
        )

    def test_open_category_undeclared_literal_is_not_disjoint_from_matching_equality(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task != 'speech'"],
            ["task == 'dancing'"],
        )

    @given(
        left=st.text(
            min_size=1,
            max_size=12,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        right=st.text(
            min_size=1,
            max_size=12,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
    )
    @settings(deadline=None)
    def test_distinct_open_category_literals_are_disjoint(self, left, right):
        assume(left not in {"speech", "singing", "whisper"})
        assume(right not in {"speech", "singing", "whisper"})
        assume(left != right)

        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)

        assert solver.are_disjoint(
            [f"task == '{left}'"],
            [f"task == '{right}'"],
        )

    def test_boolean_disjoint(self):
        """voiced == true vs voiced == false are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["voiced == true"],
            ["voiced == false"],
        )

    def test_boolean_same_not_disjoint(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["voiced == true"],
            ["voiced == true"],
        )

    def test_mixed_concepts_disjoint(self):
        """Different category values make them disjoint even with same numeric."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'", "fundamental_frequency > 100"],
            ["task == 'singing'", "fundamental_frequency > 100"],
        )


@z3_only
class TestZ3CompoundConditions:
    """Test &&, ||, and combinations."""

    def test_and_conditions_disjoint(self):
        """(F0 > 100 && F0 < 150) vs (F0 > 200 && F0 < 250) are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency > 100 && fundamental_frequency < 150"],
            ["fundamental_frequency > 200 && fundamental_frequency < 250"],
        )

    def test_and_conditions_overlapping(self):
        """(F0 > 100 && F0 < 250) vs (F0 > 200 && F0 < 350) overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency > 100 && fundamental_frequency < 250"],
            ["fundamental_frequency > 200 && fundamental_frequency < 350"],
        )

    def test_or_condition(self):
        """(task == 'speech' || task == 'whisper') vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech' || task == 'whisper'"],
            ["task == 'singing'"],
        )

    def test_or_condition_overlapping(self):
        """(task == 'speech' || task == 'singing') vs task == 'singing' overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task == 'speech' || task == 'singing'"],
            ["task == 'singing'"],
        )


@z3_only
class TestZ3InOperator:
    """Test the 'in' operator translation."""

    def test_in_list_disjoint(self):
        """task in ['speech', 'whisper'] vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task in ['speech', 'whisper']"],
            ["task == 'singing'"],
        )

    def test_in_list_overlapping(self):
        """task in ['speech', 'singing'] vs task == 'singing' overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task in ['speech', 'singing']"],
            ["task == 'singing'"],
        )

    def test_open_category_in_list_accepts_undeclared_literal(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task in ['speech', 'dancing']"],
            ["task == 'dancing'"],
        )


@z3_only
class TestZ3CrossConceptArithmetic:
    """Test arithmetic expressions across concepts (e.g. F0 / Ps > 2.0)."""

    def test_ratio_disjoint(self):
        """F0 / Ps > 3.0 vs F0 / Ps < 1.0 are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency / subglottal_pressure > 3.0"],
            ["fundamental_frequency / subglottal_pressure < 1.0"],
        )

    def test_ratio_overlapping(self):
        """F0 / Ps > 2.0 vs F0 / Ps > 3.0 overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency / subglottal_pressure > 2.0"],
            ["fundamental_frequency / subglottal_pressure > 3.0"],
        )

    def test_division_by_zero_unsoundness(self):
        """Division by zero makes Z3 unsound: x/0 is an uninterpreted total
        function in Z3, so F0/Ps > 3 and F0/Ps < 1 are satisfiable when Ps=0
        (Z3 picks an arbitrary value for x/0). The solver must guard against
        this by constraining denominators to be non-zero."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        # Without fix: Z3 says disjoint (wrong — Ps=0 satisfies both via
        # uninterpreted x/0). With fix: denominator != 0 guard makes these
        # genuinely disjoint (no unsound x/0 path).
        # We test the property that matters: the solver adds the guard.
        # Verify by checking a case where the guard changes the answer:
        # "F0 / Ps > 0" vs "F0 / Ps < 0" — without guard, disjoint;
        # but we also need Ps != 0 to be asserted.
        # Actually test with a direct Z3 probe:
        import z3 as _z3
        ctx = solver._ctx
        f0 = solver._get_real("fundamental_frequency")
        ps = solver._get_real("subglottal_pressure")
        # Translate a condition with division — should add non-zero guard
        expr = solver._condition_to_z3(
            "fundamental_frequency / subglottal_pressure > 3.0"
        )
        # The translated expression, when added to a solver, should make
        # ps == 0 unsatisfiable (because of the non-zero guard)
        s = _z3.Solver(ctx=ctx)
        s.add(expr)
        s.add(ps == _z3.RealVal(0, ctx))
        assert s.check() == _z3.unsat, (
            "Division expression should be UNSAT when denominator is 0 "
            "(non-zero guard missing)"
        )


@z3_only
class TestZ3Negation:
    """Test negation (!) translation."""

    def test_negation_disjoint(self):
        """voiced == true vs !(voiced == true) are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["voiced == true"],
            ["!(voiced == true)"],
        )

    def test_negation_of_category(self):
        """task == 'speech' vs !(task == 'speech') are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'"],
            ["!(task == 'speech')"],
        )


@z3_only
class TestZ3Equivalence:
    """Test equivalence detection (both A∧¬B and B∧¬A are UNSAT)."""

    def test_identical_conditions_equivalent(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 100"],
        )

    def test_different_conditions_not_equivalent(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_equivalent(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
        )

    def test_reordered_conditions_equivalent(self):
        """Order shouldn't matter — conditions are conjuncted."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["fundamental_frequency > 100", "task == 'speech'"],
            ["task == 'speech'", "fundamental_frequency > 100"],
        )

    def test_logically_equivalent_different_form(self):
        """!(F0 <= 100) is equivalent to F0 > 100."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["!(fundamental_frequency <= 100)"],
            ["fundamental_frequency > 100"],
        )

    def test_open_category_inequality_is_not_closed_domain_equivalent(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_equivalent(
            ["task != 'speech'"],
            ["task in ['singing', 'whisper']"],
        )


@z3_only
class TestUnknownNames:
    def test_unknown_concept_name_is_hard_error(self):
        from propstore.z3_conditions import Z3TranslationError

        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)

        with pytest.raises(Z3TranslationError, match="Undefined concept|Unknown concept"):
            solver.are_disjoint(
                ["missing > 0"],
                ["fundamental_frequency > 100"],
            )


@z3_only
class TestZ3IntegrationWithConflictDetector:
    """Test that Z3 is wired into _classify_conditions properly."""

    def test_z3_detects_numeric_overlap(self):
        """Two claims with F0>100 and F0>200 should be OVERLAP, not PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["fundamental_frequency > 100"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 200"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_z3_detects_category_phi_node(self):
        """task == 'speech' vs task == 'singing' -> PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'singing'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_z3_detects_compound_overlap(self):
        """Compound conditions with partial overlap."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["fundamental_frequency > 100 && fundamental_frequency < 300"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 200 && fundamental_frequency < 400"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_z3_detects_equivalent_as_conflict(self):
        """Logically equivalent conditions -> CONFLICT."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["!(fundamental_frequency <= 100)"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 100"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT


@z3_only
class TestBatchEquivalenceClasses:
    """Tests for batch equivalence class partitioning."""

    def _make_solver(self):
        return Z3ConditionSolver(_make_cel_registry())

    def test_single_condition_one_class(self):
        """One condition set -> one class containing just index 0."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes(
            [["fundamental_frequency > 100"]]
        )
        assert result == [[0]]

    def test_identical_conditions_one_class(self):
        """Three identical condition sets -> one class with indices [0, 1, 2]."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes([
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 100"],
        ])
        assert result == [[0, 1, 2]]

    def test_all_different_conditions(self):
        """Three distinct conditions -> three classes, one index each."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes([
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
            ["fundamental_frequency > 300"],
        ])
        assert result == [[0], [1], [2]]

    def test_mixed_equivalent_and_different(self):
        """Some equivalent, some not -> correct partition."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes([
            ["fundamental_frequency > 100"],                   # A
            ["fundamental_frequency > 200"],                   # B
            ["fundamental_frequency > 100"],                   # A' (same as A)
            ["task == 'speech'"],                               # C
        ])
        assert result == [[0, 2], [1], [3]]

    def test_logically_equivalent_different_form(self):
        """Conditions that are syntactically different but logically equivalent
        (e.g. '!(F0 <= 100)' vs 'F0 > 100') end up in same class."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes([
            ["!(fundamental_frequency <= 100)"],
            ["fundamental_frequency > 100"],
        ])
        assert result == [[0, 1]]

    def test_empty_input_empty_output(self):
        """No condition sets -> empty partition."""
        solver = self._make_solver()
        result = solver.partition_equivalence_classes([])
        assert result == []

    def test_matches_pairwise(self):
        """Verify batch partition matches exhaustive pairwise are_equivalent() results."""
        solver = self._make_solver()
        condition_sets = [
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
            ["!(fundamental_frequency <= 100)"],   # equiv to index 0
            ["task == 'speech'"],
            ["task == 'speech'"],                   # equiv to index 3
            ["fundamental_frequency > 200"],        # equiv to index 1
        ]
        partition = solver.partition_equivalence_classes(condition_sets)

        # Build set of equivalent pairs from partition
        equiv_pairs = set()
        for group in partition:
            for ii in range(len(group)):
                for jj in range(ii + 1, len(group)):
                    equiv_pairs.add((group[ii], group[jj]))

        # Build set of equivalent pairs from pairwise comparison
        pairwise_pairs = set()
        for ii in range(len(condition_sets)):
            for jj in range(ii + 1, len(condition_sets)):
                if solver.are_equivalent(condition_sets[ii], condition_sets[jj]):
                    pairwise_pairs.add((ii, jj))

        assert equiv_pairs == pairwise_pairs


@z3_only
class TestZ3Caching:
    """Cache checked and translated condition expressions across repeated queries."""

    def test_reuses_checked_conditions_across_repeated_disjoint_queries(self, monkeypatch):
        import propstore.z3_conditions as z3_conditions_module

        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        real_check = z3_conditions_module.check_cel_expr
        check_calls: list[str] = []

        def counting_check(expr, registry):
            check_calls.append(str(expr))
            return real_check(expr, registry)

        monkeypatch.setattr(z3_conditions_module, "check_cel_expr", counting_check)

        left = ["fundamental_frequency > 100", "task == 'speech'"]
        right = ["task == 'singing'"]

        assert solver.are_disjoint(left, right)
        assert solver.are_disjoint(list(reversed(left)), right)

        assert check_calls == [
            "fundamental_frequency > 100",
            "task == 'speech'",
            "task == 'singing'",
        ]

    def test_reuses_translated_condition_sets_across_repeated_queries(self, monkeypatch):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        real_translate = solver._translate
        translate_calls = 0

        def counting_translate(node):
            nonlocal translate_calls
            translate_calls += 1
            return real_translate(node)

        monkeypatch.setattr(solver, "_translate", counting_translate)

        left = ["fundamental_frequency > 100 && fundamental_frequency < 300"]
        right = ["fundamental_frequency > 200 && fundamental_frequency < 400"]

        assert not solver.are_disjoint(left, right)
        first_call_count = translate_calls

        assert not solver.are_disjoint(left, right)

        assert first_call_count > 0
        assert translate_calls == first_call_count

    def test_classify_conditions_can_reuse_supplied_solver(self, monkeypatch):
        import propstore.z3_conditions as z3_conditions_module

        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        real_check = z3_conditions_module.check_cel_expr
        check_calls: list[str] = []

        def counting_check(expr, registry):
            check_calls.append(str(expr))
            return real_check(expr, registry)

        monkeypatch.setattr(z3_conditions_module, "check_cel_expr", counting_check)

        left = ["fundamental_frequency > 100", "task == 'speech'"]
        right = ["fundamental_frequency > 200", "task == 'speech'"]

        assert _classify_conditions(left, right, registry, solver=solver) == ConflictClass.OVERLAP
        assert _classify_conditions(list(reversed(left)), right, registry, solver=solver) == ConflictClass.OVERLAP

        assert check_calls == [
            "fundamental_frequency > 100",
            "task == 'speech'",
            "fundamental_frequency > 200",
        ]


# ── Partition exception-handling tests (Group 2) ────────────────────


class TestPartitionExceptionHandling:
    def test_translation_error_propagates(self):
        """Z3TranslationError in are_equivalent should propagate."""
        from unittest.mock import patch
        from propstore.cel_checker import ConceptInfo, KindType
        from propstore.z3_conditions import Z3TranslationError, Z3ConditionSolver

        registry = {"freq": ConceptInfo(id="freq", canonical_name="freq", kind=KindType.QUANTITY)}
        solver = Z3ConditionSolver(registry)

        call_count = 0
        original_are_equivalent = solver.are_equivalent

        def flaky_are_equivalent(a, b):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Z3TranslationError("translation failed")
            return original_are_equivalent(a, b)

        condition_sets = [
            ["freq > 100"],
            ["freq > 200"],  # This comparison will raise on first call
            ["freq > 100"],  # This should match the first
        ]

        with patch.object(solver, "are_equivalent", side_effect=flaky_are_equivalent):
            with pytest.raises(Z3TranslationError, match="translation failed"):
                solver.partition_equivalence_classes(condition_sets)

    def test_unexpected_error_propagates(self):
        """RuntimeError in are_equivalent should propagate."""
        from unittest.mock import patch
        from propstore.cel_checker import ConceptInfo, KindType
        from propstore.z3_conditions import Z3ConditionSolver

        registry = {"freq": ConceptInfo(id="freq", canonical_name="freq", kind=KindType.QUANTITY)}
        solver = Z3ConditionSolver(registry)

        condition_sets = [
            ["freq > 100"],
            ["freq > 200"],
        ]

        with patch.object(
            solver, "are_equivalent", side_effect=RuntimeError("unexpected")
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                solver.partition_equivalence_classes(condition_sets)


# ── Guard state leak tests (F9) ─────────────────────────────────────


@z3_only
class TestZ3GuardStateLeak:
    """Tests for _current_guards shared mutable state fragility.

    Finding C1/C2 from audit-z3-cel-conflict.md: _current_guards is an
    instance attribute set per-condition in _condition_to_z3(), never
    initialized in __init__. This makes _translate() crash when called
    directly, and means guard state leaks across translations.
    """

    def test_two_division_conditions_get_independent_guards(self):
        """Two conditions dividing by the same variable should each get
        independent guards.  After translating both via _condition_to_z3,
        the _current_guards attribute should be initialized and each
        condition's cached Z3 expression should independently include
        the denominator-non-zero guard.

        This test verifies that _current_guards is properly initialized
        as an instance attribute (not set ad-hoc inside _condition_to_z3).
        It checks hasattr BEFORE any translation — which fails because
        __init__ never creates _current_guards.
        """
        import z3 as _z3

        registry = {
            "a": ConceptInfo(id="a", canonical_name="a", kind=KindType.QUANTITY),
            "y": ConceptInfo(id="y", canonical_name="y", kind=KindType.QUANTITY),
        }
        solver = Z3ConditionSolver(registry)

        # _current_guards should exist as an instance attribute from __init__,
        # so that any method can safely reference it.  Currently it doesn't —
        # it's only created inside _condition_to_z3().
        assert hasattr(solver, "_current_guards"), (
            "_current_guards must be initialized in __init__ so that "
            "_translate can safely reference it without going through "
            "_condition_to_z3 first"
        )

        # Translate two conditions that both divide by y
        expr_a = solver._condition_to_z3("a / y > 0")
        expr_b = solver._condition_to_z3("a / y < 5")

        # Both expressions should make y==0 unsatisfiable (guard present)
        ctx = solver._ctx
        y = solver._get_real("y")
        zero = _z3.RealVal(0, ctx)

        s1 = _z3.Solver(ctx=ctx)
        s1.add(expr_a)
        s1.add(y == zero)
        assert s1.check() == _z3.unsat, "Condition A must guard against y==0"

        s2 = _z3.Solver(ctx=ctx)
        s2.add(expr_b)
        s2.add(y == zero)
        assert s2.check() == _z3.unsat, "Condition B must guard against y==0"

    def test_direct_translate_does_not_crash_on_division_guard(self):
        """Calling _translate() directly (bypassing _condition_to_z3) on an
        AST containing division should not raise AttributeError.

        Currently _current_guards is only set inside _condition_to_z3(),
        so calling _translate() on a division node will crash at line 163
        with: AttributeError: 'Z3ConditionSolver' object has no attribute
        '_current_guards'.
        """
        from propstore.cel_checker import BinaryOpNode, NameNode, LiteralNode

        registry = {
            "a": ConceptInfo(id="a", canonical_name="a", kind=KindType.QUANTITY),
            "y": ConceptInfo(id="y", canonical_name="y", kind=KindType.QUANTITY),
        }
        solver = Z3ConditionSolver(registry)

        # Build AST for "a / y" — a division that triggers guard collection
        div_node = BinaryOpNode(
            op="/",
            left=NameNode(name="a"),
            right=NameNode(name="y"),
        )

        # Wrap in a comparison: "a / y > 0"
        cmp_node = BinaryOpNode(
            op=">",
            left=div_node,
            right=LiteralNode(value=0, lit_type="int"),
        )

        # _translate() called directly (not through _condition_to_z3) should
        # not crash.  Currently it does because _current_guards is not
        # initialized in __init__.
        result = solver._translate(cmp_node)
        assert result is not None
