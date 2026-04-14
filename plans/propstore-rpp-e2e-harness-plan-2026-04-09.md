# Propstore / Research-Papers-Plugin E2E Harness Plan

**Date:** 2026-04-09
**Scope:** create the executable end-to-end harness for `propstore` working with `../research-papers-plugin`
**Status:** Proposed
**Repos:**
- `C:/Users/Q/code/propstore`
- `C:/Users/Q/code/research-papers-plugin`

---

## Goal

Create a trusted executable oracle for the cross-repo workflow so future changes can be judged against a real end-to-end contract instead of local guesses.

This plan is only for creating the harness.

It is not:

1. a delete-and-rebuild plan
2. a migration plan
3. a cleanup plan
4. a replacement plan

---

## External System

The external system is:

- `C:/Users/Q/code/research-papers-plugin`

The harness must prove that `propstore` works with that repo's documented and tested workflow.

Primary contract surfaces:

1. [test_source_workflow_contracts.py](C:/Users/Q/code/research-papers-plugin/plugins/research-papers/tests/test_source_workflow_contracts.py)
2. [test_sync_propstore_source.py](C:/Users/Q/code/research-papers-plugin/plugins/research-papers/tests/test_sync_propstore_source.py)
3. [integration.md](C:/Users/Q/code/propstore/docs/integration.md)

---

## Required Workflow

The harness must exercise this workflow:

1. `pks source init`
2. `pks source add-concepts`
3. `pks source write-notes`
4. `pks source write-metadata`
5. `pks source add-claim`
6. `pks source add-justification`
7. `pks source add-stance`
8. `pks source finalize`
9. `pks source promote`
10. `pks build`

The harness must fail at the first broken step and report that step clearly.

---

## Non-Negotiable Rules

1. Do not broaden scope beyond the harness.
2. Do not change architecture as part of this plan unless a harness prerequisite forces a minimal change.
3. Do not mix speculative cleanup with oracle construction.
4. Keep the harness executable from the filesystem, not just described in prose.
5. Every pytest invocation must be `uv run pytest -vv` and tee full output to `logs/test-runs/`.
6. If an external workflow assumption is unclear, derive it from existing tests/docs before inventing anything.

---

## Deliverables

1. one executable harness entrypoint in this repo
2. one minimal test fixture or fixture workflow that the harness runs against
3. one narrow test target for the harness itself
4. one documented command for running the harness manually
5. one combined validation command that runs:
   - relevant propstore-side tests
   - relevant plugin-side workflow contract tests
   - the harness

---

## Harness Shape

The harness should:

1. create or use an isolated temporary propstore knowledge repo
2. select one minimal paper/source fixture
3. materialize the required source-side artifacts
4. run the full `pks source *` workflow and `pks build`
5. capture stdout/stderr and step results
6. stop at first failure
7. emit a compact success/failure report with the failing command if any

Preferred implementation location:

- `scripts/` for the executable harness
- `tests/` for the harness test

---

## Fixture Requirements

The fixture must be minimal but complete enough to exercise the cross-repo path.

Required fixture artifacts:

1. source identity inputs for `pks source init`
2. concepts batch
3. notes file
4. metadata file
5. claims batch
6. justifications batch
7. stances batch

The fixture should be:

1. small
2. deterministic
3. local to the repo
4. independent of network access

---

## Test Logging

Use timestamped logs for every pytest run.

PowerShell pattern:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv <target> 2>&1 | Tee-Object "logs/test-runs/$ts-<label>.log"
```

Examples:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_source_claims.py 2>&1 | Tee-Object "logs/test-runs/$ts-source-claims.log"
```

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv ..\research-papers-plugin\plugins\research-papers\tests\test_source_workflow_contracts.py ..\research-papers-plugin\plugins\research-papers\tests\test_sync_propstore_source.py 2>&1 | Tee-Object "logs/test-runs/$ts-plugin-contracts.log"
```

---

## Execution Slices

### Slice 1: Pin the Contract Surface

**Intent:**
Make the harness answer to existing cross-repo contracts rather than invented behavior.

**Work:**

1. enumerate the exact plugin tests and docs the harness is supposed to satisfy
2. enumerate the exact `pks` commands and required inputs
3. record the expected success criteria for each command

**Exit criteria:**

1. the harness command list is frozen
2. the required fixture files are frozen

---

### Slice 2: Create the Minimal Fixture

**Intent:**
Create one deterministic local fixture for the workflow.

**Work:**

1. add the minimal source artifacts
2. keep the fixture small and readable
3. ensure the fixture can be copied into a temp workspace during test execution

**Exit criteria:**

1. all required fixture files exist
2. the fixture is sufficient to attempt the full workflow

---

### Slice 3: Implement the Harness Script

**Intent:**
Create the executable script that runs the workflow end-to-end.

**Work:**

1. create the script under `scripts/`
2. run each step in order
3. stop on first failure
4. emit a readable result summary

**Exit criteria:**

1. the harness is executable locally
2. the first-failing-step reporting works

---

### Slice 4: Add the Harness Test

**Intent:**
Make the harness itself a tested surface.

**Work:**

1. add a test under `tests/`
2. run the harness against the minimal fixture in an isolated temp location
3. assert success or a precisely expected currently-known failure

**Exit criteria:**

1. the harness test exists
2. the harness test is runnable with `uv run pytest -vv`

---

### Slice 5: Add the Combined Oracle Command

**Intent:**
Create one command sequence that validates the cross-repo contract in practice.

**Work:**

1. run relevant propstore tests
2. run plugin workflow contract tests
3. run the harness
4. tee the output to timestamped logs

**Exit criteria:**

1. one documented oracle command sequence exists
2. future structural work can use it as the gate

---

## Final Verification

Do not report this plan complete until all of the following are true:

1. the harness exists on disk
2. the fixture exists on disk
3. the harness test exists on disk
4. the plugin workflow contract tests are part of the oracle story
5. the harness can be run manually
6. the harness reports the first failing step clearly

---

## Immediate First Steps

1. pin the contract surface from existing docs/tests
2. create the minimal fixture
3. implement the harness script
4. add the harness test
