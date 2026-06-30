from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli, compiler_cmds


def _raise_value_error(*_args, **_kwargs) -> None:
    raise ValueError("'is_a' is not a valid GraphRelationType")


def test_root_cli_renders_known_runtime_errors_without_traceback(monkeypatch) -> None:
    monkeypatch.setattr(compiler_cmds, "build_repository", _raise_value_error)

    result = CliRunner().invoke(cli, ["build"])

    assert result.exit_code == 1
    assert "Error: 'is_a' is not a valid GraphRelationType" in result.output
    assert "Hint: rerun with --traceback or PKS_TRACEBACK=1" in result.output
    assert "Traceback" not in result.output


def test_root_cli_traceback_env_disables_error_wrapper(monkeypatch) -> None:
    monkeypatch.setattr(compiler_cmds, "build_repository", _raise_value_error)

    result = CliRunner().invoke(cli, ["build"], env={"PKS_TRACEBACK": "1"})

    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
    assert "Hint: rerun with --traceback" not in result.output


def test_root_cli_traceback_flag_disables_error_wrapper(monkeypatch) -> None:
    monkeypatch.setattr(compiler_cmds, "build_repository", _raise_value_error)

    result = CliRunner().invoke(cli, ["--traceback", "build"])

    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
    assert "Hint: rerun with --traceback" not in result.output
