# Docstring Audit: propstore/world/ and worldline modules

Audited 2026-03-24. Every finding cites a specific file and line number.

---

## 1. world/__init__.py

**File:** `propstore/world/__init__.py`, line 1

Docstring: `"Public render/store interfaces for propstore."`

**Severity: HALF-TRUTH** -- The module re-exports both render-layer types (RenderPolicy, ResolutionStrategy, ResolvedResult) and store-layer types (ArtifactStore, WorldModel). It also re-exports the `resolve` function, `BoundWorld`, `HypotheticalWorld`, `Environment`, `SyntheticClaim`, etc. Calling these "render/store interfaces" is underselling it -- this is the entire world query surface, including the belief-space protocol, resolution logic, and hypothetical reasoning. "render/store" implies two layers; the actual exports span at least four of the six architectural layers.

---

## 2. world/bound.py

### 2a. Module docstring

**File:** `propstore/world/bound.py`, line 1
**Docstring:** `"BoundWorld -- condition-bound view over a WorldModel."`
**Actual:** BoundWorld is also context-scoped (via `context_id` and `context_hierarchy`). The docstring says "condition-bound" but omits that context membership filtering is a first-class feature of this class, not just condition bindings.
**Severity: OMISSION**

### 2b. BoundWorld class docstring

**File:** `propstore/world/bound.py`, line 105
**Docstring:** `"The world under specific condition bindings, optionally scoped to a context."`
**Actual:** Accurate. No issue.

### 2c. `_bindings_to_cel` docstring

**File:** `propstore/world/bound.py`, line 148
**Docstring:** `"Convert keyword bindings to CEL condition strings."`
**Actual:** The method also handles booleans specially (converting Python `True`/`False` to CEL `true`/`false`), and handles non-string, non-bool values by converting them with `f"{key} == {value}"`. "Keyword bindings" is vague but not wrong. Accurate enough.

### 2d. `is_active` docstring

**File:** `propstore/world/bound.py`, line 160
**Docstring:** `"Check if a claim is active under the current bindings and context."`
**Actual:** The method also incorporates `effective_assumptions` from the environment (line 124-126 in `__init__`), which are added to `_binding_conds`. The docstring says "bindings and context" but does not mention assumptions. Assumptions can materially change which claims are active.
**Severity: OMISSION**

### 2e. `is_active` logic: "no bindings -> everything active"

**File:** `propstore/world/bound.py`, line 177
**Code:** `if not self._binding_conds: return True  # no bindings -> everything active`
**Actual:** This comment is misleading. If there are no binding conditions AND no effective assumptions, then a claim with conditions is still considered active. This means a conditional claim (e.g., "only valid at temperature == 300K") is treated as active even when no temperature binding exists. The inline comment documents this as intentional, but it is semantically surprising -- "everything active" hides the fact that conditional claims are being included without their conditions being satisfied.
**Severity: HALF-TRUTH** (the comment, not a docstring per se, but documents intent)

### 2f. `collect_known_values` docstring

**File:** `propstore/world/bound.py`, line 208
**Docstring:** `"Resolve numeric values for a list of concept IDs."`
**Actual:** The method only returns float values. If a concept's value is a non-numeric string, it is silently dropped (the `float(val)` in the try/except). "Resolve numeric values" is accurate but hides the silent discard of non-numeric values.
**Severity: OMISSION**

### 2g. `conflicts` docstring

**File:** `propstore/world/bound.py`, line 281
**Docstring:** `"Return active conflicts, revalidated against the current belief space."`
**Actual:** The method does two things: (1) filters stored conflicts from `self._store.conflicts()` to only those where both claims are active, and (2) calls `_recomputed_conflicts` which runs a fresh `detect_conflicts` over the active claims. "Revalidated" undersells step 2 -- it is not just revalidating existing conflicts, it is also discovering new conflicts that the stored conflict table may not contain.
**Severity: HALF-TRUTH**

### 2h. `explain` docstring

**File:** `propstore/world/bound.py`, line 304
**Docstring:** `"Stance walk filtered to active claims."`
**Actual:** The method first checks if the root claim itself is active (returning [] if not), then walks the stance graph from the store and filters to only stances whose *target* claims are active. It does NOT filter on whether the *source* claim of each stance is active -- it filters only on `target_claim_id`. "Filtered to active claims" implies both sides are filtered.
**Severity: HALF-TRUTH**

---

## 3. world/hypothetical.py

### 3a. Module docstring

**File:** `propstore/world/hypothetical.py`, line 1
**Docstring:** `"HypotheticalWorld -- in-memory overlay on a BoundWorld."`
**Actual:** Accurate.

### 3b. Class docstring

**File:** `propstore/world/hypothetical.py`, line 16
**Docstring:** `"In-memory overlay on a BoundWorld -- removes/adds claims without mutation."`
**Actual:** Accurate. The class does filter out removed claim IDs and inject synthetic claims without mutating the underlying BoundWorld.

### 3c. `_synthetic_to_dict` docstring

**File:** `propstore/world/hypothetical.py`, line 37
**Docstring:** `"Convert a SyntheticClaim to the dict format used by claims."`
**Actual:** The conversion only populates `id`, `concept_id`, `type`, `value`, and `conditions_cel`. Real claim dicts can have many more fields (provenance_json, sample_size, source_file, body, variables_json, context_id, etc.). Synthetic claims produced by this method will fail lookups on any of those fields. This is not documented.
**Severity: OMISSION**

### 3d. `derived_value` docstring

**File:** `propstore/world/hypothetical.py`, line 78
**Docstring:** `"Derive using this hypothetical world's active claims."`
**Actual:** The resolver was constructed with `self._base.collect_known_values` and `self._base.extract_variable_concepts` (line 31-32), which means `collect_known_values` calls `self._base.value_of` (BoundWorld), not `self.value_of` (HypotheticalWorld). So derivation of intermediate values does NOT use the hypothetical world's active claims for `collect_known_values`. The docstring claim "this hypothetical world's active claims" is **partially false** -- `value_of` on the resolver IS the hypothetical's, but `collect_known_values` reaches through to the base.
**Severity: HALF-TRUTH** -- derivation uses a mix of hypothetical and base resolution depending on the code path.

### 3e. `recompute_conflicts` docstring

**File:** `propstore/world/hypothetical.py`, line 112
**Docstring:** `"Check for direct value disagreements among active claims."`
**Actual:** The method does simple pairwise string inequality on `value` fields. It does not use the conflict detector infrastructure (no CEL condition checking, no concept registry, no type-aware comparison). "Direct value disagreements" is accurate but hides that this is a much coarser check than what `_recomputed_conflicts` does in `conflicts()`.
**Severity: OMISSION**

### 3f. `diff` docstring

**File:** `propstore/world/hypothetical.py`, line 146
**Docstring:** `"Compare base and hypothetical value_of for all affected concepts."`
**Actual:** "All affected concepts" means only concepts directly referenced by synthetics or removed claims. It does NOT transitively discover concepts affected via parameterization relationships. If removing a claim for concept A causes a derivation of concept B to change, B will not appear in the diff.
**Severity: HALF-TRUTH**

---

## 4. world/model.py

### 4a. Module docstring

**File:** `propstore/world/model.py`, line 1
**Docstring:** `"WorldModel -- read-only reasoner over a compiled sidecar."`
**Actual:** WorldModel is primarily a data access layer (SQL queries against SQLite), not a "reasoner." The reasoning happens in BoundWorld, resolution.py, and value_resolver.py. WorldModel does have `chain_query` (which does reasoning), and `bind` (which creates a BoundWorld that reasons), so "reasoner" is a stretch -- it is more of a data store that can spawn reasoners.
**Severity: HALF-TRUTH**

### 4b. Class docstring

**File:** `propstore/world/model.py`, line 39
**Docstring:** `"Read-only reasoner over a compiled sidecar."`
**Actual:** Same issue as 4a. Also, "read-only" is accurate -- nothing mutates the SQLite DB.

### 4c. `_parameterizations_for` docstring

**File:** `propstore/world/model.py`, line 367
**Docstring:** `"Get parameterization rows where output_concept_id matches."`
**Actual:** Accurate. The SQL query is `WHERE output_concept_id = ?`.

### 4d. `_group_members` docstring

**File:** `propstore/world/model.py`, line 380
**Docstring:** `"Get all concept_ids in the same parameterization group."`
**Actual:** Accurate. Queries `parameterization_group` by `group_id`.

### 4e. `explain` docstring

**File:** `propstore/world/model.py`, line 401
**Docstring:** `"Walk claim_stance edges breadth-first from claim_id."`
**Actual:** Accurate. The implementation uses a deque-based BFS.

### 4f. `chain_query` docstring

**File:** `propstore/world/model.py`, line 472
**Docstring:** `"Traverse the parameter space to derive the target concept."`
**Actual:** The method does more than just derivation. It also tries direct `value_of` (claim lookup) and `resolved_value` (conflict resolution). "Traverse the parameter space" implies pure derivation, but the method is a multi-strategy resolution pipeline that tries claims first, then resolution, then derivation, in an iterative fixpoint loop.
**Severity: HALF-TRUTH**

### 4g. `similar_claims` docstring

**File:** `propstore/world/model.py`, line 301
**Docstring:** `"Find claims similar to the given claim by embedding distance. Requires sqlite-vec extension and pre-computed embeddings."`
**Actual:** Accurate. The method loads the vec extension and delegates to `find_similar`.

### 4h. `similar_concepts` docstring

**File:** `propstore/world/model.py`, line 323
**Docstring:** `"Find concepts similar to the given concept by embedding distance. Requires sqlite-vec extension and pre-computed embeddings."`
**Actual:** Accurate. Delegates to `find_similar_concepts`.

### 4i. `resolve_concept` docstring

**File:** `propstore/world/model.py`, line 190
**Docstring:** `"Resolve a concept by alias, ID, or canonical name."`
**Actual:** Accurate. Tries alias first, then direct ID lookup, then canonical_name query.

---

## 5. world/resolution.py

### 5a. Module docstring

**File:** `propstore/world/resolution.py`, lines 1-6
**Docstring:** `"Resolution helpers for conflicted concepts. ResolutionStrategy chooses a winner among active claims after the active belief space has already been computed by the configured reasoning backend. Run 1 keeps the existing claim-graph backend as the default."`
**Actual:** The phrase "after the active belief space has already been computed by the configured reasoning backend" implies the reasoning backend pre-filters claims before resolution. In practice, the active belief space is computed by `BoundWorld.is_active()` using CEL condition checking (Z3 solver), not by the "reasoning backend." The `ReasoningBackend.CLAIM_GRAPH` enum is only used inside the `ARGUMENTATION` strategy branch. The reasoning backend does not compute the active belief space -- it is used only for argumentation-based resolution.
**Severity: LIE** -- The module docstring describes an architecture that does not exist. The reasoning backend does NOT compute the active belief space; it is only consulted for one specific resolution strategy.

Also: "Run 1" is internal jargon that means nothing to a reader without context of the project's phased implementation history.
**Severity: STALE** -- This was a planning note that should have been cleaned up.

### 5b. `_resolve_recency` docstring

**File:** `propstore/world/resolution.py`, line 23
**Docstring:** `"Pick the claim with the most recent date in provenance_json."`
**Actual:** The method does lexicographic string comparison on the `date` field (`date > best_date`). This works for ISO 8601 dates but the docstring does not mention that it relies on string ordering. If dates are in non-ISO format, this silently picks the wrong claim.
**Severity: OMISSION**

### 5c. `_resolve_sample_size` docstring

**File:** `propstore/world/resolution.py`, line 44
**Docstring:** `"Pick the claim with the largest sample_size."`
**Actual:** Accurate.

### 5d. `_resolve_claim_graph_argumentation` docstring

**File:** `propstore/world/resolution.py`, lines 66-70
**Docstring:** `"Resolve in the current claim-graph backend. The AF is built over the whole active belief space, then projected back to the target concept's active claims."`
**Actual:** The function receives `target_claims` and `active_claims` as separate parameters and passes `active_ids` to `compute_claim_graph_justified_claims`. The AF is indeed built over all active claims (not just the target's). Then `survivors = result & target_ids` projects back. The docstring is accurate.

### 5e. `resolve` function docstring

**File:** `propstore/world/resolution.py`, line 116
**Docstring:** `"Apply a resolution strategy to a conflicted concept."`
**Actual:** The function also handles non-conflicted cases: it returns early for `no_claims`, `determined`, and any other status. It is not limited to conflicted concepts. "Apply a resolution strategy to a conflicted concept" is what it does in the interesting case, but it also acts as a general-purpose status passthrough.
**Severity: HALF-TRUTH**

---

## 6. world/types.py

### 6a. Module docstring

**File:** `propstore/world/types.py`, line 1
**Docstring:** `"Data classes, enums, and protocols for the render/store layer."`
**Actual:** Same issue as `__init__.py` -- these types span more than just render/store. `BeliefSpace` is a reasoning protocol, `Environment` is a query-binding type, `SyntheticClaim` is used for hypothetical reasoning. "render/store layer" is too narrow.
**Severity: HALF-TRUTH**

### 6b. `ReasoningBackend` docstring

**File:** `propstore/world/types.py`, lines 39-43
**Docstring:** `"Semantic backend used to interpret the active belief space. Run 1 keeps the existing claim-graph backend as the default. ResolutionStrategy remains a separate render-time winner-selection axis."`
**Actual:** The `ReasoningBackend` enum has exactly one member: `CLAIM_GRAPH`. It is not used to "interpret the active belief space" -- the active belief space is always computed by `BoundWorld.is_active()` using Z3 condition solving. `ReasoningBackend` is only checked in `resolution.py` line 195, inside the `ARGUMENTATION` strategy, to select which argumentation implementation to call. The docstring describes a future architecture where different backends would compute different belief spaces, but that architecture does not exist.
**Severity: LIE** -- Same as finding 5a. The reasoning backend does not interpret the active belief space.

Also: "Run 1" is stale planning jargon.
**Severity: STALE**

### 6c. `RenderPolicy` docstring

**File:** `propstore/world/types.py`, lines 92-97
**Docstring:** `"Render-time policy. reasoning_backend selects the semantic backend used to interpret the active belief space. strategy is only used when a conflicted concept needs a winner selected at render time."`
**Actual:** Same false claim about `reasoning_backend`. The `reasoning_backend` field is passed through to `_resolve_claim_graph_argumentation` and is only checked as a guard (`if reasoning_backend != ReasoningBackend.CLAIM_GRAPH: raise NotImplementedError`). It does not "select the semantic backend used to interpret the active belief space."
**Severity: LIE**

### 6d. `ValueResult.status` comment

**File:** `propstore/world/types.py`, line 17
**Comment:** `# "determined" | "conflicted" | "underdetermined" | "no_claims"`
**Actual:** Looking at `value_of_from_active` in `value_resolver.py`, the method returns `no_claims`, `determined`, or `conflicted`. It never returns `"underdetermined"`. The only occurrence of `"underdetermined"` status is never produced by this code path.
**Severity: STALE** -- `"underdetermined"` was likely a planned status that was never implemented, or was renamed to something else.

### 6e. `DerivedResult.status` comment

**File:** `propstore/world/types.py`, line 24
**Comment:** `# "derived" | "underspecified" | "no_relationship" | "conflicted"`
**Actual:** Looking at `value_resolver.py`, `derived_value` and `_derive_from_parameterization` do produce all four of these statuses. Accurate.

---

## 7. world/value_resolver.py

### 7a. Module docstring

**File:** `propstore/world/value_resolver.py`, line 1
**Docstring:** `"Shared value and derivation resolution for belief-space views."`
**Actual:** Accurate. The `ActiveClaimResolver` is instantiated by both `BoundWorld` and `HypotheticalWorld`.

### 7b. Class docstring

**File:** `propstore/world/value_resolver.py`, line 15
**Docstring:** `"Resolve values and derived values for a belief-space view."`
**Actual:** Accurate.

### 7c. No docstring on `value_of_from_active`

**File:** `propstore/world/value_resolver.py`, line 81
**Observation:** This is the most complex method in the file (53 lines, handles algorithm claims vs value claims, normalization, equivalence checking). It has no docstring at all.
**Severity: OMISSION**

### 7d. No docstring on `_derive_from_parameterization`

**File:** `propstore/world/value_resolver.py`, line 136
**Observation:** Complex method (67 lines) with recursive derivation, cycle detection via `derivation_stack`, and multi-path resolution. No docstring.
**Severity: OMISSION**

### 7e. No docstring on `_normalize_value`

**File:** `propstore/world/value_resolver.py`, line 220
**Observation:** Converts int/float to float, passes strings through, excludes bools (despite bool being a subclass of int in Python). The bool exclusion is a subtle behavior with no documentation.
**Severity: OMISSION**

### 7f. No docstring on `_algorithm_matches_direct_value`

**File:** `propstore/world/value_resolver.py`, line 225
**Observation:** The method returns a three-valued result (True, False, None) where None means "cannot determine." No docstring explains the semantics of the None return.
**Severity: OMISSION**

---

## 8. worldline.py

### 8a. Module docstring

**File:** `propstore/worldline.py`, lines 1-10
**Docstring:** Claims grounding in "de Kleer 1986 (ATMS labels), Martins 1983 (belief spaces), Green 2007 (provenance semirings), Groth 2010 (nanopublications)."
**Actual:** The WorldlineDefinition is a YAML-serializable dataclass. There is no ATMS label tracking, no belief space formalism, no provenance semiring algebra, and no nanopublication structure in this file. The `compute_worldline_content_hash` function computes a SHA-256 hash -- not a semiring annotation. The citation to Groth 2010 (nanopublications) is especially unfounded: there is no RDF, no named graph, no nanopublication structure.
**Severity: LIE** -- The literature citations describe aspirational grounding, not what the code does. The code is a straightforward YAML data structure with a content hash.

### 8b. `WorldlineInputs` docstring

**File:** `propstore/worldline.py`, line 25
**Docstring:** `"The input specification for a worldline query."`
**Actual:** Accurate.

### 8c. `WorldlinePolicy` docstring

**File:** `propstore/worldline.py`, lines 54-58
**Docstring:** `"Render policy for a worldline. reasoning_backend identifies the semantic backend. strategy is still the render-time conflict winner selection policy."`
**Actual:** The word "still" implies this is a deliberate retention from a previous design. The `reasoning_backend` claim inherits the same LIE from types.py -- it does not select a semantic backend that interprets the belief space; it is only a guard in the argumentation resolution path.
**Severity: HALF-TRUTH**

### 8d. `WorldlineResult` docstring

**File:** `propstore/worldline.py`, line 104
**Docstring:** `"The materialized results of a worldline query."`
**Actual:** Accurate.

### 8e. `WorldlineDefinition` docstring

**File:** `propstore/worldline.py`, lines 147-151
**Docstring:** `"A worldline: question + optional answer. The question (id, name, inputs, policy, targets) is human-authored. The answer (results) is machine-generated by run_worldline()."`
**Actual:** Accurate.

### 8f. `is_stale` docstring

**File:** `propstore/worldline.py`, lines 219-223
**Docstring:** `"Check if this worldline's results are stale. A worldline is stale if re-materializing it under the current world produces a different fingerprint than the stored results."`
**Actual:** Accurate -- the method calls `run_worldline` and compares content hashes. However, the docstring omits that `is_stale` returns `False` (not stale) when `results is None`, which is semantically surprising. An unrun worldline is not "stale" but also not "fresh" -- it is "unrun." The method conflates "unrun" with "not stale."
**Severity: OMISSION**

### 8g. `compute_worldline_content_hash` docstring

**File:** `propstore/worldline.py`, line 246
**Docstring:** `"Compute a deterministic fingerprint for materialized worldline content."`
**Actual:** Accurate. Uses SHA-256 over JSON-serialized payload.

---

## 9. worldline_runner.py

### 9a. Module docstring

**File:** `propstore/worldline_runner.py`, lines 1-21
**Docstring (key claims):**

1. `"Injecting overrides as synthetic claims"` (line 4)
   **Actual:** Overrides are NOT injected as synthetic claims. Lines 85-89 have a comment explicitly stating: "Overrides are handled via override_values in derived_value(), not via SyntheticClaims." The docstring directly contradicts the code.
   **Severity: LIE**

2. `"4. Computing a content hash over dependencies for staleness detection"` (line 8)
   **Actual:** The content hash is computed over `values`, `steps`, `dependencies`, `sensitivity`, and `argumentation` (line 215-221, via `compute_worldline_content_hash`). It is NOT computed "over dependencies" alone -- it includes the full result payload. The content hash is a hash of the materialized results, not just the dependencies.
   **Severity: LIE**

3. `"The dependency tracking follows de Kleer 1986 (ATMS): every derived datum carries its minimal assumption set."` (lines 9-11)
   **Actual:** There is no minimal assumption set tracking. Dependencies are accumulated into a flat `dependency_claims: set[str]` (line 103) and there is no attempt to track which claims are the minimal set for each derived datum. All contributing claim IDs are thrown into one set. This is a flat dependency list, not ATMS-style assumption labeling.
   **Severity: LIE**

4. `"Soundness (P2) requires every dependency to be necessary; completeness (P3) requires no missing dependencies."` (lines 11-12)
   **Actual:** Neither property is enforced or even approximated. Dependencies are added opportunistically (e.g., all claims from a resolved concept, not just the winning claim -- see line 372-375 where ALL `rr.claims` are added). The code tracks *all claims consulted*, not *minimal necessary claims*.
   **Severity: LIE**

5. `"Override precedence follows Martins 1983 (belief spaces)"` (lines 14-16)
   **Actual:** Since overrides are float dicts passed to `derived_value`, not synthetic claims in a belief space, there is no Martins 1983 mechanism here. The override is a simple dict lookup that bypasses the belief space entirely.
   **Severity: LIE**

6. `"Content hashing for staleness follows Green 2007 (provenance semirings)"` (lines 18-19)
   **Actual:** The hash is a SHA-256 of JSON. Provenance semirings involve algebraic annotations (K-relations) that track how tuples are derived. There is no semiring structure here.
   **Severity: LIE**

### 9b. `run_worldline` docstring

**File:** `propstore/worldline_runner.py`, lines 42-55
**Docstring:** `"Materialize a worldline: compute results for all targets."`
**Actual:** Accurate at a high level. The Parameters/Returns sections are also accurate.

### 9c. `_pre_resolve_conflicts` docstring

**File:** `propstore/worldline_runner.py`, lines 243-254
**Docstring:** `"Walks the parameterization graph from each target (via shared parameterization_walk.reachable_concepts), collecting all input concepts."`
**Actual:** Accurate. The method does call `reachable_concepts` and resolves conflicted inputs.

### 9d. `_compute_hash` docstring (DEAD CODE)

**File:** `propstore/worldline_runner.py`, lines 669-675
**Docstring:** `"Compute a content hash over the current state of dependency claims. This is a coarse projection of the full provenance polynomial (Green 2007)..."`
**Actual:** This function is never called anywhere in the codebase. The actual hashing is done by `compute_worldline_content_hash` in `worldline.py`. This is dead code with a docstring describing behavior that nothing invokes.
**Severity: STALE** -- This was replaced by `compute_worldline_content_hash` but never cleaned up.

### 9e. `_claim_payload` docstring

**File:** `propstore/worldline_runner.py`, line 553
**Docstring:** `"Preserve non-scalar claim payloads in worldline results."`
**Actual:** The method also preserves scalar fields: `value` (any type), `claim_type` (string), `statement` (string), `expression` (string), `body` (string), `name` (string), `canonical_ast` (string). These are all scalar values. The name "non-scalar" is misleading -- only `variables` (parsed from JSON) could be non-scalar.
**Severity: HALF-TRUTH**

### 9f. `_trace_input_source` docstring

**File:** `propstore/worldline_runner.py`, line 587
**Docstring:** `"Trace where an input value came from, recursing through derived inputs."`
**Actual:** Accurate. The method recursively traces through claims, resolution, and derivation.

### 9g. `_context_dependencies` docstring

**File:** `propstore/worldline_runner.py`, line 699
**Docstring:** `"Collect context-scoped inputs that affect a worldline materialization."`
**Actual:** The method collects the context_id and its effective_assumptions. It does not collect "inputs" -- it collects context identity and assumptions. "Inputs" is misleading.
**Severity: HALF-TRUTH**

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| LIE | 9 |
| HALF-TRUTH | 11 |
| STALE | 3 |
| OMISSION | 9 |
| **Total** | **32** |

### Systemic Patterns

1. **The "reasoning backend" lie** (5a, 6b, 6c, 8c): Four docstrings across three files claim `ReasoningBackend` "interprets the active belief space." It does not. The active belief space is always computed by Z3 condition solving in BoundWorld. The reasoning backend is only consulted inside one resolution strategy. This is a consistent, repeated false claim.

2. **Aspirational literature citations** (8a, 9a): The worldline module docstrings cite ATMS, provenance semirings, belief spaces, and nanopublications. None of these formalisms are implemented. The code is a YAML structure with a SHA-256 hash and a flat dependency set.

3. **Missing docstrings on complex methods** (7c-7f): The most algorithmically complex code in value_resolver.py has no docstrings at all, while simpler pass-through methods in other files are documented.

4. **"Omission" pattern in BoundWorld/HypotheticalWorld**: Docstrings describe the happy path but hide surprising behaviors (assumptions affecting activation, silent discard of non-numeric values, partial base-world leakage in hypothetical derivation).
