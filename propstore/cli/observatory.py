"""pks observatory - run epistemic observatory fixtures.

Thin Click adapter over :func:`propstore.observatory.evaluate_scenarios`: loads
scenario fixtures (one :class:`~propstore.observatory.EvaluationScenario` JSON
object per ``--fixture`` file), runs them through the deterministic harness, and
renders the resulting :class:`~propstore.observatory.ObservatoryReport`. No
evaluation logic lives here (CLAUDE.md "CLI adapter discipline").
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeGuard

import click

from propstore.cli.helpers import fail
from propstore.cli.output import emit
from propstore.observatory import (
    EvaluationScenario,
    ObservatoryReport,
    evaluate_scenarios,
)


@click.group()
def observatory() -> None:
    """Run epistemic observatory fixtures."""


@observatory.command("run")
@click.option(
    "--fixture",
    "fixture_paths",
    multiple=True,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Scenario fixture JSON file (repeatable).",
)
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(("json", "text")),
    show_default=True,
)
def run_cmd(fixture_paths: tuple[Path, ...], output_format: str) -> None:
    """Run scenario fixtures through the observatory harness."""
    scenarios = tuple(_load_scenario(path) for path in fixture_paths)
    report = evaluate_scenarios(scenarios)
    if output_format == "json":
        emit(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    emit(_render_text(report))


def _is_scenario_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    """JSON boundary: ``json.loads`` yields str-keyed objects, so a decoded mapping
    is the typed scenario payload. This is the one documented untyped-payload check.
    """
    return isinstance(value, Mapping)


def _load_scenario(path: Path) -> EvaluationScenario:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON: {exc}")
    if not _is_scenario_mapping(raw):
        fail(f"{path}: fixture must contain one scenario object")
    return EvaluationScenario.from_dict(raw)


def _render_text(report: ObservatoryReport) -> str:
    lines = [
        f"observatory report: {len(report.scenario_results)} scenarios",
        f"content hash: {report.content_hash}",
    ]
    for result in report.scenario_results:
        status = "pass" if result.passed else "fail"
        lines.append(
            f"{status}: {result.scenario_id} "
            f"operator={result.operator_family} policy={result.policy_id}"
        )
    return "\n".join(lines)
