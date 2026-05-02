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

## Target Architecture

### Propstore Carrier

Add a first-class projection carrier:

```python
IstLiteralKey(context_id: ContextId, proposition_id: ClaimId | str)
```

Every context-scoped claim projects to an `ist(context, proposition)` literal.
The proposition remains the claim/assertion identity; the context is no longer
metadata that disappears before ASPIC/Dung.

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

## Non-Negotiable Rules

- Delete the old production semantic path before adding the new one.
- Do not preserve boolean lifting and `ist`-literal lifting in parallel.
- Do not move context lifting into `argumentation`.
- Do not let Gunray own propstore identity, context policy, or source truth.
- Do not add adapter aliases such as `can_lift_decision(...)` while keeping the
  old boolean call graph.
- Do not pre-materialize lifted assertions as committed canonical truth.
  Storage may cache inspected materializations, but render and projection policy
  must decide what is active.
- Every red test must cite the paper commitment it pins.
- Every phase ends with a logged targeted pytest run and `uv run pyright
  propstore` when production Python changed.

## Mechanical Order

This checklist is already topologically ordered. During execution, run a small
order-check script or use a dependency table before starting implementation.
The allowed order is:

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
```

Do not start a later phase while an earlier phase has unchecked production
items unless the user explicitly defers it.

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

Red tests:

- `tests/architecture/test_ist_projection_contract.py`
  - asserts every contextual claim must have a projected `IstLiteralKey`.
  - cites McCarthy 1993 and Guha 1991.
- `tests/architecture/test_lifting_decision_contract.py`
  - asserts production lifting decisions expose status, mode, rule id,
    support, provenance, and optional exception/witness.
  - cites Guha DCR-P/DCR-T and Bozzato justified exceptions.
- `tests/architecture/test_backend_identity_contracts.py`
  - asserts Gunray ground atoms and ASPIC literals are backend atoms with
    projection-frame provenance, not propstore source identity.
  - cites Diller 2025 and Modgil/Prakken 2018.

Green implementation:

- Add only failing contract tests and a `plans/...` workstream order check if
  needed.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-contracts tests/architecture/test_ist_projection_contract.py tests/architecture/test_lifting_decision_contract.py tests/architecture/test_backend_identity_contracts.py
```

## Phase 1 - `ist(c,p)` Literal Identity

Purpose: make context visible at the formal projection boundary.

Red tests:

- Contextual `ActiveClaim(context_id="ctx_a", claim_id="claim_x")` projects to
  `IstLiteralKey("ctx_a", "claim_x")`.
- Two claims with the same proposition and different contexts produce distinct
  ASPIC literals.
- Non-contextual claims either fail at the boundary or use an explicit
  repository root context. No silent unqualified literal path remains.

Green implementation:

- Add `IstLiteralKey` in `propstore/core/literal_keys.py`.
- Update `propstore/aspic_bridge/translate.py::claims_to_literals`.
- Update projection provenance in `propstore/aspic_bridge/projection.py`.
- Update every caller and test fixture that assumed claim id alone was the
  ASPIC atom identity.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-literals tests/test_ws_f_aspic_bridge.py tests/test_structured_projection.py tests/test_context_lifting_phase4.py
uv run pyright propstore
```

## Phase 2 - Delete Boolean Lifting as Semantic API

Purpose: replace boolean lift checks with typed lifting decisions.

Red tests:

- A conditional lifting rule with unsatisfied CEL conditions returns `BLOCKED`
  or `UNKNOWN`, never `True`.
- A conditional lifting rule with satisfied CEL conditions returns `LIFTED`
  with a solver witness.
- Existing context conflict classification consumes decisions, not `can_lift`.
- Micropub lift inspection renders a decision report, not just `liftable: bool`.

Green implementation:

- Add `LiftingDecision`, `LiftingDecisionStatus`, and typed provenance fields in
  `propstore/context_lifting.py`.
- Replace semantic callers in `propstore/core/activation.py`,
  `propstore/conflict_detector/context.py`,
  `propstore/conflict_detector/orchestrator.py`,
  `propstore/app/micropubs.py`, and world-bound activation.
- Keep no production reasoning call to `can_lift`.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label lifting-decisions tests/test_context_lifting_ws5.py tests/test_context_lifting_phase4.py tests/test_conflict_orchestrator_isolation.py tests/test_micropublications_phase4.py
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

Green implementation:

- Thread a condition solver or `ExceptionPatternSolver`-compatible protocol
  into lifting decision construction.
- Separate rule applicability conditions from target context assumptions in
  `effective_assumptions`.
- Update sidecar materialization rows to persist decision status and witness
  provenance.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-gated-lifting tests/test_context_lifting_ws5.py tests/test_z3_conditions.py tests/test_sidecar_contexts.py
uv run pyright propstore
```

## Phase 4 - Unified CKR Exception Carrier

Purpose: make blocked lifting and contextual justifiable exceptions one
evidence-bearing mechanism.

Red tests:

- A lifting exception and a `JustifiableException` produce the same
  `ExceptionDefeat` carrier shape.
- Multiple applicable exceptions report a policy issue once.
- A clashing set blocks only the matching target context and proposition.
- Exception support composes with lifting-rule support by provenance polynomial
  multiplication.

Green implementation:

- Replace `LiftingException` production semantics with the shared
  `defeasibility` exception carrier.
- Update `apply_exception_defeats_to_csaf` so blocked lifting undercuts the
  generated lifting rule.
- Delete any old lifting-exception-only production path.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ckr-exception-unification tests/test_defeasibility_support_contract.py tests/test_defeasibility_satisfaction.py tests/test_defeasibility_aspic_integration.py tests/test_context_lifting_ws5.py
uv run pyright propstore
```

## Phase 5 - ASPIC Lifting Projection

Purpose: make lifting rules produce inspectable arguments.

Red tests:

- For each `LIFTED` bridge decision, ASPIC has an argument concluding target
  `ist(target, p)`.
- For each `BLOCKED` decision, the lifting-rule argument is defeated or absent
  according to the exception status.
- ASPIC extensions are attack-conflict-free against raw attacks, not merely
  defeats.
- Projection provenance maps every target `ist` literal back to source
  assertion id and lifting rule id.

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

## Phase 6 - Gunray Grounding Projection Frames

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
- Review `argumentation.datalog_grounding`: keep it only if it remains a pure
  optional formal reduction over Gunray public types; otherwise move the
  propstore-specific projection responsibility back into propstore and update
  callers.

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label gunray-projection-frames tests/test_grounding_grounder.py tests/test_grounding_translator.py tests/test_grounded_bundle_round_trip.py tests/test_ws7_grounding_completion.py
uv run pyright propstore
```

## Phase 7 - World, ATMS, Conflict, and Worldline Convergence

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

## Phase 8 - Package Boundary Cleanup

Purpose: remove architectural residue after the new path is live.

Red tests:

- `argumentation.__init__` is shallow or lazy; importing
  `argumentation.dung` does not import unrelated ABA/ADF/VAF/solver modules.
- Propstore imports only explicit `argumentation` modules it uses.
- No production propstore code imports Gunray internal modules.
- No production semantic code calls `LiftingSystem.can_lift`.

Green implementation:

- Update `../argumentation/src/argumentation/__init__.py` if needed.
- Update propstore import sites.
- Add import-boundary tests in all three repos as appropriate.
- Pin propstore only to pushed remote dependency commits, never local paths.

Gates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label boundary-cleanup tests/architecture/test_import_boundaries.py tests/architecture/test_forbidden_symbols.py
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

## Full Completion Gate

After every phase-specific gate passes, run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ist-argumentation-gunray-full tests
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
```

Before declaring the workstream complete, search must show:

```powershell
rg -n -F "can_lift(" propstore tests docs
rg -n -F "LiftingException" propstore tests docs
rg -n -F "IstLiteralKey" propstore tests docs
```

Expected final state:

- no production semantic use of `can_lift`;
- no lifting-exception-only production path;
- `IstLiteralKey` is present at every ASPIC projection boundary where context is
  in scope.

## Completion Definition

The workstream is complete only when all of the following are true:

- Contextual claims project as `ist(c,p)` literals.
- Lifting rules are represented as formal argumentation inputs with provenance.
- Lifting conditions are evaluated in the lifting decision path.
- Blocked lifting and CKR justifiable exceptions share one defeat carrier.
- Gunray outputs are carried through typed projection frames and never become
  propstore identity.
- Bound world, conflict detection, ATMS, structured projection, and worldlines
  agree on lifted/blocked/unknown status.
- Full propstore, argumentation, and gunray gates pass.
- Documentation describes the final architecture without old/new dual paths.
