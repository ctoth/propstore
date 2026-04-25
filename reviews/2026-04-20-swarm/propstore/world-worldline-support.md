# world / worldline / support_revision — Review

Date: 2026-04-20
Reviewer: analyst subagent (gauntlet, review-only)
Scope: `propstore/world/`, `propstore/worldline/`, `propstore/support_revision/`

## Coverage

Fully read:
- `support_revision/__init__.py`, `operators.py`, `iterated.py`, `entrenchment.py`, `state.py`, `af_adapter.py`, `workflows.py`
- `world/__init__.py`, `assignment_selection_merge.py`
- `world/atms.py` through line 2320/2537 (core engine, propagation, nogoods, futures, relevance/intervention, serialization)
- `worldline/runner.py`, `revision_capture.py`, `argumentation.py`, `resolution.py:1-200`, `definition.py`, `hashing.py`, `trace.py`, `result_types.py:1-100`
- `core/labels.py` excerpt for `EnvironmentKey`, `NogoodSet`, `Label`, `combine_labels`, `merge_labels`

Partially read / not read (best-effort scope):
- `world/atms.py:2320-2537` (tail — serialization helpers)
- `world/bound.py` (1175 lines — did not read; BoundWorld adapter)
- `world/model.py`, `types.py`, `resolution.py`, `hypothetical.py`, `queries.py`, `value_resolver.py`, `consistency.py`
- `worldline/resolution.py:200+`, `interfaces.py`, `revision_types.py`
- `support_revision/projection.py`, `explain.py`, `explanation_types.py`, `snapshot_types.py`

Findings limited to files actually inspected. No cheap tests were run; this is a read-only pass.

## Layer Bleeding

**SR-L1 — `support_revision` exposes a full AGM surface despite the package-level disclaimer.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/__init__.py:1-42`, `operators.py:93-160`, `iterated.py:59-158`, `state.py:136-188`
- The package docstring states: "This package is not AGM belief revision. Formal AGM, iterated revision, IC merge, and AF revision live in `propstore.belief_set`." The public API nevertheless exports `expand`, `contract`, `revise`, `iterated_revise` with `lexicographic` and `restrained` operator modes (`iterated.py:133-142`), `EpistemicState` (`state.py:162-187`) with a `history: tuple[RevisionEpisode, ...]` field, and `RevisionEpisode`. The `lexicographic`/`restrained` operator family is Nayak-Booth-Meyer 2003 iterated revision — revision *semantics*, not support-incision *mechanics*. CLAUDE.md is explicit: "`propstore.support_revision` is only a support-incision adapter for scoped worldline capture; it is not AGM or AF revision."
- Severity: HIGH (principle violation; either the docstring lies or `belief_set` duplicates this logic)
- Suggested fix: decide. Option A — rename to incision-only names (`incise_support_for_claim`, `expand_with_atom`, `recompute_supports`), delete the DP operator family, drop `RevisionEpisode.history`, keep only the incision semantics needed by worldline. Option B — move `iterated.py`, `operators.py`, `entrenchment.py`, `EpistemicState` to `propstore.belief_set` and reduce this package to a minimal adapter surface used by worldline.

**SR-L2 — `iterated.py` enforces a merge-point precondition that is AGM theory.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/iterated.py:67-68`
- `if len(state.scope.merge_parent_commits) > 1: raise ValueError("iterated revision is undefined at a merge point; use an explicit merge path")` is an iterated-revision correctness condition (DP/Booth). By CLAUDE.md it lives in `belief_set`.
- Severity: HIGH
- Suggested fix: move to `belief_set` alongside SR-L1.

**WL-L1 — `worldline.revision_capture` consumes the AGM-shaped public surface, cascading SR-L1.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py:13-55`
- `capture_revision_state` branches on `operation in {"expand", "contract", "revise", "iterated_revise"}` and delegates to `bound.expand/contract/revise/iterated_revise/revision_explain`. If SR-L1 is resolved, this call site moves.
- Severity: MEDIUM (cascade of SR-L1)
- Suggested fix: follow SR-L1 resolution mechanically.

**WL-L2 — `worldline/argumentation.py:_capture_aspic` directly imports argumentation machinery (`structured_projection`, `GroundedRulesBundle`) from layer 4 and wires it during worldline runtime.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/argumentation.py:137-190`
- The layered architecture places `worldline` above argumentation, so this import direction is permitted. The concern is subtler: `_capture_aspic` silently short-circuits to `None` if `getattr(world, "grounding_bundle", None)` is not callable (line 159-160). If a store doesn't implement the protocol, the worldline still reports "no argumentation state" with no diagnostic reason. That is honest-ignorance-adjacent, but the serialized worldline result hashes over the *absence* of state identically to a genuine "no argumentation applicable," which hides whether the backend is unsupported or genuinely empty.
- Severity: LOW (principle-adjacent: silent ignorance vs structured ignorance)
- Suggested fix: emit a typed `WorldlineArgumentationState(backend="aspic", status="unsupported_store")` rather than `None`.

## ATMS Correctness

**ATMS-C1 — `_build` outer loop has no iteration cap; may oscillate if `NogoodSet` equality is ordering-sensitive.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1274-1280`
- Code:
  ```python
  while True:
      self._propagate_labels()
      added_justifications = self._materialize_parameterization_justifications()
      updated_nogoods = self._update_nogoods()
      if not added_justifications and not updated_nogoods:
          self._propagate_labels()
          break
  ```
- No max-iteration guard. Termination hinges on `_update_nogoods()` returning `False` via `updated == self.nogoods` (line 1488) — a dataclass equality that compares `provenance_nogoods: tuple[ProvenanceNogood, ...]` (`core/labels.py:71`) by tuple order.
- Severity: MEDIUM
- Suggested fix: add explicit max-iteration guard that raises if exceeded; log each iteration count.

**ATMS-C2 — `_update_nogoods` equality is sensitive to `ProvenanceNogood` tuple ordering.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1459-1495`
- `environments: list[EnvironmentKey] = list(self.nogoods.environments)` then iterates conflicts, appending newly-computed `env_a.union(env_b)` — the `environments` list can end up in a different order than a stable canonical ordering even if the set is unchanged (because `self.nogoods.environments` is already normalized, but appended environments are not reordered before `NogoodSet(tuple(environments))`). The constructor's `normalize_environments` inside `NogoodSet.environments` property will dedupe, but the `provenance_nogoods` tuple stored by the constructor is built via `tuple(_environment_to_provenance_nogood(e) for e in normalize_environments(environments))` — ordering derives from `normalize_environments` which sorts by `(len, assumption_ids, context_ids)`. So ordering *should* be stable across calls with the same set. This makes the equality reliable as long as normalization is deterministic. Still worth pinning with a direct set-based comparison.
- Severity: MEDIUM (brittle; silent infinite loop risk if normalization ever drifts)
- Suggested fix: replace `if updated == self.nogoods` with `if set(updated.environments) == set(self.nogoods.environments)`.

**ATMS-C3 — `_update_nogoods` accumulates duplicate provenance entries across outer iterations.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1459-1495`
- Each outer iteration reads `self._nogood_provenance` (line 1462-1463) as seed, then appends new details (line 1478-1485) as conflicts are re-scanned. The same (claim_a, claim_b, env_a, env_b) tuple is appended again on every iteration where the conflict still fires. Final `self._nogood_provenance` (lines 1491-1494) keeps the full accumulated tuple per environment. `explain_nogood` (line 1098-1105) returns the raw tuple; consumers see duplicated provenance rows.
- Severity: LOW
- Suggested fix: dedupe the `list[ATMSNogoodProvenanceDetail]` per environment before storing (the detail is a TypedDict; dedupe by serialized JSON).

**ATMS-C4 — `essential_support` silently drops `context_ids` when returning the shared environment.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1055-1082`
- Returns `EnvironmentKey(tuple(sorted(shared)))` — `shared` is built from `env.assumption_ids` only (line 1079-1081). `context_ids` never enter the intersection or the returned key. Claims that depend on a context (via `Label.context(context_id)` seeding) lose context provenance in the essential-support report.
- Severity: MEDIUM (silent provenance drop; CLAUDE.md: "honest ignorance over fabricated confidence")
- Suggested fix:
  ```python
  shared_assumptions = set(compatible[0].assumption_ids)
  shared_contexts = set(compatible[0].context_ids)
  for env in compatible[1:]:
      shared_assumptions.intersection_update(env.assumption_ids)
      shared_contexts.intersection_update(env.context_ids)
  return EnvironmentKey(tuple(sorted(shared_assumptions)), context_ids=tuple(sorted(shared_contexts)))
  ```

**ATMS-C5 — `_serialize_environment_key` drops `context_ids` for every downstream serialization consumer.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:2293-2297`
- `return list(environment.assumption_ids)` — used to render essential_support, nogood_detail environments, witness environments, intervention-plan environments, and the `argumentation_state` JSON payload that propagates into worldline content hashes. Every consumer sees assumption ids only; context provenance is invisible in all serialized output.
- Severity: MEDIUM (systemic provenance drop; affects reproducibility of context-dependent claims via `content_hash`)
- Suggested fix: serialize as `{"assumption_ids": [...], "context_ids": [...]}` and update all consumers; or at minimum serialize context ids inline as `ctx:<id>` entries if the typed shape must stay flat.

**ATMS-C6 — `_build_micropublication_nodes_and_justifications` silently skips micropublications with missing claim antecedents.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1327-1358`
- If any referenced claim is missing (lines 1343-1350), `claim_node_ids` is reset and the loop `break`s; the subsequent `if not claim_node_ids: continue` (line 1352) skips creating a justification. The micropub node exists (line 1333-1336) but with no justification, so its label stays empty and its status is `OUT`. No diagnostic is emitted. `explain_node` reports "no exact ATMS justification produced a label" (line 1672) rather than "micropub X referenced missing claim Y."
- Severity: MEDIUM (silent data drop, principle violation)
- Suggested fix: track missing-claim diagnostics per micropub in a dedicated store, surface via `explain_node` and `verify_labels`.

**ATMS-C7 — `_iter_future_queryable_sets` enumerates the full power set up to `limit` entries; each entry rebuilds the ATMS graph from scratch.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1780-1794`, `1796-1800`
- `for width in range(1, len(normalized)+1): for queryable_set in combinations(normalized, width)`. With K queryables and default `limit=8`, small-K cases are fine, but `limit` is a soft cap over the total; with 15 queryables and `limit=10000`, nearly all 2^15 subsets are enumerated. Each subset yields a full ATMS rebuild via `self.__class__(self._runtime.replay(queryable_set))` (line 1800). No memoization; `node_future_statuses` and `node_relevance` both invoke `_future_entries` separately and duplicate the work.
- Severity: MEDIUM (silent performance cliff and redundancy)
- Suggested fix: pre-filter queryables by potential label impact before rebuild; memoize `_future_engine` by queryable-set identity per engine instance.

**ATMS-C8 — `_was_pruned_by_nogood` classifies cycle branches as "not pruned by nogood" even when the cycle masks a pruned support path.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1674-1696`
- The `_visited` guard short-circuits the recursion at `if node_id in _visited: return False`. If the only surviving path to a pruned antecedent goes through a cycle, the function returns `False` and the caller classifies the node as `MISSING_SUPPORT` rather than `NOGOOD_PRUNED`. Classification bug, not a correctness bug — the node is still correctly OUT.
- Severity: LOW
- Suggested fix: treat cycle detection as "unknown pruning reason" distinct from `NOGOOD_PRUNED`/`MISSING_SUPPORT`; or separately record cycle-observed nodes in the verification pass.

**ATMS-C9 — `verify_labels` is not invoked on the build path and has no CI integration.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1107-1163`
- Declared as a verification API; no caller in the surveyed code. Without runtime verification, the only check that ATMS labels are consistent, minimal, sound, and complete is manual invocation.
- Severity: INFO (latent verification debt)
- Suggested fix: run `verify_labels` in test fixtures or as a `--verify` mode on the engine; document as QA surface.

## Bugs & Silent Failures

**SR-B1 — `_choose_incision_set` is exponential in support-set cardinality with no cap.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/operators.py:257-289`
- `combinations(candidates, size)` for `size in range(1, len(candidates)+1)` is an exhaustive hitting-set search. O(2^n) over assumptions reachable from target support sets. The early `if best_combo is not None: break` after each size class keeps the common case linear in the minimal-hitting-set size, but worst case with n≥25 is infeasible.
- Severity: MEDIUM (silent scaling cliff)
- Suggested fix: cap `len(candidates)`; fall back to entrenchment-weighted greedy hitting-set with explicit `TooManyCandidatesError` at the hard bound.

**SR-B2 — `stabilize_belief_base` fixpoint uses atom-id-tuple equality.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/operators.py:226`
- `if tuple(atom.atom_id for atom in rebuilt.atoms) == tuple(atom.atom_id for atom in active_base.atoms)`. The algorithm is monotone-shrinking (rejected atoms are removed from `active_base` for the next iteration, so they cannot re-enter), so the equality check is equivalent to `not round_rejected`. Defensible but fragile — a future change that allows re-admission would silently infinite-loop or terminate incorrectly.
- Severity: LOW
- Suggested fix: `if not round_rejected: return ...; assert accepted_set.isdisjoint(all_rejected)`.

**SR-B3 — `_rebuild_base` uses string-prefix heuristic to filter assumptions.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/operators.py:319-343`
- `if f"assumption:{assumption.assumption_id}" in accepted_ids or assumption.assumption_id in accepted_ids`. The second disjunct accepts a raw assumption_id matching a claim atom_id. If an author picks a string that collides, filtering misbehaves.
- Severity: LOW
- Suggested fix: canonicalize atom_id format at ingest; drop the raw-id fallback.

**ASM-B1 — `enumerate_candidate_assignments` does a full Cartesian product over observed values.**
- File: `C:/Users/Q/code/propstore/propstore/world/assignment_selection_merge.py:86-111`
- `product(*domains)` — N concepts × K distinct source values → K^N candidates. Dedup is O(n) per insert (line 109), so dedup is O(n²) total. No bound or warning.
- Severity: MEDIUM (silent exponential)
- Suggested fix: cap the cross-product size with explicit error; or move to a distance-minimizing search that does not enumerate.

**ASM-B2 — `assignment_satisfies_mu` recompiles Z3 constraints on every call.**
- File: `C:/Users/Q/code/propstore/propstore/world/assignment_selection_merge.py:279-282`
- `solve_assignment_selection_merge` compiles once (line 315) and reuses; any external caller invoking `assignment_satisfies_mu` per candidate re-instantiates Z3 per call. Signature invites misuse.
- Severity: LOW
- Suggested fix: accept pre-compiled constraints, or make it private if always paired with the solver path.

**ASM-B3 — `claim_distance` silently coerces types.**
- File: `C:/Users/Q/code/propstore/propstore/world/assignment_selection_merge.py:38-50`
- `"3"` vs `3.0` → distance 0.0 via `float()` coercion. `None` vs `3.0` → 1.0 via Hamming fallback. Mixing types through an undocumented coercion path corrupts distance semantics.
- Severity: LOW
- Suggested fix: require same-type inputs or raise `TypeError`; document coercion rules explicitly.

**WL-B1 — `run_worldline` swallows argumentation and revision capture failures via broad `except Exception`, contaminating `content_hash`.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:107-132`
- `except Exception as exc: logger.warning(...); argumentation_state = WorldlineArgumentationState(status="error", error=f"argumentation capture failed: {exc}")`. The error string contains the raw exception message, which may include object ids or timestamps. The error state flows into `compute_worldline_content_hash` (`hashing.py:17-44`), so transient failures produce hashes distinct from clean runs even though the stored state is intended to be a stable fingerprint. `is_stale` (`definition.py:360-371`) compares hashes, so a transient argumentation failure makes a cached worldline permanently "stale."
- Severity: MEDIUM (silent failure + content_hash instability; breaks rerun caching)
- Suggested fix: narrow the exception class; redact volatile parts of `exc` (object ids, timestamps) before hashing; or exclude the `error` field from the hash and report it separately.

**WL-B2 — `run_worldline` override resolution silently drops unknown concept names.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:51-55`
- `concept_id = _resolve_concept_name(world, name); if concept_id is not None: override_concept_ids[concept_id] = value`. An override for an unknown concept is dropped from `override_concept_ids` without diagnostic. `trace.record_override(name, value)` still logs it, but no downstream surface flags "you overrode X but X was not found."
- Severity: MEDIUM (silent drop of authored user intent)
- Suggested fix: emit an unresolved-override diagnostic on the trace; surface as a warning in `WorldlineResult`.

**WL-B3 — Unknown targets are silently marked `underspecified`.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:89-94`
- A target that resolves to no concept_id is excluded from `target_map` at line 66-67, then later the defensive catch at line 89-94 produces `WorldlineTargetValue(status="underspecified", reason=...)`. The defensive path is invoked but the original lookup failure is not surfaced as a distinct diagnostic on the trace.
- Severity: LOW
- Suggested fix: record an unresolved-target step at the point of skip.

**WL-B4 — `WorldlineDefinition.is_stale` recomputes the entire worldline just to compare content hashes.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/definition.py:360-371`
- `current_results = run_worldline(self, world); return current_results.content_hash != stored_hash`. The only way to check staleness is to re-run the full computation — no short-circuit on dependency fingerprints, no cheap check.
- Severity: LOW (performance, not correctness)
- Suggested fix: cache dependency-only fingerprints and short-circuit staleness when none of the declared dependencies have changed.

**WL-B5 — `capture_argumentation_state` silently returns `None` when the backend's preconditions aren't met; `run_worldline` hashes `None` identically to "argumentation intentionally skipped."**
- File: `C:/Users/Q/code/propstore/propstore/worldline/argumentation.py:40-83`, `runner.py:104-121`
- The function returns `None` for `CLAIM_GRAPH`/`ASPIC`/`PRAF` if the backing store lacks `relation_edge`; for `ATMS` if the bound is not `HasATMSEngine`; and for any backend not listed. No diagnostic distinguishes "backend unavailable in this store" from "no arguments applied." The serialized worldline hash is identical in both cases.
- Severity: MEDIUM (silent ignorance)
- Suggested fix: return a typed "unsupported" or "skipped" `WorldlineArgumentationState` so callers can distinguish.

**WL-B6 — `active_stance_dependencies` uses JSON-serialized row as its dependency key, relying on `default=str` for non-JSON types.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/argumentation.py:284-335`
- `json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":"), default=str)`. `default=str` means any object that doesn't JSON-serialize becomes its `str()` repr — which for many dataclasses and IDs is stable but for others (e.g., anything with `<object at 0x...>`) is nondeterministic. If a stance row ever carries a non-JSON-native attribute with a volatile repr, the content hash becomes nondeterministic.
- Severity: LOW-MEDIUM (latent reproducibility hazard)
- Suggested fix: explicit key-projection to known-serializable fields; raise on unexpected types rather than falling back to `str()`.

## Dead Code / Drift

**DEAD-1 — `verify_labels` is not invoked on any build or test surface surveyed.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1107-1163`
- Severity: INFO
- Suggested fix: wire into CI as a post-build invariant, or remove.

**DEAD-2 — `_visible_context_ids` recomputes per call during build and propagation.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1746-1755`
- Not dead; minor perf nit. `_bound_environment_key` (line 1731-1738) and `_build_context_nodes` (line 1296-1304) both call it.
- Severity: INFO
- Suggested fix: memoize once per engine instance.

**DRIFT-1 — `_claim_input_candidates` in `support_revision/operators.py` handles legacy identifier shapes (namespace:value, logical_id, artifact_id, bare atom_id) that the state-level `coerce_active_claim` also normalizes.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/operators.py:23-56`
- Likely dead compatibility surface if atom_id normalization is now canonical.
- Severity: LOW
- Suggested fix: audit callers; if normalization is canonical, remove the legacy branches.

## Positive Observations

**POS-1 — ATMS label algebra is polynomial-backed; `normalize_environments` correctly maintains the minimal-environments antichain invariant.**
- File: `C:/Users/Q/code/propstore/propstore/core/labels.py:102-126`, `265-295`
- `combine_labels` is monotone cross-product with nogood pruning; `merge_labels` is alternative-support union. `normalize_environments` sorts by size/assumption_ids/context_ids and prunes supersets via `subsumes`. This is the correct implementation of de Kleer's minimal labels.

**POS-2 — `NogoodSet.excludes` uses polynomial `live()` semantics rather than naive set-containment; subsumption is handled correctly.**
- File: `C:/Users/Q/code/propstore/propstore/core/labels.py:97-99`
- An environment is nogood iff some nogood subset is a subset — `live` evaluates this on the polynomial ring rather than iterating set inclusions manually.

**POS-3 — ATMS build loop alternates propagation, parameterization materialization, and nogood update.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:1274-1280`
- The shape is correct: derived nodes materialized from existing supports can themselves become antecedents for further derivations. The sequencing is right; the termination criterion is where the concerns live (see ATMS-C1, C2).

**POS-4 — `_explain_justification` handles cycles via `seen_nodes` and emits an `ATMSCycleAntecedent` sentinel rather than recursing infinitely.**
- File: `C:/Users/Q/code/propstore/propstore/world/atms.py:2230-2237`
- Clean: the cycle is surfaced in the explanation payload, not silently elided.

**POS-5 — `worldline/runner.py` threads `dependency_claims` through to `content_hash` via `WorldlineDependencies`, preserving provenance for reproducibility.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:134-149`, `worldline/hashing.py:17-44`
- Consistent with the "lazy until render, provenance throughout" principle.

**POS-6 — `support_revision/state.py` is fully frozen dataclasses with `__post_init__` normalization of IDs; the data types themselves do not permit mutation.**
- File: `C:/Users/Q/code/propstore/propstore/support_revision/state.py:33-187`
- Immutability discipline is correct; any layer-bleed concerns are about *behavior* not *data*.

**POS-7 — `worldline/argumentation.py` dispatches reasoning backend selection explicitly rather than inferring from store shape.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/argumentation.py:40-78`
- `reasoning_backend` is carried on `definition.policy` and matched explicitly; good render-layer discipline.

## Summary

- Two HIGH-severity principle violations (`SR-L1`, `SR-L2`) on the support_revision / belief_set boundary; the package has drifted into AGM territory despite its disclaimer.
- Two MEDIUM principle-level ATMS provenance drops (`ATMS-C4`, `ATMS-C5`) where `context_ids` vanish from essential-support / serialized output.
- Two MEDIUM silent-failure / silent-drop bugs in the worldline runner (`WL-B1`, `WL-B2`, `WL-B5`) that interact with `content_hash` reproducibility.
- Several MEDIUM scaling cliffs with no bounds (`SR-B1`, `ASM-B1`, `ATMS-C7`).
- One MEDIUM ATMS silent skip (`ATMS-C6` on micropubs with missing claims).
- Multiple LOW-severity bugs around fixpoint termination, string-prefix heuristics, type coercion, and provenance dedup.

The codebase generally respects the lazy-until-render principle and the polynomial-backed label algebra is solid; the most acute issues are at the support_revision layer boundary and in silent drops that bypass honest-ignorance discipline.
