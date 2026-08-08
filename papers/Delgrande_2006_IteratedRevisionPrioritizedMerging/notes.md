---
title: "Iterated Revision as Prioritized Merging"
authors: "James Delgrande, Didier Dubois, and Jérôme Lang"
year: 2006
venue: "KR 2006"
pages: "210-220"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# Iterated Revision as Prioritized Merging

## One-Sentence Summary

For reports about a static world, iterated revision is best modelled as prioritized merging of explicitly represented observations with reliability levels, not as automatic recency priority or mutation of an underlying entrenchment relation.

## Why Prioritized Merging

- Standard iterated revision accepts each new observation and thereby gives recency priority. In a static/inertial world, arrival order is not intrinsically informative: independent reports can arrive in any order and older reports can be closer to the event. (p. 210)
- Reports may instead have varying reliability. The appropriate problem is then to merge a prior epistemic state and observations, each explicitly evaluated for reliability, into one consistent belief result. (pp. 210-211)
- The paper distinguishes three scenarios: belief revision as defeasible inference from stable background conditionals; belief revision as incorporation of uncertain evidence; and revision of the background plausibility/entrenchment ordering itself. They require different operations and should not be conflated. (pp. 211-212)
- In the evidence-incorporation scenario, the prior epistemic state and observations are homogeneous uncertain evidence. Iteration is meaningful, but reliability need not equal recency. In defeasible inference, contingent observations query a stable entrenchment relation instead of revising it. (pp. 211-212)

## Typed Reliability Inputs

- A prioritized observation base is a sequence of multisets of consistent propositional formulas, one multiset per reliability level. Equivalently, each observation formula can carry a reliability degree, subject to a total preorder. Higher index/degree means more reliable. (p. 213)
- Prior beliefs are not a special object in this model; if present they are another prioritized formula or set of formulas. The operator consumes the whole represented observation base rather than a loose map supplied beside an otherwise unrelated revision call. (p. 213)
- Reliability must not be confused with likelihood. Reliability is confidence in the source of an observation; the observation may be highly reliable even when what it reports is an unlikely event. The paper relates reliability levels to evidence theory, belief functions, and possibilistic necessity/entrenchment. (p. 213)

## Operators and Postulates

- A prioritized merging operator maps a prioritized observation base to a formula. Equal reliability reduces to commutative merging; one item per level yields the standard iterated-revision shape. Best-out, discrimin, leximin, and linear merging embody different policies for retaining consistent subsets. (pp. 214-215)
- The core postulates require priority monotonicity, consistency, tautology invariance, optimism when all inputs are jointly consistent, syntax invariance, and generalized success. Right associativity permits sequential computation and connects constrained flat merging to prioritized merging. (pp. 215-216)
- Restricting prioritized merging to two-level ordered bases recovers the AGM revision postulates. Most iterated-revision postulates examined follow from the merging postulates. (pp. 217-218)
- Darwiche-Pearl C2 is singled out as controversial because it makes a more reliable contradictory observation totally override a weaker compound observation, even discarding its compatible parts. Adding C2 collapses the allowable operator to linear merging. (p. 218)

## Complex Observations

- A formula plus a reliability level divides worlds only into accepted/rejected states. More expressive observations can themselves be epistemic states or ordinal conditional/kappa functions, making the task one of merging epistemic states. (pp. 218-219)
- Kappa/possibility formulations demonstrate that a sound numerical design represents the semantics of observations and combination, rather than treating numbers as unconstrained precedence knobs. (p. 219)

## Propstore Decision Relevance

- Source reliability is a real capability, but its owner is an evidence/prioritized-observation model and a specified merge operator. It is not a field-prefix override of support-revision entrenchment.
- `source_paper` provenance should remain represented at the claim/Micropublication evidence owner. A future policy may evaluate that evidence and construct typed reliability levels, but the policy must state scale semantics, comparison scope, aggregation, and the merge operator.
- `context` is not shown by this paper to be a string prefix for reliability. A context-dependent policy would need a typed context and evidence interpretation before it could construct a prioritized observation base.
- The existing test-only override therefore should be deleted, not wired. Doing so removes a misleading conflation without foreclosing a future generic prioritized-evidence capability.

## Limitations

- The main framework assumes observations describe the same static world and uses finite propositional logic. (pp. 210, 213)
- The paper does not specify how a real system estimates source reliability or reconciles multiple provenance signals; those are upstream evidence-policy questions. (pp. 213, 219-220)

## Collection Cross-References

### Already in Collection

- [A Mathematical Theory of Evidence](../Shafer_1976_MathematicalTheoryEvidence/notes.md) - supplies the evidence-theoretic interpretation of unreliable testimony that the paper distinguishes from likelihood.
- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gardenfors_1988_RevisionsKnowledgeSystemsEntrenchment/notes.md) - supplies the AGM entrenchment tradition against which the paper separates evidence incorporation, defeasible inference, and revision of background knowledge.

### New Leads (Not Yet in Collection)

- Dubois and Prade (1991) - “Epistemic entrenchment and possibilistic logic” - links reliability levels, necessity, and formal entrenchment.
- Konieczny and Pino-Pérez (2002) - “Merging information under constraints: a qualitative framework” - provides the flat-merging representation results lifted here to prioritized merging.
- Darwiche and Pearl (1997) - “On the logic of iterated belief revision” - provides the iterated-revision postulates, including the controversial C2 total-override rule.

### Supersedes or Recontextualizes

- (none)

### Cited By (in Collection)

- (none found)

### Conceptual Links (not citation-based)

- [Modellings for Belief Change: Prioritization and Entrenchment](../Rott_1992_ModellingsBeliefChangePrioritization/notes.md) - both prevent direct identification of priority with entrenchment; Rott derives retractability from base contraction, while this paper makes report reliability an input to merging.
- [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - both preserve evidence-state information above propositional commitment and reject silent information loss during combination, using different uncertainty formalisms.
