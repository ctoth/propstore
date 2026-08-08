---
title: "Modellings for Belief Change: Prioritization and Entrenchment"
authors: "Hans Rott"
year: 1992
venue: "Theoria"
doi_url: "https://doi.org/10.1111/j.1755-2567.1992.tb01154.x"
pages: "21-57"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# Modellings for Belief Change: Prioritization and Entrenchment

## One-Sentence Summary

Priorities over explicit beliefs and epistemic entrenchment over derived beliefs are distinct but related representations, connected only through formal constructions over candidate sub-bases and contraction behavior rather than direct transfer of item weights.

## Representation and Change

- A belief base `H` contains explicit beliefs and generates the belief set `K = Cn(H)` of explicit plus implicit consequences. A belief state is therefore represented by `<H,K>`, but a change operation cannot in general output a new base that both preserves the base format and contains exactly the post-change explicit beliefs. (pp. 21-23)
- Rott adopts base change: revision acts on explicit beliefs because derived beliefs should be lost when their explicit warrants are lost. The paper studies the resulting change to `K` using `H`, without pretending to determine a successor `H`. (pp. 23, 28)
- Contraction searches maximal sub-bases that no longer imply the target. Maxichoice selects one; meet contraction intersects the consequences of all equally admissible maximal sub-bases. Even the unprioritized case exposes a tension between preserving an explicit-base representation and preserving intuitive derived disjunctions. (pp. 24-28)
- Multiple contraction has pick and bunch forms: discard at least one member of a set, or discard every member, respectively. These distinctions later become essential for extending entrenchment to sets of sentences. (pp. 28-30)

## Prioritized Belief Bases

- Realistic explicit beliefs can differ in importance, relevance, plausibility, value, or certainty. Rott deliberately leaves the interpretation open but requires a weak, modular ordering over members of `H`; equivalence classes form levels of priority. (p. 30)
- The item ordering induces a lexicographic-style preference over subsets: one subset is better if it first exceeds another at some priority level while matching it at all higher levels. Prioritized contraction selects maximal non-implying sub-bases under this induced relation, not by looking up a weight for the sentence being revised. (pp. 30-31)
- The induced subset relation must be base-specific, maximizing, and “stoppered” so candidate sets can reach preferred maximal alternatives. Converse well-foundedness of priority levels suffices; without it, contraction may have no maximal candidate. (pp. 31-33)

## Entrenchment Is Not Priority

- Epistemic entrenchment means comparative retractability: `φ < ψ` means it is easier to discard `φ` than `ψ`. Rott states that a higher base priority does not directly imply greater entrenchment, nor vice versa. The key difference is that entrenchment must respect logical relationships, which raw base priority does not. (p. 34)
- The entrenchment postulates cover non-triviality/irreflexivity, propagation up and down entailment, conjunction, minimality/maximality, and, only in the standard Gärdenfors-Makinson version, modularity. Contraction can reveal entrenchment by observing which proposition survives a contraction that forces a choice. (pp. 34-38)
- Rott distinguishes a competitive interpretation (which of two beliefs survives direct competition) from a minimal-change interpretation (whether discarding one can be achieved with less loss of important information). Extending these to sets yields pick and bunch entrenchment. (pp. 36-40)

## Generating Entrenchment from a Base

- A tempting positive construction based on proof sets fails conjunction constraints. The correct negative construction compares ways of discarding beliefs: `ψ` is more entrenched than `φ` when every optimal way of discarding `ψ` is dominated by a better way of discarding `φ`. (pp. 41-43)
- The generated relation satisfies generalized entrenchment but not the standard modularity condition. The counterexample demonstrates again that the priority relation and the induced entrenchment relation are different kinds of object. (pp. 43-44)
- The Coincidence Lemma proves that, for pick contraction, the competitive and minimal-change interpretations agree. Several alternate formulations using maximal non-implying theory subsets or arbitrary sentence sets reduce to the same construction. (pp. 44-47)

## Approximation and Special Cases

- Singleton entrenchment is insufficient to reproduce general prioritized meet-base contraction. Small and large EE contractions provide lower and upper bounds; the inclusions can be strict even without prioritization. (pp. 48-49)
- Exact agreement is recovered for closed bases, for a recovery-enforcing “blown-up” contraction, and when contraction is merely the intermediate step in Levi revision. (pp. 49-51)
- The conclusion emphasizes that the starting point is a fixed prioritized base whose explicit items and syntactic structure govern change. The bridge between contraction and entrenchment is exact in one direction and only approximate for general contraction operations. (pp. 51-54)
- The connective-free generalization does not license direct transfer to unstructured truth-maintenance nodes or nonmonotonic systems; Horn-like identification of nodes is insufficient because the underlying consequence operation is assumed monotonic. (p. 55)

## Propstore Decision Relevance

- A source, context, kind, or atom label with an integer priority is not an epistemic-entrenchment relation. At most it could contribute to the priority of a typed explicit belief in an owned belief base.
- To wire such input legitimately, Propstore would need: a defined belief-base owner; an interpretation of the scale; a typed association between priorities and explicit beliefs; a stable induced preference over candidate sub-bases; and a specified contraction/revision construction. The current per-call prefix map supplies none of these.
- Source provenance should remain attached to the Micropublication/claim evidence object. If a future credibility policy turns provenance evidence into base priorities, that is a separate generic policy and must be explicit and auditable.
- Deleting a test-only override does not discard a valid entrenchment implementation. It removes a representation that conflates metadata matching, source reliability, and proposition-level retractability.

## Limitations

- The priority interpretation is intentionally generic and does not decide how empirical source reliability should be measured. (p. 30)
- The framework assumes monotonic consequence and syntax-sensitive base change; it warns against immediate transfer to nonmonotonic truth-maintenance structures. (p. 55)

## Collection Cross-References

### Already in Collection

- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gardenfors_1988_RevisionsKnowledgeSystemsEntrenchment/notes.md) - supplies the standard closed-belief-set entrenchment representation that Rott generalizes and contrasts with explicit-base priority.

### New Leads (Not Yet in Collection)

- Nebel (1992) - “Syntax-based approaches to belief revision” - develops prioritized belief-base revision and the opposite mapping direction considered by Rott.
- Dubois and Prade (1991) - “Epistemic entrenchment and possibilistic logic” - gives a formal numeric representation of entrenchment rather than an uninterpreted weight map.
- Rott (1992b) - “Preferential belief change using generalized epistemic entrenchment” - relaxes standard modularity and develops the generalized relation used here.

### Supersedes or Recontextualizes

- (none)

### Cited By (in Collection)

- (none found)

### Conceptual Links (not citation-based)

- [Iterated Revision as Prioritized Merging](../Delgrande_2006_IteratedRevisionPrioritizedMerging/notes.md) - gives reliability-ranked observations a typed merging semantics; this is a later, separate owner for information-source priority rather than proposition-level entrenchment.
- [Connections Between the ATMS and AGM Belief Revision](../Dixon_1993_ATMSandAGM/notes.md) - both construct entrenchment from a richer explicit representation, but Rott uses prioritized bases while Dixon uses ATMS labels and justifications.
