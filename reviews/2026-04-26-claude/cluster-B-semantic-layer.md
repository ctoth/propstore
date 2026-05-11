# Cluster B: semantic layer (claims, contexts, predicates, rules, families, grounding)

Reviewer: review-cluster-B (analyst). Date: 2026-04-26.

## Scope

In-scope code (read in full):
- `propstore/claims.py`, `claim_graph.py`, `claim_references.py`, `stances.py`
- `propstore/predicate_files.py`, `rule_files.py`, `proposals.py`
- `propstore/families/__init__.py`, `addresses.py` (registry.py was not exhaustively read - 891 LOC; see open question)
- `propstore/families/{claims,contexts,documents,forms,identity,concepts}` document modules
- `propstore/grounding/{__init__,bundle,complement,explanations,facts,grounder,gunray_complement,inspection,loading,predicates,translator}.py`

Sampled YAML: `knowledge/claims/Hobbs_1985_OntologicalPromiscuity.yaml`, `knowledge/contexts/ctx_bohannon_pierce_vaughan_2006_relational_lenses.yaml`, `knowledge/justifications/Hobbs_1985_OntologicalPromiscuity.yaml`. The `knowledge/{stances,predicates,rules,sidecar,sources,worldlines}` subdirectories are EMPTY on disk; the schema modules describing them (StanceFileDocument, PredicatesFileDocument, RulesFileDocument, SourceClaimsDocument, etc.) have no real-world test data in this checkout.

Paper notes consulted: Garcia 2004 (DeLP), McCarthy 1993 (FormalizingContext), Bozzato 2018 (CKR/justifiable exceptions), Bozzato 2020 (DKB/DL-Lite), Maher 2021 (Defeasible Datalog), Diller 2025 (Grounding Rule-Based Argumentation), Clark 2014 (Micropublications), Kuhn 2014 (Trusty URIs), Groth 2010 (Nanopublication), Guha 1991 (Contexts), Ghidini 2001 (Local Models Semantics).

## Bugs

### HIGH

**B1. `proposals.commit_stance_proposals` reads `transaction.commit_sha` outside its `with` block.** `proposals.py:182-202`. The line `sha = transaction.commit_sha` is at module-flat indent after the `with repo.families.transact(...) as transaction:` block exits. Whether the binding still has a populated `commit_sha` after `__exit__` depends entirely on the unverified contract of `repo.families.transact()`. If the context manager finalizes the commit only on `__exit__`, this works; if `transaction` is invalidated/cleared on exit, `sha` is None and the next line raises `ValueError("stance proposal transaction did not produce a commit")`. The function is also written so that the `if sha is None: raise` catches this — but it raises a misleading "transaction did not produce a commit" message when the real failure mode is an ordering bug. Sister function `promote_stance_proposals` uses the transaction only inside the `with`, never reading `commit_sha`, but does not return a sha at all — a caller wanting to verify promotion completed cannot.

**B2. `proposals.stance_proposal_relpath` passes a sentinel `cast("Repository", object())` as the repository.** `proposals.py:30-43`. Two functions construct `cast("Repository", object())` and hand it to `PROPOSAL_STANCE_FAMILY.address_for`. This works only because the proposal-stance address scheme presently ignores the repository for path computation. Anyone adding `repo.root` access to `address_for` (perfectly reasonable for resolving the placement) silently breaks every caller of `stance_proposal_relpath` and `stance_proposal_branch`. The cast also lies to the type checker. There is no test pinning the contract that `address_for` is repo-independent.

**B3. `plan_stance_proposal_promotion` silently drops typo paths.** `proposals.py:93-101`. When `path` is provided and the requested filename isn't in `available_by_name`, `selected_refs` becomes the empty list and the function returns a plan with `items=()`. A user typing `propstore promote-stance --path foo.yaml` gets a successful "0 promoted" result instead of an error. Compare with the cleaner `not in` raise pattern used elsewhere.

**B4. `claim_references.ClaimReferenceResolver.resolve_promoted_target` shadows logical ids with local ids.** `claim_references.py:46-57`. The order is: `source.local_to_artifact` → `source.logical_to_artifact` → `primary.logical_to_artifact` → primary artifact set / `ps:claim:` prefix. A claim whose paper-local id collides with a logical-id namespace (e.g., a paper authored a claim with local id `claim2` AND another paper has logical id `Hobbs:claim2`) silently rewrites to the local match without warning. The Hobbs yaml shows logical ids of the form `Hobbs_1985_OntologicalPromiscuity:claim2` — this collision is not hypothetical; namespaces must be prefixed identically to the local id to avoid the trap. There is no asymmetric-key check in `build_source_claim_reference_index`.

**B5. `grounding/inspection.parse_query_atom` splits arguments on bare commas.** `inspection.py:228-256`. `query.partition("(")` extracts the inner argument list and then `raw_args.split(",")` ignores quoted commas. `parse_query_atom('p("a, b", c)')` returns three arguments `['"a', ' b"', ' c']` instead of two. Predicates whose ground rows include strings with commas (perfectly legal scalars per the gunray contract) cannot be queried via the explain/query CLI.

**B6. `OpinionDocument.__post_init__` may never run.** `families/claims/documents.py:386-394`. `OpinionDocument` is a `DocumentStruct` (msgspec.Struct subclass), not a `@dataclass`. msgspec calls `__post_init__` after decoding only under specific configurations; if not configured, the validation that asserts `b + d + u = 1.0` and that `a in (0,1)` is dead code. Subjective-logic opinions with invalid masses then leak into stance resolutions and into `SourceTrustQualityDocument`-derived computations. Add a runtime test that constructing `OpinionDocument(b=2.0, d=0.0, u=0.0, a=0.5, provenance=...)` raises.

**B7. `ProvenanceDocument.page` is a required `int`.** `families/claims/documents.py:297`. Any source without page numbers — preprints, web pages, software repos, books cited by chapter, conference talks cited by date, datasets — cannot construct a `ProvenanceDocument`. The Hobbs yaml uses page numbers, so no caught regressions yet, but the schema's required-page assumption is principled-design drift from the project's "every imported KB row" stance. `SourceProvenanceDocument` (sources.py:394-416) has `page: int | None = None` — i.e., the *source-side* provenance is optional but the *primary-side* mirror is required. Schema sloppiness, not deliberate distinction.

### MED

**B8. Two stance shapes coexist with different fields.** `families/claims/documents.py:432` defines `StanceDocument` (target, type, conditions_differ, note, resolution, strength, target_justification_id) — embedded inside ClaimDocument. `families/documents/stances.py:12` defines `StanceEntryDocument` (source_claim, target, type, strength, note, conditions_differ, resolution, target_justification_id, artifact_code) — used in standalone `StanceFileDocument`. `StanceEntryDocument.type` is `Optional`; `StanceDocument.type` is required. There is no migration path between the two; a stance authored inline on a claim and a stance authored in a stance file describing the same `(source, target, type)` are not de-duplicated.

**B9. `StanceType` enum mixes paper-grounded values with propstore-specific ones.** `stances.py:8`. `REBUTS`, `UNDERCUTS`, `UNDERMINES` are Pollock/ASPIC+ canonical attack types. `SUPPORTS` is from Cayrol 2005 / Clark 2014 bipolar. `EXPLAINS`, `SUPERSEDES`, `ABSTAIN`, `NONE` are not in any cited paper. No docstring distinguishes "stance the user took" from "stance computed by render-time policy" from "stance representing absence of stance" (`NONE` and `ABSTAIN` are both valid; what's the difference?).

**B10. `grounding/facts._scalar_value` silently coerces unknown types via `str(...)`.** `facts.py:321-324`. `_scalar_value` returns `value` if it's `str | int | float | bool`, otherwise `str(value)`. Coercing an enum, a CelExpr, or a dataclass to its repr loses type information and silently lets schema mistakes through to ground atoms. Should raise.

**B11. `claim.context.id` flat extraction loses the McCarthy/Guha lifting structure.** `facts.py:243-253`. The `claim_context` derived-from kind emits `predicate_id(claim_id, context_id)` — a binary relation between claim and a context id string. McCarthy 1993 ist(c, p) and Guha 1991's lifting rules require contexts to expose specializes-relations, parameter bindings, abnormality predicates, and presentIn scope. `ContextDocument` (contexts/documents.py:60) carries `structure.assumptions`, `structure.parameters`, `structure.perspective`, `lifting_rules` — but **none of those fields can be sourced via the `derived_from` DSL**. A predicate cannot be defined as "this claim's context's assumption set includes X" because the DSL has no `claim.context.assumption` or `context.parameter` form.

**B12. `grounding/inspection.format_ground_rule` assumes 3-element kind set; defaults to strict on unknown.** `inspection.py:186-197`. The `kind` lookup table maps `strict→<-`, `defeasible→-<`, `defeater→~<` and falls back to `<-` for anything else. If gunray adds a new rule kind (or returns a kind string with surface variation), the rendered text silently misrepresents the rule as strict. Should raise on unknown kind so render drift surfaces.

**B13. `grounding/translator._normalise_superiority` accepts authored superiority pairs that reference rule ids in *the same file* or any other file in the bundle, but the validation uses `non_strict_rule_ids` which is built across all rule files.** `translator.py:135-150,188-225`. If two rule files both author a rule with id `R1` (allowed because `RuleDocument.id` is just a string and there is no cross-file uniqueness check), `superiority` validation cannot tell which file's `R1` is meant. The grounder will silently choose one. There is no authored-rule-id uniqueness check anywhere I read; predicates have a `DuplicatePredicateError` at registry build time, rules don't.

**B14. `grounding/grounder.ground` calls `gunray.inspect_grounding(theory)` eagerly even when nobody asked.** `grounder.py:171`. The `grounding_inspection` field on `GroundedRulesBundle` is `None`-able but the call is always made. For large theories this is wasted work on every invocation; expose a flag analogous to `return_arguments`.

**B15. `proposals.build_stance_document` accepts `stances: list[dict]` (untyped).** `proposals.py:148-163`. Caller-supplied `dict` payloads are funneled through `convert_document_value` to a `StanceFileDocument`. If the caller passes a malformed dict, the failure surfaces inside msgspec rather than at the propstore boundary. Should accept `list[StanceEntryDocument]` to push validation upstream.

### LOW

**B16. `claim_graph.compute_claim_graph_justified_claims` collapses GROUNDED to a single frozenset.** `claim_graph.py:90-94`. For `ArgumentationSemantics.GROUNDED` the function returns `accepted[0] if accepted else frozenset()`. This is correct under standard Dung semantics (grounded extension is unique), but the cast obscures whether the empty case is "no extension" vs "extension is the empty set" — both valid and meaningfully different.

**B17. `claim_references.ImportedClaimHandleIndex.record` returns a "newly conflicted" boolean that is unused at the call sites I read.** `claim_references.py:74-82`. Either document the return value or drop it.

**B18. `_argument_sort_key` projects rule ids to a sorted tuple, losing authored order.** `grounder.py:230-234`. Garcia 2004 specificity comparison and rule-priority rely on rule order; deterministic sort over rule ids is fine for byte-identical bundles but **not** for argument identity across runs in which the same set of rules has different authored order. The bundle stores `source_rules` separately so the order is recoverable, but `arguments` ordering itself doesn't carry it.

**B19. `MicropublicationDocument.__post_init__` validates `claims` non-empty but is a `DocumentStruct` (see B6).** `families/documents/micropubs.py:35-37`. Same risk as OpinionDocument: validation may be dead code.

## Schema/code drift

**D1. ClaimDocument has both flat fields and a nested `proposition: AtomicPropositionDocument | IstPropositionDocument | None`.** `families/claims/documents.py:560-680`. Every claim attribute (`statement`, `concepts`, `conditions`, `value`, `unit`, `expression`, `equations`, ...) appears twice: once as a top-level field on ClaimDocument, once inside AtomicPropositionDocument. The on-disk yaml (`knowledge/claims/Hobbs_1985_OntologicalPromiscuity.yaml`) uses the *flat* shape — every claim has `statement`, `concepts`, `conditions` at the claim's top level and **no** `proposition` block, **no** `context` block. ClaimDocument declares `context: ContextReferenceDocument` with no default — this would normally raise on strict load. Either: (a) the loader is lenient and the schema is misleading, (b) the yaml is failing to load and nobody noticed, or (c) there is a pre-load shim somewhere that synthesizes `context` from `claim.context` strings. Whichever it is, the schema's promise (every claim has a `ContextReferenceDocument`) is not what the storage layer actually carries.

**D2. SourceClaimDocument declares `context: str | None = None` while ClaimDocument declares `context: ContextReferenceDocument`.** `families/documents/sources.py:247` vs `families/claims/documents.py:561`. The source-side carries a string context id; the primary-side requires a structured ContextReferenceDocument. The promotion path from source to primary must lift a string into a struct, but I see no such lifting in `proposals.py` or in `claim_references.py`. The source-vs-primary mismatch is silent.

**D3. `derived_from` DSL prefixes do not cover stances, justifications, micropubs, or context structure.** `grounding/predicates.py:46-53,181-322`. The DSL supports `concept.relation`, `claim.attribute`, `claim.condition`, `claim.role`, `claim.context`, `claim.provenance`. There is no way to author a predicate sourced from a stance (no `stance.type`, `stance.source_claim`), from a justification (no `justification.premises`, `justification.rule_kind`), from a micropub (no `micropub.evidence`), or from a context's structural fields (no `claim.context.parameter`, `claim.context.perspective`). Bozzato 2018-style `ovr(...)` predicates and Diller 2025-style "non-approximated predicate" derivations are out of reach.

**D4. `RuleDocument.kind` does not distinguish proper vs blocking defeaters.** `families/documents/rules.py:88-91`. Garcia 2004 §4 (Defs 4.1, 4.2) distinguishes proper defeaters (the attacker is strictly preferred) from blocking defeaters (no preference). The schema collapses both into the single string `"defeater"`. Acceptable argumentation lines (Def 4.7 condition 4) require the distinction at runtime.

**D5. `ContextDocument` is rich, but nothing in the grounding pipeline reads `lifting_rules`, `structure.assumptions`, `structure.parameters`, or `structure.perspective`.** `families/contexts/documents.py:60-84`. The structured context model is authored but inert at the grounding layer. The fact extractor only reads `claim.context.id` (B11). The McCarthy/Guha-shaped affordances are present in storage and absent in inference.

**D6. `MicropublicationDocument` is defined but never referenced by grounding or stance proposals.** `families/documents/micropubs.py`. Carries `claims` (tuple of claim references), `evidence`, `assumptions`, `stance` — i.e., the Clark 2014 model — but I observed no fact extractor, no claim-graph integration, no proposal pipeline that materialises micropublications. Stub schema.

**D7. `derived_from` in two different namespaces.** `PredicateDocument.derived_from` is the grounder DSL string. `SourceTrustDocument.derived_from` is `tuple[str, ...]` of source ids. Same field name, totally different semantics. Confusing for authors and for AI agents asked to populate either.

**D8. `StanceEntryDocument.type` is `StanceType | None`** (`families/documents/stances.py:15`) **but `StanceDocument.type` is required** (`families/claims/documents.py:432`). The standalone-file shape allows untyped stances; the embedded shape forbids them. `coerce_stance_type` (`stances.py:28`) accepts None and returns None — there is no "stance with no type" semantics described anywhere. Should be required in both places, or the optional case should be documented.

**D9. `SourceJustificationDocument.rule_kind` is `str | None`, no enum.** `families/documents/sources.py:419-447`. The Hobbs justifications yaml uses values like `causal_explanation`, `comparison_based_inference`, `definition_application`, `scope_limitation`. None of these are validated against an enum; typos like `casual_explanation` would silently land in storage. The `RuleDocument.kind` enum is enforced via Literal but justifications are free-text.

**D10. `version_id: str | None` on ClaimDocument vs `version_id: VersionId` strict typing intent.** `families/claims/documents.py:563`. The yaml stores `version_id: sha256:d6b04b...` — a string with a hash prefix. There is no parser that splits the algorithm prefix and validates the hex. Trusty-URI-style content addressing (Kuhn 2014) would benefit from a typed wrapper.

**D11. `OpinionDocument.provenance` requires Provenance** (sources.py:25 `from propstore.provenance import Provenance`) **but the SourceTrustQualityDocument carries the same b/d/u/a quartet without Provenance.** `families/documents/sources.py:44-58`. Two opinion encodings, only one carries provenance. This violates the project principle that every imported KB row carries provenance.

## Missing features (per-paper)

**M1. Garcia 2004 §3.5 generalized specificity.** Propstore delegates argument comparison to gunray (`grounder.py:128-134` policy keyword). The propstore semantic layer has no specificity computation, no rule-priority criterion, no preference ordering at the stance level beyond the stance type. Propstore could carry an authored specificity hint per claim ("this argument's premises are strictly more specific than..."), but doesn't.

**M2. Garcia 2004 §4.1-4.2 proper vs blocking defeater distinction.** See D4. The `defeater` rule kind collapses both, and the StanceType enum has no analog.

**M3. Garcia 2004 §6 default negation in extended DeLP.** The `RuleDocument` body is a tuple of positive AtomDocument with a `negated` strong-negation flag. There is no representation of `not L` (default negation) distinct from `~L` (strong). DeLP §6.1 explicitly requires both.

**M4. Garcia 2004 §6.2 presumptions (defeasible rule with empty body).** `RuleDocument.body` defaults to empty tuple, so syntactically a defeasible rule with empty body is allowed; but there's no marker that it's a presumption, no separate priority handling, and the comparison criterion §6.3 (presumptions need different treatment) isn't surfaced.

**M5. McCarthy 1993 / Guha 1991 lifting rules.** `LiftingRuleDocument` exists (contexts/documents.py:38) with `id, source, target, conditions, mode, justification`. The grounder doesn't read it. There is no Enter/Leave context primitive, no `presentIn` predicate, no DCR-T/DCR-P abnormality predicates. McCarthy's `ist(c, ist(c', p))` nested form is supported at the schema level (`IstPropositionDocument` is recursive), but on-disk yaml never uses it and no grounder pass reads it.

**M6. Bozzato 2018 §4 clashing assumptions.** No schema for `(axiom, exception)` pairs. The `derived_from` DSL has no `claim.exception` or `claim.clashing_assumption` form. Justifiable-exception semantics — which is the closest analog to propstore's "non-commitment unless render-time override" discipline — is the missing piece.

**M7. Bozzato 2018 §5 datalog overriding rules with `not ovr(...)` guards.** Propstore relies on gunray for defeasibility; gunray performs DeLP-style argumentation, not CKR-style overriding. The two are not equivalent (CKR overrides axiom application per-instance with positive justification; DeLP defeats arguments through dialectical analysis). No schema-level marker that an authored rule is a "global defeasible inclusion" vs a "local override."

**M8. Bozzato 2020 instance-level exception inheritance.** `ClaimDocument` has no exception-set field analogous to CAS-interpretation Σ. Per-instance exceptions to global claims are not representable.

**M9. Maher 2021 stratified evaluation hint.** `RuleDocument` has no stratification metadata; the grounder cannot signal "this rule subset is hierarchical" to gunray to enable stratified bottom-up evaluation. Maher §10 explicitly notes hierarchical theories are stratified; propstore loses the optimization opportunity.

**M10. Diller 2025 §5 non-approximated predicates.** Definition 12 identifies predicates resolvable by strict-rule and fact closure alone. The propstore grounder unconditionally hands the whole theory to gunray. There is no propstore-side eager evaluation of `definitely(...)` rows for non-approximated predicates, no opportunity to short-circuit.

**M11. Clark 2014 SupportGraph / ChallengeGraph DAG primitives.** `MicropublicationDocument` has `claims: tuple[str, ...]`, `evidence`, `assumptions`, but no explicit `supportGraph` / `challengeGraph` DAG structure with transitive `supports` and induced `challenges` relations. Clark 2014 §3 makes these first-class. Propstore reduces them to a flat stance list.

**M12. Clark 2014 holotypes / similarity groups.** Concept-level grouping with a designated representative. No schema for holotype claims; `canonical_name` on concepts is the closest analog but covers concept naming, not claim grouping.

**M13. Kuhn 2014 trusty URIs.** `artifact_id: ps:claim:64074723581652c3` looks content-addressed but I observed no hash-verification path. The Trusty URI shape (45-char artifact code with module+version+hash) isn't implemented; `artifact_id` is just a generated id. `artifact_code: sha256:d6b04b...` exists on `SourceClaimDocument` but is not validated against the document content. RDF-graph-level hashing (Kuhn 2014's key innovation) is absent.

**M14. Kuhn 2017 granular references.** No support for incremental versioning of claims; `version_id` is a single hash, not a chain.

**M15. Groth 2010 `assertedBy`.** Stances have `source_claim` (who asserts the stance) but a stance is not a nanopub; the broader "this paper asserts the union of the following claims" relation is not first-class. Sources have a `trust` block but no `assertedBy` link from a source to a specific named-graph of claims.

**M16. Groth 2010 / Clark 2014 named-graph serialization.** Pure YAML; no RDF/Named-Graph serialization path. Cross-publication aggregation in the S-Evidence sense is not directly supported.

**M17. Ghidini 2001 bridge rules / compatibility relation.** `LiftingRuleDocument` is the closest construct but lacks the cross-context model-compatibility check Ghidini formalizes (premises in one context, conclusions in another, with semantic compatibility constraint).

## Principle drift

**P1. Non-commitment is well-honored in `grounder.py` but violated in `claim_references.py` and `proposals.py`.** The grounder explicitly normalizes all four DeLP answer sections (definitely/defeasibly/not_defeasibly/undecided) to be present even when empty (`grounder.py:237-287`) and freezes them with MappingProxyType. This is exemplary. By contrast `ClaimReferenceResolver.resolve_promoted_target` (claim_references.py:46-57) commits in the storage path: a promoted stance gets *one* artifact id, ambiguity is rejected (`require_unambiguous` raises) rather than recorded as a defeasible claim with its own provenance. The storage layer is making a commitment instead of preserving disagreement.

**P2. Promotion path moves bytes from proposal branch to main without preserving the heuristic-proposal flag.** `proposals.promote_stance_proposals` (`proposals.py:124-145`) calls `transaction.stances.save(...)` with the proposal document verbatim. The promoted stance becomes "primary" with no marker that it originated from a heuristic LLM classifier (`classification_model`, `classification_date` survive on the `StanceFileDocument` envelope, but the per-stance entry has no provenance distinguishing heuristic-promoted from authored). This violates the project's stated principle that "every imported KB row is a defeasible claim with provenance, never truth — no source is privileged." After promotion, the stance is indistinguishable from an authored one.

**P3. Grounding atoms lose claim-level provenance at the boundary.** `extract_facts` (`facts.py:114-156`) collects atoms keyed by `(predicate, arguments)` — flat tuples. The `claim_id` appears as an argument scalar but the rest of the claim's provenance (paper, page, section, quote_fragment, extraction model) does not travel with the atom. Once the gunray model is built, no further reference to the originating claim exists. This breaks Clark 2014's transitive provenance principle. Diller 2025 §3 also assumes atoms are pure tuples, but propstore's "every imported row is a defeasible claim with provenance" stance demands the provenance be queryable from the ground bundle.

**P4. Gunray choice of policy.BLOCKING is hard-coded as the default in two places** (`grounder.py:77`, `explanations.py:30`). The policy is a defeasible choice (Garcia 2004 distinguishes ambiguity-blocking vs ambiguity-propagating regimes). Hardcoding a default is fine; the docstring at `grounder.py:130-136` admits only BLOCKING is supported on the dialectical-tree path. Propstore should either expose this contract via the bundle or remove the policy keyword to prevent confusion.

**P5. The four-section "non-commitment" guarantee leaks at render time.** `inspection.format_ground_rule` (`inspection.py:186-197`) defaults unknown rule kinds to `<-` (strict). A rule that gunray classifies as something other than the three known kinds gets silently rendered as strict — collapsing genuine ambiguity into commitment at the render boundary. The non-commitment discipline holds in the bundle but is broken on the way out.

**P6. Source-side trust opinions are not provenance-tagged the same way as claim-side opinions.** `OpinionDocument.provenance: Provenance` (required) vs `SourceTrustQualityDocument` (no provenance field, just b/d/u/a). The trust statement is itself a claim — by project principle it must carry provenance.

**P7. Stance promotion writes through git transactions without preserving the proposal commit history as a stance-level field.** `commit_stance_proposals` (`proposals.py:171-202`) writes to the proposal branch. Subsequent promotion (`promote_stance_proposals`) reads the proposal tip and saves to the main branch. Neither path records on the resulting StanceEntryDocument that this stance originated from commit `<sha>` of the proposal branch. Provenance information that exists in git is dropped from the storage entity.

**P8. `RuleDocument.id` is not enforced unique across rule files.** See B13. A defeasible knowledge base under DeLP/Diller treats rule identity as global. propstore lets two files independently mint `R1`, which the grounder's superiority validator silently picks one of.

## Open questions for Q

1. **Is the on-disk claim shape supposed to be flat (as the Hobbs yaml shows) or `proposition`-wrapped (as `ClaimDocument.proposition` suggests)?** The schema currently allows both; storage uses only the flat form. Is `proposition` a planned migration target or a stale alternative? (D1.)

2. **Is `ClaimDocument.context` truly required?** The on-disk yaml doesn't carry it. If contexts are mandatory, the loader should fail; if they're optional, the schema is wrong. Same question for `ProvenanceDocument.page`. (D1, B7.)

3. **Why does the `derived_from` DSL deliberately exclude stances and justifications as predicate sources?** The principled fix to support Bozzato 2018 overriding semantics requires this; was it left out by design (e.g., to keep the grounder rule-based-only) or by oversight? (D3, M7.)

4. **What is the intended difference between `StanceType.NONE` and `StanceType.ABSTAIN`?** No docstring distinguishes them. (B9.)

5. **Are heuristic-promoted stances supposed to be marked as such after promotion?** Currently they are indistinguishable from authored ones; this seems contrary to the "no source is privileged" principle. (P2.)

6. **Is `version_id` meant to be a content-addressed Trusty URI per Kuhn 2014, or just a string hash?** If the former, the validation/computation path is missing. (M13, D10.)

7. **Should grounded atoms carry claim provenance?** Currently they don't, which breaks Clark 2014-style transitive provenance. (P3.)

8. **Is `MicropublicationDocument` actually wired anywhere?** I observed only the schema, no fact extractor or argument builder. If unused, it's stub schema — should it be removed or activated? (D6.)

9. **What is the migration plan from `StanceDocument` (embedded on claim) to `StanceEntryDocument` (in stance file)?** Two coexisting shapes are accumulating cost. (B8, D8.)

10. **Are knowledge/{stances,predicates,rules,sidecar,worldlines} supposed to be empty in this checkout?** The schema modules are well-developed but the on-disk directories are empty. Either fixtures are missing from this snapshot or the storage layer hasn't seen real use yet for those families.

11. **Does `families/registry.py` (891 LOC, not exhaustively read) define authored-rule-id uniqueness?** I found no such check at the schema or registry levels visible from the modules I read. (B13, P8.)

12. **Is `OpinionDocument` validation expected to run?** As a `DocumentStruct`, `__post_init__` may be dead code. If it is dead, invalid opinions are silently accepted. (B6.)
