# Cluster D: aspic_bridge + structured argumentation

Reviewer: Claude (Opus 4.7), 2026-04-26.

## Scope

In-scope code:
- `propstore/aspic_bridge/{__init__.py, build.py, extract.py, grounding.py, projection.py, query.py, translate.py, README.md}`
- `propstore/defeasibility.py`, `propstore/preference.py`, `propstore/condition_classifier.py`
- `propstore/core/literal_keys.py` (referenced)
- External: `argumentation/src/argumentation/aspic.py`, `argumentation/preference.py`

Tests skimmed (not run):
- `tests/test_aspic_bridge.py`, `tests/test_aspic_bridge_grounded.py`,
  `tests/test_aspic_bridge_review_v2.py`, `tests/test_argumentation_integration.py`,
  `tests/test_argumentation_package_track_e.py`,
  `tests/test_defeasibility_aspic_integration.py`.

Reference papers consulted (notes.md only): Modgil_2014, Modgil_2018,
Prakken_2010, Prakken_2012, Prakken_2013, Prakken_2019 (accrual),
Caminada_2007, Caminada_2006, Modgil_2009, Modgil_2011, Lehtonen_2024,
Wallner_2024 (value-based), Dauphin_2018, Li_2017, Thimm_2020,
Odekerken_2025, Toni_2014.

## ASPIC+ feature coverage matrix

Note: features delegated to the external `argumentation.aspic` kernel are
marked "kernel". Bridge-only features are marked with a propstore file.

| Feature (paper) | Status |
|---|---|
| Strict / defeasible rule split (Modgil 2014 Def 3.1; Modgil 2018 Def 2) | kernel `argumentation/aspic.py:138`; bridge maps in `translate.py:84-101` |
| Defeasible rule names `n(r)` (Modgil 2018 Def 2) | bridge stores justification id at `translate.py:99`; grounded rules synthesise names at `grounding.py:181`; **strict rules deliberately set `name=None`** (`translate.py:90`, `grounding.py:189`) |
| K_n / K_p split (Modgil 2014 Def 3.3; Modgil 2018 Def 4) | bridge `translate.py:223-237` (uses `premise_kind == "necessary"`) |
| Reported-claim premises | bridge `extract.py:62-71`, `translate.py:213-237` |
| Contrariness function (Modgil 2018 Def 1; Modgil 2014 Def 5.1) | partial — bridge `translate.py:106-183`. **Asymmetric contrary direction is only used for undercutters; classical-attack stances always produce contradictories** (`translate.py:136-140`) |
| Undermining attack (Def 8a) | kernel `aspic.py:1043-1047` |
| Rebut attack (Def 8b) | kernel `aspic.py:1049-1056`; modelled via stance type `rebuts` and via `claims_to_kb` premises |
| Undercut attack (Def 8c) | kernel `aspic.py:1058-1062`; bridge wires named-rule literals at `translate.py:141-178` |
| Restricted vs unrestricted rebut (Caminada/Amgoud 2007; Modgil 2018 §6.2) | **MISSING** — kernel does not expose a restricted-rebut switch and bridge does not select one. All rebuts are unrestricted (i.e. allow defeasible rebut on any defeasible head, regardless of strict-rule support of the head) |
| Preference-independent contrary attacks (Modgil 2014 Def 5.2; "contrary-based attacks always succeed") | **MISSING in bridge data path**. The bridge's `stances_to_contrariness` only writes contraries for undercutter rule-name literals (`translate.py:178`); rebut/undermine stances are *always* written as contradictories (`translate.py:137-140`). So propstore can never express a domain-level asymmetric contrary attack between two claim literals |
| Preference-dependent rebut/undermine (Def 9) | kernel `aspic.py:_set_strictly_less` & `compute_defeats`; bridge supplies `PreferenceConfig` |
| Last-link / weakest-link (Modgil 2018 Def 20-21) | kernel exposes both via `comparison`/`link` knobs; bridge default `comparison="elitist", link="last"` (`build.py:223`) |
| Elitist vs Democratic (Def 19) | kernel; bridge passthrough only |
| Premise ordering K_p (Def 19) | bridge `translate.py:255-305` via Pareto over `MetadataStrengthVector` (3-d). **Does not respect the comparison knob — premise order is built once via Pareto regardless of `elitist`/`democratic`** |
| Rule ordering R_d | bridge supports authored superiority pairs from grounded rule files via `grounding.py:232-270` projecting onto grounded instances |
| Transposition closure of strict rules (Modgil 2014 Def 4.3; Modgil 2018 Def 12) | kernel `transposition_closure`; bridge invokes at `build.py:149-153`. **Bridge passes a *modified* contrariness to transposition that drops preference-sensitive (`supersedes`/`undermines`) pairs (`build.py:96-111`). This is non-standard; see drift section** |
| Closure of K_n under strict rules (Modgil 2014 Def 3.4) | kernel `strict_closure` exists but bridge never calls it on K_n directly; it relies on argument construction |
| c-consistency (Modgil 2018 Def 6) | kernel `is_c_consistent`; **bridge does not check K_n c-consistency** before constructing arguments |
| Well-formedness postulate (Modgil 2014 §5: contraries cannot be axioms / strict-rule consequents) | **MISSING** — bridge never validates this; nothing prevents an undercutter rule-name literal from also appearing as a strict-rule consequent or as a K_n axiom |
| Sub-argument closure / strict closure / direct & indirect consistency postulates | not asserted at bridge level. Bridge tests `TestBridgeRationalityPostulates` (test_aspic_bridge.py:825) sample under Hypothesis but nothing in bridge code enforces them |
| Argument schemes (Modgil 2014 §4.3; Prakken 2013) | **MISSING** — no scheme/critical-question machinery; tests don't exercise schemes |
| Accrual of arguments (Prakken 2019) | **MISSING** — no accrual sets, no l-defeat, no `aSAF` |
| Value-based ASPIC+ (Wallner 2024) | **MISSING** — no value scale, agent-specific subjective KB, value filter |
| Preferential ASPIC+ / ASP encoding (Lehtonen 2024) | **MISSING** — no defeasible-element rephrasing; bridge always builds the full argument set |
| ASPIC-END (Dauphin 2018, natural-deduction explanations) | **MISSING** |
| Two forms of minimality / regular arguments (Li 2017) | **MISSING** — kernel can produce non-minimal / circular / redundant arguments and bridge does not filter them |
| Approximate reasoning by sampling (Thimm 2020) | **MISSING** |
| Incomplete information / IAFs (Odekerken 2025) | **MISSING from bridge**; the package has `partial_af.py` but the bridge never produces a partial AF from claim incompleteness |
| ABA reduction (Modgil 2014 §5; Toni 2014) | **MISSING** — no ABA rules / assumption polarity in the bridge |

## Bugs in build/extract/grounding/projection/query/translate

### HIGH

1. **Transposition closure runs against a *filtered* contrariness, then is
   used by `compute_defeats` against the *unfiltered* contrariness.**
   `build.py:149-179`. `_transposition_contrariness(contrariness, stance_pairs)`
   strips preference-sensitive (`supersedes` / `undermines`) directional
   pairs from `contradictories` before passing into `transposition_closure`,
   but `system.contrariness` (used downstream by `compute_attacks` and the
   defeat filter) is the *unfiltered* `contrariness`. Net effect: the
   transposed strict-rule set may not be closed under transposition with
   respect to the contrariness the system actually uses for attacks. Modgil
   2014 §5 (well-formedness for rationality postulates) requires the
   *whole* contrariness to participate in transposition. This is a silent
   correctness violation of postulates 1-4 (sub-argument closure, strict
   closure, direct/indirect consistency).

2. **`stances_to_contrariness` blindly writes every `rebuts` stance as a
   contradictory** (`translate.py:136-138`) without checking whether the
   pair is already known to be a contrary in the other direction. If a
   user authors `rebuts(a, b)` and `undermines(b, a)`, the latter is also
   a contradictory `(b, a)`; both end up symmetric. The asymmetric
   directional intent of `undermines`/`supersedes` is lost the moment a
   `rebuts` exists in either direction. There is no test for the mixed
   case in the test suite (search `test_stances_to_contrariness` —
   nothing covers conflicting authored stances).

3. **Premise ordering ignores the `comparison`/`link` knobs.**
   `translate.py:255-305` builds `premise_order` via `_component_wise_dominates`
   (Pareto on a 3-vector) regardless of whether the caller asked for
   elitist or democratic, last-link or weakest-link. Modgil 2018 Def 19
   defines set comparison; the *base order* on individual premises is the
   user's input. Pareto-domination is a propstore policy choice, but it
   forces a specific premise base order and ignores its own input parameter.
   Tests `TestPreferenceConfig` (test_aspic_bridge.py:616) do not assert
   that `comparison="democratic"` changes anything — they cannot, because
   the call only forwards the string into `PreferenceConfig`.

4. **`grounded_rules_to_rules` produces grounded undercutters using
   *only* the named-rule prefix match.** `grounding.py:206-226`. The
   undercutter constructed for a `defeater` rule attacks every grounded
   instance whose `name == defeater_head.contrary` — i.e. it requires the
   defeater head literal to *literally equal* the contrary of a rule name
   atom. Because rule name atoms have arity zero (`GroundAtom(rule.name)`),
   this only fires when the defeater rule conclusion is also a name
   literal. The intended Garcia-Simari / DeLP defeater semantics
   (defeater body => `~head_of_some_rule`) is not realised: the code
   compares `rule.consequent == defeater_head.contrary`, where `defeater_head`
   is a *content* literal, not a rule-name literal. The branch produces
   no undercutters whenever defeaters target content. (Reading: line 210
   filters `rule.consequent == defeater_head.contrary` — this can only be
   true when `defeater_head` is the negation of a rule-name literal, which
   is exactly what the rule-file `defeater` mode is meant to avoid.) Either
   the comment or the code is wrong; either way, the test
   `test_defeater_rule_in_bundle_emits_undercutter_rule`
   (test_aspic_bridge_grounded.py:711) appears to exercise a narrow case.

5. **`query_claim` uses a private kernel symbol.** `query.py:13` imports
   `_contraries_of` from `argumentation.aspic`. Underscore prefix marks
   private API; the package boundary doc (`docs/argumentation-package-boundary.md`)
   says propstore must consume the kernel through public API. Boundary
   violation; will break silently if the kernel renames.

6. **`query_claim` `arguments_against` only collects arguments whose
   conclusion is *exactly* a contrary of `goal`** (`query.py:99-107`). It
   does not include arguments that attack the goal via undercut on the
   rule that derives the goal, nor arguments that undermine an ordinary
   premise of the goal-deriving argument. Per Modgil 2018 Def 8 attack
   types are three; this query exposes only one. Callers that read
   `arguments_against` to compute "is this claim being challenged?" will
   miss undercuts and underminings.

7. **`csaf_to_projection` rewrites `framework.attacks` from `csaf.attacks`
   but `framework.defeats` from `csaf.framework.defeats`.** `projection.py:260-275`.
   Defeats use kernel ids verbatim (already filtered to projected ids);
   attacks rebuild via `csaf.arg_to_id`. If an `Attack`'s
   `attacker`/`target` is *not* in `csaf.arg_to_id`, it is silently
   dropped. There is no symmetric assertion that defeats whose ids exist
   must also exist as attacks. Skew between `attacks` and `defeats` will
   not be detected here.

### MED

8. **`_filter_preference_sensitive_stance_attacks` only inspects
   `undermining` and `rebutting`** (`build.py:182-214`). For `undercutting`
   it always passes the attack through. That is consistent with Modgil
   2018 Def 9 (undercut always defeats). But the *directional* intent of
   `supersedes` / `undermines` stances also implies the *reverse*
   undermining attack should be cut, not just contradictory rebuts.
   Currently the filter checks `(target_literal, attacker_literal) in
   directed_pairs and (attacker_literal, target_literal) not in
   directed_pairs`. For `undermining` attacks the `target_literal` is
   the *premise* of the target sub (`build.py:183-189`). Premises here
   are claim literals (positive), so the check works for directed claim
   attack pairs. But because `claims_to_kb` only puts a claim into K_p
   if it has a `reported_claim` justification, undermining-on-claim only
   triggers for those. The asymmetry of `supersedes(a, b)` does not
   protect `b` against an undermining attack from a *different* claim
   `c` whose conclusion is a contradictory of `b`'s premise — only
   pairs explicitly in `stance_pairs` are filtered.

9. **`build_arguments_for(... max_depth=10)` is hard-coded.**
   `query.py:60`. Real claim graphs may have deeper rule chains.
   Truncation silently produces an under-approximation of arguments;
   `arguments_for` may be empty when arguments do exist beyond depth 10.
   No warning is emitted.

10. **`csaf_to_projection` strength fall-back is `0.0` for vacuous opinions
    and `min` over sub-arguments for grounded** (`projection.py:204-208`,
    `projection.py:142-152`). But `_grounded_argument_strength` uses
    `_DEFEASIBLE_RULE_STRENGTH = 0.7` (`projection.py:33`) as a magic
    constant unconnected to either the metadata strength vector or the
    PreferenceConfig. So a "rule-derived" argument always reports 0.7
    even if the underlying defeasible rule has authored superiority that
    makes it strictly stronger / weaker than peers. Strength is therefore
    not faithful to the preference layer.

11. **`_default_support_metadata` collapses `(has_context, has_conditions)`
    into a 2x2 table** (`projection.py:36-47`) but only emits an
    `EXACT` `Label.empty()` when both are absent. There is no path that
    emits a `Label` when conditions exist; `(label, support_quality)`
    becomes `(None, MIXED|CONTEXT_VISIBLE_ONLY|SEMANTIC_COMPATIBLE)` and the
    explicit label is permanently lost. Downstream consumers reading
    `arg.label` for context-conditioned arguments always see `None`.

12. **`_arguments_concluding(csaf, claim_id)` matches by
    `conc(arg).atom.predicate == claim_id`** (`defeasibility.py:412-417`).
    For grounded predicate atoms the predicate is the predicate name, not
    a claim id; this match silently mis-fires when a claim id collides
    with a predicate name string. Since claim ids and predicate names
    share no namespace discipline (free-form strings), collisions are
    possible.

13. **`apply_exception_defeats_to_csaf` mutates the AF only with extra
    *defeats*, not extra attacks** (`defeasibility.py:373-389`). The
    new `framework` carries `defeats=csaf.framework.defeats | defeat_ids`
    but `attacks=csaf.framework.attacks` (unchanged). Downstream code
    reading `framework.attacks` to compute a Dung graph will not see the
    CKR exception edges. Consumers that key on `attacks` (e.g. bipolar /
    probabilistic AF construction) will silently lose the CKR layer.

14. **`grounded_rule_order_from_bundle` projects authored superiority
    by string-prefix match on rule names** (`grounding.py:253-268`,
    `_source_rule_id` at line 273). Two distinct schemas whose ids share
    a `#` boundary — or any rule whose user-authored id contains `#` —
    will alias. There is no assertion that authored ids are `#`-free.
    The substitution-key separator is also `#` (`grounding.py:181`); a
    user id like `r#weak` would split incorrectly.

15. **`stances_to_contrariness` raises `ValueError` for ambiguous
    undercut targets** (`translate.py:167-172`) but only if **no**
    `target_justification_id` is given and there is more than one
    matching defeasible rule. If exactly one matches at this moment,
    the bridge silently picks it; later bundle expansion may add a
    second matching grounded rule, retroactively turning the same
    stance into ambiguous. The pipeline is non-monotone w.r.t. authored
    stance correctness when bundles grow.

### LOW

16. **`extract.py:_extract_justifications` builds `justification_id` as
    `f"{stance_type}:{src}->{tgt}"`** (lines 75-83). The `->` substring
    is not escaped; if a claim id contains `->`, the id is ambiguous.

17. **`projection.py:_source_assertion_ids_for_claim` accepts strings
    *or* sequences** (lines 64-72) but a single string is wrapped as
    `(raw,)` while a list of one string is preserved verbatim. Two
    upstream conventions silently coexist.

18. **`build.py:_build_language` is called twice** (lines 147, 154).
    The second call recomputes the language after transposition closure.
    Each call iterates the entire literal/rule space. For large bundles
    this doubles the language build cost.

19. **`condition_classifier._try_z3_classify` raises bare
    `RuntimeError` on Z3 import failure** (lines 28-30). All upstream
    code paths must catch the bare exception; there is no typed
    `Z3Unavailable`.

20. **`preference.metadata_strength_vector`** falls back to
    `Opinion.vacuous` whenever metadata is incomplete (`preference.py:128-135`)
    but `_component_wise_dominates` (`translate.py:240-252`) returns
    `False` when `is_vacuous`. So a single vacuous-vector claim never
    contributes to `premise_order`. This is *almost* correct
    epistemically, but it also means metadata-rich claims among
    metadata-poor neighbours never get ordered against the poor ones,
    silently dropping authored confidence.

## Drift from Modgil_2014 reference paper

The bridge claims (in docstrings) to follow Modgil & Prakken 2018, but
Modgil 2014 is the cluster's named reference. Drift items:

A. **Contrariness is reduced to symmetric contradiction for content
   literals.** Modgil 2014 Def 5.1 makes the *contrary vs contradictory*
   distinction central: contrary attacks always succeed, contradictory
   attacks are preference-dependent. The bridge writes contraries only
   for undercutter rule-name literals (`translate.py:178`). Domain
   stances (`rebuts`, `supersedes`, `undermines`) all become
   contradictories. There is no path for a user to assert "claim a is a
   *contrary* of claim b" with the asymmetric, preference-independent
   semantics Modgil 2014 §5 describes. The DSL has thrown away half of
   Modgil's contrariness function.

B. **Restricted vs unrestricted rebut not chosen.** Caminada & Amgoud
   2007 (rationality postulates) requires a particular rebut policy for
   the postulates to hold; Modgil 2018 §6.2 discusses how preferences
   interact with restricted rebut. The bridge ships only the kernel's
   single rebut variant (unrestricted) and never asserts the postulates.
   Tests at `test_aspic_bridge.py:825` *spot-check* sub-argument closure
   and consistency under Hypothesis but do not verify the conditions
   under which they should hold.

C. **Well-formedness pre-flight missing.** Modgil 2014 §5 (last
   paragraph) requires that contraries cannot be axioms, ordinary
   premises, or strict-rule consequents. The bridge does no such check
   before assembling the `ArgumentationSystem`. A grounded bundle whose
   `definitely` section happens to inject a literal that some authored
   stance has marked as a contrary will silently violate well-formedness;
   the postulates may then fail with no diagnostic.

D. **Closure under transposition uses a deliberately *narrowed*
   contrariness.** As noted above (HIGH-1), `_transposition_contrariness`
   drops preference-sensitive contradictories from the relation passed
   into `transposition_closure`. The paper says transposition operates
   over the language and the contrariness; intentionally hiding part of
   the contrariness from transposition means the closed strict rule set
   may be *missing* transpositions that the unfiltered relation requires.
   Direct consistency (Modgil 2014 §4.2 Theorem) is no longer guaranteed.

E. **`PremiseArg.is_axiom`** distinction is honoured only at the kernel
   level. The bridge populates `KnowledgeBase` with axioms vs premises
   from `premise_kind == "necessary"` (`translate.py:232-235`) but
   `extract.py:_extract_justifications` builds `reported:{claim_id}`
   for *every* active claim — including those that should be axioms.
   `claims_to_kb` then sorts them into K_n vs K_p purely from the
   `premise_kind` *attribute*. If the active claim does not carry
   `premise_kind="necessary"`, it lands in K_p by default. The default
   silently makes propstore claims attackable. Modgil 2014 §3.3: K_n
   contains *necessary* premises; the framework gives the modeller the
   choice. The bridge collapses the choice to "K_p unless explicitly
   marked", which is asymmetric to the intended interpretation.

F. **Ordinary-premise undermining vs reported-claim semantics
   conflated.** Reported claims become `PremiseArg` (`is_axiom=False`),
   so they can be undermined. But `stances_to_contrariness` writes
   stance-based contradictories on the claim's positive literal, not
   on its negation. To undermine a premise `p`, the kernel needs an
   argument concluding a contrary of `p`. Per `claims_to_literals`,
   every claim is a *positive* literal; their `Literal.contrary` is the
   *structurally negated* form, which never appears as anyone's
   conclusion. So the only way an undermining attack ever fires for a
   claim premise is through the bridge's stance-injected contradictory
   pairs. This is a covert reduction of ASPIC+ semantics: the bridge
   never produces *negation-based* attacks on claims, only stance-based
   ones. Two claims with no authored stance between them never attack
   even if they are domain-level contradictories.

## Preference / value-based / accrual gaps

- **No value-based ASPIC+ at all.** Wallner 2024's value-based ASPIC+
  filters the knowledge base and rule set per agent. There is no agent,
  no value scale, no proposition-value scoring in propstore. Even the
  upstream `argumentation.value_based` module (visible at
  `argumentation/src/argumentation/value_based.py`, line count not
  inspected) is never imported by the bridge.
- **No accrual.** Prakken 2019's accrual sets and `l`-defeat are absent.
  Multiple parallel justifications for the same claim simply produce
  multiple arguments with the same conclusion; preferences do not
  combine cumulatively.
- **No preferential ASPIC+ (Lehtonen 2024).** The bridge always
  enumerates the full argument set via `build_arguments`; there is no
  defeasible-element rephrasing for scalability. For a rule-graph with
  branching factor `b` and depth `d`, the construction is `O(b^d)` —
  the bridge has no escape valve.
- **Premise ordering is metadata-only and 3-d Pareto.** The dimensions
  are `(log1p(sample_size), 1/uncertainty, confidence)` (`preference.py:137-141`).
  This conflates orthogonal evidence types: a claim with `n=10000` and
  `confidence=0.5` is incomparable to one with `n=5` and
  `confidence=0.99`, so neither becomes preferred. In practice,
  authored superiority is the *only* way to get a non-trivial rule
  ordering; Pareto on three independent metadata axes will almost
  always abstain.
- **No subjective-logic propagation.** `MetadataStrengthVector` carries
  an `Opinion`, but `_component_wise_dominates` looks only at
  `dimensions` and `is_vacuous`. The opinion's `b/d/u` decomposition is
  not used for the ordering. The whole point of carrying the
  uncertainty is therefore lost at the comparison step.
- **Authored superiority is projected by string-prefix match**
  (`grounding.py:253-268`). There is no schema-level guarantee that
  rule ids form a clean namespace; collisions silently merge orderings.
- **No rule-set comparison (set ordering on rules).** Modgil 2018 Def 19
  is implemented inside the kernel's `_set_strictly_less`, but the
  bridge supplies only individual rule pairs. There is no path for a
  user to assert "the *set* of rules `{r1, r2}` is preferred to
  `{r3, r4, r5}`" which is the full Def 19 semantics.

## How propstore couples to ../argumentation pkg (boundary cleanliness)

Surface use is mostly clean — the bridge imports public symbols from
`argumentation.aspic`, `argumentation.dung`, and `argumentation.preference`.
Specific concerns:

1. **Private symbol import**: `propstore/aspic_bridge/query.py:13` imports
   `_contraries_of`. The leading underscore is a public-API marker. The
   boundary doc (`docs/argumentation-package-boundary.md` lines 24-65)
   says the kernel owns its API surface; the bridge should not reach
   into `_`-prefixed names. Same in
   `tests/remediation/phase_5_bridge/test_T5_4_query_goal_contraries.py:1`.

2. **Star-import forbidden but not enforced**: the boundary doc forbids
   `from argumentation.dung import *` (line 148). I did not see any
   `import *` from argumentation in production code (Grep above). Good.

3. **Symbol leakage via default arg**: `propstore/aspic_bridge/__init__.py:23`
   uses `GUNRAY_COMPLEMENT_ENCODER` as a default. This is propstore-side,
   so OK, but the same `__init__` re-exports `grounded_rules_to_rules`
   with the encoder bound. The kernel `argumentation.aspic` does not
   know about complement encoders. The bridge keeps that knowledge on
   the propstore side, which is correct.

4. **`projection.py:260` calls `type(csaf.framework)(...)`** rather than
   importing the kernel's `ArgumentationFramework` constructor. Reflective
   construction couples to the runtime class without expressing the
   coupling at import time. If the kernel ever returns a subclass, this
   silently constructs the subclass; if it ever returns a frozen
   namedtuple, `type(...)(arguments=..., defeats=..., attacks=...)`
   may break. Importing the constructor explicitly is cleaner.

5. **`build.py:182-189` reads `attack.target_sub.premise`** by
   `isinstance` against `PremiseArg` and unpacks the `.premise`
   attribute. This is a stable kernel surface (Def 5 clause 1) but the
   bridge depends on the kernel's *concrete* dataclass shape rather
   than going through a `prem(target_sub)` helper. Brittle to kernel
   refactors.

6. **`docs/argumentation-package-boundary.md`** says (lines 95-101)
   `propstore.preference` owns *only* metadata strength vectors. That
   matches the file. Good. But `aspic_bridge/translate.py` *also*
   computes `_component_wise_dominates` locally (lines 240-252) instead
   of importing a comparable helper from `argumentation.preference`.
   Risk: two implementations of "Pareto on a vector" can drift. The
   kernel should either own this or the bridge should not duplicate it
   under a different name.

7. **`condition_classifier.py`** is imported by `defeasibility.py`
   indirectly (via cel/z3) but does not touch `argumentation`. Boundary
   clean.

8. **`defeasibility.py:21-22`** imports `Argument`, `CSAF`, `conc`
   (public), and `ArgumentationFramework` (public). Clean.

## Open questions for Q

1. Is the deliberate decision that propstore **never** asserts the
   asymmetric `contrary` direction between two domain claim literals?
   If so, Modgil 2014 §5's contrariness is half-implemented on
   purpose, and the bridge should stop documenting itself as following
   the general framework.

2. The transposition closure runs over a *filtered* contrariness
   (`build.py:96-111`). Is that intentional, or did someone narrow the
   transposition input to make the strict-rule set smaller without
   noticing it breaks the rationality postulate proofs?

3. `query_claim` uses a hard-coded `max_depth=10` (`query.py:60`).
   Is depth 10 the right ceiling for the largest expected claim graph,
   or should the cap come from the bundle / be configurable / be
   removed in favour of the kernel's `build_arguments`?

4. `arguments_against` (`query.py:99-107`) returns only conclusion-
   based contraries. Should it include arguments that undercut the
   goal-deriving rule and arguments that undermine premises of the
   goal-deriving argument? If yes, this is a bug; if no, the field is
   misnamed.

5. Magic constants `_STRICT_RULE_STRENGTH = 1.0` and
   `_DEFEASIBLE_RULE_STRENGTH = 0.7` in `projection.py:32-33` — what
   paper / decision do they trace to? They are not derived from the
   bundle, the metadata strength vector, or the preference config.

6. Default `comparison="elitist", link="last"` in `build.py:223`. Modgil
   2018 §3.5 notes both choices have trade-offs; Lehtonen 2024 Prop 17
   notes `weakest+grounded` is NP-hard. Has propstore made a deliberate
   choice for `last`? Premise order ignores both knobs (HIGH-3) — is
   that intentional?

7. Should `apply_exception_defeats_to_csaf` (`defeasibility.py:373-389`)
   also propagate the new edges into `framework.attacks` to keep
   bipolar/probabilistic projections consistent with the Dung edges?

8. `grounded_rules_to_rules` defeater branch (`grounding.py:206-226`):
   the documented intent is DeLP/Garcia-Simari defeaters that produce
   undercutters against opposing rules, but the implementation matches
   `defeater_head.contrary` against rule consequents. This appears to
   only fire for name-literal defeaters. Is the test
   `test_defeater_rule_in_bundle_emits_undercutter_rule` exercising the
   intended semantics, or is it testing the only case the implementation
   actually supports?

9. K_n vs K_p assignment is driven by `premise_kind == "necessary"`
   (`translate.py:232`). Default is K_p. Should the default flip in
   any policy mode (e.g. for definitional / curated background facts)?

10. Are `argumentation.value_based`, `argumentation.accrual` (if it
    exists), `argumentation.aspic_incomplete` deliberately not bridged
    yet, or is that scope creep that fell off?

11. Should the bridge perform a `is_c_consistent(K_n, R_s, contrariness)`
    pre-flight check (kernel `aspic.py:497`) and raise on inconsistent
    axioms? Right now an inconsistent K_n silently produces a CSAF whose
    extensions are vacuous-or-ill-defined.

12. The bridge produces only the "complete" CSAF (`build_bridge_csaf`)
    or a single-goal slice (`query_claim`). There is no streaming /
    incremental construction. For a 10k-claim bundle this is `O(n)` to
    `O(b^d)` per call. Is that acceptable, or is Lehtonen 2024 ASP
    encoding on the roadmap?

End of cluster D review.
