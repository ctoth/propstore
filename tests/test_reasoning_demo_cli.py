from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from propstore.demo import materialize_reasoning_demo


def _materialize_demo(tmp_path):
    root = tmp_path / "knowledge"
    materialize_reasoning_demo(root)
    return root


def test_reasoning_demo_grounding_status(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "grounding", "status"])

    assert result.exit_code == 0, result.output
    assert "Grounding surface: ready" in result.output
    assert "Facts: 1" in result.output
    assert "definitely: 1" in result.output
    assert "defeasibly: 2" in result.output


def test_reasoning_demo_grounding_show_and_query(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    show_result = runner.invoke(cli, ["-C", str(root), "grounding", "show"])

    assert show_result.exit_code == 0, show_result.output
    assert "Facts (1):" in show_result.output
    assert "bird(tweety)" in show_result.output
    assert "Grounded rules (1):" in show_result.output
    assert "r_flies_from_bird: flies(tweety) -< bird(tweety)" in show_result.output
    assert "definitely:" in show_result.output
    assert "defeasibly:" in show_result.output

    query_result = runner.invoke(
        cli,
        ["-C", str(root), "grounding", "query", "flies(tweety)"],
    )

    assert query_result.exit_code == 0, query_result.output
    assert "flies(tweety)" in query_result.output
    assert "status: defeasibly" in query_result.output


def test_reasoning_demo_grounding_arguments(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "grounding", "arguments"])

    assert result.exit_code == 0, result.output
    assert "Arguments (" in result.output
    assert "bird(tweety) <= fact" in result.output
    assert "flies(tweety) <= r_flies_from_bird" in result.output


def test_reasoning_demo_grounding_explain(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["-C", str(root), "grounding", "explain", "flies(tweety)"],
    )

    assert result.exit_code == 0, result.output
    assert "status: defeasibly" in result.output
    assert "Textual explanation:" in result.output
    assert "flies(tweety) is YES." in result.output
    assert "via r_flies_from_bird" in result.output
    assert "Dialectical tree:" in result.output


def test_reasoning_demo_build_and_world_extensions(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    build_result = runner.invoke(cli, ["-C", str(root), "build"])
    assert build_result.exit_code == 0, build_result.output
    assert root.joinpath("sidecar", "propstore.sqlite").exists()

    extensions_result = runner.invoke(
        cli,
        ["-C", str(root), "world", "extensions", "--backend", "aspic"],
    )

    assert extensions_result.exit_code == 0, extensions_result.output
    assert "Backend: aspic" in extensions_result.output
    assert "Accepted (2 claims):" in extensions_result.output
    assert "flight_score = 1.0" in extensions_result.output
    assert "flight_score = 0.0" in extensions_result.output


def test_reasoning_demo_worldline_run_and_show(tmp_path) -> None:
    root = _materialize_demo(tmp_path)

    runner = CliRunner()
    build_result = runner.invoke(cli, ["-C", str(root), "build"])
    assert build_result.exit_code == 0, build_result.output

    run_result = runner.invoke(
        cli,
        [
            "-C",
            str(root),
            "worldline",
            "run",
            "demo",
            "--target",
            "flight_score",
            "--strategy",
            "argumentation",
            "--reasoning-backend",
            "aspic",
        ],
    )

    assert run_result.exit_code == 0, run_result.output
    assert "flight_score: 1.0 (resolved, resolved)" in run_result.output
    assert root.joinpath("sidecar", "propstore.sqlite").exists()

    show_result = runner.invoke(cli, ["-C", str(root), "worldline", "show", "demo"])

    assert show_result.exit_code == 0, show_result.output
    assert "flight_score: 1.0 (resolved, resolved)" in show_result.output
    assert "[winner: claim_can_fly]" in show_result.output
    assert "Defeated claims:" in show_result.output
