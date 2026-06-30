"""propstore entity families.

Each domain entity is ONE quire charter class (``@charter`` on a ``CharterDoc``
subclass). Its storage column projection, SQLAlchemy model, and serialized
document contract all fall out of the field annotations — there is no separately
authored DTO/Record/Row/payload layer. See CLAUDE.md and PLAN.md.

Cross-family references are declared as :class:`quire.references.ForeignKeySpec`
annotations directly on the referencing charter field (via ``charter_field``).
The family registry's foreign-key graph is *derived* from those field
annotations (``quire.charters.registry_from_charters``); there is no separate
hand-authored foreign-key table. ``SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION`` is the
one contract version every such cross-family reference is versioned under, kept
here so each family module shares the single canonical value.
"""

from __future__ import annotations

from quire.contracts import contract_version

SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = contract_version("2026.06.29")

__all__ = ["SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION"]
