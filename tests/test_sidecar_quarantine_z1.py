"""Z1 standing gate: the charter-derived sidecar quarantines dangling refs.

gaps.md Z1 / PLAN §12.1: the multi-charter build sidecar must **quarantine** a
dangling foreign-key reference (insert it as a blocked row + diagnostic so render
policy can decide) rather than let a hard SQL FK constraint **reject** it and
abort the build. The charter-derived schema emits real SQL foreign keys — two of
them non-nullable (``rule_superiority.superior_rule_id`` /
``inferior_rule_id`` -> ``defeasible_rule``; ``micropublication.context_id`` ->
``context``) — and quire enforces foreign keys by default. So the build must
populate with foreign-key enforcement **off** (advisory FKs); this test pins both
halves of that decision against the real propstore charter schema.

These two tests are the RED->GREEN gate for the Z1 mechanism:

* ``test_default_enforcement_would_reject`` documents the hazard: under the
  default (enforcing) write path a dangling ref raises ``IntegrityError`` and
  would abort the whole build. This is what Z1 forbids the build from doing.
* ``test_advisory_write_quarantines_dangling_ref`` proves the fix: the same
  dangling ref inserts under the advisory write path and is visible to the
  reader, so the build proceeds and render policy decides.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from quire.sqlalchemy_store import (
    create_sqlalchemy_store,
    readonly_session,
    writable_session,
)

from propstore.derived_schema import build_world_sidecar_schema


def _valid_rule_values(rule_id: str) -> dict[str, object]:
    return {
        "rule_id": rule_id,
        "kind": "defeasible",
        "head": "p",
        "body": "q",
    }


def _superiority_values(
    superiority_id: str, superior_rule_id: str, inferior_rule_id: str
) -> dict[str, object]:
    return {
        "superiority_id": superiority_id,
        "superior_rule_id": superior_rule_id,
        "inferior_rule_id": inferior_rule_id,
    }


def test_default_enforcement_would_reject(tmp_path: Path) -> None:
    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)

    with pytest.raises(IntegrityError):
        with writable_session(store, schema) as session:
            session.add_family("defeasible_rule", _valid_rule_values("rule:1"))
            # superior_rule_id points at a rule that does not exist.
            session.add_family(
                "rule_superiority",
                _superiority_values("sup:1", "rule:missing", "rule:1"),
            )
            session.commit()


def test_advisory_write_quarantines_dangling_ref(tmp_path: Path) -> None:
    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)

    with writable_session(store, schema, enforce_foreign_keys=False) as session:
        session.add_family("defeasible_rule", _valid_rule_values("rule:1"))
        # A well-formed superiority (both refs resolve) and a dangling one.
        session.add_family(
            "rule_superiority",
            _superiority_values("sup:valid", "rule:1", "rule:1"),
        )
        session.add_family(
            "rule_superiority",
            _superiority_values("sup:blocked", "rule:missing", "rule:1"),
        )
        session.commit()

    with readonly_session(store, schema) as session:
        rows = session.session.execute(
            text(
                "SELECT superiority_id, superior_rule_id FROM rule_superiority "
                "ORDER BY superiority_id"
            )
        ).all()
    assert [(row[0], row[1]) for row in rows] == [
        ("sup:blocked", "rule:missing"),
        ("sup:valid", "rule:1"),
    ]
