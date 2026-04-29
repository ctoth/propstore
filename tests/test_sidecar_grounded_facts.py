"""Tests for sidecar grounded-facts persistence — chunk 1.6a (red).

These tests describe the contract for a new sidecar module that
persists the four gunray sections (``definitely`` / ``defeasibly`` /
``not_defeasibly`` / ``undecided``) from a
``propstore.grounding.bundle.GroundedRulesBundle`` into the sidecar's
SQLite store.

Target module: ``propstore.sidecar.rules`` (new). Chosen over
extending ``propstore.sidecar.claims`` because the existing sidecar
convention is one topic module per subsystem (``claims.py``,
``concepts.py``, ``sources.py``); grounded facts are their own topic
and deserve their own module. Schema creation helper also lives in
``propstore.sidecar.rules`` to keep the grounded-fact table colocated
with the functions that write and read it.

None of the target symbols exist yet — every import of
``propstore.sidecar.rules`` is deferred into test/strategy bodies so
pytest can *collect* this file cleanly while every test fails at run
time with ``ModuleNotFoundError``. That is the contract for this
chunk's RED commit.

Phase 1 scope: persist only ``grounded_facts`` (the four sections).
Ground rule instances stay in-memory via the bundle for Chunk 1.7
(bridge). Section persistence across the four keys and full
round-trip of the sections map is what these tests pin down.

Non-commitment discipline anchor (project CLAUDE.md): storage never
silently collapses a verdict. Every section is persistable, every
section is readable back, empty inner maps for sections that contain
no rows.

Theoretical sources:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is
      a finite set of ground atoms keyed by predicate id. The
      grounded-fact table stores one row per ground atom per section,
      with the argument tuple JSON-encoded so the SQLite primary key
      ``(predicate, arguments, section)`` enforces set semantics.
    - Section 3 (Definition 9): grounding is a deterministic function
      of the program and its fact base. The round-trip property
      ``read(populate(bundle)) == bundle.sections`` therefore has to
      hold for *every* bundle — that is the determinism check pinned
      by the Hypothesis property test.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (pp.3-4): the canonical DeLP example is
      ``bird(tweety) ∈ Facts`` with the defeasible rule
      ``flies(X) -< bird(X)``. That example is re-used here as a
      concrete regression case: the sidecar must round-trip a bundle
      whose ``definitely`` section contains ``{bird: {(tweety,)}}``
      and whose ``defeasibly`` section contains both
      ``{bird: {(tweety,)}}`` and ``{flies: {(tweety,)}}``.
    - Section 4 (p.25): the four-valued answer system
      ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto the four section
      names. All four sections are required to round-trip, even when
      some are empty, because storage is forbidden from collapsing a
      verdict (non-commitment anchor).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import TYPE_CHECKING

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

if TYPE_CHECKING:
    from propstore.grounding.bundle import GroundedRulesBundle


# ---------------------------------------------------------------------------
# Deferred-import strategies and helpers.
#
# Every import of ``propstore.sidecar.rules`` and
# ``propstore.grounding.bundle`` happens inside a function body so that
# pytest *collection* does not fail even though the target module does
# not exist yet. Runtime execution will then raise
# ``ModuleNotFoundError`` on every test — which is the correct RED
# failure mode for chunk 1.6a.
# ---------------------------------------------------------------------------


def _fresh_conn_with_schema() -> sqlite3.Connection:
    """Return an in-memory SQLite connection with the grounded_fact table.

    Lives inside the tests (no fixtures, no conftest per the prompt
    constraints). Imports ``create_grounded_fact_table`` from the
    as-yet-unbuilt ``propstore.sidecar.rules`` module so every test
    using it fails with ``ModuleNotFoundError`` at runtime.

    Diller, Borg, Bex 2025 §3 Definition 7: a Datalog fact base is a
    finite set of ground atoms; the table stores one row per atom per
    section.
    """
    from propstore.sidecar.rules import create_grounded_fact_table

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    return conn


def _make_bundle(
    sections: Mapping[str, Mapping[str, frozenset[tuple[object, ...]]]],
) -> GroundedRulesBundle:
    """Construct a ``GroundedRulesBundle`` with empty source_rules / facts.

    Phase 1 scope (prompt §"Phase 1 scope"): only the ``sections`` map
    matters for persistence; the ``source_rules`` and ``source_facts``
    fields are carried through the bundle dataclass but are not part
    of the grounded-fact table contract.

    Diller, Borg, Bex 2025 §3: the ground model travels with the
    program; these tests exercise the ground-model half only.
    """
    from types import MappingProxyType

    from propstore.grounding.bundle import GroundedRulesBundle

    # Freeze the outer mapping so the bundle matches the shape that
    # ``grounder.ground`` produces (see
    # ``propstore.grounding.grounder._normalise_sections``).
    normalized: dict[str, Mapping[str, frozenset[tuple[object, ...]]]] = {}
    for name in ("yes", "no", "undecided", "unknown"):
        inner = sections.get(name, {})
        inner_frozen: dict[str, frozenset[tuple[object, ...]]] = {}
        for predicate_id, rows in inner.items():
            inner_frozen[predicate_id] = frozenset(rows)
        normalized[name] = MappingProxyType(inner_frozen)
    return GroundedRulesBundle(
        source_rules=(),
        source_facts=(),
        sections=MappingProxyType(normalized),
    )


# ---------------------------------------------------------------------------
# Hypothesis strategies.
# ---------------------------------------------------------------------------


# Scalar strategy matches ``argumentation.aspic.Scalar`` (and
# ``gunray.schema.Scalar``): ``str | int | float | bool``. Diller,
# Borg, Bex 2025 §3 Definition 7: ground terms are first-order
# constants; the Scalar union is propstore's concrete realisation.
_SCALAR: st.SearchStrategy[object] = st.one_of(
    st.text(
        alphabet=st.characters(
            min_codepoint=32, max_codepoint=126, blacklist_characters='"\\'
        ),
        min_size=1,
        max_size=6,
    ),
    st.integers(min_value=-100, max_value=100),
    st.booleans(),
    # Exclude NaN/Infinity so JSON round-trip is well-defined. Garcia &
    # Simari 2004 §4 non-commitment discipline: the persistence layer
    # must be lossless, which requires a deterministic value domain.
    st.floats(
        min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
    ),
)

_PREDICATE_NAME: st.SearchStrategy[str] = st.text(
    alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
    min_size=1,
    max_size=5,
)

_ARG_TUPLE: st.SearchStrategy[tuple[object, ...]] = st.lists(
    _SCALAR, min_size=0, max_size=3
).map(tuple)

_INNER_MAP: st.SearchStrategy[dict[str, frozenset[tuple[object, ...]]]] = st.dictionaries(
    _PREDICATE_NAME,
    st.lists(_ARG_TUPLE, min_size=0, max_size=3).map(frozenset),
    min_size=0,
    max_size=3,
)


def bundles_with_facts() -> st.SearchStrategy[GroundedRulesBundle]:
    """Strategy producing small ``GroundedRulesBundle`` instances.

    Phase 1: ``source_rules`` and ``source_facts`` are always empty —
    only the ``sections`` map matters for persistence (prompt
    §"Phase 1 scope"). The four gunray section keys are always
    present, per Garcia & Simari 2004 §4 (p.25) four-valued answer
    system and the non-commitment discipline anchor that every bundle
    exposes all four sections.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs; the round-trip property
    tests use this strategy to drive the ``populate`` → ``read``
    determinism check.
    """
    return st.fixed_dictionaries(
        {
            "yes": _INNER_MAP,
            "no": _INNER_MAP,
            "undecided": _INNER_MAP,
            "unknown": _INNER_MAP,
        }
    ).map(_make_bundle)


def _sections_as_plain_dict(
    bundle: GroundedRulesBundle,
) -> dict[str, dict[str, frozenset[tuple[object, ...]]]]:
    """Copy bundle.sections into a plain ``dict`` of ``dict`` for compare.

    The bundle wraps its outer and inner maps in ``MappingProxyType``
    (see ``propstore.grounding.grounder._normalise_sections``); the
    read function is allowed to return any ``Mapping`` shape, so the
    round-trip assertions compare through this normaliser.

    Diller, Borg, Bex 2025 §3 Definition 9: determinism is about
    value-equality of the ground model, not about the concrete
    ``Mapping`` subclass.
    """
    return {
        name: dict(inner.items()) for name, inner in bundle.sections.items()
    }


# ---------------------------------------------------------------------------
# Schema tests.
# ---------------------------------------------------------------------------


def test_grounded_fact_table_exists() -> None:
    """After creating the sidecar schema, the ``grounded_fact`` table
    exists with exactly the columns ``predicate``, ``arguments``,
    ``section``.

    Diller, Borg, Bex 2025 §3 Definition 7: the fact base is a set of
    ground atoms keyed by predicate id; the propstore sidecar realises
    that set as rows in ``grounded_fact`` with argument tuples
    JSON-encoded into a single ``TEXT`` column so SQLite's primary key
    mechanism can enforce set semantics across variable-arity atoms.
    """
    conn = _fresh_conn_with_schema()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='grounded_fact'"
        ).fetchall()
        assert rows == [("grounded_fact",)]

        columns = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA table_info(grounded_fact)").fetchall()
        }
        assert set(columns.keys()) == {"predicate", "arguments", "section"}
        assert columns["predicate"] == "TEXT"
        assert columns["arguments"] == "TEXT"
        assert columns["section"] == "TEXT"
    finally:
        conn.close()


def test_grounded_fact_table_primary_key_uniqueness() -> None:
    """Two inserts with identical ``(predicate, arguments, section)``
    raise ``sqlite3.IntegrityError``. The primary key enforces
    deduplication at the storage layer.

    Garcia & Simari 2004 §4 (p.25): each four-valued verdict is
    itself a set of ground atoms; duplicates within a verdict carry
    no additional information. The primary key hardens this set
    semantics so a careless re-populate cannot double-count.
    """
    conn = _fresh_conn_with_schema()
    try:
        conn.execute(
            "INSERT INTO grounded_fact (predicate, arguments, section) "
            "VALUES (?, ?, ?)",
            ("bird", json.dumps(["tweety"]), "yes"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO grounded_fact (predicate, arguments, section) "
                "VALUES (?, ?, ?)",
                ("bird", json.dumps(["tweety"]), "yes"),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Populate tests.
# ---------------------------------------------------------------------------


def test_populate_empty_bundle_inserts_zero_rows() -> None:
    """A bundle with all four sections empty produces no rows but
    returns successfully (return value ``0``).

    Diller, Borg, Bex 2025 §3: the empty program is a valid Datalog
    input and produces an empty ground model. Persisting that empty
    model must be lossless — zero rows, no error.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle({})
        inserted = populate_grounded_facts(conn, bundle)
        assert inserted == 0
        count = conn.execute(
            "SELECT COUNT(*) FROM grounded_fact"
        ).fetchone()[0]
        assert count == 0
    finally:
        conn.close()


def test_populate_single_fact_one_section() -> None:
    """Bundle with ``definitely = {bird: {(tweety,)}}`` and the other
    three sections empty. ``populate_grounded_facts`` returns ``1``
    and inserts exactly one row with ``section='definitely'``.

    Garcia & Simari 2004 §3 (pp.3-4): this is the "Tweety is a bird"
    base fact, the simplest possible instance of a definitely-true
    ground atom.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle(
            {"yes": {"bird": frozenset({("tweety",)})}}
        )
        inserted = populate_grounded_facts(conn, bundle)
        assert inserted == 1

        rows = conn.execute(
            "SELECT predicate, arguments, section FROM grounded_fact"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "bird"
        assert json.loads(rows[0][1]) == ["tweety"]
        assert rows[0][2] == "yes"
    finally:
        conn.close()


def test_populate_same_atom_multiple_sections() -> None:
    """An atom may appear in several sections — e.g. ``bird(tweety)``
    lives in both ``definitely`` and ``defeasibly`` because of
    gunray's ``definitely ⊆ defeasibly`` invariant. Each section
    gets its own row; the primary key ``(predicate, arguments,
    section)`` means there is no collision.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system is
    not a partition — a single atom can carry multiple verdicts
    simultaneously, and storage must preserve that multiplicity.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle(
            {
                "yes": {"bird": frozenset({("tweety",)})},
                "no": {"bird": frozenset({("tweety",)})},
            }
        )
        inserted = populate_grounded_facts(conn, bundle)
        assert inserted == 2

        sections = {
            row[0]
            for row in conn.execute(
                "SELECT section FROM grounded_fact "
                "WHERE predicate = 'bird'"
            ).fetchall()
        }
        assert sections == {"yes", "no"}
    finally:
        conn.close()


def test_populate_all_four_sections() -> None:
    """A bundle with at least one atom in each of the four sections
    inserts exactly one row per section.

    Garcia & Simari 2004 §4 (p.25) four-valued answer system: every
    verdict in ``{YES, NO, UNDECIDED, UNKNOWN}`` (mapped to
    ``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
    ``undecided``) has to be individually persistable — that is the
    non-commitment discipline anchor.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle(
            {
                "yes": {"p": frozenset({(1,)})},
                "no": {"q": frozenset({(2,)})},
                "undecided": {"s": frozenset({(4,)})},
                "unknown": {"t": frozenset({(5,)})},
            }
        )
        inserted = populate_grounded_facts(conn, bundle)
        assert inserted == 4

        counts = dict(
            conn.execute(
                "SELECT section, COUNT(*) FROM grounded_fact GROUP BY section"
            ).fetchall()
        )
        assert counts == {
            "yes": 1,
            "no": 1,
            "undecided": 1,
            "unknown": 1,
        }
    finally:
        conn.close()


@pytest.mark.property
@given(bundle=st.deferred(bundles_with_facts))
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_populate_row_count_matches_section_content(bundle) -> None:
    """``populate_grounded_facts`` returns a count equal to the sum of
    inner-set sizes across all four sections.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs; the number of persisted
    rows has to match the number of ground atoms in the bundle's
    ground model exactly — no duplicates, no drops.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = _fresh_conn_with_schema()
    try:
        expected = sum(
            len(inner)
            for section_map in bundle.sections.values()
            for inner in section_map.values()
        )
        inserted = populate_grounded_facts(conn, bundle)
        assert inserted == expected

        actual = conn.execute(
            "SELECT COUNT(*) FROM grounded_fact"
        ).fetchone()[0]
        assert actual == expected
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Round-trip tests.
# ---------------------------------------------------------------------------


def test_round_trip_empty_bundle() -> None:
    """``populate`` then ``read`` of an empty bundle yields empty
    inner maps for all four section keys.

    Garcia & Simari 2004 §4 (p.25) non-commitment discipline: all four
    section keys are always present in the read result, even when the
    bundle is empty. Storage never silently drops a verdict.
    """
    from propstore.sidecar.rules import (
        populate_grounded_facts,
        read_grounded_facts,
    )

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle({})
        populate_grounded_facts(conn, bundle)
        result = read_grounded_facts(conn)
        assert set(result.keys()) == {
            "yes",
            "no",
            "undecided",
            "unknown",
        }
        for section_name, inner in result.items():
            assert dict(inner.items()) == {}, (
                f"section {section_name!r} should be empty"
            )
    finally:
        conn.close()


def test_round_trip_single_fact() -> None:
    """``populate`` then ``read`` of a bundle with one fact yields
    identical section structure for that atom.

    Garcia & Simari 2004 §3 (pp.3-4): the canonical DeLP regression
    case — a single ``bird(tweety)`` fact in the ``definitely``
    section must round-trip byte-for-byte.
    """
    from propstore.sidecar.rules import (
        populate_grounded_facts,
        read_grounded_facts,
    )

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle(
            {"yes": {"bird": frozenset({("tweety",)})}}
        )
        populate_grounded_facts(conn, bundle)
        result = read_grounded_facts(conn)

        assert dict(result["yes"].items()) == {
            "bird": frozenset({("tweety",)})
        }
        for name in ("no", "undecided", "unknown"):
            assert dict(result[name].items()) == {}
    finally:
        conn.close()


@pytest.mark.property
@given(bundle=st.deferred(bundles_with_facts))
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_round_trip_arbitrary_bundle(bundle) -> None:
    """For any bundle, ``populate(bundle)`` followed by ``read()``
    yields a section mapping equal to ``bundle.sections``.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs, so the composition
    ``read ∘ populate`` on a fresh connection must be the identity on
    the sections map. This is the determinism property for the
    persistence layer.
    """
    from propstore.sidecar.rules import (
        populate_grounded_facts,
        read_grounded_facts,
    )

    conn = _fresh_conn_with_schema()
    try:
        populate_grounded_facts(conn, bundle)
        result = read_grounded_facts(conn)

        expected = _sections_as_plain_dict(bundle)
        actual = {name: dict(inner.items()) for name, inner in result.items()}
        assert actual == expected
    finally:
        conn.close()


def test_round_trip_delp_birds_fly_tweety() -> None:
    """Concrete regression case from Garcia & Simari 2004 §3 (pp.3-4):

        fact: bird(tweety)
        rule: flies(X) -< bird(X)

    Grounding produces
    ``definitely = {bird: {(tweety,)}}`` (the base fact) and
    ``defeasibly = {bird: {(tweety,)}, flies: {(tweety,)}}`` (the
    base fact plus the defeasibly derived ``flies(tweety)``).

    ``populate`` then ``read`` must recover both sections exactly.
    """
    from propstore.sidecar.rules import (
        populate_grounded_facts,
        read_grounded_facts,
    )

    conn = _fresh_conn_with_schema()
    try:
        bundle = _make_bundle(
            {
                "yes": {
                    "bird": frozenset({("tweety",)}),
                    "flies": frozenset({("tweety",)}),
                },
            }
        )
        inserted = populate_grounded_facts(conn, bundle)
        # 2 rows for yes (bird, flies).
        assert inserted == 2

        result = read_grounded_facts(conn)
        assert dict(result["yes"].items()) == {
            "bird": frozenset({("tweety",)}),
            "flies": frozenset({("tweety",)}),
        }
        assert dict(result["no"].items()) == {}
        assert dict(result["undecided"].items()) == {}
        assert dict(result["unknown"].items()) == {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Integration with sidecar build.
# ---------------------------------------------------------------------------


def test_populate_requires_schema_created() -> None:
    """Calling ``populate_grounded_facts`` on a connection that has no
    ``grounded_fact`` table raises ``sqlite3.OperationalError``
    (``no such table``). Catches the obvious misuse of slotting the
    populate call into ``build_sidecar`` before the schema-creation
    step.

    Diller, Borg, Bex 2025 §3: the ground model depends on the fact
    base; analogously, persistence depends on the schema — both
    dependencies have to be explicit, and failing loudly is the
    non-commitment-discipline-compatible behaviour for a misuse.
    """
    from propstore.sidecar.rules import populate_grounded_facts

    conn = sqlite3.connect(":memory:")
    try:
        bundle = _make_bundle({"yes": {"bird": frozenset({("tweety",)})}})
        with pytest.raises(sqlite3.OperationalError):
            populate_grounded_facts(conn, bundle)
    finally:
        conn.close()
