"""Phase 10-2: the ``pks web`` launcher command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def test_root_help_lists_web_command() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "web" in result.output
    assert "Serve the propstore web UI." in result.output


def test_web_command_serves_current_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import propstore.cli.web as web_cli

    repo = Repository.init(tmp_path / "knowledge")
    calls: list[tuple[object, str, int]] = []

    def fake_run_web_server(app: object, *, host: str, port: int) -> None:
        calls.append((app, host, port))

    monkeypatch.setattr(web_cli, "run_web_server", fake_run_web_server)

    result = CliRunner().invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "web",
            "--host",
            "0.0.0.0",
            "--insecure",
            "--port",
            "8765",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    app, host, port = calls[0]
    assert app.state.repository_root == repo.root
    assert host == "0.0.0.0"
    assert port == 8765
    assert f"Serving propstore web UI for {repo.root}" in result.output
    assert "Open http://127.0.0.1:8765" in result.output
    assert "Claim view: http://127.0.0.1:8765/claim/<claim_id>" in result.output
