"""Linear semantic pass runner."""

from __future__ import annotations

from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry, PipelineRegistryError
from propstore.semantic_passes.types import PipelineResult, StageId


class PipelineExecutionError(ValueError):
    """Raised when a pass violates the declared stage contract."""


def run_pipeline(
    value: object,
    *,
    family: PropstoreFamily,
    start_stage: StageId,
    target_stage: StageId,
    registry: PipelineRegistry,
    context: object,
) -> PipelineResult[object]:
    pipeline = registry.pipeline(
        family=family,
        start_stage=start_stage,
        target_stage=target_stage,
    )
    current_stage = start_stage
    current_value = value
    diagnostics = []

    for pass_class in pipeline.passes:
        if pass_class.family is not family:
            raise PipelineExecutionError(
                f"pass {pass_class.name!r} declares family "
                f"{pass_class.family.value!r}, not {family.value!r}"
            )
        if pass_class.input_stage != current_stage:
            raise PipelineExecutionError(
                f"pass {pass_class.name!r} expected stage "
                f"{pass_class.input_stage.value!r}, got {current_stage.value!r}"
            )
        pass_instance = pass_class()
        result = pass_instance.run(current_value, context)
        diagnostics.extend(result.diagnostics)
        current_stage = pass_class.output_stage
        if result.output is None:
            if result.errors:
                return PipelineResult(
                    family=family,
                    stage=current_stage,
                    output=None,
                    diagnostics=tuple(diagnostics),
                )
            raise PipelineExecutionError(
                f"pass {pass_class.name!r} produced no output for "
                f"required stage {current_stage.value!r}"
            )
        current_value = result.output

    if current_stage != target_stage:
        raise PipelineRegistryError(
            f"pipeline stopped at {current_stage.value!r}, "
            f"not requested target {target_stage.value!r}"
        )
    return PipelineResult(
        family=family,
        stage=current_stage,
        output=current_value,
        diagnostics=tuple(diagnostics),
    )
