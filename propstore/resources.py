"""Resource loading for development and installed modes.

Pattern from polyarray: uses importlib.resources for installed packages,
direct Path access for development (source tree).

Resources live in propstore/_resources/.
"""
from __future__ import annotations

import json
from importlib.resources.abc import Traversable
from pathlib import Path


_DEVELOPMENT_MODE: bool | None = None


def _is_development_mode() -> bool:
    """Detect if running from source tree vs installed package."""
    global _DEVELOPMENT_MODE
    if _DEVELOPMENT_MODE is not None:
        return _DEVELOPMENT_MODE

    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent
    _DEVELOPMENT_MODE = (repo_root / ".git").exists()
    return _DEVELOPMENT_MODE


def _development_resource(relative_path: str) -> Path:
    return Path(__file__).resolve().parent / "_resources" / relative_path


def _installed_resource(relative_path: str) -> Traversable:
    from importlib.resources import files

    return files("propstore").joinpath("_resources", relative_path)


def _get_resource(relative_path: str) -> Path | Traversable:
    """Get a resource handle for development or installed mode."""
    if _is_development_mode():
        return _development_resource(relative_path)
    return _installed_resource(relative_path)


def load_resource_text(relative_path: str) -> str:
    """Load a resource file as text.

    Args:
        relative_path: Path relative to propstore/_resources/
                      Example: "physgen_units.json"
    """
    resource = _get_resource(relative_path)
    return resource.read_text(encoding="utf-8")


def load_resource_json(relative_path: str) -> dict | list:
    """Load a JSON resource from ``propstore/_resources``."""
    return json.loads(load_resource_text(relative_path))


def resource_exists(relative_path: str) -> bool:
    """Check if a resource exists."""
    resource = _get_resource(relative_path)
    return resource.is_file()
