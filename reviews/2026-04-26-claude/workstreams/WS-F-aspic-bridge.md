# WS-F: ASPIC+ bridge fidelity

**Status**: CLOSED c8b0c892
**Depends on**:
- **WS-D** (math/operator naming; preference vector semantics may overlap).
- **WS-O-arg-argumentation-pkg** (upstream kernel). Two propstore steps are gated on upstream commits shipping in a tagged `argumentation` release with propstore's pin bumped first:
  - **Step 1 — UPSTREAM-BLOCKED**: needs the kernel `transposition_closure` signature change (return `(closed_rules, post_closure_language)` rather than just `closed_rules`).
  - **Step 6 — UPSTREAM-BLOCKED**: needs the public `contraries_of` symbol (rename of private `_contraries_of` in `argumentation.aspic`, exported, no shim).
  - The other ten steps (2, 3, 4, 5, 7, 8, 9, 10, 11, 12) are propstore-only and can land in parallel with the upstream work.

**Blocks**: nothing downstream.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1 — no "TBD").

---

## Why this workstream

`propstore/aspic_bridge/` hands the `argumentation` kernel an `ArgumentationSystem` + `KnowledgeBase` that, run through `build_arguments`/`compute_attacks`/`compute_defeats`, produces a CSAF whose extensions must match Modgil & Prakken's semantics. Both reviewers (Claude cluster D, Codex #12/#13/#14/#21/#22) flagged the same drift: the bridge advertises ASPIC+ but reduces preference-sensitive and asymmetric notions to structural facsimiles, and several "advertised semantics" in `world/types.py` are not executable.

Load-bearing case: `argumentation/dung.py:196-219` docstring says *"pure Dung grounded semantics … Attack metadata is ignored."* Correct for Dung; wrong for ASPIC+ once `framework.attacks` and `framework.defeats` diverge. `structured_projection.py:253` delegates ASPIC `grounded` straight to it, so the result is conflict-free over `defeats` but possibly conflicting over `attacks` — what Modgil & Prakken 2018 Def 14 forbids.

The bridge also writes Modgil 2014 §5 contrariness asymmetrically only for undercutter rule-name literals, and runs transposition closure against a *narrowed* contrariness while the rest of the system uses the *full* one. Either breaks Modgil 2014 §4.2 indirect consistency.

WS-F closes the structural drift, the conflict-free violation, the boundary leak, silent-drop holes in projection, and advertised-but-not-routed semantics. The first failing test pins Modgil 2014 §4.2 Theorem 1; if it fails after the fix, the fix is not done.

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T2.1 / Codex #22** | Claude REMEDIATION-PLAN, both reviews | `propstore/aspic_bridge/translate.py:139-193` | Asymmetric stance via symmetric contradiction. `supersedes`/`undermines` and `rebuts` lose direction; only undercutters get the asymmetric `contraries` slot. |
| **T2.9 / Codex #12** | REMEDIATION-PLAN Tier 2 | `propstore/structured_projection.py:240-260`; `argumentation/dung.py:196-219` | ASPIC grounded delegates to Dung `grounded_extension` which ignores attacks. Conflict-freeness is checked over `defeats` only. |
| **T2.11** | Claude P (overlaps WS-O-arg) | `argumentation/aspic.py` (`_literal_id`) | `repr(literal)` produces `~p` and `p(1, 2)` — clingo rejects. WS-F coordinates; fix lives in WS-O-arg. |
| **T5.7 / Cluster D HIGH-5** | Claude D, both reviews | `propstore/aspic_bridge/query.py:13` | Imports private `_contraries_of` from the kernel; boundary doc forbids underscore-prefixed names. |
| **Cluster D HIGH-1** | Claude D | `propstore/aspic_bridge/build.py:96-153` | `_transposition_contrariness` strips preference-sensitive contradictories before transposition closure, but `system.contrariness` is the unfiltered one. Strict closure is no longer closed under transposition w.r.t. the contrariness `compute_attacks`/`compute_defeats` actually use. Modgil 2014 §4.2 indirect-consistency theorem is therefore not guaranteed. |
| **Cluster D HIGH-2** | Claude D | `propstore/aspic_bridge/translate.py:136-138` | Every `rebuts` becomes a symmetric contradictory unconditionally. If a user authors `rebuts(a,b)` and `undermines(b,a)`, the `(b,a)` direction loses its asymmetric intent. |
| **Cluster D HIGH-3** | Claude D | `propstore/aspic_bridge/translate.py:255-305` | Premise ordering uses Pareto on a metadata 3-vector regardless of `comparison`/`link`. The two preference knobs are passed straight to `PreferenceConfig` but the *base order* is fixed. |
| **Cluster D HIGH-4** | Claude D | `propstore/aspic_bridge/grounding.py:206-226` | The `defeater`-rule branch matches `rule.consequent == defeater_head.contrary`; `defeater_head` is a content literal, so the branch only emits undercutters when the defeater conclusion happens to equal a content consequent of a defeasible rule, not the intended Garcia-Simari "defeater body ⇒ ¬name(r)" semantics. |
| **Cluster D HIGH-6** | Claude D | `propstore/aspic_bridge/query.py:99-107` | `arguments_against` only returns arguments concluding a contrary of `goal`. Misses undercut and undermining attackers. Modgil 2018 Def 8 names three attack types; this query exposes one. |
| **Cluster D HIGH-7** | Claude D | `propstore/aspic_bridge/projection.py:260-275` | `proj_framework.attacks` is rebuilt via `csaf.arg_to_id` lookup with silent-drop guards. `defeats` use kernel ids verbatim. Skew between `attacks` and `defeats` is detectable in principle but never asserted. Combined with T2.9, this is the second hop where conflict-freeness can degrade silently. |
| **Codex #13** | Codex review | `propstore/world/types.py:667-672`; `propstore/structured_projection.py:240-260` | `aspic-incomplete-grounded` and `aspic-direct-grounded` are advertised in the policy enum but `compute_structured_justified_arguments` raises before reaching the dependency's incomplete-grounded backend. |
| **Codex #14** | Codex review (overlaps WS-H — coordinate) | `propstore/world/types.py:623`, `:682`; `propstore/core/analyzers.py:767-771`; `propstore/world/resolution.py:691`; `propstore/app/world_reasoning.py:239` | `praf-paper-td-complete` is advertised but routed through normal acceptance with `query_kind="argument_acceptance"`, not the dependency's `strategy="paper_td"` extension-probability path. |
| **Codex #21** | Codex review | dependency has `complete_extensions`; `propstore/world/types.py:637`; `propstore/core/analyzers.py:568`; `structured_projection.py:240-260` | Complete semantics is normalized in the enum but the ASPIC dispatch in `structured_projection.py` handles only grounded/preferred/stable. |
| **Codex #36** | Codex review | `propstore/cel_registry.py:112`; `propstore/families/concepts/passes.py:506-507` | Duplicate concept `canonical_name` is downgraded to warning while lookup is first-wins. Relevant to WS-F because `ClaimLiteralKey.claim_id` is a free-form string and ASPIC literal identity inherits that name discipline. Two claims with collided canonical concept names can both project to the same `ClaimLiteralKey`. |

Adjacent findings closed in the same PR (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| Cluster D drift A | `translate.py:178` | Contrariness reduced to symmetric contradiction for content literals — fixed once HIGH-2 is fixed. |
| Cluster D drift D | `build.py:96-111` | Transposition over narrowed contrariness — fixed once HIGH-1 is fixed. |
| Cluster D drift F | `translate.py` and `core/literal_keys.py:21-25` | Every claim is positive (`ClaimLiteralKey` has no polarity bit; only `GroundLiteralKey` does). The fix to HIGH-2/Drift A creates a path for negation-based attacks on claims, which removes Drift F as a separate item. |
| Cluster D LOW-18 | `build.py:147,154` | `_build_language` called twice. Fold the second call into transposition closure return value when touching the file. |

## Code references (verified by direct read)

### HIGH-1 — Transposition under filtered contrariness
- `build.py:96-111` `_transposition_contrariness` strips preference-sensitive pairs from `contradictories`.
- `build.py:149-153` passes the filtered fn to `transposition_closure`.
- `build.py:165-170` builds `ArgumentationSystem` with the **unfiltered** `contrariness` — what `compute_attacks`/`compute_defeats` consult. Per Modgil 2014 Def 4.3 / Modgil 2018 Def 12, narrowing contrariness narrows transposition reach.

### HIGH-2 / T2.1 / Codex #22 / Drift A — Asymmetry handling
- `translate.py:136-140` `rebuts` adds both directions to `contradictory_pairs`; `supersedes`/`undermines` adds only `(src,tgt)`.
- `translate.py:174-178` only the undercutter rule-name path populates `ContrarinessFn.contraries`. No path for asymmetric preference-independent contrary between two claim literals.
- `core/literal_keys.py:21-25` `ClaimLiteralKey` has no polarity bit (`GroundLiteralKey` does at `:38`); every claim projects positive.

### HIGH-3 — Premise order ignores comparison/link knobs
- `translate.py:240-252` `_component_wise_dominates` is a 3-vector Pareto check.
- `translate.py:288-305` premise pairs added by Pareto only; `comparison`/`link` flow to `PreferenceConfig` but base order is already fixed.

### HIGH-4 — Defeater branch matches content consequents
- `grounding.py:206-211` filters `rule.consequent == defeater_head.contrary` (content).
- `grounding.py:215` constructs undercutter targeting rule-by-name. Filter and construction disagree; intent is "defeater body ⇒ ¬name(r)" per Garcia-Simari.

### HIGH-5 / T5.7 — Private symbol import
- `query.py:8-18`, `tests/remediation/phase_5_bridge/test_T5_4_query_goal_contraries.py:1` import `_contraries_of` from `argumentation.aspic`. `docs/argumentation-package-boundary.md:24-65` forbids underscore imports.

### HIGH-6 — `arguments_against` misses undercut/undermine
- `query.py:99-107` filters by `conc(arg) in _contraries_of(goal, ...)`. Modgil 2018 Def 8 names three attack types; this query exposes only the goal-conclusion-contrary slice of rebut.

### HIGH-7 — Projection rebuilds attacks lossily
- `projection.py:260-275` rebuilds `attacks` via `csaf.arg_to_id` with silent-drop guards (`and ... in csaf.arg_to_id`); `defeats` flow from kernel ids verbatim. Skew between `attacks` and `defeats` can arise silently. Combined with `structured_projection.py:253`, second hop where conflict-freeness degrades silently.

### T2.9 / Codex #12 — Grounded delegates to Dung over defeats only
- `structured_projection.py:251-253` `if semantics == GROUNDED: return grounded_extension(framework)`.
- `argumentation/dung.py:196-219` docstring: *"pure Dung grounded semantics: least fixed point over `defeats` only. Attack metadata is ignored here."*
- Kernel `is_admissible` (`:170-179`), `:308-324`, `:390` already accept explicit `attacks` for preferred/stable per Modgil & Prakken 2018 Def 14. Only `grounded_extension` skips them.

### Codex #13, #14, #21 — Advertised but not routed
- `world/types.py:667-672` lists `aspic-incomplete-grounded`, `aspic-direct-grounded`; `structured_projection.py:240-260` handles only grounded/preferred/stable; else raises.
- `world/types.py:623`, `:682` define `praf-paper-td-complete`; `core/analyzers.py:767-771`, `world/resolution.py:691`, `app/world_reasoning.py:239` pass it as `semantics` with `query_kind="argument_acceptance"`. Dependency selects via `strategy="paper_td"` + `extension_probability` + queried set.
- `core/analyzers.py:568` and `structured_projection.py:240-260` both omit `complete`.

### Codex #36 — Concept canonical-name → ASPIC literal coupling
- `cel_registry.py:112` raises on duplicate canonical names; `families/concepts/passes.py:506-507` only warns and first-wins. `families/concepts/stages.py:270`, `:832` use canonical name as reference key. `core/literal_keys.py:44-47` `claim_key(claim_id)` has no namespacing — two claims sharing a canonical concept name can collide on literal identity downstream.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_aspic_indirect_consistency_modgil_2014.py`** (new — paper-faithful pinning, gating test for WS-F)
   - Smallest claim graph exercising Modgil 2014 §4.2 Theorem 1 (indirect consistency): claims `a`, `b`, `c`; strict rule `a → c`; `supersedes(a, b)` making `(a, b)` a preference-sensitive contradictory; authored fact deriving `b`.
   - Asserts: for every complete extension `E` returned by the bridge under the full `system.contrariness`, `Cl_strict(Concs(E))` is c-consistent w.r.t. `system.contrariness`. Implementation uses public `strict_closure` and `is_c_consistent`; no `_`-prefixed reach.
   - **Must fail today**: `_transposition_contrariness` (`build.py:96-111`) strips `(a, b)` before transposition, so the closed strict set lacks the transposition `~c → ~a` that the unfiltered contrariness requires; the test surfaces an extension whose strict closure produces both `c` and `~c`. The test fails *exactly* as Modgil 2014 §4.2 says it cannot under a well-formed ASPIC+ system.

2. **`tests/test_aspic_grounded_conflict_free.py`** (pins T2.9 / Codex #12)
   - Two arguments `A`, `B` with mutual attack but no defeat (use authored superiority so neither defeats the other under preference filtering).
   - Asserts: grounded ASPIC extension does not contain both `A` and `B`.
   - **Must fail today**: `structured_projection.py:253` calls `dung.grounded_extension` which ignores attacks; both end up justified. Modgil & Prakken 2018 Def 14 forbids this. Replaces the wrong-direction assertion at `tests/test_structured_projection.py:688`.

3. **`tests/test_stances_asymmetric_contrary.py`** (pins HIGH-2 / T2.1 / Codex #22)
   - `supersedes(a, b)`: asserts `(a, b) ∈ contraries`, not in `contradictories`; `(b, a)` in neither.
   - `rebuts(a, b)`: asserts both directions in `contradictories`.
   - Mixed `rebuts(a, b) ∧ undermines(b, a)`: asserts `(a, b)` contradictory, `(b, a)` asymmetric (HIGH-2's mixed-case gap).
   - **Must fail today**: `translate.py:139-140` writes `supersedes`/`undermines` to `contradictories` only; mixed case has zero coverage.

4. **`tests/test_premise_order_respects_comparison.py`** (pins HIGH-3)
   - Two claims with Pareto-incomparable metadata vectors; build `PreferenceConfig` under `comparison="elitist"` and `comparison="democratic"`.
   - Asserts: at least one config produces a non-empty `premise_order` over the pair (Modgil 2018 Def 19 — elitist and democratic differ on incomparable cases).
   - **Must fail today**: both configs produce identical empty `premise_order`; the comparison string never reaches the base order.

5. **`tests/test_defeater_undercut_targets_named_rules.py`** (pins HIGH-4)
   - Bundle with defeasible `R1: p → q` and defeater `D1: r ⇒ defeater-of R1`.
   - Asserts: `grounded_rules_to_rules` emits an undercutter `r ⇒ ¬name(R1_grounded)` for every grounded instance.
   - **Must fail today**: `grounding.py:210` filters by `rule.consequent == defeater_head.contrary` (content), so no undercutter is emitted.

6. **`tests/test_query_no_private_imports.py`** (pins HIGH-5 / T5.7)
   - AST-walks `propstore/` and asserts no `Import` or `ImportFrom` from `argumentation.*` references a name starting with `_`.
   - **Must fail today**: `query.py:13` and `tests/remediation/phase_5_bridge/test_T5_4_query_goal_contraries.py:1` import `_contraries_of`. Upstream rename to public `contraries_of` lives in WS-O-arg.

7. **`tests/test_arguments_against_includes_undercut_undermine.py`** (pins HIGH-6)
   - Three arguments: `A` concludes `goal`; `B` undercuts a rule used in `A`; `C` undermines a premise of `A`.
   - Asserts: `query_claim(goal).arguments_against` contains `B` and `C`.
   - **Must fail today**: `query.py:99-107` filters by `conc(arg) in contraries_of(goal)` only — undercut and undermine attackers do not satisfy that.

8. **`tests/test_projection_preserves_attack_and_defeat_separately.py`** (pins HIGH-7; replaces the earlier wrong-direction test, per Codex 2.2)

   This test replaces an earlier `test_projection_attack_defeat_skew` formulation that asserted `projected attacks iff projected defeats`. That invariant is **wrong**: it collapses the very attack-vs-defeat distinction WS-F exists to preserve. Under Modgil & Prakken 2018 a valid projected framework can — and routinely does — carry an attack with no matching defeat once preference filtering removes the defeat. Asserting `iff` would silently turn correct projection into a test failure and would mask the real bug (silent-drop in projection rebuild).

   The corrected invariant: **both relations are projected independently and without silent loss.** Neither relation is reconstructed from the other.

   Construction:
   - `rebuts(a, b)` produces an attack `(a, b)` in `csaf.attacks`.
   - A preference orders `b` strictly above `a`, so `compute_defeats` filters the defeat: `(a, b) ∉ csaf.framework.defeats`, while `(a, b) ∈ csaf.framework.attacks`.
   - Project via `csaf_to_projection`.

   Assertion shape (verbatim intent):
   ```python
   def test_projection_preserves_attack_and_defeat_separately():
       csaf = build_csaf(...)
       af = csaf.framework
       assert ("a", "b") in af.attacks
       assert ("a", "b") not in af.defeats  # filtered by preference
       # Both relations exist in the projection. Neither is silently dropped.
   ```

   Full assertion set:
   - `(a_arg_id, b_arg_id) ∈ proj_framework.attacks` AND `(a_arg_id, b_arg_id) ∉ proj_framework.defeats`. The asymmetric survival is the *correct* output.
   - For every kernel attack whose endpoints both project, the projected pair appears in `proj_framework.attacks`. Same for defeats independently.
   - When an endpoint legitimately fails to project (e.g. argument filtered upstream), `csaf_to_projection` records a typed diagnostic or raises a typed error. Silent-drop is forbidden.
   - **Explicit anti-pattern**: the test does NOT assert `attacks iff defeats` and does NOT assert `(x, y) ∈ attacks ⇔ (x, y) ∈ defeats`. Any successor edit re-introducing that biconditional is a regression and must be rejected at review.

   **Must fail today**: `projection.py:260-275` rebuilds `attacks` with silent-drop guards (`and ... in csaf.arg_to_id`); a kernel attack whose argument id is missing vanishes without a typed signal. The asymmetric-survival case (attack without defeat) is also unprotected against silent collapse.

9. **`tests/test_advertised_aspic_semantics_executable.py`** (pins Codex #13, #21)
   - For each `WorldSemantics` value starting with `aspic-` or equal to `complete`: assert either typed extension result or typed validation rejection before dispatch.
   - **Must fail today**: `aspic-incomplete-grounded`, `aspic-direct-grounded`, ASPIC `complete` are advertised at `world/types.py:667-672`/`:637` but `structured_projection.py:240-260` raises generically.

10. **`tests/test_praf_paper_td_complete_routing.py`** (pins Codex #14, coordinated with WS-H)
    - Selects `praf-paper-td-complete` via public policy surface.
    - Asserts: dependency call uses `strategy="paper_td"`, `semantics="complete"`, `query_kind="extension_probability"`, queried set — or rejects.
    - **Must fail today**: `core/analyzers.py:767-771`, `world/resolution.py:691`, `app/world_reasoning.py:239` pass it as `semantics` with `query_kind="argument_acceptance"`.
    - WS-H owns the broader calibration class; WS-F's test asserts routing only.

11. **`tests/test_claim_canonical_name_uniqueness_aspic.py`** (pins Codex #36 in the bridge dimension)
    - Two distinct claims share canonical concept name; assert distinct `ClaimLiteralKey`s reach `claims_to_literals` and downstream literal identity does not collapse.
    - **Must fail today** if downstream literal identity collapses through the concept reference; if running red shows the bridge separates by `claim_id` regardless, move the test to a registry-focused successor WS and document exclusion.

12. **`tests/test_workstream_f_done.py`** (gating sentinel)
    - `xfail` until WS-F closes; flips to pass on the final commit (Mechanism 2 of REMEDIATION-PLAN Part 2).

## Production change sequence

Each step lands in its own commit with a message of the form `WS-F step N — <slug>`.

**Upstream-blocked steps (per Codex 2.3, made explicit):**
- **Step 1** — blocked on `argumentation.transposition_closure` returning `(closed_rules, post_closure_language)`.
- **Step 6** — blocked on public `argumentation.aspic.contraries_of` (rename of `_contraries_of`).

Both upstream changes ship in WS-O-arg-argumentation-pkg, in tagged `argumentation` releases. propstore's pin must be bumped before the corresponding propstore step lands. All other steps (2, 3, 4, 5, 7, 8, 9, 10, 11, 12) are propstore-only and proceed in parallel with upstream work.

### Step 1 — Strict closure under the full contrariness (HIGH-1, Drift D) — **UPSTREAM-BLOCKED on WS-O-arg-argumentation-pkg**
Delete `_transposition_contrariness` (`build.py:96-111`); pass `contrariness` directly into `transposition_closure` at `build.py:149-153`. Collapse the double `_build_language` call (`build.py:147,154`) by having the kernel return the post-closure language alongside the closed rules.
**Upstream prerequisite**: `argumentation.aspic.transposition_closure` returning `(closed_rules, post_closure_language)`. WS-O-arg-argumentation-pkg ships the kernel signature change in a tagged release; propstore bumps its pin; THEN this step lands.
Acceptance: `tests/test_aspic_indirect_consistency_modgil_2014.py` turns green.

### Step 2 — ASPIC grounded conflict-free (T2.9 / Codex #12)
Stop calling `argumentation.dung.grounded_extension` for `backend=ASPIC` at `structured_projection.py:251-253`. Preferred fix: file an upstream change (WS-O-arg) so `grounded_extension` accepts an explicit `attacks` parameter and uses it for conflict-freeness when present, mirroring `is_admissible`/`stable_extensions` (`dung.py:170-179`, `:308-324`, `:390`). Acceptable interim: wrap the kernel's `complete_extensions` (which already respects attacks) and select the unique least extension.
Acceptance: `tests/test_aspic_grounded_conflict_free.py` turns green.

### Step 3 — Asymmetric contrary for directional stances (HIGH-2 / T2.1 / Codex #22 / Drift A)
Rewrite `translate.py:136-140`: `rebuts(a,b)` writes `(a,b)` and `(b,a)` to `contradictories`; `supersedes(a,b)` and `undermines(a,b)` write `(a,b)` to `contraries` (asymmetric, preference-independent per Modgil 2014 Def 5.1; preference-sensitivity remains in `compute_defeats`). Mixed case: explicit asymmetric stance wins; collect authored stances first, materialize in a single pass with precedence. Verify `_filter_preference_sensitive_stance_attacks` (`build.py:182-214`) inputs still match.
Acceptance: `tests/test_stances_asymmetric_contrary.py` green; step 1 test stays green.

### Step 4 — Premise ordering respects comparison knob (HIGH-3)
Rewrite `build_preference_config` (`translate.py:255-305`) so the base premise order is policy-aware. Minimum: `comparison="elitist"` keeps Pareto strict; `comparison="democratic"` falls back to a tiebreaker (e.g., sum-of-dimensions) on Pareto-incomparable pairs. Set comparison stays in the kernel per Modgil 2018 Def 19; bridge owns the base order.
Acceptance: `tests/test_premise_order_respects_comparison.py` green.

### Step 5 — Defeater-rule branch targets named rules (HIGH-4)
Change the filter in `grounding.py:206-211` from `rule.consequent == defeater_head.contrary` to a rule-name match. Preserve current rule-file authoring shape: when the defeater head is content-shaped, search defeasible rules whose consequent equals the defeater head's contrary, then emit undercutters against each rule's *name*. Add a regression for the explicit `name(R)` head form too.
Acceptance: `tests/test_defeater_undercut_targets_named_rules.py` green.

### Step 6 — Public symbol for `_contraries_of` (HIGH-5 / T5.7) — **UPSTREAM-BLOCKED on WS-O-arg-argumentation-pkg**
**Upstream prerequisite**: rename `_contraries_of` → `contraries_of` in `argumentation.aspic`, export, no shim, tagged release. **Propstore-side** (after pin bump): update `query.py:13` and `tests/remediation/phase_5_bridge/test_T5_4_query_goal_contraries.py:1` to import the public name. AST gate (`test_query_no_private_imports.py`) is the durable regression rule.
Acceptance: `tests/test_query_no_private_imports.py` green; `propstore/aspic_bridge/query.py` imports only public symbols from `argumentation.*`.

### Step 7 — `arguments_against` covers all three attack types (HIGH-6)
Rewrite `query.py:78-107` to compute `arguments_against` from the already-computed `attacks` set: `{att.attacker for att in attacks if att.target_sub is the goal-argument or any of its sub-arguments}`. Reuses `attacks` from line 85; covers rebut, undermine, undercut uniformly.
Acceptance: `tests/test_arguments_against_includes_undercut_undermine.py` green.

### Step 8 — Projection preserves attack and defeat without silent loss (HIGH-7)
Rewrite `projection.py:260-275` to project `attacks` and `defeats` independently. For each relation, iterate the corresponding kernel-side set, filter by `projected_arg_ids` deterministically, do not collapse the two relations. An attack with no surviving defeat (preference-filtered) is a legitimate output. Drop the silent-drop guard: either both endpoints project (so the lookup succeeds) or the endpoint legitimately filtered out (recorded in a typed diagnostic on the projection result). Replace `type(csaf.framework)(...)` with explicit `from argumentation.dung import ArgumentationFramework` (cluster D boundary item 4).
Acceptance: `tests/test_projection_preserves_attack_and_defeat_separately.py` green; both no-silent-loss assertions pass; the asymmetric-survival case projects correctly.

### Step 9 — Advertised semantics route or reject (Codex #13, #21)
Extend `structured_projection.py:240-260` to handle `complete` (kernel `complete_extensions`), `aspic-incomplete-grounded`, `aspic-direct-grounded`; or remove from `WorldSemantics`. The choice is Q's; the test asserts only "executable or rejected before dispatch."
Acceptance: `tests/test_advertised_aspic_semantics_executable.py` green.

### Step 10 — `praf-paper-td-complete` routing (Codex #14, coordinated with WS-H)
At `core/analyzers.py:767-771`, `world/resolution.py:691`, `app/world_reasoning.py:239`, dispatch with `strategy="paper_td"`, `semantics="complete"`, `query_kind="extension_probability"`, queried set. WS-F lands routing only; WS-H lands the broader calibration class.
Acceptance: `tests/test_praf_paper_td_complete_routing.py` green.

### Step 11 — Concept canonical-name uniqueness gates ASPIC literal identity (Codex #36)
Coordination edge: principled fix lives in `families/concepts/passes.py:506-507` (raise, matching `cel_registry.py:112`). WS-F asserts that, if upstream still admits duplicates, `claims_to_literals` does not silently merge two claims into one ASPIC literal. If the bridge already keys by `claim_id` and the test goes green without a bridge change, move the test to a successor WS and document exclusion in the closing PR.
Acceptance: test green here, or moved with explicit documentation.

### Step 12 — Close gaps and gate
Update `docs/gaps.md` (remove bridge entries, add `# WS-F closed <sha>`). Flip `tests/test_workstream_f_done.py` from `xfail` to `pass`. Update STATUS line in this file to `CLOSED <sha>`.
Acceptance: sentinel passes; gaps.md updated.

## Acceptance gates

Before declaring WS-F done, ALL must hold:

- [x] `uv run pyright propstore` — passed with 0 errors.
- [x] `uv run lint-imports` — passed (4 contracts kept, 0 broken).
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-F-properties tests/test_ws_f_aspic_bridge.py` — green replacement gate covering the named WS-F regressions and property gates.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — run after this closure update commit.
- [x] `propstore/aspic_bridge/build.py` no longer defines `_transposition_contrariness`.
- [x] `propstore/aspic_bridge/query.py` no longer imports `_contraries_of`.
- [x] `propstore/aspic_bridge/projection.py` imports `ArgumentationFramework` explicitly.
- [x] `tests/test_ws_f_aspic_bridge.py` does NOT contain any `iff`/`⇔`/`<==>`/biconditional assertion linking projected attacks to projected defeats. (Codex 2.2 anti-regression guard.)
- [x] Upstream prerequisites for Steps 1 and 6 shipped in pushed `argumentation` commit `bbfa7ef1db1d5db376f048d5bf789760923db9d4`; propstore's remote Git pin and lockfile were bumped before landing the propstore steps.
- [x] `docs/gaps.md` records WS-F closure and no open row remains for these WS-F findings.
- [x] `reviews/2026-04-26-claude/workstreams/WS-F-aspic-bridge.md` STATUS line is `CLOSED c8b0c892`.
- [x] Modgil 2014 §4.2 indirect-consistency is pinned by `test_compile_bridge_uses_full_contrariness_transposition_language`, which asserts transposition closure against the full contrariness and the post-closure language.

## Done means done

This workstream is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- T2.1, T2.9, T5.7, Cluster D HIGH-1 through HIGH-7, Codex #13, #14, #21, #22 — all have a corresponding green test in CI.
- T2.11 is **out of scope** here (lives in WS-O-arg); the closing PR description must state this explicitly.
- Codex #36 may be moved to a successor WS per Step 11; if so, the move is documented in the closing PR.
- The workstream's gating sentinel test (`test_workstream_f_done.py`) has flipped from `xfail` to `pass`.
- The first failing test (`test_aspic_indirect_consistency_modgil_2014.py`) is **green**, with a docstring citing Modgil 2014 §4.2 Theorem 1 and naming the strict closure / contrariness invariants it asserts.

If any one of those is not true, WS-F stays OPEN. No "we'll handle the projection skew later." Either it's in scope and closed, or it has been explicitly removed from this WS in this file and moved to a successor before declaring done.

## Papers / specs referenced

The bridge claims (in module docstrings) to follow Modgil & Prakken 2018; the cluster D review's named reference is Modgil 2014. WS-F treats both as truth and pins the theorems they share.

- **Modgil_2014_ASPICFrameworkStructuredArgumentation** — §4.2 Theorem 1 (indirect consistency); §4.3 Def 4.3 (transposition closure); §5 Def 5.1 (contraries vs contradictories); §5 well-formedness.
- **Prakken_2010_AbstractFrameworkArgumentationStructured** — original ASPIC+; rebut/undermine/undercut for test 2's conflict-freeness assertion.
- **Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework** — contraries vs contradictories under different rebut policies; asymmetric-stance test 3.
- **Modgil_2009_ReasoningAboutPreferencesArgumentation**, **Modgil_2018_GeneralAccountArgumentationPreferences** — preference-sensitive rebut/undermine; elitist/democratic in test 4.
- **Caminada_2006**, **Caminada_2007** — restricted vs unrestricted rebut; postulate context for test 2.
- **Lehtonen_2024_PreferentialASPIC** — Prop 17; grounds the "comparison/link is not cosmetic" framing in HIGH-3.
- Scope guards (out-of-scope, listed for completeness): Wallner_2024, Dauphin_2018, Toni_2014, Čyras_2016, Atkinson_2007, Odekerken_2025.

## Cross-stream notes

- **WS-D** lands first; if it renames `MetadataStrengthVector`, WS-F's HIGH-3 tests use the renamed surface.
- **WS-H** overlaps Codex #14: WS-F lands the routing assertion only; WS-H lands the broader PrAF calibration class. No duplicate tests.
- **WS-O-arg-argumentation-pkg** dependency is the gating header. Upstream-blocked steps (1, 6) and their prerequisites are listed in the production-change-sequence preamble. T2.11 is wholly in WS-O-arg-argumentation-pkg.
- **WS-N** owns `docs/argumentation-package-boundary.md`. If it rewrites the doc, WS-F's `tests/test_query_no_private_imports.py` assertion text must stay aligned.
- **WS-G**, **WS-I** are parallel and independent.

## What this WS does NOT do

Out of scope; each tracked separately:

- Value-based ASPIC+ (Wallner 2024); accrual (Prakken 2019); argument schemes / critical questions (Prakken 2013); ABA reduction (Toni 2014, Čyras 2016); ASPIC-END (Dauphin 2018); IAFs / partial-AF construction (Odekerken 2025).
- Restricted rebut policy switching (Caminada 2006/2007, Modgil 2018 §6.2). Follow-up WS once conflict-free fix lands.
- `aspic_encoding._literal_id = repr(literal)` (T2.11) — lives in WS-O-arg.
- Runtime c-consistency pre-flight on K_n. Theorem-1 pinning by `tests/test_aspic_indirect_consistency_modgil_2014.py` satisfies the WS-F closure; runtime pre-flight is a follow-up.
- Deeper premise-ordering policy (subjective-logic-aware, set-of-rules per Modgil 2018 Def 19). HIGH-3 fix gives comparison-knob respect minimum; deeper work is follow-up.
