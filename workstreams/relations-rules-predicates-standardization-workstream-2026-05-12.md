# Relations, Rules, And Predicates Standardization Workstream

Date: 2026-05-12

## Goal

Finish the semantic-artifact cutover by deleting the remaining bucket-shaped
canonical rule and predicate surfaces, then standardize the shared semantic
artifact and semantic-link architecture.

This is a test-driven, deletion-first workstream. We control Propstore,
`pks`, and the research-papers plugin workflows, so do not preserve old and new
canonical paths in parallel.

## Target Architecture

Canonical semantic units are first-class artifacts:

- one claim artifact
- one stance artifact
- one justification artifact
- one micropublication artifact
- one same-as assertion artifact
- one predicate artifact
- one rule artifact
- one rule-superiority artifact for rule-priority assertions

Typed semantic links live in the relation system:

- claim -> concept links with roles `about`, `output`, `target`, `input`
- rule -> predicate links for every head/body predicate reference
- rule-superiority -> rule links for superior/inferior rule refs
- stance -> claim links
- justification -> claim links

The public relation import surface is `propstore.core.relations`. There is no
`propstore.core.relations.kernel` public path and no
`propstore.core.claim_concept_link_roles` module.

## Non-Goals

- Do not preserve compatibility with old canonical `rules/<file>.yaml` or
  `predicates/<file>.yaml` bucket files unless the user explicitly creates an
  old-repository compatibility requirement.
- Do not add import shims, alias modules, fallback readers, or wrapper facades.
- Do not move Propstore semantic policy into Quire.
- Do not standardize boilerplate before the remaining bucket families are
  deleted.

## Execution Rules

- Work delete-first.
- Add tests that fail against the old surface before implementing each phase.
- Delete the old production surface first, then use type, import, search, and
  test failures as the work queue.
- Commit every intentional edit slice atomically with path-limited git commands.
- After every commit, reread this workstream before choosing the next edit
  slice.
- After every passing substantial targeted test run, reread this workstream
  before choosing the next edit slice.
- Do not report completion while old production paths coexist with new paths.
- Use logged pytest wrappers for tests.
- Run Python tooling through `uv`.
- If Quire changes become necessary, implement and push Quire first, then pin
  Propstore to a pushed remote commit or tag. Never pin to a local path.

## Dependency Order

Execute in this order:

1. Relations module consolidation
2. Predicate canonical artifact cutover
3. Rule canonical artifact cutover
4. Rule-superiority artifact cutover
5. Research-papers plugin and `pks` workflow updates
6. Boilerplate standardization
7. Contract, manifest, documentation, and full-suite closure

Before implementation, make this dependency order mechanically executable:
write or run an order check that proves each dependent phase appears after its
prerequisites. If the check fails, repair this workstream before editing
production code.

## Phase 1: Relations Module Consolidation

Goal: make `propstore.core.relations` the single public relation module and
move claim-concept link roles into it.

Delete-first targets:

- Delete `propstore/core/relations/kernel.py`.
- Delete `propstore/core/relations/__init__.py`.
- Delete `propstore/core/claim_concept_link_roles.py`.

Tasks:

- Replace the package `propstore/core/relations/` with a module
  `propstore/core/relations.py`.
- Move the current relation kernel domain objects into that module:
  - `RelationConceptRef`
  - `RoleBinding`
  - `RoleBindingSet`
  - `RoleDefinition`
  - `RoleSignature`
  - `RelationPropertyKind`
  - `RelationPropertyAssertion`
  - `RelationPropertySet`
  - `BOOTSTRAP_RELATION_IDS`
- Move `ClaimConceptLinkRole` and `coerce_claim_concept_link_role` into
  `propstore.core.relations`.
- Update every caller to import relation and claim-link role types from
  `propstore.core.relations`.
- Do not leave a compatibility module at the old paths.

Tests first:

- Add a boundary test that importing `propstore.core.relations.kernel` fails.
- Add a boundary test that `propstore.core.claim_concept_link_roles` does not
  exist.
- Add a public-surface test that `ClaimConceptLinkRole`,
  `RelationConceptRef`, and `RoleBindingSet` import from
  `propstore.core.relations`.

Gate:

- `rg -n "core\\.relations\\.kernel|claim_concept_link_roles" propstore tests`
  has no production or test imports except negative boundary tests.
- `uv run pyright propstore` passes.
- Logged targeted tests for relations, situated assertions, claim views, concept
  views, sidecar build, world overlay, and support revision pass.

## Phase 2: Predicate Canonical Artifact Cutover

Goal: make each `PredicateDocument` a first-class canonical artifact.

Delete-first targets:

- Delete canonical production use of `PredicatesFileDocument`.
- Delete `PREDICATE_FILE_FAMILY` as the canonical predicate family.
- Delete `PredicateFileRef` as the canonical predicate ref.
- Delete canonical `predicates/<file>.yaml` bucket placement.

Tasks:

- Add `PredicateRef` keyed by predicate id.
- Add `PREDICATE_FAMILY` whose document type is `PredicateDocument`.
- Define placement as one YAML artifact per predicate id.
- Update `pks predicate add/list/show/remove` to operate on predicate
  artifacts.
- Keep `--file` only as optional authoring metadata if still useful; it must not
  determine canonical storage.
- Update duplicate detection to run over predicate artifact ids.
- Update `PredicateRegistry.from_files` or replace it with a registry builder
  over predicate documents.
- Update grounding input loading to iterate predicate artifacts directly.
- Update proposal predicate promotion so each proposed declaration promotes to
  one predicate artifact.
- Delete canonical code that rewrites an entire predicate bucket to add/remove
  one predicate.

Tests first:

- Predicate add writes one predicate artifact.
- Predicate list/show/remove work over predicate artifacts.
- Duplicate predicate ids are rejected across artifacts.
- Grounding builds the same registry from predicate artifacts as before.
- Predicate proposal promotion creates N predicate artifacts for N declarations.
- No production path requires `PredicatesFileDocument` as canonical storage.

Gate:

- `rg -n "PredicatesFileDocument|PredicateFileRef|PREDICATE_FILE_FAMILY" propstore`
  shows no canonical production use. Source-local or deleted tests must be
  updated, not shimmed.
- Logged predicate CLI, proposal, grounding, and build tests pass.
- `uv run pyright propstore` passes.

## Phase 3: Rule Canonical Artifact Cutover

Goal: make each `RuleDocument` a first-class canonical artifact.

Delete-first targets:

- Delete canonical production use of `RulesFileDocument`.
- Delete `RULE_FILE_FAMILY` as the canonical rule family.
- Delete `RuleFileRef` as the canonical rule ref.
- Delete canonical `rules/<file>.yaml` bucket placement.

Tasks:

- Add `RuleRef` keyed by stable rule id, with source/paper metadata on the rule
  document or adjacent provenance field if needed.
- Add `RULE_FAMILY` whose document type is `RuleDocument`.
- Define placement as one YAML artifact per rule id.
- Update `pks rule add/list/show/remove` to operate on rule artifacts.
- Keep `--file` only as optional authoring metadata if still useful; it must not
  determine canonical storage.
- Update rule validation to check predicate references against predicate
  artifacts.
- Update grounding input loading to iterate rule artifacts directly.
- Update rule proposal promotion to promote one proposal rule to one canonical
  rule artifact without wrapping it in a one-rule `RulesFileDocument`.
- Delete code that rewrites an entire rule bucket to add/remove one rule.

Tests first:

- Rule add writes one rule artifact.
- Rule list/show/remove work over rule artifacts.
- Rule validation rejects undeclared predicates and arity mismatches.
- Grounding produces the same grounded bundle from rule artifacts as before.
- Rule proposal promotion creates one rule artifact per promoted rule.
- No production path requires `RulesFileDocument` as canonical storage.

Gate:

- `rg -n "RulesFileDocument|RuleFileRef|RULE_FILE_FAMILY" propstore`
  shows no canonical production use.
- Logged rule CLI, proposal, grounding, ASPIC bridge, and build tests pass.
- `uv run pyright propstore` passes.

## Phase 4: Rule-Superiority Artifact Cutover

Goal: make rule-priority assertions first-class semantic artifacts instead of
entries inside a rules bucket.

Delete-first targets:

- Delete `RulesFileDocument.superiority` as production canonical storage.
- Delete code that requires superior and inferior rules to be in the same rule
  file.

Tasks:

- Add `RuleSuperiorityDocument` with:
  - superior rule ref
  - inferior rule ref
  - optional source/provenance metadata
- Add `RuleSuperiorityRef`.
- Add a canonical family for rule-superiority artifacts.
- Update `pks rule superiority add/remove/list` to operate on superiority
  artifacts.
- Validate that both referenced rules exist.
- Validate that neither referenced rule is strict.
- Validate the priority graph remains acyclic over rule artifacts.
- Update grounding/ASPIC paths to read superiority artifacts directly if they
  consume priority.

Tests first:

- Superiority add writes one superiority artifact.
- Superiority remove deletes one superiority artifact.
- Unknown rule refs are rejected.
- Strict-rule priority refs are rejected.
- Cycles are rejected across artifacts.
- Grounding/argumentation behavior remains unchanged for equivalent priority
  inputs.

Gate:

- `rg -n "superiority" propstore/families/documents/rules.py propstore/app/rules.py`
  shows no bucket-owned canonical priority storage.
- Logged rule superiority, grounding, and ASPIC tests pass.
- `uv run pyright propstore` passes.

## Phase 5: Research-Papers Plugin And `pks` Workflow Updates

Goal: update external authoring workflows we control so they describe artifact
semantics, not bucket files.

Tasks:

- Update `../research-papers-plugin` skills:
  - `register-predicates`
  - `author-rules`
  - `paper-process`
- Replace language such as "one predicates file per paper" and "one rules file
  per paper" with artifact semantics.
- Keep paper/source metadata guidance where useful, but do not describe
  canonical buckets.
- Update examples to use the new `pks predicate` and `pks rule` behavior.
- Run plugin-local checks if available.
- If plugin changes are committed, commit them atomically in the plugin repo.

Gate:

- `rg -n "knowledge/rules/<|knowledge/predicates/<|one rules file|one predicates file|rules file|predicates file" ../research-papers-plugin/plugins/research-papers`
  has no stale canonical-bucket instructions except historical notes that are
  explicitly marked historical.

## Phase 6: Boilerplate Standardization

Goal: remove duplicated family CRUD and proposal boilerplate after all semantic
families have one-artifact shape.

Target helper shape:

- Put the shared artifact iteration/load/save/delete helper on the typed family
  abstraction, not in per-family owner modules.
- The practical target is a generically typed family surface:
  `FamilyStore[RefT, DocT].iter_handles() -> Iterator[ArtifactHandle[RefT, DocT]]`,
  plus the existing typed `load`, `save`, `delete`, `address`, and
  `ref_from_path` operations.
- The conceptual invariant is dependent: the family key determines its exact
  ref and document types. In Python, enforce that with typed bound-family
  attributes and generic fallback APIs, not with untyped dynamic payloads.
- Do not replace `iter_micropubs`, `iter_rules`, `iter_predicates`, or similar
  wrappers with renamed per-family wrappers. If a wrapper only forwards to the
  family artifact store, delete it and call the typed family helper directly.
- Keep family-specific functions only when they encode real domain policy
  beyond iteration, such as canonical/source filtering, validation, report
  projection, or semantic ordering. Rename those as policy, not as generic
  `iter_*` plumbing.

Tasks:

- Identify repeated list/show/remove/add-artifact patterns across:
  - claims
  - stances
  - justifications
  - micropublications
  - same-as assertions
  - predicates
  - rules
  - rule-superiority
- Identify thin `iter_*` helpers, including `iter_micropubs`-style functions,
  and delete the ones that merely duplicate typed family iteration.
- Extract only family-level generic helpers that remove real duplication and
  preserve typed owner-layer APIs. Do not add wrapper/facade layers for their
  own sake.
- Standardize proposal promotion for one proposal artifact to one canonical
  artifact.
- Standardize test fixture helpers for artifact commit payloads.
- Standardize authored counts in app/world status over artifact handles.
- Keep CLI modules as presentation adapters only.

Tests first:

- Add or update family-registry tests that prove canonical semantic families
  use one artifact document, not bucket documents.
- Add typed family-helper tests that prove the generic family surface preserves
  the concrete ref/document types for at least rules, predicates, and one
  non-rule semantic family such as micropublications.
- Add deletion tests for thin `iter_*` wrappers that should no longer exist.
- Add regression tests for generic helpers only after at least two real
  families use them.

Gate:

- No duplicated bucket-style helper remains for canonical semantic families.
- No thin per-family `iter_*` wrapper remains when the typed family helper
  already expresses the same operation.
- CLI modules do not own mutation semantics.
- Logged contract, CLI, proposal, import, merge, build, and world tests pass.
- `uv run pyright propstore` passes.

## Phase 7: Contract, Manifest, Documentation, And Full-Suite Closure

Goal: make the final architecture enforceable.

Tasks:

- Update semantic family contracts.
- Update checked-in contract manifests with required version bumps.
- Update docs to describe semantic artifacts plus typed semantic links.
- Document source-local authoring convenience separately from canonical
  artifact identity.
- Add boundary tests preventing reintroduction of:
  - `propstore.core.relations.kernel`
  - `propstore.core.claim_concept_link_roles`
  - canonical `RulesFileDocument`
  - canonical `PredicatesFileDocument`
  - rule-superiority entries hidden in rule buckets
- Run the final search gates.
- Run package Pyright.
- Run the full logged pytest suite.

Final gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label relations-rules-predicates-standardization-final`
- `git status --short --untracked-files=no` is clean.

## Definition Of Done

This workstream is complete only when:

- `propstore.core.relations` is a module, not a package.
- `propstore.core.relations.kernel` does not exist.
- `propstore.core.claim_concept_link_roles` does not exist.
- `ClaimConceptLinkRole` imports from `propstore.core.relations`.
- Predicates are one canonical artifact per `PredicateDocument`.
- Rules are one canonical artifact per `RuleDocument`.
- Rule-superiority assertions are their own canonical artifacts.
- Research-papers plugin instructions no longer describe canonical rule or
  predicate bucket files.
- Shared family CRUD/proposal boilerplate is standardized only after the bucket
  surfaces are gone.
- Full Pyright and full logged pytest pass.
