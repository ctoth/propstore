"""propstore entity families.

Each domain entity is ONE quire charter class (``@charter`` on a ``CharterDoc``
subclass). Its storage column projection, SQLAlchemy model, and serialized
document contract all fall out of the field annotations — there is no separately
authored DTO/Record/Row/payload layer. See CLAUDE.md and PLAN.md.
"""

from __future__ import annotations
