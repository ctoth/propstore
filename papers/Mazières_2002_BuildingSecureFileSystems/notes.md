---
title: "Building secure file systems out of Byzantine storage"
authors: "David Mazières, Dennis Shasha"
year: 2002
venue: "Proceedings of the Twenty-First ACM Symposium on Principles of Distributed Computing (PODC 2002), pp. 108-117"
doi_url: "https://doi.org/10.1145/571825.571840"
pages: "108-117"
affiliation: "NYU Department of Computer Science"
funding: "NSF awards CCR-0093361 and IIS-9988345"
note: "PDF converted with Ghostscript from the authors' PostScript (https://www.scs.stanford.edu/~dm/home/papers/mazieres:sundr-podc.ps.gz). That copy is numbered 1-10, not the proceedings' 108-117; page citations (p.N) below use the printed 1-10 numbers. Full version: NYU TR2002-826."
---

# Building secure file systems out of Byzantine storage

## One-Sentence Summary
Defines *fork consistency* (via fetch-modify consistency and forking trees) as the strongest achievable integrity guarantee for a multi-user file system on an untrusted server, gives a sufficient "protocol correctness theorem", and proves that SUNDR's signed version-vector protocol (bare-bones, then concurrent with update certificates and a pending version list) is fork consistent whether or not the server obeys the protocol. *(p.1, pp.3-9)*

## Problem Addressed
Servers are often run by people with no role in the data (administrators, consultants, intruders). Byzantine server failures such as subtle tampering may go undetected. Signatures alone guarantee authenticity but not freshness: if the last signed update u1 sees from u2 is 24 hours old, u1 cannot tell whether u2 has been idle or the server is concealing u2's updates. Ideal immediate detection of any server misbehaviour is not achievable. *(p.1)*

## Key Contributions
- Fork consistency: if the server hides even one change by one user from another, the two can never again see each other's changes, which is easily detected with any out-of-band communication. *(p.1)*
- Formal definitions: client, principal, orderable, fetch-modify consistent, forking tree/forking group, fork consistent. *(pp.3-4)*
- Protocol correctness theorem: a partial order with two properties suffices for fork consistency; constructive proof building the forking tree from maximal chains. *(pp.4-5)*
- SUNDR architecture: block server with STORE/RETRIEVE/UNREFERENCE, virtual inodes, i-tables as hash trees, i-handles, signed version structures. *(pp.2-3)*
- Bare-bones protocol with version structures as signed version vectors and proofs (Proposition one client, Fetch-modify lemma, No join lemma, Bare-bones theorem). *(pp.5-7)*
- Concurrent protocol with update certificates, version-structure hashes V(x), user-version-hash triples, pending version list, and corresponding proofs. *(pp.7-9)*
- Claimed first to "render Byzantine file server failures readily detectable". *(p.1)*

## Study Design (empirical papers)
*Not empirical; protocol with proofs. No implementation measurements beyond cited signature timings.*

## Methodology
Formal definitions of consistency, a sufficient condition (protocol correctness theorem), then protocols proven to meet it. Cryptographic assumptions: collision-resistant hash; signatures existentially unforgeable under chosen-message attack; the paper assumes no collisions and no forgeries. *(p.2)* Secrecy is out of scope (intended to be layered with existing cryptographic storage techniques). *(p.1)*

## Key Equations / Statistical Models

### Version structure notation (Definition 7) *(p.5)*

$$
\{\textsc{vrs}, h, u, u_1\text{-}n_1\; u_2\text{-}n_2 \ldots\}_{K_u^{-1}}
$$
Where: VRS is a type constant; h the i-handle; u the owner; u_i-n_i means user u_i at version n_i; subscript K_u^{-1} means signed by u's private key.

### Version lookup and order (Definitions 8, 9) *(p.5)*

$$
x[u] = \text{u's version number in } x, \text{ or } 0 \text{ if } u \notin x
$$

$$
x \le y \iff \forall u.\; x[u] \le y[u]
$$

$$
x < y \iff x \le y \wedge \exists v.\; x[v] < y[v]
$$

### Bare-bones protocol update *(p.5)*

$$
x[v] \leftarrow y_v[v] \quad \forall v \in VSL
$$

$$
x[u] \leftarrow x[u] + 1
$$

### Update certificate (concurrent protocol) *(p.7)*

$$
\{\textsc{upd}, u, n, H(y_u), \text{inode-list}\}_{K_u^{-1}}
$$
Where: UPD a type constant; n u's new version number in the forthcoming version structure, normally n = y_u[u] + 1 (except when pipelining); H(y_u) collision-resistant hash of u's current VSL entry; inode-list holds <i-number, file handle> for modified file inodes and <i-number, delta> for directory inodes; empty for a fetch.

### Extended version structure and V *(p.7)*

$$
x = \{\textsc{vrs}, u, h, u_1\text{-}n_1\; u_2\text{-}n_2 \ldots, u_k\text{-}n_k\text{-}h_k \ldots\}
$$
V(x): remove the i-handle h, sort user-version pairs by user and user-version-hash triples by user and version, output a collision-resistant hash H of the remaining sorted fields. Hash values in triples are either the reserved value bottom or V of a version structure. Every structure x owned by u is assumed to contain u-x[u]-bottom.

### Order on extended version structures (Definition 10) *(p.7)*
x <= y iff (1) for all users u, x[u] <= y[u]; and (2) for each user-version-hash triple u-n-h in y, one of: (a) x[u] < n (x happened before the pending operation), (b) x also contains u-n-h (x after the pending op and reflects it), (c) x contains u-n-bottom and h = V(x) (x was the pending operation). x = y if identical except possibly the i-handle; x < y iff x <= y and x != y. Proposition: <= is transitive. *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Rabin signature time (1,024-bit, 800 MHz Pentium III) | - | ms | 7 | - | p.1 | |
| Rabin verification time | - | microseconds | 50 | - | p.1 | |
| Esign signature time (2,048-bit) | - | microseconds | 350 | - | p.1 | patented |
| Esign verification time | - | microseconds | 200 | - | p.1 | |
| Signatures per open or close of modified file | - | signatures | 2 | - | pp.1-2 | plus one network round trip |
| Extra asynchronous message before others see fresh contents | - | messages | 1 | - | p.2 | |
| i-number width | - | bits | 64 | - | p.3 | per-user virtual inode numbers |
| Root directory inode | - | i-number | 2 | - | p.3 | in superuser's i-table |
| BFS replica threshold (comparison) | - | fraction | > 2/3 uncompromised | - | p.2 | SUNDR needs one honest replica |

## Effect Sizes / Key Quantitative Results
*None reported.*

## Methods & Implementation Details

### Architecture (Section 3)
- Two subproblems: (1) from a user's i-handle and an i-number, retrieve and verify any block of a file; (2) a protocol for users to update i-handles and ensure each has every other user's latest i-handle. *(p.2)*
- Server stores blocks without interpreting them. RPCs: STORE (store a chunk), RETRIEVE (by collision-resistant hash), UNREFERENCE (decrement the user's per-block reference count; reclaim when zero for all users). *(p.2)*
- Keys: every user has a public key; key management out of scope (e.g. superuser key in pathname as in SFS, others in /etc/sundr_users; groups in /etc/group). Server authenticates users (to prevent unreferencing others' blocks) and has its own public key; all RPCs authenticated so users can hold the server responsible for incorrect replies. *(p.2)*
- Server stores a signed version structure per user and group (version data + i-handle) plus in-progress information. *(p.2)*
- Virtual inode: metadata plus size and hash of each block; hash of an indirect block for large files (double-, triple-, quadruple-indirect possible). Hash of a virtual inode = file handle. *(p.3, Fig. 1)*
- i-table: per user/group ordered list mapping 64-bit i-numbers to file handles; broken into blocks and stored as a hash tree; root hash = i-handle. Directories are virtual inodes whose data are sorted <file name, user, i-number> triples. *(p.3)*
- To modify: compute new i-handle, STORE new blocks, compute and sign a new version structure, update via UPDATE and COMMIT RPCs, then UNREFERENCE unneeded blocks. *(p.3)*

### Definitions (Section 4) *(pp.3-4)*
- Uses fetches and modifications rather than opens/closes: fetch-modify consistency instead of close-to-open. A fetch validates a cached copy or downloads new contents; a modification makes new content visible (on close, fsync, certain metadata ops).
- Def 1 Client: produces fetch/modify requests, each with a wall-clock *issue time*; completion time is when the routine returns. Clocks not assumed synchronized; a client does not know the issue time of its own operations.
- Def 2 Principal: entity authorized to access the file system with a public signature key whose private half the server does not know (user, user-as-group-member, client on behalf of a user).
- Def 3 Orderable: each op's completion time later than its issue time and a partial order *happens before* such that (1) if O1 completes before O2 is issued, O1 happens before O2; (2) it orders any two operations by the same client; (3) it totally orders all modifications to a given file; (4) it orders any fetch of a file w.r.t. all modifications to that file.
- Def 4 Fetch-modify consistent: orderable and every fetch F of file f returns the contents produced by exactly the modifications that happened before F, in happens-before order. (In SUNDR modifications overwrite whole files, so only the last modification matters.)
- Def 5 Forking tree: tree whose nodes carry forking groups (sets of operations) with: (1) every forking group fetch-modify consistent; (2) for every client c some forking group contains every op by c; (3) for any op O, nodes whose groups contain O include a common ancestor n and all descendants of n; (4) common operations ordered the same in all groups; (5) every op in a node's group occurred in the parent's group or happened after every op in the parent's group.
- Def 6 Fork consistent: the file system always guarantees a forking tree exists on completed operations.
- Example: c1 modifies f (M), c2 then fetches an older version (F): M and F go into new groups G1 and G2; c1 and c2 can never again see each other's operations; no later ops by others can join G0. *(p.4)*

### Protocol correctness theorem (4.1) *(pp.4-5)*
A set of completed operations is fork consistent if there is a partial order < with: (1) every two distinct operations of a single client are ordered; (2) for any op q, {o | o <= q} is totally ordered and fetch-modify consistent with < as happens-before.
Proof: take maximal operations X = {x_1...x_k}; chains C_i = {y | y <= x_i} totally ordered; tree nodes are the chains and the greatest common prefix of every pair; parent = longest strict prefix that is a node; verify the five properties. Example maximal chains s1 = A,B,C,D,E,F; s2 = A,B,C,D'',E''; s3 = A,B,C',D',E' yield the tree in Fig. 2 (root A,B; children A,B,C and A,B,C',D',E'; A,B,C has children A,B,C,D,E,F and A,B,C,D'',E'').

### Bare-bones protocol (4.2) *(pp.5-6)*
Assumptions: one client per user; each file writable by one user (no group-writable files); low concurrency. Every signed i-handle has a monotonically increasing version number; users sign their view of others' version numbers too. The server maintains the version structure list (VSL), latest signed structure per user, and sends it to anyone fetching or modifying. User u's update:
1. Obtain exclusive lock on and download the VSL (lock coordinated by server, not trusted). y_v = v's entry.
2. Verify y_u is its current version structure and verify signatures on other entries.
3. Create x initialised from y_u; update i-handle if needed.
4. For each v in VSL, x[v] <- y_v[v].
5. x[u] <- x[u] + 1.
6. Verify all previous VSL entries (incl. old y_u) are totally ordered and x is greater than all (fails if y_v[w] > y_w[w] for some v, w).
7. Sign x and send to server, releasing the lock.
8. Server checks x is totally ordered w.r.t. the other VSL entries (protection against malicious clients).
Issue time = start of step 1; completion = end of last step.
- Worked example: u, v at version 1; u updates to h'_u (u-2 v-1); v updates (u-2 v-2); if the server withholds u's new structure from v, VSL holds y_u = (u-2, v-1) and y_v = (u-1, v-2), which are unordered. *(p.6)*

Results *(pp.6-7)*:
- Proposition one client: all version structures by one obedient client are totally ordered (steps 2-6).
- Fetch-modify lemma: if all clients follow the protocol and O = {o | vs(o) <= q} is totally ordered by <, then O is fetch-modify consistent with < as happens-before, whether or not the server obeys.
- No join lemma: if x and y are unordered, no protocol-following client will sign a structure greater than both. Key step: a client c signs at most one t with t[c] = n, and two structures signed by c are ordered with t < t' iff t[c] < t'[c].
- Bare-bones theorem: following clients achieve fork consistency whether or not the server obeys the protocol.

### Concurrent protocol (4.3) *(pp.7-9)*
- The bare-bones global VSL lock is unacceptable; users declare pending updates with signed update certificates so others can concurrently perform non-conflicting operations. *(p.7)*
- Server maintains a pending version list (PVL) of <update certificate, unsigned version structure l> pairs; l equals u's upcoming structure except i-handle = bottom; removed once the structure enters the VSL. *(p.7)*
- Steps (Fig. 3) *(pp.7-8)*:
  1. u sends an update certificate with its new version number and modified inodes.
  2. Server sends VSL and PVL, plus old version structures still referenced by PVL certificates (needed only when pipelining).
  3. u sanity-checks: all signatures verify; certificate hashes match the same user's signed structures; all structures (signed and unsigned) totally ordered by new <; old structures less than that user's VSL entry; per-client certificate version numbers consecutive starting one above the VSL entry; PVL contains u's step-1 certificate (and none by u with greater versions).
  4. Initialise x from the VSL as in bare-bones; for each client with a certificate, raise that user's version in x to n (highest if multiple); x[u] is the step-1 version.
  5. For every PVL entry <{UPD, v, n, H(y_v), inode-list}, l> except u's own, add triple v-n-V(l) to x; for u's own, add u-x[u]-bottom.
  6. Check y < x for all VSL entries y; for every unsigned l in PVL, check l < x or l = x and it corresponds to the step-1 certificate.
  7. Sign x and send; server checks x totally ordered w.r.t. VSL and PVL.
  8. Modify-fetch conflict: if fetching a file listed in a PVL certificate, wait for the server to send the version structure for the file's latest version and check it matches the unsigned PVL structure.
- Proposition concurrent one client; Concurrent fetch-modify lemma; Concurrent no join lemma (uses that some x' in L or P satisfies x <= x' < z); Concurrent Bare-Bones theorem: fork consistency whether or not the server obeys. *(pp.8-9)*

### Groups and pragmatics (4.4, 4.5) *(p.9)*
- Groups have their own i-table, and every version structure carries a version number per group; details in the full version [12].
- Client failures: a fetch waiting on a never-completing modification could time out with an error and sign the structure it would have signed; forking tree still exists on completed operations except error-returning fetches. Incomplete modifies can be reissued from another client using the certificate's inode-list.
- Malicious clients can write spurious data to files they own but not others'; server refuses order-breaking structures; even with bad clients colluding with a bad server, completed operations by good clients on files no bad client can write remain fork consistent.
- Multiple clients per user handled like users within groups; optimisation: non-signer users need only the version of one client (the one that made that user's most recent modification); clients can eventually drop out after logout.
- Bandwidth: server can send only version structures new since the client's last operation rather than the full VSL.

## Figures of Interest
- **Fig 1 (p.3):** SUNDR virtual inode: metadata, H(B0), size, H(B1), size, ..., H(H(B7),...), size pointing to an indirect block with H(B7), H(B8).
- **Fig 2 (p.5):** forking tree from three maximal chains.
- **Fig 3 (p.8):** concurrent bare-bones protocol message flow (update certificate; server sends VSL + PVL; client computes and sends version structure; server puts it in VSL).

## Results Summary
Both protocols are proven fork consistent whether or not the server follows the protocol. The only attack not immediately detectable is to create an exact replica and partition users so each group sees one replica and the groups' operations are entirely concealed; even this is revealed by out-of-band communication (simple pinging protocol, trusted version-verification server, informal human communication). *(pp.9-10)*

## Limitations
- Ideal immediate detection is not achievable; fork consistency is a deliberate weakening. *(p.1)*
- Partitioning attacks are detected only via out-of-band communication. *(pp.9-10)*
- No data secrecy in the described system. *(p.1)*
- Key management out of scope. *(p.2)*
- Bare-bones protocol serializes all updates with a global lock. *(p.7)*
- Group extension and multi-client optimisations deferred to the full version. *(p.9)*
- In the concurrent protocol a fetch may wait forever on a failed modification unless a timeout/error is added. *(p.9)*
- Every client needs a small amount of persistent storage for version information about the last message it signed. *(p.1)*
- Assumes signatures can be computed faster than network round trips. *(p.1)*

## Arguments Against Prior Work
- OceanStore: weak consistency and security guarantees. *(p.2)*
- Swallow: client-side encryption for access control but cannot grant read-only access; an attacker with read access controlling network or server can substitute arbitrary data for any version. *(p.2)*
- CFS (Blaze): no sharing between users, no freshness or integrity guarantee. *(p.2)*
- Cepheus: trusts the server for integrity of read-shared data. *(p.2)*
- SNAD: signatures for integrity but no freshness guarantee. *(p.2)*
- PFS: integrity on an untrusted disk but really a local file system; no simultaneous multi-client access. *(p.2)*
- BFS: needs more than 2/3 uncompromised replicas; SUNDR needs no replication and trusts only the user's client; with replication only one replica need be honest; different freshness guarantees. *(p.2)*
- P2P systems (xFS, Farsite, Chord, Pastry, CFS on DHTs) could benefit; SUNDR is "the first to implement anything resembling traditional file system semantics without trusting the storage infrastructure". *(p.2)*

## Design Rationale
- Users sign their own updates so neither server nor other users can forge them; private keys stay off the server. *(p.1)*
- Users sign not only their own version number but their view of everyone else's, making withheld updates produce permanently unordered structures. *(p.5)*
- Server performs its own ordering check as protection against malicious clients, but correctness does not depend on the server. *(p.6)*
- Hash trees (Merkle) to verify a block without touching the whole file system, as in SFSRO. *(p.2, p.3)*
- Update certificates allow concurrency without a global lock; triples with V(x) record pending operations so the order stays well defined. *(p.7)*
- Concurrent operations can be piggybacked into one pair of signed messages to reduce signatures on loaded clients. *(p.2)*

## Testable Properties
- All version structures created by one obedient client are totally ordered. *(p.6, p.8)*
- A client signs at most one version structure t with t[c] = n; two structures by the same client are ordered and t < t' iff t[c] < t'[c]. *(p.6)*
- If the server withholds one user's update from another, their version structures become unordered (e.g. (u-2, v-1) vs (u-1, v-2)). *(p.6)*
- No join: once x and y are unordered, no obedient client signs anything greater than both. *(p.6, p.9)*
- <= on extended version structures is transitive. *(p.7)*
- A set of operations admitting a partial order meeting the two conditions of the protocol correctness theorem is fork consistent. *(p.4)*
- Fork consistency holds whether or not the server obeys the protocol (both protocols). *(p.7, p.9)*
- Opening or closing a modified file costs two client signatures and one round trip. *(pp.1-2)*

## Relevance to Project
propstore federates git-backed repositories whose hosts need not be trusted. Fork consistency is the precise guarantee available when a storage peer can show different users different histories: signed version vectors (each party signing its view of every other party's version) make equivocation permanently detectable on the next contact, and out-of-band gossip of heads exposes partitions. This complements Crosby-Wallach and RFC 6962 (which prove append-only growth of one log) with a multi-writer setting closer to multiple authors pushing to a shared store, and matches propstore's stance of recording divergence rather than collapsing it.

## Open Questions
- [ ] Group-writable files and multi-client optimisations are only sketched; details in TR2002-826 [12].
- [ ] How SUNDR's version vectors scale with many users is not analysed here.

## Related Work Worth Reading
- [12] Mazières and Shasha, TR2002-826 (full version with group protocol and proofs).
- [9] Fu, Kaashoek, Mazières, SFSRO (hash-tree read-only file system).
- [5] Castro and Liskov, Practical Byzantine Fault Tolerance (BFS).
- [13] Merkle, hash trees.
- [11] Mazières et al., SFS (self-certifying pathnames).
- [10] Maheshwari and Vingralek, TDB on untrusted storage.

## Collection Cross-References

### Already in Collection
- (none)

### New Leads (Not Yet in Collection)
- Castro and Liskov (1999) - "Practical byzantine fault tolerance" - BFS, the replicated alternative to trusting one server
- Fu, Kaashoek and Mazières (2000) - "Fast and secure distributed read-only file system" - SFSRO, hash-tree read-only file system
- Merkle - "A digital signature based on a conventional encryption function" - hash trees
- Maheshwari and Vingralek (2000) - "How to build a trusted database system on untrusted storage" - TDB
- Mazières, Kaminsky, Kaashoek and Witchel (1999) - "Separating key management from file system security" - SFS self-certifying pathnames

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found; [Efficient Data Structures for Tamper-Evident Logging](../Crosby_2009_EfficientDataStructuresTamper-Evident/notes.md) cites the later SUNDR system paper, Li, Krohn, Mazières and Shasha 2004, not this one)

### Conceptual Links (not citation-based)
- [Time, Clocks, and the Ordering of Events in a Distributed System](../Lamport_1978_TimeClocksOrderingEvents/notes.md) - Strong. The *happens before* partial order in Def 3 (Orderable) and the componentwise order on version structures (Def 10) are the happened-before relation and a vector-valued relative of Lamport's logical clocks. Lamport assumes honest processes and extends happened-before to one total order by tie-breaking; this paper drops that trust and proves a forking tree of per-group orders exists instead.
- [Certificate Transparency](../Laurie_2013_CertificateTransparency/notes.md) - Strong. RFC 6962's log can present conflicting views to different clients, the single-log analogue of a forking server; signed tree heads plus client gossip make that detectable, as signed version structures plus out-of-band communication do here. Neither specifies the gossip channel.
- [Efficient Data Structures for Tamper-Evident Logging](../Crosby_2009_EfficientDataStructuresTamper-Evident/notes.md) - Strong. Crosby and Wallach's history tree lets an untrusted logger's inconsistent histories be caught by incremental proofs between signed commitments plus gossip; fork consistency is the multi-writer counterpart, where the untrusted party is a file server and the evidence is signed version structures. Their notes list the later SUNDR system among version-vector designs that rely on trusted clients signing updates.
