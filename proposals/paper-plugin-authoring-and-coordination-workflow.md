# Source-Oriented Knowledge Architecture: Unifying Extraction, Identification, Verification, and Trust

**Date:** 2026-04-04  
**Status:** Draft replacement for the earlier paper-plugin authoring proposal

## Problem

The current `propstore` + `research-papers-plugin` split has seven concrete failures.

1. Agents lack a shared, structured space to converge on concept names, aliases, and collisions.
2. Canonical `knowledge/concepts/*.yaml` is asked to do both coordination work and accepted-registry work.
3. Paper-local extraction becomes blocked on premature global naming decisions.
4. The import bridge is unnecessary impedance. RPP writes `claims.yaml` and related artifacts, then `pks import-papers` in `propstore/cli/compiler_cmds.py` and `propstore/repo/repo_import.py` translates them into propstore’s model. Every contract change must be made twice.
5. `p_arg_from_claim()` in `propstore/praf.py` returns `Opinion.dogmatic_true()` for every claim. PrAF uncertainty is therefore mostly cosmetic.
6. The default base rate `a=0.5` in `propstore/opinion.py` is not honest ignorance when replication-rate evidence is available and could be represented as ordinary claims.
7. The system is coupled to “papers” as a core concept. The branch model in `propstore/repo/branch.py`, the plugin directory structure, and the import surface all assume academic papers even though the core data model in `docs/data-model.md` is source-agnostic.

The existing codebase already contains most of the formal machinery this architecture needs:

- repository truth in `propstore/repo/git_backend.py`
- formal merge objects in `propstore/repo/merge_framework.py`, `propstore/repo/merge_classifier.py`, and `propstore/repo/paf_merge.py`
- exact support tracking in `propstore/world/atms.py`
- subjective logic in `propstore/opinion.py`
- probabilistic argumentation in `propstore/praf.py`
- parameterization reachability in `propstore/parameterization_groups.py`
- durable proposal branches in `propstore/proposals.py`

The missing work is connection and rescoping, not a new reasoning substrate.

**Touches existing:** `docs/integration.md`, `docs/git-backend.md`, `docs/semantic-merge.md`, `propstore/cli/compiler_cmds.py`, `propstore/repo/repo_import.py`, `propstore/praf.py`, `propstore/repo/branch.py`, `../research-papers-plugin/plugins/research-papers/skills/register-concepts/SKILL.md`, `../research-papers-plugin/plugins/research-papers/skills/paper-process/SKILL.md`

## Source Abstraction

Replace **paper** as the primary unit with **source**.

A source is a typed body of evidence with:

- origin: where the bytes came from
- extraction: what artifacts were proposed from it
- lifecycle: proposed, accepted, deprecated
- trust: a calibration bundle containing a prior base rate and a source-quality opinion

`academic_paper` becomes one source kind, not the core ontology of the system.

### Source object

```yaml
id: "tag:ctoth@audiom.com,2026:source/Halpin_2010_OwlSameAsIsntSame"
kind: academic_paper
origin:
  type: doi
  value: "10.1007/978-3-642-17746-0_20"
  retrieved: "2026-04-04T12:00:00Z"
  content_ref: "ni:///sha-256;UyaQV-Ev4rdLoHyJJWCi11OHfrYv9E1aGQAlMO2X_-Q"
trust:
  prior_base_rate: 0.62
  quality:
    b: 0.0
    d: 0.0
    u: 1.0
    a: 0.5
  derived_from:
    - "tag:ctoth@audiom.com,2026:claim/Camerer_2018:replication_rate_nature_science_social_science"
    - "tag:ctoth@audiom.com,2026:claim/Ioannidis_2005:ppv_depends_on_power_bias_prestudy_odds"
metadata:
  title: "When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data"
  authors:
    - "Harry Halpin"
    - "Patrick J. Hayes"
  year: 2010
```

### Repository implications

- Add a first-class `Source` record and source loaders in propstore core.
- Add `source/` as a branch kind in `propstore/repo/branch.py`. Keep `paper/` as a migration alias initially.
- Keep `papers/` in the plugin repo as the domain workspace for `academic_paper` sources. Propstore should not own that directory; it should own the git-backed source state.
- Treat plugin-specific metadata as pass-through source metadata. Propstore preserves it but does not interpret it beyond `kind`, `origin`, and trust-calibration selectors.

### Source-local authoring branch

All unresolved source-local artifacts live on `source/<slug>` branches:

- `source.yaml`
- `concepts.yaml`
- `claims.yaml`
- `justifications.yaml`
- `stances.yaml`
- `notes.md`
- `metadata.json`

That keeps unresolved authoring state off `master` while preserving repository centrality from `docs/git-backend.md`.

**Existing and reusable:** `KnowledgeRepo` in `propstore/repo/git_backend.py`, branch metadata in `propstore/repo/branch.py`, proposal branches in `propstore/proposals.py`, structured identifier classification in `../research-papers-plugin/plugins/research-papers/scripts/_paper_id.py`  
**Build:** source schema, source branch kind, source lifecycle commands

## URI and Identification

Three identifier layers are required. They solve different problems and must not be collapsed.

### 1. `tag:` URIs for entity identity

Use `tag:` URIs for sources, concepts, claims, stances, justifications, and contexts.

- globally unique within a configured authority
- human-mintable
- resolution-independent
- compatible with YAML-native tagging culture

Examples:

- `tag:ctoth@audiom.com,2026:source/Halpin_2010_OwlSameAsIsntSame`
- `tag:ctoth@audiom.com,2026:concept/claims_identical`
- `tag:ctoth@audiom.com,2026:claim/Halpin_2010_OwlSameAsIsntSame:claims_identical_not_transitive`

### 2. `ni:` URIs for content integrity

Use `ni:` URIs for source bytes and other raw artifact integrity checks.

- source PDF integrity
- sidecar/worldline rebuild skipping
- re-fetch validation

This standardizes the existing ad hoc SHA-256 usage described in `docs/worldlines.md`.

### 3. Trusty-style artifact codes for knowledge verification

Use artifact codes over canonical semantic content to create a Merkle DAG over the knowledge graph.

For a claim, hash over:

- source `tag:` URI
- source `ni:` content reference
- claim semantic payload
- referenced concept URIs
- referenced justification IDs
- referenced stance target IDs

The first implementation does not need fully externalized trusty URI serialization on day one. It does need a stable `artifact_code()` contract on core entities so semantic verification is independent of YAML layout.

### Implementation surface

- New URI helpers, likely in a dedicated module such as `propstore/uri.py`
- `Source.uri()`, `Claim.uri()`, `Concept.uri()`
- `Source.content_ref()` from bytes
- `artifact_code()` on claim-like entities
- repo config value for the local tagging authority

**Existing and reusable:** `propstore/repo/git_backend.py`, current logical/artifact ID machinery used by `propstore/repo/repo_import.py` and `propstore/identity.py`  
**Build:** standards-based URI layer, semantic artifact-code canonicalization

## Verified Provenance

The system should verify knowledge at five layers.

1. **Storage verification.** Git already provides a Merkle DAG over blobs, trees, and commits via `KnowledgeRepo`.
2. **Content verification.** Artifact codes verify semantic objects independent of serialization.
3. **Origin verification.** `origin.content_ref` verifies the actual source bytes. The current `stamp_provenance.py` already stamps agent, skill, plugin version, and timestamp; keep that and attach it to source commits.
4. **Epistemic verification.** ATMS labels in `propstore/world/atms.py` answer which assumptions support a belief and what interventions would change it.
5. **Temporal verification.** Commit history pins a belief state to a revision, as already modeled in `docs/git-backend.md` and `docs/worldlines.md`.

### Required behavior

`pks verify tree <claim-id>` should:

1. resolve the claim at a commit
2. walk its justification and stance references
3. recompute artifact codes
4. report the first mismatch, if any
5. show source origin verification status if the source bytes are available
6. show the ATMS support label for the current belief

That makes “is this still valid?” a repository query, not an ad hoc operator judgment.

**Existing and reusable:** `propstore/repo/git_backend.py`, `propstore/world/atms.py`, worldline staleness model from `docs/worldlines.md`, `../research-papers-plugin/plugins/research-papers/scripts/stamp_provenance.py`  
**Build:** semantic verification walk, source-origin verification objects, artifact-code storage

## Trust Calibration

### Replace the `dogmatic_true()` shortcut

`p_arg_from_claim()` in `propstore/praf.py` currently returns `Opinion.dogmatic_true()` for all active claims. That defeats the purpose of a probabilistic layer.

The trust contract needs three distinct layers:

1. **source prior base rate**
   A scalar probability derived from calibration claims. This is where replication science enters.
2. **claim-level evidence opinion**
   An opinion built from the claim's own evidence strength when available.
3. **source-quality trust opinion**
   An opinion about the reliability of the source and extraction path, applied as a discount rather than a replacement for the base rate.

`p_arg_from_claim()` should compose these in that order. It should not conflate them into one undifferentiated field called "trust".

### Calibration claims live inside propstore

Replication-rate evidence is ordinary knowledge. It should be represented as normal claims, not hard-coded constants.

```yaml
source:
  id: "tag:ctoth@audiom.com,2026:source/OpenScienceCollaboration_2015_ReproducibilityPsychology"
produced_by:
  agent: "automated-agent"
  skill: "source-add-claim"
  timestamp: "2026-04-04T12:20:00Z"
claims:
  - id: psychology_replication_rate_2015
    type: parameter
    concept: "tag:ctoth@audiom.com,2026:concept/base_replication_rate"
    value: 0.36
    unit: "probability"
    conditions:
      - "domain == 'psychology'"
    provenance:
      page: 649
      section: "Main Results"
```

### Derivation path

Use the existing parameterization system from `docs/parameterization.md` and `propstore/parameterization_groups.py`:

- level 1: field/venue/methodology replication-rate claims
- level 2: modifiers such as pre-registration, sample size, and design type
- level 3: derived source prior base rate

The initial implementation can be simple:

- add concepts for `base_replication_rate`, `sample_size_modifier`, `preregistration_modifier`, `source_trust_base_rate`
- store these as ordinary parameter claims and equations
- derive source prior calibration through `chain_query()`

### Subjective logic contract

- `a` becomes a derived quantity, not a constant
- source prior is represented as `Opinion.vacuous(a=prior_base_rate)`
- claim-level evidence is represented separately, for example by `from_probability(p, n, a=prior_base_rate)`
- source-quality trust is a separate opinion used with `discount(trust, claim_opinion)`
- `u` reflects calibration uncertainty and source-quality uncertainty, not only missing evidence
- if no calibration evidence matches a source, `Opinion.vacuous(a=0.5)` remains the fallback

That fallback finally means “unknown,” not “ignored available evidence.”

### Executable `p_arg_from_claim()` contract

For a claim `c` from source `s`:

1. Resolve `prior_base_rate(s)` by querying calibration claims through the parameterization layer.
2. Build `omega_prior = Opinion.vacuous(a=prior_base_rate(s))`.
3. If `c` has explicit evidence metadata, build `omega_claim = from_probability(p_claim, n_eff, a=prior_base_rate(s))`.
   If not, set `omega_claim = omega_prior`.
4. Resolve `omega_source_quality(s)`.
   Initial implementation may default to `Opinion.vacuous(a=0.5)` unless there is explicit source-quality evidence.
5. Return:
   - `omega_claim` if `omega_source_quality` is vacuous
   - otherwise `discount(omega_source_quality, omega_claim)`

This keeps the semantics separate:

- field replication rates set the base rate
- claim-local evidence sharpens or weakens the claim itself
- source-quality trust discounts that claim evidence when provenance or source quality is questionable

This also gives an implementable staging path:

- phase 1: derive only `prior_base_rate`, leave source-quality vacuous
- phase 2: add source-quality opinions from adjudicated source metadata or integrity failures
- phase 3: add richer claim-local evidence extraction

**Existing and reusable:** `propstore/praf.py`, `propstore/opinion.py`, `docs/probabilistic-argumentation.md`, `docs/subjective-logic.md`, `docs/parameterization.md`, `propstore/parameterization_groups.py`  
**Build:** source calibration lookup, calibration concept set, calibration ingest, claim-to-source trust routing

## Unified CLI Surface

RPP skills should become orchestrators over `pks source *`. They should stop owning ID assignment, validation, import translation, and provenance semantics.

### Source lifecycle commands

```bash
pks source init Halpin_2010_OwlSameAsIsntSame \
  --kind academic_paper \
  --origin-type doi \
  --origin-value 10.1007/978-3-642-17746-0_20

pks source write-notes Halpin_2010_OwlSameAsIsntSame --file papers/Halpin_2010_OwlSameAsIsntSame/notes.md
pks source write-metadata Halpin_2010_OwlSameAsIsntSame --file papers/Halpin_2010_OwlSameAsIsntSame/metadata.json

pks source propose-concept Halpin_2010_OwlSameAsIsntSame \
  --name claims_identical \
  --definition "A weak identity relation between claim assertions." \
  --form structural

pks source add-claim Halpin_2010_OwlSameAsIsntSame --batch papers/Halpin_2010_OwlSameAsIsntSame/claims.yaml
pks source add-justification Halpin_2010_OwlSameAsIsntSame --batch papers/Halpin_2010_OwlSameAsIsntSame/justifications.yaml
pks source add-stance Halpin_2010_OwlSameAsIsntSame --batch papers/Halpin_2010_OwlSameAsIsntSame/stances.yaml

pks source finalize Halpin_2010_OwlSameAsIsntSame
pks source promote Halpin_2010_OwlSameAsIsntSame
pks source sync Halpin_2010_OwlSameAsIsntSame
```

Claim IDs for `pks source add-claim --batch` should be content-stable, not sequential. The default contract should be:

- keep the human-authored local handle from the source file for readability
- compute the canonical claim ID from canonicalized claim content plus source URI
- preserve the local handle as source-local metadata

That gives stable re-extraction behavior without forcing authors to mint hashes by hand. Sequential `claim1` / `claim2` IDs should disappear from the source contract.

### Concept coordination commands

```bash
pks concept align --sources source/Halpin_2010_OwlSameAsIsntSame source/Melo_2013_NotQuiteSameIdentity
pks concept show align:weak_identity_relations
pks concept query align:weak_identity_relations --mode skeptical --operator leximax
pks concept decide align:weak_identity_relations --accept alt_claims_identical --reject alt_weak_identity_relation
pks concept promote align:weak_identity_relations
```

`pks concept align` must serialize its result as a git-backed merge artifact, not as a new ad hoc coordination directory. The natural substrate is the same partial-framework logic used by `PartialArgumentationFramework` in `propstore/repo/merge_framework.py` and merge operators in `propstore/repo/paf_merge.py`.

Recommended persistence:

- branch: `proposal/concepts`
- path: `merge/concepts/<cluster-id>.yaml`

The persisted object should be a serialized concept-alignment merge framework:

```yaml
kind: concept_alignment_framework
id: "align:weak_identity_relations"
created_at: "2026-04-04T12:30:00Z"
sources:
  - "tag:ctoth@audiom.com,2026:source/Halpin_2010_OwlSameAsIsntSame"
  - "tag:ctoth@audiom.com,2026:source/Melo_2013_NotQuiteSameIdentity"
arguments:
  - id: alt_claims_identical
    source: "tag:ctoth@audiom.com,2026:source/Halpin_2010_OwlSameAsIsntSame"
    local_handle: claims_identical
    proposed_name: claims_identical
    proposed_uri: "tag:ctoth@audiom.com,2026:concept/claims_identical"
    definition: "A weak identity relation between claim assertions."
    form: structural
  - id: alt_weak_identity_relation
    source: "tag:ctoth@audiom.com,2026:source/Melo_2013_NotQuiteSameIdentity"
    local_handle: weak_identity_relation
    proposed_name: weak_identity_relation
    proposed_uri: "tag:ctoth@audiom.com,2026:concept/weak_identity_relation"
    definition: "A constrained identity relation that must respect explicit non-identity."
    form: structural
framework:
  attacks:
    - [alt_claims_identical, alt_weak_identity_relation]
    - [alt_weak_identity_relation, alt_claims_identical]
  ignorance: []
  non_attacks: []
queries:
  skeptical_acceptance: []
  credulous_acceptance:
    - alt_claims_identical
    - alt_weak_identity_relation
  operator_scores:
    leximax:
      alt_claims_identical: 1
      alt_weak_identity_relation: 1
decision:
  status: open
  accepted: []
  rejected: []
  promoted_concept: null
```

That object must be sufficient for four commands:

- `pks concept show <cluster-id>`: render arguments, attacks, ignorance, and current decision state
- `pks concept query <cluster-id> --mode skeptical|credulous --operator sum|max|leximax`: compute acceptable alternatives using `PartialArgumentationFramework.completions()` and the exact operators in `paf_merge.py`
- `pks concept decide <cluster-id> --accept ... --reject ...`: persist operator or human decisions without mutating canonical concept files
- `pks concept promote <cluster-id>`: mint or update the accepted canonical concept on `master`, write aliases, and record the promoted concept URI back into the decision block

### `pks source finalize`

`pks source finalize <source>` is the mandatory pre-promotion gate. It should run, in order:

1. validate source-local files and references on the `source/<slug>` branch
2. resolve cross-source stance targets against accepted repository state
3. run concept conflict classification for newly proposed concepts
4. compute the parameterization-topology preview and report any component merges
5. compute or refresh artifact codes for source-local semantic objects
6. evaluate calibration coverage for the source and report whether claim priors will be derived or will fall back to `a=0.5`
7. write a git-backed finalize report on the source branch

Recommended report path:

- `merge/finalize/<source-slug>.yaml`

Minimum finalize-report fields:

```yaml
kind: source_finalize_report
source: "tag:ctoth@audiom.com,2026:source/Halpin_2010_OwlSameAsIsntSame"
status: ready
claim_reference_errors: []
stance_reference_errors: []
concept_alignment_candidates:
  - "align:weak_identity_relations"
parameterization_group_merges: []
artifact_code_status: complete
calibration:
  prior_base_rate_status: covered
  source_quality_status: vacuous
  fallback_to_default_base_rate: false
```

Promotion should refuse to run if finalize status is not `ready`.

### Transitional batch contract

Keep batch commands so current RPP skills can migrate incrementally. `pks import-papers` should shrink to a compatibility shim and then disappear.

**Existing and reusable:** validation/build surfaces in `propstore/cli/compiler_cmds.py`, committed proposal pattern in `propstore/proposals.py`  
**Build:** `pks source *`, `pks concept align`, direct source-branch writes, compatibility shims

## Three-Layer Workflow

### Layer 1: source-local authoring

Lives on `source/<slug>` branches.

This layer contains what one source appears to say before cross-source reconciliation:

- `source.yaml`
- `concepts.yaml`
- `claims.yaml`
- `justifications.yaml`
- `stances.yaml`
- notes and pass-through metadata

Claim extraction must be possible here without global concept agreement.

### Layer 2: coordination through formal merge artifacts

Do not introduce `coordination/concepts/*.yaml`.

Instead:

- read concept inventories from source branches
- classify concept alternatives using the same `attack` / `ignorance` / `non_attack` partition used by `PartialArgumentationFramework`
- persist concept-alignment merge artifacts on `proposal/concepts`
- use the exact merge operators in `propstore/repo/paf_merge.py` for consensus queries where appropriate

The serialized artifact can be YAML, but semantically it is a merge framework, not a freeform coordination note.

### Layer 3: canonical repository state

Only accepted concepts, accepted claims, accepted stances, accepted contexts, and accepted worldlines belong on `master`.

Promotion from a source branch should go through the same two-level pattern already described in `docs/semantic-merge.md`:

- storage merge: git two-parent commit
- semantic merge: formal object over disagreements

### Concept conflict detection

Add a concept-mode classifier aligned to the existing disagreement taxonomy from `docs/conflict-detection.md`:

- name collision with incompatible definitions: `CONFLICT`
- embedding-similar or alias-like definition overlap: `OVERLAP`
- same term but disjoint scope or regime: `PHI_NODE`
- same canonical handle but incompatible form: `CONFLICT`
- no meaningful overlap: `COMPATIBLE`

`pks source finalize` should run this check before promotion.

The minimum classifier input for each alternative is:

- source URI
- local handle
- proposed canonical name
- definition text
- form
- alias list
- parameterization relationships, if any

The minimum classifier output is:

- `attack` when both alternatives cannot be promoted simultaneously to one canonical concept
- `ignorance` when they may or may not overlap and need review
- `non_attack` when they are clearly distinct and may coexist

That output must be written back into the persisted alignment object so promotion does not need to rerun the entire alignment pass.

### Parameterization topology check

If accepting a concept inventory would merge parameterization components, report that explicitly using `build_groups()` from `propstore/parameterization_groups.py`. A concept decision can change derivation reachability and therefore cannot be treated as a pure naming edit.

**Existing and reusable:** `propstore/repo/merge_framework.py`, `propstore/repo/merge_classifier.py`, `propstore/repo/paf_merge.py`, `propstore/parameterization_groups.py`, `docs/conflict-detection.md`  
**Build:** concept-mode classifier, serialized concept-alignment merge artifacts, finalize-time topology preview

## Workflow Changes By Skill

### `paper-reader`

Remains domain-specific. It still reads page PNGs, writes notes, description, citations, and metadata under `papers/`. It should additionally call `pks source init`, `pks source write-notes`, and `pks source write-metadata`.

### `register-concepts`

Stop calling `pks concept add` directly as the default path. It should call `pks source propose-concept` and rely on propstore to:

- check the accepted registry
- record exact matches immediately
- leave unresolved proposals on the source branch
- enqueue concept-alignment work when needed

This absorbs the old proposal's vague "reconcile before register" step. The pre-check now lives inside `pks source propose-concept` as automatic canonical-registry lookup plus concept-alignment enqueueing. The citation-oriented `reconcile` skill remains a separate RPP operation.

### `extract-claims`

Stop treating direct global concept registration as a prerequisite. It should read source-local concept handles and call `pks source add-claim --batch`. The current `claim1`/`claim2` generation in `generate_claims.py` must be replaced by propstore-assigned stable IDs.

### `extract-justifications`

Continue extracting separately. Write to `justifications.yaml` and call `pks source add-justification --batch`.

### `extract-stances`

Stop embedding stances inline. Write `stances.yaml` and call `pks source add-stance --batch`. Cross-source targets should resolve against accepted repository state during import into the source branch, not in a later opaque importer.

### `paper-process`

The main flow becomes:

1. retrieve
2. read
3. source init / notes / metadata
4. register concepts
5. extract claims
6. extract justifications
7. extract stances
8. finalize

The current skip from reader to claim extraction is a contract violation and should be removed.

### `reconcile`

Keep as an RPP skill. Citation reconciliation is source-kind-specific and does not belong in propstore core.

### `reconcile-vocabulary`

Retarget to `pks concept align`. Similarity grouping logic from `bootstrap_concepts.py` should move into propstore as a proposal heuristic, not remain the semantic source of truth.

### `adjudicate`

Keep as a domain-level judgment skill. It should consume promoted claims and concept-alignment artifacts, not raw source-local scratch.

**Touches existing:** all listed RPP skills plus `../research-papers-plugin/plugins/research-papers/scripts/generate_claims.py`, `bootstrap_concepts.py`, `propose_concepts.py`, `stamp_provenance.py`

## Migration Path

### Phase 1: source foundations

1. Add source schema and storage.
2. Add `source/` branch kind to `propstore/repo/branch.py`.
3. Add `pks source init`, `write-notes`, `write-metadata`.
4. Retarget `paper-reader` to create source branches.
5. Add `tag:` and `ni:` minting helpers.

### Phase 2: concept coordination

6. Add `pks source propose-concept`.
7. Retarget `register-concepts`.
8. Add concept-alignment merge artifacts backed by `PartialArgumentationFramework`.
9. Add concept conflict classification and finalize-time parameterization-group preview.

### Phase 3: direct source authoring

10. Add `pks source add-claim --batch`.
11. Add `pks source add-justification --batch`.
12. Add `pks source add-stance --batch`.
13. Retarget extraction skills.
14. Reduce `pks import-papers` to compatibility mode.

### Phase 4: verification

15. Add semantic artifact codes.
16. Add `pks verify tree`.
17. Attach source-origin verification to `origin.content_ref`.

### Phase 5: trust calibration

18. Ingest calibration sources for Camerer 2016, Camerer 2018, OSC 2015, and Ioannidis 2005.
19. Add source prior calibration derivation through parameterization chains.
20. Replace `p_arg_from_claim()` dogmatic behavior.

### Phase 6: cleanup

21. Change `paper-process` to the new ordering permanently.
22. Remove the import bridge once all production skills call `pks source *`.

### Deferred work

- full recursive trusty-URI externalization
- richer claim-level trust modifiers beyond source prior plus source-quality discounting
- more sophisticated concept-alignment heuristics beyond initial similarity grouping plus operator review

## Invariants

1. The repository, not the worktree, is the semantic source of truth.
2. Source-local extraction is possible before collection-wide concept agreement is complete.
3. No unresolved source-local state lives on `master`.
4. Every claim traces to exactly one source with a verifiable origin.
5. Canonical concept files contain accepted registry state only.
6. Plugins call `pks source *` directly; the import bridge is transitional and then removed.
7. Artifact codes form a Merkle DAG over the knowledge graph.
8. `Opinion.a` is a derived quantity when calibration evidence exists.
9. Merge coordination uses the existing formal merge substrate rather than an ad hoc directory convention.
10. Concept decisions that alter parameterization reachability must be surfaced before promotion.
11. Stances and justifications are first-class artifacts, never inline side effects inside claims.
12. Proposal history is durable git state and remains auditable from commits alone.

## Why This Fits The Literature

- `docs/semantic-merge.md` and `propstore/repo/paf_merge.py` already implement the IC-merge and AF-merge direction associated with Konieczny and Coste-Marquis. This proposal reuses that substrate for concept alignment instead of inventing a second reconciliation model.
- `docs/structured-argumentation.md`, `docs/atms.md`, and `propstore/world/atms.py` already provide the support and intervention machinery needed for deconvergence: “what assumption would force a split or a merge?”
- `docs/subjective-logic.md` and `propstore/opinion.py` already provide the opinion algebra needed for source priors, claim evidence, and source-quality discounting.
- `docs/probabilistic-argumentation.md` and `propstore/praf.py` already provide the probabilistic acceptance layer that should consume calibrated source priors instead of `dogmatic_true()`.
- Groth 2010 and nanopublication-style provenance fit the move to source-scoped claims with explicit provenance and verification layers.
- RFC 4151, RFC 6920, and Kuhn 2014 give the three identifier layers a standards-based division of labor: identity, integrity, and semantic immutability.
- Replication-science papers provide empirical priors that can live as ordinary claims and feed back into source calibration through propstore’s own parameterization machinery.

## References

- RFC 4151. The `tag:` URI scheme.
- RFC 6920. `ni:` URIs for naming things with hashes.
- Kuhn, T. and Dumontier, M. 2014. Trusty URIs.
- Groth, P., Gibson, A., and Velterop, J. 2010. The Anatomy of a Nanopublication.
- Konieczny, S. and Pino Pérez, R. 2002. Merging Information Under Constraints.
- Coste-Marquis, S. et al. 2007. Merging Argumentation Frameworks.
- Camerer, C. et al. 2016. Evaluating replicability of laboratory experiments in economics.
- Open Science Collaboration. 2015. Estimating the reproducibility of psychological science.
- Camerer, C. et al. 2018. Evaluating the replicability of social science experiments in Nature and Science.
- Ioannidis, J. P. A. 2005. Why Most Published Research Findings Are False.
