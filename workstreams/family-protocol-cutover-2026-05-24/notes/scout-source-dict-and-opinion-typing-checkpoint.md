# Scout: source dict + opinion typing — checkpoint

2026-05-24 — scout dispatched to answer 4 questions about `source` dict, persistence opinion typing, import-graph, Opinion shape.

## Status
- Read prompt + scout-v001-v003-typed-claim-api.md (prior scout's report) + `propstore/opinion.py` + `propstore/core/graph_types.py` ClaimNode block.
- Read `propstore/praf/engine.py` lines 180-300 (reader side of `source` keys).
- Read `propstore/argumentation.py` lines 680-720 (`build_praf_from_shared_input`, omitted_relations missing_fields).
- Read `propstore/praf/projection.py` (lightweight delegator).
- Read `propstore/probabilistic_relations.py` (RelationProvenance keys list — includes `opinion_belief/disbelief/uncertainty/base_rate`).

## Observations (verified)

### `opinion_*` keys in propstore code (verified, file:line):
- `propstore/argumentation.py:710-713` — only as `missing_fields` literal in `NoCalibration` (for OMITTED relation calibration). NOT a read or write of attributes bag.
- `propstore/probabilistic_relations.py:24-27` — `_PROVENANCE_KEYS` tuple. Used at line 74-78 (`provenance_from_row`) to read these as keys of a stance ROW DICT (not ClaimNode.attributes). It's a stance-row provenance digest, not a ClaimNode read.
- `propstore/praf/engine.py:202-217, 272-277` — primary readers via `claim_metadata_value`.
- `propstore/praf/engine.py:312-318, 343-345` — `_opinion_from_payload(stance, prefix=...)` reads stance DICT (relation/stance row, not ClaimNode).
- `propstore/relation_analysis.py:37` — `row.attribute_value("opinion_uncertainty")` — `row` is a Relation row (per Relations charter line 147-150 these are TYPED columns on Relation, accessed via attribute_value).
- `propstore/families/relations/declaration.py:147-150` — Relation family TYPED CharterFields. Lines 214-217: WRITER (from resolution.opinion). This is RELATION family, not Claim family.
- `propstore/world/resolution.py:123-126, 170-173, 593-596` — `opinion_*` fields on a `_ClaimResolution`-like dataclass + 5 callsites (already enumerated by prior scout).

### `source_prior_base_rate` / `source_quality_opinion` in propstore code:
- READERS: only `propstore/praf/engine.py:204, 217` (already enumerated by prior scout).
- WRITERS: NONE in `propstore/`. Search of `propstore/` finds only the two reader sites + the `missing_fields` literals at 229/231/234/238.
- TESTS write to `ClaimNode.attributes` dict — e.g. `tests/typed_family_fixtures.py:21-22`, `tests/test_core_analyzers.py:175,185`, `tests/test_praf_integration.py` (multiple), `tests/test_worldline_praf.py:71,81`, `tests/test_ws_f_aspic_bridge.py:487` (`attributes={"source_prior_base_rate": prior}`).
- This means: in PRODUCTION there is NO writer that puts `source_prior_base_rate` or `source_quality_opinion` into a ClaimNode's attributes. Only TEST FIXTURES do.

### What this strongly suggests for Section 6 (verdict on source dict's fate):
- `source` dict reads at `praf/engine.py:202-219` only touch `source.get("trust").get("prior_base_rate")` and `source.get("trust").get("quality")`. These are FALLBACKS for the typed `source_prior_base_rate` and `source_quality_opinion` reads.
- If no production code WRITES either the `source` dict or the two `source_*` keys into ClaimNode.attributes, then the entire path is test-fixture-only.
- Need to verify the `source` writer side now — pending grep.

### Opinion shape (verified from `propstore/opinion.py`):
- `Opinion(_DoxaOpinion)` subclass. `_DoxaOpinion` is frozen dataclass (per docstring line 83-84). Constructor takes `(b, d, u, a, provenance=None, allow_dogmatic=False)`. Uses `object.__setattr__` to attach provenance (line 88).
- Has `__repr__` override. Subclass of frozen dataclass → hashable+orderable per parent semantics. Provenance field added via slot trick.
- Construction is pure — calls `super().__init__` (which does range/sum validation) then attaches provenance. No global registration, no side effects.
- `Opinion(0.5, 0.0, 0.5, 0.5, None)` — works iff `b+d+u==1.0` (validated by parent). Caller must ensure mass-sum.

### Import graph audit pending
- `propstore/opinion.py` imports:
  - `from doxa import BetaEvidence, Opinion`
  - `from doxa.opinion import W`
  - `from propstore.provenance import Provenance, ProvenanceStatus, compose_provenance`
- Need to check `propstore.provenance` import chain — does it touch `propstore.core.graph_types`?

## Pending work
1. Grep writers of `source` key into ClaimNode.attributes in propstore/.
2. Grep ClaimNode construction sites — does anything in production stuff opinion_* into .attributes?
3. Trace `propstore.provenance` imports for import-cycle check.
4. Confirm `propstore.families.claims.declaration.Claim`/`ClaimNumericPayload` does NOT have opinion_* fields (prior scout said no — verify).
5. Write deliverable report.

## Blockers
None. Continue.

## Update 2 — additional findings

### `source` writers in propstore/ (verified):
- `propstore/demo/reasoning_demo.py:85, 148` — `"source": {"paper": "reasoning_demo"}` in CLAIM FILE PAYLOAD dict (input to `normalize_claim_file_payload`), NOT writing to ClaimNode.attributes. This is the document-level `source` field for the whole claim file.
- `propstore/app/rules.py:217` — `"source": {"paper": request.paper}` in RULE DOCUMENT payload, NOT ClaimNode.attributes.
- `grep "attributes.*\"source\"" propstore/` returns ZERO matches in propstore/ production code.
- TEST writer to `ClaimNode.attributes`: only `tests/test_ws_f_aspic_bridge.py:487` writes `attributes={"source_prior_base_rate": prior}` directly. NO test writes the dict-shaped `source` into ClaimNode.attributes.

### Canonical ClaimNode builder verified:
- `propstore/families/claims/graph.py:34-73` `claim_node_from_claim` is the single production builder Claim → ClaimNode.
- `_claim_graph_attributes` (line 95-117) only adds: `primary_logical_id, logical_ids_json, version_id, seq, target_concept, provenance_json, premise_kind, branch, build_status, stage, promotion_status, confidence`.
- It does NOT write `source`, `source_prior_base_rate`, `source_quality_opinion`, or any `opinion_*` keys.
- `confidence` IS written here (line 112-114) from `numeric_payload.confidence`.

### Persistence-side verified — NO opinion fields on Claim/ClaimNumericPayload:
- `grep "opinion_belief|opinion_disbelief|opinion_uncertainty|opinion_base_rate|claim_opinion" propstore/families/claims/declaration.py` → zero matches.
- ClaimNumericPayload at line 243 just has `pass` (FamilyModel autogen); charter at line 386-?? lists numeric fields. Already trusted prior scout: only sample_size, uncertainty, confidence, value, bounds, etc.

### Opinion ENTERS Claim from outside? Trace shows:
- Calibrator: `propstore/heuristic/calibrate.py` produces `Opinion` objects but does NOT write back to Claim charter fields.
- praf/engine.py BUILDS Opinion from raw numeric values + provenance.
- `propstore/families/relations/declaration.py:214-217` is the only WRITER that populates `opinion_belief/disbelief/...` typed columns — and it's on RELATION family, not Claim.
- Therefore: Opinion is PURELY IN-MEMORY for Claim. Round-trips through Relation (stance edge), not through Claim. The `source_prior_base_rate / source_quality_opinion` attribute values on ClaimNode are populated... NOWHERE in current production code (verified by zero writers).

### Import-graph verified:
- `propstore.opinion` imports: `doxa.BetaEvidence/Opinion/W` (external), `propstore.provenance.{Provenance, ProvenanceStatus, compose_provenance}`.
- `propstore.provenance.__init__` imports: `msgspec`, `dulwich`, `quire.notes`, `quire.documents`, and from internal sibling modules (`derivative, homomorphism, nogoods, polynomial, projections, records, support, variables`).
- Internal siblings checked:
  - `provenance/projections.py` imports `propstore.core.id_types` (NOT graph_types)
  - `provenance/trusty.py` imports `propstore.uri`
  - Others import only sibling provenance modules.
- NONE of these touch `propstore.core.graph_types` or `propstore.core.conditions.*` or anything that would round back.
- `core/graph_types.py` imports: `cel_types, families.claims.types, core.conditions.{checked,codec}, core.environment, core.exactness_types, core.graph_relation_types, core.id_types, core.labels`. NO import of `propstore.opinion` or `propstore.provenance`.
- VERDICT: Adding `from propstore.opinion import Opinion` to `propstore/core/graph_types.py` is SAFE — no cycle.

### Opinion shape compatibility:
- Subclass of frozen dataclass `_DoxaOpinion`. Uses `object.__setattr__` for provenance attach (line 88).
- Frozen-dataclass means immutable and hashable IF parent's __eq__/__hash__ are inherited (frozen dataclass auto-generates both based on fields).
- Provenance field is class-level annotation `Provenance | None = None` (line 72) but NOT part of doxa.Opinion's dataclass fields — it lives "off-the-books" attached via __setattr__. This means: equality/hashing is based on (b,d,u,a) from parent dataclass only; provenance is NOT in hash/eq.
- Constructor `Opinion(b, d, u, a, provenance=None, allow_dogmatic=False)` — works iff `b+d+u==1.0` per parent validation.
- Usable as a default-`None` field on another frozen dataclass: YES, since None is the default and Opinion itself is hashable+orderable. The `compare=False` pattern used for `checked_conditions` / `label` is NOT required.
- No import side effects.

### Pending: write the final deliverable report. All section answers are now in hand.
