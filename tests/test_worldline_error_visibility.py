"""Red-phase tests for worldline_runner silent exception swallowing.

Audit findings F1.4 and F1.5: bare ``except Exception`` blocks at
worldline_runner.py:179 and :266 silently swallow sensitivity-analysis
and argumentation-capture failures.  The caller receives empty/None
results with no indication that an error occurred.

These tests assert that the WorldlineResult carries an explicit error
indicator when those subsystems raise.  They should FAIL on the current
code because the current code swallows the exception and provides no
error field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from propstore.world import Environment
from propstore.world.types import ReasoningBackend, RenderPolicy, ResolutionStrategy
from propstore.worldline import (
    WorldlineDefinition,
    WorldlineInputs,
)
from propstore.worldline_runner import run_worldline


# ── helpers ──────────────────────────────────────────────────────────


def _make_definition(
    *,
    targets: list[str],
    strategy: ResolutionStrategy | None = None,
    reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH,
) -> WorldlineDefinition:
    return WorldlineDefinition(
        id="test-err-visibility",
        name="error visibility test",
        inputs=WorldlineInputs(environment=Environment(), overrides={}),
        policy=RenderPolicy(
            strategy=strategy,
            reasoning_backend=reasoning_backend,
        ),
        targets=targets,
    )


@dataclass
class _FakeValueResult:
    status: str = "determined"
    claims: list[dict[str, Any]] = field(default_factory=lambda: [
        {"id": "claim-1", "value": 42.0}
    ])


@dataclass
class _FakeDerivedResult:
    status: str = "derived"
    value: float = 42.0
    formula: str = "x * y"
    input_values: dict[str, float] = field(default_factory=lambda: {
        "input_a": 6.0, "input_b": 7.0,
    })


class _FakeWorld:
    """Minimal stand-in for WorldModel."""

    _bound: _FakeBound | None = None

    def resolve_concept(self, name: str) -> str | None:
        return f"concept:{name}"

    def get_concept(self, cid: str) -> dict | None:
        return {"canonical_name": cid.replace("concept:", "")}

    def has_table(self, name: str) -> bool:
        return name == "claim_stance"

    def parameterizations_for(self, cid: str) -> list:
        return []

    def stances_between(self, ids):
        return []

    def bind(self, environment, *, policy=None):
        if self._bound is not None:
            return self._bound
        return _FakeBound()

    def chain_query(self, concept_id, **kw):
        raise LookupError("no chain")


class _FakeBound:
    """Minimal stand-in for a bound WorldModel."""

    _bindings: dict = {}

    def value_of(self, concept_id: str) -> _FakeValueResult:
        return _FakeValueResult()

    def derived_value(self, concept_id: str, **kw) -> _FakeDerivedResult:
        return _FakeDerivedResult()

    def active_claims(self) -> list[dict]:
        return [{"id": "claim-1", "value": 42.0}]

    def claim_support(self, claim):
        return (None, object())


# ── Test 1: sensitivity analysis error is surfaced ───────────────────


class TestSensitivityErrorVisibility:
    """F1.4 — worldline_runner.py:179 swallows sensitivity failures."""

    def test_sensitivity_failure_produces_error_indicator(self):
        """When analyze_sensitivity raises, the result must carry an
        error indicator — not silently return sensitivity=None."""
        definition = _make_definition(targets=["output_qty"])

        world = _FakeWorld()
        fake_bound = _FakeBound()

        # Make value_of return "derived" status so the sensitivity path triggers
        fake_bound.value_of = lambda cid: _FakeValueResult(
            status="determined",
            claims=[{"id": "claim-1", "value": 42.0}],
        )

        # Force the target to appear as "derived" in the values dict so
        # the sensitivity analysis block at line 160 fires.
        derived_entry = {
            "status": "derived",
            "value": 42.0,
            "source": "derived",
            "formula": "x * y",
            "inputs_used": {},
        }

        world._bound = fake_bound

        with (
            patch("propstore.worldline_runner._resolve_concept_name", return_value="concept:output_qty"),
            patch("propstore.worldline_runner._resolve_target", return_value=derived_entry),
            patch(
                "propstore.sensitivity.analyze_sensitivity",
                side_effect=RuntimeError("boom — sensitivity engine crashed"),
            ),
        ):
            result = run_worldline(definition, world)

        # Current (buggy) behaviour: sensitivity is None with no error.
        # Expected (fixed) behaviour: result carries an explicit error
        # indicator so the caller knows the analysis was attempted and failed.
        assert result.sensitivity is not None, (
            "sensitivity is None — the exception was silently swallowed "
            "(F1.4: bare except Exception at worldline_runner.py:179)"
        )
        # The error indicator could be a dict with an error key, or a
        # dedicated field — we check for either pattern.
        if isinstance(result.sensitivity, dict):
            has_error = any(
                "error" in str(v).lower()
                for v in result.sensitivity.values()
            )
            assert has_error, (
                "sensitivity dict exists but contains no error indicator"
            )


# ── Test 2: argumentation capture error is surfaced ──────────────────


class TestArgumentationErrorVisibility:
    """F1.5 — worldline_runner.py:266 swallows argumentation failures."""

    def test_argumentation_failure_produces_error_indicator(self):
        """When argumentation capture raises, the result must carry an
        error indicator — not silently return argumentation=None."""
        definition = _make_definition(
            targets=["output_qty"],
            strategy=ResolutionStrategy.ARGUMENTATION,
            reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
        )

        world = _FakeWorld()
        fake_bound = _FakeBound()

        # Make active_claims raise to trigger the except block at line 266
        fake_bound.active_claims = MagicMock(
            side_effect=RuntimeError("boom — argumentation crashed"),
        )

        world._bound = fake_bound

        with (
            patch("propstore.worldline_runner._resolve_concept_name", return_value="concept:output_qty"),
            patch("propstore.worldline_runner._resolve_target", return_value={
                "status": "determined", "value": 42.0, "source": "claim",
            }),
        ):
            result = run_worldline(definition, world)

        # Current (buggy) behaviour: argumentation is None with no error.
        # Expected (fixed) behaviour: explicit error indicator.
        assert result.argumentation is not None, (
            "argumentation is None — the exception was silently swallowed "
            "(F1.5: bare except Exception at worldline_runner.py:266)"
        )
        if isinstance(result.argumentation, dict):
            has_error = any(
                "error" in str(v).lower()
                for v in result.argumentation.values()
            )
            assert has_error, (
                "argumentation dict exists but contains no error indicator"
            )
