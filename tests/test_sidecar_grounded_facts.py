"""The raw-sqlite grounded_fact sidecar: populate / read / integrity / round-trip."""

from __future__ import annotations

import json
import sqlite3

import gunray
import pytest

from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import GroundedRulesBundle, SECTION_NAMES
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.sidecar import (
    create_grounded_fact_table,
    populate_grounded_facts,
    read_grounded_facts,
)


def _bundle() -> GroundedRulesBundle:
    rules = (
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="flies", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(predicate="bird", terms=(Term(kind="var", name="X"),)),
                ),
            ),
        ),
    )
    facts = (gunray.GroundAtom(predicate="bird", arguments=("tweety",)),)
    return ground(rules, facts, PredicateRegistry.from_documents(()))


def _total_rows(bundle: GroundedRulesBundle) -> int:
    return sum(len(rows) for inner in bundle.sections.values() for rows in inner.values())


def test_populate_returns_row_count() -> None:
    bundle = _bundle()
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    assert populate_grounded_facts(conn, bundle) == _total_rows(bundle)


def test_read_returns_all_four_keys() -> None:
    bundle = _bundle()
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)
    read = read_grounded_facts(conn)
    assert set(read.keys()) == set(SECTION_NAMES)


def test_round_trip_matches_bundle_sections() -> None:
    bundle = _bundle()
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, bundle)
    read = read_grounded_facts(conn)
    assert {name: dict(inner) for name, inner in read.items()} == {
        name: dict(inner) for name, inner in bundle.sections.items()
    }


def test_empty_bundle_writes_no_rows_but_reads_four_keys() -> None:
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    assert populate_grounded_facts(conn, GroundedRulesBundle.empty()) == 0
    read = read_grounded_facts(conn)
    assert set(read.keys()) == set(SECTION_NAMES)
    assert all(read[name] == {} for name in SECTION_NAMES)


def test_primary_key_rejects_duplicate_row() -> None:
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    conn.execute(
        "INSERT INTO grounded_fact (predicate, arguments, section) VALUES (?, ?, ?)",
        ("bird", json.dumps(["tweety"]), "yes"),
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO grounded_fact (predicate, arguments, section) VALUES (?, ?, ?)",
            ("bird", json.dumps(["tweety"]), "yes"),
        )


def test_same_atom_in_different_sections_coexists() -> None:
    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    for section in ("yes", "no"):
        conn.execute(
            "INSERT INTO grounded_fact (predicate, arguments, section) VALUES (?, ?, ?)",
            ("bird", json.dumps(["tweety"]), section),
        )
    read = read_grounded_facts(conn)
    assert ("tweety",) in read["yes"]["bird"]
    assert ("tweety",) in read["no"]["bird"]


def test_populate_without_table_raises_operational_error() -> None:
    conn = sqlite3.connect(":memory:")
    with pytest.raises(sqlite3.OperationalError):
        populate_grounded_facts(conn, _bundle())
