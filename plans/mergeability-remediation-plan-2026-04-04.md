# Mergeability Remediation Plan

Date: 2026-04-04
Status: proposed
Scope: independent-repo mergeability for claims, concepts, stances, and paper-project workflows

## Verdict

The current repo is strong enough to support:

- deterministic convergence when two sources share the same paper identity and the same local claim handles
- explicit preservation of conflicts and regime splits at the claim layer
- committed-snapshot import as a reproducible ingestion primitive

The current repo is not yet strong enough to support:

- clean merging of independently built repositories in the general case
- semantically safe concept convergence across independent repos
- merged repositories that remain first-class semantic inputs for later merges
- trustworthy round-trip mergeability for `research-papers-plugin` cross-paper stance and richer graph artifacts

This plan is therefore a hardening and closure plan, not a ground-up redesign.

## Paper Pass

I reread the following local papers from page PNGs while building this plan:

- [Juty_2020_UniquePersistentResolvableIdentifiers](/C:/Users/Q/code/propstore/papers/Juty_2020_UniquePersistentResolvableIdentifiers)
- [Wilkinson_2016_FAIRGuidingPrinciplesScientific](/C:/Users/Q/code/propstore/papers/Wilkinson_2016_FAIRGuidingPrinciplesScientific)
- [Kuhn_2017_ReliableGranularReferences](/C:/Users/Q/code/propstore/papers/Kuhn_2017_ReliableGranularReferences)
- [Kuhn_2014_TrustyURIs](/C:/Users/Q/code/propstore/papers/Kuhn_2014_TrustyURIs)
- [Raad_2019_SameAsProblemSurvey](/C:/Users/Q/code/propstore/papers/Raad_2019_SameAsProblemSurvey)
- [Groth_2010_AnatomyNanopublication](/C:/Users/Q/code/propstore/papers/Groth_2010_AnatomyNanopublication)
- [Konieczny_2002_MergingInformationUnderConstraints](/C:/Users/Q/code/propstore/papers/Konieczny_2002_MergingInformationUnderConstraints)
- [Coste-Marquis_2007_MergingDung'sArgumentationSystems](/C:/Users/Q/code/propstore/papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems)
- [Halpin_2010_OwlSameAsIsntSame](/C:/Users/Q/code/propstore/papers/Halpin_2010_OwlSameAsIsntSame)
- [Melo_2013_NotQuiteSameIdentity](/C:/Users/Q/code/propstore/papers/Melo_2013_NotQuiteSameIdentity)
- [Beek_2018_SameAs.ccClosure500MOwl](/C:/Users/Q/code/propstore/papers/Beek_2018_SameAs.ccClosure500MOwl)

Targeted reread takeaways:

- Juty p.2: FAIR identifiers must be uniquely specifiable, locatable via a retrieval protocol, and paired with descriptive metadata. Repo-name fallback identity is therefore too weak for canonical object identity.
- Wilkinson Box 2 p.4: F1 and F3 require globally unique persistent identifiers and explicit metadata linkage from metadata to the identified object. This supports first-class object identifiers plus explicit identity metadata rather than implicit local row names.
- Kuhn 2017 p.5-6: fingerprints and topics are distinct. Content hashes are for immutable content identity; topic identity persists across content change. This directly supports separating `version_id` from long-lived logical/object identity.
- Kuhn 2014 p.2: cryptographic IDs are excellent for verification and immutability, but they are not sufficient as the only identity surface for evolving objects.
- Raad p.1-3: `owl:sameAs`-strength collapse is routinely too strong; contextual identity and weaker relations are needed. This argues against eager storage-time collapse across independent repos.
- Groth p.52-54: statements should be first-class identifiable objects with provenance and attribution attached, and multiple nanopublications can refer to the same statement. This supports preserving multiple source assertions about the same proposition without overwrite.
- Konieczny p.777: IC0-IC8 constrain merge operators, but they do not justify throwing away divergent inputs from the stored semantic surface.
- Coste-Marquis 2007 p.736, p.739: consensual expansion plus edit-distance-based AF merge is already enough merge theory for the current system; the missing pieces are identity and closure, not another argumentation merge formalism.
- Halpin 2010 p.310-312: `owl:sameAs` is too strong as the default relation, and the practically useful replacement is not one weaker predicate but a family of weaker relations with different transitivity/symmetry behavior. In particular, a claim-level identity proposal can be non-transitive.
- Melo 2013 p.1093-1094: identity management needs explicit distinctness constraints and a repair operation, not just better positive matching. The right formal picture is: links create connected components, constraints forbid some co-membership, and repair removes a minimal bad cut rather than blindly propagating identity.
- Beek 2018 p.74-75: closure over identity links is computationally easy with union-find but semantically dangerous when the wrong relation is closed. Identity sets can explode to absurd size, so closure must be restricted to trusted transitive relations and never applied indiscriminately.

## Do We Need More Papers?

For the merge operator core: no immediate gap.

The repo already has enough theory for:

- IC merging under constraints
- AF merging via PAFs, consensual expansion, and edit distance
- persistent identifiers, content verification, and statement-level provenance
- caution against overly strong identity collapse
- graded / weaker-than-global identity
- graph-based identity repair and closure-risk evidence

The previously missing identity papers are now in hand. No further paper is required before coding the next slice.

What changed after reading them:

1. The plan now needs an explicit identity-relation layer, not just `semantic_candidates`.
2. The plan now needs explicit distinctness constraints and repair, not just candidate linkage.
3. The plan must distinguish relations that are safe to close transitively from relations that are not.

## Current Failure Surfaces

### 1. Claim convergence depends on shared paper-local handles

Observed locally:

- same paper + same local IDs converges
- same paper + different local IDs does not converge; it only produces semantic candidates
- missing `source.paper` falls back to repo-scoped identity, which preserves coexistence but prevents convergence

Code surfaces:

- [propstore/identity.py](/C:/Users/Q/code/propstore/propstore/identity.py)
- [propstore/repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)
- [propstore/repo/merge_classifier.py](/C:/Users/Q/code/propstore/propstore/repo/merge_classifier.py)
- [scripts/mergeability_probe.py](/C:/Users/Q/code/propstore/scripts/mergeability_probe.py)
- [scripts/mergeability_probe_extended.py](/C:/Users/Q/code/propstore/scripts/mergeability_probe_extended.py)

Implication:

- local claim numbering is currently part of semantic convergence
- this is acceptable for within-paper continuity
- this is not acceptable as the only path for cross-repo convergence

### 2. Concept identity is not repo-safe

Imported concepts derive `artifact_id` from a normalized local handle under a shared propstore namespace.

Implication:

- two independent repos can accidentally collapse distinct concepts if they used the same local concept handle
- this is the most serious remaining identity bug

Primary code surface:

- [propstore/repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)

### 3. Divergent merges are not semantically closed

When two branches contain different versions of the same claim artifact, the merge commit omits them from `claims/merged.yaml` and preserves them only in `merge/manifest.yaml`.

Implication:

- the merged repo is not itself a full semantic input for later merge/import/query layers
- disagreement is preserved as metadata, but not as normal first-class claim data

Primary code surface:

- [propstore/repo/merge_commit.py](/C:/Users/Q/code/propstore/propstore/repo/merge_commit.py)

### 4. Non-claim semantic files are overwrite-merged

Current merge commit behavior copies right-hand non-claim files and then overwrites with left-hand non-claim files on path collision.

Implication:

- `concepts/`, `stances/`, `worldlines/`, and related first-class files do not yet have a semantic merge path

Primary code surface:

- [propstore/repo/merge_commit.py](/C:/Users/Q/code/propstore/propstore/repo/merge_commit.py)

### 5. Plugin boundary is only partially mergeable

`pks import-papers` imports `claims.yaml`, but not richer paper-project artifacts like `justifications.yaml`. The plugin also documents cross-paper stance targets using `PaperDir:claimN`, while propstore validation expects existing target claim IDs after normalization.

Implication:

- independent paper projects can converge on imported claims
- they cannot yet reliably converge on richer cross-paper graph structure

Primary surfaces:

- [propstore/cli/compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)
- [propstore/validate_claims.py](/C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [extract-stances/SKILL.md](/C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/extract-stances/SKILL.md)

### 6. There is no explicit negative identity surface

The current repo can express candidate sameness informally, but it has no first-class way to say:

- these two artifacts are probably the same in a limited context
- these two artifacts are definitely distinct and must never collapse
- this identity proposal came from a source assertion and is not globally trusted

Implication:

- the system has no principled brake on closure
- reconciliation cannot be staged safely

Literature pressure:

- Halpin: weaker, typed identity relations are necessary
- Melo: distinctness constraints are first-class
- Beek: unguarded closure produces pathological equivalence sets

## Plan

### Phase 0: Identity Semantics Contract

Goal:

- define which identity relations exist, which are transitive, and which are only reviewable proposals

Required changes:

1. Introduce explicit identity-relation types with semantics:
   - `same_individual`
   - `claims_identical`
   - `same_topic`
   - `same_source_handle`
   - `same_version_of`
   - `distinct_from`
   - `distinct_in_context`
2. Mark which relations are allowed in closure:
   - `same_individual`: closure-eligible
   - `claims_identical`: not closure-eligible by default
   - `same_topic`: never closure-eligible
   - `distinct_*`: hard constraints against collapse
3. Add a short repo-level contract documenting these semantics.

Acceptance tests:

- transitive closure over `same_individual` works
- no closure is applied across `claims_identical`
- `distinct_from` blocks reconciliation and merge collapse

### Phase 1: Identity Contract Hardening

Goal:

- make object identity safe across independently built repos

Required changes:

1. Remove repo-name fallback as a canonical identity basis for imported claims when a stronger source identity exists.
2. Require imported claims to preserve:
   - `artifact_id`
   - one or more `logical_ids`
   - `version_id`
   - provenance pointing to paper/source
3. Make concept import repo-safe:
   - concepts must not derive global artifact identity solely from a local handle in the shared `propstore` namespace
   - concept identity should follow the same layered model as claims: durable object identity, namespaced logical identity, immutable version identity
4. Preserve source assertions separately from approved identity:
   - source-imported sameness proposals become relation objects, not immediate collapse
5. Add first-class identity relations for claims and concepts using the Phase 0 vocabulary.

Acceptance tests:

- two independent repos using the same local concept handle for different meanings do not collapse
- two repos importing the same paper with the same claim handles do converge
- two repos importing semantically same claims with different local handles remain distinct but receive explicit typed identity relations
- two repos importing same-named but meaningfully different concepts stay distinct if a distinctness constraint is present

### Phase 2: Distinctness Constraints And Repair

Goal:

- prevent and repair incorrect collapse before transitive closure can spread it

Required changes:

1. Add first-class distinctness constraints for claims and concepts.
2. Seed constraints from strong local invariants where available:
   - same-repo unique-name assumptions where appropriate
   - incompatible concept domains
   - incompatible source-local object identities
   - explicit human review decisions
3. Build a repair surface over the identity graph:
   - detect violations where a closure-eligible identity path connects nodes forbidden by distinctness constraints
   - compute minimal cuts or at least report candidate cuts
4. Keep this as a reviewable operation, not an invisible mutation.

Acceptance tests:

- a bad identity link creating a forbidden collapse is detected
- repairing one bad link can clear multiple violations
- closure over repaired graph no longer violates distinctness constraints

### Phase 3: Merge Closure

Goal:

- make merged repos first-class semantic repos rather than partial projections

Required changes:

1. Divergent alternatives must remain present on the normal semantic surface after merge.
2. `merge/manifest.yaml` can remain as provenance/reporting, but not as the only location of unresolved alternatives.
3. Materialized merge output should represent unresolved alternatives as first-class stored objects with explicit branch/source provenance.
4. Queries and later merges must see those objects through the same loaders used for ordinary claims.

Acceptance tests:

- merge a conflict, then merge the result with a third branch; unresolved alternatives are still visible and classifiable
- `load_claim_files()` over the merged tree sees divergent alternatives without needing manifest-only logic

5. Merge-time identity closure may only use closure-eligible relations from Phase 0.

Acceptance tests:

- a non-transitive identity proposal does not cause merged alternatives to disappear
- only approved closure-eligible identity links can collapse alternatives

### Phase 4: Non-Claim Semantic Merge

Goal:

- stop path-overwrite behavior for first-class semantic files

Required changes:

1. Add merge logic for:
   - `concepts/`
   - `stances/`
   - `contexts/`
   - `worldlines/`
2. Treat overwrite as an error or explicit last-resort policy, not the default silent behavior.
3. Normalize cross-object references so merged outputs remain referentially intact.

Acceptance tests:

- same-path concept files from two repos do not silently overwrite
- same-path stance files with distinct source artifacts preserve both sources or merge cleanly

### Phase 5: Research-Papers Boundary Repair

Goal:

- make independent paper-project repos realistically mergeable

Required changes:

1. Align `extract-stances` target contract with propstore import/validation.
2. Support imported richer graph artifacts, starting with `justifications.yaml` if retained as a first-class paper-project output.
3. Decide one canonical identity source for paper claims:
   - paper dir + local claim handle for source-facing identity
   - propstore artifact identity for storage identity
4. Add an explicit reconciliation pass for semantically duplicated claims created by independent extraction ordering differences.
5. Add a path for paper-project imports to emit typed identity proposals instead of assuming immediate cross-paper target resolution.

Acceptance tests:

- two paper repos containing 4 papers, with 2 shared and 2 distinct, import and merge without losing cross-paper stance structure
- same paper extracted twice with different claim numbering yields typed identity proposals plus a reconciliation workflow, not silent duplication

### Phase 6: Reconciliation Workflow

Goal:

- provide a principled operator for moving from coexistence to approved convergence

Required changes:

1. Add a reviewable reconciliation surface over `semantic_candidates` and the new identity relations.
2. Support explicit user-approved promotion:
   - `claims_identical` -> `same_individual`
   - `same_topic` remains weaker and non-collapsing
3. Support explicit rejection:
   - promote to `distinct_from`
4. Record reconciliation decisions as first-class semantic state, not ad hoc file rewrites.

Acceptance tests:

- a semantic-candidate pair can be linked as contextual same-identity without forcing global collapse
- a rejected candidate pair becomes `distinct_from` and stays non-collapsing on later import
- later imports respect prior reconciliation decisions and distinctness constraints

## Recommended Immediate Coding Order

1. Implement Phase 0 identity semantics contract.
2. Fix concept identity import under the new contract.
3. Add distinctness constraints and a first repair detector.
4. Fix merge closure for divergent claims under closure-eligible relations only.
5. Fix stance/import contract at the `research-papers-plugin` boundary.
6. Add explicit reconciliation state and promotion/rejection workflow.

This order attacks the actual blockers in the order they most threaten independent-repo mergeability.

## Experiment Suite To Keep Running

Keep and expand these scenarios:

1. Two independently built repos, same paper, same claim handles, same content.
2. Two independently built repos, same paper, same claim handles, conflicting values.
3. Two independently built repos, same paper, different claim handles, same semantics.
4. Two repos with missing `source.paper`.
5. Fork, then each side adds:
   - one same new paper
   - one different new paper
6. Two repos with concept-handle collision but different concept definitions.
7. Two paper-project repos with cross-paper stances through `import-papers`.

Local probe surfaces:

- [scripts/mergeability_probe.py](/C:/Users/Q/code/propstore/scripts/mergeability_probe.py)
- [scripts/mergeability_probe_extended.py](/C:/Users/Q/code/propstore/scripts/mergeability_probe_extended.py)

## Test Status

Focused merge/import test run passed:

- [20260404-012730-mergeability.txt](/C:/Users/Q/code/propstore/logs/test-runs/20260404-012730-mergeability.txt)

That means the current surface is internally consistent. The plan above is about closing the remaining architectural gaps, not stabilizing a broken implementation.
