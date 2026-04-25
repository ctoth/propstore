# Argumentation bridge review — 2026-04-20

Scope: `propstore/aspic_bridge/**`, `propstore/praf/**`, `propstore/defeasibility.py`, `propstore/preference.py`. Formal kernel is the pip-installed `argumentation` package at `.venv/Lib/site-packages/argumentation/`.

## Layer / Boundary Violations

### 1. `apply_exception_defeats_to_csaf` injects CKR defeats into `framework.attacks` as well as `framework.defeats`
- File: `C:/Users/Q/code/propstore/propstore/defeasibility.py:359-368`
- Kernel contract (`argumentation/dung.py:19-33`): `framework.attacks` is the **pre-preference** attack layer; `framework.defeats` is post-preference. CKR exception defeats bypass preferences but are semantically derived defeats, not pre-preference attacks. Adding the same pairs to both fields conflates the two layers, and a consumer that iterates `framework.attacks` expecting the full Modgil/Prakken attack set will see CKR-injected pairs that have no corresponding `Attack` kind/target_sub record.
- Severity: medium-high (silent semantic drift; will corrupt any downstream that reasons off `attacks \ defeats`).
- Fix: inject only into `framework.defeats` and `csaf.defeats`; leave `framework.attacks` alone, or produce synthetic `Attack(kind="ckr_exception", ...)` records and add them to `csaf.attacks` in parallel. Do not pretend the Dung defeat edge is also an ASPIC attack.

### 2. `csaf.attacks` (typed `frozenset[Attack]`) is not updated by CKR injection
- File: `C:/Users/Q/code/propstore/propstore/defeasibility.py:320-373`
- `csaf.defeats` gets the new pairs (369-372) and `framework` gets them in arg-id form, but the structured `csaf.attacks: frozenset[Attack]` is never extended. Consumers that go back to the typed attack layer will see defeats with no matching Attack.
- Severity: medium (structural inconsistency between the two representations of the same relation).
- Fix: either mint exception `Attack` records or document and enforce that `csaf.attacks` is not preserved as a superset of defeats after CKR injection.

### 3. Supersedes + undermines silently treated as preference-independent contraries in bridge, conflicts with canonical vocabulary
- Files:
  - `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:135-136`
  - `C:/Users/Q/code/propstore/propstore/core/relation_types.py:17-24`
- `translate.stances_to_contrariness` maps both `supersedes` and `undermines` into `contrary_pairs`, which flows into the ASPIC+ `ContrarinessFn.contraries` set. `_is_preference_independent_attack` (aspic.py:655-667) treats contrary edges as preference-independent — so an undermining stance authored in propstore becomes an always-defeat edge regardless of `PreferenceConfig`. That directly contradicts `PREFERENCE_SENSITIVE_ATTACK_TYPES = {REBUTS, UNDERMINES}` in `relation_types.py:21-24` and Modgil/Prakken Def 9 (undermining **is** preference-sensitive).
- Severity: high (wrong defeat semantics on a canonical stance type).
- Fix: map `undermines` to `contradictory_pairs` (symmetric, preference-sensitive) and keep `supersedes` as contrary only if `supersedes` really means "preference-independent override" in propstore's stance vocabulary. Make the bridge agree with `relation_types.py`.

### 4. Bridge silently rewrites `stance_type=="contradicts"` to `"rebuts"`
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:29-37`
- `_coerce_bridge_stance_row` accepts a stance type that is NOT in `ATTACK_TYPES / GRAPH_RELATION_TYPES` (`core/relation_types.py`) and rewrites it locally. This is a local-only vocabulary extension hidden at the translation boundary. Storage-layer contract says stance types come from `GraphRelationType`.
- Severity: medium (drift between canonical stance vocabulary and bridge-accepted inputs; hides input validation errors).
- Fix: remove the special case; either add `contradicts` to the canonical vocabulary or reject it at the storage layer, not silently here.

### 5. `defeasibility._pattern_selects_use` returns `None` for unbound-variable patterns
- File: `C:/Users/Q/code/propstore/propstore/defeasibility.py:416-423`
- If a pattern references a name not in the use's bindings, the function returns `None` → `evaluate_contextual_claim` classifies the result as `UNKNOWN` / `INCOMPLETE_SOUND`. Authoring error (typo in binding name, missing binding) is invisible and collapses to "conservative UNKNOWN." Per CLAUDE.md "Honest ignorance over fabricated confidence" this is defensible, but it is indistinguishable from a solver-unknown exception.
- Severity: medium (authoring-error silencing masquerading as theoretical uncertainty).
- Fix: distinguish structural failures (unbound name, parse failure) from solver UNKNOWN. Raise or surface a `PatternBindingError` at evaluation time, or add a distinct `DecidabilityStatus.UNBOUND_VARIABLE`.

## Re-implementation of argumentation package

### 6. `translate._transitive_closure` re-implements `strict_partial_order_closure`
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:224-241`
- The package already exposes `argumentation.preference.strict_partial_order_closure` (used elsewhere in the same file at line 290, and in `grounding.py:12,269`). This private helper duplicates the logic and — crucially — does **not** validate irreflexivity or detect cycles, unlike the kernel helper. A cyclic premise order would be silently closed instead of raising.
- Severity: medium (dead reimplementation + looser contract than the canonical helper).
- Fix: delete `_transitive_closure` and call `strict_partial_order_closure(premise_order)`; accept that cyclic premise orders raise (they should).

### 7. `_goal_contraries` mirrors `_contraries_of` in the kernel
- Files:
  - `C:/Users/Q/code/propstore/propstore/aspic_bridge/query.py:50-62`
  - `argumentation/aspic.py:770-789` (`_contraries_of`, private but already used inside the kernel)
- Bridge re-implements the same loop over `language`. Acceptable as a helper, but flag: any future change to contrariness semantics (e.g., ABA-style negation handling) must be synchronized in two places.
- Severity: low (duplication, not drift yet).
- Fix: expose `_contraries_of` (or an equivalent) in the kernel's public surface and import it.

### 8. `_component_wise_dominates` is a private Pareto helper used once
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:216-221`
- Pareto dominance over fixed-length vectors is entirely generic. `metadata_strength_vector` lives in propstore, so its Pareto closure could be a candidate for either the kernel's `preference.py` or a propstore helper module, not translate internals.
- Severity: low.

## ASPIC+ / Dung Correctness

### 9. `build_bridge_csaf` filters defeats-to-ids with a condition that cannot be false
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/build.py:184-195`
- `arg_to_id` is populated from `sorted(arguments, key=repr)` (176-182). `attacks` and `defeats` only reference `Argument` instances produced by `compute_attacks` / `compute_defeats`, which are drawn from `arguments`. The guards `if attacker in arg_to_id and target in arg_to_id` are vacuous. The danger: the guards **hide** the invariant instead of asserting it. If someone later passes an `arguments` set smaller than the domain, defeats would silently disappear.
- Severity: low-medium (silent-failure smell).
- Fix: replace guards with assertions, or let the dict lookup raise.

### 10. `query_claim` computes defeats only over the goal-relevant argument subset
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/query.py:92-107`
- `build_arguments_for(..., include_attackers=True)` claims to include reinstatement chains (aspic.py:940-976). But `compute_attacks` / `compute_defeats` are called **only over this subset**, so attacks between included attackers and arguments **not reachable from the goal** are lost. For extension-level questions this is correct; for per-claim queries that also consider lateral attacks between attackers, results will differ from the full CSAF. Not obviously wrong, but worth naming in the docstring.
- Severity: low (documentation / callers-beware; returning "arguments_against" that ignores attackers on attackers could mislead).

### 11. `grounding._literal_for_atom` mutates the literal dict for "look up or insert"
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/grounding.py:121-133`
- Called during `grounded_rules_to_rules` and `_ground_facts_to_axioms`, so the caller's `literals` mapping is mutated. Fine for this pipeline, but it means `claims_to_literals → justifications_to_rules → stances_to_contrariness → grounded_rules_to_rules` ordering in `build.compile_bridge_context:102-111` matters: `stances_to_contrariness` runs **before** grounded rules add their literals, so stance target literals referring to claim ids work, but any stance whose source/target matches a grounded-atom literal key (ground_key) will silently `continue` at translate.py:124 because those literals don't exist yet. If future stances reference grounded predicates, this ordering will drop them.
- Severity: medium (ordering dependency with silent filter).
- Fix: either (a) build literals first (claims + grounded) then do stances once, or (b) explicitly document the invariant that stances may only target claim-keyed literals.

### 12. `grounding.grounded_rules_to_rules` adds defeaters as defeasible rules — undercut semantics encoded via literal negation
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/grounding.py:204-228`
- The defeater rule concludes the negation of a rule-name literal. For this to fire as an undercut, the contrariness function must include `(rule_name, ~rule_name)` contradictory. That only happens for rules already in `defeasible_rules` at the time `stances_to_contrariness` ran. But grounded defeater rules are added to `defeasible_rules` **after** `stances_to_contrariness` is called (build.py:108-111), so their own rule-name contradictions are registered (translate.py:112-116 runs over the `defeasible_rules` passed in — which at that point only contains justification-derived rules). Grounded undercuts therefore rely on `build_language` adding `name_lit.contrary` (build.py:74-79), AND on the kernel's `compute_attacks` generating undercut attacks via the `name_lit` / `target_rule_name` contradiction. That contradiction is not seeded in contrariness, so undercut attacks via grounded defeaters may fail to materialize.
- Severity: high (if verified — bug that silences grounded undercut defeaters).
- Fix: call `stances_to_contrariness` (or a dedicated rule-name contrariness pass) after the full `defeasible_rules` set is assembled, including grounded rules. Alternatively seed contradictory `(rule_name, ~rule_name)` pairs for **every** defeasible rule, not only those present at the first stance pass.

### 13. Defeater "directional contrary" not installed
- File: same as above.
- Related: the `~rule_name` contradictories exist, but there is no **contrary** pair (asymmetric). Per `_is_preference_independent_attack` (aspic.py:662-667), undercutting is unconditionally preference-independent via its `kind` — so the contradictory wiring is sufficient in that path. But if a consumer inspects `contraries` to reason about preference-independence, they will wrongly treat an undercut as preference-dependent. The kernel itself is fine; bridge consumers may mis-classify.
- Severity: low.

### 14. `compute_defeats` semantics vs bridge reasoning about "always-defeat"
- Not a bridge bug, but a reminder: `_is_preference_independent_attack` checks `contraries.is_contrary(conc(attacker), target_lit)`. If the bridge puts a pair into `contraries` under `undermines` (finding 3), then every `undermine` attack becomes preference-independent, silently overriding `PreferenceConfig`. Same root cause as 3.

## Bugs & Silent Failures

### 15. `preference.metadata_strength_vector` fabricates finite strength when uncertainty is missing
- File: `C:/Users/Q/code/propstore/propstore/preference.py:32-36`
- When `uncertainty` is `None`/`0`, `inverse_uncertainty` defaults to `1.0`. That is a made-up number, violating CLAUDE.md: "a made-up 0.75 is not" a valid signal. A claim with no uncertainty data ends up comparable-at-Pareto to a claim with measured uncertainty = 1.0.
- Severity: high (principle violation; affects every preference-derived defeat filter).
- Fix: return a sentinel / None for the missing component, skip Pareto comparison when any component is missing, or mark the vector as `vacuous` and exclude from premise order.

### 16. `translate.justifications_to_rules` silently drops justifications whose premises are unknown
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:73-76`
- If a premise literal is not in `literals`, the rule is skipped with no warning. Combined with finding 11, upstream filtering mistakes disappear.
- Severity: medium.
- Fix: at minimum log; preferably raise when a referenced claim id is missing and only skip when the *conclusion* is an intentional out-of-scope reference.

### 17. `stances_to_contrariness` raises on ambiguous undercut but only if `target_justification_id is None`
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/translate.py:163-168`
- Correct behavior. But if `target_justification_id` is given and matches zero rules (line 157-162), the error message says "did not match a defeasible justification for target claim" — the user-facing ID is `target_claim_id` rather than including candidates considered. Debuggability.
- Severity: low.

### 18. `projection.csaf_to_projection` infers `claim_id` only from literal predicate string identity
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/projection.py:76-80`
- `claim_id = conclusion.atom.predicate if conclusion.atom.predicate in claim_id_set and not conclusion.negated else None`. A grounded atom whose predicate happens to equal a claim id would be misattributed as the claim, and its `arguments` tuple would be ignored entirely (predicate match is string-only). Probability low, but collision possible across claim ids and predicate namespaces.
- Severity: low-medium.
- Fix: match via `LiteralKey` not raw predicate; carry the ClaimLiteralKey / GroundLiteralKey distinction through to the projection.

### 19. `projection.csaf_to_projection` computes `premise_claim_ids` and `dependency_claim_ids` identically
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/projection.py:91-95, 123-127`
- Exact duplicate tuple. Either the two concepts have diverged in spec and the implementation hasn't caught up, or one of the fields is dead.
- Severity: low (dead/confused data model).
- Fix: remove one field, or define a real difference (e.g., include grounded-fact antecedents in dependencies but not premises).

### 20. `projection.csaf_to_projection` strength defaults to 0.0 for grounded-only arguments
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/projection.py:102-106`
- "no claim → strength 0.0" silently makes every grounded-rule argument the weakest possible. This is not vacuousness-correct; it fabricates the lowest strength. With Pareto dominance (finding 15), the all-zero vector would be dominated by almost everything.
- Severity: medium.
- Fix: use a vacuous-strength marker or exclude non-claim arguments from metadata comparison.

### 21. `defeasibility.evaluate_contextual_claim` multiple-exception policy issue is reported but both defeats are still emitted
- File: `C:/Users/Q/code/propstore/propstore/defeasibility.py:287-294, 310-317`
- When >1 exception applies, a `MULTIPLE_APPLICABLE_EXCEPTIONS` policy issue is recorded, but `defeats` contains all of them. Downstream `apply_exception_defeats_to_csaf` blindly adds every defeat edge (334-354). The "policy issue" is advisory only — it does not gate defeat injection.
- Severity: medium (silent conflict resolution by union).
- Fix: decide a policy: either emit all defeats (current, but document), or require the caller to resolve policy issues before passing results to `apply_exception_defeats_to_csaf`.

### 22. `apply_exception_defeats_to_csaf` raises on empty attacker arguments
- File: `C:/Users/Q/code/propstore/propstore/defeasibility.py:347-350`
- `"CKR exception has no ASPIC argument for its justification claims"` fires if *any* exception has no attackers, even if other exceptions for the same use DO. The result is all-or-nothing rather than per-exception. Combined with finding 21, this couples unrelated exceptions' fate.
- Severity: medium.
- Fix: skip the exception with a warning; continue with those that have attackers.

### 23. `praf.engine.enforce_coh` falls back to `defeats` when attacks is None
- File: `C:/Users/Q/code/propstore/propstore/praf/engine.py:281`
- `attacks = praf.framework.attacks if praf.framework.attacks is not None else praf.framework.defeats`. COH is about argument-vs-attacker pairs (pre-preference), not defeats. Enforcing COH on the post-preference relation double-counts preferential filtering and produces the wrong constraint surface. Dung framework explicitly separates the two.
- Severity: high (principle / semantics error for probabilistic consistency).
- Fix: require `framework.attacks` to be populated for COH enforcement; raise rather than silently fall back.

### 24. `praf.engine.enforce_coh` fixed-point loop silently truncates at 100 iterations
- File: `C:/Users/Q/code/propstore/propstore/praf/engine.py:297-315`
- No convergence detection beyond "no violations this pass." If the projection step does not contract (pathological `n`/base-rate setups), the loop stops at 100 and returns a still-incoherent state with `changed=True`, allowing the final reconstruction block (320-333) to emit opinions that do not satisfy COH.
- Severity: medium.
- Fix: after the loop, assert `any_violation is False`; if not, raise a non-convergence error.

### 25. `praf.engine.enforce_coh` assumes `evidence_n = 10.0` when `u <= 1e-9`
- File: `C:/Users/Q/code/propstore/propstore/praf/engine.py:293-295`
- Magic constant. Per CLAUDE.md this is fabricated confidence for zero-uncertainty opinions.
- Severity: medium.
- Fix: make the non-vacuous evidence count explicit in the Opinion type or error for u≈0.

### 26. `summarize_defeat_relations` constructs `Opinion(p, 1-p, 0, 0.5)` with no provenance
- File: `C:/Users/Q/code/propstore/propstore/praf/engine.py:380-384`
- Every derived relation is given dogmatic certainty (u=0) and a hard-coded base rate of 0.5, without `Provenance`. The summary output pretends to be calibrated.
- Severity: high (violates the "typed provenance" principle; the Opinion lacks `ProvenanceStatus.CALIBRATED` or `STATED` marker).
- Fix: attach proper `Provenance(status=CALIBRATED, ...)` and carry forward the input provenance.

## Dead Code / Drift

### 27. `_transitive_closure` duplicate (see finding 6).

### 28. `premise_claim_ids` vs `dependency_claim_ids` duplicate (see finding 19).

### 29. `extract._extract_justifications` silently ignores stance attributes when promoting to justifications
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/extract.py:72-83`
- The attributes are threaded through, but there is no validation that the original stance was a defeasible support vs a scientific-method explanation — both become the same rule_kind literal. Fine only if `rule_strength` resolution happens downstream.
- Severity: low.

### 30. `_gunray_complement` prefix-toggle predicate encoding is tunneling gunray-specific encoding through the ASPIC bridge
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/grounding.py:17-31`
- The ASPIC bridge should not know about the `~`-prefix convention of a specific grounding toolchain. This leaks a storage-encoding concern into the translation layer.
- Severity: low-medium.
- Fix: normalize predicate polarity at the grounding boundary (inside `propstore.grounding`), pass typed `(predicate, negated)` into the bridge.

### 31. `aspic_bridge/__init__.py` does not export `apply_exception_defeats_to_csaf`
- File: `C:/Users/Q/code/propstore/propstore/aspic_bridge/__init__.py`
- Callers must reach into `propstore.defeasibility` directly to compose the CKR boundary injection with `build_bridge_csaf`. The boundary contract in CLAUDE.md says defeasibility "injects exception-derived Dung defeats AT the ASPIC+ boundary" — but that composition is not surfaced from the bridge facade. Callers can wire it wrong.
- Severity: low (ergonomics), medium (invariant enforcement).
- Fix: add a `build_bridge_csaf_with_exceptions` (or accept an `exceptions` param on `build_bridge_csaf`) that composes the two.

## Positive Observations

- `aspic_bridge` correctly imports formal types from `argumentation.aspic` rather than re-implementing; `Literal`, `Rule`, `KnowledgeBase`, `ArgumentationSystem`, `CSAF`, `build_arguments`, `compute_attacks`, `compute_defeats`, `transposition_closure` are all kernel-sourced.
- `defeasibility.py` does not extend ASPIC+ internals; it only consumes the public CSAF surface and adds Dung-level defeat edges. The separation of concerns — CKR decides which contextual uses are excepted, ASPIC+ owns argument construction — matches CLAUDE.md.
- `strict_partial_order_closure` is reused both for `rule_order` (translate.py:290) and for grounded rule projection (grounding.py:269), with proper cycle detection.
- `query_claim` correctly uses kernel `build_arguments_for` (goal-directed, memoized) with `include_attackers=True`; it does not re-implement backward chaining.
- `contrariness` construction includes rule-name literals for every named defeasible rule at the time stances are processed — the mechanism for wiring undercuts is in place (even if ordering relative to grounded rules is a concern, finding 12).
- `preference.strictly_weaker` (kernel) handles elitist/democratic comparisons; the bridge delegates rather than re-implementing.
- No context semantics (`ist(c, p)`, lifting, CKR) leak into the kernel: grep over `argumentation/aspic.py` for `context|ist|CKR|exception|lifting` finds only string matches inside unrelated docstrings. ASPIC+ does not own context semantics.

## Summary of highest-severity issues

Must-fix (functional or principle-violating):
- 3 (undermines → contrary): wrong defeat-filter semantics, contradicts canonical `relation_types`.
- 12 (grounded undercut contrariness): likely silent no-op for grounded defeaters.
- 15 (fabricated `1/uncertainty`): fabricated confidence.
- 23 (enforce_coh falls back to defeats): wrong-layer COH enforcement.
- 26 (dogmatic opinions w/o provenance): provenance violation in `summarize_defeat_relations`.

Needs resolution but less urgent:
- 1 (CKR into attacks), 2 (csaf.attacks not updated), 4 (`contradicts` rewrite), 11 (ordering dependency), 20 (grounded-arg strength 0), 21/22 (multiple-exception policy coupling), 24/25 (COH magic constants).
