"""Embedding derived-index helpers over quire's vector adapter.

This is not a charter family — the embedding index is a *lazy, separate* store, so
it is deliberately kept out of the world-sidecar charter schema (declaring vector
caches there would force ``sqlite_vec`` to load on every sidecar build/read and
break the core-without-extra contract). The vector tables are created on demand
and the ``sqlite_vec`` extension is loaded lazily, only when an embedding feature
is actually invoked.
"""

from __future__ import annotations
