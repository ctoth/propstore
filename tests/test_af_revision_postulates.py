from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.belief_set import Atom, Formula, conjunction, negate
from argumentation.af_revision import (
    AFChangeKind,
    ExtensionRevisionState,
    baumann_2015_kernel_union_expand,
    cayrol_2014_classify_grounded_argument_addition,
    diller_2015_revise_by_framework,
    diller_2015_revise_by_formula,
    stable_kernel,
)
from argumentation.dung import ArgumentationFramework, grounded_extension, stable_extensions


pytestmark = pytest.mark.property

ARGUMENTS = frozenset({"a", "b", "c"})
A = Atom("a")
B = Atom("b")
C = Atom("c")
FORMULAS: tuple[Formula, ...] = (
    A,
    B,
    C,
    negate(A),
    conjunction(A, B),
    conjunction(A, negate(B)),
)

st_formula = st.sampled_from(FORMULAS)


@st.composite
def st_framework(draw) -> ArgumentationFramework:
    pairs = tuple((left, right) for left in sorted(ARGUMENTS) for right in sorted(ARGUMENTS))
    defeats = frozenset(draw(st.sets(st.sampled_from(pairs), max_size=5)))
    return ArgumentationFramework(arguments=ARGUMENTS, defeats=defeats)


@st.composite
def st_revision_state(draw) -> ExtensionRevisionState:
    extensions = tuple(frozenset(ext) for ext in stable_extensions(draw(st_framework())))
    if not extensions:
        extensions = (frozenset(),)
    ranking = {
        candidate: draw(st.integers(min_value=0, max_value=4))
        for candidate in ExtensionRevisionState.all_extensions(ARGUMENTS)
    }
    return ExtensionRevisionState.from_extensions(ARGUMENTS, extensions, ranking=ranking)


def _satisfies(extension: frozenset[str], formula: Formula) -> bool:
    return formula.evaluate(extension)


@pytest.mark.property
@given(st_framework(), st_framework())
@settings(deadline=None)
def test_baumann_brewka_2015_kernel_union_expansion_success_and_inclusion(
    base: ArgumentationFramework,
    new: ArgumentationFramework,
) -> None:
    expanded = baumann_2015_kernel_union_expand(base, new)
    union = ArgumentationFramework(
        arguments=base.arguments | new.arguments,
        defeats=frozenset(base.defeats | new.defeats),
        attacks=frozenset((base.attacks or base.defeats) | (new.attacks or new.defeats)),
    )

    assert base.arguments <= expanded.arguments
    assert new.arguments <= expanded.arguments
    assert expanded == stable_kernel(union)
    assert baumann_2015_kernel_union_expand(expanded, new) == expanded


@pytest.mark.property
@given(st_revision_state(), st_formula)
@settings(deadline=None)
def test_diller_2015_p_star_1_p_star_6_formula_revision(
    state: ExtensionRevisionState,
    formula: Formula,
) -> None:
    result = diller_2015_revise_by_formula(state, formula)

    assert all(_satisfies(extension, formula) for extension in result.extensions)
    if any(_satisfies(extension, formula) for extension in state.all_extensions(state.arguments)):
        assert result.extensions

    syntactic_variant = conjunction(formula, Atom("__top_guard__").or_(negate(Atom("__top_guard__"))))
    variant = diller_2015_revise_by_formula(state.with_argument("__top_guard__"), syntactic_variant)
    projected = tuple(frozenset(arg for arg in ext if arg != "__top_guard__") for ext in variant.extensions)
    assert frozenset(projected) == frozenset(result.extensions)

    satisfying = tuple(
        extension
        for extension in state.all_extensions(state.arguments)
        if _satisfies(extension, formula)
    )
    assert result.extensions == state.minimal_extensions(satisfying)


@pytest.mark.property
@given(st_revision_state(), st_framework())
@settings(deadline=None)
def test_diller_2015_a_star_1_a_star_6_framework_revision(
    state: ExtensionRevisionState,
    framework: ArgumentationFramework,
) -> None:
    target_extensions = tuple(stable_extensions(framework)) or (frozenset(),)
    result = diller_2015_revise_by_framework(state, framework, semantics="stable")

    assert frozenset(result.extensions) <= frozenset(target_extensions)
    if frozenset(state.extensions) & frozenset(target_extensions):
        assert frozenset(result.extensions) == frozenset(state.extensions) & frozenset(target_extensions)
    if target_extensions:
        assert result.extensions
    assert result.extensions == state.minimal_extensions(target_extensions)


@pytest.mark.property
@given(st_framework())
@settings(deadline=None)
def test_cayrol_2014_grounded_addition_is_never_restrictive_or_questioning(
    framework: ArgumentationFramework,
) -> None:
    added = "z"
    attacks = frozenset({(added, target) for target in grounded_extension(framework)})
    kind = cayrol_2014_classify_grounded_argument_addition(framework, added, attacks)

    assert kind not in {AFChangeKind.RESTRICTIVE, AFChangeKind.QUESTIONING}
