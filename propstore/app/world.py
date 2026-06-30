"""Application-layer world opener for the render view tier.

The view-builders take an already-open :class:`~propstore.world.WorldQuery`; this
module is the one place the app layer *opens* one over a repository, lowering the
"sidecar not built yet" :class:`FileNotFoundError` into the typed
:class:`WorldSidecarMissingError` the adapters and the repository-overview report
recognise. Opening is kept separate from viewing so the builders stay pure
``(world, policy) -> report`` functions.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from propstore.world import WorldQuery

if TYPE_CHECKING:
    from propstore.repository import Repository


class WorldAppError(Exception):
    """Base class for expected app-layer world failures."""


class WorldSidecarMissingError(WorldAppError):
    """Raised when the world sidecar has not been built yet."""

    def __init__(self) -> None:
        super().__init__("Sidecar not found. Run 'pks build' first.")


@contextmanager
def open_app_world_model(repo: Repository) -> Iterator[WorldQuery]:
    """Open a :class:`WorldQuery` over ``repo`` for the lifetime of the context.

    A not-yet-built sidecar surfaces as :class:`WorldSidecarMissingError` (its
    cause — "run pks build" — is preserved, never collapsed to an empty result).
    """

    try:
        world = WorldQuery(repo)
    except FileNotFoundError as exc:
        raise WorldSidecarMissingError() from exc
    try:
        yield world
    finally:
        world.close()
