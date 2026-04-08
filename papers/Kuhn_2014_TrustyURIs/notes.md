---
title: "Trusty URIs: Verifiable, Immutable, and Permanent Digital Artifacts for Linked Data"
authors: "Tobias Kuhn, Michel Dumontier"
year: 2014
venue: "ESWC 2014 (European Semantic Web Conference), LNCS 8465"
doi_url: "https://doi.org/10.1007/978-3-319-11964-9_27"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:55:18Z"
---
# Trusty URIs: Verifiable, Immutable, and Permanent Digital Artifacts for Linked Data

## One-Sentence Summary
Proposes embedding cryptographic hash values in URIs to make digital artifacts on the semantic web verifiable, immutable, and permanent -- applicable to both files and RDF graphs, with format-independent hashing at the abstract RDF level.

## Problem Addressed
Digital resources on the web lack reliable mechanisms for verification, immutability, and permanence. URLs can change, content can be silently modified, and there is no built-in way to verify that a retrieved resource matches what was originally published. This is especially problematic for scientific data and nanopublications, where provenance and verifiability are critical. *(p.0)*

## Key Contributions
- A technique for including cryptographic hash values in URIs ("trusty URIs") that makes digital artifacts verifiable, immutable, and permanent *(p.0)*
- Verification works at the abstract RDF graph level, not just byte-level, so hash values are preserved across different serialization formats (Turtle, N-Triples, RDF/XML, TriX, TriG, N-Quads) *(p.0)*
- A modular architecture with artifact codes that support different content types (files vs. RDF content) *(p.4)*
- Self-referencing mechanism allowing URIs within an artifact to contain the hash of the artifact itself *(p.5)*
- Solution for blank nodes in RDF by converting them into trusty URIs *(p.5-6)*
- Reference implementations in Java, Perl, and Python *(p.7)*
- Evaluation on nanopublications and Bio2RDF datasets showing practical performance *(p.10-13)*

## Methodology
The approach embeds a cryptographic hash value as a suffix in a URI. The hash is computed over the content of the digital artifact -- either the raw bytes (for files) or a normalized representation (for RDF graphs). The key innovation is computing hashes at the abstract RDF graph level rather than at the byte level, which means the same trusty URI remains valid regardless of which RDF serialization format is used. *(p.0-1)*

### Core Design Requirements *(p.2)*
1. For meta-data digital artifacts, all self-references (i.e., their own URIs) should be allowed
2. Verification should be performed at a more abstract level than just bytes, with modules for different types of content; it should be possible to verify a digital artifact even if it is presented in a different format
3. It should not be necessary to access the artifact at its original location to verify it; everyone should be allowed to make verifiable URIs without a central authority
4. The approach should be based on current established standards and be compatible with existing tools and formats

### Three Properties of Trusty URIs *(p.2)*
1. **Verifiable**: A retrieved artifact can be checked against its trusty URI hash to confirm it hasn't been tampered with
2. **Immutable**: Once a trusty URI is established, its artifact code is fixed; any change creates a new URI, making the old one a "complete backwards compatibility link history"
3. **Permanent**: Even if the original hosting changes, the artifact can be verified by anyone who has a copy, and search engines/web archives can independently confirm identity

## Key Equations / Statistical Models

### Hash Computation Performance *(p.12-13)*
Hash computation time scales as:

$$
T = O(n \log n)
$$

Where: $T$ is computation time, $n$ is file size in bytes. This applies to the sorting step required for RDF normalization.
*(p.12)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Hash algorithm (module FA) | - | - | SHA-256 | - | 6 | For file artifacts |
| Hash algorithm (module RA) | - | - | SHA-256 | - | 6 | For RDF content |
| Artifact code length | - | characters | 45 | - | 4 | Module type (2) + version (1) + hash (42) |
| Hash encoding | - | - | Base64 | - | 4 | a-z, A-F, 0-9, - (modified Base64 notation) |
| Hash value length in URI | - | Base64 chars | 42 | - | 4 | 256 bits encoded in Base64 |
| Nanopublication dataset size | - | nanopubs | 10,000 | - | 10 | TriG format test set |
| Bio2RDF dataset size | - | files | 451 | - | 12 | N-Triples format, up to 177GB |
| Bio2RDF total triples | - | triples | >1 billion | - | 9 | 19 resources in second coordinated release |
| 2GB file transform time | - | minutes | ~5 | - | 13 | TransformRdf |
| 2GB file check time | - | minutes | ~2 | - | 13 | CheckFile |
| 177GB file transform time | - | hours | ~29 | - | 13 | Largest Bio2RDF file |
| 177GB file check time | - | hours | ~3 | - | 13 | Largest Bio2RDF file |

## Methods & Implementation Details

### Artifact Code Structure *(p.4)*
- Trusty URIs end with an **artifact code** in Base64 notation
- Format: 2 characters (module identifier) + 1 character (version) + 42 characters (hash value)
- Total: 45 characters appended to the end of the URI
- Characters used: `a-z`, `A-F`, `0-9`, `-` (representing numbers 0 to 63 in modified Base64)
- Example: `http://example.org/r1.RAMrMmSQx75d...` *(p.4)*

### Module System *(p.6)*
Two module types available:
- **Module FA** (File Artifacts): Computes SHA-256 hash of file bytes; module identifier chars are `FA`
- **Module RA** (RDF Content): Computes hash over normalized/sorted RDF content; module identifier chars are `RA`

Module RA works on RDF content and can cover entire named graphs. It supports self-references and handles blank nodes as described below. *(p.6)*

### Self-References *(p.5)*
- The artifact code is embedded in the URI, but the URI appears inside the artifact (circular dependency)
- Solved by using a **placeholder `#`** where the artifact code eventually appears
- During generation: define structure of new trusty URI by adding placeholder `#`
- During hash computation: replace all occurrences of the artifact code with blank space, then calculate hash
- The content is successfully verified if and only if the resulting hash matches the one from the trusty URI *(p.5)*
- For strong hashing algorithms, it is impossible to ensure that a calculated sequence of bytes was already part of the original content before the transformation, so replacing the placeholder is reversible *(p.5)*

### Blank Node Handling *(p.5-6)*
- Blank nodes are converted into trusty URIs by hashing
- Blank nodes can be seen as externally quantified variables; using the trusty URI with a blank node placeholder resolves identity
- The two dots `..` indicate these were derived from blank nodes but are now immutable URIs
- This approach solves the problem of blank nodes for normalization, is completely general, works on possible input graphs, fully supports RDF semantics, and does not require auxiliary triples *(p.6)*

### ni-URIs Compatibility *(p.6)*
- All trusty URIs can be transformed into ni-URIs with or without explicitly specifying an authority
- However, ni-URIs are limited: no self-references, no blank node handling, and the range of verifiability does not directly extend to referenced artifacts *(p.3)*

### Content Negotiation *(p.6)*
- For modules like RA that operate at the byte level, content negotiation can be used to retrieve the same content in different formats (depending on the requested content type in the HTTP request) when a trusty URI is accessed *(p.6)*

### Implementation Libraries *(p.7)*
- **Java**: `trustyuri-java` -- most complete implementation
- **Perl**: `trustyuri-perl` -- uses Apache Jena for RDF processing
- **Python**: `trustyuri-python` -- uses RDFLib package
- All three provide: RunBatch, CheckFile, ProcessFile (general); CheckFile, CheckLargeRdf, CheckSortedRdf, TransformRdf, TransformLargeRdf, TransformNanopub, CheckNanopubViaSparql (RDF module) *(p.7-8)*

### Evaluation Setup *(p.10)*
- Test collection: 10,000 nanopublications in TriG format from previous work
- Transformed into trusty URI nanopublications using TransformNanopub
- Corrupted files created by: (a) changing a random single byte, or (b) replacing an upper-case letter, yielding only (mostly) valid characters *(p.10)*
- Tested with CheckFile of all implementations supporting the respective format *(p.10)*

## Figures of Interest
- **Fig 1 (p.2):** Schematic illustration of the range of verifiability -- trusty URI on top with green arrows showing verifiable reference tree reaching all artifacts via trusty URI links
- **Fig 2 (p.9):** Screenshot of nanobrowser interface showing green jigsaw puzzle icon for successful verification, and download format options (trig, xml, nq)
- **Fig 3 (p.13):** Log-log plot of time required for transforming (top) and checking (bottom) Bio2RDF files versus file size, showing O(n log n) scaling with dotted line for available memory boundary

## Results Summary

### Nanopublication Performance *(p.10-11)*
- **Normal mode (individual file checks)**:
  - Valid files: 100% correctly identified as valid across all implementations and formats
  - Corrupted files: Detection rates vary -- some formats detect 100% invalid, others detect ~84% invalid with ~15% error (due to subtle single-byte corruption) *(p.11)*
  - Java N-Quads: mean 0.5229s per file; Python N-Quads: 0.1935s; Perl N-Quads: 0.7843s *(p.11)*
- **Batch mode**: 
  - Dramatically faster -- Java N-Quads: mean 0.0019s per file; Python N-Quads: 0.0070s *(p.11)*
  - Same detection rates as normal mode *(p.11)*

### Bio2RDF Performance *(p.12-13)*
- 451 N-Triples format files tested
- Some outlier files had errors due to extra information in the RDF file not part of the RDF content (extra-information in TriG format) *(p.10)*
- Performance scales O(n log n) with file size *(p.12)*
- CheckSortedRdf is fastest for large files; TransformLargeRdf superior only for very large files *(p.13)*
- 2GB file: ~5 min to transform, ~2 min to check *(p.13)*
- 177GB file (largest): 29 hours to transform, ~3 hours to check *(p.13)*
- Files larger than available memory take more time but still complete *(p.13)*

### Corrupted File Detection *(p.10-11)*
- The RDF implementation in Java and Python (for the respective system utilities to handle XML) does not properly check that two elements have the same trusty URI
- Both TriG/XML files that erroneously validated were < 1.2KB (file 0.637) when running Java, and 141 TriG file (0.0872) when running Python *(p.10)*
- Due to minor bugs in the used RDF libraries; the extra information is not sufficiently checked *(p.10)*

## Limitations
- Hash computation for RDF requires sorting, which is O(n log n) -- not O(n) like simple file hashing *(p.12)*
- Very large files (>available memory) significantly increase processing time *(p.13)*
- Some RDF library implementations have bugs that cause false validation of corrupted files in edge cases (TriX in Java, TriG in Python) *(p.10)*
- The approach does not currently address the "ontology evolution" problem -- if the meaning of terms changes, the hash only guarantees syntactic identity, not semantic stability *(implied)*
- Requires all participants to adopt trusty URIs for full benefit -- partial adoption still leaves non-trusty URI links as weak points in the verification chain *(p.2, Fig 1)*
- Blank node handling adds overhead and complexity *(p.5-6)*

## Arguments Against Prior Work
- **ni-URIs (RFC 6920)**: Limited because they do not support self-references, cannot handle blank nodes, and their range of verifiability does not directly extend to referenced artifacts *(p.3)*
- **Git/version control hashes**: Git uses content-addressing but hash sequences are implementation-specific and not URI-compatible; git does not operate at the abstract RDF level *(p.3)*
- **Named Information URIs**: While compatible (trusty URIs can be transformed to ni-URIs), ni-URIs are server-bound and require custom-made software for resolution *(p.3)*
- **Standards for quantitative datasets and XML documents**: Exist but are "not general enough to cover RDF content (at least not in a convenient way) and keep the hash value separate from the URI reference, which means that the range of verifiability does not directly extend to referenced artifacts" *(p.3)*

## Design Rationale
- **Why hash in the URI itself**: Embedding the hash directly in the URI means any existing URI-based infrastructure (links, caches, search engines) automatically preserves the verification capability without requiring side-channel metadata *(p.1-2)*
- **Why abstract-level (RDF graph) hashing instead of byte-level**: Byte-level hashing breaks when the same RDF graph is serialized in different formats; abstract-level hashing preserves verification across Turtle, N-Triples, RDF/XML, TriX, TriG, N-Quads *(p.0, p.4)*
- **Why Base64 not hex**: More compact encoding allows fitting the full 256-bit hash in 42 characters instead of 64 *(p.4)*
- **Why modular architecture**: Different content types need different normalization strategies; the module system allows extending to new content types while keeping the URI structure consistent *(p.6)*
- **Why self-references**: Nanopublications and other semantic web artifacts naturally need to reference themselves (for provenance, metadata about the artifact itself); forbidding self-references would cripple the approach for its primary use case *(p.5)*

## Testable Properties
- A valid trusty URI artifact must hash to the same value regardless of RDF serialization format (Turtle, N-Triples, RDF/XML, TriX, TriG, N-Quads) *(p.0, p.4)*
- Any single-byte modification to a valid trusty URI artifact must produce a different hash (with overwhelming probability) *(p.10)*
- Artifact codes must be exactly 45 characters: 2 (module) + 1 (version) + 42 (hash) *(p.4)*
- CheckFile on a valid trusty URI file must return true; on any corrupted version must return false (modulo library bugs) *(p.10)*
- TransformRdf followed by CheckFile on the output must always succeed *(p.10)*
- For batch mode, per-file checking time should be orders of magnitude less than normal mode (amortized overhead) *(p.11)*
- Hash computation time must scale as O(n log n) for RDF content due to sorting requirement *(p.12)*
- Self-referencing: replacing artifact code with blank space and recomputing hash must yield the original artifact code *(p.5)*

## Relevance to Project
This paper is directly relevant to propstore's content-addressed sidecar and provenance infrastructure. Trusty URIs provide a formal mechanism for making claims, nanopublications, and knowledge artifacts verifiable and immutable -- exactly the properties needed for a non-commitment-discipline repository. The hash-in-URI approach could strengthen propstore's content-hash addressing by extending verification to the entire reference tree, not just individual artifacts. The RDF-level hashing is particularly relevant if propstore ever exposes its knowledge as linked data.

## Open Questions
- [ ] Could trusty URIs be used for propstore claim identifiers to make them self-verifying?
- [ ] How does this relate to propstore's existing content-hash addressed sidecar?
- [ ] Could the self-reference mechanism be applied to propstore's branch/merge provenance?

## Related Work Worth Reading
- [13] Kuhn et al. "Broadening the Scope of Nanopublications" -- nanobrowser application using trusty URIs
- [12] Kuhn. "A Survey and Classification of Controlled Natural Languages" -- CNL for nanopublications
- [4] Callahan, Cruz Lebre, Dumontier. "Bio2RDF release 2" -- major application of trusty URIs to life sciences
- [1] M. Altman and G. King. "A Proposed Standard for the Scholarly Citation of Quantitative Data" -- related provenance work
- [8] P. Farrell et al. "Signing HTTP messages" -- complementary approach using signatures rather than hashes
- [16] C.W. Pua and D. Wagner. "Security considerations for incremental hash functions" -- relevant to the hash algorithm choice

## Collection Cross-References

### Already in Collection
- [[Groth_2010_AnatomyNanopublication]] -- cited implicitly; nanopublications are the primary use case motivating trusty URIs. Groth defines the nanopub model, Kuhn 2014 provides the verification/immutability layer on top.

### Now in Collection (previously listed as leads)
- (none -- this is the first reconciliation)

### New Leads (Not Yet in Collection)
- Carroll (2003) -- "Signing RDF Graphs" -- earlier work on RDF graph signing, relevant background for the design space of content verification
- Callahan et al. (2013) -- "Bio2RDF release 2" -- major application dataset with >1 billion triples

### Supersedes or Recontextualizes
- [[Kuhn_2015_DigitalArtifactsVerifiable]] -- the 2015 paper is an expanded journal version of this 2014 conference paper, with larger evaluation (154,256 nanopublications vs 10,000) and formal definitions (Defs 1-4). The 2015 version supersedes this one for formal reference, but this 2014 paper is the original venue publication.

### Cited By (in Collection)
- [[Kuhn_2015_DigitalArtifactsVerifiable]] -- extended version of this paper
- [[Kuhn_2017_ReliableGranularReferences]] -- cites this as the foundational trusty URI paper; builds incremental versioning and granular references on top of trusty URIs

### Conceptual Links (not citation-based)
- [[Juty_2020_UniquePersistentResolvableIdentifiers]] -- surveys persistent identifier systems (DOI, ARK, PURL); trusty URIs solve the verification problem that Juty's surveyed systems leave open (they guarantee resolution but not content integrity)
- [[Groth_2010_AnatomyNanopublication]] -- defines the nanopublication data model that trusty URIs make verifiable; complementary layers of the same architecture
