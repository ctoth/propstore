"""TDD tests for the form dimensions feature.

Tests the planned `dimensions` field on form definitions — a dict mapping
SI base dimension symbols (L, M, T, I, Theta, N, J) to integer exponents.
These tests are written BEFORE implementation and should fail until the
dimensions feature is built.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml
from hypothesis import given, assume, settings, HealthCheck
from hypothesis import strategies as st

from propstore.form_utils import (
    FormDefinition,
    load_form,
    validate_form_files,
)
from propstore.unit_dimensions import clear_symbol_table, _symbol_table

# ── Constants ─────────────────────────────────────────────────────────

SI_BASE_DIMENSIONS = {"L", "M", "T", "I", "Theta", "N", "J"}

FORM_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "generated" / "form.schema.json"


def _load_schema() -> dict:
    with open(FORM_SCHEMA_PATH) as f:
        return json.load(f)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def forms_dir():
    """Return the real forms directory."""
    return Path(__file__).parent.parent / "propstore" / "_resources" / "forms"


@pytest.fixture
def form_schema() -> dict:
    return _load_schema()


def _write_form_yaml(directory: Path, name: str, data: dict) -> Path:
    """Write a form YAML file and return its path."""
    path = directory / f"{name}.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return path


# ── Unit Tests ────────────────────────────────────────────────────────


class TestDimensionsSchemaValidation:
    """Test that the JSON schema correctly validates the dimensions field."""

    def test_form_with_dimensions_validates(self, form_schema: dict) -> None:
        """Form with dimensions: {T: -1} validates as non-dimensionless."""
        form_data = {
            "name": "test_freq",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {"T": -1},
        }
        # Should not raise
        jsonschema.validate(form_data, form_schema)

    def test_form_with_empty_dimensions_validates(self, form_schema: dict) -> None:
        """Form with dimensions: {} validates as dimensionless."""
        form_data = {
            "name": "test_ratio",
            "dimensionless": True,
            "dimensions": {},
        }
        jsonschema.validate(form_data, form_schema)

    def test_dimensions_conflict_nonempty_but_dimensionless(self) -> None:
        """Form with dimensions: {T: -1} but dimensionless: true fails validation.

        A form cannot claim to be dimensionless while having non-empty dimensions.
        This should be caught either by the schema or by validate_form_files.
        Tested via TestDimensionsValidationLogic below.
        """
        pass

    def test_form_without_dimensions_still_validates(
        self, form_schema: dict
    ) -> None:
        """Backward compat: form with no dimensions field still validates."""
        form_data = {
            "name": "test_legacy",
            "dimensionless": False,
            "unit_symbol": "Pa",
        }
        jsonschema.validate(form_data, form_schema)

    def test_dimensions_rejects_non_integer_exponent(
        self, form_schema: dict
    ) -> None:
        """Dimension exponents must be integers; floats should fail."""
        form_data = {
            "name": "test_bad_exp",
            "dimensionless": False,
            "dimensions": {"T": -1.5},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(form_data, form_schema)

    def test_dimensions_rejects_invalid_key(self, form_schema: dict) -> None:
        """Dimension keys must be identifiers; '123' is invalid."""
        form_data = {
            "name": "test_bad_key",
            "dimensionless": False,
            "dimensions": {"123": 1},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(form_data, form_schema)

    def test_dimensions_accepts_custom_key(self, form_schema: dict) -> None:
        """Dimension keys can be any valid identifier, not just SI symbols."""
        form_data = {
            "name": "test_custom",
            "dimensionless": False,
            "dimensions": {"Currency": 1, "Quantity": -1},
        }
        # Should not raise
        jsonschema.validate(form_data, form_schema)


class TestDimensionsValidationLogic:
    """Test validation logic that catches dimension/dimensionless conflicts."""

    def test_nonempty_dimensions_but_dimensionless_fails_validation(
        self, tmp_path: Path
    ) -> None:
        """validate_form_files rejects dimensionless=true with non-empty dimensions."""
        _write_form_yaml(tmp_path, "bad_form", {
            "name": "bad_form",
            "dimensionless": True,
            "dimensions": {"T": -1},
        })
        result = validate_form_files(tmp_path)
        assert len(result.errors) > 0
        # At least one error should mention the conflict
        combined = " ".join(result.errors)
        assert "dimension" in combined.lower()

    def test_empty_dimensions_but_not_dimensionless_quantity_fails(
        self, tmp_path: Path
    ) -> None:
        """A quantity form with dimensions: {} but dimensionless: false should fail.

        A quantity form that claims to not be dimensionless must have at least
        one non-zero dimension exponent. (Category/structural forms are exempt.)
        """
        _write_form_yaml(tmp_path, "bad_qty", {
            "name": "bad_qty",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {},
        })
        result = validate_form_files(tmp_path)
        assert len(result.errors) > 0
        combined = " ".join(result.errors)
        assert "dimension" in combined.lower()

    def test_valid_form_passes_validation(self, tmp_path: Path) -> None:
        """A correctly configured form passes validate_form_files."""
        _write_form_yaml(tmp_path, "good_form", {
            "name": "good_form",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {"T": -1},
        })
        result = validate_form_files(tmp_path)
        assert result.ok

    def test_no_dimensions_field_passes_validation(self, tmp_path: Path) -> None:
        """Backward compat: form without dimensions field still passes."""
        _write_form_yaml(tmp_path, "legacy", {
            "name": "legacy",
            "dimensionless": False,
            "unit_symbol": "Pa",
        })
        result = validate_form_files(tmp_path)
        assert result.ok


class TestFormDefinitionDimensions:
    """Test that FormDefinition correctly loads the dimensions field."""

    def test_load_form_with_dimensions(self, tmp_path: Path) -> None:
        """load_form populates dimensions on FormDefinition."""
        _write_form_yaml(tmp_path, "freq_test", {
            "name": "freq_test",
            "dimensionless": False,
            "unit_symbol": "Hz",
            "dimensions": {"T": -1},
        })
        fd = load_form(tmp_path, "freq_test")
        assert fd is not None
        assert hasattr(fd, "dimensions")
        assert fd.dimensions == {"T": -1}

    def test_load_form_dimensionless_has_empty_dimensions(
        self, tmp_path: Path
    ) -> None:
        """Dimensionless form gets dimensions={}."""
        _write_form_yaml(tmp_path, "ratio_test", {
            "name": "ratio_test",
            "dimensionless": True,
            "base": "ratio",
            "dimensions": {},
        })
        fd = load_form(tmp_path, "ratio_test")
        assert fd is not None
        assert fd.dimensions == {}

    def test_load_form_without_dimensions_field(self, tmp_path: Path) -> None:
        """Form without explicit dimensions field gets None or empty dict."""
        _write_form_yaml(tmp_path, "legacy_test", {
            "name": "legacy_test",
            "dimensionless": False,
            "unit_symbol": "Pa",
        })
        fd = load_form(tmp_path, "legacy_test")
        assert fd is not None
        # Missing dimensions are represented as absent or as an empty mapping.
        assert fd.dimensions is None or fd.dimensions == {}


class TestFormAddCLIDimensions:
    """Test that `pks form add --dimensions ...` creates correct YAML."""

    def test_form_add_with_dimensions_creates_yaml(self, tmp_path: Path) -> None:
        """form add --dimensions '{"T": -1}' writes dimensions to YAML."""
        from click.testing import CliRunner
        from propstore.cli.form import add

        runner = CliRunner()
        result = runner.invoke(
            add,
            [
                "--name", "test_form",
                "--dimensions", '{"T": -1}',
                "--dimensionless", "false",
            ],
            obj={"repo": _make_mock_repo(tmp_path)},
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify the written YAML
        form_path = tmp_path / "forms" / "test_form.yaml"
        assert form_path.exists()
        with open(form_path) as f:
            data = yaml.safe_load(f)
        assert data["dimensions"] == {"T": -1}
        assert data["dimensionless"] is False
        assert data["name"] == "test_form"

    def test_form_add_dimensionless_with_empty_dimensions(
        self, tmp_path: Path
    ) -> None:
        """form add for dimensionless form creates dimensions: {}."""
        from click.testing import CliRunner
        from propstore.cli.form import add

        runner = CliRunner()
        result = runner.invoke(
            add,
            [
                "--name", "test_dimless",
                "--dimensions", "{}",
                "--dimensionless", "true",
            ],
            obj={"repo": _make_mock_repo(tmp_path)},
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        form_path = tmp_path / "forms" / "test_dimless.yaml"
        assert form_path.exists()
        with open(form_path) as f:
            data = yaml.safe_load(f)
        assert data["dimensions"] == {} or data["dimensions"] is None
        assert data["dimensionless"] is True


# ── Hypothesis Property-Based Tests ──────────────────────────────────

# Strategy for valid SI dimension dicts
_dim_key_strategy = st.sampled_from(sorted(SI_BASE_DIMENSIONS))
_dim_exponent_strategy = st.integers(min_value=-4, max_value=4)
_dimensions_strategy = st.dictionaries(
    keys=_dim_key_strategy,
    values=_dim_exponent_strategy,
    min_size=0,
    max_size=7,
)


class TestDimensionsPropertyBased:
    """Hypothesis property-based tests for dimensions invariants."""

    @given(dimensions=_dimensions_strategy)
    @settings()
    def test_nonempty_dimensions_implies_not_dimensionless(
        self, dimensions: dict[str, int],
    ) -> None:
        """If dimensions is non-empty, form must not be dimensionless."""
        assume(len(dimensions) > 0)
        assume(any(v != 0 for v in dimensions.values()))
        td = Path(tempfile.mkdtemp())
        form_data = {
            "name": "prop_test",
            "dimensionless": False,
            "unit_symbol": "X",
            "dimensions": dimensions,
        }
        _write_form_yaml(td, "prop_test", form_data)
        fd = load_form(td, "prop_test")
        assert fd is not None
        assert fd.is_dimensionless is False

    @given(dimensions=_dimensions_strategy)
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_dimensionless_implies_empty_or_absent_dimensions(
        self, dimensions: dict[str, int],
    ) -> None:
        """If dimensionless is true, dimensions must be {} or absent."""
        # Only test with truly empty dimensions (all zeros count as empty
        # in dimensional analysis)
        assume(all(v == 0 for v in dimensions.values()))
        td = Path(tempfile.mkdtemp())
        form_data = {
            "name": "dimless_prop",
            "dimensionless": True,
            "base": "ratio",
            "dimensions": {k: v for k, v in dimensions.items() if v != 0},
        }
        _write_form_yaml(td, "dimless_prop", form_data)
        fd = load_form(td, "dimless_prop")
        assert fd is not None
        assert fd.is_dimensionless is True
        # Dimensions should be empty or absent
        assert fd.dimensions is None or fd.dimensions == {} or all(
            v == 0 for v in fd.dimensions.values()
        )

    @given(
        exponent=st.one_of(
            st.floats(allow_nan=False, allow_infinity=False).filter(
                lambda x: x != int(x) if x == x else True
            ),
            st.text(min_size=1, max_size=5),
        )
    )
    @settings(deadline=None)
    def test_non_integer_exponents_rejected(
        self, exponent: Any,
    ) -> None:
        """Dimension exponents must be integers; non-integers fail schema."""
        schema = _load_schema()
        form_data = {
            "name": "bad_exp",
            "dimensionless": False,
            "dimensions": {"T": exponent},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(form_data, schema)

    @given(key=st.text(min_size=1, max_size=10).filter(
        lambda k: not k or not k[0].isalpha() or not all(c.isalnum() or c == '_' for c in k)
    ))
    @settings()
    def test_invalid_dimension_keys_rejected(
        self, key: str,
    ) -> None:
        """Dimension keys must be valid identifiers (start with letter, alphanumeric/underscore)."""
        assume(len(key) > 0)
        schema = _load_schema()
        form_data = {
            "name": "bad_key",
            "dimensionless": False,
            "dimensions": {key: 1},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(form_data, schema)

    @given(dimensions=_dimensions_strategy.filter(lambda d: len(d) > 0))
    @settings()
    def test_forms_with_same_dimensions_compatible(
        self, dimensions: dict[str, int],
    ) -> None:
        """Two forms with identical dimensions represent the same physical kind."""
        td = Path(tempfile.mkdtemp())
        _write_form_yaml(td, "form_a", {
            "name": "form_a",
            "dimensionless": False,
            "unit_symbol": "X",
            "dimensions": dimensions,
        })
        _write_form_yaml(td, "form_b", {
            "name": "form_b",
            "dimensionless": False,
            "unit_symbol": "Y",
            "dimensions": dimensions,
        })
        fd_a = load_form(td, "form_a")
        fd_b = load_form(td, "form_b")
        assert fd_a is not None and fd_b is not None
        assert fd_a.dimensions == fd_b.dimensions



class TestSymbolTableReset:
    """Tests for symbol table invalidation via clear_symbol_table() (F7.3).

    The _symbol_table module-level dict accumulates entries across calls to
    register_form_units() and is never reset. These tests verify that
    clear_symbol_table() exists and works correctly. They SHOULD FAIL
    because clear_symbol_table() does not exist yet.
    """

    def test_clear_symbol_table_empties_table(self) -> None:
        """clear_symbol_table() resets the symbol table to None/empty."""
        from propstore.unit_dimensions import _get_symbol_table

        # Force the table to be loaded
        table = _get_symbol_table()
        assert table is not None
        assert len(table) > 0  # physgen_units.json has entries

        # Clear and verify
        clear_symbol_table()

        # After clearing, the internal _symbol_table should be None
        # (so next _get_symbol_table() call re-loads from disk)
        import propstore.unit_dimensions as ud
        assert ud._symbol_table is None

    def test_clear_symbol_table_removes_registered_form_units(
        self, tmp_path: Path
    ) -> None:
        """After clear, previously registered form units are gone."""
        from propstore.unit_dimensions import (
            _get_symbol_table,
            register_form_units,
            resolve_unit_dimensions,
        )

        # Write a form with a custom extra_unit
        _write_form_yaml(tmp_path, "custom_form", {
            "name": "custom_form",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "X",
            "dimensions": {"L": 1},
            "extra_units": [
                {"symbol": "cX", "dimensions": {"L": 1}},
            ],
        })

        # Register the custom unit
        register_form_units(tmp_path)
        assert resolve_unit_dimensions("cX") is not None

        # Clear the symbol table
        clear_symbol_table()

        # After clearing & reloading base table, custom unit should be gone
        result = resolve_unit_dimensions("cX")
        assert result is None


# ── Helpers ───────────────────────────────────────────────────────────


def _make_mock_repo(base: Path):
    from propstore.repository import Repository

    return Repository.init(base)
