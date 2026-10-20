---
tags: [merkle-trees, transparency-logs, tamper-evidence, provenance]
---
RFC 6962 specifies Certificate Transparency, an experimental protocol for append-only, publicly auditable logs of TLS certificates built on a binary SHA-256 Merkle tree with signed certificate timestamps and signed tree heads. It gives exact recursive definitions of the Merkle Tree Hash, inclusion audit paths, and minimal consistency proofs (at most ceil(log2 n)+1 nodes), an HTTPS/JSON log API, and monitor/auditor procedures that make log equivocation or failure to merge within the Maximum Merge Delay publicly detectable. It is the reference design for verifiable append-only histories, relevant to propstore's git-backed provenance, federation between peers, and detecting divergent views of a shared log.
