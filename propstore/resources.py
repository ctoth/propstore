"""Resource loading for development and installed modes.

Shipped data lives in ``propstore/_resources``. In a source checkout we read it
through the filesystem; once installed as a wheel we read it through
``importlib.resources``. Both code paths return a handle exposing ``read_text``
and ``is_file``, so the public helpers are mode-agnostic.
"""

from __future__ import annotations

from importlib.resources.abc import Traversable
from pathlib import Path

_development_mode: bool | None = None


def _is_development_mode() -> bool:
    """Detect whether we are running from a source tree (vs an installed wheel)."""

    global _development_mode
    if _development_mode is not None:
        return _development_mode
    repo_root = Path(__file__).resolve().parent.parent
    _development_mode = (repo_root / ".git").exists()
    return _development_mode


def _resource(relative_path: str) -> Path | Traversable:
    if _is_development_mode():
        return Path(__file__).resolve().parent / "_resources" / relative_path
    from importlib.resources import files

    return files("propstore").joinpath("_resources", relative_path)


def load_resource_text(relative_path: str) -> str:
    """Return the text of ``propstore/_resources/<relative_path>``."""

    return _resource(relative_path).read_text(encoding="utf-8")


def resource_exists(relative_path: str) -> bool:
    """Return whether ``propstore/_resources/<relative_path>`` is a file."""

    return _resource(relative_path).is_file()


def iter_resource_files(relative_path: str) -> list[str]:
    """Return the sorted file names directly under ``_resources/<relative_path>``.

    Works in both source-tree (``Path``) and installed-wheel (``Traversable``)
    modes; only immediate children that are files are returned.
    """

    base = _resource(relative_path)
    return sorted(child.name for child in base.iterdir() if child.is_file())
