"""Composition keeps the weakest honest status visible — including VACUOUS.

The rank comment in propstore/provenance says a derived value is no more
trustworthy than its least-grounded input. A vacuous input is the
least-grounded input possible (Jøsang 2001: total ignorance), so composing
it with any graded status must yield VACUOUS — ignorance is never laundered
out of a derivation chain.
"""

from __future__ import annotations

from propstore.provenance import Provenance, ProvenanceStatus, compose_provenance


def _record(status: ProvenanceStatus) -> Provenance:
    return Provenance(
        status=status,
        witnesses=(),
        operations=(f"origin:{status.value}",),
    )


def _composed_status(*statuses: ProvenanceStatus) -> ProvenanceStatus:
    return compose_provenance(
        *(_record(status) for status in statuses), operation="test"
    ).status


def test_vacuous_survives_composition_with_any_graded_status() -> None:
    for graded in (
        ProvenanceStatus.MEASURED,
        ProvenanceStatus.CALIBRATED,
        ProvenanceStatus.STATED,
        ProvenanceStatus.DEFAULTED,
    ):
        assert _composed_status(ProvenanceStatus.VACUOUS, graded) is (
            ProvenanceStatus.VACUOUS
        ), graded
        assert _composed_status(graded, ProvenanceStatus.VACUOUS) is (
            ProvenanceStatus.VACUOUS
        ), graded


def test_existing_relative_order_of_graded_statuses_is_unchanged() -> None:
    assert (
        _composed_status(ProvenanceStatus.STATED, ProvenanceStatus.MEASURED)
        is ProvenanceStatus.MEASURED
    )
    assert (
        _composed_status(ProvenanceStatus.MEASURED, ProvenanceStatus.CALIBRATED)
        is ProvenanceStatus.CALIBRATED
    )
    assert (
        _composed_status(ProvenanceStatus.CALIBRATED, ProvenanceStatus.DEFAULTED)
        is ProvenanceStatus.DEFAULTED
    )
