# Cluster J: worldline + support_revision + context lifting

## Scope

- propstore/worldline/{__init__,argumentation,definition,hashing,interfaces,resolution,result_types,revision_capture,revision_types,runner,trace}.py
- propstore/support_revision/{__init__,af_adapter,entrenchment,explain,explanation_types,history,iterated,operators,projection,snapshot_types,state,workflows}.py
- propstore/world/hypothetical.py (656 LOC, focused on counterfactual surface)
- propstore/context_lifting.py (229 LOC)
- tests/test_worldline*.py, tests/test_revision*.py, tests/test_context_lifting*.py
- docs/worldlines.md
- Paper notes: Bonanno 2007, Bonanno 2010 (file is named 2010 but title is 2012),
  Spohn 1988, Pearl 2000, Halpern 2005, McCarthy 1993, Bozzato 2018.

## Worldline runner correctness

The runner pipeline at `propstore/worldline/runner.py:38-162` follows
`bind -> overrides -> trace setup -> pre_resolve_conflicts ->
per-target resolution -> sensitivity -> argumentation -> revision ->
content_hash`. A handful of correctness concerns:

**R-1 (HIGH) — Transient errors mutate the content hash.**
- runner.py:117-121 catches all argumentation exceptions and writes a
  `WorldlineArgumentationState(status="error", error=...)` payload.
- runner.py:127-133 does the same for revision capture.
- runner.py:203-207 does the same per-target for sensitivity.
- All three error payloads are then fed into
  `compute_worldline_content_hash` (runner.py:143-151).
- Consequence: a transient failure (e.g., `grounding_bundle` not yet
  loaded, ATMS engine momentarily unavailable, sensitivity solver
  out-of-memory) produces a different hash than a successful run.
  `WorldlineDefinition.is_stale` (definition.py:360-371) will report
  the worldline as stale even though no inputs changed; the next
  successful run flips the hash again. Staleness detection is the
  documented purpose of the hash (docs/worldlines.md:46-48). The error
  string itself (`f"...failed: {exc}"`) often embeds object reprs with
  memory addresses, causing two errors with the *same* root cause to
  diverge in hash.

**R-2 (HIGH) — `is_stale` runs the full materialization.**
`definition.py:368-371` literally calls `run_worldline(self, world)`
inside `is_stale()`. There is no cheap fingerprint, no incremental
dependency check. This re-runs sensitivity, argumentation,
revision and the entire resolution cascade just to compare 16 hex
chars. A "list stale worldlines" CLI hits O(N) full materializations.
The cluster-A storage layer is not cheap.

**R-3 (HIGH) — String-typed overrides silently dropped from sensitivity.**
runner.py:173-177 builds `float_overrides` by iterating
`override_concept_ids` and only keeping `int|float`. A worldline with
a string override (e.g., setting `speaker_sex='male'`) gets a
sensitivity report computed against the *unconstrained* world. The
WorldlineSensitivityReport carries no marker that the override was
ignored, and the result still hashes as if sensitivity was honest.

**R-4 (MED) — Single-extension only for argumentation backends.**
argumentation.py:107-111 (CLAIM_GRAPH) takes
`analyzer_result.extensions[0]` only when `len(extensions) == 1`.
Anything else (preferred semantics with multiple extensions, stable
with multiple stable extensions) yields `justified_claims = None`,
which short-circuits to `return None` at line 127-128. Runner then
treats argumentation as silently absent. Multi-extension semantics
are first-class in Dung 1995 and downstream — silently dropping
non-singleton extensions is wrong both for `preferred` and for any
multi-status semantics.

**R-5 (MED) — Override sentinel is a fragile string prefix.**
trace.py:47 filters claim_id via
`not claim_id.startswith("__override_")`. The sentinel is unguarded
by any constant or test. If any caller renames or reformats override
synthetic claim IDs (no enforcement found in the cluster), they
silently leak into `dependency_claims` and the content hash.

**R-6 (MED) — Chain step dependency tracking under-counts.**
resolution.py:405-409 iterates `chain_result.steps` and only records
claim dependencies for steps where `step.source == "claim"`. Steps
sourced from `"resolved"` (conflict resolution) or `"derived"` are
not added to `dependency_claims`. Effect: chained derivations that
internally consume conflicting claims do not contribute their
contributing claims to the dependency set. Staleness detection will
miss claim changes inside chained derivations.

**R-7 (MED) — `pre_resolve_conflicts` ordering is non-deterministic.**
resolution.py:92-95 calls `reachable_concepts(...)` returning the
concepts as a set; then iterates `for cid in needs_check`. Set
iteration in CPython is insertion-ordered for `dict`, but
`reachable_concepts` is built from a set comprehension — order is
hash-dependent. Side effects on `context.resolved_values` and on
trace.steps depend on iteration order. Two equivalent runs can
record steps in different orders; steps go into the content hash
(hashing.py:34) → hash flip.

**R-8 (LOW) — `_context_dependencies` order tied to
`effective_assumptions`.** runner.py:213-224 returns
`["context_id", "assumption:..."*]` in whatever order
`bound._environment.effective_assumptions` returns. If that ever
becomes a set or unordered iterable, hash flips. Worth pinning a
sort.

**R-9 (LOW) — `runner.py:154` `computed = datetime.now(...)`** — not
in the hash (good) but it is the only timestamp on a result object
that is otherwise content-addressable; round-trips lose the
"originally computed at" anchor.

## Hashing / snapshot stability

**H-1 (HIGH) — `default=str` is a JSON escape hatch into nondeterminism.**
- hashing.py:44 (`json.dumps(..., default=str)`) — any non-JSON
  value (Enum, dataclass, set, custom object) silently becomes
  `str(value)`. Two genuinely different objects whose `__str__`
  collide produce identical hashes; conversely an object whose
  `__str__` includes a memory address (rare but possible for default
  reprs) flips the hash on every run.
- argumentation.py:285-289 (`_stance_dependency_key`) — same fallback.
- support_revision/history.py:40-47 (`_canonical_json`) — same
  fallback used for EpistemicSnapshot content_hash.
- support_revision/projection.py:168-176 (`_digest`) — same fallback
  used for condition fingerprints.
- This is a systemic determinism risk, not a one-off bug. A
  conservative change is to switch to a strict encoder that raises
  rather than coerces to str.

**H-2 (MED) — Truncation to 16 hex.** hashing.py:46
`hexdigest()[:16]` is 64 bits. Birthday collision at ~2^32
worldlines (~4 billion). Cheap to widen. The same 16-char truncation
is used in `_digest` at projection.py:176 for condition references —
collisions there silently merge unrelated conditions.

**H-3 (HIGH) — Snapshot "replay determinism" does not actually
replay.** support_revision/history.py:239-256
`check_replay_determinism` only verifies that recorded
`state_in_hash` and `state_out_hash` self-match and that the chain
is contiguous. It does NOT re-execute the operator on `state_in`
with `policy_payload + operation` and confirm `state_out` is
reproduced. Bit-perfect storage corruption is detected;
algorithmically incorrect transitions are not. The method name
overstates the guarantee.

**H-4 (MED) — Iterated revision freezes entrenchment from prior
state.** iterated.py:108-112 `_entrenchment_from_state` rebuilds an
`EntrenchmentReport` from the *current state's* `ranked_atom_ids`
and `entrenchment_reasons`; it never re-runs `compute_entrenchment`
on the new (revised) belief base. So after a revise, atoms get
entrenched by support counts derived from the pre-revision base. In
particular, atoms that gain or lose support due to the revision are
re-ranked using stale support counts. This makes iterated chains
diverge from one-shot revisions on the same input.

**H-5 (MED) — `EpistemicStateSnapshot.from_state` is a shallow copy.**
snapshot_types.py:319-329 just copies references to the same
`BeliefBase`, `accepted_atom_ids`, `entrenchment_reasons`. Snapshot
is hash-stable only because the underlying dataclasses are frozen.
Any future addition of a mutable field (Mapping subclass, list,
external cache) silently breaks immutability of historical snapshots.

**H-6 (MED) — `_revision_state_snapshot` returns the live state, not
a snapshot.** revision_capture.py:72-79: when `state.to_dict` is
callable, the function returns the *state* object, not a snapshot
copy. Subsequent serialization through
`WorldlineRevisionState.to_dict()` then calls `_to_plain_data` on it
(revision_types.py:224), which only walks `to_dict` once. If anyone
mutates the state object between capture and serialization (e.g.,
shared epistemic state held by a workflow), the recorded payload
drifts.

## Counterfactual / causal semantics gap

**Pearl/Halpern do-operator: ABSENT.**

Pearl 2000 defines `do(X = x)` as model surgery (Definition 3.2.1,
notes p.70):
> replace the structural equation for X with the constant X = x,
> deleting all arrows into X in the causal graph, and computing the
> resulting distribution over the remaining variables.

Halpern 2005 carries this forward: "Interventions are modeled by
replacing structural equations: to set X = x', replace F_X with the
constant function x'." (notes p.79-80).

`HypotheticalWorld` (`world/hypothetical.py:438-593`) does the
opposite. It is a graph *overlay*: it adds claims, removes claims by
ID, lets the existing parameterization graph propagate. Concretely:
- Lines 481-490: builds a `GraphDelta(add_claims, remove_claim_ids)`
  and applies it to the compiled graph. There is no removal of
  *parameterizations* feeding the overridden concept.
- Lines 552-560: recomputes conflicts via `_recomputed_conflicts`,
  which makes the override claim *compete* with the existing claim
  for that concept under conflict resolution policy — instead of
  unconditionally severing the parent edges.
- Lines 610-619: `derived_value` is delegated to the overlay
  BoundWorld, which evaluates parameterizations from parents whose
  edges were never cut.

So a "counterfactual" `X = 5` here behaves like an *additional
witness* for X = 5, not like the Pearl-style atomic intervention
that fixes X regardless of its causal parents. For an overdetermined
case (Halpern 2005 Fig 1, forest fire / Suzy-Billy preemption),
HypotheticalWorld cannot distinguish "fix X" from "another claim
asserts X."

`diff()` at hypothetical.py:636-654 only walks concepts whose
*claims* were directly added/removed (line 636-643). Concepts
derived via parameterization from those concepts are not in
`affected` and not surfaced. Downstream causal effects of an
intervention are invisible.

**Spohn OCF: ABSENT.**

Spohn 1988 (notes Sect "Ordinal Conditional Function (OCF)") defines
kappa as a function from propositions to ordinals, with
A_n-conditionalization parameterized by firmness `n`
(`κ_{A,n}(w) = κ(w) - min(κ(A), n)` for `w ∈ A`).
EpistemicState in `support_revision/state.py:184-209` carries:
- `ranked_atom_ids: tuple[str, ...]` — pure positional ordering
- `ranking: Mapping[str, int]` — integer position derived from index
  in `ranked_atom_ids` (`make_epistemic_state`,
  iterated.py:22; `advance_epistemic_state` line 51)

There is no kappa value: no firmness parameter on revision input,
no surprise levels, no commutativity guarantee. The "ranking" int is
a sort key, not an ordinal disbelief grade. Iterated.py operators
`lexicographic` and `restrained` (lines 134-141) move atoms by
position only.

Result: Darwiche & Pearl C1-C4 are not implementable on this state
representation, because they require comparing kappa values across
revisions. Likewise the connection to subjective-logic uncertainty
that the project memory notes (`Imports are opinions`) hints at
cannot be made on positional ranks.

**Bonanno branching-time: PARTIALLY GAPPED.**

Bonanno 2007 (notes Limitations) requires Backward Uniqueness — each
instant has at most one predecessor. Bonanno 2012 relaxes this with
the PLS frame property and ternary `B(h, K, phi)`.

Current code:
- `RevisionScope` at state.py:90-104 carries `branch`, `commit`, and
  `merge_parent_commits: tuple[str, ...]`. The data model accepts a
  DAG with merges.
- iterated.py:66-67 `iterated_revise` raises `ValueError` when
  `len(state.scope.merge_parent_commits) > 1`. Test
  `test_run_worldline_revision_merge_point_refusal_is_explicit` in
  test_worldline_revision.py:272-311 confirms this is intentional.
- The runner converts the refusal into an error payload that is
  hashed (R-1 above), so a worldline at a merge point is permanently
  flagged as having an error revision state.

The code thus *detects* the merge point but provides no merge
operator. Bonanno 2012 §6 "Iterated belief revision" gives the
ternary operator `B(h, K, phi)` semantics that propstore would need
to satisfy AGM-consistency at branch joins. There is no
implementation, no tests, no surface area. This is a missing
feature, not a bug; calling it out because the data model already
implies it.

**Halpern actual cause (AC1/AC2/AC3): ABSENT.**

Halpern 2005 Definition 3.1 requires partition (Z, W) search and
freeze-and-test reasoning. Nothing in worldline/, support_revision/,
or hypothetical.py implements actual-cause queries. The data layer
has the raw materials (parameterization graph + override surface);
the query layer is missing.

## Context lifting reality check (rules authored vs applied)

**Cluster B's flag was that authored lifting rules are not applied.
That is overstated.** Concrete evidence:

`materialize_lifted_assertions` IS called from production code:
- `propstore/core/activation.py:62` —
  `_claim_projected_into_environment` materializes a lift query and
  filters claims into the bound environment. This is the correct
  enforcement point: a claim authored in context `c1` is visible in
  bound environment with `context_id=c2` only if the lifting system
  has a rule c1->c2 and the proposition isn't blocked by an
  exception.
- `propstore/sidecar/passes.py:179` — sidecar build pass also
  materializes lifts for the loaded contexts.

So the rules ARE consumed for cross-context visibility. What is
correctly observed by Cluster B (and confirmed independently here):
- The materialization is **single-pass**:
  context_lifting.py:176-214 iterates each rule once per assertion.
  Transitive lifts (c1 -> c2 -> c3) are NOT computed. Concretely if
  rule R1 says c1->c2 and rule R2 says c2->c3, an assertion authored
  in c1 is NOT visible in c3 even though composition would say
  otherwise. Bozzato 2018 CKR semantics define lifting via fixpoint
  closure under `eval()`; this implementation computes only the
  immediate-lift.
- No cycle detection. Two rules c1->c2 and c2->c1 with the same
  proposition will not loop because of single-pass, but they
  silently lose the closure semantics.
- `LiftingMaterializationStatus.BLOCKED` records exceptions at
  context_lifting.py:208-213 with a `clashing_set`. But the
  consumer at activation.py:70-73 only checks `status is LIFTED`,
  so blocked records exist as data but contribute nothing
  observable. Bozzato 2018 requires the blocked record to *justify*
  itself with a clashing assumption set; the field is recorded but
  never tested, only carried as provenance.
- McCarthy 1993 lifting axioms include the modal `ist(c, p)` and
  the transcendence operator. The propstore lifting system models
  only the propagation rules (BRIDGE / SPECIALIZATION /
  DECONTEXTUALIZATION as enum tags); there are no axioms that
  express *what mode means* — they are uninterpreted labels.

The worldline layer itself never references LiftingSystem. The
`_context_dependencies` (runner.py:213-224) records only the
context_id and the effective_assumptions; it does NOT record which
lifting rules contributed to making a claim visible. Provenance is
therefore lossy: a worldline result cannot answer "which lifting
rule made this claim count?". Bozzato 2018's clashing_set / CAS
model would expect the blocked exceptions to flow into the
explanation; they do not reach `WorldlineResult.dependencies`.

## Bugs

### HIGH

- **B1**: Transient subsystem errors flip the content hash and leak
  exception reprs into the hash payload — runner.py:117-133, 203-207
  + hashing.py:44.
- **B2**: `is_stale` runs full re-materialization on every check —
  definition.py:368-371. Pathological for batch staleness queries.
- **B3**: String overrides silently dropped from sensitivity but
  not flagged in the report — runner.py:173-177.
- **B4**: `default=str` JSON fallback in every content-hash path
  destroys determinism on any non-JSON-native object —
  hashing.py:44, history.py:47, argumentation.py:289,
  projection.py:174.
- **B5**: `check_replay_determinism` does not actually replay; it
  only checks recorded hash chain integrity —
  history.py:239-256. The name is a guarantee the code does not
  provide.
- **B6**: HypotheticalWorld is not a Pearl intervention. Override
  claims compete via conflict resolution rather than severing
  causal-parent edges — hypothetical.py:438-593.
- **B7**: `_choose_incision_set` enumerates 2^|candidates|
  combinations with `max_candidates=None` from public API —
  operators.py:91-99 calls without the ceiling, so DoS via large
  support sets is reachable. The ceiling parameter exists
  (operators.py:255-296) but is unused at the public surface.
- **B8**: Iterated revision uses stale support counts.
  `_entrenchment_from_state` (iterated.py:108-112) reconstructs an
  EntrenchmentReport from prior `ranked_atom_ids` instead of
  recomputing on the revised base. Iterated chains diverge from
  one-shot revisions.
- **B9**: Multi-extension argumentation semantics silently
  discarded. argumentation.py:107-111 only honors single-extension
  results; preferred / stable / multi-status semantics give no
  argumentation_state at all.

### MED

- **B10**: `_revision_state_snapshot` returns the live state object
  rather than a snapshot copy when `to_dict` is callable —
  revision_capture.py:72-79.
- **B11**: `pre_resolve_conflicts` iterates a set, ordering depends
  on hash. Steps recorded in nondeterministic order go into the
  content hash — resolution.py:92-95 + 117-124.
- **B12**: Chain step dependency tracking only counts `source ==
  "claim"` steps, missing `resolved` and `derived` chain steps —
  resolution.py:405-409.
- **B13**: `_query_target_atom_ids` raises on contract targets that
  don't begin with `ps:assertion:` or `assumption:`, but the
  WorldlineRevisionQuery shape allows arbitrary `target` strings.
  User-supplied concept names blow up — revision_capture.py:91-95.
- **B14**: Override sentinel `__override_` is a string prefix, not
  an enforced constant — trace.py:47.
- **B15**: 16-hex truncation of SHA-256 across worldlines AND
  condition fingerprints — hashing.py:46, projection.py:176.
- **B16**: `_GraphOverlayStore.compiled_graph` raises
  `TypeError("compiled_graph() is unavailable for semantic-only
  overlays")` when `_compiled is None` (hypothetical.py:413-416),
  but callers using `__getattr__` proxy will already have failed
  earlier. The error is shadowed if any other path tries to read
  it — confusing diagnostics.
- **B17**: Lifting rules not transitively closed —
  context_lifting.py:176-214. Two-hop lifts silently lost; cycles
  silently lose closure.
- **B18**: Lifting `BLOCKED` exceptions are computed and stored but
  never observed by activation — context_lifting.py:208 vs
  activation.py:70-73. Worldline provenance does not include
  lifting rule IDs or blocked clashing sets.
- **B19**: `_context_dependencies` orders assumptions by raw
  iteration over `effective_assumptions`. No sort — fragile against
  upstream changes — runner.py:222-223.
- **B20**: Snapshot is shallow copy; future addition of any mutable
  field on EpistemicState breaks historical immutability —
  snapshot_types.py:319-329.

### LOW

- **B21**: `computed` timestamp is wall-clock with no UTC enforcement
  beyond the single `timezone.utc` arg — runner.py:154. If the
  process clock changes the timestamp shifts; not in hash but
  observable.
- **B22**: `_resolve_chain_target` swallows arbitrary `Exception` and
  produces an error WorldlineTargetValue (resolution.py:375-386).
  Same hash-flip pattern as B1 but per-target, not whole-result.
- **B23**: `display_claim_id` (resolution.py:50-59) returns either
  the claim's `primary_logical_value` *or* the claim_id — meaning
  two different claims with the same logical value collide in the
  dependency claim list. Hashing then sees identical strings and
  cannot distinguish them.
- **B24**: `entrenchment.compute_entrenchment` ranks ties by raw
  `atom_id` lexicographic order (entrenchment.py:62). Stable but
  couples behavior to ID format. If atom_ids ever get a UUID
  prefix, ranking flips arbitrarily.
- **B25**: `coerce_assumption_ref` (state.py:33-39) silently coerces
  missing `kind` and `source` to empty strings; only
  `assumption_id` is validated. Two distinct assumptions with the
  same id but different kinds collide.

## Missing features

1. **Pearl do-operator** — needed for any genuine counterfactual
   query. Requires severing the parameterization edges feeding the
   intervened concept, not just adding a competing claim.
2. **Halpern actual-cause query** — AC1/AC2/AC3 evaluator over the
   parameterization graph + a witness search. None present.
3. **Spohn OCF ranking with firmness parameter** — required for
   Darwiche-Pearl iterated postulates and for any future bridge to
   subjective-logic uncertainty (per project memory note
   `imports_are_opinions`).
4. **Bonanno branching-time merge** — `merge_parent_commits` data
   model exists but `iterated_revise` refuses any DAG with
   |merge_parents|>1. Bonanno 2012 §6 ternary `B(h, K, phi)`
   provides the formal target.
5. **Lifting closure** — transitive composition of lifting rules,
   per Bozzato 2018 / McCarthy 1993. Single-pass only today.
6. **Lifting provenance in worldline output** —
   `WorldlineDependencies` should carry the rule_ids and exception
   ids that contributed to the claim being visible.
7. **`is_stale` cheap path** — fingerprint of input dependencies
   (claims, stances, contexts, parameterizations) without re-running
   the resolution cascade.
8. **Real `check_replay_determinism`** — re-execute the operator
   from `state_in` and compare hashes; today it only checks chain
   integrity.
9. **Sensitivity over string-typed overrides** — at minimum, mark
   the sensitivity report as "skipped due to non-numeric override"
   so the result faithfully reflects what was computed.
10. **Multi-extension argumentation surface** — capture `extensions:
    tuple[frozenset[str], ...]` and `inference_mode` (credulous /
    skeptical) in `WorldlineArgumentationState` rather than picking
    the first or punting.
11. **Strict canonical JSON** — replace `default=str` with a strict
    encoder that raises on unknown types so determinism failures
    are loud.
12. **Iterated revision recompute entrenchment** — call
    `compute_entrenchment` on the revised base instead of
    reconstructing from prior state.

## Open questions for Q

1. Does propstore intend HypotheticalWorld to be a Pearl-style
   intervention or only a "what if this claim were also asserted"
   overlay? The docstring says "graph-delta overlay" which matches
   today's behavior, but the project memory note on counterfactuals
   in `application-layer-and-undo.md` (not yet read) may say
   otherwise. If Pearl semantics are wanted, this is a fundamental
   redesign.
2. Is the merge-point refusal in `iterated_revise` permanent
   (intentional scope limit) or a placeholder until Bonanno 2012
   ternary B(h, K, phi) lands? The error path is wired into the
   worldline runner and tested at
   test_worldline_revision.py:272-311, suggesting it is current
   intended behavior.
3. Should `is_stale` rely on a cheap dependency fingerprint or is
   the current full re-materialization the policy choice ("always
   re-derive to be safe")? If the latter, the docs should say so;
   if not, a fingerprint table needs design.
4. Does the project intend `EpistemicState.ranking` to be ordinal
   positions (current behavior) or to migrate to Spohn kappa values?
   The integer-position implementation precludes Darwiche-Pearl and
   any subjective-logic bridge.
5. Are multi-extension semantics in scope for argumentation
   backends? Today the runner silently drops anything that is not a
   single grounded extension. If preferred / stable are supposed to
   be supported via the worldline surface, this is a behavior bug;
   if argumentation worldlines are scoped to grounded only, that
   should be documented.
6. Is the lifting layer expected to compute closure under
   composition, or are users expected to author every transitive
   rule explicitly? Bozzato 2018 implies closure semantics; the
   implementation does single-pass.
7. Should `WorldlineDependencies` be augmented with
   `lifting_rules: tuple[str, ...]` and `blocked_exceptions:
   tuple[str, ...]`? Without these, two worldlines that happen to
   produce the same values but rely on different lifting rules will
   share a content hash and look identical.
8. The `default=str` JSON fallback exists in four hashing
   surfaces (worldline, snapshot, stance dependency, condition
   digest). Is this consistent by intent, or should the project
   move to strict encoders? Determinism is load-bearing for the
   staleness contract.
