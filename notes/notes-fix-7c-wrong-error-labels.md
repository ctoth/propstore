# Fix 7C: Wrong Error Labels

## GOAL
Fix `_validate_observation` to use actual claim type in error messages instead of hardcoded "observation".

## OBSERVATIONS
- Bug at `propstore/validate_claims.py` line 236-237: mechanism, comparison, limitation types call `_validate_observation`
- `_validate_observation` (line 513-529) hardcodes "observation" in two error messages:
  - `"observation claim '{cid}' missing 'statement'"` (line 519)
  - `"observation claim '{cid}' missing 'concepts'"` (line 523)
  - `"observation claim '{cid}' references nonexistent concept"` (line 528-529)
- Test file is `tests/test_validate_claims.py` (1501 lines)
- Helper `make_observation_claim` exists at line 59, hardcodes `type: "observation"`
- Need to add a `claim_type` param to `_validate_observation` and pass it from call sites

## DONE
- Read prompt, validation code, test file structure

## NEXT
1. Read end of test file to find insertion point
2. Write RED tests (mechanism/comparison/limitation missing statement → error says correct type)
3. Run tests to confirm RED
4. Implement fix in validate_claims.py
5. Run tests to confirm GREEN
6. Commit
