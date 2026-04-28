from __future__ import annotations

import pytest

from argumentation.aspic import (
    ArgumentationSystem,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    Rule,
)
from argumentation.aspic_encoding import encode_aspic_theory


def test_argumentation_pin_rejects_duplicate_defeasible_rule_names() -> None:
    p = Literal(GroundAtom("p"))
    q = Literal(GroundAtom("q"))
    r = Literal(GroundAtom("r"))
    system = ArgumentationSystem(
        language=frozenset({p, q, r}),
        contrariness=ContrarinessFn(frozenset()),
        strict_rules=frozenset(),
        defeasible_rules=frozenset(
            {
                Rule((p,), q, "defeasible", "dup"),
                Rule((p,), r, "defeasible", "dup"),
            }
        ),
    )

    with pytest.raises(ValueError, match="duplicate defeasible rule name"):
        encode_aspic_theory(
            system,
            KnowledgeBase(axioms=frozenset({p}), premises=frozenset()),
            PreferenceConfig(frozenset(), frozenset(), comparison="elitist", link="last"),
        )
