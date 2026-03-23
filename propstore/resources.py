"""Resource loading for development and installed modes.

Pattern from polyarray: uses importlib.resources for installed packages,
direct Path access for development (source tree).

Resources live in propstore/_resources/.
"""
from __future__ import annotations

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


def _get_resource_root() -> Path:
    """Get root resource directory.

    Development: Path("<repo>/propstore/_resources")
    Installed: importlib.resources.files("propstore") / "_resources"
    """
    if _is_development_mode():
        return Path(__file__).resolve().parent / "_resources"
    else:
        from importlib.resources import files
        # files() returns a Traversable; for our JSON use case we need
        # as_posix() compatible access, but read_text works on both.
        return files("propstore") / "_resources"  # type: ignore[return-value] # Traversable is not Path; works at runtime via duck typing


def load_resource_text(relative_path: str) -> str:
    """Load a resource file as text.

    Args:
        relative_path: Path relative to propstore/_resources/
                      Example: "physgen_units.json"
    """
    root = _get_resource_root()
    resource = root.joinpath(relative_path)
    return resource.read_text(encoding="utf-8")


def resource_exists(relative_path: str) -> bool:
    """Check if a resource exists."""
    root = _get_resource_root()
    resource = root.joinpath(relative_path)
    return resource.is_file()
