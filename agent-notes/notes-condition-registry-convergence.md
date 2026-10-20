# Condition Registry Cleanup Refactor Fixed-Point Log - 2026-07-21

Target architecture:
- `Concept` remains the canonical stored data object.
- `ConceptCheckPass` owns canonical CEL-symbol validation, form resolution, category consistency, and the canonical-name-keyed condition-ir registry.
- `CompilationContext`, world, and source workflows consume checked owner output or condition-ir directly at their true boundary.
- No Propstore registry adapter/builder module survives.

Forbidden surfaces:
- `propstore/cel_registry.py`
- `concept_kind`, `concept_info_from_concept`, `build_canonical_cel_registry`
- `claim_conditions.lower_concept`, `claim_conditions.condition_registry`
- id-keyed condition registry construction
- missing/dangling form fallback to `KindType.CATEGORY`
- condition semantics read from `FormDefinition.parameters`
- `canonical_name=seed.name`
- flat promoted concepts that drop form/category semantics
- same-shaped replacement registry helpers or dual paths

Search gates:
- `rg -n 'propstore\.cel_registry|build_canonical_cel_registry|concept_info_from_concept|concept_kind|lower_concept' propstore tests`
- `rg -n 'cc\.condition_registry|claim_conditions\.condition_registry|from propstore\.claim_conditions import condition_registry' propstore tests`
- `rg -n '\{info\.id: info|registry\[info\.id\]' propstore tests`
- `rg -n 'parameters\.get\("extensible"\)|parameters\.get\("values"\)' propstore tests`
- `rg -n 'defaults? to .*CATEGORY|dangling.*CATEGORY|missing.*CATEGORY' propstore tests`
- `rg -n 'build_compilation_context_from_loaded|build_authored_concept_registry' propstore tests`

Runtime gates:
- Logged per-slice pytest commands in `plans/condition-registry-convergence-2026-07-21.md`
- `uv run pyright propstore`
- `uv run lint-imports`
- changed-path Ruff per slice
- final focused and full logged pytest suites

## Iteration 0 - plan activation

Slice read:
- `plans/condition-registry-convergence-2026-07-21.md`
- `protocols:cleanup-refactor`

Surfaces:
- execution plan
  - Disposition: keep
  - Owner after cleanup: `plans/condition-registry-convergence-2026-07-21.md`
  - Action: created and committed the execution control surface alone.
  - Evidence: commit `0c929c31 docs(conditions): plan condition registry convergence`.
- plan heading trailing whitespace
  - Disposition: rewrite
  - Owner after cleanup: same plan file
  - Action: removed two Markdown hard-break suffixes after `git diff --cached --check` exposed them and amended the activation commit before Slice 1.
  - Evidence: amended commit `0c929c31`.

Gate results:
- Pass: all 26 plan-named paths existed during planning.
- Pass: focused planning baseline, 57 tests.
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: `uv run lint-imports`, 3 contracts kept.
- Known unrelated baseline: full Ruff reports 53 F401 failures outside this workstream; changed-path Ruff is the plan authority.
- Initial commit command did not stop when `git diff --cached --check` reported whitespace because the shell command sequence used separators. The whitespace is being corrected and the commit amended before any source work.

Git state:
- Branch: `master`.
- Plan activation commit: `0c929c31`.
- Pre-existing unrelated untracked path: `pyghidra_mcp_projects/`; preserve untouched.
- This notes file must remain uncommitted.

Blocker:
- None.

Next slice:
- Reread the plan, then execute Slice 1: canonical CEL-symbol contract.

## Iteration 1 - Slice 1 canonical CEL-symbol contract

Surfaces changed:
- `propstore/app/project_init.py`: project seeds now put `seed.ref` in
  `Concept.canonical_name`; the display phrase remains lexical data.
- `propstore/families/concepts_passes.py`: the concept pass validates authored
  names through direct `cel_parser.parse`/`Ident` use and rejects duplicate
  canonical names.
- `propstore/source/concepts.py`: source proposal normalization rejects a
  `proposed_name` that is not exactly one CEL identifier.
- focused fixtures/tests: display phrases moved to lexical forms; identity,
  symbol, and display-form separation plus invalid/duplicate-name behavior are
  covered.

Broken dependency-edge classifications:
- `test_concept_view_known` expected the old display phrase in
  `canonical_name`: valid concept-view capability with the wrong
  representation. Disposition: assert the canonical CEL symbol.
- `test_concept_view_resolves_by_name` queried the deleted display-name
  representation: valid capability with the wrong representation.
  Disposition: use a dedicated concept whose URI id differs from its canonical
  CEL symbol so the test still proves name lookup.
- The first dedicated-concept setup omitted the required reference argument to
  `BoundFamily.save`: valid test fixture using its true owner incorrectly.
  Disposition: call the existing family API with the explicit reference,
  document, and commit message.

Gate results so far:
- Pass: changed-path Ruff before the concept-view repair.
- Fail: logged Slice 1 run had 53 passes and 2 old-representation expectation
  failures; log
  `logs/test-runs/condition-registry-s1-20260721-152513.log`.
- Fail: next logged Slice 1 run had 54 passes and one fixture setup failure;
  log `logs/test-runs/condition-registry-s1-20260721-152702.log`.
- Pass: corrected logged Slice 1 gate, 55 tests; log
  `logs/test-runs/condition-registry-s1-20260721-152804.log`.
- Pass: exact Slice 1 changed-path Ruff gate.
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: search for `canonical_name=seed.name` has zero hits.
- Pass: `git diff --check`.

Blocker:
- None.

Commit:
- `35b18e88 refactor(concepts): make canonical names CEL symbols`

Next action:
- Verify the post-commit Git state, reread the plan, and begin Slice 2 with its
  first unchecked item.

## Iteration 2 - Slice 2 preserve promoted concept semantics

Surfaces changed so far:
- `propstore/families/concepts.py`: added canonical typed category values and
  openness; bumped the concept charter contract version to `2026.07.21`.
- `propstore/source/promote.py`: deleted the flat minted-Concept construction
  and directly constructs the canonical lemon entry, self-owned sense
  reference, authored form link, and category metadata.
- `tests/test_source_promote_p83b.py`: added closed-category and quantity
  proposal -> promotion -> canonical reload proof.
- `tests/test_concept_skeleton.py`: asserted the canonical fields and absence
  of source-local proposal fields in the Concept charter.
- Regenerated the checked-in manifest with
  `uv run pks contract-manifest --write`.

First gate result:
- Fail: 77 passed, 12 failed; log
  `logs/test-runs/condition-registry-s2-20260721-153244.log`.
- Pass after classified repairs: 89 tests; log
  `logs/test-runs/condition-registry-s2-20260721-153432.log`.
- Pass after final direct-form and stale-description cleanup: 89 tests; log
  `logs/test-runs/condition-registry-s2-20260721-153645.log`.
- Pass: corrected exact changed-path Ruff gate, including
  `propstore/families/registry.py`.
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: final rerun of changed-path Ruff and package Pyright after the last
  production edit.
- Pass: regenerated manifest is current and its HEAD compatibility gate accepts
  the concept and family-registry version bumps.
- Pass: `git diff --check` and the stale flat-promotion wording search has zero
  hits.

Broken dependency-edge classifications:
- Sidecar tuple binding failures: valid canonical category capability with the
  wrong storage representation annotation. Disposition: keep the typed tuple
  on `Concept` and mark that charter field JSON-backed.
- Existing promotion tests authored `dimensionless` while their master form
  registry was empty: dead/old fixture assumption exposed because the old flat
  promotion dropped the form link. Disposition: make the existing promotion
  fixture own the `dimensionless` `FormDefinition` it authors.
- `family-registry:propstore` manifest drift failure: valid contract capability
  in its already-owned registry owner. The plan omitted
  `propstore/families/registry.py`, but a concept-charter body change also
  changes the derived family-registry body. Disposition: correct the plan's
  active boundary and bump
  `PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION` from `2026.07.21.1` to
  `2026.07.21.2` before regenerating the manifest again.

Blocker:
- None; the failed gate gives an exact owner and versioned correction.

Commit:
- `faa6851e refactor(source): preserve promoted concept semantics`

Next action:
- Verify the post-commit Git state, reread the plan, and begin Slice 3's atomic
  registry-owner cutover.

## Iteration 3 - Slice 3 atomic checked-owner cutover

Deleted old surfaces:
- `propstore/cel_registry.py` deleted in full.
- `lower_concept` and `condition_registry` deleted from
  `propstore/claim_conditions.py`.
- `tests/test_cel_registry.py` deleted as the obsolete module contract.

Owner work completed so far:
- `ConceptCheckedRegistry` now carries condition-ir's own
  canonical-name-keyed `ConceptInfo` mapping.
- `ConceptCheckPass` resolves only explicit existing forms, omits missing and
  dangling forms, carries typed category metadata, and rejects category
  metadata attached to non-category forms.
- `CompilationContext.cel_registry` was renamed to `condition_registry`.
- `build_authored_concept_registry` and
  `build_compilation_context_from_loaded` were deleted.
- The valid replacement owner API consumes `ConceptCheckedRegistry`; compiler
  workflows pass `concept_result.output` directly.
- Claim passes and derived conflict compilation consume the renamed context
  field.
- Source promotion revalidation now runs the concept pass before constructing
  compilation context and running the claim pass.

Broken dependency-edge classifications completed:
- Compiler context rebuilt a registry from loaded concepts: already-owned
  capability that must use the checked concept owner directly. Disposition:
  consume `ConceptCheckedRegistry`.
- Compiler workflows passed pre-check loaded concepts: valid capability with
  the wrong representation. Disposition: pass `concept_result.output`.
- Source promotion claim revalidation rebuilt from loaded concepts: valid
  capability with the wrong representation. Disposition: run the concept pass,
  then consume its checked output.
- Claim pass and derived build read the old context field name: valid
  capability with the wrong owner-facing name. Disposition: read
  `condition_registry`.

Current state:
- Slice 3 remains one uncommitted atomic source slice as required.
- No runtime, typing, lint, or search gate has been run yet because production
  caller cutover is incomplete.

Blocker:
- None.

Next action:
- Finish `propstore/source/claims.py`: delete its old lowering/registry path,
  run the canonical concept pass for primary concepts, and add source-local
  `ConceptInfo` values directly under proposed/local CEL names. Then update the
  world solver and classify the remaining test/import fallout.

### Iteration 3 checkpoint 2

Additional owner work completed:
- `propstore/source/claims.py` no longer imports the deleted claim-layer
  lowering/registry functions. Primary concepts run through
  `ConceptCheckPass`; source-local proposal documents construct condition-ir's
  `ConceptInfo` directly and are keyed under proposed/local names without
  converting them to canonical `Concept` objects.
- `WorldQuery.condition_solver()` runs the canonical concept pass over sidecar
  concepts/forms and passes its checked registry to condition-ir's
  `with_standard_synthetic_bindings` directly.
- Claim-condition, context-lifting, defeasibility, and sidecar-context tests now
  construct condition-ir registries directly at their package boundary; the
  deleted Propstore registry functions are not recreated.
- Compilation-context tests now prove consumption of checked concept output and
  canonical-name lookup with a stable concept URI.
- Concept-pass owner tests now cover missing-form omission, stable-id lowering,
  URI rejection as CEL source, explicit closed-category projection, and
  rejection of category metadata on a quantity form.

Additional dependency-edge classifications:
- Source claim validation manually lowered primary `Concept` values: already-
  owned capability. Disposition: consume `ConceptCheckedRegistry`, then add only
  source-local `ConceptInfo` at the source boundary.
- World solver imported the deleted generic builder: already-owned capability.
  Disposition: run `ConceptCheckPass` and call condition-ir's synthetic-binding
  API directly.
- Tests of `claim_conditions.condition_registry`/`lower_concept`: obsolete
  old-surface contracts or direct condition-ir fixtures. Disposition: delete
  the lowering contract and use package-native `ConceptInfo` mappings.
- Compilation-context tests of loaded-concept rebuilding: wrong
  representation. Disposition: run the concept pass and pass checked output.

Current state:
- The atomic cutover is still uncommitted and caller repair is incomplete.
- No gate has been run yet.

Blocker:
- None.

Next action:
- Finish owner tests for dangling-form omission and replace the remaining
  `build_compilation_context_from_loaded` test callers, then run the forbidden
  searches to expose the next dependency edges.

### Iteration 3 checkpoint 3

Focused gate history:
- Fail: 152 passed, 5 test-fixture failures; log
  `logs/test-runs/condition-registry-s3-20260721-154903.log`.
- Fail: 153 passed, 4 lexical-sense invariant fixture failures; log
  `logs/test-runs/condition-registry-s3-20260721-154950.log`.
- Pass: 157 tests; log
  `logs/test-runs/condition-registry-s3-20260721-155031.log`.

Focused failure classifications:
- New lexical-entry test fixtures omitted the required `senses` input, then
  used an empty tuple that violates the at-least-one-sense invariant: valid
  owner tests with incorrect canonical fixture construction. Disposition: add
  a self-owned `LexicalSense(OntologyReference(uri=concept_id))`.
- `check_cel_expression` clean-result assertion expected a tuple while the
  package returns a list: valid proof with the wrong package carrier
  expectation. Disposition: assert the result is empty without imposing a
  container type.

Current gate results:
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: `uv run lint-imports`, 3 contracts kept.
- Pass: Ruff over all 15 changed surviving Python files.
- Pass: all six Slice 3 forbidden searches, each with zero hits.

Current state:
- Required proofs 1-7 are explicit in concept-pass owner tests.
- Compiler, promotion, and world paths all consume the checked metadata, but
  the plan's proof 8 still needs one explicit same-concept comparison across
  compiler and world plus source-local category validation evidence.

Blocker:
- None.

Next action:
- Add the remaining cross-workflow metadata proof without adding a production
  helper, rerun the affected logged focused suite and all Slice 3 gates, then
  review the exact atomic diff.

### Iteration 3 checkpoint 4

Additional evidence and repair:
- Pass: 158 tests after adding the explicit compiler/world metadata identity
  proof; log `logs/test-runs/condition-registry-s3-20260721-155357.log`.
- Exact diff review found that `_revalidate_promoted_claims` returned before
  running `ConceptCheckPass` when a source had no promoted claims. This was an
  invalid structural-concept promotion bypass: concept-only sources could
  promote category metadata on non-category forms without owner validation.
- Disposition: run `ConceptCheckPass` before the empty-claims return and reject
  promotion when that owner pass fails. Added a concept-only promotion proof
  using category values on the `dimensionless` quantity form.

Current state:
- The final Slice 3 focused logged gate was started after that repair. Its live
  execution cell expired during context compaction, so the result must be read
  from the wrapper's authoritative `logs/test-runs` record.
- `scripts/run_logged_pytest.py` confirms logs are written to
  `logs/test-runs/<label>-<timestamp>.log`.
- The atomic Slice 3 cutover remains uncommitted. No subsequent slice has
  started.

Blocker:
- None. The live tool cell is unavailable, but its durable test log is the
  intended result record.

Next action:
- Locate the newest `logs/test-runs/condition-registry-s3-*.log`, inspect its
  final summary, and, if passing, rerun the Slice 3 static/search gates before
  staging and committing the exact slice.

### Iteration 3 checkpoint 5

Final pre-commit evidence:
- Pass: 159 tests in 13.65 seconds; log
  `logs/test-runs/condition-registry-s3-20260721-155647.log`.
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: `uv run lint-imports`, 3 contracts kept.
- Pass: Ruff over all 17 surviving changed Python paths.
- Pass: all six exact Slice 3 forbidden-surface searches, each with zero hits.
- Pass: `git diff --check`.
- The tracked diff is exactly the recorded 19-path Slice 3 boundary: 17
  modified surviving files plus deletion of `propstore/cel_registry.py` and
  `tests/test_cel_registry.py`.
- The only unrelated untracked status is the pre-existing
  `pyghidra_mcp_projects/`, which remains untouched.

Current state:
- Slice 3 is fully gated and remains uncommitted only long enough to inspect the
  staged boundary and create its required commit.

Blocker:
- None.

Next action:
- Stage only the exact 19 recorded Slice 3 paths, inspect the staged name/status
  and cached patch integrity, then commit as
  `refactor(conditions): derive registries from checked concepts`.

### Iteration 3 commit

- Kept commit: `f68d2209 refactor(conditions): derive registries from checked concepts`.
- Commit boundary: exactly the 19 recorded Slice 3 paths; the old registry
  module and its obsolete module-contract test were deleted.

Next action:
- Verify tracked state is clean, reread Slice 4, and begin its first unchecked
  item by rerunning every search gate from Slices 1 and 3.

## Iteration 4 - Fixed-point closeout

Committed kept slices:
- `35b18e88 refactor(concepts): make canonical names CEL symbols`
- `faa6851e refactor(source): preserve promoted concept semantics`
- `f68d2209 refactor(conditions): derive registries from checked concepts`

Closeout evidence:
- The Slice 1 search for `canonical_name=seed.name` has zero hits.
- All six Slice 3 forbidden-surface searches have zero hits.
- Exact residual hits across all seven prior search gates: none.
- Added dated registry-ownership supersession notes without rewriting history
  to:
  - `plans/cel-registry-hardening-workstream-2026-04-14.md`
  - `plans/cel-subsystem-unification-plan-2026-04-08.md`
  - `plans/cel-typed-expression-workstream-2026-04-16.md`
  - `plans/concept-canonical-typing-workstream-2026-04-09.md`
- Updated the active plan's completed Slice 1-3 checkboxes and results, and its
  completed Slice 4 record items. Its status explicitly says the final
  convergence gates are pending.

Current state:
- Slice 4 contains only the five named plan records. It is uncommitted pending
  final diff/status inspection and its required record commit.
- Tracked source state was clean before the record edits. The unrelated
  pre-existing `pyghidra_mcp_projects/` remains untouched.

Blocker:
- None.

Next action:
- Complete the active plan's fixed-point-record checkbox, inspect and commit
  only the five plan files as
  `docs(conditions): close obsolete registry workstreams`, then run the final
  convergence gates in their prescribed order.

### Iteration 4 commit

- Kept commit: `e47f22ae docs(conditions): close obsolete registry workstreams`.
- Commit boundary: exactly the active convergence plan and the four named
  historical plan records.

Next action:
- Run the final focused logged suite, then package Pyright, import-linter, full
  logged suite, and union-of-changed-Python-paths Ruff in the exact plan order.

## Final convergence gate iteration 1

Gate results:
- Pass: final focused suite, 230 tests in 15.23 seconds; log
  `logs/test-runs/condition-registry-focused-20260721-160437.log`.
- Pass: `uv run pyright propstore`, 0 errors.
- Pass: `uv run lint-imports`, 3 contracts kept.
- Fail: full suite, 11 failed, 1727 passed, 2 skipped; log
  `logs/test-runs/condition-registry-full-20260721-160530.log`.

Broken dependency-edge classifications and dispositions:
- Nine claim/concept CLI, web, and view assertions expect title-cased lexical
  display text (`Speed`, `Distance`) in `canonical_name`: valid presentation
  capabilities with the wrong representation. Disposition: retain the
  production CEL-symbol contract and update the test expectations to `speed`
  and `distance`; do not add title-casing or a presentation adapter.
- Two `test_verify_recompute_p93.py` promotion paths author a source concept
  linked to `dimensionless` while the fixture's form family is empty: valid
  promotion capability with an invalid owner fixture. Disposition: register
  the existing dimensionless quantity `FormDefinition` in `_new_source`, using
  the already-proven source-promotion fixture pattern.

Current state:
- The final runtime gate is not complete. No production defect was exposed;
  the six affected test files are stale fixtures/expectations from Slices 1-2.
- No final-gate fallout edit has started.

Blocker:
- None.

Next action:
- Repair only the six classified test files, run their focused logged gate,
  and continue the full-gate fixed point before union-path Ruff.

## Final convergence gate iteration 2

Gate results:
- Pass: six-file fallout suite, 48 tests in 14.18 seconds; log
  `logs/test-runs/condition-registry-full-fallout-20260721-160846.log`.
- Pass: full suite, 1738 passed and 2 skipped in 98.89 seconds; log
  `logs/test-runs/condition-registry-full-20260721-160922.log`.
- Pass: Ruff over the exact 31 surviving Python paths changed from the plan
  activation parent through the current tree.

Current state:
- All prescribed final convergence gates pass. The six classified test fixture
  repairs remain uncommitted as one final-gate fallout slice.
- The active plan still truthfully reports final gates pending until this slice
  is committed, the searches are rerun on the final tree, and the durable plan
  completion record is updated.

Blocker:
- None.

Next action:
- Rerun all seven searches on the final tree, inspect the exact six-file test
  diff, commit the fallout slice, then update and commit the active plan's final
  completion evidence.

## Final convergence fallout commit

- Pass: all seven searches had zero hits after the final test repairs.
- Kept commit: `f6329f7e test(conditions): align full-suite concept fixtures`.
- Commit boundary: exactly the six classified full-suite test fixtures.

Next action:
- Update the active plan from final-gates-pending to completed with the exact
  final logs and counts, commit that durable completion record, verify the final
  Git state, and close the fixed-point notes.

## Fixed-point completion

- Kept completion-record commit:
  `30670336 docs(conditions): record convergence completion`.
- Plan activation and required slices, in order:
  - `0c929c31 docs(conditions): plan condition registry convergence`
  - `35b18e88 refactor(concepts): make canonical names CEL symbols`
  - `faa6851e refactor(source): preserve promoted concept semantics`
  - `f68d2209 refactor(conditions): derive registries from checked concepts`
  - `e47f22ae docs(conditions): close obsolete registry workstreams`
- Final-gate fallout and completion records:
  - `f6329f7e test(conditions): align full-suite concept fixtures`
  - `30670336 docs(conditions): record convergence completion`
- Final evidence: 230 focused tests passed; package Pyright passed with 0
  errors; 3 import contracts were kept; 1738 full-suite tests passed with 2
  skipped; Ruff passed over 31 changed Python paths; all seven searches had
  zero hits; contract-manifest currentness and compatibility passed.
- Fixed point reached. No old registry production path remains, the active plan
  status is completed, and the unrelated `pyghidra_mcp_projects/` path was not
  modified.

Blocker:
- None.

Next action:
- None; verify final Git status and hand off the completed work.

## Completion audit reopening - compiler registry widening

Audit finding:
- `_enforce_cel_structural_invariants` in
  `propstore/compiler/workflows.py` accepts `Mapping[str, object]`, imports
  `ConceptInfo` locally, and reconstructs a `typed_registry` with an
  `isinstance` filter even though its only caller already supplies
  `CompilationContext.condition_registry: Mapping[str, ConceptInfo]`.
- This contradicts the direct checked-owner target and the repository rule
  forbidding local type-narrowing blocks as replacements for deleted payload
  or registry surfaces. The previous completion claim was therefore premature.

Classification and disposition:
- Broken edge: compiler structural-invariant workflow -> checked condition
  registry.
- Classification: already-owned capability using the wrong representation.
- Disposition: rewrite the parameter as `Mapping[str, ConceptInfo]`, rename it
  `condition_registry`, delete the local import and reconstructed mapping, and
  pass the owner mapping directly to `structural_concepts_in_expression`.
- Owner after repair: `ConceptCheckedRegistry.condition_registry`, carried by
  `CompilationContext.condition_registry`.

Slice gates:
- Search: no `typed_registry`, `cel_registry`, or `Mapping[str, object]` remains
  in the structural-invariant function.
- Runtime: logged compiler-workflow tests, changed-path Ruff, package Pyright,
  import-linter, all seven convergence searches, and the full logged suite.

Current state:
- Branch `master`; no tracked changes before reopening. The only visible
  untracked path remains the pre-existing `pyghidra_mcp_projects/`.
- `protocols:cleanup-refactor` is the active control surface.

Next action:
- Reopen the tracked plan with this exact unchecked repair, commit that record,
  then execute the one-file deletion-first slice.

Reopening commit:
- `941631bf docs(conditions): reopen compiler registry convergence`.

Next action:
- Delete the compiler registry widening exactly as specified by the reopened
  plan, then run its search and focused gates.

Audit repair evidence:
- Deleted the `Mapping[str, object]` parameter, old `cel_registry` spelling,
  local `ConceptInfo` import, `typed_registry` reconstruction, and
  `isinstance` filter from `_enforce_cel_structural_invariants`.
- The function now consumes `condition_registry: Mapping[str, ConceptInfo]`
  and passes the checked owner mapping directly.
- Pass: audit search has zero hits.
- Pass: 18 focused tests in 6.89 seconds; log
  `logs/test-runs/condition-registry-audit-20260721-161810.log`.
- Pass: changed-file Ruff.
- Pass: package Pyright, 0 errors.
- Pass: import-linter, 3 contracts kept.

Next action:
- Inspect and commit only `propstore/compiler/workflows.py` as
  `refactor(compiler): consume checked condition registry directly`, then run
  the seven searches and post-repair full logged suite.

Audit repair commit:
- `d383169f refactor(compiler): consume checked condition registry directly`.

Next action:
- Run all seven convergence searches on the committed repair, then the exact
  `condition-registry-full-audit` logged suite.

Audit closeout evidence:
- Pass: all seven convergence searches have zero hits on commit `d383169f`.
- Pass: post-repair full suite, 1738 passed and 2 skipped in 76.16 seconds;
  log `logs/test-runs/condition-registry-full-audit-20260721-162023.log`.
- The audit repair has passed every focused, static, architectural, search, and
  full runtime gate named by the reopened plan.

Next action:
- Mark every audit-repair item and plan status completed, commit the durable
  completion record as
  `docs(conditions): record audited convergence completion`, then perform the
  final current-state audit before closing the persistent goal.

Audited completion commit:
- `8e54f39e docs(conditions): record audited convergence completion`.

Fixed-point completion after production-surface audit:
- No compiler registry object widening, local narrowing block, or reconstructed
  registry remains.
- All original and audit-repair plan items are complete and committed.
- Final post-repair evidence: 18 focused tests passed; changed-file Ruff,
  package Pyright, and all 3 import contracts passed; all convergence searches
  are zero-hit; 1738 full-suite tests passed with 2 skipped.

Next action:
- None after the final current-state audit; close the persistent goal if the
  worktree, plan, searches, logs, notes, and commit ledger all agree.
