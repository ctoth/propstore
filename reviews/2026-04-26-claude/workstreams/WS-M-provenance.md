# WS-M: Provenance — Trusty URI, PROV-O export, gunray boundary, full-hash identity

**Status**: CLOSED 623f892d
**Depends on**: WS-CM (canonical micropub payload + Trusty URI identity), WS-E (assertion-id provenance, sameAs grading), **WS-O-gun** (per Codex 1.13 + D-18: gunray must wire `EnumerationExceeded`/`max_arguments` before propstore can default `return_arguments=True`), RFC 6920 (`ni://` URI scheme), W3C PROV-O / PROV-DM / PROV-N — last three pending retrieval per `reviews/2026-04-26-claude/REMEDIATION-PLAN.md:298`.
**Blocks**: nothing downstream of this file. WS-N's architecture contracts can lean on WS-M but do not require it to land first.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

---

## Why this matters

Four of propstore's load-bearing claims are written into the architecture documents and the citation set, and none of them is enforced in code:

1. The architecture claims **Buneman/Carroll-grade provenance** is carried through the system. A read of `propstore/provenance/__init__.py:43-47` confirms the `prov:` namespace prefix is declared — but a grep of the rest of `propstore/` finds zero `prov:Activity`, zero `prov:Entity`, zero `prov:Agent`, zero `prov:wasDerivedFrom`, zero `prov:wasGeneratedBy`, zero `prov:used`. The PROV-O notes at `papers/Moreau_2013_PROV-O/notes.md` are the only place those strings appear in-repo. The doc claim is decorative.
2. The architecture claims **Trusty URI** discipline (Kuhn 2014). `propstore/provenance/__init__.py:120-121` builds strings of the shape `ni:///sha-1;<value>` via `_sha_text`. That function performs no hash computation, no canonicalization, and no verification. The Kuhn 2014 §3 artifact-code format is not used. The string `trusty` does not appear in `propstore/` source.
3. The architecture claims **gunray's DefeasibleTrace** is preserved across the propstore/gunray boundary. `propstore/sidecar/rules.py:299-313` returns `GroundedRulesBundle(source_rules=(), source_facts=(), …)` on rehydrate. The docstring at lines 303-307 calls this "intentional"; the bundle's own docstring at `grounding/bundle.py:8-10` calls full retention a contract. Two parts of the same subsystem disagree.
4. The architecture **implicitly** assumes identity is content-addressable end to end. In practice, several production identity surfaces are *truncated* hashes (`[:16]`, `[:24]`, `[:32]`-as-identity). Truncation reduces a verifiable Trusty URI to a near-collision-free coincidence. Per **D-20** the truncated-hash policy now belongs to WS-M: production stores full content hashes; truncation is a render-only concern.

These are not minor. Once provenance is decorative, every other guarantee that names a paper falls into "we cite it but we do not verify it." That is exactly the failure mode the *imports are opinions* memory rule was put in place to prevent. WS-M closes the hole.

## Review findings covered

WS-M closes everything in the table below. "Done means done" — every finding is gone from `docs/gaps.md` and has at least one green test gating it.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T4.1** | Claude REMEDIATION-PLAN | `cluster-R-gunray.md` §"Provenance through evaluation" | Gunray boundary must preserve `DefeasibleTrace` *and* the rule-id back-pointers — both directions. |
| **T4.2** | Claude REMEDIATION-PLAN | `provenance/__init__.py:120-121` | Trusty URI verification (Kuhn 2014): `_sha_text` builds `ni:///sha-1;…` URIs without computing or verifying the hash. |
| **T4.3** | Claude REMEDIATION-PLAN | `provenance/__init__.py:43-47` (only `@context` mention of `prov:`); zero PROV-O classes elsewhere | PROV-O export (Moreau 2013) emitting `prov:Activity` / `prov:Entity` / `prov:Agent` at the export boundary. |
| **T4.4** | Claude REMEDIATION-PLAN | `storage/repository_import.py` (zero provenance grep — verified) | `repository_import.py` annotates imported rows with provenance. |
| **T4.5** | Claude REMEDIATION-PLAN | `provenance/__init__.py:185, 224-233`, `_dedupe_sorted` line 141-142 | `compose_provenance` preserves causal order — drops the alphabetical sort. |
| **T4.6** | Claude REMEDIATION-PLAN | `provenance/projections.py:45-50, :107` | `WhySupport.subsumes` rename or fix to match behaviour (Buneman 2001 §4 Def 7). |
| **T4.7** | Claude REMEDIATION-PLAN | `core/labels.py:265, :350, :375` | Semiring polynomial provenance not collapsed to ATMS why-labels prematurely (Codex #27). |
| **T4.8 (D-20)** | DECISIONS.md D-20 | `worldline/hashing.py:46`, `support_revision/projection.py:174`, `source/finalize.py:38-40` | Every short-hash identity site converted to full content-hash identity; truncation moves to render-time only. |
| **Cluster M HIGH-1** | `cluster-M-provenance-sources.md:321-327` | `sidecar/rules.py:299-313`, `grounding/bundle.py` docstring | Grounded facts persist to sidecar without provenance; rehydration empties `source_rules`/`source_facts`. propstore-side fix; gunray-side overlap is WS-O-gun. |
| **Cluster M HIGH-2** | `cluster-M-provenance-sources.md:328-332` | `source/promote.py:745-758` | Promote mutates the `provenance` dict in-place; never composes a typed `Provenance`; never writes a git note via `write_provenance_note`. |
| **Cluster M HIGH-3 = T4.2** | — | — | Trusty URI verification missing. |
| **Cluster M HIGH-4 = T4.3** | — | — | PROV-O export missing. |
| **Cluster M MED-1 = T4.6** | — | — | `WhySupport.subsumes` naming/behaviour mismatch. |
| **Cluster M MED-2 = T4.5** | — | — | `compose_provenance` causal-order drop. |
| **Cluster M MED-3** | `cluster-M-provenance-sources.md:362-371` | `provenance/__init__.py:145-151` vs `:213-218` | Two witness-key tuple orderings in the same module. |
| **Cluster M MED-6** | `cluster-M-provenance-sources.md:387-392` | `source/finalize.py:38-40` | `_stable_micropub_artifact_id` payload-blind hash. Micropub identity is owned by WS-CM per D-29; WS-M consumes it for provenance verification. |

Adjacent findings closed in the same PR because the substrate is open:

| Finding | Citation | Why included |
|---|---|---|
| `compose_provenance` cannot encode named graph | `provenance/__init__.py:225-232`, `:236-247` | Result has `graph_name=None`; `encode_named_graph` would raise. While we touch `compose_provenance` to fix MED-2, name the invariant. |
| `Provenance.graph_name` typing | `provenance/__init__.py:90-98` | `graph_name: str \| None` permits the unencodable case. Same touch zone. |
| `derive_source_variable_id` 128-bit truncation | `provenance/variables.py:51-59` | Subsumed by D-20: full 256-bit hash now, truncation moves out of identity. |

## Code references (verified by direct read)

### Trusty URI surface (decorative)
- `propstore/provenance/__init__.py:120-121` — `_sha_text(value)` returns `value if value.startswith("ni:///sha-1;") else f"ni:///sha-1;{value}"`. No hashing, no verification. **Per Codex re-review #17**: the SHA-1 prefix here is a relic of the original draft; WS-M targets **sha-256 only** per RFC 6920 modern-preference + Kuhn 2014 follow-on practice. Step 1 below replaces this with `compute_ni_uri(... algorithm="sha-256")`; SHA-1 is dropped from the primary target and not preserved as a fallback.
- `propstore/source/finalize.py:38-40` — `_stable_micropub_artifact_id` computes `sha256(f"{source_id}\\0{claim_id}")[:24]` and prefixes `ps:micropub:`. Payload-blind AND truncated. Two D-20 violations in one expression.
- `propstore/provenance/variables.py:51-59` — `derive_source_variable_id` truncates SHA-256 to 32 hex chars (128 bits). D-20 says: store the full hash.

### Truncated-hash identity sites (D-20 audit, verified)
- `propstore/worldline/hashing.py:46` — 16-hex truncation used as identity.
- `propstore/support_revision/projection.py:174` — 32-hex truncation used as identity.
- `propstore/source/finalize.py:38-40` — `[:24]` micropub artifact id (above).
- `propstore/provenance/variables.py:51-59` — `[:32]` source variable id (above).
- Any `[:N]` slice on a hex digest reachable from a write path is suspect; Step 1 below runs the full audit and adds matches.

### PROV-O surface (decorative)
- `propstore/provenance/__init__.py:43-47` — `_CONTEXT` declares `prov:` and `swp:` prefixes.
- `propstore/provenance/__init__.py:236-247` — `encode_named_graph` emits a document with `@type: "NamedGraph"` and a `provenance` payload using propstore-internal keys (`status`, `witnesses`, `derived_from`, `operations`). No `prov:Activity`, no `prov:Entity`, no `prov:Agent`.
- `propstore/provenance/records.py:54-280` — five typed records (`SourceVersionProvenanceRecord`, `LicenseProvenanceRecord`, `ImportRunProvenanceRecord`, `ProjectionFrameProvenanceRecord`, `ExternalStatementProvenanceRecord`, `ExternalInferenceProvenanceRecord`) all expose `to_payload()` returning hand-rolled dicts. None are emitted as PROV-O.

### compose_provenance (causal order destroyed)
- `propstore/provenance/__init__.py:189-233` — appends `record.operations` first then `operation` last; line 224 appends new `operation` to the list.
- `propstore/provenance/__init__.py:141-142` — `_dedupe_sorted` is `tuple(sorted(set(values)))`.
- `propstore/provenance/__init__.py:185` — `_canonical_provenance` runs `operations` through `_dedupe_sorted`. Causal order destroyed at canonicalisation. PROV-O `prov:wasInformedBy` chains require ordered predecessors.

### Witness-key ordering inconsistency
- `propstore/provenance/__init__.py:145-151` — `_witness_key = (asserter, method, source_artifact_code, timestamp)`.
- `propstore/provenance/__init__.py:213-218` — `compose_provenance` builds dedup keys as `(asserter, timestamp, source_artifact_code, method)`.

### WhySupport.subsumes (naming inverted)
- `propstore/provenance/projections.py:45-50` — `subsumes(self, other)` returns True when `set(self.assumption_ids).issubset(other.assumption_ids)`. So `self.subsumes(other)` reads "self is *subsumed by* other."
- `propstore/provenance/projections.py:107` — used as `if any(existing.subsumes(candidate) for existing in minimal): continue`. Effective behaviour is correct as a *minimal* basis (Buneman 2001 §4 Def 7); the name is the bug. Pin behaviour with a property test, then rename.

### Promote: provenance laundering
- `propstore/source/promote.py:745-758` — for every promoted claim, reads `claim.get("provenance")` as a dict, mutates only `provenance.paper`, writes back. No `Provenance` construction, no `compose_provenance`, no `write_provenance_note`. Grep for `write_provenance_note` in `propstore/source/` returns zero matches.

### Repository import: provenance-blind
- `propstore/storage/repository_import.py` — full read; grep for `provenance|Provenance|witness|trusty|prov:` returns zero matches. `RepositoryImportPlan` and `commit_repository_import` write documents from one repository's snapshot into another's branch with no attached provenance record. Direct violation of "imports are opinions."

### Sidecar grounded facts: provenance lost across boundary
- `propstore/sidecar/rules.py:299-313` — `read_grounded_bundle` returns empty `source_rules`/`source_facts`; docstring claims "intentional."
- `propstore/grounding/bundle.py:8-10` — bundle docstring claims full retention is the contract. Inconsistent.
- `propstore/grounding/grounder.py:170-171` — calls `evaluator.evaluate(theory, policy)` (the non-trace entry) and then separately `gunray.inspect_grounding(theory)`. The `DefeasibleTrace` is discarded at the boundary.
- `propstore/grounding/grounder.py:141-149` — `return_arguments` defaults to `False`. Per Codex 1.13 the default flips to `True` *only after WS-O-gun ships budget wiring* (D-18 `EnumerationExceeded` / `max_arguments`). Until then, defaulting on would risk a hang or partial "complete" result on the exponential-argument path WS-O-gun documents.

### Semiring polynomial → ATMS labels (premature collapse)
- `propstore/core/labels.py:265-282` — `combine_labels` carries a `ProvenancePolynomial`, then on every iteration runs `_polynomial_to_environments(support)` (line 278) → ATMS, normalises against nogoods, converts back via `_environments_to_polynomial`. Coefficient information (Green 2007 §3 `N[X]` derivation count) is lost on the way in.
- `propstore/core/labels.py:350-356`, `:359-372`, `:375-387` — round-trip is lossy; `derivation_count` projection computed *after* `combine_labels` is wrong even when the pre-combine polynomial was correct.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_trusty_uri_verification.py`** (new — gating sentinel)
   - **Per Codex re-review #17**: Trusty URIs emitted by propstore use the **`ni:///sha-256;…` form exclusively**. RFC 6920 supports both SHA-1 and SHA-256, but modern Trusty URI practice (Kuhn 2014 follow-on) uses SHA-256; SHA-1 is dropped from the primary target.
   - For every callsite that emits a `ni:///sha-256;…` string, assert the suffix is exactly the SHA-256 of the canonicalised content the URI claims to name.
   - Assert that no `ni:///sha-1;` string is emitted by any production code path; grep the codebase for the literal `ni:///sha-1;` and assert zero hits in `propstore/` (matches in test fixtures asserting the absence are allowed; matches in this WS file's prose are allowed).
   - Assert `compute_ni_uri(b"some-content")` returns a string starting with `ni:///sha-256;`.
   - Assert `_sha_text("not-a-hash")` (where it still exists during transition) raises; after Step 1 the function is gone.
   - Pin canonical encoding to RFC 6920 / Kuhn 2014 §3 once on disk; the test tolerates either hex or base64url so long as round-trip verifies.
   - **Must fail today**: `_sha_text` builds `ni:///sha-1;` strings without verification AND uses the wrong (legacy) algorithm.

2. **`tests/test_no_truncated_identity.py`** (new — D-20 sentinel)
   - AST-walk `propstore/`; flag every `Subscript` slice over a hex digest expression (`hashlib.*hexdigest()[:N]` or `_sha*(...)[:N]`).
   - Grep complement: `[:16]`, `[:24]`, `[:32]`, `[:40]` literal slices in any `propstore/**/*.py` outside the display-only allowlist (`propstore/web/html.py`, `propstore/web/render.py`).
   - Assert the matched-set is empty.
   - Allowlist file `propstore/web/render.py` (and similar render-only modules) is documented in the test header. New display-only zones need an explicit comment + test entry.
   - **Must fail today**: at least four hits — `worldline/hashing.py:46`, `support_revision/projection.py:174`, `source/finalize.py:38-40`, `provenance/variables.py:51-59`.

3. **`tests/test_prov_o_export.py`** (new)
   - For each of the five typed records in `propstore/provenance/records.py`, call a new `to_prov_o()` method and assert the result is a valid PROV-O JSON-LD document.
   - Validation: parse to RDF, run `pyshacl`/`rdflib` checks against W3C PROV-O OWL constraints (spec retrieval pending). Until then, shape-only: each record emits at least one `prov:Entity` or `prov:Activity` typed node, and the appropriate `wasDerivedFrom` / `wasAssociatedWith` / `wasQuotedFrom` predicates.
   - Specifically:
     - `SourceVersionProvenanceRecord` → `prov:Entity` with `prov:hadPrimarySource`.
     - `ImportRunProvenanceRecord` → `prov:Activity` with `prov:used` + `prov:wasAssociatedWith`.
     - `ProjectionFrameProvenanceRecord` → `prov:Activity` deriving entities (`prov:wasDerivedFrom`).
     - `ExternalStatementProvenanceRecord` → `prov:Entity` with `prov:wasQuotedFrom` (when `attitude == quoted`) or `prov:wasAttributedTo` (when `attitude == asserted`).
     - `ExternalInferenceProvenanceRecord` → `prov:Activity` with `prov:used` over premises and `prov:generated` for the conclusion.
   - PROV-O is a **read-only export representation** (Codex 1.5). The internal mutation paths still operate on the typed records. Round-trip `prov_o_to_record(record_to_prov_o(r)) == r` is **not** required and is **not** tested — PROV-O is a one-way projection out of the internal model.
   - **Must fail today**: no `to_prov_o()` method exists.

4. **`tests/test_compose_provenance_causal_order.py`** (new)
   - Call `compose_provenance(rec_a, rec_b, operation="op_z")`, where each carries an `operations` tuple already in causal order.
   - Assert composed `Provenance.operations` is the *concatenation* in input order plus `"op_z"` at the end.
   - Assert that swapping `rec_a` and `rec_b` produces a different result whenever the chains differ.
   - **Must fail today**: `_canonical_provenance` `_dedupe_sorted` reorders alphabetically.

5. **`tests/test_witness_key_uniformity.py`** (new)
   - AST-walk `propstore/provenance/__init__.py`; locate every `_witness_key`-shaped tuple literal. Assert all such tuples have the same field order.
   - Assert that `compose_provenance`'s dedup-key tuple at line 213-218 uses `_witness_key(witness)` rather than an ad-hoc tuple.
   - **Must fail today**: `:145-151` and `:213-218` use different orders.

6. **`tests/test_why_support_subsumes.py`** (new)
   - Hypothesis property test: for any two `WhySupport` values `A`, `B`, the chosen API name reads consistently with set-inclusion semantics.
   - Pair with a unit test on `normalize_why_supports` that asserts the **minimal** witness basis under Buneman 2001 §4 Def 7.
   - **Must fail today**: at least one of `subsumes` and `normalize_why_supports` disagrees with its name.

7. **`tests/test_polynomial_provenance_preserved_through_combine.py`** (new)
   - Build a polynomial `P` with at least one term whose coefficient is `> 1`.
   - Pass through `combine_labels(label_a, label_a)`.
   - Assert resulting `Label.support.polynomial` has the correct `derivation_count` projection (Green 2007 §3 `N[X]`).
   - **Must fail today**: `_polynomial_to_environments` is square-free.

8. **`tests/test_grounded_bundle_round_trip.py`** (new)
   - Build a small `GroundedRulesBundle` with non-empty `source_rules`, `source_facts`, and `arguments`; persist via the sidecar build path; reopen via `read_grounded_bundle`.
   - Assert all four of `source_rules`, `source_facts`, `sections`, and `arguments` round-trip byte-for-byte.
   - **Must fail today**: `read_grounded_bundle` empties `source_rules`/`source_facts`.

9. **`tests/test_grounder_budget_exceeded.py`** (new — Codex 1.13 sequencing gate)
   - Construct a fixture where gunray's argument enumeration exceeds the configured `max_arguments` budget.
   - Assert `grounder.evaluate(...)` returns `ResultStatus.BUDGET_EXCEEDED` (not a hang, not a partial "complete" result, not a silent truncation).
   - This test is **independent of WS-O-gun closure**: while WS-O-gun is open, this test pins the contract that propstore exposes; it depends on `EnumerationExceeded` being raisable by gunray, which is exactly the WS-O-gun deliverable.
   - **Must fail today**: `return_arguments=False` default papers over the issue; once defaulted to True without budget wiring, the test would hang. WS-M's default flip waits until this test passes.

10. **`tests/test_grounder_default_returns_arguments.py`** (new — depends on WS-O-gun close)
    - With WS-O-gun shipped, assert `grounder.evaluate(...)` defaults `return_arguments=True` and the resulting `DefeasibleTrace` is non-empty for any non-trivial theory.
    - **Gated**: this test stays `skipif WS-O-gun open` until WS-O-gun's gating sentinel turns green; at that point the skip is removed in the same commit that flips the default.
    - **Must fail today**: default is `False`.

11. **`tests/test_micropub_identity_consumes_wscm.py`** (new)
    - Import the WS-CM micropub identity helper used by source finalization.
    - Assert emitted ids begin with `ni:///sha-256;` and contain the full digest, not a `[:24]` truncation or `ps:micropub:` pseudo-id.
    - Assert WS-M provenance export records the WS-CM id unchanged rather than recomputing a separate micropub id.
    - **Must fail today**: payload-blind AND truncated.

12. **`tests/test_repository_import_provenance_attached.py`** (new)
    - Run `commit_repository_import` end-to-end on a synthetic source repo; assert each row has an attached typed provenance record.
    - Assert a git note exists on the import commit on `refs/notes/provenance` carrying the `ImportRunProvenanceRecord` named-graph payload.
    - **Must fail today**: zero provenance handling.

13. **`tests/test_promote_writes_provenance_note.py`** (new)
    - Run the source-promote flow on a fixture branch; assert a git note exists on `refs/notes/provenance` for the promoted commit, decoding to a `Provenance` whose `operations` includes `"promote"` and whose `witnesses` records the promoting agent.
    - **Must fail today**: `promote.py:745-758` mutates a dict in place.

14. **`tests/test_workstream_m_done.py`** (new — gating sentinel)
    - `xfail` until WS-M closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-M step N — <slug>`.

### Step 1 — Trusty URI compute-and-verify + truncated-hash audit (D-20)
- New module `propstore/provenance/trusty.py` exposing `compute_ni_uri(content: bytes, *, algorithm: str = "sha-256") -> str` and `verify_ni_uri(uri: str, content: bytes) -> None`. **Per Codex re-review #17**: `algorithm` defaults to `"sha-256"` and is the only algorithm propstore emits. SHA-1 is rejected at the call boundary (passing `algorithm="sha-1"` raises `ValueError`); RFC 6920's continued allowance of SHA-1 is acknowledged in the module docstring but not surfaced as a callable option.
- Replace `_sha_text` with a call into `compute_ni_uri`. Every existing `"ni:///sha-1;<x>"` string is **recomputed against the SHA-256 of the canonicalised content** and re-emitted as `"ni:///sha-256;<sha-256-digest>"`. Old SHA-1 forms are not preserved as a fallback (per `feedback_no_fallbacks` + D-3); any persisted SHA-1-form Trusty URIs in pre-existing branches stay inert per the no-old-data rule.
- **D-20 audit pass**: walk every match from `tests/test_no_truncated_identity.py`. For each site:
  - `worldline/hashing.py:46` — production identity becomes the full hash; any caller that displays this id calls into the render layer for truncation.
  - `support_revision/projection.py:174` — same treatment.
  - `provenance/variables.py:51-59` — `derive_source_variable_id` returns the full 256-bit hash. Storage column widens to `TEXT` (already TEXT in sidecar; no migration needed since per D-3 we do not migrate old data).
  - `source/finalize.py:38-40` — handled by WS-CM; WS-M verifies it is consumed unchanged.
- Render layer: `propstore/web/html.py` and `propstore/web/render.py` gain a small `truncate_for_display(hash_str: str, n: int = 12) -> str` helper. This is the only zone where slicing a hex digest is permitted; the test allowlist points here.
- **No migration command** (per Codex 1.4 + D-3): old repos do not get migrated. Old micropub ids and old short-hash ids in pre-existing branches stay as they are and are inert; no `propstore migrate-*` command ships. If old-repo support ever becomes required, it gets its own user-approved compatibility WS — not a default plan step.

Acceptance: `tests/test_trusty_uri_verification.py` and `tests/test_no_truncated_identity.py` turn green.

### Step 2 — PROV-O export-only serializer (Codex 1.5)
- New module `propstore/provenance/prov_o.py` exposing `to_prov_o(record)` for each typed record in `records.py`, plus `provenance_to_prov_o(provenance: Provenance)` for the named-graph case.
- Output format: JSON-LD using the existing `_CONTEXT` mapping.
- **Single-path discipline**: PROV-O is the canonical serialization for **provenance EXPORT only**. Internal mutation paths use the typed records / `Provenance` exclusively. PROV-O is generated from those at export time, never stored in production, never read back. No "optional alongside" emission. `encode_named_graph` continues to write the propstore-internal payload to disk; `to_prov_o` is invoked only by the export surface (CLI export, HTTP export, etc.).
- The `_CONTEXT` block already declares the prefixes; the export module hangs PROV-O typed nodes off them at projection time.
- No `from_prov_o` / `prov_o_to_record` is built. Round-trip is not a goal. Codex 1.5 closes the dual-path risk.

Acceptance: `tests/test_prov_o_export.py` turns green; grep for `prov_o` imports inside any `propstore/storage/`, `propstore/source/`, `propstore/sidecar/` module returns zero matches (export module is the only consumer).

### Step 3 — `compose_provenance` causal order + uniform witness key
- Replace the per-record dedup-key tuple in `provenance/__init__.py:213-218` with a call to `_witness_key(witness)`.
- Drop the `_dedupe_sorted` call on `operations` inside `_canonical_provenance` (line 185); replace with `_dedupe_preserve_order`.
- Keep `derived_from` sorted (it is a set of source pointers, not a chain) and document the asymmetry.
- Add an `EncodableProvenance` newtype (or factory) requiring `graph_name` so the unencodable case cannot reach `encode_named_graph`.

Acceptance: `tests/test_compose_provenance_causal_order.py` and `tests/test_witness_key_uniformity.py` turn green.

### Step 4 — `WhySupport.subsumes` naming/behaviour fix
- Rename to `is_subsumed_by` (operation is correct; name is wrong). Update the single in-tree caller (`projections.py:107`).

Acceptance: `tests/test_why_support_subsumes.py` turns green.

### Step 5 — Polynomial preserved through `combine_labels`
- Replace the round-trip-through-environments inside `combine_labels` (`core/labels.py:278-281`) with direct polynomial-level multiplication and a polynomial-level nogood filter.
- Add a `Homomorphism[NogoodFilter]` so the filter is a typed projection rather than a representation conversion.
- Confirm `derivation_count` and `boolean_presence` projections agree pre- and post-combine.

Acceptance: `tests/test_polynomial_provenance_preserved_through_combine.py` turns green.

### Step 6 — Gunray boundary preserves DefeasibleTrace + back-pointers
- Change `propstore/grounding/grounder.py:170` to `evaluator.evaluate_with_trace(theory, policy)`. Pull `arguments`, `trees`, `markings` from the resulting `DefeasibleTrace`. Drop the separate `gunray.inspect_grounding(theory)` re-grounding pass (collaterally fixes `cluster-R-gunray.md` HIGH-3 duplicate work).
- **Default `return_arguments` flip is gated**: Codex 1.13 says propstore defaults `return_arguments=True` *only after WS-O-gun ships* the `EnumerationExceeded` / `max_arguments` wiring (D-18). While WS-O-gun is open:
  - The `BUDGET_EXCEEDED` contract test (`test_grounder_budget_exceeded.py`) is the propstore-side gate; it asserts that *if* gunray raises `EnumerationExceeded`, propstore returns `ResultStatus.BUDGET_EXCEEDED` rather than hanging or producing a misleading "complete" result.
  - The default flip test (`test_grounder_default_returns_arguments.py`) stays `skipif WS-O-gun open`.
  - The default in `grounder.py:141-149` stays `False`.
- Once WS-O-gun closes: in the same commit, flip the default to `True`, remove the `skipif`, and ensure callers pass `max_arguments` (or accept the default budget) so `EnumerationExceeded` is reachable.
- Persist `source_rules` and `source_facts` to the sidecar via a new `grounded_bundle_inputs` table (or extend `grounded_fact_empty_predicate` with a foreign-key-able input table). Update `read_grounded_bundle` to populate from the sidecar.
- Fix the `bundle.py` vs `rules.py:303-307` docstring inconsistency by picking full retention and updating both.

Acceptance: `tests/test_grounded_bundle_round_trip.py` turns green; `tests/test_grounder_budget_exceeded.py` turns green; `tests/test_grounder_default_returns_arguments.py` remains skipped until WS-O-gun closes, then flips green in the same commit as the default flip.

### Step 7 — Repository import attaches provenance
- Extend `RepositoryImportPlan` with a required `import_run: ImportRunProvenanceRecord` field.
- In `commit_repository_import`, after the transaction commits, write a named-graph note via `write_provenance_note` keyed on the import commit SHA carrying the `ImportRunProvenanceRecord` and any per-licence `LicenseProvenanceRecord`s.
- Per "imports are opinions": emit one `ExternalStatementProvenanceRecord` per imported claim row pointing at the source statement's locator inside the upstream repo.

Acceptance: `tests/test_repository_import_provenance_attached.py` turns green.

### Step 8 — `promote` writes a provenance note
- Replace the in-place `provenance` dict mutation at `propstore/source/promote.py:745-758` with a call to `compose_provenance` over each input claim's existing `ProvenanceWitness` chain plus a new witness whose `method` is `"promote"` and `asserter` is the promoting agent.
- After the promote transaction commits, attach a named graph via `write_provenance_note` to the promote commit SHA.

Acceptance: `tests/test_promote_writes_provenance_note.py` turns green.

### Step 9 — Consume WS-CM micropub identity unchanged
- Delete any WS-M-owned rewrite of `_stable_micropub_artifact_id`; that surface belongs to WS-CM.
- Assert provenance export, source provenance records, and Trusty URI verification use the WS-CM `ni:///sha-256;...` micropub id unchanged.
- Existing short ids are not normalized in place. New finalizations use WS-CM full Trusty URI ids. Render code truncates for display only.
- **No migration command** (Codex 1.4): this is a breaking change for any repo that already has micropubs under the old id. Per D-3 we do not maintain compat. Old repos either re-finalize from source (which is the intended discipline) or stay on the old id space; propstore at HEAD does not import their stale ids.

Acceptance: `tests/test_micropub_identity_consumes_wscm.py` turns green.

### Step 10 — Close gaps and gate
- Update `docs/gaps.md`: remove every row matching the findings table; add a `# WS-M closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_m_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

Acceptance: `tests/test_workstream_m_done.py` passes.

## Acceptance gates

Before declaring WS-M done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors (`2026-04-30` post-fix rerun).
- [x] `uv run lint-imports` — passes (`2026-04-30` post-fix rerun).
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-M ...` — all targeted WS-M gates green in `logs/test-runs/WS-M-final-targeted-20260430-021537.log`; post-full regression set green in `logs/test-runs/WS-M-full-failure-set-rerun-20260430-023309.log`.
- [x] WS-M property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-M test run or a named companion run.
- [x] Full suite no new failures: `logs/test-runs/WS-M-full-rerun-20260430-023410.log` reports 3473 passed, 2 skipped.
- [x] `propstore/provenance/__init__.py` no longer contains the bare `_sha_text` template; every `ni:///` URI is verifiable.
- [x] `rg -n -F "prov:Activity" propstore` returns matches only inside `propstore/provenance/prov_o.py`.
- [x] `rg -n "write_provenance_note|read_provenance_note" propstore/source` returns the source promotion call path.
- [x] `rg -n -F "provenance" propstore/storage/repository_import.py` returns the repository import provenance path.
- [x] `propstore/sidecar/rules.py:read_grounded_bundle` no longer returns empty `source_rules`/`source_facts`.
- [x] AST audit (`tests/test_no_truncated_identity.py`): zero `[:N]` slices on hex digests in production identity paths; render-only allowlist documented.
- [x] No `propstore migrate-*` command exists (Codex 1.4).
- [x] PROV-O is reachable only from the export module — internal storage/source/sidecar code does not import `prov_o`.
- [x] `docs/gaps.md` has no open rows for the findings listed above.
- [x] STATUS line is `CLOSED 623f892d`.

## Done means done

WS-M is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- T4.1 through T4.8, plus Cluster M HIGH-1, HIGH-2, MED-3, MED-6 — each has a green test in CI.
- The Trusty URI module computes and verifies; D-20 audit shows zero truncated identities outside the render layer; PROV-O export emits at least Activity/Entity/Agent for the five typed records and is invoked only from the export surface; `compose_provenance` preserves causal order; `WhySupport.subsumes` reads consistently; `combine_labels` no longer round-trips through ATMS; `read_grounded_bundle` round-trips `source_rules` and `source_facts`; `repository_import.py` attaches typed provenance; `promote.py` writes a git note.
- The `BUDGET_EXCEEDED` contract test is green; the default-`return_arguments=True` test is green (which requires WS-O-gun closed).
- `gaps.md` is updated.
- The gating sentinel (`test_workstream_m_done.py`) flipped from `xfail` to `pass`.

If any one of those is not true, WS-M stays OPEN. No "we'll get to PROV-O later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Papers / specs referenced

- **Buneman, Khanna, Tan 2001** — *Why and Where: A Characterization of Data Provenance.* Pin: §4 Def 7. `papers/Buneman_2001_CharacterizationDataProvenance/notes.md`.
- **Carroll, Bizer, Hayes, Stickler 2005** — *Named Graphs, Provenance, and Trust.* Pin: §5 SWP. `papers/Carroll_2005_NamedGraphsProvenanceTrust/notes.md`.
- **Green, Karvounarakis, Tannen 2007** — *Provenance Semirings.* Pin: §3 (`N[X]` universal). `papers/Green_2007_ProvenanceSemirings/notes.md`.
- **Moreau, Missier (eds.) 2013** — *PROV-O: The PROV Ontology.* Pin: §3 core; Tables 2-3 Qualification Pattern. `papers/Moreau_2013_PROV-O/notes.md`. W3C PROV-O / PROV-DM / PROV-N specs pending retrieval.
- **Kuhn, Dumontier 2014** — *Trusty URIs.* Pin: §3 modules; §3.2 immutability. `papers/Kuhn_2014_TrustyURIs/notes.md`. RFC 6920 pending retrieval.
- **Kuhn 2015** — *Digital Artifacts for Verifiable Citations.* `papers/Kuhn_2015_DigitalArtifactsVerifiable/notes.md`.
- **Kuhn et al. 2017** — *Reliable, Granular References.* `papers/Kuhn_2017_ReliableGranularReferences/notes.md`.
- **Groth et al. 2010** — *Anatomy of a Nanopublication.* Successor WS. `papers/Groth_2010_AnatomyNanopublication/notes.md`.
- **Clark, Ciccarese, Goble 2014** — *Micropublications.* Successor WS. `papers/Clark_2014_Micropublications/notes.md`.
- **Greenberg 2009** — *How Citation Distortions Create Unfounded Authority.* Pin: justifies "imports are opinions". `papers/Greenberg_2009_CitationDistortions/notes.md`.
- **Juty et al. 2020** — *Unique, Persistent, Resolvable.* Pin: every artifact id is a Trusty URI. `papers/Juty_2020_UniquePersistentResolvableIdentifiers/notes.md`.
- **Wilkinson et al. 2016** — *FAIR Guiding Principles.* Pin: I1, R1. `papers/Wilkinson_2016_FAIRGuidingPrinciplesScientific/notes.md`.

External specs (pending retrieval):

- **RFC 6920** — *Naming Things with Hashes.* Required for `compute_ni_uri` canonical form.
- **W3C PROV-O / PROV-DM / PROV-N** — Required for full structural validation in `tests/test_prov_o_export.py`.

Both listed in `reviews/2026-04-26-claude/REMEDIATION-PLAN.md:298, 357`.

## Cross-stream notes

- WS-M depends on **WS-E** (assertion-id includes provenance; sameAs is graded).
- WS-M depends on **WS-O-gun** (Codex 1.13 + D-18) for the default `return_arguments=True` flip and the `EnumerationExceeded` budget contract. Until WS-O-gun closes, propstore tests pin `BUDGET_EXCEEDED` rather than the default-on path.
- WS-M overlaps with **WS-CM** on micropub identity only as a consumer. WS-CM owns canonical payload + id. WS-M verifies and exports the id; it does not recompute a separate micropub identity.
- WS-M overlaps with **WS-A** on identity boundaries: once WS-A reserves `ps:` and rejects source-local minting, WS-M's content-derived ids land into a clean canonical namespace.
- WS-M does NOT change `propstore/sidecar/schema.py:claim_core.provenance_json` from a JSON column to a typed table — successor WS.
- WS-M does NOT add the missing semirings (`Trio(X)`, `Lin(X)`, typed `Why(X)`, probability, security-classification, ω-continuous Datalog) — successor WSes.
- WS-M does NOT touch nanopublication three-graph emission (Groth 2010) or SWP performative warrants (Carroll 2005 §5) — successor WS.

## What this WS does NOT do

- Does NOT add nanopublication three-graph emission. Successor WS.
- Does NOT add SWP signing. Successor WS.
- Does NOT add the missing semiring projections. Successor WS.
- Does NOT add ω-continuous recursive-Datalog provenance. Successor WS.
- Does NOT replace `claim_core.provenance_json` with a typed table. Successor WS.
- Does NOT close the source-paper claim provenance asymmetry. Q decision needed.
- Does NOT change `_compute_blocked_claim_artifact_ids` provenance-scope conflation (`promote.py:323-419`, MED-8). Successor WS.
- Does NOT ship a migration command (Codex 1.4). If old-repo compatibility is ever required, it gets its own explicitly user-approved WS.
- Does NOT add a PROV-O reverse-projection / round-trip (Codex 1.5). PROV-O is a one-way export.
