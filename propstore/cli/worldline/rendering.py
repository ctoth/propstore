"""CLI-local worldline rendering helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from propstore.worldline.definition import WorldlineResult
from propstore.worldline.result_types import WorldlineTargetValue


def format_target_value_line(
    target: str,
    value: WorldlineTargetValue,
    *,
    include_details: bool,
) -> str:
    if value.value is None:
        reason = value.reason or ""
        return f"{target}: {value.status} \u2014 {reason}"

    source = value.source or ""
    line = f"{target}: {value.value} ({value.status}, {source})"
    if include_details and value.formula:
        line += f" via {value.formula}"
    if include_details and value.winning_claim_id:
        line += f" [winner: {value.winning_claim_id}]"
    return line


def target_value_lines(
    values: Mapping[str, WorldlineTargetValue],
    *,
    include_details: bool,
) -> Iterable[str]:
    for target, value in values.items():
        yield format_target_value_line(target, value, include_details=include_details)


def derivation_trace_lines(result: WorldlineResult) -> Iterable[str]:
    for step in result.steps:
        extra = ""
        if step.claim_id:
            extra = f" [claim: {step.claim_id}]"
        if step.formula:
            extra = f" via {step.formula}"
        yield f"{step.concept} = {step.value} ({step.source}){extra}"


def sensitivity_lines(result: WorldlineResult) -> Iterable[str]:
    if result.sensitivity is None:
        return
    for concept, outcome in result.sensitivity.targets.items():
        if outcome.error is not None:
            yield f"{concept}: ERROR \u2014 {outcome.error}"
            continue
        for entry in outcome.entries:
            yield (
                f"{concept}: d/d({entry.input_name}) = {entry.partial_derivative}, "
                f"elasticity = {entry.elasticity}"
            )
