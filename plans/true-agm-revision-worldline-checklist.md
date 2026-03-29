# True AGM Revision — Worldline Checklist

**Date:** 2026-03-29
**Depends on:** `proposals/true-agm-revision-proposal.md`
**Scope:** concrete implementation checklist for revision-aware worldline capture and replay
**Status:** Implemented

---

## Goal

Add explicit worldline support for revision episodes without collapsing one-shot results, iterated state, and merge behavior into a single ambiguous payload.

Deliverables:

- `WorldlineDefinition.revision`
- `WorldlineResult.revision`
- revision-aware capture in `propstore/worldline_runner.py`
- tests for serialization, hashing, capture, and merge-point refusal

---

## Contract Decisions

### 1. Query/result separation

`WorldlineDefinition` owns the requested revision operation.

`WorldlineResult` owns the materialized revision outcome.

Do not infer the query from the result payload or vice versa.

### 2. Query shape

Add a dedicated revision query block with the smallest surface that matches the existing revision APIs:

- `operation`
  - `expand`
  - `contract`
  - `revise`
  - `iterated_revise`
- `atom`
  - required for `expand`, `revise`, `iterated_revise`
- `target`
  - required for `contract`
- `conflicts`
  - optional for `revise` and `iterated_revise`
- `operator`
  - optional and only meaningful for `iterated_revise`

### 3. Result shape

Store a structured `revision` payload on `WorldlineResult`:

- `operation`
- `input_atom_id`
- `target_atom_ids`
- `result`
  - `accepted_atom_ids`
  - `rejected_atom_ids`
  - `incision_set`
  - `explanation`
- `state`
  - omitted for one-shot operations
  - `epistemic_state_payload(...)` for iterated revision

### 4. Replay rule

Persist:

- episode result fields directly
- explicit iterated-state summary when present

Do not persist:

- only a raw opaque state blob
- only a partial summary that cannot distinguish one-shot from iterated output

### 5. Staleness rule

Revision payloads must participate in `compute_worldline_content_hash(...)`.

If revision-relevant support, claim, ranking, or history changes, rerunning the worldline must produce a different hash.

### 6. Merge boundary

Worldline revision capture must preserve the same refusal behavior as the revision package:

- merge points do not run revision
- refusal must surface as an explicit error payload, not silent omission

---

## Checklist

### 1. Add worldline revision dataclasses/parsing

Primary file:

- `propstore/worldline.py`

Tasks:

- add `WorldlineRevisionQuery` or equivalent
- add optional `revision` field to `WorldlineDefinition`
- add optional `revision` field to `WorldlineResult`
- update `from_dict(...)`
- update `to_dict(...)`
- update `compute_worldline_content_hash(...)`

Acceptance:

- query and result payloads round-trip cleanly
- one-shot and iterated result payloads stay distinguishable

### 2. Add worldline runner capture path

Primary file:

- `propstore/worldline_runner.py`

Tasks:

- detect explicit `definition.revision`
- call the existing `BoundWorld` revision surface:
  - `expand(...)`
  - `contract(...)`
  - `revise(...)`
  - `iterated_revise(...)`
- capture result payload in `WorldlineResult.revision`
- preserve existing value/step/dependency behavior

Acceptance:

- revision capture is opt-in
- existing non-revision worldlines are unchanged

### 3. Define error/refusal behavior

Primary file:

- `propstore/worldline_runner.py`

Tasks:

- surface merge-point refusal in the `revision` payload
- surface malformed revision query errors clearly
- do not swallow revision capture exceptions silently

Acceptance:

- failures are visible in result payloads and logs

### 4. Add tests

Primary files:

- `tests/test_worldline_revision.py`
- optionally `tests/test_worldline.py`

Core tests:

- `WorldlineDefinition` round-trips an explicit revision query block
- `WorldlineResult` round-trips a revision result payload
- content hash changes when revision payload changes
- `run_worldline(...)` captures one-shot revision payloads
- `run_worldline(...)` captures iterated revision payloads with state summary
- merge-point refusal is explicit in the revision payload

### 5. Defer what is still not part of this slice

Do not do here:

- implicit revision for ordinary worldlines
- merge-object revision
- worldline-driven AF-level revision
- revision-aware CLI authoring sugar beyond whatever already exists for worldlines

Acceptance:

- worldline integration remains a thin replay/capture layer over the existing revision package
