# CEL registry architecture review

## Task

Read-only assessment of how much of `propstore/cel_registry.py` belongs as methods on `Concept`, versus being renamed or relocated.

## Current findings

- `Concept` is the canonical authored charter/document. It owns stored concept fields, not condition-ir projection behavior or cross-family lookup.
- All meaningful behavior in `cel_registry.py` depends on external state or an external consumer type:
  - `concept_kind` resolves through `Mapping[str, FormDefinition]`.
  - `_category_extensible` reads the linked `FormDefinition`.
  - `concept_info_from_concept` creates condition-ir's `ConceptInfo` and delegates to `claim_conditions.lower_concept`.
  - `build_canonical_cel_registry` aggregates many concepts and adds condition-ir synthetic bindings.
- Therefore none of the three public functions is a natural `Concept` instance method. A `Concept.to_concept_info(form_registry)` method would couple the canonical entity to one downstream substrate and require a global family registry argument.
- The module is historically residual: its older form adapted `ConceptDocument`, sidecar rows, and JSON form parameters. Those multiple representations no longer exist.
- Conversion ownership is currently split between `cel_registry.py` and `claim_conditions.py`: the former resolves form metadata, while the latter constructs `ConceptInfo` and the final id-keyed mapping.
- `source/claims.py` independently resolves concept form names and kinds before calling `lower_concept`, so there are already multiple projection paths with different unresolved-form policy.
- The strongest current direction is to keep this as a boundary projection, not entity behavior, and consolidate/rename its owner around condition-registry construction rather than CEL or `Concept` methods.
- One separate representation problem is `_category_extensible` reading `FormDefinition.parameters["extensible"]` from a loose semantic dict; that likely wants an explicit typed form field if the behavior remains.
- The registry-key contract is contradictory and must be settled before moving code:
  - `claim_conditions.condition_registry` and `cel_registry` key by `ConceptInfo.id` / `Concept.concept_id`.
  - condition-ir's registry helpers describe and manipulate canonical-name-keyed registries, and its CEL frontend looks identifiers up by the registry key.
  - `conflict_detector.orchestrator` checks registry collisions by `concept.canonical_name`.
  - production concept ids are minted as values such as `ps:concept:...`, which are not ordinary CEL identifiers, while source conditions use identifier-like authored names.
  - current tests conceal the issue by using simple ids, often equal to the canonical name, and explicitly asserting id-keying.
- Missing-form policy is also split: `cel_registry.concept_kind` fabricates `KindType.CATEGORY` for absent/dangling forms, while `source.claims._cel_concept_infos` skips unresolved concepts. This is compilation/diagnostic policy and must not become entity behavior.
- Recommended target shape: keep `Concept` data-only; rename `cel_registry.py` toward `condition_registry.py`; collapse its public helper surface to one registry construction boundary; keep claim checking/serialization in `claim_conditions.py`; delete or relocate the duplicate lowering/registry wrappers so there is one owner. Do not add a `Concept.to_concept_info(...)` method or a linked-form convenience helper.

## Repository state observed

- Branch: `master`, ahead of `origin/master` by 16 commits.
- Pre-existing untracked path: `pyghidra_mcp_projects/`.
- No source edits, staging, commits, or tests were performed for this review.

## Blocker

No inspection blocker. An implementation would require an explicit decision on the condition binding key and unresolved-form behavior before mutation.

## Next action

Finish and write an execution-ready repo-local plan. No source mutation is authorized yet.

## Planning update - 2026-07-21

- `protocols:cleanup-refactor` is the active control surface for the planned work.
- The historical plans confirm the name-keyed contract but are stale about current owners and types:
  - `plans/cel-registry-hardening-workstream-2026-04-14.md`
  - `plans/cel-subsystem-unification-plan-2026-04-08.md`
  - `plans/cel-typed-expression-workstream-2026-04-16.md`
  - `plans/concept-canonical-typing-workstream-2026-04-09.md`
- Current production compilation already runs `ConceptCheckPass` before building `CompilationContext`, but ignores `ConceptCheckedRegistry` and rebuilds from the loaded concepts. This makes the checked concept pass the strongest existing owner for CEL binding validation, form resolution, and `ConceptInfo` projection.
- A deletion-first target can therefore delete `propstore/cel_registry.py`, delete `claim_conditions.lower_concept` and `claim_conditions.condition_registry`, and make callers consume the condition registry produced by the checked concept owner rather than recreating the same builder under a new name.
- `canonical_name` is currently overloaded as both machine binding and display text. The canonical lemon display owner already exists at `lexical_entry.canonical_form.written_rep`; project initialization currently incorrectly copies `seed.name` into both surfaces. The plan should establish `canonical_name` as the CEL symbol and use `seed.ref` for it.
- Source promotion currently constructs a flat `Concept` and drops both the source proposal's form and its typed `form_parameters`. Existing project seed construction demonstrates an executable full `LexicalEntry` pattern using the minted concept id as the sense reference.
- Category values/extensibility are per-concept source data (`SourceConceptFormParametersDocument`), not global `FormDefinition` data. A complete plan must preserve them as explicit typed canonical concept fields rather than reading `FormDefinition.parameters` or dropping them during promotion.
- Baseline command passed: `powershell -File scripts/run_logged_pytest.ps1 -Label cel-registry-plan-baseline tests/test_cel_registry.py tests/test_claim_conditions.py tests/test_compilation_context.py tests/test_family_passes.py tests/test_source_authoring_p82.py tests/test_app_project_init.py -q` -> 57 passed in 6.85s, log `logs/test-runs/cel-registry-plan-baseline-20260721-145843.log`.
- Current Git state observed before planning: `master`, ahead of `origin/master`; pre-existing untracked `pyghidra_mcp_projects/`. The notes file itself is also intentionally uncommitted.
- The new plan will explicitly create its fixed-point record before source edits, name each atomic slice and gate, and supersede only the stale CEL-registry portions of the historical plans without changing the unrelated active convergence plan.
