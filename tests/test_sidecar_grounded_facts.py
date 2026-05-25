"""Typed grounded-rule persistence contract tests."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from propstore.families.rules.declaration import (
    load_grounded_sections,
    persist_grounded_bundle,
)
from propstore.families.registry import world_schema
from propstore.grounding.bundle import GroundedRulesBundle


def _fresh_store(tmp_path: Path) -> Path:
    sidecar_path = tmp_path / "propstore.sqlite"
    create_sqlalchemy_store(sidecar_path, world_schema())
    return sidecar_path


def _make_bundle(
    sections: Mapping[str, Mapping[str, frozenset[tuple[object, ...]]]],
) -> GroundedRulesBundle:
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


_SCALAR: st.SearchStrategy[object] = st.one_of(
    st.text(
        alphabet=st.characters(
            min_codepoint=32,
            max_codepoint=126,
            blacklist_characters='"\\',
        ),
        min_size=1,
        max_size=6,
    ),
    st.integers(min_value=-100, max_value=100),
    st.booleans(),
    st.floats(
        min_value=-1000.0,
        max_value=1000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
)
_PREDICATE_NAME: st.SearchStrategy[str] = st.text(
    alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
    min_size=1,
    max_size=5,
)
_ARG_TUPLE: st.SearchStrategy[tuple[object, ...]] = st.lists(
    _SCALAR,
    min_size=0,
    max_size=3,
).map(tuple)
_INNER_MAP: st.SearchStrategy[dict[str, frozenset[tuple[object, ...]]]] = (
    st.dictionaries(
        _PREDICATE_NAME,
        st.lists(_ARG_TUPLE, min_size=0, max_size=3).map(frozenset),
        min_size=0,
        max_size=3,
    )
)


def bundles_with_facts() -> st.SearchStrategy[GroundedRulesBundle]:
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
    return {
        name: dict(inner.items()) for name, inner in bundle.sections.items()
    }


def test_grounded_fact_tables_are_declared_by_world_charter() -> None:
    schema = world_schema()

    assert set(schema.table("grounded_fact").c.keys()) == {
        "predicate",
        "arguments",
        "section",
    }
    assert set(schema.table("grounded_fact_empty_predicate").c.keys()) == {
        "section",
        "predicate",
    }
    assert set(schema.table("grounded_bundle_input").c.keys()) == {
        "kind",
        "position",
        "payload",
    }


def test_grounded_fact_primary_key_uniqueness(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle({"yes": {"bird": frozenset({("tweety",)})}})

    with pytest.raises(IntegrityError):
        with writable_session(sidecar_path, world_schema()) as derived:
            persist_grounded_bundle(derived, bundle)
            persist_grounded_bundle(derived, bundle)
            derived.session.commit()


def test_persist_empty_bundle_inserts_zero_facts(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)

    with writable_session(sidecar_path, world_schema()) as derived:
        inserted = persist_grounded_bundle(derived, _make_bundle({}))
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        grounded_fact = derived.schema.table("grounded_fact")
        count = derived.session.execute(select(func.count()).select_from(grounded_fact)).scalar_one()

    assert inserted == 0
    assert count == 0


def test_persist_single_fact_one_section(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle({"yes": {"bird": frozenset({("tweety",)})}})

    with writable_session(sidecar_path, world_schema()) as derived:
        inserted = persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        grounded_fact = derived.schema.table("grounded_fact")
        rows = derived.session.execute(select(grounded_fact)).mappings().all()

    assert inserted == 1
    assert [row["predicate"] for row in rows] == ["bird"]
    assert [row["arguments"] for row in rows] == ['["tweety"]']
    assert [row["section"] for row in rows] == ["yes"]


def test_persist_same_atom_multiple_sections(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle(
        {
            "yes": {"bird": frozenset({("tweety",)})},
            "no": {"bird": frozenset({("tweety",)})},
        }
    )

    with writable_session(sidecar_path, world_schema()) as derived:
        inserted = persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        grounded_fact = derived.schema.table("grounded_fact")
        sections = {
            row["section"]
            for row in derived.session.execute(
                select(grounded_fact.c.section).where(
                    grounded_fact.c.predicate == "bird"
                )
            ).mappings()
        }

    assert inserted == 2
    assert sections == {"yes", "no"}


def test_persist_all_four_sections(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle(
        {
            "yes": {"p": frozenset({(1,)})},
            "no": {"q": frozenset({(2,)})},
            "undecided": {"s": frozenset({(4,)})},
            "unknown": {"t": frozenset({(5,)})},
        }
    )

    with writable_session(sidecar_path, world_schema()) as derived:
        inserted = persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        grounded_fact = derived.schema.table("grounded_fact")
        rows = derived.session.execute(
            select(grounded_fact.c.section, func.count())
            .group_by(grounded_fact.c.section)
        ).all()

    assert inserted == 4
    assert dict(rows) == {
        "yes": 1,
        "no": 1,
        "undecided": 1,
        "unknown": 1,
    }


@pytest.mark.property
@given(bundle=st.deferred(bundles_with_facts))
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_persisted_row_count_matches_section_content(
    bundle: GroundedRulesBundle,
) -> None:
    with TemporaryDirectory() as temp_dir:
        sidecar_path = _fresh_store(Path(temp_dir))
        expected = sum(
            len(inner)
            for section_map in bundle.sections.values()
            for inner in section_map.values()
        )

        with writable_session(sidecar_path, world_schema()) as derived:
            inserted = persist_grounded_bundle(derived, bundle)
            derived.session.commit()

        with readonly_session(sidecar_path, world_schema()) as derived:
            grounded_fact = derived.schema.table("grounded_fact")
            actual = derived.session.execute(select(func.count()).select_from(grounded_fact)).scalar_one()

    assert inserted == expected
    assert actual == expected


def test_round_trip_empty_bundle(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)

    with writable_session(sidecar_path, world_schema()) as derived:
        persist_grounded_bundle(derived, _make_bundle({}))
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        result = load_grounded_sections(derived)

    assert set(result.keys()) == {"yes", "no", "undecided", "unknown"}
    assert all(dict(inner.items()) == {} for inner in result.values())


def test_round_trip_single_fact(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle({"yes": {"bird": frozenset({("tweety",)})}})

    with writable_session(sidecar_path, world_schema()) as derived:
        persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        result = load_grounded_sections(derived)

    assert dict(result["yes"].items()) == {"bird": frozenset({("tweety",)})}
    for name in ("no", "undecided", "unknown"):
        assert dict(result[name].items()) == {}


@pytest.mark.property
@given(bundle=st.deferred(bundles_with_facts))
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_round_trip_arbitrary_bundle(
    bundle: GroundedRulesBundle,
) -> None:
    with TemporaryDirectory() as temp_dir:
        sidecar_path = _fresh_store(Path(temp_dir))

        with writable_session(sidecar_path, world_schema()) as derived:
            persist_grounded_bundle(derived, bundle)
            derived.session.commit()

        with readonly_session(sidecar_path, world_schema()) as derived:
            result = load_grounded_sections(derived)

    expected = _sections_as_plain_dict(bundle)
    actual = {name: dict(inner.items()) for name, inner in result.items()}
    assert actual == expected


def test_round_trip_delp_birds_fly_tweety(tmp_path: Path) -> None:
    sidecar_path = _fresh_store(tmp_path)
    bundle = _make_bundle(
        {
            "yes": {
                "bird": frozenset({("tweety",)}),
                "flies": frozenset({("tweety",)}),
            },
        }
    )

    with writable_session(sidecar_path, world_schema()) as derived:
        inserted = persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        result = load_grounded_sections(derived)

    assert inserted == 2
    assert dict(result["yes"].items()) == {
        "bird": frozenset({("tweety",)}),
        "flies": frozenset({("tweety",)}),
    }
    assert dict(result["no"].items()) == {}
    assert dict(result["undecided"].items()) == {}
    assert dict(result["unknown"].items()) == {}
