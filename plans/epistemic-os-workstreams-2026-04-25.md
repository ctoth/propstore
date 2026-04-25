# Epistemic OS Workstreams

Date: 2026-04-25
Status: Execution control surface
Scope: principled machinery before imports; NL grounding deferred

## Intent

This plan is deliberately not a shortest-path plan. The target is the most
principled, highest-payoff architecture: build the semantic machinery that lets
imports, reasoning backends, policy, provenance, and audits all land on one
shared substrate.

The trunk is:

```text
relation concepts -> situated assertions -> context lifting -> projection
round trips -> import-ready provenance -> epistemic state machinery
```

Bulk imports and NL grounding are deferred. The machinery needed to import
correctly is not deferred.

I read the epistemic operating system roadmap and the 2026-04-21 situated
assertion synthesis. I reread notes excerpts from the local paper collection
for the central context, grounding, ATMS, AGM, ASPIC, micropublication,
provenance, lemon, frame, and proto-role papers. I did not reread the PDFs or
page images for this plan. Page-image rereads are explicit gates below.

Claude was run as an external design critic with the same "reach for the
principled architecture" instruction. Its useful correction was to make the
workstream graph dependency-ordered and to make page-image rereads binding
before work that depends on formal diagrams or definitions.

## Non-Negotiable Method

Every implementation slice uses red/green TDD:

1. Red commit: add the failing example/property tests first.
2. Green commit: implement the smallest principled production change that
   makes that slice green.
3. Reread this workstream artifact after every green commit.
4. Rewrite this artifact in the same commit, or the next immediate commit, if
   the implementation changes the plan, dependency graph, tests, or definition
   of done.
5. Commit often. No edited production or test file remains uncommitted before
   moving to the next slice.

Every green commit must run the appropriate targeted test through the logged
pytest wrapper and, when the package surface is touched, `uv run pyright
propstore`. The full gate remains:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label <slice> <tests...>
uv run pyright propstore
```

Use Hypothesis wherever a property is clearer than an example. The default
shape is tiny generated structures plus brute-force oracle checks.

Source code should cite papers when the code is implementing a literature
definition, theorem, or invariant. The citation belongs near the invariant or
algorithm, not in vague module prose. Tests should cite the same paper and
page/image checkpoint when they encode a formal property.

## Gates

The plan is only useful if it prevents old and new semantics from coexisting.
Each implementation slice therefore needs explicit gates, not only passing
behavior tests.

### Slice Gate Template

Every slice must name these before the red commit:

```text
target_surface:
old_surfaces_to_delete:
allowed_owner_modules:
forbidden_imports:
forbidden_symbols:
forbidden_storage_columns:
positive_tests:
negative_tests:
pyright_scope:
paper_checkpoint:
deletion_ledger:
```

Definitions:

- `target_surface`: the one abstraction this slice is converging on.
- `old_surfaces_to_delete`: production modules, functions, fields, columns,
  document shapes, or helper families that must not survive the slice.
- `allowed_owner_modules`: the only modules allowed to own the semantics.
- `forbidden_imports`: import paths that prove old ownership survived.
- `forbidden_symbols`: names that prove old representation survived.
- `forbidden_storage_columns`: schema columns that would duplicate semantics in
  sidecar/runtime storage.
- `positive_tests`: behavior and property tests that prove the new path works.
- `negative_tests`: tests that fail if the old path still exists.
- `pyright_scope`: touched package surface for `uv run pyright propstore`.
- `paper_checkpoint`: note/page-image reread required before code.
- `deletion_ledger`: the concrete files/functions removed or rewritten in the
  green commit.

### Mechanical Gate Types

Use these gate types aggressively:

1. Import-linter or AST import tests
   - Example: `propstore.cli` must not import owner-layer internals except typed
     request/report APIs.
   - Example: `propstore.sidecar` must not import backend projection engines.
   - Example: backend adapters must not be imported by assertion identity code.

2. Forbidden-symbol tests
   - Use `rg -F` or an AST visitor in tests to ban old helper names once a
     replacement lands.
   - Examples: old `predicate` emitters, old path helpers, old claim-bucket
     merge functions, old context visibility fields.

3. Schema gates
   - Tests inspect generated SQLite schema and fail on columns that duplicate
     semantic ownership.
   - Example: after situated assertions own relation identity, sidecar may store
     `assertion_id` and indexed role facts, but must not reintroduce a
     free-standing semantic `predicate TEXT` column.

4. Runtime path gates
   - Monkeypatch or sentinel tests prove runtime cannot silently rebuild a
     replacement path from repository files when sidecar is supposed to own the
     compiled substrate.
   - Example: after grounding sidecar materialization lands, `WorldModel` must
     fail loudly if the sidecar table is missing rather than calling a direct
     bundle builder.

5. Round-trip gates
   - New representations must have parse/render or project/lift properties.
   - Old representations must not be accepted unless the stream explicitly says
     old data support is in scope.

6. Diff gates
   - Before the green commit, run `git diff --check`.
   - Review `git diff --stat` and `git diff --name-only` against the slice gate.
   - If a file outside the declared write set changed, explain it in the commit
     message or split it out.

7. Artifact reread gate
   - After every green commit, reread this file.
   - If the slice changed scope or discovered an old path, update this file
     before starting the next red commit.

### Definition Of Refactored

A slice is not refactored just because tests pass. It is refactored only when:

- production callers use the target surface directly;
- old production surfaces are deleted, not wrapped;
- old names are absent from production search, except in changelog/history/docs
  that explicitly describe the deletion;
- negative tests fail if the old path is reintroduced;
- the sidecar/runtime boundary has one owner for the semantic behavior;
- pyright and targeted logged tests pass;
- the deletion ledger names what was removed.

### Standard Gate Commands

For every code slice, run the slice-specific commands plus the relevant subset
of these:

```powershell
rg -n -F "<old symbol>" propstore tests docs proposals
powershell -File scripts/run_logged_pytest.ps1 -Label <slice> <tests...>
uv run pyright propstore
git diff --check
git status --short
```

When a symbol is intentionally retained in docs or historical proposals, the
negative test should scan production paths only or allowlist the documented
reference explicitly.

## Workstream Graph

### WS0: Literature and Workstream Control

Purpose:

- Keep the work literature-grounded instead of drifting into local taste.
- Maintain a live plan that changes after evidence, not after vibes.

Definition of done:

- The active workstream file names the controlling proposals and papers.
- Each implementation stream lists paper checkpoints before code begins.
- Each green commit either confirms the plan still holds or updates it.
- Every source-code citation added by a stream has a matching test or design
  note citation.

Deletion-first constraint:

- No "temporary plan" or duplicate checklist survives once this file owns the
  stream. Old plan fragments must be merged or deleted when superseded.

Testing:

- Meta-tests are acceptable for architectural gates, for example import
  boundary checks, forbidden-column checks, and "no old module import" checks.

### WS1: Bootstrap Relation Kernel

Purpose:

- Relations are propstore concepts, but the system still needs a tiny kernel
  whose semantics are implemented directly.
- This prevents the circularity where relation definitions require relations
  before any relation semantics exist.

Deliverables:

- Bootstrap relation vocabulary for `relation_concept`, `role`, `has_role`,
  `role_domain`, `role_range`, `subtype_of`, `instance_of`,
  `contextualizes`, `condition_applies`, `supports`, `undercuts`, `rebuts`,
  `base_rate_for`, `calibrates`, and `published_in`.
- Typed `RoleSignature`, role binding validation, and relation property
  assertions.
- Relation identity is not a bare predicate string.

Deletion-first constraint:

- Any production path that creates semantic predicate strings without a
  relation concept reference must be deleted or rewritten in the same stream.

Red/green tests:

- Red: bootstrap role-signature tests and a grep/import boundary test proving
  no new bare-predicate production path is allowed.
- Green: relation kernel and the minimal caller rewrites.
- Hypothesis: inverse involution, symmetric canonicalization, transitive
  closure containment on tiny graphs, role-domain/range totality.

Paper checkpoints:

- Cimiano 2016 notes for OntoLex-Lemon.
- Buitelaar 2011 page images before finalizing the relation/lexical binding.
- Dowty 1991 notes for proto-role pressure.
- Fillmore 1982 and Baker 1998 notes for frame roles.

### WS2: Situated Assertion Substrate

Purpose:

- The atom is not a claim row, predicate string, CEL expression, or backend
  atom. The atom is a situated assertion:
  `(relation, role_bindings, context, condition, provenance_ref)`.

Deliverables:

- Domain objects for `SituatedAssertion`, `RelationConceptRef`,
  `RoleBinding`, `RoleBindingSet`, `ContextReference`, `ConditionRef`, and
  `ProvenanceGraphRef`.
- Identity rules that exclude provenance from assertion identity.
- Rival normalized candidates can coexist with explicit equivalence witnesses.

Deletion-first constraint:

- No new core semantic pipeline may pass loose dicts or legacy claim-shaped
  payloads as semantic objects. Boundary IO converts immediately.
- No compatibility adapter survives past the slice that updates its callers.

Red/green tests:

- Red: identity stability and provenance non-contamination tests.
- Green: domain objects and first source/canonical conversion.
- Hypothesis: role-order canonicalization, rival-normalization coexistence,
  render/parse round trips for tiny assertions.

Paper checkpoints:

- Re-read the situated assertion synthesis.
- Clark 2014 notes for claim/provenance/evidence separation.
- Carroll 2005 notes now; page images before provenance carrier code.

### WS3: ConditionIR and CEL Frontend Split

Purpose:

- CEL is an authoring/query language, not the ontology.
- Runtime helpers such as `_rt` belong only in backend IR, never in the
  semantic condition IR.

Deliverables:

- Closed typed `ConditionIR`.
- Frontend pipeline: source text to surface AST to resolved AST to ConditionIR.
- Backend emitters for Python AST, JavaScript/ESTree where needed, Z3, and SQL
  fragments where sound.
- Source spans survive frontend passes.

Deletion-first constraint:

- Runtime consumers must consume checked ConditionIR, not raw CEL strings.
- Backend helper nodes are forbidden in ConditionIR by type and test.

Red/green tests:

- Red: `ConditionIR` purity tests and initial CEL-to-IR fixtures.
- Green: frontend lowering and one backend emitter.
- Hypothesis: Python/JS agreement on tiny expressions, Z3 agreement for the
  decidable fragment, span containment, no backend node under IR.

Paper checkpoints:

- No paper gate. Re-read the compiler middle-end plan and the CEL section of
  the situated assertion synthesis.

### WS4: Provenance Named-Graph Carrier

Purpose:

- Provenance must point to named graph state and must not contaminate assertion
  identity.
- Import runs, external statements, backend projections, and lifted results all
  need auditable provenance before imports begin.

Deliverables:

- Deterministic JSON-LD named graph model.
- Git-notes provenance storage remains the durable carrier.
- Import-run, projection-frame, external-statement, external-inference, source
  version/hash, and license provenance records.
- Probability-bearing values carry explicit `ProvenanceStatus`.

Deletion-first constraint:

- Remove any identity computation that changes assertion identity when only
  provenance changes.
- Remove any probability path that silently manufactures provenance.

Red/green tests:

- Red: named graph determinism, provenance identity isolation, and probability
  status boundary tests.
- Green: named graph carrier and first callers.
- Hypothesis: deterministic serialization, graph merge associativity where
  claimed, status totality at reasoning boundaries.

Paper checkpoints:

- Carroll 2005 page images for named graphs, quoting, assertion, trust.
- Green 2007 notes for provenance semiring algebra.
- Buneman 2001 notes for provenance lineage.

### WS5: Full Context Lifting

Purpose:

- Fully complete context lifting instead of leaving it as a small side engine.
- Context is first-class `ist(c, p)` machinery with authored lifting rules,
  exceptions, conditions, and provenance.

Deliverables:

- Contextual assertions use the same situated assertion substrate.
- Lifting rules are source artifacts and compile to sidecar materializations.
- Lifting can produce derived assertions with provenance and explanation.
- Exceptions/abnormality/undercutters are explicit and local to the relevant
  context.
- ATMS, ASPIC, and query surfaces consume lifted assertions through projection
  boundaries, not special visibility paths.

Deletion-first constraint:

- Delete any old production surface that treats context visibility or hierarchy
  as the semantic lifting mechanism.
- No second context system.

Red/green tests:

- Red: `ist(c, p)` examples, lifting exception examples, and sidecar
  materialization expectations.
- Green: authored lifting rules and first projection/query integration.
- Hypothesis: positive lifting monotonicity, exception locality, context-stack
  enter/exit round trip, no sibling-context leakage.

Paper checkpoints:

- Guha 1991 page images before implementing lifting semantics.
- McCarthy 1993 page images for `ist`, entering/exiting, and lifting.
- McCarthy 1997 notes for expanded applications.
- Kallem 2006 page images for Cyc microtheory visibility, including what we
  deliberately do not copy.
- Bozzato 2018 page images for CKR-style justifiable exceptions.

### WS6: Projection Boundary V2

Purpose:

- Backends are projections. Backend atoms, Z3 terms, ASPIC arguments, SQL rows,
  and gunray atoms are not propstore identity.

Deliverables:

- Typed projection protocol with explicit source assertion ids.
- Gunray/Datalog, Z3, ASPIC, SQL, and future Python/JS projections either
  round-trip identity or produce typed loss witnesses.
- Backend results lift back into propstore as situated assertions with
  projection provenance.

Deletion-first constraint:

- Delete projection paths that emit bare backend strings without assertion-id
  mapping.
- Replace the current partial grounding source-kind surface with assertion
  projection, rather than carrying both.

Red/green tests:

- Red: projection round-trip tests and loss-witness refusal tests.
- Green: first backend projection replacement.
- Hypothesis: `lift(project(a)) == a` for in-scope fragments, every backend
  result has attribution, projection refusal is explicit when lossy.

Paper checkpoints:

- Diller 2025 page images before gunray/Datalog projection.
- Modgil 2014 and Prakken 2010 notes before ASPIC projection changes.
- Dung 1995 notes for AF boundary semantics.

### WS7: Grounding Completion

Purpose:

- Finish grounding as real machinery, not only `concept_relation` facts.
- Imports need full structural grounding before they can land cleanly.

Deliverables:

- Ground facts for relation concepts, role bindings, claim attributes, claim
  conditions, contextual facts, and provenance-aware derived facts.
- Full four-status rule output support where the backend supplies it:
  definitely, defeasibly, not defeasibly, undecided.
- Sidecar materialization is the runtime source; runtime does not rebuild a
  parallel bundle from repository files.

Deletion-first constraint:

- Remove direct runtime rebuild paths once sidecar materialization owns the
  compiled grounding substrate.
- Remove any tests or docs that describe `claim.attribute` and
  `claim.condition` as parsed-but-unmaterialized final behavior.

Red/green tests:

- Red: sidecar-grounded fact tests for each source kind and four-status output.
- Green: fact extraction, sidecar build integration, ASPIC/gunray consumption.
- Hypothesis: fact extraction is deterministic, sidecar and direct compiler
  oracle agree during the cutover, grounding order does not change emitted
  assertion ids.

Paper checkpoints:

- Diller 2025 page images.
- Garcia 2004 notes for four-valued DeLP query distinction.

### WS8: Opinions and Base-Rate Resolution

Purpose:

- Opinions attach to assertions, not global relation names.
- Ignorance is not `a = 0.5`; missing priors are typed unresolved results.

Deliverables:

- Opinion construction requires an assertion id.
- `BaseRateProfile` and resolver operate over propstore assertions.
- Resolver can return `BaseRateUnresolved`.
- Stratification prevents recursive prior resolution from looping.
- Replication-rate/base-rate content is represented as assertions, not code
  constants.

Deletion-first constraint:

- Remove silent `0.5` defaults from docs, calibration code, sidecar schema, and
  tests unless a sourced prior or explicit policy produced 0.5.

Red/green tests:

- Red: no-default-half tests and unresolved-prior tests.
- Green: resolver and caller rewrites.
- Hypothesis: fusion algebra properties, stratification termination, missing
  prior never returns a numeric opinion.

Paper checkpoints:

- Re-read `docs/subjective-logic.md`.
- Re-read local replication notes before writing fixture assertions.
- Denoeux 2018 notes if belief-function decision behavior is touched.

### WS9: Belief, Merge, Revision Repointing

Purpose:

- Existing AGM, iterated revision, ATMS, AF, ASPIC, and merge machinery should
  operate over situated assertion identity.
- This is not a mechanical rename; postulates may reveal identity problems.

Deliverables:

- Belief/revision/merge/worldline paths use situated assertion ids.
- Existing AGM, DP, ATMS, Dung, ASPIC, PAF, and IC-merge tests remain green.
- Structured consumers project from kernel state and do not own belief change.

Deletion-first constraint:

- Delete claim-bucket merge semantics and any fallback path that bypasses the
  formal merge object.
- No "old claim id" to "assertion id" compatibility shim after the callers are
  updated.

Red/green tests:

- Red: assertion-id versions of the existing postulate tests.
- Green: re-pointed world/repo/argumentation code.
- Hypothesis: AGM/DP postulates over generated tiny assertion languages, PAF
  completion count and merge operator invariants over assertion ids, ATMS label
  soundness/completeness over assertion ids.

Paper checkpoints:

- Alchourron 1985 notes for AGM.
- Darwiche 1997 notes for iterated revision.
- de Kleer 1986 notes and Dixon 1993 page images for ATMS/AGM bridging.
- Coste-Marquis 2007 page images before changing merge universe identity.
- Konieczny and Pino Perez 2002 notes for IC postulates.

### WS10: Snapshot, Journal, and Diff

Purpose:

- Worldlines are not enough for the operating system target. State history must
  be durable, queryable, diffable, and replayable.

Deliverables:

- `EpistemicSnapshot` with stable serialization.
- Transition journal records state-in, operation, policy, operator, state-out,
  and explanation.
- Semantic diff over assertion acceptance, warrant, ranking, provenance, and
  dependency deltas.
- Replay determinism checks.

Deletion-first constraint:

- Any code treating worldline payloads as the authoritative state-history layer
  must move to snapshots/journals.

Red/green tests:

- Red: snapshot round trip, replay determinism, and diff apply tests.
- Green: snapshot/journal/diff owner layer.
- Hypothesis: `apply(diff(a, b), a) == b`, replay hash determinism,
  independent operation commutation where claimed.

Paper checkpoints:

- Bonanno 2007/2010 notes if branching-time belief change affects identity.
- Klein 2003 notes if ontology evolution diff vocabulary is used.

### WS11: Import-Ready Machinery

Purpose:

- Imports are deferred, but the import contract must be complete.
- Import should be just another compiler into situated assertions, provenance
  graphs, contexts, relation concepts, and equivalence witnesses.

Deliverables:

- Typed authored-form to situated-assertion compiler.
- External source identity, source version/hash, import run, external statement
  id, external inference id, mapping policy, license, and context/microtheory
  mapping.
- Equivalence witness store for rival normalized candidates.
- Lens-style surface/structural round trips for non-NL fixtures.

Deletion-first constraint:

- Delete any import path that guesses semantic relations without an explicit
  witness or unresolved result.
- No bulk importer may land before this machinery is green.

Red/green tests:

- Red: import compiler fixture and equivalence witness tests.
- Green: import machinery owner package.
- Hypothesis: lens PutGet/GetPut laws for surface/structural fixtures,
  equivalence witness composition without identity collapse.

Paper checkpoints:

- Bohannon 2006 page images for relational lens laws.
- Beek 2018 notes for `sameAs` and equivalence hazards.
- OpenCyc/Cyc notes before context/microtheory mapping.

### WS12: Policy and Governance

Purpose:

- Policy is not scattered flags. Policy is inspectable, serializable,
  replayable propstore content.

Deliverables:

- `PolicyProfile`, `RevisionPolicy`, `MergePolicy`,
  `AdmissibilityProfile`, source-trust profiles, escalation policies.
- Policies can be represented as assertions where appropriate.
- Every state transition names a policy id and includes it in replay hashes.

Deletion-first constraint:

- Remove hidden defaults from critical revision/merge/projection paths.
- CLI flags parse into typed policy requests; CLI does not own policy logic.

Red/green tests:

- Red: replay hash sensitivity and policy serialization tests.
- Green: policy owner layer and caller rewrites.
- Hypothesis: policy serialization round trip, replay hash changes when policy
  changes, default resolution determinism.

Paper checkpoints:

- Carroll 2005 notes for trust policy boundaries.
- Modgil preference papers notes if argument preference policy changes.

### WS13: Process Manager

Purpose:

- Fragility, next-query, intervention, revision, and merge should become
  executable epistemic workflows, not isolated queries.

Deliverables:

- `InvestigationPlan`, intervention plan, queued revision/merge jobs, and
  completion records.
- Jobs reference snapshots, policies, assertions, and journal entries.
- Process manager reuses fragility and bounded intervention machinery.

Deletion-first constraint:

- Replace CLI-only workflow semantics with owner-layer job objects.

Red/green tests:

- Red: queued job and investigation replay tests.
- Green: process manager owner layer and one public query path.
- Hypothesis: job serialization round trip, deterministic replay under fixed
  inputs, idempotent completion recording.

Paper checkpoints:

- Doyle 1979 notes for TMS/problem-solver boundary.
- de Kleer 1986 notes for assumptions/environments.

### WS14: Public Surfaces and Observatory

Purpose:

- Expose the operating system honestly, and continuously measure semantic
  behavior.

Deliverables:

- CLI and Python API are typed presentation surfaces only.
- Evaluation harness compares operator families, policies, replay results, and
  known falsification scenarios.
- Documentation maps source artifact to assertion to projection to state to
  journal.

Deletion-first constraint:

- Move any remaining semantic workflow code out of `propstore.cli`.
- Delete ad hoc scripts once they are covered by the observatory harness.

Red/green tests:

- Red: CLI adapter boundary tests and evaluation determinism fixtures.
- Green: public surfaces and observatory harness.
- Hypothesis: API/CLI typed-request equivalence, replay determinism, stable
  export/import of reports.

Paper checkpoints:

- Clark 2014 page images for micropublication visual model.
- Greenberg 2009 notes if citation-distortion examples become evaluation
  fixtures.

## Global Property Program

Use Hypothesis aggressively for:

- relation algebra properties;
- assertion identity stability;
- provenance non-contamination;
- ConditionIR/backend semantic agreement;
- context lifting locality and monotonicity;
- projection round-trip identity;
- grounding determinism;
- base-rate stratification;
- AGM/DP/PAF/ATMS postulates over situated assertions;
- snapshot diff exactness;
- import lens laws;
- policy replay hash sensitivity.

Keep conventional examples for:

- Guha/McCarthy `ist(c, p)` examples;
- Kallem microtheory hierarchy examples;
- Diller 2025 grounding examples;
- Dung/ASPIC attack and defeat examples;
- Coste-Marquis/Konieczny merge examples;
- de Kleer/Dixon ATMS examples;
- Clark micropublication examples;
- lemon/frame/proto-role polysemy examples;
- replication/base-rate fixtures as sourced assertions, never constants.

## Commit Shape

Each stream is split into many small commits. The expected rhythm is:

```text
commit: red tests for WS<n> slice <x>
commit: green implementation for WS<n> slice <x>
commit: update workstream artifact if the green changed the plan
commit: red tests for WS<n> slice <x+1>
commit: green implementation for WS<n> slice <x+1>
```

If a slice cannot produce a kept green improvement after two red/green attempts,
stop and report the exact blocked workstream item instead of widening scope.

## Current Source-Code Reality To Respect

The current repo already has substantial pieces:

- context lifting exists but is a small explicit-rule engine, not the full
  situated assertion/context substrate;
- grounding parses richer source kinds, but extraction is still first-slice
  behavior for `concept_relation`;
- sidecar has grounded-fact helpers, but runtime still has direct rebuild
  paths;
- merge/revision/ATMS/ASPIC/property tests already exist and should be
  preserved as postulate gates;
- Hypothesis is already part of the project and widely used;
- tests already cite papers in several argumentation and worldline areas.

The work is therefore not greenfield. The task is direct convergence: delete
the old partial semantic surfaces as each target surface lands, update every
caller, and keep the paper-backed postulates green.
