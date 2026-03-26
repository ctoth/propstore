# Overclaim Audit: Bounded Intervention Planner

## GOAL
Identify semantic risks where users read target OUT/next-query ranking as stronger than the replay substrate supports.

## DONE
- Read bound.py fully (BoundWorld surface API for interventions, stability, relevance, next-queryables)
- Read atms.py: _future_entries, _future_engine, _iter_future_queryable_sets, _concept_future_entries, _minimal_future_entries
- Read atms.py: node_interventions, claim_interventions, concept_interventions, next_queryables_for_node/claim/concept
- Read atms.py: _next_queryables_from_plans (the ranking logic)
- Read atms.py: _node_intervention_plan, _concept_intervention_plan (plan structure)
- Read atms.py: _coerce_node_target_status, _future_reaches_node_target

## KEY OBSERVATIONS

### Replay substrate is bounded combinatorial enumeration, NOT full ATMS context switching
- `_iter_future_queryable_sets` yields `combinations(normalized, width)` up to `limit` (default 8)
- This means it enumerates width-1, width-2, etc. subsets of queryables, stopping at `limit` total futures
- With e.g. 10 queryables and limit=8, only 10 singletons would be checked (and not even all of them — only 8)
- Width-2+ combos are silently skipped when limit is hit during width-1 enumeration

### _future_engine rebuilds an entirely new BoundWorld + ATMSEngine per future
- This is honest replay — it doesn't fake the result — but it's expensive and incomplete
- Each future adds queryable assumptions to the environment and rebuilds from scratch
- **The futures explored depend on the ORDER of combinations() which is lexicographic on queryable IDs**

### Intervention plans = "which futures reached the target status"
- `node_interventions` filters futures to those that are consistent AND match target status
- Then `_minimal_future_entries` prunes to set-inclusion-minimal queryable sets
- Plan includes `minimality_basis: "set_inclusion_over_queryable_ids"` — this is honest

### Next-query ranking = plan_count + smallest_plan_size
- `_next_queryables_from_plans` groups by individual queryable, counts how many plans contain it
- Sort key: `(smallest_plan_size, -plan_count, queryable_cel)`
- **This is a frequency heuristic over the explored subset, NOT an information-theoretic measure**

### CRITICAL OVERCLAIM RISKS IDENTIFIED

1. **"stable" when limit truncates exploration**: `concept_is_stable` / `claim_is_stable` return True if no witnesses found — but witnesses could exist beyond the limit. The `limit` field is in the stability report but the boolean `stable` doesn't qualify itself.

2. **Next-query ranking looks authoritative but is subset-dependent**: The ranking is entirely determined by which futures were enumerated. With limit=8 and many queryables, only width-1 combos are checked, so queryables that only matter in combination are invisible.

3. **"could_become_in: false" reads as "cannot become IN"**: The field name `could_become_in` is a positive claim about possibility, but it actually means "was not observed to become IN within the explored bound."

4. **Intervention plans say "sufficient" implicitly**: Each plan lists queryable_ids that, in the replayed future, achieved the target. But the user may read this as "these are sufficient in general" when they're sufficient only in the specific replay (same store, same claims, same conflicts).

5. **target_status=OUT for interventions requires NOGOOD_PRUNED**: `_future_reaches_node_target` checks `out_kind == NOGOOD_PRUNED` for OUT targets, silently filtering MISSING_SUPPORT futures. No documentation explains why or that this narrows the result.

## NEXT
- Write the three-section analysis
