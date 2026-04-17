# Standing Disciplines

These rules apply to every workstream in this directory. They are not negotiable per-workstream. They were derived from the 2026-04-16 review's cross-axis patterns — every major finding traces back to one of these disciplines being absent.

## 1. Citation-as-claim

Every citation in a docstring, comment, or CLAUDE.md paragraph of the form "per Paper YYYY Def N" or "implements Operator from Author YYYY" is a **claim**. The claim is backed by:

- **(a)** a property test whose name contains the citation (e.g. `test_modgil_prakken_2018_def_22_strict_partial_order`), OR
- **(b)** a runtime invariant check (e.g. `verify_labels()` at `world/atms.py:1016-1072` validates de Kleer 1986's four label invariants), OR
- **(c)** an `xfail` pending test with a link to the workstream that will make it pass.

An unbacked citation is a lie. Strike it or back it. No exceptions.

CI lint: a pre-commit or CI job that scans docstrings for citation patterns and fails if no matching test / invariant / xfail-with-issue-link exists. This lint will be installed as part of the initial discipline baseline.

## 2. Docs never lead code

CLAUDE.md paragraphs, `docs/*.md` files, and module docstrings are *descriptions* of what the code does, not *advertisements* for what we hope it will do. Corollary:

- If you change a strict-typed module, you check CLAUDE.md for references to it and update them in the same commit.
- If you remove or weaken a postulate's test, you update CLAUDE.md's claims about it in the same commit.
- If you rename a module, every doc that references the old name is updated in the same commit.

**`docs/gaps.md` is the source of truth for known limitations.** Replaces the old "Known Limitations" section of CLAUDE.md (which the review found to be materially inaccurate). Every gap has a finding reference and/or a workstream reference. New gaps are only added when observed; existing gaps are only removed when a test proves closure.

## 3. Honest ignorance over fabricated confidence

The system represents uncertainty explicitly. The following are **forbidden**:

- Returning a default probability (0.5, 0.7, whatever) when no evidence or calibration exists. Use a vacuous `Opinion(0, 0, 1, a)` with a `status="defaulted"` provenance instead.
- Collapsing a three-valued solver result (Z3's `sat | unsat | unknown`; CEL evaluation `ok | type_error | runtime_error`; LLM classification with "no stance") to bool at the interface boundary. Use a `SolverResult` sum type.
- Mapping unknown to a specific known value (e.g. Z3 unknown → `ConflictClass.OVERLAP`). Unknown has its own variant.
- Silent `except Exception: pass` or `except: return default`. Every exception is either propagated or explicitly labeled-and-reported.
- Writing an invariant-violating struct (e.g. `b=d=u=0.0` when `b+d+u=1.0` is the opinion invariant). Types enforce invariants at construction.

## 4. Non-commitment at source; resolution at render

The source of truth holds disagreement. Rival normalizations, rival stances, rival candidate supersession stories, rival concept alignments all survive in storage. The render layer picks one per explicit policy.

- Heuristic output (LLM, embedding, classification, alignment proposal) goes to proposal branches. Never mutates source.
- User-initiated `promote` is the only path from proposal to source.
- `finalize` produces a derived artifact, not an overwrite of authored source.
- Merge operators emit partial frameworks holding both sides' attacks + ignorance + compatibility, not a collapsed winner.

## 5. Filter at render, not at build

The build step populates the sidecar with everything it has. Problems with specific data become **quarantine rows with diagnostic attached**, not **abort-the-batch errors**.

- `sidecar/build.py` populates every valid claim; problematic claims get a `build_diagnostics` row.
- `compiler/passes.py` does not drop `stage: draft` files from the semantic bundle — it emits them with a `stage='draft'` annotation, and the render layer filters per policy.
- `source/promote.py` permits partial promotion: valid claims promote, invalid ones stay on source with an explicit blocked marker.

The design checklist from `CLAUDE.md` applies:
1. Does this prevent ANY data from reaching the sidecar? → WRONG.
2. Does this require human action before data becomes queryable? → WRONG.
3. Does this add a gate anywhere before render time? → WRONG.
4. Is filtering happening at build time or render time? Build → WRONG.

## 6. No backward-compat shims

The project has no external users and no on-disk format commitment. Breaking changes are the default. The only thing you don't break is:

- The paper-to-code faithfulness (if a paper says X, the code continues to say X through the refactor).
- Running property tests and postulate tests (they stay green; if a refactor makes a postulate harder to verify, that's a design concern).
- Q's local repos (via an explicit migration CLI, not via silent compat).

If you find yourself writing a "legacy" path, a "v1" path, a backward-compat shim, or a parallel-support branch — stop. Rip out the old interface in one pass. Fix every caller. Q specifically authorized this mode of work.

## 7. Papers first

Before writing types or code for a theory-grounded subsystem, you have **read the paper and produced understandable notes in `papers/<name>/notes.md`**. If the notes already exist and are adequate, re-read them. If they're stubs, fill them.

Wrong typing is expensive to reverse. An afternoon rereading Jøsang 2001 is cheaper than a week of refactoring `Opinion` because the discount operator's semantics were misremembered.

## 8. Provenance accompanies every probability

Every `Opinion`, every stance, every calibration count, every prior, every derived probability carries a `Provenance` record. The provenance records the status (`measured | calibrated | stated | defaulted | vacuous`), witness (who asserted, when, from what source), and composition history (for fused opinions — recoverable to the per-source originals).

No probability enters the argumentation or render layer without a provenance. No fusion operator loses provenance. No serialization path drops it.

## 9. Tests as postulates

Formal properties from papers become Hypothesis `@given` strategies. Example tests that should be property tests are a mistake to preserve — convert them.

- Subjective logic: `b + d + u = 1`; consensus commutative; CCF Table I example; WBF (when fixed) against paper formula.
- Dung: each semantic property expressed as `@given` over generated AFs.
- AGM: K*1-K*8 as `@given` over generated belief sets + revise inputs.
- DP: C1-C4 as `@given` over iterated revision sequences.
- IC: IC0-IC8 over generated belief-base profiles + integrity constraints.
- ASPIC+: rationality postulates (direct consistency, closure) under each preference construction.

Every module claiming a postulate has the `@given` test for it, or an explicit `xfail` linking to the workstream that will produce it.

## 10. When in doubt, stop

Every place the review found a bug was a place someone continued coding through uncertainty instead of stopping to verify. Conventions for stopping:

- **You don't understand the paper → re-read it. Then read its predecessor. Then re-read again.**
- **You don't know how to type something → write examples of the values the type should hold; let the shape follow.**
- **You think you know but the code disagrees → the code wins. Find the observation that disambiguates.**
- **You're about to write a silent fallback → the fallback is wrong. Let the error propagate and re-design the caller.**
- **You're about to write a backward-compat shim → delete the old instead. Q authorized this.**
- **You're still stuck after all that → write state to `notes/<workstream>-state.md`, stop, request Q's attention.**

## 11. Test the boundary, not the interior

Heavy use of mocks is a smell. Tests that mock the DB, mock the LLM, mock Z3, and then verify the structure of calls are testing the test harness, not the code.

- Unit tests exercise pure logic with real inputs.
- Integration tests use real Z3, real sqlite sidecar, real dulwich repos. These run fast enough; `pytest.ini_options` already has `timeout = 300`.
- LLM / embedding-dependent tests: use a fixture that records a real API call's result on first run and replays it on subsequent runs (cassette-style), or use a tiny local model. Do not mock the LLM's response shape as a dict.

## 12. Notes as breadcrumbs, not essays

When you checkpoint state, write 1-2 sentences per entry in `notes/<workstream>-state.md`, with a timestamp. Enough to pick up where you left off or to let Q see where you are. Not enough to become its own project.

That's the discipline layer. Everything downstream is a specific subject-matter application of these rules.
