---
title: "Revisions of Knowledge Systems Using Epistemic Entrenchment"
authors: "Peter Gärdenfors and David Makinson"
year: 1988
venue: "TARK II"
pages: "83-95"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# Revisions of Knowledge Systems Using Epistemic Entrenchment

## One-Sentence Summary

Epistemic entrenchment is a logically constrained qualitative ordering of propositions relative to a knowledge set, and the paper proves that such orderings and AGM-compliant contraction functions determine one another.

## Problem and Setup

- Revision incorporates information inconsistent with the current knowledge set; contraction removes a proposition and whatever else must be withdrawn to stop implying it. Logic alone does not choose among the possible withdrawals, so a non-logical ordering of epistemic importance is required. (pp. 83-86)
- A knowledge set `K` is deductively closed in compact classical propositional logic. Expansion is logical closure after adding `A`; revision and contraction are non-monotonic operations that require a choice policy. The authors acknowledge that deductive closure is not a practical database representation, but use it to state the semantics. (pp. 84-86)
- The revision postulates K*1-K*8 and contraction postulates K−1-K−8 formalize closure, success, minimal change/inclusion and vacuity, consistency, extensionality, recovery, and the conjunctive interaction laws. Levi and Harper identities translate between revision and contraction. (pp. 86-87)

## Epistemic Entrenchment

- `A ≤ B` means that `B` is at least as epistemically entrenched as `A`; on contraction, less entrenched propositions are surrendered before more entrenched ones. The ordering is qualitative rather than numerical and is relative to the current `K`, not a permanent global property of an atom or record. (pp. 87-88)
- The defining constraints are: EE1 transitivity; EE2 dominance (`A ⊢ B` implies `A ≤ B`); EE3 conjunctiveness (`A ≤ A∧B` or `B ≤ A∧B`); EE4 minimality (for consistent `K`, propositions outside `K` occupy the bottom); and EE5 maximality (only valid propositions occupy the absolute top). These imply connectivity, so classic epistemic entrenchment is a total preorder with strong conjunction behavior. (p. 89)
- Entrenchment is recovered from contraction by `A ≤ B` iff `A` is not retained when contracting `A∧B`, or `A∧B` is valid. Conversely, contraction retains `B` under contraction by `A` iff `B∈K` and either `A < A∨B` or `A` is valid. (pp. 89-90)

## Representation Results

- Theorem 4: any ordering satisfying EE1-EE5 uniquely determines, through the contraction rule, a contraction operator satisfying K−1-K−8. Theorem 5 proves the converse. Corollary 6 makes the constructions inverse: the rational contraction functions and admissible entrenchment orderings are interchangeable representations. (p. 90)
- The appendix proves the Levi/Harper correspondences and the representation results in detail; these are logical constraints on propositions and contraction behavior, not a generic precedence table over record metadata. (pp. 91-94)
- For a finite Boolean knowledge algebra, the ordering is determined by its ordering over the dual atoms/top elements. Consequently the information needed is linear in the number of atomic facts even though the closed knowledge set is exponential. (pp. 90-91, 94-95)

## Propstore Decision Relevance

- A prefix matcher over `atom`, `source`, `context`, or `kind` with arbitrary integer priorities does not implement the paper's epistemic-entrenchment relation: it need not respect logical dominance, conjunctiveness, knowledge-set-relative minimality/maximality, or total comparability.
- Source credibility and contextual applicability are legitimate capabilities, but they are different semantic inputs. They require explicit evidence/reliability or prioritized-information owners that can explain how they induce a proposition ordering or merging policy; attaching weights directly to revision calls conflates those capabilities with epistemic entrenchment.
- Therefore a test-only override surface should not be “wired in” as the entrenchment owner. Deleting it preserves the opportunity to design source reliability or contextual selection at their correct generic owners later.

## Limitations

- The framework is single-agent, propositional, deductively closed, and non-iterated in this presentation; it does not itself supply a provenance-aware source reliability model. (pp. 84-90)
- Its computational claim concerns how much ordering information suffices semantically, not an implementation algorithm for large structured claim stores. (pp. 90-91)

## Collection Cross-References

### Already in Collection

- [Modellings for Belief Change: Prioritization and Entrenchment](../Rott_1992_ModellingsBeliefChangePrioritization/notes.md) - cites this paper as the standard proposition-level representation and shows why explicit-base priority and epistemic entrenchment are not directly interchangeable.

### New Leads (Not Yet in Collection)

- Alchourrón, Gärdenfors, and Makinson (1985) - “On the logic of theory change: Partial meet contraction functions and their associated revision functions” - the AGM postulate and representation foundation used throughout this paper.
- Gärdenfors (1984) - “Epistemic importance and minimal changes of belief” - the direct precursor to the qualitative entrenchment ordering.
- Grove (1986) - “Two modellings for theory change” - a semantic alternative for comparing entrenchment with systems of spheres.

### Supersedes or Recontextualizes

- (none)

### Cited By (in Collection)

- [Connections Between the ATMS and AGM Belief Revision](../Dixon_1993_ATMSandAGM/notes.md) - uses EE1-EE5 and the entrenchment-contraction bridge as the formal target for an ATMS-label encoding.
- [Modellings for Belief Change: Prioritization and Entrenchment](../Rott_1992_ModellingsBeliefChangePrioritization/notes.md) - generalizes the analysis from closed belief sets to prioritized explicit belief bases and identifies where the bridge is exact or approximate.

### Conceptual Links (not citation-based)

- [Axiomatic Characterization of the AGM Theory of Belief Revision in a Temporal Logic](../Bonanno_2007_AGMBeliefRevisionTemporalLogic/notes.md) - provides a temporal-frame characterization of the same AGM revision constraints; the plausibility structure is a semantic counterpart of the proposition ordering used here.
- [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - both keep an epistemic state richer than a single committed proposition set, while assigning that state different formal carriers and change rules.
