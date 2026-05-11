# Cluster L: families + parameterization + structured_projection + sidecar + forms

## Scope

Files reviewed in full or in load-bearing part:

- `propstore/families/registry.py` (892 lines)
- `propstore/families/addresses.py` (6 lines)
- `propstore/families/concepts/{documents,passes,stages}.py`
- `propstore/families/claims/{documents,stages,passes}.py` (skim)
- `propstore/families/contexts/{documents,passes}.py`
- `propstore/families/forms/{documents,stages,passes}.py`
- `propstore/families/identity/{claims,concepts,logical_ids}.py`
- `propstore/families/documents/*.py` (skim of merge, sources, worldlines, micropubs)
- `propstore/parameterization_groups.py`, `propstore/parameterization_walk.py`
- `propstore/structured_projection.py`
- `propstore/sidecar/build.py`, `propstore/sidecar/concepts.py` (head)
- `propstore/dimensions.py`, `propstore/unit_dimensions.py`, `propstore/form_utils.py`
- `propstore/core/lemon/{__init__,types,forms,qualia}.py`
- `tests/test_parameterization_groups.py`, `tests/` directory listing
- knowledge/forms/acceleration.yaml (sample)
- papers/Cimiano_2016_OntoLexLemonCommunityReport/notes.md
- papers/Pustejovsky_1991_GenerativeLexicon/notes.md

Cluster B's note about a brief touch on `families/documents/sources.py` was honored;
this report focuses elsewhere on the documents subdir.

## Schema / document discipline

### `ClaimDocument` carries two parallel encodings (HIGH)

`propstore/families/claims/documents.py:560-680` defines `ClaimDocument` with both
`proposition: AtomicPropositionDocument | IstPropositionDocument | None = None`
AND ~30 inline duplicate fields (`body`, `expression`, `variables`, `parameters`,
`statement`, `concepts`, `unit`, `value`, `lower_bound`, `upper_bound`, …) that
mirror what `AtomicPropositionDocument` carries (lines 459-486). The schema
permits a claim to populate both shapes simultaneously with no enforced
disjointness. `to_payload` (line 604-680) writes both sides if present and even
emits a top-level `context` and the proposition's nested `IstProposition.context`
without reconciliation. This is a charter document for write-time / read-time
divergence: a producer using one shape and a consumer reading the other will
silently drop data. Worse, version-id hashing depends on the canonical payload
(`canonicalize_claim_for_version` in identity/claims.py:28) which
deepcopies whatever shape is present — so hash identity is a function of which
side the producer happened to fill. Recommend a tagged-union discriminator with
`forbid_unknown_fields=True` and one-shape-only validation.

### `ConceptIdScanDocument` opts out of strictness (MED)

`families/concepts/documents.py:110` sets
`forbid_unknown_fields=False` while every sibling DocumentStruct inherits the
default. There is no comment explaining the carve-out. Either the rest of the
schema is too strict for unknown fields and this is a workaround, or this
struct accepts trash silently. Pick one discipline.

### `LexicalEntryDocument.__post_init__` (concepts/documents.py:85-87)

Runtime-only enforcement that `senses` is non-empty. msgspec gives no
schema-level cardinality constraint, so authored YAML with empty senses fails
*after* decode. Fine, but the same constraint exists in
`propstore.core.lemon.types.LexicalEntry.__post_init__` (types.py:43-46).
Two parallel models with two parallel enforcements (see Lemon section).

### `FormDocument` field defaults inconsistent (LOW)

`families/forms/documents.py:25-36`: `dimensions: dict[str,int] | None = None`
treats absent as None, but `extra_units: tuple[...] = ()` and
`parameters: dict[str,Any] = msgspec.field(default_factory=dict)` treat absent
as empty. The "absent vs empty" distinction is not actually used downstream
(form_utils.py:51 maps None → None and dict(...) for the present case).
`parameters: dict[str, Any]` is the only `Any` escape hatch in the form schema.

### `FormDefinition` (forms/stages.py:30) is a mutable, cached, shared object (HIGH)

`FormDefinition` is `@dataclass` (mutable) with mutable defaults
(`set`, `dict`). Instances are stored in a module-level `_form_cache`
(stages.py:59) and returned by reference from `load_form`. Any caller who
mutates `allowed_units`, `parameters`, or `conversions` mutates the cached
copy for every other caller in the process. This is a thread-safety and
correctness bug waiting to happen. Use `@dataclass(frozen=True)` and
`MappingProxyType` / frozenset, or hand out copies.

### Two-copies of form parsing logic (MED)

`form_utils.py` and `families/forms/stages.py` both define `parse_form`,
`_KIND_MAP`, `_path_cache_key`, `load_form`, `load_form_path`,
`load_all_forms`, `load_all_forms_path`, `kind_type_from_form_name`,
`load_form_definition`, `allowed_units_from_form_definition`. They diverge
slightly already (`form_utils.parse_form` includes a `dimensions = None if ...
else dict(...)` line; `stages.parse_form` does the same — for now). Without a
tombstone or explicit deprecation, they will drift. Pick one home.

### `_form_cache` keying inconsistency (MED)

`form_utils.py:18-22` and `forms/stages.py:75-78` both build a cache key with
`Path.resolve()` for `Path`, `KnowledgePath.cache_key()` for `KnowledgePath`.
Same logical directory accessed via both Path and KnowledgePath gets cached
twice. Cache also never invalidates on mtime, so editing a form file mid-
process returns the stale parse. `clear_form_cache()` exists but caller
responsibility.

### `parse_form` form-name fallback is surprising (LOW)

`forms/stages.py:81-86` and `form_utils.py:33-41`: if `data.kind` is not a
`str`, fall back to `kind_type_from_form_name(form_name)`. That helper
checks for *exact* form name `"category"`, `"structural"`, `"boolean"`,
`"timepoint"`, else QUANTITY (form_utils.py:157-170). So a form file named
`temperature_category.yaml` with no `kind:` line silently becomes QUANTITY
because the helper does `form == "category"` not `"category" in form`. The
surprise is asymmetric: `category.yaml` works, `temperature_category.yaml`
does not. Either document the rule or make it substring-aware (or require
`kind:` always).

## Identity & address resolution

### `families/addresses.py` is a stub (LOW)

The whole file is a `NewType("SemanticFamilyAddress", str)`. Real address
resolution lives in `registry.semantic_address_path` (line 889-891), which
delegates to `family.address_for(repo, ref).require_path()`. The NewType
wrapper adds zero invariants. Fine, but note that calling code that imports
`SemanticFamilyAddress` is type-string-coerced — no runtime check, so
mistakes are not caught.

### `SourceBranchPlacement.branch_name` collision policy is wrong (HIGH)

`registry.py:191-210`. The collision suffix (`sha1-12`) is appended only when
`safe_stem != value` — i.e. when slug-encoding altered the original. Two
inputs that already happen to slug-encode the same way without modification
silently collide. Concrete failure case: `Hello` and `hello` both
slug-encode (via `safe_slug`) to the same stem with no encoding alteration,
so neither gets a suffix. Same with `force` and `Force` if `safe_slug`
preserves case (have not verified `safe_slug`'s exact rules, but the
guard-by-equality is structurally wrong regardless). The fix is to derive
the suffix from the original value unconditionally when collisions are
possible, or maintain a registry of allocated stems within the branch.

### `normalize_logical_value` does NO case folding (HIGH)

`families/identity/logical_ids.py:38-46`. `Force` and `force` produce
distinct logical IDs (`source:force` vs `source:Force`), distinct artifact
IDs (sha256 differs), and distinct branches. This conflicts with typical
lemon usage (Cimiano 2016 §3.1, p.5-7) where `LexicalEntry.canonicalForm`
normalizes for entry identity. The propstore concept registry is
therefore vulnerable to silently splitting one lemma into two entries by
case alone. Pair this with the SourceBranchPlacement defect above and a
producer that emits `Force` once and `force` once gets two distinct
concepts pointing at distinct branches.

### `_concept_logical_ids` dedup uses formatted-id only (MED)

`families/identity/concepts.py:341-382`. Dedup is by formatted
`namespace:value`. If a user-supplied entry has `namespace=propstore` with a
not-yet-normalized value, the appended propstore entry (line 375-381) gets
normalized while the existing one does not — both end up in the list.
Two `propstore:foo`-ish entries can coexist if one was authored with mixed
case and the other normalized.

### Artifact-ID truncation to 64 bits (LOW, doc-only)

`derive_concept_artifact_id` (identity/concepts.py:24-31) and
`derive_claim_artifact_id` (identity/claims.py:18-25) truncate sha256 to 16
hex chars (~64 bits). Birthday-bound is ~4 billion entries before 50%
collision risk — fine for the foreseeable future but undocumented. Add a
comment to that effect, or use 24 hex chars to push the bound out.

### `_concept_satisfies_type` traversal can blow up (LOW)

`families/concepts/passes.py:107-131`. BFS over concept relationships with no
depth bound. If two concepts have a cyclic IS_A (which the schema does not
forbid), the visited set protects against infinite loops, but the resulting
"satisfies type" decision is order-dependent and may yield false positives
once a cycle short-circuits the chain. Add a contract that IS_A graph is
acyclic, and validate.

## Forms round-trip correctness

### Unit symbols: round-trip works for symmetric conversions, NOT for affine offsets (MED)

`dimensions.normalize_to_si` and `from_si` (dimensions.py:66-113) implement
multiplicative, affine, and logarithmic conversions using inputs from
`UnitConversion`. For `affine`, round-trip is algebraically exact only when
no FP rounding occurs. With realistic offsets (e.g., 273.15 for Celsius),
`(value*m + b - b)/m` will drift in the last ULPs. No test of `from_si ∘
normalize_to_si == identity` exists in the test list (`test_form_algebra`,
`test_form_dimensions`, `test_form_utils`). Recommend an explicit
hypothesis property test for round-trip on each conversion type.

### Unit alias bypass (LOW)

`dimensions.py:29-37` defines `_PINT_ALIASES` for a small fixed set
(`°C → degC`, `µ → u`, `d → day`, etc.). Any unit symbol not in the alias
table and not understood by Pint goes straight to `pint.UndefinedUnitError →
ValueError`. There is no overlap check between `_PINT_ALIASES` and form's
own `extra_units` — if a form declares `extra_units: [{symbol: "°C", ...}]`
the form-declared dims register in `unit_dimensions._symbol_table` but
`normalize_to_si` still routes through `_PINT_ALIASES["°C"] = "degC"`, which
*may* succeed via Pint or *may* shadow the form's intent. Two unit
resolution paths with no agreed precedence.

### `parse_form` short-circuit on `unit==form.unit_symbol` is exact-string (MED)

`dimensions.py:68`, `dimensions.py:93`. A claim recording `unit: "celsius"`
against a form with `unit_symbol: "°C"` will go through Pint instead of
short-circuiting, even though they refer to the same SI unit. Round-trip
in this case can drift further. Normalize unit symbols before equality
check.

### Form filename = name policy is enforced lazily (LOW)

`forms/passes.py:104-116` raises diagnostic if `document.name !=
form.filename`. But `LoadedForm.filename` (stages.py:24) is a free-form
string set by callers. `sidecar/build.py:325` constructs `LoadedForm(filename
=handle.ref.name, document=handle.document)` — fine. But callers passing
`LoadedForm` directly (e.g. in tests) can bypass.

### Acceleration form on disk lacks fields the schema declares (informational)

knowledge/forms/acceleration.yaml has no `base`, `qudt`, `note`,
`common_alternatives` (just `[]`). All optional in `FormDocument`. So the
load works. But this means there are no real-world test inputs exercising
the optional fields; round-trip on missing-optionals is structurally tested
by msgspec's defaults but no runtime test in the listed test files
(`test_form_workflows`, `test_form_utils`) exercises a fully-populated form.

## Parameterization walk completeness

### Conditional branches are erased (HIGH)

`parameterization_walk.reachable_concepts` (parameterization_walk.py:18-58)
walks parameterization edges via the `parameterizations_for(cid)` callback
and follows `concept_ids`. It NEVER inspects the `conditions` field on a
parameterization row. So a relationship that says "concept X parameterizes
concept Y *only when condition C holds*" is treated as unconditional
reachability. Worldline conflict pre-resolution
(`conflict_detector.parameterization_conflicts`, per the docstring at line
1-7) will declare conflicts across branches that cannot simultaneously
hold. This is a paper-fidelity issue: Pustejovsky 1991 (qualia + projective
inheritance) and Fillmore frame semantics both depend on conditional
selection. Propstore stores the conditions
(`ParameterizationRelationshipDocument.conditions: tuple[CelExpr, ...]`,
concepts/documents.py:52) but the walker discards them.

### Sympy-less parameterizations dropped silently (HIGH)

`parameterization_edges_from_registry` (parameterization_walk.py:61-98)
returns edges only for parameterizations with both `inputs` AND `sympy_expr`
(line 88: `if not inputs or not sympy_expr: continue`). A relationship that
uses `formula` (string/equation) or carries only structural inputs (e.g., a
qualia-mediated coercion or a categorical mapping) is silently excluded. The
exactness filter (line 84-85) further drops anything not in the allowed set.
This is a "drop and forget" that makes the parameterization graph used
downstream a *strict subset* of what is authored. Worldline conflict
detection therefore underreports.

### `parameterization_groups.build_groups` alias collision (HIGH)

`parameterization_groups.py:79-129`. Line 94:
`alias_to_id.setdefault(candidate, concept_id)` — first-seen-wins. Two
concepts that both expose the alias `"force"` will resolve all incoming
parameterization input edges naming `"force"` to whichever concept happened
to be enumerated first. The second concept's parameterizations may union
into a component it does not belong to. There is no collision diagnostic
emitted. With case-insensitive alias resolution NOT performed (per the
identity layer's no-case-fold policy), this risk is dampened — but it
remains for case-identical aliases, which are the common case for canonical
names. Tests (test_parameterization_groups.py) only cover happy-path
disjoint-concept scenarios.

### `_parameterization_inputs` ignores formula and conditions (MED)

`parameterization_groups.py:57-76` extracts only `inputs`. Formulas with
implicit dependencies (e.g., free symbols in `sympy` not listed in `inputs`)
are not included. This is a producer-discipline issue but propstore has
no validator that asserts every free symbol in `sympy` appears in `inputs`.

## structured_projection (proposals-only check)

### No source mutation (PASS)

`structured_projection.py` is a thin facade. `build_structured_projection`
(line 209-237) imports and delegates to `aspic_bridge.build_aspic_projection`.
No filesystem writes. No commit-back to source. Result types
(`StructuredProjection`, `LiftedProjectionResult`,
`LiftedAnalyzerProjectionResult`) are frozen dataclasses with no I/O. This
file passes the proposals-only discipline.

### Side observations

- `ProjectionAtom.__post_init__` (line 58-63): coerces
  `source_assertion_ids` to `tuple(sorted({str(value) for ...}))`. Order is
  destroyed. If callers depend on insertion order (e.g., for provenance
  trace replay), this is silent loss.
- `_assertion_ids_for_claims` (line 181-198): error message uses
  `{missing!r}` against the full list of unresolved claim IDs. For large
  projections this can produce gigantic exceptions. Truncate or sample.

## Lemon / OntoLex / qualia gap analysis

### Two parallel lemon class hierarchies (HIGH)

There are two `LexicalForm` / `LexicalEntry` / `LexicalSense` definitions:

- `propstore/core/lemon/{forms,types}.py` — frozen dataclasses with
  `__post_init__` text validation, used for in-memory analysis.
- `propstore/families/concepts/documents.py` — `DocumentStruct` (msgspec)
  used for YAML decode.

Both define `LexicalForm` (one as `LexicalForm`, the other as
`LexicalFormDocument`), `LexicalSense`/`LexicalSenseDocument`,
`LexicalEntry`/`LexicalEntryDocument`. The two impose the same invariants
in different places: `lemon/types.py:43-52` raises in `__post_init__` and
`families/concepts/documents.py:85-87` does the same. There is no shared
trait, no single source of truth. Adding a new sense-level field requires
edits in two files, and they will drift.

### OntoLex coverage matrix vs Cimiano 2016

What propstore has:
- `LexicalEntry` (lemon/types.py:34, families/concepts/documents.py:78)
- `LexicalForm` / canonical_form / other_forms
- `LexicalSense.reference` (semantics-by-reference, p.3 of Cimiano)
- `usage` field (p.20)
- `qualia` (Pustejovsky-style, attached at sense level)
- `description_kind` (propstore-specific extension)
- `role_bundles` (Dowty-proto-roles attached at sense level)
- `physical_dimension_form` (propstore-specific, NOT in OntoLex)

What propstore is missing from Cimiano 2016 core:
- `Word`, `MultiwordExpression`, `Affix` subclasses of LexicalEntry (p.6).
  Grep returns nothing. Multi-word lemmas are not first-class.
- `LexicalConcept` (p.20). The skos:Concept reification — separate from
  ontology referent. Cimiano explicitly calls this out as the
  "semasiological/onomasiological split" (p.20-21). Propstore has only the
  ontology-referent side (`OntologyReference`); no mental-concept
  reification.
- `ConceptSet` (p.24).
- `evokes` / `lexicalizedSense` properties.
- `synsem` module entirely — `SyntacticFrame`, `SyntacticArgument`,
  `OntoMap`, `synBehavior`, `synArg`, `propertyDomain`, `propertyRange`.
  Cimiano §4 (p.25-38). Grep returns nothing.
- `decomp` module entirely — `subterm`, `Component`, `constituent`,
  `correspondsTo`. Cimiano §5 (p.39-44). Grep returns nothing.
- `vartrans` module entirely — `LexicoSemanticRelation`, `Translation`,
  `SenseRelation`, `ConceptualRelation`, `TerminologicalRelation`. Cimiano
  §6 (p.45-57). The `families/concepts/documents.py:ConceptRelationshipDocument`
  has a `type: ConceptRelationshipType` enum but it's not the same
  taxonomy.
- `lime` module entirely — `Lexicon`, `LexicalizationSet`,
  `ConceptualizationSet`, `LexicalLinkset`, statistics
  (`avgNumOfLexicalizations`, `percentage`, `coverage`). Cimiano §7
  (p.58-72).

Cimiano 2016 is the W3C target spec the project's CLAUDE.md cites. The
implementation is a tiny core+qualia subset. This is fine if the project
is honest about it — but as long as the code uses lemon-flavored names,
external integrators will assume OntoLex compliance. Worth Q's call on
whether to (a) rename to a propstore-specific namespace, (b) implement the
missing modules, or (c) document the intentional-subset boundary.

### Cimiano property-chain semantics not enforced

Cimiano gives property chains: `denotes ≡ sense ∘ reference` (p.14),
`evokes ≡ sense ∘ isLexicalizedSenseOf` (p.21),
`translatableAs ≡ isSenseOf ∘ translation ∘ sense` (p.55). Propstore does
not encode these as derivation rules. If any future use of the lemon
graph crosses these chains, they must be hand-rolled.

### Pustejovsky qualia drift from paper

`propstore/core/lemon/qualia.py:73-96` `purposive_chain` follows TELIC[0]
only — first child. Pustejovsky 1991 p.20 leaves multi-purposive
interpretation open; propstore commits silently to "first listed". For
a noun like *novel* with multiple telic roles (`read`, `study`, `gift`)
this is deterministic but not principled. At minimum, document the choice;
ideally let callers pass a selection policy.

`coerce_via_qualia` (qualia.py:48-70): returns the first matching
candidate (line 56-69). If multiple candidates satisfy the type
constraint, no diagnostic — and the choice is dependent on YAML
authoring order. Pustejovsky's coercion (1991 p.20, Function Application
with Coercion) implies *the* coercion path; with multiple, the lexicon
should either compose them or surface ambiguity. Silent first-match is
the worst of both worlds.

## Bugs (HIGH/MED/LOW)

### HIGH

1. **`ClaimDocument` two-shape encoding** —
   families/claims/documents.py:560-680. Inline fields *and* `proposition`
   union both populated; version-id depends on which side a producer used.
   Fix: tagged-union discriminator + forbid inline fields when proposition
   is present (or vice versa), and assert at decode.

2. **`SourceBranchPlacement.branch_name` collision detection broken** —
   registry.py:191-210. Suffix added only when slug-encoding alters input,
   so equal-stem-by-coincidence still collides.

3. **`normalize_logical_value` does no case folding** —
   identity/logical_ids.py:38-46. `Force` and `force` produce different
   artifact IDs and different branches. Splits lemma identity silently.

4. **`FormDefinition` is mutable & cached & shared** —
   forms/stages.py:30. Caller mutation poisons the cache for everyone.

5. **`parameterization_walk.reachable_concepts` ignores conditions** —
   parameterization_walk.py:18-58. Conditional branches are walked as if
   unconditional; conflict detection over-reports.

6. **`parameterization_walk.parameterization_edges_from_registry` drops
   sympy-less rels** — parameterization_walk.py:88. Whole categories of
   parameterization disappear from analysis.

7. **`parameterization_groups.build_groups` alias collision** —
   parameterization_groups.py:94. Two concepts sharing an alias merge
   silently into the first-seen concept's component.

8. **Two-tier lemon model with no shared invariants** — lemon/types.py vs
   families/concepts/documents.py. Drift inevitable.

### MED

9. `ConceptIdScanDocument` opts out of `forbid_unknown_fields` —
   concepts/documents.py:110. Inconsistent strictness.

10. Two parallel form-loading code paths (`form_utils.py` and
    `forms/stages.py`) with same logic. Drift inevitable.

11. `_form_cache` keying inconsistent across Path vs KnowledgePath; no
    mtime invalidation. Stale reads possible.

12. `dimensions.normalize_to_si` short-circuit is exact-string —
    `"celsius"` vs `"°C"` for the same SI unit go through pint instead.
    Round-trip drift.

13. `_concept_logical_ids` dedup uses formatted-id only —
    concepts.py:341-382. Mixed-case authoring can yield duplicate
    propstore-namespace entries.

14. `_parameterization_inputs` (groups.py:57) ignores `formula` free
    symbols — implicit dependencies invisible to grouping.

15. `LexicalEntryDocument` and `LexicalEntry` both runtime-validate
    "≥1 sense" — duplicated invariant.

### LOW

16. `families/addresses.py` is a 6-line NewType wrapper that adds zero
    invariants — misleading import target.

17. Artifact-ID truncation to 64 bits is undocumented. Birthday-bound is
    fine but should be on record.

18. `parse_form` form-name fallback uses exact-equality match for
    `category`/`structural`/etc, so `temperature_category.yaml` becomes
    QUANTITY (forms/stages.py:81-86, form_utils.py:33-41).

19. `ProjectionAtom.__post_init__` destroys insertion order on
    `source_assertion_ids` (structured_projection.py:58-63).

20. `purposive_chain` and `coerce_via_qualia` always pick first
    candidate; no policy hook, no ambiguity diagnostic.

21. `_concept_satisfies_type` (concepts/passes.py:107-131) has no acyclic
    contract on IS_A graph — cycle-induced order-dependence possible.

22. `_assertion_ids_for_claims` (structured_projection.py:181-198) uses
    `{missing!r}` for error message — can produce huge exceptions.

### Test gap

23. `tests/test_parameterization_groups.py` covers only happy-path
    disjoint-alias scenarios. No alias-collision test, no
    case-fold test, no cyclic IS_A test, no conditional-branch
    parameterization test, no sympy-less rel test, no
    `ClaimDocument.proposition`-vs-inline-field consistency test, no
    form round-trip property test (e.g., `from_si(normalize_to_si(v))
    == v`), no `FormDefinition`-mutability isolation test.

## Open questions for Q

- **Lemon scope:** Is propstore intentionally a tiny lemon subset
  (core + qualia + proto-roles) or aspirationally targeting OntoLex
  compliance? If the latter, missing modules (synsem, decomp, vartrans,
  lime) need to land. If the former, propstore should rename
  `LexicalEntry`/`LexicalSense` to a propstore-prefixed namespace to
  avoid implying compliance.
- **Case-insensitive identity:** Should `Force` and `force` collapse to
  one logical ID? Cimiano-style ontologies typically do. If yes, the
  identity layer needs case folding *and* an audit of existing knowledge
  files.
- **Two-shape `ClaimDocument`:** Was the inline-fields path introduced
  before `proposition`/`AtomicPropositionDocument` and never removed?
  If so, deprecate one shape and migrate authored claims.
- **Parameterization conditions:** Should conditional parameterization
  edges be walked, ignored, or projected per branch? The current code
  silently merges branches; this changes worldline conflict semantics.
- **`structured_projection` proposals discipline:** PASS in this file,
  but `aspic_bridge.build_aspic_projection` was not in scope here —
  cluster D should confirm it doesn't write back either.
- **Form caching:** Is `_form_cache` intended to survive across pipeline
  runs? If yes, mtime invalidation is required. If no, the global
  module-level dict is the wrong shape.
- **Pustejovsky multi-purposive selection:** Should `purposive_chain`
  expose a selection policy parameter, or compose all telic candidates?
  Current first-only is undocumented.
- **`SourceBranchPlacement.contract_body` says `collision_suffix:
  sha1-12` (registry.py:209)** but the implementation only applies it
  conditionally. Either fix the implementation or fix the contract — the
  contract version is `2026.04.30` so this discrepancy is fresh.
