# Property-based TDD hardening matrix

**Status**: REQUIRED companion to the workstreams.
**Owner**: Codex implementation owner + human reviewer required.

This file is the cross-workstream test-hardening surface. Every workstream should keep its example tests, but the paper-derived invariants below are the tests that catch whole classes of wrong implementations rather than one canned fixture. Unless a stream explicitly states why a property is impossible to generate safely, its "done" sentinel must include the relevant property tests.

Use Hypothesis for Python properties. Keep strategies small at first, then expand. Mark every property test with the paper / decision it is asserting in the test name or docstring. A property that only proves "the function does not crash" is not enough.

## Global strategy rules

- Generate typed domain objects, not loose dicts, except at IO boundary tests.
- Generate minimal examples first: one source, one claim, one relation, one branch, then scale with `max_size`.
- Assert algebraic laws when the paper gives an algebra: identity, idempotence, monotonicity, associativity, commutativity, absorption, conservation, or closure.
- Assert fail-closed behavior for invalid generated inputs.
- For graph algorithms, generate small graphs exhaustively or near-exhaustively before growing.
- For external packages, the property lives upstream when the implementation lives upstream; propstore keeps only pin/sentinel properties.

## WS-A schema fidelity

- YAML/JSON row decode immediately converts to domain objects; generated rows with extra canonical-forbidden source-local fields fail at the boundary.
- Domain object -> sidecar row -> domain object round-trips for claims, concepts, sources, stances, justifications, and rule documents.
- Canonical payload ordering is stable under input key-order permutation.
- Invalid enum values, missing required fields, and source-local-only readability metadata fail before entering the semantic pipeline.

## WS-B render policy

- Rendering is pure: generated query inputs do not mutate repo state, sidecar files, or SQLite mtime/content.
- Render output is deterministic under input ordering permutations that are semantically identical.
- Read-only sidecar opens never create missing databases or journal files.

## WS-C sidecar atomicity

- Materialize is all-or-nothing: for generated snapshots and generated local edits, either all files are written or no pre-existing file bytes change.
- Promote sidecar mirror is a projection of committed git state: generated failure points before git commit leave sidecar unchanged.
- Sidecar row insertion is idempotent for duplicate generated batches with identical ids and links.
- Claim logical-id reuse with different generated version content produces a detected version conflict, not silent first-writer-wins.

## WS-CM micropub identity

- Same canonical micropub payload always produces the same `ni:///sha-256;...` id.
- Permuting non-semantic input order before canonicalization does not change the id.
- Changing any semantic field in the canonical payload changes the id.
- `verify_ni_uri(compute_ni_uri(payload), payload)` succeeds, and verification against any mutated payload fails.
- The generated artifact id is never based only on `(source_id, claim_id)`.

## WS-D math naming

- Pignistic transform preserves total mass and maps singleton masses consistently with Smets/Kennes TBM notes.
- Vacuous belief assignments stay vacuous under pignistic projection.
- WBF composition preserves defined normalization bounds and rejects impossible mass/weight combinations.
- Renamed mathematical surfaces are behavioral changes where the paper requires them, not naming-only aliases.

## WS-E source promote

- Finalize/promote is branch-head linearizable: generated stale expected heads fail without mutation.
- Re-running promote on already-promoted generated content is idempotent or emits a typed duplicate report, never a partial write.
- Assertion ids and sameAs provenance survive source finalize -> promote -> sidecar projection.
- Generated malformed source-local fields cannot leak into canonical promoted payloads.

## WS-F ASPIC bridge

- For generated small ASPIC theories, every projected attack has a source argument and target argument in the original theory.
- Defeat implies attack, but attack does not have to imply defeat; generated preference orderings must include counterexamples.
- Strict-rule closure is monotone under adding strict premises.
- Bridge output is stable under alpha-renaming of generated rule ids that preserves rule identity.

## WS-G belief revision

- Generated finite belief sets satisfy AGM-style success, inclusion, vacuity, consistency, and extensionality where each postulate applies.
- OCF ranks preserve ordering under positive affine transformations.
- Revision by logically equivalent generated formulas yields equivalent revised states.
- Cache keys are semantic: syntactically different but equivalent formulas do not fork cache identity unless the workstream explicitly chooses syntax-sensitive storage.

## WS-H probabilistic argumentation

- Generated probabilities stay in `[0, 1]` and normalize where the paper-defined model requires normalization.
- Adding independent support cannot decrease support strength under monotone support semantics.
- Adding independent attack cannot increase acceptance strength under monotone attack semantics.
- DF-QuAD / bipolar generated examples preserve the paper's attack/support symmetry and boundary cases.

## WS-I ATMS world

- Generated justifications produce labels that are minimal consistent environments; no returned environment has a strict subset with the same support.
- Adding a non-conflicting justification is monotone for support.
- Adding a contradiction removes or marks inconsistent environments without mutating unrelated labels.
- Budgeted stability is monotone in the budget: if `limit=n` succeeds, `limit=n+1` must not fail for the same graph.

## WS-J worldline causal

- Worldline hashes are deterministic under semantically identical generated operation orderings.
- Renaming `HypotheticalWorld` to `OverlayWorld` preserves overlay behavior exactly on generated examples.
- Overlay worlds add claims and leave causal/parameterization edges intact.
- Replay journals reproduce the same generated world state and hash.

## WS-J2 intervention world

- `do(X=x)` severs every generated incoming edge to `X` and no outgoing edges from `X`.
- `observe(X=x)` preserves generated incoming edges and fails closed when deterministic SCM evaluation disagrees.
- `do` and `observe` traces have disjoint provenance sentinels.
- HP actual-cause minimality: generated candidate cause sets with removable conjuncts fail AC3.
- Interventions on independent variables do not change generated descendants outside the variable's reachable subgraph.

## WS-K heuristic discipline

- Embedding model identity is injective over generated provider/name/revision/dimension tuples; sanitized display names never determine identity.
- Bidirectional classification preserves two independent generated perspectives; reversing source/target is not allowed to reuse the same payload.
- Distance dedupe never collapses asymmetric generated distances to `min(forward, reverse)`.
- Trust output is generated by the argumentation pipeline with provenance, not by a heuristic write path.

## WS-K2 meta-rule extraction

- Generated proposed rules using undeclared predicates fail promotion.
- Generated promoted rules are variable-safe: every variable in the head appears in a positive body literal or an explicitly accepted binding form.
- Predicate declaration round-trip preserves name, arity, argument types, and source-paper provenance.
- For generated metadata facts, promoted rules fire deterministically through the WS-K consumer API.

## WS-L merge

- Structured merge is idempotent: merging a generated branch with itself yields no conflict and no content change.
- Independent generated edits commute.
- Conflicting generated edits produce typed conflicts that preserve both sides and provenance.
- Merge result hashes are deterministic under branch traversal order permutations.

## WS-M provenance

- `compute_ni_uri` / `verify_ni_uri` round-trip for generated byte payloads; mutated bytes fail verification.
- PROV-O export for generated provenance records emits at least one typed Entity or Activity and preserves `wasDerivedFrom` / `wasGeneratedBy` edges where applicable.
- `compose_provenance` preserves causal operation order while deduping exact duplicate witnesses.
- Semiring polynomial provenance is not collapsed to ATMS why-labels before the boundary named by the workstream.

## WS-N1 architecture immediate

- Shim deletion gates are search-backed properties: generated import attempts against old names fail, and generated imports against new names succeed.
- CLI owner APIs accept typed requests and never import Click, write stdout/stderr, or call `sys.exit`.
- Canonical JSON helper identity is singular: generated canonicalizable payloads produce the same bytes through the one surviving helper.

## WS-N2 layered architecture

- For every generated lower-layer -> higher-layer synthetic import, `lint-imports` fails and names the layered contract.
- For generated allowed higher-layer -> lower-layer imports, the contract does not fail solely due to direction.
- No allowlist file can make a generated violation pass.

## WS-O-arg upstream kernel

- Ideal extension is admissible and subset-contained in every preferred extension for generated small AFs.
- The mutual-defense generator must include cases where no singleton extension is admissible but a pair is admissible.
- ASP literal encoding round-trips generated literals and always emits clingo-loadable identifiers.
- Rule-name collision detection fails on generated duplicate defeasible names before emitting ambiguous facts.
- AF revision classification matches generated subset-content cases from Cayrol et al., not cardinality alone.

## WS-O-arg ABA/ADF

- Flat ABA generated frameworks reduce to Dung AFs with acceptance preserved under the documented reduction.
- Non-flat generated ABA inputs fail with a typed out-of-scope error.
- ADF generated acceptance conditions evaluate consistently under all generated two-valued interpretations.

## WS-O-arg Dung extensions

- Generated complete extensions satisfy conflict-freeness, admissibility, and defense closure.
- Eager/stage/semi-stable/prudent generated outputs satisfy their defining maximality/minimality predicates.
- Labelling and extension representations round-trip: `in` set equals the extension, and `out`/`undec` match Caminada constraints.

## WS-O-arg VAF/ranking

- Generated VAF attacks succeed or fail exactly according to audience value ordering.
- Ranking semantics return a typed `RankingResult`; non-convergence is data, not an exception or silent partial result.
- Ranking preorder properties hold for generated outputs: reflexivity and transitivity where the selected semantics requires them.
- Gradual streams consume `RankingResult`; they do not redefine convergence ownership.

## WS-O-arg gradual

- Generated attack/support graphs keep strengths within the paper-defined range.
- Monotone support and monotone attack properties hold for DF-QuAD/bipolar semantics.
- Iterative semantics expose convergence state and never silently return the last iterate as a proof.

## WS-O-ast ast-equiv

- Generated alpha-equivalent functions compare equivalent after canonicalization.
- Generated bound names, comprehension targets, lambda args, and local assignments are not returned by `extract_free_variables`.
- Generated free references are returned by `extract_free_variables`.
- `Tier.BYTECODE` is absent; generated true-equivalence cases at `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL` are accepted, while `NONE` is undecided.

## WS-O-bri bridgman

- Generated dimension expressions satisfy multiplication, division, and power algebra laws.
- Transcendentals accept only generated dimensionless arguments and raise `DimensionalError` for dimensioned arguments.
- Canonical dimension signatures are stable under unit-order permutations.
- `verify_equation` is absent from generated import attempts and from AST scans.

## WS-O-gun Garcia/gunray

- Generated dialectical trees obey Garcia acceptable-line constraints, including the block-on-block ban.
- Proper and blocking defeaters are generated separately and never collapsed.
- Generated section classification partitions literals into exactly `yes/no/undecided/unknown`.
- Presumption specificity examples preserve the Garcia 2004 section 6.3 adjustment.
- Enumeration budgets are monotone: increasing `max_arguments` cannot turn a successful complete result into `BUDGET_EXCEEDED`.

## WS-O-qui quire

- Generated content-addressed writes are stable under semantic no-op rewrites.
- Branch-head compare-and-swap fails closed for generated stale heads.
- Transaction replay yields the same final tree and head as the original generated operation sequence.

## WS-P CEL / units / equations

- Generated CEL strings round-trip through lexer/parser for all supported escape forms in the local CEL spec checkout at `~/src/cel-spec`.
- Generated ternaries evaluate only the selected branch for type/effect checks where CEL semantics require short-circuiting.
- Generated division constraints include non-zero guards before Z3 reasoning.
- Generated equation comparisons preserve orientation where orientation is semantically meaningful.
- Algorithm equivalence suppresses conflicts only for generated `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL` true-equivalence results; `NONE` does not suppress.

## WS-Q CAS branch-head discipline

- Generated stale expected heads fail before mutation for finalize, import, promote, and sidecar-relevant writes.
- Generated concurrent operations have a serializable winning order: one succeeds, the other observes a typed stale-head failure.
- Failed CAS attempts leave the worktree, sidecar, and branch head unchanged.
