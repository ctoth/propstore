"""Sidecar persistence for grounded facts — chunk 1.6b (green).

This module persists the four gunray answer sections
(``yes`` / ``no`` / ``undecided`` / ``unknown``)
from a :class:`propstore.grounding.bundle.GroundedRulesBundle` into
the sidecar's SQLite store. The grounding inputs are persisted with
explicit JSON payloads rather than Python object pickles because the
sidecar is a durable boundary, not an in-process cache.

The design follows the existing sidecar convention of *one topic
module per subsystem* (``claims.py``, ``concepts.py``, ``sources.py``);
grounded facts are their own topic and get their own module. The
``CREATE TABLE`` helper is colocated here because the grounded-fact
table does not cross-reference any other sidecar table, so keeping
schema and read/write functions physically next to one another makes
the module self-contained.

Non-commitment discipline anchor (project CLAUDE.md): storage never
silently collapses a grounded classification. All four section keys are always
present in the read result, even when the bundle is empty. The
primary key ``(predicate, arguments, section)`` lets a single ground
atom appear under multiple sections simultaneously when an upstream
answer surface does so, and the storage layer must not silently dedupe
it away.

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
      ``yes = {bird: {(tweety,)}, flies: {(tweety,)}}``. The
      persistence layer must round-trip that structure byte-for-byte.
    - Section 4 (p.25): the four-valued answer system
      ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto the four section
      names. All four sections are always returned by
      :func:`read_grounded_facts`, even when some are empty, because
      storage is forbidden from collapsing a grounded classification.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import gunray
import msgspec
from argumentation.aspic import Scalar
from argumentation.aspic import GroundAtom as AspicGroundAtom
from propstore.families.documents.rules import RulesFileDocument
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.rule_files import LoadedRuleFile

# Garcia & Simari 2004 §4 (p.25): the four-valued answer system. The
# tuple order is the deterministic iteration order used by
# ``populate_grounded_facts`` so row insertion is reproducible.
_SECTION_NAMES: tuple[str, ...] = (
    "yes",
    "no",
    "undecided",
    "unknown",
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
    atom to appear under multiple sections.

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
    empty inner set is still a *grounded classification* — "predicate p is known to
    the program and its derivation for section s is empty" — and
    storage must not silently drop it. The empty-predicate table is
    how that grounded classification is persisted.
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
    conn.execute(
        "CREATE TABLE IF NOT EXISTS grounded_bundle_input ("
        "kind TEXT NOT NULL, "
        "position INTEGER NOT NULL, "
        "payload BLOB NOT NULL, "
        "PRIMARY KEY (kind, position)"
        ")"
    )


def populate_grounded_facts(
    conn: sqlite3.Connection,
    bundle: GroundedRulesBundle,
) -> int:
    """Insert every ground atom in ``bundle.sections`` into ``grounded_fact``.

    Iterates the four section keys in a deterministic order
    (``yes`` → ``no`` → ``undecided`` → ``unknown``). Within each section, predicates are iterated in
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

    Garcia & Simari 2004 §4 (p.25): each four-valued grounded classification is
    itself a set of ground atoms; the composite primary key hardens
    that set semantics at the storage layer so duplicates within a
    grounded classification raise loudly instead of being silently coalesced.
    """
    inserted = 0
    _persist_bundle_inputs(conn, bundle)
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
                # non-commitment discipline — an empty grounded classification is
                # still a grounded classification). Persist the presence record to
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


def _persist_bundle_inputs(conn: sqlite3.Connection, bundle: GroundedRulesBundle) -> None:
    rows = (
        ("source_rule", bundle.source_rules),
        ("source_fact", bundle.source_facts),
        ("argument", bundle.arguments),
    )
    for kind, values in rows:
        for position, value in enumerate(values):
            conn.execute(
                "INSERT INTO grounded_bundle_input "
                "(kind, position, payload) VALUES (?, ?, ?)",
                (kind, position, _encode_bundle_input(kind, value)),
            )


def _read_bundle_inputs(conn: sqlite3.Connection, kind: str) -> tuple[object, ...]:
    cursor = conn.execute(
        "SELECT payload FROM grounded_bundle_input WHERE kind = ? ORDER BY position",
        (kind,),
    )
    return tuple(_decode_bundle_input(kind, payload) for (payload,) in cursor.fetchall())


def _encode_bundle_input(kind: str, value: object) -> bytes:
    payload = _bundle_input_payload(kind, value)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decode_bundle_input(kind: str, payload: bytes) -> object:
    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict) or decoded.get("kind") != kind:
        raise ValueError(f"grounded bundle input payload has wrong kind for {kind!r}")
    tag = decoded.get("tag")
    value = decoded.get("value")
    if tag == "json":
        return value
    if tag == "aspic_ground_atom":
        if not isinstance(value, dict):
            raise ValueError("aspic ground atom payload must be an object")
        return AspicGroundAtom(
            predicate=str(value["predicate"]),
            arguments=tuple(value["arguments"]),
        )
    if tag == "gunray_argument":
        if not isinstance(value, dict):
            raise ValueError("gunray argument payload must be an object")
        return gunray.Argument(
            rules=frozenset(_decode_gunray_rule(rule) for rule in value["rules"]),
            conclusion=_decode_gunray_atom(value["conclusion"]),
        )
    if tag == "loaded_rule_file":
        if not isinstance(value, dict):
            raise ValueError("loaded rule file payload must be an object")
        document = msgspec.convert(value["document"], type=RulesFileDocument)
        source_path = value.get("source_path")
        knowledge_root = value.get("knowledge_root")
        return LoadedRuleFile(
            filename=str(value["filename"]),
            source_path=None if source_path is None else Path(str(source_path)),
            knowledge_root=None if knowledge_root is None else Path(str(knowledge_root)),
            document=document,
        )
    raise ValueError(f"unsupported grounded bundle input tag {tag!r}")


def _bundle_input_payload(kind: str, value: object) -> dict[str, object]:
    if _is_json_value(value):
        return {"kind": kind, "tag": "json", "value": value}
    if isinstance(value, AspicGroundAtom):
        return {
            "kind": kind,
            "tag": "aspic_ground_atom",
            "value": {
                "predicate": value.predicate,
                "arguments": list(value.arguments),
            },
        }
    if isinstance(value, gunray.Argument):
        return {
            "kind": kind,
            "tag": "gunray_argument",
            "value": {
                "rules": [
                    _encode_gunray_rule(rule)
                    for rule in sorted(value.rules, key=_rule_key)
                ],
                "conclusion": _encode_gunray_atom(value.conclusion),
            },
        }
    if isinstance(value, LoadedRuleFile):
        return {
            "kind": kind,
            "tag": "loaded_rule_file",
            "value": {
                "filename": value.filename,
                "source_path": None if value.source_path is None else str(value.source_path),
                "knowledge_root": (
                    None if value.knowledge_root is None else str(value.knowledge_root)
                ),
                "document": msgspec.to_builtins(value.document),
            },
        }
    raise TypeError(f"cannot persist grounded bundle {kind} input {type(value).__name__}")


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, tuple | list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(item)
            for key, item in value.items()
        )
    return False


def _encode_gunray_atom(atom: gunray.GroundAtom) -> dict[str, object]:
    return {"predicate": atom.predicate, "arguments": list(atom.arguments)}


def _decode_gunray_atom(payload: object) -> gunray.GroundAtom:
    if not isinstance(payload, dict):
        raise ValueError("gunray atom payload must be an object")
    return gunray.GroundAtom(
        predicate=str(payload["predicate"]),
        arguments=tuple(payload["arguments"]),
    )


def _encode_gunray_rule(rule: gunray.GroundDefeasibleRule) -> dict[str, object]:
    return {
        "rule_id": rule.rule_id,
        "kind": rule.kind,
        "head": _encode_gunray_atom(rule.head),
        "body": [_encode_gunray_atom(atom) for atom in rule.body],
        "default_negated_body": [
            _encode_gunray_atom(atom) for atom in rule.default_negated_body
        ],
    }


def _decode_gunray_rule(payload: object) -> gunray.GroundDefeasibleRule:
    if not isinstance(payload, dict):
        raise ValueError("gunray rule payload must be an object")
    return gunray.GroundDefeasibleRule(
        rule_id=str(payload["rule_id"]),
        kind=str(payload["kind"]),
        head=_decode_gunray_atom(payload["head"]),
        body=tuple(_decode_gunray_atom(atom) for atom in payload["body"]),
        default_negated_body=tuple(
            _decode_gunray_atom(atom) for atom in payload["default_negated_body"]
        ),
    )


def _rule_key(rule: gunray.GroundDefeasibleRule) -> tuple[str, str, str]:
    return (rule.rule_id, rule.kind, repr(rule.head))


def read_grounded_facts(
    conn: sqlite3.Connection,
) -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Read every row of ``grounded_fact`` back into a sections mapping.

    Returns an immutable mapping whose outer keys are exactly the
    four section names (always present, even when empty) and whose
    inner maps go ``predicate_id -> frozenset(arg_tuple)``. Argument
    tuples are decoded from the JSON column via ``json.loads`` and
    cast to :class:`tuple`; Python's ``json`` module preserves the
    :data:`~argumentation.aspic.Scalar` union (``str``/``int``/``float``/
    ``bool``) losslessly for the domain the Hypothesis strategy
    samples (NaN/Infinity are excluded at the strategy level so the
    round-trip is well defined).

    Garcia & Simari 2004 §4 (p.25) non-commitment discipline: all
    four section keys are always present in the read result. Storage
    never silently drops a grounded classification, so an empty bundle still yields
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
    # drops a grounded classification (Garcia & Simari 2004 §4 (p.25)).
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


def read_grounded_bundle(conn: sqlite3.Connection) -> GroundedRulesBundle:
    """Rehydrate a runtime grounding bundle from persisted grounding inputs.

    The sidecar persists the source rule/fact inputs and the materialized
    four-status section map. Re-running the typed grounder here restores the
    Gunray inspection frame required by ASPIC projection, then verifies that
    the recomputed sections match the stored materialization.
    """

    stored_sections = read_grounded_facts(conn)
    bundle = ground(
        _read_source_rules(conn),
        _read_source_facts(conn),
        PredicateRegistry(()),
        return_arguments=True,
    )
    if bundle.sections != stored_sections:
        raise ValueError("persisted grounded facts diverge from grounded inputs")
    return bundle


def _read_source_rules(conn: sqlite3.Connection) -> tuple[LoadedRuleFile, ...]:
    values = _read_bundle_inputs(conn, "source_rule")
    if not all(isinstance(value, LoadedRuleFile) for value in values):
        raise TypeError("grounded source_rule inputs must be LoadedRuleFile values")
    return tuple(value for value in values if isinstance(value, LoadedRuleFile))


def _read_source_facts(conn: sqlite3.Connection) -> tuple[AspicGroundAtom, ...]:
    values = _read_bundle_inputs(conn, "source_fact")
    if not all(isinstance(value, AspicGroundAtom) for value in values):
        raise TypeError("grounded source_fact inputs must be ASPIC GroundAtom values")
    return tuple(value for value in values if isinstance(value, AspicGroundAtom))
