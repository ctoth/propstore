# WS-WL-7: IC merge realization for multi-parent worldlines

**Status**: OPEN
**Depends on**: `WS-WORLDLINE` workstreams 1-6, pushed `belief-set` IC merge kernel
**Blocks**: realized multi-parent worldline revision, replayable IC merge journals, argumentation/evidence inspection for merged worldlines
**Owner**: Propstore implementation owner, with `belief-set` dependency owner only if the formal kernel lacks required selected-world metadata

---

## Why this exists

`WS-WL-4` made multi-parent worldlines deletion-first and honest: they no longer fall through to iterated revision. They either invoke the formal IC merge adapter or fail with `RevisionMergeRequiredFailure`.

That is still not the end state. The formal dependency currently returns an IC merge decision over interpretations. Propstore must now realize that decision back into its own epistemic state without inventing formal merge semantics locally and without treating worldline merge as CRUD over atom ids.

This workstream makes the missing step executable:

- formal IC merge chooses integrity-constraint-satisfying interpretations;
- Propstore maps the chosen interpretation(s) back to known support-revision atoms;
- support, ATMS labels, argumentation visibility, replay metadata, and event hashes remain inspectable;
- unmappable or ambiguous formal results fail typed and preserve the formal decision.

---

## Source Documents Read From Page Images

These notes are grounded in direct page-image reads, not PDF text extraction.

### Konieczny and Pino Perez 2002

Path:

- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-000.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-001.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-002.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-003.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-004.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-005.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-006.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-007.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-008.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-009.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-010.png`
- `../belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-011.png`

Implementation constraints from the page images:

- The merge input is a multiset of source belief bases, not a set that erases repeated sources.
- The operator takes two inputs: a profile and explicit integrity constraints.
- The output must satisfy the integrity constraints when they are satisfiable.
- If the conjunction of the profile and the integrity constraint is consistent, the result should be that conjunction.
- The model-theoretic representation is over interpretations/worlds; the result is the minimal IC-satisfying interpretations under the profile preorder.
- Majority and arbitration are different operator families; Propstore must record which formal operator produced the decision.
- The page-004 IC0-IC8 postulates are the executable paper contract for generated properties.
- Theorem 3.7 on page-007 ties IC merging to selecting minimal models of the integrity constraint under a syncretic assignment. Propstore realization must therefore consume selected worlds; it must not re-run an ad hoc local merge.

### Dixon and Foo 1993

Path:

- `papers/Dixon_1993_ATMSandAGM/pngs/page-000.png`
- `papers/Dixon_1993_ATMSandAGM/pngs/page-001.png`
- `papers/Dixon_1993_ATMSandAGM/pngs/page-002.png`

Implementation constraints from the page images:

- ATMS beliefs are accepted through support environments and labels, not just by toggling proposition membership.
- Labels must be consistent, sound, complete, and minimal.
- Assumptions are foundational beliefs; realization must preserve the distinction between accepted assertion atoms and active assumptions.
- Support realization may use AGM-style machinery operationally, but Propstore must keep support/label semantics explicit.

### Rotstein et al. 2008

Path:

- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/pngs/page-000.png`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/pngs/page-001.png`
- `papers/Rotstein_2008_ArgumentTheoryChangeRevision/pngs/page-004.png`

Implementation constraints from the page images:

- Argument theory change separates the universal argument pool from the currently active arguments.
- Activating or deactivating arguments propagates through subargument structure.
- Revision can be viewed as expansion followed by contraction, but the contraction choice is where minimal-change behavior lives.
- Propstore realization must expose inactive/unmapped facts rather than silently dropping them from argumentation views.

### Modgil and Prakken 2014

Path:

- `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/pngs/page-000.png`
- `papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/pngs/page-001.png`

Implementation constraint from the page images:

- The first rendered pages were cover/link pages rather than substantive formal content. Do not use them as evidence for implementation details in this workstream. Use existing ASPIC bridge tests and `WS-WL-6` for structured-argumentation surface constraints unless later page images are reread directly.

---

## Global Non-Negotiables

- Do not implement IC merge, distance scoring, syncretic assignment, or KPP postulates inside Propstore.
- Do not reintroduce `support_revision.operators`, `support_revision.belief_dynamics`, or production `*_belief_base` entrypoints.
- Do not call assignment-selection merge from this workstream.
- Do not let CLI, web, source promotion, worldline, ATMS, or argumentation code import `belief_set`.
- Keep `propstore.support_revision.belief_set_adapter` as the only production `belief_set` import edge.
- Do not add compatibility shims for the current `realization_not_implemented` behavior.
- If `belief-set` must expose more selected-world metadata, update and push `belief-set` first, then pin Propstore to a pushed immutable commit.
- Every red test must fail on the current `realization_not_implemented` path before implementation.
- Use Hypothesis for generated profile/worldline/replay properties.

---

## Target Architecture

The target flow is:

1. `dispatch(JournalOperator.IC_MERGE, ...)` validates policy, profile ids, parent ids, and explicit IC payload.
2. `belief_set_adapter.decide_ic_merge_profile(...)` projects the profile to formal formulas and calls the formal IC merge kernel.
3. The formal decision report records:
   - operator: `ic_merge`
   - formal policy, including `sigma` or `gmax`
   - profile atom ids as a multiset
   - integrity constraint payload and normalized formula ids
   - selected worlds or selected-world hash
   - scored worlds hash
   - accepted and rejected formula ids
4. `realize_ic_merge_decision(...)` maps every selected world back to Propstore atoms.
5. If the selected worlds define one exact Propstore atom valuation, a new `EpistemicState` is produced.
6. If selected worlds are disjunctive, ambiguous, or contain formal atoms with no Propstore atom, realization fails typed with the formal decision preserved.
7. The revision event records decision, realization or failure, parent profile ids, IC payload, policy snapshot, replay status, and content hash.
8. Replay recomputes the same decision and realized state, and rejects profile, IC, policy, or selected-world drift before claiming success.

---

## Owned Surfaces

- `propstore/support_revision/belief_set_adapter.py`
- `propstore/support_revision/dispatch.py`
- `propstore/support_revision/realization.py`
- `propstore/support_revision/state.py`
- `propstore/support_revision/snapshot_types.py`
- `propstore/support_revision/history.py`
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/revision_types.py`
- `propstore/support_revision/af_adapter.py`
- `propstore/app/world_revision.py`
- `propstore/cli/world/revision.py`
- `tests/test_worldline_ic_merge.py`
- new `tests/test_worldline_ic_merge_realization.py`
- new `tests/test_worldline_ic_merge_properties.py`

---

## Phase 1: Formal Decision Metadata Contract

### Red tests first

Add to `tests/test_worldline_ic_merge_realization.py`:

- `test_ic_merge_decision_report_records_profile_multiset_and_integrity_constraint`
- `test_ic_merge_decision_report_records_selected_worlds_hash`
- `test_ic_merge_decision_report_records_formal_operator_family`
- `test_ic_merge_decision_preserves_duplicate_profile_members`

The duplicate-profile test is required by KPP page-001/page-003: belief sets are multisets, and majority behavior can depend on repetition.

### Implementation tasks

- Extend `decide_ic_merge_profile(...)` to accept an explicit `merge_operator` value, defaulting only where current policy explicitly says so.
- Preserve `profile_atom_ids` as `tuple[tuple[str, ...], ...]` in the report trace.
- Add selected-world and scored-world hashes to `FormalRevisionDecisionReport.trace`.
- Add normalized `integrity_constraint` payload to the report trace.
- Keep raw formal world objects out of app-facing payloads unless a stable JSON projection exists.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-metadata tests/test_worldline_ic_merge.py tests/test_worldline_ic_merge_realization.py
```

### Done checks

- Formal decision metadata is sufficient to audit KPP profile, IC, operator family, selected worlds, and scored worlds.
- Duplicate profile entries survive all Propstore projections.
- No non-adapter production module imports `belief_set`.

---

## Phase 2: Exact Realization For Single-Valuation Results

### Red tests first

Add examples to `tests/test_worldline_ic_merge_realization.py`:

- `test_realizable_ic_merge_returns_epistemic_state_instead_of_realization_not_implemented`
- `test_realized_ic_merge_accepts_exact_atoms_from_selected_world`
- `test_realized_ic_merge_rejects_atoms_false_in_selected_world`
- `test_realized_ic_merge_preserves_support_for_surviving_atoms`
- `test_realized_ic_merge_records_realization_report_in_event`

Minimal example:

- parent 1 supports `a`;
- parent 2 supports `b`;
- IC requires `a`;
- formal selected world makes `a` true and `b` false;
- realized Propstore state accepts `a`, rejects `b`, and records why.

### Implementation tasks

- Add `realize_ic_merge_decision(base, decision, ...)` in `propstore/support_revision/realization.py`.
- Reuse existing `SupportRevisionRealization` and `RevisionAtomDetail` rather than creating a parallel report type unless the existing report cannot represent merge.
- Add a `selection_rule`, for example `ic_merge_selected_world`.
- Preserve surviving support sets for accepted atoms.
- Mark rejected atoms with a merge-specific reason such as `ic_merge_world_false`.
- Thread the realization into `RevisionEvent`.
- Replace `dispatch`'s current `realization_not_implemented` failure with this realization path.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-realization tests/test_worldline_ic_merge.py tests/test_worldline_ic_merge_realization.py tests/test_revision_event_contract.py tests/test_worldline_revision_event_capture.py
```

### Done checks

- A realizable single-world IC merge produces an `EpistemicState`.
- The event has formal decision and support realization fields.
- Accepted/rejected atom ids match the selected world valuation exactly.
- The old `realization_not_implemented` path is deleted, not wrapped.

---

## Phase 3: Typed Failures For Unrealisable Formal Results

### Red tests first

Add:

- `test_disjunctive_selected_worlds_fail_with_typed_ambiguous_realization`
- `test_selected_world_with_unknown_formal_atom_fails_typed`
- `test_unsatisfiable_integrity_constraint_preserves_formal_decision`
- `test_unrealizable_merge_failure_event_preserves_selected_world_hash`
- `test_unrealizable_merge_failure_is_replayable_as_failure`

### Implementation tasks

- Extend `RevisionMergeRequiredFailure` with structured fields:
  - `reason`
  - `parent_commits`
  - `decision_report`
  - `profile_atom_ids`
  - `integrity_constraint`
  - `selected_worlds_hash`
- Use reason values:
  - `ambiguous_selected_worlds`
  - `unmapped_formal_atom`
  - `unsatisfiable_integrity_constraint`
  - `empty_selected_worlds`
- Ensure the exception message remains stable for existing merge-point callers.
- Store failed realization details in `RevisionEvent.realization_failure`.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-failures tests/test_worldline_ic_merge_realization.py tests/test_worldline_ic_merge.py tests/test_journal_entry_contract.py
```

### Done checks

- Every impossible realization preserves the formal decision.
- No failure degenerates into a generic `ValueError` or `RuntimeError`.
- Replay can reproduce the same typed failure without hiding the original formal decision.

---

## Phase 4: Hypothesis Property Suite

### Red tests first

Create `tests/test_worldline_ic_merge_properties.py`.

Strategies must generate small bounded cases only:

- alphabet size: 1-5 atoms;
- profile size: 1-4 members;
- profile member atoms as tuples preserving duplicates;
- IC payloads: `top` or single atom initially;
- operator family: `sigma`, `gmax`;
- selected worlds constrained to small signatures.

Properties:

- IC0: realized accepted atom set always satisfies the IC when IC is satisfiable and realization succeeds.
- IC2: when the conjunction of the profile and IC is consistent and single-valued, realization equals that conjunction.
- Profile multiset sensitivity: duplicate profile entries are preserved through report hashing.
- Replay determinism: direct dispatch and journal replay produce the same latest state or the same typed failure.
- Hash sensitivity: event content hash changes when profile, IC, selected worlds, realization, or policy changes.
- Mapping totality: realization succeeds iff every formal atom in the selected valuation maps to a known Propstore atom and the selected worlds define one exact valuation.
- Accepted/rejected partition: accepted and rejected atom ids are disjoint and cover the projected merge alphabet when realization succeeds.
- Assignment-selection separation: generated IC merge tests must not call assignment-selection merge entrypoints.

### Implementation tasks

- Add small helper strategies near the tests, not in production code.
- Use explicit `max_candidates` or `max_alphabet_size` in every generated call.
- Add `@example(...)` cases for:
  - KPP page-002 two-expert all-rise/all-fall style conflict;
  - KPP page-004 IC2 conjunction case;
  - ambiguous two-world result that must fail typed.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-properties tests/test_worldline_ic_merge_properties.py tests/test_worldline_ic_merge_realization.py
```

### Done checks

- Hypothesis covers successful realization and typed-failure paths.
- Counterexamples become committed `@example` regressions.
- Generated tests stay below formal-kernel blowup thresholds.

---

## Phase 5: Replay, Journal, And Worldline Capture

### Red tests first

Add:

- `test_ic_merge_journal_replay_reconstructs_realized_state`
- `test_ic_merge_replay_rejects_profile_drift`
- `test_ic_merge_replay_rejects_integrity_constraint_drift`
- `test_ic_merge_replay_rejects_policy_drift_before_semantic_replay`
- `test_worldline_capture_serializes_ic_merge_event`

### Implementation tasks

- Extend journal operator input schema for IC merge with:
  - `profile_atom_ids`
  - `merge_parent_commits`
  - `integrity_constraint`
  - `merge_operator`
  - `max_alphabet_size`
- Ensure replay compares recorded event profile/IC/operator/policy to recomputed values.
- Extend `WorldlineRevisionState` serialization to render merge event fields distinctly from revise/contract fields.
- Keep old journals unsupported unless they contain complete typed merge event data.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-replay tests/test_capture_journal.py tests/test_journal_entry_contract.py tests/test_worldline_revision.py tests/test_worldline_ic_merge_realization.py
```

### Done checks

- IC merge replay is deterministic.
- Replay rejects drift before claiming a state match.
- Worldline capture exposes profile, IC, operator, formal decision, realization, and policy as separate facts.

---

## Phase 6: Argumentation, ATMS, And Evidence Views

### Red tests first

Add:

- `test_ic_merge_argumentation_view_reports_unmapped_merge_atoms`
- `test_ic_merge_argumentation_view_preserves_source_claim_ids`
- `test_ic_merge_atms_view_preserves_support_label_minimality`
- `test_ic_merge_rejected_atoms_explain_selected_world_false`
- `test_ic_merge_app_cli_payload_separates_decision_realization_policy_and_diagnostics`

### Implementation tasks

- Thread IC merge event hashes into argumentation/evidence projections.
- Ensure accepted assertions without source claims are reported as unmapped, not dropped.
- Ensure accepted assumptions remain visible even if not projected as ASPIC arguments.
- Keep ATMS support labels consistent, sound, complete, and minimal at the Propstore layer.
- Add read-only app/CLI renderers for merge event inspection.

### Verification

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-views tests/test_revision_argumentation_views.py tests/test_revision_af_adapter.py tests/test_revision_cli.py tests/test_web_revision_readonly.py tests/test_worldline_ic_merge_realization.py
```

### Done checks

- No accepted merge atom disappears without a diagnostic.
- Argumentation and evidence views can explain whether an atom was accepted by selected IC merge world, rejected by selected world, or unmapped.
- App/CLI/web surfaces do not invent merge semantics.

---

## Cross-Workstream Final Gate

Run after all phases complete:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label wl-ic-merge-final tests/test_worldline_ic_merge.py tests/test_worldline_ic_merge_realization.py tests/test_worldline_ic_merge_properties.py tests/test_capture_journal.py tests/test_journal_entry_contract.py tests/test_revision_argumentation_views.py tests/test_revision_cli.py tests/test_web_revision_readonly.py
powershell -File scripts/run_logged_pytest.ps1 -Label wl-final tests/
```

Final state must satisfy:

- Multi-parent worldlines with realizable IC merge produce a new `EpistemicState`.
- Non-realizable formal outputs fail typed and preserve the formal decision.
- Merge replay is deterministic and hash-sensitive to parent profile, IC, formal operator, selected worlds, realization, and policy.
- Duplicate profile members are preserved end-to-end.
- IC merge realization is separate from assignment-selection merge.
- Propstore does not implement formal IC merge logic locally.
- `propstore.support_revision.belief_set_adapter` is still the only production `belief_set` import edge.
- `support_revision.operators` and `support_revision.belief_dynamics` remain absent.
- Hypothesis properties cover success, ambiguity, unmapped formal atoms, policy drift, and replay determinism.

