---
title: "SameAs Networks and Beyond: Analyzing Deployment Status and Implications of owl:sameAs in Linked Data"
authors: "Li Ding, Joshua Shinavier, Zhenning Shangguan, Deborah L. McGuinness"
year: 2010
venue: "ISWC 2010, Lecture Notes in Computer Science 6496"
doi_url: "https://doi.org/10.1007/978-3-642-17746-0_10"
pages: "145-160"
---

# SameAs Networks and Beyond: Analyzing Deployment Status and Implications of owl:sameAs in Linked Data

## One-Sentence Summary
This paper builds and analyzes ESameNet, an extended owl:sameAs network dataset from BTC 2010, to characterize sameAs deployment, summarize publisher-level connectivity, and derive class-level similarity signals for ontology mapping and error detection *(p.145-p.160)*.

## Problem Addressed
Millions of owl:sameAs statements had been published in Linked Data, but their large-scale deployment status, topology, and implications for ontology inference were not quantitatively characterized in a statistically meaningful way *(p.145-p.146)*. The authors focus on three practical questions: how sameAs networks are deployed on the Web of Data, what common interests exist among Linked Data publishers, and how Web ontologies are affected by owl:sameAs inference *(p.146-p.148)*.

## Key Contributions
- Defines SameAs networks as weakly connected components over owl:sameAs-filtered RDF graphs and studies their structural properties using a large real-world dataset rather than small samples *(p.146-p.148)*.
- Constructs ESameNet by extending SameAs networks with pay-level-domain (PLD) statements and RDF type statements, adding publisher and class worlds around resource nodes *(p.148-p.150)*.
- Reports quantitative properties of 8,711,398 unique owl:sameAs statements covering 6,932,678 unique URI resources, 645,400 blank nodes, and 2,890,027 weakly connected components *(p.149-p.151)*.
- Introduces PLD networks as weighted directed abstractions of SameAs networks and uses them to expose publisher communities and topic-level common interests *(p.152-p.155)*.
- Introduces CLS networks for class-level similarity from shared instances and owl:sameAs-mediated common instances, showing potential support for class alignment and error detection *(p.155-p.157)*.

## Study Design (empirical papers)
- **Type:** Large-scale observational graph analysis of Web of Data RDF statements in the Billion Triple Challenge 2010 corpus *(p.146-p.150)*.
- **Population:** ESameNet subset derived from BTC 2010, including 8,711,398 unique owl:sameAs statements after duplicate removal, 6,932,678 unique URI resources, 645,400 blank nodes, 552,622,105 rdf:type statements, 488,138,983 distinct typed RDF resources, 168,503 distinct RDFS/OWL classes, and 967 distinct PLDs *(p.149-p.150)*.
- **Intervention(s):** None.
- **Comparator(s):** Not a controlled experiment; comparisons are between SameAs, PLD, and CLS graph representations and between class-pair categories *(p.150-p.157)*.
- **Primary endpoint(s):** Graph structure and deployment metrics: weak component count and size, average path length, in-degree distribution, PLD-level clusters, and CLS class-pair labels *(p.150-p.157)*.
- **Secondary endpoint(s):** Qualitative implications for publisher communities, ontology mapping, schema-level inconsistency detection, and future sameAs inference analysis *(p.154-p.159)*.
- **Follow-up:** No longitudinal follow-up; future work proposes comparing BTC datasets from consecutive years to evaluate evolution over time *(p.159)*.

## Methodology
The paper treats all owl:sameAs statements as a directed graph over RDF resources, then analyzes weakly connected components as SameAs networks *(p.146-p.147)*. To reduce small-sample bias, it uses BTC 2010, which the authors describe as covering a significant portion of the Web of Data *(p.146)*. The ESameNet dataset is built by adding PLD statements, derived from HTTP URI parsing and blank-node/non-HTTP named-graph assumptions, plus rdf:type statements already present in the BTC graph *(p.148-p.150)*.

For basic SameAs topology, the authors count components, path length, component-size distribution, and in-degree distribution *(p.150-p.152)*. For publisher analysis, they collapse resource-level SameAs arcs to weighted directed PLD arcs, using normalized counts of unique SameAs links between resources from source and target PLDs *(p.152-p.154)*. For ontology analysis, they build CLS networks from type statements and from owl:sameAs-mediated pairs of typed resources, then inspect class-pair categories that suggest equivalence, error, or possible subclass relations *(p.155-p.157)*.

## Key Equations / Statistical Models

$$
H = psf(G, P)
$$
Where: `psf` is the predicate-based sub-graph filter; `G` is an RDF graph; `P` is a set of RDF properties; `H` is the subgraph of `G` whose triples use predicates in `P` *(p.146)*.

$$
SN = \text{weakly connected component of } psf(G, \{\text{owl:sameAs}\})
$$
Where: `SN` is a SameAs network in RDF graph `G`; components are weakly connected, so directed owl:sameAs arcs are treated as undirected for component membership *(p.146)*.

$$
ESN = SN + CLS + PLD + \text{type/PLD arcs}
$$
Where: `ESN` is an extended SameAs network with three node worlds: resource nodes (`RES`), class nodes (`CLS`), and pay-level domain nodes (`PLD`); RDF type and PLD-linking statements are added as new arcs *(p.148-p.149)*.

$$
w(\langle pld_1, pld_2\rangle) =
\frac{\#\{(u_1,u_2): u_1\ ex:hasPLD\ pld_1,\ u_2\ ex:hasPLD\ pld_2,\ u_1\ owl:sameAs\ u_2\}}{\text{outdegree}(pld_1)}
$$
Where: `w` is the PLD arc weight, computed by counting unique SameAs statements between resources from `pld1` and `pld2`, normalized by the outdegree of `pld1` *(p.152)*.

$$
w(C_1,C_2) = \#\{\text{common instances shared by class } C_1 \text{ and class } C_2\}
$$
Where: `w` is a CLS arc weight; the paper considers class relations including equivalence, subclass-of, disjointness, and class-overlap, with overlap not directly mapped to OWL properties *(p.155-p.156)*.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| BTC 2010 sameAs statements before duplicate removal | - | statements | 9,358,227 | - | 149 | Valid statements after removing invalid statements but before duplicate removal |
| Unique owl:sameAs statements in ESameNet | - | statements | 8,711,398 | - | 149, 151 | Non-duplicate sameAs statements used for analysis |
| Unique URI resources in SameAs statements | - | resources | 6,932,678 | - | 149, 151 | URI resources connected by sameAs statements |
| Blank nodes in SameAs statements | - | blank nodes | 645,400 | - | 149 | Blank nodes in sameAs statement coverage |
| rdf:type statements copied from BTC 2010 | - | statements | 552,622,105 | - | 150 | Type statements used to extend ESameNet |
| Distinct typed RDF resources | - | resources | 488,138,983 | - | 150 | Resources covered by type statements |
| Distinct RDFS/OWL classes | - | classes | 168,503 | - | 150, 156 | Class universe for CLS-ALL |
| Distinct PLDs | - | domains | 967 | - | 150 | Extracted pay-level domains |
| Weakly connected SameAs components | - | components | 2,890,027 | - | 151 | Components in ESameNet sameAs graph |
| Average URI resources per component | - | resources/component | 2.4 | - | 151 | Average component coverage |
| Average graph path length | - | hops | 1.07 | - | 151 | Indicates most components are simple pairs |
| Components with hundreds of resources | - | components | 41 | - | 151 | Larger components in the sameAs graph |
| Components with thousands of resources | - | components | 2 | - | 151 | Very large sameAs components |
| Largest foaf:knows component in 2005 comparison | - | persons | 24,559 | - | 150 | Used as contrast with SameAs scale |
| Largest SameAs component in 2010 | - | resources | 5,000 | - | 150-p.151 | Contrast with foaf:knows component |
| Resources with owl:sameAs in-degree 1 | - | resources | 2,974,914 | - | 151 | Slightly more than expected under pure power law |
| High-end in-degree order | - | inbound links | 4,000 | - | 151 | Highest end of in-degree distribution |
| PLD visualization weight threshold | - | normalized weight | 0.00001 | 0.00001-0.06 | 153 | Arcs below threshold and self-loops omitted; 0.06 is max arc weight |
| CLS-SAME nodes | - | classes | 6,555 | - | 156 | Classes in sameAs-mediated CLS network |
| CLS-SAME arcs | - | arcs | 21,628 | - | 156 | Weighted class-pair arcs using Query B |
| CLS-ALL one-instance class share | - | percent/classes | 45% | 77K classes | 156 | About 77K classes have only one instance |
| CLS-ALL high-instance classes | - | instances/class | over 100 million | - | 156 | A few classes have more than 100 million instances |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| SameAs graph size | Unique sameAs statements | 8,711,398 | - | - | BTC 2010 ESameNet | 149 |
| SameAs graph coverage | Unique URI resources | 6,932,678 | - | - | BTC 2010 ESameNet | 149, 151 |
| SameAs component count | Weakly connected components | 2,890,027 | - | - | SameAs graph | 151 |
| SameAs component sparsity | Average path length | 1.07 | - | - | SameAs graph | 151 |
| Component size distribution | Qualitative histogram result | Most components size 2-3 | - | - | Figure 3 | 151 |
| In-degree distribution | Qualitative log-log result | Power-law pattern, with deviations at in-degree 1 and 10-20 | - | - | Figure 4 | 151-p.152 |
| CLS-SAME graph size | Nodes and arcs | 6,555 nodes, 21,628 arcs | - | - | Query B over sameAs-connected typed resources | 156 |

## Methods & Implementation Details
- Build SameAs statements by copying all owl:sameAs triples from BTC 2010, removing invalid and duplicate statements, and retaining unique URI resources plus blank nodes *(p.149)*.
- Copy all rdf:type statements for RDF resources in BTC 2010 to support class-level analysis *(p.149-p.150)*.
- Extract PLD statements by regular-expression parsing of HTTP URIs; for blank nodes or non-HTTP URIs, assume the same PLD as the named graph hosting the corresponding SameAs statements *(p.150)*.
- Use AllegroGraph triple store version 4.0 and Allegro Common Lisp version 8.2 to load the BTC 2010 dataset and extract ESameNet *(p.150)*.
- Run computational tasks on a server with 2x Quad-Core Intel Xeon 2.33GHz CPUs, 64GB memory, and 4TB disk space *(p.150)*.
- Use Cytoscape and its Organic layout to render PLD network clusters; node size reflects sum of incoming and outgoing arc weights, arc thickness reflects arc weight, and node color is randomly assigned with distinct colors *(p.153)*.
- Omit PLD arcs with weight below 0.00001 and omit self-loops for visual clarity in Figure 5; the maximum visible weight is 0.06 *(p.153)*.
- For PLD explanation, retrieve rdf:type information for resources at each source and target PLD with a SPARQL query, then compare the `k` most frequent source and target types *(p.154-p.155)*.
- Build CLS-ALL using Query A over all type statements and CLS-SAME using Query B over SameAs-connected resources; Query B assumes owl:sameAs is neither symmetric nor transitive for this experiment *(p.156)*.

## Figures of Interest
- **Fig. 1 (p.147):** Example SameAs network around "Paul Allen", showing one-way and reciprocal sameAs arcs, authority nodes with high in-degree, and hub nodes with high out-degree.
- **Fig. 2 (p.149):** Example extended SameAs network fragment with three layers: Class (CLS), Resource (RES), and Pay-Level Domain (PLD), connected by rdf:type, owl:sameAs, and ex:hasPLD arcs.
- **Fig. 3 (p.151):** Histogram of SameAs component sizes, showing most components are very small.
- **Fig. 4 (p.152):** Log-log in-degree distribution of RDF resources in ESameNet, showing a power-law-like pattern.
- **Fig. 5 (p.153):** Largest PLD network cluster generated from ESameNet, with dbpedia.org as a central node and visible communities around music, scientific publication, bioinformatics, and Semantic Web data.

## Results Summary
SameAs networks in ESameNet are usually small and star-like rather than large, complex social-network-style graphs. The dataset has 2,890,027 weakly connected components, an average of 2.4 URI resources per component, and average path length 1.07, implying that most components are pairs or small local structures *(p.151)*. The in-degree distribution has a power-law pattern but with excess in-degree-1 resources and excess in-degree 10-20 resources; high-end resources have roughly 4,000 inbound owl:sameAs links *(p.151-p.152)*.

PLD networks provide a higher-level view of data publisher connectivity. Figure 5 shows visually identifiable communities, including a scientific publication cluster with `l3s.de`, `rkbexplorer.com`, `uni-trier.de`, `sciencedirect.com`, `acm.org`, `gbv.de`, `bibsonomy.org`, and `doi.org`, plus clusters around bioinformatics and Semantic Web communities *(p.153-p.154)*. The authors argue that comparing top-k rdf:type labels across PLD arcs can explain why publishers are connected; for example, dbtune.org and zitgist.com both publish music data with top types from the Music Ontology *(p.154-p.155)*.

CLS networks show that sameAs-mediated common instances can suggest ontology relationships, but the relationships are heterogeneous. Some class pairs appear equivalent because their URIs have the same local name; some are likely erroneous after ontology-definition checking; and some unlabeled pairs involve general-purpose classes that may suggest subclass relations *(p.156-p.157)*. The authors conclude that classification over CLS networks could support automated class alignment and error detection *(p.157)*.

## Limitations
- The authors do not inspect the intended semantics of individual owl:sameAs assertions because they are not the owners of those statements; the analysis deliberately focuses on structural properties *(p.147-p.148)*.
- PLD extraction for blank nodes and non-HTTP URIs assumes the hosting named graph's PLD, which is a pragmatic approximation *(p.150)*.
- Out-degree analysis is skipped for space reasons; in-degree is used because out-degree is typically controlled by publishers, while in-degree reflects how many publishers link to a resource *(p.151)*.
- Figure 5 omits arcs below a threshold and self-loops, so it is not a complete rendering of the PLD network *(p.153)*.
- Query B for CLS-SAME assumes owl:sameAs is neither symmetric nor transitive; alternative assumptions are left for future study *(p.156)*.
- The study is based on BTC 2010 and does not analyze temporal evolution except as proposed future work *(p.159)*.

## Arguments Against Prior Work
- Prior reported results on owl:sameAs were derived from very small sample datasets, so they did not provide statistically significant deployment analysis for the Web of Data *(p.145)*.
- Linked Data literature reported that owl:sameAs is often used in ways that do not strictly agree with OWL's official semantics, motivating objective large-scale structural analysis rather than relying on semantic intent claims *(p.145-p.147)*.
- Vatant argued that mashup use of owl:sameAs is not necessarily symmetric; the paper treats reciprocal links as a practical indicator of stronger equivalence *(p.147)*.
- Jaffri et al. argued that owl:sameAs equivalence is often context-dependent and application-scoped; the paper notes that Web-published sameAs statements seldom guarantee full transitivity despite OWL semantics *(p.147)*.
- McCusker and McGuinness warned that owl:sameAs can confuse provenance and ground truths in bioinformatics; this paper situates such concerns in a broader large-scale deployment analysis *(p.158)*.

## Design Rationale
- The authors use weakly connected components for SameAs networks because the deployed sameAs graph is directed but the analysis needs connected units of resources related by sameAs statements *(p.146-p.147)*.
- They use BTC 2010 to reduce bias from small samples and to obtain a broad real-world Web of Data sample *(p.146-p.149)*.
- They add PLD nodes because PLDs can identify Linked Data publishers and provide a meaningful abstraction over millions of resource-level statements *(p.148-p.153)*.
- They add type nodes because rdf:type information can explain why PLDs connect and can support class-level similarity and ontology mapping analysis *(p.148-p.157)*.
- They avoid assuming full OWL sameAs semantics in the CLS-SAME query so the class-overlap relation can be analyzed conservatively under deployed Web data conditions *(p.156)*.

## Testable Properties
- A SameAs network is a weakly connected component of the owl:sameAs-filtered RDF graph *(p.146)*.
- In ESameNet, PLD statements must connect RDF resources to literal PLD names using `ex:hasPLD`, and type statements connect RDF resources to RDFS/OWL classes using `rdf:type` *(p.148-p.150)*.
- The ESameNet sameAs graph contains exactly 2,890,027 weakly connected components under the authors' BTC 2010 extraction *(p.151)*.
- The average path length of the sameAs graph is 1.07, implying that transitive inference over individual SameAs networks is not computationally expensive and can be parallelized *(p.151)*.
- The in-degree distribution of ESameNet resources should show a power-law pattern when plotted on a log-log scale, with notable deviations at in-degree 1 and 10-20 *(p.151-p.152)*.
- PLD arc weights should be normalized counts of unique sameAs statements between resource pairs from source and target PLDs divided by source PLD outdegree *(p.152)*.
- CLS-SAME should contain 6,555 unique RDFS/OWL class nodes and 21,628 weighted arcs when built from this ESameNet extraction using Query B *(p.156)*.

## Relevance to Project
This paper is directly relevant to a provenance- and claim-oriented knowledge system because it treats identity assertions as deployed, directed, source-sensitive graph data rather than as automatically safe global equality. Its distinctions among resource-level SameAs networks, publisher-level PLD abstractions, and class-level similarity networks provide useful design patterns for separating canonical identity, source-local identity claims, publisher provenance, and schema-level inference surfaces *(p.146-p.157)*.

## Open Questions
- [ ] How would the reported component counts and degree distributions change on a modern Linked Data crawl rather than BTC 2010? *(p.159)*
- [ ] Which alternative assumptions about owl:sameAs symmetry and transitivity give the most useful CLS network for ontology alignment without over-merging? *(p.156-p.159)*
- [ ] Can PLD-level community detection be made robust to publisher rehosting, mirrors, and blank-node named-graph assumptions? *(p.150-p.154)*
- [ ] What classifiers best distinguish CLS equivalence, subclass, overlap, and error cases using sameAs-mediated common instances? *(p.156-p.157)*

## Related Work Worth Reading
- Halpin and Hayes, "When owl:sameAs isn't the same", for identity-link semantics and alternative interpretations of owl:sameAs *(p.147, p.158)*.
- McCusker and McGuinness, "owl:sameAs considered harmful to provenance", for provenance and ground-truth risks from strong identity assertions *(p.147, p.158)*.
- Jaffri, Glaser, and Millard, "URI disambiguation in the context of linked data", for context-dependent equivalence and co-reference management *(p.147, p.158-p.159)*.
- Ge et al., "Object Link Structure in the Semantic Web", for graph-structure analysis and object link graphs related to schema-level relations *(p.158)*.
- Nikolov, Uren, and Motta, "Data Linking: Capturing and Utilising Implicit Schema-level Relations", for deriving schema-level mappings from instance-level links *(p.158-p.160)*.

## Collection Cross-References

### Already in Collection
- [When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data](../Halpin_2010_OwlSameAsIsntSame/notes.md) - cited for the critique that deployed owl:sameAs often fails strict identity semantics and motivates weaker or contextual identity relations.
- [Towards Identity in Linked Data](../McCusker_2010_TowardsIdentityLinkedData/notes.md) - cited for provenance and ground-truth risks created by treating owl:sameAs as unconditional identity.

### New Leads (Not Yet in Collection)
- Jaffri, Glaser, and Millard (2008) - "URI disambiguation in the context of linked data" - relevant for context-dependent co-reference management.
- Vatant (2007) - "Using owl:sameAs in linked data" - relevant for non-symmetric mashup-oriented sameAs usage.
- Ge et al. (2010) - "Object Link Structure in the Semantic Web" - relevant for graph-structure analysis and schema-level relations from instance links.
- Nikolov, Uren, and Motta (2010) - "Data Linking: Capturing and Utilising Implicit Schema-level Relations" - relevant for deriving schema-level mappings from instance-level links.

### Supersedes or Recontextualizes
- This paper recontextualizes the semantic critiques in Halpin et al. and McCusker and McGuinness by adding large-scale BTC 2010 deployment statistics and graph abstractions, but it does not supersede their semantic or provenance analyses.

### Cited By (in Collection)
- [The sameAs Problem: A Survey on Identity Management in the Web of Data](../Raad_2019_SameAsProblemSurvey/notes.md) - cites this paper as an early large-scale analysis of owl:sameAs deployment and implications.

### Conceptual Links (not citation-based)
- [sameAs.cc: The Closure of 500M owl:sameAs Statements](../Beek_2018_SameAs.ccClosure500MOwl/notes.md) - continues the large-scale sameAs-network line of work with closure over hundreds of millions of explicit links, while Ding et al. emphasize BTC 2010 deployment structure, PLD abstraction, and class-level effects.
- [Is my:sameAs the same as your:sameAs? Lenticular Lenses for Context-Specific Identity](../Idrissou_2017_LenticularLensesContextSpecificIdentity/notes.md) - addresses the same problem from a context-specific identity perspective, complementing Ding et al.'s evidence that deployed sameAs links should not be flattened into unconditional global equality.
- [Not Quite the Same: Identity Constraints for the Web of Linked Data](../Melo_2013_NotQuiteSameIdentity/notes.md) - provides a constraint-based approach to detecting problematic identity links, which is a downstream use case suggested by Ding et al.'s class-level similarity and error-detection discussion.
