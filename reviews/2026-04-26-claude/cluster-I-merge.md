# Cluster I: merge / structured_merge

## Scope

Read in full:
- `C:\Users\Q\code\propstore\propstore\merge\__init__.py`
- `C:\Users\Q\code\propstore\propstore\merge\description_kinds.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_claims.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_commit.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_report.py`
- `C:\Users\Q\code\propstore\propstore\merge\structured_merge.py`
- `C:\Users\Q\code\propstore\propstore\structured_projection.py`
- `C:\Users\Q\code\propstore\docs\semantic-merge.md`
- `C:\Users\Q\code\propstore\docs\algorithm-comparison.md` (only marginally merge-relevant)
- Tests: `tests\test_merge_classifier.py`, `tests\test_repo_merge_object.py`, `tests\test_structured_merge_projection.py`, `tests\test_merge_report.py`. `tests\test_assignment_selection_merge.py` lives against `propstore.world.assignment_selection_merge` and is out of merge-module scope. `tests\test_merge_cli.py` is CLI plumbing only and adds no semantic surface.

Paper notes consulted: Konieczny 2002 (IC0–IC8), Coste-Marquis 2007 (PAFs), Booth 2006 (admissible/restrained revision), Roddick 1995 (schema versioning), Bohannon 2006 (lenses), Halpin 2010 / Beek 2018 / Raad 2019 / Melo 2013 (sameAs identity), Buneman 2001 (why-vs-where provenance). Klein 2003, Velegrakis 2004, Flouris 2008 not read for time; flagged in open questions.

## IC merge postulate coverage

The doc `docs\semantic-merge.md` lines 30–34 names Coste-Marquis 2007 and Konieczny & Pino Perez 2002 as literature alignment. The actual coverage in the merge module is patchy.

| Postulate | Status | Evidence |
|---|---|---|
| IC0 (`Δ_µ(Ψ) ⊢ µ`) | Not applicable — no `µ` | `build_merge_framework` (`merge_classifier.py:286-476`) takes only `(snapshot, branch_a, branch_b)`; no integrity-constraint argument. |
| IC1 (consistency under consistent µ) | Trivial — emits all alternatives, no consistency check | n/a |
| IC2 (`⋀Ψ` consistent with µ → result is conjunction) | Violated for non-trivial cases. Two claims that "agree" structurally but differ on `conditions`/`stances`/`context` are emitted as one argument because `_semantic_payload` (`merge_claims.py:127-139`) strips those keys before computing the assertion id. So the merge falsely treats regime-split claims as identical and folds them. | `merge_claims.py:127-139`, used by `merge_classifier.py:113-120` `_claim_semantic_key`/`_claims_equal` and the assertion-id computation in `merge_claims.py:75-91`. |
| IC3 (syntax independence) | Partial. `_stable_json` (`merge_claims.py:158-165`) uses `sort_keys=True`, giving syntactic key-order independence; but no semantic equivalence rewriting. Test `test_syntax_independence_claim_order` and `_filename` (`tests\test_merge_classifier.py:138-179`) only cover ordering and filename moves. |
| IC4 (no source totally overridden) | Structurally OK at storage time. Branch-keyed file refs `_claims_ref_for_argument` (`merge_commit.py:23-33`) keep both rivals on disk. Cite Clark micropublications in the docstring. |
| IC5 / IC6 (sub-merge consistency) | Not enforced. No multi-base merge construction; `build_merge_framework` is binary only (`merge_classifier.py:286-291`). |
| IC7 / IC8 (constraint monotonicity) | n/a — no µ. |

The structured side (`structured_merge.py:346-381` `build_structured_merge_candidates`) delegates to `argumentation.partial_af.{sum,max,leximax}_merge_frameworks`. These names map to Konieczny's Sigma/Max/GMax operator family at the AF level (per Coste-Marquis 2007), but none of the IC postulates are checked locally and no µ-style integrity-constraint surface is exposed. The propstore Konieczny notes already record (`papers/Konieczny_2002.../notes.md:255-260`) that "a per-concept predicate such as 'value is in range' is only a restricted adaptation of µ … do not cite IC0–IC8 for an unconstrained scalar wrapper." The merge code is a less restricted adaptation than that warning describes — it cites IC operators in `docs/semantic-merge.md:124-147` while having no µ at all.

Net: the docs claim "exact AF merge operators" alignment with Konieczny 2002, but the merge-module surface has no integrity-constraint mechanism, no IC2 conjunction (because of the strip), and no IC5–IC8 paths. Either the doc claim should be downgraded or the µ surface should be added.

## Disagreement-collapse audit (non-commitment principle)

The user-stated rule: *never collapse disagreement in storage unless user explicitly requests migration*. I found four collapses, two of them documented as expected-behavior tests.

1. **`_canonical_claim_groups` union-find on shared `logical_id`** (`merge_classifier.py:142-197`). Any artifacts sharing a `logical_id` are unified into one canonical-claim component, with the lexicographically-first logical-id chosen as the label (line 192). This is exactly the `sameAs.cc` closure algorithm Beek 2018 uses on 558M owl:sameAs triples — and Beek's punchline is that the largest closure set conflates Albert Einstein, country names, and the empty string (Beek notes lines 142-146). The merge code applies the same union-find with no quality filter, no Halpin-style graded identity (`sim:claimsIdentical` is non-transitive in Halpin 2010 lines 7-8 of the Similarity Ontology table), no contextual identity in Raad 2019 sense, no Melo 2013 minimum-multicut repair. Test `test_same_logical_id_different_artifacts_merge_as_conflicting_alternatives` (`tests\test_merge_classifier.py:294-323`) documents this collapse to a single `canonical_claim_id` as expected behavior.

2. **`_semantic_payload` strips `conditions`, `stances`, `context`, `provenance`** (`merge_claims.py:127-139`). Two parameter claims with the same `value` and `concept` but different `conditions` are silently treated as semantically equal under `_claims_equal` (`merge_classifier.py:119-120`). `conditions` is the precise mechanism for encoding regime splits. After this strip, regime-disagreeing claims look identical to the merge code unless they reach the `_classify_pair` path (which only fires when `_claims_equal` already returned False). This is a HIGH-severity collapse because the conflict-vs-phi distinction was explicitly carved out in `docs/semantic-merge.md:91-97` and the code's own `_classify_pair` knows about regime splits — but the equality check upstream defeats it.

3. **Assertion-id collision folds independent corroborating claims**. `MergeClaim.assertion` (`merge_claims.py:75-87`) computes the situated `assertion_id` from `_semantic_payload(self.document)`, which strips `provenance` (line 134). Two claims from different papers with identical statement/concept/value collide on the same `assertion_id`. `_deduplicate_arguments` (`merge_classifier.py:479-490`) then keeps only one argument, merging branch_origins. Test `test_create_merge_commit_collapses_duplicate_assertions_without_candidate_bucket` (`tests\test_repo_merge_object.py:255-296`) and the report version `test_merge_report_collapses_duplicate_assertion_identity_without_candidate_bucket` (`tests\test_merge_report.py:186-229`) lock in this behavior: two claims with `artifact_id=ps:claim:leftcandidate0001` (paper `left_paper`) and `ps:claim:rightcandidate0001` (paper `right_paper`), same statement text, collapse to a single argument and `semantic_candidates == []`. **Two papers independently asserting the same statement is information** (corroboration count, agreement across sources). Folding them to one assertion at storage time loses that. This is a collapse-of-disagreement on the *non*-disagreement axis: the system can no longer distinguish "one paper said it" from "two papers said it."

4. **`build_structured_merge_candidates` returns merged AFs** (`structured_merge.py:346-381`). Sum / Max / Leximax operators inherently pick a winning merged AF (or a small set). When called with the documented `operator="sum"` default, this yields a single AF that drops attack-relations not chosen by the aggregation. Coste-Marquis 2007 framing makes this an aggregation, not a storage decision — but exposing it as the structured merge boundary without a back-mapping from merged-AF arguments to source claim ids means consumers cannot recover which source's attack relation was overridden. `argumentation_evidence_from_projection` (`structured_merge.py:66-93`) only handles a single per-branch projection, not the merged-AF candidate.

Mitigating factors found: `_claims_ref_for_argument` does branch-keyed file refs for rivals (`merge_commit.py:23-33`), and `MergeArgument.branch_origins` is preserved through to the manifest (test `test_merge_commit_preserves_branch_origin_provenance` `tests\test_merge_classifier.py:326-358`). These mitigate (1) at the file level but not at the canonical-claim-id level.

## sameAs / identity-merge correctness

The relevant code is the union-find in `_canonical_claim_groups` (`merge_classifier.py:142-197`).

- **Halpin 2010** distinguishes 8 graded identity properties (`sim:sameIndividual` reflexive+symmetric+transitive vs `sim:claimsIdentical` reflexive+symmetric+*not* transitive). The merge code treats every shared `logical_id` as a transitive equivalence assertion. There is no Similarity Ontology distinction. A logical-id alias chain `A↔B`, `B↔C` makes A,B,C one component (`_union` lines 154-158, `_find` lines 147-152) — full transitive closure — even if the two assertions originate from different papers with different identity criteria.
- **Beek 2018** empirical demonstration: transitive closure on 558M owl:sameAs triples produces a 177,794-member set conflating Einstein with countries. The propstore code is structurally identical (union-find with merge-by-rank — Beek section 3.3, propstore lines 154-158). No quality filter at all.
- **Raad 2019** notes contextual identity is needed; transitivity propagates errors. The merge module has no notion of identity context.
- **Melo 2013** treats erroneous identity-link removal as a minimum multicut. None of this defensive machinery exists in the merge code; the union-find runs unconditionally over whatever logical-ids appear in any branch's claim documents.
- **`_canonical_claim_groups` label choice** at line 192: `component_label[root] = logical_candidates[0] if logical_candidates else sorted(artifact_ids)[0]`. The canonical label is the lexicographically-first `logical_id` in the component. Arbitrary by lexical order, no semantic basis. Two branches that produce different orderings will (because the input is sorted at line 170) get a deterministic but arbitrary label.

Concrete failure scenario: a branch added a `logical_id = ("pubmed", "12345")` alias to claim X (because some auto-extraction step decided pubmed:12345 and the existing claim are the same paper). Another branch added the same `logical_id` to claim Y for a different reason. Building the merge framework now unifies X and Y into one canonical-claim group, even if X and Y are about completely different propositions. Both rival claims will be emitted as `MergeArgument`s and the framework will note them as candidates, but the canonical-claim-id is now an artifact of the bad alias rather than the actual semantics. The `summarize_merge_framework` `canonical_groups` (`merge_report.py:74-80`) carries this conflation forward into reports.

The recommended fix is to treat every `logical_id` link as a defeasible claim with provenance (per the project's own `feedback_imports_are_opinions` memory entry) and run the merge over those defeasible claims rather than committing to union-find at storage time.

## Bugs

### HIGH

- **HIGH-1 — Disagreement-collapse via assertion-id computation excluding provenance.** `merge_claims.py:75-87` (`MergeClaim.assertion`) hashes `_semantic_payload` which drops `provenance` (`merge_claims.py:134`). `_deduplicate_arguments` (`merge_classifier.py:479-490`) then keys only on `assertion_id`. Two papers with identical statement/concept fold to one argument. Confirmed expected behavior by `tests\test_repo_merge_object.py:255-296` and `tests\test_merge_report.py:186-229`. Violates the non-commitment principle: corroboration count is lost.

- **HIGH-2 — Regime-split disagreement equated as identity.** `_semantic_payload` (`merge_claims.py:127-139`) strips `conditions`, `stances`, `context`. `_claim_semantic_key` (`merge_classifier.py:113-116`) and `_claims_equal` (`merge_classifier.py:119-120`) then treat two parameter-claims with same value but different `conditions` as equal. In the conflict path the regime-split is detected by `_classify_pair`, but the upstream `if _claims_equal(...)` short-circuit at `merge_classifier.py:338-346` prevents `_classify_pair` from running for these.

- **HIGH-3 — Union-find sameAs collapse on `logical_id`.** `_canonical_claim_groups` (`merge_classifier.py:142-197`) unconditionally transitively closes any shared logical-id. This is the Beek 2018 / Halpin 2010 / Raad 2019 documented failure mode. No graded identity, no context, no error detection, no Halpin `sim:claimsIdentical` non-transitivity option, no Melo 2013 multicut repair.

- **HIGH-4 — `_classify_pair` fall-through heuristic.** `merge_classifier.py:254-256`: when the conflict detector returns no record, the code uses `_extract_concept(left) != _extract_concept(right)` as the COMPATIBLE/CONFLICT decider. That heuristic is silently default-CONFLICT when concepts match and silently default-COMPATIBLE when they differ. Both choices will be wrong in many real cases (different concepts that contradict; same concept that doesn't actually conflict). No documented justification, no reference to Konieczny or Coste-Marquis.

### MED

- **MED-1 — `Z3TranslationError` silently demoted to PHI_NODE.** `merge_classifier.py:236-240`. When Z3 fails to translate a condition AND the two sides have different conditions, the code returns `_DiffKind.PHI_NODE`. A real translation error becomes a "regime split" without any warning surfaced. The original `Z3TranslationError` is then re-raised only when conditions match. Failure mode: a condition the project cannot z3-translate becomes "this is just a different regime, no conflict."

- **MED-2 — `_materialized_claim_payload` mutates `artifact_id` and drops `branch_origin` from materialized provenance for rivals.** `merge_commit.py:36-46`. Sets `payload["artifact_id"] = argument.assertion_id` and `provenance.pop("branch_origin", None)`. The materialized claim file then has identity that does not match any branch source. The branch-origin info still exists in the manifest, but the materialized claim alone — what most downstream consumers will read — has lost the branch_origin from its provenance dict. This is a Buneman 2001 where-provenance violation; the rewrite (storage merge) is not traceable.

- **MED-3 — `source.paper` overwritten to literal `"merged"`.** `merge_commit.py:128`. The materialized claim file's `source.paper` field is set to `"merged"`, dropping the original paper identity. Buneman why-provenance violation. Anyone reading `claims/merged*.yaml` and looking at `source.paper` sees `"merged"` rather than the real source.

- **MED-4 — Synthetic `comparison_source = "merge_comparison"` leaks into conflict_detector.** `merge_classifier.py:208-215`. When neither side has paper provenance, the literal string `"merge_comparison"` is fed into `conflict_claim_from_payload(source_paper=...)`. This synthetic paper id may then appear in any conflict record produced downstream and contaminate the conflict-detector audit trail.

- **MED-5 — Asymmetric branch precedence on non-claim files.** `merge_commit.py:75-82`: `right_entries` are written first, then `left_entries` overwrite. So branch_a (the "left") wins on non-claim files. Roddick 1995 §1.2 calls out symmetry as a pragmatic requirement (`papers/Roddick_1995.../notes.md:81`). Swapping `branch_a, branch_b` would yield a different non-claim materialization. No test covers this; deterministic-merge test `test_conflict_merge_is_deterministic` only checks same-args repeat-call, not swap.

- **MED-6 — Tests freeze undesired behavior.** `tests\test_repo_merge_object.py:255-296` and `tests\test_merge_report.py:186-229` lock in HIGH-1 (cross-paper assertion-id collapse) as expected behavior. `tests\test_merge_classifier.py:294-323` locks in HIGH-3 (logical-id union-find) as expected. These tests will block any non-commitment-principle fix.

### LOW

- **LOW-1 — Tempfile per branch grounding bundle build.** `structured_merge.py:154-166` `_read_branch_grounding_bundle` creates a fresh `tempfile.TemporaryDirectory`, writes a sidecar SQLite, opens it, reads the bundle, closes. Per branch, per call to `build_branch_structured_summary`. No cache. `build_structured_merge_candidates` calls it twice (once per branch — `structured_merge.py:367-370`). Slow and wasteful for repeated merges.

- **LOW-2 — Only `grounded` semantics in argumentation evidence.** `structured_merge.py:74-75` raises ValueError otherwise. `compute_structured_justified_arguments` (`structured_projection.py:240-261`) supports `preferred` and `stable`. The merge surface is artificially narrower than the projection surface.

- **LOW-3 — Lens GetPut violated by `artifact_id` mutation.** Per Bohannon 2006: a GetPut-respecting lens requires `put(get(s), s) = s`. `create_merge_commit` materializes an artifact with `artifact_id = assertion_id` for rivals, so reading the merged tree back as branch state then merging again will not yield the same source state. Implication for repeated merges and merge-of-merge composition — not currently tested.

- **LOW-4 — `build_structured_merge_candidates` returns merged AFs with no claim back-mapping.** `structured_merge.py:346-381` returns `list[ArgumentationFramework]` directly. The argument ids in the merged AF are no longer connected to the underlying claim ids the way `BranchStructuredSummary.projection.argument_to_claim_id` connects them within a single branch. Consumers cannot lift the merge result back to assertion ids the way `argumentation_evidence_from_projection` does for a single branch.

- **LOW-5 — Empty grounding bundle is built even when no claims.** `structured_merge.py:324-331`: only builds the projection if `active_claims` is non-empty, otherwise constructs `_empty_projection()`. Good. But `_BranchSnapshotStore.grounding_bundle` is lazy (line 145-151), so the cost is paid only on the projection path. OK.

- **LOW-6 — `coreference_query` exposes preferred/stable but does nothing with attacks beyond grounded.** `description_kinds.py:27-44`. The semantics dispatch is fine; just orphaned because nothing in the merge module routes to non-grounded.

- **LOW-7 — `_claim_candidate_key` excludes `logical_ids`** (`merge_classifier.py:123-126`). This means the `semantic_candidates` grouping treats two arguments with different logical-id sets but same payload as candidates. Probably what is intended, but interacts badly with HIGH-3: candidates are grouped across canonical components, then filtered out when `len({argument_index[claim_id].canonical_claim_id for claim_id in claim_ids}) > 1` (line 459) requires *more than one* canonical group. The filter is `> 1`, meaning candidates from a single canonical group are dropped, which contradicts the intuitive purpose of `semantic_candidates`. Worth verifying intent.

## Missing features

- **No integrity-constraint µ surface.** Konieczny IC merging is built around `Δ_µ(Ψ)`. The merge module accepts no µ and provides no place to put one. If µ is to remain "out of scope," the doc claims about Konieczny alignment should be downgraded. If it is in scope, an IntegrityConstraint surface needs to thread through `build_merge_framework`.

- **No multi-base merge.** `build_merge_framework` is binary. Konieczny postulates IC5/IC6 are about merging belief multisets `Ψ₁ ⊔ Ψ₂`. Coste-Marquis 2007 Proposition 35 / Definition 38 (majority PAF) all assume n-ary profiles. Cannot verify those properties without n-ary support.

- **No graded sameAs.** Halpin 2010's Similarity Ontology (sameIndividual / claimsIdentical / almostSameAs etc.) is the textbook fix for the union-find collapse. Not present.

- **No identity-link quality scoring or repair.** Melo 2013 minimum multicut, Raad 2018 network metrics. Not present. The merge runs blind.

- **No witness basis / minimal witness basis.** Buneman 2001 minimal witness basis (`papers/Buneman_2001.../notes.md:130`) is the formal object that should accompany every merged claim — the smallest justifying source set. The `MergeArgument.branch_origins` is a coarse approximation but not a Buneman witness basis.

- **Where-provenance not preserved across the merge_commit rewrite.** Buneman 2001 Proposition 2 requires traceable queries for where-provenance preservation. `_materialized_claim_payload` is not traceable: it mutates `artifact_id` and drops `branch_origin` from provenance.

- **No back-mapping from merged-AF candidates to claim ids.** `build_structured_merge_candidates` returns `list[ArgumentationFramework]` with no `argument_to_claim_id` mapping for the merged frameworks. Consumers can't lift a merge candidate to assertion ids the way they can for a single branch.

- **No structured-merge support beyond `grounded`.** `argumentation_evidence_from_projection` rejects everything else.

- **No revision-style operator (admissible / restrained).** Booth 2006 frames how to combine prior epistemic state with new input. The merge module is purely binary set-merge; there is no "current state revised by branch B" operation. If the project intends to support iterated branch absorption, Booth's admissibility criterion (`P` postulate) and lexicographic / restrained operator distinction would apply.

- **No schema-versioning awareness for non-claim families.** Roddick 1995 distinguishes evolution (no data loss) from versioning (history retained). Stances, contexts, conditions, and other family files are merged left-over-right (`merge_commit.py:75-82`) with no checks. If branch_a and branch_b each modified the same stance file, branch_a wins silently — schema modification, not evolution.

## Open questions for Q

1. Is the cross-paper `assertion_id` collapse (HIGH-1) intentional? The tests freeze it as expected behavior, but it conflicts with the non-commitment principle and erases corroboration count. If intentional, the docstring on `MergeClaim.assertion` should state "two papers with identical content collapse to one argument" loudly. If not, the assertion-id needs to fold provenance.

2. Is the `logical_id` union-find (HIGH-3) intentional? Per `feedback_imports_are_opinions`, every imported KB row is a defeasible claim. Logical-id aliases are KB rows. Should they be defeasibly merged through the argumentation layer rather than committed to via union-find at the storage merge boundary?

3. Should `_semantic_payload` keep `conditions` and `stances` in the equality key? Stripping them silently equates regime-split claims, which contradicts the `_classify_pair` regime-split detection downstream.

4. Should the merge module accept an integrity-constraint µ? If yes, what shape — a CEL expression, a render policy, a separate `Constraint` family? If no, the docs/semantic-merge.md Konieczny alignment claim should be downgraded.

5. Is `build_structured_merge_candidates` intended as a render-time aggregation (caller commits to one) or a storage-time aggregation (multiple stored candidates)? If render, document that and warn callers; if storage, the project's non-commitment principle is again at risk.

6. Should `merge_commit.py` preserve full `provenance.paper` instead of overwriting with `"merged"`? Buneman 2001 why-provenance argues yes; current behavior loses the source identity of the materialized claim file.

7. Is the asymmetric branch precedence on non-claim files (`merge_commit.py:75-82`, branch_a wins) intentional? Roddick 1995 symmetry would say no. Tests don't catch it.

8. Should `Z3TranslationError` ever silently demote to PHI_NODE? Current behavior at `merge_classifier.py:236-240` hides translation failures behind a regime-split label. A noisier failure mode (e.g. a third `_DiffKind.UNTRANSLATABLE` that records the error) would preserve information.

9. Klein 2003 / Velegrakis 2004 / Flouris 2008 paper notes were not read for time. Likely relevant to ontology evolution / change classification / mapping consistency under schema change. Worth a follow-up cluster pass.

10. The `MergeClaim` document strips `provenance` for assertion-id but `provenance_payload()` still includes `branch_origin` (`merge_claims.py:99-107`). Two assertions with the same content but different `branch_origin` will have the same assertion id but different `provenance_payload`. Is the design intent that branch_origin is metadata-only and not part of identity? If so, the materialized payload at `merge_commit.py:43-44` correctly pops it, but then where-provenance is lost. The two design choices interact badly and should be explicit.
