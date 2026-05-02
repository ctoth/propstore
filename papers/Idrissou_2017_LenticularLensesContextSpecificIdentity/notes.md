---
title: "Is my:sameAs the same as your:sameAs? Lenticular Lenses for Context-Specific Identity"
authors: "Al Koudous Idrissou, Rinke Hoekstra, Frank van Harmelen, Ali Khalili, Peter van den Besselaar"
year: 2017
venue: "K-CAP 2017"
doi_url: "https://doi.org/10.1145/3148011.3148029"
pages: 8
produced_by:
  agent: "Codex GPT-5"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-05-02T00:42:52Z"
---
# Is my:sameAs the same as your:sameAs? Lenticular Lenses for Context-Specific Identity

## One-Sentence Summary
Presents Lenticular Lenses, an RDF model and workflow for generating, annotating, selecting, validating, and combining context-specific equality links so that identity across datasets is task-dependent rather than globally collapsed into `owl:sameAs`. *(p.0-p.7)*

## Problem Addressed
Semantic Web data integration depends on correspondence links between entities in different datasets, but `owl:sameAs` asserts full equality between resources independently of context. The paper argues that whether two resources should be treated as equal depends not just on intrinsic properties, but on the purpose or task for which the resources are used. Misguided or overly strong `:sameAs` links are especially damaging because transitive predicates can propagate equivalence along chains and make the outer endpoints increasingly erroneous. *(p.0)*

The central research question is: how can users construct, share, and use context-sensitive equality relationships between semantic web datasets? The authors answer by making both links and link-generation methods explicit, decorating candidate correspondences with metadata about how, why, when, and by whom they were generated, and letting users construct task-specific "lenticular lenses" by selecting and combining candidate linksets. *(p.1)*

## Key Contributions
- Defines context-specific equality using two property sets: one for indiscernibility and one for propagation, then extends the definition to multiple datasets with an alignment procedure for corresponding properties and values. *(p.2-p.3)*
- Defines `linkset` as all context-specific correspondences between two datasets, and `lenticular lens` as a set of context-specific correspondences constructed from linksets by union, intersection, difference, and composition. *(p.3)*
- Provides an RDF representation that uses singleton properties for triple-level correspondence metadata and a linktype hierarchy for task-, domain-, and generic identity predicates. *(p.3-p.4)*
- Gives a SPARQL-oriented implementation strategy and Algorithm 1 for generating a lens while normalizing unordered pairs, reconstructing unique singleton link predicates, and preserving provenance. *(p.5-p.6)*
- Evaluates the approach qualitatively with three Science, Technology and Innovation case studies involving GRID, OrgRef, ETER, LeidenRanking, and enriched GADM-derived datasets. *(p.6-p.7)*

## Study Design
- **Type:** Methodological system paper with qualitative case-study evaluation. *(p.6)*
- **Population:** Not applicable; the evaluation uses STI-linked datasets and prototype user workflows. *(p.6-p.7)*
- **Intervention(s):** Lenticular Lens modeling workflow for constructing, refining, and combining linksets. *(p.3-p.7)*
- **Comparator(s):** Existing black-box matching systems, link-specification systems, OpenPHACTS scientific lenses, RDF reification, named graphs, and singleton properties. *(p.1-p.3)*
- **Primary endpoint(s):** Whether the model provides the functionality needed by increasingly complex STI alignment case studies. *(p.6)*
- **Secondary endpoint(s):** Time/space complexity characteristics and support for provenance, reuse, validation, and mixed-initiative curation. *(p.5-p.7)*

## Methodology
The paper combines formal modeling, RDF representation design, and qualitative validation. It first analyzes why global identity semantics are too strong for Semantic Web deployment, then defines context-sensitive indiscernibility and propagation. It builds an RDF meta-model that records metadata for individual correspondences and linksets, then demonstrates construction of lenses by set-like operators over linksets. The implementation is exposed through a prototype user interface that supports context definition, linkset generation, manual refinement, approval/rejection annotation, and final view construction. *(p.0-p.7)*

## Key Equations / Statistical Models

$$
\forall p: x = y \leftrightarrow (\langle x,p,v\rangle \leftrightarrow \langle y,p,v\rangle)
$$

Where: equality under the OWL-style Leibniz principle is expressed as a bi-implication over all predicates `p`; the right direction captures indiscernibility of identicals, while the left direction captures identity of indiscernibles. The paper argues both directions are too strong for open-world Semantic Web deployment when quantified over all possible predicates. *(p.2)*

$$
\forall p \in \Pi: x =_{\Pi} y \leftrightarrow (\langle x,p,v\rangle \leftrightarrow \langle y,p,v\rangle)
$$

Where: `Pi` is a context-defining set of predicates that are necessary and sufficient to determine indiscernibility. This restricts indiscernibility to a finite context. *(p.2)*

$$
\forall p \notin \Pi: x =_{\Pi} y \land \langle x,p,v\rangle \rightarrow \langle y,p,v\rangle
$$

Where: the paper raises the problem of whether non-context properties should propagate over contextual equality. The answer differs per context. In the drug example, `structure` determines equivalence classes while `target` propagates within those classes and `brand` does not propagate. *(p.2)*

$$
\forall p \in \Pi: x =_{(\Pi,\Psi)} y \leftrightarrow (\langle x,p,v\rangle \leftrightarrow \langle y,p,v\rangle)
$$

Where: `Pi` is the set of predicates used for contextualized equality. *(p.2)*

$$
\forall p \in \Psi: x =_{(\Pi,\Psi)} y \rightarrow (\langle x,p,v\rangle \leftrightarrow \langle y,p,v\rangle)
$$

Where: `Psi` is the set of predicates whose values propagate once contextualized equality has been established. Predicates outside `Pi union Psi` remain unchanged. *(p.2)*

$$
x =_{(\Pi,\Psi,\approx)} y \leftrightarrow
\forall p_1,p_2 \in \Pi \text{ with } p_1 \approx p_2
\text{ and } \forall v_1,v_2 \text{ with } v_1 \approx v_2:
\langle x,p_1,v_1\rangle \leftrightarrow \langle y,p_2,v_2\rangle
$$

Where: `approx` indicates an alignment procedure between properties and values across datasets with different namespaces. A context becomes `(Pi, Psi, approx)` rather than only property sets in a single namespace. *(p.3)*

$$
L = \{(x,y) \in D_1 \times D_2 \mid x =_{(\Pi,\Psi,\approx)} y\}
$$

Where: a linkset `L` is the set of all context-specific correspondences between two datasets `D1` and `D2`. *(p.3)*

$$
(x,y) \in \bigcup L_i \leftrightarrow \exists i : (x,y) \in L_i
$$

Where: a lens can be formed as the union of multiple linksets. *(p.3)*

$$
(x,y) \in \bigcap L_i \leftrightarrow \forall i : (x,y) \in L_i
$$

Where: a lens can require that a correspondence appears in every selected linkset. *(p.3)*

$$
(x,y) \in L_a - L_b \leftrightarrow (x,y) \in L_a \land (x,y) \notin L_b
$$

Where: a lens can remove correspondences found in another linkset. *(p.3)*

$$
(x,y) \in L_a \circ L_b \leftrightarrow \exists z : (x,z) \in L_a \land (z,y) \in L_b
$$

Where: lens composition connects correspondences through an intermediate entity `z`. *(p.3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Linkset B triples | - | triples | 816 | - | p.4 | Example metadata for `:linkset_B` |
| Linkset B similarity interval | theta | score | - | ]0.8, 1[ | p.4 | `rdfs:comment` says similarity measured in interval `]0.8 1[` |
| Linkset B candidate strength 1 | `ll:strength` | score | 0.875 | - | p.4 | Evidence: "Institute of Cancer Research" compared to "The Institute of Cancer Research" |
| Linkset B candidate strength 2 | `ll:strength` | score | 0.818 | - | p.4 | Evidence: "London Business school" compared to "Lauder Business School" |
| Lens R_Y triples | - | triples | 66 | - | p.5 | Metadata in Listing 6 |
| Lens R_Y expected correspondences | - | correspondences | 33 | - | p.5 | Metadata in Listing 6 |
| Lens R_Y removed duplicates | - | correspondences | 7 | - | p.5 | Metadata in Listing 6 |
| Approximate string matching threshold, case 1 filter | theta | score | 0.85 | - | p.6 | Correspondences filtered on name similarity greater than 0.85 and token "3M" in the subject or object |
| Linkset creation UI threshold | theta | score | 0.8 | - | p.6 | Figure 2 UI shows threshold for approximate matching |
| Number of supported matching mechanisms | - | mechanisms | 6 | - | p.6 | Exact string, approximate string, URI identity, embedded, intermediate, geo-similarity |
| LeidenRanking university coverage | - | universities | 800 | - | p.7 | LeidenRanking provides performance metrics for over 800 major universities worldwide |
| GRID size | \|X\| | instances | 74523 | - | p.7 | Used in exact-similarity timing example |
| OrgRef size | \|Y\| | instances | 32010 | - | p.7 | Used in exact-similarity timing example |
| Exact-similarity linkset runtime | - | time | <1 | minutes | p.7 | Implemented fully in SPARQL on commodity hardware for GRID/OrgRef example |
| Dutch university correlation | r | correlation | 0.58 | - | p.7 | Correlation between number of R&D organizations and LeidenRanking performance score in case study 3 |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| R&D organizations vs LeidenRanking performance | Correlation | 0.58 | - | - | Dutch universities only, case study 3 | p.7 |
| Exact-similarity linkset generation | Runtime | <1 minute | - | - | GRID 74523 instances vs OrgRef 32010 instances on commodity hardware | p.7 |

## Methods & Implementation Details
- Candidate correspondences are first generated as one or more linksets; each candidate set records the reasons why the links were generated, how they were generated, when, and by whom. Users then select and combine candidate sets into context-specific lenticular lenses. *(p.1)*
- Related work is grouped into identifying/generating equality relations, expressing correspondences, and metadata that enables on-demand selection of the right links without inconsistency. *(p.1)*
- Basic terminology distinguishes RDF links/correspondences, linksets, and linktypes. If the link predicate expresses equality, the relation is a linktype such as `owl:sameAs` or `skos:exactMatch`. *(p.1)*
- Black-box matchers such as AGDISTIS, LogMap, and OtO do not encode enough domain- or context-specific considerations, making them less suitable for task-specific linksets. *(p.1)*
- Linkage Query Writer and SILK are more promising because their user-defined rules explicitly represent context-specific identity criteria, but they do not record justifications in declarative RDF metadata. *(p.1)*
- OpenPHACTS scientific lenses improve on SILK by having declarative metadata and practical encoding, but they are limited to whole-lens/linkset metadata, only support union of linksets, and express correspondences using the linking predicate directly, which can introduce inconsistency when lenses are combined. *(p.1-p.2)*
- RDF reification and n-ary relations allow statement-level metadata but add at least four new triples and make querying harder; named graphs also increase query complexity and are optimized for fewer named graphs. Inline RDF* and SPARQL* reduce verbosity but require RDF*/SPARQL* support. *(p.2)*
- Singleton properties give each candidate link its own uniquely identifiable predicate while preserving semantics through `rdf:singletonPropertyOf`, but query complexity and performance are affected. The paper uses singleton properties because experiments suggest they are less affected than alternatives. *(p.2)*
- Each correspondence in a linkset is connected through a singleton property with a triple-specific linktype, and the singleton-specific graph records evidence and strength. The generic named graph relates each singleton property to a shared task-specific property. *(p.4)*
- The linktype hierarchy connects triple-specific linktypes, task-specific linktypes, domain-specific linktypes, and generic predicates such as `isRelatedTo`. Task/domain predicates are represented with subproperty relations, context-property relations, and `prov:wasDerivedFrom`. *(p.4)*
- Linkset metadata uses VOID/BDB-style fields to record target datasets, target entity types, aligned subject/object properties, mechanism, link predicate, number of triples, justification, and comments. *(p.4-p.5)*
- Lens metadata records the target linksets, number of triples, expected correspondences, removed duplicates, operator, assertion method, and query. *(p.5)*
- The SPARQL query in Listing 7 generates `Lens_R_Y` by implementing intersection over linksets R and Y while excluding common ancestors that have a common child ancestor. *(p.5)*
- Algorithm 1 handles union by abstracting away singleton properties and direction, collecting unordered entity pairs, creating new singleton properties for resulting pairs, choosing a consistent direction by alphabetical dataset-name order, and recording derivation provenance in the specific graph. *(p.5-p.6)*

## Algorithms

### Algorithm 1: Generate a Lens Using UNION
Input: a set of alignments `G = {Linkset/Lens}` of size `n` triples. Output: lens graphs. Complexity: `O(n log n)` assuming efficient search. *(p.5)*

1. Add generic metadata about the lens to `genericGraph`. *(p.5)*
2. For each alignment graph `g` in `G`, add `g` to a temporary graph. *(p.5)*
3. Iterate over each triple `(x,p,y)` in the temporary graph. *(p.5)*
4. Collect all triples connecting the same ordered pair: `[(x,q,y) | (x,q,y) in tempGraph]`; the search is `O(log n)`. *(p.5)*
5. Remove the collected triples from the temporary graph. *(p.5)*
6. Extract the predicate list `preds = [q | (x,q,y) in triples]`. *(p.5)*
7. Create `r = singletonProperty(preds)`. *(p.5)*
8. If `x < y`, add `(x,r,y)` to the main graph; otherwise add `(y,r,x)` to enforce a consistent direction. *(p.5-p.6)*
9. For each original predicate `q`, add `(r, prov:derivedFrom, q)` to the specific graph. *(p.5)*
10. Return `[mainGraph, genericGraph, specificGraph]`. *(p.5)*

## Figures of Interest
- **Figure 1 (p.4):** Meta-model for correspondences. Shows usual predicates above domain-specific linktypes, task-specific linktypes, triple-specific linktypes, linksets, and metadata. This is the core representation stack for preserving context at multiple abstraction levels.
- **Figure 2 (p.6):** Linkset creation UI. Shows users selecting source/target datasets, entity types, properties to align, matching method, threshold, and alignment creation.
- **Figure 3 (p.7):** Integration model for case study 3. Shows ETER, GRID, LeidenRanking, GRID-enriched, and ETER-enriched datasets connected through several linksets and lenses.

## Results Summary
The qualitative evaluation finds that the model can represent increasingly complex STI alignment workflows. Case studies 1 and 2 align GRID and OrgRef for different research questions and demonstrate reuse/refinement of existing linksets through additional filters such as geography. Case study 3 combines multiple linksets and lenses across five datasets to create a table for investigating whether university ranks in LeidenRanking can be predicted from university characteristics in other datasets. The example finds a correlation of 0.58 between number of R&D organizations and LeidenRanking performance score for Dutch universities, motivating further analysis rather than claiming causal identification. *(p.6-p.7)*

## Limitations
- The paper does not propose a new disambiguation or matching method; it assumes existing alignment methods can generate candidate linksets and focuses on annotation, selection, reuse, and combination. *(p.7)*
- The evaluation is qualitative and case-study based because the authors state that quantitative evaluation of a methodological proposal is not obvious. *(p.6)*
- Singleton properties are not always easy to use, so the system allows conversion from enriched alignments to the usual flat format and importing flat alignments from other tools. *(p.7)*
- Other performance parameters are strongly triple-store dependent, and exact similarity in SPARQL is only reported for one example scale. *(p.7)*
- The impact of evolving referenced resources and dataset versions on correspondence networks remains future work. *(p.7)*

## Arguments Against Prior Work
- `owl:sameAs` is too blunt because it entails full equality between resources independent of context. *(p.0)*
- `skos:related` has less far-reaching consequences than a misguided `:sameAs`, but weaker alternatives reduce utility if they no longer express intended semantics. Different linktypes are required for different circumstances. *(p.0)*
- Black-box matchers are intended to be generic and do not consider domain- or context-specific suitability of a linkset. *(p.1)*
- User-guided systems such as LQW and SILK encode context-specific conditions in rules, but do not retain declarative metadata about the justification for each mapping, making reuse difficult. *(p.1)*
- OpenPHACTS scientific lenses provide useful declarative metadata but are too limited: metadata is at whole-linkset/lens level, lenses only union linksets, and direct use of the linking predicate creates semantic interaction when multiple lenses compete. *(p.1-p.2)*
- RDF reification, n-ary relation patterns, named graphs, and RDF*/SPARQL* each have representation or query-complexity costs for triple-level metadata. *(p.2)*

## Design Rationale
- Use context-specific equality because the truth value of an equality assertion depends on the task and context in which it is generated. *(p.0-p.2)*
- Separate indiscernibility predicates `Pi` from propagation predicates `Psi` because some properties determine equality classes while different properties should propagate within those classes. *(p.2)*
- Add an alignment procedure `approx` because properties and values across datasets live in different namespaces and cannot be compared by simple shared predicate identity. *(p.3)*
- Use singleton properties to decorate individual correspondences with metadata while keeping semantics available through a parent linktype hierarchy. *(p.2-p.4)*
- Introduce unique link predicates per individual correspondence so competing lenses do not interact semantically through the same equality predicate. *(p.2)*
- Provide set-like lens operators because useful context-specific views require union, intersection, difference, and composition rather than only enabling/disabling whole linksets. *(p.3-p.5)*
- Preserve rejected correspondences in linksets, annotated as rejected, so linksets can be reused and provenance remains complete. *(p.6)*

## Testable Properties
- A context-specific equality implementation must distinguish predicates used for indiscernibility from predicates that propagate after equality is established. *(p.2)*
- Predicates outside `Pi union Psi` must remain unchanged under contextualized equality. *(p.2)*
- Across multiple datasets, property/value comparison must use an explicit alignment procedure `approx`; shared predicate names are not assumed. *(p.3)*
- A linkset between `D1` and `D2` must contain only pairs from `D1 x D2` satisfying contextualized equality for the chosen context. *(p.3)*
- A lens union includes a pair if the pair appears in at least one selected linkset; an intersection includes a pair only if it appears in every selected linkset. *(p.3)*
- A lens difference must remove pairs that appear in the subtracting linkset; composition must include `(x,y)` only when an intermediate `z` connects through both component linksets. *(p.3)*
- Generating a union lens must normalize direction and generate new singleton properties for resulting correspondences, preserving `prov:derivedFrom` links to source predicates. *(p.5-p.6)*
- Decorating correspondences has `O(1)` insertion cost per correspondence and increases output size by a fixed number `n` of triples per correspondence. *(p.7)*

## Relevance to Project
This paper is highly relevant to propstore's concept identity and source-local/canonical boundary discipline. It argues against global identity collapse and provides a representation strategy where identity is context-specific, provenance-rich, and computed as a view over candidate correspondences. The separation between candidate linksets, metadata, user validation, and final lenses maps well to propstore's need to keep source-local authoring state out of canonical identity while still supporting reusable, policy-driven concept reconciliation.

## Open Questions
- [ ] How should propstore represent `Pi` and `Psi` for concept identity decisions so that equality-determining properties and propagation properties remain explicit?
- [ ] Should propstore use singleton-property-like correspondence identifiers, named correspondence objects, or another domain object to retain per-link provenance without inheriting RDF singleton-property query costs?
- [ ] How should rejected-but-retained correspondences be represented so they remain reusable evidence rather than disappearing from the source-local record?
- [ ] What is the propstore equivalent of a Lenticular Lens: a source-local view, a merge policy, a render-time identity closure, or a separate reconciliation artifact?

## Related Work Worth Reading
- Welty, C., and Fikes, R. "A Reusable Ontology for Fluents in OWL" / contextualized sameAs line of work cited by the paper as [4] for a context-based semantics of `owl:sameAs`.
- Brenninkmeijer et al. (2012) and Batchelor et al. (2014) on OpenPHACTS scientific lenses, which this paper extends beyond whole-linkset metadata and union-only composition.
- Nguyen et al. (2014) on singleton properties, the representational mechanism used for correspondence-level metadata.
- Volz et al. (2009), SILK, and Linkage Query Writer as alignment tools whose outputs the paper wants to make reusable through declarative metadata.

## Collection Cross-References

### Already in Collection
- [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md) - cited for the claim that `owl:sameAs` is often misused and that transitive equality semantics can make outer endpoints of an identity chain increasingly erroneous. *(p.0, p.7)*

### New Leads (Not Yet in Collection)
- Beek, W., Schlobach, S., and van Harmelen, F. (2016) - "A contextualised semantics for owl: sameAs" - direct formal precursor for context-specific indiscernibility and property-limited equality.
- Batchelor et al. (2014) - "Scientific lenses to support multiple views over linked chemistry data" - OpenPHACTS scientific lenses precursor.
- Brenninkmeijer et al. (2012) - "Scientific lenses over linked data" - earlier scientific lens model.
- Nguyen et al. (2014) - "Don't like RDF reification?: making statements about statements using singleton property" - representational basis for triple-specific link metadata.

### Supersedes or Recontextualizes
- Recontextualizes `owl:sameAs` misuse literature by moving from detecting misuse to constructing context-specific equality predicates and views with explicit provenance. *(p.0-p.7)*

### Conceptual Links (not citation-based)
- [The sameAs Problem: A Survey on Identity Management in the Web of Data](../Raad_2019_SameAsProblemSurvey/notes.md) - Strong: Raad surveys the sameAs identity-management problem that this paper addresses constructively. Idrissou et al. provide an implementation-facing model for context-specific links, linksets, and lenses.
- [sameAs.cc: The Closure of 500M owl:sameAs Statements](../Beek_2018_SameAs.ccClosure500MOwl/notes.md) - Strong: sameAs.cc demonstrates the scale and risk of equivalence closure over global `owl:sameAs`; Lenticular Lenses give a way to avoid turning every correspondence into global closure.
- [Not Quite the Same: Identity Constraints for the Web of Linked Data](../Melo_2013_NotQuiteSameIdentity/notes.md) - Moderate: de Melo repairs erroneous sameAs graphs by constraint optimization, while Idrissou et al. prevent some erroneous commitments by requiring context-specific linksets and task-specific lenses before equality is used.

### Cited By (in Collection)
- [sameAs.cc: The Closure of 500M owl:sameAs Statements](../Beek_2018_SameAs.ccClosure500MOwl/notes.md) - cites this paper as a context-specific identity/lenticular-lens approach related to managing sameAs semantics and identity closure.
