from __future__ import annotations

from hypothesis import given, strategies as st
import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.z3_conditions import Z3ConditionSolver, Z3TranslationError


@pytest.mark.property
@given(
    original=st.lists(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1),
        min_size=1,
        max_size=4,
        unique=True,
    ),
    added=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
    ),
)
def test_z3_solver_snapshots_category_registry(original: list[str], added: str) -> None:
    if added in original:
        return
    registry = {
        "kind": ConceptInfo(
            "kind-id",
            "kind",
            KindType.CATEGORY,
            category_values=list(original),
            category_extensible=False,
        )
    }
    solver = Z3ConditionSolver(registry)

    registry["kind"].category_values.append(added)

    with pytest.raises(Z3TranslationError, match="not in value set|Unknown category value"):
        solver.is_condition_satisfied(f"kind == '{added}'", {"kind": added})
