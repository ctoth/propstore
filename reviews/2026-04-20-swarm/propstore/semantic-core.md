# Semantic Core Review — 2026-04-20

Scope: `propstore/core`, `propstore/families`, `propstore/grounding`, the root-level
CEL / Z3 / dimensions / context / claim modules, plus `form_utils.py`,
`predicate_files.py`, `claim_references.py`. Dual mission: principle adversary
pass against lemon/ist/TIMEPOINT/dimension rules, and analyst pass for silent bugs.

## Lemon-Shape Violations

### Duplicate `ontology_reference` parallel to `sense.reference`
- File: `propstore/families/concepts/documents.py:90-108`
  (`ConceptDocument.ontology_reference`)
- Summary: `ConceptDocument` carries both a top-level
  `ontology_reference: OntologyReferenceDocument` and per-sense
  `lexical_entry.senses[i].reference`. The validator
  (`propstore/families/concepts/passes.py:206-229`, `_validate_lemon_document`)
  simply enforces that the top-level URI must appear in some sense — i.e. it is
  a shadow field, always derivable, and silently ambiguous if divergent.
  OntoLex-Lemon / Buitelaar 2011 defines the ontology link per LexicalSense,
  not at the entry level; there is no "primary reference" on a lexical entry.
  `concept_document_to_record_payload` (`stages.py:674-683`) dereferences
  `senses[0]` when no sense matches the outer `ontology_reference.uri`, which
  can silently attribute a concept's `definition` and `form` to the wrong sense.
  Finally, `_ensure_ontology_reference` (`families/identity/concepts.py:250-264`)
  auto-generates a self-referential URI equal to the artifact ID when missing —
  a non-ontology "ontology reference" that exists only to satisfy the shadow
  field.
- Severity: HIGH (lemon-shape violation; silent semantic misattribution on
  divergence)
- Fix: drop `ConceptDocument.ontology_reference`; identify the "primary" sense
  via an explicit authored flag or render-time policy, not a parallel field.

### `LexicalEntryDocument.physical_dimension_form` is REQUIRED at the document layer and OPTIONAL in the dataclass
- Files: `propstore/families/concepts/documents.py:82` vs
  `propstore/core/lemon/types.py:41`
- Summary: `LexicalEntryDocument.physical_dimension_form: str` — required with
  no default. `LexicalEntry.physical_dimension_form: str | None = None` —
  optional. `_lexical_entry_payload` at `stages.py:146-147` emits the field only
  when non-None, so a concept that loaded from YAML with the field becomes
  a concept that, after the dataclass/payload round-trip, may re-decode missing
  that required field and fail. `concept_document_to_record_payload` at
  `stages.py:683-687` further raises on None at record-payload time, but only
  after the dataclass has happily accepted the instance. Three layers disagree
  on whether this field is required and under what conditions.
- Severity: HIGH (round-trip breaker; inconsistent invariants across the three
  sources of truth)
- Fix: make the document schema match the dataclass (optional), OR make the
  dataclass match the document (required). Don't leave them disagreeing. If
  you choose "required for kinds that need it, None otherwise", drive that
  from form-kind, not from three ad hoc None-checks.

### `concept_document_to_record_payload` silently dereferences `senses[0]` on ontology-reference mismatch
- File: `propstore/families/concepts/stages.py:674-683`
- Summary: `next((... if sense.reference.uri == reference_uri), data.lexical_entry.senses[0])`.
  When `ontology_reference.uri` doesn't match any sense (validator can catch
  this but only in the semantic-check pass, which runs after this conversion
  in several code paths), the fallback picks the first sense — so `definition`
  is built from that sense's `usage` instead of failing loudly.
- Severity: MEDIUM (silent semantic misattribution)
- Fix: raise on mismatch; or — preferred — delete the duplicate
  `ontology_reference` field and use sense URI as the sole source of truth.

### `_ensure_ontology_reference` builds a self-referential URI from the artifact id
- File: `propstore/families/identity/concepts.py:250-264`
- Summary: When no `ontology_reference` is present, `_ensure_ontology_reference`
  writes `{"uri": artifact_id, "label": effective_name}`. The ontology URI
  becomes `ps:concept:<digest>` — a propstore artifact id, not an actual
  ontology entity. Lemon's whole point is that LexicalSense links a lexical
  entry to an EXTERNAL ontology concept. A self-referential URI undermines the
  model: there is no external ontology being lexicalized.
- Severity: HIGH (principle violation: lemon requires a real ontology
  reference; auto-generating one short-circuits the semantics)
- Fix: refuse to normalize a concept without an authored ontology reference,
  OR — if the propstore artifact id IS the ontology entity for
  natively-authored concepts — document the convention and stop pretending
  it's an ontology link.

### `LexicalSense.role_bundles` is `Mapping[str, ProtoRoleBundle] | None` — `None` and empty dict collapse
- File: `propstore/core/lemon/types.py:23-30`
- Summary: `role_bundles: Mapping[str, ProtoRoleBundle] | None = None`.
  `__post_init__` validates keys only when `role_bundles is not None`.
  `None` (no Dowty analysis performed) and `{}` (Dowty analysis was run and
  found no roles) both serialize to nothing. The non-commitment principle
  says "honest ignorance over fabricated confidence" — these two states mean
  different things. Same concern applies to `qualia` / `description_kind`.
- Severity: LOW (principle violation, small)
- Fix: use a small wrapper carrying presence + provenance (even if empty), or
  document the convention that None means "not analyzed".

## Principle Violations

### TIMEPOINT is bypassable as a parameterization input via name-based form-kind inference
- Files:
  - `propstore/form_utils.py:508-520` (`kind_type_from_form_name`)
  - `propstore/families/forms/stages.py:177-188` (duplicate of above)
  - `propstore/families/concepts/passes.py:573-577` (parameterization input
    check uses `kind_type_from_form_name(input_concept.record.form)`)
- Summary: CLAUDE.md says TIMEPOINT is not valid for parameterization or
  dimensional algebra. The parameterization-input check at `passes.py:573`
  relies on `kind_type_from_form_name(form)` — which maps the form NAME
  string to a kind. If the concept's form is `elapsed_time`, the NAME
  doesn't match any of the special cases (`category`/`structural`/`boolean`/
  `timepoint`) so the function returns `KindType.QUANTITY`. Meanwhile
  `parse_form` reads the form YAML file's `kind: timepoint` field and
  returns `KindType.TIMEPOINT`. Two code paths disagree; the parameterization
  gate uses the weaker one. Result: a TIMEPOINT concept can be passed as a
  parameterization input, and the dimensional check will then attempt
  `mul_dims`/`div_dims` over the timepoint's form dimensions — which is the
  exact "dimensional algebra over TIMEPOINT" behavior the principle forbids.
- Severity: HIGH (principle violation bypass)
- Fix: in `passes.py:573`, resolve kind via the loaded FormDefinition
  (`_form_definition(c, input_concept.record.form).kind`), not via the name
  heuristic. Delete `kind_type_from_form_name` entirely — it's a fallback
  that lies.

### Duplicate `_KIND_MAP` / `kind_type_from_form_name` / `parse_form` across modules
- Files: `propstore/form_utils.py:373-561` vs
  `propstore/families/forms/stages.py:62-221`
- Summary: Same functions, same `_KIND_MAP`, two independent module-global
  `_form_cache` dicts and two `clear_form_cache` functions. When one module's
  cache is cleared (e.g. by a test), the other is stale. Callers split across
  both modules — changes to one implementation silently miss the other.
- Severity: MEDIUM (drift + dual cache correctness hazard)
- Fix: `form_utils` should delegate to / re-export from
  `families/forms/stages`. Single cache.

### Temporal interval ordering is enforced via canonical-name suffix match
- File: `propstore/z3_conditions.py:462-497`
  (`_temporal_ordering_constraints`)
- Summary: `from_var <= until_var` is added only for TIMEPOINT concepts whose
  canonical names end in `_from` and `_until` with a shared prefix. Nothing
  prevents someone from authoring interval endpoints as `start_time` /
  `end_time` or `valid_begin` / `valid_end`. Those get no ordering
  constraint, so inverted intervals are silently SAT.
- Severity: MEDIUM (silent under-constraint of non-conforming naming)
- Fix: pair interval endpoints via an authored concept relationship
  (e.g. `interval_end_of`), not by name-suffix regex.

### Description-temporal Allen registry synthesizes TIMEPOINT concepts with fixed names
- File: `propstore/core/lemon/temporal.py:78-103`
- Summary: `description_temporal_relation` builds a private registry of four
  TIMEPOINT concepts (`left_from`/`left_until`/`right_from`/`right_until`)
  and relies on the solver's name-suffix ordering to enforce
  `valid_from <= valid_until`. It happens to match because the four names
  end in `_from`/`_until`. This is a fragile invariant held together by
  coincidence between two unrelated modules — no test pins the name
  convention to the solver convention.
- Severity: LOW (works today, brittle)
- Fix: add a regression test that breaks if either side changes.

### `LiftingSystem.effective_assumptions` silently deduplicates rule-derived conditions
- File: `propstore/context_lifting.py:91-98`
- Summary: `tuple(dict.fromkeys(assumptions))` keeps insertion order but
  collapses duplicates across context assumptions and rule conditions.
  Two independent lifting rules that both carry the same CEL condition now
  yield one assumption in the effective set, losing provenance about WHICH
  rule contributed it. For the principle of preserving argument structure
  until render time, this is a collapse.
- Severity: LOW (principle drift, not currently unsound)
- Fix: carry (condition, rule_id) pairs; deduplicate at render time with
  policy, not silently at access time.

## CEL/Z3 Type Correctness

### Z3 `&&` / `||` are not short-circuit — division guards can force unsound UNSAT
- File: `propstore/z3_conditions.py:229-260`
- Summary: `z3.And(self._translate(left), self._translate(right))` translates
  both sides regardless of the LHS. If the RHS contains `x / y` where
  `y == 0` is the legitimate binding, the division guard `y != 0` is
  conjuncted into the whole expression. For
  `is_condition_satisfied("x > 0 && y/x > 1", {"x": 0, "y": 5})`, CEL
  semantics (short-circuit) say "false && whatever = false" (condition not
  satisfied). The Z3 translation conjuncts `x != 0` into the expression; the
  binding sets `x == 0`; result: UNSAT. Wrong answer.
- Severity: MEDIUM (unsound disjointness / satisfaction for short-circuited
  denominators)
- Fix: scope division guards so they apply only to the branch where the
  division participates. Rewrite `&&` as `z3.Or(z3.Not(left), z3.And(left,
  right_with_guards))` or similar, or maintain a per-subexpression guard
  list and conjunct only where reached.

### Division-guard state is instance-level mutable list
- File: `propstore/z3_conditions.py:140, 257-260, 405-418`
- Summary: `self._current_guards: list[Any]` is reset at the top of
  `_condition_to_z3` and mutated during `_translate`. Any caller that invokes
  `_translate` directly (or any recursion path that invokes `_condition_to_z3`
  re-entrantly) loses the per-call scoping. Currently sound only because all
  external callers go through `_condition_to_z3`; latent hazard.
- Severity: LOW (latent)
- Fix: return guards from `_translate` as part of the translation result;
  eliminate the instance attribute.

### `_retry_with_standard_bindings` masks undefined-concept errors by inventing synthetic categories
- File: `propstore/core/activation.py:87-121, 147-157, 183-193`
- Summary: When `are_disjoint` raises `Z3TranslationError`, activation code
  scans the CEL conditions for identifier-shaped names and auto-registers
  every one as a fresh synthetic extensible-category concept, then retries.
  That converts typos ("sourse" instead of "source") and genuinely undefined
  concepts into a pass — the retry now knows about "sourse" as an extensible
  category concept and returns a valid answer. The solver's honest-ignorance
  contract becomes fabricated success.
- Severity: HIGH (principle violation; silent semantic drift from typos)
- Fix: the retry should only augment with the declared
  `STANDARD_SYNTHETIC_BINDING_NAMES`, not with every unrecognized identifier
  scraped from the condition text. Bare undefined concepts must propagate.

### `_claim_conditions` crashes activation on malformed JSON
- File: `propstore/core/activation.py:59-70`
- Summary: `loaded = json.loads(raw)` inside `_claim_conditions` has no error
  handling. If `conditions_cel` is a non-JSON string (corrupted sidecar row,
  wrong-kind value), `JSONDecodeError` propagates up from activation — a
  layer that would otherwise just return "not active" becomes a hard crash
  across the whole activation walk.
- Severity: MEDIUM (single bad row kills the entire active-graph computation)
- Fix: catch `JSONDecodeError`, treat as "no conditions" or emit a typed
  diagnostic.

### `_resolve_type` returns `NUMERIC` for TIMEPOINT even when comparing to a string literal, losing specificity
- File: `propstore/cel_checker.py:747-758`
- Summary: The error message in
  `_check_concept_literal_type_mismatch` says "Quantity concept '...'
  compared to string literal" for both QUANTITY and TIMEPOINT concepts.
  Misleading — a user debugging a TIMEPOINT will search for "TIMEPOINT" and
  find nothing.
- Severity: LOW (error message quality)
- Fix: branch on `info.kind` and emit the actual kind name.

### `check_cel_expression` swallows runtime `ValueError`s beyond parse errors
- File: `propstore/cel_checker.py:416-439`
- Summary: Only parse errors are captured; any other exception from
  `_check_node` (e.g. a KeyError from a malformed registry entry) propagates.
  Meanwhile `check_cel_expr` at `461-482` raises on ANY hard error. Two
  entry points, different error contracts, no docstring explaining the
  distinction.
- Severity: LOW (API contract clarity)
- Fix: document or unify.

## Bugs & Silent Failures

### `next_concept_id_for_repo` has a read-modify-write race
- File: `propstore/concept_ids.py:32-56`
- Summary: Two concurrent concept creations both read `counter = N`, both
  compute `next = N+1`, both attempt `record_concept_id_counter(N+1)`.
  `_read_concept_id_counter` + `write_blob_ref` is not atomic. The second
  writer's conditional bail at line 54-55 stops the counter from
  regressing, but the concept file has already been authored with
  `concept(N+1)` on both branches — collision.
- Severity: MEDIUM (integrity on concurrent creation; propstore supports
  branches/worktrees)
- Fix: atomic compare-and-swap on the ref blob, or serialize creation
  through a ref-level lock.

### `ClaimReferenceIndex.resolve_local` accepts qualified IDs without existence check
- File: `propstore/claim_references.py:19-27`
- Summary: If `reference.startswith("ps:claim:")`, it's returned verbatim
  with no check that the artifact ID exists in the index. Downstream a
  stance can reference a non-existent claim that will only fail later in
  the pipeline with a less-helpful error.
- Severity: LOW
- Fix: `if reference in self.artifact_ids: return reference` else raise.

### `ImportedClaimHandleIndex.record` has an obscure third-call silent-noop path
- File: `propstore/claim_references.py:74-82`
- Summary: After the second artifact_id mapping turns a local_id ambiguous
  (value becomes None), a third attempt finds
  `previous is None and local_id in _local_to_artifact` true and returns
  False without recording anything. This means a THIRD attempt with a
  THIRD artifact is silently indistinguishable from a second-attempt
  noop. The method name and return type don't signal "I am now sticky-
  ambiguous".
- Severity: LOW (API ergonomics)
- Fix: rename `record_or_mark_ambiguous`; document the stickiness.

### `_concept_satisfies_type` ignores multi-hop IS_A / KIND_OF chains
- File: `propstore/families/concepts/passes.py:107-123`
- Summary: Walks only one level of IS_A / KIND_OF. A IS_A B IS_A C
  cannot satisfy a slot type constraint of C when the concept being
  checked is A. Description-kind slot-type checks fail legitimately
  matching concepts.
- Severity: MEDIUM (false-negative type satisfaction)
- Fix: BFS over IS_A / KIND_OF edges with cycle detection.

### 16-hex-char SHA256 truncation for artifact IDs — 64 bits of entropy
- Files: `families/identity/concepts.py:30`,
  `families/identity/claims.py:24`, `sidecar/concept_utils.py:22`,
  `source/claims.py:43`, `worldline/hashing.py:44`
- Summary: `hexdigest()[:16]` gives ~64 bits. Birthday collision on the
  order of 2^32 ~= 4 billion artifacts. Fine for a single project but not
  if propstore is ever used to catalog orders-of-magnitude-larger corpora
  (e.g. wiktionary-sized lexicalizations). No warning or docstring pinning
  the choice.
- Severity: LOW (forward-looking; not currently reachable)
- Fix: document the entropy budget and the expected scale ceiling, or
  use the full hex.

### `normalize_concept_document_for_write` double-normalizes and trusts the second result
- File: `propstore/families/concepts/stages.py:647-669`
- Summary: `normalize_canonical_concept_payload` is called once, converted
  back to a document, then called AGAIN on the round-tripped payload
  before hashing. The first normalization result is thrown away. If
  normalization is non-idempotent (and
  `normalize_canonical_concept_payload` recomputes `version_id` each
  call — line 128 in `families/identity/concepts.py`), the two versions
  could differ. Currently idempotent because the function deep-copies
  input, but fragile.
- Severity: LOW
- Fix: one normalization, one version-id stamp.

### `add_context.filepath = repo.root / relpath` — path separator hazards on Windows
- File: `propstore/context_workflows.py:82-91`
- Summary: `relpath = ....require_path()` returns a `TreePath` path. The
  `dry-run:{relpath}` source tag at line 90 concatenates through `{}`
  format — the format uses TreePath's __str__, which preserves forward
  slashes. Downstream consumers that split the string on `\` or expect
  OS separators may silently misparse. Not a crash, a surface for
  drift.
- Severity: INFORMATIONAL

### `coreference_query` allows self-attacking arguments
- File: `propstore/core/lemon/description_kinds.py:130-150`
- Summary: Attacks `(a, a)` are not rejected. Technically legal in Dung
  AF (self-attackers are never in grounded/preferred extensions), but
  authoring a merge argument that attacks itself is almost certainly a
  bug and the system has no way to signal it.
- Severity: LOW
- Fix: warn on self-attacks at `coreference_query` build time.

### Translation layer coupling — `core/lemon/temporal.py` imports from `argumentation.dung`
- File: `propstore/core/lemon/description_kinds.py:9-14`
- Summary: `core/lemon/` is supposed to be the concept-layer (layer 2)
  artifact. It imports from `argumentation.dung` (layer 4). CLAUDE.md says
  one-way dependencies top depends on bottom. The import at the lemon
  layer breaks that.
- Severity: MEDIUM (architecture layering violation)
- Fix: move coreference-resolution semantics (which need Dung AFs) out of
  `core/lemon/` and into an adjacent module that the argumentation layer
  can own.

### `PredicateRegistry.validate_atom` doesn't validate argument types, only arity
- File: `propstore/grounding/predicates.py:331-356`
- Summary: Diller 2025 §4 discusses typed argument vectors, and
  `PredicateDocument` carries arg types, but `validate_atom` only checks
  arity. A declaration `bird(Species)` accepts `bird("Tuesday")` as a
  valid atom. Fact extraction does the right thing by construction
  (one argument from concept canonical name), but rule bodies from
  authored rule files could smuggle wrong-typed atoms through.
- Severity: MEDIUM (Datalog schema laxity)
- Fix: extend `validate_atom` to check arg-type compatibility.

### `extract_facts` uses `canonical_name` as the ground term — but canonical names can be arbitrary strings with CEL-reserved characters
- File: `propstore/grounding/facts.py:150-167`
- Summary: `canonical_name` is a free-form `written_rep` from lemon. It
  can contain spaces, Unicode, punctuation. Downstream Datalog atom
  rendering (in gunray) stringifies — fine if gunray's grammar is
  tolerant, but a canonical name like `"red wine"` or `"H₂O"` will
  produce atoms whose downstream grounding may be fragile. No
  sanitization here.
- Severity: LOW (assumes gunray tolerates arbitrary strings as
  constants)
- Fix: sanitize or use a stable identifier (artifact_id) as the term.

## Dead Code / Drift

### Duplicate form helpers across `form_utils.py` and `families/forms/stages.py`
- Same as above — two modules with near-identical `_KIND_MAP`,
  `kind_type_from_form_name`, `kind_value_from_form_name`, `parse_form`,
  `load_form`, `load_all_forms`, `load_form_definition`,
  `allowed_units_from_form_definition`, `clear_form_cache`, `_form_cache`.
- Severity: MEDIUM
- Fix: delete the `form_utils` duplicates; re-export from
  `families/forms/stages`.

### `_form_cache` caches are module-global, not scoped to repo
- Files: `propstore/form_utils.py:111`,
  `propstore/families/forms/stages.py:59`
- Summary: cache key is `(path_string, form_name)`. Multi-repo processes
  or branch switches where a repo's forms change underneath the same
  path will hit stale entries. Not currently reachable in single-repo
  usage but the cache is a silent contract violation waiting to happen.
- Severity: LOW
- Fix: key by repo commit hash or invalidate on filesystem change.

### `concept_reference_keys` in `families/identity/concepts.py:132-150` appears unused
- File: `propstore/families/identity/concepts.py:132-150`
- Summary: Module-level helper that returns a set of reference keys; a
  sibling function of the same name exists in
  `families/concepts/stages.py:704-721` as `concept_reference_keys`. Grep
  shows the identity-module variant called from nowhere obvious within
  the scoped review area. Possible dead code — confirm call sites before
  deletion.
- Severity: INFORMATIONAL (flag for cleanup)

### `clear_symbol_table` in `unit_dimensions.py` / `clear_form_cache` in form helpers — orphan tools
- Summary: Exposed for tests but no test in the reviewed code path is
  currently shown invoking them. Keeping them cheap but they are drift
  attractors: if the loading logic changes and the cache key changes, the
  clear function still "works" but clears the wrong keys.
- Severity: INFORMATIONAL

## Positive Observations

1. `LexicalSense.reference` is a single `OntologyReference` (functional),
   matching OntoLex-Lemon exactly. `LexicalEntry.references` is a
   derived-tuple view, never a parallel mutable state.
   (`core/lemon/types.py:18-23, 58-60`)
2. `LexicalEntry.physical_dimension_form` lives on the entry, not on
   `LexicalForm`, matching the principle.
   (`core/lemon/types.py:41`, `core/lemon/forms.py:17-38`)
3. Qualia references carry per-reference provenance and optional type
   constraints; `coerce_via_qualia` builds a `CoercedReference` with a
   traceable role path. (`core/lemon/qualia.py:22-70`)
4. `ProtoRoleBundle`'s `GradedEntailment` validates `[0,1]` in
   `__post_init__` and enforces that property strings match a known
   ProtoAgent/ProtoPatient enum. Dowty 1991 done properly.
   (`core/lemon/proto_roles.py:26-47`)
5. `DescriptionKind.slots` enforces unique slot names; `DescriptionClaim`
   validates slot-binding types at construction.
   (`core/lemon/description_kinds.py:29-80`)
6. `ContextReference` is a first-class dataclass; `LiftingSystem`
   validates that every rule references known contexts and that
   assumption keys match declared context IDs — no implicit ancestry.
   (`context_lifting.py`)
7. `Z3ConditionSolver` adds temporal-ordering constraints in all three
   solver entry points (disjoint / equivalent / satisfied), consistently.
8. `PredicateRegistry.from_files` rejects duplicate predicate IDs;
   `parse_derived_from` is strict about the three sanctioned DSL shapes
   and refuses anything else. (`grounding/predicates.py:242-300`)
9. `extract_facts` deduplicates via set and sorts for deterministic
   output — good adherence to Diller 2025 §3 Def 9.
   (`grounding/facts.py:118, 175-177`)
10. `_validate_lemon_document` catches duplicate sense references and
    ensures the outer `ontology_reference.uri` appears among sense
    references — at least where the validator runs.
    (`families/concepts/passes.py:206-229`)
11. Honest-ignorance thread: `SolverUnknown` / `SolverSat` / `SolverUnsat`
    form a proper three-valued result type; `_require_decided` converts to
    two-valued only at explicit two-valued call sites.
    (`z3_conditions.py:53-112`)
12. `CheckedCelExpr` carries a `registry_fingerprint` and
    `_require_matching_fingerprint` blocks using a CEL expression checked
    against a different registry — prevents a whole class of silent
    mis-evaluation. (`z3_conditions.py:370-403`)
13. Ground-bundle normalization in `grounding/grounder.py:242-292` restores
    all four Garcia & Simari 2004 §4 sections even when gunray drops
    empty ones — correct non-commitment discipline.
14. `ConflictRowInput` / `ClaimRowInput` / `StanceRowInput` in
    `core/analyzers.py` separate the typed-row boundary from the dict
    plumbing cleanly. (`core/analyzers.py:145-198`)
