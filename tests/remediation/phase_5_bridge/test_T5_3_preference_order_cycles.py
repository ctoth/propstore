import pytest

from argumentation.aspic import GroundAtom, Literal
from argumentation.preference import strict_partial_order_closure
from propstore.aspic_bridge import translate


def _bridge_preference_closure():
    return getattr(translate, "_transitive_closure", strict_partial_order_closure)


def test_preference_order_closure_detects_cycles() -> None:
    a = Literal(GroundAtom("a"))
    b = Literal(GroundAtom("b"))
    c = Literal(GroundAtom("c"))

    with pytest.raises(ValueError, match="cycle"):
        _bridge_preference_closure()({(a, b), (b, c), (c, a)})
