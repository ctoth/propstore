"""Sidecar persistence for grounded facts — chunk 1.6b (green).

This module persists the four gunray sections
(``definitely`` / ``defeasibly`` / ``not_defeasibly`` / ``undecided``)
from a :class:`propstore.grounding.bundle.GroundedRulesBundle` into
the sidecar's SQLite store. Phase 1 scope: only the ``sections`` map
of the bundle is written to storage; the ``source_rules`` and
``source_facts`` fields are carried by the bundle itself but are not
part of the grounded-fact table contract.

The design follows the existing sidecar convention of *one topic
module per subsystem* (``claims.py``, ``concepts.py``, ``sources.py``);
grounded facts are their own topic and get their own module. The
``CREATE TABLE`` helper is colocated here because the grounded-fact
table does not cross-reference any other sidecar table, so keeping
schema and read/write functions physically next to one another makes
the module self-contained.

Non-commitment discipline anchor (project CLAUDE.md): storage never
silently collapses a verdict. All four section keys are always
present in the read result, even when the bundle is empty. The
primary key ``(predicate, arguments, section)`` lets a single ground
atom appear under multiple sections simultaneously — gunray's
``definitely ⊆ defeasibly`` invariant requires exactly that
multiplicity, and the storage layer must not silently dedupe it
away.

Theoretical anchors:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is
      a finite set of ground atoms keyed by predicate id. The
      grounded-fact table stores one row per ground atom per section;
      argument tuples are JSON-encoded into a single ``TEXT`` column
      so SQLite's primary-key mechanism can enforce set semantics
      across variable-arity atoms.
    - Section 3 (Definition 9): grounding is a deterministic function
      of the program and its fact base. The round-trip property
      ``read(populate(bundle)) == bundle.sections`` therefore must
      hold for every bundle — that is the determinism pin for this
      persistence layer.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (pp.3-4): the canonical DeLP example is
      ``bird(tweety) ∈ Facts`` with the defeasible rule
      ``flies(X) -< bird(X)``; grounding produces
      ``definitely = {bird: {(tweety,)}}`` and
      ``defeasibly = {bird: {(tweety,)}, flies: {(tweety,)}}``. The
      persistence layer must round-trip that structure byte-for-byte.
    - Section 4 (p.25): the four-valued answer system
      ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto the four section
      names. All four sections are always returned by
      :func:`read_grounded_facts`, even when some are empty, because
      storage is forbidden from collapsing a verdict.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from types import MappingProxyType

from propstore.aspic import Scalar
from propstore.grounding.bundle import GroundedRulesBundle

# Garcia & Simari 2004 §4 (p.25): the four-valued answer system. The
# tuple order is the deterministic iteration order used by
# ``populate_grounded_facts`` so row insertion is reproducible.
_SECTION_NAMES: tuple[str, ...] = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)


def create_grounded_fact_table(conn: sqlite3.Connection) -> None:
    """Create the grounded-fact tables if they do not already exist.

    Two tables are created in this call:

    .. code-block:: sql

        CREATE TABLE IF NOT EXISTS grounded_fact (
            predicate TEXT NOT NULL,
            arguments TEXT NOT NULL,
            section   TEXT NOT NULL,
            PRIMARY KEY (predicate, arguments, section)
        );

        CREATE TABLE IF NOT EXISTS grounded_fact_empty_predicate (
            section   TEXT NOT NULL,
            predicate TEXT NOT NULL,
            PRIMARY KEY (section, predicate)
        );

    The ``grounded_fact`` composite primary key enforces set
    semantics per section while still permitting the same ground
    atom to appear under multiple sections (gunray's
    ``definitely ⊆ defeasibly`` invariant).

    The ``grounded_fact_empty_predicate`` companion table records
    predicate keys whose inner ``frozenset`` is empty — gunray's
    ground model can legitimately contain
    ``section[predicate] = frozenset()``, meaning "the predicate is
    mentioned by the program but the grounder produced no facts for
    it in this section". Storing that presence record in a separate
    table is required because ``grounded_fact`` stores one row per
    ground atom, and an empty frozenset has zero atoms to insert.
    Keeping the empty-predicate marker out of ``grounded_fact`` also
    preserves the invariant that
    ``COUNT(*) FROM grounded_fact`` equals the sum of inner-set
    sizes across all four sections (pinned by
    ``test_populate_row_count_matches_section_content``).

    Diller, Borg, Bex 2025 §3 Definition 7 (p.3): a Datalog fact base
    is a finite set of ground atoms keyed by predicate id. The
    propstore sidecar realises that set as rows in ``grounded_fact``
    with argument tuples JSON-encoded into a single ``TEXT`` column
    so SQLite's primary-key mechanism can enforce set semantics
    across variable-arity atoms.

    Garcia & Simari 2004 §4 (p.25) non-commitment discipline: an
    empty inner set is still a *verdict* — "predicate p is known to
    the program and its derivation for section s is empty" — and
    storage must not silently drop it. The empty-predicate table is
    how that verdict is persisted.
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS grounded_fact ("
        "predicate TEXT NOT NULL, "
        "arguments TEXT NOT NULL, "
        "section TEXT NOT NULL, "
        "PRIMARY KEY (predicate, arguments, section)"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS grounded_fact_empty_predicate ("
        "section TEXT NOT NULL, "
        "predicate TEXT NOT NULL, "
        "PRIMARY KEY (section, predicate)"
        ")"
    )


def populate_grounded_facts(
    conn: sqlite3.Connection,
    bundle: GroundedRulesBundle,
) -> int:
    """Insert every ground atom in ``bundle.sections`` into ``grounded_fact``.

    Iterates the four section keys in a deterministic order
    (``definitely`` → ``defeasibly`` → ``not_defeasibly`` →
    ``undecided``). Within each section, predicates are iterated in
    sorted order and their argument tuples are iterated in a stable
    order derived by sorting on the JSON-encoded argument string, so
    the insert sequence is reproducible even though ``frozenset``
    iteration itself is unordered.

    Each row is inserted via ``INSERT`` (no ``OR IGNORE``), which
    means a duplicate insert raises :class:`sqlite3.IntegrityError`.
    The test ``test_grounded_fact_table_primary_key_uniqueness``
    pins that behaviour; it also guards against a careless
    re-populate double-counting rows.

    Returns the total number of rows inserted, which must match the
    sum of inner-set sizes across all four sections.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs, so the number of persisted
    rows has to match the number of ground atoms in the bundle's
    ground model exactly — no duplicates, no drops.

    Garcia & Simari 2004 §4 (p.25): each four-valued verdict is
    itself a set of ground atoms; the composite primary key hardens
    that set semantics at the storage layer so duplicates within a
    verdict raise loudly instead of being silently coalesced.
    """
    inserted = 0
    sections = bundle.sections
    for section_name in _SECTION_NAMES:
        inner_map = sections.get(section_name)
        if inner_map is None:
            continue
        for predicate_id in sorted(inner_map.keys()):
            rows = inner_map[predicate_id]
            if not rows:
                # Predicate is mentioned in this section with zero
                # ground atoms (see Garcia & Simari 2004 §4 (p.25)
                # non-commitment discipline — an empty verdict is
                # still a verdict). Persist the presence record to
                # the companion table so the round-trip preserves
                # the predicate key. Empty-predicate markers do NOT
                # count toward the inserted total because they are
                # not ground atoms — the
                # ``test_populate_row_count_matches_section_content``
                # contract sums inner-set *sizes*, which are zero
                # for an empty frozenset.
                conn.execute(
                    "INSERT INTO grounded_fact_empty_predicate "
                    "(section, predicate) VALUES (?, ?)",
                    (section_name, predicate_id),
                )
                continue
            # Pre-encode argument tuples so we can sort for a stable
            # insert order; ``frozenset`` iteration is unordered but
            # the determinism pin in Diller 2025 §3 Def 9 is about
            # the output set, not iteration order, so sorting the
            # JSON strings is safe and reproducible.
            encoded = sorted(
                json.dumps(list(arg_tuple)) for arg_tuple in rows
            )
            for encoded_arguments in encoded:
                conn.execute(
                    "INSERT INTO grounded_fact "
                    "(predicate, arguments, section) VALUES (?, ?, ?)",
                    (predicate_id, encoded_arguments, section_name),
                )
                inserted += 1
    return inserted


def read_grounded_facts(
    conn: sqlite3.Connection,
) -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Read every row of ``grounded_fact`` back into a sections mapping.

    Returns an immutable mapping whose outer keys are exactly the
    four section names (always present, even when empty) and whose
    inner maps go ``predicate_id -> frozenset(arg_tuple)``. Argument
    tuples are decoded from the JSON column via ``json.loads`` and
    cast to :class:`tuple`; Python's ``json`` module preserves the
    :data:`~propstore.aspic.Scalar` union (``str``/``int``/``float``/
    ``bool``) losslessly for the domain the Hypothesis strategy
    samples (NaN/Infinity are excluded at the strategy level so the
    round-trip is well defined).

    Garcia & Simari 2004 §4 (p.25) non-commitment discipline: all
    four section keys are always present in the read result. Storage
    never silently drops a verdict, so an empty bundle still yields
    four empty inner maps.

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder is a
    deterministic function of its inputs, so the composition
    ``read ∘ populate`` on a fresh connection must be the identity on
    the sections map. That determinism is what the round-trip
    property test pins.
    """
    result: dict[str, dict[str, set[tuple[Scalar, ...]]]] = {
        name: {} for name in _SECTION_NAMES
    }
    cursor = conn.execute(
        "SELECT predicate, arguments, section FROM grounded_fact"
    )
    for predicate_id, encoded_arguments, section_name in cursor.fetchall():
        # Defensive: the table schema pins ``section`` to one of the
        # four names, but if some future caller inserts a stray value
        # we surface it loudly rather than silently dropping the row.
        if section_name not in result:
            raise ValueError(
                f"grounded_fact row has unknown section {section_name!r}"
            )
        decoded = tuple(json.loads(encoded_arguments))
        predicate_bucket = result[section_name].setdefault(predicate_id, set())
        predicate_bucket.add(decoded)

    # Merge empty-predicate markers. These contribute predicate keys
    # whose inner ``frozenset`` is empty, preserving the
    # non-commitment-discipline guarantee that storage never silently
    # drops a verdict (Garcia & Simari 2004 §4 (p.25)).
    empty_cursor = conn.execute(
        "SELECT section, predicate FROM grounded_fact_empty_predicate"
    )
    for section_name, predicate_id in empty_cursor.fetchall():
        if section_name not in result:
            raise ValueError(
                "grounded_fact_empty_predicate row has unknown section "
                f"{section_name!r}"
            )
        # ``setdefault`` preserves any atoms already accumulated
        # above; if the section truly has no atoms for this
        # predicate the bucket stays empty and maps to
        # ``frozenset()`` in the frozen output.
        result[section_name].setdefault(predicate_id, set())

    frozen: dict[str, Mapping[str, frozenset[tuple[Scalar, ...]]]] = {}
    for section_name in _SECTION_NAMES:
        inner_frozen: dict[str, frozenset[tuple[Scalar, ...]]] = {
            predicate_id: frozenset(rows)
            for predicate_id, rows in result[section_name].items()
        }
        frozen[section_name] = MappingProxyType(inner_frozen)
    return MappingProxyType(frozen)
