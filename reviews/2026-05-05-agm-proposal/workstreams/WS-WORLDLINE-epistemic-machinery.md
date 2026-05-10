# WS-WORLDLINE: Executable epistemic machinery workstreams

**Status**: OPEN
**Depends on**: `233361ac` deletion-first Propstore/belief-set cutover
**Blocks**: rigorous worldline revision replay, policy-auditable epistemic state, IC merge at multi-parent worldlines, web/app revision inspection
**Owner**: Propstore implementation owner, with `belief-set` dependency owner for formal kernel changes

---

## Why this exists

The deletion-first cutover removed the old Propstore operator surface:

- `propstore/support_revision/operators.py` is deleted.
- `propstore/support_revision/belief_dynamics.py` is deleted.
- Production `expand_belief_base`, `contract_belief_base`, and `revise_belief_base` names are guarded against returning.
- `BoundWorld` and journal `dispatch` call `belief_set_adapter.decide_*` directly, then realize the result over Propstore support and worldline objects.

That is cleaner, but it is not the end state. Propstore is not CRUD over entity files with revision tacked on. The operating surface is a semantic system: source promotion, support projection, ATMS, argumentation, probabilistic evidence, policies, worldlines, journals, replay, app/CLI/web surfaces, and formal dependencies all participate.

These workstreams make that machinery executable.

---

## Source Documents

Use these local notes as source documents before implementing the relevant workstream. Do not rely on PDF text extraction for rereads.

- `papers/Dixon_1993_ATMSandAGM/notes.md`
- `papers/Falkenhainer_1987_BeliefMaintenanceSystem/notes.md`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/notes.md`
- `papers/Baumann_2019_AGMContractionDung/notes.md`
- `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md`
- `papers/Thimm_2020_ApproximateReasoningASPICArgumentSampling/notes.md`
- `../belief-set/papers/Alchourron_1985_TheoryChange/notes.md`
- `../belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md`
- `../belief-set/papers/Grove_1988_TwoModellingsTheoryChange/notes.md`
- `../belief-set/papers/Hansson_1989_NewOperatorsTheoryChange/notes.md`
- `../belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`

---

## Dependency Order

Execute in this order unless a later workstream is explicitly split by the owner.

| Order | Workstream | Depends on | Primary outcome |
|---:|---|---|---|
| 1 | WS-WL-1 Revision Event Contract | deletion-first cutover | One typed event object for decision plus realization plus replay metadata |
| 2 | WS-WL-2 Policy And Ranking Provenance | WS-WL-1 | Ranking/default policy is explicit, hashed, replay-checked |
| 3 | WS-WL-3 Replay Property Suite | WS-WL-1, WS-WL-2 | Hypothesis tests prove replay/content-hash/policy sensitivity |
| 4 | WS-WL-4 Multi-Parent IC Merge | WS-WL-1, WS-WL-2 | Merge points use formal IC merge or typed merge-required failure |
| 5 | WS-WL-5 Support Realization Postulates | WS-WL-1, WS-WL-3 | Support incision has named postulates and executable properties |
| 6 | WS-WL-6 Argumentation And Evidence Views | WS-WL-1, WS-WL-3, WS-WL-5 | ATMS/ASPIC/PRAF views consume revision events without silent drops |

---

## Global Non-Negotiables

- Do not reintroduce `support_revision.operators`, `support_revision.belief_dynamics`, or production `*_belief_base` operator entrypoints.
- Do not implement formal AGM, IC merge, Grove spheres, Hansson contraction, or Spohn OCF kernels inside Propstore.
- Do not add compatibility aliases, fallback readers, duplicate old/new paths, or bridge shims.
- Do not treat worldlines as CRUD records. Worldlines are semantic traces with policy, support, evidence, argumentation, and replay consequences.
- Do not call assignment-selection merge formal IC merge.
- Do not let CLI, web, source promotion, or worldline code import `belief_set`.
- If a formal dependency is missing, update and push the dependency first, then pin Propstore to a pushed remote tag or immutable commit.

---

## WS-WL-1: Revision Event Contract

**Goal**: Make revision events the central Propstore object. A revision event is not just a result payload; it is the audit unit for worldline epistemic change.

**Owned surfaces**:

- `propstore/support_revision/state.py`
- `propstore/support_revision/snapshot_types.py`
- `propstore/support_revision/history.py`
- `propstore/support_revision/dispatch.py`
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/revision_types.py`
- `propstore/app/world_revision.py`
- `propstore/cli/world/revision.py`

**Red tests first**:

- Add `tests/test_revision_event_contract.py`.
- Add `tests/test_worldline_revision_event_capture.py`.
- Add a failing test that an event contains:
  - pre-state snapshot hash
  - input atom or target ids
  - formal decision report
  - support realization report
  - policy snapshot
  - replay status
  - realization failure, if realization fails after formal decision
- Add a failing test that `capture_revision_state` stores the event, not only a flattened result.

**Implementation tasks**:

- Introduce a typed `RevisionEvent` or `RevisionEpisodeEvent` dataclass.
- Move journal metadata from incidental result fields into the event.
- Make `dispatch` return an epistemic state whose latest history item carries the event.
- Make `WorldlineRevisionState` serialize the event contract.
- Keep app and CLI as adapters over the typed event. They may render, but not invent event semantics.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-event tests/test_revision_event_contract.py tests/test_worldline_revision_event_capture.py tests/test_worldline_revision.py tests/test_capture_journal.py tests/test_journal_entry_contract.py
```

**Done checks**:

- Worldline capture and journal replay expose the same event fields.
- A formal decision produced before realization failure is still inspectable.
- No production import of `belief_set` exists outside `propstore.support_revision.belief_set_adapter`.

---

## WS-WL-2: Policy And Ranking Provenance

**Goal**: Make ranking and entrenchment policy explicit. Spohn-style defaults and support-derived ordering must not be invisible implementation choices.

**Owned surfaces**:

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/entrenchment.py`
- `propstore/support_revision/history.py`
- `propstore/policies.py`
- `propstore/worldline/revision_capture.py`
- `propstore/support_revision/dispatch.py`

**Red tests first**:

- Add `tests/test_revision_policy_provenance.py`.
- Add a failing test that synthesized Spohn rankings are marked as defaulted in the formal decision report trace.
- Add a failing test that replay rejects a journal whose ranking or entrenchment policy version does not match the event.
- Add a failing test that changing ranking policy changes either the event policy hash or the replay verdict.

**Implementation tasks**:

- Add an explicit ranking policy payload to revision events.
- Tag `_distance_ranked_state` outputs as defaulted, including method name and input hash.
- Include ranking and entrenchment policy hashes in `FormalRevisionDecisionReport.trace` or event metadata.
- Update `dispatch._required_policy_snapshot` to validate values, not just key presence.
- Preserve old journals only if they are explicitly rejected as legacy/unsupported; do not add silent compatibility.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-policy tests/test_revision_policy_provenance.py tests/test_policy_governance.py tests/test_capture_journal.py tests/test_replay_determinism_actually_replays.py
```

**Done checks**:

- Defaulted ranking is visibly defaulted.
- Policy mismatch fails before semantic replay.
- Policy profile identity changes when revision ranking policy changes.

---

## WS-WL-3: Replay Property Suite

**Goal**: Use Hypothesis to prove the worldline machinery is stable under replay, sensitive to real changes, and insensitive to irrelevant serialization ordering.

**Owned surfaces**:

- `tests/test_worldline_revision_properties.py`
- `tests/test_revision_event_contract.py`
- `tests/test_capture_journal.py`
- `tests/test_replay_determinism_actually_replays.py`
- supporting fixtures under `tests/fixtures/` or `tests/support_revision/`

**Red tests first**:

- Generate small belief bases with assumptions, assertions, support sets, and conflict maps.
- Generate one-shot and iterated revision event sequences.
- Add failing properties for:
  - replay determinism
  - event serialization round trip
  - content hash changes when decision, realization, or policy changes
  - content hash stability under mapping-order changes
  - accepted and rejected sets are disjoint
  - replayed latest state equals direct dispatch latest state

**Implementation tasks**:

- Build reusable Hypothesis strategies for Propstore revision states.
- Keep strategies small enough to avoid exponential formal-kernel blowups.
- Use explicit `max_candidates` in every generated revision operation.
- Add regression examples from discovered counterexamples.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-properties tests/test_worldline_revision_properties.py tests/test_revision_properties.py tests/test_capture_journal.py tests/test_replay_determinism_actually_replays.py
```

**Done checks**:

- Property tests cover expand, contract, revise, and iterated revise.
- Counterexample examples are committed when Hypothesis finds a bug.
- Tests fail if event hashes ignore policy or realization.

---

## WS-WL-4: Multi-Parent IC Merge

**Goal**: Multi-parent worldlines must use formal IC merge under integrity constraints, or fail with a typed merge-required result. They must not accidentally run iterated revision.

**Owned surfaces**:

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/dispatch.py`
- `propstore/support_revision/iterated.py`
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/revision_types.py`
- `propstore/world/bound.py`

**Red tests first**:

- Add `tests/test_worldline_ic_merge.py`.
- Add a failing test that a state with two `merge_parent_commits` does not enter iterated revise.
- Add a failing test that a merge operation calls `decide_ic_merge` with:
  - profile formulas for parent states
  - an explicit integrity constraint
  - max alphabet budget
- Add a failing test that absent integrity constraints produce a typed merge-required failure, not a generic exception.

**Implementation tasks**:

- Decide whether current `belief_set_adapter.decide_ic_merge` has enough reverse mapping to realize merged atoms. If not, update `belief-set` and adapter first.
- Add a worldline revision operation for merge, separate from iterated revise.
- Store parent profile ids and integrity constraint ids in the revision event.
- Keep assignment-selection merge separate and unchanged.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge tests/test_worldline_ic_merge.py tests/test_revision_merge_uses_ic_merge.py tests/test_worldline_revision.py tests/test_journal_entry_contract.py
```

**Done checks**:

- Multi-parent iterated revise fails with typed merge-required result.
- IC merge events record profile, constraint, formal decision, and realization.
- No assignment-selection merge tests change meaning.

---

## WS-WL-5: Support Realization Postulates

**Goal**: Name and test Propstore support realization as its own layer. It is not formal AGM, but it must have explicit postulates grounded in ATMS/AGM and argument-change papers.

**Owned surfaces**:

- `propstore/support_revision/realization.py`
- `propstore/support_revision/entrenchment.py`
- `propstore/support_revision/explain.py`
- `tests/test_support_realization_postulates.py`
- `tests/test_revision_operators.py`

**Red tests first**:

- Add properties for:
  - incision success: rejected supported targets lose every support set
  - minimality: no strict subset of the incision set realizes the same target rejection under the same support sets
  - entrenchment direction: among equal-size cuts, less entrenched support is cut
  - cascade: descendants with no surviving support are rejected
  - preservation: independent supported atoms survive
  - no recovery promise for AF/Dung contraction
- Add examples from Dixon 1993, Rotstein 2008, and Baumann 2019 notes where applicable.

**Implementation tasks**:

- Rename private support helper names if needed to stop implying formal AGM ownership.
- Keep hitting-set enumeration as support realization only.
- Make budget exhaustion return or preserve formal decision information through event failure from WS-WL-1.
- Add explanation fields for why each cut was selected.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-support-postulates tests/test_support_realization_postulates.py tests/test_revision_operators.py tests/test_revision_explain.py tests/remediation/phase_8_dos_anytime/test_T8_1_choose_incision_set_ceiling.py
```

**Done checks**:

- Tests document the layer as support realization, not AGM contraction.
- No test or doc claims Harper recovery for AF/Dung contraction.
- Enumeration failure preserves formal decision context through the revision event.

---

## WS-WL-6: Argumentation And Evidence Views

**Goal**: Revision events must feed Propstore's non-CRUD reasoning machinery: ATMS, ASPIC, abstract argumentation, PRAF, evidence/provenance, app/CLI/web projections.

**Owned surfaces**:

- `propstore/support_revision/af_adapter.py`
- `propstore/world/atms.py`
- `propstore/argumentation*`
- `propstore/praf*`
- `propstore/app/world_revision.py`
- `propstore/cli/world/revision.py`
- web read-only revision views, if present

**Red tests first**:

- Add `tests/test_revision_argumentation_views.py`.
- Add a failing test that accepted assertion atoms with no source claims are reported as synthetic/unmapped, not silently dropped.
- Add a failing test that accepted assumption atoms are visible in the revision event even if not projected as arguments.
- Add a failing test that ASPIC/AF views preserve source claim ids for accepted assertions.
- Add a failing test that PRAF/argumentation outputs include enough event references to explain why a claim was accepted or rejected.

**Implementation tasks**:

- Add diagnostics for unmapped revision atoms in `project_epistemic_state_argumentation_view`.
- Thread revision event ids through argumentation and evidence reports.
- Keep approximation/sampling surfaces honest: sampled views may be approximate, but they must say so.
- Add read-only app/web payloads for event inspection before adding mutating UI.

**Verification**:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-argumentation-evidence tests/test_revision_argumentation_views.py tests/test_revision_af_adapter.py tests/test_aspic_bridge.py tests/test_praf.py tests/test_revision_cli.py tests/test_web_revision_readonly.py
```

**Done checks**:

- No accepted revision atom disappears without a diagnostic.
- Argumentation views reference revision event ids or source claim ids.
- App/CLI/web surfaces render decision, realization, policy, and diagnostics as separate facts.

---

## Cross-Workstream Final Gate

Run this after all six workstreams are complete.

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-final tests/
```

Final state must satisfy:

- `propstore.support_revision.belief_set_adapter` is still the only production `belief_set` import edge.
- `support_revision.operators` and `support_revision.belief_dynamics` are absent.
- Worldline revision events are the audit unit for one-shot, iterated, and merge revision.
- Replay is deterministic, policy-checked, and hash-sensitive to decision, realization, and policy.
- Multi-parent worldlines use IC merge or typed merge-required failure.
- Support realization postulates are executable and do not claim formal AGM ownership.
- Argumentation/evidence views expose unmapped or approximate facts honestly.
