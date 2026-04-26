"""WS8 base-rate resolution over situated assertion identity."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from propstore.core.base_rates import (
    BaseRateProfile,
    BaseRateResolved,
    BaseRateResolver,
    BaseRateUnresolved,
)
from propstore.core.id_types import AssertionId
from propstore.provenance import Provenance, ProvenanceStatus


def _aid(name: str) -> AssertionId:
    return AssertionId(f"ps:assertion:{name}")


def _provenance(operation: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.CALIBRATED,
        witnesses=(),
        operations=(operation,),
    )


def test_missing_base_rate_is_unresolved_not_half() -> None:
    result = BaseRateResolver(()).resolve(_aid("claim"))

    assert isinstance(result, BaseRateUnresolved)
    assert result.assertion_id == _aid("claim")
    assert result.reason == "missing_base_rate"


def test_base_rate_profile_resolves_for_assertion_id() -> None:
    profile = BaseRateProfile(
        profile_assertion_id=_aid("psychology_replication_rate"),
        target_assertion_id=_aid("psychology_claim"),
        value=0.36,
        evidence_assertion_ids=(_aid("aarts_2015_replication_rate"),),
        provenance=_provenance("aarts_2015_replication_notes"),
    )

    result = BaseRateResolver((profile,)).resolve(_aid("psychology_claim"))

    assert isinstance(result, BaseRateResolved)
    assert result.value == 0.36
    assert result.profile_assertion_id == _aid("psychology_replication_rate")
    assert result.evidence_assertion_ids == (_aid("aarts_2015_replication_rate"),)
    assert result.provenance.status == ProvenanceStatus.CALIBRATED


def test_base_rate_profile_requires_assertion_ids() -> None:
    try:
        BaseRateProfile(
            profile_assertion_id=AssertionId("not-an-assertion"),
            target_assertion_id=_aid("claim"),
            value=0.36,
            provenance=_provenance("bad_profile"),
        )
    except ValueError as exc:
        assert "profile_assertion_id" in str(exc)
    else:
        raise AssertionError("base-rate profiles must be authored as assertions")


def test_recursive_base_rate_dependency_is_unresolved() -> None:
    first = BaseRateProfile(
        profile_assertion_id=_aid("first_profile"),
        target_assertion_id=_aid("first"),
        value=0.36,
        dependency_assertion_ids=(_aid("second"),),
        stratum=1,
        provenance=_provenance("first"),
    )
    second = BaseRateProfile(
        profile_assertion_id=_aid("second_profile"),
        target_assertion_id=_aid("second"),
        value=0.61,
        dependency_assertion_ids=(_aid("first"),),
        stratum=1,
        provenance=_provenance("second"),
    )

    result = BaseRateResolver((first, second)).resolve(_aid("first"))

    assert isinstance(result, BaseRateUnresolved)
    assert result.reason == "recursive_base_rate"
    assert result.missing_fields == ("base_rate_profile",)


@given(st.lists(st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False), min_size=1, max_size=8))
def test_stratified_base_rate_chain_terminates(values: list[float]) -> None:
    profiles = tuple(
        BaseRateProfile(
            profile_assertion_id=_aid(f"profile_{idx}"),
            target_assertion_id=_aid(f"target_{idx}"),
            value=value,
            dependency_assertion_ids=(() if idx == 0 else (_aid(f"target_{idx - 1}"),)),
            stratum=idx,
            provenance=_provenance(f"profile_{idx}"),
        )
        for idx, value in enumerate(values)
    )

    result = BaseRateResolver(profiles).resolve(_aid(f"target_{len(values) - 1}"))

    assert isinstance(result, BaseRateResolved)
    assert result.value == values[-1]
