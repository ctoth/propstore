# Cluster R: gunray dependency

Reviewer: Claude (Opus 4.7), 2026-04-26.

## Scope and purpose

In-scope source (read in full): every file under `C:\Users\Q\code\gunray\src\gunray\` —
`__init__.py`, `_internal.py`, `adapter.py`, `answer.py`, `anytime.py`,
`arguments.py`, `closure.py` (head only), `compiled.py` (skim),
`conformance_adapter.py` (not read), `defeasible.py`, `dialectic.py`,
`disagreement.py`, `errors.py`, `evaluator.py` (head only), `grounding.py`,
`parser.py`, `preference.py`, `relation.py` (skim), `schema.py`,
`semantics.py` (skim), `stratify.py`, `trace.py`, `types.py`.

In-scope docs read: `pyproject.toml`, `README.md`, `ARCHITECTURE.md`,
`CITATIONS.md`, paper notes for Garcia & Simari 2004 (cited verbatim in
docstrings), Diller 2025 (`papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md`),
Maher 2021 (`papers/Maher_2021_DefeasibleReasoningDatalog/notes.md`).

Propstore consumers grepped: `propstore/grounding/{translator.py, grounder.py,
explanations.py, inspection.py, gunray_complement.py}`,
`tests/test_grounding_translator.py`, `tests/test_grounding_grounder.py`,
`tests/test_defeasible_conformance_tranche.py`,
`reviews/2026-04-20-swarm/deps/gunray.md`.

**Purpose** (verified from README and CITATIONS): gunray is a pure-Python
zero-dep defeasible logic engine. Three engines under one dispatcher:
(1) DeLP per Garcia & Simari 2004 on `DefeasibleTheory`, (2) stratified
Datalog per Apt-Blair-Walker 1988 on `Program`, (3) KLM closure per
Morris/Ross/Meyer 2020 on the propositional fragment via `ClosureEvaluator`.
Cluster guess in the dispatch prompt was correct: this is the cluster of
defeasible Datalog / ground-rule resolution. Diller 2025 is cited as
"contextual" in `CITATIONS.md` but is in fact partially implemented in
`grounding.py:_simplify_strict_fact_grounding` (CITATIONS drift; see Bug
LOW-1).

## Architecture overview

Layering, observed:

- `types.py` and `schema.py` define the value types. **Two parallel rule
  representations exist** — `schema.Rule` (id/head/body strings, the
  user-authored surface) and `types.Rule` (parsed: heads/positive_body/
  negative_body/constraints/source_text). Translation happens in
  `parser.py`.
- `parser.py` parses both Datalog rule strings and the structured
  `DefeasibleTheory` envelope into `types.DefeasibleRule` /
  `types.Rule`.
- `_internal.py` is the cross-module helper sink: grounding
  (`_ground_theory`, `_ground_rule_instances`, `_positive_closure_for_grounding`),
  body matching (`_match_positive_body`), program validation, safety
  enforcement.
- `arguments.py` enumerates argument structures (Garcia 04 Def 3.1) by
  bottom-up minimal subset construction; calls `_ground_theory` and
  `disagreement.strict_closure`.
- `disagreement.py` implements complement, strict closure, and `disagrees`
  (Def 3.3).
- `preference.py` provides `TrivialPreference`, `GeneralizedSpecificity`
  (Simari & Loui 1992 Lemma 2.4), `SuperiorityPreference` (Garcia 04
  §4.1), `CompositePreference` (first-criterion-to-fire).
- `dialectic.py` builds dialectical trees (Def 5.1 + Def 4.7 acceptable
  argumentation lines), marks via Procedure 5.1, renders as Unicode and
  Mermaid, and explains in prose.
- `defeasible.py` is the entry point for `DefeasibleTheory` evaluation;
  routes strict-only theories through `evaluator.py` (semi-naive Datalog),
  otherwise runs the argument pipeline and projects to the four-valued
  section dict.
- `evaluator.py` + `stratify.py` implement semi-naive Datalog with
  Apt-Blair-Walker stratification.
- `closure.py` is a separate KLM closure engine used for the
  `*_CLOSURE` policy values (zero-arity propositional fragment only).
- `grounding.py` exposes a public grounding-inspection surface
  (`inspect_grounding`) with a Diller 2025-shaped simplification.
- `anytime.py` — single-class sentinel for bounded enumeration
  (`EnumerationExceeded`).
- `adapter.py` — `GunrayEvaluator` dispatcher.
- `trace.py` — execution traces (`DatalogTrace`, `DefeasibleTrace`).

The dependency graph is mostly clean; `dialectic.py` does have lazy
imports of `arguments`/`preference` to break a cycle, and `defeasible.py`
imports from `dialectic` lazily for the same reason. There is one
suspicious cross-module *non*-private import described in Bug MED-3.

## Paper-faithful coverage

| Mechanism | Paper citation | Implementation | Verdict |
|---|---|---|---|
| Argument structure (Def 3.1, Simari Def 2.2) | Garcia 04 p.8; Simari 92 p.10 | `arguments.py:33-160`, bottom-up minimal construction | OK |
| Sub-argument relation | Garcia 04 Fig 1 | `arguments.is_subargument` | OK |
| Disagreement (Def 3.3) | Garcia 04 p.10 | `disagreement.disagrees`, seeded with `Pi` facts | OK; pitfall checked (ARCHITECTURE.md:188-195) |
| Strict closure | implied by Def 3.3 | `disagreement.strict_closure` | OK; **memoization-free**, called per subset in `build_arguments` (perf, see HIGH-1) |
| Counter-argument at sub-arg (Def 3.4) | Garcia 04 p.11 | `dialectic.counter_argues` + `_disagreeing_subarguments` | OK; descends into sub-args |
| Proper / blocking defeater (Def 4.1/4.2) | Garcia 04 §4 | `dialectic.proper_defeater`, `blocking_defeater`, `_defeat_kind` | OK |
| Acceptable argumentation line (Def 4.7) | Garcia 04 p.19 | `dialectic._expand` cond 2 (concordance), 3 (no sub-arg re-entry), 4 (no blocking-on-blocking); cond 1 finite | Mostly OK; see MED-1 (block-on-block check uses *parent edge*, paper says any prior segment) |
| Dialectical tree (Def 5.1) | Garcia 04 p.21 | `dialectic.build_tree` | OK |
| Procedure 5.1 marking | Garcia 04 §5 | `dialectic.mark` (recursive, no caching) | Correct but exponential in tree depth (see MED-2) |
| Four-valued answer (Def 5.3) | Garcia 04 p.28 | `answer.Answer`, `dialectic.answer`, `defeasible._evaluate_via_argument_pipeline` projection | Mostly OK; the section projection expands the answer into FOUR sections per atom; `not_defeasibly` semantics is propstore-specific not Garcia's — see MED-4 |
| Generalized specificity (Lemma 2.4) | Simari 92 p.14 | `preference.GeneralizedSpecificity` with `An(T)` antecedents | OK; empty-rules guard mirrors superiority |
| Rule priority (§4.1) | Garcia 04 §4.1 | `preference.SuperiorityPreference` with Floyd-Warshall closure | OK |
| Composed preference | Garcia 04 §4.1 | `preference.CompositePreference` first-fire | OK; documented asymmetry recovery from earlier any-wins bug |
| Presumptions (§6.2) | Garcia 04 p.32 | `schema.DefeasibleTheory.presumptions` validated empty-body, plumbed as defeasible kind | OK |
| Explanation prose (§6) | Garcia 04 p.29 | `dialectic.explain` walks marked tree | OK |
| Strict-only fast path Π consistency | Goldszmidt-Pearl 1992 (background) | `defeasible._is_strict_only_theory`, `_raise_if_strict_pi_contradictory` | OK; raises `ContradictoryStrictTheoryError` |
| Stratified Datalog (Apt-Blair-Walker 1988) | safety + stratification | `stratify.stratify`, `_internal._validate_program` | OK |
| Nemo existential negation (Ivliev 2024) | KR 2024 | `NegationSemantics.NEMO` | exposed; not deeply audited |
| KLM closure (Morris/Ross/Meyer 2020) | Algorithms 3-5, p.150-153 | `closure.ClosureEvaluator` zero-arity only | OK; explicit scope cap |
| Antoniou ambiguity propagation | Antoniou 2007 | **out-of-contract**; `Policy.PROPAGATING` deprecated | Documented in ARCHITECTURE |
| Diller 2025 grounding simplification | KR 2025 Algorithm 2 | `grounding._simplify_strict_fact_grounding` is a *conservative subset* (resolves strict rules with definite-fact bodies into the fact base; no defeasible removal, no Transformations 1-2 in full) | Partial — see LOW-1 |
| Maher 2021 metaprogram compilation | TPLP submission | **not implemented** — Gunray uses direct DeLP pipeline; CITATIONS lists Maher as "alternative path considered and not taken" | Documented |

## Provenance through evaluation

This is the cluster B/D claim. Findings, observed in source:

**Internal provenance is well-preserved.** Every grounded rule carries
its source `rule_id` and `kind` (`types.GroundDefeasibleRule:89-93`).
Arguments carry `frozenset[GroundDefeasibleRule]` rather than just rule
ids, so the full body atoms and head are reachable from every argument
(`arguments.Argument:32-46`). Dialectical trees retain the argument at
every node (`dialectic.DialecticalNode:191-200`). The new
`grounding.GroundRuleInstance` even carries the `substitution` tuple
that produced each ground instance (`grounding.py:20-29`) — this is
strictly more provenance than Garcia 04 calls for.

**Provenance IS dropped at the section projection.** The
`_evaluate_via_argument_pipeline` final pass (`defeasible.py:196-239`)
collapses every warranted/strict/no/undecided atom into a
`dict[str, set[FactTuple]]` keyed by predicate. The argument that
warranted each atom, the rule(s) that fired, the substitution that
grounded them — none of that survives into `DefeasibleModel.sections`.
Verified: `_atoms_to_section` (`defeasible.py:328-332`) just builds a
`{predicate: {tuple_of_args}}` map. There is no per-fact provenance
edge.

**The escape hatch exists but is opt-in: `DefeasibleTrace`.** When
`evaluate_with_trace` is called the resulting `DefeasibleTrace` carries
`arguments`, `trees`, and `markings` (`trace.py:129-167`,
`defeasible.py:241-252`). So a determined caller can recover provenance.
But (a) the bare `evaluate` pathway throws the trace away
(`defeasible.py:71-77`), (b) `DefeasibleTrace.markings` is keyed by
*conclusion atom only*, so if multiple distinct arguments warrant the
same atom only the last one (with `label == "U"` preference) survives
(`defeasible.py:172-176`), and (c) the propstore `GroundedRulesBundle`
only stores `arguments` when callers pass `return_arguments=True` and
even then keys by `_argument_sort_key` rather than by conclusion
(`propstore/grounding/grounder.py:190-198`).

**At the propstore boundary specifically.** The translator
(`propstore/grounding/translator.py:78-185`) converts authored
`RuleDocument` → `gunray.Rule` by stringifying head and body atoms via
`_stringify_atom`. The `RuleDocument.id` is preserved as
`gunray.Rule.id`, so the rule-id-as-handle works. **But every other
piece of `RuleDocument` provenance is dropped at this boundary**:
- `RuleDocument` carries metadata about authoring (file, justification,
  source quote) that propstore considers load-bearing per the
  `imports_are_opinions` principle. Gunray sees only `(id, head, body)`.
- Atom-level provenance (which `AtomDocument` came from which import row,
  with what confidence) is rendered to the surface string and erased
  beyond what gunray's parser can recover.
- The grounded section is normalised back into a four-section dict
  (`propstore/grounding/grounder.py:237-287`) that re-mirrors the gunray
  shape; nothing in that normalisation re-attaches per-fact rule-id /
  argument links to the propstore source.

**Verdict on the cluster B/D claim.** Cluster B and D are correct that
provenance is dropped at the gunray boundary, but the drop happens in
*two* places, not one. (1) On the propstore→gunray side: the translator
flattens structured `AtomDocument`/`RuleDocument` to strings; only the
rule id survives as a handle. (2) On the gunray→propstore side: the
default `evaluate` path discards the `DefeasibleTrace`, so even the
internally-preserved argument graph never reaches the propstore caller
unless `return_arguments=True` is explicitly threaded. The
`GroundingInspection` surface in `grounding.py` returns the grounded
rule instances with substitutions but is also opt-in
(`propstore/grounding/grounder.py:171` calls `gunray.inspect_grounding`
unconditionally now, which is good — that's a fix from earlier code).

## Boundary with propstore

Read every consumer in propstore. Observations:

1. **`propstore/grounding/translator.py:translate_to_theory`** —
   imports `gunray` as a top-level package and reads
   `gunray.{Rule, DefeasibleTheory, Scalar}`. Closes the authored
   superiority pairs via `argumentation.preference.strict_partial_order_closure`
   then submits them as `superiority`. Note: `conflicts=()` is hardcoded
   (`translator.py:184`). `gunray.DefeasibleTheory.conflicts` is the
   slot the strict-only fast path uses to detect predicate-pair
   contradictions beyond strong-negation `~p` vs `p`; propstore never
   populates it. This is a missed channel for domain-asserted
   incompatibilities (e.g. propstore's `incompatible_with` predicates).
2. **`propstore/grounding/grounder.py:ground`** — Calls
   `evaluator.evaluate(theory, policy)` — the **non-trace** entry point —
   so the `DefeasibleTrace.arguments`, `.trees`, `.markings` are
   discarded. Then separately calls `gunray.inspect_grounding(theory)`
   to re-derive the grounded rule instances. **This re-grounds the
   theory a second time** — `inspect_grounding` does its own
   `parse_defeasible_theory` and `_positive_closure_for_grounding` pass
   (`gunray/grounding.py:73-121`). Wasteful given that `evaluate`
   already grounded. Fix: use `evaluate_with_trace` and pull arguments
   from the trace.
3. **`propstore/grounding/explanations.py:build_grounding_text_explanation`**
   — Uses `evaluate_with_trace`, then calls `trace.tree_for_parts`.
   When the requested atom has no tree it tries the complement. If both
   miss, returns a "Gunray did not produce a dialectical tree" message.
   This degrades silently — there is no explanation of *why* (atom not
   in language? UNDECIDED with no warrant tree? section was empty?). See
   MED-5.
4. **`propstore/grounding/gunray_complement.py:GunrayComplementEncoder`**
   — Trivial wrapper over `gunray.complement` that round-trips a bare
   predicate string through `GroundAtom`. Functional but odd: the
   encoder discards the arguments tuple and works only on predicates,
   yet wraps it in a `GroundAtom` with empty arguments to call
   `complement`. Just calling `gunray.complement` directly with the
   right `GroundAtom` would be clearer.
5. **`propstore/grounding/inspection.py`** — Layers a propstore-side
   inspection surface on top of `GroundedRulesBundle`. The grounded
   rules are recovered via *deduplicating across `bundle.arguments`*
   (`inspection.py:_grounded_rules:153-183`), which is roundabout and
   loses any rule that participated in no argument (e.g. a strict rule
   that fired but then no defeasible argument referenced it). The
   `GroundingInspection` already on `bundle.grounding_inspection`
   contains exactly the grounded rules; the inspection layer should use
   that directly.
6. **Type leakage**. `propstore/grounding/translator.py:65` imports
   `from argumentation.aspic import GroundAtom`, then accepts those
   `GroundAtom`s as input but never converts them to
   `gunray.GroundAtom` (gunray's own `GroundAtom` from `types.py`).
   They share the same `predicate` / `arguments` shape but are nominally
   distinct types from different packages. Tests that round-trip these
   could silently confuse the two.

## Bugs

### HIGH

**HIGH-1: `build_arguments` is exponential in defeasible-rule count for adversarial theories.**
`arguments.py:_has_redundant_nonempty_subset` (lines 186-201) is called
inside the `_add_minimal_argument` flow. For each candidate
`rule_set`, it iterates every rule in the set, removes it, builds a
combined strict closure, and checks if the conclusion is still
derivable. This is `O(|rule_set|)` strict-closure passes per candidate.
The outer loop in `build_arguments:131-159` iterates every *product* of
support sets across the body atoms. Worst case: a theory with k chained
defeasible rules where each rule head is required by the next produces
`2^O(k)` candidate combinations to check, each with `O(k)` redundancy
checks, each requiring an `O(k * |strict_rules|)` strict closure (which
itself is *memoization-free* per `disagreement.py:18-19` docstring).
The `pi_closure` is precomputed once but per-candidate closures are
not. Combine this with the dialectical tree's `_concordant_rules`
caching being **per-tree** rather than **per-theory**
(`dialectic.py:309`), and a 20-rule theory does the same closure
hundreds of times across multiple trees during the
`_evaluate_via_argument_pipeline` loop. The README says "naive
enumeration; efficiency is a Block 2+ concern" but Block 2 has happened
(per code comments) without addressing this.

**HIGH-2: `disagrees` cache is recreated per call.**
`dialectic.counter_argues` (lines 89-113) calls `_theory_strict_rules`
and `_theory_pi_facts` on every invocation. Both re-parse the theory
via `parse_defeasible_theory` and re-ground via
`_positive_closure_for_grounding` and `_ground_rule_instances`. For a
theory with N arguments, the dialectical tree construction calls
`counter_argues` (or `_disagreeing_subarguments`) up to `N^2` times
just for the root tree, and the recursive `_expand`
(`dialectic.py:324-408`) calls it for every (candidate, current) pair
at every depth. This means the entire grounding pass runs `O(N^2)`
times per dialectical tree, on top of HIGH-1. Symptom in production
will be that propstore CLI `gpr ground` becomes unusable on theories
with more than ~30 grounded defeasible rules.

**HIGH-3: `inspect_grounding` is called twice in propstore's `ground`
function** (`propstore/grounding/grounder.py:170-171`). The
`evaluator.evaluate` call on line 170 internally grounds the theory.
The very next line then calls `gunray.inspect_grounding(theory)` which
reparses and regrounds. This is a propstore bug, not a gunray bug, but
it is in the gunray boundary contract: gunray should expose the
grounded inspection from `evaluate_with_trace` rather than as a
separate call that has to re-do the work. The fact that two parallel
grounders exist (`_internal._ground_theory` and the
`inspect_grounding` path that re-runs `parse_defeasible_theory`) is
itself suspicious — they should share one entry point.

### MED

**MED-1: Def 4.7 condition 4 (block-on-block) only inspects the immediate parent edge.**
`dialectic._expand` (lines 354-355) checks
`if parent_edge_kind == "blocking" and kind == "blocking": continue`.
Garcia 04 Def 4.7 condition for blocking-defeater chains is
"if `<A_i, h_i>` is a blocking defeater of `<A_{i-1}, h_{i-1}>` and
`<A_{i+1}, h_{i+1}>` exists in the line, then `<A_{i+1}, h_{i+1}>` is
a proper defeater of `<A_i, h_i>`" — i.e. the prohibition is on
consecutive blocking edges anywhere in the line. The current code is
correct under that reading because each step only sees its parent edge.
However, the `edge_kinds[-1]` lookup happens in the recursive frame
*for the candidate's parent only*; it does not need the full list. Read
again: `parent_edge_kind = edge_kinds[-1]` at line 345. That is the
edge attaching `current` (the parent of `candidate`) to *its* parent.
The new `candidate`'s edge `kind` is what's classified into the
`parent_edge_kind` slot of the *next* recursion. So the comparison is
"the edge `current←parent` was blocking AND the edge `candidate←current`
is blocking." That correctly forbids consecutive blocking edges. This
turns out to be OK on re-reading — withdrawing the bug. **Replacing
with**: edge_kinds[0] is initialized as `[None]` matching `[root]`, so
the "no parent" sentinel works. Confirmed correct.

**MED-1 (replacement): `_evaluate_via_argument_pipeline` builds at most one tree per conclusion.**
`defeasible.py:163-176` guards with
`if arg.conclusion in warranted: continue` and
`if arg.conclusion not in trees or label == "U"`. So if argument A1 for
`flies(opus)` marks `D` and is checked first, and argument A2 for the
same atom would mark `U` but is checked *second*, the U mark is
captured and warranted is updated correctly. But: the trace's
`trees[atom]` only retains *one* tree per atom; the rendered explanation
will pick whichever tree was last seen. For an atom with multiple
distinct supporting arguments (e.g., two unrelated chains of rules
both proving `bird(opus)`) the explanation only shows one. Garcia 04 §6
says the explanation should report *all* arguments considered, not the
first or last. This is a fidelity gap, not strictly wrong.

**MED-2: `mark()` is recursive without memoization.**
`dialectic.mark` (`dialectic.py:411-427`) recurses on every
`DialecticalNode`. For a tree of depth `d` with branching factor `b`,
the same subtree is re-marked on every visit if it appears as a
subtree of multiple paths. In gunray's tree construction the same
sub-argument can be a child of multiple nodes (because every defeater
of a node can be the same defeater of a sub-argument), so the tree
can have shared children. `mark` uses identity comparisons inherent to
recursion; without memoization the marking is exponential in the worst
case. The `_mark_table` helper at lines 488-504 *does* memoize (stored
in a dict keyed by node), but `mark()` itself, the public function,
does not. Callers that use `mark()` for a single root walk the tree
naively. Switch `mark` to use `_mark_table` and return
`_mark_table(tree)[tree]`.

**MED-3: Cross-module use of an underscore name violates the stated discipline.**
ARCHITECTURE.md:198-200 ("No cross-module private imports") and
`_internal.py` is positioned as the shared sink. **Yet** `dialectic.py`
imports `_atom_sort_key`, `_fact_atoms`, `_force_strict_for_closure`
from `_internal` — that's fine since `_internal` is the sink — but
`grounding.py` imports `_ground_rule_instances_with_substitutions` and
`_positive_closure_for_grounding` from `_internal`, and exports their
*outputs* through public types (`GroundRuleInstance`,
`GroundingInspection`). The boundary between "shared helper" and
"public API" has been crossed in `grounding.py`'s direction. If
`_ground_rule_instances_with_substitutions` ever changes its return
shape, `grounding.py:_public_substitution` (line 137) will silently
break the public surface.

**MED-4: `not_defeasibly` semantics is propstore-derived, not Garcia 2004.**
`defeasible.py:196-229` projects the four-valued answer into FOUR
sections: `definitely`, `defeasibly`, `not_defeasibly`, `undecided`.
Garcia 04 Def 5.3 only defines `YES`/`NO`/`UNDECIDED`/`UNKNOWN`. The
section names map: `definitely=strict`, `defeasibly=YES or strict`,
`not_defeasibly=NO and not strict`, `undecided=UNDECIDED`. The mapping
also folds in a "defeater_touches" rule
(`defeasible.py:215-217, 223-224`) that sends an atom into
`not_defeasibly` if a Nute/Antoniou-style defeater rule probed it.
This last clause has no analogue in Garcia 04 — it is a propstore
contract per the comment "post-Block-2, ... defeater rule is a pure
attacker." The comment cites
`notes/b2_defeater_participation.md` which lives in gunray, not in any
peer-reviewed source. The attribution to "Nute/Antoniou reading" in
CITATIONS.md:64-68 is informal — neither paper is cited with chapter
and verse. This is a load-bearing semantic decision that needs paper
backing or formal documentation; otherwise downstream consumers might
read `not_defeasibly` as Garcia's `NO`, which it is not.

**MED-5: `build_grounding_text_explanation` falls back silently to the complement.**
`propstore/grounding/explanations.py:43-53` tries the requested atom's
predicate, then if that fails, tries `_complement_predicate(atom.predicate)`.
If the complement *is* found, the user is told an explanation for an
atom they didn't ask about — and the only signal is that
`explained_atom != requested_atom`. There is no error message or
warning. For a propstore caller that asks "explain `flies(opus)`" and
gets an explanation for `~flies(opus)`, this is misleading. At minimum,
the message field should call this out.

**MED-6: `superiority` validation does not detect cycles or self-pairs.**
`schema.DefeasibleTheory.__post_init__` (lines 164-170) checks every
referenced rule id exists, but does not check that the pair list is
acyclic, and does not reject `(r1, r1)` self-pairs. The downstream
`SuperiorityPreference.__init__` (`preference.py:225-253`) computes
the transitive closure with a Floyd-Warshall-style loop; if `(r1, r2)`
and `(r2, r1)` are both supplied, the closure produces both
`(r1, r1)` and `(r2, r2)` and `prefers(arg_with_r1, arg_with_r2)`
becomes True *and* `prefers(arg_with_r2, arg_with_r1)` becomes True,
violating the strict-partial-order axiom that
`CompositePreference.__doc__` claims is a precondition. Hypothesis
property tests on composite preference (cited in
`preference.py:354-362`) cannot catch this if the test never generates
cyclic input.

**MED-7: Strict-only fast path drops the full argument view.**
`defeasible.py:_evaluate_strict_only_theory_with_trace` (lines 280-301)
builds a `DefeasibleModel` with only `definitely` and `defeasibly`
sections (mirrored). It does NOT populate the trace's `arguments`,
`trees`, or `markings`. So a propstore caller that asked for
`return_arguments=True` on a strict-only theory gets an empty argument
tuple — no way to enumerate the trivial single-rule strict arguments
even though `build_arguments` would have produced
`Argument(rules=frozenset(), conclusion=h)` for every strict
consequence. Non-trace evaluation paths suffer the same limitation;
inconsistent with the documented "argument view is opt-in" contract.

### LOW

**LOW-1: CITATIONS.md miscategorises Diller 2025.**
`CITATIONS.md:83-86` puts Diller 2025 under "Contextual (shaped design,
not directly implemented)" with the comment "Gunray enumerates arguments
directly from DeLP rules rather than compiling through ASPIC+." But
`grounding.py:153-195` implements a "conservative DeLP-compatible
fragment" of Diller's Algorithm 2 (per its own docstring at line
163-168). The grounding simplification *is* a partial Diller
implementation; the citation should reflect that, and the docstring
should pin to specific theorem / page numbers.

**LOW-2: `anytime.py` is not used by any other module in `src/gunray/`.**
Grep for `EnumerationExceeded`: imported in `__init__.py:11`,
`_internal.py:10`, used as a return type only by
`_head_only_bindings(max_candidates: int)` overload
(`_internal.py:228-287`). No caller of `_head_only_bindings` actually
passes `max_candidates`; checked all references in `_internal.py` and
`arguments.py`. The anytime escape hatch is dead. Either wire it
through to `build_arguments` so users can bound enumeration, or remove
it.

**LOW-3: `compiled.py` "fast path" is opaque from outside.**
`_internal._iter_positive_body_matches_from_ordered_atoms`
(`_internal.py:381-390`) calls `compile_simple_matcher` and falls back
to the generic matcher if `None` is returned. Whether and when the
compiled path is taken is invisible to the trace; the
`RuleFireTrace.derived_count` does not record which path produced the
binding. For debugging the rare case where compiled vs. generic
matching diverge (which the ARCHITECTURE.md says is "cross-checked
against the generic matcher in tests"), there is no observability.

**LOW-4: `parser.parse_atom_text` rejects bare `p()`.**
`parser.py:_find_atom_argument_bounds` (lines 345-354) demands
non-empty inner content between parens. The translator
(`propstore/grounding/translator.py:_stringify_atom:251-262`) must work
around this by emitting `p` rather than `p()` for arity-0 atoms. This
is asymmetric: bareword for arity-0, parens for arity ≥ 1. A
better-behaved parser would accept either.

**LOW-5: `disagreement.strict_closure` ignores its `seeds` argument when seeds and facts overlap.**
The function unions seeds and facts (`disagreement.py:54`). The "seed
the closure with `{h1, h2}`" pattern in `disagrees` (line 87) works
because the closure expands the union. But the `seeds` parameter would
be redundant if a caller always passes facts as `facts=`. Both
arguments serving the same role with no semantic difference invites
caller confusion. Minor naming/API issue.

**LOW-6: `_collect_conflicts` returns a value that callers ignore.**
`parser.parse_defeasible_theory` returns a 3-tuple
`(facts, rules, conflicts)`, with `conflicts` being a closure of
strong-negation pairs and user-supplied `theory.conflicts` pairs
(`parser.py:283-303`). Every caller in the codebase destructures with
`_conflicts` (underscore-ignored). Verified: `_internal.py:77`,
`grounding.py:76`, `dialectic.py:71, 85`, `closure.py` (skim). The
conflict set is computed and discarded everywhere except the strict-only
fast path's `_raise_if_strict_pi_contradictory`. Either propagate it
through `_GroundedTheory` so the dialectical pipeline can use it, or
stop computing it.

**LOW-7: `Policy` enum mixes orthogonal concerns.**
`schema.Policy` has `BLOCKING`, `RATIONAL_CLOSURE`,
`LEXICOGRAPHIC_CLOSURE`, `RELEVANT_CLOSURE`. The first selects a
dialectical-tree marking discipline; the last three dispatch to a
totally different evaluator (KLM closure). The `adapter.evaluate`
dispatcher uses set-membership in `_CLOSURE_POLICIES`
(`defeasible.py:55-59` and `adapter.py:59-64`) to route. Two unrelated
choices share one type. A consumer that wants to set a marking policy
and a closure independently has no way to express it. Refactor as two
enums.

## Missing features

- **Argument-level provenance accessor**. There is no
  `arguments_for_atom(model, predicate, args)` on `DefeasibleModel`.
  Callers must call `evaluate_with_trace` and use
  `trace.arguments_for_conclusion(...)`. See provenance section.
- **Per-fact rule-id back-pointer in the section dict**.
  `DefeasibleModel.sections["defeasibly"]["flies"]` returns
  `{("opus",), ...}`; there is no way to know which rule chain
  warranted any specific tuple without reaching into the trace.
- **Conflict-aware section projection**. `theory.conflicts` is plumbed
  into the strict-only fast path but the argument-pipeline path
  ignores it. A pair `(left_predicate, right_predicate)` declared as
  conflicting should be surfaced in the projection (e.g., split atom
  pairs into `undecided` when both sides end up `defeasibly`).
- **Antoniou ambiguity-propagating policy**. Documented as
  out-of-contract. Propstore may need it for `imports_are_opinions`
  semantics where two competing imports should both surface as
  conflicting rather than one being silenced by blocking marking.
- **Restricted vs. unrestricted rebut configuration**. Caminada-Amgoud
  2007's restricted-rebut switch (which forbids defeasible rebut on
  defeasibly-derived heads) is not exposed.
- **Argument minimality-set inspection**. `is_subargument` exists but
  there is no `minimal_arguments_for(atom)` helper.
- **Closure engine arity > 0**. `closure.py` is propositional only;
  any first-order use of KLM closure routes through the DeLP path
  instead.
- **Trace serialisation**. `DefeasibleTrace` carries dicts of
  unhashable types and is not JSON/yaml-serialisable. Propstore's
  sidecar persistence cannot store it.
- **Determinism contract on argument enumeration**. `build_arguments`
  returns `frozenset[Argument]`; ordering inside the frozenset is
  hash-based (i.e., depends on rule_id strings and CPython's hash seed
  if `PYTHONHASHSEED` is unset). The propstore `_argument_sort_key`
  re-sorts, but every gunray internal that iterates `arguments` uses
  set order. Determinism leaks.

## Open questions for Q

1. **Is `not_defeasibly` propstore-required, or a gunray invention?**
   `defeasible.py:196-229` projects an atom into `not_defeasibly` when
   *either* (a) its complement is warranted, *or* (b) a defeater rule
   probed it. The (b) clause is the Nute/Antoniou reading and has no
   Garcia 04 backing. Should `not_defeasibly` be split into two named
   sections (e.g., `defeated` and `probed`) or kept conflated?

2. **Should the propstore `ground()` always pass `return_arguments=True`?**
   The kwarg defaults `False` for "backwards compatibility" but every
   downstream consumer that wants to do anything beyond a yes/no query
   needs the argument set. Defaulting to `True` would also fix HIGH-3
   by making `inspect_grounding` redundant.

3. **`gunray.DefeasibleTheory.conflicts` is unused by propstore.** Is
   propstore intentionally not surfacing user-asserted predicate
   conflicts (e.g., `incompatible_with` rows from imports), or is this
   a missing wiring? If wired, the strict-only fast path would catch
   many more contradictions.

4. **Should gunray's evaluator emit a per-atom argument index?** The
   propstore notes mention "claim provenance dropped at the gunray
   boundary." A typed `Mapping[GroundAtom, tuple[Argument, ...]]` on
   `DefeasibleModel` would close the cluster B/D gap completely
   without needing the trace.

5. **Is the Policy enum split intentional (closure vs. dialectical)?**
   See LOW-7. If propstore plans to expose closure-policy queries
   alongside dialectical queries, conflating them in one enum is a
   trap.

6. **Does propstore plan to consume Maher 2021's compilation route, or
   stay on the direct DeLP pipeline?** CITATIONS lists Maher as
   "alternative path considered and not taken" but `notes/maher_*.md`
   in either repo would clarify the decision.

7. **`anytime.py` exists but is wired to nothing.** Is the bounded
   enumeration intended for a future API, or is it dead from a
   half-completed work item?
