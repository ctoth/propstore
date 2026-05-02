---
title: "CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories"
authors: "André Valdestilhas, Tommaso Soru, Axel-Cyrille Ngonga Ngomo"
year: 2017
venue: "Proceedings of Web Intelligence, Leipzig, Germany, August 2017; final DOI venue WI 2017"
doi_url: "https://doi.org/10.1145/3106426.3106497"
pages: 8
---

# CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories

## One-Sentence Summary
CEDAL detects inconsistent transitive RDF identity links by partitioning a link-repository graph with union-find and flagging clusters that contain distinct resources from the same dataset, avoiding full equivalence-closure materialization at Web scale. *(p.1-p.3)*

## Problem Addressed
Linked Data link repositories contain large numbers of cross-knowledge-base links, especially `owl:sameAs`, but transitivity can imply that two distinct URIs inside the same source dataset denote the same entity, which violates the authors' use of URI uniqueness within a dataset and indicates either a wrong link path or an error in the source knowledge base. *(p.1)* Classical reasoners can detect such contradictions through equivalence closure, but closure computation has worst-case quadratic size, creates a much larger query substrate, and did not scale to millions of links in the authors' Pellet experiments. *(p.1)* The paper asks whether erroneous links can be detected efficiently and whether linkset consistency can be discovered without computing all property-axiom closures. *(p.1-p.2)*

## Key Contributions
- Defines CEDAL, a time-efficient algorithm for detecting erroneous links in large-scale link repositories without computing all equivalence closures required by the property axiom. *(p.2-p.3)*
- Tracks consistency problems inside link repositories by returning erroneous resource candidates, their original file/linkset name, dataset, and path evidence. *(p.3)*
- Shows the algorithm is scalable in sequential, CPU-parallel, and GPU-parallel configurations. *(p.2, p.5-p.6)*
- Applies CEDAL to LinkLion, processing 19,200,114 `owl:sameAs` links in 4.6 minutes and finding 1,352,366 erroneous candidates over 254 domains and 553 linkset files. *(p.4)*
- Introduces linkset-quality measures based on the number of erroneous candidates, with the implemented evaluation focused on M1, the consistency index. *(p.4)*

## Study Design
- **Type:** Algorithm design plus empirical runtime and link-quality evaluation. *(p.3-p.6)*
- **Population:** LinkLion link repository; 19,606,657 `sameAs` triples including duplicates and 19,200,114 processed non-duplicate links. *(p.4)*
- **Intervention(s):** Run CEDAL over merged LinkLion linksets using graph partitioning/union-find; compare runtime against ClosureGenerator and Pellet for closure-like tasks. *(p.3-p.6)*
- **Comparator(s):** Classical closure computation with ClosureGenerator and reasoning with Pellet; also provenance-specific comparison across sameas.org, LIMES, Silk, and DBpedia Extraction Framework. *(p.5-p.6)*
- **Primary endpoint(s):** Runtime scalability and count/rate of erroneous resource candidates. *(p.4-p.6)*
- **Secondary endpoint(s):** Linkset ranking score, consistency index M1 by provenance, CPU/GPU scaling. *(p.4-p.6)*
- **Follow-up:** Manual validation of a random sample of 100 errors found 90% were type (2), but the authors state automatic distinction was infeasible because semantic accuracy needs human feedback and many URIs were unreachable due to HTTP 404/500/503/timeouts. *(p.4)*

## Methodology
The method models the union of all input linksets as an RDF graph in which RDF resources are graph nodes and links are edges. Each linkset connects subject resources described in one dataset with object resources described in another dataset. The algorithm partitions the graph into connected components with union-find, then inspects each partition for repeated dataset membership among distinct resources. If more than one resource in a cluster belongs to the same dataset, CEDAL flags those resources as erroneous candidates because equivalent resources should not be duplicated inside a single dataset under the paper's uniqueness assumption. *(p.2-p.3)*

The implementation uses adjacency lists and graph partitions rather than computing transitive closure. Each directed edge is stored once, and a bidirectional edge is represented as two directed edges. Partition processing can be run independently and in parallel, including CPU/GPU load distribution. *(p.2-p.3, p.5)*

## Key Equations / Statistical Models

Transitive property definition:

$$
\forall a,b,c \in X : (p(a,b) \wedge p(b,c)) \Longrightarrow p(a,c)
$$

Here `p` is a relation between two elements of a set `X`; `owl:sameAs` is treated as an equivalence relation that is reflexive, symmetric, and transitive. *(p.2)*

RDF graph partitioning:

$$
\bigcup_{1 \le i \le k} P_i = V,\qquad P_i \cap P_j = \emptyset \text{ for } i \ne j
$$

Here `G = (V,E,lbl,L)` is a graph, `C` is a division of `V` into `k` partitions `P_1,...,P_k`, `E_C` is the set of edges whose vertices belong to different partitions, `lbl : E \cup V \to L` labels edges or vertices, and `L` is a set of labels. *(p.2)*

Link membership:

$$
(s,p,o) \in L : s \in D_i,\ o \in D_j,\ i \ne j
$$

Here a link `L` in the union of linksets contains triples whose subject resource is in dataset `D_i` and whose object resource is in a different dataset `D_j`. *(p.3)*

Candidate restriction:

$$
\forall r_i,r_j \in P : r_i \ne r_j \Rightarrow (r_i,x,r_j) \in L^* \vee (r_j,x,r_i) \in L^*
$$

Each candidate `P` is a set of resources belonging to the same dataset and connected through the transitive link closure `L^*`, with `x` typically being `owl:sameAs`. *(p.3)*

Positive candidate definition:

$$
P \in P^+ \Longleftrightarrow (\exists r_1 \in P \cap D_1,\ r_2 \in P \cap D_2) \therefore D_1 = D_2 \Rightarrow r_1 \ne r_2
$$

The positive class contains candidates with errors: resources in the same candidate cluster are in the same dataset but are distinct resources. *(p.3)*

Negative candidate definition:

$$
P \in P^- \Longleftrightarrow (\forall r_1 \in P \cap D_1,\ r_2 \in P \cap D_2) \therefore D_1 = D_2 \Rightarrow r_1 = r_2
$$

The negative class contains candidates without the duplicated-resource error under the same dataset condition. *(p.3)*

Consistency index:

$$
M1 = \frac{\sum_{P \in P^-} |P|}{\sum_{P \in P} |P|}
$$

Here `P^-` is the set of consistent, non-erroneous candidates; M1 is the rate of consistent resources inside linkset repositories and is called the consistency index. *(p.4)*

Semantic-accuracy-oriented metric:

$$
M2 = \frac{|\{P \in P^+ : \forall r_i,r_j \in P,\ r_i \ne r_j \Rightarrow f(r_i,p,r_j)=1\}| + |P^-|}{|P|}
$$

Here `f(s,p,o)` verifies whether triple `(s,p,o)` holds in the real world, returning 1 if true and 0 otherwise. This metric addresses type (1) semantic-accuracy errors and is left for future work. *(p.4)*

Redundancy-oriented metric:

$$
M3 = \frac{|\{P \in P^+ : \exists r_i,r_j \in P,\ r_i \ne r_j \Rightarrow f(r_i,p,r_j)=0\}| + |P^-|}{|P|}
$$

This metric addresses type (2) consistency/conciseness errors and is dependent on M2; it is also left for future work. *(p.4)*

Erroneous-candidate ranking score:

$$
\mu = \frac{|C|(|C|-1)}{2}
$$

The score uses the cardinality of `C`, the detected erroneous candidates, to rank knowledge-base pairs by the number of potentially wrong pairings inside a candidate set. *(p.5)*

Complexity claim:

$$
O(n^2) \to O(m \log n)
$$

The authors describe replacing full closure computation with adjacency lists plus union-find graph partitioning as decreasing time complexity from quadratic closure behavior to `O(m log n)`, where `m` is the number of union/find operations over `n` elements. *(p.1, p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Linked Data Web cross-KB facts | - | facts | - | >500,000,000 | 1 | Motivation-scale estimate for link statements across knowledge bases. |
| Processed LinkLion `owl:sameAs` links | - | links | 19,200,114 | - | 1,4 | Processed by CEDAL in 4.6 minutes; table reports 19,606,657 `sameAs` triples with duplicates. |
| LinkLion `sameAs` triples including duplicates | - | triples | 19,606,657 | - | 4 | Table 1, 99.9% of LinkLion links. |
| CEDAL processing time on full LinkLion sameAs links | - | minutes | 4.6 | - | 1,4 | Using configuration (2), Intel Xeon Core i7 with 40 cores and 128 GB RAM. |
| Error fraction among considered `owl:sameAs` links | - | percent | 13 | >=13 | 1,6,8 | At least 13% of considered links were erroneous. |
| Erroneous candidates found | - | candidates | 1,352,366 | - | 4 | Full LinkLion run. |
| Domains with errors | - | domains | 254 | - | 4 | Full LinkLion run. |
| Linkset files with errors | - | files | 553 | - | 4 | Full LinkLion run; 48.3% had fewer than 10 erroneous resources. |
| Manual validation sample size | - | occurrences | 100 | - | 4 | Random sample of errors manually analyzed. |
| Manual sample type (2) share | - | percent | 90 | - | 4 | Type (2) consistency/conciseness errors. |
| Laptop test configuration CPU | - | cores | Intel Core i7 | - | 4 | 8 GB RAM, NVIDIA NVS4200, Windows 10, Java SE Development Kit 8. |
| Server test configuration CPU | - | cores | Intel Xeon Core i7, 40 cores | - | 4 | 128 GB RAM, Ubuntu 14.04.5 LTS, Java SE Development Kit 8. |
| sameas.org provenance error rate | - | percent | 13.5 | - | 6 | Table 4, 3,792,326 errors over 28,130,994 resources, M1 0.865. |
| LIMES provenance error rate | - | percent | 4.1 | - | 6 | Table 4, 1,130 errors over 27,819 resources, M1 0.951. |
| Silk provenance error rate | - | percent | 2.8 | - | 6 | Table 4, 5,933 errors over 208,300 resources, M1 0.972. |
| DBpedia Extraction Framework error rate | - | percent | 1.4 | - | 6 | Table 4, 12,615 errors over 914,180 resources, M1 0.986. |
| All-framework error rate | - | percent | 13.0 | - | 6 | Table 4, 3,812,004 errors over 29,281,293 resources, M1 0.870. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Full LinkLion processing | Runtime | 4.6 minutes | - | - | 19,200,114 `owl:sameAs` links on 40-core Xeon configuration | 4 |
| Erroneous links considered | Percent erroneous | at least 13% | - | - | LinkLion `owl:sameAs` links considered by CEDAL | 1,6,8 |
| Manual sample composition | Percent type (2) | 90% | - | - | 100 manually analyzed error occurrences | 4 |
| sameas.org provenance quality | Error rate / M1 | 13.5% / 0.865 | - | - | sameas.org-generated links | 6 |
| LIMES provenance quality | Error rate / M1 | 4.1% / 0.951 | - | - | LIMES-generated links | 6 |
| Silk provenance quality | Error rate / M1 | 2.8% / 0.972 | - | - | Silk-generated links | 6 |
| DBpedia Extraction Framework quality | Error rate / M1 | 1.4% / 0.986 | - | - | DBpedia Extraction Framework links | 6 |
| Closure comparison | Relative speed | up to three orders faster than Pellet at 10^6 triples | - | - | Figure 7 comparison with Pellet and ClosureGenerator | 6 |

## Methods & Implementation Details
- Input to Algorithm 1 is a set of links `L`, each of the form `(s,p,o)` with subject dataset and target dataset annotations; output is an error list with erroneous nodes. *(p.3)*
- CEDAL first computes graph partitions with `getPartitions(G(V,E))`; for each partition `P`, it builds `clusterDataset` by pushing each resource `r` and its extracted dataset into a resource-to-dataset map. *(p.3)*
- For each resource in `clusterDataset`, if `countDataset(r) > 1`, the algorithm pushes `resource.originalFileName + resource.dataset + resource.path` into `ErrorList`. *(p.3)*
- `getPartitions(G(V,E))` iterates over vertices, pushes each resource and extracted dataset into the map, connects all nodes related to vertex `v` into a union-find structure, pushes the union-find result as graph partition `V` into `P`, and returns `P`. *(p.3)*
- The example workflow merges multiple linksets, graph-partitions and clusters the merged graph, detects clusters where a dataset has two or more resources, and outputs the wrong paths in original linksets. *(p.3)*
- The algorithm can classify discovered erroneous candidates into semantic-accuracy errors and consistency/conciseness errors, but automatic classification is limited by the need for human judgment and URI reachability failures. *(p.3-p.4)*
- The parallel implementation separates graph partitions across threads and spreads those threads over CPU/GPU cores when available. *(p.5)*
- CEDAL preserves provenance of links rather than automatically removing links, because the output is a set of candidates requiring semantic assessment and human feedback. *(p.6-p.7)*

## Figures of Interest
- **Figure 1 (p.2):** Manual detection example where Freebase contains two resources for Barack Obama/Obama II that become equivalent through cross-dataset links to DBpedia/OpenCyc, exposing erroneous resource candidates in the same dataset.
- **Figure 2 (p.3):** CEDAL pipeline: merge linksets, graph partition and cluster, run error detection, and output suspicious same-dataset resources and wrong paths.
- **Figure 3 (p.3):** Two error types: semantic-accuracy error (`dbr:dresden owl:sameAs geo:leipzig`) and consistency/conciseness error where DBpedia has duplicated Leipzig resources linked to the same GeoNames city.
- **Figure 4 (p.5):** Error-rank bar charts for top 5 knowledge-base pairs with more candidates and top 5 with fewer candidates, using legends from Table 3.
- **Figure 5 (p.6):** Runtime results by input size, CPU, and GPU; GPU improves more clearly for input size `10^6` than for `10^3`.
- **Figure 6 (p.5):** CPU/GPU partition distribution workflow for CEDAL.
- **Figure 7 (p.6):** Pellet vs. ClosureGenerator vs. CEDAL; CEDAL is significantly faster at larger input sizes.

## Results Summary
CEDAL processed all 19,200,114 LinkLion `owl:sameAs` links in 4.6 minutes on the 40-core Xeon configuration, found 1,352,366 erroneous candidates, and showed that 48.3% of the 553 linkset files with detected errors had fewer than 10 erroneous resources. *(p.4)* In provenance analysis, sameas.org links had a 13.5% error rate and M1 0.865, while LIMES, Silk, and the DBpedia Extraction Framework all had below 5% errors and higher M1 scores. *(p.6)* Runtime experiments show CEDAL scales with larger linksets and can benefit from CPU/GPU parallelism, with Figure 7 showing substantially better performance than Pellet and ClosureGenerator at `10^6` triples. *(p.5-p.6)*

## Limitations
CEDAL detects erroneous candidates and suspicious paths, not necessarily the specific wrong link, because any link along an equivalence path or the source knowledge base itself may be responsible. *(p.1, p.3)* Semantic-accuracy classification requires human judgment, and many URIs cannot be reached due to HTTP errors or timeouts, so the paper does not automate M2/M3 evaluation. *(p.4)* The authors focus on computing M1 and leave M2/M3 and a broader survey of linkset quality for future work. *(p.4, p.8)* CEDAL does not automatically remove links or constraint violations; it preserves provenance and produces candidates for downstream validation. *(p.6-p.7)*

## Arguments Against Prior Work
- Full transitive closure has quadratic worst-case size and produces a much larger query substrate, making it too expensive for Web-scale linked data. *(p.1)*
- Pellet, described as the fastest inference engine to the authors' knowledge, did not scale to the millions of links found on the Web of Data in their closure-style experiments. *(p.1, p.6)*
- Quality work focused on dataset completeness or SKOS vocabularies does not directly evaluate large-scale link repositories or `owl:sameAs` link consistency at LinkLion scale. *(p.7)*
- Some prior erroneous-link approaches mitigate constraints automatically or operate on smaller datasets, whereas CEDAL classifies errors, preserves provenance, and scales from 1 million to 19 million links. *(p.7)*

## Design Rationale
- The core design avoids closure materialization and instead uses adjacency lists plus graph partitioning because error detection only needs connected equivalence clusters and same-dataset duplicates. *(p.1-p.3)*
- Union-find is chosen to compute partitions efficiently, reducing the complexity burden compared with closure-based reasoning. *(p.1, p.3, p.8)*
- Provenance is retained in the output because the algorithm cannot always know which link or source assertion caused a bad equivalence; downstream human or semantic validation is needed. *(p.3-p.7)*
- Parallelization over partitions is natural because errors can be calculated independently for each graph partition. *(p.5)*

## Testable Properties
- If a partition contains two or more distinct resources from the same dataset, CEDAL must emit an erroneous candidate with source file, dataset, and path provenance. *(p.3)*
- For a linkset repository dominated by transitive `owl:sameAs`, graph partitioning should detect same-dataset duplicates without computing full closure. *(p.1-p.3)*
- On LinkLion-scale input, a correct reproduction should process approximately 19.2 million sameAs links and find about 1.35 million erroneous candidates under the paper's data/version assumptions. *(p.4)*
- sameas.org-generated links should show worse consistency than LIMES, Silk, and DBpedia Extraction Framework links under the paper's provenance analysis. *(p.6)*
- CEDAL runtime should grow much more slowly than Pellet/ClosureGenerator on the tested triple sizes, especially near `10^6` triples. *(p.6)*

## Relevance to Project
CEDAL is directly relevant to propstore's identity and concept-merge discipline. It gives a concrete graph-side check for when transitive identity closure collapses distinct source-local resources that should remain separate, supporting a policy where identity closure is a query-time or analysis-time hypothesis rather than an unconditional canonical merge. Its provenance-preserving error output also matches the need to keep source-local authorship and path evidence attached to candidate contradictions rather than silently normalizing them away.

## Open Questions
- [ ] How should propstore represent same-dataset duplicate resources and cross-source identity paths so CEDAL-like checks can run without collapsing canonical identity?
- [ ] Can CEDAL's partition-level evidence be integrated with argumentation or ATMS labels to represent "one of these identity links is wrong" without immediately selecting a culprit?
- [ ] How should M2/M3-style semantic and redundancy checks be implemented when human feedback or unreachable source URIs are required?
- [ ] What data model best preserves original linkset filename, dataset, and path evidence for later provenance-aware review?

## Related Work Worth Reading
- Melo 2013, "Not quite the same: Identity constraints for the web of linked data" for formal identity-constraint violations and repair. *(p.7, reference [10])*
- Beek et al. 2014, "LOD laundromat" for large-scale linked-data cleaning context. *(p.7, reference [7])*
- Nentwig et al. 2014, "LinkLion: A link repository for the web of data" for the repository used in the evaluation. *(p.8, reference [14])*
- Tarjan 1975, "Efficiency of a good but not linear set union algorithm" for the union-find basis. *(p.8, reference [21])*
- Zaveri et al. 2015, "Quality assessment for linked data: A survey" for quality dimensions used to frame error types. *(p.8, reference [26])*
