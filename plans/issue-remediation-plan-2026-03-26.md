# Issue Remediation Plan

Date: 2026-03-26

Goal: resolve the review findings one by one, rereading the relevant literature before each fix, adding regression/property tests with each change, and committing each issue separately.

## Working Rules

1. Read the paper sections that define the intended behavior immediately before changing code for that issue.
2. Keep each fix scoped to one issue and its tests.
3. Stage only the files changed for the current issue.
4. Commit after each issue passes its targeted verification.
5. Avoid mixing unrelated cleanup into these commits.

## Ordered Issues

### 1. Grounded Semantics Divergence for `attacks` vs `defeats`

Relevant literature:
- Dung 1995
- Amgoud and Vesic 2011
- Modgil and Prakken 2018

Work:
- Reconfirm whether the implementation should compute standard grounded semantics, preference-based grounded semantics, or a weaker skeptical acceptance notion.
- Fix the current behavior where a returned "grounded" set may fail to be a complete extension.
- Update any caller assumptions in claim-graph resolution.
- Add fixed regressions for asymmetric attack/preference counterexamples.
- Add a property test that the claimed grounded extension is complete whenever that semantics label is retained.

Commit target:
- Core semantics and associated tests only.

### 2. ASPIC Elitist Set Comparison

Relevant literature:
- Modgil and Prakken 2018

Work:
- Recheck the exact elitist and democratic ordering definitions.
- Fix the reversed elitist set comparison implementation.
- Add direct comparator tests from the paper definition.
- Add a structured defeat regression where the wrong comparator changes the defeat outcome.

Commit target:
- `aspic` comparator logic and associated tests only.

### 3. Resolver Misreports Empty Skeptical Intersection as Universal Defeat

Relevant literature:
- Dung 1995

Work:
- Separate "not skeptically accepted" from "defeated in every extension".
- Correct the resolution result and/or status messaging for preferred and stable semantics.
- Add mutual-attack and multiple-extension regressions.

Commit target:
- Resolver behavior and associated tests only.

### 4. `HypotheticalWorld` ATMS Substitutability

Relevant literature:
- de Kleer 1986
- Dixon 1993

Work:
- Decide whether `HypotheticalWorld` must preserve the ATMS interface or explicitly degrade to a supported backend.
- Implement the chosen behavior without runtime failure for ordinary use.
- Replace the current crash-blessing regression with a behavior test.

Commit target:
- `HypotheticalWorld` / resolution integration and associated tests only.

### 5. Property-Test Sweep and Gaps

Relevant literature:
- Reuse issue-specific papers as needed

Work:
- Add any remaining Hypothesis properties not naturally included in the earlier commits.
- Focus on semantics invariants rather than incidental implementation details.
- Run the relevant targeted suites and then a broader verification pass.

Commit target:
- Only genuinely new tests or small supporting refactors required by those tests.

## Expected Commit Sequence

1. Fix grounded semantics divergence.
2. Fix ASPIC elitist comparison.
3. Fix skeptical-resolution reporting.
4. Fix `HypotheticalWorld` ATMS handling.
5. Add any remaining property-test coverage.
