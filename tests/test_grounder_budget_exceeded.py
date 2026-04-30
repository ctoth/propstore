from __future__ import annotations

from types import SimpleNamespace

import gunray


def test_grounder_returns_budget_exceeded_bundle_on_gunray_limit(monkeypatch) -> None:
    import propstore.grounding.grounder as grounder

    monkeypatch.setattr(grounder, "translate_to_theory", lambda *args, **kwargs: object())

    class FakeEvaluator:
        def evaluate_with_trace(self, *args, **kwargs):
            raise gunray.EnumerationExceeded(
                partial_arguments=("arg:partial",),  # type: ignore[arg-type]
                max_arguments=1,
                partial_trace=SimpleNamespace(
                    arguments=("arg:partial",),
                    grounding_inspection="inspection",
                ),
                reason="budget hit",
            )

    monkeypatch.setattr(gunray, "GunrayEvaluator", FakeEvaluator)

    bundle = grounder.ground([], (), object(), max_arguments=1)  # type: ignore[arg-type]

    assert bundle.status == "budget_exceeded"
    assert bundle.budget_reason == "budget hit"
    assert bundle.arguments == ("arg:partial",)
    assert bundle.grounding_inspection == "inspection"
