from __future__ import annotations

from argumentation.af_revision import AFChangeKind, _classify_extension_change


def test_argumentation_pin_revision_classifier_uses_extension_content() -> None:
    assert (
        _classify_extension_change(
            (frozenset({"a"}), frozenset({"b"})),
            (frozenset({"a"}),),
        )
        is AFChangeKind.DECISIVE
    )
    assert (
        _classify_extension_change(
            (frozenset({"a"}),),
            (frozenset({"a", "b"}), frozenset({"a", "c"})),
        )
        is AFChangeKind.EXPANSIVE
    )
