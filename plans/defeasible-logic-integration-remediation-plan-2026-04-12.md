# Defeasible Logic Integration Remediation Plan

Superseded on 2026-04-14 by
`plans/defeasible-reasoning-workstream-2026-04-14.md`.

Date: 2026-04-12
Updated: 2026-04-13

## Scope

This plan resolves the current defeasible-logic integration issues:

1. The grounded-rule path is implemented in the translator/grounder/bridge corridor but is not wired into normal product entrypoints.
2. Strong negation is still missing as an implemented feature on the propstore grounding path.
3. The public projection surface drops grounded arguments even when the bridge builds them.

This is a target-architecture plan, not a migration plan. We control both sides of these interfaces, so the plan changes the interfaces, updates every caller, and deletes the old silent-empty behavior.

## Literature Basis Consulted

I reread the relevant pages from local page images, not extracted paper text.

- `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-002.png`
- `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-003.png`
- `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/pngs/page-004.png`
- `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-003.png`
- `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-004.png`
- `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-029.png`
- `papers/Garcia_2004_DefeasibleLogicProgramming/pngs/page-030.png`
- `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-006.png`
- `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-007.png`
- `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-008.png`

The points that matter for implementation:

- Diller 2025 pages 3-4: the grounded theory is a deterministic function of the argumentation theory plus fact base. Grounding is not an optional sidecar decoration; it is part of the theory identity.
- Garcia & Simari 2004 pages 98-99: a DeLP program consists of facts, strict rules, and defeasible rules; strong negation is part of the language of literals.
- Garcia & Simari 2004 pages 124-125: default negation is distinct from strong negation and must not be collapsed into it.
- Modgil & Prakken 2018 pages 8-9: the argumentation system and its arguments are defined over the full logical language and full rule base, not only over authored top-level claims.

## Current Repo Facts

- The tested grounding corridor exists:
  - `propstore/grounding/translator.py`
  - `propstore/grounding/grounder.py`
  - `propstore/aspic_bridge.py`
- The normal product facade still erases grounding by passing `GroundedRulesBundle.empty()` in:
  - `propstore/structured_projection.py`
- Normal callers still use that facade:
  - `propstore/world/resolution.py`
  - `propstore/worldline/argumentation.py`
  - `propstore/repo/structured_merge.py`
  - `propstore/cli/compiler_cmds.py`
- Strong negation is no longer silently erased. The translator now fails loudly on `AtomDocument.negated=True`.
- The missing feature is therefore full strong-negation support, not repair of a silent rewrite bug.
- `StructuredProjection` currently filters out any argument whose conclusion is not an authored claim id.

## Current Conformance Facts

The implementation order should now start from the conformance surface in `..\datalog-conformance-suite`, then move downward into gunray/propstore internals.

- The suite already contains defeasible strong-negation cases, not just placeholders.
- The existing YAML surface already uses heads like:
  - `~flies(X)`
  - `~fly(X)`
  - `~p`
  - `~a`
- Relevant current corpus slices:
  - `src/datalog_conformance/_tests/defeasible/basic/depysible_birds.yaml`
  - `src/datalog_conformance/_tests/defeasible/basic/bozzato_example1_bob.yaml`
  - `src/datalog_conformance/_tests/defeasible/superiority/maher_example2_tweety.yaml`
  - `src/datalog_conformance/_tests/defeasible/superiority/maher_example3_freddie_nonflight.yaml`
  - `src/datalog_conformance/_tests/defeasible/ambiguity/antoniou_basic_ambiguity.yaml`
  - `src/datalog_conformance/_tests/defeasible/closure/morris_core_examples.yaml`
  - `src/datalog_conformance/_tests/defeasible/klm/morris_relevant_counterexamples.yaml`
- The suite runner already exercises `theory` cases per policy through:
  - `tests/test_conformance.py`
  - `src/datalog_conformance/runner.py`
- The suite docs already define the workstream discipline for ambiguity and closure in:
  - `docs/POLICY_AND_CLOSURE_WORKSTREAMS.md`
- The suite docs already treat concrete evaluator adapters as the right forcing boundary:
  - `docs/IMPLEMENTATIONS.md`

This changes the correct execution order. The missing feature should be implemented from the conformance suite upward:

1. force the external evaluator contract to express the target semantics,
2. make gunray satisfy that external contract,
3. make propstore consume that evaluator surface correctly,
4. wire the grounded theory into real product entrypoints.

## Target Architecture

### 1. Make grounding a required reasoning input

The reasoning boundary must take a real grounded context, not synthesize emptiness internally.

Target state:

- `build_structured_projection(...)` requires a grounded input instead of constructing `GroundedRulesBundle.empty()` itself.
- All ASPIC-facing callers supply grounding explicitly.
- The only valid uses of `GroundedRulesBundle.empty()` are unit tests and explicitly rule-free reasoning scenarios.

Implementation shape:

1. Add a repository-level grounding loader module that constructs:
   - loaded concepts
   - loaded predicate files / `PredicateRegistry`
   - loaded rule files
   - extracted facts
   - grounded bundle
2. Put that loader at the knowledge/repository boundary, not inside `aspic_bridge.py`.
3. Thread the bundle through:
   - `build_structured_projection`
   - world resolution
   - worldline capture
   - structured merge
   - compiler CLI flows
4. Delete the current silent-empty wrapper behavior.

Rationale:

- Diller 2025 treats grounding as part of theory construction, so the normal reasoning path must receive the grounded theory that corresponds to the actual repository state.

### 2. Implement strong negation correctly end-to-end

The current boundary is now safe but incomplete: propstore rejects strong negation instead of translating it.

Target state:

- Strong negation from `RuleDocument` survives translation into gunray.
- Strong-negated grounded atoms from gunray are normalized back into ASPIC negative literals, not treated as predicate names beginning with `~`.
- Default negation remains deferred and continues to fail loudly until its semantics are implemented.

Implementation shape:

1. Conformance-first forcing surface:
   - Add or activate a gunray-backed conformance run against the existing defeasible corpus in `..\datalog-conformance-suite`.
   - Start from the already-authored strong-negation cases in `defeasible/basic` and `defeasible/superiority`.
   - Require green behavior there before widening the propstore product call path.
2. Translator:
   - Change atom stringification so `AtomDocument.negated=True` renders with gunray's `~predicate(...)` syntax.
   - Add tests for strong-negated heads and body literals.
3. Grounder / bridge normalization:
   - Introduce a single normalization function for gunray predicate keys and ground atoms:
     - `~flies(tweety)` from gunray becomes `Literal(atom=GroundAtom("flies", ("tweety",)), negated=True)` on the ASPIC side.
     - Do not encode strong negation as `GroundAtom(predicate="~flies", ...)`.
   - Use that normalization consistently in:
     - grounded fact injection
     - grounded rule generation
     - query-goal parsing
     - contrariness / conflict handling
4. Conflict semantics:
   - Map strong-negated predicate pairs into explicit contraries/contradictories at the bridge boundary.
   - Do not rely on string prefix conventions beyond the gunray adapter boundary.
5. Keep `negative_body` as a hard failure until the extended-DeLP path is designed. Garcia 2004 pages 124-125 makes that separation non-optional.

Rationale:

- Garcia & Simari distinguishes strong negation from default negation.
- `../gunray` already has parser and evaluator support for `~predicate(...)`, so the correct target is full support, not permanent refusal.

### 3. Replace claim-only projection with full argument projection

`StructuredProjection` is currently too narrow for the grounded-language path. The bridge can build arguments over the full language, but the projection surface throws away any argument whose conclusion is not an authored claim id.

Target state:

- The public projection surface represents every argument in the CSAF.
- Claim-linked arguments carry claim linkage explicitly.
- Non-claim grounded literals are first-class projected arguments with a canonical literal/conclusion key.
- Claim-only consumers filter intentionally on top of this surface instead of receiving an already-truncated graph.

Implementation shape:

1. Replace the current claim-only projection schema with a general argument projection schema.
2. Each projected argument should carry:
   - `arg_id`
   - canonical conclusion key
   - `claim_id | None`
   - top-rule kind
   - support / dependency metadata
   - subargument ids
3. Rebuild framework filtering over the full projected argument set.
4. Add a separate helper for claim-only views if needed by UI or reporting code.
5. Remove the current filter that drops non-claim conclusions.

Rationale:

- Modgil & Prakken defines arguments over the full language, not over a claim-id subset.
- This also removes the current dangling-subargument problem caused by keeping `subargument_ids` that can point to filtered-out grounded arguments.

## Concrete Workstreams

### Workstream A: Conformance Surface First

Files and repos likely involved:

- `..\datalog-conformance-suite\src\datalog_conformance\_tests\defeasible\basic\*.yaml`
- `..\datalog-conformance-suite\src\datalog_conformance\_tests\defeasible\superiority\*.yaml`
- `..\datalog-conformance-suite\tests\test_conformance.py`
- `..\datalog-conformance-suite\src\datalog_conformance\runner.py`
- gunray conformance adapter surface

Deliverables:

- one reproducible conformance command that runs gunray against the current defeasible corpus
- an explicit focused tranche for strong-negation-bearing defeasible cases
- a pinned passing/failing baseline before propstore-side changes start

Acceptance gate:

- propstore work does not start by inventing new internal tests for the missing feature first
- the first forcing surface is the existing public conformance corpus

### Workstream B: Strong Negation Semantics

Files likely involved:

- `propstore/grounding/translator.py`
- `propstore/grounding/grounder.py`
- `propstore/aspic_bridge.py`
- gunray conformance adapter / gunray-facing normalization code
- tests in `tests/test_grounding_translator.py`
- tests in `tests/test_grounding_grounder.py`
- tests in `tests/test_aspic_bridge_grounded.py`
- tests in `tests/test_gunray_integration.py`
- focused conformance invocations against `..\datalog-conformance-suite`

Deliverables:

- strong-negated rules survive translation
- grounded `~predicate` results normalize to ASPIC negative literals
- querying a strong-negated grounded literal works
- default negation still raises loudly

### Workstream C: Grounding Load Boundary

Files likely involved:

- new grounding loader module
- `propstore/structured_projection.py`
- `propstore/world/resolution.py`
- `propstore/worldline/argumentation.py`
- `propstore/repo/structured_merge.py`
- `propstore/cli/compiler_cmds.py`

Deliverables:

- one canonical function to build the bundle from repo state
- no production caller silently using `GroundedRulesBundle.empty()`
- integration tests from real product entrypoints

### Workstream D: Projection Surface Cutover

Files likely involved:

- `propstore/structured_projection.py`
- `propstore/aspic_bridge.py`
- downstream consumers of `StructuredProjection`
- tests for projection, resolution, worldline, merge, and review regressions

Deliverables:

- projection contains all arguments, not just authored-claim conclusions
- claim-linked and non-claim arguments coexist in one typed surface
- no dangling `subargument_ids`

## Test Plan

1. Keep the current grounding corridor green:
   - translator
   - grounder
   - grounded bridge
   - gunray integration
2. Add conformance-driven strong-negation checks first:
   - run the existing defeasible corpus in `..\datalog-conformance-suite` against gunray
   - create a named strong-negation tranche from the current YAML corpus
   - require that tranche to pass before wiring product callers
3. Add product-entrypoint tests proving a real repository-backed bundle is used in:
   - resolution
   - worldline argumentation
   - structured merge
   - compiler CLI ASPIC path
4. Add strong-negation tests:
   - `~flies(X)` rule translation
   - `~flies(tweety)` in grounded sections
   - bridge/query handling of negative literals
5. Add projection cutover tests:
   - full projected graph contains grounded non-claim arguments
   - claim-only helpers still work where needed
   - no projected subargument reference points outside the projected graph

All pytest runs should use:

- `uv run pytest -vv`
- full output logged under `logs/test-runs/`

## Execution Order

1. Conformance surface first
2. Strong negation semantics
3. Grounding load boundary
4. Full projection cutover
5. Real-caller integration tests

That order keeps the architecture coherent:

- first force the externally visible defeasible semantics at the existing conformance boundary,
- then implement the missing strong-negation feature behind that boundary,
- then make the real system receive the right grounded theory,
- then expose the resulting arguments on the public projection surface.

## Explicit Non-Goals

- Do not add compatibility shims that preserve the old silent-empty bundle behavior.
- Do not silently rewrite default negation into strong negation or positive literals.
- Do not treat sidecar grounded sections as the authority for rebuilding arguments unless the sidecar also becomes authoritative for the full grounded theory identity. For now, the simplest correct path is to compute the grounded bundle from repository inputs at the load boundary.
