"""Tests for the CEL condition expression type-checker.

Each test specifies the registry (concept name → kind) and the expected
errors/warnings. Tests are organized by the type rule from the compiler
contract they exercise.
"""

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from propstore.cel_checker import (
    BinaryOpNode,
    CelError,
    ConceptInfo,
    KindType,
    TernaryNode,
    UnaryOpNode,
    build_cel_registry,
    build_cel_registry_from_loaded,
    check_cel_expression,
    parse_cel,
    tokenize,
)
from propstore.validate import LoadedConcept


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


# ── Tokenizer tests ──────────────────────────────────────────────────

class TestTokenizer:
    def test_simple_comparison(self):
        tokens = tokenize("F0 > 200")
        assert tokens[0].value == "F0"
        assert tokens[1].value == ">"
        assert tokens[2].value == 200

    def test_string_literal(self):
        tokens = tokenize("task == 'singing'")
        assert tokens[2].value == "singing"

    def test_double_quoted_string(self):
        tokens = tokenize('task == "singing"')
        assert tokens[2].value == "singing"

    def test_logical_operators(self):
        tokens = tokenize("F0 > 200 && task == 'singing'")
        ops = [t.value for t in tokens if t.type.name == "OP"]
        assert ">" in ops
        assert "&&" in ops
        assert "==" in ops

    def test_float_literal(self):
        tokens = tokenize("F1 / F0 > 3.0")
        floats = [t for t in tokens if t.type.name == "FLOAT_LIT"]
        assert len(floats) == 1
        assert floats[0].value == 3.0

    def test_in_keyword(self):
        tokens = tokenize("task in ['speech', 'singing']")
        in_tokens = [t for t in tokens if t.type.name == "IN"]
        assert len(in_tokens) == 1

    def test_boolean_literal(self):
        tokens = tokenize("phonation_present == true")
        bools = [t for t in tokens if t.type.name == "BOOL_LIT"]
        assert len(bools) == 1
        assert bools[0].value is True

    def test_negation(self):
        tokens = tokenize("!phonation_present")
        assert tokens[0].value == "!"

    def test_string_literal_unescapes_quotes(self):
        """Escaped quotes inside string literals should be unescaped."""
        tokens = tokenize(r'category == "has \"inner\" quotes"')
        string_token = [t for t in tokens if t.type.name == "STRING_LIT"][0]
        assert string_token.value == 'has "inner" quotes'

    def test_string_literal_unescapes_backslash(self):
        """Escaped backslashes inside string literals should be unescaped."""
        tokens = tokenize(r'category == "path\\to\\file"')
        string_token = [t for t in tokens if t.type.name == "STRING_LIT"][0]
        assert string_token.value == "path\\to\\file"

    def test_single_quoted_string_unescapes(self):
        """Single-quoted strings should also unescape."""
        tokens = tokenize(r"category == 'it\'s here'")
        string_token = [t for t in tokens if t.type.name == "STRING_LIT"][0]
        assert string_token.value == "it's here"


# ── Parser tests ─────────────────────────────────────────────────────

class TestParser:
    def test_simple_comparison(self):
        ast = parse_cel("F0 > 200")
        assert ast.__class__.__name__ == "BinaryOpNode"

    def test_compound_expression(self):
        ast = parse_cel("F0 > 200 && task == 'singing'")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == "&&"

    def test_ratio_comparison(self):
        ast = parse_cel("F1 / F0 > 3.0")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == ">"

    def test_in_expression(self):
        ast = parse_cel("task in ['speech', 'singing']")
        assert ast.__class__.__name__ == "InNode"

    def test_parenthesized(self):
        ast = parse_cel("(F0 + F1) * 2")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == "*"

    def test_ternary(self):
        ast = parse_cel("phonation_present ? F0 : 0")
        assert isinstance(ast, TernaryNode)

    def test_negation(self):
        ast = parse_cel("!phonation_present")
        assert isinstance(ast, UnaryOpNode)
        assert ast.op == "!"

    def test_unary_minus(self):
        ast = parse_cel("-F0")
        assert isinstance(ast, UnaryOpNode)
        assert ast.op == "-"


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


@given(name=_name_strategy, op=_op_strategy, val=_num_strategy)
@settings(max_examples=50)
def test_unknown_name_always_errors(name, op, val):
    """Any expression referencing a name not in the registry produces an error."""
    assume(name not in ("true", "false", "in"))
    registry = {}
    expr = f"{name} {op} {val}"
    errors = check_cel_expression(expr, registry)
    hard_errors = [e for e in errors if not e.is_warning]
    assert len(hard_errors) >= 1, f"Expected error for undefined '{name}' in: {expr}"


@given(val=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L", "N"))))
@settings(max_examples=30)
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


# ── build_cel_registry tests ─────────────────────────────────────────


class TestBuildCelRegistry:
    """Tests for the consolidated build_cel_registry function."""

    def test_dict_input_quantity(self):
        concept_registry = {
            "concept1": {
                "canonical_name": "temperature",
                "form": "quantity",
            }
        }
        result = build_cel_registry(concept_registry)
        assert "temperature" in result
        info = result["temperature"]
        assert info.id == "concept1"
        assert info.kind == KindType.QUANTITY
        assert info.category_values == []

    def test_dict_input_category(self):
        concept_registry = {
            "concept2": {
                "canonical_name": "color",
                "form": "category",
                "form_parameters": {
                    "values": ["red", "green", "blue"],
                    "extensible": False,
                },
            }
        }
        result = build_cel_registry(concept_registry)
        assert "color" in result
        info = result["color"]
        assert info.kind == KindType.CATEGORY
        assert info.category_values == ["red", "green", "blue"]
        assert info.category_extensible is False

    def test_skips_missing_name(self):
        concept_registry = {
            "concept3": {"form": "quantity"},  # no canonical_name
        }
        result = build_cel_registry(concept_registry)
        assert len(result) == 0

    def test_skips_missing_form(self):
        concept_registry = {
            "concept4": {"canonical_name": "pressure"},  # no form
        }
        result = build_cel_registry(concept_registry)
        assert len(result) == 0

    def test_category_extensible_defaults_true(self):
        concept_registry = {
            "concept5": {
                "canonical_name": "status",
                "form": "category",
                "form_parameters": {"values": ["active"]},
            }
        }
        result = build_cel_registry(concept_registry)
        assert result["status"].category_extensible is True

    def test_from_loaded_concepts(self):
        from pathlib import Path

        concepts = [
            LoadedConcept(
                filename="temperature",
                filepath=Path("fake/temperature.yaml"),
                data={
                    "id": "concept1",
                    "canonical_name": "temperature",
                    "form": "quantity",
                },
            ),
            LoadedConcept(
                filename="color",
                filepath=Path("fake/color.yaml"),
                data={
                    "id": "concept2",
                    "canonical_name": "color",
                    "form": "category",
                    "form_parameters": {
                        "values": ["red", "blue"],
                        "extensible": False,
                    },
                },
            ),
        ]
        result = build_cel_registry_from_loaded(concepts)
        assert "temperature" in result
        assert "color" in result
        assert result["temperature"].kind == KindType.QUANTITY
        assert result["color"].category_values == ["red", "blue"]

    def test_from_loaded_skips_no_id(self):
        from pathlib import Path

        concepts = [
            LoadedConcept(
                filename="mystery",
                filepath=Path("fake/mystery.yaml"),
                data={
                    "canonical_name": "mystery",
                    "form": "quantity",
                },
            ),
        ]
        result = build_cel_registry_from_loaded(concepts)
        assert len(result) == 0


def test_category_from_cli_round_trip():
    """Category concept created with values -> CEL checker validates against those values."""
    registry = build_cel_registry({
        "concept1": {
            "canonical_name": "dataset",
            "form": "category",
            "form_parameters": {"values": ["ActivityNet", "YouCook2"], "extensible": False},
        }
    })
    # Valid value -> no errors
    errors = check_cel_expression("dataset == 'ActivityNet'", registry)
    assert not any(not e.is_warning for e in errors)

    # Invalid value on non-extensible -> error (not just warning)
    errors = check_cel_expression("dataset == 'UNKNOWN'", registry)
    assert any(not e.is_warning for e in errors)
