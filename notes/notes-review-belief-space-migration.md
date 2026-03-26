# Review: render-belief-space-migration branch (round 2)

## GOAL
Full review of all working-tree changes for bugs, regressions, architectural mismatches, missing cleanup, test gaps.

## What the branch does
1. Deletes `propstore/world_model.py` (was a backward-compat shim)
2. Introduces protocol types in `types.py`: `ArtifactStore`, `BeliefSpace`, `Environment`, `RenderPolicy`
3. Decouples `argumentation.py` from `sqlite3.Connection` → takes `ArtifactStore`
4. Decouples `graph_export.py` from concrete types → takes `ArtifactStore`/`BeliefSpace`
5. Adds `bind()` with Environment + RenderPolicy, BoundWorld carries policy
6. Adds `resolved_value()` to BoundWorld and HypotheticalWorld
7. Public wrappers on WorldModel for previously private methods
8. CLI: all imports → `from propstore.world import ...`; passes WorldModel as ArtifactStore
9. Test adapter: `SQLiteArgumentationStore` for argumentation tests
10. New test file: `test_render_contracts.py`
11. `Repository.store` cached_property with `close()`

## Findings

### HIGH
- `_resolve_argumentation` calls `world._has_table()` (private) — inconsistent with migration goal
- `resolve()` reaches into `view._store` and `view._base._store` (private attrs)

### MEDIUM
- BoundWorld keeps both `self._store` and `self._world` — need to verify `_world` usage
- graph_export.py docstring still says WorldModel/BoundWorld
- `SQLiteArgumentationStore` only implements 2 of ~20 ArtifactStore methods

### LOW
- validate_claims: unreachable `data.get("claims", [])` fallback after guard
- CLI double-dict wrapping in `all_concepts()` loop

## Round 3 Observations

### Protocol conformance
- WorldModel does NOT declare `class WorldModel(ArtifactStore)` — it structurally satisfies the protocol but static checkers can't verify drift
- BoundWorld and HypotheticalWorld do NOT declare BeliefSpace conformance
- This is acceptable for structural typing but fragile — any protocol method rename or addition silently breaks

### Resolution layer leaks abstraction
- `resolution.py:182-185`: `resolve()` does `isinstance(view, BoundWorld)` and `isinstance(view, HypotheticalWorld)` to extract `view._store` / `view._base._store` — this defeats the protocol pattern. A third BeliefSpace impl would fail with "no world for argumentation"
- `_resolve_argumentation` at resolution.py:67 calls `world.has_table("claim_stance")` — this IS on the ArtifactStore protocol, so it's fine

### BoundWorld constructor backwards compat
- BoundWorld.__init__ accepts BOTH old-style `bindings`/`context_id` kwargs AND new `environment` param. If `environment` is None, it constructs one from bindings/context_id. This is reasonable transitional compat.

### Repository.store
- `cached_property` returning WorldModel, with `close()` that checks `self.__dict__` for lazy cleanup. Clean pattern.

### graph_export.py
- Clean migration to ArtifactStore/BeliefSpace protocols. No private attribute access.

### validate_claims.py
- Line 135: `claims = data.get("claims", [])` is unreachable default (line 131 guards `"claims" not in data` with continue). Harmless but dead code.

### SQLiteArgumentationStore
- Only implements claims_by_ids, stances_between, has_table — the 3 methods argumentation actually needs. This is valid for tests but means the protocol is too broad for argumentation's actual needs.

### HypotheticalWorld.conflicts() potential double-counting
- Line 89: starts from `self._base.conflicts()` which already unions stored + recomputed conflicts for the BASE active claims. Then recomputes for HYPOTHETICAL active claims. The `seen` set deduplicates by (a_id, b_id, concept_id) key but does NOT check reverse direction — so if base had (X,Y,c) and recomputed has (Y,X,c), both survive. BoundWorld.conflicts() DOES check reverse_key.

### Test coverage
- test_world_model.py imports all new types and tests protocol-level behavior
- test_argumentation_integration.py and test_bipolar_argumentation.py properly use SQLiteArgumentationStore adapter
- test_render_time_filtering.py uses SQLiteArgumentationStore
- test_sensitivity.py, test_claim_notes.py, test_graph_export.py have minimal import changes

### world_model.py deletion
- File is fully deleted (was 3 lines). Need to verify no remaining imports.

## Round 4 — Full code review observations

### 1. resolve() abstraction leak (resolution.py:180-185) — HIGH
`resolve()` does `isinstance(view, BoundWorld)` then accesses `view._store` and `view._base._store`. This is the central protocol violation: any third BeliefSpace implementation would hit the "no world for argumentation" fallback. The `world` parameter exists to avoid this, but callers from `BoundWorld.resolved_value()` and `HypotheticalWorld.resolved_value()` already pass `world=self._store`, so the isinstance fallback is dead code for internal callers — but external callers using `resolve()` directly with a custom BeliefSpace will fail silently.

### 2. HypotheticalWorld.conflicts() missing reverse-key dedup (hypothetical.py:91-96) — MEDIUM
BoundWorld.conflicts() checks both `key` and `reverse_key` in `seen` before appending. HypotheticalWorld.conflicts() only checks `key`. If a conflict (A,B,c) exists in base and (B,A,c) appears in recomputed, both survive. This is an asymmetry between the two BeliefSpace implementations.

### 3. SQLiteArgumentationStore missing has_table (test adapter) — LOW
The test adapter implements claims_by_ids and stances_between but NOT has_table, which `_resolve_argumentation` calls. Tests pass because argumentation tests call build_argumentation_framework directly, never going through resolve(). But this means the adapter isn't a valid ArtifactStore for the full resolution path.

### 4. Public wrappers are pure delegation (model.py:95-96, 245-246, 272-273, 291-292) — STYLE
`condition_solver()`, `has_table()`, `parameterizations_for()`, `group_members()` are 1-line wrappers around private methods. Acceptable for protocol compliance but the private methods are now dead weight — nothing internal calls them anymore except the wrappers themselves.

### 5. proposal_policy field unused — LOW
`RenderPolicy.proposal_policy` is declared with default "source_only" but never read anywhere in the codebase.

### 6. cli/compiler_cmds.py double-dict (line ~943) — TRIVIAL
`for cdata in wm.all_concepts(): cdata = dict(cdata)` — all_concepts() already returns list[dict], the re-wrapping is redundant.

### 7. Environment.context_id flows correctly
WorldModel.bind() → Environment → BoundWorld.__init__ correctly propagates context_id. Verified.

### 8. chain_query properly uses bound.resolved_value() now
Was previously calling `resolve(bound, cid, strategy, world=self)` — now calls `bound.resolved_value(cid)` which inherits the policy. Clean improvement.

## Round 5 — Fresh review (2026-03-23)

### Test suite: 182 passed, 0 failed
All affected test files pass: test_render_contracts, test_world_model, test_argumentation_integration, test_bipolar_argumentation, test_render_time_filtering, test_sensitivity, test_graph_export, test_claim_notes.

### Old import path fully removed from source
`from propstore.world_model` only appears in `propstore.txt` (untracked text dump). All `.py` files use `from propstore.world import ...`. `propstore/world_model.py` has been deleted.

### validate_claims.py change
Added early guard `if "claims" not in data: continue` before the existing `data.get("claims", [])`. The `.get()` fallback on line after is now dead code but harmless.

### cli/claim.py change
Single import path change. Clean.

### cli/compiler_cmds.py changes
- 14 import path changes from world_model → world
- `wm._conn` replaced with `wm` (ArtifactStore) for argumentation calls (lines 678, 684)
- `wm._conn.execute(...)` replaced with `wm.all_concepts()` (line 941)
- `wm._conn.execute("SELECT * FROM parameterization ...")` replaced with `wm.parameterizations_for(cid)` (removed from diff)
- Double-dict wrapping: `for cdata in wm.all_concepts(): cdata = dict(cdata)` — all_concepts() already returns list[dict], so the re-wrapping is redundant but harmless (sqlite3.Row objects are gone)

### SQLiteArgumentationStore (test adapter)
Only implements `claims_by_ids` and `stances_between` — NOT `has_table`. This is fine because argumentation.py's `build_argumentation_framework` doesn't call `has_table`. But `compute_justified_claims` calls `build_argumentation_framework` which doesn't call `has_table` either — `has_table` is only called in `_resolve_argumentation` in resolution.py, and tests never route through that path with this adapter.

### Confirmed findings for final review

**HIGH: isinstance checks in resolve() break protocol abstraction (resolution.py:180-185)**
`resolve()` does `isinstance(view, BoundWorld)` / `isinstance(view, HypotheticalWorld)` to extract `_store`. Any third BeliefSpace impl hits "no world for argumentation" silently. Internal callers (BoundWorld.resolved_value, HypotheticalWorld.resolved_value) pass `world=` explicitly, so this is dead-code-ish for now but is a landmine.

**MEDIUM: HypotheticalWorld.conflicts() missing reverse-key dedup (hypothetical.py:91-96)**
BoundWorld.conflicts() checks both (A,B,c) and (B,A,c) in `seen`. HypotheticalWorld.conflicts() only checks (A,B,c). Asymmetric behavior — potential duplicate conflicts in hypothetical worlds.

**MEDIUM: condition_solver() return type untyped in ArtifactStore protocol (types.py:116)**
`def condition_solver(self): ...` has no return type annotation. Every other method in both protocols is typed.

**LOW: proposal_policy field declared but never read (types.py:84)**
`RenderPolicy.proposal_policy` defaults to "source_only" but nothing in the codebase reads it.

**LOW: WorldModel doesn't declare protocol conformance (model.py:35)**
`class WorldModel:` not `class WorldModel(ArtifactStore):`. BoundWorld/HypotheticalWorld don't declare BeliefSpace. Structural typing works at runtime but static checkers can't verify drift.

**TRIVIAL: Double dict() wrapping (compiler_cmds.py ~line 943)**
`for cdata in wm.all_concepts(): cdata = dict(cdata)` — redundant since all_concepts() returns list[dict].
