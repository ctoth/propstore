"""Charter-derived multi-family world-sidecar schema.

The world sidecar's SQL schema is **not** hand-authored. It falls out of the
charter foreign-key graph: ``build_sqlalchemy_schema(charter_catalog(*registered
charters))`` derives every table, column, and foreign key from the
``@charter``-decorated document classes (see
:mod:`propstore.families.registry`). The reference tree's ~33-table
``projection_catalog.py`` plus the per-family ``compile_*_sidecar_rows`` /
``populate_*`` projection mass therefore vanishes — *the projection is the
charter*. A per-row projection is just ``session.add_family(name, {charter
fields})``.

Two load-bearing constraints govern callers:

1. **Schema-local mappings.** ``build_sqlalchemy_schema`` gives every schema its
   own mapper registry and mapped subclasses. Authored charter models remain the
   behavior owners; SQL reads and writes obtain the mapped row class from the
   schema. Build code still threads one schema through a build so every step uses
   the same catalog and schema hash.

2. **Quarantine, not reject (Z1).** The derived schema emits real SQL foreign
   keys (some non-nullable). A build that aborted on a dangling reference would
   violate the non-commitment discipline. The build writes with
   ``writable_session(..., enforce_foreign_keys=False)`` so foreign keys are
   *advisory* during population: a dangling reference inserts as a blocked row
   plus a diagnostic instead of raising ``IntegrityError``. The reader opens with
   enforcement on; ``PRAGMA foreign_keys`` governs mutations, not ``SELECT``.
"""

from __future__ import annotations

from quire.charters import charter_catalog
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema

from propstore.families.registry import registered_charters

WORLD_SIDECAR_SCHEMA_VERSION = 1
"""Bumped when the charter-derived schema shape changes incompatibly.

This feeds the derived-store cache key (``derived_build``) so a schema-shape
change invalidates every cached sidecar.
"""


def build_world_sidecar_schema() -> SqlAlchemySchema:
    """Build a charter-derived multi-family sidecar schema."""

    return build_sqlalchemy_schema(charter_catalog(*registered_charters()))
