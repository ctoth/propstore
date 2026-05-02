# Context Lifting, Argumentation, and Gunray Workstream - 2026-05-02

## Objective

Make context lifting, structured argumentation, and Gunray grounding fit through
one explicit semantic carrier:

```text
ist(context_id, proposition_id)
```

The target architecture is direct:

- propstore owns situated assertions, contexts, lifting rules, CKR-style
  exceptions, provenance, source identity, world policy, and projection frames.
- `argumentation` owns finite formal argumentation objects and algorithms.
- Gunray owns DeLP, Datalog grounding, dialectical trees, KLM closure, answer
  sections, and grounding inspection.
- Propstore projects situated assertions into `argumentation` and Gunray
  backend objects, calls those kernels, and lifts formal results back into
  propstore provenance-bearing records.

Do not add compatibility shims, old/new dual paths, or helper-shaped aliases for
the current boolean lifting surface. Change the interface, update every caller,
and delete the old production path.

## Paper Basis

This workstream is based on the existing processed paper notes and local package
code. It did not perform a fresh page-image reread while drafting this plan.
Page PNGs are available for the papers; during execution, any paper claim that
needs rereading or adjudication must be checked from page images directly, not
from `pdftotext`, `full_text.txt`, or another extracted-text surrogate.

Primary context and lifting papers from `./papers`:

- `McCarthy_1993_FormalizingContext` - first-class `ist(c, p)`, lifting rules,
  entering/leaving contexts, decontextualization.
- `Guha_1991_ContextsFormalization` - context structures, Enter/Exit rules,
  DCR-P/DCR-T, articulation axioms, relative decontextualization.
- `McCarthy_1997_FormalizingContextExpanded` - expanded context position.
- `Bozzato_2018_ContextKnowledgeJustifiableExceptions` - CKR justified
  exceptions and clashing assumptions.
- `Bozzato_2020_DatalogDefeasibleDLLite` - datalog-facing contextual
  defeasibility.

Primary argumentation papers from `../argumentation/papers`:

- `Dung_1995_AcceptabilityArguments` - AF, attack, admissible, complete,
  preferred, stable, grounded semantics.
- `Modgil_2018_GeneralAccountArgumentationPreferences` - ASPIC+ attacks,
  defeats, attack-conflict-free extensions, rationality postulates, preferences.
- `Prakken_2010_AbstractFrameworkArgumentationStructured` and
  `Prakken_2019_ModellingAccrualArgumentsASPIC`.
- `Atkinson_2007_PracticalReasoningPresumptiveArgumentation` and
  `Bench-Capon_2003_PersuasionPracticalArgumentValue-based` for later value and
  practical-reasoning integration over the same carrier.
- `Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault`,
  `Toni_2014_TutorialAssumption-basedArgumentation`, `Brewka_2013_*`,
  `Cayrol_2005_*`, and `Coste-Marquis_2007_*` as package-owned formal kernels,
  not propstore context semantics.

Primary Gunray papers from `../gunray/papers`:

- `Diller_2025_GroundingRule-BasedArgumentationDatalog` - Datalog grounding,
  non-approximated predicates, ASPIC+-specific simplification.
- `Garcia_2004_DefeasibleLogicProgramming` - DeLP argument structures,
  dialectical trees, four-valued query answers.
- `Simari_1992_MathematicalTreatmentDefeasibleReasoning` - specificity,
  argument structures, counterargument, defeat.
- `Morris_2020_DefeasibleDisjunctiveDatalog`,
  `Maher_2021_DefeasibleReasoningDatalog`, `Goldszmidt_1992_*`, and
  `Antoniou_2007_*` guide explicit out-of-contract choices.

Boundary-relevant belief dynamics papers from `../belief-set/papers`:

- `Alchourron_1985_TheoryChange`, `Gärdenfors_1988_*`, and
  `Spohn_1988_*` specify the formal AGM, entrenchment, and OCF operators owned
  by `belief_set`.
- `Konieczny_2002_MergingInformationUnderConstraints` specifies formal IC
  merge over propositional belief bases.
- These papers matter as boundaries: this workstream must not reimplement AGM,
  IC merge, or Spohn revision under the context-lifting/argumentation names.

## Target Architecture

### Propstore Carrier

Add a first-class projection carrier:

```python
IstLiteralKey(context_id: ContextId, proposition_id: ClaimId)
```

Every context-scoped claim projects to an `ist(context, proposition)` literal.
The proposition remains the claim/assertion identity; the context is no longer
metadata that disappears before ASPIC/Dung.

ASPIC backend atom shape:

```python
Literal(
    atom=GroundAtom(
        predicate="ist",
        arguments=(str(context_id), str(proposition_id)),
    ),
    negated=False,
)
```

The key and the atom must both carry context. Storing context only in the
`LiteralKey` is insufficient because downstream ASPIC, Dung, projection, and
worldline code consumes `Literal.atom` after the key has disappeared.

### Lifting Decision

Replace semantic use of `LiftingSystem.can_lift(source, target) -> bool` with a
typed decision path:

```python
LiftingDecision(
    source_context,
    target_context,
    proposition_id,
    status,          # lifted | blocked | unknown
    mode,            # bridge | specialization | decontextualization
    rule_id,
    rule_conditions,
    support,
    provenance,
    exception=None,
    solver_witness=None,
)
```

`UNKNOWN` is pinned to Garcia and Simari 2004's four-valued answer discipline
and to propstore's existing solver-unknown boundary: when the reasoner cannot
soundly decide a lifting rule condition, the result is not converted into a
positive lift or a blocking exception. It is carried as incomplete-soundness
evidence.

`can_lift` may remain only as a presentation helper if needed, but production
reasoning must consume the typed decision.

### ASPIC Projection

Each lifted decision becomes a formal ASPIC+ object:

- `LIFTED` via `BRIDGE`: strict rule from source `ist` to target `ist`.
- `LIFTED` via `SPECIALIZATION`: defeasible rule whose antecedents include the
  source `ist` plus target assumptions that make the specialization meaningful.
- `LIFTED` via `DECONTEXTUALIZATION`: defeasible rule that records perspective
  or parameter loss in projection provenance.
- `BLOCKED`: undercut or defeat against the lifting rule, backed by the same
  exception carrier used by CKR justifiable exceptions.
- `UNKNOWN`: no rule emitted; projection records an incomplete-soundness
  witness.

### Gunray Boundary

Gunray remains a backend. Propstore translates rule/fact documents into
Gunray `DefeasibleTheory` or `Program`, keeps Gunray traces and grounding
inspection, then projects grounded instances into ASPIC+ through a typed frame.
Gunray atoms are backend encodings, not propstore identity.

### Argumentation Boundary

`argumentation` accepts already-projected finite formal objects. It does not
import propstore and does not own contexts, lifting, CEL, source identity,
sidecars, or provenance.

### Belief-Set Boundary

`belief_set` owns finite propositional AGM revision, contraction, iterated
revision, epistemic entrenchment, Spohn states, and IC merge. It is not part of
the `ist(c,p)` projection path and must not receive propstore contexts, lifting
rules, Gunray atoms, ASPIC arguments, source identity, sidecar rows, or
provenance objects.

Propstore may adapt a rendered, finite propositional abstraction into
`belief_set` only when the task is explicitly formal belief revision or IC
merge. Context lifting and exception defeats remain propstore-to-argumentation
projections, not belief-set operations.

## Non-Negotiable Rules

- Delete the old production semantic path before adding the new one.
- Do not preserve boolean lifting and `ist`-literal lifting in parallel.
- Do not move context lifting into `argumentation`.
- Do not move context lifting into `belief_set` or encode contexts as raw
  propositional atoms for revision unless a phase explicitly defines a
  belief-revision projection and integrity constraint.
- Do not let Gunray own propstore identity, context policy, or source truth.
- Do not add adapter aliases such as `can_lift_decision(...)` while keeping the
  old boolean call graph.
- Do not pre-materialize lifted assertions as committed canonical truth.
  Storage may cache inspected materializations, but render and projection policy
  must decide what is active.
- Sidecar rows may store decision inspection records, but provenance graph
  content remains in the provenance carrier and git notes. Sidecar rows must not
  become claim identity.
- Every red test must cite the paper commitment it pins.
- Every phase that opens or closes an architectural gap updates `docs/gaps.md`
  in the same commit.
- Every phase ends with a logged targeted pytest run and `uv run pyright
  propstore` when production Python changed.

## Mechanical Order

This checklist is already topologically ordered. Before implementation starts,
add or run a reusable order-check script that verifies the dependency graph
below:

```text
-1 -> 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
```

Do not start a later phase while an earlier phase has unchecked production
items unless the user explicitly defers it.

## Per-Phase Completion Checklist

Every implementation phase must end with:

- the phase's red tests failing before production edits and passing after;
- the phase's logged pytest gate;
- `uv run pyright propstore` when propstore production Python changed;
- `docs/gaps.md` updated in the same commit for opened or closed gaps;
- `git status --short -- <owned paths>` clean after the phase commit.

If a phase slice produces no kept improvement, revert that slice completely
before trying a second approach. If two consecutive slices on the same target
produce no kept improvement, stop and report the exact blocked phase item.

Temporal CEL scope: lifting conditions may reuse the existing TIMEPOINT/Z3 path
for Allen-like or time-scoped conditions, but this workstream does not change
`KindType.TIMEPOINT` semantics. Any TIMEPOINT failure is a condition-solver
issue and must be surfaced as `UNKNOWN`/incomplete-soundness, not as an
implicit lift.

## Phase -1 - Baseline and Dependency Inventory

Purpose: establish the repo state before destructive interface replacement.

Baseline commands:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-workstream-baseline tests
uv run pyright propstore
```

Dependency package baselines:

```powershell
Push-Location ..\argumentation
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\gunray
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\belief-set
uv run pytest
uv run pyright belief_set
Pop-Location
```

Inventory commands:

```powershell
rg -n -F "can_lift(" propstore tests docs
rg -n -F "LiftingException" propstore tests docs
rg -n -F "LiftingMaterializationStatus" propstore tests docs
rg -n -F "LiteralKey" propstore tests
rg -n -F "belief_set" propstore/context_lifting.py propstore/aspic_bridge propstore/grounding
rg -n -F "can_lift" propstore/cli propstore/app C:\Users\Q\code\research-papers-plugin
rg -n -F "from argumentation" propstore tests docs
```

Required artifact:

- Add a dated baseline note under `notes/` listing command outcomes, log paths,
  and the exact inventory counts. If any baseline fails for unrelated existing
  worktree reasons, record that plainly before starting Phase 0.
- Include an import-baseline note for `argumentation.__init__` so Phase 8 can
  measure whether root-package import behavior improved rather than widened
  scope unexpectedly.

## Phase 0 - Paper-Backed Contract Inventory

Purpose: make the literature commitments executable before changing production
code.

Paper-image verification:

- For every red test that cites a paper definition or theorem not already
  pinned by a local paper note with page references, inspect the relevant
  `pages/*.png` files in `./papers`, `../argumentation/papers`, or
  `../gunray/papers`.
- Record the exact paper directory, page image filename, and cited definition
  or theorem in the test docstring or adjacent test comment.
- Do not use PDF text extraction as evidence for a test expectation.
- Minimum page-image checklist before Phase 0 tests are accepted:
  - Bozzato 2018 definitions 4-6 for justified exceptions and clashing
    assumptions.
  - Garcia and Simari 2004 section 4 for four-valued answer status.
  - Guha 1991 section 3 for DCR-P, DCR-T, and articulation axioms.
  - Modgil and Prakken 2018 sections 3-4 for defeats and
    attack-conflict-free extensions.
  - Diller 2025 section 4 for non-approximated predicates.

Red tests:

- `tests/architecture/test_ist_projection_contract.py`
  - asserts every contextual claim must have a projected `IstLiteralKey`.
  - cites McCarthy 1993 and Guha 1991.
- `tests/architecture/test_lifting_decision_contract.py`
  - asserts production lifting decisions expose status, mode, rule id,
    support, provenance, and optional exception/witness.
  - cites Guha DCR-P/DCR-T, Bozzato justified exceptions, and Garcia 2004
    `UNKNOWN` for incomplete query status.
- `tests/architecture/test_backend_identity_contracts.py`
  - asserts Gunray ground atoms and ASPIC literals are backend atoms with
    projection-frame provenance, not propstore source identity.
  - cites Diller 2025 and Modgil/Prakken 2018.
- `tests/architecture/test_belief_set_boundary_contract.py`
  - asserts `propstore/context_lifting.py`, `propstore/aspic_bridge/**`, and
    `propstore/grounding/**` do not import `belief_set`.
  - is a regression guard that passes today and must continue to pass through
    every later phase; it is not a phase-driving red test.
  - positively asserts that every propstore import edge to `belief_set` goes
    through `propstore.support_revision` or a named future formal-revision or
    IC-merge adapter.
  - cites AGM/IC papers only as excluded boundary surfaces.

Green implementation:

- Add only failing contract tests and a `plans/...` workstream order check if
  needed.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-contracts tests/architecture/test_ist_projection_contract.py tests/architecture/test_lifting_decision_contract.py tests/architecture/test_backend_identity_contracts.py tests/architecture/test_belief_set_boundary_contract.py
```

## Phase 1 - `ist(c,p)` Literal Identity

Purpose: make context visible at the formal projection boundary.

Red tests:

- Contextual `ActiveClaim(context_id="ctx_a", claim_id="claim_x")` projects to
  `IstLiteralKey("ctx_a", "claim_x")`.
- Two claims with the same proposition and different contexts produce distinct
  ASPIC literals.
- The produced ASPIC literal atom is exactly `GroundAtom("ist",
  ("ctx_a", "claim_x"))`, not `GroundAtom("claim_x")` with context hidden in
  metadata.
- `IstLiteralKey` equality and hashing are distinct from `ClaimLiteralKey` and
  `GroundLiteralKey`.
- Non-contextual claims either fail at the boundary or use an explicit
  repository root context. No silent unqualified literal path remains.

Green implementation:

- Add `IstLiteralKey` in `propstore/core/literal_keys.py`.
- Expand the `LiteralKey` union and update every `match`, `isinstance`, dict
  key, serialization, and projection consumer identified by the Phase -1
  inventory.
- Update `propstore/aspic_bridge/translate.py::claims_to_literals`.
- Update projection provenance in `propstore/aspic_bridge/projection.py`.
- Update every caller and test fixture that assumed claim id alone was the
  ASPIC atom identity.
- Keep the Phase 0 belief-set import-boundary test in the Phase 1 gate so drift
  is caught before later phases.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-literals tests/test_ws_f_aspic_bridge.py tests/test_structured_projection.py tests/test_context_lifting_phase4.py tests/architecture/test_belief_set_boundary_contract.py
uv run pyright propstore
```

## Phase 2 - Unified Lifting Decisions and CKR Exceptions

Purpose: replace boolean lift checks and the lifting-exception-only path with
one typed decision and exception carrier. This phase intentionally combines the
old Phase 2 and Phase 4 concerns so `BLOCKED` never depends on a future
exception migration.

Red tests:

- A conditional lifting rule with unsatisfied CEL conditions returns `BLOCKED`
  or `UNKNOWN`, never `True`.
- A conditional lifting rule with satisfied CEL conditions returns `LIFTED`
  with a solver witness.
- `LiftingMaterializationStatus` is gone from production code or is renamed and
  absorbed into `LiftingDecisionStatus`; no parallel status enum survives.
- A current `LiftingException(id, rule_id, target, proposition_id,
  clashing_set, justification)` maps to the shared exception carrier with:
  `id` as exception identity, `rule_id` as target rule provenance,
  `target/proposition_id` as defeated `ist` use, `clashing_set` as justification
  evidence, and `justification` as explanatory provenance.
- A lifting exception and a `JustifiableException` produce the same
  `ExceptionDefeat` carrier shape.
- Exception support composes with lifting-rule support by provenance polynomial
  multiplication.
- Existing context conflict classification consumes decisions, not `can_lift`.
- Micropub lift inspection renders a decision report, not just `liftable: bool`.

Green implementation:

- Add `LiftingDecision`, `LiftingDecisionStatus`, and typed provenance fields in
  `propstore/context_lifting.py`.
- Replace `LiftingException` production semantics with the shared
  `defeasibility` exception carrier in the same slice.
- Delete the old lifting-exception-only production path in the same commit that
  introduces `BLOCKED` decisions.
- Rename the existing `LiftingDecisionCache` in
  `propstore/conflict_detector/orchestrator.py` if needed so it cannot be
  confused with the domain decision object.
- Replace semantic callers in `propstore/core/activation.py`,
  `propstore/conflict_detector/context.py`,
  `propstore/conflict_detector/orchestrator.py`,
  `propstore/app/micropubs.py`, and world-bound activation.
- Keep no production reasoning call to `can_lift`.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label lifting-decisions tests/test_context_lifting_ws5.py tests/test_context_lifting_phase4.py tests/test_conflict_orchestrator_isolation.py tests/test_micropublications_phase4.py tests/test_defeasibility_support_contract.py tests/test_defeasibility_satisfaction.py
uv run pyright propstore
```

## Phase 3 - Condition-Gated Lifting

Purpose: make lifting-rule CEL conditions load-bearing.

Red tests:

- `LiftingRule.conditions` are evaluated during decision construction.
- `SolverUnknown` yields `UNKNOWN` with incomplete-soundness provenance.
- `Z3TranslationError` yields an authoring-boundary diagnostic, not a silent
  lift.
- Rule conditions and target context assumptions are not conflated.
- Cached sidecar materialization rows are inspection records only: changing a
  lifting rule, exception, or condition changes the decision on rebuild and does
  not make the old row canonical truth.
- Create `tests/test_sidecar_contexts.py` for decision-status persistence,
  witness references, sidecar schema/version bump behavior, and invalidation of
  inspection rows after lifting-rule, exception, or condition changes.

Green implementation:

- Thread the existing `ExceptionPatternSolver` protocol into lifting decision
  construction. The Z3 implementation adapts `Z3ConditionSolver` to that
  protocol; callers do not receive a second condition-solver API.
- Separate rule applicability conditions from target context assumptions in
  `effective_assumptions`.
- Update sidecar materialization rows to persist decision status and witness
  references. If the sidecar schema changes, increment the sidecar schema
  version and add a schema/version test. Full provenance graph content remains
  in the provenance carrier and git notes.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-gated-lifting tests/test_context_lifting_ws5.py tests/test_z3_conditions.py tests/test_sidecar_contexts.py
uv run pks build
uv run pyright propstore
```

## Phase 4 - ASPIC Lifting Projection

Purpose: make lifting rules produce inspectable arguments.

Red tests:

- For each `LIFTED` bridge decision, ASPIC has an argument concluding target
  `ist(target, p)`.
- For each `BLOCKED` decision, the lifting-rule argument is defeated or absent
  according to the exception status.
- ASPIC extensions are attack-conflict-free against raw attacks, not merely
  defeats; cite Modgil and Prakken 2018 sections 3-4 in the test docstring.
- Projection provenance maps every target `ist` literal back to source
  assertion id and lifting rule id.
- `apply_exception_defeats_to_csaf` undercuts generated lifting rules through
  the same shared exception carrier used by contextual exceptions.

Green implementation:

- Add `propstore/aspic_bridge/lifting_projection.py`.
- Wire generated lifting rules into `compile_bridge_context`.
- Extend structured projection result types to expose lifting provenance and
  backend atom identity.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label aspic-lifting-projection tests/test_ws_f_aspic_bridge.py tests/test_structured_projection.py tests/test_defeasibility_aspic_integration.py tests/test_context_lifting_ws5.py
uv run pyright propstore
```

## Phase 5 - Gunray Grounding Projection Frames

Purpose: prevent Gunray backend atoms from becoming propstore identity.

Red tests:

- Every Gunray-derived ASPIC literal has a projection frame that records source
  rule ids, source fact ids, substitutions, and backend atom encoding.
- Strong negation remains typed at the adapter boundary.
- Gunray `YES/NO/UNDECIDED/UNKNOWN` sections are preserved without collapsing
  non-commitment.
- Grounding inspection from Gunray is used directly; no re-grounding fallback
  path survives in production.

Green implementation:

- Tighten `propstore/grounding/bundle.py`,
  `propstore/grounding/grounder.py`, and
  `propstore/aspic_bridge/grounding.py` around projection-frame records.
- Keep `argumentation.datalog_grounding` as the optional formal reduction over
  Gunray public types. Do not move it in this workstream. Add import-boundary
  tests proving it imports no propstore modules and consumes only Gunray public
  API.
- Propstore remains responsible for `GroundedRulesBundle`, source rule/fact
  provenance, projection frames, sidecar rows, and render policy.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label gunray-projection-frames tests/test_grounding_grounder.py tests/test_grounding_translator.py tests/test_grounded_bundle_round_trip.py tests/test_ws7_grounding_completion.py
uv run pyright propstore
```

## Phase 6 - World, ATMS, Conflict, and Worldline Convergence

Purpose: make every runtime view consume the same situated projection.

Red tests:

- Bound world active claims, ATMS claim support, conflict detection, and
  worldline dependencies agree on lifted/blocked/unknown decisions.
- ATMS labels contain target context support only when a lifting decision is
  exact enough to justify it.
- Conflict detector emits `CONTEXT_PHI_NODE` only when no applicable lifting
  decision exists in either direction.
- Worldline dependencies include source assertion ids, lifting rule ids,
  exception ids, and solver witnesses for blocked/unknown cases.

Green implementation:

- Update `propstore/core/activation.py`, `propstore/world/atms.py`,
  `propstore/conflict_detector/*`, and `propstore/worldline/*`.
- Delete any local lifting approximation that does not consume
  `LiftingDecision`.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label situated-runtime-convergence tests/test_atms_engine.py tests/test_lifting_blocked_in_provenance.py tests/test_worldline_argumentation_multi_extension.py tests/test_conflict_detector.py tests/test_world_query.py
uv run pyright propstore
```

## Phase 7 - Cross-Repo Coordination and Dependency Pins

Purpose: make dependency package changes reproducible from clean checkouts.

Rules:

- If `argumentation`, Gunray, or `belief_set` changes, push that repository
  first.
- Propstore may pin only a pushed remote tag or immutable pushed commit SHA.
- Never pin to a local path, editable path, local repository URL, or unpushed
  branch.

Required order:

1. All dependency repo full pytest and pyright gates are green at the SHA to be
   pinned.
2. Push dependency commits.
3. Update propstore `pyproject.toml` / `uv.lock` to pushed immutable refs.
4. Run propstore targeted gates affected by the dependency.
5. Run propstore full completion gate.

Gates:

```powershell
git -C ..\argumentation status --short
git -C ..\gunray status --short
git -C ..\belief-set status --short
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'file://' pyproject.toml uv.lock
```

## Phase 8 - Package, CLI, Workflow, and Documentation Cleanup

Purpose: remove architectural residue after the new path is live.

Red tests:

- `argumentation.__init__` is shallow or lazy; importing
  `argumentation.dung` does not import unrelated ABA/ADF/VAF/solver modules.
- Propstore imports only explicit `argumentation` modules it uses.
- No production propstore code imports Gunray internal modules.
- No production semantic code calls `LiftingSystem.can_lift`.
- No production context-lifting code imports `belief_set`; belief-set use stays
  behind formal revision or IC-merge adapters.
- CLI/app reports expose typed lifting decision fields rather than `liftable:
  bool`.
- Research workflow and skill code has no stale `can_lift` or
  `LiftingException` assumptions.
- `docs/gaps.md`, `docs/contexts-and-micropubs.md`, `docs/argumentation.md`,
  and CLI docs describe the final path only.

Green implementation:

- `argumentation.__init__` shallowing must ship as its own pushed
  `argumentation` commit. Re-pin propstore to that pushed SHA per Phase 7
  before running propstore boundary-cleanup gates. Do not edit the local
  argumentation checkout and rely on path-based resolution.
- Update `../argumentation/src/argumentation/__init__.py` if needed.
- Update propstore import sites.
- Add import-boundary tests in all three repos as appropriate.
- Pin propstore only to pushed remote dependency commits, never local paths.
- Audit `propstore/cli/**`, `propstore/app/**`,
  `C:/Users/Q/code/research-papers-plugin/**`, and local skills for stale
  lifting APIs.

Gates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label boundary-cleanup tests/architecture/test_import_boundaries.py tests/architecture/test_forbidden_symbols.py
rg -n -F "can_lift" propstore/cli propstore/app C:\Users\Q\code\research-papers-plugin
rg -n -F "LiftingException" propstore/cli propstore/app C:\Users\Q\code\research-papers-plugin
uv run pyright propstore
```

In `../argumentation`:

```powershell
uv run pytest tests/test_import_boundaries.py tests/test_docs_surface.py
uv run pyright src
```

In `../gunray`:

```powershell
uv run pytest tests/test_public_api.py tests/test_workstream_o_gun_contract.py
uv run pyright src
```

In `../belief-set`:

```powershell
uv run pytest tests/test_belief_set_postulates.py tests/test_belief_set_iterated_postulates.py tests/test_ic_merge_Maj_Arb.py
uv run pyright belief_set
```

## Full Completion Gate

After every phase-specific gate passes, run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-argumentation-gunray-full tests
uv run pks build
uv run pyright propstore
```

Then run dependency package gates:

```powershell
Push-Location ..\argumentation
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\gunray
uv run pytest
uv run pyright src
Pop-Location

Push-Location ..\belief-set
uv run pytest
uv run pyright belief_set
Pop-Location
```

Before declaring the workstream complete, search must show:

```powershell
rg -n -F "can_lift(" propstore tests docs
rg -n -F "LiftingException" propstore tests docs
rg -n -F "LiftingMaterializationStatus" propstore tests docs
rg -n -F "IstLiteralKey" propstore tests docs
rg -n -F "belief_set" propstore/context_lifting.py propstore/aspic_bridge propstore/grounding
rg -n -F "can_lift(" ..\argumentation ..\gunray ..\belief-set
rg -n -F "LiftingException" ..\argumentation ..\gunray ..\belief-set
```

`LiftingMaterializationStatus` may appear only in historical notes, reviews, or
`docs/gaps.md`; it must have no production hits.

Expected final state:

- no production semantic use of `can_lift`;
- no lifting-exception-only production path;
- `IstLiteralKey` is present at every ASPIC projection boundary where context is
  in scope.
- no context-lifting, ASPIC-bridge, or Gunray-grounding production path imports
  `belief_set`.

## Completion Definition

The workstream is complete only when all of the following are true:

- Contextual claims project as `ist(c,p)` literals.
- Lifting rules are represented as formal argumentation inputs with provenance.
- Lifting conditions are evaluated in the lifting decision path.
- Blocked lifting and CKR justifiable exceptions share one defeat carrier.
- Gunray outputs are carried through typed projection frames and never become
  propstore identity.
- Belief-set remains a formal belief-dynamics dependency only; this workstream
  does not repurpose it as a context or argumentation engine.
- Bound world, conflict detection, ATMS, structured projection, and worldlines
  agree on lifted/blocked/unknown status.
- Full propstore, argumentation, gunray, and belief-set gates pass.
- Documentation describes the final architecture without old/new dual paths.
