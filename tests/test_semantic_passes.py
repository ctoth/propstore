"""Tests for the explicit semantic-pass pipeline framework.

The framework (``propstore.semantic_passes``) has no reference test in the
feature-peak tree; PLAN.md §7 mandates one be written. These tests pin the
registry's stage-contract checking, the runner's linear execution + quarantine
short-circuit, and the ``PropstoreFamily`` drift gate against the charter
registry.
"""

from __future__ import annotations

from enum import StrEnum

import pytest

from propstore.families.registry import PropstoreFamily, registered_family_names
from propstore.semantic_passes.registry import PipelineRegistry, PipelineRegistryError
from propstore.semantic_passes.runner import PipelineExecutionError, run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult


class _Stage(StrEnum):
    AUTHORED = "authored"
    NORMALIZED = "normalized"
    CHECKED = "checked"


class _Normalize:
    family = PropstoreFamily.CONCEPT
    name = "normalize"
    version = "1"
    input_stage = _Stage.AUTHORED
    output_stage = _Stage.NORMALIZED

    def run(self, value: object, context: object) -> PassResult[object]:
        assert isinstance(value, str)
        return PassResult.ok(value.strip())


class _Check:
    family = PropstoreFamily.CONCEPT
    name = "check"
    version = "1"
    input_stage = _Stage.NORMALIZED
    output_stage = _Stage.CHECKED

    def run(self, value: object, context: object) -> PassResult[object]:
        assert isinstance(value, str)
        return PassResult.ok(value.upper())


class _Quarantine:
    """A check pass that declines to produce output (records an error)."""

    family = PropstoreFamily.CONCEPT
    name = "check"
    version = "1"
    input_stage = _Stage.NORMALIZED
    output_stage = _Stage.CHECKED

    def run(self, value: object, context: object) -> PassResult[object]:
        return PassResult(
            output=None,
            diagnostics=(
                PassDiagnostic(
                    level="error",
                    code="invalid",
                    message="declined",
                    family=self.family,
                    stage=self.output_stage,
                ),
            ),
        )


def _registry(*passes: type[object]) -> PipelineRegistry:
    registry = PipelineRegistry()
    for pass_class in passes:
        registry.register(pass_class)
    return registry


def test_registry_rejects_duplicate_pass_name() -> None:
    registry = PipelineRegistry()
    registry.register(_Normalize)
    with pytest.raises(PipelineRegistryError, match="duplicate pass name"):
        registry.register(_Normalize)


def test_registry_rejects_family_mismatch() -> None:
    registry = PipelineRegistry()
    with pytest.raises(PipelineRegistryError, match="declares family"):
        registry.register(_Normalize, family=PropstoreFamily.CLAIM)


def test_pipeline_rejects_non_contiguous_stages() -> None:
    # Only the CHECK pass is registered; selecting from AUTHORED cannot start it
    # because CHECK expects NORMALIZED as its input stage.
    registry = _registry(_Check)
    with pytest.raises(PipelineRegistryError, match="expects"):
        registry.pipeline(
            family=PropstoreFamily.CONCEPT,
            start_stage=_Stage.AUTHORED,
            target_stage=_Stage.CHECKED,
        )


def test_pipeline_empty_when_start_equals_target() -> None:
    registry = _registry(_Normalize, _Check)
    pipeline = registry.pipeline(
        family=PropstoreFamily.CONCEPT,
        start_stage=_Stage.CHECKED,
        target_stage=_Stage.CHECKED,
    )
    assert pipeline.passes == ()


def test_pipeline_unreachable_target_raises() -> None:
    registry = _registry(_Normalize)
    with pytest.raises(PipelineRegistryError, match="cannot reach"):
        registry.pipeline(
            family=PropstoreFamily.CONCEPT,
            start_stage=_Stage.AUTHORED,
            target_stage=_Stage.CHECKED,
        )


def test_runner_executes_passes_in_order() -> None:
    registry = _registry(_Normalize, _Check)
    result = run_pipeline(
        "  hello  ",
        family=PropstoreFamily.CONCEPT,
        start_stage=_Stage.AUTHORED,
        target_stage=_Stage.CHECKED,
        registry=registry,
        context=None,
    )
    assert result.ok
    assert result.output == "HELLO"
    assert result.stage is _Stage.CHECKED


def test_runner_short_circuits_on_quarantine() -> None:
    registry = _registry(_Normalize, _Quarantine)
    result = run_pipeline(
        "x",
        family=PropstoreFamily.CONCEPT,
        start_stage=_Stage.AUTHORED,
        target_stage=_Stage.CHECKED,
        registry=registry,
        context=None,
    )
    assert not result.ok
    assert result.output is None
    assert len(result.errors) == 1
    assert result.errors[0].code == "invalid"


def test_runner_no_family_for_unregistered() -> None:
    registry = PipelineRegistry()
    with pytest.raises(PipelineRegistryError, match="no semantic passes"):
        run_pipeline(
            "x",
            family=PropstoreFamily.CONCEPT,
            start_stage=_Stage.AUTHORED,
            target_stage=_Stage.CHECKED,
            registry=registry,
            context=None,
        )


def test_pipeline_execution_error_is_value_error() -> None:
    # PipelineExecutionError surfaces as a ValueError subclass for callers.
    assert issubclass(PipelineExecutionError, ValueError)


def test_pass_diagnostic_render_and_contains() -> None:
    diagnostic = PassDiagnostic(
        level="warning",
        code="lint",
        message="missing description",
        family=PropstoreFamily.CONCEPT,
        stage=_Stage.CHECKED,
        filename="concept/foo.yaml",
    )
    assert "concept/foo.yaml" in diagnostic
    assert diagnostic.render().startswith("concept/foo.yaml: ")
    assert diagnostic.is_warning


def test_propstore_family_matches_registry() -> None:
    # Drift gate: the typed family enum must stay in lockstep with the
    # charter-derived registry. Adding a charter without a member fails here.
    assert {member.value for member in PropstoreFamily} == set(
        registered_family_names()
    )
