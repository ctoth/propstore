# Abstract

## Original Text (Verbatim)

To make digital resources on the web verifiable, immutable, and permanent, we propose a technique to include cryptographic hash values in URIs. We call them trusty URIs and we show how they can be used by approaches like nanopublications to make not only specific resources but their entire reference trees verifiable. Digital artifacts can be identified not only on the byte level but also on more abstract levels such as RDF graphs, which means that resources keep their hash values even when presented in a different format. Our approach sticks to the core principles of the web, namely openness and decentralized architecture, is fully compatible with existing standards and protocols, and our therefore shows that these desired properties are indeed accomplishable by our approach, and that it remains practical even for very large files.

---

## Our Interpretation

The paper addresses the fundamental problem that web URIs provide no guarantee that the resource they point to hasn't changed since publication. By embedding cryptographic hashes directly into URIs, the authors create self-verifying identifiers that work at the abstract RDF graph level (not just bytes), meaning the same trusty URI validates across different serialization formats. This is relevant to propstore's content-addressed storage model and could inform how claim and artifact identifiers are constructed to be self-verifying across the entire reference tree.
