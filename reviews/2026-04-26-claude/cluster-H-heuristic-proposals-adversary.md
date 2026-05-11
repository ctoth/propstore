# Cluster H: heuristic + proposals discipline (adversary)

Reviewer: review-cluster-H (adversary). Date: 2026-04-26.

## Scope

In-scope code (read in full):
- `propstore/heuristic/__init__.py` — empty stub
- `propstore/heuristic/source_trust.py`
- `propstore/proposals.py`
- `propstore/classify.py`
- `propstore/relate.py`
- `propstore/relation_analysis.py`
- `propstore/condition_classifier.py`
- `propstore/semantic_passes/{__init__,runner,registry,types,diagnostics}.py`
- `propstore/description_generator.py`
- `propstore/embed.py`
- `propstore/epistemic_process.py`

Cross-reference reads (partial):
- `propstore/app/sources.py` (lines 175-235, 490-517) — caller of `derive_source_document_trust`
- `propstore/app/claims.py` (lines 560-644) — caller of `commit_stance_proposals`
- `propstore/app/proposals.py` (full) — caller of promote
- `propstore/source/finalize.py` (lines 100-220) — receives heuristic-modified SourceDocument
- `propstore/source/passes.py` (head) — confirms semantic_passes consumed by source layer
- `.importlinter` (full)
- Greps: `derive_source_document_trust`, `commit_stance_proposals|promote_stance_proposals`, reverse-direction imports of classify/relate/proposals/heuristic/semantic_passes, `knowledge/` writes from heuristic side, `source-heuristic` contract definition.

## Layering violations (architecture drift)

### HIGH

**H1. `derive_source_document_trust` is heuristic logic that lands in source-layer storage with no proposal ceremony.** `propstore/heuristic/source_trust.py:103-172` mutates a `SourceDocument`'s `trust` block (assigning `prior_base_rate`, `derived_from`, and `status=CALIBRATED`) by running a `WorldModel.chain_query`. The two callers in `propstore/app/sources.py` are `finalize_source` (line 190-201) and `_auto_finalize_source` (line 504-516). Both pass the heuristic-mutated document straight into `finalize_source_branch(repo, name, source_doc=derive_source_document_trust(repo, source_doc))`. `propstore/source/finalize.py:178-185` then writes that exact document into `transaction.source_documents.save(ref, ...)` on the source branch. There is no proposal branch, no `proposal_source_documents` family, no human review step. The architecture says heuristics emit *proposals only*; this path emits source-layer truth. Compare with the stance pipeline, which at least uses `commit_stance_proposals → plan_stance_proposal_promotion → promote_stance_proposals`. Trust calibration has no equivalent.

**H2. The `source-heuristic` import-linter contract is the only directional gate, and it is one-way only.** `.importlinter` lines 13-19 forbid `propstore.source -> propstore.heuristic`. Nothing forbids `propstore.heuristic` from importing `propstore.source` or `propstore.world` or `propstore.repository` — and `source_trust.py` does exactly that (`from propstore.repository import Repository`, `from propstore.families.documents.sources import SourceDocument`, `from propstore.source.common import load_source_metadata, normalize_source_slug`, and lazily `from propstore.world import WorldModel`). The architecture diagram (memory: `project_architecture_layers`) says heuristic depends on source for *reading*. Fine in principle, but combined with H1 the heuristic layer is now constructing typed source-layer documents that get persisted. The contract does not catch the leak because the leak goes via *return value*, not import direction.

### MEDIUM

**H3. `derive_source_document_trust` opens a `WorldModel` from inside the heuristic layer.** `source_trust.py:119-166`. The heuristic layer now depends transitively on `propstore.world.WorldModel`, `wm.chain_query`, `wm.resolve_concept`. The architecture lists "world" as part of the typing/argumentation substrate. Heuristic invoking world-model chain queries to compute a numeric prior, and then writing that prior into source storage, conflates three layers in one function: heuristic computation → world reasoning → source authoring. If world resolution changes semantics, source-layer trust silently changes too, with no proposal record showing what changed.

**H4. `derive_source_document_trust` returns `ProvenanceStatus` strings as bare values inside a Python dict.** `source_trust.py:108-170`. The trust dict contains `status`, `prior_base_rate`, `quality`, `derived_from` — but the *witnesses* and *operations* tuples that `Provenance` carries elsewhere (cf. `classify.py:_vacuous_classifier_opinion` building a real `Provenance(status=..., witnesses=(), operations=("stance_classification_error",))`) are absent. The trust dict has *status only*. It does not record *which* heuristic computed the prior, *when*, with *what model version*, against *which world snapshot*. See H8.

## Provenance / "imports are opinions" violations

### HIGH

**H5. Trust calibration writes a numeric `prior_base_rate` into source storage with no operation tag, no agent, no commit-of-knowledge, no timestamp.** Per the `feedback_imports_are_opinions` memory: every imported KB row, every LLM proposal, every mined association is a defeasible claim with provenance. `derive_source_document_trust` produces a `prior_base_rate: float` and a `derived_from: list[str]` and stops. `derived_from` lists step concept IDs (line 149), which is *which world-model concepts were chained*, not *what evidence supports the prior*. The downstream consumers (`propstore/sidecar/passes.py:112-118`, `propstore/praf/engine.py:160`, `propstore/core/row_types.py:466,655-656,722`) treat `prior_base_rate` as an authoritative numeric input to argumentation. There is no opinion uncertainty (no `b/d/u/a` tetrad) — just a float — in direct contradiction to the rest of the codebase, which carries Jøsang opinions everywhere. A heuristic-derived prior should be an `Opinion` with measurable uncertainty, not a bare float.

**H6. Stance proposals carry rich provenance; trust proposals do not even exist as proposals.** `propstore/proposals.py:148-163` builds a `StanceFileDocument` carrying `source_claim`, `classification_model`, `classification_date`, and per-stance opinion provenance from `classify._opinion_payload` (which carries Provenance.status and Provenance.operations). Source-trust calibration has no analog. There is no `TrustProposalDocument`, no `proposal_source_trust` family, no record of *which* heuristic version computed the value, no way to audit a flipped prior between two runs, no way to disagree.

### MEDIUM

**H7. `classify._build_stance_dict` returns `confidence = 0.0` when `stance_type == "none"` AND when opinion is unresolved, conflating two different states.** `classify.py:299-302`. A reader downstream cannot distinguish "no relationship" from "I tried to compute confidence and failed." The `unresolved` field is set independently and exists in `resolution.unresolved_calibration`, so the disambiguation is recoverable, but `confidence = 0.0` on a non-vacuous stance is misleading. See `relate.relate_all_async:259-264` which routes by `stance["type"] != "none"` only — the relate orchestrator never inspects unresolved_calibration, so unresolved-but-typed stances get filed as real stances with confidence 0.

**H8. `derive_source_document_trust` resets `trust["status"] = ProvenanceStatus.DEFAULTED.value` if `derived_from` is empty after a calibration attempt** (`source_trust.py:168-169`). The CALIBRATED status set on line 164 is silently downgraded if no concept-chain steps survived the binding filter. The mechanism: `wm.chain_query` produced a `DETERMINED` value but `claim.artifact_id` was not a non-empty string, so `resolved_from` stayed empty, then `derived_from = resolved_from or derived_from` kept the previous empty list, then the post-hoc downgrade fires. The user gets a `DEFAULTED` trust with a calibrated prior and no record that the world model actually answered. This is provenance *erasure*.

## Non-commitment / disagreement-collapse violations

### HIGH

**H9. `relate_all_async` deduplicates pair candidates by `frozenset({a, b})` keeping shortest distance, then runs *one* bidirectional LLM call per surviving pair.** `propstore/relate.py:67-74` (`dedup_pairs`) and `relate.py:213-220`. Two embedding models can independently rank `(a, b)` and `(b, a)` differently, but after dedup only one direction's embedding distance survives, and that single distance is fed into corpus calibration (`relate.py:223`) and used for *both* forward and reverse stance opinions. This collapses disagreement between the two embedding models into a single number before the LLM ever runs. The "non-commitment discipline" memory says: never collapse disagreement in storage. The deduplication step does exactly that, in-memory, before persistence.

**H10. The single-LLM-call bidirectional classification pattern (`classify.classify_stance_async`) prevents disagreement between forward and reverse from being separately observed.** `classify.py:351-401`. The LLM gets both claims and is *asked* to produce both directions in one response. If the LLM is internally biased to keep forward and reverse consistent (avoid A-rebuts-B + B-supports-A), that bias is now baked into the persisted stances with no detection mechanism. A two-call pattern (independent forward, independent reverse) would let the system observe LLM-internal disagreement. The current one-call design forecloses that observation by construction.

### MEDIUM

**H11. `relate_all_async:258-263` files stances under one source claim regardless of which side the LLM speaks for.** When both forward and reverse non-none stances result, both are appended to `all_stances[source_id]`. The `source_id = claim_a["id"] if stance["target"] == claim_b["id"] else claim_b["id"]` logic is correct, but the result is that `commit_stance_proposals(repo, stances_by_claim, ...)` writes *one* StanceFileDocument per source claim that conflates LLM-classified stances *from* different perspectives. There's no separation between "stances claim A makes about others" and "stances others make about claim A" at the proposal level. This is fine in argumentation theory, but at the proposal lifecycle level it means promoting "A's stances" also promotes downstream-authored "stances *toward* A" if they happened to share a key.

## Boundary leaks (heuristic writing source-layer state)

### HIGH

**H12. The trust calibration path (`finalize_source` and `_auto_finalize_source`) commits heuristic output directly to the source branch without proposal review.** Already noted in H1. Restated here for the boundary lens: the boundary between heuristic and source IS supposed to be the proposal branch. For stances, the boundary holds: heuristic commits to `proposal_stances` (separate branch), an explicit user step calls `promote_stance_proposals` to copy onto the canonical `stances` family. For trust, the boundary doesn't exist: heuristic mutates the SourceDocument *value*, and the next caller persists it on the source branch in the same transaction as `attach_source_artifact_codes`. There is no human in the loop. There is no audit log of *what trust was before* vs. *what trust is now*.

### LOW

**H13. `embed.py` writes embeddings via `SidecarClaimEmbeddingStore`/`SidecarConceptEmbeddingStore`.** Fine — the sidecar is a derived cache, not source storage. But `embed_claims` and `embed_concepts` accept arbitrary model names and `SidecarEmbeddingRegistry` will register *any* model. There is no control over which models are admitted. A typo'd model name silently registers a new model row that downstream `find_similar_disagree` will treat as a disagreeing reference. Not a leak per se, but the embedding registry is treated as a write-anywhere bag.

## Bugs in proposal lifecycle

### HIGH

**H14. `proposals.commit_stance_proposals` reads `transaction.commit_sha` after the `with` block exits.** `proposals.py:182-202`. Lines 199-202 are unindented from the `with repo.families.transact(...)` block. Whether the binding is still valid after `__exit__` depends entirely on the unverified contract of the transaction context manager. If `transaction` invalidates `commit_sha` on exit, the function raises a misleading "stance proposal transaction did not produce a commit" error when the real cause is the ordering bug. (Cluster B already noted the same pattern; restated here for proposal-lifecycle completeness.) Concretely: the lifecycle's *commit step* may be silently broken on certain backend configurations.

**H15. `promote_stance_proposals` does not delete or supersede the source proposal entries after promotion.** `proposals.py:124-145`. The function copies from `proposal_stances` to `stances` and returns. The proposal branch retains all promoted entries forever. Re-running `plan_stance_proposal_promotion` after a promote will re-plan the same items (same filenames, same source_claims) and re-promote, potentially clobbering subsequent edits to the canonical `stances` family. There is no idempotency guard ("this proposal was already promoted at sha X"). For a system that tracks defeasible claims with provenance, the proposal-tip → promoted-tip mapping is missing.

**H16. `plan_stance_proposal_promotion` silently drops typo paths.** `proposals.py:93-101`. When `path` is provided and the requested filename isn't in `available_by_name`, `selected_refs = []` and the function returns a plan with `items=()`. CLI users get a successful "0 promoted" instead of an error. (Also flagged by Cluster B.) For the proposal-lifecycle audit: this means a user can *believe* they promoted a proposal when in fact nothing happened.

### MEDIUM

**H17. `stance_proposal_relpath` and `stance_proposal_branch` pass `cast("Repository", object())` as the repo.** `proposals.py:30-43`. The type cast lies to mypy and the construction depends on `address_for` ignoring the repo argument. Adding any repo-aware logic to `address_for` (e.g., resolving the proposal directory under `repo.root`) breaks all callers silently. There is no test pinning the contract that `address_for` is repo-independent for proposal stances. The proposal lifecycle thus rests on an unwritten contract.

**H18. `commit_stance_proposals` fails loud on empty input** (`proposals.py:179-180`: `raise ValueError("stances_by_claim must not be empty")`) but `relate_claims` in `app/claims.py:601-602` returns an empty `ClaimRelateReport(branch=...)` for the single-claim case when stances are empty. The two are inconsistent: bulk callers must check emptiness themselves, single-claim caller does it implicitly, no one factored this. Minor surface bug, but it shows the lifecycle wasn't designed end-to-end.

## What is RIGHT (so the next iteration doesn't break it)

1. **Stance proposal lifecycle architecture (commit → plan → promote) is the right shape.** Dedicated branch via `PROPOSAL_STANCE_FAMILY`, separate family store, explicit promotion step. Keep this. Apply the same pattern to trust calibration (see Open Q1).
2. **`classify.py` provenance discipline is a model.** Every abstain path constructs a real `Opinion.vacuous(...)` carrying `Provenance(status=ProvenanceStatus.VACUOUS, operations=("stance_classification_error",))`. Each operation is a distinct enum-string. `_opinion_payload` serializes Provenance as a structured payload, not a bare float. The `BaseRateUnresolved` sentinel correctly distinguishes "I have no opinion because I don't know what base rate to use" from "I have an opinion of zero." This is exactly what `feedback_imports_are_opinions` says should happen.
3. **`condition_classifier.classify_conditions` failing loud when Z3 is unavailable** (`condition_classifier.py:30: raise RuntimeError("Z3 condition reasoning is required but unavailable")`) is the right call. No silent fallback to "everything OVERLAP." This matches `feedback_no_fallbacks`.
4. **`relation_analysis.stance_summary` is read-only** and explicitly comments that "all stances participate in AF construction regardless of opinion uncertainty" (line 21-24). It defers filtering to render time. This is the non-commitment discipline applied correctly.
5. **`semantic_passes` substrate** declares `family + input_stage + output_stage` per pass and the runner refuses mismatched stage transitions (`runner.py:38-42`). The pipeline is a typed graph, not a free-for-all. `SemanticPass` is a Protocol with no I/O — a pure transformation contract. This is good infrastructure.
6. **`epistemic_process` records are content-hashed dataclasses** with versioned schemas (`_INVESTIGATION_PLAN_VERSION`, etc.) and `_check_recorded_identity` verifying that recorded `plan_id`/`content_hash` match the computed values on `from_dict`. Evidence-of-integrity is built in.
7. **The `source-heuristic` import contract exists at all.** It catches the obvious mistake of source importing heuristic. Keep it. Add the inverse (see Open Q2).

## Open questions for Q

1. **Should source-trust calibration go through a proposal branch?** Currently `derive_source_document_trust` mutates a SourceDocument and `finalize_source_branch` commits it on the source branch in one transaction. To enforce "heuristic produces proposals only," this would need: a `proposal_source_trust` family, a `commit_trust_proposals` analog of `commit_stance_proposals`, and a `promote_trust_proposals` step. Worth it, or is trust calibration legitimately an inline "compute and stamp" operation because the prior is a function of source metadata + world snapshot?
2. **Should the import-linter contract be expanded to forbid `heuristic -> source.finalize` (the writer surface)?** Currently `source.heuristic.source_trust` imports `propstore.source.common` for *readers* (`load_source_metadata`, `normalize_source_slug`). That's fine. But there's no contract preventing it from importing `propstore.source.finalize.finalize_source_branch` and writing directly. A finer-grained contract (`propstore.heuristic` may not import `propstore.source.finalize` or `propstore.source.passes`) would make the boundary mechanical.
3. **Should `relate_all` use a two-call (forward, then reverse) classification rather than one bidirectional call?** The current single-call design (H10) collapses LLM-internal disagreement between forward and reverse. Two independent calls cost 2× LLM but expose disagreement explicitly, which the rest of the system is designed to preserve.
4. **Is the dedup-by-`frozenset` in `relate.dedup_pairs` (H9) actually the desired semantics?** It assumes embedding-distance is symmetric (`d(a,b) == d(b,a)`) and that taking the minimum is correct. If the embedding store is asymmetric (some sidecar implementations are), this collapses real distance information. Should dedup keep both distances and pass the pair (forward_distance, reverse_distance) into corpus calibration?
5. **Should `commit_stance_proposals` move the `commit_sha` read inside the `with` block?** (H14) This is a 2-line fix.
6. **Should `promote_stance_proposals` track promoted proposals to prevent re-promotion?** (H15) Either record promoted-from sha or delete proposal on promote.
7. **Should `prior_base_rate` in source trust be an `Opinion` rather than a float?** (H5) Lifting it to `Opinion` adds uncertainty representation; it also breaks `propstore.core.row_types` and `propstore.praf.engine.py:160` which read it as a float.
