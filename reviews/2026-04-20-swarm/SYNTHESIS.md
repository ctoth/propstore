# propstore Cross-Repo Review Synthesis — 2026-04-20

Fourteen parallel analyst agents reviewed propstore (9 subsystems) and every git-pinned dep (`quire`, `argumentation`, `bridgman`, `gunray`, `ast-equiv`). Every finding below cites the source report under `reviews/2026-04-20-swarm/`. Every file-line reference is taken from those reports; this document is synthesis, not re-discovery.

## 1. Cross-cutting patterns

The same architectural failure modes recur in multiple subsystems. They are the highest-leverage fixes because each pattern touches ~3–10 findings.

### P1. Disagreement-collapse in storage (CLAUDE.md non-commitment discipline)

The core principle says: *do not collapse disagreement in storage unless the user explicitly requests migration.* It is violated in five places.

| Site | Finding |
| --- | --- |
| `propstore/storage/merge_commit.py:49-55` | Two-parent merge commit tree filters claim alternatives via `Counter(artifact_id) == 1`. Manifest metadata survives; rival **claim bodies do not**. (CRIT, storage.md) |
| `propstore/merge/` (`create_merge_commit` path) | Same bug surface, reported independently — classifier correctly emits disambiguated alternatives, then the write path filters them. (CRIT, merge.md) |
| `propstore/belief_set/agm.py:104-110` | `full_meet_contract` rebuilds output state with flat 0/1 ranks, erasing all prior entrenchment. (HIGH, belief_set.md) |
| `propstore/merge/` (`_classify_pair`) | Returns `CONFLICT` when `detect_conflicts` produces zero records — fabricated conflict where `UNKNOWN` is honest. (HIGH, merge.md) |
| `ast-equiv/src/canonicalizer.py:291-298` | `x == True` rewritten to `x`; `x == False` to `not x`. Unsound for non-boolean `x`; silently collapses distinct claims before they reach propstore. (HIGH, ast-equiv.md) |
| `propstore/world/atms.py:1055-1082, 2293-2297` | `essential_support` and `_serialize_environment_key` drop `context_ids` — context-dependent claims lose provenance in every serialized environment (explanations, intervention plans, argumentation state feeding `content_hash`). (MED, world-worldline-support.md) |

### P2. Fabricated confidence / provenance drops (honest-ignorance principle)

CLAUDE.md: *every probability-bearing document value that enters the argumentation layer must carry typed provenance: `measured|calibrated|stated|defaulted|vacuous`.* Violations, in decreasing severity:

- `belief_set/agm.py:125-143` — every AGM revision trace is stamped with `timestamp="1970-01-01T00:00:00Z"`, `ProvenanceStatus.STATED`, `source_artifact_code="ws-b-belief-set-layer"`. Hardcoded fabrication. (CRIT, belief_set.md)
- `classify.py:96-120, 151, 163-165, 242` — emits `"type": "error"` stance (not in `VALID_STANCE_TYPES`, will crash downstream); fabricates `strength="moderate"` when LLM omits the field; fabricates reverse stance on malformed JSON. (HIGH, heuristic-opinion.md)
- `calibrate.py:193-207` — `CorpusCalibrator.to_opinion` drops `CALIBRATED` provenance and hardcodes `base_rate=0.5`. Ignores the whole reason the calibrator exists. (HIGH, heuristic-opinion.md)
- `preference.py:32-36` — `metadata_strength_vector` fabricates `1/uncertainty = 1.0` when data is missing; every preference-derived defeat filter inherits the lie. (HIGH, argumentation-bridge.md)
- `source_calibration.py:93-145` — silently overwrites caller-supplied prior with `chain_query` result, stripping claim provenance to a bare float; also reaches from a storage-adjacent module into `propstore.world`. (HIGH, storage.md + heuristic-opinion.md)
- `ic_merge.py:76-78` — fabricates `len(signature) + 1` as distance when profile member is unsat; should be `math.inf`. (HIGH, belief_set.md)
- `core/activation._retry_with_standard_bindings` — regex-scrapes identifiers from CEL text and auto-registers them as synthetic concepts. Typos become valid concepts. (HIGH, semantic-core.md)
- `praf/engine.py:380-384` — `summarize_defeat_relations` emits dogmatic opinions `(p, 1-p, 0, 0.5)` with no `ProvenanceStatus`. (HIGH, argumentation-bridge.md)
- `fragility_contributors.py:395-400, 479-481, 555` — fabricated fragility coefficients with no citation. (MED, heuristic-opinion.md)
- `provenance/__init__.py:349-371` — `stamp_file` writes `produced_by` with no `ProvenanceStatus` field; the stamping path itself bypasses typed provenance. (HIGH, storage.md)
- `aspic_bridge/projection.csaf_to_projection:102-106` — grounded-only arguments get `strength=0.0` hardcoded. (MED, argumentation-bridge.md)

### P3. Build-time gates (Design Checklist rule 5: filter at render, not build)

The compiler/sidecar report quotes the rule in its own comments at `sidecar/build.py:11-12` and `sidecar/schema.py:12`, then violates it 26 times. Sample:

- `sidecar/build.py:307-311` — `except BaseException: sidecar_path.unlink(); raise`. Any exception, including Ctrl+C and `SystemExit`, wipes the entire sidecar. (CRIT)
- `compiler/workflows.py:131-141, 276-285, 305-309, 324-328, 345-355, 360-363, 394-397, 399-402, 405-415` — `CompilerWorkflowError` aborts `build_repository` before `build_sidecar` even runs, on concept/form/context/claim validation errors. (HIGH)
- `sidecar/build.py:95-97, 159-161` — form-validation and claim-pipeline `None` both raise `ValueError`, killing the build. (HIGH)
- `sidecar/passes.py:526-529, 539-542, 599-603, 612-615, 773-776` — five `sqlite3.IntegrityError` raises on dangling stance/justification/micropub refs; one bad ref kills the whole build. (HIGH)
- `source/promote.py:180-206, 504-506` — hard `ValueError` gates on ambiguous or unresolved concept mappings before data reaches sidecar. (HIGH, storage.md)

Schema v3 is *correctly designed* for render-time filtering (`claim_core.build_status`, `claim_core.stage`, `claim_core.promotion_status`, `build_diagnostics` table). The raw-id quarantine path at `sidecar/passes.py:704-755` and the grounded-fact persistence at `sidecar/rules.py` show the team knows the pattern. The other write paths ignore it. **One fix — generalize the raw-id quarantine pattern — defuses most of the rule-5 debt.**

### P4. Layer bleeding (one-way-dependency rule)

CLAUDE.md declares a strict 6-layer stack. Inversions:

- `propstore/storage/merge_commit.py:10` — Layer 1 imports from `propstore.merge.*` (Layer 4). (CRIT, storage.md)
- `propstore/source_calibration.py` + `source/finalize.py:100` — storage-adjacent modules invoke `derive_source_trust`, reaching into `propstore.world`. (HIGH, storage.md)
- `propstore/core/lemon/description_kinds.py` — concept layer (2) imports `argumentation.dung` (layer 4). (HIGH, semantic-core.md)
- `propstore/support_revision` — exports `expand`/`contract`/`revise`/`iterated_revise` with Nayak-Booth-Meyer DP operators plus an `EpistemicState` carrying `history`. CLAUDE.md forbids (SR-L1, SR-L2); only belief_set owns AGM/DP. (HIGH, world-worldline-support.md)
- `propstore/worldline/revision_capture.py` — consumes the forbidden AGM-shaped surface from support_revision, cascading the leak. (HIGH)
- `propstore/defeasibility.apply_exception_defeats_to_csaf:359-368` — CKR exception defeats injected into BOTH `framework.defeats` (post-preference) AND `framework.attacks` (pre-preference). ASPIC+ layers conflated. (HIGH, argumentation-bridge.md)
- `propstore/grounding._gunray_complement:17-31` — gunray-specific `~`-prefix encoding leaks through the ASPIC bridge. (MED, argumentation-bridge.md)
- `propstore/praf/engine.enforce_coh:281` — falls back to `defeats` (post-preference) when `attacks` is None; COH is pre-preference by construction. (HIGH, argumentation-bridge.md)

### P5. Dead code that lies about itself

- `belief_set/iterated.py:42-52` — `restrained_revise` is **byte-identical** to `revise`; docstring cites Booth-Meyer 2006. Tests don't probe operator-distinguishing properties, so the lie sits. (CRIT, belief_set.md)
- `source/alignment.py:68-78` — `classify_relation` never returns `"ignorance"`; the `elif relation == "ignorance"` branch (`:122-124`) is dead. Epistemic uncertainty collapsed to `non_attack`. (HIGH, storage.md)
- `aspic_bridge/projection:91-95, 123-127` — `premise_claim_ids` and `dependency_claim_ids` computed identically. One is dead or the spec drifted. (MED, argumentation-bridge.md)
- `argumentation/af_revision.py:21-28, 186-198` — `AFChangeKind.RESTRICTIVE` and `QUESTIONING` enum members dead. (MED, argumentation.md)
- `argumentation/af_revision.py:121-130` — `baumann_2015_kernel_union_expand` **does not compute kernels**; naive union masquerading as a Baumann 2015 citation. Tests only check monotonicity/idempotence (properties naive union also satisfies). (HIGH)
- `belief_set/agm.py:113-121` vs `iterated.py:63-71` — `extend_state` duplicated verbatim. (MED)
- `translate._transitive_closure` (`aspic_bridge/translate.py:224-241`) duplicates `argumentation.preference.strict_partial_order_closure`; local copy **does not detect cycles** unlike the canonical helper. (HIGH)
- `query._goal_contraries` mirrors kernel `_contraries_of`. (MED)
- `form_utils.py` vs `families/forms/stages.py` — two independent `_form_cache` globals and two `clear_form_cache`. Cache-consistency hazard. (MED, semantic-core.md)
- `ast-equiv`: Tier 4 documented/disabled, `_COMMUTATIVE_OPS` never read, `_VarCounter` never instantiated, `"True"/"False"/"None"` dead `KNOWN_BUILTINS` entries. (MED)
- Nine CLI dead-code items (`DC-1..DC-7`, cli.md).

### P6. Race / TOCTOU / atomicity

- `quire/git_store.py:262-308, 680-725` — `_commit` and `commit_flat_tree` read `tip_sha`, validate `expected_head`, then write via `refs[name] = sha`. Not atomic. Dulwich's `set_if_equals` is unused. `write_ref` / `write_blob_ref` have no CAS option at all. (HIGH, quire.md)
- `propstore/storage/merge_commit.py:114` — propstore calls `commit_flat_tree` WITHOUT `expected_head`. Merge races silently drop files. (HIGH, quire.md — consumer side)
- `sidecar/build.py:246-314` — non-atomic sidecar write. Crash between `unlink` and commit leaves a partial DB; `.hash` file still points at the prior successful hash, so the next invocation short-circuits against the partial DB. (HIGH, compiler-sidecar.md)
- `propstore/concept_ids.py:32-56` — `next_concept_id_for_repo` is read-modify-write, race on concurrent creation. (MED, semantic-core.md)
- Multiple `sqlite3` direct-connect sites in `source/promote.py`, `source/status.py` — no timeout, no WAL, no isolation. Races against the sidecar build pipeline. (MED, storage.md)
- `sidecar/build.py:81-84` — `content_hash` excludes `SCHEMA_VERSION`; schema upgrades don't trigger rebuild on unchanged commit. (HIGH, compiler-sidecar.md)

### P7. Silent-failure cliffs (diagnosis-killers)

- `worldline/runner.run_worldline:107-132` — broad `except Exception` on argumentation/revision capture; error *strings* with volatile fragments flow into `content_hash`, making transient failures permanently cache-busting. (MED, world-worldline-support.md)
- `sidecar/build.py:293` — `except (ImportError, Exception)` catches base `Exception` with only stderr output; no `build_diagnostics` row. (HIGH, compiler-sidecar.md)
- `quire/git_store.py:730-750, 988-991` — `_read_branch_meta` swallows JSON/Unicode errors; worktree prune catches all `OSError` on rmdir (Windows-relevant). (HIGH, quire.md)
- `gunray/_internal.py:183-190` — silent `KeyError` swallow; four `SemanticError` swallows in same file. (HIGH, gunray.md)
- `gunray/defeasible.py:84` — `del policy` silently discards closure policies that should route to `ClosureEvaluator`. README advertises direct use. (HIGH, gunray.md)
- `ast-equiv/comparison.py:227, 238` — three `except Exception: pass` blocks; pathological inputs and `RecursionError` indistinguishable from "genuinely inequivalent." (HIGH, ast-equiv.md)
- `bridgman/src/__init__.py:29-30` — bare `except ImportError: pass` hides not just missing-sympy but any other import failure in `symbolic.py`. (HIGH, bridgman.md)
- `propstore/families/claims/passes/checks.py:773` — catches `bridgman.DimensionalError` in an `except` tuple, but if sympy is missing the name itself raises `AttributeError` before the except clause evaluates. (HIGH, bridgman.md)

### P8. DoS / combinatorial blowup with no guards

- `argumentation/partial_af.py:231-338` — `sum_merge_frameworks` / `max_merge_frameworks` / `leximax_merge_frameworks` enumerate `2^(|A|²)` AFs. Five args = 33M candidates. No guard. propstore's merge subsystem calls these. (HIGH, argumentation.md)
- `gunray/_internal.py:201-219` — `_head_only_bindings` Cartesian product `|C|^N`, no safety gate. Adversarial DoS surface. (HIGH, gunray.md)
- `world/assignment_selection_merge.py:86-111` — `enumerate_candidate_assignments` K^N Cartesian, O(n²) dedup, no bound. (MED, world-worldline-support.md)
- `support_revision/operators.py:257-289` — `_choose_incision_set` O(2^n) over support-set members, no cap. (MED)
- `world/atms.py` — `_iter_future_queryable_sets` full 2^K power set bounded only by `limit`; each entry triggers a full ATMS rebuild. (MED)
- `belief_set/ic_merge._distance_to_formula` — re-enumerates worlds per (world, formula) pair, O(4^n). (MED)
- `aspic.py:852-932` (argumentation) — `build_arguments_for` cycle handling non-idempotent; memoization is depth-order-dependent, fixpoint correct but intermediate state fragile. (MED)

### P9. Consumer drift (propstore → deps)

- **gunray** (gunray.md):
  - `propstore/grounding/inspection.py:18` imports `from gunray.types import GroundDefeasibleRule`. `gunray.types` docstring marks itself internal and it is not in `__init__.py`.
  - `propstore/grounding/grounder.py:53` imports `DefeasibleSections` from `gunray.schema` — not in `__all__`.
  - `GunrayEvaluator.evaluate -> object` throws away all type info; `grounder.py:177` must `cast(DefeasibleModel, ...)`.
  - `grounder.py` calls `build_arguments(theory)` twice when `return_arguments=True` (work duplicated because `DefeasibleTrace.arguments` isn't routed through `evaluate`).
  - **Bonus gunray bug:** `schema.py:91-97` declares `Rule.body: list[str]` on a `frozen=True, slots=True` dataclass. `body.append()` works; `hash()` raises `TypeError`. Same lie on `DefeasibleTheory`'s six list fields. Duplicate rule IDs silently accepted.
- **bridgman** (bridgman.md): `propstore/families/concepts/passes.py:19` hard-imports `verify_expr`, `dims_of_expr`, `DimensionalError` — all sympy-gated in bridgman. If sympy is missing the imports themselves fail. bridgman's marketing of sympy as "optional" is fiction in practice.
- **ast-equiv** (ast-equiv.md):
  - `propstore/conflict_detector/algorithms.py:47` catches only `(ValueError, SyntaxError)` — misses `AlgorithmParseError` and `RecursionError`.
  - `propstore/sidecar/claim_utils.py:464` wraps nothing — `AlgorithmParseError` aborts sidecar build.
  - `propstore/world/value_resolver.py:524,566` catches `AstToSympyError` which is never raised out of `compare()`. Dead branch.
  - `comparison.py:227,238` both return `tier=2` (SymPy and bytecode). propstore's gate `result.tier <= 2` in `conflict_detector/algorithms.py:55` conflates them.
  - `canonical_dump` passes `concept_names` to `PositionalRenamer.rename`; `_normalize_and_canonicalize` (feeds SymPy and bytecode tiers) does not. Same input, different trees inside one `compare()`.
- **quire** (quire.md):
  - `quire/__init__.py:19-39` — `quire.documents` is imported by ~40 propstore files but is NOT in `__all__`. Same for `quire.artifacts`, `quire.family_store`, `quire.tree_path`, `quire.git_store`. Any tightening cascades.
  - `quire.artifacts` protocols lack `flat_tree_entries`/`store_blob`/`commit_flat_tree`; propstore's merge path must type against concrete `GitStore`.
  - Consumer bypass: `write_note` hardcodes author/message, so propstore calls `write_git_note` free function directly (`provenance/__init__.py:223`).

### P10. CLI adapter discipline

Detail in cli.md. Summary: *no owner module imports Click, the lazy registry works, family `__init__`s are rule-compliant*. The surface is mostly clean. Real issues:

- `proposal_cmds.py:40-44` — `pks` lies about promotions by iterating `plan.items` instead of the actual promoted result. (MED)
- Multiple exit-code holes: `pks show` / `pks checkout` emit errors to stdout and return 0 on not-found. (MED)
- `worldline_refresh` hardcodes defaults duplicating `@click.option` defaults; silent drift. (MED)
- Click glue bleeds faintly into owner: `coerce_worldline_cli_value` and `_parse_revision_atom_json` are owner-side functions doing CLI coercion work; owner-side types for `AppRevision*Request.atom` fields are the open question. (LOW-MED)

---

## 2. Correctness findings in deps

### argumentation (argumentation.md)
- **Stable-extension CF/defeat hybrid unpinned** (`dung.py:293-322`, `dung_z3.py:138-181`) — conflict-freeness uses pre-preference `attacks`, coverage uses post-preference `defeats`. Legal under M&P but diverges from pure Dung 1995 Def 12. No pinning test. (MED-HIGH)
- `_extend_state:207` silently defaults unknown ranks to 0 — changes Diller 2015 revision outcomes. (MED)
- `accepted_arguments` returns empty for empty extension family — conflates "no acceptance" with "semantics undefined" under stable. (MED)

### quire (quire.md)
- `revert_commit` does NOT check that `commit_sha` is reachable from target branch — silent inverse against unrelated branch tip. (HIGH)
- `materialize_worktree` overwrites unconditionally; `sync_worktree()` deletes untracked. Safe only on empty init. (HIGH)
- `VersionId.__lt__` reparses on every comparison, raises `ValueError` for non-calendar versions instead of `NotImplemented`. (MED)

### gunray (gunray.md)
- Frozen-list mutability lie on six fields (above). (HIGH)
- Duplicate rule IDs silently accepted across and within kinds; `SuperiorityPreference._closure` keyed by rule_id — collisions corrupt preference silently. (HIGH)
- Section projection adds non-paper `defeater_touches → not_defeasibly` clause deviating from García 04 Def 5.3. (MED — flagged as engineering choice, not bug)

### bridgman (bridgman.md)
- Symbolic `Pow` with non-numeric exponent raises `TypeError` (`float(exponent)` on `Symbol`). propstore catches only `(KeyError, ValueError, ImportError)`. (MED)
- `pow_dims(d, n: int)` never runtime-checks; float n silently produces `dict[str, float]` breaking contract. (MED)
- `Fraction(float(exponent))` on a sympy Float goes through IEEE-754. (MED)
- Doc says `"THETA"`, propstore uses `"Theta"`. Cosmetic but real drift. (LOW)

### ast-equiv (ast-equiv.md)
- `_reduce_stmts:147-183` reduces only the longer side. `compare(a,b).equivalent != compare(b,a).equivalent`. Symmetry test doesn't cover it (compares body to itself). (HIGH)
- `canonicalizer.py:619-729, 372-376, 307-320` — temp-var inlining + Mult commutative sort + chained-compare collapse reorder/dedup without side-effect checks. `t = f(); g(); use(t)` → `g(); use(f())`. (HIGH)

---

## 3. Prioritized punch list

### CRITICAL — data loss / immediate correctness / directional deception

1. **storage/merge_commit.py:49-55** — restore rival claim bodies in merge tree. The pair with `propstore/merge/` shares the same root.
2. **sidecar/build.py:307-311** — narrow `except BaseException` to `Exception`, stop unlinking the sidecar on any failure, write a `build_diagnostics` row instead.
3. **belief_set/iterated.py:42-52** — implement actual restrained revision or delete the function and the false Booth-Meyer citation.
4. **belief_set/agm.py:125-143** — route real timestamp + caller-supplied `ProvenanceStatus` into the trace instead of hardcoded `1970` / `STATED`.
5. **source/promote.py:743-751** — defuse zip-slip by rejecting any tracked path with `..`.
6. **compiler/workflows.py** — generalize the raw-id quarantine pattern to concept/form/context/claim validation errors. Remove the 9 `CompilerWorkflowError` aborts.

### HIGH — principle violations + silent correctness

7. **aspic_bridge/translate.py:135-136** — split `undermines` / `supersedes` from `contrary_pairs`; `undermines` is preference-sensitive per `core/relation_types.py:21-24`.
8. **preference.py:32-36** — when metadata is missing, return a vacuous opinion, not `1/uncertainty = 1.0`.
9. **classify.py** — drop the invalid `"error"` stance type (crash-on-downstream), fail hard on missing `strength`, reject malformed LLM JSON instead of fabricating a reverse stance.
10. **calibrate.py:193-207** — `to_opinion` must stamp `CALIBRATED` provenance and use the calibrator's base rate, not 0.5.
11. **source_calibration.py:93-145** — stop overwriting caller-supplied priors; do not reach into `propstore.world` from a storage-adjacent module.
12. **support_revision** — remove exported AGM/DP operators; if worldline needs them, it should import from belief_set.
13. **core/lemon/description_kinds.py** — remove the `argumentation.dung` import; concepts do not depend on argumentation.
14. **defeasibility.apply_exception_defeats_to_csaf:359-368** — inject CKR defeats via the post-preference `defeats` surface only; also keep `csaf.attacks: frozenset[Attack]` structurally consistent.
15. **aspic_bridge/translate._transitive_closure** — delete, use `argumentation.preference.strict_partial_order_closure` (cycle detection included).
16. **storage/merge_commit.py:10** — stop importing from `propstore.merge`. Move the shared logic to a neutral module or invert the direction.
17. **ic_merge.py:76-78** — unsat profile member distance is `math.inf`, not `len(sig)+1`.
18. **ast-equiv canonicalizer.py** — gate `x == True → x` on provable bool type; gate temp-var inlining, Mult-sort, chained-compare collapse on side-effect-freeness.
19. **gunray schema.py** — switch `body` and the five `DefeasibleTheory` list fields to `tuple[str, ...]`; enforce unique rule IDs cross-kind.
20. **quire expected_head** — use `dulwich.set_if_equals` for CAS; require `expected_head` on `commit_flat_tree` from propstore merge path.
21. **sidecar content_hash** — include `SCHEMA_VERSION`; make sidecar write atomic (tmp + `os.replace` + fsync both files).
22. **world/atms.py:2293-2297** — include `context_ids` in `_serialize_environment_key`; audit `essential_support` for the same drop.
23. **core/activation._retry_with_standard_bindings** — fail loudly on unknown CEL identifiers; do not auto-register concepts from regex scrapes.
24. **argumentation af_revision.py:121-130** — implement Baumann 2015 kernels or delete the function and its citation.
25. **argumentation partial_af.py merge family** — gate the 2^(|A|²) enumeration behind an explicit opt-in or a cardinality ceiling.

### MED — drift, dead code, silent failures, DoS surfaces

26. Collapse two independent `_form_cache` globals / two `clear_form_cache` into one.
27. Delete the `"ignorance"` branch in `source/alignment.py:122-124` (dead) or make `classify_relation` actually return it.
28. Delete `AFChangeKind.RESTRICTIVE` and `QUESTIONING` or make `_classify_extension_change` return them.
29. Fix `proposal_cmds.py:40-44` to iterate the real promotion result; fix `pks show`/`checkout` exit codes.
30. Fix `gunray/defeasible.py:84` — route closure policies to `ClosureEvaluator`, not `del`.
31. Fix `quire.documents` et al. — move to `__all__` or carve a deliberate public submodule path.
32. Fix `bridgman` sympy-gated imports: either drop the "optional sympy" claim or make `verify_expr`, `dims_of_expr`, `DimensionalError` import-safe without sympy.
33. Defuse `_head_only_bindings` / `enumerate_candidate_assignments` / `_choose_incision_set` / `_iter_future_queryable_sets` Cartesian explosions with explicit caps + diagnostic rows.
34. Fix `ast-equiv` Tier 2 collision — distinct tier numbers for SymPy vs bytecode.
35. Fix `ast-equiv` symmetry — reduce both sides in `_reduce_stmts`.
36. Drop `"True"/"False"/"None"` from `KNOWN_BUILTINS`; add RecursionError handling in `propstore/conflict_detector/algorithms.py:47`.

### LOW — cosmetic / deferred

See per-report `Dead Code / Drift` and `Positive Observations` sections in each file.

---

## 4. What is healthy

Ample evidence the team understands the principles. The fixes are narrow, and the patterns to copy already exist in the repo.

- `sidecar/rules.py` — grounded-fact persistence with verbatim paper citations, empty-predicate companion table preserving "empty verdict is still a verdict." Exemplary module.
- `sidecar/passes.py:704-755` — raw-id quarantine: the template for fixing the rest of the rule-5 debt.
- `world/assignment_selection_merge` — returns all ties as winners. Non-commitment done right.
- `belief_set/ic_merge` — emits contradiction when `mu` is unsatisfiable. Honest ignorance.
- Label algebra (`core/labels.py:102-295`) — polynomial-backed with proper antichain minimization and polynomial-live nogood exclusion. Theoretical core of the ATMS is correct.
- `_explain_justification` (ATMS) — cycle guard with `ATMSCycleAntecedent` sentinel instead of silent elision.
- `opinion.py` — Jøsang 2001 with page citations, van der Heijden 2018 Table I verified; `imps_rev` rejects non-provenance opinions with a hard error; `categorical_to_opinion` stamps provenance correctly.
- argumentation package — citation discipline excellent, immutable frozen dataclasses throughout, Z3 backend + brute-force share helpers so differential tests are meaningful.
- gunray — excellent paper-citation discipline; `CLAUDE.md` documents the exact pitfalls prior agents hit; Def 4.7 acceptable-line conditions enforced at construction.
- quire — iterator-first API, refs validated at construction, 1353-line Hypothesis stateful test suite for `GitStore`, `ContractManifest` enforces bump-or-marker discipline.
- bridgman — minimal API, `py.typed` shipped, zero hard deps, correct free-abelian-group algebra, F=ma/E=mc²/Maxwell c tested.
- CLI lazy registry works; no owner module imports Click.

The repo is not broken. It is drifting in specific, identifiable places against its own stated principles.

---

## 5. Review coverage gaps (honest ignorance)

- `world/bound.py` (1175 lines) and several secondary `world/`/`worldline/` files were not read in this pass. (world-worldline-support.md)
- Test suites for deps were NOT re-run. Findings are code inspection, not reproduction, except where the bridgman agent confirmed `x**n` with symbolic exponent experimentally and the gunray agent confirmed the frozen-list mutation experimentally.
- belief_set test suite not run (Hypothesis with `deadline=None`, not cheap).
- `quire/documents/codecs.py` beyond public surface, and most quire non-`git_store` test files, spot-checked only.
- argumentation test suite not re-run.

---

## 6. Per-report inventory

Absolute paths to every source report generated by the swarm:

- `reviews/2026-04-20-swarm/propstore/storage.md`
- `reviews/2026-04-20-swarm/propstore/belief_set.md`
- `reviews/2026-04-20-swarm/propstore/world-worldline-support.md`
- `reviews/2026-04-20-swarm/propstore/argumentation-bridge.md`
- `reviews/2026-04-20-swarm/propstore/semantic-core.md`
- `reviews/2026-04-20-swarm/propstore/cli.md`
- `reviews/2026-04-20-swarm/propstore/compiler-sidecar.md`
- `reviews/2026-04-20-swarm/propstore/merge.md`
- `reviews/2026-04-20-swarm/propstore/heuristic-opinion.md`
- `reviews/2026-04-20-swarm/deps/quire.md`
- `reviews/2026-04-20-swarm/deps/argumentation.md`
- `reviews/2026-04-20-swarm/deps/bridgman.md`
- `reviews/2026-04-20-swarm/deps/gunray.md`
- `reviews/2026-04-20-swarm/deps/ast-equiv.md`
