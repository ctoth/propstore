from __future__ import annotations

from argumentation.dung import ArgumentationFramework
from argumentation.dynamic import (
    DynamicUpdate,
    IncrementalDynamicArgumentationFramework,
    incremental_extension_update,
)


def test_argumentation_pin_exposes_dynamic_incremental_update_surface() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c", "d", "e"}),
        defeats=frozenset(
            {
                ("a", "b"),
                ("b", "c"),
                ("b", "d"),
                ("c", "d"),
                ("c", "e"),
                ("e", "c"),
            }
        ),
    )

    result = incremental_extension_update(
        framework,
        DynamicUpdate("add_att", "d", "d"),
        semantics="preferred",
        initial_extension=frozenset({"a", "d", "e"}),
    )

    assert result.influenced == frozenset({"d"})
    assert result.reduced_extension == frozenset()
    assert result.extension == frozenset({"a", "e"})
    assert result.used_incremental is True


def test_argumentation_pin_exposes_dynamic_query_metadata() -> None:
    dynamic = IncrementalDynamicArgumentationFramework(
        ArgumentationFramework(arguments=frozenset({"a"}), defeats=frozenset()),
        semantics="grounded",
        current_extension=frozenset({"a"}),
    )

    result = dynamic.apply(DynamicUpdate("add_arg", "b"))
    answer = dynamic.query_skeptical("b")

    assert result.used_incremental is False
    assert result.fallback_reason == "unsupported_update_kind"
    assert answer.accepted is True
    assert answer.witness == frozenset({"a", "b"})
