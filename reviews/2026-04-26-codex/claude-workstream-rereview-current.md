# Re-review of current Claude workstreams

Date: 2026-04-27

## Read status

I re-reviewed the current files in `reviews/2026-04-26-claude/workstreams/` after Claude's revisions. I directly inspected the updated index, decisions log, and high-risk changed streams: WS-A, WS-B, WS-C, WS-I, WS-J, WS-K, WS-M, WS-N1, WS-N2, WS-P, WS-Q, and several dependency streams. I also used three explorer subagents to re-check the argumentation, dependency/math, and architecture/source-trust areas.

I did not rerun tests and did not reread the cited papers from page images in this pass. Findings below are about the current workstream text and dependency graph.

## What Improved

Claude fixed many of the previous control-surface defects:

- WS-F now declares its WS-O-arg dependency and no longer asserts projected attacks iff projected defeats.
- WS-G now separates "must fail today" tests from coverage gates, uses a deterministic cache fixture, and carries an OCF contraction derivation.
- WS-H now waits for the DF-QuAD paper contract instead of pinning symmetry by intuition.
- WS-I now frames `is_stable` as interface replacement rather than a shim rename.
- WS-J now depends on WS-I, fixes the hash-test premise, makes `max_candidates` explicit, and adds a journal storage contract before replay.
- WS-K now owns embedding identity, H10 forward/reverse independence, and H11 perspective-specific stance filing.
- WS-K2 no longer depends on a missing predicate-registration skill and adds CLI tests.
- WS-M removes the migration command, makes PROV-O export-only, and gates default `return_arguments=True` on gunray budget handling.
- WS-O-bri deletes `verify_equation` instead of deprecating it.
- WS-O-ast resolves the earlier open decisions and deletes the bytecode tier.
- WS-O-gun-garcia now states TDD discipline and includes coordinated propstore schema scope.

The current set is much closer to executable than the previous one.

## Current Findings

### 1. WS-C / WS-M / WS-E dependency cycle remains

WS-C declares a dependency on WS-M and blocks WS-E. WS-M depends on WS-E. WS-C Step 3 says it waits for WS-M Step 9. WS-M Step 9 says WS-C must ship first so it can hash the final micropub shape.

That cycle is not executable:

- WS-C depends on WS-M.
- WS-M depends on WS-E.
- WS-E depends on WS-C.
- WS-C Step 3 and WS-M Step 9 each say the other goes first.

Amendment: split the work:

- WS-C owns the canonical micropub payload shape and dedupe-shape contract, without waiting for WS-M.
- WS-M owns the hash/Trusty URI function and applies it to the WS-C-final payload.
- WS-E depends on the WS-C promote-ordering step, not on all of WS-C.

### 2. WS-K / WS-K2 dependency cycle remains

WS-K says it depends on WS-K2 for the rule corpus. WS-K2 says it depends on WS-K for `source_trust_argumentation` and blocks WS-K's first failing test. Later WS-K2 describes parallel coordination.

Amendment: make the header match the intended execution:

- WS-K can implement and test `source_trust_argumentation` with hand-stubbed rule fixtures.
- WS-K2 depends on the WS-K consumer API for its end-to-end firing test.
- Production trust quality depends on promoted WS-K2 rules, but WS-K implementation does not.

### 3. Owner lines are still stale in foundational streams

Several current workstreams still contain `Owner: TBD`, despite Codex 2.1:

- WS-A
- WS-B
- WS-D
- WS-L
- WS-N / WS-N1 / WS-N2
- WS-O-qui
- WS-O-gun-gunray
- WS-Q

Amendment: apply the same owner wording used in the revised streams: `Codex implementation owner + human reviewer required`, unless a named owner is chosen.

### 4. WS-K lists H13 as covered but excludes it

WS-K's finding table includes H13 embedding-registry admission control. Its "done means done" says every finding in the table is closed. Its out-of-scope section then says admission control remains a separate LOW concern and the fix lives elsewhere.

Amendment: either remove H13 from the covered-findings table or add a concrete admission-control step/test. D-19 embedding identity is not the same as admission control.

### 5. WS-I has stale cross-stream text

WS-J now correctly depends on WS-I. WS-I still says WS-J does not formally depend on it and later tells WS-J to "pick one."

Amendment: update WS-I to match the current graph: WS-I formally blocks WS-J and WS-J2.

### 6. WS-N1 misroutes `return_arguments` default ownership

WS-N1 still routes the `grounder.return_arguments` default wording to whatever WS-K decides. Current ownership elsewhere is WS-O-gun for budget wiring and WS-M for the propstore default flip/provenance boundary.

Amendment: WS-N1 should only delete the backwards-compat text if it touches that docstring; semantic ownership belongs to WS-O-gun + WS-M.

### 7. WS-N2 can close with the layered contract still soft

WS-N2 says it closes all architecture-contract findings, but it can declare done with residual layered violations under a soft-gate allowlist.

That is not a true closure of T5.3 unless the finding is redefined as "contract exists, not necessarily enforced."

Amendment: choose one:

- make WS-N2 close only when the layered contract is hard-fail clean; or
- rename it to a contract-introduction stream and create a follow-up stream that closes residual violations and flips the gate hard.

The current "done means done" language overclaims if residual violations remain allowed.

### 8. WS-O-arg ideal-extension construction is still unsafe

The old intersection proof was removed, but the new greedy single-argument construction can still stop too early. A larger admissible subset may require adding mutually defending arguments together; checking only one candidate argument at a time does not prove maximal admissibility inside the preferred intersection.

Amendment: implement the paper construction directly, or enumerate admissible subsets of the preferred-intersection carrier and select the maximal admissible one under set inclusion. Add a counterexample where no single argument can be added first, but a pair can be added together.

### 9. WS-O-arg dependency text still has stale parallel claims

The index now says VAF/ranking blocks gradual. Some argumentation workstreams still say the four substreams are independent or can run in parallel.

Amendment: normalize every WS-O-arg file to the same graph:

- WS-O-arg-argumentation-pkg first.
- WS-O-arg-vaf-ranking before WS-O-arg-gradual.
- ABA/ADF and Dung extensions can run independently after WS-O-arg-argumentation-pkg.

### 10. WS-O-arg sentinel location confusion remains

WS-O-arg-gradual and WS-O-arg-vaf-ranking still mix upstream `argumentation/tests/...` sentinels with propstore-side pin-bump sentinels.

Amendment: every upstream stream should have two explicitly named sentinels:

- `argumentation/tests/test_workstream_<id>_done.py` closes upstream behavior.
- `propstore/tests/test_dependency_<id>_pin.py` or equivalent closes the propstore pin/observable behavior.

Do not say an upstream test "lives propstore-side."

### 11. WS-O-arg convergence ownership still overlaps in text

The current graph assigns `RankingResult` and ranking convergence to WS-O-arg-vaf-ranking. WS-O-arg-gradual still says VAF/ranking owns a unified contract across `gradual.py`, while VAF/ranking says it does not modify `gradual.py`.

Amendment: make the boundary exact:

- VAF/ranking owns the `RankingResult` type and ranking module behavior.
- Gradual owns changes to gradual kernels that return or consume that type.

### 12. WS-O-gun-garcia misnames Garcia's four-valued surface

The text cites Garcia Def 5.3 as `YES/NO/UNDECIDED/UNKNOWN`, but the target type uses `yes/no/undecided/definitely`. That is not exact convergence to the cited surface.

Amendment: either name the fields after Garcia's surface exactly, or explain why `definitely` is a separate derived section and keep `unknown` in the Garcia result type.

### 13. WS-P still has an unresolved API fork against WS-O-ast

WS-P depends on WS-O-ast. WS-O-ast resolves the API as `extract_free_variables`. WS-P still contains `Either 9a/9b` language and later refers to a non-existent `free_names(tree)`.

Amendment: remove the fork and target the resolved `extract_free_variables` API. If WS-P can run without WS-O-ast, then it should not declare that dependency.

### 14. WS-P still depends on pending CEL spec retrieval for done gates

WS-P includes CEL string-escape work in acceptance/done gates while also saying the CEL spec is pending retrieval. That leaves an external unresolved source in the production close-out.

Amendment: retrieve/process the CEL spec before WS-P starts, or split the CEL escape grammar into a prerequisite spec-ingestion stream.

### 15. WS-O-ast / WS-P tier contract is inconsistent

WS-O-ast's post-D-14 tier set is `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`. WS-P describes `{CANONICAL, SYMPY, <fallback>}` and accepts only canonical/sympy as not-conflict. The fate of `PARTIAL_EVAL` is unclear.

Amendment: define whether `PARTIAL_EVAL` is proof-strength enough to suppress a conflict, or whether it maps to `UNKNOWN`. Do not leave it as an unnamed fallback.

### 16. WS-O-bri has an error-severity contradiction

The propstore test text says invalid `sin(L)` records a warning, while the same stream's error-handling contract requires `bridgman.DimensionalError` to be recorded as an error.

Amendment: invalid dimensional expressions should be errors; reserve warnings for intentionally unsupported but non-fatal advisory checks.

### 17. WS-M Trusty URI algorithm is inconsistent

WS-M's first failing test still frames verification around `ni:///sha-1`, while the target `compute_ni_uri` defaults to `sha-256` and recomputes existing strings.

Amendment: choose the algorithm and URI spelling once. Given the current design, prefer `sha-256` and update tests to assert `ni:///sha-256;...` or whatever RFC 6920 form is selected. Do not keep SHA-1 in the primary target unless it is explicitly required.

### 18. WS-J2 dependency header omits WS-A

WS-J2 header depends only on WS-J, while cross-stream notes say WS-A is a prerequisite and WS-J2 should not start before WS-A merges.

Amendment: add WS-A to the dependency header, or state that WS-J's closure implies WS-A and make that transitive dependency explicit.

### 19. WS-J2 observation semantics are under-tested

WS-J2 promises to distinguish observation from intervention, but the current tests mostly prove separate type/prefix behavior and deterministic inconsistency handling. Full Bayesian observation is out of scope, so the finding is only superficially closed.

Amendment: either narrow the finding to "observation is explicitly not intervention and fails closed outside deterministic constraints," or add a real observation semantics stream. Do not claim Bayesian observation semantics are fixed.

## Smaller Stale-Text Issues

- WS-O-arg-vaf-ranking still refers to `WS-O-arg-bugs`; the current file name is `WS-O-arg-argumentation-pkg`.
- WS-N legacy file remains alongside WS-N1/WS-N2 and still has `Owner: TBD`; either mark it superseded or delete/move it.
- WS-B owner line contains `TBD` even though it also includes the replacement wording.
- DECISIONS.md D-13 still says `verify_equation` is demoted/deprecated, while WS-O-bri now correctly deletes it. DECISIONS.md says it is authoritative when files conflict, so this should be updated or explicitly superseded by Codex 2.27.

## Recommended Next Fix Pass

1. Fix dependency headers and cross-stream ordering first: WS-C/M/E, WS-K/K2, WS-I/J, WS-O-arg substreams.
2. Normalize owner lines across every workstream.
3. Remove stale superseded files or mark them superseded at the top.
4. Resolve remaining semantic targets before implementation: ideal extension, Garcia section names, ast-equiv tier mapping, Trusty URI algorithm, CEL spec source.
5. Make every upstream dependency stream use paired upstream/propstore sentinels.

## Bottom Line

The current workstreams are much better than the previous draft and incorporate most Codex feedback. The remaining problems are narrower but still serious: two dependency cycles, a still-unsafe ideal-extension algorithm, several stale cross-stream references, and a few places where a workstream can declare done while the underlying guarantee remains soft or under-specified. Fixing those should make the folder usable as an execution plan.
