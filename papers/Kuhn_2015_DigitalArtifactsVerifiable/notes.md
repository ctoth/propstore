---
title: "Making Digital Artifacts on the Web Verifiable and Reliable"
authors: "Tobias Kuhn, Michel Dumontier"
year: 2015
venue: "IEEE Transactions on Knowledge and Data Engineering"
doi_url: "https://doi.org/10.1109/TKDE.2014.2380053"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:56:06Z"
---
# Making Digital Artifacts on the Web Verifiable and Reliable

## One-Sentence Summary
Proposes "trusty URIs" — URIs that embed cryptographic hash values — as a decentralized, format-independent mechanism to verify the integrity and immutability of digital artifacts (datasets, code, texts, images, RDF graphs) on the Web.

## Problem Addressed
The current Web has no general mechanism to make digital artifacts — datasets, code, texts, images — verifiable and permanent. *(p.1)* Digital artifacts are supposed to be immutable but there is no convention or authority to enforce this. *(p.1)* Existing cryptographic approaches (PGP signatures, checksums) are applied externally and not integrated into the identifier itself, creating a disconnect between referencing and verifying artifacts. *(p.2)* Hash-based approaches like content-addressable storage and Git exist but are domain-specific and don't generalize to arbitrary Web resources. *(p.2)*

## Key Contributions
- A URI scheme ("trusty URIs") that embeds a cryptographic hash of the artifact content directly in the URI, making verification intrinsic to referencing *(p.1)*
- Two concrete module types: module FA for byte-level file content, and module RA for RDF graphs (nanopublications) *(p.3-5)*
- A specification that is backwards-compatible with existing Web infrastructure, open, and decentralized *(p.1-2)*
- Implementation in Java, Perl, and Python with performance evaluation *(p.7)*
- Evaluation on nanopublication datasets showing scalability to millions of artifacts *(p.8-10)*

## Methodology
The authors define a URI structure that contains a hash of the referenced content. The URI itself serves as both an identifier and a verification token. Two module types handle different content types: module FA for arbitrary files (byte-level hashing) and module RA for RDF content (graph-level hashing with canonicalization). The approach is evaluated through implementations in three programming languages and tested on real-world nanopublication datasets. *(p.1, 3-9)*

## Key Definitions

**Definition 1 (Base64url characters):** Every character that is a standard ASCII letter (A-Z or a-z), a digit (0-9), a hyphen (-), or an underscore (_) is called a Base64url character, representing in this order the numbers from 0 to 63. There are no other Base64url characters. *(p.5)*

**Definition 2 (Trusty URI):** Every trusty URI ends with at least 25 Base64url characters. The sequence of characters following the last non-Base64url character is called the artifact code. The first two characters of the artifact code are called the module identifier. The sequence of characters following the module identifier is called data part, which is identical to or contains a hash part. The current modules only generate URIs with exactly 45 trailing Base64url characters, but the definition is kept general for future modules. *(p.5)*

**Definition 3 (Potential trusty URI):** Every URI that could be a trusty URI according to the restrictions of Definition 2 with a module identifier matching a defined module and with a data part that is consistent with the structural restrictions of the given module (in particular with respect to its length) is called a potential trusty URI. *(p.5)*

**Definition 4 (Verified trusty URI):** Given a potential trusty URI and a digital artifact, if the identifier part refers to an artifact that returns a hash value for the digital artifact that is identical to the one encoded in the hash part, then the potential trusty URI is a verified trusty URI and the digital artifact is its verified content. *(p.5)*

## Module Types

### Module FA (File Artifact)
- Version A of module type F (module identifier `FA`) *(p.3)*
- Calculates hash by reading entire file content using SHA-256 on the content of the file in its byte representation *(p.3)*
- The file and other sub-modules are not considered; only byte-level content matters *(p.3)*
- Two zero-bits are appended to the resulting hash value, then transformed to Base64url notation *(p.3)*
- The resulting 43 characters make up the data part of the trusty URI *(p.3)*
- File extension like `.txt` or `.ttl` to trusty URIs is supported, with the restriction that extensions use only Base64url characters plus dot (.), slash (/), and hash sign (#) *(p.3)*

### Module RA (RDF Artifact)
- Version A of module type R (module identifier `RA`) *(p.5-6)*
- Works on RDF content: handles multiple graphs *(p.5)*
- Supports nanopublication structure (head, assertion, provenance, pubinfo graphs) *(p.5-6)*
- The module R format supports multiple graphs whereas module F handles only a single file *(p.4)*
- Hash blank nodes are not supported and have to be deleted in the same way when a trusty URI is produced *(p.6)*
- To check whether a given artifact code correctly represents a given set of named graphs, the triples and graphs have to be sorted; the trusty URI in the RDF data must appear in the RDF data if it represents a self-reference, with all occurrences of the given artifact code in the URIs replaced by a placeholder *(p.6)*
- Sorting algorithm for triples with 9 precedence rules for comparison *(p.6-7)*:
  1. If their predicate URIs differ, the triple with the lexicographically smaller preprocessed predicate URI is first *(p.6)*
  2. If one has a literal as object and the other has a non-literal, the triple with the non-literal as object is first *(p.7)*
  3. If both have a URI as object, the triple with the lexicographically smaller preprocessed object URI is first *(p.7)*
  4. If the literal labels of the objects differ, the triple with the lexicographically smaller literal label is first *(p.7)*
  5. If one of the object literals has a datatype identifier and the other does not, the triple without a datatype identifier is first *(p.7)*
  6. If one of the object literals has a language identifier and the other does not, the triple without a language identifier is first *(p.7)*
  7. The triple with the lexicographically smaller datatype or language identifier is first *(p.7)*
  8. If two strings have different characters at at least one position, the string with the smaller integer value at the first differing position is first *(p.7)*
  9. Otherwise the shorter string is first *(p.7)*
- Uses Unicode character ordering defined as strings of Unicode characters; if two strings have different characters at at least one position, the string with the smaller integer value at the first differing position is first. Otherwise the shorter string is first *(p.7)*

## Self-References in Trusty URIs
- A nanopublication that contains its own trusty URI inside its content creates a self-reference problem *(p.3)*
- Solution: use a placeholder for the hash part during generation. The generation process involves: (1) not yet computing the hash from a given artifact, but (2) actually transforming the artifact into a new version that contains the newly generated trusty URI *(p.3)*
- A resource like `http://example.org/r1` might have the following RDF triple with a placeholder:
  `http://example.org/r1 ...` becomes `http://example.org/RA...hash...` *(p.3)*
- To transform such a resource: first define the structure of the new URI by adding a placeholder where the artifact code should eventually appear, then replace placeholder by the calculated artifact code *(p.3)*

## Trusty URI Properties
- **Verifiable:** Contain a hash that can be checked against content *(p.1-2)*
- **Immutable:** Content cannot be changed without invalidating the URI *(p.2)*
- **Decentralized:** No central authority needed — anyone can create and verify *(p.2)*
- **Format-independent:** Works for datasets, code, texts, images *(p.1)*
- **Backwards-compatible:** Work with existing Web infrastructure *(p.2)*
- **Open:** No proprietary technology required *(p.2)*
- Certain module can be defined in a way that makes artifacts and their URIs transferable to another module, where the module identifier can be switched to the second module without changing the hash or breaking the verification of the artifact *(p.4)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Hash algorithm | — | — | SHA-256 | — | 3 | Used for both FA and RA modules |
| Artifact code length | — | Base64url chars | 45 | ≥25 | 5 | 2 char module ID + 43 char data part |
| Module identifier length | — | chars | 2 | 2 | 5 | First char = type, second char = version |
| Base64url encoding | — | — | — | 0-63 | 5 | A-Z, a-z, 0-9, hyphen, underscore |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Nanopublication checking (Java, normal, N-Quads) | Time | 0.0328s | — | — | 154256 files, 8.58GB | 9 |
| Nanopublication checking (Java, batch, N-Quads) | Time | 0.0018s | — | — | 154256 files, 8.58GB | 9 |
| Valid ratio (Java, normal) | Fraction | 100% | — | — | All formats | 9 |
| Bio2RDF dataset | Size | ~1 billion triples | — | — | 19 resources | 9 |
| Bio2RDF checking (Java, batch, TriG) | Time | 0.0069s per file | — | — | 858 files, 3.1GB-47.2GB range | 10 |
| Corrupted file detection (normal mode) | Rate | 100% | — | — | All implementations | 9 |
| Corrupted file detection (batch mode) | Rate | 0.83%-15.6% miss | — | — | Java batch TriG | 9 |
| File processing throughput | Speed | ~1s avg per file | — | — | Normal mode, 16-core Xeon server | 9 |

## Methods & Implementation Details
- Three implementations: Java (uses Sesame library [21] for RDF), Perl (Trine package), and Python (RDFLib) *(p.7)*
- Available functions across implementations: *(p.7)*
  - **CheckFile**: takes a file and calculates its hash by applying the respective module
  - **ProcessFile**: takes a file, calculates its hash using module FA, and renames it to make it a trusty file
  - **TransformRdf**: takes an RDF file and a base URI, and transforms the file into a trusty file using a module of type R
  - **TransformLargeRdf**: same as above but using temporary files instead of loading entire content into memory
  - **CheckLargeRdf**: checks an RDF file using module RA without loading the whole content into memory but using temporary files instead
  - **CheckSortedRdf**: checks an RDF file assuming that it is already sorted (and raises an error otherwise). Current implementations generate such sorted files by default, but this is not required by the specification
  - **RunBatch**: reads commands (any of the above) from a file and executes them one after the other *(p.7)*
- Nanopublication validator interface integrates trusty URI features: users can generate trusty URIs for nanopublications, and nanopublications with trusty URIs are automatically verified *(p.7)*
- Evaluation on Linux server (Debian) with 16 Intel Xeon CPUs at 2.27GHz and 24GB of memory *(p.8)*

## Figures of Interest
- **Fig 1 (p.2):** Schematic illustration of the range of verifiability for the trusty URI (top left). Green arrows show the range of verifiability that covers all artifacts that can be reached by following trusty URI links (green arrows).
- **Fig 2 (p.6):** Schematic representation of the general structure of trusty URIs showing URI prefix, module identifier, hash part, extension, artifact code, data part, and full trusty URI structure.
- **Fig 3 (p.8):** The nanopublication validator interface — shows screenshots of validation results for valid, invalid, and publishable nanopublications.
- **Fig 4 (p.10):** Time required for transforming (top) and checking (bottom) files versus file size for the Bio2RDF dataset. Log-log scale showing linear relationship between file size and processing time.

## Results Summary
- Hash Generation and Checking on Nanopublications: first test collection of 154,256 nanopublications in TriG format; three implementations successfully transformed these into trusty URI nanopublications using the Java implementation, then checked them with all three implementations *(p.8)*
- Corrupted files were reliably detected in normal mode (100% across all implementations) *(p.9)*
- In batch mode, some corrupted files could be missed: the changed TriG value was not part of the RDF content but of the meta-information; the meta-information is not sufficiently checked, leading to acceptable false negatives *(p.9)*
- Bio2RDF dataset testing: over 1 billion triples for 19 resources made available as nanopublications using Bio2RDF [25]; these contained 524 RDF files in N-Triples format, converted to TriG; the largest file of the dataset (47.7GB) was successfully processed in 29 hours and checked in about 3 hours *(p.9-10)*
- Performance: batch mode ~5x faster than normal mode; Java implementation fastest overall; checking is reasonably fast even in normal mode with average values below 0.6s per file *(p.9)*
- Table 1 (p.9) shows comprehensive performance results across Java, Perl, Python implementations in normal and batch modes for all file operations *(p.9)*

## Limitations
- If hash algorithms should become vulnerable to attacks in the future, new modules might also become necessary *(p.4)*
- Batch mode checking has a theoretical limit due to computational complexity of O(n log n) — TransformLargeRdf and CheckLargeRdf are superior to their counterparts only for very large files *(p.9)*
- Java library accepts invalid XML version numbers such as 1.1 (TriG files) and doesn't check Base64url character restrictions on argument names *(p.8)*
- The approach creates a tension with content negotiation: the same content negotiation can be used to return the same content in different formats depending on the request, but changing format would change the hash *(p.4)*
- Blank nodes in RDF are not supported and have to be deleted when a trusty URI is produced *(p.6)*
- Self-referencing creates additional complexity and requires a two-step transformation process *(p.3)*

## Arguments Against Prior Work
- Existing approaches (PGP, checksums) decouple the verification from the identifier, meaning one can encounter a modified artifact without knowing its hash or where to find the original hash *(p.2)*
- Content-addressable storage (like Git) uses hashes internally but doesn't expose them as Web-compatible URIs *(p.2)*
- Named Information (ni:) URIs [16] assign names to digital artifacts, but their hash values exist in a separate name space from HTTP URIs, making them unusable as linked data identifiers *(p.2)*
- DOI and other persistent identifiers delegate to a central resolver and don't embed content verification *(p.2)*
- Previous proposals for signed RDF graphs use domain-specific approaches that don't generalize to arbitrary digital artifacts *(p.2)*

## Design Rationale
- Hash is embedded directly in the URI rather than stored separately to ensure verification is always possible whenever the URI is encountered *(p.1-2)*
- SHA-256 chosen as the hash algorithm — well-established and considered secure at time of writing *(p.3)*
- Base64url encoding chosen because it uses only URI-safe characters (no percent-encoding needed) *(p.5)*
- Module system designed for extensibility: new content types can be handled by defining new modules without breaking existing ones *(p.3-4)*
- Self-reference handling uses placeholder substitution rather than excluding self-references, preserving the ability for artifacts to reference themselves (critical for nanopublications) *(p.3)*
- Sorting algorithm for RDF triples uses lexicographic ordering to ensure deterministic serialization independent of the original triple order *(p.6-7)*

## Testable Properties
- Any trusty URI with module FA can be verified by computing SHA-256 of the file content and comparing to the hash in the URI *(p.3)*
- Trusty URIs must end with at least 25 Base64url characters *(p.5)*
- The artifact code is exactly 45 Base64url characters for current modules (2 module ID + 43 data) *(p.5)*
- Hash verification must be format-independent: same content → same hash regardless of how it's stored *(p.1)*
- Self-referencing trusty URIs: replacing the artifact code with a placeholder and recomputing the hash must yield the same artifact code *(p.3)*
- Sorting algorithm for RDF triples must be deterministic: same set of triples → same sorted order → same hash *(p.6-7)*
- Corrupted content must be detected with 100% accuracy in normal (non-batch) mode *(p.9)*
- Processing time scales linearly with file size (shown in Fig 4) *(p.10)*

## Relevance to Project
This paper is relevant to propstore's content-addressed storage and provenance tracking. The trusty URI concept directly parallels propstore's use of content-hash addressing for the sidecar, where artifacts are rebuilt only when source changes. The cryptographic verification approach could strengthen propstore's immutability guarantees for claims and knowledge artifacts. The module system (FA for files, RA for RDF) demonstrates how to handle different content types within a unified verification framework, which maps to propstore's need to verify different artifact types (claims, concepts, stances). The nanopublication ecosystem described here is a concrete deployment of the kind of decentralized, verifiable knowledge infrastructure that propstore's argumentation layer aims to support.

## Open Questions
- [ ] Could trusty URI concepts be applied to propstore's claim/stance storage for stronger integrity guarantees?
- [ ] How does the nanopublication ecosystem's approach to provenance compare with propstore's ATMS-based provenance tracking?
- [ ] Would adopting content-hash URIs improve propstore's ability to detect and handle conflicting knowledge updates?

## Related Work Worth Reading
- [16] K. Hoelscher, "The Metalab documents" — ni: URI scheme for Named Information (RFC 6920) *(p.2)*
- [25] Bio2RDF: mapping and linking life science databases to create a knowledge network *(p.9)*
- [21] Sesame library for parsing and storing RDF and SPARQL *(p.7)*
- Nanopublications generally — the ecosystem built around trusty URIs for scientific claims
- [12] The underlying concept of nanopublications *(p.2)*
- [17] Allman and King, "A proposed standard for the citation of quantitative data" *(p.10)*

## Collection Cross-References

### Already in Collection
- [[Kuhn_2014_TrustyURIs]] — this 2015 paper is the extended journal version of that 2014 conference paper. Adds formal definitions (Defs 1-4), larger evaluation (154,256 nanopublications vs 10,000), and Bio2RDF testing with >1 billion triples.
- [[Groth_2010_AnatomyNanopublication]] — cited as [12]; defines the nanopublication data model that trusty URIs are primarily designed to verify.

### New Leads (Not Yet in Collection)
- Carroll (2003) — "Signing RDF Graphs" — prior work on cryptographic verification of RDF; trusty URIs generalize beyond this RDF-only approach.
- RFC 6920 — Named Information (ni:) URI scheme — closest prior art; embeds hashes in URIs but in a separate namespace from HTTP.

### Supersedes or Recontextualizes
- [[Kuhn_2014_TrustyURIs]] — this 2015 IEEE TKDE paper is the extended journal version of the 2014 ESWC conference paper. It supersedes the 2014 version for formal reference with additional formal definitions, expanded evaluation, and more thorough specification of module types.

### Cited By (in Collection)
- [[Kuhn_2017_ReliableGranularReferences]] — builds incremental versioning and granular subset references on top of trusty URIs; cites this as [18].

### Conceptual Links (not citation-based)
- [[Kuhn_2014_TrustyURIs]] — same authors, same core contribution; the 2014 paper is the original venue, this is the extended version.
- [[Kuhn_2017_ReliableGranularReferences]] — extends trusty URIs to handle evolving datasets with incremental versioning; demonstrates the trusty URI ecosystem at scale with WikiPathways and DisGeNET.
- [[Groth_2010_AnatomyNanopublication]] — complementary layers: Groth defines the nanopublication data model, Kuhn 2015 provides the cryptographic verification layer on top.
