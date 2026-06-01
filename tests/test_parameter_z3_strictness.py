from unittest.mock import patch

import pytest

from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts
from propstore.core.conditions.solver import ConditionSolver, Z3TranslationError


def test_z3_partition_failure_raises() -> None:
    cel_registry = {
        "freq": ConceptInfo(
            id="freq",
            canonical_name="freq",
            kind=KindType.QUANTITY,
        ),
        "source": ConceptInfo(
            id="source",
            canonical_name="source",
            kind=KindType.CATEGORY,
            category_values=["test_paper"],
            category_extensible=False,
        ),
    }
    solver = ConditionSolver(cel_registry)
    claims = _make_claims(
        [
            {
                "id": "p1",
                "type": "parameter",
                "concept": "freq",
                "body": "100",
                "conditions": ["freq > 50"],
            },
            {
                "id": "p2",
                "type": "parameter",
                "concept": "freq",
                "body": "200",
                "conditions": ["freq > 50"],
            },
            {
                "id": "p3",
                "type": "parameter",
                "concept": "freq",
                "body": "300",
                "conditions": ["freq > 50"],
            },
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
            detect_parameter_conflicts(claims, cel_registry, solver=solver)
