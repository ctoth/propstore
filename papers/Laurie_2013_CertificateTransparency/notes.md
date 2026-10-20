---
title: "Certificate Transparency"
authors: "Ben Laurie, Adam Langley, Emilia Kasper"
year: 2013
venue: "IETF RFC 6962 (Experimental), ISSN 2070-1721"
doi_url: "https://doi.org/10.17487/RFC6962"
pages: "27"
affiliations: "Google UK Ltd.; Google Inc.; Google Switzerland GmbH"
note: "PDF is a Chrome print of https://www.rfc-editor.org/rfc/rfc6962.html (24 PDF pages). Page citations (p.N) below use the RFC's own printed [Page N] footers, not PDF page indices."
---

# Certificate Transparency

## One-Sentence Summary
Specifies an append-only, publicly auditable log of TLS certificates built on a binary Merkle hash tree with exact recursive definitions of the tree hash (MTH), inclusion (audit) paths, and consistency proofs, plus signed timestamps (SCTs), signed tree heads (STHs), an HTTPS/JSON client API, and monitor/auditor procedures for detecting log misbehaviour. *(p.1, pp.4-7, pp.9-23)*

## Problem Addressed
Misissued certificates: CAs can issue certificates that the named subject did not request, and nothing makes that issuance visible. CT does not prevent misissue; it makes issuance publicly visible so interested parties (especially those named in certificates) can detect it, and it lets anyone audit the logs themselves rather than trusting them. *(p.1, p.3)* The longer-term intent is that clients refuse certificates that do not appear in a log, effectively forcing CAs to log every issued certificate. *(p.1)*

## Key Contributions
- A precise Merkle Tree Hash over an ordered list of arbitrary (non-power-of-two) length with leaf/node domain separation. *(pp.4-5)*
- Recursive definitions of the Merkle audit path PATH(m, D[n]) and the minimal Merkle consistency proof PROOF(m, D[n]) via SUBPROOF. *(pp.5-7)*
- Log entry formats (X.509 chains and Precertificate chains), the Signed Certificate Timestamp (SCT) as a promise to include within the Maximum Merge Delay (MMD), and the Signed Tree Head (STH). *(pp.9-16)*
- Three delivery mechanisms for SCTs in TLS (X.509v3 extension, TLS extension, OCSP stapling). *(pp.13-15)*
- An HTTPS/JSON log API: add-chain, add-pre-chain, get-sth, get-sth-consistency, get-proof-by-hash, get-entries, get-roots, get-entry-and-proof. *(pp.17-21)*
- Client roles (submitter, TLS client, monitor, auditor) and a monitor algorithm; misbehaviour detection via audit proofs and gossip of STHs. *(pp.21-25)*

## Study Design (empirical papers)
*Not an empirical paper; protocol specification.*

## Methodology
Protocol specification. Data structures follow TLS presentation language (Section 4 of RFC 5246). Key words per RFC 2119. *(p.4)* The mechanism is general but this document only describes its use for public TLS server certificates issued by public CAs. *(p.3)*

## Key Equations / Statistical Models

### Merkle Tree Hash (Section 2.1)
Input: ordered list of n inputs D[n] = {d(0), d(1), ..., d(n-1)}. Output: a single 32-byte Merkle Tree Hash. Hash algorithm: SHA-256 (fixed for this experiment; it is anticipated each log could specify a hash algorithm). *(p.4)*

$$
MTH(\{\}) = \text{SHA-256}()
$$
The hash of an empty list is the hash of the empty string. *(p.4)*

$$
MTH(\{d(0)\}) = \text{SHA-256}(\texttt{0x00} \,\|\, d(0))
$$
Leaf hash of a one-entry list. *(p.5)*

$$
MTH(D[n]) = \text{SHA-256}(\texttt{0x01} \,\|\, MTH(D[0{:}k]) \,\|\, MTH(D[k{:}n])), \quad k < n \le 2k
$$
Where: for n > 1, k is the largest power of two smaller than n; || is concatenation; D[k1:k2] is the list {d(k1), ..., d(k2-1)} of length k2 - k1. The 0x00/0x01 prefixes give leaf/node domain separation, "required to give second preimage resistance". Length need not be a power of two; the tree may be unbalanced but its shape is uniquely determined by the number of leaves. The tree is "essentially the same as the history tree [CrosbyWallach] proposal, except our definition handles non-full trees differently." *(p.5)*

### Merkle Audit Paths (Section 2.1.1)
An audit path for a leaf is the shortest list of additional nodes required to compute the Merkle Tree Hash; at each step toward the root a path node is combined with the node computed so far. If the computed root matches the true root, the path proves the leaf exists in the tree. *(pp.5-6)*

$$
PATH(0, \{d(0)\}) = \{\}
$$

$$
PATH(m, D[n]) = PATH(m, D[0{:}k]) : MTH(D[k{:}n]) \quad \text{for } m < k
$$

$$
PATH(m, D[n]) = PATH(m-k, D[k{:}n]) : MTH(D[0{:}k]) \quad \text{for } m \ge k
$$
Where: PATH(m, D[n]) is the path for the (m+1)th input d(m), 0 <= m < n; k is the largest power of two smaller than n; ":" is list concatenation. *(p.6)*

### Merkle Consistency Proofs (Section 2.1.2)
A consistency proof for MTH(D[n]) and a previously advertised MTH(D[0:m]), m <= n, is the list of nodes needed to verify that the first m inputs are equal in both trees: a set of intermediate nodes sufficient to verify MTH(D[n]) such that (a subset of) the same nodes verify MTH(D[0:m]). The algorithm outputs the (unique) minimal consistency proof. *(p.6)*

$$
PROOF(m, D[n]) = SUBPROOF(m, D[n], \text{true}), \quad 0 < m < n
$$

$$
SUBPROOF(m, D[m], \text{true}) = \{\}
$$

$$
SUBPROOF(m, D[m], \text{false}) = \{MTH(D[m])\}
$$

$$
SUBPROOF(m, D[n], b) = SUBPROOF(m, D[0{:}k], b) : MTH(D[k{:}n]) \quad \text{if } m \le k
$$

$$
SUBPROOF(m, D[n], b) = SUBPROOF(m-k, D[k{:}n], \text{false}) : MTH(D[0{:}k]) \quad \text{if } m > k
$$
Where: for m < n, k is the largest power of two smaller than n. The boolean b records whether m is the value for which PROOF was originally requested (so MTH(D[0:m]) is already known and need not be included). If m <= k the right subtree D[k:n] exists only in the current tree, so prove the left subtree consistent and add a commitment to D[k:n]. If m > k the left subtree D[0:k] is identical in both trees, so prove the right subtree consistent and add a commitment to D[0:k]. *(pp.6-7)*

$$
|PROOF(m, D[n])| \le \lceil \log_2 n \rceil + 1
$$
Upper bound on the number of nodes in the proof. *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Merkle hash function | - | - | SHA-256 | fixed | p.4, p.15 | anticipated per-log choice in future |
| Tree hash output size | - | bytes | 32 | - | p.4 | |
| Leaf hash prefix | - | byte | 0x00 | - | p.5 | domain separation |
| Interior node hash prefix | - | byte | 0x01 | - | p.5 | domain separation |
| Consistency proof size bound | - | nodes | ceil(log2(n)) + 1 | - | p.7 | upper bound |
| ECDSA curve | - | - | NIST P-256 | - | p.8 | DSS D.1.2.3 |
| RSA signature scheme | - | - | RSASSA-PKCS1-V1_5 with SHA-256 | - | p.8 | RFC 3447 s.8.2 |
| Minimum RSA key size | - | bits | 2048 | >= 2048 | p.8 | |
| Maximum Merge Delay | MMD | time | not fixed by RFC | - | p.9 | log's promise window |
| SCT/STH timestamp | - | ms since 1970-01-01 00:00 (NTP, ignoring leap seconds) | - | uint64 | p.13 | |
| Log key_id | - | bytes | 32 | - | p.12 | SHA-256 of DER SubjectPublicKeyInfo of log key |
| issuer_key_hash | - | bytes | 32 | - | p.12 | SHA-256 of DER SPKI of issuer key |
| ASN.1Cert length | - | bytes | - | 1..2^24-1 | p.11 | |
| certificate_chain length | - | bytes | - | 0..2^24-1 | p.11 | |
| CtExtensions length | - | bytes | - | 0..2^16-1 | p.12 | |
| SerializedSCT length | - | bytes | - | 1..2^16-1 | p.13 | |
| sct_list length | - | bytes | - | 1..2^16-1 | p.13 | |
| Precertificate poison extension OID | - | OID | 1.3.6.1.4.1.11129.2.4.3 | - | p.9 | critical; extnValue ASN.1 NULL (0x05 0x00) |
| Precertificate Signing Certificate EKU OID | - | OID | 1.3.6.1.4.1.11129.2.4.4 | - | p.10 | CA:true |
| Embedded SCT list X.509v3 extension OID | - | OID | 1.3.6.1.4.1.11129.2.4.2 | - | p.14 | |
| OCSP SCT extension OID | - | OID | 1.3.6.1.4.1.11129.2.4.5 | - | p.14 | |
| TLS ExtensionType for SCT | - | - | 18 | - | p.23 | "signed_certificate_timestamp" |

## Effect Sizes / Key Quantitative Results
*None; specification.*

## Methods & Implementation Details

### Signatures (Section 2.1.4)
- Logs MUST use either ECDSA over NIST P-256 or RSA (RSASSA-PKCS1-V1_5 with SHA-256) with a key of at least 2048 bits. *(p.8)*

### Log operation (Section 3)
- A log is "a single, ever-growing, append-only Merkle Tree" of certificates. Anyone can submit; certificate owners or their CAs are expected to usually submit. *(p.9)*
- On a valid submission the log MUST immediately return an SCT: the log's promise to incorporate the certificate in the Merkle Tree within the MMD. A previously seen certificate MAY get the same SCT as before. *(p.9)*
- TLS servers MUST present an SCT from one or more logs with the certificate; TLS clients MUST reject certificates without a valid SCT for the end-entity certificate. *(p.9)*
- Periodically the log appends all new entries to the tree and signs the root. The log MUST incorporate a certificate within the MMD after SCT issuance. *(p.9)*
- Log operators MUST NOT impose conditions on retrieving or sharing log data. *(p.9)*

### Log entries (Section 3.1)
- The log SHALL publish a list of acceptable root certificates (possibly the union of major browser vendors' roots). Each submission MUST include all additional certificates needed to chain to an accepted root; the root MAY be omitted. *(p.9)*
- Precertificates: a CA may submit before issuance a Precertificate, built from the to-be-issued certificate by adding a critical poison extension (OID 1.3.6.1.4.1.11129.2.4.3, extnValue ASN.1 NULL 0x05 0x00) so standard X.509v3 clients cannot validate it, signed either by a special Precertificate Signing Certificate (CA:true, EKU 1.3.6.1.4.1.11129.2.4.4, directly certified by the CA that will sign the final certificate) or by the CA certificate that will sign the final certificate. *(pp.9-10)*
- The signature on the TBSCertificate indicates the CA's intent to issue; this intent is binding: misissuance of the Precertificate equals misissuance of the final certificate. *(p.10)*
- Logs MUST verify the chain to a trusted root; MAY accept expired, not-yet-valid, revoked or otherwise not-fully-valid certificates to accommodate CA software quirks; MUST refuse to publish certificates without a valid chain to a known root. On acceptance the log MUST store the entire chain used for verification (including the root, even if omitted from submission) and MUST present it for auditing on request, to prevent a CA from avoiding blame by logging a partial or empty chain. This excludes self-signed and DANE-based certificates until a spam-control mechanism is found. *(p.10)*
- Data structures *(pp.10-11)*:
  - `enum { x509_entry(0), precert_entry(1), (65535) } LogEntryType;`
  - `struct { LogEntryType entry_type; select (entry_type) { case x509_entry: X509ChainEntry; case precert_entry: PrecertChainEntry; } entry; } LogEntry;`
  - `opaque ASN.1Cert<1..2^24-1>;`
  - `struct { ASN.1Cert leaf_certificate; ASN.1Cert certificate_chain<0..2^24-1>; } X509ChainEntry;`
  - `struct { ASN.1Cert pre_certificate; ASN.1Cert precertificate_chain<0..2^24-1>; } PrecertChainEntry;`
- Logs MAY limit accepted chain length. Future revisions may add LogEntryType values. In certificate_chain the first certificate MUST certify the end-entity certificate, each following MUST directly certify the preceding one, and the final MUST be a root accepted by the log. In precertificate_chain the first MAY be a Precertificate Signing Certificate and MUST certify the first certificate; same chaining rules. *(p.11)*

### Signed Certificate Timestamp (Section 3.2)
- `enum { certificate_timestamp(0), tree_hash(1), (255) } SignatureType;` `enum { v1(0), (255) } Version;` `struct { opaque key_id[32]; } LogID;` `opaque TBSCertificate<1..2^24-1>;` `struct { opaque issuer_key_hash[32]; TBSCertificate tbs_certificate; } PreCert;` `opaque CtExtensions<0..2^16-1>;` *(pp.11-12)*
- key_id: SHA-256 of the log's public key over DER SubjectPublicKeyInfo. issuer_key_hash: SHA-256 of the issuer's public key (DER SPKI), needed to bind the issuer to the final certificate. *(p.12)*
- tbs_certificate: DER TBSCertificate of the Precertificate without signature and poison extension. If the Precertificate is not signed with the issuing CA certificate, the issuer is changed to that of the final issuing CA. It can be reconstructed from the final certificate by extracting the TBSCertificate and deleting the SCT extension. Because the TBSCertificate's AlgorithmIdentifier must match both signature algorithms, the Precertificate and final certificate must be signed with the same algorithm and parameters. If an Authority Key Identifier extension is present with a Precertificate Signing Certificate, it must also be present in that signing certificate and the TBSCertificate's AKI is changed to match the final issuer. *(p.12)*
- SignedCertificateTimestamp struct: sct_version; LogID id; uint64 timestamp; CtExtensions extensions; digitally-signed struct { Version sct_version; SignatureType signature_type = certificate_timestamp; uint64 timestamp; LogEntryType entry_type; select(entry_type) { x509_entry: ASN.1Cert; precert_entry: PreCert } signed_entry; CtExtensions extensions; }. Encoding of digitally-signed is per RFC 5246. *(p.13)*
- sct_version is v1; timestamp is current NTP time in ms since the epoch ignoring leap seconds; entry_type may be implicit from context; signed_entry is leaf_certificate or PreCert; no extensions currently specified. *(p.13)*

### Including SCTs in TLS (Section 3.3, 3.3.1)
- At least one log's SCT for the end-entity certificate must be in the handshake via (a) X.509v3 certificate extension, (b) TLS extension "signed_certificate_timestamp", or (c) OCSP stapling with OCSP extension OID 1.3.6.1.4.1.11129.2.4.5 and body `SignedCertificateTimestampList ::= OCTET STRING`. *(pp.13-14)*
- At least one SCT MUST be included; servers MAY include more. A CA MAY submit a Precertificate to multiple logs and embed all SCTs in the final certificate as an X.509v3 extension (OID 1.3.6.1.4.1.11129.2.4.2); clients reconstruct the original TBSCertificate to verify. *(p.14)*
- `opaque SerializedSCT<1..2^16-1>; struct { SerializedSCT sct_list <1..2^16-1>; } SignedCertificateTimestampList;` Each SCT is individually decodable so out-of-date clients can skip SCT versions they do not understand. *(pp.14-15)*
- TLS clients MUST implement all three mechanisms; servers MUST implement at least one; existing servers can generally use the certificate extension unmodified. Servers should send SCTs from multiple logs in case a log is unacceptable (e.g. struck off for misbehaviour or key compromise). *(p.15)*
- TLS extension: clients SHOULD send ClientHello extension with empty extension_data; servers MUST only send SCTs to clients that indicated support, setting extension_data to SignedCertificateTimestampList. On session resumption the server is not expected to process or include it. *(p.15)*

### Merkle Tree leaves (Section 3.4)
- `enum { timestamped_entry(0), (255) } MerkleLeafType;` `struct { uint64 timestamp; LogEntryType entry_type; select(entry_type) { x509_entry: ASN.1Cert; precert_entry: PreCert; } signed_entry; CtExtensions extensions; } TimestampedEntry;` `struct { Version version; MerkleLeafType leaf_type; select (leaf_type) { case timestamped_entry: TimestampedEntry; } } MerkleTreeLeaf;` *(pp.15-16)*
- Leaves of the tree are the leaf hashes of the MerkleTreeLeaf structures; timestamp, signed_entry, extensions copy the corresponding SCT. *(p.16)*

### Signed Tree Head (Section 3.5)
- Every time the log appends entries it SHOULD sign: digitally-signed struct { Version version; SignatureType signature_type = tree_hash; uint64 timestamp; uint64 tree_size; opaque sha256_root_hash[32]; } TreeHeadSignature. *(p.16)*
- The STH timestamp MUST be at least as recent as the most recent SCT timestamp in the tree; each subsequent timestamp MUST be more recent than the previous. tree_size is the number of entries. *(p.16)*
- Each log MUST produce on demand an STH no older than the MMD; if no submissions arrive during an MMD period the log SHALL sign the same Merkle Tree Hash with a fresh timestamp. *(p.17)*

### Log client API (Section 4)
- HTTPS GET or POST; POST parameters and all responses JSON; GET parameters order-independent form-urlencoded; binary data base64. Unknown fields should be ignored. <log server> may include a path. Errors are HTTP 4xx/5xx with human-readable messages. *(p.17)*
- 4.1 `POST /ct/v1/add-chain` in: chain (array of base64 certs, end-entity first, last is root or chains to known root). out: sct_version, id (base64 log ID; submitters are not assumed to know it), timestamp, extensions (logs should set empty string), signature (base64). A v1 client that cannot verify a non-v1 SCT MUST NOT construe this as an error; log clients do not need to verify this structure, only TLS clients do. *(pp.17-18)*
- 4.2 `POST /ct/v1/add-pre-chain` in: chain of base64 Precertificates; same outputs. *(p.18)*
- 4.3 `GET /ct/v1/get-sth` out: tree_size, timestamp, sha256_root_hash (base64), tree_head_signature. *(p.18)*
- 4.4 `GET /ct/v1/get-sth-consistency` in: first, second (tree sizes from existing v1 STHs). out: consistency (array of base64 nodes). No signature needed because it is used to verify a signed STH. *(p.19)*
- 4.5 `GET /ct/v1/get-proof-by-hash` in: hash (base64 v1 leaf hash per s.3.4), tree_size (existing v1 STH). out: leaf_index (0-based), audit_path. *(p.19)*
- 4.6 `GET /ct/v1/get-entries` in: start, end (0-based inclusive). out: entries[] of {leaf_input (base64 MerkleTreeLeaf), extra_data (certificate_chain for X509ChainEntry, whole PrecertChainEntry for precert)}. Not signed; verified by rebuilding the tree hash against an STH. All leaves MUST be v1, but a v1 client MUST NOT treat unrecognised MerkleLeafType or LogEntryType as an error; it treats unrecognised leaves as opaque tree input. start/end SHOULD be in 0 <= x < tree_size; logs MAY return partial responses when end >= tree_size; logs MAY cap entries per request and SHALL then return the maximum permissible, sequential from start. *(pp.19-20)*
- 4.7 `GET /ct/v1/get-roots` out: certificates (base64 accepted roots). *(p.21)*
- 4.8 `GET /ct/v1/get-entry-and-proof` in: leaf_index, tree_size (existing STH). out: leaf_input, extra_data, audit_path. "probably only useful for debugging". *(p.21)*

### Clients (Section 5)
- Any inconsistency is evidence of log misbehaviour, and signatures prevent the log from denying it. All clients should gossip, exchanging at least STHs, which is all that is required to ensure a consistent view; gossip mechanism deferred to a separate document. *(p.21)*
- Submitters submit certificates/Precertificates and use returned SCTs. *(p.22)*
- TLS clients validate the SCT signature over data computed from the SCT plus certificate with the log's public key (key distribution out of scope). TLS clients MUST reject SCTs whose timestamp is in the future. *(p.22)*
- Monitor algorithm (per log) *(pp.22-23)*:
  1. Fetch current STH (4.3).
  2. Verify STH signature.
  3. Fetch all entries corresponding to the STH (4.6).
  4. Confirm the tree built from fetched entries gives the STH's hash.
  5. Fetch current STH; repeat until it changes.
  6. Verify STH signature.
  7. Fetch all new entries (4.6); if they remain unavailable for an extended period, treat as log misbehaviour.
  8. Either (1) verify the full updated entry list hashes to the new STH, or, if not keeping all entries, (2) fetch a consistency proof new vs previous STH (4.4), (3) verify it, (4) verify the new entries generate the corresponding elements of the consistency proof.
  9. Go to step 5.
- Auditors take partial information and verify consistency with other partial information; may be part of a TLS client, standalone, or a monitor function. Any pair of STHs from a log can be checked with a consistency proof (4.4). A certificate with an SCT can be checked against any STH dated after SCT timestamp + MMD with an audit proof (4.5). *(pp.23-24)*

## Figures of Interest
- **Example tree (p.7):** 7-leaf tree; leaves a..f, j over d0..d6; g=H(a,b), h=H(c,d), i=H(e,f), j=leaf d6, k=H(g,h), l=H(i,j), hash=H(k,l). Audit paths: d0 -> [b, h, l]; d3 -> [c, g, l]; d4 -> [f, j, k]; d6 -> [i, k].
- **Incremental build (p.8):** hash0 (3 leaves), hash1=k (4 leaves), hash2 (6 leaves), hash (7 leaves). PROOF(3, D[7]) = [c, d, g, l] (c, g verify hash0; d, l show consistency). PROOF(4, D[7]) = [l] (verify with hash1=k and l). PROOF(6, D[7]) = [i, j, k] (k, i verify hash2; j additionally shows consistency).

## Results Summary
Specification only; no evaluation. Claimed properties: a log's two misbehaviours (failing to incorporate an SCT'd certificate within MMD; presenting conflicting views) are "promptly and publicly detectable". *(pp.24-25)*

## Limitations
- Logs do not prevent misissue and do not themselves detect it; they rely on interested parties such as domain owners to monitor. *(p.3, p.24)*
- An SCT is not a guarantee the certificate is not misissued: the subject may not check the logs, or the CA may refuse to revoke. *(p.24)*
- A misissued certificate with an SCT can be used for up to the MMD before it is available for audit. *(p.24)*
- Self-signed and DANE-based certificates effectively excluded pending a spam-control mechanism. *(p.10)*
- How clients obtain log public keys is not described. *(p.22)*
- Gossip protocol is not specified (separate document). *(p.21)*
- Hash algorithm fixed to SHA-256 for the experiment. *(p.4)*
- Future changes listed: key roll without creating a new log; hash/signing algorithm agility; gossip protocols. *(p.25)*
- Transcription note: the add-chain sct_version text reads "A compliant v1 implementation MUST NOT expect this to be 0 (i.e., v1)." exactly as printed. *(p.17)*

## Arguments Against Prior Work
- Positions its Merkle tree as essentially Crosby and Wallach's history tree, differing in how non-full trees are handled. *(p.5)*
- Implicit critique of the existing CA system: issuance is invisible to subjects, so misissue goes unnoticed. *(p.3)*

## Design Rationale
- Logs are untrusted; Merkle trees avoid blind trust because equivocation is detectable by comparing roots and consistency proofs. *(p.4)*
- Requiring chains rooted in a known CA prevents logs being spammed into uselessness. *(p.3)*
- Checking is asynchronous so TLS connections proceed without delay despite network issues and firewalls. *(p.4)*
- Storing the full verifying chain prevents a CA avoiding blame by logging a partial or empty chain. *(p.10)*
- Leaf/node prefix domain separation for second-preimage resistance. *(p.5)*
- SCTs serialised individually so old clients can skip unknown versions. *(p.15)*
- Consistency proofs and get-entries are unsigned because they are verified against a signed STH. *(p.19, p.20)*
- Privacy: MMD checks need not reveal the exact certificate to the log; clients can ask a trusted auditor, or request proofs for a batch around the SCT timestamp. *(p.24)*
- Efficiency: third-party auditors need not keep a copy of each log; STHs update without recomputing the tree; consistency proofs verify append-only updates without auditing the whole tree. *(p.25)*

## Testable Properties
- MTH({}) = SHA-256 of the empty string. *(p.4)*
- MTH({d}) = SHA-256(0x00 || d); interior = SHA-256(0x01 || left || right) with split at largest power of two k < n. *(p.5)*
- Tree shape is uniquely determined by n. *(p.5)*
- PATH(0, {d(0)}) is empty; for the 7-leaf example, PATH(0)=[b,h,l], PATH(3)=[c,g,l], PATH(4)=[f,j,k], PATH(6)=[i,k]. *(p.7)*
- PROOF(3, D[7]) = [c,d,g,l]; PROOF(4, D[7]) = [l]; PROOF(6, D[7]) = [i,j,k]. *(p.8)*
- |PROOF(m, D[n])| <= ceil(log2 n) + 1. *(p.7)*
- The consistency proof is the unique minimal one. *(p.6)*
- STH timestamps strictly increase and are >= the latest SCT timestamp in the tree. *(p.16)*
- An STH no older than MMD is always available. *(p.17)*
- Every SCT'd certificate appears in every STH dated after SCT timestamp + MMD. *(p.9, p.24)*
- Two conflicting STHs from the same log constitute cryptographic proof of misbehaviour. *(p.25)*
- TLS clients reject SCTs with future timestamps. *(p.22)*

## Relevance to Project
propstore stores provenance on git notes and claims in git-backed storage; CT is the canonical design for an append-only, publicly verifiable log with compact inclusion and consistency proofs over an untrusted operator. The exact MTH/PATH/PROOF recursions are directly implementable for verifying that a federated peer's claim history only grows (consistency proof between two observed heads) and that a specific artifact is included (audit path), and STH gossip is the mechanism for detecting equivocation between peers. The SCT-as-promise-within-MMD pattern is a model for "accepted now, provably included later" without a pre-render gate.

## Open Questions
- [ ] How should log public keys be distributed? (explicitly out of scope, p.22)
- [ ] What gossip protocol? (deferred, p.21)
- [ ] The RFC does not fix an MMD value.

## Related Work Worth Reading
- Crosby and Wallach 2009, "Efficient Data Structures for Tamper-Evident Logging" (history tree basis). *(p.26)*
- RFC 5246 (TLS 1.2), RFC 5280 (X.509 profile), RFC 6066 (TLS extensions), RFC 2560 (OCSP), RFC 5905 (NTPv4). *(pp.26-27)*

## Collection Cross-References

### Already in Collection
- [Efficient Data Structures for Tamper-Evident Logging](../Crosby_2009_EfficientDataStructuresTamper-Evident/notes.md) - [CrosbyWallach], the history tree on which CT's Merkle tree, audit paths and consistency proofs are based; CT differs in how non-full trees are handled *(p.26)*

### New Leads (Not Yet in Collection)
- RFC 5246 - TLS 1.2, whose presentation language and digitally-signed encoding define all CT data structures
- RFC 5280 - X.509 profile, the TBSCertificate structure underlying Precertificates
- RFC 6066 - TLS extensions, one of the three SCT delivery mechanisms
- RFC 2560 - OCSP, whose stapling carries SCTs

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found; Crosby and Wallach 2009 and Mazières and Shasha 2002 predate this RFC and mention it only in this collection's project-relevance notes)

### Conceptual Links (not citation-based)
- [Building secure file systems out of Byzantine storage](../Mazières_2002_BuildingSecureFileSystems/notes.md) - Strong. Both treat the storage operator as untrusted and make equivocation detectable rather than impossible: CT's log can present conflicting views, which signed tree heads plus client gossip expose; SUNDR's server can fork users' views, which signed version structures plus out-of-band communication expose. CT covers one append-only log with a single writer (the log); SUNDR covers a multi-user file system. Both leave the gossip/out-of-band channel unspecified.
