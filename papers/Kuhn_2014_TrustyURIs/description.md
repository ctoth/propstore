---
tags: [content-addressing, provenance, linked-data, semantic-web, cryptographic-hashing]
---
This paper proposes trusty URIs, a technique for embedding cryptographic hash values directly into URIs to make digital artifacts on the semantic web verifiable, immutable, and permanent. The approach works at the abstract RDF graph level rather than byte level, preserving hash validity across different serialization formats, and supports self-references and blank node handling through a modular architecture with implementations in Java, Perl, and Python. Relevant to propstore's content-hash addressed sidecar infrastructure and the broader goal of making knowledge artifacts self-verifying with full provenance chains.
