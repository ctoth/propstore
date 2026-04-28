from __future__ import annotations

from argumentation.dung import ArgumentationFramework, admissible, ideal_extension


def test_argumentation_pin_ideal_extension_handles_mutual_defense() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b", "x", "y"}),
        defeats=frozenset(
            {
                ("x", "a"),
                ("x", "x"),
                ("b", "x"),
                ("y", "b"),
                ("y", "y"),
                ("a", "y"),
            }
        ),
    )

    ideal = ideal_extension(framework)

    assert ideal == frozenset({"a", "b"})
    assert admissible(ideal, framework.arguments, framework.defeats)
