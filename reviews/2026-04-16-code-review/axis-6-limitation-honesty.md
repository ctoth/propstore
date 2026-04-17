# Axis 6 — Limitation Honesty

Compiled from cross-axis findings. No subagent dispatch — primary synthesis.

## The question

CLAUDE.md has a "Known Limitations" section. Does it cover the real limitations, or does it screen worse ones by mentioning small honest gaps while omitting structural ones?

## CLAUDE.md's declared limitations

1. **ASPIC+ argument construction** — "Rule ordering in the bridge is always empty — only premise ordering from metadata has discriminating power."
2. **Decision criteria** — "Interval dominance (Denoeux 2019) not yet implemented. Pignistic, Hurwicz, lower/upper bound are in `world/types.py:apply_decision_criterion`."
3. **Semantic merge** — "Assignment-level IC merge with CEL/Z3 is implemented. Full belief-base/model semantics for Konieczny IC0-IC8 and rich PAF attack inversion (Amgoud & Vesic 2014) are deferred."
4. **Deduction, comultiplication, abduction** — "Extended Jøsang operators not implemented. Core 2001 operators are complete."

## Verdict against the axis findings

### Declared limitation 1 — ASPIC+ rule ordering empty

**Status: accurate, understated.**

Axis 3a confirmed empty `rule_order` at `aspic_bridge/translate.py:276`. Axis 7 additionally found the *upstream* source: unconditional empty `superiority=[]` at `grounding/translator.py:171-178` — priority information is dropped across the *whole* defeasible pipeline, not just the aspic_bridge leaf. Axis 9 also independently confirmed the drop.

The CLAUDE.md sentence describes a symptom; the cause is a layer upstream. Understated.

### Declared limitation 2 — Decision criteria

**Status: materially false.**

Axis 3b F2 (CRIT) verified against Denoeux 2018 paper PNG (pngs/page-017.png Eq 30): `world/types.py:1064-1066` is labeled `"pignistic"` and cites Denoeux p.17-18, but the implemented formula is Jøsang `b + a·u`. Denoeux's binomial BetP is `b + u/2`. Diverges whenever `a ≠ 0.5`.

The CLAUDE.md sentence reports "Pignistic ... implemented." It is not implemented. What's implemented under that name is expectation under Jøsang's subjective-logic projection — a reasonable operator, but not the cited paper's operator.

The other three criteria (Hurwicz, lower, upper) were not verified against paper by axis 3b; confidence that they match their cited paper is uncalibrated.

### Declared limitation 3 — Semantic merge

**Status: understates the departure.**

Axis 3c on `world/ic_merge.py:312-350`: candidate enumeration is `product(observed_source_values_per_concept)` — only values that appear in the sources are candidates. A true Konieczny IC merge candidate space is all `μ`-models. Sources `x=5` and `x=10` will never admit `x=7` as a winner here, even when the integrity constraint `μ` allows the interval.

CLAUDE.md's phrasing "Assignment-level IC merge with CEL/Z3 is implemented" is correct at the *interface* level (the function takes concept-value assignments and integrity constraints). But the reader who knows Konieczny 2002 will read "IC merge" as model-theoretic min-over-models distance; what they get is majority-vote-under-constraint selection among observed values. A different operator wearing the same name.

The module's own docstring (`ic_merge.py:1-12`) is more honest than CLAUDE.md: it explicitly says "adapts them to observed concept values rather than full belief-base model semantics." CLAUDE.md should at least mirror that honesty.

### Declared limitation 4 — Extended Jøsang operators not implemented, core 2001 operators complete

**Status: materially false.**

Axis 3b F1 (CONFIRMED against vdH 2018 pngs/page-004.png): `opinion.wbf()` is algebraically aCBF (associative cumulative belief fusion), not WBF. Three structural divergences from the paper formula. Worked example drifts 0.175 absolute on uncertainty. The commit message on c7a9215 self-acknowledges this open bug.

Axis 3b historical context: until commit c7a9215 landed on 2026-04-14, `_ccf_average` was a simplification that reduced to plain averaging of (b, d, u) across sources. Two dogmatic sources disagreeing completely produced `(0.5, 0.5, 0)` — fake confident consensus exactly where the honest-ignorance principle demands vacuous. The fix is two days old.

"Core 2001 operators are complete" is therefore false at two levels: WBF is still broken; CCF was broken for most of the project's month-long history and was only fixed days before this review.

## Limitations CLAUDE.md does not mention

Collected from axes 1, 2, 3a, 3c, 3d, 3e, 4, 5, 7, 9. Ordered by structural significance.

### 1. AGM revision is AGM in name only (axis 3c)

`propstore/revision/` — 1663 LOC, **zero literature citations in source**, **zero K*1-K*8 / C1-C4 / EE1-EE5 / P*1-P*6 / A*1-A*6 tests**. The only Levi test is tautological (`revise` equals its own definition). "Entrenchment" is a weighted-support-count total order, not Gärdenfors entrenchment. "Restrained" and "lexicographic" in `iterated.py` are atom-tuple rearrangements with no preorder semantics. Recovery (K-6) is not even *syntactically expressible* because atoms are not formulas and there is no `Cn` closure.

This is not a known-gap-acknowledged-as-deferred. CLAUDE.md's layer-4 description calls it "Argumentation layer — Dung AF construction, ASPIC+ bridge..." and elsewhere names revision via linked plans (`plans/true-agm-revision-phase1-2-checklist.md`, status "Implemented through Phase 5"). The code does not implement AGM semantics.

### 2. AF revision is absent entirely (axis 3c)

CLAUDE.md's "Literature Grounding" references the argumentation lineage including Baumann, Diller, Cayrol. `propstore/revision/af_adapter.py` does *not* implement AF revision — it projects an active-claim subset of a store. No module in the codebase implements Baumann 2015 expansion kernels, Diller 2015 extension-based revision, or Cayrol 2014 change operators.

### 3. Semantic substrate has zero structural implementation (axis 3d)

Grep across `propstore/` for `qualia|telic|agentive|constitutive|proto_role|lemon|LexicalEntry|LexicalForm|LexicalSense|lexicon|sameAs|ist\(c|lifting|bridge_rule|LocalModels` → **zero hits**. Grep for `frame` → one file (`opinion.py`), and every hit is Dempster-Shafer "frame of discernment," not Fillmore.

Four papers (Fillmore 1982, Pustejovsky 1991, Buitelaar 2011, McCarthy 1993) are named in CLAUDE.md as grounding the concept/semantic layer. None are cashed out. What exists: dimensional-quantity annotations + SKOS-style taxonomy + visibility-inheritance contexts + token-Jaccard reconciliation. A coherent stack — just not the stack CLAUDE.md advertises.

### 4. Z3 three-valued results collapse to bool; no timeouts (axis 3e)

`propstore/z3_conditions.py:444, 463, 481, 489` — `sat | unsat | unknown` → `bool`. Grep for `timeout|set_param|set_option` across `propstore/` → zero hits. Combined with `condition_classifier.py:32-36` silently mapping `unknown` → `ConflictClass.OVERLAP`, every Z3 timeout anywhere in the system becomes a persisted OVERLAP conflict record with no provenance signal. `dung_z3.py:151, 197` enumeration loops silently truncate on `unknown` inputs. No `SolverResult` sum type exists; no test exercises the `unknown` path.

Honest-ignorance principle violation at the argumentation-core entry point.

### 5. Probabilistic argumentation complexity does not deliver the advertised bound (axis 3a)

`praf/treedecomp.py:13-17` self-documents that row count is `O(2^|defeats| * 2^|args|)`, not the Popescu & Wallner 2024 `O(2^tw)` bound the engine dispatch assumes. `praf/engine.py:843-875` routes queries through the backend on treewidth-cutoff assumptions that rely on the paper's bound holding. Queries that the engine considers cheap may be exponentially expensive.

### 6. Defeasibility priority information is unconditionally dropped (axis 7)

`grounding/translator.py:171-178` hard-codes `superiority=[]`; `aspic_bridge/translate.py:275-280` hard-codes `rule_order=frozenset()`. The defeasible pipeline flows priority data in from the rule files and drops it on the floor twice before reaching the ASPIC+ layer. This is not "rule ordering always empty" in the sense CLAUDE.md declares (which sounds like a leaf-level gap) — it is systematic drop across the whole subsystem.

### 7. LLM stance classifier produces invariant-violating opinions (axis 5)

`classify.py:148-161` writes `opinion_belief = opinion_disbelief = opinion_uncertainty = 0.0` when the LLM emits `"type": "none"`. `b+d+u = 0`, violating `Opinion`'s own declared invariant (`opinion.py:33-43`). Persists as a dict bypassing validation; downstream interpretable as dogmatic_false via `p_relation_from_stance`.

### 8. Fabricated dogmatic opinions in sensitivity analysis (axis 1, axis 5)

`fragility_scoring.py:366-367`: `p_args = {arg: dogmatic_true() for arg in framework.arguments}`; `p_defeats` likewise. A "sensitivity analysis" sold as measuring fragility under uncertainty begins by fabricating that all arguments are certain.

### 9. Hard-coded "corpus frequency priors" with no corpus (axis 1)

`calibrate.py:211-217` `_DEFAULT_BASE_RATES = {"strong": 0.7, "moderate": 0.5, "weak": 0.3, "none": 0.1}` — documented as "corpus frequency priors," but no corpus is sampled. Every uncalibrated LLM stance classification inherits these as the `a` parameter of a vacuous opinion. The one signal subjective logic reserves for honest prior ignorance is silently filled with category-keyed guesses.

### 10. Build-time filtering that should be render-time (axis 1)

`sidecar/build.py:75-82` aborts the entire sidecar build on any raw-id claim error. `compiler/passes.py:289-307` drops every `stage: draft` file from the semantic bundle. `source/promote.py:186-188` refuses to promote a source branch with any finalize errors. Each violates the design checklist's "is filtering happening at build time or render time? If build → WRONG."

### 11. Preference heuristic is not Modgil-Prakken (axis 3a)

`preference.py` uses Pareto dominance on a 3-vector (`metadata_strength_vector`, `claim_strength`). Modgil-Prakken 2018 Def 22 is a strict partial order from a base ordering over premises. The file self-documents the split, but the heuristic flows into the bridge unlabeled.

### 12. ATMS/ASPIC+ bridge claim doesn't match the merge pipeline (axis 3c)

CLAUDE.md: `propstore/repo/` provides "branch reasoning (ATMS/ASPIC+ bridge)." Actual merge classifier (`repo/merge_classifier.py`) routes through `conflict_detector` and `structured_projection` — not through ATMS label/nogood machinery. ATMS lives in `world/atms.py` (not `repo/`) per axis 9.

### 13. Test markers lie about content (axis 4)

54 files use `@given`. Only 1 carries the `property` pytest marker. A CI invocation of `-m property` runs 6 tests when 365 property tests exist. The marker layer is aspirational; reality is something else.

### 14. Seven production modules with zero test references (axis 4)

1506 LOC in `diagnostics.py`, `fragility_contributors.py`, `fragility_scoring.py`, `fragility_types.py`, `parameterization_walk.py`, `probabilistic_relations.py`, `source_calibration.py`. Plus `conflict_detector/orchestrator.py` has zero direct test references despite being the orchestrator for the whole conflict-detection pipeline. Modules with findings overlap with modules with no tests.

### 15. Citing paper for authority while implementing something different (axis 9, cross-cutting)

The structural failure that appears in several forms:
- `aspic.py:55, 74, 91-93` cites "Modgil & Prakken 2018, Def 1 (p.8)" for contrariness. Paper's Def 1 is p.4 about Dung acceptability; content is from Def 2 p.8.
- `world/types.py:1064-1066` cites Denoeux; implements Jøsang.
- `revision/*.py` names operators after Booth 2006 and AGM; implements neither.
- `wbf()` named for WBF; computes aCBF.

Each individually is a fixable citation error. As a pattern, it signals that the codebase has drifted from its literature references without the drift being visible in type signatures or tests. This is the class of problem the review exists to surface.

## Summary

**CLAUDE.md's Known Limitations section mentions four things. Two of those four are materially false** (Pignistic is Jøsang, not Denoeux; core 2001 Jøsang operators are not complete — WBF is broken). The other two understate the scope of the departure.

**The list above adds fifteen structural limitations not mentioned in CLAUDE.md,** most of them larger in scope than the ones that *are* mentioned. The pattern is clear: CLAUDE.md declares gaps in small honest ways ("Denoeux interval dominance not yet implemented") while omitting the gaps that would require rearchitecting a layer to fix.

Recommendation: the Known Limitations section should be replaced with an honest scope-of-current-implementation paragraph, and a living `docs/gaps.md` should track every known drift with a severity and a link to the finding or workstream that would close it.

## Open questions

- Is the "Known Limitations" section intentional low-commitment phrasing (the author knows there's more but wanted to name the operator gaps specifically) or does it reflect the author's actual belief about the system's state?
- How much of the drift comes from the documentation lagging behind a moving codebase, versus the codebase being presented aspirationally in docs that were never true?
- If every citation must be property-test-backed, what percentage of current citations survive?
