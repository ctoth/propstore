---
title: "When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data"
authors: "Harry Halpin, Patrick J. Hayes, James P. McCusker, Deborah L. McGuinness, Henry S. Thompson"
year: 2010
venue: "International Semantic Web Conference (ISWC 2010), LNCS 6496"
doi_url: "https://doi.org/10.1007/978-3-642-17746-0_20"
pages: "305-320"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-04T08:01:19Z"
---
# When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data

## One-Sentence Summary
Proposes a Similarity Ontology with eight graded identity/similarity properties to replace the overloaded owl:sameAs in Linked Data, backed by an empirical Mechanical Turk experiment showing that roughly half of sampled owl:sameAs statements are not true identity. *(p.0-13)*

## Problem Addressed
owl:sameAs is the only standard mechanism for linking entities across Linked Data datasets, but it is semantically too strong for most actual uses. It asserts full Leibnizian identity (indiscernibility of identicals), meaning all properties of one URI must hold for the other. In practice, publishers use it loosely to mean similarity, relatedness, or intentional equivalence, leading to incorrect inferences when OWL reasoners treat it as true identity. *(p.0-1)*

## Key Contributions
- Formal analysis of why owl:sameAs is problematic: it conflates referential identity with weaker similarity relations *(p.1-2)*
- Taxonomy of five kinds of identity/similarity relationships between URIs: identical-but-referentially-opaque, intentionally-equivalent, matching, similar, and related *(p.3-6)*
- A Similarity Ontology with eight new properties (sub-properties of owl:sameAs or independent) with formally specified reflexivity, symmetry, and transitivity characteristics *(p.6-8)*
- Empirical experiment using Amazon Mechanical Turk on 250 randomly sampled owl:sameAs statements from the Linked Open Data Cloud, showing substantial misuse *(p.8-13)*

## Methodology
The paper combines philosophical/logical analysis of identity with an empirical crowdsourcing study. The theoretical contribution defines a hierarchy of identity-like relations with different logical properties. The empirical study randomly samples owl:sameAs triples from the Linked Open Data Cloud (58.7M triples, 1,202 domains), has three human judges classify each into similarity categories, and measures inter-annotator agreement. *(p.0, 8-12)*

## Key Equations / Statistical Models

$$
\forall x \forall y (x = y \leftrightarrow \forall P (P(x) \leftrightarrow P(y)))
$$
Where: Leibniz's Law — two things are identical iff they share all properties. This is what owl:sameAs formally commits to.
*(p.1)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Total owl:sameAs triples in LOD Cloud | - | count | 58,691,520 | - | p.9 | From OpenLink copy of LOD Cloud |
| Unique domain names | - | count | 1,202 | - | p.9 | Domains providing sameAs triples |
| Power-law exponent estimate | - | - | 2.42 | - | p.9 | Failed significance test (p=.08, p<=.1) |
| Sample size for experiment | N | count | 250 | - | p.10 | Weighted random sample after filtering |
| Number of judges | - | count | 3 | - | p.10 | Mechanical Turk workers |
| Kappa (before optimization) | kappa | - | 0.215 | - | p.12 | Fair agreement on 6-category scale |
| Kappa (after optimization to 3 categories) | kappa | - | 0.435 | - | p.12 | Moderate agreement |
| True sameAs rate (optimized) | - | % | ~51 | 29-72 | p.12-13 | Range across 3 raters |
| Could-use-weaker-relation rate | - | % | ~21 | 18-24 | p.13 | Intermediate cases needing sim: properties |
| Cannot-judge rate | - | % | ~27 | 8-46 | p.13 | Can't tell or not related, based on RDF alone |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Inter-rater agreement (6 categories) | Cohen's kappa | 0.215 | - | - | 3 judges, 250 sameAs pairs | p.12 |
| Inter-rater agreement (3 categories) | Cohen's kappa | 0.435 | - | - | 3 judges, 250 sameAs pairs after category merge | p.12 |
| Approximate true identity rate | % of sample | ~51% | 29-72% | - | Across 3 raters, optimized categories | p.12-13 |

## Methods & Implementation Details
- Data source: All owl:sameAs triples from OpenLink's copy of the Linked Open Data Cloud *(p.9)*
- Top providers: bio2rdf (26M), uniprot (6M), DBPedia (4.3M), Freebase (3.2M), Max Planck Institute (0.85M), OpenCyc (0.2M), Geonames (0.1M), Zemanta (0.05M) *(p.9)*
- Distribution of sameAs links across domains follows approximately power-law (log-log space), but failed formal power-law test (Clauset et al. method, p=.08) *(p.9)*
- Sampling: Weighted random sample of 250 after excluding bio2rdf/uniprot (biomedical, needs specialists) and two linked datasets with nearly all same-domain links *(p.9-10)*
- Mechanical Turk interface: Showed two-column table of properties for each URI pair, judges selected from {Same, Matching, Similar, Related, Unrelated, Don't Know} *(p.10-11)*
- Each HIT covered 5 sameAs pairs, paid $0.02 per HIT, filtered to US-based workers *(p.10)*
- Initial 6 categories reduced to 3 (Identical / Similar-Matching-Related / Can't Tell-Not Related) to improve kappa *(p.12)*

## Figures of Interest
- **Fig 1 (p.7):** Sub-property relationships between the 8 Similarity Ontology properties and existing OWL/RDFS/SKOS properties. Shows hierarchy from owl:sameAs at top through sim:sameIndividual, sim:claimsIdentical, etc.
- **Fig 2 (p.9):** Log-log rank-frequency plot of domains in sameAs statements. Shows power-law-like distribution.
- **Fig 3 (p.11):** Mechanical Turk interface screenshot — two-column property table for URI pair evaluation.
- **Fig 4 (p.11):** Category assignment counts per judge (raw 6 categories). Shows substantial disagreement between judges, especially around "Similar" category.
- **Fig 5 (p.13):** Category frequencies after optimization to 3 categories. Shows convergence between judges on "Same As" end but divergence on "Don't Know or Not Related" end.

## Results Summary
- Inter-annotator agreement was only "fair" (kappa=0.215) on the 6-way classification, improving to "moderate" (kappa=0.435) when collapsed to 3 categories *(p.12)*
- Approximately 51% of owl:sameAs statements were judged truly identical (range 29-72% across raters) *(p.12-13)*
- About 21% (+/- 3%) would benefit from a weaker similarity property instead of owl:sameAs *(p.13)*
- About 27% (+/- 19%) could not be reliably judged based only on the RDF retrieved *(p.13)*
- Judges showed systematically different thresholds: one strict (few "same"), one lenient (many "same"), one in between *(p.11-12)*

## Limitations
- Small sample (250 pairs) from a single snapshot of the LOD Cloud *(p.13)*
- Non-specialist judges on Mechanical Turk; biomedical domains excluded because they require expertise *(p.9-10)*
- Only examined properties retrievable via RDF — did not dereference to human-readable descriptions *(p.12)*
- The 6-category taxonomy proved too fine-grained for reliable human agreement; 3 categories were needed *(p.12)*
- No evaluation of whether the proposed Similarity Ontology properties are themselves reliably distinguishable by users *(p.13-14)*
- Power-law hypothesis for domain distribution was not confirmed (p=.08) *(p.9)*

## Arguments Against Prior Work
- Against using owl:sameAs as the universal identity link: it commits to full Leibnizian identity which most publishers don't intend *(p.0-2)*
- Against treating referential transparency as default in Linked Data: many contexts are referentially opaque (quotation, belief contexts, temporal indexing) where substitutivity fails *(p.3-4)*
- Against SKOS as sufficient: SKOS provides exactMatch/closeMatch but these are designed for concept schemes, not arbitrary entity linking, and lack formal logical grounding for identity *(p.6)*
- Against simple "coreference resolution" framing: the problem is not just finding which URIs denote the same thing, but representing the *kind* of relationship (identity vs. similarity vs. relatedness) *(p.2-3)*

## Design Rationale
- Eight properties rather than one because identity is not binary — there is a spectrum from strict logical identity to loose topical relatedness *(p.3-6)*
- Properties are defined with specific combinations of reflexivity, symmetry, and transitivity to capture precise logical commitments *(p.6-7)*
- sim:sameIndividual is reflexive, symmetric, transitive — the strongest, equivalent to owl:sameAs for referentially transparent contexts *(p.7)*
- sim:claimsIdentical is reflexive, symmetric, but NOT transitive — prevents identity chains propagating across disagreeing sources *(p.7)*
- sim:almostSameAs is reflexive, symmetric, but NOT transitive — for cases that share most but not all properties *(p.7)*
- Named graphs are used for provenance to track who asserted each identity claim *(p.8)*
- Proposed using a simple property (sim:hasContext) on named graphs rather than complex reification *(p.8)*

## The Similarity Ontology: Eight Properties (Table 1, p.7)

| Property | Reflexive | Symmetric | Transitive | Description |
|----------|-----------|-----------|------------|-------------|
| sim:sameIndividual | Yes | Yes | Yes | True referential identity (like owl:sameAs in transparent contexts) |
| sim:claimsIdentical | Yes | Yes | No | Agent claims identity but transitivity blocked |
| sim:almostSameAs | Yes | Yes | No | Share most properties but not all |
| sim:sameContentAs | Yes | Yes | No | Same informational content, different carrier |
| sim:sameResourceAs | Yes | Yes | No | Same resource, possibly different serializations |
| sim:similarTo | Yes | Yes | No | Share some notable properties |
| sim:sameClassAs | Yes | Yes | Yes | Membership in same class |
| sim:sameScientificNameAs | Yes | Yes | No | Same scientific name but possibly different identity criteria |

Sub-property chain (Fig 1, p.7): owl:sameAs -> sim:sameIndividual -> sim:claimsIdentical -> sim:almostSameAs; also sim:sameContentAs and sim:sameResourceAs branch off sim:almostSameAs.

## Testable Properties
- owl:sameAs entails full substitutivity: if `owl:sameAs(a,b)` then for all properties P, `P(a) <-> P(b)` *(p.1)*
- sim:claimsIdentical must NOT be transitive: `claimsIdentical(a,b)` and `claimsIdentical(b,c)` must not entail `claimsIdentical(a,c)` *(p.7)*
- sim:almostSameAs must NOT be transitive *(p.7)*
- sim:sameIndividual IS transitive and should be semantically equivalent to owl:sameAs in referentially transparent contexts *(p.7)*
- Approximately half of owl:sameAs statements in the LOD Cloud are not true identity *(p.12-13)*
- The distribution of owl:sameAs links across domains is heavy-tailed but not strictly power-law *(p.9)*

## Relevance to Project
Directly relevant to propstore's concept identity layer. The paper formalizes exactly the problem propstore faces: when two concept URIs/identifiers are declared "the same," what does that actually mean? The Similarity Ontology's graded identity properties map to propstore's need to hold multiple rival normalizations without collapsing them. Specifically:
- sim:claimsIdentical (non-transitive) matches propstore's design of storing identity claims as proposals rather than facts
- The named-graph provenance approach aligns with propstore's provenance-per-claim model
- The empirical finding that ~50% of identity assertions are wrong validates propstore's non-commitment discipline

## Open Questions
- [ ] How does the Similarity Ontology interact with OWL reasoning in practice? Does declaring sim:sameIndividual as a sub-property of owl:sameAs cause unintended inference chains?
- [ ] Has the Similarity Ontology been adopted or extended since 2010? (Check Raad et al. 2019, Beek et al. 2018 which are in the collection)
- [ ] Could propstore use sim:claimsIdentical as the default identity predicate instead of owl:sameAs?
- [ ] What is the current scale of owl:sameAs misuse (the 2010 data is from 58M triples; the web has grown enormously)?

## Related Work Worth Reading
- Halpin & Hayes (2010) "When owl:sameAs isn't the same" — WWW 2010 workshop version, shorter *(ref 9)*
- Nikolov et al. (2007) "Knofuss: a comprehensive architecture for knowledge fusion" — addresses entity resolution *(ref 15)*
- Volz et al. (2009) "Discovering and maintaining links on the web of data" — link maintenance *(ref 17)*
- Jentzsch et al. (2009) "Enabling tailored therapeutics with linked data" — example of biomedical sameAs use *(ref 10)*
- McCusker & McGuinness (2010) "Towards identity in linked data" — companion work on identity *(ref 12)*

## Collection Cross-References

### Already in Collection
- [[Raad_2019_SameAsProblemSurvey]] — directly surveys the owl:sameAs problem this paper introduced; categorizes Halpin's Similarity Ontology as a "vocabulary enrichment" approach and builds on the "contextual identity" concept
- [[Beek_2018_SameAs.ccClosure500MOwl]] — provides large-scale empirical confirmation at 558M triples (vs. Halpin's 58M); demonstrates that transitive closure of owl:sameAs produces absurd identity sets, vindicating Halpin's argument that transitivity is too strong
- [[Melo_2013_NotQuiteSameIdentity]] — formalizes identity constraint detection as minimum multicut; provides algorithmic solution to the error-detection problem Halpin identified qualitatively

### Cited By (in Collection)
- [[Raad_2019_SameAsProblemSurvey]] — cites as foundational critique; uses Halpin's contextual identity concept and error-rate findings
- [[Beek_2018_SameAs.ccClosure500MOwl]] — cites as foundational analysis of identity confusion in Linked Data

### New Leads (Not Yet in Collection)
- Ding et al. (2010) — "owl:sameAs and linked data: An empirical study" — parallel empirical study from Falcon search engine; larger scale, different methodology
- Bouquet et al. (2008) — "Entity name system: The backbone of an open and scalable web of data" — alternative architecture for identity resolution
- McCusker & McGuinness (2010) — "Towards identity in linked data" — companion work by co-authors with deeper formal treatment

### Conceptual Links (not citation-based)
- [[McCarthy_1993_FormalizingContext]] — Strong: Halpin's referential opacity argument (contexts where substitutivity fails) directly instantiates McCarthy's `ist(c, p)` formalization of context-dependent truth. The Similarity Ontology's sim:hasContext property on named graphs is a Linked Data realization of McCarthy's context lifting.
- [[Groth_2010_AnatomyNanopublication]] — Moderate: Halpin proposes using named graphs with provenance properties to track who asserted identity claims; nanopublications formalize exactly this pattern (assertion + provenance + publication info in named graphs).
- [[Kuhn_2014_TrustyURIs]] — Moderate: Trusty URIs address the flip side of Halpin's problem — ensuring that URIs reliably identify the same content over time, complementing Halpin's concern about when different URIs are (mis)claimed to identify the same thing.
- [[Juty_2020_UniquePersistentResolvableIdentifiers]] — Moderate: addresses persistent identifier design for scientific data, relevant to Halpin's finding that biomedical datasets (bio2rdf, uniprot) are the heaviest owl:sameAs users.
