# Revision Postulate Product Gap

Date: 2026-04-16

Workstream phase: Phase 8, Revision Postulate Properties

Grounding:

- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png`
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png`

## Finding

The current `propstore.revision` implementation exposes finite belief-base
operators over support incision:

- `expand`
- `contract`
- `revise`
- `stabilize_belief_base`
- iterated ranking updates over `EpistemicState`

It does not expose the full Diller et al. 2015 semantic surface of revision by
propositional formulas or by argumentation frameworks as sets of extensions.
In particular, the model/extension-intersection postulates corresponding to
the paper's P*5/P*6 and A*5/A*6 cannot be tested directly without a production
interface that accepts formulas or AFs and returns the revised extension set.

## Kept Coverage

`tests/test_revision_properties.py` now adds generated postulate checks for
the behavior this code does expose:

- success for satisfiable, nonconflicting inputs
- consistency as non-empty accepted results with disjoint accepted/rejected IDs
- syntax irrelevance for equivalent claim inputs
- inclusion on expansion
- idempotence of stabilization

## Needed Follow-Up

Add a dedicated revision-semantics workstream if propstore should implement
the paper-level Diller operators directly:

- formula/AF revision input surface
- extension-set semantics for revision outputs
- postulate tests for P*1-P*6, A*1-A*6, and Acyc over bounded generated AFs
