"""Extension semantics over a directly-constructed StructuredProjection (Phase 6b).

The store/world-backed projection tests (``build_aspic_projection`` over a
``BoundWorld``, worldline capture, the ``world extensions`` CLI) are deferred to
the world layer (Phase 7). Ported here is the Phase-6-pure subset: the ASPIC+
extension semantics computed by ``compute_structured_justified_arguments`` over a
``StructuredProjection`` built by hand, including the attack-aware grounded
meaning and the claim-graph-only semantics rejection.
"""

from __future__ import annotations

import pytest
from argumentation.core.dung import ArgumentationFramework, complete_extensions
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.structured_projection import (
    StructuredProjection,
    SupportQuality,
    compute_structured_justified_arguments,
)


def _projection(framework: ArgumentationFramework) -> StructuredProjection:
    return StructuredProjection(
        arguments=(),
        framework=framework,
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )


@st.composite
def _frameworks_with_optional_attacks(draw: st.DrawFn) -> ArgumentationFramework:
    n_args = draw(st.integers(min_value=1, max_value=4))
    arguments = tuple(f"arg:{idx}" for idx in range(n_args))
    possible_edges = [(src, tgt) for src in arguments for tgt in arguments if src != tgt]
    if possible_edges:
        defeats = frozenset(
            draw(st.sets(st.sampled_from(possible_edges), max_size=len(possible_edges)))
        )
    else:
        defeats = frozenset()
    attacks_choice = draw(st.sampled_from(["none", "same", "arbitrary"]))
    if attacks_choice == "none":
        attacks: frozenset[tuple[str, str]] | None = None
    elif attacks_choice == "same":
        attacks = defeats
    else:
        attacks = (
            frozenset(
                draw(st.sets(st.sampled_from(possible_edges), max_size=len(possible_edges)))
            )
            if possible_edges
            else frozenset()
        )
    return ArgumentationFramework(arguments=frozenset(arguments), defeats=defeats, attacks=attacks)


def test_support_quality_is_re_exported() -> None:
    assert SupportQuality.EXACT.value == "exact"


def test_aspic_grounded_semantics_respects_attacks_when_attacks_exist() -> None:
    projection = _projection(
        ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset({("arg:a", "arg:b"), ("arg:b", "arg:a")}),
        )
    )

    justified = compute_structured_justified_arguments(projection, semantics="grounded")

    assert justified == frozenset()


def test_structured_projection_rejects_claim_graph_only_semantics() -> None:
    projection = _projection(
        ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset(),
            attacks=frozenset(),
        )
    )

    with pytest.raises(ValueError, match="does not support semantics"):
        compute_structured_justified_arguments(projection, semantics="d-preferred")


@pytest.mark.property
@given(framework=_frameworks_with_optional_attacks())
@settings(deadline=None)
def test_aspic_grounded_semantics_matches_least_complete_extension(
    framework: ArgumentationFramework,
) -> None:
    projection = _projection(framework)

    justified = compute_structured_justified_arguments(projection, semantics="grounded")

    complete = [frozenset(ext) for ext in complete_extensions(framework)]
    expected = (
        frozenset()
        if not complete
        else min(complete, key=lambda ext: (len(ext), tuple(sorted(ext))))
    )
    assert justified == expected
