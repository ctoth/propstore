"""WS-J Step 1: worldline hashes use strict canonical JSON."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


@dataclass(frozen=True)
class _NotJsonNative:
    value: int


_RFC8785_SAFE_INTEGERS = st.integers(
    min_value=-(2**53) + 1,
    max_value=2**53 - 1,
)
_JSON_SCALARS = st.none() | st.booleans() | _RFC8785_SAFE_INTEGERS | st.text(max_size=12)
_JSON_VALUES = st.recursive(
    _JSON_SCALARS,
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(st.text(min_size=1, max_size=8), children, max_size=4),
    max_leaves=16,
)


@given(payload=_JSON_VALUES)
@pytest.mark.property
@settings(max_examples=20)
def test_ws_j_rfc8785_dumps_is_deterministic_for_json_native_payloads(
    payload: object,
) -> None:
    """Codex 2.10: JSON-native payloads get byte-stable canonical encoding."""

    import rfc8785

    assert rfc8785.dumps(payload) == rfc8785.dumps(payload)


@given(
    value=st.one_of(
        st.builds(_NotJsonNative, st.integers()),
        st.builds(set, st.lists(st.integers(), max_size=3)),
        st.builds(Path, st.text(min_size=1, max_size=8)),
    )
)
@pytest.mark.property
@settings(max_examples=12)
def test_ws_j_rfc8785_dumps_rejects_non_json_native_payloads(value: object) -> None:
    """J-H2: unknown objects fail loudly instead of being stringified into hashes."""

    import rfc8785

    with pytest.raises(rfc8785.CanonicalizationError) as exc_info:
        rfc8785.dumps({"value": value})

    assert type(value).__name__ in str(exc_info.value)


@pytest.mark.parametrize("value", [-(2**53), 2**53])
def test_ws_j_rfc8785_dumps_rejects_integers_outside_rfc8785_domain(
    value: int,
) -> None:
    import rfc8785

    with pytest.raises(rfc8785.CanonicalizationError):
        rfc8785.dumps(value)


def test_ws_j_worldline_revision_hash_surfaces_do_not_use_default_str() -> None:
    """J-H2: worldline and support-revision hash surfaces must not hide unknowns."""

    import propstore.support_revision.history as history
    import propstore.support_revision.projection as projection
    import propstore.worldline.argumentation as argumentation
    import propstore.worldline.hashing as hashing

    for module in (history, projection, argumentation, hashing):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "default=str" not in source
