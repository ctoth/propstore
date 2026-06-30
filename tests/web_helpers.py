"""Shared TestClient builder for the Phase 10-2 web-route tests.

Builds the demo corpus through :func:`tests.app_render_helpers.build_demo_repo`
and wraps a FastAPI ``TestClient`` around the read-only web app pointed at it.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from propstore.web.app import create_app
from tests.app_render_helpers import build_demo_repo


def demo_client(tmp_path: Path) -> TestClient:
    repo = build_demo_repo(tmp_path)
    return TestClient(create_app(repository_root=repo.root))
