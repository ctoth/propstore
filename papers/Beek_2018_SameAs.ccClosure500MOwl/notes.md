---
title: "sameAs.cc: The Closure of 500M owl:sameAs Statements"
authors: "Wouter Beek, Joe Raad, Jan Wielemaker, Frank van Harmelen"
year: 2018
venue: "Extended Semantic Web Conference (ESWC 2018), LNCS vol. 10843"
doi_url: "https://doi.org/10.1007/978-3-319-93417-4_5"
pages: "65-80"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-04-04T07:55:54Z"
---
# sameAs.cc: The Closure of 500M owl:sameAs Statements

## One-Sentence Summary
Presents sameAs.cc, the largest collected dataset and web service of owl:sameAs identity statements from the LOD Cloud (558M explicit statements, 179M unique terms), including their equivalence closure and analytical characterization of identity set distributions, namespace linking patterns, and schema assertions about owl:sameAs itself.

## Problem Addressed
The owl:sameAs predicate is essential for the Semantic Web because it allows independently minted identifiers to be recognized as denoting the same entity. However, no central authority enforces the Unique Name Assumption, so the same real-world entity can be denoted by many different names across datasets. A comprehensive, up-to-date collection of all owl:sameAs assertions and their transitive closure did not previously exist at the scale of the entire LOD Cloud. *(p.0)*

Prior work (Schmachtenberg et al. 2014) crawled 8.38M owl:sameAs statements from 559 resources; Ding et al. 2010 studied owl:sameAs from the Falcon search engine's 4.7M statements. The LOD Laundromat (Beek et al. 2014) collected 558M statements — 66x more. *(p.1)*

## Key Contributions
1. Largest downloadable dataset of identity statements gathered from the LOD Cloud, including equivalence closure, exposed via web service. *(p.2)*
2. In-depth analysis of the dataset: explicit and implicit identity relations, distribution properties, namespace-level linking patterns, schema assertions. *(p.2)*
3. Efficient approach for extracting, storing, and calculating identity closure that fits on a USB stick and runs from a regular laptop. *(p.2)*

## Methodology
Data source: LOD Laundromat corpus, which crawls and cleans Linked Open Data into a uniform format (HDT). Identity statements extracted via SPARQL CONSTRUCT queries over the LOD-a-lot file (single HDT file of entire LOD Cloud). *(p.4)*

Closure computed using union-find with path compression and merge-by-rank, implemented in C++. The entire closure computation takes approximately 5 minutes on a regular laptop. *(p.5)*

The dataset is served via RocksDB (for fast key-value lookup of identity sets) and HDT (for SPARQL queries over schema data). *(p.12)*

## Key Equations / Statistical Models

### Explicit Identity Relation
$$
\sim_e
$$
Where: $\sim_e$ is the set of pairs $(x,y)$ for which a statement $\langle x, \texttt{owl:sameAs}, y \rangle$ has been asserted in a publicly accessible dataset.
*(p.2)*

### Implicit Identity Relation
$$
\sim_i
$$
Where: $\sim_i$ is the explicit identity relation closed under equivalence (reflexivity, symmetry, and transitivity).
*(p.2)*

### Equivalence Set
$$
[x]_\sim = \{y \mid x \sim y\}
$$
Where: $[x]_\sim$ is the equivalence set (identity set) of term $x$ — all terms considered identical to $x$ under relation $\sim$.
*(p.2)*

### Full Materialization Size
$$
|\sim_i| \approx 2 \times 10^{12}
$$
Where: this is the number of owl:sameAs triples that would be needed to fully materialize the closure. Impractical to store directly.
*(p.10)*

### Identity Set Size Distribution
Power-law distribution with exponent $3.3 \pm 0.04$ for identity set cardinality in $\sim_i$. *(p.9)*

### Statements-per-Term Distribution
Power-law distribution with coefficient $-2.528$ for the number of owl:sameAs statements per term (from 2011 Billion Triple Challenge dataset; the 2015 LOD Laundromat corpus does not follow a power-law). *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Explicit owl:sameAs statements | - | count | 558,943,116 | - | 6 | From LOD Laundromat corpus |
| Unique terms in ~_e | - | count | 179,739,567 | - | 6 | IRIs: 175,078,015 (97.41%), Literals: 3,583,673 (1.99%), Blank nodes: 1,077,847 (0.60%) |
| Unique terms in ~_i | - | count | 179,672,306 | - | 9 | Slightly fewer than ~_e due to reflexive-only terms |
| Reflexive-only terms | - | count | 67,261 | - | 9 | 0.037% of terms appear only in reflexive owl:sameAs |
| Non-singleton identity sets | - | count | 48,999,148 | - | 9 | From LOD-a-lot extraction |
| Singleton identity sets | - | count | 5,044,948,869 | - | 9 | Terms in ~_i with trivial identity set |
| Unique terms in non-singleton sets | - | count | 5,093,948,017 | - | 9 | |
| Size-2 identity sets | - | count | 31,337,556 | 63.96% | 9 | Majority of non-singleton sets |
| Largest identity set cardinality | - | count | 177,794 | - | 9 | Contains Albert Einstein, countries, empty string |
| Identity set size power-law exponent | - | - | 3.3 | +/- 0.04 | 9 | |
| Statements-per-term power-law coeff | - | - | -2.528 | - | 7 | From 2011 BTC dataset only |
| Namespaces (host-based) | - | count | 2,618 | - | 8 | In namespace-level identity graph |
| Namespace graph edges | - | count | 10,791 | - | 8 | |
| Namespace graph components | - | count | 142 | - | 8 | |
| Schema assertions about owl:sameAs | - | count | 2,773 | - | 11 | Extending owl:sameAs beyond OWL definition |
| HTTP(S) IRIs | - | count | 174,995,686 | 97.36% | 6 | Of all IRIs in identity relation |
| URN IRIs | - | count | 47,126 | - | 6 | |
| info: IRIs | - | count | 34,718 | - | 6 | |
| Closure computation time | - | min | ~5 | - | 5 | C++ on regular laptop |
| Sort/dedup time | - | min | ~26 | - | 4 | GNU sort unique on SSD |
| Full materialization triples | - | count | ~2 * 10^12 | - | 10 | Impractical to store |

## Methods & Implementation Details

### Explicit Identity Extraction (Sec 3.1)
- Source: LOD-a-lot HDT file (single file containing entire LOD Cloud) *(p.4)*
- SPARQL CONSTRUCT query extracts all `owl:sameAs` triples *(p.4)*
- Uses Prolog HDT library (`hdt` C++ library) to stream result set *(p.4)*
- Output: sorted N-Triples file *(p.4)*
- SPARQL query pattern: `{?s owl:sameAs ?o} UNION {?o owl:sameAs ?s}` to capture both directions *(p.4)*

### Deduplication (Sec 3.2)
- Explicit identity relation is reduced reflexivity and symmetry *(p.4)*
- Canonical ordering: for each pair, store `(min(x,y), max(x,y))` *(p.4)*
- GNU sort unique used for deduplication; takes 26 minutes on SSD *(p.4)*
- Reduces input data significantly before closure computation *(p.4)*

### Closure Algorithm (Sec 3.3) — Union-Find
Three cases when processing edge `(x, z)`: *(p.5)*
1. **Neither x nor z in any identity set:** Create new set, assign both x and z *(p.5)*
2. **One in a set, other not:** Add the unassigned term to the existing set. If the new term has a mapping from identity set id to RDF term via RocksDB, the key of the new identity set is from the existing set *(p.5)*
3. **Both in different identity sets:** Merge smaller set into larger (merge by rank). Update values in RocksDB to merge the smaller into the larger. Merging of values takes place by iterating through smaller set and inserting into larger. *(p.5)*
- Implementation: C++ with RocksDB for persistent key-value storage *(p.5)*
- Each identity set file (N) stores sorted RDF terms *(p.5)*
- Entire closure computation: ~5 minutes on regular laptop *(p.5)*
- Initial creation step only needs to be performed once *(p.5)*

### Identity Schema Extraction (Sec 3.4)
- SPARQL query extracts all triples where owl:sameAs appears as subject or object *(p.6)*
- Stored in separate HDT file *(p.6)*

### Query Answering
- SPARQL query engine resolves identity by looking up `[x]` for every matched binding *(p.3)*
- External identity service needed because Semantic Web has no backlinks *(p.3)*
- Query answering under entailment: when a SPARQL query is evaluated under OWL entailment, the engine must follow a large number of owl:sameAs links *(p.3)*

## Figures of Interest
- **Fig 1 (p.6):** Overview of terms in identity relation — tree breakdown: 179.7M terms -> IRIs (175M), Literals (3.6M), Blank nodes (1.1M); IRIs by scheme: HTTP (175M), URN (47K), info (35K), HTTPS (201), other (485)
- **Fig 2 (p.7):** Number of owl:sameAs statements per term (log-log scale) — roughly power-law distribution for incoming arcs, outgoing arcs, and total statements
- **Fig 3 (p.8):** Number of terms in identity links by namespace (bar chart) — highly skewed, most namespaces have 0-10 terms
- **Fig 4 (p.9):** Distribution of internal edges, incoming links, and outgoing links by namespace — most namespaces have incoming links, fewer have outgoing, confirming asymmetric linking pattern
- **Fig 5 (p.10):** All inter-dataset links in LOD Cloud — network visualization showing dbpedia.org and freebase.com as central hubs with dense interconnections
- **Fig 6 (p.10):** Distribution of identity set cardinality in ~_i — x-axis lists all 48,999,148 non-singleton identity sets, showing sharp power-law tail with very few extremely large sets
- **Fig 7 (p.13):** Screenshot of sameAs.cc Closure API showing identity set for Albert Einstein — demonstrates the web service returning all equivalent URIs

## Results Summary
- 558,943,116 explicit owl:sameAs statements extracted from the LOD Cloud *(p.6)*
- 179,739,567 unique terms participate in the explicit identity relation *(p.6)*
- Equivalence closure yields 48,999,148 non-singleton identity sets containing 5,093,948,017 unique terms *(p.9)*
- 63.96% of non-singleton identity sets have exactly 2 members *(p.9)*
- Largest identity set has 177,794 members (includes Albert Einstein, country names, and the empty string — indicating data quality issues) *(p.9)*
- Full materialization of ~_i would require ~2 trillion triples — impractical *(p.10)*
- Namespace-level analysis reveals 2,618 namespaces connected by 10,791 edges in 142 components *(p.8)*
- Most namespaces use owl:sameAs only for linking to other datasets (Unique Name Assumption holds internally), but some have internal owl:sameAs edges *(p.8)*
- High-centrality hubs: dbpedia.org, freebase.com, bibsonomy.org, geonames.org, bio2rdf.org *(p.8)*
- 2,773 schema assertions about owl:sameAs extend it beyond its OWL definition, some introducing semantic bugs (e.g., treating identity as mere equivalence) *(p.11)*

## Limitations
- The dataset is a snapshot of the LOD Cloud at crawl time; it becomes stale as data changes *(p.13)*
- The largest identity set (177,794 members) reveals serious data quality problems — owl:sameAs is used incorrectly to assert relatedness rather than true identity *(p.9)*
- Some super-property assertions introduce semantic bugs (e.g., `skos:exactMatch` being declared equivalent to owl:sameAs conflates identity with close-enough matching) *(p.11)*
- No mechanism to assess the quality or correctness of individual owl:sameAs assertions — the closure propagates errors *(p.9)*
- schema:sameAs from Schema.org has substantially different semantics ("same topic" vs equality) but gets conflated *(p.2)*

## Arguments Against Prior Work
- Prior collections of owl:sameAs (Ding et al. 2010, Schmachtenberg et al. 2014) were orders of magnitude smaller. The LOD Laundromat-based approach yields 66x more statements than previous best. *(p.1)*
- The Billion Triple Challenge dataset's power-law distribution for statements-per-term does not hold for the full LOD Laundromat corpus — prior distributional claims were artifacts of smaller samples. *(p.7)*
- Existing query engines that evaluate under OWL entailment must follow owl:sameAs links, but there is no centralized identity service. Each engine must independently crawl and maintain its own owl:sameAs data. *(p.3)*

## Design Rationale
- **Union-find with merge-by-rank chosen over naive approaches** because the identity sets can be very large (up to 177K members) and merging must be efficient. *(p.5)*
- **RocksDB chosen for persistent storage** because identity sets need disk-backed key-value access; the full closure is too large for memory on a regular laptop but RocksDB handles it efficiently. *(p.5)*
- **HDT chosen for schema storage** because it supports SPARQL queries compactly. *(p.12)*
- **Canonical ordering (min/max) for deduplication** to exploit symmetry of owl:sameAs and reduce data before closure computation. *(p.4)*
- **External web service architecture** because the Semantic Web lacks backlinks — you cannot discover that resource X is owl:sameAs Y by dereferencing X alone. *(p.3)*
- **N-Triples format for ~_e distribution** allows standard tools; RocksDB snapshot for ~_i allows fast random access to identity sets. *(p.12)*

## Testable Properties
- Identity closure must be reflexive, symmetric, and transitive over all terms *(p.2)*
- `|terms in ~_i| <= |terms in ~_e|` because closure can only merge, not create new terms *(p.9)*
- For any term x, `x in [x]_~` (reflexivity of equivalence sets) *(p.2)*
- If `x in [y]_~` then `y in [x]_~` (symmetry) *(p.2)*
- If `x in [y]_~` and `y in [z]_~` then `x in [z]_~` (transitivity) *(p.2)*
- Merge-by-rank: when merging two identity sets, the smaller is always merged into the larger *(p.5)*
- Non-singleton identity set count (48,999,148) + singleton count should account for all terms *(p.9)*
- Identity set size distribution follows power law with exponent ~3.3 *(p.9)*
- Majority (63.96%) of non-singleton identity sets should have size 2 *(p.9)*

## Relevance to Project
This paper is directly relevant to propstore's concept layer and vocabulary reconciliation. The owl:sameAs closure problem is structurally identical to the concept identity problem in propstore: multiple names/URIs for the same concept must be reconciled without prematurely collapsing disagreement. Key takeaways:
1. **Union-find with merge-by-rank** is the right algorithm for computing identity closures at scale
2. **Identity propagation introduces errors** — the largest identity set conflates Einstein with countries, showing that transitive closure of "same as" claims without quality filtering is dangerous
3. **The non-commitment principle applies** — propstore should store all identity assertions but compute closure only at render time, not at storage time
4. **Schema assertions about identity predicates can introduce semantic bugs** — sub-property and super-property relationships on owl:sameAs change its meaning in ways data publishers may not intend

## Open Questions
- [ ] How should propstore handle owl:sameAs-style identity assertions that are known to be erroneous? Should error correction happen at storage or render time? [Addressed by Melo_2013_NotQuiteSameIdentity — formalizes detection via unique name constraints and repair via minimum multicut optimization; correction is a graph operation over the link structure, orthogonal to storage vs render time]
- [ ] Is the power-law distribution of identity set sizes (exponent 3.3) a universal property of identity closure, or specific to the LOD Cloud?
- [ ] The paper notes schema:sameAs has different semantics from owl:sameAs — how should propstore distinguish between "truly identical" and "same topic" relationships?

## Collection Cross-References

### Already in Collection
- [[Raad_2019_SameAsProblemSurvey]] — survey by the same research group (Raad, Beek, van Harmelen) that builds on this paper's dataset to categorize identity link errors and detection approaches

### Cited By (in Collection)
- [[Raad_2019_SameAsProblemSurvey]] — cites this paper as the large-scale empirical dataset underpinning the survey's analysis of identity link proliferation and error propagation

### New Leads (Not Yet in Collection)
- ~~Halpin et al. (2010) — "When owl:sameAs Isn't the Same" — foundational critique of sameAs semantics in the Semantic Web~~ → NOW IN COLLECTION: [[Halpin_2010_OwlSameAsIsntSame]]
- Ding et al. (2010) — earlier owl:sameAs deployment study from Falcon search engine at smaller scale
- Beek et al. (2014) — LOD Laundromat: the data infrastructure underlying this paper

### Now in Collection (previously listed as leads)
- [[Halpin_2010_OwlSameAsIsntSame]] — Foundational critique of owl:sameAs. Proposes Similarity Ontology with eight graded identity properties. Empirical study shows ~50% of owl:sameAs in LOD Cloud are not true identity. Beek's closure analysis at scale confirms and quantifies the identity confusion Halpin first characterized.

### Supersedes or Recontextualizes
- This paper provides the empirical dataset that [[Raad_2019_SameAsProblemSurvey]] surveys and categorizes

### Conceptual Links (not citation-based)
- [[Raad_2019_SameAsProblemSurvey]] — Strong: same research group, directly builds on this dataset. Raad 2019 categorizes the identity errors that this paper's closure reveals (e.g., the 177K-member identity set conflating Einstein with countries). Together they form a problem-statement + solution pair for identity quality on the Semantic Web.
- [[Melo_2013_NotQuiteSameIdentity]] — Strong: de Melo's constraint-based cleaning method (minimum multicut with LP relaxation) directly addresses the erroneous identity links that sameAs.cc closure reveals. The unique name assumption constraints de Melo formalizes would detect violations in the largest identity sets here.

## Related Work Worth Reading
- Beek et al. (2014) LOD Laundromat — the data source for this paper's identity statements
- Ding et al. (2010) — earlier study of owl:sameAs from Falcon search engine
- Halpin et al. (2010) — analysis of owl:sameAs in the Semantic Web (identity crisis) → NOW IN COLLECTION: [[Halpin_2010_OwlSameAsIsntSame]]
- Raad et al. (2018) — detecting erroneous identity links on the web of data
- Schmachtenberg et al. (2014) — adoption of linked data best practices across topical domains
