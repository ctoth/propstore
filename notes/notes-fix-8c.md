# Fix 8C: Resource Leaks — Session Notes

## GOAL
TDD fix for sqlite3 connection leaks in CLI commands (claim.py embed/relate, concept.py embed/search).

## DONE
- RED test written in tests/test_cli.py::TestConnectionClosedOnError
- Fixed all 4 locations with contextlib.closing() in claim.py and concept.py
- RED test confirmed failing before fix

## STUCK
- Test still failing after fix. The mock patch target `sqlite3.connect` isn't being intercepted.
- The `import sqlite3` is inside the function body of `claim.py embed`. Patching `sqlite3.connect` globally should work, but CliRunner may be doing something odd, or the patch target needs to be module-specific.
- Need to check: is `contextlib.closing` actually calling close? Or is the mock not being used at all?

## NEXT
- Debug: check if `sqlite3.connect` patch is actually intercepted by adding a print or checking mock_connect.called
- May need to patch `propstore.cli.claim.sqlite3` instead of top-level `sqlite3`
