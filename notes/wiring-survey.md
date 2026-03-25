# Wiring Survey: Connection Points in propstore

Date: 2026-03-25

## Q1: What does `compute_consistent_beliefs()` actually do?

**Location:** `propstore/argumentation.py:319-374`

**Full path:**
1. Takes `store: ArtifactStore` and `active_claim_ids: set[str]`
2. Loads claim rows via `store.claims_by_ids()` (line 337)
3. Computes scalar strengths via `claim_strength()` from `preference.py`, averaging multi-dim to a single float (line 341-346)
4. Wraps claims into a synthetic `LoadedClaimFile` (line 350-354)
5. Builds a minimal concept registry from claim concept IDs (line 357-362)
6. Calls `conflict_detector.detect_conflicts()` (line 364)
7. Filters records to CONFLICT, OVERLAP, PARAM_CONFLICT classes (line 367-372)
8. Passes conflict pairs + strengths to `maxsat_resolver.resolve_conflicts()` which uses Z3 Optimize (line 374)
9. Returns `frozenset[str]` of claim IDs to keep

**Who calls it:** Nobody in production code. Grep for `compute_consistent_beliefs` across all `.py` files returns only its definition at `argumentation.py:319`. It is not imported or called anywhere. This is dead code -- defined but never wired into any pipeline.

**Does it use conflict_detector?** Yes, `conflict_detector.detect_conflicts()` at line 364.
**Does it use maxsat_resolver?** Yes, `maxsat_resolver.resolve_conflicts()` at line 374.

## Q2: Resolution flow for each reasoning backend

**Entry point:** `resolution.py:287` `resolve()` function.

All backends share the same entry: `resolve()` checks `vr.status` from `view.value_of(concept_id)`. If "conflicted", it dispatches based on `strategy` and `reasoning_backend`.

### CLAIM_GRAPH (resolution.py:379-386)
- Calls `_resolve_claim_graph_argumentation()` (line 80)
- Which calls `argumentation.compute_claim_graph_justified_claims()` (line 100)
- Which calls `build_argumentation_framework()` then `grounded_extension()`/`preferred_extensions()`/`stable_extensions()` from `dung.py`
- **Data in:** `target_claims` (concept's active claims), `active_claims` (all active), `world` (ArtifactStore), semantics, comparison
- **Data out:** `(winner_id, reason)` tuple. Winner selected by: intersect extension with target concept's claim IDs. If exactly 1 survives, that's the winner.

### STRUCTURED_PROJECTION (resolution.py:387-395)
- Calls `_resolve_structured_argumentation()` (line 124)
- Which calls `build_structured_projection()` then `compute_structured_justified_arguments()` from `structured_argument.py`
- Each claim maps to `arg:{claim_id}`. Extension computed over arg IDs, then mapped back to claim IDs via `argument_to_claim_id`.
- **Data in:** same as CLAIM_GRAPH plus `view: BeliefSpace` (for `claim_support` metadata)
- **Data out:** same `(winner_id, reason)` tuple

### PRAF (resolution.py:396-404)
- Calls `_resolve_praf()` (line 188)
- Which calls `argumentation.build_praf()` then `praf.compute_praf_acceptance()`
- **Data in:** same as CLAIM_GRAPH plus `policy` (for PRAF strategy params)
- **Data out:** `(winner_id, reason, acceptance_probs)` -- 3-tuple. Winner selected by highest acceptance probability among target claims, with `math.isclose` tie detection.
- `acceptance_probs` is stored in `ResolvedResult.acceptance_probs` (types.py:146)

### ATMS (resolution.py:405-406)
- Calls `_resolve_atms_support()` (line 268)
- Uses `view.atms_engine().supported_claim_ids()` intersected with target IDs
- **Data in:** `target_claims`, `view: BeliefSpace`
- **Data out:** `(winner_id, reason)` -- no opinion/probability data

### Winner selection pattern (resolution.py:412-427)
After backend dispatch, ALL backends converge at line 412: if `winner_id is None`, return CONFLICTED with reason. Otherwise, look up the winning claim's value and return RESOLVED.

## Q3: Where does `apply_decision_criterion()` need to be called?

**The function exists** at `types.py:216-264`. It is fully implemented with pignistic, lower_bound, upper_bound, and hurwicz criteria.

**Current call sites:** Only in tests (`tests/test_render_policy_opinions.py`). It is NOT called in any production code path.

**Where the policy fields are read but unused:** In `resolution.py:329-332`, the resolve function extracts `_decision_criterion`, `_pessimism_index`, and `_show_uncertainty_interval` from the policy but stores them in local variables prefixed with `_` and never uses them. This is explicitly noted in a comment: "used post-resolution for re-interpreting opinion uncertainty at render time".

**Where it would naturally slot in:**

1. **PRAF path (resolution.py:248-258):** After computing `best_prob = max(target_probs.values())` at line 248. Currently `target_probs` uses raw `acceptance.get(cid, 0.0)` which is already an expectation (pignistic). The decision criterion could reinterpret acceptance probabilities using the opinion components if they were available at this point. However, PrAF acceptance probs are scalar floats (not opinions) -- they come from MC sampling counts, not from opinion algebra. So the criterion would need to be applied earlier, at the stance level, not at the acceptance probability level.

2. **The real insertion point is in `_resolve_praf` or in the caller of `resolve()`:** The `ResolvedResult` already carries `acceptance_probs`. A post-resolution step could take these probabilities plus the stance opinions and apply the criterion. But this requires carrying opinion components through to the resolution result, which is not currently done.

3. **Alternative: at the worldline_runner level (worldline_runner.py:439-460):** After `resolve()` returns, the `_resolve_target` function could apply the criterion to reinterpret the confidence/probability values in the result.

**Summary:** `apply_decision_criterion` is defined, tested in isolation, configured in both `RenderPolicy` and `WorldlinePolicy`, extracted from policy in `resolve()`, but never actually applied to any data in the production path.

## Q4: What would it take to auto-generate defeats from conflicts?

**Conflicts table schema** (from `conflict_detector/models.py:19-28`):
```
ConflictRecord:
  concept_id: str
  claim_a_id: str
  claim_b_id: str
  warning_class: ConflictClass  # CONFLICT, OVERLAP, PARAM_CONFLICT, PHI_NODE, etc.
  conditions_a: list[str]
  conditions_b: list[str]
  value_a: str
  value_b: str
  derivation_chain: str | None
```

**What `build_argumentation_framework()` expects** (argumentation.py:101-176):
- `store.stances_between(active_claim_ids)` returning dicts with: `claim_id`, `target_claim_id`, `stance_type` (one of rebuts/undercuts/undermines/supersedes/supports/explains/none), and optionally `confidence`, `opinion_belief/disbelief/uncertainty/base_rate`
- The AF is built from stance rows, not conflict records

**The gap:**
1. Conflicts give you `(claim_a_id, claim_b_id)` pairs with `warning_class` but no `stance_type`. You need to map conflict classes to attack types: CONFLICT/OVERLAP -> "rebuts" (bidirectional), PARAM_CONFLICT -> "rebuts" (bidirectional).
2. Conflicts are symmetric pairs; stances are directed. Each conflict would generate two stance-like records (A attacks B, B attacks A).
3. Conflicts have no opinion/confidence data. Under the current scheme, missing opinion -> `Opinion.dogmatic_true()` (praf.py:104-105), which means the defeat is certain. This is a strong assumption.
4. Conflicts are detected from claim data (values, conditions), not from LLM classification. They represent structural/logical conflicts, not epistemic stances.
5. The `compute_consistent_beliefs()` function at argumentation.py:319 already bridges conflicts to MaxSMT but never feeds into the AF pipeline. A simpler approach would be to synthesize stance rows from conflict records and feed them through the existing AF pipeline.

**Concrete work:** A function `conflicts_to_stances(conflicts: list[ConflictRecord]) -> list[dict]` that maps each conflict pair to two stance dicts with `stance_type="rebuts"` and `opinion=Opinion.vacuous()` (honest ignorance about whether the conflict constitutes a real defeat). These synthetic stances could be merged with real stances in `stances_between()` or injected at AF build time.

## Q5: What does the calibration framework need?

**`categorical_to_opinion()`** (calibrate.py:219-271):
- Takes `category: str` ("strong"/"moderate"/"weak"/"none"), `pass_number: int`, and optional `calibration_counts`
- `calibration_counts` type: `dict[tuple[int, str], tuple[int, int]]` -- maps `(pass_number, category)` to `(correct_count, total_count)`
- Without calibration data: returns `Opinion.vacuous(a=base_rate)` -- honest ignorance
- With calibration data: `r = correct_count`, `s = total_count - correct_count`, then `from_evidence(r, s, base_rate)`

**Where calibration data would come from:**
A validation set of human-judged stances. The pipeline would be:
1. Run NLI classification on a set of claim pairs
2. Have humans judge whether each classification was correct
3. Aggregate: for each (pass_number, category), count correct vs total
4. Store as a dict and pass to `categorical_to_opinion()`

**Is there infrastructure for collecting it?** No. Grep for `calibration_counts` shows it referenced only in:
- `calibrate.py` (definition)
- `tests/test_calibrate.py` (test with synthetic data)
- `tests/test_relate_opinions.py` (test)
- Various notes files

The actual call site in `relate.py:196` calls `categorical_to_opinion(strength, pass_number)` with NO calibration_counts argument, meaning it always returns vacuous opinions. There is no mechanism to collect, store, or load calibration data from the knowledge base or sidecar.

**`CorpusCalibrator`** (calibrate.py:105-203):
- Takes `reference_distances: list[float]` -- pairwise distances from the corpus
- `to_opinion(distance)` converts a distance to an Opinion via local CDF density
- Uses `_effective_sample_size()` with kernel bandwidth `h = 1/sqrt(n)` and caps at `_MAX_N_EFF = 50`
- Not called anywhere in production code (only in tests). Would be used in the embedding pipeline to calibrate raw distances.

## Q6: PRAF opinion-to-sampling-probability chain

**Full chain:**

1. **Stance DB row** has columns: `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, `opinion_base_rate`, `confidence` (from `relate.py:210-213` which writes these fields)

2. **`build_praf()`** (argumentation.py:179-233):
   - Calls `build_argumentation_framework()` first to get the AF (defeats set)
   - Re-loads stances via `store.stances_between()` (line 205)
   - Indexes stances by `(source_id, target_id)` (line 208-214)
   - For each defeat in `af.defeats`, looks up the stance and calls `p_defeat_from_stance(stance)` (line 221)
   - For derived defeats (Cayrol) or missing stances, uses `Opinion.dogmatic_true()` (line 225)

3. **`p_defeat_from_stance()`** (praf.py:81-105):
   - Fallback chain:
     - If opinion columns (b,d,u,a) all present -> `Opinion(b, d, u, a)` (line 97)
     - Elif confidence present -> `from_probability(confidence, 1)` (line 101) -- this gives moderate uncertainty (n=1 means W=2, so u = 2/(2+2) = 0.5)
     - Else -> `Opinion.dogmatic_true()` (line 105) -- certain defeat, backward compat

4. **`p_arg_from_claim()`** (praf.py:71-78):
   - Always returns `Opinion.dogmatic_true()` -- all active claims exist with certainty
   - This is a stub/hook; no claim-level existence uncertainty is modeled

5. **MC sampling** (`_sample_subgraph()`, praf.py:249-295):
   - For each argument: `p_a = praf.p_args[a].expectation()` (line 268), include if `rng.random() < p_a`
   - For each defeat: `praf.p_defeats[(f,t)].expectation()` (line 277), include if `rng.random() < that`
   - `Opinion.expectation()` = `b + a * u` (Josang 2001 Def 6)

6. **Current reality with vacuous opinions:** Since `relate.py:196` always passes no calibration data, `categorical_to_opinion()` returns vacuous opinions (b=0, d=0, u=1, a=base_rate). So:
   - For "strong" stances: `expectation() = 0 + 0.7 * 1 = 0.7`
   - For "moderate": `0.5`
   - For "weak": `0.3`
   - For "none": `0.1`

   These base rates (defined at calibrate.py:211-216) effectively become the sampling probabilities for defeats in the PRAF MC sampler.

## Q7: Structured argument vacuous pruning

**Location:** `structured_argument.py:148-151` in `_build_projected_framework()`

```python
        # Soft epsilon prune: only remove stances with zero information content
        opinion_u = stance.get("opinion_uncertainty")
        if opinion_u is not None and opinion_u > 0.99:
            # Vacuous opinion -- no information content (Josang 2001, p.8)
            continue
```

**This pruning is UNCONDITIONAL.** There is no flag, no policy check, no configuration. If a stance has `opinion_uncertainty > 0.99`, it is silently dropped from the structured projection AF.

**This is a gate before render time**, which violates the CLAUDE.md design checklist item 3: "Does this add a gate anywhere before render time? If yes -> WRONG."

**Contrast with other backends:**
- `argumentation.py` `build_argumentation_framework()` (lines 101-176): NO vacuous pruning. All stances with attack types participate regardless of uncertainty.
- `praf.py` `_sample_subgraph()` (lines 249-295): NO pruning. Vacuous opinions get low expectation values, meaning they rarely survive sampling -- the probabilistic framework handles uncertainty naturally.

**The STRUCTURED_PROJECTION backend is the only one that hard-prunes vacuous stances.** This means the same stance data can produce different AF structures depending on which backend is selected, not because of different semantics but because of an inconsistent pre-filter.

## Q8: How worldline_runner.py invokes argumentation

**Entry:** `run_worldline()` at worldline_runner.py:36

**Backend selection logic:**
1. `definition.policy` is a `WorldlinePolicy` (from worldline.py:53), which has `reasoning_backend: str = "claim_graph"` (line 64)
2. `worldline_runner.py:71` converts to enum: `ReasoningBackend(definition.policy.reasoning_backend)`
3. This goes into `RenderPolicy(reasoning_backend=...)` at line 71
4. The policy is passed to `world.bind(environment, policy=policy)` creating a BoundWorld (line 87)
5. Resolution happens at `_resolve_target()` (line 139) -> `resolve()` (line 440) which dispatches on the backend

**Argumentation state capture** (worldline_runner.py:187-276):
- Section 5 builds `argumentation_state` ONLY when `strategy.value == "argumentation"` (line 190)
- For `claim_graph`: calls `compute_claim_graph_justified_claims()` directly (line 201)
- For `structured_projection`: calls `build_structured_projection()` + `compute_structured_justified_arguments()` (line 229-238)
- For `atms`: calls `atms_engine().argumentation_state()` (line 253)
- **PRAF is missing from argumentation state capture.** There is no `elif reasoning_backend == "praf"` branch in the argumentation state section. PRAF resolution works (via `_resolve_praf` in resolution.py), but the worldline doesn't capture its argumentation state for the result.

**WorldlinePolicy** (worldline.py:53-83):
- Has `decision_criterion`, `pessimism_index`, `show_uncertainty_interval` fields
- Has `praf_strategy`, `praf_mc_epsilon`, `praf_mc_confidence`, `praf_treewidth_cutoff`, `praf_mc_seed`
- These are all forwarded to `RenderPolicy` at worldline_runner.py:75-83

## Q9: Test coverage at the seams

### Files found:

| Test file | What it covers |
|-----------|---------------|
| `tests/test_argumentation_integration.py` | Full pipeline: stance graph -> preference filter -> Dung AF -> extensions. Uses in-memory SQLite with SQLiteArgumentationStore mock. |
| `tests/test_praf_integration.py` | PrAF integration into resolution pipeline. Uses _MockStore and _MockBeliefSpace. Tests resolution.resolve() with ReasoningBackend.PRAF. |
| `tests/test_praf.py` | Unit tests for praf.py: MC sampling, exact enumeration, deterministic fallback, component decomposition. |
| `tests/test_structured_argument.py` | Structured argument projection tests. |
| `tests/test_bipolar_argumentation.py` | Cayrol 2005 derived defeats, support chains. |
| `tests/test_calibrate.py` | TemperatureScaler, CorpusCalibrator, categorical_to_opinion, ECE. |
| `tests/test_relate_opinions.py` | Opinion algebra wiring in relate.py. Vacuous opinions without calibration. |
| `tests/test_render_policy_opinions.py` | apply_decision_criterion in isolation. All four criteria tested. |
| `tests/test_worldline.py` | Worldline materialization. |
| `tests/test_maxsat_resolver.py` | MaxSMT resolver in isolation. |
| `tests/test_conflict_detector.py` | Conflict detection in isolation. |
| `tests/test_opinion.py` | Opinion algebra (from_evidence, from_probability, fusion, etc). |
| `tests/test_dfquad.py` | DF-QuAD gradual semantics. |

### Gaps at the seams:

1. **No test for `compute_consistent_beliefs()`** -- it's dead code with no callers and no tests.
2. **No test for resolution.py dispatch logic with real stores** -- the integration tests use mocks. There's no test_resolution.py file at all.
3. **No test for worldline argumentation state capture** -- worldline tests exist but I didn't verify if they cover the argumentation_state section.
4. **No test for `apply_decision_criterion` in a real resolution path** -- only tested in isolation in test_render_policy_opinions.py.
5. **No test for conflicts -> defeats pipeline** (because it doesn't exist yet).
6. **No test for PRAF argumentation state in worldline** (because that branch doesn't exist in worldline_runner.py).
7. **No test for CorpusCalibrator in the embedding pipeline** (because it's not wired in yet).

## Q10: Is there a policy that configures decision_criterion?

**Yes, both policy types have the field:**

- `RenderPolicy` (types.py:197): `decision_criterion: str = "pignistic"` with `pessimism_index: float = 0.5` and `show_uncertainty_interval: bool = False`
- `WorldlinePolicy` (worldline.py:69-75): same three fields with same defaults

**WorldlinePolicy -> RenderPolicy forwarding** (worldline_runner.py:75-77):
```python
policy = RenderPolicy(
    ...
    decision_criterion=definition.policy.decision_criterion,
    pessimism_index=definition.policy.pessimism_index,
    show_uncertainty_interval=definition.policy.show_uncertainty_interval,
    ...
)
```

**Where it's read but unused** (resolution.py:329-332):
```python
_decision_criterion = policy.decision_criterion
_pessimism_index = policy.pessimism_index
_show_uncertainty_interval = policy.show_uncertainty_interval
```
These are extracted into underscore-prefixed locals and discarded. The comment says "used post-resolution for re-interpreting opinion uncertainty at render time" but this post-resolution step does not exist.

**CLI configuration:** I did not exhaustively trace CLI argument parsing, but WorldlinePolicy.from_dict() (worldline.py:86) reads from a dict, suggesting YAML worldline definitions can set these fields.

---

## Summary of Key Findings

1. **`compute_consistent_beliefs()` is dead code** -- defined at argumentation.py:319, never called, bridges conflict_detector to maxsat_resolver but nobody uses the bridge.

2. **`apply_decision_criterion()` is defined, tested, configured in policies, extracted from policy in resolve(), but never applied** to actual resolution data. The three policy fields (`decision_criterion`, `pessimism_index`, `show_uncertainty_interval`) flow from WorldlinePolicy through RenderPolicy to resolve() where they are read into unused locals.

3. **Vacuous pruning inconsistency:** structured_argument.py:148-151 unconditionally prunes stances with opinion_uncertainty > 0.99. The other two backends (claim_graph, PRAF) do not prune. This is a gate before render time.

4. **PRAF argumentation state missing from worldline:** worldline_runner.py:194-256 captures argumentation state for claim_graph, structured_projection, and atms -- but not PRAF.

5. **Calibration is fully stubbed:** categorical_to_opinion() always returns vacuous opinions in production because relate.py:196 never passes calibration_counts. No infrastructure exists to collect or store calibration data.

6. **Vacuous opinions become base-rate sampling probabilities in PRAF:** The chain is vacuous opinion -> expectation() = base_rate -> MC sampling probability. So "strong" stances get 0.7 defeat probability, "moderate" 0.5, etc. This is driven by _DEFAULT_BASE_RATES at calibrate.py:211-216, not by any empirical evidence.

7. **Conflicts-to-defeats gap:** Conflict records have the right claim pair IDs but no stance_type or opinion. A mapping function is needed to synthesize stance-like records for the AF pipeline.
