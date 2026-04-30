# WS-L: Merge non-commitment & sameAs discipline

**Status**: CLOSED 8485babf
**Depends on**: WS-E (source/promote provenance must be present in claim documents before assertion-id can fold it)
**Blocks**: nothing
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Why this is essential

The propstore design principle is explicit: *never collapse disagreement in storage unless the user explicitly requests migration.* The merge module violates this principle in four distinct ways at storage time, three of them locked in by tests. Two papers asserting the same proposition collapse to one argument; logical-id aliases run union-find with no quality filter (the Beek 2018 pathology); regime-split claims with different `conditions` are folded by the assertion-id hash; and `_classify_pair` decides COMPATIBLE vs CONFLICT by an undocumented heuristic over `_extract_concept`.

The corroboration case is the simplest illustration. When `left_paper` and `right_paper` both state "X causes Y," that is *two* pieces of information: the proposition and the independent agreement of two sources. The current code collapses them to one `MergeArgument` with merged `branch_origins` and `semantic_candidates=[]`. A reader of the resulting manifest cannot tell whether one paper or twenty supports the claim. The tests at `tests/test_repo_merge_object.py:255-296` and `tests/test_merge_report.py:186-229` lock the collapse in as expected behavior.

The sameAs case is the textbook pathology Beek 2018 documented over 558M owl:sameAs triples — the largest closure component conflated Einstein, country names, and the empty string — and the merge module reproduces the algorithm verbatim: union-find with merge-by-rank, lexicographic label choice, no Halpin Similarity Ontology distinction, no Melo 2013 multicut, no Raad 2019 contextual identity. A single bad logical-id alias collapses the whole component into one `canonical_claim_id`. The `feedback_imports_are_opinions` memory entry says every imported KB row is a defeasible claim with provenance; logical-id aliases are KB rows; the merge module treats them as truth.

WS-L closes these by reshaping the assertion-id, replacing `_canonical_claim_groups` union-find with defeasible sameAs assertions, fixing materialized-payload provenance loss, fixing symmetric-merge violations on non-claim files, surfacing `Z3TranslationError`, exposing an integrity-constraint µ surface for Konieczny IC merging, and adding the n-ary / graded-identity / witness-basis / schema-versioning hooks the cluster-I report flagged.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed has a green test gating it before WS-L is marked CLOSED.

### Tier-3 non-commitment findings

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T3.3** | Claude REMEDIATION-PLAN Tier 3 | `propstore/merge/merge_claims.py:127-139` (`_semantic_payload`); `:75-87` (`MergeClaim.assertion`) | `_semantic_payload` strips `provenance`, `conditions`, `stances`, `context` from the claim payload before hashing into `assertion_id`. Two papers asserting the same statement collide on `assertion_id`; `_deduplicate_arguments` then folds them. Cross-paper assertion-id collapse. |
| **T3.4** | Claude REMEDIATION-PLAN Tier 3 | `propstore/merge/merge_classifier.py:142-197` (`_canonical_claim_groups`) | Union-find on shared `logical_id` with no quality filter. Beek 2018 pathological algorithm reproduced. No graded identity, no contextual identity, no minimum-multicut repair. |

### Cluster I HIGH

| Finding | Citation | Description |
|---|---|---|
| **HIGH-1** | `merge_claims.py:75-87`, `:127-139`; `merge_classifier.py:479-490` | Cross-paper assertion-id collapse. Confirmed by `tests/test_repo_merge_object.py:255-296` (`test_create_merge_commit_collapses_duplicate_assertions_without_candidate_bucket`) and `tests/test_merge_report.py:186-229`. |
| **HIGH-2** | `merge_claims.py:127-139` (strips `conditions`); `merge_classifier.py:338-346` then `:479-490` | Regime-split disagreement equated as identity. Two parameter-claims with same value but different `conditions` first emit two arguments (because `_claim_semantic_key` at `:113-116` retains conditions, so `_claims_equal` returns False), then share `assertion_id` (because `_semantic_payload` strips conditions) and `_deduplicate_arguments` folds them. The user-visible outcome: regime-disagreeing claims are stored as one. |
| **HIGH-3** | `merge_classifier.py:142-197` | Union-find sameAs collapse. Cite Halpin 2010, Beek 2018, Melo 2013, Raad 2019. |
| **HIGH-4** | `merge_classifier.py:254-256` | `_classify_pair` fallthrough heuristic: when the conflict detector returns no record, the code uses `_extract_concept(left) != _extract_concept(right)` as the COMPATIBLE/CONFLICT decider. Different concepts → COMPATIBLE silently; same concept → CONFLICT silently. No documented justification, no paper citation. |

### Cluster I MED

| Finding | Citation | Description |
|---|---|---|
| **MED-1** | `merge_classifier.py:236-240` | `Z3TranslationError` silently demoted to `PHI_NODE` when conditions differ. A real translation error is hidden behind a regime-split label. |
| **MED-2** | `merge_commit.py:36-46` | `_materialized_claim_payload` mutates `artifact_id := assertion_id` and pops `branch_origin` from provenance. Buneman 2001 where-provenance violation. |
| **MED-3** | `merge_commit.py:128` | `source.paper` overwritten to literal `"merged"`. Buneman 2001 why-provenance violation. |
| **MED-4** | `merge_classifier.py:208-215` | Synthetic `comparison_source = "merge_comparison"` literal leaked into `conflict_claim_from_payload(source_paper=...)`. May appear in any conflict record produced downstream, contaminating the conflict-detector audit trail. |
| **MED-5** | `merge_commit.py:75-82` | `right_entries` written first, then `left_entries` overwrite. `branch_a` (the left) wins on non-claim files. Roddick 1995 §1.2 calls out symmetry as a pragmatic requirement. No test covers the swap. |
| **MED-6** | `tests/test_repo_merge_object.py:255-296`, `tests/test_merge_report.py:186-229`, `tests/test_merge_classifier.py:294-323` | Tests pin the current incorrect behavior. Closing WS-L requires changing or removing these tests with a paper-trail rationale. |

### Cluster I missing features

| Finding | Description |
|---|---|
| **No IC µ surface** | `build_merge_framework` accepts no integrity constraint. Konieczny IC0/IC7/IC8 unverifiable. |
| **No multi-base merge** | Binary only (`merge_classifier.py:286-291`). Konieczny IC5/IC6 and Coste-Marquis 2007 majority/leximax PAFs assume n-ary profiles. |
| **No graded sameAs** | Halpin 2010 Similarity Ontology (`sim:sameIndividual`, `sim:claimsIdentical`, `sim:almostSameAs`) — textbook fix for the union-find collapse. |
| **No identity-link quality** | Melo 2013 minimum multicut. Raad 2019 network metrics. Not present. |
| **No witness basis** | Buneman 2001 minimal witness basis. `MergeArgument.branch_origins` is a coarse proxy. |
| **No AF support beyond grounded** | `argumentation_evidence_from_projection` (`structured_merge.py:73-74`) raises ValueError for `preferred`/`stable` though `compute_structured_justified_arguments` supports both. |
| **No Booth admissible/restrained** | Booth 2006 revision operators absent. |
| **No schema-versioning awareness** | Roddick 1995 evolution vs versioning. Stances, contexts, conditions merged left-over-right. |
| **No back-mapping from merged-AF candidates** | `build_structured_merge_candidates` returns `list[ArgumentationFramework]` with no `argument_to_claim_id`. |

## Code references (verified by direct read)

### Assertion-id is provenance-blind
- `propstore/merge/merge_claims.py:75-87` — `MergeClaim.assertion` builds a `SituatedAssertion` whose `RoleBinding("content", _stable_json(_semantic_payload(self.document)))` becomes the identity payload.
- `propstore/merge/merge_claims.py:127-139` — `_semantic_payload` pops `artifact_id`, `artifact_code`, `id`, `logical_ids`, `version_id`, `provenance`, `stances`, `context`, `conditions`. The `provenance_ref` at line 86 is built separately and is not part of `assertion_id` identity in the dedup path used by `_deduplicate_arguments`.

### Union-find sameAs (Beek 2018 pathological algorithm)
- `propstore/merge/merge_classifier.py:142-197` — `_canonical_claim_groups` builds `parent`/`_find`/`_union`, walks every `artifact_id` sharing a `logical_id`, and unions them. Line 192 picks the lexicographically-first `logical_id` as the canonical label. No quality filter, no provenance check, no graded identity.

### Equality and dedup paths
- `propstore/merge/merge_classifier.py:113-116` — `_claim_semantic_key` skips only `artifact_id`, `version_id`, `provenance`. **Retains** `conditions`, `stances`, `context`. So `_claims_equal` is condition-sensitive.
- `propstore/merge/merge_classifier.py:119-120` — `_claims_equal` calls `_claim_semantic_key`.
- `propstore/merge/merge_classifier.py:338-346` — short-circuit emits one argument when `_claims_equal` is True.
- `propstore/merge/merge_classifier.py:479-490` — `_deduplicate_arguments` keys on `assertion_id`. Because `assertion_id` strips conditions, two arguments emitted by different paths (with different conditions) collide here and are folded.

### Classify-pair fallthrough
- `propstore/merge/merge_classifier.py:208-215` — synthetic `comparison_source = "merge_comparison"` when neither side has paper provenance.
- `propstore/merge/merge_classifier.py:236-240` — `Z3TranslationError` → `PHI_NODE` if conditions differ, else re-raise.
- `propstore/merge/merge_classifier.py:254-256` — fallthrough decision: different concept → COMPATIBLE; same concept → CONFLICT.

### Materialized-claim provenance loss
- `propstore/merge/merge_commit.py:36-46` — `_materialized_claim_payload` mutates `artifact_id` to `assertion_id` for rivals and pops `branch_origin` from `provenance`. Buneman 2001 where-provenance is no longer recoverable from the materialized file alone.
- `propstore/merge/merge_commit.py:75-82` — right written first, left overwrites. Branch_a wins.
- `propstore/merge/merge_commit.py:128` — `"paper": "merged"` literal. Buneman 2001 why-provenance violation.

### Structured merge surface
- `propstore/merge/structured_merge.py:66-93` — `argumentation_evidence_from_projection` only supports `grounded`. Raises `ValueError` otherwise.
- `propstore/merge/structured_merge.py:346-381` — `build_structured_merge_candidates` returns `list[ArgumentationFramework]` with no claim back-mapping.

### Tests pinning incorrect behavior
- `tests/test_repo_merge_object.py:255-296` — `test_create_merge_commit_collapses_duplicate_assertions_without_candidate_bucket`. Two artifacts with `paper="left_paper"` and `paper="right_paper"`, identical `statement`, collapse to one argument and `semantic_candidates == []`.
- `tests/test_merge_report.py:186-229` — same collapse asserted at the report layer.
- `tests/test_merge_classifier.py:294-323` — `test_same_logical_id_different_artifacts_merge_as_conflicting_alternatives`. Documents union-find collapse to one `canonical_claim_id` as expected behavior.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_merge_corroboration_preserved.py`** (new — gating sentinel)
   - Two papers `left_paper` and `right_paper` each commit the same statement text on distinct artifact_ids and logical_ids. After `create_merge_commit`: `len(manifest["merge"]["arguments"]) == 2`; corroboration field records both as independent supporters.
   - **Must fail today**: collapses to 1 argument with merged `branch_origins`.

2. **`tests/test_merge_assertion_id_includes_provenance.py`** (new)
   - Two `MergeClaim`s with identical document content but distinct `provenance.paper`. Asserts `claim_a.assertion_id != claim_b.assertion_id`.
   - **Must fail today**: `_semantic_payload` strips provenance.

3. **`tests/test_merge_regime_split_preserved.py`** (new)
   - Two parameter claims, same concept/value, different `conditions` (e.g., `T<100` vs `T>=100`). After `build_merge_framework`: two distinct `MergeArgument`s, ignorance edge.
   - **Must fail today**: collide on `assertion_id` (conditions stripped), then deduplicated.

4. **`tests/test_canonical_claim_groups_no_union_find.py`** (new)
   - Logical-id alias chain `A↔B`, `B↔C` from three papers. Asserts A, B, C are NOT in one component unless each link has a non-defeated `sameAs_assertions` record.
   - **Must fail today**: union-find unconditionally unions them.

5. **`tests/test_classify_pair_no_concept_fallthrough.py`** (new)
   - Conflict detector returns no record. Concepts match → asserts `UNKNOWN`, not `CONFLICT`. Concepts differ → asserts `UNKNOWN`, not `COMPATIBLE`.
   - **Must fail today**: lines 254-256 default to CONFLICT/COMPATIBLE.

6. **`tests/test_z3_translation_error_surfaced.py`** (new)
   - `Z3TranslationError` triggered, conditions differ. Asserts a third `_DiffKind.UNTRANSLATABLE` recording the exception, or re-raise. Not `PHI_NODE`.
   - **Must fail today**: `merge_classifier.py:236-240` returns `PHI_NODE`.

7. **`tests/test_materialized_claim_provenance_preserved.py`** (new)
   - After `create_merge_commit` with rivals from `left_paper`/`right_paper`: each materialized claim's `provenance.paper` is its real source, not `"merged"`; `provenance.branch_origin` present.
   - **Must fail today**: `merge_commit.py:128` overwrites paper; `:44` pops branch_origin.

8. **`tests/test_merge_symmetry_non_claim_files.py`** (new)
   - Branch A and B each carry a different `concepts/foo.yaml`. Swap-call `create_merge_commit`. Asserts either identical materialization or a surfaced `MergeConflictRecord` (no silent left-wins).
   - **Must fail today**: `:75-82` lets branch_a win.

9. **`tests/test_comparison_source_no_synthetic_paper.py`** (new)
   - `_classify_pair` on two claims with no paper provenance. Asserts no conflict-record field contains `"merge_comparison"`.
   - **Must fail today**: `:215` injects this synthetic source.

10. **`tests/test_ic_postulate_coverage.py`** (new — Konieczny IC properties via Hypothesis)
    - IC2 conjunction; IC4 no-override; IC5/IC6 sub-merge consistency for n-ary; IC7/IC8 µ monotonicity.
    - **Must fail today**: `build_merge_framework` accepts no µ and no n-ary profile.

11. **`tests/test_structured_merge_supports_preferred_stable.py`** (new)
    - `argumentation_evidence_from_projection(..., semantics="preferred"/"stable")` returns multi-extension evidence (Caminada/Polberg).
    - **Must fail today**: `structured_merge.py:73-74` raises ValueError.

12. **`tests/test_workstream_l_done.py`** (new — gating sentinel)
    - `xfail` until WS-L closes. Per Mechanism 2 in REMEDIATION-PLAN Part 2.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-L step N — <slug>`.

### Step 1 — Fold provenance into assertion-id

`propstore/merge/merge_claims.py:127-139`: change `_semantic_payload` to keep `provenance` (specifically the source-paper component) in the hash. Decision point: should the provenance fold include paper id only, or paper id + page + extraction date? Follow Trusty URI / nanopub practice (Kuhn 2014 cited in T4.2): content-identity includes everything that makes the assertion citable. Recommend paper-id + paper-version (if present) + the document `provenance.paper` field. Do NOT include `branch_origin` (which is merge-internal metadata).

Acceptance: `test_merge_assertion_id_includes_provenance.py` and `test_merge_corroboration_preserved.py` turn green. Delete `tests/test_repo_merge_object.py:255-296` and `tests/test_merge_report.py:186-229` with a commit message citing the principle. Per Q's "no old repos" rule, no shim, no compatibility flag.

### Step 2 — Keep `conditions` in assertion-id; surface PHI_NODE where they differ

`merge_claims.py:127-139`: also keep `conditions` in `_semantic_payload`. Two regime-split claims now have distinct `assertion_id`s and survive `_deduplicate_arguments`. Verify the downstream `_classify_pair` correctly classifies them as PHI_NODE (already supported via `_DiffKind.PHI_NODE`).

Acceptance: `test_merge_regime_split_preserved.py` turns green.

### Step 3 — Replace union-find on `logical_id` with defeasible `sameAs_assertions`

`propstore/merge/merge_classifier.py:142-197`: do NOT do union-find. Instead, emit a `sameAs_assertions` family record per logical-id alias claim, with provenance. The merge boundary delegates to the argumentation layer: if `sameAs(A, B)` is grounded-accepted, A and B share a canonical_claim_id; otherwise they remain distinct.

Sub-steps:
- 3a: define `propstore/families/sameas/` family schema with `(left_artifact_id, right_artifact_id, evidence_source, provenance)`.
- 3b: a Halpin Similarity Ontology vocab — `sim:sameIndividual` (RST), `sim:claimsIdentical` (RS, not T), `sim:almostSameAs` (RS, not T). Per-assertion type field.
- 3c: `_canonical_claim_groups` reads `sameAs_assertions`, treats them as defeasible inputs to argumentation, takes the grounded extension, only THEN unions artifacts in accepted components.
- 3d: a Melo 2013 minimum-multicut hook for erroneous-link repair. Surface the cut as a report rather than auto-applying.

Acceptance: `test_canonical_claim_groups_no_union_find.py` turns green. Delete `tests/test_merge_classifier.py:294-323` with rationale.

### Step 4 — Fix `_classify_pair` fallthrough

`merge_classifier.py:254-256`: replace the concept-comparison heuristic with `_DiffKind.UNKNOWN` and a recorded reason string. The CONFLICT/COMPATIBLE choice must come from the conflict-detector, not from a side-channel concept comparison. If conflict-detector returns nothing, the system does not know. Make ignorance explicit.

Acceptance: `test_classify_pair_no_concept_fallthrough.py` turns green.

### Step 5 — Surface Z3TranslationError

`merge_classifier.py:236-240`: introduce `_DiffKind.UNTRANSLATABLE` (or re-raise unconditionally and let the caller record the failure). PHI_NODE means "different regime, no conflict." A translation failure is not a regime split.

Acceptance: `test_z3_translation_error_surfaced.py` turns green.

### Step 6 — Stop synthetic comparison_source

`merge_classifier.py:208-215`: when neither side has paper provenance, do NOT synthesize `"merge_comparison"`. Instead, pass `source_paper=None` to `conflict_claim_from_payload` (if the API allows) or raise a typed error stating the merge cannot be performed without provenance. The latter is better — provenance gaps should surface, not be papered over.

Acceptance: `test_comparison_source_no_synthetic_paper.py` turns green.

### Step 7 — Preserve provenance through materialization

`merge_commit.py:36-46`: stop mutating `artifact_id`. Stop popping `branch_origin`. The materialized claim payload should preserve all provenance keys. If two rival claims share an `artifact_id`, keep both with full identity — the branch-keyed file ref at `_claims_ref_for_argument` already handles separate citability.

`merge_commit.py:128`: stop overwriting `source.paper` with `"merged"`. Either preserve the original paper, or use a list (`source.papers: [left_paper, right_paper]`).

Acceptance: `test_materialized_claim_provenance_preserved.py` turns green.

### Step 8 — Symmetric non-claim file merge

`merge_commit.py:75-82`: replace the left-wins policy with explicit conflict-record emission for any path where `right_entries[path] != left_entries[path]`. Roddick 1995 distinguishes evolution from versioning; conflicts must be visible, not silently resolved.

Acceptance: `test_merge_symmetry_non_claim_files.py` turns green.

### Step 9 — Structured-merge `preferred` and `stable` semantics

`structured_merge.py:73-74`: route `preferred` and `stable` to `compute_structured_justified_arguments` from `propstore/structured_projection.py:240-261` (which already supports them). Preserve multi-extension by returning a `BranchArgumentationEvidence` whose `accepted_assertion_ids` is the *credulous* set and a new `skeptical_assertion_ids` is the *skeptical* set, never reducing to a single extension.

Acceptance: `test_structured_merge_supports_preferred_stable.py` turns green.

### Step 10 — Add IC µ surface and n-ary profiles

`merge_classifier.py:286-291` (`build_merge_framework`): add an optional `integrity_constraint: IntegrityConstraint | None = None` parameter and an `additional_branches: Sequence[str] = ()` parameter for n-ary profiles. The IntegrityConstraint shape is a CEL expression evaluated against the candidate merged set; non-satisfying merge candidates are pruned per Konieczny IC0.

Coste-Marquis 2007 majority/leximax PAFs require n-ary; route through `argumentation.partial_af.{sum,max,leximax}_merge_frameworks` which already accepts a profile dict.

Acceptance: `test_ic_postulate_coverage.py` turns green for IC2, IC4, IC5, IC6, IC7, IC8 properties.

### Step 11 — Witness basis on every MergeArgument

Add `MergeArgument.witness_basis: tuple[ProvenanceWitness, ...]` per Buneman 2001 Proposition 2. Each witness records the source artifact_id + paper + the rule chain (if any) that grounds the merged claim. `branch_origins` becomes the coarse summary; `witness_basis` is the formal object.

Acceptance: a new `test_merge_witness_basis.py` asserts every `MergeArgument` carries a non-empty witness basis traceable to source artifact_ids.

### Step 12 — Booth admissible/restrained revision (deferred to research spike)

Booth 2006 admissible / restrained revision is a research-spike feature, not a bug fix. Add a `Δ_revise(prior_state, branch)` method as a separate operator alongside `build_merge_framework`. Out of scope for the WS-L bug-fix portion; tracked in a follow-up research-spike workstream WS-L.2.

### Step 13 — Schema-versioning awareness

For non-claim families (stances, contexts, conditions), implement Roddick 1995 evolution-vs-versioning distinction. When branch_a and branch_b both modified the same file, emit a `SchemaConflictRecord` rather than silently picking one. This is partially covered by Step 8 but extends to the family-aware case where mere file-content equality is too coarse (e.g., a stance file with reordered entries should not be flagged as conflict).

Acceptance: a new `test_schema_versioning_conflict.py` for stance and context families.

### Step 14 — Close gaps and gate

- Update `docs/gaps.md`: remove cluster-I HIGH/MED entries; add `# WS-L closed <sha>` line in the "Closed gaps" section.
- Update `docs/semantic-merge.md`: either downgrade the Konieczny IC0-IC8 alignment claim to "IC2/IC4 verified, IC0/IC5/IC6/IC7/IC8 require µ surface (added in WS-L)" or remove the claim entirely if µ is not in scope.
- Flip `tests/test_workstream_l_done.py` from `xfail` to `pass`.
- Update `reviews/2026-04-26-claude/workstreams/WS-L-merge.md` STATUS line to `CLOSED <sha>`.

Acceptance: `tests/test_workstream_l_done.py` passes; gaps.md has new closed entries.

## Acceptance gates

Before declaring WS-L done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors.
- [ ] `uv run lint-imports` — passes (this WS adds `propstore/families/sameas/` and `propstore/merge/witness.py`; verify no contract regressions).
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-L tests/test_merge_corroboration_preserved.py tests/test_merge_assertion_id_includes_provenance.py tests/test_merge_regime_split_preserved.py tests/test_canonical_claim_groups_no_union_find.py tests/test_classify_pair_no_concept_fallthrough.py tests/test_z3_translation_error_surfaced.py tests/test_materialized_claim_provenance_preserved.py tests/test_merge_symmetry_non_claim_files.py tests/test_comparison_source_no_synthetic_paper.py tests/test_ic_postulate_coverage.py tests/test_structured_merge_supports_preferred_stable.py tests/test_merge_witness_basis.py tests/test_schema_versioning_conflict.py tests/test_workstream_l_done.py` — all green.
- [ ] Full suite — no NEW failures vs the WS-A baseline. Specifically: `tests/test_repo_merge_object.py:255-296`, `tests/test_merge_report.py:186-229`, `tests/test_merge_classifier.py:294-323` are deleted (with paper-trail commits), not left red.
- [ ] `propstore/merge/merge_claims.py:_semantic_payload` includes `provenance` and `conditions` in the hashed payload.
- [ ] `propstore/merge/merge_classifier.py:_canonical_claim_groups` no longer runs union-find unconditionally.
- [ ] `propstore/merge/merge_classifier.py:_classify_pair` does not have the concept-comparison fallthrough at lines 254-256.
- [ ] `propstore/merge/merge_commit.py:_materialized_claim_payload` does not mutate `artifact_id` and does not pop `branch_origin`.
- [ ] `propstore/merge/merge_commit.py` does not overwrite `source.paper` with `"merged"`.
- [ ] `propstore/merge/structured_merge.py:argumentation_evidence_from_projection` supports `preferred` and `stable`.
- [ ] `docs/gaps.md` has no open rows for the findings listed above.
- [ ] `docs/semantic-merge.md` Konieczny alignment claim is either downgraded or accompanied by the new µ surface.
- [ ] `reviews/2026-04-26-claude/workstreams/WS-L-merge.md` STATUS line is `CLOSED <sha>`.

## Done means done

This workstream is done when **every finding in the tables at the top is closed**, not when "most" are closed. Specifically:

- T3.3 and T3.4 — both have green tests and the assertion-id / sameAs algorithms are corrected.
- HIGH-1 through HIGH-4 — all four have green tests gating the corrected behavior.
- MED-1 through MED-6 — every MED finding has either a green test or a documented removed test (per Q's "no old repos" rule).
- The missing-features list — IC µ surface exists, n-ary profiles exist, graded sameAs vocab exists, witness basis exists, structured merge supports preferred/stable. Booth admissible/restrained may be deferred to WS-L.2 if explicitly noted in this file.
- `gaps.md` is updated.
- `tests/test_workstream_l_done.py` has flipped from xfail to pass.

If any one of those is not true, WS-L stays OPEN. No "we'll get to graded sameAs later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS L.x) before declaring done.

## Papers / specs referenced

- **Konieczny & Pino Perez 2002** — IC0–IC8 postulates, syncretic assignments, Sigma/Max/GMax operators. Notes warning at `papers/Konieczny_2002.../notes.md:255-260`: "do not cite IC0–IC8 for an unconstrained scalar wrapper." WS-L Step 10 adds the µ surface.
- **Coste-Marquis et al. 2007** — PAF aggregation operators, n-ary profiles. WS-L's n-ary support makes Proposition 35 / Definition 38 verifiable.
- **Booth & Meyer 2006** — Admissible / restrained revision. Postulate P, lexicographic vs admissible vs restrained. Deferred to WS-L.2.
- **Halpin et al. 2010** — Similarity Ontology with 8 graded identity properties. Step 3b adopts `sim:sameIndividual`, `sim:claimsIdentical`, `sim:almostSameAs`.
- **Beek et al. 2018** — closure on 558M triples produces a 177,794-member set conflating Einstein, country names, empty string. Propstore union-find is structurally identical. Step 3 removes unconditional closure.
- **Melo et al. 2013** — minimum-multicut for erroneous identity-link removal. Step 3d.
- **Raad et al. 2019** — network metrics for identity-link quality. Step 3 references.
- **Buneman et al. 2001** — why/where-provenance, minimal witness basis. Steps 7 and 11.
- **Bohannon et al. 2006** — Lenses GetPut law. Current `artifact_id` mutation violates GetPut for merge-of-merge composition. Step 7 closes.
- **Roddick 1995** — symmetry as pragmatic requirement; evolution vs versioning. Steps 8 and 13.
- **Kuhn et al. 2014** — Trusty URIs (cross-link to T4.2 / WS-M). Informs Step 1's provenance fold choice.
- **Klein 2003 / Velegrakis 2004 / Flouris 2008** — not read for time. Tracked as WS-L follow-up; not gating.

## Cross-stream notes

- **WS-E dependency**: Step 1 (fold provenance into assertion-id) requires source/promote to place trustworthy provenance on every claim document. WS-E closes the dangling-justification and synthetic-trust holes that would corrupt the fold input.
- **WS-M overlap**: Step 11 (witness basis) overlaps WS-M's PROV-O serializer. A Buneman witness basis should serialize to PROV-O `prov:wasDerivedFrom`. Reuse WS-M's `Witness` dataclass if it ships first.
- **WS-D overlap**: Step 9 (`preferred`/`stable` semantics) touches operator-naming hygiene. Confirm semantics names match Caminada/Polberg.
- **WS-K overlap**: Step 3's `sameAs_assertions` is heuristic-layer (Layer 3). Coordinate with WS-K to ensure it lands in `propstore/heuristic/sameas/`. The merge module consumes the family; it does not own identity-claim production.
- **WS-O-arg dependency**: Step 9 routes through `argumentation.partial_af` and `argumentation.dung`. If WS-O-arg fixes ideal/grounded issues (T2.10, Codex #12), those flow through. Ensure the `argumentation` pin is up-to-date before declaring WS-L green.

## What this WS does NOT do

- Does NOT implement Booth 2006 admissible/restrained revision — that's WS-L.2.
- Does NOT add a full PROV-O serializer — that's WS-M.
- Does NOT touch the heuristic-vs-Layer-1 boundary broadly — that's WS-K. WS-L only relocates the new `sameAs_assertions` family per WS-K guidance.
- Does NOT change argumentation-package internals — those are WS-O-arg.
- Does NOT add Caminada semi-stable, ABA, ADF, or Bench-Capon VAF — Tier 7 coverage gaps.
- Does NOT add a Pearl `do()` operator at the merge boundary — that's WS-J / T6.1.
- Does NOT delete `_canonical_claim_groups` outright — Step 3 rewrites it as a defeasible-claim consumer. The merge module still needs to answer "are these two artifacts the same canonical claim?" — it just must not answer by union-find at storage time.
