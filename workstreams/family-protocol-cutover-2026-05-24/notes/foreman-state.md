# Foreman state (~15:45 2026-05-25)

## Cut #34 LANDED — Quire batch_specs + multi-FK
Quire `e6eaed4 Add charter batch specs and multi foreign keys`. Propstore pinned `6b2ee445`. 350 Quire tests pass. 3526/4 propstore baseline.

## Cut #35 LANDED — Phase 05 PARTIAL
Commit `9dcb7f96 Move family protocol contracts to charters`.
Closed: V012 (FK tables), V013 (REFERENCE_KEYS), V016 (iter_document_schema_types), V017 (DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES).
Deferred (V014/V015): registry-owned source batch helpers + batch_specs.py kept with NOTE comments — Quire doesn't yet have generic batch IO to replace the handwritten callbacks. Batch specs themselves moved onto FamilyCharter.batch_specs.

## Trying Phase 06 next
Source lifecycle state machines. Major deletion targets: ClaimConceptSource type, rewrite_claim_concept_refs, normalize_source_claims_payload, source-loader fanout, concrete document fields in SourcePromotionPlan, root concept alignment workflow.

## Status
HEAD `9dcb7f96`. All gates clean. Phase 04 COMPLETE. Phase 05 partial. Continuing.

# Foreman state (~15:30 2026-05-25)

## Phase 05 blocked on more Quire-side work
Cut #32 H-D'd on Quire `FamilyCharter.batch_specs` (Phase 02 deferred).
Cut #33 (narrowed partial) H-D'd because Quire's `CharterField.foreign_key` is single-slot, but `concept.parameterization_relationships` needs TWO FKs (`concept_parameterization_input` + `concept_parameterization_canonical_claim`).

Both genuine Quire-side limitations needing more Phase 02 work.

## What landed (cumulative)
- Phase 01: DONE
- Phase 02: 6 Quire commits pushed; lifecycle/local-id/graph/FTS/batch_specs/multi-FK still deferred
- Phase 03: DONE
- Phase 04: 14 of 14 families CLOSED ✅
- Phase 05: blocked on Quire batch_specs + multi-FK (Cut #32 + #33 markers at HEAD)
- Phase 06, 07, 08: not touched (depend on Phase 05 + remaining Phase 02)
- Phase 09: V035, V036 done; V037-V039 done via Cut #28 worldlines
- Phase 10: V041, V042 done; V040 (root context_lifting) and V046 still
- Phase 11: V044 done; V043 needs Phase 02 local-id reservation
- Phase 12: not touched

## Stashes
- Cut #25 predicates retry was popped + landed in Cut #23 (commit cbd055d3)
- Cut #25 stances was popped + landed as Cut #25 (commit 9a35cfc4)
No remaining stashes.

## Final state
HEAD `1848786d Record cut33 phase05 partial blocker`. Working tree clean. Test suite at baseline.

## Cut #31 LANDED — CLAIMS FAMILY CLOSED — 14/14 PHASE 04 COMPLETE

## CUT #31 LANDED — CLAIMS FAMILY CLOSED — 14/14 PHASE 04 COMPLETE
HEAD `6cee7e70 Phase 04 claims: author AUTHORED_CLAIM_CHARTER alongside compiled sibling charters`. ALL 14 of 14 Phase 04 families fully closed.

Final family: forms, contexts, justifications, sources, micropubs, sameas, stances, merge, source_alignment, worldlines, predicates, rules, concepts, claims.

Alongside-charter pattern (Cuts #29 rules, #30 concepts, #31 claims) for spec-level-complex families: add AUTHORED_*_CHARTER capturing the authored input shape as JSON blobs ALONGSIDE the existing compiled storage charters. Preserves the compile pipeline while typing the authored surface.

Cut #31 specifics:
- AUTHORED_CLAIM_CHARTER added; 47 importers updated; full ClaimDocument tree replaced by generated_document()
- ClaimTypeContract registry moved into declaration.py
- OpinionDocument invariants preserved via Quire validator hook
- Full suite 3526/4 baseline; pyright 0/0/0; lint-imports kept

## Phase 04: 14 OF 14 FAMILIES CLOSED ✅


## Cut #29 LANDED — rules family closed
HEAD `88e6beee Phase 04 rules: author AUTHORED_RULE_* charters + replace handwritten documents`. **12 of 14 Phase 04 families closed.**

Added authored-rule charters ALONGSIDE existing grounded-runtime charters. Nested JSON-blob types kept. Registered AUTHORED_RULES_FAMILY_CONTRACT_VERSION. All gates clean.

## Final Phase 04 state
Closed (12): forms, contexts, justifications, sources, micropubs, sameas, stances, merge, source_alignment, worldlines, predicates, rules.
Remaining 2: claims, concepts (both genuinely hard — multi-charter aggregation / lemon-tree).

## Phase tallies
- Phase 01: DONE
- Phase 02: Substantial Quire foundation (6 commits pushed); lifecycle/local-id/graph/FTS/__init__ removal still deferred
- Phase 03: DONE
- Phase 04: 12 of 14 families closed
- Phase 05-08: NOT TOUCHED
- Phase 09: PARTIAL — V035 full, V036
- Phase 10: PARTIAL — V041, V042
- Phase 11: PARTIAL — V044
- Phase 12: NOT TOUCHED



## Cut #23 predicates SALVAGED — about to commit
- App-layer arity validation relaxed (allow empty arg_types) to mirror charter validator
- Merge-conflict markers from stash-pop resolved in registry.py + contracts.py (kept both merge and predicates imports)
- PROPOSAL_PREDICATES bumped to PREDICATE_FAMILY_CONTRACT_VERSION (was using PROPOSAL_DECLARATION_ARTIFACT_FAMILY_CONTRACT_VERSION which was stale relative to body change)
- Contract manifest tests pass 8/8

Running full suite then commit.


## Cut #23 predicates retry (~14:00)
Popped predicates stash. Had merge conflict markers in registry.py (stash base was older than HEAD). Resolved conflict to keep BOTH `merge` and `predicates` family imports. Runtime import succeeds; pyright stale-cache warnings will clear after .venv refresh. Relaxed app/predicates.py arity check to mirror charter validator (allow empty arg_types).

Running full suite to verify.


## Cut #28 worldlines LANDED — HEAD 6a8008e3 → 9f91085d (morning status update)
**10 of 14 Phase 04 families closed.** Worldlines authored with WORLDLINE_DEFINITION_CHARTER, WORLDLINE_RESULT_CHARTER, WORLDLINE_REVISION_STATE_CHARTER, WORLDLINE_JOURNAL_CHARTER. Renamed `values` column to `target_values` with `document_name="values"` to avoid SQL reserved-word collision (the test_world_model_branch_column_required.py H-C fix).

## Final Phase 04 state at ~13:45
Closed (10): forms, contexts, justifications, sources, micropubs, sameas, stances, merge, source_alignment, worldlines.
Remaining 4 require SPEC-LEVEL Q DECISIONS per audit:
- **claims** — multi-charter aggregation; ClaimDocument compiles into 5 sibling rows
- **concepts** — lemon authored shape vs compiled charter shape; charter has compiled-derived columns, document has ontology/lexical/qualia tree
- **predicates** — app-layer validation in propstore/app/predicates.py rejects empty arg_types before charter validation
- **rules** — authored DeLP rules blob-stored in grounded_bundle_input.payload; needs separate authored-rule family

Each of these has audit-noted complexity that exceeds "author charter + delete handwritten." Not mechanical cuts.

## Quire commits all pushed (6)
85acdb5b, 11335ce5, d47159a, 95d2e66, b8990ca, 5852fc6.

## Stashes
- Cut #23 predicates (`On master: Cut #23 predicates retry`) — partial work; needs deeper app-layer validation refactor

## Phase tallies
- Phase 01: DONE
- Phase 02: Substantial Quire foundation (6 commits pushed); lifecycle/local-id/graph/FTS/__init__ removal still deferred
- Phase 03: DONE
- Phase 04: 10 of 14 families closed
- Phase 05-08: NOT TOUCHED (depend on Phase 04 + remaining Phase 02)
- Phase 09: PARTIAL — V035 (full), V036 closed
- Phase 10: PARTIAL — V041, V042 closed
- Phase 11: PARTIAL — V044 closed (V043 needs Quire local-id reservation = Phase 02 deferred)
- Phase 12: NOT TOUCHED

## Cut #26 LANDED — merge family closed

## Cut #26 LANDED — merge family closed
HEAD `32e6f9b3 Phase 04 merge: author MERGE_MANIFEST_CHARTER + replace handwritten document`. 8 of 14 Phase 04 families now closed: forms, contexts, justifications, sources, micropubs, sameas, stances, merge.

Gates all clean: pyright 0/0/0, lint-imports kept, full suite 3526/4 baseline. Atomic commit.

## Remaining Phase 04 families (6)
- predicates — stashed (Cut #23): validator-too-eager at app/predicates.py:154 (not just charter validator); needs deeper app-layer fix
- claims — BLOCKED: multi-charter aggregation (compiles into 5 sibling charter rows + concept-link rows from ClaimTypeContract)
- concepts — BLOCKED: lemon nested tree + __post_init__ on LexicalEntryDocument
- rules — BLOCKED: authored rules stored as JSON blob inside grounded_bundle_input.payload (separate charter family needed)
- source_alignment — audit says transient (2 importers, render-layer)
- worldlines — audit says render-layer, exclude

## Stashes
- Cut #23 predicates (`On master: Cut #23 predicates retry`)
- Cut #25 stances was POPPED + landed as Cut #25 atomic commit `9a35cfc4`

## Quire state
6 commits all pushed to ctoth/quire:
- 85acdb5b — typed attrs
- 11335ce5 — generated_document + document_codec
- d47159a — nullable + document_name + union safety
- 95d2e66 — parse_boundary="json" codec
- b8990ca — SQLAlchemy TypeDecorator
- 5852fc6 — FamilyCharter.validators

## Phase status
- Phase 01: DONE
- Phase 02: PARTIAL (lifecycle/local-id/graph/FTS/__init__ removal still deferred)
- Phase 03: DONE
- Phase 04: 8 of 14 families closed
- Phase 05-08: NOT TOUCHED
- Phase 09: PARTIAL (V035, V036 closed)
- Phase 10: PARTIAL (V041, V042 closed)
- Phase 11: PARTIAL (V044 closed)
- Phase 12: NOT TOUCHED

Continuing to try one more family if possible.
