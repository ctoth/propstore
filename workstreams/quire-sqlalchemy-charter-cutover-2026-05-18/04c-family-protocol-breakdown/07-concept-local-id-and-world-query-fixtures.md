# 07 Concept Local Id And World Query Fixtures

## Final State

Numeric concept handles are concept-family identity policy backed by generic
Quire local-id reservation. Root `propstore/concept_ids.py` is gone.

World-query tests construct typed claim/domain fixtures. They do not mutate
claim dictionaries with `claim["..."]`.

## Delete First

- Delete root `propstore/concept_ids.py` after Quire reservation support exists.
- Delete root imports of `candidate_concept_id_for_repo` and
  `reserve_concept_id_candidate`.
- Delete `tests/test_world_query.py` dict-shaped claim mutation helpers.

## Repair Owners

- Concept family identity owner: numeric concept handle parsing/reservation and
  local-id policy.
- Quire family metadata: generic local-id reservation/counter mechanics.
- Tests: typed family/domain fixtures.

## Search Gates

```powershell
rg -n -F -- "propstore.concept_ids" propstore tests
rg -n -F -- "candidate_concept_id_for_repo" propstore tests
rg -n -F -- "reserve_concept_id_candidate" propstore tests
rg -n -F -- "select_concept_ids_for_group" propstore tests
rg -n -F -- "search_concept_ids" propstore tests
rg -n -F -- "resolve_sidecar_concept_id" propstore tests
rg -n -F -- 'claim["' tests/test_world_query.py
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label concept-local-id-fixtures tests/test_concept_workflows.py tests/remediation/phase_7_race_atomicity/test_T7_4_concept_id_counter.py tests/test_world_query.py
```

## Completion

- [ ] Root concept-id module is deleted.
- [ ] Concept local-id behavior is concept-family identity behavior backed by
      Quire reservation.
- [ ] World-query tests use typed fixtures.
- [ ] Search, type, and test gates pass.
