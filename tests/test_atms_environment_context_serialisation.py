"""WS-I Step 5: serialized ATMS environments preserve contexts."""

from __future__ import annotations

from propstore.app.world_atms import _support_ids
from propstore.core.labels import EnvironmentKey, Label

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_environment_serialization_preserves_assumptions_and_contexts() -> None:
    """Codex #25: Martins 1983 belief-space contexts must survive serialization."""

    engine = _make_bound(_ATMSStore(claims=[])).atms_engine()
    environment = EnvironmentKey(("a1",), context_ids=("ctx1",))
    expected = {"assumption_ids": ["a1"], "context_ids": ["ctx1"]}

    assert engine._serialize_environment_key(environment) == expected
    assert engine._serialize_label(Label((environment,))) == [expected]

    engine.nogoods = engine.nogoods.add(environment)
    detail = engine._serialize_nogood_detail(environment)
    assert detail.environment == expected

    assert _support_ids(environment) == expected
