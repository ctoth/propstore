from __future__ import annotations

import pytest

import bridgman


def test_bridgman_pin_is_post_verify_equation_deletion() -> None:
    assert bridgman.__version__ >= "0.2.0"
    assert not hasattr(bridgman, "verify_equation")
    with pytest.raises(ImportError):
        from bridgman import verify_equation  # noqa: F401
