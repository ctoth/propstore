# Workstream A — Semantic Substrate Retrofit

Date: 2026-04-16
Status: active, tightened 2026-04-17 for non-Davidsonian execution; phase 4 exit verification in progress
Depends on: `disciplines.md`, `judgment-rubric.md`, `../../semantic-substrate-papers.md` (paper list + retrieval state), `ws-a0-repository-artifact-boundary.md` before phase 2 document-boundary conversion
Blocks (within this set): WS-B (needs phase 1), WS-C (needs phase 4), WS-Z-types (needs phase 1 for full payoff)
Review context: `../axis-3d-semantic.md` (primary), `../axis-9-doc-drift.md`, `../axis-1-principle-adherence.md`

## Progress log

- 2026-04-17: Workstream tightened for non-Davidsonian execution. Required implementation papers for the selected path were confirmed present in `./papers`; optional explanatory/rejection papers are not blockers.
- 2026-04-17: Phase 1 foundation slice implemented: typed `ProvenanceStatus`, `ProvenanceWitness`, `Provenance`; deterministic JSON-LD named-graph serialization; git-notes round trip on `refs/notes/provenance`; provenance composition property tests; `Opinion.provenance` composition through fusion/discounting; `SourceTrustDocument` and `SourceTrustQualityDocument` mandatory status fields; `ResolutionDocument` collapsed to `opinion: OpinionDocument | None`; classifier/proposal outputs migrated to nested `resolution.opinion`; sidecar projection updated at the storage boundary.
- 2026-04-17: Phase 1 foundation verification: `tests/test_provenance_foundations.py` passed; targeted affected suite `tests/test_source_trust.py tests/test_classify.py tests/test_relate_opinions.py tests/test_build_sidecar.py tests/test_praf.py` passed (`194 passed`).
- 2026-04-17: Removed the erroneous old-repo migration/backfill requirement from the workstream. Existing pre-workstream knowledge repositories are explicitly not a compatibility target; no migration, backfill, adapter, fallback, or bridge CLI belongs in WS-A.
- 2026-04-17: Phase 2 lemon foundation slice implemented: `propstore/core/lemon/` now defines `OntologyReference`, `LexicalForm`, `LexicalSense`, and `LexicalEntry`; `LexicalForm` rejects dimensional metadata by construction; concept alignment no longer uses definition-token/Jaccard overlap and instead classifies exact lemon identity/reference relations.
- 2026-04-17: Added WS-A0 as a prerequisite after the attempted `ConceptDocument` lemon hard-boundary slice exposed repository/artifact boundary debt: non-CLI production modules import `propstore.cli.repository`, `Repository.store` couples repository to `WorldModel`, and canonical concept loading bypasses artifact families/store. WS-A phase 2 may continue with standalone lemon work, but the canonical concept-document conversion must wait for WS-A0 gates to be active and green.
- 2026-04-17: WS-A0 completed and phase 2 canonical concept-document conversion resumed. `ConceptDocument` now rejects the old flat `canonical_name`/`definition`/`form` artifact shape and requires lemon-shaped `ontology_reference` plus `lexical_entry`; the runtime `ConceptRecord` projection remains explicit at the artifact boundary. Fixture authors now emit canonical lemon concept artifacts and project to record payloads only for in-memory registries. Verification slice passed: `tests/test_lemon_concept_documents.py tests/test_artifact_identity_policy.py tests/test_claim_compiler.py tests/test_build_sidecar.py` (`107 passed`).
- 2026-04-17: Phase 2 document-boundary fallout tightened: validator fixtures now author lemon artifacts directly; `pks concept add/show/rename/link` save and validate through the artifact document boundary; canonical concept version IDs remain artifact-version IDs instead of being overwritten by flat record projections; `lexical_entry.physical_dimension_form` is required for canonical concept documents. Verification slice passed: `tests/test_validator.py` plus focused concept CLI mutation/build tests (`52 passed`).
- 2026-04-17: Added and completed WS-A00 after the repository boundary cleanup still left a confusing `propstore.repo.repository.Repository` surface and a second repo-shaped `KnowledgeRepo` type. The canonical facade is now `propstore.repository.Repository`; the low-level git carrier is `propstore.repo.GitStore`; gates reject the old nested repository import and old carrier class name. Verification slice passed: repository naming gates (`7 passed`) and affected repository/storage/import/property suite (`158 passed`).
- 2026-04-17: Added WS-A000 after the remaining `propstore.repo` package and `Repo*` public type names kept a second repo-shaped vocabulary beside `propstore.repository.Repository`. Phase 3 canonical document work remains behind this prerequisite until the storage naming gates are active and green.
- 2026-04-17: WS-A000 completed. The canonical repository facade remains `propstore.repository.Repository`; git-backed storage and merge primitives now live under `propstore.storage`; `propstore/repo/` is deleted; public `Repo*` production type names were removed. Final verification passed: storage naming/world boundary plus affected storage/import/merge/source/worldline suite (`263 passed`), including GitStore Hypothesis properties; `uv run pyright propstore/storage propstore/repository.py propstore/cli/repository_import_cmd.py` passed with `0 errors`.
- 2026-04-17: WS-A000 doc cleanup completed after stale docs still described the deleted `propstore/repo` storage surface and old `RepoMergeFramework` type. Added a current-doc boundary gate and updated `CLAUDE.md`, `docs/git-backend.md`, `docs/semantic-merge.md`, and the branch-storage test docstring to the `propstore.storage` / `RepositoryMergeFramework` vocabulary.
- 2026-04-17: Phase 2 lemon document-boundary affected suite passed after stale flat-concept expectations were removed from CLI, validator, alignment, import, artifact-store, sidecar, and compiler coverage (`tests/test_lemon_concept_documents.py tests/test_artifact_identity_policy.py tests/test_cli.py tests/test_validator.py tests/test_build_sidecar.py tests/test_claim_compiler.py tests/test_concept_alignment_cli.py tests/test_import_repo.py tests/test_artifact_store.py`, `262 passed`).
- 2026-04-17: Phase 2 form/dimension split completed. Physical dimension conversion, Pint integration, unit aliases, and dimensional algebra now live in `propstore.dimensions`; `propstore.form_utils` is limited to authored form loading/validation; lemon `LexicalForm` now lives in `propstore.core.lemon.forms`; gates reject dimension-algebra ownership or public re-export from `form_utils`. Verification slice passed: boundary gates (`4 passed`) and affected form/compiler/sidecar/validator suite (`301 passed`).
- 2026-04-17: Phase 2 lemon invariant/documentation slice completed. Existing Buitelaar 2011 and OntoLex-Lemon paper artifacts were confirmed complete and non-stub by file/content inspection; no page-image reread was performed in this slice. `validate_concepts` now retains the canonical `ConceptDocument` and checks lemon document invariants; homographs no longer collapse entry identity or require filename equality; duplicate sense references and ontology references without matching senses are rejected. `docs/lemon-concepts.md`, `docs/gaps.md`, and CLAUDE.md now describe the implemented Phase 2 state without claiming Phase 3/4 semantics are live. Verification slice passed: invariant gates (`9 passed`) and affected validator/alignment/CLI/sidecar/compiler/CEL suite (`318 passed`). `uv run pyright --strict propstore/core/lemon` was attempted but the installed Pyright CLI rejects `--strict`; `uv run pyright propstore/core/lemon` passed with `0 errors`.
- 2026-04-17: Phase 2 exit criteria satisfied. `rg -F "jaccard" propstore tests docs` returns no matches; the remaining semantic substrate gap is Phase 3/4 work, not lemon container work.
- 2026-04-17: Phase 3 first substrate slice completed. Existing Pustejovsky 1991, Dowty 1991, and Fillmore 1982 paper artifacts were confirmed complete and non-stub by file/content inspection; no page-image reread was performed in this slice. Added `propstore/core/lemon/qualia.py`, `proto_roles.py`, and `description_kinds.py`; extended `LexicalSense` with optional `qualia`, `description_kind`, and `role_bundles`; added `docs/qualia-and-proto-roles.md` with the worldline review note. Verification slice passed: focused semantic properties (`15 passed`), affected lemon/validator/alignment/TIMEPOINT suite (`86 passed`), and `uv run pyright propstore/core/lemon` (`0 errors`).
- 2026-04-17: Phase 3 document persistence and validation slice completed. `ConceptDocument.lexical_entry.senses[]` now persists provenance, qualia, description-kind, and proto-role bundle fields through the artifact schema and canonical payload renderer; validator cross-reference checks now reject qualia targets that are missing or that fail their type constraints. Proto-role entailment properties are strict document strings validated by the agent/patient slot they inhabit, avoiding the msgspec multi-`StrEnum` union limitation while preserving Dowty's separate proto-agent/proto-patient vocabularies. Verification slice passed: red gate failed on unknown Phase 3 fields (`4 failed`), focused green (`5 passed`), affected lemon/validator/Hypothesis suite (`21 passed`), and `uv run pyright propstore/artifacts/documents/concepts.py propstore/core/concepts.py propstore/core/lemon propstore/validate_concepts.py` (`0 errors`).
- 2026-04-17: Phase 3 concept CLI manipulation slice completed. Added `pks concept qualia-add`, `pks concept description-kind`, and `pks concept proto-role`; all save through the artifact boundary, require explicit provenance witnesses for qualia/proto-role updates, validate before writing, and canonicalize post-coercion payloads before hashing. Verification slice passed: red command gate failed on missing commands (`3 failed`), focused CLI green (`3 passed`), full concept CLI suite (`86 passed`), focused semantic/CLI final suite (`24 passed`), and `uv run pyright propstore/cli/concept.py propstore/core/concepts.py` (`0 errors`).
- 2026-04-17: Phase 3 seed concept slice completed. `pks init` now seeds packaged concept resources for the required description-kind concepts (`Observation`, `Measurement`, `Assertion`, `Decision`, `Reaction`), the `Measurement_Instrument` TELIC qualia example, and `Causal_Connection` as a description-kind over two description-claims plus an explicit account slot. Seed concept writes go through `ArtifactStore.prepare`, so initialized repositories receive normalized artifact IDs, logical IDs, version IDs, provenance-bearing Phase 3 fields, and validator-ready YAML. Verification slice passed: red init seed gate failed on missing concept files (`2 failed`), focused green including `validate_after_init` (`3 passed`), affected init/validator/lemon/CLI suite (`72 passed`), and `uv run pyright propstore/cli/init.py propstore/core/lemon propstore/artifacts/documents/concepts.py` (`0 errors`).
- 2026-04-17: Phase 3 coreference-as-Dung slice completed. Description-claim coreference now has a `CoreferenceQuery` carrying the stored merge hypotheses plus an explicit `dung.ArgumentationFramework`; cluster rendering is computed under requested Dung semantics, so grounded can withhold mutually attacking cluster hypotheses while preferred/stable can surface rival clusters without mutating the stored query. Verification slice passed: red import/query gate failed before the surface existed (`1 error`), focused green (`1 passed`), affected Phase 3 semantic/document/validator suite (`22 passed`), and `uv run pyright propstore/core/lemon` (`0 errors`).
- 2026-04-17: Phase 3 description-temporal slice completed. Added `DescriptionTemporalAnchor`, `AllenRelation`, and `description_temporal_relation` as a thin description-claim interval layer over existing `KindType.TIMEPOINT` + `Z3ConditionSolver`; this keeps Allen-1983 reasoning on the existing Z3 path and avoids a second temporal/event solver. Verification slice passed: red import gate failed before the surface existed (`1 error`), focused Hypothesis property green (`1 passed`), affected Phase 3/TIMEPOINT suite (`36 passed`), and `uv run pyright propstore/core/lemon` (`0 errors`).
- 2026-04-17: Phase 3 exit criteria satisfied. Pustejovsky 1991, Dowty 1991, and Fillmore 1982 paper artifacts have non-stub `notes.md` files by file/content inspection; no page-image reread was performed. `docs/event-semantics.md` and `docs/qualia-and-proto-roles.md` describe the implemented non-Davidsonian semantics; `qualia.py`, `proto_roles.py`, and `description_kinds.py` live under `propstore/core/lemon`; `propstore/core/lemon/events.py` does not exist; the required seed description-kind names are present; `worldline/` remains deliberately unchanged with the documented adoption point. Verification passed: Phase 3 exit suite (`189 passed`) and `uv run pyright propstore/core/lemon propstore/artifacts/documents/concepts.py propstore/cli/concept.py propstore/cli/init.py propstore/validate_concepts.py` (`0 errors`).
- 2026-04-17: Phase 4 paper inventory and Clark dedupe slice completed. The complete Clark artifact was canonicalized from `papers/Clark_2014_MicropublicationsSemanticModel/` to `papers/Clark_2014_Micropublications/`; `papers/index.md`, live paper cross-references, tag symlinks, and `semantic-substrate-papers.md` now use the canonical path. The Clark paper lint passed for required files, source artifacts, index entry, collection cross-reference section, page citations, and zero legacy wikilinks. McCarthy 1993, Guha 1991, Giunchiglia-Serafini 1994, McCarthy-Buvac 1997, and Bozzato 2018 all have non-stub `notes.md` files by file/content inspection. The Guha corpus item is the thesis titled _Contexts: A Formalization and Some Applications_, so it covers the previously split formalization/applications entries.
- 2026-04-17: Phase 4 context/lifting slice completed. `context_hierarchy.py` is deleted and replaced by `context_lifting.py`; `ContextDocument` now carries structured assumptions, parameters, perspective, and explicit lifting rules; `ClaimDocument.context` is required as a `ContextReference`; the sidecar stores context structure plus `context_lifting_rule`; `WorldModel`, `BoundWorld`, activation, conflict detection, parameterization conflict detection, and ATMS entry points consume `LiftingSystem` instead of visibility inheritance. Active docs now describe explicit lifting, and stale context-hierarchy docs are gated away. Verification slice passed: Phase 4 context red gate failed before implementation, focused context suite (`23 passed`), affected context/conflict/property/ATMS/git/build/compiler suite (`383 passed`), and `uv run pyright propstore/context_lifting.py propstore/context_types.py propstore/artifacts/documents/contexts.py propstore/artifacts/documents/claims.py propstore/compiler/passes.py propstore/conflict_detector propstore/sidecar/claims.py propstore/sidecar/build.py propstore/core/activation.py` (`0 errors`). A broader `pyright` command including `world/` still fails on pre-existing typing debt in `world/atms.py`, `world/bound.py`, `world/hypothetical.py`, and `world/model.py`. No page-image paper reread was performed in this slice; the implementation follows the already processed McCarthy 1993, Guha 1991, Giunchiglia-Serafini 1994, and Bozzato 2018 notes.
- 2026-04-17: Phase 4 exit fallout slice completed after `uv sync --upgrade` exposed test authorship that still omitted explicit contexts or bypassed the canonical artifact shapes. Test resource authorship now creates `contexts/ctx_test.yaml` before context-qualified claims; repository import tests author canonical claim context references as `{"id": ...}`; source-local claim batches keep their source schema and promotion canonicalizes to the artifact schema. Revision projection now treats context-qualified active claims as exact when their support can be reconstructed as a context label plus compiled assumption labels, so context-scoped claims participate in AGM-facing belief bases instead of disappearing from revision CLI views. Verification slice passed: focused revision/source failures (`10 passed`) and broader context fallout suite (`378 passed`). `uv run pyright` was attempted on the touched production/test surfaces; it still fails on existing `compiler_cmds.py`, `world/bound.py`, and test typing debt, so no new type-clean claim is made for this slice.
- 2026-04-17: Phase 4 nested-`ist` document slice completed. `ClaimDocument` now has tagged `AtomicPropositionDocument` and recursive `IstPropositionDocument` proposition shapes, with packaged JSON Schema support for nested `ist(c, p)` documents. Operational nested-context reasoning remains outside this phase per scope, but the type-level parse/round-trip surface exists now. Verification slice passed: red nested-`ist` import gate failed before implementation, focused nested-`ist` + compiler/document suite (`14 passed`, including a Hypothesis context-stack round-trip), and `uv run pyright propstore/artifacts/documents/claims.py` (`0 errors`).
- 2026-04-17: Phase 4 micropublication document/source slice completed. Added `MicropublicationDocument` / `MicropublicationsFileDocument`, source and canonical micropub artifact families, `micropubs.yaml` composition during source finalize, canonical `micropubs/{source}.yaml` promotion filtered to valid claim members, and `pks source propose-claim --context` so source-authored claims cannot promote without explicit context. Promotion now canonicalizes source-local context strings to `ContextReference` before computing claim version IDs. Verification slice passed: red micropub import gate failed before implementation, focused micropub suite (`3 passed`), affected source/finalize/promote/propose suite (`39 passed`), focused source-context fallout suite (`5 passed`), and `uv run pyright propstore/artifacts/documents/micropubs.py` (`0 errors`). A broader source-module Pyright run still exposes existing lazy-export/generic typing debt in `artifacts.families`, `source.common`, `source.finalize`, and `source.promote`; that debt is not resolved in this slice.
- 2026-04-17: Phase 4 micropublication CLI slice completed. Added `pks micropub bundle`, `pks micropub show`, and `pks micropub lift` over canonical micropub artifact families; `lift` checks the authored context lifting system rather than scanning files ad hoc. Verification slice passed: red CLI gate failed before implementation on missing `micropub` command; narrow CLI test (`1 passed`); affected micropub/source suite (`40 passed`); and `uv run pyright propstore/cli/micropub.py` (`0 errors`).
- 2026-04-17: Phase 4 ATMS context-dimension slice completed. `EnvironmentKey` now carries sorted/deduped `context_ids` alongside assumption IDs; label union/subsumption/minimality include that context dimension; the ATMS engine seeds context nodes and uses them as explicit antecedents for context-scoped claims, so a context claim is not represented as unconditional and context lifting preserves label antichain invariants. Verification slice passed: red context-dimension gate failed before implementation; focused red-to-green tests (`4 passed`); affected labels/ATMS/context suite (`95 passed`); and `uv run pyright propstore/core/labels.py` (`0 errors`). `uv run pyright propstore/core/labels.py propstore/world/atms.py` still fails on previously recorded `world/atms.py` typing debt around typed-dict/value-status inference and conflict row typing; that broader debt is not resolved in this slice.
- 2026-04-17: Phase 4 micropublication-as-ATMS-node slice completed. Canonical `micropubs/{source}.yaml` artifacts now populate dedicated sidecar `micropublication` and `micropublication_claim` tables; `WorldModel.all_micropublications()` returns typed `ActiveMicropublication` objects; `ATMSEngine` materializes micropub bundle nodes whose labels combine the micropub context node with all member claim nodes. Verification slice passed: red gate failed before implementation on missing `WorldModel.all_micropublications()` and `ATMSEngine.supported_micropub_ids()`; focused red-to-green tests (`2 passed`); affected micropub/ATMS/context-label suite (`80 passed`); and `uv run pyright propstore/core/micropublications.py propstore/sidecar/micropublications.py` (`0 errors`).
- 2026-04-17: Phase 4 documentation and gap-closure slice completed. `docs/contexts-and-micropubs.md` now connects the implemented McCarthy/Guha `ist(c,p)` context/lifting substrate, Clark micropublication bundles, ATMS context labels, and phase-3 descriptivist event semantics; `CLAUDE.md`, `docs/atms.md`, `docs/cli-reference.md`, `docs/python-api.md`, and `docs/gaps.md` now describe the implemented state rather than the pre-phase-4 gap. Verification slice passed: focused Phase 4 docs smoke suite (`tests/test_context_lifting_phase4.py tests/test_micropublications_phase4.py tests/test_labels_properties.py tests/test_atms_engine.py`, `69 passed`). This slice cites processed paper notes; no fresh page-image paper reread was performed.

## What you're doing

Propstore advertises itself as a "semantic operating system" grounded in frame semantics (Fillmore 1982, Baker 1998 FrameNet), the generative lexicon (Pustejovsky 1991), ontology lexicalization (Buitelaar 2011 lemon / OntoLex), context formalization (McCarthy 1993, Guha 1991), micropublications (Clark 2014), and provenance semantics (Buneman 2001, Carroll 2005). The 2026-04-16 code review found that **none of these papers have structural representation in the code**. What exists instead is a dimensional-quantity ontology (via pint), a SKOS-style taxonomy of concepts, visibility-inheritance contexts (ancestry-based, not `ist(c,p)`), and token-Jaccard reconciliation for alignment.

Your job: cash out the rhetoric. Read the papers. Design and implement the type system they describe. Migrate the existing code onto the new substrate. Produce a concept/semantic layer that actually delivers frame semantics + qualia + lemon + `ist(c,p)` + micropublications + provenance, as an integrated whole.

This is the biggest workstream in the set. It is structured as four phases, but those phases are *internal* to the workstream — they share a type system, they share a target-architecture implementation pass, they share a papers-read first pass. Do not treat them as separable workstreams.

## What the review actually found

Verbatim, so you don't have to chase the axis report:

> **Axis 3d, biggest drift:** The four papers CLAUDE.md explicitly names as grounding the concept/semantic layer — Fillmore 1982, Pustejovsky 1991, Buitelaar 2011 (lemon), McCarthy 1993 (`ist(c, p)`) — have zero corresponding structural content in code. Grep for `qualia|telic|agentive|constitutive|proto_role|lemon|LexicalEntry|LexicalForm|LexicalSense|lexicon|sameAs|ist\(c|lifting|bridge_rule|LocalModels` across `propstore/` → zero hits. Grep for `frame` → one file (`opinion.py`), and every hit is "binomial frame of discernment" (Dempster-Shafer), not Fillmore.

> **Axis 3d, honest assessment:** Of 6 clauses in CLAUDE.md's "Concept/semantic layer" paragraph, 2 are cashed out (forms + CEL/Z3), 4 are misdescriptions. The 4 misdescriptions are precisely the ones referencing semantic-substrate papers. What propstore actually implements is a dimensional-quantity system + SKOS taxonomy + visibility-inheritance contexts + string-token Jaccard reconciliation + partial micropublication info structure.

> **Axis 9 cross-ref:** `papers/Clark_2014_Micropublications/` and `papers/Clark_2014_MicropublicationsSemanticModel/` are two directories on disk with divergent `notes.md` — same paper, duplicated. Only the `SemanticModel` variant has the PDF.

> **Axis 9 cross-ref:** `Buneman_2001_CharacterizationDataProvenance` and `Carroll_2005_NamedGraphsProvenanceTrust` are metadata-only stubs with no PDF and no notes. The foundational provenance papers have never been read.

> **Axis 1 Finding 2.4 (HIGH):** `source_calibration.derive_source_trust` silently defaults `prior_base_rate=0.5` without provenance on the stored payload. The `SourceTrustDocument` has no `status` field. Downstream readers cannot distinguish "derived" from "had nothing."

> **Axis 1 Structural S2:** `SourceTrustDocument` and `SourceTrustQualityDocument` carry numeric values with no `status` field. Cannot label ignorance.

> **Axis 1 Structural S3:** `ResolutionDocument` has four independent scalar opinion fields instead of `opinion: Opinion | None`. Permits invariant-violating `(0.0, 0.0, 0.0, 0.5)`.

## Vision

When this workstream is complete, propstore has:

- **Typed provenance woven through everything.** Every probability, every stance, every opinion, every derived quantity carries a `Provenance` record whose `status` field distinguishes `measured | calibrated | stated | defaulted | vacuous`. Fusion operators compose provenance. Serialization preserves it.
- **A lemon-shaped concept registry.** `LexicalEntry → Form → LexicalSense → OntologyReference`, with entry-level physical-dimension annotations (the existing `pint` integration finds its principled home as a sibling of lemon rather than mixed into it).
- **Qualia as the generative-lexicon substrate at the sense level.** `LexicalSense.qualia: QualiaStructure` holds four roles (formal, constitutive, telic, agentive) per Pustejovsky 1991 with type-driven coercion rules. Qualia values are typed `QualiaReference` objects into other concepts, carrying provenance and licensing transitive composition (X's TELIC is Y, Y's TELIC is Z → X has a purposive chain to Z — this is the generative bit).
- **Description-kinds as concepts (events as defeasible coreference).** propstore does not treat events as individuals with pre-descriptive identity. There are description-kind concepts — `Observation`, `Measurement`, `Assertion`, `Decision`, `Reaction` — whose senses carry frame-like participant slots (observer, observed, instrumentation; quantity, value, instrument; etc.) and temporal anchoring via TIMEPOINT. Particular descriptions are *claims* of these kinds, living in the existing claim machinery. What we informally call "an event" is a render-time inference: a cluster of description-claims under an explicit merge-hypothesis whose justification is itself a defeasible Dung argument. Coreference is never a stored fact; it is the conclusion of an argument that survives attack under some assumption-set, queryable at render time. See `docs/event-semantics.md` for the full position statement and its commitments against Davidsonian / neo-Davidsonian event reification.
- **Graded proto-role entailments on relational roles.** Dowty 1991 proto-agent (volition, sentience, causation, movement, change-of-state) and proto-patient (affected, incremental theme, stationary, causally affected, change-of-state) entailments decorate thematic roles as `GradedEntailment(value ∈ [0,1], provenance)`. Graded and provenance-bearing — honest ignorance works at this layer too; ASP's argument-realization predictions compose.
- **First-class contexts per McCarthy 1993 `ist(c, p)`.** Contexts are logical objects, not visibility tags. Lifting rules per Guha 1991 + Giunchiglia-Serafini 1994 connect them. Bozzato 2018 justifiable exceptions sit on top (feeds directly into WS-C).
- **Claims as context-qualified propositions.** Every claim is `(context, proposition)`, not bare proposition. Visibility inheritance is retired; its behavior, where users want it, is re-expressed as explicit lifting rules per repo.
- **Clark micropublications as the composition rule.** A micropub bundles a claim (or claims) with evidence references, assumption sets, stance, and provenance into a publishable atomic unit. Each micropub is an ATMS node (the label algebra gains context dimension).
- **Alignment by lexical identity, not by token Jaccard.** Reconciliation walks lemon entries and senses; if no match, it proposes candidates on a proposal branch rather than silently collapsing.
- **No old-repo compatibility path.** The target architecture is implemented directly. Existing pre-workstream knowledge repositories are not a compatibility target and must not drive backfill, migration, adapter, fallback, or bridge code.

## Phase structure (internal to this workstream)

Phases are sequenced because the downstream phases depend on upstream *type decisions*, not because they require separate merges. One workstream, one integrated design doc, one target architecture, one PR chain.

### Phase 1 — Provenance foundations

**Papers:** Buneman 2001, Carroll 2005. Optional secondary: Moreau 2013 PROV-O, Green-Karvounarakis-Tannen 2007 semirings.

**Scope:**
- Process Buneman 2001 and Carroll 2005 `notes.md` to non-stub depth.
- Design `Provenance` type: fields for witness chain (asserter, timestamp, source-artifact-code, method), status discriminator (`measured | calibrated | stated | defaulted | vacuous`), composition algebra for fusion-derived provenance.
- **Storage mechanism: git-notes via dulwich.** The logical form of provenance is a named graph per Carroll 2005. The *storage realization* is git-notes: provenance named-graph payloads attach to claim-object SHAs as notes on a dedicated notes ref (e.g. `refs/notes/provenance`). This keeps the claim object's content-hash stable while provenance rides alongside — the "provenance does not contaminate claim identity" invariant is enforced by git's object model itself. Dulwich ≥ 1.1.0 (already the propstore pin) supports notes natively via `dulwich.notes`. No parallel per-repo provenance table; no impedance mismatch; notes push/pull via standard git refspecs (`refs/notes/*:refs/notes/*`), which means the provenance carrier is **substrate-independent** — works with local dulwich, GitHub / GitLab, Cloudflare Artifacts, or any git-speaking remote.
- **Decidability of content-hashing:** every provenance payload is itself content-addressed (hash of the named-graph serialization), so identical witness chains dedupe automatically at the note-object level. No custom dedup layer; git's own object dedup suffices.
- Named-graph serialization format (the content that lives inside the note): JSON-LD or Turtle — decision during design; pick whichever round-trips most cleanly with `msgspec`. Readers reconstruct the named graph from the note; they never reconstruct from a side table.
- Rewrite `propstore/provenance.py`. Existing agent-timestamp stamping becomes the `method="stated"` branch.
- `SourceTrustDocument` + `SourceTrustQualityDocument` gain `status` field. Mandatory, not optional.
- `ResolutionDocument` collapses four scalars into `opinion: OpinionDocument | None` (a single tagged field).
- `Opinion` carries provenance as an optional field (or use a tagged-union variant distinguishing raw `Opinion(...)` from `Opinion.with_provenance(..., provenance)`).
- Fusion operators (`consensus_pair`, `_ccf_binomial`, `wbf` — once fixed in WS-Z-types — and any future operators) compose provenance through their output.
- Property tests: provenance composition under fusion where the underlying operator is associative; named-graph round-trip; `status`-field parse-time enforcement; `SourceTrustDocument.status` mandatory at load.
- No old-repo migration surface. Existing knowledge repositories are not a compatibility target for this workstream; do not add a backfill, reauthor, bridge, fallback, or compatibility CLI. New authored data must use the Phase 1 document shape directly, and pre-Phase-1 payloads fail at the document boundary.

**Phase 1 exit:** Buneman + Carroll notes non-stub; `docs/provenance.md` exists and documents the git-notes storage mechanism + serialization format; `uv run pyright --strict propstore/provenance.py` green; `test_provenance*` green and expanded with composition properties + a git-notes round-trip test (write a provenance note on a claim SHA; read it back via `dulwich.notes`; verify named-graph content is byte-identical); CLAUDE.md's provenance paragraph updated to reflect the git-notes-as-carrier decision.

### Phase 2 — Lemon concept container

**Papers:** Buitelaar 2011. Secondary: OntoLex-Lemon community report (Cimiano, McCrae, Buitelaar 2020 — fetch if not already retrieved).

**Prerequisite:** Complete `ws-a0-repository-artifact-boundary.md` before changing the canonical `ConceptDocument` shape. The lemon core package and source-alignment Jaccard removal can exist before WS-A0; the storage/document boundary cannot. The prerequisite is not migration work. It is a layer-boundary correction that prevents two concept-loading production paths from coexisting.

**Scope:**
- Process Buitelaar 2011 notes; fetch + process OntoLex-Lemon 2020+ spec.
- Design `LexicalEntry`, `Form`, `LexicalSense`, `OntologyReference` types.
- Decide Form↔dimension relationship: `Form` does NOT carry dimensional annotation directly (dimensional annotation rides on the `LexicalEntry` or on a sibling `Measurement` document); this preserves lemon's separation and keeps the pint integration clean.
- Split `form_utils.py`: physical-dimension algebra moves to `propstore/dimensions.py`; lemon `Form` machinery lives in `propstore/core/lemon/forms.py`.
- Rewrite `core/concepts.py` only after WS-A0: a concept becomes the `(LexicalEntry, OntologyReference)` pair (an entry has senses; a reference may be pointed at by multiple senses), and canonical concept reads go through artifact families/store rather than a direct `load_document(..., ConceptDocument, ...)` path.
- `source/alignment.py`: **remove the Jaccard fallback**. Reconciliation tries `LexicalEntry` identity → `Form` identity → `OntologyReference` equality. If all miss, candidates are proposed on the proposal branch with `status="alignment_candidate"`. Jaccard is *gone*, not demoted.
- CLI: `pks concept` and `pks form` reshape around lemon.
- Validation: `validate_concepts.py` checks lemon invariants (entry has ≥1 sense; sense has ≤1 reference; homography permitted at entry level, polysemy at sense level).
- Property tests: lemon structural invariants; homograph vs. polyseme distinction.
- New authored concepts use lemon entries directly. Do not add a flat-concept migration path, default-sense backfill, or alias compatibility bridge.

**Phase 2 exit:** Buitelaar + OntoLex-Lemon notes non-stub; `docs/lemon-concepts.md` exists; `propstore/core/lemon/` package live; `form_utils.py` split completed; `source/alignment.py` Jaccard removed; CLAUDE.md's concept/semantic paragraph updated.

### Phase 3 — Qualia, proto-roles, and description-kinds

**Two reframing notes preceded this phase. Both materially change what gets implemented; read the layered history before proceeding.**

**First reframe (FrameNet drop):** an early draft committed to a FrameNet inventory import. FrameNet is a *lexicographic catalog* — `Causation.Cause` is a string label with a prose definition, not a typed slot with entailments. Fillmore 1982 is a pre-formal conceptual paper that motivated FrameNet's taxonomic work, not a formalism target. We dropped FrameNet entirely in favor of formalisms that have actual algebra: Pustejovsky qualia (type-driven coercion) and Dowty proto-roles (graded entailments that predict argument realization).

**Second reframe (Davidsonian event drop — events as defeasible coreference):** the post-FrameNet draft committed to Davidsonian / neo-Davidsonian events as first-class typed individuals (Parsons 1990). On closer reading, Davidson required event identity to be a metaphysical fact about the world — same causes/effects (1969, abandoned as circular), then sameness of spatiotemporal region (1985, contested). propstore is not in the business of asserting metaphysical identity conditions; doing so would re-introduce the kind of pre-descriptive individuation that the project's non-commitment discipline rejects elsewhere. We are dropping Davidson, dropping Parsons, dropping the `Event` type, dropping `causes`/`precedes`/`overlaps` as primitives between determinate event referents.

What replaces them: description-kinds as concepts; particular descriptions as claims; coreference between descriptions resolved by Dung-style argumentation over merge proposals at render time. The full position belongs in `docs/event-semantics.md` before shipping description-kind behavior. This is a non-Davidsonian implementation decision: Davidson, Parsons, Hobbs, Quine, and Putnam are useful rejection/background context, but they are not retrieval blockers for the executable type system.

What survives from the previous draft: Pustejovsky qualia (composes over description-kind concepts), Dowty proto-roles (decorates participant slots on description-kind senses), TIMEPOINT-anchored Allen-1983 temporal reasoning (description-claims are temporally located via the existing solver; nothing changes here), and the `worldline/` cross-reference (an agent's worldline is the agent's own trajectory through their own description-claims — the physics metaphor fits more naturally under the descriptivist reading, where a worldline is also relative to an observer's frame).

**Papers (primary, read fully before coding this phase):**
- Pustejovsky 1991 — qualia structure with type-driven coercion. Composes over description-kind concepts.
- Dowty 1991 — proto-agent / proto-patient graded entailments. Decorates participant slots.

**Papers (secondary, read for context):**
- Fillmore 1982 — understand the mental-frame motivation before implementing Pustejovsky's formalization.
- Hobbs 1985, Quine 1968, and late-period Putnam — optional explanatory background for the non-Davidsonian descriptivist position. Do not block implementation on these unless `docs/event-semantics.md` needs a new philosophical argument not already covered by the repo decision.

**Papers (optional):** Pustejovsky 2013+ (qualia refinements), Jackendoff 1990 (alternative semantic ontology for comparison), Levin-Rappaport Hovav 2005 (argument-realization theory operationalizing Dowty).

**Read for "what we are explicitly NOT doing and why":**
- Davidson 1967, *The Logical Form of Action Sentences*. Read to understand the position propstore rejects, and why event-as-individual was tempting.
- Davidson 1969 + 1985 essays on event identity. Read to see the metaphysical commitment we are not making.
- Parsons 1990, *Events in the Semantics of English*. The clean neo-Davidsonian reference; instructive as the maximally-developed version of the position we are choosing against.

**NOT implementation targets:** Baker 1998 (FrameNet operationalization), the FrameNet inventory, Davidsonian or neo-Davidsonian event reification. No `Event` type. No event-individuation primitives. No `causes(e1, e2)` between determinate event referents.

**Scope:**

*Qualia (Pustejovsky):*
- Design `QualiaStructure(formal, constitutive, telic, agentive)` with each field `list[QualiaReference] | None`.
- Each `QualiaReference(reference: OntologyReference, type_constraint: TypeConstraint | None, provenance: Provenance)`. Typed, not just a pointer.
- Implement **type-driven coercion**: if a predicate expects type T and an argument has type U, walk the argument's qualia for a coercion path (typically TELIC) that produces a T-typed view. Coercion is explicit — every coerced reference records the coercion path in its provenance so downstream reasoning can trace "we got a readable thing by coercing a book through its TELIC."
- Property tests: coercion soundness (coerced view satisfies target type); qualia transitivity (if X's TELIC is Y and Y's TELIC is Z, there is a recoverable purposive chain X → Z); qualia invariants (e.g. FORMAL is stable under coercion; AGENTIVE preserves a source witness).

*Description-kinds (replacing the Davidsonian event subsection):*

**Anchor before designing.** Two existing facts about propstore shape the description-kind type design:

1. **Temporal anchoring reuses `KindType.TIMEPOINT`.** Description-claims are not a new coordinate system. They live in the temporal coordinate propstore already implements: `cel_checker.KindType.TIMEPOINT` (maps to `z3.Real`) + `Z3ConditionSolver` providing Allen-1983 interval reasoning over real-valued constraints. A description-claim's temporal location uses TIMEPOINT-valued concept-references; temporal relations between description-claims (precedes, overlaps, during, equals, starts, finishes, ...) resolve via Z3 conjunction over the existing real-valued interval constraints. Per-claim `valid_from`/`valid_until` scoping (today's shape exercised in `tests/test_temporal_conditions.py`) remains the mechanism. **Do not build a second temporal layer; description-claims ride on the first.**

2. **`worldline/` is the natural home for an agent's description trajectory.** propstore's `worldline/` module tracks an agent's trajectory through epistemic state. In the descriptivist event model, a worldline is the agent's own sequence of description-claims (observations, measurements, assertions, decisions made by that agent over time). The physics metaphor — a worldline as the timelike trajectory from an observer's frame of reference — fits naturally; in physics too, a worldline is relative to a frame, not an objective fact about the universe. The module's existing types (`worldline/trace.py`, `worldline/revision_capture.py`, `worldline/argumentation.py`) likely want to be revisited so trajectory entries are description-claims rather than a parallel-invented type. **Read worldline/ before designing description-kind types to make sure they compose, not collide.**

*Concrete deliverables for description-kinds:*

- Define seed description-kind concepts as lemon LexicalEntries with senses carrying participant slots:
  - `Observation` — slots: observer, observed, instrumentation, temporal-location, conditions.
  - `Measurement` — slots: quantity-measured, value, instrument, units, temporal-location, conditions, calibration-reference.
  - `Assertion` — slots: asserter, asserted-claim, temporal-location, source, evidential-basis.
  - `Decision` — slots: decider, decision-content, temporal-location, options-considered, justification.
  - `Reaction` — slots: reactants, products, conditions, temporal-location, reaction-type.
- Each slot carries a `type_constraint: OntologyReference` and a `proto_role_bundle: ProtoRoleBundle | None` (Dowty proto-role decorations on the description-kind's argument structure).
- Description-claims are claims of these concepts. They live in `claim_core` like every other claim. Their `predicate` is the description-kind concept; their bindings are the slot-value assignments.
- A description-claim's temporal location is a TIMEPOINT-valued slot binding; temporal reasoning over multiple description-claims uses the existing Z3+Allen machinery on those slot bindings.
- **No `Event` type. No `EventStructure`. No `EventReference`. No `causes(e1, e2)` primitive between determinate event individuals.** Causal connection is itself a *causal-connection assertion* — a description-kind whose participants are two other description-claims and whose `account: Literal["stated", "counterfactual", "statistical", "mechanistic"]` tag carries the kind of causal claim being made. Causal-connection assertions are claims like any other; they have provenance, they can be merged, attacked, defeated.
- **Coreference between description-claims is not a stored relation; it is a render-time inference.** Two description-claims that the system or a user might "treat as describing the same event" do so under an explicit merge-hypothesis. The merge-hypothesis is a Dung argument; its acceptance is policy-dependent (which extension of the argumentation framework, which assumption-set in ATMS terms). The render layer surfaces a `MergedDescriptionCluster` as the answer to "give me the cluster of descriptions about X" — but the cluster is computed at query time, the merge-justification is inspectable, and rival cluster-hypotheses survive in storage.
- Property tests for the description-kinds:
  - Slot-binding type-constraint enforcement.
  - Description-claims compose with provenance (every binding has its source recoverable via provenance).
  - Temporal reasoning over description-claim timestamps reduces to the existing Z3+Allen path; no new solver required.
  - Coreference query (given two description-claims, return the merge-argument for treating them as co-referring) returns a Dung argument structure; the argument's acceptance under different semantics yields different cluster compositions; storage is policy-invariant.
  - For causal-connection assertions: transitivity is *conditional* on the `account` tag; "stated" causation does not imply "counterfactual" causation. Don't try to bake a unified causal closure into the type.
- Description-claims compose: a participant of one description-claim can itself be another description-claim (a causal-connection assertion has two description-claims as its participants; an assertion-claim's `asserted-claim` slot can be filled by another claim, including another description-claim; nested narratives are description-claims whose participants include description-claims about the same temporal region).
- Temporal primitives apply at the description-claim level via the existing Z3+TIMEPOINT machinery — no new solver. Two description-claims with TIMEPOINT-valued temporal-location slots can be checked for Allen-relation disjointness/overlap via Z3 conjunction over the slot bindings. The 13 Allen relations apply at the description-claim level; a thin module on top of `Z3ConditionSolver` provides them. There is no separate event-temporal layer because there is no event individual to anchor.

*Proto-roles (Dowty):*
- Design `ProtoRoleBundle(proto_agent_entailments, proto_patient_entailments)`.
- Each entailment: `GradedEntailment(property: ProtoRoleProperty, value: float ∈ [0,1], provenance: Provenance)`. Dowty's proto-agent properties: volition, sentience, causation, movement, change-of-state. Proto-patient: affected, incremental theme, stationary, causally affected, change-of-state.
- Graded, not binary — Dowty's paper argues entailments vary in strength, and provenance-bearing grades let us express "moderate-strength causation entailment with witness X" honestly.
- Dowty's Argument Selection Principle as a property test: for relational concepts with proto-role bundles on both argument positions, the position with the higher total proto-agent entailment weight is predicted as syntactic subject. ASP should be stable under independent re-bundlings and transparent under composition.

*`LexicalSense` extension:*
- `qualia: QualiaStructure | None`
- `description_kind: DescriptionKind | None` (for description-kind concepts such as Observation, Measurement, Assertion, Decision, Reaction; None for non-description concepts)
- `role_bundles: dict[RoleName, ProtoRoleBundle] | None` (for relational concepts with nameable arguments)

*Fillmore-read:*
- Verify notes for Fillmore 1982 are non-stub in `papers/Fillmore_1982_FrameSemantics/notes.md`. The notes should explain the frame concept as cognitive structure and explain why propstore uses Pustejovsky qualia + Dowty proto-roles + description-kinds rather than FrameNet or Davidsonian event individuals.

*CLI:*
- `pks concept qualia-add`, `pks concept description-kind`, `pks concept proto-role` — the primary manipulation surface.

*Validation:*
- Qualia reference integrity (each QualiaReference points at an existing concept satisfying type_constraint).
- Description-kind slot type-constraint satisfaction.
- Proto-role entailment values in [0, 1].
- `GradedEntailment.provenance` mandatory (no silent defaults; same discipline as WS-A phase 1).

*Seed examples:*
- One canonical qualia-carrying concept: pick something from propstore's use case, e.g. `Measurement_Instrument` with TELIC pointing at the measurement activity it affords.
- One description-kind concept: e.g. `Measurement` with typed participant slots (quantity-measured, value, instrument, units, temporal-location), each with provenance-bearing bindings.
- One relational description-kind replacing a "frame label": `Causal_Connection` as a description-kind whose participants are two other description-claims and whose `account` tag distinguishes stated/counterfactual/statistical/mechanistic claims.

**Phase 3 exit:** Pustejovsky 1991, Dowty 1991, and Fillmore 1982 notes verified non-stub; `docs/event-semantics.md` exists with the non-Davidsonian descriptivist position statement; `docs/qualia-and-proto-roles.md` exists describing the implemented semantics; modules `propstore/core/lemon/qualia.py`, `propstore/core/lemon/proto_roles.py`, `propstore/core/lemon/description_kinds.py` (NOT `events.py` — the naming matters) live; seed description-kind concepts (`Observation`, `Measurement`, `Assertion`, `Decision`, `Reaction`) defined in the seed knowledge tree; property tests green for qualia coercion, proto-role-driven argument selection, slot-binding type enforcement, coreference-as-Dung-argument behavior; the existing TIMEPOINT-based per-claim scoping (per `tests/test_temporal_conditions.py`) continues to pass unchanged; `worldline/` reviewed and either adopted as the agent's-description-trajectory consumer or deliberately left unchanged with a documented reason; CLAUDE.md's concept-content paragraph updated with honest description (qualia + proto-roles + description-kinds — no "frame semantics" rhetoric, no FrameNet reference, no Davidsonian-event reference).

### Phase 4 — Contexts + micropublications

**Cross-reference to phase 3's descriptivist event reframe.** Under the descriptivist event semantics committed to in phase 3 (see `docs/event-semantics.md`), contexts are interpretable as description-clusters: a `Context` may *be* the cluster of descriptions propstore informally calls "the Stanford Prison Experiment" or "the 2024 RHIC run." McCarthy's `ist(c, p)` reads as "p is true in the context of (the inference cluster I am calling) c," where the cluster's coherence is itself a defeasible Dung argument. This composes cleanly with WS-C's CKR justifiable exceptions: an exception is "this generalization holds in cluster c, except in the cases described by these other description-claims." No new type machinery is required for the descriptivist reading — the existing `Context` design extended in this phase already supports it. Make this connection explicit in `docs/contexts-and-micropubs.md`.

**Papers:** Clark 2014 (dedupe first, then process), McCarthy 1993, Guha 1991. Fetch: Giunchiglia-Serafini 1994 (local model semantics); McCarthy-Buvac 1997 (formalizing context, expanded notes). Cross-reference Bozzato 2018 (already in corpus for WS-C). The Guha artifact is the thesis _Contexts: A Formalization and Some Applications_, covering the formalization and applications entries previously listed separately.

**Scope:**
- **Dedupe Clark_2014 directories.** Canonicalize to `Clark_2014_Micropublications/` (drop `MicropublicationsSemanticModel` suffix). Merge unique content from the stale dir, ensure the PDF is in the canonical dir, delete stale, update `papers/index.md`.
- Process all four priority papers + Giunchiglia-Serafini 1994 + McCarthy-Buvac 1997 to non-stub depth.
- Design `Context` as a first-class logical term with identity, structure, composition. Commit to **structured contexts** (carrying assumptions, parameters, perspective) rather than opaque handles — structured is what McCarthy's philosophical framework + Guha's operationalization + Bozzato's CKR all push toward.
- Design `LiftingRule` per Guha 1991 bridge rules + Bozzato 2018 justifiable exceptions (the WS-C prep). Concrete types for lifting rules that fit the DL-Lite-adjacent decidable fragment where possible, falling back to sound-but-incomplete reasoning with Z3 routed for decidable subqueries.
- Design `ist(c, p)` as the primary claim shape. **Commit to nested `ist` at the type level now** — a context can contain `ist`-statements that reference contexts. Operational reasoning over nested contexts can land later; the type shape is cheap now.
- Design `Micropublication` per Clark 2014: bundle of claims + evidence references + assumption set + stance + provenance. **Each micropub IS an ATMS node.** The label algebra in `world/atms.py` + `core/labels.py` gains context dimension.
- `ClaimDocument` grows `context: ContextReference`.
- New `MicropubDocument`.
- `context_hierarchy.py` → `context_lifting.py`. **Visibility inheritance is retired, not demoted.** New authored contexts use explicit lifting rules directly; do not add old hierarchy migration code.
- `source/` emits micropubs, not bare claim bundles. `finalize.py` composes into micropubs. `promote.py` promotes whole micropubs atomically.
- CLI: `pks context` presents first-class contexts; `pks micropub show / bundle / lift` commands; `pks claim` takes context argument.
- ATMS property tests extended with context dimension: labels still minimal + consistent + complete + sound; context-lifting preserves label invariants.
- Property tests: `ist`-composition under lifting; micropub well-formedness; context identity; nested-`ist` parsing and round-trip; ATMS label algebra with context dimension.
- New authored claims require an explicit context. Do not add a default-`GLOBAL` migration path, hierarchy-to-lifting auto-generator, or visibility compatibility bridge. Visibility inheritance dies.

**Phase 4 exit:** Clark dedupe complete; Clark 2014, McCarthy 1993, Guha 1991, Giunchiglia-Serafini 1994, McCarthy-Buvac 1997, and Bozzato 2018 at non-stub depth; `docs/contexts-and-micropubs.md` exists; context/lifting modules live; claim representation migrated; ATMS label algebra extended; CLAUDE.md's context + micropublication paragraphs updated.

## What you are NOT doing

- **Not fully implementing context-qualified attacks in the argumentation layer.** The data structures permit it after this workstream; the argumentation-layer reasoning over context-qualified attacks/defeats is *future* work. Types support it; semantics can evolve.
- **Not importing FrameNet.** FrameNet is a lexicographic catalog without formal algebra — `Causation.Cause` is a string label with a prose definition, not a typed slot with entailments. Propstore is not an NLP parser; the inventory adds no formal content we can reason over. The structural frame-like commitment is Pustejovsky qualia + description-kinds-as-concepts + Dowty proto-roles, which *do* compose algebraically without Davidsonian event individuals. (If a later project decides to consume natural-language text and bind it to propstore concepts, FrameNet-style parsing could live in a separate heuristic workstream feeding proposal branches. Not this workstream.)
- **Not touching `revision/`, `world/ic_merge.py`, `aspic*`, `praf/`, `grounding/`, `conflict_detector/` except where they must consume the new types.** The argumentation + revision + defeasibility + merge subsystems are other workstreams. Your scope is the concept/semantic substrate + provenance + claim representation.
- **Not building LLM-driven classifiers for frames / qualia / contexts.** Those are heuristic layer concerns and belong on proposal branches; they can be added later as independent heuristic workstreams.
- **Not committing to full DL-Lite semantics.** Use CKR's *structure* over propstore's richer claim language; accept sound-but-incomplete reasoning at the top; route decidable subqueries to Z3.

## Papers (comprehensive list)

See `../../../semantic-substrate-papers.md` at the repo root for the canonical list and retrieval state. Quick reference:

**Phase 1:** Buneman 2001, Carroll 2005. Optional: Moreau 2013, Green 2007.

**Phase 2:** Buitelaar 2011. Fetch: OntoLex-Lemon community report (Cimiano/McCrae/Buitelaar 2020+).

**Phase 3:** Pustejovsky 1991, Dowty 1991. Secondary: Fillmore 1982 (concept grounding only, not implementation target). Optional explanatory/rejection context: Hobbs 1985, Quine 1968, late-period Putnam, Davidson event papers, Parsons 1990. NOT implementing: FrameNet (Baker 1998 is read-for-context only; the Berkeley inventory is not imported), Davidsonian or neo-Davidsonian event reification.

**Phase 4:** Clark 2014 (deduped), McCarthy 1993, Guha 1991. Fetch: Giunchiglia-Serafini 1994, McCarthy-Buvac 1997. Cross-reference: Bozzato 2018.

The required implementation papers for the non-Davidsonian path are present in `./papers` as of 2026-04-17. Optional explanatory/rejection-context papers are not blockers.

## Red flags — stop if you find yourself

- About to add a `"legacy"` status value to `Provenance`.
- About to preserve Jaccard reconciliation "as a fallback."
- About to keep visibility inheritance as a default lifting rule.
- About to defer nested `ist` to a future workstream.
- About to use `list[OntologyReference]` as the qualia structure (loses typed coercion — the generative bit).
- About to import FrameNet, ship a frame inventory, or add a `FrameBinding` type.
- About to add an `Event` type, `EventStructure`, `EventReference`, `TemporalAnchoring`, or `causes(e1, e2)` primitive between determinate events. **There is no event individual.** See `docs/event-semantics.md`. Description-kinds are concepts; particular descriptions are claims; coreference is a Dung argument resolved at render time.
- About to commit to Davidsonian or neo-Davidsonian event identity. propstore rejects the metaphysical commitment (Davidson 1969 causal identity, Davidson 1985 spatiotemporal identity). Read the position statement before any type design that could re-introduce event-as-individual.
- About to model `Causation` as anything other than a description-kind whose participants are two other description-claims and whose `account` tag distinguishes the kind of causal claim being made.
- About to fabricate a default prior instead of marking `status="vacuous"`.
- About to build a parallel per-repo provenance table or side-car index. The storage mechanism is **git-notes on a dedicated notes ref** (`refs/notes/provenance`) via `dulwich.notes`. No parallel table. Named-graph payloads live inside the note contents; git's object model handles dedup. If you find yourself writing `CREATE TABLE provenance (...)`, stop — the wrong mechanism.
- About to write a backward-compat shim for old schemas.
- About to make `ConceptDocument` lemon-shaped while `propstore/core/concepts.py` still directly decodes concept YAML or while non-CLI production modules still import `propstore.cli.repository`. Complete WS-A0 first.
- About to cite a paper for a formula you have not property-tested.
- About to start coding before the relevant paper's notes are non-stub.

Each is a principled-path violation. Stop, re-read `disciplines.md`, re-read `principled-path.md`, ask Q if still unsure.

## Exit criteria (workstream-level)

- All four phases' exit criteria satisfied.
- `uv run pytest tests/` green, including all new property tests.
- `uv run pyright --strict` green on all new modules in `propstore/core/lemon/`, `propstore/core/contexts/`, and `propstore/provenance.py`.
- CLAUDE.md's literature grounding section updated: semantic-substrate papers now cited with references to passing tests that verify the structural commitments.
- `docs/gaps.md` updated: axis-3d findings for each phase are resolved and removed; any new gaps discovered during the work are added with plan.
- The five fabrication/collapse patterns the review flagged are no longer *reachable* from the new type system — you cannot construct a probability without provenance; you cannot construct a `ResolutionDocument` with `(0,0,0,0.5)`; you cannot construct a `SourceTrust` without a `status`.

## On learning

This workstream involves reading 10+ papers deeply and integrating them into a coherent type system. That is a lot of reading. It is also a tremendous opportunity. These papers — Fillmore on frames, Pustejovsky on the generative lexicon, Buitelaar on lemon, McCarthy on contexts, Clark on micropublications, Buneman on provenance — are the intellectual substrate of essentially every principled knowledge-representation system in the next decade. Read them slowly. Take notes. Let them teach you.

The implementation is the payoff. The reading is the point.
