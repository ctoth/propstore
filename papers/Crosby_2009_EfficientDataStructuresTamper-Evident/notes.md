---
title: "Efficient Data Structures for Tamper-Evident Logging"
authors: "Scott A. Crosby, Dan S. Wallach"
year: 2009
venue: "Proceedings of the 18th USENIX Security Symposium (Montreal), pp. 317-334"
doi_url: ""
pages: "317-334"
affiliation: "Department of Computer Science, Rice University"
funding: "NSF grants CNS-0524211 and CNS-0509297"
note: "PDF from https://www.usenix.org/legacy/event/sec09/tech/full_papers/crosby.pdf (17 PDF pages, no printed page numbers visible). Page citations (p.N) below are 1-based PDF page numbers."
---

# Efficient Data Structures for Tamper-Evident Logging

## One-Sentence Summary
Defines tamper-evident history semantics for an untrusted logger audited by clients and auditors (five algorithms: ADD, INCR.GEN, MEMBERSHIP.GEN, INCR.VF, MEMBERSHIP.VF; property: historical consistency) and gives the *history tree*, a versioned Merkle tree whose incremental and membership proofs are O(log n), plus *Merkle aggregation* for authenticated attribute queries and verifiable safe deletion, evaluated on an 80-million-event syslog trace. *(pp.1-3, pp.4-10)*

## Problem Addressed
An untrusted logger is the sole author of a dynamic log and signs a stream of commitments, each a snapshot of the whole log. Authenticated dictionaries detect tampering *within* a snapshot, but nothing stops a logger making snapshots with "inconsistent claims about the past". Existing hash-chain logs require auditors to examine every intermediate event between snapshots (linear space and time); skip-list designs need a full scan to prove internal consistency; CATS only probabilistically detects tampering; Pavlou and Snodgrass's auditing is expensive. Prior authenticated data structures assume a trusted author (e.g., SUNDR trusts clients to sign updates). *(pp.1-2)*

## Key Contributions
- Formal semantics: membership auditing, incremental auditing, the tamper-evident history system as a 5-tuple of algorithms, and Historical Consistency. *(pp.2-3)*
- Observation that "a tamper-evident log requires frequent auditing": an unaudited commitment can be tampered with undetected. *(p.2)*
- History tree with versioned hash recurrence (Fig. 5) so any older view's root can be recomputed; O(log n) ADD, incremental and membership proofs; proofs need no signatures. *(pp.4-7)*
- Partial proofs and frozen hash cache; mapping onto write-once append-only storage in post-order. *(p.7)*
- Merkle aggregation (tau, oplus, Gamma) with authenticated queries (no false negatives) and safe deletion. *(pp.8-10)*
- Prototype on syslog: 1,750 events/s with signatures on one core, 10,500 events/s with signatures offloaded; 3 KB-scale membership proofs in an 80M-event log. *(p.1, pp.10-12)*

## Study Design (empirical papers)
- **Type:** Systems prototype benchmark.
- **Population:** Syslog trace of 4 million events from 13 departmental servers over 106 hours (9 facilities, 6 levels, 52 distinct tags; 88.1% mail server, 11.5% from 98,743 failed ssh connection attempts, 0.393% other); replayed 20x to 80 million events. *(p.11)*
- **Platform:** Python 2.5.2 + C++ hybrid; Intel Core 2 Duo 2.4 GHz, 4 GB RAM, 64-bit Linux; single-threaded; SHA-1 and 1024-bit DSA from OpenSSL. *(p.11)*
- **Endpoints:** insertion rate, proof generation rate and size, verification rate, safe-deletion kept ratio, query overhead ratio. *(pp.11-13)*

## Methodology

### Security model (Section 2)
- Standard assumptions: no signature forgery, no hash collisions. Secrecy of events is out of scope (encryption). Single monolithic log on a single host. Goal is detection, not prevention; replication for availability is out of scope. *(p.2)*
- Entities: many *clients* generate events; a centralized, totally untrusted *logger*; one or more trusted *auditors*. Clients and auditors have very limited storage; loggers unlimited. At least one auditor is incorruptible. One host may play client and auditor. *(p.2)*
- Clients are trusted only while following the insertion protocol; once correctly inserted, an event must not be undetectably hidden or modified "even if the original client is subsequently colluding with the logger". *(p.2)*
- Incremental proofs: current and prior commitment make consistent claims about past events. Membership proofs: return an event with a proof it is consistent with the current commitment. "These two styles of proofs are sufficient to yield tamper-evidence." *(p.2)*

### Semantics (Section 2.1)
- On each event X the logger assigns index i, appends, and produces a version-i commitment C_i depending on X_0...X_i, bound to version i, signed and published. Each commitment fixes an *independent* history; primes distinguish histories (events of C'_j are X'_0...X'_j). *(pp.2-3)*
- Membership auditing: given index i and commitment C_j, i <= j, return X_i and proof that C_j implies X_i is the ith event. *(p.3)*
- Incremental auditing: given C_j and C'_k, j <= k, prove consistent claims: X_a = X'_a for all a in [0, j]. Once verified the auditor can discard C_j. Rollback-and-fork tampering is caught by historical consistency plus the logger's inability to generate an incremental proof between commitments on different forks. *(p.3)*

### Client insertion protocol (Section 2.2)
- Clients must immediately redistribute received commitments to auditors (e.g., gossip) to prevent later collusion to roll back. Not every auditor need audit every commitment "so long as some auditor audits every commitment". Auditors must reconcile commitments from multiple clients/auditors, or the logger publishes commitments publicly. *(p.3)*

### Definition: tamper-evident history (Section 2.3)
Five algorithms *(p.3)*:
- H.ADD(X) -> C_j: append event, return new commitment.
- H.INCR.GEN(C_i, C_j) -> P: incremental proof, i <= j.
- H.MEMBERSHIP.GEN(i, C_j) -> (P, X_i): membership proof for event i from C_j, i <= j.
- P.INCR.VF(C'_i, C_j) -> {T, F}: checks P proves C_j fixes every entry fixed by C'_i; T if no divergence detected.
- P.MEMBERSHIP.VF(i, C_j, X'_i) -> {T, F}: checks P proves X'_i is the ith event in log defined by C_j.
- First three run on the logger; verifiers run on auditors/clients. Only commitments are signed; proofs need no signatures.

**Historical Consistency** *(p.3)*: if P.INCR.VF(C_j, C_k) = T with j <= k, and P'.MEMBERSHIP.VF(i, C_j, X'_i) = T and P''.MEMBERSHIP.VF(i, C_k, X''_i) = T with i <= j, then X'_i = X''_i.

### Other threat models (Section 2.4)
- Forward integrity (Bellare and Yee): clients fully trusted with limited storage; logger honest until a Byzantine failure; must not undetectably tamper with pre-failure events. Under this model membership auditing of just-added events is unnecessary, but incremental auditing is still needed, and membership auditing is still needed to examine old events. *(pp.3-4)*
- Itkis: detect divergence without online interaction; proved an O(n) lower bound on commitment size; this paper gets a tighter bound because the logger cooperates in generating proofs. *(p.4)*
- Trusted hardware alternative: security rests on protecting hardware; the cryptographic approach rests on simpler assumptions. *(p.4)*

## Key Equations / Statistical Models

### History tree structure (Section 3)
A filled history tree of depth d is a binary Merkle tree storing 2^d events. Interior node I_{i,r} has index i and layer r; leaf I_{i,0} stores X_i; I_{i,r} has left child I_{i,r-1} and right child I_{i+2^{r-1}, r-1}. Empty subtrees are represented as a box (written here as `EMPTY`). Leaf label is the hash of the event; interior label is hash of the concatenation of children's labels. *(p.4)*

A version-n history tree stores n+1 events X_0...X_n. A version-v view reconstructs interior hashes for a tree containing only X_0...X_v. *(p.6)*

### Recurrence (Figure 5) *(p.6)*

$$
A^v_{i,0} = H(0 \,\|\, X_i) \quad \text{if } v \ge i
$$

$$
A^v_{i,r} = H(1 \,\|\, A^v_{i,r-1} \,\|\, \square) \quad \text{if } v < i + 2^{r-1}
$$

$$
A^v_{i,r} = H(1 \,\|\, A^v_{i,r-1} \,\|\, A^v_{i+2^{r-1},r-1}) \quad \text{if } v \ge i + 2^{r-1}
$$

$$
C_n = A^n_{0,d}
$$

$$
A^v_{i,r} \equiv FH_{i,r} \quad \text{whenever } v \ge i + 2^r - 1
$$
Where: A^v_{i,r} is the hash on node I_{i,r} in view v; H is the hash function; square is the empty-subtree placeholder; C_n is the version-n commitment; FH_{i,r} is the cached frozen hash. *(p.6)*

$$
d = \lceil \log_2(n+1) \rceil
$$
Depth grows when the tree fills (n = 2^d - 1): a new root one level up with the old tree as left child and an empty right child. Illustrations assume fixed depth. *(p.6)*

Frozen node: I_{i,r} is frozen in a version-n tree when n >= i + 2^r - 1; its hash never changes again. With the frozen hash cache, any A^v_{i,r} can be recomputed in O(d). Inserting an event freezes O(1) expected, O(d) worst-case nodes. *(p.6)*

### Hash chain baseline *(p.5)*

$$
C_i = H(C_{i-1} \,\|\, X_i), \quad C_{-1} = \square
$$
Does not permit events to be skipped; proofs must include every intermediate event.

### Merkle aggregation (Figure 8) *(p.10)*

$$
A^v_{i,r}.* = H(A^v_{i,r}.H \,\|\, A^v_{i,r}.A)
$$

$$
A^v_{i,0}.H = H(0 \,\|\, X_i) \quad \text{if } v \ge i
$$

$$
A^v_{i,0}.A = \Gamma(X_i) \quad \text{if } v \ge i
$$

$$
A^v_{i,r}.H = H(1 \,\|\, A^v_{i,r-1}.* \,\|\, \square) \quad \text{if } v < i + 2^{r-1}
$$

$$
A^v_{i,r}.H = H(1 \,\|\, A^v_{i,r-1}.* \,\|\, A^v_{i+2^{r-1},r-1}.*) \quad \text{if } v \ge i + 2^{r-1}
$$

$$
A^v_{i,r}.A = A^v_{i,r-1}.A \quad \text{if } v < i + 2^{r-1}
$$

$$
A^v_{i,r}.A = A^v_{i,r-1}.A \oplus A^v_{i+2^{r-1},r-1}.A \quad \text{if } v \ge i + 2^{r-1}
$$

$$
C_n = A^n_{0,d}.*
$$
Where: .H is a node's hash label, .A its attribute annotation, .* the subtree authenticator fixing both the node's hash and attributes and recursively the whole subtree. The hash label does *not* fix the node's own attributes; the authenticator does. Aggregation strategy is the 3-tuple (tau, oplus, Gamma): tau the attribute type, oplus a deterministic aggregation function for interior nodes, Gamma a deterministic event-to-attribute function. *(pp.9-10)*

Storage/proof inflation factor *(p.10)*:

$$
\frac{A + B}{A}
$$
Where A is hash size and B attribute size.

### Stable and exact predicates *(p.10)*
Stable: for all x, Q(x) implies Q^Gamma(Gamma(x)); for all x, y, Q^Gamma(x) or Q^Gamma(y) implies Q^Gamma(x oplus y); and for all x, Q^Gamma(x) or Q^Gamma(square) implies Q^Gamma(x oplus square).
Exact: Q(x) iff Q^Gamma(Gamma(x)), and Q^Gamma(x) or Q^Gamma(y) iff Q^Gamma(x oplus y).

Query proof size with t matching events *(p.10)*:

$$
O((1 + t)\log_2 n)
$$

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Tree depth | d | levels | ceil(log2(n+1)) | - | p.6 | |
| Events in a version-n tree | - | events | n+1 | - | p.6 | |
| Pruned tree size, self-contained proof | - | frozen nodes | 2d | at most | p.7 | path to X_i and X_j |
| Pruned tree size when log moved to version k | - | nodes | 3d | at most | p.7 | paths to X_i, X_j around version k |
| Partial proof size | - | frozen hashes | O(log2(n-j)) | - | p.7 | O(1) if proof after every insertion |
| Auditor cache for partial proofs | - | hashes | d | - | p.7 | |
| Hash function (prototype) | - | - | SHA-1 | - | p.11 | 20 bytes per node |
| Signature (prototype) | - | - | DSA-1024 | - | p.11 | OpenSSL |
| Attributes per node (prototype) | B | bytes | 20 | - | p.11 | five attributes |
| Leaf offset+length in value store | - | bytes | 12 | - | p.11 | |
| Tag/host Bloom filter | - | - | 2-of-32 bits | 4-of-64 | p.11, p.12 | |
| Merkle aggregation RAM limit | - | events | ~4 million | - | p.11 | query results must fit in RAM |
| Trace size (80M events) | - | GB | 14.0 | - | p.11 | history tree adds 13.6 GB |
| History tree + value store (80M) | - | GB | 27 | - | p.12 | |
| Signed-commitment batching example | - | commitments per signature | 16 | - | p.14 | estimated 17,000 events/s |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Membership proof, random event | size | 3100 bytes (approx. 3 KB) | - | - | 80M-event log | p.1, p.5 |
| Hash-chain equivalent proof | size | 800 MB / avg 40 million hashes | - | - | 80M-event log | p.1, p.5 |
| Insert rate with signatures | rate | 1,750 events/s | - | - | one core | p.1, p.11 |
| Insert rate signatures offloaded | rate | 10,500 events/s | - | - | 1.9 MB/s, 1.1 TB/week | p.1, p.12 |
| Parse syslog message | rate / % CPU | 81,000 events/s / 2.4% | - | - | Table 2 | p.12 |
| Insert event into log | rate / % CPU | 66,000 events/s / 2.6% | - | - | Table 2 | p.12 |
| Generate commitment | rate / % CPU | 15,000 events/s / 11.8% | - | - | Table 2 | p.12 |
| Sign commitment | rate / % CPU | 2,100 events/s / 83.3% | - | - | Table 2 | p.12 |
| Membership proofs, with locality | rate / size | 8,600/s / avg 2,400 bytes | - | - | recent 5M events in RAM | p.12 |
| Membership proofs, no locality | rate / size | 32/s / avg 3,100 bytes | - | - | disk seek bound | p.12 |
| Incremental proof size | size | 1200-2500 bytes | - | - | distance 2 to 2M events | p.12 |
| Incremental proof generation | rate | 10,500-18,000 proofs/s | - | - | shorter distance faster | p.12 |
| gzip on proofs | effect | halves size, halves generation rate | - | - | | p.12 |
| Scaling 4M to 80M | slowdown | roughly 10% | - | - | insertion and incremental audit | p.12 |
| DSA-1024 verification | rate | 1,900/s | - | - | auditor | p.12 |
| Pruned tree parsing (Python) | rate | 480/s | - | - | auditor | p.12 |
| Proof verification after parse | rate | 9,000/s | - | - | auditor | p.12 |
| Safe deletion keep one host | events kept / size | 1.92% events, 2.29% serialized size, 14 s | - | - | 4M log | p.12 |
| Safe deletion nodes purged | fraction | 95.1% of nodes (98.08% events purged) | - | - | 4M log | p.12-13 |
| Bloom queries exceeding worst case | count | 34 of 65 | - | - | 2-of-32 Bloom | p.12 |
| 4-of-64 Bloom | effect | 15% fewer nodes, +64 bits per node | - | - | | p.12 |
| Bloom filters matching <1% of events | purge | over 90% of nodes | - | - | safe deletion | p.13 |
| Max insert rate, everything else offloaded | rate | 38,000 events/s | - | - | one core | p.14 |

Predicates used: 86 total = 52 (one tag each), 13 (one host), 9 (one facility), 6 (one level each), 6 (k highest levels). *(p.12)*

## Methods & Implementation Details
- Five operations on the history tree *(pp.6-7)*:
  - H.ADD(X) -> C_n: next free slot n; C_n by eqs (1)-(4).
  - H.INCR.GEN(C_i, C_j) -> P: pruned tree P is a version-j proof skeleton including a path to X_i.
  - H.MEMBERSHIP.GEN(i, C_j) -> (P, X_i): same construction.
  - P.INCR.VF(C''_i, C'_j): from P compute A^i_{0,d} and A^j_{0,d} (needs a path to X_i); T iff C''_i = A^i_{0,d} and C'_j = A^j_{0,d}.
  - P.MEMBERSHIP.VF(i, C'_j, X'_i): compute A^j_{0,d} and extract X_i (needs path); T iff C'_j = A^j_{0,d} and X_i = X'_i.
- Proof skeleton: the minimum pruned tree of a version-n tree containing only frozen nodes: frozen hashes of the left siblings on the path from X_n to the root. A leaf is included by recursively *splitting* nodes on its path (include children's hashes instead of the node). *(p.6)*
- Worked example (Figs 1-4, 6): incremental proof from C'_2 (3 events) to C''_6 (7 events). The pruned tree P includes I_{0,1}, X_2, X_3, I_{4,1}, X_6; the auditor recomputes C_6 and, by treating X_3 and I_{4,2} as empty, C_2; equality of circled nodes shows both commit the same X_0, X_1, X_2 though X_0, X_1, X_4, X_5 are unknown to the auditor. *(pp.4-6)*
- Incremental and membership proofs share structure and implementation; one pruned tree can embed paths to several leaves. *(p.7)*
- Full vs minimum representation: proofs carry frozen hashes only for stubs. *(p.7)*
- Round-based time-stamping: publish last commitment per round; a client proves its document X_j was submitted in the round and its order via paths to X_i, X_j, X_k; a separate tree per round equals Buldas et al.'s threaded authentication tree. *(p.7)*
- Secondary storage: frozen nodes are immutable; predetermined write order (X_0), (X_1, I_{0,1}), (X_2), (X_3, I_{2,1}, I_{0,2}), (X_4), ... equals post-order; (index, layer) to byte offset in O(log n) arithmetic; variable-length events in a separate append-only value store, leaves hold offsets. *(p.7)*
- Merkle aggregation query: H.QUERY(C_j, Q^Gamma) -> P returns pruned tree where every elided subtree does not match; P.QUERY.VF(C'_j, Q^Gamma) checks every stub fails Q^Gamma and reconstructed C_j = C'_j. Builder starts from proof skeleton and splits nodes where Q^Gamma(FH_{i,r}.A) holds. Verifier recursively traverses P; a stub with Q^Gamma true fails verification. *(p.10)*
- Safe deletion: Q(x) stable, true for events to keep; logger stores a pruned tree with all nodes/leaves where Q^Gamma holds; for a deleted X_i it supplies a path to an ancestor A with Q^Gamma(A) false, which implies Q(X_i) false. Purging X_i...X_j means proofs involving C_i...C_j can no longer be generated, so audits using those commitments must be performed first. Safe deletion does not save space on append-only storage. *(pp.10-11)*
- Private search: aggregation needs only Gamma(X_i); clients can encrypt events and sign public attributes; Bloom filters give private indexing. *(p.11)*
- Prototype attributes: tags and hosts as 2-of-32-bit Bloom filters; facilities and hosts as bit-vectors; message timestamp as an interval for range queries. *(p.11)*
- Scaling (Section 6): offload signatures (>80% of insert cost, no interdependencies); compute commitments concurrently (read-only access); replicas on multiple hosts; logs larger than RAM partitioned across a cluster; sign batches: delay returning C_i until a signature exists for some later C_j, client then requests a membership proof from C_j to event i and checks X_i = X. *(pp.13-14)*

## Figures of Interest
- **Fig 1 (p.4):** version-2 history, C'_2 = I'_{0,3}.
- **Fig 2 (p.4):** version-6 history, C''_6 = I''_{0,3}.
- **Fig 3 (p.4):** incremental proof P between version 2 and 6; circled nodes included.
- **Fig 4 (p.5):** graphical notation: solid discs included hashes, dots recomputable/may change, open circles recomputable/frozen, grey unnecessary.
- **Fig 5 (p.6):** hash recurrence (1)-(4).
- **Fig 6 (p.6):** proof skeleton for a version-6 tree.
- **Fig 7 (p.9):** Merkle aggregation with X_2 and X_5 flagged.
- **Fig 8 (p.10):** Merkle aggregation recurrences (5)-(10).
- **Fig 9 (p.13):** safe deletion overhead: fraction of annotations kept vs fraction of events kept, with best/worst-case bounds.
- **Fig 10 (p.13):** query overhead per event vs fraction of events in result.
- **Table 1 (p.8):** complexity comparison (below).
- **Table 2 (p.12):** logger per-step performance.

### Table 1 (p.8)

| Operation | Hash chain | Skip list | History tree |
|-----------|-----------|-----------|--------------|
| ADD time | O(1) | O(1) | O(log2 n) |
| INCR.GEN proof size to C_k | O(n-k) | O(n) | O(log2 n) |
| MEMBERSHIP.GEN proof size for X_k | O(n-k) | O(n) | O(log2 n) |
| Cache size | - | O(log2 n) | O(log2 n) |
| INCR.GEN partial proof size | - | O(n-j) | O(log2(n-j)) |
| MEMBERSHIP.GEN partial proof size | - | O(log2(n-i)) | O(log2(n-i)) |

All three have O(1) storage per event and O(1) commitment size. *(p.8)*

## Results Summary
The history tree "strictly dominates both hash chains and skip lists in proof generation time and proof sizes", especially for partial auditing or partial proofs. *(p.8)* Prototype throughput and proof sizes as tabulated above; auditors cannot individually verify as fast as the logger generates, but auditors operate independently in parallel. *(p.12)* Authenticated query overhead is modest with exact predicates; inexact Bloom predicates sometimes exceed the worst-case bound. *(p.13)*

## Limitations
- Detection only; cannot prevent destruction or alteration; availability via replication is out of scope. *(p.2)*
- Requires frequent auditing; an unaudited commitment gives no guarantee. *(p.2, p.8)*
- Single monolithic logger; scaling beyond ~38,000 events/s needs disjoint logs with entanglement, left as future work. *(p.14)*
- Low-locality membership proofs are disk-seek bound (32/s). *(p.12)*
- Merkle aggregation query results limited to what fits in RAM (~4M events); experiments used the 4M log. *(p.11, p.12)*
- Aggregation strategy fixed at log creation, restricting later queries. *(p.9)*
- A dishonest logger or client can insert false entries whose attributes pollute queries; unaudited events' attributes are not guaranteed. *(p.10)*
- Safe deletion makes proofs involving purged commitments impossible; does not save space on append-only storage. *(pp.10-11)*
- Trusting clients during insertion; a malicious client can insert garbage. *(p.2)*

## Arguments Against Prior Work
- Hash chains [56, 17, 57]: auditors must examine every intermediate event; proofs O(n-k); every auditor must eventually receive every event; feasible only at low volume. *(p.1, p.5, p.8)*
- Skip list (Maniatis and Baker [43]): logarithmic lookups assume known internal consistency, which requires scanning the whole log; suffers the multi-path problem; auditor with no prior contact must receive every event. *(pp.1-2, p.8)*
- CATS [63]: only probabilistic detection by auditing subsets. *(p.2)*
- Pavlou and Snodgrass [51]: each auditor must visit each snapshot. *(p.2)*
- Authenticated data structures [34, 49, 5, 11, 24, 2]: assume a trusted author; SUNDR [36] uses version vectors but only trusted clients sign updates. *(p.1)*
- Hash chains and skip lists only have a fleeting ADD-time advantage; they suffer O(n-j) the moment incremental audits happen and cannot reduce it by random auditing. *(p.8)*
- Append-only databases [64, 47] depend on write-once storage semantics not independently verifiable by a remote auditor. *(p.14)*
- Prior Merkle-based secure aggregation in sensor networks [13, 45] is less efficient and interactive. *(p.15)*

## Design Rationale
- Novelty is a versioned hash computation over the Merkle tree so snapshots with distinct roots can be proved consistent. *(p.4)*
- Canonical representation: one unique path from C_n to each X_i, avoiding cross-checking of alternative paths. *(p.8)*
- Proofs need no signatures; only commitments are signed. *(p.3)*
- Skipping nodes in audits is safe because skipped events are fixed by unchanged hashes above them; enables selective and probabilistic auditing policies; total auditing overhead proportional to number of events rather than events times auditors. *(p.5)*
- Leaf/interior prefix 0/1 in hashes. *(p.6)*
- Subtree authenticator design allows eliding a subtree with one hash plus one attribute set while letting the verifier locally check aggregation. *(p.9)*
- False positives allowed in queries (filtered by auditor), false negatives forbidden. *(p.10)*

## Testable Properties
- Historical consistency: verified incremental proof C_j to C_k plus membership proofs of index i in both implies the same event. *(p.3)*
- Node I_{i,r} frozen iff n >= i + 2^r - 1; frozen hashes never change. *(p.6)*
- Self-contained proof has at most 2d frozen nodes; at most 3d when generated against a later version k. *(p.7)*
- ADD freezes O(1) expected, O(d) worst-case nodes. *(p.6)*
- History tree proofs are O(log2 n) vs O(n-k) for hash chains (Table 1). *(p.8)*
- A query proof with t matching events has size O((1+t) log2 n). *(p.10)*
- A stub in a query proof whose attributes satisfy a stable Q^Gamma makes verification fail. *(p.10)*
- Merkle aggregation inflates storage and proofs by (A+B)/A. *(p.10)*
- Write order of frozen nodes equals post-order traversal. *(p.7)*

## Relevance to Project
Directly applicable to propstore's git-backed, append-only provenance and federation: the history tree is the structure RFC 6962 adopts (with different non-full-tree handling). The semantics (membership vs incremental auditing, historical consistency, gossip of commitments) give a vocabulary for verifying that a peer's published claim/provenance history only grows and has not forked. Merkle aggregation with (tau, oplus, Gamma) is a model for authenticated render-time queries over attributes (e.g., provenance status) with no false negatives, and safe deletion shows how purges can be proven policy-conformant rather than trusted.

## Open Questions
- [ ] Multi-logger designs with entanglement are future work (p.14).
- [ ] No exact handling specified in this paper for non-full trees beyond growing depth; RFC 6962 handles non-full trees differently.

## Related Work Worth Reading
- [43] Maniatis and Baker, timeline entanglement (USENIX Security 2002).
- [36] Li, Krohn, Mazieres, Shasha, SUNDR (OSDI 2004).
- [10] Buldas, Lipmaa, Schoenmakers, accountable time-stamping (threaded authentication tree).
- [27] Haber and Stornetta, time-stamping.
- [57] Schneier and Kelsey, secure audit logs.
- [4] Bellare and Yee, forward integrity.
- [31] Itkis, cryptographic tamper evidence.
- [28] Haeberlen et al., PeerReview.

## Collection Cross-References

### Already in Collection
- (none - [36] is Li, Krohn, Mazières and Shasha's SUNDR system paper, OSDI 2004, not the 2002 Mazières and Shasha fork-consistency paper in the collection)

### New Leads (Not Yet in Collection)
- Maniatis and Baker (2002) - "Secure history preservation through timeline entanglement" - the skip-list log the paper argues against; proposed direction for multi-logger scaling
- Li, Krohn, Mazières and Shasha (2004) - "Secure untrusted data repository (SUNDR)" - untrusted storage with fork detection by trusted clients
- Buldas, Lipmaa and Schoenmakers (2000) - "Optimally efficient accountable time-stamping" - threaded authentication tree, equivalent to per-round history trees
- Schneier and Kelsey (1999) - "Secure audit logs to support computer forensics" - the classic hash-chain secure audit log
- Bellare and Yee (1997) - "Forward integrity for secure audit logs" - forward-integrity threat model
- Haber and Stornetta - "How to time-stamp a digital document" - linked time-stamping
- Merkle (1988) - "A digital signature based on a conventional encryption function" - Merkle hash trees

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [Certificate Transparency](../Laurie_2013_CertificateTransparency/notes.md) - [CrosbyWallach]; RFC 6962's Merkle tree, audit paths and consistency proofs are based on this paper's history tree, with different handling of non-full trees

### Conceptual Links (not citation-based)
- [Building secure file systems out of Byzantine storage](../Mazières_2002_BuildingSecureFileSystems/notes.md) - Strong. Both make an untrusted party's equivocation detectable: here an untrusted logger that shows different auditors inconsistent histories is caught by incremental (consistency) proofs between commitments plus gossip of commitments; there an untrusted file server that forks users' views is caught by signed version structures plus out-of-band communication. This paper's notes place SUNDR among systems that use version vectors with only trusted clients signing updates.
