from __future__ import annotations

from argumentation.dung import ArgumentationFramework
from argumentation.enforcement import (
    enforce_expansion_credulous,
    enforce_liberal_expansion_extension,
    is_normal_expansion,
)


def test_argumentation_pin_exposes_expansion_enforcement_surface() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )

    result = enforce_expansion_credulous(
        framework,
        "b",
        semantics="preferred",
        kind="normal",
        candidate_new_arguments=frozenset({"x1"}),
        max_new_arguments=1,
        max_added_defeats=1,
    )

    assert result.expansion.new_arguments == frozenset({"x1"})
    assert result.expansion.added_defeats == frozenset({("x1", "a")})
    assert framework.defeats <= result.witness_framework.defeats
    assert is_normal_expansion(framework, result.witness_framework)
    assert any("b" in extension for extension in result.extensions)


def test_argumentation_pin_exposes_liberal_enforcement_surface() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a1", "a2", "a3", "a4", "a5"}),
        defeats=frozenset(
            {
                ("a1", "a2"),
                ("a3", "a2"),
                ("a3", "a4"),
                ("a4", "a3"),
                ("a4", "a5"),
                ("a5", "a5"),
            }
        ),
    )
    target = frozenset({"a1", "a3"})

    result = enforce_liberal_expansion_extension(
        framework,
        target,
        source_semantics="stable",
        target_semantics="preferred",
        variant="strict",
        candidate_new_arguments=frozenset(),
        max_new_arguments=0,
        max_added_defeats=0,
    )

    assert result.source_semantics == "stable"
    assert result.semantics == "preferred"
    assert result.cost == 0
    assert result.witness_framework == framework
