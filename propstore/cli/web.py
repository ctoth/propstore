"""CLI command for serving the propstore web adapter."""

from __future__ import annotations

from typing import Any
from webbrowser import open as open_browser_url

import click


@click.command("web")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host interface to bind.")
@click.option(
    "--insecure",
    is_flag=True,
    help="Allow serving without authentication on a public network interface.",
)
@click.option(
    "--port",
    default=8000,
    show_default=True,
    type=click.IntRange(1, 65535),
    help="TCP port to bind.",
)
@click.option("--open", "open_browser", is_flag=True, help="Open the web UI in a browser.")
@click.pass_obj
def web(
    obj: dict[str, Any],
    host: str,
    insecure: bool,
    port: int,
    open_browser: bool,
) -> None:
    """Serve the read-only propstore web UI."""
    if _is_public_bind(host) and not insecure:
        raise click.ClickException(
            "Refusing to serve propstore on a public network interface without "
            "--insecure. Bind to 127.0.0.1 or pass --insecure to acknowledge "
            "the no-auth public-bind risk."
        )
    repo = obj["repo"]
    repository_root = repo.root
    app = create_web_app(repository_root=repository_root)
    url = _display_url(host, port)
    if _is_public_bind(host):
        click.echo(
            f"WARNING: serving propstore with no auth on {host}.",
            err=True,
        )
    click.echo(f"Serving propstore web UI for {repository_root}")
    click.echo(f"Open {url}")
    click.echo(f"Claim view: {url}/claim/<claim_id>")
    click.echo(f"Neighborhood view: {url}/claim/<claim_id>/neighborhood")
    if open_browser:
        open_browser_url(url)
    run_web_server(app, host=host, port=port)


def create_web_app(*, repository_root):
    from propstore.web.app import create_app

    return create_app(repository_root=repository_root)


def run_web_server(app, *, host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def _display_url(host: str, port: int) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{port}"


def _is_public_bind(host: str) -> bool:
    return host not in {"127.0.0.1", "::1", "localhost"}
