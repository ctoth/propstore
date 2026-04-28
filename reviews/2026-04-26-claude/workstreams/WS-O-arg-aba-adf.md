# WS-O-arg-aba-adf: argumentation pkg coverage — flat ABA + ADF foundational frameworks

**Status**: CLOSED 58bbae38
**Scope**: flat ABA only (Bondarenko 1997 §4 / Toni 2014 §3 flatness condition) + arbitrary ADFs (Brewka 2013 operator-based semantics). **Non-flat ABA is explicitly out of scope** per Codex 2.20.
**Depends on**: `WS-O-arg-argumentation-pkg` — every HIGH bug in the existing
kernel must merge upstream first; new ABA/ADF kernels are not allowed to
import a known-broken `dung.ideal_extension` or a known-broken
`aspic_encoding._literal_id`.
**Blocks**: nothing in propstore directly. propstore consumes only the
public API of `argumentation`, so propstore-side work proceeds in parallel
on existing kernels. This workstream gates *future* propstore consumers
that want to phrase reasoning problems as flat ABA or ADF rather than as
Dung + ASPIC+.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

---

## Why this exists

D-15 froze the dependency-package policy: gaps in `argumentation` close
upstream, propstore pins new versions. D-16 committed to "all four
groups — implement everything" from the cluster-P coverage inventory.
Group A is the flat-ABA + ADF foundational pair, both absent from the
package today (`cluster-P-argumentation-pkg.md:308-323`). Cluster P names
flat ABA + ADF as the two largest missing formalism families; the
package cannot claim to be a citation-anchored library for formal
argumentation (`argumentation/README.md:1`) while two of the four
textbook formalisms are missing. D-8 (trust calibration as
argumentation) promotes these kernels from optional to load-bearing for
any future propstore consumer that wants to reason at the assumption
level (flat ABA) or with multi-valued acceptance conditions (ADF).

This WS produces two new modules in `argumentation`. propstore ships
nothing here; the propstore-side change is a single pin bump.

## Review findings covered

This workstream closes ALL of the following from the cluster-P inventory.
"Done means done" — every finding listed has a corresponding green test
in the `argumentation` test suite gated on the upstream PR(s).

| Finding | Source | Citation | Description |
|---|---|---|---|
| **P-A.1** | `cluster-P-argumentation-pkg.md:308-315` | `argumentation/src/argumentation/` (no `adf.py`) | ADF (Brewka 2010, 2013) NOT IMPLEMENTED. No acceptance condition machinery, no link classification, no two- or three-valued ADF semantics, no link-based decomposition. |
| **P-A.2** | `cluster-P-argumentation-pkg.md:317-323` | `argumentation/src/argumentation/` (no `aba.py`) | flat ABA (Bondarenko 1997 §4, Toni 2014 §3) NOT IMPLEMENTED. No assumption layer, no contrary mapping for assumptions, no deduction-based attack derivation. |
| **P-A.3** | `cluster-P-argumentation-pkg.md:646-652` | bibliography lists Bondarenko 1997, Toni 2014, Brewka 2010, Brewka 2013 | Four foundational papers under the argumentation track with no executable kernel. |
| **P-A.4** | `cluster-P-argumentation-pkg.md:741-746` (open question 4) | n/a | Q's open question: "Is propstore meant to use ABA/ADF formalisms, and if so are these expected to land in `argumentation` (as new modules)?" — D-16 answers yes; this WS lands the flat-ABA + ADF kernels. |

Adjacent items folded in because the marginal cost is small while we are
touching this surface:

| Finding | Citation | Why included |
|---|---|---|
| ABA+ preferences (Čyras 2016), restricted to flat ABA+ | `DECISIONS.md:166-172` (D-16 Group A scope) | The cluster-P inventory lists Bondarenko/Toni; D-16 explicitly names "Cyras 2016 ABA+" alongside, because preferences in flat ABA are a strict superset of plain flat ABA and the implementation path through the contrary mapping is shared. Building plain flat ABA without ABA+ would require a second pass through the same code. ABA+ over non-flat frameworks is out of scope on the same boundary as plain non-flat ABA. |
| ICCMA-style I/O for ABA + ADF | `cluster-P-argumentation-pkg.md:340-359` | The ICCMA 2025 protocol surveys include ABA tracks (ABA-DC, ABA-DS, ABA-EE) and ADF tracks. Without I/O the kernels cannot be probo-callable, which is the same gap the existing `iccma.py` was built to close for Dung AFs. Same pattern, two new files. |
| Consumer-surface seam in propstore | `WS-O-arg-argumentation-pkg.md` (referenced) | If propstore eventually consumes flat ABA / ADF, the seam is the public `argumentation` import surface. Not a code change in propstore in this WS; called out so reviewers know to gate on it. |

## Code references (verified by direct read)

### Existing kernel pattern — what to match

`argumentation/src/argumentation/dung.py:18-50` — `ArgumentationFramework`
is a `@dataclass(frozen=True)` with `__post_init__` normalisation, a
`_normalize_relation` validator, and explicit type aliases. Same shape
must be reused for `ABAFramework` and `AbstractDialecticalFramework`.

`argumentation/src/argumentation/dung.py:99-110` — `conflict_free` is a
free function over the dataclass plus a relation. ABA and ADF predicates
should be free functions in the same style; no methods on the dataclass
beyond `__post_init__`.

`argumentation/src/argumentation/iccma.py:1-72` — pattern for ICCMA
text I/O: `parse_<x>(text) -> X` + `write_<x>(framework: X) -> str`,
strict header validation, deterministic sort on output. Both new modules
mirror this pattern with formalism-specific headers (`p aba`, `p adf`).

`argumentation/src/argumentation/__init__.py:3-43` — re-export list. Two
new entries, alphabetical: `aba` between `accrual` and `af_revision`;
`adf` between `aspic_incomplete` and `bipolar`.

`argumentation/src/argumentation/aspic.py:25-81, 137-162` — pattern for
defining a structured argumentation language (`GroundAtom`, `Literal`,
`Rule`). flat ABA reuses the same `Literal` and `Rule` types — assumptions are
a *subset* of literals, not a new type. Reuse, do not duplicate.

### Paper anchors

`papers/Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/notes.md:38-95`
— ABA framework `<T, Ab, ¯>`, deductive system schema, conflict-free
(Def 2.2), attack (Def 3.1), closed (Def 3.3), stable (Def 3.4),
admissibility (Def 4.3), preferred (Def 4.4), flat (Def 4.10), `Def`
operator (Def 5.1, 5.2). The flatness condition (Def 4.10) is the
acceptance gate for this WS — we implement only frameworks that satisfy
it. Each Bondarenko definition becomes a function with a docstring citing
the paper, page, and equation.

`papers/Toni_2014_TutorialAssumption-basedArgumentation/notes.md:46-100`
— rule schema `σ_0 ← σ_1, ..., σ_m`, ABA framework `<L, R, A, ¯>`, three
deduction views (tree-style, backward, forward), three attack views
(argument-to-argument, set-to-set, hybrid), flat ABA condition. The
tutorial gives the operational story the Bondarenko paper sets up
formally. Worked examples (Ex 3.1, 5.1–5.4) are all flat and become
first failing tests.

`papers/Brewka_2010_AbstractDialecticalFrameworks/notes.md:31-89` — ADF
definition `D = (S, L, C)`, Dung AF as special case via
`C_s = ¬a_1 ∧ ... ∧ ¬a_n`, three-valued interpretations, consensus
operator `Γ_D`, grounded as least fixpoint of `Γ_D` from `v_u`, stable
model via reduced ADF `D^M`, weighted ADF acceptance.

`papers/Brewka_2013_AbstractDialecticalFrameworksRevisited/notes.md:31-99`
— operator-based three-valued semantics for arbitrary ADFs (not just
bipolar). `v` admissible iff `v ≤_i Γ_D(v)`; `v` complete iff
`Γ_D(v) = v`; `v` preferred iff `≤_i`-maximal admissible. Stable via
reduct `D^v` for arbitrary ADFs. Complexity bounds (NP-c, coNP-c, DP-c,
Σ2P-c) anchor expected-failure tests for the right complexity behavior.

Čyras 2016 (flat ABA+) and Polberg 2017 (ADF thesis) were retrieved as
part of the D-16 scope expansion and are listed in the SOURCE MATERIALS
of this WS. Their notes.md files do not yet exist in `papers/` at WS-
creation time. **First action of this WS is paper-process them.** No
code change proceeds before those notes.md files exist.

### Public API the kernels must expose

Each new module exposes the framework dataclass + the predicate/operator
free functions + the semantics computers, mirroring `dung.py` plus
`labelling.py`:

`argumentation/src/argumentation/aba.py` (new — flat ABA only):
- `ABAFramework` (frozen dataclass: language, rules, assumptions, contrary)
  — `__post_init__` rejects any framework whose `assumptions` set
  intersects the heads of `rules` (the flatness condition, Bondarenko Def
  4.10). Non-flat input raises `NotFlatABAError` at construction time.
  There is no API path that accepts a non-flat framework.
- `ABAPlusFramework` (frozen dataclass: ABAFramework + preference order
  over assumptions) — inherits the flatness gate from its embedded
  `ABAFramework`.
- `derives(framework, premises, conclusion) -> bool` — `T ∪ S ⊢ α` test
- `argument_for(framework, conclusion) -> ABAArgument` — supported tree
- `attacks(framework, attacker_assumptions, target_assumptions) -> bool`
- `closed(framework, assumption_set) -> bool` — Bondarenko Def 3.3
- `conflict_free`, `admissible`, `def_operator` — Defs 2.2, 4.3, 5.1-5.2
- Semantics computers (flat-ABA only, over the assumption frame):
  `naive_extensions`, `stable_extensions`, `complete_extensions`,
  `preferred_extensions`, `grounded_extension`, `ideal_extension`,
  `well_founded_extension`. Each is computed directly over the
  assumption frame using the flat-ABA correspondence to Dung extensions
  (Toni 2012 Theorem 2), not via ASPIC+ projection.
- `aba_to_dung(framework) -> ArgumentationFramework` — bridge to existing
  Dung machinery for callers who want it. Defined only because the input
  is flat.
- ABA+ extensions: `attacks_with_preferences(framework, attacker, target)`
  per Čyras 2016 Def 3 (preferences over assumptions filter attacks
  exactly as M&P Def 9 does in ASPIC+). Operates on flat ABA+ frameworks
  only.

`argumentation/src/argumentation/adf.py` (new):
- `AbstractDialecticalFramework` (frozen dataclass: statements, links,
  acceptance conditions). Acceptance condition representation: a typed
  AST per D-25 (see "Acceptance-condition AST" below); the dataclass
  stores one `AcceptanceCondition` AST per statement, indexed by
  statement id.
- `LinkType` enum: `SUPPORTING`, `ATTACKING`, `BOTH`, `NEITHER`,
  `UNDEFINED` (Brewka 2010 §3 link classification).
- `classify_link(framework, parent, child) -> LinkType` — pure function
  over the AST structure (Polberg 2017 ch.4). Does not need to evaluate
  the condition over all parent assignments; reads the AST directly.
- `ThreeValued` enum: `T`, `F`, `U` with information ordering `≤_i`.
- `Interpretation` (alias for a canonical mapping form
  `frozenset[tuple[str, ThreeValued]]`).
- `gamma(framework, interpretation) -> Interpretation` — consensus
  operator; on each statement `s`, evaluate the AST `C_s` under all
  two-valued completions of the parents that extend the current
  interpretation, return the meet.
- `grounded_interpretation(framework) -> Interpretation` — least fixpoint
  of `Γ` from all-undefined.
- `is_admissible`, `is_complete`, `is_preferred`, `is_stable` per Brewka
  2013 operator-based definitions.
- Computers: `complete_models`, `preferred_models`, `stable_models`,
  `model_models` (two-valued), `admissible_interpretations`.
- `adf_to_dung(framework) -> ArgumentationFramework` — bridge for the
  AF-encoded special case (`C_s = ∧¬a_i`).
- `dung_to_adf(af) -> AbstractDialecticalFramework` — inverse bridge.

`argumentation/src/argumentation/iccma.py` (extend, new functions):
- `parse_aba(text) -> ABAFramework`, `write_aba(framework) -> str` for an
  ICCMA-style ABA text format. ICCMA 2023 onwards specifies an `aba`
  problem family; the file format follows the ASP-flavoured grammar
  (`a 1.`, `c 1 2.`, `r 3 1 2.`). Parser rejects non-flat input with
  `NotFlatABAError` (consistent with the dataclass gate).
- `parse_adf(text) -> AbstractDialecticalFramework`,
  `write_adf(framework) -> str` for ADF text format. ICCMA 2023 onwards
  specifies an `adf` problem family using a propositional-formula
  grammar for acceptance conditions. The grammar maps directly onto the
  `AcceptanceCondition` AST (round-trip preserves AST shape).

### Acceptance-condition AST (D-25)

D-25 locks in a typed AST over parent labels. Callable representation is
not implemented; there is no dual path (per `feedback_no_fallbacks.md`).

`AcceptanceCondition` is a sum type with these node constructors, all
immutable frozen dataclasses:

- `Atom(parent: str)` — references a parent statement label. The label
  must appear in the framework's `par(s)` for the owning statement;
  enforced at framework-construction time.
- `Not(child: AcceptanceCondition)`
- `And(children: tuple[AcceptanceCondition, ...])` — `n`-ary, `n ≥ 0`;
  empty `And` is logically `True` (canonicalized to `True_`).
- `Or(children: tuple[AcceptanceCondition, ...])` — `n`-ary, `n ≥ 0`;
  empty `Or` is logically `False` (canonicalized to `False_`).
- `True_` — singleton.
- `False_` — singleton.

Properties locked in:

- **Serializable to JSON.** Each node has a deterministic JSON shape
  (`{"op": "Atom", "parent": "a"}`, `{"op": "Not", "child": {...}}`,
  `{"op": "And", "children": [...]}`, etc.). Round-trip
  `AST → JSON → AST` is the identity on canonical-form ASTs.
- **Serializable to ICCMA ADF format.** The ICCMA 2023+ ADF grammar is
  a propositional-formula syntax that maps node-for-node onto the AST.
  `write_adf` emits this; `parse_adf` constructs ASTs.
- **Inspectable by the structural-link classifier.** `classify_link`
  walks the AST for `C_child` and reads the dependency on `parent`
  *structurally* (Polberg 2017 ch.4 monotonicity-by-structure
  algorithm). It does not need to evaluate the AST over all parent
  assignments to decide `SUPPORTING` vs `ATTACKING`; the AST shape
  determines the answer in polynomial time for the monotone cases, and
  falls back to assignment enumeration only for the genuinely
  non-monotone cases (`NEITHER`).
- **No callable representation, no `from_callable` bridge.** The
  earlier draft offered an `Option AC-1` callable path and an `AC-2`
  AST path with a `from_callable` helper; both are removed. The AST is
  the only representation. Callers that have a Python predicate must
  build an AST explicitly; this is intentional friction, because a
  predicate cannot be serialized, classified structurally, or sent to
  a SAT/ASP backend.

Polberg 2017 thesis convention is the standard reference: every ADF
algorithm in the thesis manipulates formula ASTs, not opaque callables.
The ICCMA 2023+ ADF track grammar requires AST representation in the
file format.

## First failing tests (write these first; they MUST fail before any production change)

In `argumentation/tests/`. None are in propstore. Every ABA test below
uses a *flat* framing.

### ABA tests (flat only)

1. **`tests/test_aba_bondarenko_examples.py`** (new)
   - Implements every flat worked example from Bondarenko 1997 §4 (logic
     programs viewed as ABA, three classical examples: birds/penguins,
     Yale shooting, default consistency check). Each is flat by
     construction in the paper. Each becomes:
     `def test_bondarenko_<example_n>__<semantics>():` for naive,
     stable, admissible, preferred, complete, well-founded.
   - **Must fail today**: `argumentation.aba` does not exist.

2. **`tests/test_aba_toni_2014_tutorial.py`** (new)
   - Implements Toni 2014 Examples 3.1, 5.1, 5.2, 5.3, 5.4 from the
     tutorial — all flat. Each example pins:
     - argument constructions (set of supported `(A, σ)` pairs)
     - attack relation (set of `(attacker_set, target_set)` pairs)
     - assumption-level extensions for each semantics
     - argument-level extensions (via `aba_to_dung` projection) match
       the assumption-level extensions through the Toni 2012 bijection
   - **Must fail today**: `argumentation.aba` does not exist.

3. **`tests/test_aba_plus_cyras_2016.py`** (new — primary algorithmic pin)
   - Implements every flat worked example from Čyras 2016 §3 — the ABA+
     paper that D-16 names as the primary algorithmic reference for
     preferences in flat ABA. Each `<example_id, semantics>` pair becomes a
     test. **Includes** the §3 preferred-extension worked example
     called out explicitly in this WS's SCOPE block.
   - Pins the preference-filtering rule: an attack from assumption set
     `A` on assumption `α` succeeds iff there is no assumption in `A`
     strictly weaker than `α` per the assumption preference order.
   - **Must fail today**: `argumentation.aba.ABAPlusFramework` does
     not exist.

4. **`tests/test_aba_dung_correspondence.py`** (new)
   - For each flat ABA framework in the corpus above, build the
     `aba_to_dung` projection and assert that, semantics-by-semantics,
     the extension-set of the ABA framework projects to the extension-set
     of the Dung framework via the assumption-set bijection. Toni 2012
     Theorem 2 (which assumes flatness) is the formal statement.
   - Hypothesis property test (`@pytest.mark.property`): for arbitrary
     small flat ABA frameworks (≤6 assumptions, ≤8 rules; the strategy
     filters non-flat instances), grounded extensions of `aba_to_dung(F)`
     and grounded extensions of `F` project onto each other.
   - **Must fail today**: projection function does not exist.

5. **`tests/test_aba_iccma_io.py`** (new)
   - Round-trip property: `parse_aba(write_aba(F)) == F` for every
     framework in the test corpus (all flat).
   - Format-validation: malformed inputs (missing header, bad rule
     syntax, contrary referencing non-assumption) raise `ValueError`.
   - Non-flat input rejection: an ICCMA-format ABA file whose rules have
     an assumption in the head raises `NotFlatABAError` with a citation
     to Bondarenko Def 4.10.
   - **Must fail today**: `parse_aba`/`write_aba` do not exist.

### ADF tests

6. **`tests/test_adf_acceptance_condition_ast.py`** (new — D-25 pin)
   - **AST round-trip**: for a parametrized corpus of `AcceptanceCondition`
     AST values (atom, negation, n-ary `And`/`Or`, `True_`/`False_`,
     deeply nested combinations), assert
     `from_json(to_json(ast)) == ast`. Serialization is deterministic
     (key order, child order under associative ops).
   - **ICCMA round-trip**: for the same corpus, assert
     `parse_iccma_formula(write_iccma_formula(ast)) == ast`.
   - **Structural classifier reads dependencies from AST without
     evaluation**: build an ADF whose acceptance condition for child
     `c` is `And(Atom("a"), Not(Atom("b")))`. Patch `Atom.evaluate` to
     raise `RuntimeError` if called. Call
     `classify_link(framework, parent="a", child="c")` and assert it
     returns `SUPPORTING` *without* the patched evaluator firing. Repeat
     for `parent="b"` → `ATTACKING`. The classifier reads parent
     dependencies from AST structure only.
   - **Canonicalization**: `And()` (empty) is `True_`; `Or()` is `False_`;
     `Not(Not(x))` simplifies to `x`; `And` and `Or` children are
     ordered for hashing. Equality is structural up to canonical form.
   - **No callable path**: assert that `AcceptanceCondition` exposes no
     `from_callable` constructor and no `__call__` method (introspect
     the class). The AST is the only representation per D-25.
   - **Must fail today**: `argumentation.adf` does not exist; the AST
     module does not exist.

7. **`tests/test_adf_brewka_2010_examples.py`** (new)
   - Implements every worked example from Brewka 2010 §2-5: legal-proof-
     standards ADF, the bipolar examples, the Dung-encoded ADF. Pins:
     - link classification (each `(parent, child)` to LinkType)
     - grounded interpretation
     - two-valued models (when bipolar)
   - **Must fail today**: `argumentation.adf` does not exist.

8. **`tests/test_adf_brewka_2013_revisited.py`** (new — primary algorithmic pin)
   - Implements every worked example from Brewka 2013 §3-5: Examples 1
     (the counterexample to old two-valued stable), 2 (three-cycle with
     no stable model), 3 (prioritized ADF), 4 (dynamic preference node).
     For each, pin admissible / complete / preferred / stable per the
     three-valued operator-based definitions.
   - **Must fail today**: ADF kernel and the operator do not exist.

9. **`tests/test_adf_polberg_2017.py`** (new — primary algorithmic pin)
   - Implements the worked example from Polberg 2017 thesis §X.Y called
     out explicitly in this WS's SCOPE block. The thesis is 697 pages
     and contains many; the *one* used here is the canonical ADF model-
     enumeration walk-through that Polberg uses to introduce her
     algorithmic framework. Specific section pinned in the test
     docstring after the paper-process notes.md is written.
   - Additional smaller pins from the thesis worked examples that
     exercise: (a) the structural link-classification algorithm (reads
     AST shape only), (b) the grounded fixpoint procedure, (c) the
     preferred-by-stability algorithm.
   - **Must fail today**: ADF kernel does not exist.

10. **`tests/test_adf_dung_correspondence.py`** (new)
    - For every Dung AF in the existing `tests/test_dung.py` corpus,
      build `dung_to_adf` and assert that semantics-by-semantics, the
      extension-set under Dung matches the two-valued model set under
      ADF (Brewka 2010 Theorem 1, Brewka 2013 Theorem 3). The
      `dung_to_adf` bridge produces ASTs of shape
      `And(Not(Atom(a_1)), ..., Not(Atom(a_n)))`.
    - **Must fail today**: bridge function does not exist.

11. **`tests/test_adf_link_classification.py`** (new)
    - Property test: for each generated ADF (acceptance conditions
      generated as random ASTs over a small parent set), `classify_link(parent,
      child)` returns:
      - `SUPPORTING` iff `C_child`'s AST is monotone non-decreasing in
        `parent` by structural inspection.
      - `ATTACKING` iff `C_child`'s AST is monotone non-increasing in
        `parent` by structural inspection.
      - `BOTH` iff `parent` is irrelevant to `C_child` (does not appear
        in the AST).
      - `NEITHER` iff `parent` appears non-monotonically in the AST
        (sometimes under an even number of negations, sometimes odd).
      - `UNDEFINED` only when `parent ∉ par(child)`.
    - Brewka 2010 §3, Polberg 2017 ch.4 algorithmic definition.
    - **Must fail today**: classifier does not exist.

12. **`tests/test_adf_iccma_io.py`** (new)
    - Round-trip and validation, mirroring test 5. The acceptance-
      condition formula syntax round-trips through the AST.
    - **Must fail today**: parser/writer do not exist.

### Cross-formalism gating

13. **`tests/test_aba_adf_independence.py`** (new)
    - Imports `argumentation.aba` and `argumentation.adf` and asserts
      that neither imports the other (per AST scan of the source files,
      same technique propstore uses for `lint-imports`).
    - The two formalisms are siblings, not parent-child.
    - **Must fail today**: modules do not exist.

### Paired sentinels — upstream + propstore (per Codex 2.18)

Per Codex 2.18 (already applied to WS-O-arg-argumentation-pkg), every
upstream WS needs **two** sentinels with explicit closure conditions. A
propstore commit cannot flip an upstream test; an upstream commit cannot
prove the propstore pin contains the fix. Both directions are required.

14a. **`argumentation/tests/test_workstream_o_arg_aba_adf_done.py`**
     (new — upstream sentinel; lives in the **argumentation** repo)
     - `xfail` until tests 1-13 above are all green in the argumentation
       repo and Steps 1-11 have shipped upstream.
     - Asserts the upstream behaviour shipped: `from argumentation import
       aba, adf` both succeed; `aba.ABAFramework` and
       `aba.ABAPlusFramework` exist; `adf.AbstractDialecticalFramework`
       and `adf.AcceptanceCondition` exist; `adf.classify_link` is
       importable; `aba.NotFlatABAError` is the type raised on non-flat
       input; `iccma.parse_aba`/`write_aba`/`parse_adf`/`write_adf`
       importable.
     - **Closure condition**: turns green when the final upstream PR
       (Step 11 — flat-ABA ICCMA I/O) merges to argumentation's default
       branch. Closes in the **argumentation repo**. Independent of any
       propstore-side change.
     - Mirrors `test_workstream_a_done.py` from WS-A.

14b. **`propstore/tests/architecture/test_argumentation_pin_aba_adf.py`**
     (new — propstore sentinel; lives in **propstore**)
     - Imports the public API surface from the pinned `argumentation`
       package: `from argumentation import aba, adf`; `from
       argumentation.aba import ABAFramework, ABAPlusFramework,
       NotFlatABAError`; `from argumentation.adf import
       AbstractDialecticalFramework, AcceptanceCondition, LinkType,
       classify_link`; `from argumentation.iccma import parse_aba,
       write_aba, parse_adf, write_adf`.
     - Exercises one paper-faithful behavioural assertion per major
       addition, observable from propstore (no reaching into
       argumentation internals):
       - flat ABA: build a small flat `ABAFramework` via the public
         constructor; call `grounded_extension(framework)`; assert the
         pinned Bondarenko worked-example value.
       - Non-flat rejection: assert constructing a non-flat framework
         raises `NotFlatABAError` (caller-visible boundary).
       - ABA+ preferences: build an `ABAPlusFramework`; call
         `attacks_with_preferences`; assert pinned Čyras 2016 worked-
         example value.
       - ADF: build a small `AbstractDialecticalFramework` via the public
         AST constructors (`Atom`, `Not`, `And`); call
         `grounded_interpretation(framework)`; assert pinned value.
       - Link classification: call `classify_link(framework, parent,
         child)` on an AST shaped `And(Atom("a"), Not(Atom("b")))` and
         assert `SUPPORTING` for parent `a`, `ATTACKING` for parent `b`.
       - AST callable absence: introspect `AcceptanceCondition` to assert
         no `from_callable` and no `__call__` (the D-25 boundary,
         observable from propstore).
       - ICCMA round-trip: `parse_aba(write_aba(framework)) == framework`
         on a small flat fixture.
     - Asserts `propstore/pyproject.toml`'s argumentation pin string
       equals or post-dates the recorded post-Step-11 argumentation
       commit (resolved via a recorded commit string in this WS or via
       git metadata).
     - **Closure condition**: turns green when
       `propstore/pyproject.toml`'s argumentation pin advances to a
       commit that contains all Step 1-11 fixes AND every behavioural
       assertion above passes against that pinned dependency. Closes in
       **propstore** when the pin bumps and the propstore suite re-runs
       clean.

The two-sentinel discipline ensures that a fix is genuinely reflected in
propstore behavior, not merely in upstream source. A propstore PR cannot
mark this WS closed by editing only the upstream sentinel (which lives
in a different repo); the propstore-side pin bump and 14b turning green
is the closure event for propstore.

## Production change sequence

Each step lands in its own commit in the `argumentation` repo with a
message of the form `WS-O-arg-aba-adf step N — <slug>`. propstore's only
change is the pin bump after step 12.

### Step 0 — Paper-process Čyras 2016 and Polberg 2017

Run `paper-process` on both paper PDFs. Result: notes.md files in
`papers/Čyras_2016_ABAAssumption-BasedArgumentationPreferences/` and
`papers/Polberg_2017_DevelopingAbstractDialecticalFramework/`. No code
change yet; every later step cites equation/algorithm numbers from
those notes. Both papers are required because neither has notes.md at
WS-creation time.

Acceptance: both notes.md exist, lint via the paper-collection lint
skill passes for both directories.

### Step 1 — Acceptance-condition AST + ADF dataclass

Implement the `AcceptanceCondition` AST (`Atom`, `Not`, `And`, `Or`,
`True_`, `False_`) per D-25 and the `AbstractDialecticalFramework`
dataclass in `argumentation/src/argumentation/adf.py`. Cite Brewka 2010
§2 and Polberg 2017 ch.4 in the module docstring (Polberg as the
canonical reference for AST representation); cite Brewka 2013 §2 for
the three-valued interpretation type. AST construction validates that
every `Atom(parent)` references a parent in the framework's `par(s)`
for the owning statement. Re-export from `__init__.py`.

Acceptance: `import argumentation.adf` succeeds; dataclass instances are
hashable and frozen; `__post_init__` rejects malformed inputs (link in
`L` references non-statement, `C` missing key for some statement, `Atom`
referencing a non-parent label). Test 6 (the AST-pin test) turns green.

### Step 2 — `Γ_D` consensus operator + grounded fixpoint

Implement `gamma`, `meet`, `is_admissible`, `is_complete`. Implement
`grounded_interpretation` as the least fixpoint of `Γ_D` from all-`U`.
`gamma` evaluates the AST under all two-valued completions of the
parents and takes the meet. Pin Brewka 2010 Def 4 and Brewka 2013 §2-3
in docstrings.

Acceptance: tests 7 and 8 (grounded portions) turn green.

### Step 3 — Link classification + Dung bridge

Implement `LinkType`, `classify_link`, `dung_to_adf`, `adf_to_dung`.
`classify_link` walks the AST structurally (Polberg 2017 ch.4
algorithm). `dung_to_adf` produces ASTs of the form
`And(Not(Atom(a_1)), ..., Not(Atom(a_n)))` for each statement.
Test 11 turns green; test 10 turns green. Brewka 2010 Theorem 1 and
Brewka 2013 Theorem 3 in docstrings.

### Step 4 — Preferred / stable for arbitrary ADFs

Implement `is_preferred`, `is_stable` per the three-valued operator-
based definitions; implement enumerators `preferred_models`,
`stable_models` via subset-enumeration with early pruning. Pin Brewka
2013 §3 (the new operator-based definitions that supersede the 2010
two-valued definitions on bipolar ADFs).

Acceptance: tests 7, 8, 9 fully green. Test 9 specifically pins the
Polberg 2017 worked example.

### Step 5 — ADF ICCMA I/O

Extend `iccma.py` with `parse_adf`, `write_adf`. ICCMA 2023+ ADF
grammar maps directly onto the `AcceptanceCondition` AST.

Acceptance: test 12 green.

### Step 6 — flat ABA dataclass + deduction

Implement `ABAFramework` dataclass in
`argumentation/src/argumentation/aba.py`. Reuse `Literal` and `Rule`
from `aspic.py` — assumptions are a subset of literals.

`__post_init__` enforces the flatness condition (Bondarenko Def 4.10,
Toni 2014 §3): `assumptions ∩ heads(rules) = ∅`. Non-flat input raises
`NotFlatABAError`. There is no API path that constructs a non-flat
framework.

Implement `derives(framework, premises, conclusion)` via forward
deduction (Toni 2014 §3 forward-style). The tutorial gives forward
deduction as the implementation choice; it is linear in rules per
fixed-point iteration and is well-defined under flatness.

Acceptance: `import argumentation.aba` succeeds; `derives` returns the
right boolean on the Bondarenko §4 Yale-shooting example;
`NotFlatABAError` fires on a constructed non-flat input.

### Step 7 — Argument construction + attack relation

Implement `argument_for`, `attacks` (set-of-assumptions level per Toni
2014 §4). Three attack views are equivalent under flatness (Toni 2014
§4); we implement set-to-set and lift via helper functions for the
other two.

Acceptance: test 1 (Bondarenko), test 2 (Toni) turn green for the
*conflict-free* and *attack* portions.

### Step 8 — `closed`, `Def`, semantics over flat ABA

Implement `closed`, `def_operator`, `is_admissible`,
`grounded_extension` (least fixpoint of `Def`), `complete_extensions`,
`preferred_extensions`, `stable_extensions`, `naive_extensions`,
`well_founded_extension`, `ideal_extension`. Pin Bondarenko 1997 §3-6
in docstrings. All semantics are computed over the assumption frame
under the flatness assumption — no non-flat code path exists.

Acceptance: tests 1 / 2 / 4 turn fully green.

### Step 9 — flat ABA+ preferences (Čyras 2016)

Implement `ABAPlusFramework` dataclass and the preference-filtered
attack `attacks_with_preferences`. The dataclass embeds an
`ABAFramework`, so flatness is inherited at construction time. Modify
the semantics computers to accept either `ABAFramework` or
`ABAPlusFramework` — when the latter, they invoke the preference-
filtered attack relation rather than the unfiltered one.

Acceptance: test 3 fully green, including the §3 preferred-extension
worked example called out in this WS's SCOPE.

### Step 10 — Dung bridge for flat ABA

Implement `aba_to_dung`. Toni 2014 §5 + Toni 2012 give the bijection;
both rely on flatness, which is already guaranteed by the input type.

Acceptance: test 4 green.

### Step 11 — flat ABA ICCMA I/O

Extend `iccma.py` with `parse_aba`, `write_aba`. The parser raises
`NotFlatABAError` on non-flat input from the ICCMA file format,
consistent with the dataclass gate.

Acceptance: test 5 green.

### Step 12 — Re-export, version bump, propstore pin

`argumentation/src/argumentation/__init__.py`: add `aba` and `adf` to
imports and `__all__`. Bump `argumentation` version per
`argumentation/pyproject.toml`. Cut release.

In propstore: bump pin in `propstore/pyproject.toml` to the new
`argumentation` version. Run propstore's full test suite — no propstore-
side change should be necessary (no propstore code consumes `aba` or
`adf` yet).

Acceptance: tests 13 and 14 green; propstore CI green on the bumped
pin.

### Step 13 — Close gaps and gate (both repos, paired sentinels)

- In `argumentation`: update README to include flat ABA and ADF in the
  formalism list (with the explicit "non-flat ABA out of scope"
  caveat); update `cluster-P-argumentation-pkg.md` mirror in
  propstore (this WS's source) to mark P-A.1, P-A.2, P-A.3, P-A.4 as
  closed with the upstream PR number, with a remaining open row for
  non-flat ABA pointing at the follow-up workstream.

Upstream side (argumentation):
- Flip `argumentation/tests/test_workstream_o_arg_aba_adf_done.py`
  (14a) from `xfail` to `pass`. This test lives in the **argumentation**
  repo and closes upstream behaviour.

Propstore side:
- Confirm `propstore/pyproject.toml`'s argumentation pin is on the
  post-Step-11 argumentation commit.
- Flip `propstore/tests/architecture/test_argumentation_pin_aba_adf.py`
  (14b) from `xfail` to `pass`. This test lives in **propstore** and
  closes the pin / observable-behaviour gate.
- Update this WS file's STATUS line to `CLOSED <propstore-sha>` (where
  `<propstore-sha>` is the propstore-side pin-bump commit).

Acceptance: both sentinels green in their respective repos; propstore
`gaps.md` no longer mentions ADF coverage or flat-ABA coverage. Non-flat
ABA remains open as a tracked follow-up. Per Codex 2.18, the propstore
commit cannot flip the upstream test (different repo); the upstream
commit cannot prove the propstore pin contains the fix. Both directions
are required.

## Acceptance gates

Before declaring WS-O-arg-aba-adf done, ALL must hold:

- [ ] `argumentation` repo: every test in tests 1-14 above is green on
      master.
- [ ] `argumentation` repo: full test suite green; no regressions
      against the pre-WS baseline.
- [ ] `argumentation` repo: `pyright` (or equivalent type-check) clean
      on `aba.py`, `adf.py`, `iccma.py`.
- [ ] `argumentation` repo: `aba.py` and `adf.py` each <2000 LOC. If
      either exceeds that ceiling, decompose into submodules
      (`adf/_operator.py`, `adf/_semantics.py`, etc.) before merging.
      The size ceiling is a code-review gate, not a quality gate.
- [ ] `argumentation` repo: grep audit confirms `aba.py` contains no
      code path that constructs a non-flat framework; every entry into
      `ABAFramework` flows through the `__post_init__` flatness gate.
- [ ] `argumentation` repo: grep audit confirms `adf.py` contains no
      `from_callable` and no `__call__` on `AcceptanceCondition`. AST
      is the only representation.
- [ ] propstore: `argumentation` pin is bumped to the new version;
      propstore CI green.
- [ ] propstore: `gaps.md` has no open rows for the findings listed
      in this WS (with non-flat ABA captured as a separate open row
      pointing at the follow-up WS).
- [ ] propstore: `WS-O-arg-aba-adf.md` STATUS line is
      `CLOSED <propstore-sha>`.
- [ ] propstore: `cluster-P-argumentation-pkg.md` annotated to mark
      flat-ABA / ADF gaps closed with upstream PR references; non-flat
      ABA remains an open row.

## Done means done

This workstream is done when **every finding in the table at the top is
closed under the flat-ABA scope**, not when "most" are closed.
Specifically:

- P-A.1 (ADF) — Brewka 2010 + 2013 + Polberg 2017 pinned by green
  tests; full Brewka 2013 operator-based stack (admissible, complete,
  preferred, stable) for arbitrary ADFs (not just bipolar); acceptance
  conditions represented as typed AST with JSON + ICCMA round-trip and
  structural link classification (D-25).
- P-A.2 (flat ABA) — Bondarenko 1997 + Toni 2014 pinned by green tests;
  flat ABA covers every Dung extension semantics over the assumption
  frame: grounded, preferred, stable, complete, naive, well-founded,
  ideal. Non-flat ABA is explicitly out of scope and captured as a
  separate follow-up workstream.
- P-A.3 (bibliographic coverage) — all four foundational papers have
  notes.md and are cited from the kernel docstrings line by line.
- P-A.4 (Q's open question) — closed by D-16 + this WS landing the
  flat-ABA + ADF kernels.

If any one of those is not true, WS-O-arg-aba-adf stays OPEN. No
"we'll get to the Polberg pin in a follow-up." Either the Polberg pin
is in this WS and green, or the WS scope statement is updated *in this
file* to remove it before declaring done.

The non-flat-ABA carve-out is a hard scope boundary, not a deferral
inside this WS. The public API has no non-flat code path; non-flat
input raises `NotFlatABAError` at the type boundary. A separate WS
(captured in `cluster-P-argumentation-pkg.md` as an open row) carries
the non-flat-ABA work — it requires distinct algorithms (assumption
sets that are themselves derivable, ABA-frame contraries that participate
in deduction) and a distinct correspondence-theory analysis.

## Papers / specs referenced

Primary:
- Bondarenko, Dung, Kowalski, Toni 1997 — "An abstract, argumentation-
  theoretic approach to default reasoning". `papers/Bondarenko_1997_*/`.
  Used for flat-ABA scope (Def 4.10).
- Toni 2014 — "A tutorial on assumption-based argumentation".
  `papers/Toni_2014_*/`. Used for flat-ABA scope (§3 flatness).
- Čyras 2016 — "ABA+: assumption-based argumentation with preferences".
  Newly retrieved per D-16; primary algorithmic reference for the flat
  ABA+ preference machinery.
- Brewka, Woltran 2010 — "Abstract Dialectical Frameworks".
  `papers/Brewka_2010_*/`.
- Brewka, Ellmauthaler, Strass, Wallner, Woltran 2013 — "Abstract
  Dialectical Frameworks Revisited". `papers/Brewka_2013_*/`.
- Polberg 2017 — "Developing the Abstract Dialectical Framework".
  697-page PhD thesis, primary algorithmic reference for the ADF
  kernel implementation and the AST-representation convention (D-25).
  Newly retrieved per D-16.

Secondary (load-bearing for correspondence proofs):
- Toni 2012 — bijection between flat ABA frameworks and Dung AFs (cited
  from the Toni 2014 tutorial; underpins `aba_to_dung`; flatness is a
  hypothesis of the bijection theorem).
- Strass 2013 — "Approximating operators and semantics for abstract
  dialectical frameworks" (cited from Brewka 2013; alternative
  presentation of the ADF operator).

Specs:
- ICCMA 2023+ ABA track grammar (for `parse_aba`/`write_aba`).
- ICCMA 2023+ ADF track grammar (for `parse_adf`/`write_adf`); the
  formula syntax round-trips through the `AcceptanceCondition` AST.

## Cross-stream notes

- **WS-O-arg-argumentation-pkg** MUST land first. The ADF Dung-bridge
  `dung_to_adf` calls into `dung.py`; a broken `dung.ideal_extension`
  would silently corrupt round-trip tests.
- **WS-O-arg-dung-extensions** (B) — runs in parallel with this WS after
  WS-O-arg-argumentation-pkg lands.
- **WS-O-arg-vaf-ranking** (C) — runs in parallel with this WS after
  WS-O-arg-argumentation-pkg lands; **must precede WS-O-arg-gradual** because
  it owns `RankingResult` (Codex 2.22).
- **WS-O-arg-gradual** (D) — depends on WS-O-arg-vaf-ranking shipping
  `RankingResult` first; not parallel with VAF/ranking. Independent of this
  WS once the upstream argumentation-pkg dependency closes.
- **WS-K** (D-8) does not yet consume flat ABA / ADF (consumes
  ASPIC+/DeLP). This WS is prerequisite for a future WS-K that
  expresses source-trust rules at the flat-ABA assumption level.
- **WS-F** (aspic-bridge) unchanged — propstore's ASPIC+ projection
  continues to use `aspic.py`. flat ABA / ADF would arrive through a
  new bridge in a future WS.
- **Future non-flat-ABA WS** (not opened) is the natural follow-on.
  Will revisit the dataclass gate, the correspondence theory, and the
  semantics computers; none of those changes are backward-compatible
  with the flat-only API this WS ships.

## What this WS does NOT do

- **Does NOT cover non-flat ABA.** ABA-frame contraries that are themselves
  derivable are out of scope; non-flat support requires a separate
  workstream. The public API hard-fails on non-flat input via
  `NotFlatABAError` at construction time. There is no
  `NotImplementedError` raised mid-computation — the boundary is the
  type, not the algorithm. (Codex 2.20.)
- Does NOT support a callable representation of acceptance conditions.
  AST is the only representation per D-25.
- Does NOT implement Bench-Capon 2003 VAFs (Group C — separate WS).
- Does NOT implement Bonzon 2016 ranking semantics (Group C).
- Does NOT implement DF-QuAD or Matt-Toni game-theoretic strength
  (Group D).
- Does NOT touch the existing HIGH bugs in the argumentation kernel —
  those are WS-O-arg-argumentation-pkg.
- Does NOT change propstore's ASPIC+ projection. The propstore-side
  consumer surface for flat ABA / ADF is left to a future WS that has
  a concrete propstore use case; merely shipping the kernels does not
  obligate propstore to consume them.
- Does NOT implement the ICCMA solver protocol (`-p DC-CO`,
  `-fo apx`, `-a` argv handling). That belongs to a separate WS that
  wraps `argumentation` as a probo-callable solver.
- Does NOT add ASP encoders for flat ABA or ADF. flat-ABA-specific ASP
  encoding (Lehtonen 2024 "Three Roads to ABA") and ADF ASP encoding
  (DIAMOND, Brewka 2013 §6) are valuable follow-ups but separate
  kernels.
- Does NOT add a SAT encoder for ADF stable. Polberg 2017 chapter on
  SAT encodings is the natural source; separate WS.
- Does NOT change the public surface of `dung.py`, `aspic.py`,
  `bipolar.py`, etc. The two new modules are siblings; they do not
  modify existing modules except for the `__init__.py` re-export and
  the additive `iccma.py` extension.
- Does NOT cover ABA dispute derivations (Toni 2014 §7) or ABA-related
  dialogue games. Captured as separate follow-up gaps.

## Scope honesty

Per `DECISIONS.md:177`, this work is "months, not weeks." Two kernels
combined are ~3000-4000 LOC (estimate from `dung.py` ~585 LOC +
`aspic.py` ~1385 LOC scaling — flat ABA closer to ASPIC, ADF closer to
Dung plus ~500 LOC for the AST substrate). Polberg's 697-page thesis
is a reference for future optimizations and extensions, not a TODO
list; the goal here is every Brewka 2013 semantics correct on the
Brewka 2013 corpus plus the one Polberg pin in test 9.

flat-ABA scope is Bondarenko 1997 + Toni 2014 + Čyras 2016 §3: complete
kernel for flat frameworks under all classical Dung-style semantics,
with preferences. Non-flat ABA, ABA dispute derivations (Toni 2014 §7),
and ABA dialogue games are out of scope; captured as follow-up gaps in
`cluster-P-argumentation-pkg.md`. This WS is FLAT-ABA-ONLY, and the
public API enforces that boundary mechanically (`NotFlatABAError` at
the type boundary) rather than via a runtime `NotImplementedError`.
