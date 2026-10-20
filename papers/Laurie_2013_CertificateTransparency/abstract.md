# Abstract

## Original Text (Verbatim)

This document describes an experimental protocol for publicly logging the existence of Transport Layer Security (TLS) certificates as they are issued or observed, in a manner that allows anyone to audit certificate authority (CA) activity and notice the issuance of suspect certificates as well as to audit the certificate logs themselves. The intent is that eventually clients would refuse to honor certificates that do not appear in a log, effectively forcing CAs to add all issued certificates to the logs.

Logs are network services that implement the protocol operations for submissions and queries that are defined in this document.

---

## Our Interpretation

CT addresses invisible CA misissuance by making every certificate's existence publicly logged in an untrusted but verifiable append-only Merkle tree, so that subjects and third parties can detect misissue and the logs' own misbehaviour. Its key technical content is the precise Merkle tree hash, audit path, and consistency proof definitions plus the signed-timestamp/tree-head protocol. For propstore it is a template for verifiable append-only provenance histories exchanged between parties that do not trust one another.
