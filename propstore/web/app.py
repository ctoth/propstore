"""FastAPI application construction for the web adapter."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI


def create_app(*, repository_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="propstore.web")
    app.state.repository_root = repository_root

    from propstore.web.routing import register_routes

    register_routes(app)
    return app
