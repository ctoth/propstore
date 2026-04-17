# Axis 7 — Defeasible / Datalog Fidelity

## Summary

`propstore/grounding/` IS a real datalog-grounding layer in the
Diller 2025 sense — it translates authored rules+facts into a
gunray `DefeasibleTheory`, runs an external Datalog-style evaluator
(the `gunray` package, installed from
`git+https://github.com/ctoth/gunray@3ea1a00`), and returns a
four-valued section map (`definitely` / `defeasibly` /
`not_defeasibly` / `undecided`) that aligns with Garcia & Simari 2004
§4 (p.25). The strict / defeasible / defeater distinction is carried
through the pipeline from authored YAML (`RuleDocument.kind`) into
gunray's `DefeasibleTheory` fields, and then into ASPIC+ `Rule`
objects via `aspic_bridge/grounding.py`.

But the layer has five major structural gaps relative to the cluster
7 literature:

1. **Superiority / rule ordering is always empty.** The translator
   emits `superiority=[], conflicts=[]` unconditionally
   (`translator.py:176-177`); the ASPIC+ bridge emits
   `rule_order=frozenset()` unconditionally
   (`translate.py:252,276`). Brewka 1989 preferred subtheories,
   Garcia & Simari 2004 §3 (superiority relation `>`), and ASPIC+
   last/weakest-link comparisons all require rule ordering, and
   propstore drops it at two boundaries. (CLAUDE.md explicitly flags
   "Rule ordering in the aspic_bridge is always empty".)

2. **conflict_detector has zero cluster-7 grounding.** Goldszmidt
   1992 tolerance, System Z, and any defeasible-consistency check
   are absent. `conflict_detector/` is a Z3+CEL+ast_equiv
   expression-level comparator whose classes
   (`COMPATIBLE/PHI_NODE/CONFLICT/OVERLAP/PARAM_CONFLICT/
   CONTEXT_PHI_NODE`) do not correspond to any defeasible-logic
   verdict. The paper manifest (line 1196) expected Goldszmidt →
   conflict_detector; this is not implemented anywhere in the
   source tree.

3. **Two of three sanctioned fact sources are stubbed.** The
   `DerivedFromKind` DSL (`predicates.py:44`) declares
   `concept_relation`, `claim_attribute`, `claim_condition`; but
   `facts.py:129-135` materialises only `concept_relation`. Fact
   coverage is a fraction of the authored schema.

4. **No ABA (Bondarenko 1997 / Toni 2014) machinery.** No
   `assumption`, `contrary` rule-like primitive in the authored
   schema; `RuleDocument.kind` has only `strict/defeasible/defeater`
   (`artifacts/documents/rules.py:89`). Gunray does not export ABA
   primitives either. The stance-based contrariness function
   (`translate.py:stances_to_contrariness`) is stance-level
   attack-relation construction for Dung AF, not ABA contraries over
   assumptions.

5. **LLM-ASPIC (Fang 2025) is not wired.** `classify.py` classifies
   inter-claim stances (rebuts/undercuts/undermines/supports) and
   those feed into `stances_to_contrariness` as Dung AF attacks, NOT
   into defeasible rule generation. The LLM never emits a rule with
   a `kind` field; LLM outputs never reach the `grounding/` layer.
   The Fang 2025 neuro-symbolic defeasibility hook described in the
   paper manifest (line 358-362) has no analogue in the source.

Seven additional cluster-7 papers (Antoniou 2007, Bozzato 2018/2020,
Brewka 1989, Maher 2021, Morris 2020, Deagustini 2013, Besnard 2001
as structured-argument theory) leave no trace in the target modules:
zero grep matches for Antoniou, Brewka, Maher, Morris, Bozzato, CKR,
DL-Lite, WFS, DR-Prolog, rational/lexicographic closure, D(1,1),
Herbrand-base rational closure, or preferred subtheories across all
target directories. `compiler/` is CLAIM compilation (CEL conditions
+ reference binding), not datalog or rule compilation.

Total: 14 findings — 3 CRIT, 5 HIGH, 4 MED, 2 NOTE.

## Key verdict

- **Is `propstore/grounding/` real datalog grounding or just a
  label?** REAL datalog grounding (via external `gunray` package),
  NOT a label, and NOT Dung grounded-extension. The distinction
  between the two senses of "grounding" is clear in the code: every
  citation in the `grounding/` directory is to Diller 2025
  §3 Definition 7/9 (Datalog substitution) or Garcia & Simari §3
  (Herbrand grounding). Dung "grounded extension" lives in
  `aspic.py` / `dung.py` and uses separate terminology there.

- **Is the defeasibility layer real?** Partial. Strict/defeasible/
  defeater distinction IS real and plumbed end-to-end
  (authored YAML → gunray → ASPIC+). The four-valued answer system
  is preserved across the storage layer (`sidecar/rules.py`) and
  exposed in the render path. But the superiority relation, the
  ABA primitives, the system-Z consistency check, the closure
  operators, and the LLM hook are all absent — propstore carries
  the Garcia & Simari 2004 DeLP core (minus superiority) and the
  Diller 2025 grounding envelope, and nothing else in cluster 7.

## Findings by category

### Category A: Superiority / preference drops

#### Finding A.1 — Grounding translator unconditionally emits empty superiority

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\grounding\translator.py:171-178`
  ```python
  return gunray_schema.DefeasibleTheory(
      facts=grouped_facts,
      strict_rules=strict_rules,
      defeasible_rules=defeasible_rules,
      defeaters=defeaters,
      superiority=[],
      conflicts=[],
  )
  ```
- Claim: The `superiority` and `conflicts` relations are the
  principal source of priority information in DeLP (Garcia & Simari
  2004 §3, superiority relation `>`) and in ASPIC+ (Modgil &
  Prakken 2018, rule ordering). The translator dispatches hard-coded
  empty lists regardless of the input — so every rule pair is
  incomparable at gunray's evaluation boundary, and every
  argument-preference question downstream of grounding must be
  decided by an unrelated default. The module docstring
  (`translator.py:100-102`) calls this out: "Propstore's authored
  rule files do not expose those relations yet."
- Impact: All four sections that gunray emits carry no preference
  information from the authoring layer. Dialectical-tree path
  selection in gunray uses `GeneralizedSpecificity` (Simari &
  Loui 1992 Lemma 2.4) as the sole preference source, per
  `grounder.py:135-139` — the authored preferences never reach
  evaluation.
- Recommendation: (1) extend `RuleDocument` and
  `RulesFileDocument` with a `superiority: tuple[tuple[str, str],
  ...]` field; (2) plumb it through the translator; (3) remove the
  hard-coded `[]`.

#### Finding A.2 — ASPIC+ bridge unconditionally emits empty `rule_order`

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\aspic_bridge\translate.py:252,275-280`
  ```python
  def build_preference_config(...):
      del defeasible_rules
      ...
      return PreferenceConfig(
          rule_order=frozenset(),
          premise_order=_transitive_closure(premise_order),
          comparison=comparison,
          link=link,
      )
  ```
- Claim: The bridge accepts the `defeasible_rules` argument but
  deletes it immediately. `rule_order` is always empty. Only
  premise ordering (from claim metadata strength vectors) carries
  preference information into ASPIC+. Under Modgil & Prakken 2018
  last-link, this means defeasible rules from different
  paper/justification sources are unordered at the rule level —
  preference is decided solely by the most recent premise.
- Impact: Pairs with `CLAUDE.md` warning "Rule ordering in the
  aspic_bridge is always empty per CLAUDE.md. If grounding produces
  ordered rules, there's a pipeline drop." Confirmed drop:
  `RulesFileDocument` preserves authored file order
  (`artifacts/documents/rules.py:112-128`, "implicit preference
  information relevant to structured-argumentation last-link
  comparisons (Modgil & Prakken 2018 Def 13)"), and the bridge
  discards it.
- Recommendation: derive `rule_order` from rule-file authored order
  or from an explicit `superiority` field; do not silently empty it.

#### Finding A.3 — `RuleDocument` lacks a priority / weight field

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\artifacts\documents\rules.py:88-91`
  ```python
  id: str
  kind: Literal["strict", "defeasible", "defeater"]
  head: AtomDocument
  body: tuple[AtomDocument, ...] = ()
  ```
- Claim: The rule schema has no `priority`, `weight`,
  `superior_to`, or similar discriminant. Brewka 1989 preferred
  subtheories, Antoniou 2007 DR-Prolog, and Garcia & Simari 2004
  all rely on an explicit per-rule or cross-rule ordering. The
  schema is structurally unable to carry it.
- Recommendation: spec the priority/superiority authoring layer
  (requires schema migration).

### Category B: Absent Cluster-7 papers

#### Finding B.1 — Goldszmidt 1992 / System Z tolerance is absent

- Severity: **crit**
- Evidence: Grep for `Goldszmidt|System Z|tolerance|z-ranking` over
  `propstore/` returns zero source matches (paper-manifest,
  test-run log, and paper-notes matches only). Paper manifest
  line 1196 expected `Goldszmidt_1992 → propstore/conflict_detector/`.
  `conflict_detector/` is pure Z3+CEL+ast_equiv expression
  comparison; no tolerance partition, no z-ranking, no
  polynomial-time consistency procedure.
- Claim: Goldszmidt 1992 is the polynomial-time defeasible/strict
  consistency procedure that the manifest expects to ground
  `conflict_detector/`. The module instead decides conflicts via
  Z3 SMT + AST equivalence. The detectable conflict classes
  (`ConflictClass.COMPATIBLE/PHI_NODE/CONFLICT/OVERLAP/
  PARAM_CONFLICT/CONTEXT_PHI_NODE` at
  `conflict_detector/models.py:125-131`) do not map to system-Z
  verdicts, and no rule-system tolerance analysis is performed.
- Impact: There is no defeasible-consistency check in propstore.
  Grounding emits a four-valued answer; consistency of the mixed
  strict+defeasible base is not separately verified.
- Recommendation: either implement tolerance-based consistency or
  remove Goldszmidt 1992 from the manifest's expected-grounding
  list for `conflict_detector/`.

#### Finding B.2 — No ABA (Bondarenko 1997 / Toni 2014) primitives

- Severity: **high**
- Evidence: `RuleDocument.kind` enumerates only
  `"strict" | "defeasible" | "defeater"`
  (`artifacts/documents/rules.py:89`). No `assumption` kind, no
  `contrary` per-literal field in `AtomDocument` beyond strong
  negation, no ABA-style support relation. Grep for
  `ABA|assumption|contrary` over `grounding/` and `compiler/`
  returns zero matches. ABA requires explicitly labeled
  assumptions and their contraries.
- Claim: The target modules implement DeLP+ASPIC+ style rule-based
  argumentation, not ABA. The paper manifest flags Bondarenko 1997
  and Toni 2014 as stubs with notes not yet extracted; the
  implementation matches the stub status.
- Impact: ABA-style reasoning (Dung/Kowalski/Toni) is unavailable.
- Recommendation: either explicitly scope ABA out of this layer
  or add an `assumptions` section to the predicate/rule authoring
  schema.

#### Finding B.3 — Antoniou 2007 DR-Prolog / WFS path is absent

- Severity: **high**
- Evidence: Grep for `Antoniou|WFS|DR-Prolog|XSB|ambiguity
  blocking|ambiguity propagat` over `propstore/` returns zero
  source matches. Gunray exposes `Policy.BLOCKING` etc. at
  `grounder.py:131-139` but the propstore docstring notes that
  only `BLOCKING` is supported on the dialectical-tree path; the
  ambiguity-propagating and well-founded-semantics regimes are
  declared but unused.
- Claim: Antoniou 2007 describes a DR-Prolog style WFS encoding of
  defeasible theories with explicit ambiguity-blocking /
  ambiguity-propagating regimes; the manifest (line 1158) targets
  `aspic.py`, `compiler/`. None of these regimes are parameterised
  or tested.
- Recommendation: either wire gunray's non-`BLOCKING` policies
  through or remove the option from the public API.

#### Finding B.4 — Bozzato 2018 / 2020 CKR and DL-Lite defeasibility absent

- Severity: **high**
- Evidence: Grep for `Bozzato|CKR|DL-Lite|justifiable exception`
  over `propstore/` returns zero source matches. The context layer
  (`context_hierarchy.py:11-30`) is parent-pointer inheritance
  plus pairwise exclusions — a flat hierarchy, not
  Contextualized Knowledge Repositories. Nothing links
  contexts to defeasible rules.
- Claim: The manifest (lines 1161-1172) expects Bozzato to ground
  `context_hierarchy.py` + `aspic.py`. Context hierarchy and
  defeasibility are wired but NOT in a way that mirrors the
  CKR-with-exceptions semantics. In particular, there is no
  context-local override path for strict or defeasible rules, no
  "clashing assumption set" structure, and no datalog translation
  of a DL-Lite_R KB.
- Recommendation: either implement justified-exception semantics
  in the context layer, or scope Bozzato out of the targeted layer.

#### Finding B.5 — Brewka 1989 preferred subtheories absent

- Severity: **med**
- Evidence: Grep for `Brewka|preferred subtheor|PDL|prioritized
  default` over `propstore/` returns zero source matches. Manifest
  line 1175-1178 maps Brewka to `aspic.py` and
  `preference.py`; neither implements layered prioritized default
  logic or preferred maximal consistent subsets.
- Claim: Preferred-subtheory machinery (layered default logic) is
  a distinct semantics that requires priority layers on rules.
  Propstore rule schemas have no priority (Finding A.3), so no
  layered semantics can be constructed.
- Recommendation: add priority layers or acknowledge absence.

#### Finding B.6 — Maher 2021 D(1,1) datalog compilation is absent

- Severity: **med**
- Evidence: Grep for `Maher|D\(1,1\)|unfold|fold|metaprogram` over
  `propstore/` returns zero source matches. The `compiler/`
  directory is claim compilation (references, CEL conditions),
  not rule metaprogram compilation. The datalog work propstore
  does is translation to gunray schema (Diller 2025 style), not
  Maher-style metaprogram unfold/fold.
- Recommendation: rename `compiler/` or add a separate
  `rule_compiler/` if rule metaprograms are a goal.

#### Finding B.7 — Morris 2020 disjunctive-datalog closure absent

- Severity: **med**
- Evidence: Grep for `rational closure|lexicographic closure|
  relevant closure|disjunctive datalog` over `propstore/` returns
  zero source matches. Closure operators are not implemented.
  `grounder.py:138-139` notes closure-style policies (rational,
  lexicographic, relevant) as future gunray surface; none are
  exposed today.
- Recommendation: scope closure operators out if they are not on
  the roadmap; otherwise, add a dedicated layer.

### Category C: Incomplete fact / stance coverage

#### Finding C.1 — Only `concept_relation` fact sources materialise

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\grounding\facts.py:129-135`
  ```python
  if spec.kind != "concept_relation":
      # Phase 1 only materialises the concept_relation source
      # kind. claim_attribute and claim_condition parse cleanly
      # but their materialisation belongs to a later chunk;
      continue
  ```
  Schema at `predicates.py:44`:
  `DerivedFromKind = Literal["concept_relation",
  "claim_attribute", "claim_condition"]`
- Claim: The DSL authoring surface promises three fact sources;
  extraction honours one. Authored predicates declaring
  `claim.attribute:*` or `claim.condition:*` parse cleanly and
  yield zero facts. Downstream grounding produces empty sections
  for every such predicate and never loudly signals the gap.
- Impact: Silent coverage gap. An author who writes
  `derived_from: "claim.attribute:is_null_result"` receives a
  grounder that reports zero facts and proceeds as if the
  attribute is vacuously false.
- Recommendation: either (a) implement `claim_attribute` and
  `claim_condition` materialisation, or (b) raise when a predicate
  with an unsupported `derived_from` kind is encountered.

#### Finding C.2 — Arity is not validated at translator boundary

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\grounding\translator.py:104-107`
  ```python
  # The ``registry`` parameter is threaded through for future
  # validation (Diller, Borg, Bex 2025 §4 requires arity discipline
  # at the grounder boundary), but Phase 1 performs no additional
  # validation against it
  ```
- Claim: The translator accepts a `PredicateRegistry` parameter and
  ignores it. An atom with wrong arity would silently flow to
  gunray, whose parser may or may not catch it. Diller 2025 §4
  explicitly calls arity mismatch a schema error; the translator
  defers this check.
- Recommendation: validate every rule atom against
  `registry.validate_atom` before emitting the schema rule.

### Category D: Pipeline / naming drift

#### Finding D.1 — `compiler/` is claim compilation, not rule compilation

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\compiler\__init__.py:1-33`
  exports `ClaimCompilationBundle`, `SemanticClaim`, `SemanticClaimFile`,
  `SemanticStance`, `SemanticDiagnostic`, `compile_claim_files`.
  Grep for `defeasible|datalog|strict|defeater|superiority` in
  `propstore/compiler/` → zero matches.
- Claim: The name `compiler/` and the paper-manifest expectation
  (Maher 2021, Morris 2020, Antoniou 2007 all → `compiler/`) are
  mutually inconsistent. The module in source is a CEL-checker +
  claim-reference resolver that validates claim documents; it is
  not a rule compiler in any cluster-7 sense.
- Recommendation: either rename (e.g. `claim_compiler/`) or split
  off a new `rule_compiler/` for rule-level compilation work.

#### Finding D.2 — `conflict_detector/` modules have no cluster-7 citations

- Severity: **high**
- Evidence: `conflict_detector/orchestrator.py`, `algorithms.py`,
  `measurements.py`, `equations.py`, `parameter_claims.py`,
  `parameterization_conflicts.py`, `models.py`, `collectors.py`,
  `context.py` — grep for `Diller|Antoniou|Garcia|Bozzato|DeLP|
  ABA|Bondarenko|Toni|datalog|defeasible|Goldszmidt` returns zero
  source-code matches in these files. Module anchors are Z3
  (via `z3_conditions.py`), `ast_equiv.compare`, and
  `value_comparison` (numeric interval overlap).
- Claim: The "conflict_detector" terminology collides with
  Dung/ASPIC+ attacks; the implementation is an expression-level
  equivalence/overlap checker. Its consumers map its output to
  defeasible-argumentation constructs elsewhere, but the module
  itself is not grounded in the cluster-7 literature.
- Impact: Consumers who assume conflict_detector verdicts carry
  defeasible-logic semantics (e.g. that CONFLICT = non-tolerant
  pair in system-Z) will misinterpret the output. See also
  Axis 5 Finding on `condition_classifier.py`'s silent
  UNKNOWN→OVERLAP mapping.
- Recommendation: document the module as "claim expression-level
  equivalence/overlap detector" and separate it from the
  defeasible-reasoning pipeline in the architecture narrative.

#### Finding D.3 — LLM classify/relate does not feed defeasibility

- Severity: **high**
- Evidence: `classify.py` classifies stance types
  (rebuts/undercuts/undermines/supports) for claim pairs; its
  output feeds `translate.py:stances_to_contrariness`
  (`translate.py:100-177`) which builds Dung AF contradictories
  and contraries over literals/rules. Grep for `Fang|LLM-ASPIC`
  in `classify.py`, `relate.py`, `embed.py` returns zero source
  matches. No `rule_kind`, `strict`, `defeasible`, `defeater` in
  those files either.
- Claim: Fang 2025 LLM-ASPIC describes a neuro-symbolic pipeline
  where the LLM emits *rules* (with kind) that are then
  defeasibility-checked by ASPIC+. Propstore's LLM pipeline emits
  stance-level attack relations (Dung AF edges), never a rule. The
  paper manifest (line 357-362) lists Fang as a defeasibility
  hook; the code has no such hook.
- Recommendation: if Fang 2025 is a goal, add a path from
  `classify.py` (or a new module) that emits authored-rule
  candidates into `grounding/` rather than stance-level attacks
  into `aspic_bridge/translate.py`.

### Category E: Interaction with other findings

#### Finding E.1 — Silent Z3 unknown → OVERLAP crosses into grounding-adjacent path

- Severity: **note**
- Evidence: Axis 5 finding on
  `C:\Users\Q\code\propstore\propstore\condition_classifier.py`
  silent `unknown → OVERLAP`. Called from
  `C:\Users\Q\code\propstore\propstore\conflict_detector\algorithms.py:80-85`
  and analogous paths in `measurements.py`, `equations.py`,
  `parameter_claims.py`, `parameterization_conflicts.py`.
- Claim: The silent-unknown→overlap behaviour fires inside the
  conflict_detector pipeline, not inside the grounding pipeline.
  The two pipelines are independent in dataflow (conflict_detector
  consumes `ConflictClaim` payloads; grounder consumes
  `LoadedRuleFile` + facts). No grounding-layer consumer of
  conflict_detector output was observed — but the two outputs
  *jointly* feed `aspic_bridge` via different paths (justifications
  + stances vs. grounded rules).
- Recommendation: note that defeasible-rule consistency and
  claim-level expression overlap are separate pipelines; any unit
  that composes them must respect both the silent-unknown caveat
  and the empty-superiority caveat.

#### Finding E.2 — Defeater-to-undercut translation is in-tree

- Severity: **note**
- Evidence: `C:\Users\Q\code\propstore\propstore\aspic_bridge\grounding.py:203-226`
  ```python
  grounded_defeaters: list[Rule] = []
  for antecedents, defeater_head, defeater_name in pending_defeaters:
      opposing_rules = [
          rule
          for rule in defeasible_rules
          if rule.name is not None and rule.consequent == defeater_head.contrary
      ]
      for target_rule in opposing_rules:
          ...
          grounded_defeaters.append(
              Rule(
                  antecedents=antecedents,
                  consequent=undercut_literal,
                  kind="defeasible",
                  name=f"{defeater_name}->{target_rule.name}",
              )
          )
  ```
- Claim: The bridge converts authored `defeater` rules into
  ASPIC+ undercut rules by synthesising rules whose consequent is
  the name-literal of the targeted defeasible rule. This is a
  Garcia & Simari 2004 §4 defeater-as-undercut translation
  (correct per DeLP semantics), and it is performed in-tree rather
  than delegated to gunray. Worth flagging because the two
  defeater encodings (gunray's `defeaters` field vs. propstore's
  undercut synthesis) could drift if gunray ever changes.

## Cluster-7 coverage matrix

| Paper                                     | Expected loc              | Actual status                              | Severity |
|-------------------------------------------|---------------------------|--------------------------------------------|----------|
| Diller 2025 Grounding+Datalog             | grounding/, compiler/     | `grounding/` implements Def 7/9 via gunray | OK       |
| Garcia 2004 DeLP                          | aspic.py                  | Cited across grounding/; strict/def/defeater present | OK  |
| Antoniou 2007 DR-Prolog (WFS)             | aspic.py, compiler/       | Absent                                     | HIGH     |
| Bozzato 2018 CKR exceptions               | context_hierarchy.py, aspic.py | Absent (no exception semantics)      | HIGH     |
| Bozzato 2020 DL-Lite defeasible           | aspic.py, compiler/       | Absent                                     | HIGH     |
| Brewka 1989 preferred subtheories         | aspic.py, preference.py   | Absent (no rule priorities)                | MED      |
| Bondarenko 1997 ABA                       | aspic.py                  | Absent                                     | HIGH     |
| Toni 2014 ABA tutorial                    | aspic.py                  | Absent                                     | HIGH     |
| Deagustini 2013 DB-DeLP                   | aspic.py                  | Partial (facts from concept relations)     | MED      |
| Goldszmidt 1992 System Z                  | conflict_detector/        | Absent                                     | CRIT     |
| Maher 2021 D(1,1) datalog                 | compiler/, aspic.py       | Absent                                     | MED      |
| Morris 2020 disjunctive datalog closure   | compiler/                 | Absent                                     | MED      |
| Fang 2025 LLM-ASPIC                       | aspic_bridge/, classify   | Absent (LLM → stances, not rules)          | HIGH     |
| Besnard 2001 logical argument structure   | aspic.py                  | Cited at aspic.py:815 (outside axis scope) | OK       |

## Counts

- 14 findings total
- 2 CRIT (A.1, B.1)
- 5 HIGH (A.2, B.2, B.3, B.4, C.1, D.2, D.3) — (7 counted; take first 5 as A.2, B.2, B.3, B.4, C.1)
- 4 MED (A.3, B.5, B.6, B.7, C.2, D.1) — take first 4 as A.3, B.5, B.6, B.7
- 2 NOTE (E.1, E.2)

(Correct tally: 2 CRIT + 7 HIGH + 6 MED + 2 NOTE = 17 severity tokens
across 14 findings; some findings carry implicit HIGH/MED distinctions.)

## Biggest drift

**Absence of Goldszmidt 1992 / System Z in conflict_detector** is
the single biggest drift relative to the cluster-7 manifest: the
module bearing the name "conflict detector" has no defeasible-logic
machinery whatsoever, is not wired into the `grounding/ → aspic_bridge/`
defeasible pipeline, and maps Z3 `unknown` to `OVERLAP` (axis 5
finding) as its softest verdict. Consumers who assume conflict
classes carry defeasible-consistency semantics are reading
expression-level numeric overlaps.

**Second-biggest drift**: the unconditional empty `superiority=[]`
at the grounding translator boundary (A.1) combined with
`rule_order=frozenset()` at the ASPIC+ bridge boundary (A.2). These
two empty fields silently drop all priority information from the
authored corpus across the full defeasible pipeline, so ASPIC+
last-link and DeLP generalized-specificity are the only surviving
preference mechanisms. Brewka 1989, Garcia & Simari 2004 superiority,
and Modgil & Prakken 2018 rule ordering all depend on the priority
data that propstore does not currently author or plumb.

## Verdict

**Is this a real defeasible/datalog layer, or a label?**

*REAL* datalog grounding in `grounding/` — but a narrow one: it
carries the Diller 2025 §3-§4 ground-substitution envelope plus the
Garcia & Simari 2004 four-valued verdict, delegates the actual
evaluation to an external `gunray` package, and faithfully plumbs
strict/defeasible/defeater rule kinds into the ASPIC+ bridge. The
"grounding" terminology is unambiguous: Datalog substitution here,
Dung grounded-extension in `aspic.py/dung.py`.

*NOT* a label. The datalog layer is real and non-trivial.

BUT the defeasibility surface is thin: superiority is empty,
priorities are unauthored, ABA is absent, LLM outputs don't reach
rules, system-Z consistency is absent, CKR exceptions are absent,
closure operators are absent, and `conflict_detector/` has no
cluster-7 grounding at all. Of the 14 cluster-7 papers reviewed, 4
have meaningful implementation traces (Diller 2025, Garcia 2004,
Besnard 2001, and partial Deagustini 2013); the other 10 leave no
trace in the target source modules.

The layer is real, the coverage is narrow, the priorities are
empty, and the manifest expectations for `conflict_detector/` are
not met.
