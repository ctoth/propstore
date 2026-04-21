from __future__ import annotations

import pytest

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.world.atms import ATMSEngine

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_atms_build_raises_enumeration_exceeded_past_iteration_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bound = _make_bound(_ATMSStore(claims=[]))

    monkeypatch.setattr(ATMSEngine, "_propagate_labels", lambda self: None)
    monkeypatch.setattr(
        ATMSEngine,
        "_materialize_parameterization_justifications",
        lambda self: False,
    )
    monkeypatch.setattr(ATMSEngine, "_update_nogoods", lambda self: True)

    with pytest.raises(RuntimeError) as exc_info:
        ATMSEngine(bound, max_build_iterations=2)

    assert isinstance(exc_info.value, EnumerationExceeded)
    assert exc_info.value.partial_count == 2
    assert exc_info.value.max_candidates == 2
    assert exc_info.value.remainder_provenance == ProvenanceStatus.VACUOUS
