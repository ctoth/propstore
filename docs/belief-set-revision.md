# Belief-Set Revision

Formal belief dynamics live in the external `formal-belief-set` dependency and
are imported as `belief_set`. They are separate from
`propstore.support_revision`, which is an operational support-incision adapter
for scoped worldline capture and must not be cited as AGM revision.

## Core Model

`belief_set.core.BeliefSet` represents a finite propositional theory
extensionally by its models over an explicit atom alphabet. `Cn` is therefore
the model-equivalence closure of the represented theory: `BeliefSet.cn()`
returns the closed theory object, `entails(formula)` checks truth in every
model, and `expand(belief_set, formula)` intersects the model set with the
formula's models.

The formula language is in `belief_set.language`: `Atom`, `Not`, `And`, `Or`,
`Top`, and `Bottom`. The current implementation is intentionally
finite and truth-table based so the postulate tests can quantify over complete
small languages.

## AGM And Iteration

`belief_set.agm` implements revision over
`SpohnEpistemicState`, a finite ordinal conditional function over all worlds.
`revise(state, formula)` promotes the most plausible formula-worlds and
returns a `RevisionOutcome` with package-local trace metadata.
`full_meet_contract(state, formula)` uses the Harper identity over the finite
theory.

The literature target is Alchourron-Gärdenfors-Makinson 1985 for AGM revision
and contraction, Gärdenfors-Makinson 1988 for epistemic entrenchment,
Darwiche-Pearl 1997 for iterated revision, and Booth-Meyer 2006 for
restrained revision over preorders. `belief_set.entrenchment.EpistemicEntrenchment` derives
formula entrenchment from a Spohn state by ranking negated formulas.

`belief_set.iterated` contains preorder-level operators:
`lexicographic_revise` puts all input-worlds before all countermodels while
preserving internal order, and `restrained_revise` performs the conservative
Spohn update used by the Booth-Meyer restrained family. These are the formal
operators; the support-incision package does not implement these literature
definitions.

## Gates

The postulate gate is property-based in the external package:

- `belief-set/tests/test_belief_set_postulates.py` covers `Cn`, AGM revision and
  contraction, Harper/Levi-style identities, Darwiche-Pearl C1-C4,
  Gardenfors-Makinson entrenchment conditions, and IC merge postulates.
- `belief-set/tests/test_belief_set_iterated_postulates.py` covers lexicographic and
  restrained preorder behavior.
- `tests/test_revision_retirement.py` prevents the retired
  `propstore.revision` import path from returning.

Use `propstore.support_revision` only when the desired behavior is
support-incision over the current ATMS-supported worldline projection. Use
`belief_set` for formal AGM, entrenchment, and iterated belief revision.

## Propstore Adapter Boundary

Propstore consumes the formal dependency through exactly one production import
edge: `propstore.support_revision.belief_set_adapter`. That adapter projects a
scoped support-revision `BeliefBase` to a formal `BeliefSet`, calls the
dependency-owned formal decision surfaces, and returns typed decision reports.

`propstore.support_revision.belief_dynamics`, `realization`, `iterated`, and
`entrenchment` do not own formal AGM kernels. They realize dependency decisions
over Propstore support objects and keep the result split into:

- `decision`: formulas, formal policy, formal trace, and epistemic-state hash
  where relevant.
- `realization`: accepted/rejected atom ids, support incision set, source claim
  provenance, and support-derived reasons.

## Not Implemented

These are not present in `belief_set` and should not be inferred from
the currently implemented revision, contraction, or iterated operators:

- AGM partial-meet contraction, selection functions `gamma`, and maxichoice
  contraction from Alchourron-Gärdenfors-Makinson 1985, especially the
  remainder-set construction in Section 4.
- Levi and Harper as first-class composer APIs. `revise` and
  `full_meet_contract` satisfy the relevant finite identities, but there is no
  public operator-composition surface for them; AGM Observation 2.3 is the
  cited target in Alchourron-Gärdenfors-Makinson 1985 p.513.
- Grove 1988 systems of spheres. `SpohnEpistemicState` is an OCF surface, not a
  sphere-system representation.
- Katsuno-Mendelzon update from Katsuno-Mendelzon 1991. The current operators
  are belief revision/contraction operators, not update operators.
- Hansson safe contraction and belief-base operation families. The
  `propstore.support_revision` incision machinery is an operational
  support-loss workflow, not Hansson belief-base contraction.
- The full Booth-Meyer admissible-revision family. The restrained operator
  covers the Booth-Meyer 2006 restrained-revision construction; the broader AR
  family remains deferred.

The propositional AGM items above are tracked as future implementation work in
REMEDIATION-PLAN T6.5. They are intentionally documented as absent until the
target architecture adds the full surfaces rather than local approximations.
