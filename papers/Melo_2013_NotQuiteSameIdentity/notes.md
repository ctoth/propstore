---
title: "Not Quite the Same: Identity Constraints for the Web of Linked Data"
authors: "Gerard de Melo"
year: 2013
venue: "Proceedings of the AAAI Conference on Artificial Intelligence"
doi_url: "https://doi.org/10.1609/aaai.v27i1.8468"
pages: "1092-1098"
affiliation: "ICSI Berkeley"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-04T07:59:41Z"
---
# Not Quite the Same: Identity Constraints for the Web of Linked Data

## One-Sentence Summary
Provides formal criteria for identity vs. near-identity in Linked Data, models the detection and removal of erroneous owl:sameAs links as a minimum multicut optimization problem (NP-hard), and presents an LP relaxation + Hungarian algorithm solution that identifies and removes hundreds of thousands of constraint violations at Web scale.

## Problem Addressed
The Web of Linked Data relies on owl:sameAs links to connect equivalent entities across datasets, but many existing sameAs links do not reflect genuine identity -- they conflate near-identical, similar, or merely related entities. This degrades data quality and breaks applications that depend on strict identity semantics. No scalable method existed to detect and repair these erroneous links systematically. *(p.0)*

## Key Contributions
- Theoretical analysis of identity vs. near-identity criteria for Linked Data, distinguishing strict Leibniz's Law identity from weaker notions of similarity *(p.0-1)*
- Formalization of identity constraints as unique name assumptions within datasets (DBpedia constraints) *(p.2)*
- Proof that the constraint satisfaction problem is NP-hard and APX-hard (minimum multicut reduction) *(p.2, Theorem 6)*
- LP relaxation algorithm with region growing for approximate solutions *(p.3)*
- Hungarian algorithm variant for bipartite matching when linking two data sources *(p.3)*
- Web-scale experiments on BTC 2011 dataset (22M+ sameAs links) detecting 500K+ constraint violations *(p.4-6)*

## Methodology
The paper proceeds in three stages: (1) theoretical analysis of identity criteria; (2) formalization as a combinatorial optimization problem with complexity results; (3) experimental evaluation on real Web-scale sameAs data from the Billion Triple Challenge 2011 dataset. *(p.0)*

The approach treats datasets as having implicit unique name assumptions -- within a single dataset, distinct URIs refer to distinct entities. When sameAs links create equivalence classes that merge URIs from the same dataset, this violates the constraint. The task is to remove a minimum-weight set of sameAs edges to restore consistency. *(p.1-2)*

## Key Equations / Statistical Models

### Claim 1: Leibniz's Law (Identity of Indiscernibles)
$$
x = y \iff \forall P(P(x) \leftrightarrow P(y))
$$
Where: $x, y$ are entities; $P$ ranges over all properties. Two entities are identical iff they share all properties. *(p.0)*

### Claim 2: Salience of Properties
No universal agreed-upon way of determining which properties should count as salient in determining near-identity and similarity. *(p.1)*

### DBpedia Constraint Definition
$$
D_i = \{(u_1, u_2, \ldots) \mid u_j \in D_i, u_j \neq u_k \text{ for } j \neq k\}
$$
Where: $D_i$ is a distinctness constraint -- a collection of sets of nodes from $V$ such that any two nodes $u, v \in D_i$ from different subsets $i \neq k$ are asserted to correspond to distinct entities. *(p.2)*

### Uniqueness Constraint Formalization
Given an undirected graph $G = (V, E)$ of identity links and distinctness constraints $D_1, \ldots, D_n$, an optimal cut $C$ is a cut in a set of edges $C \subseteq E$ that makes $G$ consistent with the $D_i$ if and only if the modified graph $G' = (V, E \setminus C)$ has no connected path between any two nodes $u, v \in D_i$ for any constraint $D_i$. *(p.2, Definition 4)*

### Edge Weight Definition
$$
w(e) = \sum_{t \in \text{sameAs}(e)} \text{weight}(t)
$$
Where: edge weights can be defined to quantify the number of sameAs links between the two URIs in either direction; alternatively one could also plug in similarity measures to account for other linking similarity and other evidence. *(p.2, Definition 5)*

### Optimization Objective
Given additional edge weights $w(e)$, an optimal cut $C$ is a cut with minimum $\sum_{e \in C} w(e)$. *(p.2, Definition 5)*

### LP Relaxation
$$
\text{minimize } \sum_{(i,j) \in E} d_{ij} \cdot w_{ij} \text{ subject to}
$$
$$
\sum_{(i,j) \in p} d_{ij} \geq 1, \quad \forall \text{ paths } p \text{ from } s_l \text{ to } t_l, \quad l = 1, \ldots, k
$$
$$
0 \leq d_{ij} \leq 1, \quad \forall (i,j) \in E
$$
Where: $d_{ij}$ are decision variables indicating whether edge $(i,j)$ is in the cut; $w_{ij}$ are edge weights; $s_l, t_l$ are source-target pairs that must be separated; $k$ is the number of demand pairs. *(p.3)*

Decision variables $d_{ij}$ indicate whether $e \in C$, i.e. the identity link represented by $e$ should be removed. Variables $s_{ij}, t_{ij}$ indicate the degree of separation of a node $i$ from nodes in $D_{ij}$. Line (3) ensures that $s_{ij}$ can only be greater/real if all edges along paths are placed in $C$, and hence line (2) ensures that the solution satisfies all constraints. *(p.3)*

### Bipartite Matching (Theorem 7)
$$
\text{If } G = (V, E) \text{ is bipartite with respect to disjoint node subsets } V_a, V_b \subseteq V, \text{ then computing the minimal cut } C^* \subseteq E \text{ to satisfy two constraints } D_a = \{\{v_1\}, \ldots, \{v_{n_a}\}\} \text{ for } v_i \in V_a \text{ and } D_b = \{\{v_1\}, \ldots, \{v_{n_b}\}\} \text{ for } v_j \in V_b \text{ is equivalent to solving the LSAP.}
$$
Where: LSAP = Linear Sum Assignment Problem (Hungarian algorithm). This applies when matching between exactly two data sources. *(p.3, Theorem 7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of URIs (BTC 2011) | - | count | 34,419,740 | - | 4 | Total URIs in sameAs graph |
| Number of URIs (sameAs.org) | - | count | 4,074,106 | - | 4 | sameAs.org subset |
| Connected components (BTC) | - | count | 12,735,767 | - | 5 | In BTC 2011 sameAs graph |
| Connected components (sameAs.org) | - | count | 1,387,660 | - | 5 | In sameAs.org |
| Average component size (BTC) | - | ratio | 2.70 | - | 5 | URIs per component |
| Average component size (sameAs.org) | - | ratio | 2.94 | - | 5 | URIs per component |
| Total sameAs statements | - | count | 22,441,457 | - | 4 | BTC 2011 dataset |
| Constraint violations (BTC, pre-cleaning) | - | count | 519,170 | - | 5 | Node pairs violating constraints |
| Constraint violations (sameAs.org, pre-cleaning) | - | count | 138,906 | - | 5 | Node pairs |
| Edge violations per node (BTC) | - | count | 1.85 | - | 6 | Violations per connected component |
| Removed edges (BTC) | - | count | 280,086 | - | 6 | After constraint-based cleaning |
| Removed edges (sameAs.org) | - | count | 32,793 | - | 6 | After constraint-based cleaning |
| Node sets with DBpedia entities (DBLP) | - | count | 25,599 | - | 5 | Constraint analysis |
| Node sets with DBpedia entities (Freebase) | - | count | 22,396 | - | 5 | Constraint analysis |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Constraint violations detected | count | 519,170 | - | - | BTC 2011 node pairs | 5 |
| Edges removed for consistency | count | 280,086 | - | - | BTC 2011 | 6 |
| Violations per connected component | ratio | 1.85 | - | - | BTC 2011 | 6 |
| sameAs.org violations detected | count | 138,906 | - | - | sameAs.org node pairs | 5 |
| sameAs.org edges removed | count | 32,793 | - | - | sameAs.org | 6 |
| Most frequent domain in sameAs graph | - | DBpedia | - | - | BTC 2011, by edge count | 4 |

## Methods & Implementation Details
- Graph constructed from BTC 2011 Billion Triple Challenge dataset, a large collection of triples crawled from the Web *(p.4)*
- sameAs.org web site hosts the most well-known collection of coreferent links for Linked Data *(p.4)*
- BTC 2011 chosen to roughly match the version of sameAs.org data available at time *(p.4)*
- URIs from dataset used as nodes; sameAs links as undirected edges *(p.2)*
- Distinctness constraints derived from: (1) DBLP dataset URI prefix, (2) DBpedia URI prefix, (3) Freebase, (4) GeoNames, (5) MusicBrainz, (6) UniProt *(p.4, Table 2)*
- Quasi-unique name constraints with reduced awareness: valid URI checking (DBpedia 3.7) as special conditions *(p.4)*
- The constraint-based cleaning algorithm uses LP relaxation solved in polynomial time via region growing technique (Garg, Vazirani, and Vazirani 1996) and efficiently obtains a set of $d_e \in [0,1]$ that satisfy logarthmic approximation guarantees *(p.3)*
- Hungarian algorithm (Munkres 1957) used for bipartite case -- finds optimal stable matching in polynomial time *(p.3)*
- Weighted bipartite graph: edges are choices based on preference rankings without weights; Kuhn-Munkres algorithm finds optimal assignments for LSAP (linear sum assignment problem) *(p.3)*
- Connected components analyzed individually for constraint violations *(p.5)*
- Most frequent domains: DBpedia, Freebase, linkeddata.uriburner.com, lib-onv, Max Planck Institute for Informatics -- each involved in over 250,000 undirected edges *(p.4)*

## Figures of Interest
- **Fig 1 (p.2):** Example of a DBpedia constraint $D_1 = \{\text{dbpedia:Paul}, \text{dbpedia:Paula(redirect)}, \text{dbpedia:Paula}\}$ showing how to detect a spurious link from musicbrainz:Paula to dbip:Paula. Shows freebase:Paul, dbp:Paula, musicbrainz:Paulie, Paula(redirect), illustrating how transitive closure of sameAs can merge entities that should be distinct.

## Results Summary
- The method detects over half a million node pairs that have been identified although they stem from the same data source and are thus subject to unique name assumptions *(p.5)*
- The node pairs figures count the number of distinct unordered pairs of nodes that occur within the same connected component, yet are subject to one of the unique name constraints *(p.5)*
- In a few instances, constraint violations may stem not from incorrect links but from inadvertent duplicates within a dataset (e.g., two duplicate Wikipedia articles linked to separate DBpedia URIs with different titles that describe exactly the same entity in the strict Leibnizian sense) *(p.5)*
- After cleaning: violations per connected component dropped from 1.85 to 4.24 edges removed per violation on BTC 2011 *(p.6)*
- The number of edges removed is actually lower than the number of constraint violations, because the algorithm explicitly aims at deleting a minimal number of edges to ensure constraints are no longer violated *(p.6)*
- When two densely connected sets of nodes are connected by only a single bad sameAs link, detecting and removing that sameAs link may satisfy several constraints at once *(p.6)*

## Limitations
- The OWL standard does not make a Unique Name Assumption but instead provides owl:differentFrom property; in practice most publishers do not take the trouble of publishing owl:differentFrom statements between every pair of entities *(p.1)*
- It may not be clear what universe of properties to quantify over when assessing whether all properties are shared (Leibniz's Law) *(p.1)*
- Near-identity criteria do not make identity judgments trivial -- it is nearly unambiguously clear entities one is referring to because of the general problems of identification and reference *(p.1)*
- Stability of identity over time: especially if all parts have gradually been replaced (Ship of Theseus, human body) *(p.1)*
- Properties like skos:related could be used to define context; unfortunately on the Web we also find many incorrect uses of classes, e.g. humans described as being of type OWL ontology *(p.1)*
- owl:sameAs is very rarely even used; at least two nearly in order to be able to infer that the URIs one usually deals with refer to distinct entities *(p.1)*
- Quasi-unique name constraints only capture specific forms of identity defined by the OWL standard (owl:sameAs, owl:equivalentClass, owl:equivalentProperty) -- very rare; the properties equivalentClass and equivalentProperty are more frequent but semantics does not require full identity with respect to all properties but only extensional equivalence *(p.4)*
- Some other related properties include SKOS properties for different degrees of matches and bad URIs like references to a non-existent RDFS schema property and other misspellings *(p.4)*

## Arguments Against Prior Work
- Existing sameAs links frequently do not reflect genuine identity -- they are used informally to express similarity, relatedness, or approximate equivalence *(p.0)*
- The owl:sameAs property of the FOAF vocabulary is defined to be inverse functional, but it has been noted that people often provide the home page of their company, leading to incorrect identifications *(p.1)*
- Prior work (Halpin et al. 2010) on sameAs networks and beyond: analyzing the degree/nature and implications of owl:sameAs in Linked Data did not provide a computational method for cleaning *(p.6)*
- Ding et al. (2010) empirically studied owl:sameAs and Linked Data but did not offer automated constraint-based repair *(p.6)*

## Design Rationale
- Models problem as graph-based minimum multicut rather than pairwise classification: this preserves transitivity constraints and handles global consistency *(p.2)*
- Uses LP relaxation rather than exact ILP because the problem is NP-hard and APX-hard (Theorem 6) -- polynomial-time approximation is necessary for Web scale *(p.3)*
- Bipartite matching (Hungarian algorithm) for the special case of linking exactly two data sources -- this is polynomial-time exact, not approximate *(p.3, Theorem 7)*
- Distinctness constraints derived from dataset-internal URI structure rather than requiring explicit owl:differentFrom assertions -- pragmatic given that almost no one publishes differentFrom *(p.2)*
- Edge weights based on sameAs link count rather than content similarity -- allows purely structural analysis without requiring schema alignment *(p.2)*

## Testable Properties
- Two entities from the same dataset (same URI prefix) connected by a chain of sameAs links constitutes a constraint violation *(p.2)*
- Removing minimum-weight edges to eliminate all constraint violations is equivalent to minimum multicut *(p.2, Theorem 6)*
- For bipartite graphs (two datasets), the optimal cut equals the LSAP solution (Hungarian algorithm) *(p.3, Theorem 7)*
- Pairwise non-adjacency implies that connected components never contain more than one node from $V_a$ or more than one node from $V_b$ *(p.3)*
- The number of removed edges should be less than or equal to the number of constraint violations (one removal can fix multiple violations) *(p.6)*
- After cleaning, no connected component should contain two URIs from the same distinctness constraint set *(p.2)*

## Relevance to Project
Directly relevant to propstore's concept identity and vocabulary reconciliation layer. The paper provides:
1. **Formal criteria for when two identifiers should vs. should not be treated as the same concept** -- directly applicable to concept registry deduplication
2. **Graph-based constraint violation detection** -- applicable to detecting erroneous owl:sameAs-like merges in the concept graph
3. **Distinction between strict identity and near-identity** -- mirrors propstore's non-commitment principle (don't collapse disagreement in storage)
4. **Minimum multicut formalization** -- provides a principled optimization framework for deciding which merges to undo when constraints are violated
5. **Practical evidence** that sameAs misuse is widespread (500K+ violations in 22M links) -- validates the need for careful identity management

## Open Questions
- [ ] How to integrate the LP relaxation approach with propstore's existing concept merge/split operations
- [ ] Whether the distinctness constraints can be derived automatically from propstore's form/context structure
- [ ] How to handle the "near-identity" cases the paper identifies but does not resolve (Section 6 suggestions)
- [ ] Whether edge weights could incorporate semantic similarity from the concept layer rather than just link counts

## Collection Cross-References

### Already in Collection
- (none — key citations Halpin 2010, Ding 2010, Garg 1996 are not in collection)

### Cited By (in Collection)
- [[Raad_2019_SameAsProblemSurvey]] — categorizes de Melo 2013 as a "network analysis approach" to erroneous identity link detection (p.4 of Raad)

### New Leads (Not Yet in Collection)
- Halpin et al. (2010) — "When owl:sameAs Isn't the Same" — foundational critique of sameAs semantics, introduced contextual identity
- Ding et al. (2010) — "owl:sameAs and Linked Data: An empirical study" — large-scale empirical analysis of sameAs usage
- Garg, Vazirani, and Yannakakis (1996) — "Approximate max-flow min-cut/multiflow theorems" — algorithmic foundation for LP relaxation

### Conceptual Links (not citation-based)
- [[Raad_2019_SameAsProblemSurvey]] — Strong: surveys the entire owl:sameAs identity problem space that de Melo addresses computationally. Raad categorizes de Melo's method as network-based detection and places it among terminological, semantic, and content-based alternatives.
- [[Beek_2018_SameAs.ccClosure500MOwl]] — Strong: Beek's sameAs.cc dataset (558M statements, 49M identity sets) is the natural target for de Melo's constraint-based cleaning. The largest identity sets (177K+ members conflating unrelated entities) are exactly the kind of constraint violations de Melo's method detects.
- [[Kuhn_2014_TrustyURIs]] — Moderate: both address identity integrity on the Semantic Web but from different angles -- Kuhn via cryptographic content-hashing to prevent identifier spoofing, de Melo via graph constraints to detect erroneous identity links.

## Related Work Worth Reading
- Halpin, H., Hayes, P.J., McCusker, J.P., McGuinness, D.L., and Thompson, H.S. 2010. When owl:sameAs isn't the same. *Int'l Semantic Web Conference*. -- Analysis of sameAs semantics *(p.6)*
- Ding, L., Shinavier, J., Finin, T., and McGuinness, D.L. 2010. owl:sameAs and Linked Data: An empirical study. *2nd Web Science Conference*. -- Empirical sameAs analysis *(p.6)*
- Jain, P., Hitzler, P., Sheth, A.P., Verma, K., and Yeh, P.Z. 2010. Ontology alignment: linked open data. *ISWC 2010*. -- Graph-based disambiguation of Linked Data *(p.6)*
- Garg, N., Vazirani, V.V., and Yannakakis, M. 1996. Approximate max-flow min-cut/multiflow theorems and their applications. *SIAM Journal on Computing*. -- LP relaxation technique used *(p.3)*
- Kuhn, H.W. 1955. The Hungarian method for the assignment problem. -- Foundation for bipartite matching *(p.3)*
