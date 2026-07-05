# SLICE 13 — claims @charter migration notes

Date: 2026-05-28/29. Branch recovery/may-28-curated-good. Quire pin d75b4bcd.

## Goal
Convert all hand-written `*Document`/`FamilyModel` classes in
`propstore/families/claims/declaration.py` to declarative `@charter` classes.
Contract manifest must regenerate BYTE-IDENTICAL (the arbiter).

## Verified facts (from reading source)
- charter_class API (quire/quire/charter_class.py) supports everything needed:
  `family_foreign_keys`, `reference_keys`, `extra_columns` (ColumnSpec via
  `column()`), `indexes`, `fts`, `vector_caches`, `relationships`,
  `states`/`transitions`, `validators`, `batch` (factory or DocumentBatchSpec,
  single OR tuple), `model_mixin`, `model_name`. Per-field via
  `Annotated[T, charter_field(...)]`.
- Recursive tagged-union PROVEN by quire/tests/test_charter_class_recursive.py:
  `class IstPropositionDocument(CharterDoc, tag="ist")` with
  `proposition: Annotated["AtomicPropositionDocument | IstPropositionDocument", charter_field(json=True)]`.
  tag_field default — CHECK: today's structs use `tag_field="kind"`. Probe needed
  to confirm tag_field carries (test used bare `tag=`, default tag_field is "type"
  in msgspec). THIS IS A REAL RISK — claims uses tag_field="kind".
- `@charter` generates model via `type(model_name, bases, {})`. model_mixin → the
  generated model inherits it. Binds generated model into module globals under
  model_name.
- `nullable` resolved explicitly always; `T | None` → nullable=True inner T.
- document_name: `charter_field(column_name=X)` sets column_name=X AND
  document_name=attr (the rename). So attr name = doc field name, column_name = storage.

## The collision (AUTHORED_CLAIM)
- attr `artifact_id` with column_name="id" (doc name artifact_id, col id), document_order=3
- attr `id` with column_name="source_local_id" (doc name id, col source_local_id)
- So in declarative class: two attributes `artifact_id` and `id`, each Annotated.

## JUSTIFICATION model = EXTERNAL class (KEY DIFFERENCE)
- `Justification` lives at propstore.core.justifications (real behavior FamilyModel:
  premise_ids, provenance_record, to_canonical). NOT a local pass model.
- Today JUSTIFICATION_CHARTER uses `model=Justification`, `doc_type=Justification`.
- `world/model.py:29` imports `Justification` from core.justifications (the model used
  in queries). `compile_authored_justification_models_*` constructs `Justification(...)`.
- PLAN: `@charter(model_mixin=Justification, model_name="Justification")` on
  JustificationDocument → generates a NEW model class named Justification in claims
  module inheriting behavior. BUT world/model.py imports the ORIGINAL from
  core.justifications. RISK: two distinct class objects both named Justification.
  Need to verify which one the schema/registry binds and whether manifest cares.
  DECISION POINT — may need to keep JUSTIFICATION hand-written OR verify model identity.
  registry.py uses JUSTIFICATION_CHARTER.family / generated_document() — manifest reads
  doc_type. Must confirm with manifest diff.

## Claim model = behavior mixin
- `Claim` (claims:765) has many properties/methods → model_mixin=ClaimBehavior,
  model_name="Claim". Generated model named Claim bound to module → importers
  `from ...claims.declaration import Claim` keep working.
- compile_claim_models constructs `Claim(**claim_values)` with COLUMN names
  (id, primary_logical_id, ...) — generated model must accept these kwargs. It will
  (FamilyModel kwargs).

## Registered codecs (MUST stay free functions, same qualname)
- `claim_document_to_payload` — registered as CLAIM_FAMILY `document_payload=` in
  registry.py:371. STAYS free function at module qualname. ClaimDocument.to_payload
  METHOD delegates to it.
- `justification_document_to_payload` — used by compile fn + registry? check. Used in
  declaration.py compile + as JustificationDocument.to_payload. Keep free fn.

## Charters to migrate (13) + order (leaf-first)
Pop-B nested first: ClaimLogicalId, ClaimSource, Provenance(SHARED-keep name
ProvenanceDocument), FitStatistics, VariableBinding, ParameterBinding, Resolution,
StanceDocument(claims), AtomicProposition(tag), IstProposition(tag+recursive),
JustificationProvenance, JustificationAttackTarget.
Then charters: AUTHORED_CLAIM(ClaimDocument), CLAIM_CORE(Claim), CLAIM_CONCEPT_LINK,
3x CLAIM_PAYLOAD, CLAIM_SOURCE_ASSERTION, JUSTIFICATION, EXTRACTION_PROVENANCE,
SOURCE_PROVENANCE, SOURCE_ATTACK_TARGET, SOURCE_CLAIM_DOCUMENT, SOURCE_JUSTIFICATION.
3 batch specs: CLAIM_BATCH_SPEC, SOURCE_CLAIM_BATCH_SPEC (on AUTHORED_CLAIM),
SOURCE_JUSTIFICATION_BATCH_SPEC (on JUSTIFICATION).

## BASELINE (current HEAD ebaa9958, BEFORE edits)
- manifest git diff: CLEAN (empty).
- pyright propstore: 0 errors, 0 warnings.
- focused tests (test_claim_compiler, test_source_claims, test_core_justifications,
  test_justification_rule_kind_validated, test_validate_claims, test_claim_type_contracts,
  test_promote_claim_immutability): 119 passed, 1 FAILED.
- PRE-EXISTING FAILURE (NOT a regression):
  test_source_claims.py::test_claims_document_produced_by_roundtrip —
  `'SourceClaimDocument' object has no attribute 'to_payload'`. Today's code never
  attaches to_payload to SourceClaimDocument (loop at :759 only does 10 Pop-B classes).
  PLAN: migration gives SourceClaimDocument a real to_payload method (delegate to
  _claim_struct_payload) → FIXES this pre-existing failure. Method, not a field → no
  manifest churn. Confirm manifest still byte-empty after.

## PROBES (all passed, .tmp/probe_claims_charter.py — REMOVE before done)
1. tagged-union tag_field="kind" self+sibling recursive: roundtrips, kind tag emitted.
2. external behavior class as model_mixin: generated model inherits it + FamilyModel.
3. id/source_local_id document_name collision: col id->doc artifact_id, col source_local_id
   ->doc id, document field names [context, artifact_id, id]. CORRECT.

## PROGRESS (rewrite complete)
- All 13 charters + 12 Pop-B + 2 behavior(Claim mixin)/external(Justification mixin) +
  3 batch specs migrated to @charter declarative classes.
- Module IMPORTS OK. Claim MRO = Claim->ClaimBehavior->FamilyModel. batch specs attached.
- Decision made: CLAIM_CORE/payload plain fields that hand-written left nullable-unspecified
  declared with explicit nullable=True (so SQL nullable preserved). Plain str/int annotation
  + nullable=True. RISK identified: may churn manifest to `str|None`. TESTING NOW.
- contract-manifest --write ran; `git diff --stat` printed NOTHING after ===DIFF=== →
  likely EMPTY (byte-identical). MUST confirm explicitly with git diff exit code.

## GATE RESULTS (post-rewrite)
- GATE 1 pyright propstore: 0 errors (==baseline). [fixed ClaimBehavior-before-stub order]
- GATE 4 manifest byte-empty: YES (git diff --quiet passes). THE ARBITER PASSED.
- GATE 3 pks build: SUCCESS (24 concepts rebuilt, schema built clean).
- GATE 2 focused tests: 120 passed, 0 failed (baseline was 119+1). FIXED the pre-existing
  test_claims_document_produced_by_roundtrip via SourceClaimDocument.to_payload method.
- WIDER sweep: 37 passed, 3 FAILED in test_render_policy_direct_claim.py:
  sqlite3.OperationalError: table relation_edge has no column named opinion_belief.
  This is RELATIONS family (relation_edge table, projection_model.py opinion_belief col) —
  NOT claims. Only claims/declaration.py is modified (git diff --name-only confirms).
  HYPOTHESIS: pre-existing failure unrelated to claims migration. VERIFYING with git show
  HEAD:claims file swap (non-destructive). Do NOT claim regression without proof.

## DONE — committed e9d7beb7 (2026-05-29)
- 766 insertions, 1017 deletions, 1 file (claims/declaration.py only).
- 3 opinion_belief failures PROVEN pre-existing: ran test_render_policy_direct_claim.py
  against git-show HEAD claims file (non-destructive swap), failed IDENTICALLY → relations
  family schema bug (relation_edge missing opinion_belief col, projection_model.py), NOT claims.
  Out of scope (relations = SLICE 17). Path forward: relations slice must reconcile
  relation_edge charter columns with projection_model opinion_belief expectation.
- importer sweep (merge, web routes, compiler quarantine pipeline): 12 passed.
- probes removed.

## NEXT STEPS (none — slice complete)
1. Capture baseline: pyright propstore, claim/justification tests, manifest git diff (empty expected).
2. Probe tag_field="kind" under @charter in .tmp/.
3. Probe Justification external-model-as-mixin manifest behavior (small).
4. Rewrite declaration.py.
5. Gate: pyright=0, tests green, pks build, manifest byte-empty, commit.

## MANIFEST naming + ORDER rules (the arbiter)
- Document name = decorated class __name__. So decorated classes must be named:
  ClaimDocument (AUTHORED_CLAIM), Claim_coreDocument (CLAIM_CORE),
  Claim_concept_linkDocument, Claim_numeric_payloadDocument, Claim_text_payloadDocument,
  Claim_algorithm_payloadDocument, Claim_source_assertionDocument, JustificationDocument,
  ExtractionProvenanceDocument, SourceProvenanceDocument, SourceAttackTargetDocument,
  SourceClaimDocument, SourceJustificationDocument. (Public importers want the simple ones;
  CLAIM_CORE/payload class names are internal — alias to Claim_coreDocument exactly to match
  the auto-name the hand-written charter emitted.)
- Pop-B class names kept EXACT (manifest field types ref them fully-qualified):
  ClaimLogicalIdDocument, ClaimSourceDocument, ProvenanceDocument, FitStatisticsDocument,
  VariableBindingDocument, ParameterBindingDocument, ResolutionDocument, StanceDocument,
  AtomicPropositionDocument, IstPropositionDocument, JustificationProvenanceDocument,
  JustificationAttackTargetDocument.
- DOCUMENT FIELD ORDER (charters.py:478): sort key = (document_order if set else field_index,
  field_index). field_index in declarative = ATTRIBUTE declaration order.
  ClaimDocument hand-written field tuple order: id(order3), context(order0), proposition(order1),
  source(order2), artifact_code, logical_ids, version_id, type, provenance, source_local_id(=id),
  body, concepts, conditions, confidence, equations, expression, fit, listener_population,
  lower_bound, measure, methodology, name, notes, output_concept, parameters, sample_size,
  stage, stances, statement, sympy, target_concept, uncertainty, uncertainty_type, unit,
  upper_bound, value, variables.
  Manifest doc order: context, proposition, source, artifact_id, artifact_code, logical_ids,...
  → declare attrs: context(order=0, ONLY required field, first for msgspec), proposition(order=1),
  source(order=2), artifact_id(col id, order=3), then UNORDERED in hand-written tuple order:
  artifact_code, logical_ids, version_id, type, provenance, id(col source_local_id), body, ...
  The unordered attr declaration order MUST equal that tuple order to reproduce field_index sort.
- only `context` is required (nullable=False) on AUTHORED_CLAIM. Everything else
  nullable=True/has default. So context declared first satisfies msgspec required-first.

## CRITICAL: nullable-not-passed vs declarative (SQL nullability)
- Hand-written CharterField with NO nullable= → __post_init__ sets nullable=True,
  _nullable_explicit=False. SQL to_schema_field: nullable = bool(nullable) or is_optional
  → TRUE. Document type: _nullable_explicit False → plain type, required (manifest=builtins.str).
- Declarative _resolve_nullable: plain `str` → nullable=FALSE explicit. SQL nullable=False.
  Document type: plain str required (manifest SAME). BUT SQL column nullability DIFFERS
  (False vs True). Manifest doesn't record SQL nullable, so manifest stays byte-identical,
  BUT runtime inserts of None into now-NOT-NULL columns would break pks build/tests.
- FIX: on CLAIM_CORE / payload fields that hand-written left nullable-unspecified AND are
  plain (str/int) types written as None at runtime, declare them as `T | None` (so declarative
  resolves nullable=True) BUT manifest will then show `str | None` NOT `builtins.str` → CHURN.
  CONFLICT. Resolution: the manifest shows these as `builtins.str` REQUIRED (plain). To keep
  BOTH manifest plain-required AND SQL nullable=True I need nullable=True explicit + plain type
  annotation. charter_field(nullable=True) on a `str` attr → _resolve_nullable returns True
  (explicit override), column_python_type = str (optional_inner_type(str)=str). Document type:
  _document_python_type with nullable=True AND _nullable_explicit=True → inner|None = str|None!
  That CHANGES manifest to str|None. CHURN.
  --> So hand-written nullable-unspecified is a THIRD state declarative CANNOT express:
  SQL-nullable=True + document-required(plain). Need to verify if these CLAIM_CORE fields
  actually receive None at runtime, and whether manifest currently shows them plain-required.
  Manifest (lines 1049-1106) shows ALL Claim_core fields as required plain builtins.* — INCLUDING
  target_concept, source_slug, provenance_json, context_id, branch, stage, promotion_status.
  compile_claim_models writes None for source_slug/provenance_json/branch/promotion_status/etc.
  So SQL MUST be nullable=True for those, but manifest doc = required plain.
  POSSIBLE GAP in @charter (can't express nullable-unspecified). MUST TEST: build the declarative
  Claim_coreDocument, regen manifest, diff. If churn → this is a hard-stop / Quire gap to report.
  Consider: maybe pks build tolerates because these columns get default_sql or the model accepts.
  EMPIRICAL — regen manifest + pks build will tell. Do NOT over-theorize; TEST.

## Pop-B classes that get `.to_payload` method (delegate to _claim_bound_payload free fn)
10 classes: ClaimLogicalId, ClaimSource, Provenance, FitStatistics, VariableBinding,
ParameterBinding, Resolution, StanceDocument(claims), AtomicProposition, IstProposition.
Plus properties: ClaimLogicalIdDocument.formatted, VariableBindingDocument.binding_name,
ClaimDocument.primary_logical_id. JustificationProvenance/AttackTarget/Justification .to_payload.
</content>
</invoke>
