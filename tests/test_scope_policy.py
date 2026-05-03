from __future__ import annotations

import warnings
from types import SimpleNamespace

import pytest
from hypothesis import given, settings, strategies as st

from propstore.support_revision.scope_policy import scope_policy


pytestmark = pytest.mark.property


def _snapshot_with_scope(scope: object) -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace(scope=scope))


def _single_step_journal(scope: object) -> SimpleNamespace:
    return SimpleNamespace(entries=(SimpleNamespace(state_out=_snapshot_with_scope(scope)),))


def _scope_strategy(*, missing: set[str]) -> st.SearchStrategy[SimpleNamespace]:
    values = {
        "bindings": {"character": "mara"},
        "context_id": "ctx:mara",
        "commit": "abc123",
    }
    return st.just(
        SimpleNamespace(
            **{
                field: (None if field in missing else value)
                for field, value in values.items()
            }
        )
    )


@scope_policy(
    extract_from="journal",
    extract_step="k",
    degrade={"rebind": ("bindings", "context_id")},
    require={"heavy": ("commit",)},
)
def _decorated_projection(
    journal: SimpleNamespace,
    k: int,
    *,
    rebind: bool = False,
    heavy: bool = False,
) -> tuple[bool, bool]:
    _ = journal, k
    return rebind, heavy


@given(scope=_scope_strategy(missing={"bindings"}))
@settings(deadline=None)
def test_scope_policy_degrades_on_missing_field(scope: SimpleNamespace) -> None:
    journal = _single_step_journal(scope)

    with pytest.warns(UserWarning, match="degrading to rebind=False"):
        result = _decorated_projection(journal, 0, rebind=True)

    assert result == (False, False)


@given(scope=_scope_strategy(missing={"commit"}))
@settings(deadline=None)
def test_scope_policy_raises_on_missing_required_field(scope: SimpleNamespace) -> None:
    journal = _single_step_journal(scope)

    with pytest.raises(ValueError, match="missing.*commit"):
        _decorated_projection(journal, 0, heavy=True)


@given(scope=_scope_strategy(missing=set()))
@settings(deadline=None)
def test_scope_policy_noop_when_complete(scope: SimpleNamespace) -> None:
    journal = _single_step_journal(scope)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = _decorated_projection(journal, 0, rebind=True)

    assert result == (True, False)
