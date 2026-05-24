# 08 Justification And Payload Boundaries

## Final State

Justification semantic views are typed family/graph behavior. A duplicate
`CanonicalJustification` schema/conversion family does not remain as a second
justification model.

Payload parsing lives at named IO/parser boundaries. Active runtime, family,
core, world, and worldline modules do not carry broad `_from_payload` helpers.

## Delete First

- Delete `CanonicalJustification(` construction paths outside the final typed
  justification/graph semantic owner.
- Delete the duplicate `CanonicalJustification` schema/conversion role in
  `propstore/core/justifications.py`.
- Delete `_claim_algorithm_variable_from_payload` as a broad helper name.

## Repair Owners

- Justification family: persisted and typed justification behavior.
- Active graph/world/ASPIC owners: explicit semantic view over typed
  justification and graph models.
- Claim algorithm owner: named parser boundary for algorithm variable input.

## Search Gates

```powershell
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "CanonicalJustification" propstore/core propstore/aspic_bridge tests
rg -n -F -- "_from_payload" propstore/families/claims propstore/core tests
rg -n -F -- "_from_payload" propstore/families propstore/core propstore/world propstore/worldline tests
```

`CanonicalJustification(` is zero-hit unless one final semantic view owner is
named in this file during execution. `_from_payload` is zero-hit in active
runtime/family/core/world/worldline surfaces.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label justification-payload-boundaries tests/test_aspic_bridge.py tests/test_structured_projection.py tests/test_ws_f_aspic_bridge.py tests/test_defeasibility_aspic_integration.py tests/test_world_query.py
```

## Completion

- [ ] Duplicate canonical justification schema/conversion role is deleted.
- [ ] Kept justification view behavior has one typed semantic owner.
- [ ] Broad `_from_payload` helpers are gone from active runtime/family/core
      surfaces.
- [ ] Search, type, and test gates pass.
