"""Worldline query definitions and materialization entrypoints.

This package ``__init__`` is deliberately **shallow**. The worldline charter
(``definition``) and its payload types (``query``, ``result_types``,
``revision_types``) are storage-pure — ``propstore.families.registry`` imports
the charter, so the storage layer reaches them — while ``runner`` and
``argumentation`` sit up in the world layer. Re-exporting the runner from here
would make importing *any* worldline module drag in ``propstore.world``, which
both breaks the layering contract and creates a genuine circular import
(``world.types`` imports the worldline result view).

Import the concrete module that owns the behavior:

    from propstore.worldline.definition import WorldlineDefinition
    from propstore.worldline.runner import run_worldline
"""

from __future__ import annotations
