# Judgment Rubric

When you believe a workstream (or significant phase of one) is complete, a review agent — loaded without your session context — will audit the result. This document is the rubric that review agent will apply. You should read it before you start, not after.

## The review agent has

- Full review artifacts: nine axis reports, `SYNTHESIS.md`, `principled-path.md`, `paper-manifest.md`.
- Read access to the entire codebase and test suite.
- Read access to the papers.
- No assumption of charity. The review's default stance is that drift can return to any fixed place and that "appears correct" is not the same as "is correct."
- A specific set of things it checks. Those are below.

## The review agent does not have

- Your working notes.
- Your verbal commentary in PR messages.
- The benefit of the doubt when a test is absent.
- Tolerance for the cross-axis patterns the review flagged (fabricated certainty; solver-trivalent collapse; build-time gates; postulates without tests; types that can't label ignorance; citation-for-authority without test).

## What the review agent will check

### Paper faithfulness
- For every paper in the workstream's priority list, does the code implement what the paper says, or does it implement an approximation wearing the paper's name?
  - Citation-for-authority without test-backed faithfulness is the single pattern the review flagged most across axes. The review agent will grep for citation patterns in the workstream's touched files and verify each citation maps to a passing property test or a runtime invariant.
- Are the paper's formal properties expressible in the current types? (If a postulate cannot be *stated* over the types, it cannot be *verified* over the types. That's a structural problem, not a testing gap.)
- Are operator definitions reproducible against paper-published examples where those exist (e.g. CCF Def 5 against van der Heijden 2018 Table I; Dung semantics against Dung 1995's example AFs)?

### Type-level prevention of review-flagged error modes
The review found five cross-axis patterns:
1. Fabricated certainty at calibration-free defaults.
2. Three-valued solver results collapsed to two-valued.
3. Build-time filtering that should be render-time.
4. Postulate claims without postulate tests.
5. Types that cannot label ignorance.

For every workstream, the review agent asks: has your implementation made it **impossible at the type level** to re-introduce these errors? Not "unlikely" — **impossible**. Example tests:

- Can I call `Opinion.from_category('strong')` without supplying provenance? If yes, pattern #1 is still reachable.
- Can I take a `Z3Result` and implicitly use it as `bool`? If yes, pattern #2 is still reachable.
- Does the sidecar build refuse to populate rows with diagnostics attached? If yes, pattern #3 is still reachable.
- Does a module claim "per Paper X Def Y" without a corresponding test? If yes, pattern #4 is still reachable.
- Does `SourceTrustDocument` permit numeric values with no `status` discriminator? If yes, pattern #5 is still reachable.

If any of these are reachable after the workstream, the workstream did not do its job — regardless of how many other things it did right.

### Test adequacy
- `uv run pytest tests/` green.
- Formal properties from the workstream's papers are `@given` tests, not examples.
- The `property` marker is carried by files that use `@given` (fixing the marker lie axis 4 flagged).
- No modules touched by the workstream end up in axis 4's orphan list (the seven modules with zero test references).
- Strict-typed modules pass `uv run pyright --strict` cleanly.

### Discipline adherence (see `disciplines.md`)
- Every citation-as-claim has a backing test or invariant or xfail-with-link.
- CLAUDE.md + `docs/*.md` updated in the same commits as the code they describe. No doc-ahead-of-code lag.
- `docs/gaps.md` updated: gaps closed by this workstream are removed (with the test that proves closure); any new gaps discovered are added with a link to where they'll be fixed.
- No backward-compat shims introduced.
- No `except Exception: pass`; no silent defaults; no fabricated priors.
- Proposal/promote discipline preserved (if the workstream touches heuristic pathways).
- Honest-ignorance types carry through: no probability enters a consumer without provenance.

### Design quality
- The code reads well to a reader who has read the paper but not the code.
- Type signatures tell the story. A function's type says what it does; the body just executes.
- Comments explain *why* (non-obvious constraints, subtle invariants, paper-section references) — not *what* (well-named identifiers handle that).
- Names match the papers. `consensus_pair` not `fuse_two`; `Cn` not `closure`; `ist` not `in_context`.
- Module boundaries match the layer architecture (source of truth → concept/semantic → heuristic proposals → argumentation → render → agent workflow). No upward imports.

### What the review agent will NOT hold against you
- Volume of commits. If you took 200 commits to land WS-A, that's fine.
- Time on task. If the paper reading took longer than the implementation, that's healthy.
- Intermediate broken states on your branch. We only check merge candidates.
- Unpopulated edge cases that are documented in `docs/gaps.md` with a plan.
- Design decisions that are explicitly captured and reasoned in a workstream note, even if the review agent would have chosen differently — provided the reasoning is visible and the paper is not contradicted.

## Possible verdicts

### MERGE
All rubric items pass. Workstream is complete. Celebration is proportionate.

### MERGE WITH FOLLOWUP
Rubric items pass except for a bounded set of known-and-documented gaps. Gaps are tracked in `docs/gaps.md` with concrete next steps. Merge proceeds; the gaps become their own small workstreams.

### NO-MERGE — SPECIFIC FINDINGS
One or more rubric items fail. The review agent produces a findings report — severity-tagged, evidence-cited — and returns the workstream to you for iteration. This is not a failure; this is the system doing its job. Iterate, then request review again.

### NO-MERGE — STRUCTURAL
The workstream's approach contradicts the principles at a level a few code changes can't fix. Example: if a proposed type permits the fabrication pattern structurally, or if a citation is consistently used for authority without test-backing across the workstream. Review agent escalates to Q with the recommendation to reshape the workstream itself.

## Your best defense

- **Read the axis report(s) relevant to your workstream before you code.** They tell you exactly what the review looks for. Listed in your workstream file.
- **Write tests first.** If you can't write the test for a postulate, the types aren't right. Re-design before implementing.
- **Update CLAUDE.md + `docs/gaps.md` as you go, not at the end.** Doc-ahead-of-code is the review's #1 pattern; you avoid it by writing doc + code + test in the same commit.
- **Do the hardest paper read first.** The paper you don't understand is the paper that will produce drift. Understand it before typing.
- **If you catch yourself hedging, stop and re-read `principled-path.md`.** That document catalogs the hedges and states the beautiful alternatives. Match its framing.

## Meta

This rubric is itself subject to the citation-as-claim discipline. If the review agent cites a principle when flagging a finding, the principle must come from `CLAUDE.md` or `disciplines.md` — not from the review agent's loose memory. If you find a discrepancy between the rubric and a cited principle, the cited principle wins; flag the rubric discrepancy to Q for repair.

You are not being graded in the adversarial sense. You are being audited as part of the project's ongoing truth-maintenance. The review agent and you are both working for Q, and both of you are trying to build the same right thing. Act accordingly.
