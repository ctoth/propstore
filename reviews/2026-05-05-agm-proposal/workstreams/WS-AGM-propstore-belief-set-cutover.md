# WS-AGM: Propstore / belief-set formal revision cutover

**Status**: OPEN
**Depends on**: WS-G closed foundation, current `formal-belief-set` dependency, current `formal-argumentation` dependency
**Blocks**: full formal Propstore world-revision workflow, formal worldline merge/revision replay, web revision UI
**Owner**: Propstore implementation owner plus dependency owners for `belief-set` and `argumentation`

---

## Why this workstream exists

`proposals/true-agm-revision-proposal.md` now defines the right architecture:
formal belief revision and IC merge live in `../belief-set`, formal AF revision
lives in `../argumentation`, and Propstore owns only projection, support
realization, explanation, snapshots, journals, app, CLI, and future web
presentation.

The current code does not yet implement that architecture. `propstore.revision`
is retired, but `propstore.support_revision` still contains local AGM-shaped
decision logic in operators, iterated ranking updates, and entrenchment
construction. That code must be cut over deletion-first. The final architecture
has exactly one production `belief_set` import edge:

`propstore.support_revision.belief_set_adapter`

Everything else in Propstore calls Propstore owner-layer APIs.

This workstream turns the proposal into an executable plan. It does not
reintroduce formal AGM into Propstore. It makes Propstore consume the formal
dependency kernels and realize their decisions over source-backed support.

---

## Source Documents

- `proposals/true-agm-revision-proposal.md`
- `reviews/2026-04-26-claude/workstreams/WS-G-belief-revision.md` (closed prior foundation)
- `../belief-set/papers/Alchourron_1985_TheoryChange/notes.md`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md`
- `../belief-set/papers/Grove_1988_TwoModellingsTheoryChange/notes.md`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md`
- `../belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/notes.md`
- `../belief-set/papers/Hansson_1989_NewOperatorsTheoryChange/notes.md`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`

---

## Current State Verified Before This Workstream

- `propstore.revision` is retired and guarded by `tests/test_revision_retirement.py`.
- `propstore.support_revision.belief_set_adapter` exists as the single allowed production import edge to `belief_set`.
- `tests/architecture/test_belief_set_boundary_contract.py` requires that single edge and passed in:
  `logs/test-runs/belief-set-boundary-20260505-222136.log`.
- `propstore.app.world_revision` already exposes the right app verbs.
- `pks world revision ...` already exposes the right CLI command family.
- Worldline materialization already accepts revision flags.
- `propstore.web` does not yet expose a first-class world-revision UI; its `rev` request field is repository revision selection, not belief revision.

---

## Review Findings Covered

| Finding | Current Surface | Required End State |
|---|---|---|
| Local formal-decision drift | `support_revision.operators`, `support_revision.iterated`, `support_revision.entrenchment` own AGM-shaped behavior | Formal decisions are delegated to `belief_set`; Propstore keeps only support realization |
| Boundary under-enforcement | Any future support module could import `belief_set` if the gate is loosened | Exactly `propstore.support_revision.belief_set_adapter` may import `belief_set` |
| Flattened result contract | Revision results mix formal and operational facts | Typed `decision` and `realization` payloads are separate |
| Iterated branch duplication | Propstore has local `lexicographic` / `restrained` update branches | Propstore calls `belief_set.iterated.lexicographic_revise` / `restrained_revise` |
| Entrenchment substitution | Support-derived ranking can be mistaken for formal entrenchment | Formal entrenchment/preorder decision lives in `belief_set`; support reasons are companion explanation |
| Merge/revision confusion | Merge points can be treated as revision-like support episodes | Multi-parent worldlines dispatch to IC merge or fail with typed merge-required error |
| CLI/web ambiguity | Existing CLI works, web is not wired | App/CLI use same typed result contract; web consumes app APIs later |
| Missing belief-set surfaces | Grove, Hansson, partial-meet, Levi/Harper, broader admissible family are gaps | Tracked as dependency phases, not Propstore-local implementations |

---

## Non-Negotiable Rules

- Do not implement formal AGM, Grove spheres, Hansson belief-base contraction, or IC merge kernels in Propstore.
- Do not keep old and new Propstore revision decision paths in parallel.
- Do not add compatibility shims, aliases, fallback readers, bridge normalizers, or dual-path glue.
- Do not let CLI or web import `belief_set`.
- Do not let `propstore.app` parse CLI-shaped JSON strings or render CLI-shaped errors.
- Do not call assignment-selection merge formal IC merge.
- Do not call support-revision output formal AGM.
- Do not declare this workstream complete while local formal decision branches survive in Propstore.

---

## Target Workflow

1. User selects a scoped world through app, CLI, web, or worldline materialization.
2. Propstore projects the scoped `BoundWorld` into a formal `belief_set` bundle:
   alphabet, formula mapping, closed `BeliefSet`, optional `SpohnEpistemicState`,
   optional entrenchment/preorder, and reverse maps to Propstore atom/source ids.
3. `belief_set` makes the formal decision:
   expansion, contraction, revision, iterated revision, or IC merge.
4. Propstore compares the formal answer with the support projection.
5. Propstore computes the support realization:
   accepted/rejected atom ids, support assumptions to incise, source provenance,
   explanation reasons, snapshots, and journal records.
6. App and CLI render both layers:
   formal decision first, support realization second, explanation/journal third.
7. Worldlines capture and replay the episode deterministically.
8. Web later consumes the same app payloads, starting with read-only inspect,
   preview, and explain views.

---

## Result Contract

Every revision workflow returns a typed report with two explicit parts.

`decision`:

- operation name
- formal policy name
- input formula ids / world ids / profile ids
- accepted and rejected formulas or worlds
- formal epistemic-state hash where relevant
- formal budget failure where relevant
- formal trace when provided by `belief_set`

`realization`:

- accepted atom ids
- rejected atom ids
- incision set
- source claim provenance
- support sets and essential support
- support-derived reasons
- snapshot hash
- journal metadata when captured
- replay status where relevant

The two facts must remain separately inspectable:

- "`belief_set` selected these formulas/worlds"
- "Propstore realized that decision by cutting these support assumptions"

---

## Implementation Phases

Each phase lands in its own commit or tight commit series. If a phase touches
both Propstore and a sibling dependency, commit the dependency first, push it,
then update Propstore to a remote tag or immutable commit. Never pin to a local
path.

### Phase 0 — Gate The Boundary

Status: partially done by `4b3a8a67 revision: add belief-set adapter boundary`.

Remaining work:

- Add `tests/architecture/test_no_local_agm_logic.py`.
- Static-check that Propstore local modules do not contain hand-rolled formal
  kernels after cutover:
  `lexicographic`, `restrained`, `partial meet`, `remainder`, `sphere`,
  `IC merge`, `Delta`, `Levi`, `Harper` in decision-owning code.
- Keep allowlist empty at close.

Acceptance:

- `tests/architecture/test_belief_set_boundary_contract.py` passes.
- `tests/architecture/test_no_local_agm_logic.py` fails before cutover and
  passes after cutover.

### Phase 1 — Stabilize Minimum `belief-set` Surfaces

Owner: `../belief-set`.

Required public surfaces:

- `BeliefSet`
- `expand`
- `SpohnEpistemicState`
- `agm.revise`
- `agm.full_meet_contract`
- `entrenchment.EpistemicEntrenchment`
- `iterated.lexicographic_revise`
- `iterated.restrained_revise`
- `ic_merge.merge_belief_profile`
- `AlphabetBudgetExceeded`
- `EnumerationExceeded`

Work:

- Verify API signatures and return types.
- Add propstore-shaped projection tests in `belief-set`.
- Ensure budget failures are typed and stable.
- Publish a remote dependency commit or tag if changes are needed.

Acceptance:

- `../belief-set` postulate/property tests pass.
- Propstore-shaped inputs are accepted without hidden normalization.
- Propstore dependency pin resolves from remote, never from a local path.

### Phase 2 — Projection Bundle

Owner: Propstore.

Files:

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/projection.py`
- `propstore/support_revision/state.py`

Work:

- Replace the placeholder adapter with real projection functions.
- Introduce `FormalProjectionBundle` with:
  alphabet, formal formulas, `BeliefSet`, optional `SpohnEpistemicState`,
  optional formal entrenchment/preorder, atom/formula reverse maps, source
  claim maps, and budget config.
- Map `AssertionAtom` and `AssumptionAtom` to stable formal atoms.
- Reject lossy or unrepresentable projection with typed failures.
- Propagate `AlphabetBudgetExceeded` and `EnumerationExceeded` as
  `RevisionResult` failures, not CLI exceptions.

Tests:

- `tests/test_revision_adapter_projection.py`
- `tests/test_revision_adapter_budget.py`

Acceptance:

- A fixture `BoundWorld` with exact-support active claims projects to the
  expected formal alphabet and `BeliefSet`.
- Reverse maps are bijective for active projected atoms.
- Budget failures surface as typed app-layer results.

### Phase 3 — Formal Decision Reports

Owner: Propstore.

Files:

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/state.py`
- `propstore/support_revision/workflows.py`

Work:

- Add typed decision reports for expand, contract, revise, iterated revise, and
  IC merge.
- Keep decision reports free of support-incision details.
- Carry formal traces from `belief_set` where available.
- Add conversion from formal decisions to support-realization requests.

Tests:

- `tests/test_revision_formal_decision_reports.py`

Acceptance:

- Direct `belief_set` calls and adapter decision calls agree on accepted
  formulas/worlds.
- No support-incision fields appear inside the formal decision object.

### Phase 4 — Cut Over Expand / Contract / Revise

Owner: Propstore.

Files:

- `propstore/support_revision/operators.py`
- `propstore/support_revision/workflows.py`
- `propstore/app/world_revision.py`
- `propstore/cli/world/revision.py`

Work:

- Delete local formal-decision behavior in `operators.py`.
- Use adapter decisions for expand, contract, and revise.
- Keep only Propstore support realization in operators.
- Preserve source immutability.
- Return split decision/realization payloads through app and CLI.

Tests:

- `tests/test_revision_adapter_expand_contract_revise.py`
- update `tests/test_revision_operators.py`
- update `tests/test_revision_cli.py`
- update `tests/test_revision_explain.py`

Acceptance:

- Propstore expand/contract/revise formal result equals direct `belief_set`
  decision for the fixture.
- Propstore realization explains which support assumptions were cut.
- CLI text output renders formal decision first and support realization second.
- JSON output has separate `decision` and `realization` objects.
- No local formal decision branch remains in `operators.py`.

### Phase 5 — Cut Over Iterated Revision

Owner: Propstore.

Files:

- `propstore/support_revision/iterated.py`
- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/history.py`
- `propstore/app/world_revision.py`
- `propstore/cli/world/revision.py`

Work:

- Delete local `if operator == "lexicographic"` and
  `if operator == "restrained"` ranking-update branches.
- Call `belief_set.iterated.lexicographic_revise` and
  `belief_set.iterated.restrained_revise`.
- Store formal epistemic-state hashes in snapshots/journals.
- Preserve merge-parent refusal for linear iterated revision.

Tests:

- `tests/test_revision_adapter_iterated.py`
- update `tests/test_revision_iterated.py`
- update `tests/test_revision_iterated_examples.py`
- update `tests/test_iterated_revision_recomputes_entrenchment.py`

Acceptance:

- Propstore iterated revision and direct `belief_set` iterated revision agree
  on formal accepted formulas/worlds.
- Propstore still reports support realization separately.
- Merge-parent linear iterated revision refuses with typed error.
- No local lexicographic/restrained decision branches remain.

### Phase 6 — Formal Entrenchment And Support Reasons

Owner: Propstore plus `belief-set` where needed.

Files:

- `propstore/support_revision/entrenchment.py`
- `propstore/support_revision/explanation_types.py`
- `propstore/support_revision/explain.py`
- `propstore/support_revision/belief_set_adapter.py`

Work:

- Treat formal entrenchment/preorder as a `belief_set` decision artifact.
- Convert support count, source reliability, overrides, and argument strength
  into support reasons, not substitute formal ordering.
- Keep explanation payloads able to show both formal ordering and support
  rationale.

Tests:

- update `tests/test_revision_entrenchment.py`
- update `tests/test_revision_explain.py`
- `tests/test_revision_formal_entrenchment_boundary.py`

Acceptance:

- Formal entrenchment is sourced from `belief_set` where AGM behavior is claimed.
- Propstore support reasons are companion explanation, not the formal ordering.
- Public exports do not imply Propstore owns formal AGM entrenchment.

### Phase 7 — Worldline Capture, Replay, And At-Step Projection

Owner: Propstore.

Files:

- `propstore/support_revision/history.py`
- `propstore/support_revision/dispatch.py`
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/runner.py`
- `propstore/worldline/revision_types.py`
- `propstore/app/worldlines.py`
- `propstore/cli/worldline/*`

Work:

- Journal decision and realization separately.
- Store formal epistemic-state hashes where relevant.
- Replay through normalized formal operation plus support realization.
- At-step world projection uses replayed accepted snapshot atoms.
- Keep journal content hash sensitive to both formal decision and realization.

Tests:

- update `tests/test_worldline_revision.py`
- update `tests/test_world_query_at_journal_step.py`
- update `tests/test_journal_entry_contract.py`
- update `tests/test_capture_journal.py`
- update `tests/test_replay_determinism_actually_replays.py`

Acceptance:

- Replay re-runs the formal decision through the adapter.
- Replay verifies support realization deterministically.
- Changing formal decision payload changes journal/worldline hash.
- Changing realization payload changes journal/worldline hash.

### Phase 8 — Formal IC Merge At Merge Points

Owner: Propstore plus `belief-set` if IC merge gaps are found.

Files:

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/worldline/runner.py`
- `propstore/worldline/revision_capture.py`
- `propstore/world/assignment_selection_merge.py`
- `propstore/app/merge.py`
- `propstore/cli/merge_cmds.py`

Work:

- Build formal belief profiles from merge parents.
- Source integrity constraints from worldline definition or explicit app
  request.
- Dispatch multi-parent formal merge to `belief_set.ic_merge.merge_belief_profile`.
- Keep assignment-selection merge as render-time observed-value selection.
- Refuse implicit merge when required integrity constraint is missing.

Tests:

- `tests/test_revision_merge_uses_ic_merge.py`
- update `tests/test_worldline_revision_merge_parent_evidence.py`
- update `tests/test_assignment_selection_merge.py`
- update `tests/test_cli.py` where merge output changes

Acceptance:

- Multi-parent worldline revision does not use linear iterated revision.
- Formal IC merge result is visible in decision payload.
- Assignment selection never claims to be IC merge.

### Phase 9 — App And CLI Result Contract

Owner: Propstore.

Files:

- `propstore/app/world_revision.py`
- `propstore/app/worldlines.py`
- `propstore/cli/world/revision.py`
- `propstore/cli/worldline/display.py`
- `propstore/cli/worldline/materialize.py`

Work:

- Keep existing command names and flags unless a real missing input is found.
- App returns typed request/report objects, not CLI-shaped strings.
- CLI parses flags and renders typed reports only.
- Text rendering order:
  formal decision, support realization, explanation/journal.
- JSON output has `decision` and `realization` objects.

Tests:

- update `tests/test_revision_cli.py`
- update `tests/test_cli_error_rendering.py`
- update `tests/test_cli_layout.py`
- update `tests/test_worldline.py`
- add `tests/test_revision_app_contract.py`

Acceptance:

- Existing commands still exist.
- App errors do not mention CLI flags.
- CLI output cleanly separates decision and realization.
- JSON contract is stable and documented by tests.

### Phase 10 — Web Read-Only Consumer

Owner: Propstore.

Files:

- `propstore/web/app.py`
- `propstore/web/routing.py`
- `propstore/web/serialization.py`
- `propstore/web/html.py`
- `propstore/web/static/web.css`

Work:

- Do not overload repository `rev`.
- Add read-only world-revision inspect/preview/explain routes after app
  contract is stable.
- Web calls app-layer APIs only.
- No web mutation or journal capture UI in this phase.

Tests:

- add `tests/test_web_revision_readonly.py`
- update existing web route tests if present

Acceptance:

- Web can show projected base, formal decision preview, and explanation.
- Web does not mutate sources or capture journals.
- Web does not import `belief_set`.

### Phase 11 — Dependency Formal Gaps

Owner: `../belief-set`, not Propstore.

Implement as separate dependency workstreams, each with Propstore consumer tests
only after the dependency surface exists:

- AGM partial-meet contraction with remainder sets and explicit selection
  functions
- Levi and Harper composer APIs
- Grove sphere systems and equivalent sentence/preorder representation
- Spohn conditionalization with explicit firmness
- broader Booth-Meyer admissible revision family
- explicit `BeliefBase` distinct from closed `BeliefSet`
- Hansson safe contraction
- Hansson set-valued contraction inputs
- Hansson simple/composite partial meet contraction
- Hansson minimal contraction
- Katsuno-Mendelzon update
- Konieczny-Pino-Pérez `Delta^Max`
- remaining IC merge families

Acceptance:

- Each dependency feature ships with postulate/property tests in `belief-set`.
- Propstore only adds adapter/consumer tests.
- No formal kernel lands in Propstore.

### Phase 12 — Formal AF Revision Consumer Boundary

Owner: `../argumentation` for kernels, Propstore for adapters.

Work:

- Keep formal AF revision in `argumentation.af_revision`.
- If Propstore needs AF-revision projection, add exactly one adapter:
  `propstore.support_revision.argumentation_adapter`.
- Mirror the `belief_set` import-boundary test for `argumentation`.
- No AF revision kernel in Propstore.

Tests:

- `tests/architecture/test_argumentation_boundary_contract.py`
- consumer-shape tests for AF projection and identity preservation

Acceptance:

- Propstore imports formal argumentation only through the named adapter.
- Argument identity survives projection and back-projection.

### Phase 13 — Documentation And Closure

Owner: Propstore.

Files:

- `proposals/true-agm-revision-proposal.md`
- this workstream
- `docs/belief-set-revision.md`
- `docs/ic-merge.md`
- `docs/af-revision.md`
- `docs/gaps.md` if present/current

Work:

- Update proposal status from target/cutover to implemented.
- Mark implemented surfaces versus deferred dependency gaps.
- Add final examples for app/CLI/worldline workflows.
- Add a workstream sentinel test.
- Close gaps.

Tests:

- `tests/test_workstream_agm_done.py`
- `tests/test_belief_set_docs.py`

Acceptance:

- This file status is `CLOSED <sha>`.
- Proposal no longer describes implemented behavior as target behavior.
- Deferred dependency gaps are explicit and owner-assigned.

---

## First Tests To Write

Write these before production cutover work:

1. `tests/architecture/test_no_local_agm_logic.py`
2. `tests/test_revision_adapter_projection.py`
3. `tests/test_revision_adapter_budget.py`
4. `tests/test_revision_formal_decision_reports.py`
5. `tests/test_revision_adapter_expand_contract_revise.py`
6. `tests/test_revision_adapter_iterated.py`
7. `tests/test_revision_formal_entrenchment_boundary.py`
8. `tests/test_revision_merge_uses_ic_merge.py`
9. `tests/test_revision_app_contract.py`
10. `tests/test_web_revision_readonly.py`
11. `tests/architecture/test_argumentation_boundary_contract.py`
12. `tests/test_workstream_agm_done.py`

Tests that are expected to fail before their phase must say so in the docstring
and cite the phase that turns them green.

---

## Acceptance Gates

Before closing this workstream:

- [ ] `uv run pyright propstore` passes.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label agm-boundary tests/architecture/test_belief_set_boundary_contract.py tests/architecture/test_no_local_agm_logic.py` passes.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label agm-adapter tests/test_revision_adapter_projection.py tests/test_revision_adapter_budget.py tests/test_revision_formal_decision_reports.py tests/test_revision_adapter_expand_contract_revise.py tests/test_revision_adapter_iterated.py tests/test_revision_formal_entrenchment_boundary.py` passes.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label agm-worldline tests/test_revision_merge_uses_ic_merge.py tests/test_worldline_revision.py tests/test_world_query_at_journal_step.py tests/test_journal_entry_contract.py tests/test_replay_determinism_actually_replays.py` passes.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label agm-surfaces tests/test_revision_cli.py tests/test_revision_app_contract.py tests/test_web_revision_readonly.py` passes.
- [ ] Full logged pytest passes or any pre-existing failures are documented with log path and unrelated proof.
- [ ] `propstore.support_revision.belief_set_adapter` is the only production `belief_set` import.
- [ ] No local formal AGM-shaped decision branch remains in `support_revision.operators`, `support_revision.iterated`, or `support_revision.entrenchment`.
- [ ] App/CLI results expose separate `decision` and `realization` payloads.
- [ ] Worldline journals capture and replay both decision and realization.
- [ ] Multi-parent worldline revision dispatches to IC merge or fails with typed merge-required error.
- [ ] Assignment-selection merge remains separate from IC merge.
- [ ] Web revision support, if present, is read-only and app-backed.
- [ ] Proposal and docs are updated to match implemented behavior.

---

## Done Means Done

This workstream is not complete until the production path is single-path:

- formal decision in `belief_set`
- optional formal AF decision in `argumentation`
- Propstore projection and support realization
- app/CLI/web presentation
- worldline capture/replay

If Propstore still contains a parallel local formal decision engine, this
workstream remains OPEN.

---

## What This Workstream Does Not Do

- Does not implement formal AGM kernels in Propstore.
- Does not implement Hansson, Grove, Levi/Harper, KM update, or `Delta^Max` in
  Propstore.
- Does not add web mutation or journal-capture UI before app/CLI result
  contracts stabilize.
- Does not pin dependencies to local filesystem paths.
- Does not preserve old and new revision decision paths in parallel.
