---
title: "Unique, Persistent, Resolvable: Identifiers as the Foundation of FAIR"
authors: "Nick Juty, Sarala M. Wimalaratne, Stian Soiland-Reyes, John Kunze, Carole A. Goble, Tim Clark"
year: 2020
venue: "Data Intelligence"
doi_url: "https://doi.org/10.1162/dint_a_00025"
pages: "30-39"
produced_by:
  agent: "claude-opus-4-6-1m"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:52:34Z"
---
# Unique, Persistent, Resolvable: Identifiers as the Foundation of FAIR

## One-Sentence Summary
Provides design principles and exemplar systems for persistent, globally unique, resolvable digital identifiers as the foundational infrastructure element enabling FAIR data practices in scientific research.

## Problem Addressed
The FAIR principles require that digital artifacts be Findable, Accessible, Interoperable, and Reusable, but identifiers are the foundational "F" element upon which all other FAIR principles depend. Without proper identifiers, data cannot be accessed, interpreted, or reused regardless of other infrastructure. *(p.1)*

## Key Contributions
- Defines the three essential properties of FAIR identifiers: uniqueness, persistence, and resolvability *(p.2)*
- Surveys four major identifier types (DOI, ARK, identifiers.org, PURL) with comparative analysis *(p.2-5)*
- Introduces a two-pattern framework for achieving identifier persistence: (1) registering with a redirecting service, or (2) using a unique namespace/pattern/resolver endpoint *(p.3)*
- Discusses identifier persistence as a social contract, not a purely technical property *(p.3)*
- Connects identifier infrastructure to the JDDCP data citation principles and FAIR metadata requirements *(p.6)*
- Argues for "active community" metadata standards beyond minimal provenance *(p.6)*

## Methodology
Conceptual/survey paper. Reviews identifier systems in the context of FAIR principles, analyzing exemplar persistent identifier services (DOI, ARK, identifiers.org, PURL) against criteria of uniqueness, persistence, resolvability, and metadata richness. No formal model or empirical study.

## Key Definitions

### FAIR Principles
The FAIR principles (Findable, Accessible, Interoperable, Reusable) are a model to guide the implementation of interoperable digital research artifacts. Digital artifacts must be preserved long term as the basis of modern scientific research. *(p.1)*

### Findability ("F" element)
This article focuses specifically on identifiers as required for practical implementation of the foundational "F" element of FAIR. All other FAIR principles (A, I, R) are built upon the F principle. *(p.1)*

### Identifier Requirements
To be "Findable", digital objects must be uniquely specific (they must have unique names), and must be locatable (by association of the unique name with a protocol for retrieval). They must also have at least some associated descriptive metadata to assist discovery and verification of the object when the identifier is not known a priori. *(p.2)*

### Digital Identifier
An identifier is a unique name given to an object, property, set or class. Digital identifiers are complex, ordered strings of characters uniquely capturing some digital resource. The underlying semantics of any identifier is that it means the resource to which it refers. *(p.2)*

### Persistence
Identifiers may be made "persistent" in that changes to the endpoint URIs can be made invisible and non-disruptive to users either individually (Pattern 1) or in bulk (Pattern 2) when the provider hosting structure changes. Pattern 1 allows reference to core metadata elements for individual identifiers. Pattern 2 allows re-registration to control redirection and pertinence behaviors. *(p.3)*

- **Pattern 1:** Register each identifier with a redirecting service (along with some metadata) and assign it a resolvable (e.g. DOI) *(p.3)*
- **Pattern 2:** Register a unique namespace, namespace prefix, identifier pattern, and resolver endpoint for the resource provider just once *(p.3)*

### Persistence as Social Contract
Identifier persistence is crucial for provenance, for instance if ownership of a service changes, or the server infrastructure changes (URL layout). In this sense it is a social commitment, a counter-measure to "Cool URIs don't change" [27]. *(p.3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| DOI registered unique identifiers | - | count | - | >16 million | p.3 | As of 2019, registered with DataCite |
| ARK registered organizations | - | count | - | >500 | p.4 | Registered organizations that have created ARKs |
| ARK total created identifiers | - | count | - | >3.2 billion | p.4 | Total ARKs created across all organizations |
| identifiers.org namespaces stored | - | count | - | 3,500 | p.5 | Rules for redirecting identifiers |
| identifiers.org operation period | - | years | - | >10 | p.5 | Providing URI-based identifiers to scientific community |
| Replication rate of scientific findings | - | % | - | 90-97 (claimed) | p.1 | Recent publications suggest 90-97% of scientific research data is lost within 20 years |
| FAIR EU/US funded projects | - | count | - | ~15 | p.1 | GO FAIR, FAIR4Health, FAIRplus, etc. |

## Methods & Implementation Details

### Table 1: Four FAIR Digital Identifier Types *(p.2)*

| Type | Example | Object Identified | Resolver Syntax |
|------|---------|-------------------|-----------------|
| DOI | `https://doi.org/10.1038/sdata.2016.18` | A digital object (publication) | `https://doi.org/PREFIX/SUFFIX` |
| ARK | `http://n2t.net/ark:/65665/3e2a36526-e6c3-1ae-bad4-07353dd49b6c` | A physical specimen | `http://n2t.net/ark:/NAAN/Name` |
| identifiers.org | `https://identifiers.org/uniprot:P0DP23` | Information on protein Calmodulin-3 | `https://[Resolver/]Provider]Namespace:Identifier` |
| PURL | `http://purl.org/dc/terms/publisher` | An abstracted term in DCTERMS vocabulary | `http://purl.org/path` |

### DOI System (4.1) *(p.3-4)*
- Digital Object Identifier (DOI) system (ISO 14:14) widely used in publishing to identify documents, and as dataset identifiers for data citation and interoperability
- Managed by International DOI Foundation (https://doi.org)
- Supported by various domain-centric Registration Agencies (RAs); most important RA for science is DataCite
- Membership gives an organization the right to mint a certain number of DOIs per year at various subscription levels
- Each DOI name is resolved at https://doi.org, with full URI following `https://doi.org/"DOI_name"`. DOI names are in turn consist of a prefix and a suffix, separated by a forward slash. The prefix is a code indicating the registrant who issues the DOI *(p.3)*
- Multi-step resolution process: client sends HTTP GET to doi.org resolver for the DOI of interest; doi.org sends redirect to the client with the address of the dataset "landing page" which holds the metadata *(p.4)*
- Metadata provided both in human and machine readable forms; machine readable metadata in DataCite XML and in schema.org vocabulary, serialized as JSON-LD *(p.4)*

### ARK System (4.1) *(p.4-5)*
- Archival Resource Keys supported by California Digital Library, in collaboration with DataSpace
- Work similarly to DOIs but more permissive in design; over 500 registered organizations have created over 3.2 billion ARKs
- Syntax: `https://NMA/ark:/NAAN/Name[Qualifier]` where NMA = Name Mapping Authority, NAAN = Name Assigning Authority Number (like a DOI Prefix), Name = local identifier, Qualifier = optional qualifier *(p.4)*
- Metadata is strongly recommended for publicly released ARKs, but is optional and flexible while the resource is being planned, reviewed, tested, etc. *(p.5)*
- ARK scheme is decentralized: any organization can run its own resolver
- Resolved through global Name-to-Thing resolver (http://n2t.net); N2T operates in two modes: stores records for millions of ARKs registered by the EZID service (https://ezid.cdlib.org/) and the Internet Archive; also collaborates with identifiers.org *(p.5)*

### identifiers.org System (4.2) *(p.5)*
- Provides globally resolvable HTTP URI-based identifiers to the scientific community for over a decade
- Core system: a resolver, a namespace, a namespace prefix, an identifier regex, and a local identifier resolver URI to provide globally unique persistent identifiers
- Records metadata only for the identifier namespace, not for individual identifiers; relies on the data provider to expose the appropriate metadata within the resolved webpages
- URI syntax: `https://[Resolver/][Provider/]Namespace:Identifier` where Resolver is resolution host (identifiers.org or n2t.net), Provider is an optional term indicating specific providers for a Namespace, Namespace is a registered prefix assigned to an identifier issuing authority, Identifier is the locally assigned identifier *(p.5)*
- Taken together, a namespace prefix and colon followed by a local identifier constitute a CURIE or Compact Identifier *(p.5)*
- Records all known resource-specific access URIs for a dataset or data record, including alternative access URIs. This allows alternative equivalent URIs to be consolidated as a single canonical URI string *(p.5)*

### PURL System (4.3) *(p.6)*
- Persistent Uniform Resource Locators (PURLs): generally any http URIs whose providers redirect GET requests to another location (a second URI with the added promise of long-term persistence)
- All identifier types discussed above miss this definition. However, in common usage, a PURL is an identifier minted and resolved at https://purl.org, being maintained since 2016 by the Internet Archive
- Authors do not recommend PURLs as general-purpose primary identifiers for persistently archived FAIR data *(p.6, footnote 1)*

## Figures of Interest
- **Table 1 (p.2):** Examples of FAIR digital identifiers — DOI, ARK, identifiers.org, PURL with example URIs and object types

## Limitations
- Focuses on identifier infrastructure for the "F" principle only; does not address A, I, R in depth *(p.1)*
- Does not provide a formal evaluation framework or metrics for comparing identifier systems *(p.2-6)*
- PURLs are not recommended for persistent FAIR data, but no formal analysis of failure modes is provided *(p.6)*
- The paper notes that 90-97% of scientific data is reportedly lost within 20 years, but acknowledges this may overstate the issue since "data that has not been robustly and accessibly archived, even when it is not actually 'lost'" *(p.1)*
- Persistence is described as a social commitment rather than a technical guarantee, leaving the problem of institutional failure unaddressed *(p.3)*

## Arguments Against Prior Work
- The paper criticizes the claim that 90-97% of scientific data is lost within 20 years as not accounting for data that is merely inaccessible rather than truly lost: "data attrition blocks the ability to validate results and reuse information in science" *(p.1)*
- Implicitly argues that PURLs (Pattern 1 only) are insufficient because they lack the namespace-level bulk management of Pattern 2 systems *(p.6)*

## Design Rationale
- Two-pattern approach to persistence chosen because Pattern 1 (individual registration) allows per-identifier metadata while Pattern 2 (namespace registration) allows bulk migration — different use cases require different approaches *(p.3)*
- DOI chosen as the canonical exemplar of Pattern 1 because of wide adoption and well-defined metadata requirements *(p.3)*
- identifiers.org chosen as the canonical exemplar of Pattern 2 because it supports namespace-level resolution without per-identifier registration *(p.5)*
- Authors recommend against PURLs for general identifier use because they lack structured metadata and namespace management *(p.6)*

## Testable Properties
- A valid FAIR identifier must be globally unique, persistent, and resolvable on the Web *(p.2)*
- A DOI must resolve via HTTP GET to a landing page containing descriptive metadata *(p.4)*
- An ARK must resolve via NMA to the named object, with optional qualifier for sub-objects *(p.4)*
- An identifiers.org CURIE must resolve to one or more resource-specific access URIs *(p.5)*
- Pattern 1 identifiers must be individually registered with redirecting services *(p.3)*
- Pattern 2 identifiers must use namespace-level registration with provider-specific resolver endpoints *(p.3)*

## Relevance to Project
This paper provides foundational context for propstore's identifier infrastructure. Propstore uses content-hash-addressed storage and DOI-based paper identification. The paper's framework of uniqueness, persistence, and resolvability maps onto propstore's needs for claim identifiers, concept identifiers, and paper references. The two-pattern persistence model (individual vs. namespace) is relevant to how propstore manages its own identifier schemes for claims and concepts. However, propstore is not primarily an identifier infrastructure project, so the relevance is contextual rather than directly implementable.

## Open Questions
- [ ] Does propstore's content-hash addressing satisfy the persistence requirement as defined here?
- [ ] Should propstore adopt CURIEs (identifiers.org style) for cross-referencing claims and concepts?
- [ ] How does the social contract of persistence map onto propstore's git-backed storage model?

## Collection Cross-References

### Already in Collection
- [[Clark_2014_Micropublications]] — Tim Clark is a co-author of both papers. Clark 2014 defines the micropublication semantic model for representing scientific claims with provenance, which requires the kind of persistent identifier infrastructure this paper describes.
- [[Wilkinson_2016_FAIRGuidingPrinciplesScientific]] — Cited as reference [1]; this is the original FAIR Guiding Principles paper that Juty et al. build upon, focusing specifically on the "F" (Findable) element and its identifier requirements.

### New Leads (Not Yet in Collection)
- McMurry et al. (2017) — "Identifiers for the 21st century: How to design, provision, and reuse persistent identifiers to maximize utility and impact of life science data" — practical design guide for persistent identifiers
- Wimalaratne et al. (2018) — "Uniform resolution of compact identifiers for biomedical data" — technical implementation of identifiers.org compact identifiers (CURIEs)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Groth_2010_AnatomyNanopublication]] — Both papers address how to make scientific artifacts persistently identifiable and citable. Nanopublications require globally unique, resolvable identifiers for their constituent assertions, which is exactly the infrastructure Juty et al. describe. The two-pattern persistence framework (individual registration vs. namespace-level) directly applies to nanopublication identifier schemes.

## Related Work Worth Reading
- Wilkinson et al. 2016 — The FAIR Guiding Principles for scientific data management and stewardship (the original FAIR paper) [1]
- Vines et al. 2014 — The Availability of Research Data Declines Rapidly with Article Age (data loss rates) [2]
- Joint Declaration of Data Citation Principles (JDDCP) — data citation standards [5]
- Kunze et al. — The ARK Identifier Scheme (2008) [12]
- Wimalaratne et al. 2018 — Uniform resolution of compact identifiers for biomedical data, Scientific Data [24]
