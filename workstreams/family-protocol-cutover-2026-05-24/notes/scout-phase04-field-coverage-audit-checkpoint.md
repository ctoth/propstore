# scout-phase04-field-coverage-audit checkpoint

Date: 2026-05-25

## State
- HEAD: 9e187d4c (matches expected)
- Phase: gathering inventory before report write
- Deliverable: workstreams/family-protocol-cutover-2026-05-24/reports/scout-phase04-field-coverage-audit.md (NOT YET WRITTEN)

## Observations (verified by tool output)

### Line counts of the 14 modules
- claims/documents.py: 686
- concepts/documents.py: 113
- contexts/documents.py: 84
- forms/documents.py: 39
- sameas/documents.py: 38
- documents/justifications.py: 43
- documents/merge.py: 48
- documents/micropubs.py: 57
- documents/predicates.py: 141
- documents/rules.py: 167
- documents/source_alignment.py: 94
- documents/sources.py: 547
- documents/stances.py: 55
- documents/worldlines.py: 164

### Declaration module status (verified by ls)
EXISTS:
- propstore/families/claims/declaration.py
- propstore/families/concepts/declaration.py
- propstore/families/contexts/declaration.py
- propstore/families/forms/declaration.py
- propstore/families/rules/declaration.py
- propstore/families/sources/declaration.py
- propstore/families/micropublications/declaration.py

MISSING (no declaration.py):
- sameas (dir exists, no declaration)
- justifications (empty dir)
- merge (no dir at all)
- predicates (no dir at all)
- source_alignment (no dir at all)
- stances (no dir at all)
- worldlines (no dir at all)

### Family-dir landscape
propstore/families/ contains: addresses.py, batch_specs.py, calibration, claims, concepts, contexts, diagnostics, documents, embeddings, forms, identity, justifications (empty), meta, micropublications, registry.py, relations, rules, sameas (no decl), sources.

So 7 of 14 families have MISSING CHARTER MODULE going into Phase 04. That is the headline.

## Next steps
1. Read each of the 14 document modules to inventory classes/fields/methods.
2. Read the 7 existing declaration.py modules to extract CharterField entries.
3. Run importer counts (Grep).
4. Write report.

## Blockers
None yet.

## Update 2 (mid-audit)

Read so far:
- claims/documents.py + claims/declaration.py (CLAIM_CORE + CLAIM_CONCEPT_LINK + 3 payload + CLAIM_SOURCE_ASSERTION + JUSTIFICATION charters)
- concepts/documents.py + concepts/declaration.py (CONCEPT + ALIAS + PARAMETERIZATION + PARAMETERIZATION_GROUP + RELATIONSHIP charters)
- contexts/documents.py + contexts/declaration.py (CONTEXT + CONTEXT_ASSUMPTION + CONTEXT_LIFTING_RULE + CONTEXT_LIFTING_MATERIALIZATION)
- forms/documents.py + forms/declaration.py (FORM + FORM_ALGEBRA only — fields way thinner than document)
- sameas/documents.py (NO declaration.py — MISSING CHARTER MODULE confirmed)
- documents/justifications.py
- documents/merge.py
- documents/micropubs.py

Big findings so far:
- **Claims:** Charter `claim_core` does NOT contain proposition kind, conditions_cel, lower/upper bounds, fit, listener_population, methodology, parameters, sample_size, variables, stances, equations directly — those live on payload sub-charters (numeric, text, algorithm). ClaimDocument is a flat shape that compiles INTO multiple charter rows. Direct one-to-one match is impossible — Phase 04 here requires either (a) charter normalization (unlikely) or (b) acknowledging that one Quire-emitted struct cannot replace ClaimDocument because it splits across 5 charter families. **BLOCKED / requires-spec-change.**
- **Concepts:** ConceptDocument has lexical_entry, ontology_reference, qualia, description_kind, role_bundles, parameterization_relationships nested — none of these are CharterFields in CONCEPT charter (which stores canonical_name, kind_type, form, etc. — flattened). Same pattern: doc splits across multiple charter families. Also has __post_init__ on LexicalEntryDocument (behavior).
- **Contexts:** Cleaner. ContextDocument has id/name/description/structure(=parameters+perspective+assumptions)/lifting_rules. Charter has context+assumption+lifting_rule+materialization separate. Doc→multiple-row decomposition again. NEEDS-AUGMENTATION if charter is normalized as written; or BLOCKED since one struct cannot represent the nested shape.
- **Forms:** Doc has dimensionless, base, unit_symbol, qudt, parameters, common_alternatives, delta_alternatives, kind, note, dimensions (dict), extra_units, min, max. Charter has: name, kind, unit_symbol, is_dimensionless, dimensions (as str). MISSING many fields. **NEEDS-AUGMENTATION.**
- **SameAs:** MISSING CHARTER MODULE entirely.
- **JustificationDocument:** rule_kind, rule_strength, premises, conclusion, provenance (nested), attack_target, artifact_code. There IS a JUSTIFICATION_CHARTER inside claims/declaration.py with: id, justification_kind, conclusion_claim_id, premise_claim_ids, source_relation_type, source_claim_id, provenance_json, rule_strength. Name mismatches: rule_kind→justification_kind, conclusion→conclusion_claim_id, premises→premise_claim_ids. Charter has no `attack_target` or `artifact_code`. NAME-MISMATCH + MISSING fields. **NEEDS-AUGMENTATION.**
- **MergeManifestDocument:** No `merge` declaration module. **MISSING CHARTER MODULE.** (Confirmed earlier: no propstore/families/merge dir.)
- **MicropublicationDocument:** Declaration is `micropublications/declaration.py` (exists). Need to read.

## Still to read
- documents/predicates.py
- documents/rules.py
- documents/source_alignment.py
- documents/sources.py
- documents/stances.py
- documents/worldlines.py
- rules/declaration.py
- sources/declaration.py
- micropublications/declaration.py

Then importer counts via Grep, then write deliverable.

