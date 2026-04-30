from __future__ import annotations

from types import SimpleNamespace

import gunray


def test_grounder_default_uses_trace_and_returns_arguments(monkeypatch) -> None:
    import propstore.grounding.grounder as grounder

    calls: list[tuple[str, int | None]] = []
    monkeypatch.setattr(grounder, "translate_to_theory", lambda *args, **kwargs: object())

    class FakeEvaluator:
        def evaluate_with_trace(self, *args, max_arguments=None, **kwargs):
            calls.append(("evaluate_with_trace", max_arguments))
            model = SimpleNamespace(sections={"yes": {"bird": {("tweety",)}}})
            trace = SimpleNamespace(
                arguments=("arg:bird-tweety",),
                grounding_inspection="inspection",
            )
            return model, trace

    monkeypatch.setattr(gunray, "GunrayEvaluator", FakeEvaluator)

    bundle = grounder.ground([], (), object())  # type: ignore[arg-type]

    assert calls == [("evaluate_with_trace", None)]
    assert bundle.arguments == ("arg:bird-tweety",)
    assert bundle.grounding_inspection == "inspection"
