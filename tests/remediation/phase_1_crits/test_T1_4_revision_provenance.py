from __future__ import annotations

from datetime import datetime, timezone

from propstore.belief_set import Atom, BeliefSet, SpohnEpistemicState, revise
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


P = Atom("p")
Q = Atom("q")
ALPHABET = frozenset({"p", "q"})


def _state() -> SpohnEpistemicState:
    return SpohnEpistemicState.from_belief_set(
        BeliefSet.from_formula(ALPHABET, P),
    )


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_revision_trace_uses_supplied_provenance_and_real_timestamp() -> None:
    supplied = Provenance(
        status=ProvenanceStatus.CALIBRATED,
        witnesses=(
            ProvenanceWitness(
                asserter="unit-test",
                timestamp="2026-04-20T00:00:00Z",
                source_artifact_code="unit-test-source",
                method="test",
            ),
        ),
        graph_name="urn:unit-test:revision-provenance",
    )

    before = datetime.now(timezone.utc)
    result = revise(_state(), Q, provenance=supplied)
    after = datetime.now(timezone.utc)

    trace = result.trace
    assert trace.provenance == supplied
    assert before <= trace.timestamp <= after


def test_revision_defaults_vacuous_not_stated_or_epoch() -> None:
    before = datetime.now(timezone.utc)
    result = revise(_state(), Q)
    after = datetime.now(timezone.utc)

    trace = result.trace
    assert trace.provenance.status is ProvenanceStatus.VACUOUS
    assert before <= trace.timestamp <= after
    assert all(
        _parse_utc(witness.timestamp).year != 1970
        for witness in trace.provenance.witnesses
    )
