"""FastAPI application construction for the web adapter."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app(*, repository_root: Path | None = None) -> FastAPI:
    """Build the read-only propstore web app rooted at ``repository_root``.

    The root is stashed on ``app.state`` and resolved per-request through
    :meth:`propstore.repository.Repository.find`, so the same app object serves
    whichever repository it was pointed at without holding an open handle.
    """

    app = FastAPI(title="propstore.web")
    app.state.repository_root = repository_root
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).with_name("static")),
        name="static",
    )

    from propstore.web.routing import register_routes

    register_routes(app)
    return app
