from __future__ import annotations

from propstore.families.claims.passes.checks import validate_claim_semantics
from tests.conftest import make_compilation_context


def test_algorithm_local_assignments_are_not_reported_as_unbound_names() -> None:
    diagnostics = []
    claim = {
        "type": "algorithm",
        "output_concept": "concept1",
        "body": "def algorithm(x):\n    y = x + 1\n    return y\n",
        "variables": [{"symbol": "x", "concept": "concept1"}],
    }

    validate_claim_semantics(
        claim,
        "claim1",
        "claims.yaml",
        make_compilation_context(),
        diagnostics,
    )

    assert all("name 'y' not declared" not in diagnostic.message for diagnostic in diagnostics)
