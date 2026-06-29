# propstore rewrite — execution plan

Status: DRAFT for review (scratchpad). Promote to `PLAN.md` on the `rewrite` branch as Phase 0's first commit.

## 1. What this is

propstore is rebuilt **fresh** as a thin semantic-composition layer over substrate packages.
It is NOT cleaned up in place (in-place refactor structurally invites the coercer/DTO rot that
broke it). The May-16 reference (`20e55cca`, 3702 tests green) is the **read-only spec + test
source** — consulted, never edited, never copied. Each domain entity becomes ONE quire charter
class; storage/sidecar/projections fall out of field annotations; the ~70% DTO/coercer mass is
never authored. Bespoke compute lives in substrate packages we own and `import` directly.

Governing principle (already in propstore `CLAUDE.md`): **no adapters/coercers/mirror types
across package boundaries** — a boundary is an `import`; the package owns the canonical type;
generic packages are parameterized by arguments; crossing is a call returning the package's own
type. One spelling per thing, even across packages.

## 2. How to use this plan

- The unit of work is a **slice** (a phase). Each slice's exact capabilities + gating tests live
  in `scratchpad/inventory/FEATURE_INVENTORY.md` (the targeting contract, ~296 capabilities) and
  the per-file ledger `scratchpad/inventory/_coverage_final.txt` (all 583 tests classified).
- **PORT** = behavioral test → extract from the reference, must go green on the new tree.
  **DROP** = DTO-shape test → dies with the old layer, never ported.
- A slice is DONE when its PORT tests are green and its discipline gates pass. No slice ships on vibes.
- Hard rule: if an increment "needs" a coercer or a second spelling of a thing, the boundary is
  wrong — move it / delete the mirror, do not add the coercer.

## 3. Inputs (already produced)

- `scratchpad/inventory/FEATURE_INVENTORY.md` — ~296 capabilities × {surface, gating tests, PORT/DROP, slice, substrate} + full `pks` CLI tree.
- `scratchpad/inventory/_coverage_final.txt` — 583 tests classified CLAIMED|A(capability)|B(discipline-gate)|C(consume-pin)|D(remediation-crit)|E(workstream-meta)|F(drop). 0 unclassified.
- `scratchpad/decomposition/SPEC.md` — consume/extract/propstore-proper/vanish/dead map.
- `scratchpad/decomposition/DESIGN-projection-registry.md` — worked `Claim` charter + projection-kind design.

## 4. Foundations already in place

- **Recovery**: feature-peak preserved — branch `reference/feature-peak-20e55cca`, tag `ref/feature-peak-may16` (3702 green). Worktree at `scratchpad/wt-2b240dcb`.
- **quire** (`~/code/quire`, `master`): projection-kind registry + convergence cleanup, 462 tests green, dep bumps in. The storage/charter/projection substrate.
- **Substrates SHIPPED + pinned**: `provenance-semiring` (gh ctoth/…, 13380ece), `condition-ir` (gh ctoth/…, d12de46).
- **Substrates already CONSUME-pinned** in propstore pyproject: quire, cel-parser, ast-equiv, eq-equiv, human-to-sympy, formal-argumentation, assignment-selection, doxa, bridgman, gunray, formal-belief-set.
- **Principle** captured in propstore `CLAUDE.md` (commit 5d9361da).

## 5. Substrate ledger

- DONE (extracted+pinned): provenance-semiring, condition-ir.
- CONSUME (pinned, wire per slice): quire, cel-parser, ast-equiv, eq-equiv, human-to-sympy, formal-argumentation, assignment-selection, doxa, bridgman, gunray, formal-belief-set.
- EXTRACT (during consuming phase): `atms` (Phase 7, over provenance-semiring), `causal-models` (Phase 7, Pearl/Halpern), `calibration` (Phase 10, Guo metrics).
- STAY in propstore as small pure helpers (not packages): sympy-eval (`propagation.py`), named-uri (`uri.py`/`uri_authority.py`), unit-convert (`dimensions.py` pint layer).

## 6. Dead to delete (do not rebuild)

`families/{predicates,stances,merge,source_alignment,meta}` (pycache-only), `form_utils.py` (dup of
`families/forms/stages`), `merge/description_kinds.py` (re-export → real coreference is in
`core/lemon`), `world/__pycache__` orphans, `schema/` (LinkML — obsolete under charters; confirm),
20 of 21 `test_workstream_*_done.py` (inert markers; KEEP/fold `test_workstream_o_ast_done` into the
ast-equiv consume-pin). `adjudicate` workflow: never existed; not a feature.

## 7. Cross-cutting (every phase)

- **Discipline gates in CI from day 0**: the 19 `architecture/` + boundary/import-linter tests
  (ledger class B) + the substrate-boundary principle. Rot cannot regrow.
- **Test extraction process**: for the slice, copy its PORT tests from the reference, repoint
  imports to the new tree + substrate packages, drop DTO-shape assertions. The inventory names them.
- **No-test capabilities**: ~13 flagged with weak/no gating tests. Most actually have unclaimed
  tests (wire them: verify_cli, value_resolver, scope_policy, ic-postulate). Genuinely missing —
  WRITE tests first in-phase: concept-mutation CLI, semantic-pass framework, CompilationContext,
  repo discovery, recency/sample_size resolution, world check-consistency, embed agree/disagree,
  predicate extraction, opinion_sensitivity.

## 8. Phases

### Phase 0 — Cutover & scaffold (no features)
- Create `rewrite` off `master` (anchors CLAUDE.md + pins). Clean-slate commit: delete
  `propstore/**` (KEEP `propstore/_resources/`) + `tests/`; KEEP pyproject/uv.lock, CLAUDE.md,
  AGENTS.md, .gitignore/.python-version/.ward/.importlinter/.github, papers/, docs/, README.
- Package skeleton: `propstore/__init__.py`, the lazy CLI registry shell, `pks` entrypoint.
- Wire CI = discipline gates (port the class-B architecture tests first) + the boundary principle.
- Land `PLAN.md` (this doc).
- **Exit**: empty package imports; `pks --help` works; discipline-gate CI green.

### Phase 1 — Walking skeleton (`Concept`, thinnest end-to-end)
- One `Concept` charter (minimal fields) on quire; sidecar projection falls out.
- Minimal `pks init` + minimal build + `pks concept show` + `pks world status`.
- Extract the smallest Concept behavioral tests; green.
- **Exit**: one entity flows author→store→sidecar→query→render with core tests green. Architecture proven.

### Phase 2 — concept-core + forms/dimensions
- Full lemon model (entries/forms/senses, qualia, Dowty proto-roles, description-kinds, Allen
  temporal → condition-ir, Dung coreference → argumentation), forms + dimensions (consume bridgman;
  keep unit-convert helper), concept search (FTS) + embeddings surface, concept id minting, description generation.
- PORT: FEATURE_INVENTORY slice `concept-core` (24) + concept-form-lexical capabilities.
- **Exit**: concept-core PORT tests green.

### Phase 3 — claim + conditions
- `Claim` charter; wire `condition-ir` (CEL type-check, ConditionIR, Z3 sat/disjoint/definedness/
  TIMEPOINT, sql/python/estree backends); consume `eq-equiv` (delete in-tree equation_*) + `human-to-sympy`
  (delete sympy_generator); parameterization groups/walk; value comparison (unit-aware via dimensions).
- WRITE tests for: claim-validate workflow gaps if any. PORT: `claim` slice (28).
- **Exit**: claim PORT tests green; propstore has no direct z3 import.

### Phase 4 — context + grounding + defeasibility
- First-class `ist(c,p)` contexts (assumptions/params/perspective, no ancestry), authored lifting
  rules (LIFTED/BLOCKED/UNKNOWN, CEL-gated), predicate/rule (DeLP) declarations, datalog grounding
  (consume `gunray`, 4-section), CKR justifiable exceptions → Dung defeats. Fix `grounder.py:342-351` double-count.
- PORT: `context-grounding-defeasibility` slice (18).
- **Exit**: green.

### Phase 5 — argumentation-bridge + stances
- **PREREQ (Q, 2026-06-29): bump `formal-argumentation` to NEWEST.** Current pin `90dcbe29`;
  newest is `argumentation` `main` `5ea0c34` (Fix ABA ICCMA query sidecar detection) which is
  LOCAL-ONLY, 1 ahead of `origin/main` (`5fc78e3a`). Per no-local-path-pins: push `argumentation`
  main to origin FIRST, then pin propstore `formal-argumentation` to `5ea0c34`'s full sha. Build
  this slice against that bump.
- Also lands here (moved from Phase 4 per F4.1): CKR justifiable-exceptions → Dung-defeat ASPIC+
  integration + `test_defeasibility_aspic_integration` (needs CSAF).
- **`core/analyzers.py`** (the real Dung-AF + PrAF assembly — NOT the `argumentation.py` marker),
  aspic_bridge (claims/justifications/stances → argumentation kernel), praf, claim_graph delegators,
  source-trust calibration, stances/relations, preference heuristic, opinion (consume `doxa`; keep the
  thin provenance/honesty deltas — enforce_coh, metadata_strength_vector — propstore-side).
- PORT: `argumentation-bridge` slice (34, incl. the NEW core_analyzers/justifications/base_rates rows).
- **SPLIT 5a/5b (like Phase 7)** given size + the opinion→doxa migration that ripples through the slice.
  Map: `reports/scout-p5-map.md` (0.3.0 OLD→NEW import table §D, doxa API §C, opinion-mirror caveat §E).
  - **5a value/honesty layer:** consume `doxa.Opinion` DIRECTLY (delete the reference `opinion.py` mirror;
    no propstore Opinion/BetaEvidence second-spelling, no free-fn spellings — use doxa classmethods;
    provenance carried as a PAIRING beside the opinion, not baked into a re-spelled type). stances
    (`StanceType` + relation_analysis, all stances enter AF, no pre-render gate), preference heuristic
    (`MetadataStrengthVector`/`metadata_strength_vector`/`claim_strength`), calibration (temperature
    scaling Guo 2017, ECE, base-rate-is-Opinion). No ASPIC/PrAF kernel.
  - **5b argument-assembly layer:** core/analyzers (Dung-AF+PrAF assembly), aspic_bridge (build/translate/
    query/grounding/projection/lifting on `argumentation.structured.aspic.aspic`), praf engine
    (`enforce_coh`) + projection (`argumentation.probabilistic.probabilistic` — NOT the package root),
    claim_graph delegators, source-trust projection, CKR justifiable-exceptions → Dung-defeat (CSAF).
  - **DONE 5a `1bc1ace3`; 5b `8e9a10a8`+`bbe56d71`.** 5b landed the ASPIC+ kernel bridge + PrAF value
    layer + source-trust + CKR (empty-bundle). It DEFERRED the store→AF *assembly* to Phase 6/7 (see
    next): the reference analyzers build over `conflict_detector` (Phase 6) + `world.types`/active-graph
    (Phase 7), which do not exist yet — building them now needs phantom infra / a parallel mirror.
- **Exit**: green.

### Phase 6 — merge-conflict + relations  (+ the store→AF assembly moved from 5b)
- conflict_detector (Z3 disjointness via condition-ir, eq-equiv, ast-equiv, value/param conflict),
  merge framework (Dung-backed via argumentation, partial-AF sum/max/leximax), merge-claim coreference,
  two-parent merge commit (quire), relations/sameas, concept alignment (vocab reconciliation via PAF).
- **MOVED FROM 5b (build here where conflict_detector + the active claim graph exist):** core/analyzers.py
  (Dung-AF + PrAF assembly over the active claim graph), claim_graph.py, praf.build_praf,
  aspic_bridge/projection.py (csaf_to_projection → StructuredProjection), and the gunray-inspection →
  ASPIC+ `GroundedDatalogTheory` seam for NON-empty bundles (currently `NotImplementedError` + HIGH gap
  docs/gaps.md:18). Tests: test_core_analyzers, test_praf_integration, test_praf_uncalibrated_explicit,
  test_aspic_bridge_grounded, test_core_justifications, the lifting/projection/Label subset of
  test_ws_f_aspic_bridge (the active-graph parts may slip to Phase 7). See docs/rewrite/deferred-tests.md.
- **SPLIT 6a→6d (dependency-ordered, serial), per scout map `reports/scout-p6-map.md`. Prereqs confirmed:**
  condition-ir ConditionSolver has are_equivalent_result/are_disjoint_result/Solver{Sat,Unsat,Unknown}/
  synthetic_category_concept/with_synthetic_concepts/ConceptInfo; ast-equiv has compare/ComparisonResult/
  Tier; argumentation 0.3.0 af_merging (sum/max/leximax MOVED out of partial_af), partial_af, and
  datalog_grounding.grounding_inspection_to_aspic → GroundedDatalogTheory all resolve.
  - **6a keystone:** core/{reasoning,results,labels}.py prereqs (canonical enums/value types; Phase 7
    world.types re-exports reasoning) + the `conflict_detector/` package + condition_classifier — Z3
    disjointness via condition-ir ConditionSolver, equation conflict via eq-equiv (propstore.claim_equations),
    AST via ast-equiv compare, value/param via value_comparison+dimensions, context φ-node via context_lifting.
  - **6b moved-assembly:** the Phase-6 portion of core/analyzers.py (AF/BAF/PrAF math RE-PARAMETERIZED over
    plain (claims_by_id, stance_rows, conflict_rows, active_ids); SharedAnalyzerInput WITHOUT active_graph),
    analyze_aspic_backend/analyze_claim_graph/build_praf_from_shared_input/analyze_praf, structured_projection.py,
    aspic_bridge/projection.py (csaf_to_projection→StructuredProjection; Label.empty()/None), and the
    gunray-inspection→ASPIC+ grounding-seam fill in aspic_bridge/grounding.py (closes docs/gaps.md:18).
  - **6c merge (MATH only; commit→9):** merge/ package merge MATH over PLAIN claim inputs — merge_classifier
    build_merge_framework over partial_af, IntegrityConstraint (merge-side), structured_merge sum/max/leximax
    via af_merging (per-branch CSAF→csaf_to_projection→framework, store-free), merge_claims coreference,
    merge_report. Depends on 6a (conflict_detector) + 6b (structured_projection/csaf_to_projection).
    **DEFERRED to Phase 9** (needs the Repository/snapshot facade + family registry that don't exist yet —
    quire GitStore has commit_flat_tree/commit_parent_shas but no propstore Repository binds git+families):
    two-parent `merge_commit` + MergeManifest family materialization; tests test_repo_merge_object,
    test_merge_cli, test_merge_symmetry_non_claim_files. (Same re-parameterize-now / defer-store pattern as 6b.)
  - **6d relations/alignment/sameas:** source/alignment.py (PAF over candidate proposals via partial_af;
    classify_relation via lemon identity not Jaccard; proposal-only) + sameas family. families/relations.py +
    probabilistic_relations.py already exist — consume.
- PORT: `merge-conflict` slice (27). Closes M3 IntegrityConstraint (test_ic_postulate_coverage).
- NOTE: belief-set/worldline IC-merge tests (test_ic_postulate_coverage, test_*ic_merge*, assignment_selection_
  merge) are the model-theoretic IC merge (layer 4) → Phase 7+, distinct from the merge-side IntegrityConstraint.
- **Exit**: green.

### Phase 7 — world + ATMS + worldline + belief-revision  (LARGEST — may split 7a/7b)
- 7a world/atms/worldline: world query + render policy + resolution strategies (recency/sample_size/
  argumentation/override/assignment_selection — WRITE tests for recency/sample_size), **carve `atms`
  package** (over provenance-semiring; node-builders dissolve into charter `atms-*` annotations,
  compute moves to kind emit()/engine), **carve `causal-models`** (Pearl do/Halpern), worldline
  hypothetical reasoning + capture, observatory.
- 7b belief-revision: support_revision adapter over `belief-set` (AGM/iterated/entrenchment/IC-merge),
  fragility/sensitivity (sympy-eval helper), epistemic process, policies.
- PORT: `world-atms-worldline` (40) + `belief-revision` (40).
- **Exit**: green; `atms` + `causal-models` shipped+pinned.

### Phase 8 — source + proposals + provenance + micropubs
- Source-branch lifecycle (init/add/finalize/promote, reference lowering, reserved-ns guard),
  proposal artifacts + promotion, provenance named-graph carrier (over `provenance-semiring`, on
  quire.notes — carrier stays propstore), PROV-O export, micropublications (Clark), identity
  (content-id/ni-URI; keep named-uri helper), import contract + repository import.
- PORT: `source-proposals-provenance` slice (35). WRITE test for verify_claim_tree if still unwired.
- **Exit**: green.

### Phase 9 — storage-build-compile (genuine orchestration)
- Repository facade/discovery, family registry + FK graph (now charter-derived), semantic-pass
  framework (AUTHORED→CHECKED; WRITE framework test), derived_build orchestration + rebuild-on-change
  content hashing, compiler validate/build workflows, contract manifest/versioning, diagnostics +
  authoring lints, artifact codes + verification, history/materialize. (Much grows incrementally in
  earlier phases; this completes it.)
- PORT: `storage-build-compile` slice (26) + remediation crits (class D) + discipline gates (class B).
- **Exit**: green; full build pipeline runs end-to-end.

### Phase 10 — render + cli + web + heuristic-embeddings
- Full render policy/views (per-field state + NL sentences), complete `pks` CLI tree, web UI routes,
  embeddings (quire vec adapter; embed text projection), similarity/agree-disagree (WRITE test for
  agree/disagree), LLM stance classify + relate (honest-ignorance), **extract `calibration`** (metrics
  half; CorpusCalibrator/categorical→opinion stay propstore over doxa), graph export.
- PORT: `render-cli-web` (22) + `heuristic-embeddings` (14).
- **Exit**: green; full `pks` tree works.

## 9. Completion & cutover

Done when: all ~225 PORT capabilities green on the new tree + all discipline gates green + full `pks`
CLI tree functional + remediation crits (D) green. Then flip `master` to `rewrite` (tag the old broken
master `archive/broken-master-<sha>` first). The reference branch/tag stay as historical spec.

## 10. Tracking

Each FEATURE_INVENTORY capability gets a status: todo / in-progress / green. A slice's exit gate is
all its PORT capabilities green. Track per-phase test counts vs the reference's per-slice counts.

## 11. Open decisions / risks

- `schema/` (LinkML) obsolete under charters — confirm before deleting.
- workstream-meta: drop 20, keep 1 (your call — recorded).
- Phase 7 is large; likely split 7a/7b.
- atms carve is the hardest single piece (generic engine vs propstore node-builder; semiring + carrier
  + assumption/context-kind seams) — do it WITH the world layer, not standalone, so node-builders dissolve.
- No-test capabilities: write tests before rebuilding (don't rebuild blind).
- Sequencing assumes bottom-up entity deps; if a later slice reveals an earlier charter needs a field,
  amend the charter (single source) — never add a parallel type.

## 12. ZEN HARDENING v2 — BINDING (applied after the 5-reviewer adversarial review)

These directives SUPERSEDE any conflicting phase text above. Sourced from reports/rewrite-zen-{A..E}.md
(consolidated in notes-foreman-zen-review.md). The 5 decisions below are all CONFIRMED.

### 12.0 Decisions (confirmed)
1. opinion/doxa provenance → carried OUT-OF-BAND via the git-note carrier (`refs/notes/provenance`). `doxa.Opinion`
   is the ONE imported type, unmodified. NO propstore `Opinion` subtype, NO method→function shim. (Z3)
2. atms id-brand → the engine is GENERIC over an opaque atom-id type param. NO shared id package; the kernel
   imports nothing from `propstore.core.*`. (Z3/Z4)
3. provenance carrier is pulled forward to land NO LATER than Phase 5.
4. Phase 7 is SPLIT: 7a-atms → 7a-causal → 7a-world → 7b-belief.
5. A standing BEHAVIORAL Z1 quarantine gate runs in CI from day 0 (see 12.1).

### 12.1 Standing gates (CI from day 0 — the structural import-linter gates CANNOT catch a behavioral Z1 regression)
- **Quality gate (EVERY slice, hard exit condition — no slice ships otherwise):** STRICT TYPES EVERYWHERE.
  `[tool.pyright]` in propstore/pyproject.toml is `typeCheckingMode = "strict"` (NOT "basic"); `uv run pyright propstore` = 0
  errors / 0 warnings under strict; `uv run ruff check` clean; `uv run pytest tests/ -q` all green. Strict means: no implicit
  `Any`, every function fully annotated (params + return), no untyped defs, no `# type: ignore` / `# pyright: ignore` / `cast(...)`
  to silence a real error, no `Any`-widening to dodge a type. Fix the type, not the checker. A slice with a strict-pyright error is
  NOT done.
- **Z1 quarantine gate (NEW, top priority):** feed deliberately-invalid concept/claim/form/stance → assert each
  appears as a `build_status='blocked'` quarantined sidecar row + a diagnostics row, ZERO dropped, and render-policy
  is the thing that hides it. Port the quarantine behavioral corpus (remediation `T2_2*`, the FI quarantine caps) as
  the semantic-pass framework's ACCEPTANCE test — not a self-authored one.
- **Cross-cutting non-commitment invariant (state once, gate per slice):** NO resolved value / winner / extension /
  acceptance / verdict is EVER written to storage. Build only QUARANTINES-WITH-PROVENANCE; it never filters/aborts/drops.
  Resolution is render-only. Every slice that writes storage gets a store-write boundary test asserting this.
- **z3 containment:** the gate is "no `z3` import outside the condition-ir consumption surface" (permanent import-linter
  rule, all phases) — route assignment-selection IntegrityConstraint + parameterization-Z3-strictness through condition-ir.
- **CLI discipline tests are class-B**, ported in Phase 0, so every CLI command (incl. `pks build`) is born under Z6.

### 12.2 Contract-wording fixes (inventory + plan) — do BEFORE building
- FEATURE_INVENTORY: the claim-quarantine capability wording "invalid never reaches sidecar" INVERTS non-commitment
  (reference removed that build abort; invalid lands as blocked stub row + diagnostics, render filters). Reword →
  "blocked stub row in claim_core + build_diagnostics; render filters"; PORT test asserts the stub row EXISTS (positive).
  AUDIT every inventory line phrased "never reaches"/"reject"/"blocks/filter" for the same inversion.
- DROP re-audit (irreversible — DROP is never ported): default-PORT any test named diverge/version/roundtrip/dedupe/
  collapse/quarantine until proven pure-shape. Known: `test_codex2_claim_dedupe_diverges_on_version` (marked DROP) asserts
  versions DON'T collapse = the core principle → PORT it.
- Coverage exit gate = CAPABILITY-COVERAGE DIFF vs the reference per-slice count (promote §10 tracker to a GATE), NOT
  "PORT tests green". For every hybrid PORT+DROP file, write the PORT-half assertion BEFORE the file's DROP-half is discarded.

### 12.3 One-canonical-type / delete-re-exports (Z3)
- RULE: any propstore symbol whose body is `return <pkg>.<same_name>(...)` is DELETED, callers call the package directly.
  Verified instance: `propstore.dimensions.dims_signature` (re-export of `bridgman.dims_signature`) — delete; "keep the
  unit-convert helper" means ONLY the Pint code bridgman lacks (normalize_to_si/from_si, UnitConversion, affine/log/delta).
- DELETE `argumentation.py` (2-line marker; anchor the import-linter on `core/analyzers`, the REAL Dung-AF/PrAF assembly).
- DELETE `merge/description_kinds.py` (re-export; coreference lives only in `core/lemon`, Phase 2).
- `ConflictClaim`/`MergeClaim` are field-subset VIEWS over the one `Claim` charter — NO independent storage, NO
  coerce/`to_payload`/`from_payload` roundtrip.
- condition-ir OWNS its registry-input type (the `ConceptInfo` role); propstore lowers `ConceptRecord` → it ONCE at the
  call site; no propstore `ConceptInfo` mirror. Verify `core/assertions.ConditionRef` is not a second spelling.
- eq-equiv is parameterized by PRIMITIVES (equation text + symbol bindings); the conflict detector passes `Claim` fields
  straight in; the adapter CALLS `eq-equiv.equation_signature`, never recomputes it.
- `calibration` extract: CorpusCalibrator/categorical→opinion (staying propstore) IMPORT the package's metric types
  directly — no propstore re-spelling of TemperatureScaler/ECE/Brier. `families/embeddings` crosses the quire-vec
  boundary by call-through returning quire's vec type — no propstore Embedding row mirror.
- "wire the substrate" is a real VERIFY step: eq-equiv/doxa CONSUMEs are currently UNPROVEN (nothing imports them yet).
  Reconcile the eq-equiv pin contradiction (PLAN §4 "pinned" vs SPEC "unpinned") before Phase 3.

### 12.4 Honest ignorance (Z2)
- The `view` projection kind MUST have a distinct `unknown` state (≠ blocked ≠ missing). LIFTED/EXCEPTED/solver-UNKNOWN
  route to it. Render test asserts unknown ≠ blocked ≠ missing.
- The `opinion` kind maps absent fields → a VACUOUS opinion (u=1), never a defaulted scalar.
- provenance is NEVER part of concept/claim IDENTITY (identity hash excludes it from commit 1, not Phase 8).
- Phase exits NAME their honest-ignorance gates (e.g. praf_uncalibrated_explicit, raw_confidence_not_dogmatic,
  defeat_summary_no_fabrication, explicit-base-rate), never a generic "green".

### 12.5 Phase 7 (atms) — re-scoped (replaces the §8 Phase 7 bullet + the §11 "do it WITH the world layer" note)
Split, in order, each gated independently:
- **7a-atms**: extract the `atms` engine over `provenance-semiring` + `condition-ir` (route `CelExpr` through condition-ir;
  the kernel imports NO `propstore.cel_types`/`core.id_types`). Engine generic over an opaque atom-id; COLLAPSE the
  two-tuple `EnvironmentKey` (assumption_ids + context_ids) + the `ps:source:assumption:`/`context:` prefix scheme into a
  propstore-side adapter (a generic ATMS has assumptions only; the context axis is propstore's `ist(c,p)`). DEFINE the
  package's OWN input types (parameterization/condition/conflict); propstore lowers charters into them one-direction.
  GATE: the reference's atms-specific PORT tests green against the PACKAGE ALONE (proves it's generic, not propstore-with-steps).
- **7a-causal**: extract `causal-models` (scm+intervention+actual_cause) generic over a variable→equation map. Independent of atms.
- **7a-world**: world render/resolution/queries/worldline CONSUME both packages; HERE the node-builders dissolve into the
  charter (kills the `ClaimNode→ActiveClaim→ATMSClaimNode` chain). CORRECTION to §8: the ATMS COMPUTE (Z3-equivalence,
  cartesian-product justification, sympy formula eval, the fixpoint/nogood loop) stays in the owner-layer ENGINE consuming
  the charter via a compiler — it does NOT move into a projection-kind `emit()`. ("compute moves to kind emit()" is struck.)
  Resolution strategies (recency/sample_size/argumentation/override) are render-time — WRITE recency/sample_size tests that
  assert selection happens at render over the full label set, never baked at build.
- **7b-belief**: PROVE `support_revision` DELEGATES revision/contraction to belief-set (no local reimplementation — the
  Hansson-paid-but-unused surface is the `assignment_selection_merge` duplicate-engine trap). Lower claims into belief-set's
  formula alphabet via one binding (promote "belief-formula-alphabet" to a defined kind). Assert revision capture does not
  mutate the source branch.

### 12.6 Other binding fixes
- Phase 4: CKR-exception-defeats capability + `test_defeasibility_aspic_integration` depend on the Phase-5 CSAF → MOVE that
  capability+test to Phase 5 (or pull a minimal CSAF into Phase 4). Mark the cross-phase test dependency in the inventory.
- Phase 8 promotion: trust calibration only STAMPS a `calibrated`-provenance opinion; it NEVER gates the promote/block
  decision. Blocked items quarantine (rows + diagnostics), never drop. Concept-alignment promote RECORDS a sameas/supersession
  relation with provenance and KEEPS both lemon entries addressable (never deletes the rival). Collapse the `_CONTEXT` and
  `_URI_PREFIXES` duplicate definitions before porting their consumers.
- Phase 9: `pks build` and `pks validate` share ONE pass framework + ONE set of checks; they differ ONLY in terminal sink
  (sidecar write vs none). Neither re-implements validation (no dual-path). Prove charter→FK derivation on the two hardest
  families (lemon, micropublications) as a Phase-0/1 spike, OR gate "no FK-spec literal outside a charter annotation".
  RESOLVE the backward layer dep: `artifact_verification` imports `world.WorldQuery`/`core.labels` (storage reaching up) —
  relocate claim-tree verification above world, or move the ATMS-label walk into world and call down to a serialized result.
- GHOST CHECK: the cited `grounder.py:342-351` "double-count" may not be real (it sums each rule kind once) — REPRODUCE with
  a failing test BEFORE changing the code, or drop the "fix".
- Plan §3 input-path fix: `DESIGN-projection-registry.md` is at `scratchpad/projection-audit/`, not `decomposition/`.
- Phase 1 demonstrates charter→projection on `Concept` as the first proof (the DTO-vanishes thesis must be SHOWN, not asserted);
  the skeleton stores the RAW authored form (no baked normalization) and its render step exercises a real RenderPolicy filter
  (asserts something present-in-storage-but-filtered-at-render).
