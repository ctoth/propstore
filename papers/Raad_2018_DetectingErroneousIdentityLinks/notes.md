---
title: "Detecting Erroneous Identity Links on the Web Using Network Metrics"
authors: "Joe Raad, Wouter Beek, Frank van Harmelen, Nathalie Pernelle, Fatiha Saïs"
year: 2018
venue: "The Semantic Web - ISWC 2018, Lecture Notes in Computer Science 11136"
doi_url: "https://doi.org/10.1007/978-3-030-00671-6_23"
pages: "391-407"
---

# Detecting Erroneous Identity Links on the Web Using Network Metrics

## One-Sentence Summary
The paper defines a topology-only procedure for ranking potentially erroneous `owl:sameAs` statements by compacting the explicit identity graph, detecting Louvain communities inside each equality set, and assigning each link an error degree from community density, inter-community connectivity, and link symmetry. *(p.5-p.8)*

## Problem Addressed
`owl:sameAs` has strict model-theoretic identity semantics: if `x owl:sameAs y`, every property of `x` is also attributed to `y` and vice versa, yet Linked Open Data uses it incorrectly in practice, including cases where sources link merely related or contextual resources as identical. *(p.1-p.2)* Existing approaches often require trusted source metadata, UNA assumptions, descriptions, property mappings, vocabulary alignments, or ontology axioms; the authors target an automatic, scalable method that can operate on the `owl:sameAs` network itself. *(p.3-p.4)*

## Key Contributions
- Defines a compact weighted undirected identity network derived from directed `owl:sameAs` assertions by removing reflexive edges and collapsing reciprocal links into weight 2 edges. *(p.5)*
- Defines equality sets as connected components of the compact identity network and ranks links inside each equality set after Louvain community detection. *(p.6-p.8)*
- Introduces intra-community and inter-community error-degree formulas that make low-weight links in sparse communities, or low-weight links between weakly connected communities, more suspicious. *(p.7)*
- Evaluates the method on LOD-a-lot / sameAs.cc scale: 558.9M explicit identity edges, 179.73M nodes, about 331M compact weighted edges, about 49M equality sets, about 556M ranked statements, and 24.35M detected communities. *(p.8-p.9)*
- Shows by manual evaluation that links with error degree <= 0.4 were all judged true identity links in the sampled set, while links above 0.8 and especially near 1 include many related or unrelated terms. *(p.13-p.14)*

## Study Design
- **Type:** Algorithmic graph-ranking method with manual accuracy/recall evaluations. *(p.12-p.14)*
- **Population:** `owl:sameAs` statements scraped from the 2015 LOD Laundromat via the LOD-a-lot dataset: 28B unique triples, from which 558.9M distinct identity pairs and 179.73M nodes are extracted. *(p.7-p.8)*
- **Intervention(s):** Build compact identity network, partition into equality sets, run Louvain per equality set, compute error degree per non-reflexive `owl:sameAs` statement. *(p.5-p.9)*
- **Comparator(s):** Manual judgments over sampled links; qualitative comparison to known communities for Dublin and Barack Obama equality sets. *(p.10-p.14)*
- **Primary endpoint(s):** Manual label distribution by error-degree bin and recall for newly injected erroneous identity links. *(p.13-p.14)*
- **Secondary endpoint(s):** Runtime, scalability, error-degree distribution, size and structure of equality sets and detected communities. *(p.8-p.9, p.14-p.15)*
- **Follow-up:** No longitudinal follow-up; authors propose online recalculation after LOD updates as future work. *(p.15)*

## Methodology
The method first extracts an explicit identity network from a directed labeled RDF data graph by keeping only edges whose label includes `owl:sameAs`. It then compacts the explicit identity network into a weighted undirected graph: reflexive identity assertions are omitted, one-way links have weight 1, and reciprocal directed links are represented as a single undirected edge with weight 2. Connected components of this compact graph are equality sets. Within each equality set, Louvain community detection produces non-overlapping communities, and every link is categorized as intra-community or inter-community. The assigned error degree increases when the edge is weakly asserted and when the local community or inter-community connection is sparse. *(p.5-p.8)*

The design requirements are explicitly operational: the computation must have low memory footprint, scale to the largest identity networks and preferably all LOD `owl:sameAs` links, run in parallel so errors can be detected soon after publication, and support incremental recalculation by re-ranking only the equality sets directly involved in an added or removed `owl:sameAs` link. *(p.6)*

## Key Equations / Statistical Models

$$
G = (V, E, \Sigma_E, l_E)
$$
Where `G` is a directed labeled data graph, `V` is the set of nodes, `E` is the set of edges, `Sigma_E` is the set of edge labels, and `l_E : E -> Sigma_E` maps edges to edge labels. RDF nodes are terms appearing in subject or object position of at least one triple. *(p.5)*

$$
N_{ex} = (V_{ex}, E_{ex})
$$
Where `N_ex` is the explicit identity network extracted as the edge-induced subgraph of `G` containing edges `e` such that `owl:sameAs` is included in `l_E(e)`. *(p.5)*

$$
I = (V_I, E_I, \{1,2\}, w)
$$
Where `I` is the compact identity network; `V_I` is the set of nodes, `E_I` is the set of undirected edges, `{1,2}` are edge labels/weights, and `w : E_I -> {1,2}` assigns edge weights. *(p.5)*

$$
E_I := \{ e_{ij} \in E_{ex} \mid i \ne j \}
$$
Where reflexive `owl:sameAs` links are discarded from the compact network. *(p.5)*

$$
V_I := V_{ex}[E_I]
$$
Where `V_ex[E_I]` is the vertex-induced subgraph over identity edges retained in `E_I`. *(p.5)*

$$
w(e_{ij}) :=
\begin{cases}
1, & \text{if } e_{ij} \in E_{ex}\\
2, & \text{if } e_{ji} \in E_{ex}
\end{cases}
$$
Where one-way edges receive weight 1 and reciprocal identity assertions are compacted into a weight 2 edge. The printed definition is abbreviated; the surrounding prose states the intent: if both `e_ij` and `e_ji` occur, represent them by one undirected edge with weight 2. *(p.5)*

$$
C(Q_k) = \{C_1, C_2, ..., C_n\}
$$
Where `Q_k` is an equality set, and Louvain returns non-overlapping communities whose union is `Q_k`. *(p.6)*

$$
\bigcup_{1 \le i \le n} C_i = Q_k
$$
Where the communities cover the equality set. *(p.6)*

$$
\forall C_i, C_j \in C(Q_k) \text{ such that } i \ne j,\ C_i \cap C_j = \emptyset
$$
Where Louvain communities are non-overlapping. *(p.6)*

$$
err(e_C) = \frac{1}{w(e_C)} \times \left(1 - \frac{W_C}{|C| \times (|C| - 1)}\right)
$$
Where `e_C` is an intra-community link in community `C`, `w(e_C)` is its weight, `|C|` is community size, and `W_C` is total weight over intra-community links in `C`. Lower density and lower edge weight produce higher error degree. *(p.7)*

$$
W_C = \sum_{e_C \in E_C} w(e)
$$
Where `E_C` is the set of intra-community links in community `C`. *(p.7)*

$$
err(e_{C_{ij}}) = \frac{1}{w(e_{C_{ij}})} \times \left(1 - \frac{W_{C_{ij}}}{2 \times |C_i| \times |C_j|}\right)
$$
Where `e_Cij` is an inter-community link between communities `C_i` and `C_j`, `w(e_Cij)` is its weight, and `W_Cij` is total weight over links connecting the two communities. Sparse connectivity and lower link weight produce higher error degree. *(p.7)*

$$
W_{C_{ij}} = \sum_{e_{C_{ij}} \in E_{C_{ij}}} w(e)
$$
Where `E_Cij` is the set of inter-community links between communities `C_i` and `C_j`. *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Explicit identity network edge count | `|E_ex|` | edges | 558.9M | - | p.8 | Distinct identity pairs extracted from LOD-a-lot via HDT C++ library. |
| Explicit identity network node count | `|V_ex|` | nodes | 179.73M | - | p.8 | Terms in extracted identity network. |
| Compact identity network edge count | `|E_I|` | weighted edges | ~331M | - | p.8 | After omitting reflexive and duplicate symmetric edges. |
| Compact identity network term count | `|V_I|` | terms | 179.67M | - | p.8 | After compaction, 67,261 nodes only appearing in removed edges are omitted. |
| Reflexive edges omitted | - | edges | ~2.8M | - | p.8 | Reflexive statements discarded in compact network. |
| Duplicate symmetric edges omitted | - | edges | ~225M | - | p.8 | Reciprocal assertions compacted into weight 2 edges. |
| Symmetric-edge redundancy share | - | percent | 68% | - | p.8 | Share of identity-network edges redundantly asserted with weight 2. |
| Equality set count | - | connected components | ~49M | - | p.9 | Partitioned under 5 hours using 2 CPU cores. |
| Link-ranking runtime | - | minutes | 80 | - | p.9 | On 8GB RAM Windows 10 with 2 CPU cores. |
| Total ranked statements | - | statements | ~556M | - | p.9 | Non-reflexive statements assigned error degree. |
| Detected community count | - | communities | 24.35M | - | p.9 | Community sizes vary between 2 and 4,934 terms. |
| Average community size | - | terms/community | ~7 | 2-4,934 | p.9 | Across detected communities. |
| Low error-degree share | - | percent of statements | ~73% | [0, 0.4] | p.9, p.14 | Statements below 0.4 in Fig. 1; all manually evaluated links in this range were same links in Table 1. |
| Largest equality-set term count | `Q_max` | terms | 177,794 | - | p.10 | Example largest equality set. |
| Largest equality-set compact edge count | - | weighted undirected edges | 2,849,650 | - | p.10 | Compacted from 5,547,463 distinct `owl:sameAs` statements. |
| Largest equality-set statement share | - | percent | ~1% | - | p.10 | Approximate share of all `owl:sameAs` statements. |
| Largest equality-set Louvain communities | - | communities | 930 | 32-2,320 terms | p.10 | Applied Louvain on `Q_max`. |
| Dublin community size | `C_258` | terms | 242 | - | p.10-p.11 | Community containing `http://dbpedia.org/resource/dublin`; includes city, weather, and visitor-information terms. |
| Barack Obama equality-set terms | `Q_obama` | terms | 440 | - | p.11 | Equality set containing `http://dbpedia.org/resource/Barack_Obama`. |
| Barack Obama equality-set edges | - | weighted undirected edges | 7,615 | - | p.11 | Built from 14,917 directed `owl:sameAs` statements. |
| Barack Obama Louvain communities | - | communities | 4 | 34-166 terms | p.11 | Communities `C0` through `C3`. |
| `C0` Obama community size | `C0` | terms | 166 | - | p.11 | 98% of links are cross-language symmetric DBpedia IRIs for Barack Obama the person. |
| `C1` Obama community size | `C1` | terms | 162 | - | p.11 | Mostly DBpedia IRIs for Obama in roles and political functions. |
| `C2` Obama community size | `C2` | terms | 78 | - | p.11 | Presidency and administration terms. |
| `C3` Obama community size | `C3` | terms | 34 | - | p.11 | Mixed entities including person, senate career, and a misused literal. |
| Random manual-evaluation sample | - | links | 200 | 40 per bin | p.13 | Four authors judged 50 links each over error-degree bins. |
| Additional high-error evaluation | - | links | 60 | 20 per set | p.13-p.14 | Evaluated links with error degree >0.9 under S1, S2, and S3 conditions. |
| Synthetic recall trial terms | - | terms | 40 | - | p.14 | Random distinct terms explicitly checked not to be linked by `owl:sameAs`; includes 5 from same equality set. |
| Synthetic recall generated edges | - | edges | 780 | - | p.14 | All undirected edges among 40 terms, added one at a time with weight 1. |
| Synthetic erroneous-link error-degree range | - | error degree | - | 0.87-0.9999 | p.14 | Error degrees of newly introduced erroneous identity links. |
| Recall at threshold 0.99 | - | percent | 93% | threshold 0.99 | p.14 | Recall for synthetic injected erroneous links. |
| Total experiment runtime | - | hours | 11 | - | p.14-p.15 | Runtime for evaluating available identity links at LOD scale. |
| High-confidence erroneous links | - | statements | >1.2M | [0.99, 1] | p.14 | Many from large equality sets; example largest equality set has about 13K such links. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Manual identity accuracy for error degree 0-0.2 | same links / evaluated | 35/35 excluding can't-tell; 35/40 including can't-tell | - | - | 40 sampled links in bin | p.13 |
| Manual identity accuracy for error degree 0.2-0.4 | same links / evaluated | 22/22 excluding can't-tell; 22/40 including can't-tell | - | - | 40 sampled links in bin | p.13 |
| Manual identity accuracy for error degree 0.4-0.6 | same links / evaluated | 18/21 excluding can't-tell; 18/40 including can't-tell | - | - | 40 sampled links in bin | p.13 |
| Manual identity accuracy for error degree 0.6-0.8 | same links / evaluated | 7/9 excluding can't-tell; 7/40 including can't-tell | - | - | 40 sampled links in bin | p.13 |
| Manual identity accuracy for error degree 0.8-1 | same links / evaluated | 15/22 excluding can't-tell; 15/40 including can't-tell | - | - | 40 sampled links in bin | p.13 |
| Non-same rate for error degree 0.8-1 | related/unrelated share | 31.8% | - | - | 7 non-same among 22 evaluated excluding can't-tell | p.13 |
| High-error S1 true identity rate | same / evaluated | 6/12 excluding can't-tell; 6/20 including can't-tell | - | - | Largest equality set, 20 random links | p.14 |
| High-error S2 true identity rate | same / evaluated | 6/10 excluding can't-tell; 6/20 including can't-tell | - | - | All links with error degree about 1, 20 random links | p.14 |
| High-error S3 false identity rate | related+unrelated / evaluated | 15/17 = 88.2% excluding can't-tell; 15/20 including can't-tell | - | - | Largest equality set with error degree about 1 | p.14 |
| Synthetic erroneous-link recall at threshold 0.99 | recall | 93% | - | - | 780 generated one-off erroneous links | p.14 |

## Methods & Implementation Details
- The explicit identity network is extracted using a triple pattern query `(?, owl:sameAs, ?)` over the HDT C++ library; extraction took about 4 hours using one CPU core. *(p.8)*
- Equality-set partitioning of the compact identity network used an efficient graph partitioning algorithm described in earlier sameAs.cc work; it produced about 49M equality sets in just under 5 hours using 2 CPU cores. *(p.8-p.9)*
- Link ranking applies Louvain inside each equality set; the Java implementation is public at `http://github.com/raadjoe/LOD-Community-Detection`. *(p.8-p.9)*
- Error degrees for all ranked `owl:sameAs` statements were published in the sameAs.cc identity web service. *(p.9, p.15)*
- Manual evaluation labels were: `same`, `related`, `unrelated`, and `can't tell`; judges used LOD-a-lot descriptions and did not know each link's error degree. *(p.12)*
- For recall, the authors selected 40 different terms not explicitly linked by `owl:sameAs`, generated all 780 undirected pairwise edges, added each edge with weight 1, calculated its error degree, and removed it before testing the next edge. *(p.14)*

### Algorithm 1: Identity Links Ranking
1. Input a data graph `G`; output a set of pairs `E^err = {(e1, err(e1)), ..., (em, err(em))}` where `m` is the number of edges in the identity network extracted from `G`. *(p.8)*
2. Extract `I_ex <- ExtractSameAsEdges(G)`. *(p.8)*
3. Initialize compact identity network `I` as an empty graph. *(p.8)*
4. For each directed edge `(e(v1, v2) in I_ex and v1 != v2)`, set weight 2 if the reverse edge already exists in `I`; otherwise add the edge with weight 1. *(p.8)*
5. Partition `I` into equality sets `P <- I.partition()`. *(p.8)*
6. For each equality set `Q`, run `C_set <- LouvainCommunityDetectionAlgorithm(Q)`. *(p.8)*
7. For each community edge, compute `err(e)` with `intraCommunityErroneousness(c_i)` if it is intra-community; otherwise compute `err(e)` with `interCommunityErroneousness(c_i, c_j)` where `c_j` is the other endpoint community. *(p.8)*
8. Add `(e, err(e))` to `E^err` and return `E^err`. *(p.8)*

## Definitions
- **Data graph:** Directed labeled graph `G = (V, E, Sigma_E, l_E)`, with nodes, edges, edge labels, and edge-to-label mapping. *(p.5)*
- **Explicit identity network:** Edge-induced subgraph of a data graph that only includes edges whose label set includes `owl:sameAs`. *(p.5)*
- **Identity network:** Undirected weighted graph derived from the explicit identity network by excluding reflexive edges and compacting reciprocal directed assertions as weight 2. *(p.5)*
- **Equality set:** Connected component of the compact identity network. *(p.6)*
- **Intra-community link:** Weighted edge whose endpoints are both inside the same Louvain community. *(p.6)*
- **Inter-community link:** Weighted edge whose endpoints belong to two non-overlapping Louvain communities. *(p.7)*
- **Intra-community link error degree:** Error score for an intra-community edge, increasing when community density and edge weight decrease. *(p.7)*
- **Inter-community link error degree:** Error score for an inter-community edge, increasing when connectivity between endpoint communities and edge weight decrease. *(p.7)*

## Figures of Interest
- **Fig. 1 (p.9):** Error-degree distribution over about 556M non-reflexive `owl:sameAs` statements; about 73% fall below 0.4, the largest bin is 0.2-0.4, and a visible tail remains in 0.8-1.
- **Fig. 2 (p.10):** Excerpt of 242 terms in the Dublin community; shows many multilingual DBpedia forms for Dublin, but also non-city terms such as weather and visitor-information resources.
- **Fig. 3 (p.12):** Louvain communities for the Barack Obama equality set: four non-overlapping communities separating person, roles, administration/presidency, and mixed/misused resources.

## Results Summary
The compacted identity network preserves enough structure for large-scale ranking while removing reflexive and reciprocal redundancy: from 558.9M explicit identity edges it produces about 331M weighted undirected edges over 179.67M terms. *(p.8)* Louvain-based ranking assigns error degrees to about 556M non-reflexive statements in 80 minutes on a modest Windows machine, and the full experiment runs in about 11 hours. *(p.9, p.14-p.15)*

Qualitative analysis supports the community assumption but also exposes its limits. The largest equality set contains terms for many countries, cities, things, and persons, so it clearly includes many erroneous identity assertions; Louvain divides it into 930 communities that mostly group related terms while keeping unrelated terms in other communities. *(p.10)* The Dublin community shows that same-community links are not necessarily correct because a community may contain weather and visitor-information resources alongside Dublin-city resources. *(p.10-p.11)* The Obama equality set shows that low-density role and administration communities can give correct links high error scores when non-symmetrical links sparsely connect many related terms. *(p.11-p.13)*

Manual evaluation shows monotonic usefulness at the extremes. Links with error degree <= 0.4 were 100% true identity links among evaluated non-`can't tell` cases. Links with error degree between 0.4 and 0.8 were often true identity links but sometimes related terms. Links above 0.8 were unreliable, with 31.8% of evaluated non-`can't tell` cases referring to related or unrelated terms. When the threshold is strengthened to about 0.99 and restricted to large equality sets, 88.2% of evaluated non-`can't tell` links were false identity statements. *(p.13-p.14)*

## Limitations
- Same-community `owl:sameAs` links can still be wrong; the Dublin example includes resources about Dublin weather and visitor information within a community centered on Dublin-city IRIs. *(p.10-p.11)*
- Correct identity links can receive high error degree when a community is sparse or non-symmetrical, as in Obama community `C1`, where correct links to roles/functions receive high scores due to low density. *(p.12)*
- The middle score range is not decisive: for remaining `owl:sameAs` links outside the strongest validation/detection zones, 50-85% were judged true identity links, so refined content-based methods are still needed. *(p.15)*
- Accuracy may improve by combining or comparing results from multiple community detection methods; the paper uses Louvain as a scalable, empirically strong baseline. *(p.15)*
- The approach is topology-only and does not inspect descriptions except during manual evaluation, so it cannot resolve all semantic distinctions between identity, role, contextual identity, and strong relatedness. *(p.12-p.15)*

## Arguments Against Prior Work
- Source-trustworthiness approaches require trusted-source assumptions and solve conflicts through source trust refinement, which is not available for all LOD identity links. *(p.3)*
- UNA-violation approaches assume individual datasets obey a Unique Name Assumption, but that assumption may be false for datasets built over long periods or by many contributors. *(p.3-p.4)*
- Content-based and ontology-axiom approaches require descriptions, direct/outing properties, ontology rules, or property mappings, while this paper's method only requires the `owl:sameAs` graph topology. *(p.3-p.4)*
- Prior network-metric work built local networks for selected resources and compared classic metrics to ideal distributions; this paper ranks links directly in the large-scale identity network itself. *(p.3-p.4)*

## Design Rationale
- Compacting reciprocal identity assertions into weight 2 preserves the stronger evidential signal of symmetric publication while reducing graph size. *(p.5)*
- Equality sets are the computational unit because the closure of `owl:sameAs` forms an equivalence relation; connected components provide a unique partition and keep potential link representation linear rather than quadratic. *(p.6)*
- Louvain is chosen because comparative studies found it combines high accuracy with good computational performance, and the task needs large-scale topology-only partitioning. *(p.4)*
- Intra-community error degree uses community density because a link inside a sparse community is less supported by local topology than a link inside a dense community. *(p.7)*
- Inter-community error degree uses density between communities because a cross-community link is less suspicious when the communities are heavily connected to each other and more suspicious when it is an isolated bridge. *(p.7)*

## Testable Properties
- Reflexive `owl:sameAs` statements must not contribute explicit edges to the compact identity network. *(p.5)*
- Reciprocal directed `owl:sameAs` pairs must become one undirected compact edge with weight 2. *(p.5)*
- Equality sets must be connected components of the compact identity network. *(p.6)*
- For a fixed community density, a weight 1 link must have higher error degree than a weight 2 link because the formulas multiply by `1 / w(e)`. *(p.7)*
- For fixed edge weight, decreasing intra-community density must increase intra-community error degree. *(p.7)*
- For fixed edge weight, decreasing inter-community connection density must increase inter-community error degree. *(p.7)*
- Links with error degree <= 0.4 should mostly validate as true identity links in LOD-a-lot-like data; the sample found 100% true identity among non-`can't tell` cases. *(p.13-p.14)*
- Links with error degree near 1 in large equality sets should be strong erroneous-link candidates; the S3 evaluation found 88.2% non-same among non-`can't tell` cases. *(p.14)*
- Injected false identity links between distinct terms should often receive error degree above 0.99; recall at threshold 0.99 was 93% in the synthetic test. *(p.14)*

## Relevance to Project
This paper provides a concrete, scalable scoring model for identity-link evaluation that depends only on the identity-link graph. For propstore, it is useful as a candidate provenance/quality signal for imported equivalence claims: reciprocal support, component structure, community membership, and bridge-like cross-community links can become explicit evidence dimensions rather than treating all identity claims as equivalent.

## Open Questions
- [ ] How should the project represent topology-only suspicion as a defeasible claim or justification rather than a binary rejection of identity?
- [ ] Should the score be calibrated per source graph, per equality set size, or globally as in the paper's LOD-a-lot evaluation?
- [ ] How should role/context links that are "related but not same" be represented when they are too useful to discard but too weak for canonical identity?
- [ ] Would modern Leiden/community detection variants improve stability relative to Louvain without breaking the paper's scalability assumptions?

## Related Work Worth Reading
- Beek, Schlobach, and van Harmelen 2016 on contextualized semantics for `owl:sameAs`; relevant for representing softer identity contexts. *(p.15)*
- Beek et al. 2018 on sameAs.cc closure of 500M `owl:sameAs` statements; this paper relies on the same infrastructure for equality-set partitioning. *(p.15-p.16)*
- Guéret et al. 2012 on assessing linked-data mappings using network measures; direct predecessor for network metrics. *(p.16)*
- Halpin et al. 2010 on when `owl:sameAs` is not the same; core conceptual background for the sameAs problem. *(p.16)*
- Valdestilhas et al. 2017 on time-efficient erroneous-link detection in large link repositories; closely related scalable identity-error detection. *(p.16)* → NOW IN COLLECTION: [CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories](../Valdestilhas_2017_CEDALTime-efficientDetectionErroneous/notes.md)

## Collection Cross-References

### Now in Collection (previously listed as leads)
- [CEDAL: Time-Efficient Detection of Erroneous Links in Large-Scale Link Repositories](../Valdestilhas_2017_CEDALTime-efficientDetectionErroneous/notes.md) — Provides a scalable graph-partitioning baseline for erroneous identity-link detection. It flags same-dataset duplicate resources inside transitive identity clusters, complementing Raad et al.'s topology/community-score approach to suspicious links.
