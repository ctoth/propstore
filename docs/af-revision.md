# AF Revision

`propstore.belief_set.af_revision` is the formal abstract-argumentation change
surface for WS-B. It is distinct from `propstore.support_revision.af_adapter`,
which only projects a support-incision state into argumentation-facing inputs.

## Implemented Surfaces

`baumann_2015_kernel_union_expand(base, new)` implements the Baumann-style
kernel-union expansion shape over Dung frameworks: arguments, defeats, and
attacks are unioned into the expanded framework.

`ExtensionRevisionState` represents Diller-style extension revision with a
faithful ranking over all extension candidates for a finite argument universe.
`diller_2015_revise_by_formula(state, formula)` selects the minimal ranked
extensions satisfying a formula. `diller_2015_revise_by_framework(state,
framework, semantics="stable")` revises toward the stable extensions of a
target framework, preserving overlap when possible and otherwise selecting
minimal faithful candidates.

`cayrol_2014_classify_grounded_argument_addition(framework, argument, attacks)`
classifies the effect of adding an argument under grounded semantics using the
WS-B taxonomy values in `AFChangeKind`: decisive, restrictive, questioning,
destructive, expansive, conservative, and altering.

## Gates

`tests/test_af_revision_postulates.py` property-tests the implemented Baumann,
Diller, and Cayrol-facing behavior over finite frameworks and extension
candidates. The Diller-facing checks exercise faithful ranking behavior; the
Baumann-facing checks exercise expansion by kernel union; the Cayrol-facing
checks exercise grounded-extension change classification.

## Boundaries

Do not cite `propstore.support_revision.af_adapter` as AF revision. It is a
projection adapter for current accepted support atoms. Formal AF revision lives
in `propstore.belief_set.af_revision`.
