# Defeasible Reasoning Workstream

Date: 2026-04-14
Status: active
Supersedes: `plans/defeasible-logic-integration-remediation-plan-2026-04-12.md`

## Goal

Make the `propstore` + `../gunray` reasoning path real, observable, and
semantically honest.

That means all of the following must be true at the same time:

1. A fresh repo created by `pks init` has the full directory surface needed for
   grounded reasoning authoring.
2. There is a checked-in demo repo with valid authored data that can actually be
   built and queried from the CLI.
3. The CLI exposes grounding output directly instead of hiding gunray behind the
   ASPIC claim layer.
4. The bridge does not silently narrow the authored rule language without
   either implementing the feature or deleting the surface.
5. Gunray passes the defeasible conformance cases that define the intended
   semantics for this integration.
6. End-to-end CLI tests exercise the real disk-backed path, not only parser
   plumbing or fake stores.

## What Is Already Done

Completed in this turn:

- deleted the invalid untracked `knowledge/` repo
- recreated a clean scaffold via `uv run pks init knowledge`
- fixed `pks init` so new repos now include `predicates/` and `rules/`

Files already changed:

- `propstore/cli/repository.py`
- `propstore/cli/init.py`

These changes fix the repo-shape bug. They do not yet make reasoning demoable.

## Verified Current Facts

- The runtime wiring exists:
  - `propstore/grounding/grounder.py` calls gunray
  - `propstore/world/model.py` loads a grounding bundle
  - `propstore/aspic_bridge.py` threads that bundle into the ASPIC bridge
  - `propstore/world/resolution.py` and `propstore/worldline/argumentation.py`
    consume that path for the ASPIC backend
- The live CLI is not currently a proof surface:
  - `world` and `worldline` require a built sidecar
  - the old checked-in `knowledge/` repo was invalid and had to be deleted
  - the new scaffold is valid, but empty, so it still cannot demonstrate
    reasoning
- The current ASPIC bridge only translates a narrow fragment:
  - defeasible rules only
  - no strict rule translation
  - no defeater translation
  - no `negative_body` translation
- The current demo/test surface is not sufficient:
  - some CLI tests prove flag parsing only
  - the focused test run still has unrelated repo drift and worldline failures
- Gunray still has real semantic gaps:
  - accepted xfails in the propstore conformance tranche
  - one remaining closure faithfulness failure upstream
  - dialectical `policy` does not currently implement ambiguity propagation

## End State

This workstream is done only when the repository has one coherent answer to
the user question "how can I see reasoning working?"

The answer must be:

1. initialize or copy the demo repo
2. build it successfully
3. inspect the grounded theory directly from the CLI
4. run ASPIC-backed extensions/worldlines from the same repo
5. point to passing disk-backed end-to-end tests that exercise the same path

No part of that answer may depend on:

- fake world objects
- empty grounding bundles
- parser-only tests
- invalid sample data
- undocumented manual setup

## Phase 0: Bootstrap Surface

Status: completed

Keep:

- `pks init` creates `predicates/` and `rules/`
- default packaged forms are seeded into fresh repos

Follow-up:

- add a regression test that `pks init` creates both directories
- add a regression test that a fresh scaffold contains valid form files

Acceptance:

- `uv run pks init <tmpdir>` creates `predicates/` and `rules/`
- the seeded form files include required `dimensionless`

## Phase 1: Create A Real Reasoning Demo Repo

Create one canonical, checked-in, disk-backed demo surface at:

- `examples/reasoning-demo/knowledge/`

Do not create multiple competing demo repos. Tests may copy this repo into a
temporary directory, but the authored source of truth is one demo repo.

Author the smallest repo that proves real reasoning:

- valid concepts
- valid claims
- valid stances
- valid justifications
- valid predicates
- valid rules

Include at least these cases:

1. `tweety` grounding case
   - fact `bird(tweety)`
   - defeasible rule `flies(X) -< bird(X)`
2. one explicit conflict case
   - supports actual defeat/extension computation
3. one superiority or preference case
   - proves the bridge is not only doing trivial no-attacker reasoning

Acceptance:

- `uv run pks -C examples/reasoning-demo/knowledge build`
- `uv run pks -C examples/reasoning-demo/knowledge world extensions --backend aspic`
- `uv run pks -C examples/reasoning-demo/knowledge worldline run demo --target <concept> --strategy argumentation --reasoning-backend aspic`

## Phase 2: Expose Grounding Directly In The CLI

Add a first-class grounding CLI surface. Do not force users to infer gunray
behavior indirectly from claim-level ASPIC output.

Target commands:

- `pks grounding status`
- `pks grounding show`
- `pks grounding query <atom>`
- `pks grounding arguments`

Required output surface:

- the four gunray sections
  - `definitely`
  - `defeasibly`
  - `not_defeasibly`
  - `undecided`
- the grounded rule instances
- the grounded arguments, when requested

Acceptance:

- the demo repo can show the Tweety ground result directly from the CLI
- the CLI can show when a repo has no authored grounding surface instead of
  silently falling through to an empty story

## Phase 3: Complete The Authored Rule Surface

The current bridge is too narrow. The target is not "support one happy-path
fragment forever." The target is that the authored rule language matches the
reasoning language we claim to support.

Required cuts:

1. strong negation works end to end
2. strict rules work end to end
3. defeaters work end to end
4. `negative_body` stops being an indefinite deferred branch

For `negative_body`, pick one direct state and finish it:

- implement default-negation semantics end to end against the chosen paper
  basis, or
- delete `negative_body` from the current production authoring surface

Forbidden state:

- keep `negative_body` in the authored schema
- reject it at runtime
- still describe the package as if defeasible reasoning were broadly complete

Acceptance:

- bridge code no longer raises the current "deferred to Phase 4" errors for
  supported authored surfaces
- or the unsupported authored surface is deleted outright

## Phase 4: Gunray Semantics And Conformance

Use the conformance suite as the forcing boundary, not only local unit tests.

Required upstream work in `../gunray`:

1. eliminate the accepted tranche deltas currently mirrored in propstore
2. resolve the remaining closure faithfulness failure
3. make the ambiguity policy surface honest

Target state for ambiguity policy:

- either `Policy.PROPAGATING` is restored and implemented on the dialectical
  path, or
- every propagating expectation is deleted from the public contract and test
  surface

The workstream is not done while the public surface still suggests
policy-configurable defeasible reasoning but the dialectical path discards the
policy value.

Acceptance:

- the currently xfailed conformance tranche runs green
- the upstream closure faithfulness suite runs green
- propstore no longer needs to mirror accepted gunray semantic xfails

## Phase 5: Runtime Cutover And Diagnostics

The ASPIC backend should fail clearly when the repo cannot support grounded
reasoning.

Add explicit diagnostics for:

- no sidecar
- no concepts
- no predicates/rules authored
- empty grounded bundle in an ASPIC-backed reasoning request

Make the user-facing story precise:

- if the repo is rule-free, say so
- if the repo is invalid, say so
- if the repo is valid and grounded, show the grounded results

Acceptance:

- `world` / `worldline` / `grounding` commands distinguish invalid repo state
  from valid-but-rule-free repo state
- no product path silently constructs an empty reasoning story when the user
  asked for ASPIC or grounding

## Phase 6: End-To-End Tests And Docs

Add real disk-backed tests around the demo repo.

Required tests:

1. `init` regression
2. demo repo `build`
3. demo repo `grounding show`
4. demo repo `world extensions --backend aspic`
5. demo repo `worldline run --reasoning-backend aspic`

Keep the test source of truth aligned with the real CLI path. Do not build a
separate fake path and call it coverage.

Documentation deliverables:

- README section: "Reasoning demo"
- exact CLI commands
- one short explanation of what gunray computes directly vs what propstore
  computes in the ASPIC claim layer

## Execution Order

The execution order is fixed:

1. finish bootstrap regression coverage
2. create the real demo repo
3. expose direct grounding CLI
4. complete or delete the remaining authored rule surface
5. close gunray conformance gaps
6. tighten runtime diagnostics
7. land end-to-end CLI tests and docs

Do not start with more fake tests.
Do not declare success from internal wiring alone.
Do not widen the workstream before the demo repo becomes buildable and
observable.

## Commit Slices

1. `fix(init): create predicates and rules in fresh repos`
2. `test(init): cover fresh reasoning repo scaffold`
3. `feat(demo): add disk-backed reasoning demo repo`
4. `feat(cli): expose grounding inspection commands`
5. `fix(bridge): complete or delete unsupported authored rule surfaces`
6. `fix(gunray): close conformance and policy gaps`
7. `fix(cli): add grounded-reasoning diagnostics`
8. `test(e2e): cover build, grounding, extensions, and worldline on demo repo`
9. `docs(reasoning): document the real CLI path`

## Exit Criteria

The workstream is complete only when all of these are true:

- `uv run pks init <tmpdir>` creates a reasoning-capable scaffold
- `uv run pks -C examples/reasoning-demo/knowledge build` succeeds
- `uv run pks -C examples/reasoning-demo/knowledge grounding show` succeeds
- `uv run pks -C examples/reasoning-demo/knowledge world extensions --backend aspic` succeeds
- `uv run pks -C examples/reasoning-demo/knowledge worldline run demo --target <concept> --strategy argumentation --reasoning-backend aspic` succeeds
- the upstream gunray conformance gaps identified in this review are closed or
  the public contract is narrowed explicitly and consistently
- disk-backed CLI tests cover the same commands

## Failure Modes

- treating parser flag coverage as proof of reasoning
- keeping an invalid or empty sample repo and calling the integration wired
- leaving bridge `NotImplementedError` branches in production while claiming
  feature support
- keeping ambiguity-policy parameters that the evaluator ignores
- proving only claim-level ASPIC output and never exposing the grounded theory
