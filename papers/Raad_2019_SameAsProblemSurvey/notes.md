---
title: "The sameAs Problem: A Survey on Identity Management in the Web of Data"
authors: "Joe Raad, Nathalie Pernelle, Fatiha Saïs, Wouter Beek, Frank van Harmelen"
year: 2019
venue: "arXiv preprint / survey"
doi_url: "https://doi.org/10.48550/arXiv.1907.10528"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:51:38Z"
---
# The sameAs Problem: A Survey on Identity Management in the Web of Data

## One-Sentence Summary
Surveys the owl:sameAs identity problem in Linked Data — how identity links are created, why many are erroneous, approaches for detecting and repairing them, and alternative identity predicates that relax the formal semantics of owl:sameAs.

## Problem Addressed
In a decentralized knowledge representation system like the Web of Data, multiple URIs can denote the same real-world entity. The owl:sameAs property is the standard mechanism for asserting identity, but it has formal semantics requiring full substitutability — which most publishers violate, using it loosely for "contextual similarity" instead of true identity. This leads to massive error propagation across the knowledge graph. *(p.0)*

## Key Contributions
- Comprehensive survey of the sameAs problem across five dimensions: creation, quality, detection of erroneous links, repair approaches, and alternative identity relations *(p.0)*
- Taxonomy of identity link creation approaches: matching rules, OWL reasoning, SKOS producers, and crowd-sourcing *(p.2)*
- Categorization of sameAs quality issues: unique name violations, contextual identity vs. true identity *(p.2-4)*
- Survey of erroneous identity link detection approaches: error detection via network analysis, string similarity, description comparison, property-based *(p.4-5)*
- Overview of alternative identity predicates and identity management services *(p.2, 5)*

## Methodology
Literature survey covering identity management in the Web of Data (Linked Open Data). Categorizes approaches across five main areas with a table overview of existing identity link detection approaches.

## Key Equations / Statistical Models

$$
\text{owl:sameAs}(a, b) \Rightarrow \forall P, o: P(a, o) \leftrightarrow P(b, o)
$$
Where: owl:sameAs formally means full substitutability — all properties that hold for $a$ must hold for $b$ and vice versa. *(p.0)*

$$
\text{contextual identity}: c_i \equiv_{C} c_j \text{ iff } c_i \text{ and } c_j \text{ share the same set of properties in context } C
$$
Where: Two resources are contextually identical when they share the same properties within a specific context, but may differ outside that context. *(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| sameAs statements in LOD cloud | — | count | ~559M | — | 0 | As of the 2015 LOD cloud |
| Unique real-world entities (DBpedia) | — | count | — | — | 0 | Over half a billion statements |
| LOD datasets containing sameAs | — | count | — | — | 0 | Hundreds of datasets |
| Error rate in sameAs (Halpin et al.) | — | % | — | — | 4 | Studies show significant error rates |
| Identity closure communities | — | count | 48M+ | — | 0 | Identity closure set communities |
| owl:sameAs network precision | — | ratio | — | 0.69-0.99 | 5 | Varies by approach (Table 3) |
| owl:sameAs network recall | — | ratio | — | 0.79-1.00 | 5 | Varies by approach (Table 3) |

## Methods & Implementation Details

### Identity Link Creation (Section 2)
Four main approaches for creating sameAs links *(p.2)*:
1. **Matching rules** — Key-based (inverse functional properties, IFPs) and similarity-based approaches. IFPs theoretically ensure at most one entity per value; in practice, violations common.
2. **OWL reasoning** — owl:InverseFunctionalProperty, owl:hasKey, owl:maxCardinality, owl:FunctionalProperty with owl:inverseOf can derive sameAs.
3. **SKOS producers** — skos:exactMatch predicate intended for concept schemes but often used loosely.
4. **Crowd-sourcing** — Manual assertions by dataset publishers.

### Contextual Identity (Section 2)
- The concept was introduced by Halpin et al. (2010): two resources are contextually identical when they share properties within a defined context but may differ outside it *(p.2)*
- Formally: $c_i \equiv_C c_j$ when both share the same properties restricted to context $C$
- Principles (5) and (6) refer to the notion of contextual propositional attitudes — belief/assertion contexts *(p.2)*
- In RDF, a "context" can be: a specific dataset, a named graph, or a subset of properties *(p.2)*

### The sameAs Quality Problem (Section 3)
Three categories of quality issues *(p.2-4)*:

1. **Semantic overloading** — Publishers use owl:sameAs for "related to" or "similar to" rather than strict identity. The formal semantics require full substitutability, but in practice most sameAs links express weaker relations. *(p.2)*

2. **Unique Name Assumption violations** — In LOD, 2015 and Valdestilhas et al. 2017: resources are detected by possessing IFP-violating characteristics. Two URIs that are supposed to be different but get linked as sameAs, or vice versa. *(p.4)*

3. **Contextual vs. global identity** — A resource may be the "same" in one context (e.g., geographic location) but different in another (e.g., political entity). The sameAs relation doesn't distinguish these. *(p.2)*

### Erroneous Identity Link Detection (Section 5)
Table 3 provides an overview of approaches *(p.4-5)*:

**Error detection approaches:**
- **Bhagarva et al. 2015** — Terminology-based, supervised, tested on DBpedia *(p.4)*
- **Papaleo et al. 2014** — Semantic-based, on LOD cloud *(p.4)*
- **Flickinger et al. 2016** — Supervised, on LOD *(p.4)*
- **Paulheim 2014** — Statistical outlier detection *(p.4)*
- **de Melo 2013** — Network analysis approach *(p.4)*
- **Valdestilhas et al. 2017** — Combined terminological + structural *(p.4)*

**Key finding:** The quality and accuracy of link detection approaches have not yet been thoroughly evaluated on a comprehensive gold standard dataset. Most evaluations are limited to specific datasets. *(p.4)*

### Network-Based Approaches (Section 5.3)
- Raad et al. (2018) explored the LOD identity network using three network metrics: metalink consistency, authority, and descriptiveness plus Linked Data-specific ones (closeness, richness, degree) to detect erroneous sameAs *(p.5)*
- Tested on 411K owl:sameAs links with evaluation suggesting precision between 80% and 93% and recall between 89% and 100% *(p.5)*

### Content-Based Approaches (Section 5.2)
- Treats each identity link as a feature vector and uses outlier detection methods *(p.5)*
- Cuzzola et al. 2015: used DBpedia categories for calculating similarity scores of textual descriptions associated to (claimed) identical pairs *(p.5)*

### Identity Management Services (Section 4)
- Alternative identity predicates proposed instead of owl:sameAs *(p.2)*:
  - **owl:sameAs** — Full identity (too strong for most uses)
  - **skos:exactMatch** — Intended for concept schemes
  - **rdfs:seeAlso** — Weaker "related resource" link
  - **Custom predicates** — Various proposals for graded/contextual identity
- Services for managing identity in the Web of Data: identity services share the construction of and relying on identity corpora *(p.5)*
- Key services mentioned: sameAs.org, identity resolution services *(p.5)*

### The Formal Identity Problem
- owl:sameAs is reflexive, symmetric, and transitive *(p.0)*
- Transitivity is especially problematic: if A=B and B=C, then A=C, even if A and C are clearly different entities *(p.0)*
- This creates "identity closure communities" where error propagates through transitive chains *(p.0)*
- Knowledge graphs contain over 558 million owl:sameAs statements across hundreds of datasets *(p.0)*

## Figures of Interest
- **Table 1 (p.2):** Overview of the sameAs identity link data, listing datasets (DBpedia, YAGO, Freebase), their sources, and link counts
- **Table 3 (p.4-5):** Overview of erroneous identity link detection approaches, listing type of approach, evaluation data, and precision/recall/F1

## Results Summary
The survey identifies that the sameAs problem is pervasive in the Web of Data. Key findings: (1) most sameAs links violate formal semantics, expressing contextual similarity rather than true identity; (2) error propagation through transitivity creates cascading incorrectness; (3) existing detection approaches show promise but lack comprehensive evaluation; (4) alternative predicates exist but lack adoption; (5) the problem requires both better tooling for detection/repair and community adoption of more nuanced identity predicates. *(p.5-6)*

## Limitations
- Survey scope is primarily the Linked Open Data cloud; may not generalize to all knowledge graph settings *(p.6)*
- Most detection approaches lack evaluation on comprehensive gold standards *(p.4)*
- The paper is a survey — no novel algorithmic contribution *(p.0)*
- Alternative identity predicates suffer from adoption problems *(p.5)*

## Arguments Against Prior Work
- The formal semantics of owl:sameAs (OWL specification) are too rigid for real-world identity management — most publishers need contextual or graded identity but are given only a binary, fully-substitutable predicate *(p.0, 2)*
- IFP-based identity detection (key-based matching) is unreliable because IFP violations are common in practice *(p.2)*
- Crowd-sourced identity links are error-prone due to human misunderstanding of owl:sameAs semantics *(p.2)*

## Design Rationale
- Identity should be contextual rather than global — two things can be "the same" in one context but different in another *(p.2)*
- The solution space requires both detection/repair of existing erroneous links AND alternative predicates for future assertions *(p.5-6)*
- Network-based approaches are promising because they exploit structural properties of the identity graph without requiring content comparison *(p.5)*

## Testable Properties
- Transitivity of owl:sameAs creates identity closures that grow much larger than justified — an identity closure community should be bounded *(p.0)*
- If two URIs share all properties in a context C, they are contextually identical in C *(p.2)*
- IFP violations (two distinct entities sharing an IFP value) indicate potential erroneous sameAs links *(p.4)*
- Network metrics (consistency, authority, descriptiveness) should correlate with sameAs link quality *(p.5)*
- Precision of sameAs networks evaluated by detection approaches ranges 0.69-0.99 *(p.5)*

## Relevance to Project
Directly relevant to propstore's identity management problem. The propstore system manages concepts from multiple sources that may refer to the same underlying entity. The sameAs problem is exactly the concept-merging challenge: when should two concepts from different papers be treated as "the same"? The paper's emphasis on contextual identity (rather than global identity) aligns with propstore's non-commitment principle — identity should be a render-time decision based on policy, not a storage-time collapse. The alternative identity predicate taxonomy maps to propstore's stance system where different papers may assert different identity relationships.

## Open Questions
- [ ] How does contextual identity formalization map to propstore's concept merging?
- [ ] Can the network-based detection approaches be adapted for concept identity in propstore?
- [ ] Should propstore adopt a graded identity predicate instead of binary concept merging?

## Collection Cross-References

### Already in Collection
- [[Beek_2018_SameAs.ccClosure500MOwl]] — cited as the large-scale empirical dataset underpinning the survey's analysis of identity link proliferation and error propagation

### Now in Collection (previously listed as leads)
- [[Beek_2018_SameAs.ccClosure500MOwl]] — Collects 558M explicit owl:sameAs statements from the LOD Cloud, computes equivalence closure (49M non-singleton identity sets via union-find), and reveals that transitive closure propagates identity errors (largest set: 177,794 members conflating Einstein with countries). Provides the empirical data this survey paper analyzes.
- [[Melo_2013_NotQuiteSameIdentity]] — Formalizes identity constraint detection as a minimum multicut problem (NP-hard), provides LP relaxation and Hungarian algorithm solutions, and demonstrates removal of 500K+ constraint violations from BTC 2011 sameAs data. Raad's survey categorizes this as a "network analysis approach" to erroneous link detection.
- [[Halpin_2010_OwlSameAsIsntSame]] — Foundational critique of owl:sameAs semantics. Proposes Similarity Ontology with eight graded identity properties (sameIndividual, claimsIdentical, almostSameAs, etc.). Empirical Mechanical Turk experiment shows ~50% of owl:sameAs in LOD Cloud are not true identity. Introduced the "contextual identity" concept that Raad's survey builds upon.
- [CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories](../Valdestilhas_2017_CEDALTime-efficientDetectionErroneous/notes.md) — Provides the concrete combined terminological/structural method Raad classifies: union-find graph partitioning detects same-dataset duplicate resources in transitive identity clusters, processing 19.2M LinkLion `owl:sameAs` links in 4.6 minutes and preserving provenance for review.

### New Leads (Not Yet in Collection)
- ~~Halpin et al. (2010) — "When owl:sameAs Isn't the Same" — foundational critique of sameAs semantics, introduced contextual identity~~ → NOW IN COLLECTION: [[Halpin_2010_OwlSameAsIsntSame]]
- ~~de Melo (2013) — "Not Quite the Same: Identity Constraints for the Web of Linked Data" — alternative identity constraints for linked data~~ → NOW IN COLLECTION: [[Melo_2013_NotQuiteSameIdentity]]
- ~~Valdestilhas et al. (2017) — "Cedal: Time-efficient Detection of Erroneous Links" — combined terminological + structural detection~~ → NOW IN COLLECTION: [CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories](../Valdestilhas_2017_CEDALTime-efficientDetectionErroneous/notes.md)
- Raad et al. (2018) — "Constructing and Evaluating Identity Links on the Web Using Network Statistics" — network-based link quality evaluation

## Related Work Worth Reading
- Halpin et al. 2010 — "When owl:sameAs Isn't the Same" — foundational critique of sameAs semantics → NOW IN COLLECTION: [[Halpin_2010_OwlSameAsIsntSame]]
- de Melo 2013 — "Not Quite the Same: Identity Constraints for the Web of Linked Data" — alternative identity constraints -> NOW IN COLLECTION: [[Melo_2013_NotQuiteSameIdentity]]
- Beek et al. 2018 — "sameAs.cc: The Closure of 500M owl:sameAs Statements" — large-scale identity network analysis -> NOW IN COLLECTION: [[Beek_2018_SameAs.ccClosure500MOwl]]
- Valdestilhas et al. 2017 — Error detection combining terminological and structural features → NOW IN COLLECTION: [CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories](../Valdestilhas_2017_CEDALTime-efficientDetectionErroneous/notes.md)
- Raad et al. 2018 — Network-based approaches for evaluating identity links using graph metrics
