# Proposal: Identity Architecture for Propstore

**Date:** 2026-04-03
**Status:** Proposed
**Grounded in:** local codebase, mergeability investigation, and rereads from actual page PNGs for Juty 2020, Wilkinson 2016, Kuhn 2014/2015/2017, Raad 2019, and Groth 2010

---

## Problem

Propstore currently treats raw local IDs as if they were enough semantic identity.

That is not workable for:

- independently built researcher repos
- repeated imports of paper corpora
- later reconciliation of semantically same but separately minted claims
- safe non-committing merge behavior

The failure mode is already visible in the repo:

- many imported papers use local IDs like `claim1`, `claim2`, ...
- current merge logic keys primarily on raw `claim_id`
- unrelated claims collide
- same-semantic claims with different IDs do not meet at all

This proposal defines a literature-backed identity model that separates:

1. durable object identity
2. source-facing logical identity
3. immutable content/version identity
4. explicit equivalence and update relations

---

## Literature Verdict

### Juty 2020 + Wilkinson 2016

From the actual reread:

- Juty page 2 says findable digital objects must be uniquely specifiable, locatable by a retrieval protocol, and paired with descriptive metadata.
- Wilkinson Box 2 states FAIR F1 and F3: data and metadata need globally unique persistent identifiers, and metadata must explicitly include the identifier of the thing described.

Design consequence:

- propstore needs persistent outward-facing identifiers, not just accidental local row names
- identifiers must be attached to metadata and resolvable through a stable lookup surface

### Kuhn 2014 / 2015

From the actual reread:

- trusty URIs embed artifact codes in URIs
- any content change yields a new identifier
- they are ideal for verification, immutability, and reference-tree integrity

Design consequence:

- content hashes are excellent version or content identifiers
- they are not enough as the only long-lived logical identity for evolving claims

### Kuhn 2017

From the actual reread:

- the paper explicitly separates **fingerprints** from **topics**
- fingerprints are content-based
- topics persist across updates of the same conceptual item

Design consequence:

- propstore should explicitly separate stable object/topic identity from content/version identity
- this is the cleanest literature-backed justification for a multi-layer ID model here

### Raad 2019

From the actual reread:

- `owl:sameAs` is too strong for many real uses
- contextual identity is often what people actually mean
- premature strong identity creates large error propagation

Design consequence:

- propstore should not collapse cross-source identity at ingest time by default
- equivalence should be explicit, weaker, and often context- or policy-sensitive

### Groth 2010

From the actual reread:

- statements are first-class, uniquely identifiable objects
- annotations and provenance are attached to those objects
- S-Evidence aggregates multiple nanopublications about the same statement

Design consequence:

- claims in propstore should be treated as first-class identifiable objects, not anonymous YAML rows
- multiple source assertions about the same underlying statement should aggregate through relations, not row overwrite

---

## Proposal

Propstore should adopt four identity surfaces.

This is a **clean-break proposal**.

It explicitly rejects:

- long-lived migration layers
- mixed old/new identity semantics
- compatibility adapters that preserve raw-local-ID behavior
- any production path where old identity logic and new identity logic coexist

The intended implementation shape is:

- one schema cutover
- one new canonical repository bootstrap
- one import cutover
- one merge cutover
- one deletion of the old repository

After the cutover, the old identity model and the old repository are gone.

### 1. `artifact_id`

Stable identity of the stored propstore object.

Properties:

- globally unique inside propstore
- durable across branching, import, and merge
- never reused
- opaque

Operational form:

- UUIDv7 or ULID-backed URI-like identifier
- examples:
  - `ps:claim:01JZ...`
  - `ps:concept:01JZ...`

This is the primary key for first-class stored objects.

### 2. `logical_id`

Namespaced source-facing identity for the object as expressed by some source or source family.

Properties:

- human-readable enough to inspect
- source- or namespace-scoped
- may be absent for some objects created internally
- may collide only if namespace collides

Examples:

- `Aarts_2015:claim1`
- `repoA:claim1`
- `Crossref:10.1038/foo:claim3`
- `conceptwiki:pico_embeddings`

This is the immediate fix for current merge/import failures.

### 3. `version_id`

Immutable content/version identity for a particular serialized state of the object.

Properties:

- changes whenever content changes
- suitable for verification and deduplication
- may later adopt trusty-URI style encoding if externalized

Examples:

- content hash over canonical claim payload
- git/blob/tree based derivative
- `trusty_id` as a future specialization

This is where Kuhn 2014/2015 belongs.

### 4. Identity Relations

Explicit links between objects that should not be collapsed into one ID.

Initial set:

- `same_as_candidate`
- `same_as_in_context`
- `supersedes`
- `derived_from`
- `version_of`
- `duplicate_artifact_of`
- `source_asserts_same_as`

This is where Raad belongs.

---

## What Gets `artifact_id`

Every durable, first-class, mergeable, referenceable object.

Required:

- claims
- concepts
- justifications / rules
- stance records
- contexts
- worldlines
- source/paper records

Not required:

- sidecar/cache rows
- embeddings
- compiled projections
- merge reports
- render outputs

---

## Storage Contract

Each first-class object should carry:

- `artifact_id`
- `kind`
- `logical_ids`
- `version_id`
- `provenance`
- optional identity/equivalence links

For claims specifically:

```yaml
- artifact_id: ps:claim:01JZ...
  logical_ids:
    - namespace: Aarts_2015
      value: claim1
  version_id: sha256:...
  type: observation
  statement: ...
  provenance:
    paper: Aarts_2015_EstimatingReproducibilityPsychologicalScience
    page: 3
```

Notes:

- `logical_ids` is a list, not a scalar, because imports and later reconciliation may attach multiple known logical handles
- `artifact_id` is the storage anchor
- `version_id` is the immutable content snapshot anchor

---

## Merge Rules

### Rule 1: Same `artifact_id`

Interpretation:

- same propstore object lineage

Action:

- merge as revisions/versions of the same object
- compare `version_id`
- preserve provenance and branch history

### Rule 2: Different `artifact_id`, same namespaced `logical_id`

Interpretation:

- same source-facing object identity, independently imported or recreated

Action:

- do not silently collapse on ingest
- treat as a strong identity candidate
- optionally reconcile to one canonical surviving artifact later
- maintain trace that two artifacts shared the same logical handle

### Rule 3: Different `artifact_id`, different `logical_id`, semantically similar

Interpretation:

- possible same statement, not established identity

Action:

- keep separate objects
- emit `same_as_candidate` or related relation
- let render/query/policy decide whether to fuse, compare, or keep apart

### Rule 4: Different `artifact_id`, contradictory content

Interpretation:

- disagreement, not identity failure

Action:

- preserve both
- attach stance/conflict structure
- do not rewrite history into one winner

---

## Import Rules

`import-repo` should change from raw overlay to identity-aware import.

### Required cutover behavior

1. Rewrite bare claim IDs into namespaced `logical_id`s on import.
2. Mint `artifact_id` for every imported first-class object.
3. Mint `version_id` from canonical content.
4. Rewrite all internal references to use `artifact_id` targets or resolvable logical references.
5. Import as a true semantic snapshot, including deletes.

### Namespace preference order

1. stable paper slug if known
2. source repo slug
3. explicit external namespace if the source already provides one

Example:

- raw imported `claim1` from `Aarts_2015...` becomes logical ID `Aarts_2015:claim1`
- stored object gets fresh `artifact_id`

---

## Reference Rules

Cross-object references should stop pointing only at unstable local IDs.

Preferred form:

- primary target by `artifact_id`
- optional display or source reference by `logical_id`

For new canonical repository content:

- imported source-local IDs become namespaced entries in `logical_ids`
- internal links are normalized as objects enter the new repository

This is required to avoid the current failure where merge-time renaming breaks stance targets.

---

## Resolution and Noncommitment

This proposal is intentionally non-collapsing.

What it forbids:

- treating raw local IDs as universal identity
- using content hash alone as the only identity
- using `same_as`-strength assertions as default ingestion behavior

What it enables:

- branch-safe object identity
- safe import of independently built repos
- later reconciliation without data loss
- policy-sensitive render-time equivalence

Raad and propstore's noncommitment discipline point to the same operational rule:

- identity collapse should be explicit and reviewable
- candidate identity should be representable without irreversible fusion

---

## Replacement Plan

This plan is executed as greenfield replacement, not in-place conversion.

### Cutover 1: Schema Replacement

- claims, concepts, and other first-class objects gain `artifact_id`, `logical_ids`, and `version_id`
- code that assumes raw local `id` as the storage key is removed
- any schema path that depends on old identity semantics is deleted

### Cutover 2: New Canonical Repository Bootstrap

- create a new canonical repository under the new identity schema
- nothing from the old repository is treated as canonical after this point
- the old repository is retained only until the new one is validated, then deleted

### Cutover 3: Import Replacement

- `import-repo` stops copying raw local IDs as semantic identity
- import always mints `artifact_id`
- import always derives namespaced `logical_id`
- import always rewrites references
- import always performs true snapshot replacement, including deletes

### Cutover 4: Merge Replacement

- merge logic stops keying on raw local `id`
- merge logic operates on `artifact_id`, `logical_id`, `version_id`, and explicit identity relations
- the old merge behavior is deleted rather than retained behind a flag

### Cutover 5: Relation Normalization

- stance and related reference surfaces normalize around durable object identity
- if a relation needs first-class persistence, it gets first-class identity too
- old local-ID-targeted relation behavior is removed

### Cutover 6: Externalization

- once the storage cutover is complete, resolvable external object URIs can be exposed
- immutable external verification IDs can be added on top of `version_id`

### Cutover 7: Old Repository Deletion

- after the new canonical repository is validated, delete the old repository
- there is no read bridge from old repository identity semantics into the new one

---

## Success Criteria

This proposal succeeds if:

1. independent researcher repos can be imported without local-ID collisions
2. same-semantic but differently named objects remain distinct until reconciled
3. same-source logical identities can be matched without raw row overwrite
4. merge logic works over durable IDs rather than accidental YAML-local IDs
5. provenance and references survive merge/import without dangling targets

---

## Immediate Recommendation

Adopt this as the plan constraint:

- `artifact_id` for every first-class object
- namespaced `logical_id` for every imported claim/concept that already has a source-local identity
- `version_id` for immutable content state
- explicit equivalence relations instead of eager cross-source collapse
- zero compatibility layer

If we do only one thing first, it should be:

1. claims get `artifact_id`
2. import rewrites bare `claimN` into namespaced `logical_id`
3. merge stops keying on raw local `id`

That is the smallest change that actually addresses the current mergeability failures.

---

## References

- Juty et al. (2020), *Unique, Persistent, Resolvable: Identifiers as the Foundation of FAIR*
- Wilkinson et al. (2016), *The FAIR Guiding Principles for scientific data management and stewardship*
- Kuhn and Dumontier (2014), *Trusty URIs: Verifiable, Immutable, and Permanent Digital Artifacts for Linked Data*
- Kuhn and Dumontier (2015), *Making Digital Artifacts on the Web Verifiable and Reliable*
- Kuhn et al. (2017), *Reliable Granular References to Changing Linked Data*
- Raad et al. (2019), *The sameAs Problem: A Survey on Identity Management in the Web of Data*
- Groth et al. (2010), *The Anatomy of a Nanopublication*
