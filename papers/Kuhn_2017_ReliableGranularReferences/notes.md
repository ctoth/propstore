---
title: "Reliable Granular References to Changing Linked Data"
authors: "Tobias Kuhn, Egon Willighagen, Chris Evelo, Nuria Queralt-Rosinach, Emilio Centeno, Laura I. Furlong"
year: 2017
venue: "ISWC 2017 (International Semantic Web Conference)"
doi_url: "https://doi.org/10.1007/978-3-319-68288-4_26"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:56:38Z"
---
# Reliable Granular References to Changing Linked Data

## One-Sentence Summary
This paper demonstrates that nanopublications with trusty URIs can provide granular, verifiable, persistent, and efficient references to evolving Linked Data datasets through incremental versioning and subset-based retrieval.

## Problem Addressed
Scientific datasets referenced by Linked Data URIs are brittle: identifiers point to dataset-level resources that change over time, making references unreliable and irreproducible. *(p.0)* Nanopublications introduce overhead from auxiliary triples (provenance, metadata, structural information), and it was unclear whether the approach could scale to dynamic, evolving datasets. *(p.0)*

Two specific problems with current dataset references: (1) Researchers can only specify at the dataset level which data they use as input -- they cannot reliably point to the exact subset; (2) There is no standard way of versioning datasets with version markers included, so researchers cannot be sure that others can later retrieve exactly the same dataset to reproduce results. *(p.1)*

## Key Contributions
- Demonstration that nanopublication overhead disappears when accounting for version history and incremental updates *(p.0)*
- Method for incremental versioning of nanopublication datasets using snapshots and incremental updates *(p.3-5)*
- Fingerprint and topic-based mechanism for creating decontextualized subsets that can be precisely and persistently referenced *(p.5-6)*
- Evaluation on WikiPathways (11-month incremental dataset) showing overhead turns into net gain *(p.8-10)*
- Evaluation on DisGeNET showing typical researcher subsets use only a small fraction of the full dataset *(p.8-11)*

## Methodology
The approach consists of three aspects: (1) using nanopublication concept to model datasets and their versions, (2) providing a method to create incremental datasets, and (3) connecting these components to allow flexible and reliable references to subsets of data resources. *(p.3)*

### Incremental Datasets with Nanopublications
Each nanopublication is a small RDF package with assertion, provenance, and publication info graphs, connected by trusty URIs (cryptographic hash-based identifiers). *(p.3)* A dataset version is represented as a nanopublication index -- a special nanopublication containing direct and indirect links to the nanopublications it contains. *(p.4)*

Index nanopublication sets have a size limit of 1000 entries (either elements or sub-indexes). All these links are established on trusty URIs, so the whole set structure can be cryptographically verified from just the URI of the top-index. *(p.4)*

### Snapshots to Incremental Datasets
Three kinds of changes to nanopublications: (1) removed from dataset, (2) added, (3) changed and replaced by a new version (old replaced by new). All remaining nanopublications remain unchanged and can be reused. *(p.4)*

Two approaches for calculating incremental updates: **change-based** and **timestamp-based**. *(p.5)*
- Change-based approach keeps separate lists of added and removed triples for each version after the first; the timestamp-based approach keeps all triples in the same collection but attaches timestamps of their addition or removal. *(p.5)*
- The latter has the advantage that they lead to the same overall triple count even if we require a triple to be duplicated to acquire more than one timestamp. *(p.5)*

### Fingerprints and Topics
Two concepts for decontextualized subsets: fingerprints and topics. *(p.5)*

**Fingerprints** -- like trusty URIs -- correspond to a cryptographic hash value based on the RDF content of nanopublications, but consider only a subset of the triples and may apply preprocessing and normalization. In the simplest case, a fingerprint ignores the content of the timestamp found in the publication info graph. Other variants are possible, such as ignoring the entire publication info graph. Can be configured for a given dataset and the intended use of its incremental versioning. *(p.5-6)*

**Topics** are similar to fingerprints, but normally correspond to a URI instead of a hash. A new nanopublication with an existing topic or included in the new dataset version, but the new nanopublication will be marked as an update of the old. *(p.6)*

## Key Equations / Statistical Models

$$
\text{overhead} = \frac{\text{nanopub triples} - \text{content triples}}{\text{content triples}}
$$
Where: nanopub triples = total triples in nanopublication representation, content triples = subject-predicate-object triples carrying actual data content.
*(p.2)*

$$
\text{negative overhead} = 1 - \frac{\text{total cumulative nanopub triples}}{\text{cumulative snapshot triples}}
$$
Where: this measures the gain from incremental versioning -- when overhead becomes negative, the incremental approach uses fewer triples than traditional snapshots.
*(p.10)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Index nanopub set size limit | - | entries | 1000 | - | 4 | Max elements or sub-indexes per index nanopub |
| Average triple count (assertion graph) | - | triples | ~5 | 1-20+ | 1 | Varies by dataset; DisGeNET ~5, WikiPathways varies |
| Overhead ratio (existing datasets) | - | ratio | - | 0.42-6.45 | 2 | Table 1: ranges from neuroLex (0.42) to DisGeNET v3.0.1.0 (6.45) |
| WikiPathways version count | - | versions | 11 | - | 8 | Monthly snapshots June 2016 - May 2017 |
| DisGeNET nanopub count | - | nanopubs | ~80M | - | 8 | v2.1 with 80M nanopublications |
| Nanopub server instances | - | servers | 16 | - | 7 | Distributed server network as of evaluation |
| DisGeNET papers studied | - | papers | 20 | - | 8 | Out of 28 papers using DisGeNET data |
| Negative overhead threshold | - | months | ~2 | - | 10 | After ~2 transitional months, incremental gains dominate |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Overhead for decontextualized snapshots | negative overhead | -1.5 to -3.0% | - | - | WikiPathways incremental | 10 |
| Overhead with cumulative nanopub snapshots | positive but decreasing | starts high, converges | - | - | WikiPathways | 10 |
| Typical subset size vs full dataset | percentage | mostly <5% | - | - | DisGeNET v4.0.0.0 | 11-12 |
| Subset retrieval time | seconds | ~30-40 | IQR shown | - | Typical subset (18098 nanopubs, 615332 triples) | 12 |
| Full dataset download time | seconds | ~60-80 | IQR shown | - | Full DisGeNET (48106698 triples, 1 file) | 12 |
| Papers using entire dataset | fraction | 8/20 (40%) | - | - | DisGeNET subset study | 11 |
| Papers using <5% of dataset | fraction | ~12/20 (60%) | - | - | DisGeNET subset study | 11-12 |

## Methods & Implementation Details
- **Nanopublication Operation Tool (npop):** Command-line tool implementing the approach. Key commands: *(p.7)*
  - `create`: create nanopublications from a file or stream
  - `filter`: extract/rewrite triples from nanopublication graphs by URIs or streams
  - `reuse`: take a dataset snapshot and its previous version, and generate an incremental update
  - `fingerprint`: calculate fingerprints for nanopublications following a specified configuration
  - `topic`: calculate topics according to a specified configuration
  - `decontextualize`: produce decontextualized triples for given nanopublication
- Built on existing nanopub-java library [12] *(p.7)*
- Distributed nanopublication server network with 16 server instances across 10 countries *(p.7)*
- Trusty URIs based on artifact code using SHA-256 hash *(p.3)*
- Evaluation code and data at: https://doi.org/10.6084/m9.figshare.5230639 and https://bitbucket.org/tkuhn/nanodiff-exp/ *(p.12)*

## Figures of Interest
- **Fig 1 (p.1):** Average triple counts of existing nanopublication datasets -- shows overhead from auxiliary triples
- **Fig 2 (p.4):** Schematic depiction of dataset specified with nanopublication indexes (top), observed content changes (middle), and their result as a new dataset version (bottom). Blue lines show a subset definition.
- **Fig 3 (p.10):** Overall size of the evolving WikiPathways version history -- shows cumulative nanopub snapshots vs decontextualized snapshots vs incremental approach
- **Fig 4 (p.12):** Histogram of subset sizes (in triples) relative to entire DisGeNET dataset -- most subsets are very small
- **Fig 5 (p.12):** Download times for full DisGeNET dataset vs typical subset (n=10, whiskers +/- 1.5 IQR)

## Results Summary
WikiPathways evaluation: After the first two transitional months, the incremental approach consistently outperforms traditional snapshots. The "negative overhead" of the decontextualized approach is -1.5 to -3.0%, meaning 98.5% more triples if storing only decontextualized snapshots. With cumulative nanopub snapshots, overhead converges toward the same level. *(p.10)*

DisGeNET evaluation: Of 20 papers studied, 60% used less than 5% of the dataset. The largest paper subset used only 23% of the data. Subset retrieval via the nanopub server network takes ~30-40 seconds for a typical subset vs ~60-80 seconds for the full dataset download. *(p.11-12)*

## Limitations
- The approach comes at a cost: the internal structure of each nanopublication has to be defined, and the provenance and metadata has to be separated even if it is virtually identical for a large number of them. *(p.1)*
- Fingerprints are not always sufficient for stable subset references -- topics provide a complementary mechanism for when content changes but identity should persist. *(p.6)*
- The evaluation datasets (WikiPathways, DisGeNET) are specific to life sciences; generalizability to other domains not tested. *(p.8)*
- Cryptographic guarantees on retrieved content do not depend on the system of individual servers (a feature, but also means no central authority). *(p.13)*

## Arguments Against Prior Work
- Current practice of dataset references is unreliable: researchers can only specify at the dataset level which data they use, and cannot reliably point to the exact subset that is relevant. *(p.1)*
- Existing nanopublication datasets have overhead ratios from 0.42x to 6.45x in auxiliary triples (Table 1) -- this has been a barrier to adoption. *(p.2)*
- Existing approaches to versioning Linked Data either track dataset-level changes or rely on named graphs, but do not provide cryptographic verifiability at the individual datum level. *(p.2-3)*
- RDF versioning systems, Git-based approaches for RDF, and delta-based approaches lack the granularity and cryptographic guarantees of the nanopublication approach. *(p.3)*

## Design Rationale
- **Granularity at the nanopublication level** rather than dataset level because individual scientific claims need individual provenance tracking and verification. *(p.0-1)*
- **Trusty URIs** (cryptographic hash-based) chosen over conventional URIs because they make content immutable and verifiable -- two important properties for scientific data. *(p.1)*
- **Incremental versioning** chosen over snapshot-based because it amortizes the overhead of auxiliary triples over the version history. *(p.5)*
- **Fingerprints and topics** as dual mechanisms: fingerprints for content-based identity (when you want to track the same content regardless of metadata changes), topics for semantic identity (when you want to track the same real-world entity even as its description changes). *(p.5-6)*
- **Decentralized server network** chosen over centralized repository to avoid single points of failure and to leverage the self-verifying nature of trusty URIs. *(p.7)*

## Testable Properties
- Incremental nanopub approach should produce fewer total triples than cumulative snapshot approach after sufficient version history (>2 versions). *(p.10)*
- Overhead ratio of nanopublication representation should decrease as dataset grows and version history lengthens. *(p.10)*
- Trusty URI verification: any retrieved nanopublication must pass SHA-256 hash verification against its trusty URI. *(p.3)*
- Index nanopublication set size must not exceed 1000 entries per index. *(p.4)*
- Typical researcher subsets should be a small fraction (<5% for majority) of the full dataset. *(p.11)*
- Subset retrieval time should be significantly less than full dataset download time. *(p.12)*

## Relevance to Project
This paper is directly relevant to propstore's content-hash-addressed storage and versioning design. The nanopublication model -- granular, provenance-aware, cryptographically verifiable data units with incremental versioning -- maps closely to propstore's claim-level storage with git-backed immutability. Key parallels:
- Trusty URIs (content-hash addressing) = propstore's content-hash-addressed sidecar
- Nanopublication indexes = propstore's semantic tree/index structure
- Incremental versioning = propstore's git-based branch isolation and merge semantics
- Fingerprints/topics for subset references = propstore's render policies and world queries
- The paper's non-commitment to a single dataset version aligns with propstore's formal non-commitment discipline

The fingerprint/topic distinction for subset identity is particularly interesting for propstore's concept of render policies -- different fingerprint configurations correspond to different ways of slicing the same underlying data.

## Open Questions
- [ ] Could propstore adopt trusty URI-style content hashing for individual claims (beyond the current sidecar-level hashing)?
- [ ] Does the fingerprint/topic distinction map to any existing propstore concept, or should it?
- [ ] How does the 1000-entry index limit compare to propstore's semantic tree fanout?

## Related Work Worth Reading
- Kuhn & Dumontier 2014 "Trusty URIs: Verifiable, Immutable, and Permanent Digital Artifacts for Linked Data" [13] -- foundational trusty URI paper -> NOW IN COLLECTION: [[Kuhn_2014_TrustyURIs]]
- Kuhn & Dumontier 2015 "Making digital artifacts on the web verifiable and reliable" [18] -- extended trusty URI work -> NOW IN COLLECTION: [[Kuhn_2015_DigitalArtifactsVerifiable]]
- Queralt-Rosinach et al. "Publishing DisGeNET as nanopublications" [25] -- application to DisGeNET
- Carroll et al. 2005 "Named graphs, provenance and trust" [5] -- named graphs for provenance
- Buneman et al. 2001 "Archiving scientific data" [4] -- scientific data archiving
- Wilkinson et al. 2016 "The FAIR guiding principles for scientific data management and stewardship" [32] -- FAIR principles context

## Collection Cross-References

### Already in Collection
- [[Groth_2010_AnatomyNanopublication]] — cited as [12]; defines the nanopublication model (assertion, provenance, publication info graphs) that this paper builds upon
- [[Kuhn_2014_TrustyURIs]] — cited as [18]; foundational trusty URI paper providing the cryptographic hash-based identifiers this paper extends to incremental versioning
- [[Kuhn_2015_DigitalArtifactsVerifiable]] — cited as [19]; extended journal version of the trusty URI work with formal definitions and large-scale evaluation
- [[Wilkinson_2016_FAIRGuidingPrinciplesScientific]] — cited as [32]; FAIR principles motivating the need for verifiable, persistent dataset references

### New Leads (Not Yet in Collection)
- Kuhn et al. (2016) "Decentralized provenance-aware publishing with nanopublications" — describes the decentralized server network used in the retrieval evaluation
- Queralt-Rosinach et al. (2016) "Publishing DisGeNET as nanopublications" — application to DisGeNET dataset evaluated here

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Kuhn_2014_TrustyURIs]] — already cross-references this paper as building incremental versioning on trusty URIs
- [[Kuhn_2015_DigitalArtifactsVerifiable]] — already cross-references this paper as extending trusty URIs to evolving datasets

### Conceptual Links (not citation-based)
- [[Juty_2020_UniquePersistentResolvableIdentifiers]] — both address persistent, resolvable identifiers for scientific data; Juty focuses on identifier infrastructure (identifiers.org), while this paper focuses on content-hash verification and incremental versioning. Complementary approaches to the same FAIR data goal.
