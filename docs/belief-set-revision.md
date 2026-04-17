# Belief-Set Revision

`propstore.belief_set` is the formal belief dynamics layer. It is separate
from `propstore.support_revision`, which is an operational support-incision
adapter for scoped worldline capture and must not be cited as AGM revision.

## Core Model

`propstore.belief_set.core.BeliefSet` represents a finite propositional theory
extensionally by its models over an explicit atom alphabet. `Cn` is therefore
the model-equivalence closure of the represented theory: `BeliefSet.cn()`
returns the closed theory object, `entails(formula)` checks truth in every
model, and `expand(belief_set, formula)` intersects the model set with the
formula's models.

The formula language is in `propstore.belief_set.language`: `Atom`, `Not`,
`And`, `Or`, `Top`, and `Bottom`. The current implementation is intentionally
finite and truth-table based so the postulate tests can quantify over complete
small languages.

## AGM And Iteration

`propstore.belief_set.agm` implements revision over
`SpohnEpistemicState`, a finite ordinal conditional function over all worlds.
`revise(state, formula)` promotes the most plausible formula-worlds and
returns a `RevisionOutcome` with a provenance-bearing `RevisionTrace`.
`full_meet_contract(state, formula)` uses the Harper identity over the finite
theory.

The literature target is Alchourron-Gardenfors-Makinson 1985 for AGM revision
and contraction, Gardenfors 1988 for epistemic entrenchment, Darwiche-Pearl
1997 for iterated revision, and Booth 2006 for restrained revision over
preorders. `propstore.belief_set.entrenchment.EpistemicEntrenchment` derives
formula entrenchment from a Spohn state by ranking negated formulas.

`propstore.belief_set.iterated` contains preorder-level operators:
`lexicographic_revise` puts all input-worlds before all countermodels while
preserving internal order, and `restrained_revise` performs the conservative
Spohn update used by the Booth-Meyer restrained family. These are the formal
operators; the support-incision package does not implement these literature
definitions.

## Gates

The postulate gate is property-based:

- `tests/test_belief_set_postulates.py` covers `Cn`, AGM revision and
  contraction, Harper/Levi-style identities, Darwiche-Pearl C1-C4,
  Gardenfors-Makinson entrenchment conditions, and IC merge postulates.
- `tests/test_belief_set_iterated_postulates.py` covers lexicographic and
  restrained preorder behavior.
- `tests/test_revision_retirement.py` prevents the retired
  `propstore.revision` import path from returning.

Use `propstore.support_revision` only when the desired behavior is
support-incision over the current ATMS-supported worldline projection. Use
`propstore.belief_set` for formal AGM, entrenchment, and iterated belief
revision.
