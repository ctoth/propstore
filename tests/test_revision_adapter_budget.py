from __future__ import annotations

import pytest

from belief_set import AlphabetBudgetExceeded

from propstore.support_revision.belief_set_adapter import project_formal_bundle
from propstore.support_revision.state import BeliefBase, RevisionScope
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def test_formal_projection_rejects_oversized_alphabet_with_typed_budget_error() -> None:
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=tuple(make_assertion_atom(f"atom_{index}") for index in range(17)),
    )

    with pytest.raises(AlphabetBudgetExceeded) as exc_info:
        project_formal_bundle(base, max_alphabet_size=16)

    assert exc_info.value.alphabet_size == 17
    assert exc_info.value.max_alphabet_size == 16
