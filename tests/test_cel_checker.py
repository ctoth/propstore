"""Tests for the CEL condition expression type-checker.

Each test specifies the registry (concept name → kind) and the expected
errors/warnings. Tests are organized by the type rule from the compiler
contract they exercise.
"""

import importlib

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from cel_parser import (
    OP_AND,
    OP_GT,
    OP_MUL,
    OP_NEG,
    OP_NOT,
    Call,
    Ident,
    IntLit,
    StringLit,
    parse as parse_cel,
)
from propstore.core.conditions.cel_frontend import CelError, check_cel_expression
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.cel_bindings import STANDARD_SYNTHETIC_BINDING_NAMES
from propstore.cel_registry import (
    build_canonical_cel_registry,
    build_store_cel_registry,
)
from propstore.families.concepts.stages import ConceptRecord, parse_concept_record
from propstore.core.row_types import ConceptRow


# ── Fixtures: concept registries ─────────────────────────────────────

@pytest.fixture
def registry():
    """A registry with one concept of each kind, plus extras."""
    return {
        # Quantities
        "fundamental_frequency": ConceptInfo("concept1", "fundamental_frequency", KindType.QUANTITY),
        "subglottal_pressure": ConceptInfo("concept12", "subglottal_pressure", KindType.QUANTITY),
        "speaking_rate": ConceptInfo("concept20", "speaking_rate", KindType.QUANTITY),
        "F0": ConceptInfo("concept1b", "F0", KindType.QUANTITY),
        "F1": ConceptInfo("concept2", "F1", KindType.QUANTITY),
        # Category
        "task": ConceptInfo(
            "concept30", "task", KindType.CATEGORY,
            category_values=["speech", "singing", "whisper"],
            category_extensible=True,
        ),
        "population": ConceptInfo(
            "concept31", "population", KindType.CATEGORY,
            category_values=["adult", "child", "elderly"],
            category_extensible=True,
        ),
        "vowel_type": ConceptInfo(
            "concept32", "vowel_type", KindType.CATEGORY,
            category_values=["front", "back", "central"],
            category_extensible=False,
        ),
        # Boolean
        "phonation_present": ConceptInfo("concept40", "phonation_present", KindType.BOOLEAN),
        # Structural
        "focalization": ConceptInfo("concept101", "focalization", KindType.STRUCTURAL),
        "coarticulation": ConceptInfo("concept50", "coarticulation", KindType.STRUCTURAL),
    }


# ── Parser tests (against cel-parser AST) ───────────────────────────


class TestParser:
    def test_simple_comparison(self):
        ast = parse_cel("F0 > 200")
        assert isinstance(ast, Call)
        assert ast.function == OP_GT

    def test_compound_expression(self):
        ast = parse_cel("F0 > 200 && task == 'singing'")
        assert isinstance(ast, Call)
        assert ast.function == OP_AND

    def test_ratio_comparison(self):
        ast = parse_cel("F1 / F0 > 3.0")
        assert isinstance(ast, Call)
        assert ast.function == OP_GT

    def test_in_expression(self):
        ast = parse_cel("task in ['speech', 'singing']")
        assert isinstance(ast, Call)
        assert ast.function == "@in"

    def test_parenthesized(self):
        ast = parse_cel("(F0 + F1) * 2")
        assert isinstance(ast, Call)
        assert ast.function == OP_MUL

    def test_ternary(self):
        ast = parse_cel("phonation_present ? F0 : 0")
        assert isinstance(ast, Call)
        assert ast.function == "_?_:_"

    def test_negation(self):
        ast = parse_cel("!phonation_present")
        assert isinstance(ast, Call)
        assert ast.function == OP_NOT

    def test_unary_minus(self):
        ast = parse_cel("-F0")
        assert isinstance(ast, Call)
        assert ast.function == OP_NEG


# ── Type checker: quantity concepts ──────────────────────────────────

class TestQuantityTypeChecking:
    def test_arithmetic_ok(self, registry):
        errors = check_cel_expression("F1 / F0 > 3.0", registry)
        assert not any(not e.is_warning for e in errors)

    def test_comparison_ok(self, registry):
        errors = check_cel_expression("fundamental_frequency > 200", registry)
        assert not any(not e.is_warning for e in errors)

    def test_compound_arithmetic_ok(self, registry):
        errors = check_cel_expression("speaking_rate > 3.0 && task == 'singing'", registry)
        assert not any(not e.is_warning for e in errors)

    def test_string_literal_comparison_error(self, registry):
        """Quantity concept compared to string literal → ERROR."""
        errors = check_cel_expression("fundamental_frequency == 'high'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("string literal" in e.message.lower() or "compared to string" in e.message.lower()
                    for e in hard_errors)

    def test_quantity_equality_numeric_ok(self, registry):
        errors = check_cel_expression("fundamental_frequency == 220", registry)
        assert not any(not e.is_warning for e in errors)

    def test_quantity_compared_to_category_concept_errors(self, registry):
        errors = check_cel_expression("fundamental_frequency == task", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any(
            "cannot compare quantity concept 'fundamental_frequency' to category concept 'task'"
            in e.message.lower()
            for e in hard_errors
        )


# ── Type checker: category concepts ──────────────────────────────────

class TestCategoryTypeChecking:
    def test_equality_ok(self, registry):
        errors = check_cel_expression("task == 'singing'", registry)
        assert not any(not e.is_warning for e in errors)

    def test_inequality_ok(self, registry):
        errors = check_cel_expression("task != 'whisper'", registry)
        assert not any(not e.is_warning for e in errors)

    def test_in_ok(self, registry):
        errors = check_cel_expression("task in ['speech', 'singing']", registry)
        assert not any(not e.is_warning for e in errors)

    def test_arithmetic_error(self, registry):
        """Category concept in arithmetic → ERROR."""
        errors = check_cel_expression("task + 1", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("arithmetic" in e.message.lower() for e in hard_errors)

    def test_ordering_error(self, registry):
        """Category concept in ordering → ERROR."""
        errors = check_cel_expression("task > 'singing'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("ordering" in e.message.lower() for e in hard_errors)

    def test_value_in_set_ok(self, registry):
        errors = check_cel_expression("population == 'adult'", registry)
        assert not any(not e.is_warning for e in errors)

    def test_value_not_in_set_extensible_warning(self, registry):
        """Value not in extensible category → WARNING."""
        errors = check_cel_expression("task == 'reading'", registry)
        warnings = [e for e in errors if e.is_warning]
        assert len(warnings) >= 1
        assert not any(not e.is_warning for e in errors)
        assert any("value" in e.message.lower() and "not in" in e.message.lower()
                    for e in warnings)

    def test_value_not_in_set_non_extensible_error(self, registry):
        """Value not in non-extensible category → ERROR."""
        errors = check_cel_expression("vowel_type == 'nasal'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("value" in e.message.lower() and "not in" in e.message.lower()
                    for e in hard_errors)

    def test_in_value_not_in_set_extensible_warning(self, registry):
        errors = check_cel_expression("task in ['speech', 'reading']", registry)
        warnings = [e for e in errors if e.is_warning]
        assert len(warnings) >= 1
        assert not any(not e.is_warning for e in errors)

    def test_in_value_not_in_set_non_extensible_error(self, registry):
        errors = check_cel_expression("vowel_type in ['front', 'nasal']", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1

    def test_category_compared_to_numeric_error(self, registry):
        """Category concept compared to numeric literal → ERROR."""
        errors = check_cel_expression("task == 3", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1


# ── Type checker: boolean concepts ───────────────────────────────────

class TestBooleanTypeChecking:
    def test_bare_truthy_ok(self, registry):
        """Boolean concept as bare truthy → OK."""
        errors = check_cel_expression("phonation_present", registry)
        assert not any(not e.is_warning for e in errors)

    def test_equality_ok(self, registry):
        errors = check_cel_expression("phonation_present == true", registry)
        assert not any(not e.is_warning for e in errors)

    def test_negation_ok(self, registry):
        errors = check_cel_expression("!phonation_present", registry)
        assert not any(not e.is_warning for e in errors)

    def test_arithmetic_error(self, registry):
        """Boolean concept in arithmetic → ERROR."""
        errors = check_cel_expression("phonation_present + 1", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("arithmetic" in e.message.lower() for e in hard_errors)

    def test_ordering_error(self, registry):
        """Boolean concept in ordering → ERROR."""
        errors = check_cel_expression("phonation_present > true", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("ordering" in e.message.lower() for e in hard_errors)

    def test_string_comparison_error(self, registry):
        """Boolean concept compared to string → ERROR."""
        errors = check_cel_expression("phonation_present == 'yes'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1

    def test_numeric_comparison_error(self, registry):
        """Boolean concept compared to number → ERROR."""
        errors = check_cel_expression("phonation_present == 1", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1


# ── Type checker: structural concepts ────────────────────────────────

class TestStructuralTypeChecking:
    def test_any_appearance_error(self, registry):
        """Structural concept in any expression → ERROR."""
        errors = check_cel_expression("focalization > 3", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("structural" in e.message.lower() for e in hard_errors)

    def test_equality_error(self, registry):
        errors = check_cel_expression("focalization == 'internal'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("structural" in e.message.lower() for e in hard_errors)

    def test_bare_reference_error(self, registry):
        errors = check_cel_expression("focalization", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1

    def test_in_expression_error(self, registry):
        errors = check_cel_expression("coarticulation == 'anticipatory'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1


# ── Type checker: undefined concepts ─────────────────────────────────

class TestUndefinedConcepts:
    def test_undefined_name_error(self, registry):
        errors = check_cel_expression("undefined_thing > 3", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("undefined" in e.message.lower() for e in hard_errors)

    def test_one_defined_one_not(self, registry):
        errors = check_cel_expression("F0 > mystery_concept", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1
        assert any("mystery_concept" in e.message for e in hard_errors)


# ── Type checker: complex expressions ────────────────────────────────

class TestComplexExpressions:
    def test_compound_and(self, registry):
        errors = check_cel_expression(
            "speaking_rate > 3.0 && task == 'singing'",
            registry,
        )
        assert not any(not e.is_warning for e in errors)

    def test_compound_or(self, registry):
        errors = check_cel_expression(
            "task == 'singing' || task == 'speech'",
            registry,
        )
        assert not any(not e.is_warning for e in errors)

    def test_ratio_expression(self, registry):
        errors = check_cel_expression("F1 / F0 > 3.0", registry)
        assert not any(not e.is_warning for e in errors)

    def test_mixed_valid(self, registry):
        errors = check_cel_expression(
            "F0 > 200 && population == 'adult' && phonation_present",
            registry,
        )
        assert not any(not e.is_warning for e in errors)

    def test_ternary_valid(self, registry):
        errors = check_cel_expression(
            "phonation_present ? F0 > 200 : true",
            registry,
        )
        assert not any(not e.is_warning for e in errors)


# ── Parse error handling ─────────────────────────────────────────────

class TestParseErrors:
    def test_empty_expression(self, registry):
        errors = check_cel_expression("", registry)
        assert len(errors) >= 1

    def test_malformed_expression(self, registry):
        errors = check_cel_expression(">>><< !!!", registry)
        assert len(errors) >= 1

    def test_unclosed_bracket(self, registry):
        errors = check_cel_expression("task in ['speech'", registry)
        assert len(errors) >= 1


# ── Hypothesis property tests ────────────────────────────────────────

_name_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True)
_op_strategy = st.sampled_from(["==", "!=", ">", "<", ">=", "<="])
_num_strategy = st.one_of(st.integers(0, 1000), st.floats(0.1, 1000.0, allow_nan=False, allow_infinity=False))


@pytest.mark.property
@given(name=_name_strategy, op=_op_strategy, val=_num_strategy)
@settings()
def test_unknown_name_always_errors(name, op, val):
    """Any expression referencing a name not in the registry produces an error."""
    assume(name not in ("true", "false", "in"))
    registry = {}
    expr = f"{name} {op} {val}"
    errors = check_cel_expression(expr, registry)
    hard_errors = [e for e in errors if not e.is_warning]
    assert len(hard_errors) >= 1, f"Expected error for undefined '{name}' in: {expr}"


@pytest.mark.property
@given(val=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L", "N"))))
@settings()
def test_structural_always_errors(val):
    """Structural concept in any expression always produces an error."""
    assume(val not in ("true", "false", "in"))
    registry = {
        "struct_concept": ConceptInfo("concept999", "struct_concept", KindType.STRUCTURAL),
    }
    expr = f"struct_concept == '{val}'"
    errors = check_cel_expression(expr, registry)
    hard_errors = [e for e in errors if not e.is_warning]
    assert len(hard_errors) >= 1


@pytest.mark.property
@given(
    val=st.text(
        min_size=1,
        max_size=12,
        alphabet=st.characters(whitelist_categories=("L", "N")),
    )
)
@settings()
def test_open_category_undeclared_literals_are_warnings_only(val):
    assume(val not in {"speech", "singing", "whisper"})
    registry = {
        "task": ConceptInfo(
            "concept30",
            "task",
            KindType.CATEGORY,
            category_values=["speech", "singing", "whisper"],
            category_extensible=True,
        )
    }

    errors = check_cel_expression(f"task == '{val}'", registry)

    assert errors
    assert all(error.is_warning for error in errors)


@pytest.mark.property
@given(
    val=st.text(
        min_size=1,
        max_size=12,
        alphabet=st.characters(whitelist_categories=("L", "N")),
    )
)
@settings()
def test_closed_category_undeclared_literals_are_hard_errors(val):
    assume(val not in {"front", "back", "central"})
    registry = {
        "vowel_type": ConceptInfo(
            "concept32",
            "vowel_type",
            KindType.CATEGORY,
            category_values=["front", "back", "central"],
            category_extensible=False,
        )
    }

    errors = check_cel_expression(f"vowel_type == '{val}'", registry)

    assert any(not error.is_warning for error in errors)


# ── build_cel_registry tests ─────────────────────────────────────────


class TestBuildCelRegistry:
    """Tests for typed CEL registry projection."""

    @staticmethod
    def _record(
        artifact_id: str,
        canonical_name: str,
        *,
        form: str,
        form_parameters: dict | None = None,
    ) -> ConceptRecord:
        payload = {
            "artifact_id": artifact_id,
            "canonical_name": canonical_name,
            "status": "accepted",
            "definition": f"Definition of {canonical_name}.",
            "form": form,
            "logical_ids": [{"namespace": "speech", "value": canonical_name}],
            "version_id": "sha256:" + ("0" * 64),
        }
        if form_parameters is not None:
            payload["form_parameters"] = form_parameters
        return parse_concept_record(payload)

    def test_canonical_input_quantity(self):
        result = build_canonical_cel_registry([
            self._record("ps:concept:temperature", "temperature", form="frequency"),
        ])
        assert "temperature" in result
        info = result["temperature"]
        assert info.id == "ps:concept:temperature"
        assert info.kind == KindType.QUANTITY
        assert info.category_values == []

    def test_canonical_input_category(self):
        result = build_canonical_cel_registry([
            self._record(
                "ps:concept:color",
                "color",
                form="category",
                form_parameters={
                    "values": ["red", "green", "blue"],
                    "extensible": False,
                },
            )
        ])
        assert "color" in result
        info = result["color"]
        assert info.kind == KindType.CATEGORY
        assert info.category_values == ["red", "green", "blue"]
        assert info.category_extensible is False

    def test_requires_typed_canonical_records(self):
        with pytest.raises(TypeError):
            build_canonical_cel_registry([
                {"artifact_id": "ps:concept:x", "canonical_name": "x"},
            ])

    def test_duplicate_canonical_name_is_error(self):
        with pytest.raises(ValueError, match="duplicate canonical_name"):
            build_canonical_cel_registry([
                self._record("ps:concept:task-a", "task", form="category"),
                self._record("ps:concept:task-b", "task", form="category"),
            ])

    def test_empty_canonical_name_on_canonical_record_is_error(self):
        record = ConceptRecord(
            artifact_id="ps:concept:oops",
            canonical_name="",
            status="accepted",
            definition="Definition.",
            form="frequency",
            logical_ids=(),
            version_id="sha256:" + ("1" * 64),
        )
        with pytest.raises(ValueError, match="canonical_name"):
            build_canonical_cel_registry([record])

    def test_category_extensible_defaults_true(self):
        result = build_canonical_cel_registry([
            self._record(
                "ps:concept:status",
                "status",
                form="category",
                form_parameters={"values": ["active"]},
            )
        ])
        assert result["status"].category_extensible is True

    def test_canonical_record_rejects_malformed_form_parameters(self):
        record = ConceptRecord(
            artifact_id="ps:concept:oops",
            canonical_name="oops",
            status="accepted",
            definition="Definition.",
            form="category",
            form_parameters=["active"],
            logical_ids=(),
            version_id="sha256:" + ("1" * 64),
        )

        with pytest.raises(ValueError, match="form_parameters"):
            build_canonical_cel_registry([record])

    def test_store_projection_requires_typed_rows(self):
        with pytest.raises(TypeError):
            build_store_cel_registry([{"id": "ps:concept:x", "canonical_name": "x"}])

    def test_store_projection_rejects_missing_kind(self):
        row = ConceptRow(
            concept_id="ps:concept:temperature",
            canonical_name="temperature",
            kind_type=None,
            form=None,
        )
        with pytest.raises(ValueError, match="valid kind_type or form"):
            build_store_cel_registry([row])

    def test_standard_synthetic_names_are_not_checker_owned(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("propstore.cel_checker")
        assert "source" in STANDARD_SYNTHETIC_BINDING_NAMES


def test_category_from_cli_round_trip():
    """Category concept created with values -> CEL checker validates against those values."""
    registry = build_canonical_cel_registry([
        TestBuildCelRegistry._record(
            "ps:concept:dataset",
            "dataset",
            form="category",
            form_parameters={"values": ["ActivityNet", "YouCook2"], "extensible": False},
        )
    ])
    # Valid value -> no errors
    errors = check_cel_expression("dataset == 'ActivityNet'", registry)
    assert not any(not e.is_warning for e in errors)

    # Invalid value on non-extensible -> error (not just warning)
    errors = check_cel_expression("dataset == 'UNKNOWN'", registry)
    assert any(not e.is_warning for e in errors)


# ── Type checker: logical operator operand validation (M6/F8) ────────

class TestLogicalOperatorTypeValidation:
    """Tests for M6: CEL type checker must reject non-boolean operands to && and ||.

    Bug: _check_binary returns ExprType.BOOLEAN for logical ops without
    verifying that both operands are boolean-compatible.  '3 && 5' passes
    silently when it should be a type error.

    References: audit finding M6 in notes/audit-z3-cel-conflict.md, lines 110-122.
    """

    def test_numeric_operands_to_and_is_type_error(self, registry):
        """'3 && 5' — numeric operands to && should produce a type error.

        Currently PASSES silently (bug). This test should FAIL until the
        checker is fixed to validate operand types for logical operators.
        """
        errors = check_cel_expression("3 && 5", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1, (
            "Expected type error for numeric operands to '&&', but checker accepted '3 && 5'"
        )

    def test_mixed_operand_types_to_or_is_type_error(self, registry):
        """'fundamental_frequency || "foo"' — quantity || string should be a type error.

        Currently PASSES silently (bug). This test should FAIL until the
        checker is fixed to validate operand types for logical operators.
        """
        errors = check_cel_expression("fundamental_frequency || 'foo'", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) >= 1, (
            "Expected type error for non-boolean operands to '||', "
            "but checker accepted 'fundamental_frequency || \"foo\"'"
        )

    def test_boolean_operands_to_and_ok(self, registry):
        """'true && false' — boolean literal operands to && should pass (control)."""
        errors = check_cel_expression("true && false", registry)
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) == 0, (
            f"Boolean operands to '&&' should be valid, but got errors: {hard_errors}"
        )

    def test_comparison_results_to_and_ok(self, registry):
        """'fundamental_frequency > 0 && F0 < 10' — comparisons to && should pass (control)."""
        errors = check_cel_expression(
            "fundamental_frequency > 0 && F0 < 10", registry
        )
        hard_errors = [e for e in errors if not e.is_warning]
        assert len(hard_errors) == 0, (
            f"Comparison results as operands to '&&' should be valid, but got errors: {hard_errors}"
        )
