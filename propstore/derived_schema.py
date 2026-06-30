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

1. **Single live schema (mapper-reset caveat).** ``build_sqlalchemy_schema``
   resets the global SQLAlchemy mapper registry, so a process holds exactly one
   live schema at a time. Build the schema **once** at the top of a build and
   thread that one object through every step; never rebuild it mid-build (a
   rebuild silently invalidates the mappers of any earlier instance you still
   hold). Read the schema hash off the threaded instance (``schema.catalog_hash``)
   rather than building a second schema to hash it.

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
    """Build the one charter-derived multi-family sidecar schema.

    Builds a fresh schema from every registered charter. Per the mapper-reset
    caveat above, call this **once** per build and thread the returned object;
    do not rebuild while holding a previous instance.
    """

    return build_sqlalchemy_schema(charter_catalog(*registered_charters()))
