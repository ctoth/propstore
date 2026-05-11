# Cluster M: provenance + sidecar + source ingestion

## Scope

Reviewed (read in full unless noted):

- `propstore/provenance/` — `__init__.py`, `polynomial.py`, `derivative.py`,
  `homomorphism.py`, `nogoods.py`, `projections.py`, `records.py`,
  `support.py`, `variables.py`
- `propstore/sidecar/` — `__init__.py` (skipped, re-export only),
  `build.py`, `sources.py`, `claims.py`, `passes.py`, `rules.py`,
  `concepts.py` (sampled), `embedding_store.py` (sampled),
  `micropublications.py` (sampled), `quarantine.py` (sampled),
  `schema.py` (sampled), `stages.py` (sampled)
- `propstore/source/promote.py`, `propstore/source/finalize.py`
- `propstore/sources/` — **does not exist** in tree
  (`Glob propstore/sources/**/*.py` returns nothing).
  Cluster prompt named it but no such directory is present at this
  commit. Reported as a missing-piece up-front.
- `propstore/importing/machinery.py`
- `propstore/grounding/` — `grounder.py`, `bundle.py`, `facts.py`,
  `gunray_complement.py` (other grounding files sampled)
- `propstore/compiler/__init__.py` (re-export shim)
- `docs/provenance.md`, `docs/semiring-provenance-architecture.md`
- `tests/test_provenance_polynomial_properties.py` (full)

Paper notes consulted: Buneman 2001, Green 2007, Carroll 2005, Moreau
2013 (PROV-O), Kuhn 2014 (Trusty URIs), Kuhn 2017 (Granular Refs),
Groth 2010 (Nanopublication), Wilkinson 2016 (FAIR). Clark 2014
(Micropublications), Greenberg 2009, Juty 2020, Kuhn 2015 not opened
within token budget; Cluster B is reported as having covered some.

## Semiring provenance fidelity (Green 2007)

Green 2007 §3 makes one strong claim: `N[X]` is the universal
commutative semiring; every other provenance notion (B, N, Lin(X),
Trio(X), Why(X)) is a homomorphic image obtained by a unique semiring
morphism. The architecture document (`docs/semiring-provenance-architecture.md`)
says propstore commits to this story.

What the implementation actually does:

- `propstore/provenance/polynomial.py:54-110` — `ProvenancePolynomial`
  is a canonical sparse `N[X]` value with positive integer coefficients,
  positive-exponent variable powers, and term/coefficient
  combination on construction. `__add__` concatenates terms (lines
  91-94) and the post-init combines like-terms; `__mul__` distributes
  pairwise (lines 96-110). This matches Green 2007 §3.
- Tests at `tests/test_provenance_polynomial_properties.py:39-79`
  pin `+`/`·` associativity, commutativity, identity, distributivity
  with Hypothesis. Algebra looks correct.
- `propstore/provenance/homomorphism.py:14-40` — `Homomorphism`
  Protocol with `zero`, `one`, `add`, `mul`, `variable`. `evaluate`
  walks the polynomial and applies. Clean.
- Available projections (`propstore/provenance/projections.py`):
  - `boolean_presence` (lines 53-60) — projects to **B** but is
    written as a direct existential check, not as a `Homomorphism[bool]`
    plus `evaluate`. Functionally equivalent for positive monomials but
    inconsistent with the architecture doc's claim that projections are
    "explicit homomorphisms."
  - `derivation_count` (lines 63-64) — projects to **N**, summing
    coefficients. This is `Eval_V` with `V(x) = 1` ; matches Green 2007 §3
    bag projection.
  - `tropical_cost` (lines 113-143) — min-plus projection, used as a
    derivation-cost minimum. Not a Green 2007 named projection but a
    legitimate semiring homomorphism over the (min,+) semiring. Marked
    with the "costs not confidence" warning, which is correct.
  - `why_provenance` (lines 67-88) — projects to a custom `WhySupport`
    type. Bypasses `evaluate` entirely; iterates terms and partitions
    variables by role. Buneman-style minimal-witness-basis projection
    is implemented via `normalize_why_supports` (lines 91-110) which
    drops subsumed supports. **Note:** the subsumption test at
    `projections.py:46-50` (`subsumes`) returns `True` if `self` is a
    subset of `other` — but `subsumes` is named such that one would
    read it as "self subsumes other," i.e. self ⊇ other. The
    implementation tests self ⊆ other. Used at line 107 as
    `existing.subsumes(candidate)` to decide whether to drop
    `candidate`; if `existing ⊆ candidate` then `candidate` is dropped
    — that **inverts the minimal-witness-basis intent** (Buneman 2001
    §4 Def. 7). Need to confirm with a test, but the naming is
    inconsistent with the operation either way.

What is missing vs Green 2007 §3 hierarchy:

- No `Trio(X)` projection (counting with multiplicity, abandoning
  exponents).
- No `Lin(X)` lineage projection (Boolean combinations of source
  tuples).
- No `Why(X)` *as a typed semiring* — there is a custom `WhySupport`
  but it is not exposed as a `Homomorphism[K]`, so callers cannot mix
  `evaluate(poly, why_hom)` with the rest of the projection
  infrastructure.
- No probability semiring (Fuhr–Rölleke).
- No security-classification semiring.
- No `ω`-continuous extension for recursive Datalog
  (Green 2007 §4) — the grounding pipeline is recursive (gunray
  evaluates rules), but provenance does not track the recursive fixpoint
  at all (see "Where provenance is dropped" below).

What is missing vs Green 2007 negative-result discipline:

- The architecture doc (`semiring-provenance-architecture.md` lines
  144-148) acknowledges the framework only handles positive
  provenance. Confirmed by source: there is no `__sub__`, no negation
  semiring, no m-semiring (Geerts–Poggi). Stating the limit is
  accurate.

Verdict: The polynomial layer is faithful to Green 2007 §3 for the
positive-RA fragment; the projection set is a subset of what the
architecture doc claims, and `WhySupport` is not wired through
`evaluate`. Several promised semirings are absent. The "all others
are homomorphic images" framing is not enforced — projections are
hand-coded.

## PROV-O coverage (Moreau 2013)

Searched `propstore/` for `PROV-O`, `prov:Activity`, `prov:Entity`,
`prov:Agent`, `wasGeneratedBy`, `wasDerivedFrom`, `prov:used`.

**Zero matches in source.** The PROV-O notes file is the only place
those strings appear in the repo (plus reviews/`semantic-substrate-papers.md`).

`propstore/provenance/__init__.py:43-47` declares the `prov:` namespace
prefix in the JSON-LD `@context`, and `_NamedGraphDocument` includes
it, but no actual `prov:Activity` / `prov:Entity` / `prov:Agent`
instances are emitted. The named-graph payload uses propstore-internal
predicates (`status`, `witnesses`, `graph_name`, `derived_from`,
`operations`) under the `ps:` namespace, not PROV-O classes.

The `records.py` types map cleanly onto PROV-O concepts but the
mapping is not realized:

- `SourceVersionProvenanceRecord` ↔ `prov:Entity` with
  `prov:hadPrimarySource`. Not emitted as such.
- `LicenseProvenanceRecord` ↔ no PROV equivalent (license is not in
  PROV-O but should be `dct:license`). Not emitted.
- `ImportRunProvenanceRecord` ↔ `prov:Activity` with `prov:used`
  pointing at the source entity, `prov:wasAssociatedWith` pointing
  at the importer agent. Not emitted.
- `ProjectionFrameProvenanceRecord` ↔ `prov:Activity` deriving
  entities. Not emitted.
- `ExternalStatementProvenanceRecord` ↔ `prov:Entity` with
  `prov:wasQuotedFrom` (when attitude == `quoted`) or attribution
  semantics (when attitude == `asserted`). Not emitted.
- `ExternalInferenceProvenanceRecord` ↔ `prov:Activity` with
  `prov:used` over multiple premises. Not emitted.

The records all have `to_payload()` that returns hand-rolled JSON
dicts; nothing exports to a PROV-O Turtle/JSON-LD graph. There is no
SPARQL endpoint, no CONSTRUCT, no PROV-O OWL import.

PROV-O Qualification Pattern (Moreau 2013 p.9-12, Tables 2-3) is
**unrepresented**. `Provenance.witnesses` is conceptually a Generation
qualification (`asserter`, `timestamp`, `method`) but uses propstore
field names, not `prov:Generation` / `prov:atTime` / `prov:hadRole`.

Verdict: PROV-O coverage is zero. The data model has the right
shape to project to PROV-O cheaply (an exporter would be ~200 lines)
but no exporter exists. This is a Wilkinson 2016 R1 / I1 (FAIR
"Reusable / Interoperable") gap.

## Trusty URI / nanopub / micropub provenance discipline

**Trusty URI verification: missing.** Confirmed cluster B's earlier
finding.

- `propstore/provenance/__init__.py:120-121` — `_sha_text` constructs
  `ni:///sha-1;<value>` strings (Kuhn 2014 module FA-style URIs) but
  performs no hash computation and no verification. The artifact code
  format (Kuhn 2014 §3 — 2-char module + 1-char version + 42-char
  hash) is not used.
- `propstore/artifact_codes.py` (referenced from `promote.py:28` and
  `finalize.py:5`) attaches "artifact codes" but I did not open the
  file inside this cluster's read budget; the search for `trusty`
  returns zero matches in `propstore/`, so even if codes are
  attached, the verifier-half of Kuhn 2014 §3 is absent.
- The `SourceVersionProvenanceRecord.content_hash` field
  (`records.py:33-37`) requires `hash_alg:hex` form but the validator
  only checks for the `:` separator. No verification that the hash
  algorithm is supported, no recomputation, no format-independent
  RDF normalization (Kuhn 2014 module RA).
- `derive_source_variable_id` (`variables.py:51-59`) truncates SHA-256
  to 32 hex chars (128 bits). Kuhn 2014 §3 uses full 256 bits for a
  reason; the truncation cuts the collision-resistance bound to ~2^64
  by birthday — fine at current scale but a hostile-input bound.

**Nanopublication shape vs Groth 2010: not matched.**

- Groth 2010 §3 requires three named graphs: assertion, provenance,
  publication info, all linked by trusty URIs.
- `propstore/source/finalize.py:47-97` — `_compose_source_micropubs`
  builds a single payload that mixes assertion (`claims`),
  provenance (`provenance.paper`/`page`), evidence (`evidence` list),
  and source (`source` field). One bag, no graph separation.
- No SWP (`swp:assertedBy`, `swp:Authority`, `swp:signature`)
  machinery — Carroll 2005's performative warrant model is absent.
- `_stable_micropub_artifact_id` (`finalize.py:38-40`) hashes
  `source_id\0claim_id` and prefixes `ps:micropub:`. This is a
  content-derived identifier but not a Trusty URI: the hash does not
  cover the micropub *content* (assertions, provenance, conditions),
  only the keys, so the URI does not detect content tampering.

**Micropublication (Clark 2014) tier:** the propstore micropub object
is closer to "claim with provenance" than to Clark 2014's
attribution-method-evidence triadic structure. The
`MicropublicationsFileDocument.provenance` payload is JSON-blobbed at
`passes.py:743-762` without typed witness or method/attribution roles.

## Where provenance is dropped (silent)

The cluster prompt asks specifically about silent drops. Six
confirmed sites:

1. **Gunray boundary — grounded facts.**
   `propstore/grounding/grounder.py:170-209` calls
   `evaluator.evaluate(theory, policy)` and packages the resulting
   sections. `bundle.py:73-115` claims "the bundle therefore carries
   [source_rules and source_facts] alongside the derived model so
   downstream consumers can reach back to the authored input." But:

   - `propstore/sidecar/rules.py:153-223` `populate_grounded_facts`
     persists ONLY `(predicate, arguments, section)` tuples. The
     `source_rules`, `source_facts`, and `arguments` fields of the
     bundle are not stored anywhere.
   - `read_grounded_bundle` at `rules.py:299-313` rehydrates with
     `source_rules=()` and `source_facts=()`. The docstring at lines
     303-307 admits this: "source rules and source facts are
     intentionally empty here because runtime argumentation should
     not rebuild the repository compiler inputs from files after
     sidecar build has materialized the result." This is exactly the
     silent drop — runtime consumers can never recover *why* a
     particular ground atom was derived. Buneman why-provenance is
     destroyed at the sidecar boundary.
   - `gunray.GroundingInspection` is also dropped at this boundary.

   Severity: HIGH. This contradicts the bundle docstring and breaks
   the architecture-doc claim that "current ATMS labels are already a
   why-provenance projection" — once persisted, there is no
   projection to do because the `EnvironmentKey`s do not exist on the
   read side.

2. **Source claim → promoted claim provenance laundering.**
   `propstore/source/promote.py:745-758` — when promoting, the code
   reads `claim.get("provenance")` as a dict and only copies forward
   `provenance.paper`. There is no `Provenance`/`ProvenanceWitness`
   construction; `compose_provenance` is not called; no git note is
   written via `write_provenance_note`. The named-graph machinery in
   `provenance/__init__.py:272-288` is **never imported** by
   `promote.py`. The "promote" operation should be a derivation
   (Activity in PROV-O terms) and should attach a Generation
   qualification — it does neither.

3. **Source finalize micropub composition drops witnesses.**
   `propstore/source/finalize.py:60-87` — micropub payloads include
   `evidence` with paper/page references but no `Provenance` object,
   no asserter, no method, no status. The micropub claims it was
   "composed by finalize" but there is no record of which finalize
   run, when, by whom, with what calibration.

4. **`compose_provenance` operations field is sorted alphabetically.**
   `propstore/provenance/__init__.py:185, 224-233` — the
   `operations` list is appended to in causal order
   (`record.operations` first, then the new `operation` last) but
   `_canonical_provenance` line 185 then `_dedupe_sorted` (line 142)
   converts to `tuple(sorted(set(values)))`. Causal ordering of
   operations is destroyed; replay-from-operations is not possible.

5. **Sidecar `claim_core.provenance_json` is opaque.**
   `propstore/sidecar/claims.py:38-46` — `provenance_json` is a
   single JSON column on `claim_core`. There is no separate
   `provenance_witness` table, no foreign-key to source artifacts,
   no queryable `wasDerivedFrom`. Joining provenance across claims
   requires JSON parsing in SQL.

6. **Rule-side provenance for `justification`.**
   `propstore/sidecar/passes.py:743-762` — `compile_authored_justification...`
   merges `provenance` and `attack_target` into a single dict,
   JSON-encodes it. No typed `Provenance` round-trip.

## "Imports are opinions" enforcement

Memory feedback `feedback_imports_are_opinions.md` says: every
imported KB row (BFO, QUDT, material-db, OWL rules, mined
associations, LLM proposals) is a defeasible claim with provenance,
never truth — no source is privileged.

What I observed:

- `propstore/importing/machinery.py:271-328` — `ImportMetadata`
  bundles SourceVersion + License + ImportRun + ExternalStatement +
  ExternalInference + MappingPolicy + ContextMicrotheoryMapping.
  Every authored import surface forces provenance fields; none are
  optional except `external_inference`. Good.
- `AuthoredAssertionSurface.__post_init__` (`machinery.py:91-162`)
  rejects any field that is not a non-empty URI/string. A bare
  imported claim cannot pass this validator without provenance —
  good.
- However: this lens is the structural import path. The
  source-paper claim path (`propstore/source/`) does NOT use
  `ImportAuthoredFormLens`. Source-claim ingestion goes through
  `claims.py` / `finalize.py` / `promote.py` and only ever stores a
  `paper`/`page` provenance; there is no `ExternalStatementProvenanceRecord`
  attached. So source-paper claims are imported with much *thinner*
  provenance than KB-import claims, contradicting the
  no-source-is-privileged principle in the inverse direction:
  source-paper claims are privileged in being allowed to skip the
  rich provenance witness model.
- BFO/QUDT/OWL imports: I do not see specific importers for these
  in the cluster scope. If they exist they are outside this cluster;
  if they do not exist, the principle is aspirational only.
- LLM proposals: there is no obvious "LLM proposal" provenance
  marker. The `ProvenanceStatus.STATED` value
  (`provenance/__init__.py:65`) is the closest tag but it is a
  status, not an asserter discriminator. A grep for "LLM" in the
  provenance subsystem finds nothing.

Verdict: Enforced for KB structural imports. Not enforced for source
papers (which is the dominant ingest path). Not enforced for LLM
output. Not visibly wired for OWL rules.

## Bugs (HIGH/MED/LOW)

**HIGH-1.** Grounded facts persist without provenance and rehydrate
with empty `source_rules`/`source_facts` (`sidecar/rules.py:299-313`,
`grounding/bundle.py` docstring lines 8-10). The bundle's stated
contract is broken at the sidecar boundary; downstream consumers
cannot answer "why does atom `bird(tweety)` appear in `defeasibly`?".

**HIGH-2.** Promote does not attach typed provenance and never writes
git notes for promoted claims (`source/promote.py:745-758`,
no import of `write_provenance_note`). The "named graph as
provenance carrier" story in `docs/provenance.md` lines 13-15 is not
realized for the dominant claim-creation path.

**HIGH-3.** Trusty URI verification is unimplemented despite Kuhn
2014 being explicitly cited in the architecture. URIs of the form
`ni:///sha-1;...` are constructed by `_sha_text`
(`provenance/__init__.py:120-121`) but never recomputed or checked.
Cluster B is correct.

**HIGH-4.** PROV-O export is unimplemented despite Moreau 2013 being
in the citation set. The `prov:` namespace prefix is declared but no
`prov:Activity` / `prov:Entity` / `prov:Agent` instances are emitted
anywhere in `propstore/`.

**MED-1.** `WhySupport.subsumes` (`projections.py:45-50`) is named
opposite to its operation. `self.subsumes(other)` returns True when
`self ⊆ other`, which means "self is subsumed by other," not "self
subsumes other." The downstream usage in `normalize_why_supports`
line 107 (`existing.subsumes(candidate)`) thus drops `candidate` when
`existing ⊆ candidate`. That is the **opposite** of Buneman 2001
minimal witness basis (which keeps the smallest witnesses and drops
supersets). Need a unit test to confirm but the names disagree with
the operation.

**MED-2.** `compose_provenance` reorders the operations list with
`_dedupe_sorted` (`__init__.py:141-142`, used at 185), losing causal
ordering. PROV-O `prov:wasInformedBy` chains require ordered
predecessors; alphabetical sort breaks any "this happened then this"
narrative.

**MED-3.** Two different witness-key tuple orderings exist in the
same module: `_witness_key` at `__init__.py:145-151` uses
`(asserter, method, source_artifact_code, timestamp)`, while
`compose_provenance` at lines 213-218 builds the dedup key as
`(asserter, timestamp, source_artifact_code, method)`. Frozenset
membership is unaffected (set semantics ignore order), but two
different sort orders on the same field set means a refactor that
unifies them risks subtly reordering witness output. Easy to fix;
should share one helper.

**MED-4.** `derive_source_variable_id` truncates to 128 bits
(`variables.py:59`). Birthday-bound collision at ~2^64 sources.
Acceptable for current scale but should be documented as a deliberate
choice. Trusty URI baseline is 256 bits.

**MED-5.** `Provenance.graph_name` is required for `encode_named_graph`
(via `_require_graph_name`, `__init__.py:161-167`) but `compose_provenance`
constructs a `Provenance` without setting `graph_name`
(`__init__.py:225-232`) — and then immediately calls
`_canonical_provenance(..., require_graph_name=False)`. So composed
provenance cannot be encoded as a named graph without a separate
graph-name assignment step. There is no helper for that step. Callers
will silently get a `ValueError("provenance graph_name must be
explicit")` when they try to encode.

**MED-6.** `_stable_micropub_artifact_id` (`finalize.py:38-40`) hashes
only `source_id\0claim_id`. Any change to the micropub payload (new
evidence, new conditions, new provenance) does NOT change the artifact
id. This breaks the Trusty URI principle that "any change creates a
new URI" (Kuhn 2014 §3.2 immutability property) and silently
overwrites micropubs on re-finalize.

**MED-7.** `populate_grounded_facts` uses bare `INSERT` (no `OR
IGNORE`) per the docstring at `rules.py:163-167`. If the same
`build_sidecar` runs grounding twice without dropping the table,
the second run raises `IntegrityError`. The build pipeline calls
`create_grounded_fact_table` with `IF NOT EXISTS` (line 132) — so on
a second build (force=False, existing sidecar) the table survives but
the rows survive too, and the second `INSERT` collides. Confirmed by
reading `build.py:289-594` — the temp-sidecar pattern means the
table is fresh on each rebuild, so this only bites callers who reuse
a connection. Less severe than feared but still a bug.

**MED-8.** `_compute_blocked_claim_artifact_ids` (`promote.py:323-419`)
treats stance `target` failures by recording the diagnostic against
the `source_claim`, not the stance itself. If the same source_claim
has 10 stances each with a broken target, the source_claim collects
10 `stance_reference` diagnostics and is itself blocked from
promotion. That punishes the source claim for downstream ref
breakage. Possibly intended; flagging because it conflates two
provenance scopes.

**LOW-1.** `_canonical_provenance` requires graph_name for the encode
path but allows None for compose; the type system does not encode this
invariant — `Provenance.graph_name: str | None`. A
`UnencodableProvenance` subclass or a phantom-typed witness would make
this safer.

**LOW-2.** `read_grounded_facts` raises `ValueError` for an unknown
section name (`rules.py:262-264`). The schema-level constraint is not
defended at write time; the table allows any string for `section`.

**LOW-3.** `tropical_cost` returns `inf` for an empty polynomial via
`hom.zero` (`projections.py:121`). Documented as "preferred derivation
cost"; an empty support means "no derivation," and infinite cost is the
right tropical zero. Not a bug; flagging in case caller treats `inf` as
"unknown" rather than "impossible."

**LOW-4.** `_filter_invalid_context_lifting_rows` (`build.py:256-269`)
silently drops lifting rules whose source/target context is unknown
when `context_diagnostics` is non-empty. No diagnostic is recorded
for the dropped rule. This is a silent provenance drop at the
sidecar boundary; should at least log.

**LOW-5.** `compose_provenance` status uses
`max(records, key=lambda item: _STATUS_RANK[item.status.value]).status`
(`__init__.py:201`). If two records have equal max rank, Python's
`max` returns the first input. Result depends on caller's iteration
order. Not a correctness bug (both have the same rank-equivalent
status) but a determinism wart.

## Missing features

- PROV-O exporter (Turtle / JSON-LD) for `Provenance`, `ImportRunProvenanceRecord`,
  `ExternalInferenceProvenanceRecord`, etc. ~200 lines.
- Trusty URI compute-and-verify module (Kuhn 2014 §3 modules FA + RA).
  Without this, propstore cannot detect content tampering.
- `Trio(X)`, `Lin(X)`, `Why(X)` typed semiring projections wired
  through `Homomorphism` / `evaluate` for parity with Green 2007 §3.
- ω-continuous extension or formal-power-series provenance for
  recursive Datalog (Green 2007 §4). Currently the grounding
  recursion is provenance-blind.
- Nanopublication-style three-graph emission (assertion / provenance
  / publication-info) for Groth 2010 compliance.
- SWP `assertedBy` / `Authority` / signature attribution
  (Carroll 2005 §5).
- A persistence layer for `SourceVariable` so the architecture doc's
  promise that "label storage can be collapsed into a view"
  (semiring-provenance-architecture.md line 37) can actually happen.
  Currently `SourceVariable` exists in `variables.py` but is not
  written to the sidecar.
- A negation/difference semiring or explicit refusal to support it
  with a runtime error rather than silently producing a positive-only
  polynomial.
- Provenance round-trip tests for the gunray boundary (HIGH-1).

## Open questions for Q

1. Is the cluster-prompt path `propstore/sources/` (plural, separate
   from `propstore/source/`) supposed to exist? If yes, where? If no,
   strike from future scopes. Cluster-A and Cluster-M both reference
   it.
2. Is grounded-fact provenance dropping at the sidecar boundary
   (HIGH-1) deliberate (perf) or unintended (bug)? The docstring at
   `rules.py:303-307` calls it "intentional," but the bundle docstring
   at `bundle.py:8-10` calls full provenance retention a contract.
   These two statements are inconsistent.
3. PROV-O export: should the `Provenance` named-graph encoder emit
   PROV-O classes directly, or should there be a separate
   `prov_o_export.py`? Today the code emits propstore-internal
   predicates under `ps:` namespace, which is interoperability-hostile
   per Wilkinson 2016 I1.
4. Trusty URI verification: do you want it as an opt-in module or
   enforced at write time? Without verification the immutability
   property of Kuhn 2014 cannot be claimed.
5. `WhySupport.subsumes` (MED-1): is the inverted naming intentional
   (perhaps "self is subsumed by other" was meant) or is the operation
   wrong? A renaming-only fix is safe; a behavior fix changes
   minimal-witness output.
6. `_stable_micropub_artifact_id` (MED-6): should it be a true Trusty
   URI over the full payload? If yes, the upgrade path is breaking —
   every existing micropub gets a new id.
7. Source-paper claims have weaker provenance than KB structural
   imports (the "imports are opinions" inversion). Is the asymmetry
   deliberate (papers are "primary sources" so are privileged) or
   should source-paper claims also flow through
   `ExternalStatementProvenanceRecord`?
8. `compose_provenance` operations sort (MED-2): would you prefer
   operations as a `list` retained in causal order, or as a `set` with
   explicit `prov:wasInformedBy` edges between sequenced steps?
