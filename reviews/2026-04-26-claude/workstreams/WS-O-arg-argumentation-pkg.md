# WS-O-arg: argumentation package HIGH bugs (../argumentation) — kernel correctness

**Status**: CLOSED a2f41029
**Depends on**: nothing internal. Parallel-safe with WS-A and other WS-O-* dependency fixes.
**Blocks**:
- **WS-O-arg-aba-adf** — ABA / ABA+ and ADF kernels both extend Dung-shaped extension/labelling apparatus and reuse the encoder. The collision-free defeasible-rule id scheme (Bug 3), the ASP-valid literal sanitisation (Bug 2), and the corrected ideal-extension construction (Bug 1) must be settled before sub-stream work begins; otherwise ABA's flat-attack reduction inherits broken ids and ADF's acceptance-condition encoding inherits broken literals.
- **WS-O-arg-dung-extensions** — eager, stage2, prudent, semi-stable, bipolar grounded/complete, and Caminada labelling-as-semantics all build directly on `dung.py`'s extension and admissibility primitives. The ideal-extension fix and any change to admissibility/defense reasoning must be in place first.
- **WS-O-arg-vaf-ranking** — VAF (Bench-Capon 2003) and the Bonzon ranking-semantics family extend the same AF substrate; ranking convergence proofs assume admissibility behaves correctly.
- **WS-O-arg-gradual** — DF-QuAD and Matt-Toni game-theoretic argument strength consume the same AF data shapes and (in DF-QuAD's case) the encoder. The encoder fixes must land first.
- **WS-F (propstore-side ASPIC bridge)** — needs encoder identifier scheme and rule-uniqueness invariants honest before bridge fidelity tests can mean anything.
- **WS-G (belief revision / AGM-AF)** — per **D-12** consumes argumentation's public API only. Bugs 4 and 5 (`af_revision.py`) must close before WS-G's revision tests can be trusted.

**Why this comes first**: this is the kernel that all sub-streams extend. If the kernel returns wrong answers on legitimate input, every extension built on it inherits the wrong answers and every "feature" PR ships compounding incorrectness. Fix the kernel; then extend it.

**Owner**: Codex implementation owner + human reviewer required (per **2.1**).

**Repo**: workstream lives in `C:\Users\Q\code\argumentation\`. The workstream file lives in `C:\Users\Q\code\propstore\reviews\2026-04-26-claude\workstreams\` because that is where the review producing it lives, but every test path, every code reference, and every PR mentioned below is in the *argumentation* repository at `C:\Users\Q\code\argumentation\src\argumentation\` and `C:\Users\Q\code\argumentation\tests\`. Propstore-side sentinels per finding are explicitly separated below (per **2.18**).

**Scope**: per **D-16**, this WS is narrowed to the HIGH-severity bugs only — the kernel-correctness fixes that every sub-stream extends. Coverage-gap work has been split into the four sibling sub-streams listed above. The smell about `register_backend` is removed from this WS — it is an API addition, not a correctness bug, and is tracked as a separate followup in argumentation's `gaps.md`.

**Upstream policy (D-15)**: each cluster-P HIGH bug becomes a PR in `../argumentation` with its own first-failing test in `argumentation/tests/`. propstore's pin bumps when the dep ships each fix. propstore-side test corpus re-runs against the new pin. **No wraps. No fork. No propstore-side reimplementation.** AGM-AF revision (per **D-12**) stays in argumentation; propstore consumes via public API only.

---

## Why this is a workstream

`argumentation` is a propstore dependency pinned at a specific GitHub commit. Cluster P read every module under `src/argumentation/` and produced 8 HIGH-severity defects that yield wrong output, intractable runs, or contract drift on legitimate inputs. All eight are upstream bugs — propstore consumes the affected APIs through `argumentation`'s public surface and inherits the wrong answers. They cannot be patched correctly from propstore; the fix has to land in argumentation.

Categories: wrong result on legitimate input (Bugs 1, 2, 3); classification / boundary (Bugs 4, 5); contract drift (Bugs 6, 7, 8). All eight are in scope; none are deferred. The coverage gaps and the `register_backend` smell are tracked elsewhere (see Cross-stream below).

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from the argumentation repo's `gaps.md` (or a new one will be created), has a green test in `tests/`, and has been reflected back to propstore via a pin bump and a propstore-side sentinel.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T2.10 / Bug 1** | Claude REMEDIATION-PLAN; cluster P HIGH | `dung.py:582-585` | `ideal_extension` returns union of admissibility-maximal candidates. Admissibility is not closed under union (Dung-Mancarella-Toni 2007 Def 2.2 / Thm 2.1). The companion proposal that "intersection is always admissible because subsets of admissible sets preserve defense" is also wrong; defense is not downward-closed (see Codex 2.16 below). |
| **T2.11 / Bug 2** | Claude REMEDIATION-PLAN; cluster P HIGH | `aspic_encoding.py:165` | `_literal_id = repr(literal)` produces non-loadable ASP — `~p`, `p(1, 2)`, etc. are not valid clingo identifiers in fact arguments. |
| **Bug 3** | cluster-P #3 | `aspic_encoding.py:179` | `_defeasible_rule_ids` keys by `rule.name or f"d_{index}"`; two rules with the same `name` get the same id. **Subtle**: dict-by-`Rule`-instance preserves both keys, so the collision does not surface at insert — it surfaces downstream when `d_head(<id>, <conc>)` is emitted and the consumer cannot distinguish two rules' conclusions. |
| **Bug 4** | cluster-P #4 | `af_revision.py:301-325` | `_classify_extension_change` uses cardinality-only branching. Cayrol-de-Saint-Cyr-Lagasquie-Schiex 2010 Table 3 requires subset-content reasoning; `(len(before)==2, len(after)==1)` falls through to `ALTERING` regardless of subset structure; `EXPANSIVE` requires equal cardinality which is not in the paper. |
| **Bug 5** | cluster-P #5 | `af_revision.py:60-92`, `:110-117` | `ExtensionRevisionState.__post_init__` calls `all_extensions(arguments)` — a 2^n-subset enumerator. Memory and construction time blow up beyond ~15 arguments. |
| **Bug 6** | cluster-P #6 | `preference.py:58` vs `aspic.py:1132` | `preference.strictly_weaker(non-empty, [])` returns False; `aspic._set_strictly_less(non-empty, frozenset())` returns True. Same Modgil-Prakken Def 19 lifting, opposite verdicts on the (non-empty, empty) boundary. |
| **Bug 7** | cluster-P #8 | `semantics.py:149` | Partial-AF skeptical mode uses plain intersection across `extensions(...)` (the union across completions). That is *necessary skeptical* (Baumeister/Coste-Marquis 2013); *possible skeptical* is not exposed. The dispatcher silently returns one variant under the unqualified name. |
| **Bug 8** | cluster-P #9 | `probabilistic.py:42-46` | `_z_for_confidence` accepts only exact dict keys `0.90`, `0.95`, `0.99`. Any non-literal float raises `ValueError`. Dependency-free package; correct fix is Beasley-Springer-Moro or Acklam inverse-CDF. |

## Code references (verified by direct read at HEAD on 2026-04-26)

All file:line citations below are confirmed by reading source in `C:\Users\Q\code\argumentation\src\argumentation\` directly.

### Bug 1 — `dung.py:582-585` (ideal extension union fallback)

The function builds `candidates` as admissible subsets of the intersection of preferred extensions (`dung.py:563-573`), takes set-maximal (`:574-577`), and on multiplicity returns the union (`:582-585`). Dung-Mancarella-Toni 2007 Def 2.2 / Thm 2.1: the **ideal extension** is the *largest admissible set contained in every preferred extension* — equivalently, the unique maximal element of the intersection of preferred extensions, restricted to admissible sets. The current code does not verify the union is admissible before returning. Output may violate spec.

### Bug 2 — `aspic_encoding.py:165` (`_literal_id = repr(literal)`)

`Literal.__repr__` (`aspic.py:78-81`) returns `~p` for negated literals, `p(1, 2)` for parameterised atoms. Encoder writes `axiom(~p).`, `s_body(s_0, p(1, 2)).` — neither parses in clingo. Module docstring claims Lehtonen-Niskanen-Järvisalo 2024 ASP; emitted strings are not valid ASP. Fix: sanitising scheme (`n_p` for `~p`, `p_1_2` for `p(1, 2)`) plus reverse map.

### Bug 3 — `aspic_encoding.py:176-180` (rule-name silent collision, surfaces at d_head emission)

`named[rule] = rule.name or f"d_{index}"`. Two distinct `Rule` instances with the same `.name` get the same id string. The dict is keyed by `Rule` instance (not by name), so both entries persist — the bug does not show up at insert. It surfaces later: when the encoder emits `d_head(<id>, <conc>)` facts, two rules with the same `id` produce two facts with identical first arguments and different conclusions. The consumer downstream (clingo, or any post-processor reading the encoding) cannot recover which rule each fact belongs to. `Rule` (`aspic.py:137-162`) does not enforce name uniqueness across `R_d`. Fix: detect the collision **at encode time** and raise `ValueError` with the offending name and rules listed. Detection has to walk the rule list and check `name -> [Rule]` cardinalities; a per-instance dict will not catch it.

### Bug 4 — `af_revision.py:301-325` (cardinality-only classification)

Cayrol et al. 2010 Table 3 distinguishes seven kinds (CONSERVATIVE, DESTRUCTIVE, DECISIVE, RESTRICTIVE, QUESTIONING, EXPANSIVE, ALTERING) by *subset relations* between extension families — not cardinality alone. Two specific failures:

- `(len(before)==2, len(after)==1)`: skipped by DECISIVE (requires `len(before) > 2`), skipped by RESTRICTIVE (requires `len(after) >= 2`), falls through to ALTERING. Table 3 classifies this as DECISIVE if the surviving extension equals one of the originals, RESTRICTIVE if it is a strict subset. The code never inspects extension content.
- EXPANSIVE: requires `len(after) == len(before)`. The paper's expansive case is "every old extension is properly contained in some new extension"; cardinality equality is neither necessary nor sufficient.

Fix: encode each Table 3 row as an explicit subset-content predicate.

### Bug 5 — `af_revision.py:65-92`, materialization at `:110-117`

`all_extensions` is the full powerset (`combinations(ordered, size) for size in range(len(ordered)+1)`). For 20 arguments, ~1M entries; for 30, ~1B. `__post_init__` runs it unconditionally. Diller 2015 revision is conceptually defined over the full extension lattice (paper-faithful), but eager materialisation makes the class unusable beyond ~15 arguments. Fix: lazy ranking via `Callable[[frozenset[str]], int]` plus a sparse override dict for explicit cases.

### Bug 6 — `preference.py:58` vs `aspic.py:1132`

Both functions claim to implement Modgil-Prakken 2018 Def 19 set lifting. They disagree on `(non-empty, empty)`:

- `preference.strictly_weaker(non-empty, [])` → False (`preference.py:58`: `if not set_a or not set_b: return False`).
- `aspic._set_strictly_less(non-empty, frozenset())` → True (`aspic.py:1132-1135`: `if not gamma: return False; if not gamma_prime: return True`).

Def 19 (p.21) states "non-empty Γ is strictly less than empty Γ′" — `aspic.py` is correct, `preference.py` is wrong. ASPIC+ defeat reasoning routes through `_strictly_weaker` in `aspic.py`, so internals are fine; third-party callers of `preference.strictly_weaker` get the wrong ordering.

### Bug 7 — `semantics.py:149` (partial-AF skeptical mode)

For `PartialArgumentationFramework`, `extensions(...)` returns the *union* of extensions across all completions (`semantics.py:106-111`). Plain intersection across this union (`semantics.py:149-152`) gives "accepted in every extension of every completion" — Baumeister/Coste-Marquis 2013 *necessary skeptical*. *Possible skeptical* — "accepted in every extension of some completion" — requires per-completion intersection then union. The dispatcher exposes only the former under the unqualified name. Fix: split into `necessary_skeptical` / `possible_skeptical`; reject bare `skeptical` for partial AFs.

### Bug 8 — `probabilistic.py:42-46` (z-score lookup)

`_Z_SCORES = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}`; any user supplying `0.9501`, `0.999`, or any non-literal float raises `ValueError`. Package commits to no scipy. Fix: Beasley-Springer-Moro 1977 inverse-normal-CDF (public domain, ~30 lines, accurate to 1e-9 on `(0, 1)`). Keep the dict as a fast path for the three common values.

## Ideal extension — corrected construction (per Codex 2.16)

The earlier proposal text in this WS suggested that "the intersection of admissibility-maximal candidates is always admissible because subsets of admissible sets preserve defense." That argument is wrong. Defense is **not downward-closed** under subset: a defender removed from an admissible set can leave one of its members undefended by what remains. A subset of an admissible set is conflict-free (conflict-freeness *is* downward-closed) but is not necessarily admissible.

The correct construction comes from Dung-Mancarella-Toni 2007 (paper cluster P, "Computing ideal sceptical argumentation"). The ideal extension is defined as the **largest admissible set contained in every preferred extension**, i.e. the unique maximal element of the lattice of admissible subsets of `∩ preferred(F)`. Computing it is **not** a one-shot intersection, **not** a greedy single-argument walk, and **not** a union of admissibility-maximal candidates. It is a maximality computation over the entire admissibility lattice restricted to `I = ∩ preferred(F)`.

### Why a single-argument greedy is insufficient

A greedy "while there exists `a ∈ I \ E` such that `E ∪ {a}` is admissible, add `a`" loop **stops too early**. A larger admissible subset of `I` may require adding two or more arguments **together** because they defend each other only as a set: `{a}` alone may be inadmissible (no defender in `E ∪ {a}`), `{b}` alone may be inadmissible for the same reason, but `{a, b}` together IS admissible (`a` defends `b`, `b` defends `a`). The greedy loop sees neither `a` nor `b` as individually addable from `E = ∅`, declares "no progress possible," and returns the wrong answer (`∅` instead of `{a, b}`).

The counterexample fixture pinned in `tests/test_admissibility_requires_pair.py` (see below) makes this concrete and is the regression gate.

### Faithful implementation — required approach

Use admissible-subset enumeration with set-inclusion maximality. This is the required construction for this workstream because it is direct to prove against Dung-Mancarella-Toni 2007 §3 and Theorem 1 and because the earlier restricted-characteristic-function wording computed a least fixpoint from `∅`, which fails the mutual-defense counterexample below.

1. Compute `I := ∩ preferred(F)` — conflict-free, generally not admissible.
2. Enumerate every subset `S ⊆ I` (or every conflict-free subset of `I` for a constant-factor speedup; admissibility implies conflict-freeness).
3. Filter: keep only `S` that are **admissible in `F`** (each `s ∈ S` is defended by `S` against every `F`-attacker of `s`).
4. Pick the **set-inclusion-maximal** element of the resulting collection. By Dung-Mancarella-Toni 2007 Theorem 1 this maximum is **unique**; if more than one set-inclusion-maximal candidate is present, the implementation has a bug — assert and fail loudly rather than collapse via union.
5. Return that unique maximum.

This approach is exponential in `|I|` but `|I|` is typically small (it is the carrier — the intersection of preferred extensions — not the full argument set). Pin a complexity comment in the docstring.

### What the implementation MUST NOT do

- MUST NOT collapse to "return `I`" (intersection is conflict-free but generally not admissible — the original Bug 1 and its sibling counterexample).
- MUST NOT collapse to "return the union of admissibility-maximal candidates" (current code's union fallback; admissibility is not closed under union).
- MUST NOT use single-argument greedy addition (stops at `∅` on the mutual-defense counterexample below; see `tests/test_admissibility_requires_pair.py`).
- MUST NOT collapse multiple set-inclusion-maximal candidates (Approach 1) via union or intersection — the maximum is unique by Theorem 1; multiple maxima indicate an admissibility-check bug, fail loudly.

## First failing tests (in `C:\Users\Q\code\argumentation\tests\`; write these first)

Per **D-15**, every test below lives in the **argumentation** repo, not propstore. Each test references the cluster-P finding number in its docstring. The test path layout follows the repo convention (`test_<module>.py`).

1. **`tests/test_dung_ideal_admissibility.py`** (new — Bug 1, T2.10)
   - Hypothesis-generated AF where the intersection of preferred extensions is non-trivial; assert that `ideal_extension(framework)` is itself admissible (i.e., conflict-free *and* defends each of its members against every attacker).
   - Specific hand-crafted regression: an AF with two preferred extensions sharing a common subset that admits two set-maximal admissible candidates whose union is conflict-free but not self-defending. Output of current code returns the union; assertion `admissible(result, ...)` fails.
   - **Must fail today** at the union-fallback branch.

2. **`tests/test_admissibility_not_downward_closed.py`** (new — counterexample for Codex 2.16)
   - Pin a small AF where two admissible sets `A1`, `A2` exist whose intersection is **not** admissible. Construction sketch: arguments `a, b, c, d, e`; attacks `e→a`, `b→e`, `c→a`, `d→c`. Both `{a, b}` and `{a, d}` are admissible (each contains the unique defender of `a` against one of its attackers). Intersection `{a, b} ∩ {a, d} = {a}`. `{a}` is not admissible: `e` attacks `a`, no defender remains in `{a}`.
   - Build the AF, compute admissibility of `{a, b}`, `{a, d}`, and `{a}` directly; assert the first two are admissible and `{a}` is not.
   - Then call `ideal_extension(framework)` and assert the result is **not** equal to the intersection of any pair of admissible sets you happened to find — instead it is whatever the lattice-fixed-point construction returns. The exact expected value is computed from the paper construction and pinned in the test.
   - This test serves two roles: (a) it documents that defense is not downward-closed, (b) it asserts the ideal-extension implementation does **not** compute a naive intersection.
   - **Must fail today**: the current union-fallback path returns the wrong answer; once Bug 1 is fixed via the corrected construction, the test pins the right answer for this AF.

2b. **`tests/test_admissibility_requires_pair.py`** (new — counterexample to single-argument greedy; Codex re-review #8)
   - Pin a small AF where the carrier `I = ∩ preferred(F)` equals `{a, b, c}` and where:
     - `{a}` alone is **not** admissible (some attacker of `a` is not attacked back by `{a}` itself).
     - `{b}` alone is **not** admissible (some attacker of `b` is not attacked back by `{b}` itself).
     - `{a, b}` together **IS** admissible (`a` attacks `b`'s outstanding attacker; `b` attacks `a`'s outstanding attacker — mutual defense).
   - Construction sketch: arguments `a, b, c, x, y`; attacks `x → a`, `b → x`, `y → b`, `a → y`, plus enough additional attacks to make `c` survive in every preferred extension so `I = {a, b, c}`. The exact AF is constructed in the test docstring with attacks listed line by line and a hand-traced calculation of `preferred(F)` showing that `{a, b, c}` is in the carrier. (The coder may adjust the specific construction to match what `preferred_extensions` on the fixed `dung.py` actually returns, but the property — `{a}` and `{b}` individually inadmissible, `{a, b}` together admissible — is the load-bearing structure.)
   - Compute `is_admissible(framework, {a})` and `is_admissible(framework, {b})` directly via the public API; assert both are False.
   - Compute `is_admissible(framework, {a, b})` directly; assert True.
   - Call `ideal_extension(framework)` and assert the result equals `{a, b}` (or `{a, b, c}` if `c` is independently admissible from `∅` in this construction; the test's load-bearing assertion is `result != frozenset()` and `{a, b} ⊆ result`).
   - This test is the **regression gate against single-argument greedy**: a greedy loop returns `∅` because neither `a` nor `b` can be added first when starting from `E = ∅`. The required enumeration construction returns the correct non-empty answer.
   - **Must fail today** under the current union-fallback path AND under any naive single-argument greedy implementation. Passes only under the required admissible-subset enumeration from "Ideal extension — corrected construction" above.
   - Cite Dung-Mancarella-Toni 2007 §3 / Theorem 1 verbatim in the test docstring.

3. **`tests/test_aspic_encoding_asp_validity.py`** (new — Bug 2, T2.11)
   - Encode an ASPIC theory containing a negated literal `~p` and a parameterised atom `p(1, 2)`.
   - For every emitted fact line, assert it round-trips through `clingo.Control.add(...)` (skip the test with a clear reason if clingo is not installed; do not fake it).
   - Alternative dependency-free check: compile a regex matching `[a-z][a-zA-Z0-9_]*(\([a-zA-Z0-9_,]*\))?` and assert every literal id matches it.
   - **Must fail today**: `~p` and `p(1, 2)` both fail the regex; `clingo.Control.add` raises a parse error.

4. **`tests/test_aspic_encoding_rule_collision.py`** (new — Bug 3)
   - Build a `KnowledgeBase` with two distinct defeasible rules sharing the same `name="d1"` and *different conclusions*.
   - Assert one of the following: (a) `encode_aspic_theory(...)` raises `ValueError("duplicate defeasible rule name: d1")`, or (b) the emitted `d_head(...)` facts contain distinct ids per rule (so consumers can disambiguate).
   - Crucially: this test must inspect the **emitted ASP facts**, not just the internal `_defeasible_rule_ids` dict. The bug surfaces at `d_head(<id>, <conc>)` emission — testing only the dict misses the collision.
   - **Must fail today**: encoder runs to completion; emitted `d_head` facts share an id across the two rules.

5. **`tests/test_af_revision_classification_table.py`** (new — Bug 4)
   - Hand-encode every row of Cayrol-de-Saint-Cyr-Lagasquie-Schiex 2010 Table 3 as a `(before, after, expected_kind)` triple. The paper has seven kinds; instantiate at least two `(before, after)` instances per kind from the paper's worked examples.
   - Parametrize over the table; assert `_classify_extension_change(before, after) == expected_kind`.
   - **Must fail today**: the `(len(before)==2, len(after)==1)` cases land on ALTERING regardless of subset content.

6. **`tests/test_af_revision_state_lazy.py`** (new — Bug 5)
   - Construct an `ExtensionRevisionState` with 20 arguments (a powerset of `2^20 ≈ 1M` entries) and a sparse explicit ranking dict (~10 entries). Assert construction completes in <100ms and uses <10MB resident.
   - **Must fail today**: `__post_init__` builds the full powerset eagerly; either the test takes seconds or the process exhausts memory.

7. **`tests/test_preference_aspic_parity.py`** (new — Bug 6)
   - Hypothesis-generate `(set_a, set_b, comparison, base_order)` quadruples.
   - Assert `preference.strictly_weaker(set_a, set_b, comparison)` and `aspic._set_strictly_less(frozenset(set_a), frozenset(set_b), frozenset(base_order_pairs), comparison)` agree on every input.
   - Hand-crafted boundary case: `set_a = [0.5]`, `set_b = []`, `comparison = "elitist"`. Modgil-Prakken Def 19 says True. `aspic` says True. `preference` says False.
   - **Must fail today**: parity fails on the boundary case; Hypothesis will find it within seconds.

8. **`tests/test_semantics_partial_skeptical_split.py`** (new — Bug 7)
   - Build a `PartialArgumentationFramework` with two completions; one has extensions `[{a}, {b}]`, the other `[{a, c}]`.
   - Assert `accepted_arguments(framework, semantics="grounded", mode="necessary_skeptical")` returns `frozenset()` (no argument is in every extension of every completion).
   - Assert `accepted_arguments(framework, semantics="grounded", mode="possible_skeptical")` returns `frozenset({"a", "c"})` (the second completion's only extension has both).
   - Assert `mode="skeptical"` raises `ValueError("ambiguous; use 'necessary_skeptical' or 'possible_skeptical' for partial AFs")`.
   - **Must fail today**: only `mode="skeptical"` exists; it returns the necessary-skeptical answer silently.

9. **`tests/test_probabilistic_z_inverse_cdf.py`** (new — Bug 8)
   - Parametrize over `confidence ∈ {0.90, 0.95, 0.99, 0.9501, 0.999, 0.50, 0.999999}`.
   - Assert `_z_for_confidence(c)` returns the inverse-CDF value to within 1e-6 of `scipy.stats.norm.ppf(1 - (1-c)/2)` (skip if scipy unavailable; bake the expected values into the test as constants).
   - **Must fail today** for any confidence not in the dict.

10. **`tests/test_workstream_o_arg_done.py`** (new — upstream gating sentinel)
    - `xfail` until WS-O-arg closes upstream; flips to `pass` on the final argumentation commit.
    - Closes in the dependency repo when the upstream PR for Step 9 merges. **Not** flipped by a propstore commit.

## Sentinel discipline — upstream vs propstore (per Codex 2.18)

Each finding gets **two** sentinels with explicit closure conditions. A propstore commit cannot flip an upstream test; an upstream commit cannot prove the propstore pin contains the fix. Both directions are required.

For every Bug N (1..8):

- **Upstream sentinel** — lives in `argumentation/tests/test_<module>_<bug-name>.py` (the per-bug first-failing test listed above). Asserts the bug is fixed in the argumentation source tree. **Closure condition**: turns green when the upstream PR for that bug merges to argumentation's default branch. Closes in the **argumentation repo**.

- **Propstore sentinel** — lives in `propstore/tests/architecture/test_argumentation_pin_<bug-name>.py` (new directory: `propstore/tests/architecture/` is the canonical location for tests that assert a pinned dependency carries a specific behavior). Each propstore sentinel:
  1. Imports the public API surface from the pinned `argumentation` package.
  2. Exercises the public behavior the bug fix changed — observable from propstore, not by reading argumentation's internals.
  3. Asserts the corrected behavior.
  4. **Closure condition**: turns green when `propstore/pyproject.toml`'s argumentation pin advances to a commit that contains the upstream fix. Closes in **propstore** when the pin bumps.

Per-bug propstore sentinel sketches (each is one new file under `propstore/tests/architecture/`):

| Bug | Propstore sentinel file | Public-API assertion |
|---|---|---|
| 1 | `test_argumentation_pin_ideal_admissibility.py` | Build the same AFs as the upstream tests (including the mutual-defense fixture from `test_admissibility_requires_pair.py`) via the public `ArgumentationFramework` constructor, call `ideal_extension(...)`, assert (a) result is admissible by an independent admissibility check that calls only public API and (b) on the mutual-defense fixture the result is non-empty and contains the mutually-defending pair (regression gate against single-argument greedy). |
| 2 | `test_argumentation_pin_asp_literal_validity.py` | Build a small ASPIC theory via public KB API containing `~p` and `p(1, 2)`, call the public encode entry point, assert every emitted literal id matches the clingo identifier regex. |
| 3 | `test_argumentation_pin_rule_collision.py` | Build a KB via public API with two defeasible rules sharing a name and different conclusions; call public encode; assert either `ValueError` is raised at encode time or the emitted `d_head` ids are distinct. |
| 4 | `test_argumentation_pin_classification_table.py` | Drive `_classify_extension_change` through public revision API on Cayrol Table 3 worked examples; assert each returns the paper's classification. If the classifier is not exposed publicly today, assert the classification through whatever public revision-result type carries it. |
| 5 | `test_argumentation_pin_state_lazy.py` | Construct an `ExtensionRevisionState` with 20 arguments and sparse ranking via public API; assert construction completes within a budget (e.g., 100ms wall, 10MB process delta). |
| 6 | `test_argumentation_pin_preference_parity.py` | Drive `preference.strictly_weaker` and the public ASPIC defeat path on the `(non-empty, empty)` boundary; assert agreement. |
| 7 | `test_argumentation_pin_partial_skeptical.py` | Build a `PartialArgumentationFramework` via public API; assert `mode="necessary_skeptical"`, `mode="possible_skeptical"`, and bare `mode="skeptical"` (rejection) all behave per the upstream test. |
| 8 | `test_argumentation_pin_z_continuous.py` | Call the public z-confidence path with non-literal values; assert tolerance against pinned expected values. |

There is also a global sentinel pair gating WS-O-arg as a whole:

- **Upstream global sentinel**: `argumentation/tests/test_workstream_o_arg_done.py` (test 10 above). Flipped by Step 9 in the argumentation repo.
- **Propstore global sentinel**: `propstore/tests/architecture/test_workstream_o_arg_pin_done.py` (new). Asserts `propstore/pyproject.toml`'s argumentation pin is on a commit ≥ the Step-9 commit (resolved via git metadata or a recorded commit string in a pin manifest), and that all eight per-bug propstore sentinels above import without skip. **Closure condition**: turns green in propstore when the final pin bump lands.

The two-sentinel discipline ensures that a fix is genuinely reflected in propstore behavior, not merely in upstream source. A propstore PR cannot mark WS-O-arg closed by editing only the upstream sentinel (which lives in a different repo); the propstore-side pin bump and the propstore sentinel turning green is the closure event for propstore.

## Production change sequence

Per **D-15**, each step lands as a separate PR on `argumentation`'s default branch with a message of the form `WS-O-arg step N — <slug>`. After each PR merges, propstore bumps its dependency pin and re-runs the propstore test corpus before moving to the next step. Each step's acceptance is twofold: (a) the corresponding upstream sentinel green in argumentation; (b) the propstore pin on `propstore/pyproject.toml` advanced to that argumentation commit, the corresponding propstore sentinel green, propstore's full pytest re-run clean.

The eight steps are independent and may be reordered.

### Step 1 — Bug 1: ideal extension correctness (`dung.py`)

Implement the construction described in "Ideal extension — corrected construction" above using **admissible-subset enumeration with set-inclusion maximality**. **Single-argument greedy is forbidden** — it fails the mutual-defense counterexample in `tests/test_admissibility_requires_pair.py`. The previous restricted-characteristic-function option is deleted from the plan because the least-fixpoint-from-empty wording returns `∅` on the same counterexample. Cite Dung-Mancarella-Toni 2007 §3 / Thm 1 in the docstring with page references.

PR sequence: one PR adding `tests/test_dung_ideal_admissibility.py`, `tests/test_admissibility_not_downward_closed.py`, and `tests/test_admissibility_requires_pair.py` in red, then the fix making all three green.

Acceptance:
- Upstream: `tests/test_dung_ideal_admissibility.py`, `tests/test_admissibility_not_downward_closed.py`, and `tests/test_admissibility_requires_pair.py` all green in argumentation.
- Propstore: pin bumps; `propstore/tests/architecture/test_argumentation_pin_ideal_admissibility.py` green (extended to also cover the mutual-defense fixture); propstore suite clean.

### Step 2 — Bug 2: ASP literal sanitisation (`aspic_encoding.py`)

Add `_sanitise_literal_id(literal: Literal) -> str` that:
- Replaces leading `~` with `n_`.
- Replaces `(`, `,`, `)`, ` `, and any non-`[a-zA-Z0-9_]` byte with `_`.
- Lower-cases the leading character if it is uppercase (clingo treats leading-uppercase as a variable, not a constant).
- Asserts the result matches `^[a-z][a-zA-Z0-9_]*(\([a-zA-Z0-9_,]*\))?$`.

Maintain a `dict[str, Literal]` reverse map exposed on `ASPICEncoding` so consumers (propstore aspic_bridge) can recover the original literal from a returned id.

Replace `_literal_id = repr(literal)` (`:165`) with the sanitised version.

Acceptance:
- Upstream: `tests/test_aspic_encoding_asp_validity.py` green.
- Propstore: pin bumps; `test_argumentation_pin_asp_literal_validity.py` green.

### Step 3 — Bug 3: rule-name uniqueness (`aspic_encoding.py`)

In `_defeasible_rule_ids`, walk the rules collecting `name -> [Rule]`; if any list has length > 1, raise `ValueError(f"duplicate defeasible rule name: {name!r} attached to {len(rules)} rules")` with the offending names sorted for reproducibility.

Important: the check must happen at encode-call time (when emitting `d_head` facts), not at `Rule` construction time. `Rule` is widely instantiated and adding a global registry there would create cross-encoding interference. The bug's subtlety is that it surfaces at emission, not at insert; the fix lives at the same level.

Acceptance:
- Upstream: `tests/test_aspic_encoding_rule_collision.py` green.
- Propstore: pin bumps; `test_argumentation_pin_rule_collision.py` green.

### Step 4 — Bug 4: classification table content reasoning (`af_revision.py`)

Replace `_classify_extension_change` with a function that:
- Builds set-of-frozensets for `before` and `after`.
- For each Cayrol 2010 Table 3 row, encodes the row as a predicate `(before_set, after_set) -> bool` in subset-content terms.
- Returns the first matching kind, with a `RuntimeError` if none match (this is a paper-completeness assertion — every input should match one row).

Cite Table 3 of Cayrol-de-Saint-Cyr-Lagasquie-Schiex 2010 in the docstring with a per-row paper-page reference.

Acceptance:
- Upstream: `tests/test_af_revision_classification_table.py` green.
- Propstore: pin bumps; `test_argumentation_pin_classification_table.py` green.

### Step 5 — Bug 5: lazy `ExtensionRevisionState` (`af_revision.py`)

Refactor `ExtensionRevisionState`:
- `ranking` becomes `Callable[[frozenset[str]], int] | dict[frozenset[str], int]`.
- `__post_init__` does not enumerate; it normalises the explicit dict (if dict was passed) and validates that the explicit keys are subsets of `arguments`.
- `minimal_extensions(candidates)` queries `ranking(candidate)` for each candidate in the input tuple — never the full powerset.
- `with_argument(argument)` rebuilds via the same lazy interface.
- The class-level helper `all_extensions` stays for paper-faithfulness but is no longer called from `__post_init__`; document in the docstring "do not call on >15 arguments".

Acceptance:
- Upstream: `tests/test_af_revision_state_lazy.py` green.
- Propstore: pin bumps; `test_argumentation_pin_state_lazy.py` green.

### Step 6 — Bug 6: preference / aspic parity (`preference.py`)

Align `preference.strictly_weaker` to Modgil-Prakken Def 19: when `set_a` is empty return False; when `set_b` is empty (and `set_a` is not) return True; otherwise keep the elitist/democratic branches as-is. Two-line edit at `:58` resolves the disagreement. Cite Def 19 (p.21) of Modgil-Prakken 2018 in the comment. Optionally refactor `aspic._set_strictly_less` to delegate to `preference.strictly_weaker` to remove the duplicate.

Acceptance:
- Upstream: `tests/test_preference_aspic_parity.py` green.
- Propstore: pin bumps; `test_argumentation_pin_preference_parity.py` green.

### Step 7 — Bug 7: partial-AF skeptical naming (`semantics.py`)

Split the dispatcher's `mode` enum into `{"credulous", "necessary_skeptical", "possible_skeptical"}` plus an alias `"skeptical"` that:
- For `ArgumentationFramework` (Dung): aliases to `"skeptical"` (the existing behaviour — intersect across extensions).
- For `BipolarArgumentationFramework`: aliases to `"skeptical"` (same behaviour, single-completion).
- For `PartialArgumentationFramework`: raises `ValueError("ambiguous; use 'necessary_skeptical' or 'possible_skeptical' for partial AFs")`.

Implement `possible_skeptical` over partial AFs: per-completion intersection, then union across completions.

Cite Baumeister-Coste-Marquis 2013 in the docstring.

Acceptance:
- Upstream: `tests/test_semantics_partial_skeptical_split.py` green.
- Propstore: pin bumps; `test_argumentation_pin_partial_skeptical.py` green.

### Step 8 — Bug 8: continuous z-inverse-CDF (`probabilistic.py`)

Replace `_z_for_confidence` with a Beasley-Springer-Moro 1977 inverse-normal-CDF implementation (~30 lines, public-domain, accurate to 1e-9 on `(0, 1)`). Validate `0 < confidence < 1` with a `ValueError` for out-of-range. Compute `p = 1 - (1 - confidence) / 2` and run BSM. Keep the dict as a fast path for exact `0.90 / 0.95 / 0.99`.

Acceptance:
- Upstream: `tests/test_probabilistic_z_inverse_cdf.py` green.
- Propstore: pin bumps; `test_argumentation_pin_z_continuous.py` green.

### Step 9 — Close gaps and gate (both repos)

Upstream side (argumentation):
- Update or create `argumentation/docs/gaps.md`: one row per fix above with severity, file:line, first-failing-test path, status `closed <sha>`.
- Flip `tests/test_workstream_o_arg_done.py` from `xfail` to `pass`.

Propstore side:
- Confirm `propstore/pyproject.toml`'s argumentation pin is on the post-Step-8 argumentation commit.
- Flip `propstore/tests/architecture/test_workstream_o_arg_pin_done.py` from `xfail` to `pass` (or land it green if it was newly written at this step).
- Update this WS-O-arg file's STATUS line at the top from `OPEN` to `CLOSED <sha>`.
- Confirm propstore's full pytest is green against the new pin (no NEW failures vs the WS-A baseline).

## Acceptance gates

Before declaring WS-O-arg done, ALL of the following must hold:

- [ ] `cd C:\Users\Q\code\argumentation && uv run pyright src/argumentation` — passes with 0 errors.
- [ ] `cd C:\Users\Q\code\argumentation && uv run pytest tests/` — full suite green.
- [ ] Each of the 10 upstream first-failing tests above (including `test_admissibility_not_downward_closed.py` and `test_admissibility_requires_pair.py`) is green.
- [ ] `argumentation/tests/test_workstream_o_arg_done.py` flipped to pass.
- [ ] All 8 per-bug propstore sentinels under `propstore/tests/architecture/` are green.
- [ ] `propstore/tests/architecture/test_workstream_o_arg_pin_done.py` flipped to pass.
- [ ] `propstore/pyproject.toml` argumentation pin is on the post-Step-9 commit.
- [ ] propstore's full pytest run passes against the new pin (no NEW failures vs the WS-A baseline).
- [ ] WS-O-arg property-based gates from `PROPERTY-BASED-TDD.md` are included in the upstream and propstore sentinel runs where applicable.
- [ ] This WS-O-arg file's STATUS line says `CLOSED <sha>`.

## Done means done

This workstream is done when **every HIGH-severity finding in the table at the top is closed**, in **both** repositories, not when "most" are closed. Specifically:

- Bugs 1–8 — all eight numbered fixes — have a corresponding green test in argumentation's CI (the upstream sentinel) AND a corresponding green propstore-side test asserting the pinned dependency carries the fix (the propstore sentinel).
- Each bug merged as its own PR, propstore pin bumped after each, propstore suite re-run clean each time.
- The workstream's gating sentinel pair has flipped from xfail to pass in both repos.
- This file's STATUS line is `CLOSED <sha>`.

Read-only on production except for the pin bump in `propstore/pyproject.toml` and the propstore-side sentinel files under `propstore/tests/architecture/`. No propstore-side reimplementation, no wraps, no fork.

If any one of those is not true, WS-O-arg stays OPEN.

## Cross-stream — sub-streams

Per **D-16**, the coverage-gap work originally inventoried in this WS has been split into four sub-streams. All depend on this WS completing first (per the Blocks header above). ABA/ADF and Dung-extension work can proceed independently after the kernel fixes. VAF/ranking must precede gradual because gradual consumes `RankingResult` and the convergence-contract shape from VAF/ranking. Each is acknowledged as months of work, not weeks.

- **WS-O-arg-aba-adf** (Group A): ABA / ABA+ per Čyras 2016 (with Bondarenko 1997 + Toni 2014 as background); ADF per Polberg 2017 (with Brewka 2010/2013 as background). Both are first-class kernel additions, not patches. Depends on Bugs 1, 2, 3 fixes.
- **WS-O-arg-dung-extensions** (Group B): eager, stage2, prudent, semi-stable, bipolar grounded/complete, and Caminada labelling-as-semantics operational. All sit on top of Dung's existing infrastructure plus the labelling apparatus from Caminada 2006. Depends on Bug 1 fix.
- **WS-O-arg-vaf-ranking** (Group C): Bench-Capon 2003 VAF (with Atkinson 2007 background) plus the Bonzon ranking-semantics family beyond Categoriser/Burden. Depends on Bug 1 fix; Bug 6 fix removes a confounder for ranking-comparison code paths.
- **WS-O-arg-gradual** (Group D): DF-QuAD discontinuity-free gradual semantics outside the probabilistic-only path, plus Matt-Toni 2008 game-theoretic argument strength. Depends on Bugs 2 and 8 fixes.

The `register_backend` API smell from cluster P (no propstore-side ASP backend can attach to `solve_aspic_with_backend`) is **not** in this WS and **not** in any of the four sub-streams above. It is a small upstream API addition tracked as a separate followup; see argumentation repo `gaps.md`.

## Cross-stream notes

- Parallel-safe with WS-A, WS-B, WS-C, WS-D and other WS-O-* dependency fixes (those WS-O-* streams target different dependency packages).
- After merge, **WS-F (propstore-side ASPIC bridge fidelity)** verification gets cleaner: encoder ids are honest and rule-name collisions surface as errors. WS-F's projection tests must wait for Bugs 2, 3, 6 to close before their assertions can be trusted.
- `T2.9` (ASPIC grounded conflict-free) is owned by WS-F — propstore-side delegation issue at `propstore/aspic_bridge/structured_projection.py:253`, not a defect in `argumentation.dung.grounded_extension`.
- Per **D-12**, AGM-AF revision stays upstream; propstore consumes via public API only. Bugs 4 and 5 (both `af_revision.py`) are in scope precisely because they are upstream. WS-G blocks on this WS for the revision public-API surface to be honest.

## Papers / specs referenced

Under `C:\Users\Q\code\propstore\papers\<dir>\` (verified):

- `Dung_1995_AcceptabilityArguments` — Dung semantics substrate; cited for admissibility and preferred extensions used in the ideal-extension construction.
- `Dung_2007_ComputingIdealScepticalArgumentation` (cluster P) — **authoritative for the corrected ideal-extension construction (Bug 1)**. §3 gives the lattice-fixed-point algorithm; Thm 1 gives uniqueness of the largest admissible set in the intersection of preferred extensions.
- `Modgil_2014_ASPICFrameworkStructuredArgumentation` — Def 19 set lifting (Bug 6).
- `Lehtonen_2020_AnswerSetProgrammingApproach`, `Lehtonen_2024_PreferentialASPIC` — ASP encoding background (Bug 2).

Cayrol-de-Saint-Cyr-Lagasquie-Schiex 2010 (Bug 4) and Diller 2015 (Bug 5) are cited in `af_revision.py` docstrings; not on disk at this snapshot — fixes proceed from in-source citations. Beasley-Springer-Moro 1977 (Bug 8) is classical and public-domain. Baumeister-Coste-Marquis 2013 (Bug 7) — citation alone suffices for the dispatcher rename.

## What this WS does NOT do

- NOT implement ABA, ADF, VAF, gradual, ranking, Caminada-operational, or any other coverage gap — tracked in WS-O-arg-aba-adf, WS-O-arg-dung-extensions, WS-O-arg-vaf-ranking, WS-O-arg-gradual.
- NOT add `register_backend` / `unregister_backend` symbols. Tracked separately as an upstream API followup.
- NOT touch `aspic.py` beyond Step 6's optional delegation refactor.
- NOT optimise `bipolar.py:226-229` closure rebuilds or `weighted.py:97` `2^|attacks|` enumeration; efficiency smells, correctness-clean.
- NOT touch `aspic.py:519-628` process-wide `@functools.cache`; single-threaded use is fine.
- NOT change `dung.py:413` recursive Tarjan to iterative; recursion-limit risk only, no wrong-output evidence.
- NOT write a DIMACS exporter for `sat_encoding.py`. Coverage gap, not correctness bug.
- NOT introduce any propstore-side reimplementation of AGM-AF revision, ideal extension, ASPIC encoding, or any other affected API. Per **D-12** and **D-15**, propstore consumes via the public API after each upstream PR merges.
