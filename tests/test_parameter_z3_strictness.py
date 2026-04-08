from pathlib import Path
from unittest.mock import patch

import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.conflict_detector.parameters import detect_parameter_conflicts
from propstore.loaded import LoadedEntry
from propstore.z3_conditions import Z3ConditionSolver, Z3TranslationError


def _make_claim_file(claims: list[dict]) -> LoadedEntry:
    return LoadedEntry(
        filename="test_paper",
        source_path=Path("/fake/test_paper.yaml"),
        data={"source": {"paper": "test_paper"}, "claims": claims},
    )


def test_z3_partition_failure_raises() -> None:
    cel_registry = {
        "freq": ConceptInfo(
            id="freq",
            canonical_name="freq",
            kind=KindType.QUANTITY,
        )
    }
    solver = Z3ConditionSolver(cel_registry)
    claim_file = _make_claim_file(
        [
            {"id": "p1", "type": "parameter", "concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "concept": "freq", "body": "300", "conditions": ["freq > 50"]},
        ]
    )

    with patch.object(
        solver,
        "partition_equivalence_classes",
        side_effect=Z3TranslationError("partition failed"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Z3 partitioning failed during parameter conflict detection",
        ):
            detect_parameter_conflicts([claim_file], cel_registry, solver=solver)
