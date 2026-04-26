"""pks observatory - run epistemic observatory fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from propstore.app.observatory import AppObservatoryRunRequest, run_observatory
from propstore.cli.output import emit
from propstore.observatory import EvaluationScenario, ObservatoryReport
from propstore.repository import Repository


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
)
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(("json", "text")),
    show_default=True,
)
@click.pass_obj
def run_cmd(obj: dict[str, Any], fixture_paths: tuple[Path, ...], output_format: str) -> None:
    """Run scenario fixtures through the observatory harness."""
    repo: Repository = obj["repo"]
    request = AppObservatoryRunRequest(
        scenarios=tuple(_load_scenario(path) for path in fixture_paths)
    )
    report = run_observatory(repo, request)
    if output_format == "json":
        emit(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    emit(_render_text(report))


def _load_scenario(path: Path) -> EvaluationScenario:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise click.ClickException(f"{path}: fixture must contain one scenario object")
    try:
        return EvaluationScenario.from_dict(raw)
    except ValueError as exc:
        raise click.ClickException(f"{path}: {exc}") from exc


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


__all__ = ["observatory", "run_observatory"]
