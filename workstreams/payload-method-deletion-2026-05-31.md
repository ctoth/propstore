# Cleanup Refactor Fixed-Point Log - 2026-05-31

Target architecture:
- No class method named `to_payload` or `from_payload` remains in this codebase.

Forbidden surfaces:
- Class methods named `to_payload`.
- Class methods named `from_payload`.

Search gates:
- `rg -n -F "def to_payload" propstore tests`
- `rg -n -F "def from_payload" propstore tests`

Runtime gates:
- None. The user requested deleting the methods and explicitly directed test failures to be ignored.

## Iteration 1 - `repo class methods`

Slice read:
- `scripts/rope_rename.py`
- `propstore/core/assertions/codec.py`
- `propstore/conflict_detector/models.py`
- `propstore/families/contexts/stages.py`
- `tests/builders.py`

Surfaces:
- Class methods named `to_payload` or `from_payload`
  - Disposition: delete
  - Owner after cleanup: none
  - Action: deleted 50 class methods using a Rope `Project` resource rewrite script, then removed the temporary script.
  - Evidence: dry run and applied run listed 46 `to_payload` methods and 4 `from_payload` methods.

Gate results:
- Pass: `rg -n -F "def to_payload" . -g "*.py" --glob "!pyghidra_mcp_projects/**"` returned no matches.
- Pass: `rg -n -F "def from_payload" . -g "*.py" --glob "!pyghidra_mcp_projects/**"` returned no matches.

Commit:
- Blocked: `propstore/core/assertions/codec.py` and `tests/test_situated_assertion_codec.py` had pre-existing tracked changes before this work. A path-limited commit for those files would include changes that were not part of this deletion request.

Next slice:
- None for class method definitions.
