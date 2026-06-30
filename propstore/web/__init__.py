"""Web presentation adapter package for propstore.

The web layer is the top of the presentation stack (CLAUDE.md "Architectural
Layers"): the FastAPI routes parse query parameters into typed app requests,
call the Phase-10-0 owner-layer view-builders in :mod:`propstore.app`, and render
the returned typed reports as JSON or accessible HTML. The routes own no domain
semantics — every render policy is built through
:func:`propstore.app.rendering.build_render_policy` and every world read goes
through :func:`propstore.app.world.open_app_world_model`. Nothing in the owner
layers imports this package; only the ``pks web`` launcher in the CLI does.
"""

from __future__ import annotations

__all__: list[str] = []
