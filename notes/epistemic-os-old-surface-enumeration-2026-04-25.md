# Epistemic OS Old Surface Enumeration

Date: 2026-04-25
Workstream: `plans/epistemic-os-workstreams-2026-04-25.md`

Purpose: satisfy the WS0 readiness gate requiring concrete old surfaces from
the current tree before deeper WS1/WS2 rewrites. This is an enumeration only;
it does not delete or rewrite these surfaces.

## Commands

```powershell
rg -n -F "predicate" propstore tests docs proposals plans
rg -n -F "ground" propstore tests docs proposals plans
rg -n -F "0.5" propstore tests docs proposals plans
rg -n -F "context" propstore/context_lifting.py propstore tests docs proposals plans
rg -n -F "def build_grounded_bundle" propstore
rg -n -F "def grounding_bundle" propstore
rg -n -F "contexts_visible_from" propstore
rg -n -F "create_grounded_fact_table" propstore tests
rg -n -F "class PredicateDocument" propstore
rg -n -F "class AtomDocument" propstore
rg -n -F "PredicateRegistry" propstore tests
rg -n -F "parse_derived_from" propstore tests
rg -n -F "DerivedFromSpec" propstore tests
rg -n -F "GroundAtom" propstore tests
```

## Predicate and Rule Authoring Surfaces

- `propstore/families/documents/predicates.py:44`:
  `PredicateDocument` declares authored DeLP/Datalog predicate names, arity,
  argument types, and `derived_from`.
- `propstore/families/documents/predicates.py:96`:
  `PredicatesFileDocument.predicates` is the authored predicate-file envelope.
- `propstore/families/documents/rules.py:43`:
  `AtomDocument` stores `predicate: str` as the authored rule atom symbol.
- `propstore/cli/predicate/__init__.py`,
  `propstore/cli/predicate/display.py`, and
  `propstore/cli/predicate/mutation.py` are the public predicate authoring CLI
  presentation surface.
- `propstore/predicate_files.py` owns loaded predicate-file envelopes used by
  the grounding path.
- `propstore/contract_manifests/semantic-contracts.yaml` still contains the
  `predicate_file` artifact family and the `predicates` semantic family.

## Grounding Registry and Projection Surfaces

- `propstore/grounding/predicates.py:107`:
  `DerivedFromSpec` represents the old `derived_from` DSL tags:
  `concept_relation`, `claim_attribute`, and `claim_condition`.
- `propstore/grounding/predicates.py:161`:
  `parse_derived_from()` parses the string DSL.
- `propstore/grounding/predicates.py:271`:
  `PredicateRegistry` maps authored predicate ids to signatures.
- `propstore/grounding/facts.py:65`:
  `extract_facts()` emits backend `GroundAtom` instances from current
  propstore rows and `DerivedFromSpec`.
- `propstore/grounding/translator.py:82`:
  `build_defeasible_theory()` consumes `PredicateRegistry` and `GroundAtom`
  facts.
- `propstore/grounding/grounder.py:78`:
  `ground_rules()` consumes backend `GroundAtom` facts and predicate registry
  signatures.
- `propstore/grounding/loading.py:74`:
  `build_grounded_bundle()` loads predicate files, rule files, source facts,
  defeasible theory, and grounded rules directly from repository inputs.
- `propstore/grounding/inspection.py:213`:
  `parse_query_atom()` exposes query text as a backend `GroundAtom`.

## Backend Atom Identity Surfaces

- `propstore/aspic_bridge/grounding.py:81` and `:104` convert authored rule
  atoms into ASPIC `GroundAtom` values.
- `propstore/aspic_bridge/grounding.py:293` projects grounded fact table rows
  back into ASPIC `GroundAtom` values.
- `propstore/aspic_bridge/translate.py:41`, `:119`, and `:176` create ASPIC
  `GroundAtom` values from claim ids and rule names.
- `propstore/core/literal_keys.py:50` creates `GroundLiteralKey` from a backend
  `GroundAtom`.

## Sidecar Predicate-Key Storage

- `propstore/sidecar/rules.py:80`:
  `create_grounded_fact_table()` creates `grounded_fact(predicate TEXT,
  arguments TEXT, section TEXT)` and
  `grounded_fact_empty_predicate(section TEXT, predicate TEXT)`.
- `propstore/sidecar/rules.py:149`:
  `populate_grounded_facts()` writes bundle sections keyed by predicate id.
- `propstore/sidecar/rules.py:226`:
  `read_grounded_facts()` reconstructs section maps keyed by predicate id.
- `tests/test_sidecar_grounded_facts.py:240` asserts the current
  `grounded_fact` schema contains exactly `predicate`, `arguments`, and
  `section`.

## Direct Runtime Grounding Rebuild

- `propstore/world/model.py:258`:
  `WorldModel.grounding_bundle()` directly calls
  `propstore.grounding.loading.build_grounded_bundle(self._repo)` and caches
  the result.
- `propstore/world/model.py:263` through `:266` falls back to
  `GroundedRulesBundle.empty()` when no repository root is present.
- `propstore/merge/structured_merge.py:99` exposes a merge snapshot
  `grounding_bundle()` method returning `GroundedRulesBundle.empty()`.

## Context Visibility and Lifting Surfaces

- `propstore/context_lifting.py:18`:
  `ContextReference`.
- `propstore/context_lifting.py:27`:
  `IstProposition`.
- `propstore/context_lifting.py:38`:
  `LiftingRule`.
- `propstore/context_lifting.py:52`:
  `LiftingSystem`.
- `propstore/context_lifting.py:81`:
  `LiftingSystem.can_lift()`.
- `propstore/context_lifting.py:91`:
  `LiftingSystem.effective_assumptions()`.
- `propstore/context_lifting.py:100`:
  `LiftingSystem.contexts_visible_from()`.
- `propstore/core/activation.py:50` uses
  `lifting_system.contexts_visible_from(environment.context_id)`.
- `propstore/world/bound.py:245` uses
  `lifting_system.contexts_visible_from(self._context_id)`.

## Silent or Policy-Default `0.5` Surfaces

These are not all wrong. Later WS8 deletion slices must distinguish sourced
0.5 values, binary-frame policies, Hurwicz pessimism defaults, and true silent
ignorance defaults.

- `propstore/opinion.py:53`, `:88`, `:93`, `:98`, `:308`, `:333`, and `:344`
  default opinion/base-rate constructors to `0.5`.
- `propstore/calibrate.py:144`, `:165`, `:391`, `:399`, and `:443` preserve
  corpus/category fallback base-rate behavior.
- `propstore/praf/engine.py:131`, `:177`, `:237`, and `:280` read or insert
  `0.5` opinion/base-rate priors.
- `propstore/source/common.py:107` and `:113` preserve source trust prior
  defaults.
- `propstore/heuristic/source_trust.py:89` and `:95` preserve trust/prior
  defaults.
- `propstore/sidecar/schema.py:169` keeps
  `opinion_base_rate REAL DEFAULT 0.5`.
- `docs/subjective-logic.md:16` and `:24` document total ignorance as
  defaulting to base rate 0.5.
- `tests/conftest.py:364` and `:704`, `tests/test_opinion_schema.py:141`,
  and `tests/test_relate_opinions.py:87` preserve test fixtures for default
  `0.5` behavior.

## Next Deletion-Slice Implications

- WS1 relation-concept migration must not ban backend predicate strings
  globally; it must distinguish backend/projection syntax from propstore
  semantic relation identity.
- WS6/WS7 projection and grounding deletion slices own the backend
  `GroundAtom` and sidecar predicate-key cuts.
- WS5 owns replacement of context visibility/lifting behavior with situated
  assertion context lifting.
- WS8 owns removal of silent `0.5` defaults after base-rate resolver and
  unresolved-prior objects exist.
