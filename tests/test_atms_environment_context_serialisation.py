"""WS-I Step 5: serialized ATMS environments preserve contexts."""

from __future__ import annotations

from propstore.app.world_atms import _support_ids
from propstore.core.labels import EnvironmentKey, Label, NogoodSet, SupportQuality
from propstore.world.types import (
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSNodeFutureStatusEntry,
    ATMSNodeStatus,
)

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_ws_i_environment_serialization_preserves_assumptions_and_contexts() -> None:
    """Codex #25: Martins 1983 belief-space contexts must survive serialization."""

    engine = _make_bound(_ATMSStore(claims=[])).atms_engine()
    environment = EnvironmentKey(("a1",), context_ids=("ctx1",))
    expected = {"assumption_ids": ["a1"], "context_ids": ["ctx1"]}

    assert engine._serialize_environment_key(environment) == expected
    assert engine._serialize_label(Label((environment,))) == [expected]

    engine.nogoods = NogoodSet([environment])
    detail = engine._serialize_nogood_detail(environment)
    assert detail.environment == expected

    assert _support_ids(environment) == expected

    future = ATMSNodeFutureStatusEntry(
        queryable_ids=(),
        queryable_cels=(),
        environment=(),
        consistent=True,
        status=ATMSNodeStatus.IN,
        out_kind=None,
        reason="supported",
        support_quality=SupportQuality.EXACT,
        essential_support=expected,
    )
    current = ATMSInspection(
        node_id="n1",
        status=ATMSNodeStatus.IN,
        support_quality=SupportQuality.EXACT,
        label=Label((environment,)),
        essential_support=environment,
        reason="supported",
    )

    future_report = ATMSFutureStatusReport(
        node_id="n1",
        claim_id=None,
        current=current,
        could_become_in=True,
        could_become_out=False,
        futures=(future,),
    )

    assert engine._serialize_future_entry(future)["essential_support"] == expected
    assert engine._serialize_future_report(future_report)["futures"][0][
        "essential_support"
    ] == expected
