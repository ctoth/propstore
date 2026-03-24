# Physics Demo Repo Planning — Session Notes

**Date:** 2026-03-23
**Goal:** Build standalone `propstore-demos/physics/` tutorial repo showing propstore reasoning over classical physics.

---

## STATE: Pivoted to reified queries. Papers processing in background.

## Paper retrieval status (5 agents dispatched in parallel)
1. Green 2007 — Provenance Semirings: metadata only so far, retry dispatched
2. Buneman 2001 — Why and Where: metadata only so far, retry dispatched
3. Ghidini 2001 — Local Models Semantics: retry dispatched
4. Guha 1991 — Contexts thesis: retry dispatched
5. Halpern & Pearl 2005 — Causes and Explanations: retry dispatched

### Blockers encountered
- Chrome not on PATH (`where chrome` fails). Located at `/c/Program Files/Google/Chrome/Application/chrome.exe`.
- Q restarted Claude Code with Chrome available, but `where chrome` still fails.
- First batch of agents: Green and Buneman created metadata.json but couldn't download PDFs.
- Second batch: Buneman agent restated instead of executing (didn't recognize itself as subagent).
- Third batch (current): launched with explicit "You are a SUBAGENT. Execute immediately." — awaiting results.
- Root issue: the paper-process skill uses paper-retriever which needs Chrome for sci-hub. Agents may not find it.

### What we know so far (even without the papers)
The two research reports (`notes-reified-queries-existing-papers.md`, `notes-reified-queries-research.md`) already contain substantial findings:
- TMS tradition treats derived results as persistent cached artifacts (de Kleer: "intelligent cache")
- No existing system combines ATMS dependency tracking + nanopub citability + argumentation
- Martins 1983 Belief Space is closest to a "materialized view" concept
- Martins 1988 supported wff 4-tuple (wff, origin tag, origin set, restriction set) is closest to a reified query result
- Green 2007 provenance semirings would give us "how" provenance (polynomial annotations over input claims)
- Ghidini/Giunchiglia 2001 would formalize inter-scenario compatibility constraints
- Guha 1991 lifting axioms would enable inter-scenario reasoning

### Current state (as of latest notes update)
- 5 paper-process agents dispatched (3rd attempt), all running in background
- Previous attempts failed: (1) agents couldn't find Chrome on PATH, (2) agents restated instead of executing
- 3rd attempt uses explicit "You are a SUBAGENT. Execute immediately." prefix
- Multiple background task notifications for subagent searches (b38nqg6bs, b3bf8hd4u, etc.) — these are internal to the paper agents, not main completions
- Buneman agent completed: FAILED (paywalled, no open access, sci-hub searches killed)
- Other 4 agents still running — PDFs confirmed downloaded for Green, Ghidini, Guha, Halpern
- Halpern agent created TWO directories (2000 + 2005 versions), both with PDFs + pngs
- Agents now in note extraction phase (converting PDFs → page images → reading)
- Ghidini earlier-batch agent completed but ran out of budget before note extraction (PDF only)
- Retry agents (green-retry, ghidini-retry, guha-retry, halpern-retry) still running
- Many subagent background search tasks completing — these are internal to the paper agents
- Green 2007 agent DONE: notes.md, description.md, abstract.md extracted
- Halpern 2005 agent DONE: notes.md, description.md, abstract.md, claims.yaml (15 claims) extracted
- Ghidini 2001: DONE — notes.md, description.md, abstract.md, citations.md extracted
- Guha 1991: PDF downloaded, agent completed but ran out of budget reading thesis (100+ pages). Notes NOT extracted. Need manual paper-reader run.
- Buneman 2001: FAILED — paywalled, no open access, all search attempts failed

### Paper processing final status
- Green 2007: DONE (notes + 14 claims + 5 concepts registered)
- Ghidini 2001: DONE (notes + 18 claims)
- Halpern 2005: DONE (notes + 15 claims)
- Guha 1991: PDF only — thesis too long for agent budget, paper-reader dispatched in background
- Buneman 2001: FAILED — paywalled

### Naming decision: Worldline
Q proposed "worldline" — from physics, the complete path of an object through spacetime.
In propstore: a specific traced path through the knowledge space, parameterized by inputs and policy.
- `pks world` = unbound query space (already exists)
- `pks worldline` = a specific materialized path through it (new)
- Fits physics demo literally, distinctive in KR, natural CLI extension
- Carries the right connotation: trajectory, not snapshot; can diverge, be compared, be invalidated

### Current: Worldline implementation Phase 1
- Plan approved: `~/.claude/plans/humble-foraging-wilkes.md`
- 17 TDD tests written in `tests/test_worldline.py` — all fail with ImportError (correct red phase)
- Phase 1 tests (7): data model parsing, roundtrip, validation, file loading
- Phase 2 tests (8): materialization, overrides, dependencies, partial results, determinism, accuracy
- Phase 4 tests (2): staleness detection
- Baseline: 851 existing tests pass
- Phase 1+2+4+5 DONE: 17/17 tests pass, CLI working end-to-end
- Fixed: iterative fixpoint resolution in runner (multi-pass, feeds resolved values back)
- Fixed: acceleration ← gravitational_acceleration identity parameterization in physics demo
- Chain derivation works: location=earth → g_earth=9.807 → acceleration=9.807 → force=98.07
- CLI verified: create, run, show, diff, list, refresh, delete all work
- All phases complete. Summary of commits:
  - `e3a9409` TDD tests (17 tests)
  - `71e13c5` Phase 1: data model
  - `ce27140` Phase 2: materialization engine
  - `c5153a8` Iterative fixpoint (later replaced by recursive derivation)
  - `889613b` Recursive input derivation in ActiveClaimResolver (principled fix)
  - `fc58e76` Phase 5: CLI commands
  - `79be622` Phase 3: 16 property tests (P2/P3/P5/P6/P9/P10)
  - `a390ff1` Sensitivity + argumentation state capture

### Final test counts
- 884 total tests pass (851 original + 17 worldline + 16 property)
- Physics demo: 5 worldlines working (earth_force, moon_force, emc2, resolve_G, em_speed_of_light)
- README written with verified command output

### What was built
- `propstore/worldline.py` — data model (WorldlineDefinition, WorldlineResult, WorldlineInputs, WorldlinePolicy)
- `propstore/worldline_runner.py` — materialization engine with sensitivity + argumentation
- `propstore/cli/worldline_cmds.py` — CLI: create/run/show/diff/list/refresh/delete
- `propstore/world/value_resolver.py` — recursive derived_value (principled fix for chain derivation)
- `propstore/cli/repository.py` — worldlines_dir property + init scaffolding
- `tests/test_worldline.py` — 17 TDD tests
- `tests/test_worldline_properties.py` — 16 property tests probing 6 ATMS invariants
- `propstore-demos/physics/README.md` — tutorial with verified output

### Current state
- Full chain derivation WORKING: resolve G (argumentation) → get M,R (location=earth) → derive F_grav = G·m·M/R² = 98.20 N
- Derived g ≈ 9.820 vs measured g = 9.807 — real PARAM_CONFLICT (centrifugal correction)
- Extensions display improved: grouped by type, concept names, defeaters shown
- Explain rendering fixed: shows source node + indentation for multi-hop
- Pre-resolve pass added to worldline runner: resolves conflicted inputs before derivation
- Q has been editing worldline.py and worldline_runner.py (system reminders show changes):
  - worldline.py: is_stale now re-runs worldline and compares content hashes, compute_worldline_content_hash added
  - worldline_runner.py: _resolve_concept_name now uses hasattr guards, _stance_dependency_key added, _context_dependencies added
- 4 test failures: Q's new TestWorldlineDependencyLiveness tests use FakeWorld objects missing resolve_alias/get_concept
  - _resolve_concept_name now has hasattr guards so won't crash, but FakeWorlds need get_concept to return concept so name resolves
  - Tests at lines 667, 738, 831 need updating

### README verification — real output vs written output
Discrepancies found in derivation trace:
1. **mass_earth and radius_earth missing from trace** — the trace shows only
   `gravitational_constant (resolved)` then jumps to `gravitational_force (derived)`.
   The M_earth and R_earth values were used but not recorded as steps. This is because
   `_resolve_target` only records the final derived step, not intermediate input lookups.
   Need to fix the runner to record claim-sourced inputs in the trace.
2. **Output values not rounded** — README shows "98.20" but real output is "98.1997342622469".
   Should show real values, not fabricated rounded ones.
3. **Context demo not shown** — README asserts contexts matter but never shows a run without
   context to prove F=ma fails. Need to add this comparison.
4. **PARAM_CONFLICT not demonstrated** — README describes the derived-vs-measured g discrepancy
   but doesn't show `pks world check-consistency` detecting it. Need to verify and show.
5. **Sensitivity partial derivatives check out** — d/d(R) elasticity=-2.0 is correct for
   inverse-square law. Values are consistent with G=6.6743e-11, m=10, M=5.972e24, R=6.371e6.

### README fixes applied
- Derivation trace now shows all inputs (planetary_mass, orbital_radius) with claim sources
- Deduplicated steps (pre-resolve + trace no longer double-records G)
- Context section rewritten: honest about what context scoping does and doesn't do
  (filters claims, not parameterizations; F=ma defeat is propositional, not structural)
- PARAM_CONFLICT section: honest that transitive detector doesn't catch it (G conflicted at build time)
- Show output uses real values, not rounded fabrications
- One-sentence hook added before first code block
- Committed trace fix and README honesty

### Context scoping fix
- Moved newtonian_breakdown and fma_limitation claims to context: relativistic_mechanics
- Global: 38 active, F=ma defeated (4 defeated total)
- Classical: 36 active, F=ma survives (3 defeated: boys_G, cavendish_G, ideal_gas_law)
- Context filtering works via BoundWorld._context_visible (excludes relativistic context)
- Adding --context to extensions CLI command now
- Context fix done and committed. --context on extensions command works.
### Remaining demos verified
- **Bipolar support:** ether_theory added. At threshold 0.5: mutual attack → 7 defeated (maxwell+ether+speed_of_light_from_em). At threshold 0.8: ether excluded → 5 defeated (maxwell survives, support preserved). Committed.
- **Staleness:** Fresh → modify M_earth → rebuild → STALE. Works end-to-end.
- **DRY conflict detection:** Still TODO. Shared parameterization resolver.
- **README:** Done. Final rewrite with all feedback incorporated.

### Final state of propstore commits this session
- Worldline data model, runner, CLI, property tests (Phases 1-5)
- Recursive input derivation in ActiveClaimResolver
- Pre-resolve conflicted inputs in worldline runner
- Extensions display: type labels, concept names, defeaters
- Explain display: source nodes with indentation
- --context flag on extensions command
- Shared parameterization_walk.py (DRY)
- Relaxed exactness filter in param_conflicts
- Context exclusion FK fix in build_sidecar

### Final state of physics demo commits
- 41 concepts, 39 claims, 12 stances, 2 contexts
- g=GM/R² parameterization (approximate)
- Relativistic claims scoped to context
- Ether theory for bipolar support demo
- README: single-scenario narrative, all output verified
- 896 tests pass in propstore

### Physics demo status (paused, not abandoned)
- Demo repo at `C:\Users\Q\code\propstore-demos\physics\` — 33 concepts, 38 claims, 10 stances, 2 contexts
- Build works. Argumentation works beautifully (CODATA G wins, Van der Waals beats ideal gas, F=ma undercut)
- Derivation/chain blocked by design gap: CLI treats keyword args as CEL conditions, not numeric overrides
- This gap is what motivated the reified queries pivot

## Research reports completed
- `notes-reified-queries-existing-papers.md` — scout deep-read of 11 existing papers
- `notes-reified-queries-research.md` — researcher web search for new papers
- Key synthesis: no single paper combines ATMS dependency tracking + nanopub citability + argumentation
- Propstore's materialized query = Martins supported wff + ATMS labels + nanopub citability

## Pivot reason
The physics demo exposed a design gap: propstore can store knowledge and argue about it,
but can't answer "given mass=10, what is force?" The CLI treats all keyword args as CEL
condition filters, not numeric inputs. The parameterization machinery works (SymPy, chain
queries, sensitivity) but only from claims, not user-supplied values.

Q's insight: **reified queries** — queries themselves become knowledge artifacts stored in
the knowledge base. A materialized query has inputs, a derivation chain, results, policy,
and provenance. It can be argued about, compared, invalidated when upstream claims change.

This connects to ATMS (de Kleer 1986), nanopublications (Groth 2010), named graphs
(Carroll 2005), belief revision (Dixon 1993, Martins 1988).

Now researching literature before designing.

Plan file: `C:\Users\Q\.claude\plans\humble-foraging-wilkes.md`

## What I observed

### Propstore code capabilities (verified by reading source)
- **Forms** are bare stubs (`name: pressure` and nothing else). Schema supports full SI dimensions via keys L, M, T, I, Theta, N, J.
- **Parameterization** uses SymPy for evaluation. Supports `Eq()` form for bidirectional solving. Chain query does iterative fixpoint across parameterization groups (connected components of concepts sharing inputs).
- **Conditions** are CEL strings, checked via Z3 for disjointness. Condition variables must be concepts (e.g., `location` needs to be a category concept).
- **Argumentation** is fully implemented: Dung AF with ASPIC+ preference ordering, Cayrol bipolar derived defeats, grounded/preferred/stable extensions.
- **Stances**: rebuts, undercuts, undermines, supports, explains, supersedes, none.
- **Conflict detection**: automatic at build time. Same concept, same conditions, different values = CONFLICT. Different conditions = PHI_NODE.
- **Hypothetical reasoning**: add/remove claims, diff results.
- **Sensitivity**: partial derivatives and elasticity via SymPy.

### Schemas (verified by reading JSON schemas and validation code)
- Concept IDs: must be `concept<N>` format (strict)
- Claim IDs: `[source:]claim<N>` or `[source:]<descriptive_name>` format
- Claim provenance: `paper` and `page` required
- Parameterization relationships on concepts: `formula`, `inputs`, `exactness`, `source`, `bidirectional` all required
- Form schema required fields: `name`, `dimensionless`
- Stance standalone files: `source_claim`, `stances` list with `target`, `type`

### Unit lookup (`physgen_units.json`)
- Haven't read yet — next step is to check which compound units are present
- Base SI units (m, s, kg, A, K, mol) confirmed present
- Standard derived units (N, J, Pa, W, Hz, V) confirmed present
- Compound units (m/s, m/s^2, kg*m/s, m^3) — UNKNOWN, need to check

### Papers in collection
- 50 paper directories, 1 physics-related: `deKleer_1984_QualitativePhysicsConfluences`
- Rest are argumentation/TMS papers that ground propstore's machinery
- External sources needed for physics claims: CODATA, Cavendish, Boys, NASA, Newton, Einstein, Maxwell, Van der Waals

### Integration test patterns (verified)
- `tests/test_world_model.py` — full pipeline: YAML → build sidecar → WorldModel → BoundWorld → queries
- `tests/test_argumentation_integration.py` — stance graph → AF → extensions
- Pattern: create YAML in tmp dirs, build sidecar, construct WorldModel, assert on query results

## Phase 0 Results

### Unit lookup (`physgen_units.json`)
- All needed units FOUND: m/s, m/s², m², m³, kg·m/s, kg/m³, N, J, Pa, W, Hz, V, C, mol, A, kg, m, s, Ω
- MISSING: K (Kelvin) — added to physgen_units.json with `{"Θ": 1}`
- 384 total units in the lookup table

### Forms written (25 total)
- Enriched 4 existing stubs: pressure, frequency, time, rate (were just `name:`, now have kind/unit_symbol/dimensions)
- Created 21 new physics forms: mass, force, acceleration, velocity, distance, energy, momentum, power, temperature, volume, amount, density, electric_potential, resistance, electric_current, charge, area, gravitational_param, molar_energy_per_temperature, electric_permittivity, magnetic_permeability
- Script: `scripts/write_physics_forms.py`

### Gate 0 verification
- `uv run pks validate` → "Validation passed: 250 concept(s), 26 claim file(s)"
- `uv run pytest tests/ -x -q` → 851 passed, 222 warnings (identical to baseline)
- No regressions

### Baseline test count
- 851 passed, 0 failed, 222 warnings (all warnings are pre-existing parameterization eval warnings)

## Phase 0 committed
- Commit `37d39e7` in propstore: 26 files changed (25 forms + physgen_units.json K fix)

## Phase 1 in progress
- Demo repo at `C:\Users\Q\code\propstore-demos\physics\`
- Git initialized, commit `445e4c7`
- 16 TDD gate tests in `tests/test_physics_demo.py`
- Forms copied from propstore to `knowledge/forms/`
- **uv sync solved**: removed `[build-system]` entirely — works as non-package project
  - Local dep: `propstore = { path = "../../propstore", editable = true }` in `[tool.uv.sources]`
  - ast-equiv pulled transitively through propstore

## Phase 2 completed
- 33 concept YAML files generated via `scripts/write_concepts.py`
- Key fix: parameterization inputs + sympy must use concept IDs (concept1, concept2), not canonical names
- Key fix: dimension key must be `Theta` not Unicode `Θ` (schema enforces enum)
- Key fix: old form stubs needed `dimensionless` field added
- Gate 2: `pks validate` → "Validation passed: 33 concept(s), 0 claim file(s)"
- 13 warnings (mixed-form dimensional mismatch) — expected, the heuristic doesn't understand dimensional analysis
- ID map saved in script output for reference when writing claims

## Phase 3 completed
- 6 claim files, 38 claims total
- Build: 33 concepts, 38 claims, 19 conflicts
- Unicode unit fix needed: PyYAML writes ³·² as UTF-8 but forms/claims had encoding mismatch. Fixed by replacing with ASCII: m^3, kg*m/s, m/s^2 etc.
- G conflict NOT detected by conflict_detector (shows 0 in conflicts table for concept11). Need to investigate — may be a tolerance issue or the detector only checks same-type claims differently.
- PHI_NODEs correctly detected for location-conditional claims (18 pairs across g, planetary_mass, orbital_radius)
- CONFLICT detected: ideal_gas_law vs van_der_waals_eq (concept16/pressure)
- Binding works: `location=earth` correctly filters to earth-only g, mass, radius
- `pks world query concept11` shows all 3 G values correctly

## Issue: G conflict detection
- 3 G claims (concept11): codata_G=6.6743e-11, boys_G=6.658e-11, cavendish_G=6.754e-11
- No CONFLICT record in conflicts table
- This means `value_of("gravitational_constant")` might return "conflicted" status based on value disagreement in ActiveClaimResolver, even without a conflict record
- Need to verify: does the world query still show conflicted status?
- The argumentation test depends on G being conflicted so resolution can pick a winner

## Propstore bug found and fixed
- `_populate_contexts` in `build_sidecar.py` inserted exclusions inline while iterating contexts
- If context A excludes context B but B hasn't been inserted yet → FK violation
- Fix: two-pass — insert all contexts first, then insert exclusions
- 851 tests still pass after fix

## Phase 4 progress
- 10 stance files written: 3 supersession (G chain), 3 thermodynamic (rebuts + supports), 2 relativistic (undercuts), 2 cross-domain (supports)
- 2 context files: classical_mechanics, relativistic_mechanics (mutually exclusive)
- Need to: commit propstore fix, rebuild demo, update tests to use concept IDs not canonical names

## Key discovery: canonical_name != alias
- `value_of("gravitational_constant")` returns `no_claims` — canonical name is NOT in alias table
- Must use concept IDs (concept11) or registered aliases (G) for queries
- Tests need updating to resolve canonical names → concept IDs via the concept table
- CLI `pks world query G` works (alias), `pks world query gravitational_constant` fails

## API discoveries (fixed in test file)
- `WorldModel.__init__` takes `Repository`, not `sqlite3.Connection`
- `build_sidecar` takes `repo: Repository` kwarg (handles forms_dir, contexts_dir, stances_dir internally)
- `HypotheticalWorld.__init__` takes `remove: list[str]`, not `remove_ids`
- `compute_justified_claims` takes `ArtifactStore` (WorldModel), not SQLiteArgumentationStore
- `compute_justified_claims` returns `frozenset[str]` for grounded, `list[frozenset[str]]` for preferred/stable

## Next steps (Phase 2)
1. Copy forms from propstore to demo repo's `knowledge/forms/`
2. Write ~33 concept YAML files in `knowledge/concepts/`
3. Run `pks validate` from demo repo to verify Gate 2
4. Then Phase 3: claim files
