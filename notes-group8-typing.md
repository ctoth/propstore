# Group 8: Fix repo: object Typing

## GOAL
Change `repo: object | None` to `repo: Repository | None` in build_sidecar.py and validate.py, remove type: ignore comments.

## DONE
- Baseline: 841 passed
- Read both source files, confirmed Repository class in cli/repository.py
- Added Repository import to TYPE_CHECKING block in build_sidecar.py
- Added TYPE_CHECKING block with Repository import to validate.py

## REMAINING
- Change `repo: object | None` to `repo: Repository | None` (3 in build_sidecar.py, 1 in validate.py)
- Remove `# type: ignore[union-attr]` comments (3 in build_sidecar.py, 1 in validate.py)
- _prepare_claim_insert_row already has correct return type `-> dict[str, object]` (line 733)
- Verify no circular imports
- Run tests
- Commit

## FILES
- /c/Users/Q/code/propstore/propstore/build_sidecar.py — main target
- /c/Users/Q/code/propstore/propstore/validate.py — second target
- /c/Users/Q/code/propstore/propstore/cli/repository.py — Repository class source
