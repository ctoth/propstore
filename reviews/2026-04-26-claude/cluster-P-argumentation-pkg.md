# Cluster P: argumentation package (../argumentation)

Reviewed: `C:\Users\Q\code\argumentation\` at HEAD on 2026-04-26.
24 source modules under `src/argumentation/`, ~8780 LOC. Tests
skimmed for black-box coverage; not run.

## Scope

This review covers the package implementation only — not the
propstore bridge (Cluster D) and not propstore consumers
(other clusters). I read every module under
`C:\Users\Q\code\argumentation\src\argumentation\`, the
`pyproject.toml`, `README.md`, and walked the `tests/`
directory to confirm coverage hints. I cite findings by
absolute file path and line number; no test was executed.

The package self-describes as a "finite, citation-anchored
Python library for formal argumentation" with the explicit
non-goals (`README.md:559-564`) of application provenance,
calibration, subjective-logic opinions, persistent storage,
repository workflow, and CLI. Those non-goals matter: they
delimit what should be in the package, and they predict what
propstore must own. The boundary holds in code, with one
naming exception flagged below.

## Architecture overview (modules and their roles)

`src/argumentation/__init__.py` (43 lines) re-exports 17
named submodules. Three further submodules are private to the
probabilistic stack: `probabilistic_components`,
`probabilistic_dfquad`, `probabilistic_treedecomp`.

Module roles, with line counts and primary references:

| Module | LOC | Role | Source |
| --- | ---: | --- | --- |
| `dung.py` | 585 | Dung AF dataclass + 9 extension semantics | Dung 1995, Caminada 2011, Gaggl-Woltran 2013, Dung-Mancarella-Toni 2007 |
| `dung_z3.py` | 293 | Z3 backend for complete/preferred/stable | Same |
| `labelling.py` | 127 | 3-valued labelling container | Caminada 2006 (advertised) |
| `iccma.py` | 71 | `p af n` text I/O | ICCMA format spec |
| `semantics.py` | 155 | Generic dispatch over Dung/bipolar/partial | — |
| `sat_encoding.py` | 130 | CNF encoding of stable + truth-table enumerator | — |
| `solver.py` | 182 | Typed solver-result wrappers | — |
| `preference.py` | 82 | Strict-partial-order closure + Modgil-Prakken Defs 19/22 | M&P 2018 |
| `aspic.py` | 1385 | ASPIC+ kernel: language, rules, contrariness, build, attack, defeat | M&P 2018, Prakken 2010 |
| `aspic_encoding.py` | 199 | ASP-style fact encoding + grounded reference solver | Lehtonen et al. 2024 (advertised) |
| `aspic_incomplete.py` | 110 | Exact completion-enumeration over unknown premises | Odekerken/Borg/Bex |
| `bipolar.py` | 327 | Cayrol-style bipolar AF + d/s/c admissibility | Cayrol-Lagasquie-Schiex 2005 |
| `partial_af.py` | 424 | Partial AF with completions + Coste-Marquis merges | Coste-Marquis et al. 2007 |
| `af_revision.py` | 361 | Baumann kernels + Diller revisions + Cayrol classification | Baumann 2014/15, Diller 2015, Cayrol 2014 |
| `weighted.py` | 157 | Dunne 2011 β-grounded extensions | Dunne et al. 2011 |
| `ranking.py` | 171 | Categoriser + Burden numbers | Bonzon 2016 (subset) |
| `gradual.py` | 329 | Potyka quadratic-energy + Shapley impacts | Potyka 2018, Al Anaissy 2024 |
| `value_based.py` | 156 | Subjective filter for ASPIC+ inputs | Wallner et al. 2024 |
| `accrual.py` | 141 | Weak/strong applicability over labellings | Prakken 2019 |
| `probabilistic.py` | 1419 | PrAF dispatch across 6 strategies | Li 2012, Hunter-Thimm 2017, Popescu-Wallner 2024 |
| `probabilistic_treedecomp.py` | 1663 | Min-degree TD + grounded DP + paper-faithful Popescu-Wallner | Popescu-Wallner 2024 |
| `probabilistic_dfquad.py` | 222 | DF-QuAD strengths over QuAD/BAF graphs | Freedman et al. 2025 |
| `probabilistic_components.py` | 47 | Connected-component decomposition | Hunter-Thimm 2017 |

Cross-module dependency direction is consistent: `dung.py`
is leaf; `dung_z3.py`, `sat_encoding.py`, `solver.py`,
`labelling.py`, `iccma.py`, `ranking.py`, `weighted.py`,
`gradual.py`, `bipolar.py`, `partial_af.py` all depend only on
`dung.py`. `semantics.py` depends on `dung`, `bipolar`,
`partial_af`. `aspic.py` depends on `dung` (TYPE_CHECKING) and
`preference.py` (transitively). `aspic_encoding`,
`aspic_incomplete`, `value_based`, `accrual` sit above ASPIC.
The probabilistic stack depends on `dung`. No cycles. No
imports from propstore or any application layer.

`__init__.py` is just a re-export list with no top-level
side effects. Clean.

## Dung extension semantics coverage matrix

| Semantics | Implemented | Backends | Tested | File:line |
| --- | --- | --- | --- | --- |
| grounded | yes | brute (lfp of F) | yes | `dung.py:196` |
| complete | yes | brute, z3 | yes | `dung.py:239`, `dung_z3.py:187` |
| preferred | yes | brute (filter complete), z3 | yes | `dung.py:279`, `dung_z3.py:232` |
| stable | yes | brute, z3, CNF (truth-table) | yes | `dung.py:302`, `dung_z3.py:138`, `sat_encoding.py:55` |
| naive | yes | brute | hint via `test_dung.py` | `dung.py:468` |
| semi-stable | yes | brute (range-max over complete) | hint | `dung.py:363` |
| stage | yes | brute only | hint | `dung.py:378` |
| cf2 | yes | brute (recursive SCC) | hint | `dung.py:523` |
| ideal | yes (BUG, see below) | brute | hint | `dung.py:543` |
| eager (Caminada 2007) | YES | `argumentation.dung.eager_extension` | propstore pin `c941fe4` | Closed by WS-O-arg-dung-extensions (`04281337`) |
| stage2 (Gaggl 2012/2013) | YES | `argumentation.dung.stage2_extensions` | propstore pin `c941fe4` | Closed by WS-O-arg-dung-extensions (`04281337`) |
| prudent / strongly admissible | YES | `argumentation.dung.prudent_*` | propstore pin `c941fe4` | Closed prudent extension surface; strongly admissible remains a successor if requested |
| resolution-based grounded (Baroni-Giacomin) | NO | — | — | — |

The brute paths uniformly enumerate `2^n` subsets (`dung.py:339`,
`combinations(sorted(args), size)` patterns). The auto threshold
to switch to z3 is hard-coded at `_AUTO_BACKEND_MAX_ARGS = 12`
(`dung.py:53`); it applies only to `complete`, `preferred`,
`stable`. `semi-stable`, `stage`, `cf2`, `ideal`, `naive`
remain brute-only regardless of size.

The Z3 stack covers only `complete`/`preferred`/`stable`
(`solver.py:108`). For everything else, the only escape from
exponential brute force is to write a SAT/ASP encoder oneself.
Given Tang 2025 and Lehtonen 2020 are in the bibliography and
both give well-defined polynomial encodings for semi-stable,
stage, and others, this is a substantive gap.

There is no SCC-recursive solver for any semantics other than
CF2. The Baroni-Giacomin SCC-recursive schema (Baroni 2005, in
scope) is not implemented.

## ASPIC+ kernel coverage

`aspic.py` is the largest file in the package (1385 lines) and
implements the foundational c-SAF machinery from Modgil &
Prakken 2018 and Prakken 2010. What is present:

- Logical language: `GroundAtom`, `Literal` with structural
  `.contrary` (`aspic.py:25-81`).
- Contrariness function with directional contraries and
  symmetric contradictories; `is_conflicting` correctly
  combines both directions (`aspic.py:84-134`).
- `Rule` dataclass with `kind ∈ {"strict", "defeasible"}` and
  optional `name` for undercutting (`aspic.py:137-162`).
- `KnowledgeBase` with `K_n`/`K_p` split, `ArgumentationSystem`
  bundling language/contrariness/rules, `PreferenceConfig`
  with comparison ∈ {elitist, democratic} and link ∈ {last,
  weakest} (`aspic.py:276-309`).
- Three argument constructors `PremiseArg`, `StrictArg`,
  `DefeasibleArg` with cached hashes (`aspic.py:165-254`).
- Transposition closure with degeneracy filter, full Prakken
  Def 5.1 fixpoint (`aspic.py:375-461`).
- `strict_closure`, `is_c_consistent` over closures
  (`aspic.py:464-512`).
- Bottom-up `build_arguments` with c-consistency filter and
  acyclicity check via `all_concs` (`aspic.py:673-767`).
- Goal-directed `build_arguments_for` with depth-limited
  backward chaining and reinstatement-fixpoint expansion
  (`aspic.py:792-980`).
- Three attack kinds and `compute_attacks` with
  conclusion-indexed candidate pruning
  (`aspic.py:986-1094`).
- `compute_defeats` with M&P Def 9 preference filtering;
  contrary attacks always succeed; contradictory rebut/undermine
  uses `_strictly_weaker` (`aspic.py:1237-1296`).
- `_set_strictly_less` covers Eli/Dem boundary cases for
  empty sets (`aspic.py:1100-1156`).
- `_strictly_weaker` covers last-link and weakest-link with
  the firm/strict special cases (`aspic.py:1159-1234`).
- `build_abstract_framework` returns
  `ASPICAbstractProjection` with mutual ID maps
  (`aspic.py:1311-1349`); collapses multi-attacks to set-based
  Dung defeats correctly via frozenset.
- `CSAF` packaging (`aspic.py:1355-1385`).

What is missing from a paper-faithful kernel:

- Well-formedness checker (M&P 2018 Def 11): no enforcement
  that the system is well-defined before reasoning. `CSAF`
  doc claims well-formedness but no validator runs.
- Axiom consistency check (M&P Def 13): not exposed as a
  function.
- Rationality postulate verification (Caminada-Amgoud 2007):
  no explicit `closure_under_strict_rules`,
  `direct_consistency`, `indirect_consistency`,
  `sub_argument_closure` predicates.
- The `_literal_id = repr(literal)` pattern in
  `aspic_encoding.py:165` is brittle (see "Bugs" below).
- ASPIC+ argument *complexity* signals (e.g., last-rule
  count, depth) are not exposed; useful for debugging.

`aspic_encoding.py` claims to encode ASPIC+ theories into a
"deterministic ASP-style fact vocabulary" following Lehtonen,
Niskanen & Järvisalo 2024. The encoding's structural shape
matches the paper, but several executable details fail:

- `_literal_id(literal)` returns `repr(literal)`
  (`aspic_encoding.py:165`). For a negated literal, `repr` is
  `~p`. For a propositional atom, it is the bare symbol. For
  a parameterised atom, it is `p(1, 2)`. None of these are
  valid clingo identifiers in fact arguments. The encoding
  cannot be loaded into a real ASP solver as advertised.
- `defeasible_rule_ids` (`aspic_encoding.py:176-180`) keys
  the dict by `rule.name or f"d_{index}"`. The `Rule`
  dataclass does not enforce name uniqueness, and two
  defeasible rules with the same name silently overwrite the
  earlier entry — facts lose information without warning.
- `encode_aspic_theory` does not call
  `transposition_closure` (`aspic_encoding.py:46-101`); if
  the caller forgets to pre-transpose, the encoded theory
  diverges from the c-SAF reference.
- `solve_aspic_with_backend` returns a typed
  `ASPICQueryResult` with `status="unavailable_backend"`
  instead of raising. Clean degraded-mode contract; this is
  a strength.

`aspic_incomplete.py` enumerates `2^|unknown|` completions
exhaustively (`aspic_incomplete.py:53`). Single-semantics
(grounded only). For 20 unknown premises this is ~1M
completions, each rebuilding arguments and solving grounded
from scratch. No early termination once `relevant` status is
provable, no SAT-driven existential reasoning. The
status-vocabulary `stable / relevant / unknown / unsupported`
matches Odekerken-Borg-Bex 2023.

## Bipolar / weighted / ranking / gradual / ADF / ABA coverage

### Bipolar (Cayrol 2005, Amgoud 2008)

`bipolar.py` implements:

- `BipolarArgumentationFramework` with disjoint
  arguments/defeats/supports.
- Support closure, supported targets, Cayrol derived defeats
  (supported and indirect) to fixpoint
  (`bipolar.py:100-149`).
- `set_defeats`, `set_supports`, `support_closed`, conflict-
  free, `safe`, `defends`.
- `d_admissible`, `s_admissible`, `c_admissible` per Cayrol
  Defs 9-11.
- Maximal-set computation for `d_preferred_extensions`,
  `s_preferred_extensions`, `c_preferred_extensions`.
- Stable extensions (Cayrol Def 8).

What is missing:

- Bipolar grounded and bipolar complete (no fixed-point of
  any bipolar characteristic function).
- Amgoud 2008 bipolarity types (deductive/necessary support,
  evidence-based support) are not represented as distinct
  support modes — only Cayrol abstract supports.
- QBAF / QuAD as a typed structured object (it appears only
  inside `probabilistic_dfquad.py`).
- Cayrol 2013 deductive bipolar.

Performance: `_maximal_sets` (`bipolar.py:278-292`) calls
each predicate per subset, and `defends` rebuilds
`_defeat_closure` and the attacker index every call
(`bipolar.py:226-229`). For `n` arguments this is
`n × 2^n` redundant closure rebuilds. A single hoisted
closure would be a one-line optimisation.

### Weighted (Dunne 2011, Bench-Capon 2003)

`weighted.py` implements one thing: Dunne's `β`-grounded
extensions by enumerating `2^|attacks|` deletion subsets
under a budget (`weighted.py:81-113`). Companion function
`minimum_budget_for_grounded_acceptance` is identical brute
search (`weighted.py:116-135`).

Current status after WS-O-arg-vaf-ranking:

- Dunne's α and γ measures (only β here).
- Coste-Marquis weighted preferred / stable.
- Bench-Capon 2003 Value-Based Argumentation Frameworks are
  now implemented in `vaf.py` and propstore pins upstream
  commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908`.
  `value_based.py` was deleted and the Wallner-2024 ASPIC+
  surface moved to `subjective_aspic.py`.
- Residual Bench-Capon pp. 438-447 algorithms remain open:
  argument chains, lines of argument, parity classifications,
  two-value cycle corollaries, and fact-as-highest-value
  uncertainty handling.

### Ranking (Amgoud 2013, Bonzon 2016)

Closed by WS-O-arg-vaf-ranking. `ranking.py` now exposes the
seven scoped ranking semantics under the typed `RankingResult`
contract: Categoriser, Burden, Discussion-based, Counting,
Tuples-based, h-Categoriser, and Iterated-graded. `ranking_axioms.py`
exposes the Amgoud 2013 axiom predicate suite. Propstore pins
upstream commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908`
and proves the surface in
`tests/architecture/test_argumentation_pin_vaf_ranking.py`.

`gradual.py` still owns its separate convergence contract and is
left for WS-O-arg-gradual, which consumes `RankingResult`.

### Gradual (Potyka 2018, Al Anaissy 2024, Rago 2016)

`gradual.py` implements:

- `WeightedBipolarGraph` with `[0,1]` initial weights, disjoint
  attacks/supports.
- Quadratic-energy strength fixed-point with Potyka's
  `h(x) = max(x,0)^2 / (1 + max(x,0)^2)` aggregation
  (`gradual.py:86-139`).
- Revised direct impact via attack vs argument removal
  (`gradual.py:147-204`, Al Anaissy Def 12).
- Exact Shapley attack impact via coalition enumeration
  (`gradual.py:207-258`, Al Anaissy Def 13).

Missing:

- Rago 2016 discontinuity-free QuAD (in scope) — the
  probabilistic stack ships DF-QuAD but the core gradual
  module exposes only Potyka quadratic.
- EulerB / squared-product semantics (Amgoud-Ben Naim).
- Sampled / approximate Shapley fallback for large fan-in;
  current implementation is `2^n_attacks` energy
  fixed-points each (`gradual.py:257`).

### ADF (Brewka 2010, Brewka 2013)

CLOSED by WS-O-arg-aba-adf. The `argumentation` package now
ships `adf.py` with typed acceptance-condition ASTs,
JSON/ICCMA formula round-trip, three-valued operator
semantics, Brewka 2013 reduct-based stable semantics,
structural link classification, and Dung bridge coverage.
Propstore pins upstream commit
`9887559a75c595bfcb0042adcafbf8ddedcb6ac6`; Propstore
evidence is `tests/architecture/test_argumentation_pin_aba_adf.py`.

### ABA (Bondarenko 1997, Toni 2014)

CLOSED for flat ABA by WS-O-arg-aba-adf. The
`argumentation` package now ships `aba.py` with assumptions,
contraries, forward derivability, attack/defence/extension
semantics, flat ABA+ preference-aware attack, ICCMA ABA
round-trip, and an argument-level Dung bridge that preserves
joint-support attacks. Non-flat ABA remains explicitly open
as a separate feature; the public constructor raises
`NotFlatABAError` instead of admitting a partial runtime path.

## I/O formats (ICCMA, apx, tgf)

`iccma.py` implements only the `p af n` numeric format used
since ICCMA 2019:

```
p af 3
1 2
2 3
```

`parse_af` (`iccma.py:8`) and `write_af` (`iccma.py:41`).
Strict validation: header required, attack lines must be
two numeric ids in `1..n`, comments via `#`. Round-trip
preserves attacks. Argument identifiers must be string
representations of `1..n` in `write_af` (`iccma.py:65-68`).

What is missing for being a real ICCMA participant:

- TGF (Trivial Graph Format): historically used by ICCMA
  before 2019; many third-party tools still consume it. Not
  present.
- The ICCMA solver protocol: `argv` parsing for `-p` problem
  string (`DC-CO`, `DS-PR`, `EE-ST`, `SE-CF2`, ...), `-fo`
  format selector, `-a` argument query token, witness
  output formatting per solver category. Without this the
  package cannot be wrapped as a probo-callable solver.
- APX format (ASPARTIX-style `arg(a). att(a, b).`): not
  present. APX is the lingua franca of much of the ASP-based
  argumentation community (Lehtonen 2020 in scope) and would
  let the package interoperate with clingo/ASP solvers.
- DIMACS CNF emission for the SAT encoding — `sat_encoding.py`
  ships a `CNFEncoding` dataclass but no `to_dimacs(text)`
  exporter, so the encoding can only be consumed by the
  built-in truth-table enumerator.

## Algorithmic correctness — bugs

These are concrete defects observed in source. Severity ranked.

### Severity: wrong result on legitimate input

**1. `dung.py:582-585` — `ideal_extension` returns the union of
multiple set-maximal admissible candidates.**

```python
if len(maximal) == 1:
    return maximal[0]

result: frozenset[str] = frozenset()
for candidate in maximal:
    result = result | candidate
return result
```

Per Dung-Mancarella-Toni 2007 Def 2.2, the ideal extension
is the unique maximal *admissible* set contained in every
preferred extension. The code first builds `candidates` as
admissible subsets of the intersection of preferred
extensions, then takes set-maximal of those (`dung.py:563-577`).
If the intersection has more than one set-maximal admissible
subset, the code falls into the `for candidate in maximal:
result = result | candidate` branch. The union of two
admissible sets is not guaranteed admissible — admissibility
is not closed under union. The returned "ideal extension"
may then violate admissibility, breaking the spec.

The fact that the comment claims "the unique maximal ideal
extension" while the fallback returns a union demonstrates
the author already noticed the multiplicity issue but chose
the wrong resolution. The correct resolution is that ideal
admissible sets ARE closed under union under the
intersection-of-preferreds restriction (this is the content
of Dung-Mancarella-Toni Theorem 2.1) — but only if the
union itself is admissible. The code does not verify
admissibility of the union before returning.

**2. `aspic_encoding.py:165` — `_literal_id = repr(literal)`
generates IDs that are not valid ASP identifiers.**

```python
def _literal_id(literal: Literal) -> str:
    return repr(literal)
```

`Literal.__repr__` (`aspic.py:78-81`) returns `~p` for
negated literals or `p(1, 2)` for parameterised atoms. The
encoder then writes `axiom(~p).` or `s_body(s_0,p(1, 2)).` —
neither parses in clingo (`~` is the strong-negation prefix
in some dialects only with whitespace handling, and
parameterised atom syntax must use commas without spaces).
The package documents the encoding as "ASP-style facts
following Lehtonen 2024" (`aspic_encoding.py:25`), but the
strings as emitted are not valid ASP. Real interoperation
with clingo or any KR-style solver would require sanitising
literals into legal symbols (e.g., `n_p`, `p_1_2`) and
maintaining a reverse map.

**3. `aspic_encoding.py:179` — silent rule-name collision.**

```python
def _defeasible_rule_ids(rules: frozenset[Rule]) -> dict[Rule, str]:
    named: dict[Rule, str] = {}
    for index, rule in enumerate(sorted(rules, key=repr)):
        named[rule] = rule.name or f"d_{index}"
    return named
```

If two distinct defeasible rules share the same `name`, both
get assigned the same identifier. The `Rule` dataclass does
not enforce name uniqueness across `R_d`. Downstream
`s_head` / `d_head` facts then conflate distinct rules.
Detection should raise on duplicate names.

### Severity: classification / boundary

**4. `af_revision.py:301-325` — `_classify_extension_change`
fall-through.**

The function distinguishes seven Cayrol-de-Saint-Cyr-
Lagasquie-Schiex 2010 change kinds via cardinality
comparisons. Several cases have ambiguous overlap and the
ordering may misclassify:

- `len(after) == 1 and (not before or before == (frozenset(),)
  or len(before) > 2)` (`af_revision.py:315`) handles
  "decisive" only when `before` has 0 or 3+ extensions. For
  `len(before) == 2, len(after) == 1` the decisive branch
  is skipped, the `len(before) > len(after) >= 2` branch
  needs `len(after) >= 2` so it is also skipped, and the
  case falls through to `ALTERING`. Cayrol 2010 Table 3 may
  classify this as restrictive or decisive depending on
  whether the surviving extension is a subset of one of the
  originals. The classification ignores extension content
  and uses cardinality only — which is insufficient for the
  full table.

- `EXPANSIVE` (`af_revision.py:323`): requires every old
  extension to be strictly contained in some new extension
  AND `len(after) == len(before)`. The cardinality
  constraint is suspicious; expansive change usually does
  not require equal cardinality.

The full Cayrol classification table operates on subset
relations between before and after extensions, not just
cardinalities. The current code may produce wrong labels.

**5. `af_revision.py:60-92` — `ExtensionRevisionState`
materialises the ranking dict over all `2^n` subsets in
`__post_init__`.**

```python
all_extensions = self.all_extensions(self.arguments)
...
faithful_ranking = {
    candidate: 0 if candidate in extension_set else max(...)
    for candidate, rank in self.ranking.items()
}
```

For 20 arguments this is `2^20 = ~1M` entries; for 30 it is
`~1B`. Memory and construction time both blow up. There is
no lazy evaluation. Diller-2015 revision is conceptually
defined over the full extension lattice, so the encoding
choice is paper-faithful, but the explicit materialisation
makes the code unusable beyond toy examples (~15 args).

### Severity: brittleness / contract drift

**6. `preference.py:58` — `strictly_weaker` returns False for
either empty set without documenting why.**

```python
if not set_a or not set_b:
    return False
```

`aspic.py:1100-1156` (`_set_strictly_less`) handles the
boundary cases explicitly: empty `gamma` is never less,
non-empty `gamma` is less than empty `gamma_prime`. The
two implementations therefore disagree on
`(non-empty, empty)`: `_set_strictly_less` says True,
`strictly_weaker` says False. They are not equivalent
helpers despite parallel signatures. `defeat_holds`
(`preference.py:67`) uses the disagreeing one. ASPIC+
defeat reasoning routes through `_strictly_weaker` in
`aspic.py`, not `defeat_holds`, so the inconsistency may
not manifest — but any caller importing `preference.py`
directly will get a different ordering than the ASPIC+
internals use.

**7. `sat_encoding.py:91` — `stable_extensions_from_encoding`
enumerates by truth-table.**

```python
for mask in range(1 << len(variable_ids)):
    true_variables = frozenset(
        variable for index, variable in enumerate(variable_ids)
        if mask & (1 << index)
    )
    if _satisfies(encoding.clauses, true_variables):
        ...
```

The module presents itself as a "pure SAT/CNF encoding"
(`sat_encoding.py:1`) but the included reference enumerator
is brute-force over `2^n` assignments. For any nontrivial
framework this defeats the purpose of having a CNF encoding.
The data structure is suitable for handing to a real SAT
solver — but no DIMACS exporter is provided.

**8. `semantics.py:149` — partial-AF "skeptical" naming
overload.**

```python
skeptical = set(extension_sets[0])
for extension in extension_sets[1:]:
    skeptical.intersection_update(extension)
```

For `PartialArgumentationFramework`, `extensions(...)` is
the union of extensions across all completions
(`semantics.py:106-111`). Intersecting these gives
*necessary skeptical acceptance* (Baumeister/Coste-Marquis
2013): accepted in every extension of every completion. The
literature distinguishes this from *possible skeptical
acceptance*: accepted in every extension of some
completion. The dispatcher exposes only the former under the
name "skeptical", with no flag for the latter. Callers
relying on the standard partial-AF terminology will get the
wrong semantics.

**9. `probabilistic.py:42-46` — `_z_for_confidence` brittle.**

```python
_Z_SCORES = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
def _z_for_confidence(confidence: float) -> float:
    if confidence in _Z_SCORES:
        return _Z_SCORES[confidence]
    raise ValueError(...)
```

Any user supplying `0.9501`, `0.999`, `0.95000001`, or any
float that fails dict-equality on a hard-coded literal gets
a hard error. The right design is `scipy.stats.norm.ppf(1 -
(1 - c) / 2)` — but the package is dependency-free. A
simple polynomial inverse-CDF approximation would suffice;
hard-coding three values is not OK for a quantitative API.

### Severity: design smell / efficiency

**10. `bipolar.py:226-229` — `defends` rebuilds the defeat
closure on every call.** `_maximal_sets` calls predicates per
subset → `n × 2^n` redundant closure rebuilds. Trivial
hoist available.

**11. `weighted.py:97` — enumerates `2^|attacks|` deletion
subsets.** Intractable beyond ~25 attacks.

**12. `aspic.py:519-628` — module-level `@functools.cache`
on `conc`, `prem`, `sub`, `def_rules`, `last_def_rules`,
`prem_p`, `_set_strictly_less`, `_strictly_weaker`.**
Caches are process-wide, only cleared explicitly inside
`build_arguments` and `build_arguments_for`
(`_clear_argument_function_caches()`). `compute_attacks`
and `compute_defeats` do not clear them; concurrent use
from different threads with overlapping `Argument` instances
would race on the cache mutation. Single-threaded use is
fine. Long-running test sessions (Hypothesis) accumulate
without bound until a fresh `build_*` call clears.

**13. `dung.py:413` — `_strongly_connected_components` uses
recursive Tarjan.** For deep AFs this hits Python's default
recursion limit (~1000). No iterative variant.

**14. `dung.py:259-274` — `complete_extensions` brute path
checks both `characteristic_fn(s) == s` AND `admissible(s)`
for every subset.** For `n` = 12 (the auto threshold) this
is `2^12 = 4096` subsets, each scanning all defeats. No
incremental admissibility check.

## Boundary cleanliness vs propstore consumer

The package boundary is clean and well-defended in code:

- README "Non-goals" (`README.md:559-564`) explicitly
  disclaims application provenance, source calibration,
  subjective-logic opinion calculi, persistent storage,
  repository workflow, and CLI. propstore must own all of
  these — and the `argumentation/__init__.py` import surface
  exposes nothing in those directions.
- `semantics.py` accepts only argumentation-owned dataclasses
  (`semantics.py:120-126`); refuses unknown types. propstore
  must convert its rows to these objects before invoking
  the dispatcher. Good.
- `ASPICQueryResult` returns `status="unavailable_backend"`
  rather than raising on missing optional dependencies
  (`aspic_encoding.py:138-162`). Clean contract for
  propstore to surface degraded modes.
- The `dataclass(frozen=True)` discipline is consistent.
  Immutability lets propstore safely cache/compare without
  defensive copies.
- Probabilities are plain floats in `[0, 1]`
  (`README.md:406-408`); propstore is expected to project
  subjective opinions or beta posteriors before invoking
  the kernel. README documents this contract explicitly.

The one boundary smell is `aspic_encoding.py`: the
"backend" plumbing (`solve_aspic_with_backend`) sits in the
package but the only registered backend is the in-package
materialised reference projection. propstore-side ASP /
clingo backends would attach via this surface, but the
contract for *registering* a backend is not exposed —
there is no `register_backend(name, fn)` function. The
seam is half-built.

## Missing features the literature reaches further on

Concrete features named in the bibliography but absent from
the package:

- **Non-flat ABA** — flat ABA is now implemented and guarded
  at the constructor boundary, but non-flat ABA remains a
  separate feature requiring distinct closure/correspondence
  analysis.
- **Bench-Capon 2003 VAF follow-up** — VAF/AVAF defeat and
  acceptance are closed by WS-O-arg-vaf-ranking, but the paper's
  pp. 438-447 line-of-argument and fact-uncertainty algorithms
  remain unimplemented.
- **Caminada 2006 labelling-as-semantics** (paper in scope)
  — `labelling.py` ships only a passive container with
  `from_extension`. There is no `legally_in`/`legally_out`
  predicate, no admissible-/complete-/grounded-labelling
  characterisation, no operational labelling-based solver
  (Modgil-Caminada). Caminada 2007 is also in scope; eager
  semantics is not implemented.
- **ICCMA solver protocol** (Järvisalo 2025, Niskanen 2020
  in scope) — only AF text I/O ships. No problem-string
  parsing, witness output, query argument handling. The
  package cannot be a probo-callable solver as is.
- **TGF / APX** — neither file format is supported.
- **SAT encodings beyond stable** (Tang 2025, Mahmood 2025
  in scope) — `sat_encoding.py` covers stable only.
  Polynomial encodings exist for complete, preferred,
  semi-stable, stage, and the package does not implement
  them.
- **ASP encoding for plain Dung** (Lehtonen 2020, Charwat
  2015 in scope) — only the ASPIC+-side encoder
  (`aspic_encoding.py`) exists, and its identifier scheme is
  invalid ASP (see bug #2). No `dung_to_asp` exporter.
- **Tree-decomposition / FPT for plain Dung** (Dvořák 2012,
  Fichte 2021 in scope) — the TD machinery in
  `probabilistic_treedecomp.py` is restricted to the
  probabilistic stack. No `tw_grounded`, `tw_preferred`
  for vanilla Dung AFs.
- **Stage2 / Eager / Resolution-based grounded / Prudent**
  — none of these alternative semantics ship.
- **Bipolar grounded / complete** — only d/s/c preferred and
  stable.
- **Bonzon 2016 ranking semantics beyond Categoriser/Burden**
  — no Tuples-based, h-Categoriser, Discussion-based,
  Trust-based.
- **Amgoud 2013 ranking-axiom predicates** — the axioms
  (Abstraction, Independence, etc.) are not exposed as
  testable predicates.
- **Game-theoretic argument strength** (Matt-Toni 2008 in
  scope) — not implemented.
- **DF-QuAD discontinuity-free strength** in the core
  gradual module (Rago 2016 in scope) — only used inside the
  probabilistic dfquad path; `gradual.py` ships Potyka
  quadratic only.
- **Equational approach** (Gabbay 2012 in scope) — not
  implemented.
- **AF dynamics beyond add-argument classification** (Cayrol
  2014 covered; Alfano 2017, Oikarinen 2010 strong-equivalence
  in scope) — kernel-based equivalence is not implemented.
- **Weighted alpha/gamma** (Dunne 2011) — only beta.
- **Coste-Marquis symmetric AFs** (paper in scope) — no
  symmetry-aware fast paths.
- **Persuasion / dialogue / deliberation games** (Prakken
  2006, McBurney 2009, Bench-Capon, Walton 2015) — out of
  scope candidate; reasonable to leave to a separate
  package.
- **Argument mining** (Stab 2016, Mayer 2020) — clearly out
  of scope for a finite-formal kernel.
- **Argumentative XAI** (Čyras 2021, Freedman 2025
  ArgLLMs) — clearly out of scope.

## Open questions for Q

1. **Ideal extension semantics:** The union fallback at
   `dung.py:582-585` returns a non-admissible set whenever
   the intersection of preferred extensions has more than one
   admissible-maximal subset. Do you want me to file this as
   a bug for the argumentation maintainer, or mark it as
   known-broken in the propstore bridge that calls it?

2. **ASP encoding strategy:** `aspic_encoding.py` cannot be
   consumed by clingo as written (`_literal_id = repr`
   generates invalid ASP identifiers, `~`, `(`, `,`, ` `).
   Do you want propstore to implement a sanitising wrapper
   over the encoded facts, or push for the encoder to fix
   the identifier scheme upstream?

3. **ICCMA participation:** The package has the algorithmic
   substrate (Dung semantics, AF I/O) to be wrapped as a
   probo-callable ICCMA solver, but lacks the protocol layer
   (`-p DC-CO -fo apx -a a3` style argv handling, witness
   output formatting). Is propstore the right place to add a
   thin CLI shim, or should it live in the argumentation
   package?

4. **ABA / ADF coverage:** Bondarenko 1997, Toni 2014, Brewka
   2010, Brewka 2013 are all in propstore's bibliography
   under the argumentation track. Is propstore meant to use
   ABA/ADF formalisms, and if so are these expected to land
   in `argumentation` (as new modules) or to be implemented
   propstore-side?

5. **Caminada labelling solver:** `labelling.py` is a passive
   container. Caminada 2006 is in scope and gives an
   operational labelling-based grounded/preferred/stable
   solver that is much faster than subset enumeration. Do
   you want propstore to depend on labelling-as-semantics, or
   is the current extension-only API sufficient?

6. **value_based.py naming:** CLOSED by WS-O-arg-vaf-ranking.
   The Wallner 2024 ASPIC+ subjective filtering module is now
   `subjective_aspic.py`, and Bench-Capon VAF support lives in
   `vaf.py`.

7. **ExtensionRevisionState memory blowup
   (`af_revision.py:60`):** materialises ranking over `2^n`
   subsets in `__post_init__`. Used anywhere in propstore
   that could exceed ~15 args? If yes this needs lazy
   evaluation immediately.

8. **Process-wide `@functools.cache` on `aspic.py:519-628`:**
   any concurrent or multi-system test usage in propstore
   could see stale or unbounded cache state. Acceptable
   risk, or should propstore call
   `_clear_argument_function_caches` (private) explicitly?

---

Files inspected (absolute paths):

- `C:\Users\Q\code\argumentation\src\argumentation\__init__.py`
- `C:\Users\Q\code\argumentation\src\argumentation\dung.py`
- `C:\Users\Q\code\argumentation\src\argumentation\dung_z3.py`
- `C:\Users\Q\code\argumentation\src\argumentation\labelling.py`
- `C:\Users\Q\code\argumentation\src\argumentation\iccma.py`
- `C:\Users\Q\code\argumentation\src\argumentation\semantics.py`
- `C:\Users\Q\code\argumentation\src\argumentation\sat_encoding.py`
- `C:\Users\Q\code\argumentation\src\argumentation\solver.py`
- `C:\Users\Q\code\argumentation\src\argumentation\preference.py`
- `C:\Users\Q\code\argumentation\src\argumentation\aspic.py`
- `C:\Users\Q\code\argumentation\src\argumentation\aspic_encoding.py`
- `C:\Users\Q\code\argumentation\src\argumentation\aspic_incomplete.py`
- `C:\Users\Q\code\argumentation\src\argumentation\bipolar.py`
- `C:\Users\Q\code\argumentation\src\argumentation\partial_af.py`
- `C:\Users\Q\code\argumentation\src\argumentation\af_revision.py`
- `C:\Users\Q\code\argumentation\src\argumentation\weighted.py`
- `C:\Users\Q\code\argumentation\src\argumentation\ranking.py`
- `C:\Users\Q\code\argumentation\src\argumentation\gradual.py`
- `C:\Users\Q\code\argumentation\src\argumentation\value_based.py`
- `C:\Users\Q\code\argumentation\src\argumentation\accrual.py`
- `C:\Users\Q\code\argumentation\src\argumentation\probabilistic.py`
- `C:\Users\Q\code\argumentation\src\argumentation\probabilistic_components.py`
- `C:\Users\Q\code\argumentation\src\argumentation\probabilistic_treedecomp.py` (skim)
- `C:\Users\Q\code\argumentation\pyproject.toml`
- `C:\Users\Q\code\argumentation\README.md`
