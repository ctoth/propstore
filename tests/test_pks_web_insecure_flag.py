from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def test_web_rejects_public_bind_without_insecure_flag(tmp_path, monkeypatch) -> None:
    import propstore.cli.web as web_cli

    repo = Repository.init(tmp_path / "knowledge")
    calls: list[tuple[object, str, int]] = []

    def fake_run_web_server(app, *, host: str, port: int) -> None:
        calls.append((app, host, port))

    monkeypatch.setattr(web_cli, "run_web_server", fake_run_web_server)

    result = CliRunner().invoke(
        cli,
        ["-C", str(repo.root), "web", "--host", "0.0.0.0", "--port", "8765"],
    )

    assert result.exit_code != 0
    assert calls == []
    assert "public network interface" in result.output
    assert "--insecure" in result.output


def test_web_allows_public_bind_with_insecure_warning(tmp_path, monkeypatch) -> None:
    import propstore.cli.web as web_cli

    repo = Repository.init(tmp_path / "knowledge")
    calls: list[tuple[object, str, int]] = []

    def fake_run_web_server(app, *, host: str, port: int) -> None:
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
            "--port",
            "8765",
            "--insecure",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][1:] == ("0.0.0.0", 8765)
    assert "WARNING" in result.output
    assert "0.0.0.0" in result.output


def test_web_loopback_bind_does_not_require_insecure(tmp_path, monkeypatch) -> None:
    import propstore.cli.web as web_cli

    repo = Repository.init(tmp_path / "knowledge")
    calls: list[tuple[object, str, int]] = []

    def fake_run_web_server(app, *, host: str, port: int) -> None:
        calls.append((app, host, port))

    monkeypatch.setattr(web_cli, "run_web_server", fake_run_web_server)

    result = CliRunner().invoke(
        cli,
        ["-C", str(repo.root), "web", "--host", "127.0.0.1", "--port", "8765"],
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert "WARNING" not in result.output
