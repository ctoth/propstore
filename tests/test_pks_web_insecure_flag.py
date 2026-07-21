"""Phase 10-2: ``pks web`` public-bind refusal unless ``--insecure``."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def _install_fake_server(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[object, str, int]]:
    import propstore.cli.web as web_cli

    calls: list[tuple[object, str, int]] = []

    def fake_run_web_server(app: object, *, host: str, port: int) -> None:
        calls.append((app, host, port))

    monkeypatch.setattr(web_cli, "run_web_server", fake_run_web_server)
    return calls


def test_web_rejects_public_bind_without_insecure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    calls = _install_fake_server(monkeypatch)

    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "web", "--host", "0.0.0.0", "--port", "8765"]
    )

    assert result.exit_code != 0
    assert calls == []
    assert "public network interface" in result.output
    assert "--insecure" in result.output


def test_web_allows_public_bind_with_insecure_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    calls = _install_fake_server(monkeypatch)

    result = CliRunner().invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "web",
            "--host",
            "0.0.0.0",
            "--port",
            "8765",
            "--insecure",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][1:] == ("0.0.0.0", 8765)
    assert "WARNING" in result.output


def test_web_loopback_bind_does_not_require_insecure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    calls = _install_fake_server(monkeypatch)

    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "web", "--host", "127.0.0.1", "--port", "8765"]
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert "WARNING" not in result.output
