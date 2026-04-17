# Paper-Grounded Test Suite Workstream

Date: 2026-04-16
Status: proposed
Builds on: `plans/test-suite-improvement-workstream-2026-04-13.md`

## Goal

Raise the semantic signal density of the test suite by replacing low-value
tests with paper-grounded property, metamorphic, and differential tests.

This workstream is not a general "add more tests" effort. It has three concrete
outcomes:

1. remove tests that only assert imports, type annotations, or local wiring
   trivia
2. replace brittle examples and routing checks with durable semantic contracts
3. ground new properties in the local paper collection, especially page-image
   evidence under `papers/*/pngs/` or `papers/*/pages/`

The intended end state is a smaller set of low-signal tests and a stronger set
of tests for argumentation, ASPIC, subjective logic, revision, URI identity, and
conformance behavior.

## Non-Goals

- Do not rewrite the whole suite in one pass.
- Do not remove named literature examples that serve as executable
  documentation unless a stronger paper-grounded property fully covers them.
- Do not add compatibility or migration test paths unless an external data
  constraint requires them.
- Do not mark tests as `migration` just to hide weak tests.
- Do not use PDF text extraction as paper-reading evidence. If a page must be
  reread, inspect the local PNG page image directly.

## Execution Rules

1. Work one slice at a time.
2. Each slice must end in either:
   - a kept deletion/replacement with passing targeted tests, or
   - a full revert of that slice.
3. If a candidate test is already gone, renamed, or now protects a stronger
   semantic contract, stop that candidate immediately and record that the
   earlier premise was wrong.
4. New property tests should use `@pytest.mark.property`.
5. New oracle/backend comparison tests should use `@pytest.mark.differential`.
6. Every test run must go through `scripts/run_logged_pytest.ps1`.
7. After every passing targeted or broader test run, reread this plan and pick
   the next unchecked slice.
8. Do not declare the workstream complete while any phase below is unchecked or
   explicitly deferred.

Canonical test command shape:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-slice-N tests/test_file.py
```

For full-suite verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-full
```

## Paper Grounding Inventory

These page images were directly inspected while forming this workstream:

- `papers/Dung_1995_AcceptabilityArguments/pngs/page-005.png`
  - argumentation framework, conflict-free, acceptable, admissible definitions
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-006.png`
  - preferred extension, Nixon example, Fundamental Lemma, preferred extension existence
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`
  - characteristic function monotonicity and grounded extension as least fixed point
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-05.png`
  - strong equivalence definition and `a`-kernel definition
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-07.png`
  - `a*`-kernel lemmas and preservation under union
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-12.png`
  - strong-equivalence summary and self-loop-free collapse to syntactic equality
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png`
  - transposition and closure under transposition/contraposition
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png`
  - rationality postulates and last-link ordering
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png`
  - rephrased semantics under last-link and assumption defeat setup
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png`
  - contradictory rebut/undermine with elitist and democratic lifting
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-004.png`
  - probability expectation
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png`
  - opinion definition
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-024.png`
  - consensus operator
- `papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/pngs/page-004.png`
  - weighted belief fusion cases and dogmatic/vacuous remarks
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png`
  - faithful assignment and propositional revision postulates
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png`
  - AF-based revision postulates

Any additional paper claim used during execution must cite a local page image
path in the test docstring or adjacent comment.

## Phase 0: Baseline And Inventory

Status: unchecked

Purpose: establish current state before deleting or replacing anything.

Tasks:

- [ ] Run the current migration inventory:

```powershell
uv run scripts/list_migration_tests.py
```

- [ ] Run current targeted inventory for the initial deletion candidates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-baseline-low-signal tests/test_helpers.py tests/test_render_contracts.py tests/test_form_utils.py tests/test_claim_and_stance_document_enums.py tests/test_atms_value_status_types.py tests/test_uri.py tests/test_literal_keys.py
```

- [ ] Confirm the paper page image files listed above exist.
- [ ] Record baseline test count for affected files in a short report under
  `reports/paper-grounded-test-workstream-baseline-2026-04-16.md`.

Acceptance criteria:

- Baseline report names the exact log file paths under `logs/test-runs/`.
- Baseline report states which page image paths were checked.

## Phase 1: Delete Pure Low-Signal Tests

Status: unchecked

This phase deletes tests that have no meaningful replacement requirement because
nearby tests already exercise the behavior.

### Slice 1A: YAML Helper Import Smoke

Target:

- `tests/test_helpers.py::test_write_yaml_file_importable_from_artifact_codecs`

Reason:

- It imports `write_yaml_file` and asserts `callable`.
- Neighboring tests already exercise real behavior: roundtrip, key order, block
  style, and Unicode handling.

Tasks:

- [ ] Delete only this test.
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-delete-helper-import tests/test_helpers.py
```

Acceptance criteria:

- `tests/test_helpers.py` still covers the artifact codec write behavior.
- No replacement test is added.

### Slice 1B: Render Protocol Shape Smoke

Target:

- `tests/test_render_contracts.py::test_protocol_shapes`

Reason:

- `isinstance(RenderPolicy(), RenderPolicy)` and `hasattr(..., "__mro__")`
  test Python object mechanics rather than render semantics.
- The same file already has roundtrip and policy override behavior tests.

Tasks:

- [ ] Delete only this test.
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-delete-render-protocol-shape tests/test_render_contracts.py
```

Acceptance criteria:

- Existing render policy and environment roundtrip tests remain.
- No protocol-shape smoke test remains.

### Slice 1C: Form Loading Sentinel Pair

Targets:

- `tests/test_form_utils.py::TestFormDefinitionLoading::test_load_form_with_none_returns_none`
- `tests/test_form_utils.py::TestFormDefinitionLoading::test_load_form_with_empty_string_returns_none`

Reason:

- These assert two early-return sentinels, not domain behavior.
- The meaningful boundary test is unknown form returns `None` and unknown
  document fields fail hard.

Tasks:

- [ ] Delete both sentinel tests.
- [ ] Keep `test_load_nonexistent_form_returns_none`.
- [ ] Keep `test_load_form_rejects_unknown_document_fields`.
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-delete-form-sentinels tests/test_form_utils.py
```

Acceptance criteria:

- No behavior test now depends on `None` or `""` being a first-class form name.
- Unit conversion and resource-form tests remain unchanged.

## Phase 2: Replace Annotation And Wiring Tests With Behavior

Status: unchecked

This phase removes tests that assert type annotations and replaces them with
runtime behavior contracts that would fail if those annotations drifted in a
meaningful way.

### Slice 2A: Claim/Stance Enum Annotation Echo

Target:

- `tests/test_claim_and_stance_document_enums.py::test_claim_and_stance_document_annotations_use_enums`

Keep:

- `test_claim_document_decodes_claim_and_inline_stance_enums`
- `test_source_documents_decode_claim_and_stance_enums`

Reason:

- The annotation test echoes type hints.
- The decode tests prove the runtime boundary converts authored strings into
  `ClaimType` and `StanceType`.

Tasks:

- [ ] Delete the annotation echo test.
- [ ] Add a rejection test if one is missing:
  - invalid claim type fails strict document conversion
  - invalid stance type fails strict document conversion
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-claim-stance-enum-behavior tests/test_claim_and_stance_document_enums.py
```

Acceptance criteria:

- The file tests decode/reject behavior, not annotations.
- A regression to loose string enum handling fails at runtime.

### Slice 2B: ATMS Status Annotation Echo

Target:

- `tests/test_atms_value_status_types.py`

Reason:

- The file asserts annotations on DTO fields and method return shapes.
- A stronger contract is that ATMS reports actually materialize enum-valued
  statuses through the public world/bound surfaces.

Tasks:

- [ ] Inspect current ATMS report-producing tests in `tests/test_atms_engine.py`.
- [ ] Add or strengthen behavior tests there for:
  - concept future status entries use `ValueStatus`
  - concept stability/relevance/intervention reports use `ValueStatus`
  - node explanation/intervention surfaces use `ATMSNodeStatus`
  - support quality values use `SupportQuality`
- [ ] Delete `tests/test_atms_value_status_types.py` after behavior coverage is present.
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-atms-status-behavior tests/test_atms_engine.py
```

Acceptance criteria:

- There is no test file whose only purpose is annotation reflection.
- Public ATMS outputs are proven to carry enum objects, not loose strings.

## Phase 3: URI Identity Properties

Status: unchecked

Target:

- `tests/test_uri.py::test_tag_uri_uses_configured_authority`

Reason:

- One hardcoded example gives little confidence in the URI identity surface.

Tasks:

- [ ] Replace the single example with property tests for `tag_uri`.
- [ ] Keep `test_repository_uri_authority_reads_repo_config`.
- [ ] Keep `ni_uri_for_bytes` determinism/change properties.
- [ ] New properties:
  - generated authority/kind/name inputs are deterministic
  - output starts with `tag:{authority}:`
  - generated names never introduce raw spaces into the final path component
  - equivalent whitespace in names normalizes consistently, if that is current
    intended behavior
  - path separators in generated names are either rejected or normalized
    according to the current production contract

Implementation note:

- If current behavior around slash/backslash is ambiguous, write one failing
  test that forces an explicit decision before broadening the property.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-uri-properties tests/test_uri.py
```

Acceptance criteria:

- `tag_uri` has property coverage over a generated input family.
- The old one-point example is gone or retained only as a named regression
  comment if it catches a real bug.

## Phase 4: Dung Paper Properties And Backend Differential

Status: unchecked

Grounding:

- `papers/Dung_1995_AcceptabilityArguments/pngs/page-005.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-006.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`

### Slice 4A: Dung Semantic Properties

Targets:

- `tests/test_dung.py`

Current issue:

- The file has useful properties already, but many concrete cases are doing
  paper-property work one example at a time.

Tasks:

- [ ] Add `@pytest.mark.property` to generated Dung property tests.
- [ ] Strengthen or add properties for:
  - conflict-free definition from Dung page 326
  - admissibility from Dung page 326
  - Fundamental Lemma from Dung page 327
  - every AF has at least one preferred extension from Dung page 327
  - characteristic function monotonicity from Dung page 329
  - grounded extension is the least fixed point from Dung page 329
- [ ] Keep named examples for:
  - Nixon diamond
  - reinstatement
  - odd cycle/no stable extension
- [ ] Remove redundant examples only after the property covering them is green.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-dung-properties tests/test_dung.py
```

Acceptance criteria:

- Dung definitions and theorems have explicit property tests with page-image
  citations.
- Remaining concrete examples are named anchors, not the main coverage.

### Slice 4B: Dung Z3 Differential

Targets:

- `tests/test_dung_review_v2.py`
- `tests/test_dung.py`
- `tests/test_dung_z3.py`

Current issue:

- `test_preferred_extensions_explicit_brute_backend_does_not_fall_back_to_z3`
  checks call routing by monkeypatching Z3, not semantic equivalence.

Tasks:

- [ ] Add `tests/test_dung_backend_differential.py` or integrate into
  `tests/test_dung_z3.py`.
- [ ] Generate AFs in the intersection supported by both backends.
- [ ] Assert:
  - complete extensions from native and Z3 are equal
  - preferred extensions from native and Z3 are equal, if both surfaces expose
    that backend
  - stable extensions from native and Z3 are equal, if both surfaces expose
    that backend
- [ ] Delete `tests/test_dung_review_v2.py` after differential coverage lands.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-dung-z3-differential tests/test_dung.py tests/test_dung_z3.py tests/test_dung_backend_differential.py
```

Acceptance criteria:

- No test asserts backend call routing when observable backend equivalence is
  feasible.
- Z3/native disagreement shrinks to a concrete AF.

## Phase 5: Strong Equivalence Kernel Properties

Status: unchecked

Grounding:

- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-05.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-07.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-12.png`

Purpose:

- Add missing paper-grounded coverage for strong equivalence kernels.

Tasks:

- [ ] Search current production code for any existing kernel/equivalence
  implementation.
- [ ] If no production implementation exists, create a focused proposal or
  xfail-free red tests only if this workstream is explicitly switched from test
  cleanup to feature implementation.
- [ ] If an implementation exists or is added, test:
  - self-loop-free AFs are unchanged by `a`, `a*`, and `c` kernels
  - `a`-kernel removes non-self outgoing attacks from self-attacking arguments
  - `a*`-kernel is no larger than the original relation and no smaller than the
    `a`-kernel where the paper requires it
  - kernel equality implies semantic equality under generated context unions
    for the relevant semantics and bounded AF sizes

Verification, if tests are added:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-oikarinen-kernels tests/test_strong_equivalence_kernels.py
```

Acceptance criteria:

- Either a real kernel test surface exists with page citations, or the report
  explicitly states that there is no implementation to test yet.
- No placeholder tests are committed.

## Phase 6: ASPIC Transposition And Last-Link Properties

Status: unchecked

Grounding:

- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png`
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png`

### Slice 6A: Transposition Closure Properties

Targets:

- `tests/test_aspic.py`
- `tests/test_aspic_bridge_review_v2.py`

Current issue:

- Several tests are review-regression examples. Some are valuable, but the
  durable paper contract is closure behavior, not one handpicked failure.

Tasks:

- [ ] Keep direct regressions for known bugs only if they remain distinct from
  generated properties.
- [ ] Add properties for `transposition_closure`:
  - extensive: original strict rules are retained
  - monotone: adding rules cannot shrink closure
  - idempotent: closing twice equals closing once
  - kind preserving: generated transposed rules are strict
  - every added rule corresponds to the transposition schema on page 13
- [ ] Cite `page-012.png` in the property-test docstring.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-aspic-transposition tests/test_aspic.py tests/test_aspic_bridge_review_v2.py
```

Acceptance criteria:

- Transposition behavior is primarily protected by properties.
- Remaining examples document named paper/regression cases.

### Slice 6B: Last-Link Differential Or Metamorphic Tests

Targets:

- `tests/test_preference.py`
- `tests/test_aspic.py`
- `tests/test_aspic_bridge.py`

Tasks:

- [ ] Ground existing last-link preference tests against Prakken page 16 and
  Lehtonen pages 523-524.
- [ ] Add generated tests that compare:
  - argument-enumeration defeat results
  - assumption/defeasible-element rephrased defeat results
  for bounded theories where both can be computed.
- [ ] If the assumption-level implementation is not present, add metamorphic
  properties over current preference functions:
  - equal-strength rebut/undermine succeeds
  - undercut is preference-independent
  - elitist/democratic lifting diverges on generated multi-element strength
    sets where the definitions require divergence

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-last-link tests/test_preference.py tests/test_aspic.py tests/test_aspic_bridge.py
```

Acceptance criteria:

- Preference tests cite the page-image sources for last-link and lifting.
- At least one generated test exercises elitist/democratic divergence.

## Phase 7: Subjective Logic Consolidation

Status: unchecked

Grounding:

- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-004.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-024.png`
- `papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/pngs/page-004.png`

Targets:

- `tests/test_opinion.py`
- `tests/test_opinion_schema.py`
- `tests/test_render_policy_opinions.py`
- `tests/test_praf_integration.py`

Current state:

- `tests/test_opinion.py` already has strong property coverage. Use it as the
  model for this phase.
- Several surrounding files still contain one-point default or backward-compat
  checks.

Tasks:

- [ ] Audit concrete arithmetic tests in `tests/test_opinion.py` against the
  property tests already present.
- [ ] Delete concrete tests only when an existing or new property covers the
  same invariant.
- [ ] Convert schema/default checks into behavior tests:
  - opinion fields roundtrip through storage
  - missing opinions are explicitly classified as fallback/no-data at render
    boundaries
  - decision criteria preserve `Bel <= pignistic <= Pl`
- [ ] For WBF/CCF tests, cite van der Heijden page 5 and assert:
  - vacuous inputs fuse to vacuous when all sources have no evidence
  - exactly one dogmatic source controls the result where the paper says so
  - sum invariants hold for generated opinions

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-subjective-logic tests/test_opinion.py tests/test_opinion_schema.py tests/test_render_policy_opinions.py tests/test_praf_integration.py
```

Acceptance criteria:

- Subjective-logic tests use generated opinion families for invariants.
- One-point examples remain only as named table/regression cases.

## Phase 8: Revision Postulate Properties

Status: unchecked

Grounding:

- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png`
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png`

Targets:

- `tests/test_revision_properties.py`
- `tests/test_revision_iterated_examples.py`
- `tests/test_revision_iterated.py`
- `tests/test_revision_operators.py`
- `tests/test_revision_af_adapter.py`

Tasks:

- [ ] Identify which current revision tests are examples vs postulate checks.
- [ ] Keep examples only when they correspond to named paper examples.
- [ ] Add generated postulate tests for bounded revision states:
  - success
  - syntax irrelevance
  - consistency when the revising information is satisfiable
  - inclusion/intersection behavior where the implementation exposes it
  - idempotence or iterated-revision postulates where already supported
- [ ] Cite Diller page images in test docstrings.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-revision-postulates tests/test_revision_properties.py tests/test_revision_iterated_examples.py tests/test_revision_iterated.py tests/test_revision_operators.py tests/test_revision_af_adapter.py
```

Acceptance criteria:

- Revision behavior is tested as postulates over generated states, not only
  example traces.
- Any unsupported postulate is recorded as a product gap, not silently skipped.

## Phase 9: Defeasible Conformance Suite Decision

Status: unchecked

Target:

- `tests/test_defeasible_conformance_tranche.py`

Current issue:

- The test file depends on a sibling checkout:
  `../datalog-conformance-suite/src`.
- If missing, the whole module skips.

Tasks:

- [ ] Decide whether the conformance suite is a repo-owned test oracle.
- [ ] If yes:
  - vendor the selected YAML cases or add them as normal repo test fixtures
  - remove module-level sibling-repo skip
  - mark the tests `@pytest.mark.differential`
- [ ] If no:
  - remove this file from normal suite responsibility
  - move any still-useful translator examples into local tests
- [ ] Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-defeasible-conformance tests/test_defeasible_conformance_tranche.py
```

Acceptance criteria:

- The conformance tests either run from repo-local fixtures or are removed from
  the normal suite.
- No test module silently disappears because a sibling checkout is absent.

## Phase 10: Exception Narrowing Cleanup

Status: unchecked

Target:

- `tests/test_exception_narrowing_group3.py`

Current issue:

- This file groups unrelated RuntimeError propagation regressions from a review
  batch.
- It uses mocks heavily and is organized by historical finding group, not
  product contract.

Tasks:

- [ ] For each test in the file, locate the current owning subsystem test file.
- [ ] Move or rewrite the behavior into that subsystem if it is still valuable.
- [ ] Prefer subsystem-shaped contracts:
  - missing optional table is handled narrowly
  - disk/corruption/runtime errors propagate
  - external service errors propagate or are reported explicitly
- [ ] Delete `tests/test_exception_narrowing_group3.py` after all valuable
  coverage is moved.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-exception-narrowing tests/test_build_sidecar.py tests/test_cli.py tests/test_embed_operational_error.py tests/test_param_conflicts.py tests/test_classify.py tests/test_sympy_generator.py tests/test_value_resolver_failure_reasons.py
```

Acceptance criteria:

- No test file name encodes a stale review group.
- RuntimeError/OperationalError behavior is tested where the behavior belongs.

## Phase 11: Marker And Suite Hygiene

Status: unchecked

Tasks:

- [ ] Add `@pytest.mark.property` to new and existing generated invariant tests
  touched by this workstream.
- [ ] Add `@pytest.mark.differential` to backend/oracle comparison tests touched
  by this workstream.
- [ ] Confirm no `@pytest.mark.migration` tests were added unless an external
  compatibility target forced them.
- [ ] Run:

```powershell
uv run scripts/list_migration_tests.py
```

- [ ] Run a focused changed-suite pass:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-changed-suite tests/test_helpers.py tests/test_render_contracts.py tests/test_form_utils.py tests/test_claim_and_stance_document_enums.py tests/test_atms_engine.py tests/test_uri.py tests/test_dung.py tests/test_dung_z3.py tests/test_aspic.py tests/test_preference.py tests/test_opinion.py tests/test_revision_properties.py
```

Acceptance criteria:

- Touched property/differential tests are marked.
- No migration test inventory appears unless explicitly justified.

## Phase 12: Full Verification And Closeout

Status: unchecked

Tasks:

- [ ] Run the full suite:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-full
```

- [ ] Write closeout report:

`reports/paper-grounded-test-suite-workstream-closeout-2026-04-16.md`

Closeout report must include:

- deleted tests
- replaced tests
- new property tests
- new differential tests
- paper page image paths cited in tests
- targeted log paths
- full-suite log path
- any explicitly deferred phases and why

Acceptance criteria:

- Full suite passes or the closeout identifies the exact blocked phase.
- Every unchecked phase is completed or explicitly deferred by the user.

## Completion Criteria

This workstream is complete only when:

1. pure low-signal tests listed in Phase 1 are deleted
2. annotation-only tests listed in Phase 2 are replaced by behavior tests or
   explicitly deferred with reason
3. URI, Dung, Dung/Z3, ASPIC, subjective-logic, and revision surfaces have
   stronger property/differential coverage than before
4. conformance-suite ownership is explicit
5. stale review-group tests are deleted or moved into owning subsystem files
6. touched generated tests are correctly marked
7. the full suite has been run through `scripts/run_logged_pytest.ps1`
8. the closeout report exists

