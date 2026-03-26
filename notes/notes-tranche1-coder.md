# Tranche 1 Coder Notes

## GOAL
Add `status` field to stance files: `proposal` or `accepted`. Filter at build time.

## Key Files & Observations

1. **`propstore/relate.py:write_stance_file()` (line 463)** — writes stance YAML. Need to add `status: proposal` to each stance dict in the `stances` list.

2. **`propstore/build_sidecar.py:_populate_stances_from_files()` (line 93)** — reads stance YAML files. Need to add status validation: reject missing, skip proposal, load accepted.

3. **`propstore/build_sidecar.py:_populate_claims()` (line 804)** — inline stances in claim YAML. Same filtering needed.

4. **`propstore/validate_claims.py`** — validates claim files. Need to add stance status validation for inline stances.

5. **`propstore/cli/__init__.py`** — CLI entry point. Need to register new `proposal` command group.

6. **`propstore/cli/repository.py`** — Repository class has `stances_dir` property returning `root / "stances"`.

7. **Test fixtures** — `test_build_sidecar.py` uses `concept_dir` fixture with `tmp_path / "knowledge"`. `build_sidecar()` takes `repo` kwarg to get stances_dir.

## Build sidecar call chain
- `build_sidecar()` line 280: calls `_populate_stances_from_files(conn, repo.stances_dir)` when repo is provided
- `_populate_stances_from_files()` iterates `*.yaml` in stances_dir, inserts into `claim_stance`

## Progress

### Done
- [x] Branch created: `tranche1-proposal-artifacts`
- [x] `relate.py:write_stance_file()` — added `status: proposal` to top-level dict (commit 56d8572)
- [x] `build_sidecar.py:_populate_stances_from_files()` — file-level status gate: reject missing, skip proposal, load accepted (commit a4c5c7b)
- [x] `build_sidecar.py:_populate_claims()` — per-stance status gate for inline stances (commit a4c5c7b)
- [x] `validate_claims.py` — added `_validate_inline_stances()` and `validate_stance_file()` (commit c6602e0)

### Done (continued)
- [x] `propstore/cli/proposal.py` — `pks proposal accept` command (commit 80ce847)
- [x] Registered in `propstore/cli/__init__.py` (commit 80ce847)
- [x] Updated `tests/test_world_model.py` — all 6 inline stances got `"status": "accepted"` (commit faadc7d)
- [x] Wrote `tests/test_proposal_status.py` — 8 tests (commit defa8da)
- [x] Fixed missing `import logging` in build_sidecar.py (commit 3ff6e54)
- [x] Updated `tests/test_build_sidecar.py` — 1 inline stance got `"status": "accepted"` (uncommitted)

### First test run: 41 passed, 1 error
- Error was `NameError: name 'logging' is not defined` in build_sidecar.py inline stance code
- Fixed by adding `import logging` to top-level imports

### Done (more)
- [x] Fixed test_build_sidecar.py, test_graph_export.py, test_cli.py, test_sensitivity.py inline stances (commits 6affb80, 8d895a2)

### Second test run: 392 passed, 1 failed (test_graph_export stance edge test — found & fixed more missing status fields)
### Third test run: 559 passed, 1 failed

**Current failure:** `test_validate_claims.py::TestEmptyClaimFiles::test_missing_claims_key_errors`
- This is a PRE-EXISTING failure — it tests that a file with no `claims` key gets a JSON Schema error
- The test expects `not result.ok` but result has no errors
- This has nothing to do with my changes (no stances involved)
- Need to verify: does this test fail on clean master too?

### Remaining
- [ ] Verify if test_missing_claims_key_errors is pre-existing
- [ ] Run full suite skipping that test or verify it's pre-existing
- [ ] Write report

### Design Decisions
- Stance file status is **file-level** (`data["status"]`), inline stance status is **per-stance** (`stance["status"]`)
- This matches how the two paths are consumed: file-based reads one file = one source_claim, inline reads per-stance entry
