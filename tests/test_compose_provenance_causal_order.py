from __future__ import annotations

from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    compose_provenance,
)


def _record(name: str, operations: tuple[str, ...]) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        graph_name=f"urn:graph:{name}",
        operations=operations,
        witnesses=(
            ProvenanceWitness(
                asserter=f"urn:agent:{name}",
                timestamp="2026-04-30T00:00:00Z",
                source_artifact_code=f"{name}:p1",
                method="read",
            ),
        ),
    )


def test_compose_provenance_preserves_input_causal_order() -> None:
    left = _record("left", ("read-left", "normalize-left"))
    right = _record("right", ("read-right",))

    composed = compose_provenance(left, right, operation="merge")

    assert composed.operations == (
        "read-left",
        "normalize-left",
        "read-right",
        "merge",
    )


def test_compose_provenance_is_order_sensitive_for_distinct_chains() -> None:
    left = _record("left", ("read-left",))
    right = _record("right", ("read-right",))

    assert compose_provenance(left, right, operation="merge").operations != compose_provenance(
        right,
        left,
        operation="merge",
    ).operations
