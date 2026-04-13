from __future__ import annotations

import pytest

from propstore.dung import ArgumentationFramework, preferred_extensions


def test_preferred_extensions_explicit_brute_backend_does_not_fall_back_to_z3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({f"a{i}" for i in range(13)}),
        defeats=frozenset(
            (f"a{i}", f"a{(i + 1) % 13}")
            for i in range(13)
        ),
    )

    def _boom(_framework: ArgumentationFramework):
        raise AssertionError("z3 backend should not be used for explicit brute requests")

    monkeypatch.setattr("propstore.dung_z3.z3_complete_extensions", _boom)

    preferred_extensions(framework, backend="brute")
