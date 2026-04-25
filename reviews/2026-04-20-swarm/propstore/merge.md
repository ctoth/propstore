# Merge Subsystem Review — 2026-04-20

Scope read:
- `propstore/merge/__init__.py`
- `propstore/merge/merge_claims.py`
- `propstore/merge/merge_classifier.py`
- `propstore/merge/merge_report.py`
- `propstore/merge/structured_merge.py`
- `propstore/structured_projection.py`

Cross-reference read (context only, not primary targets):
- `propstore/world/assignment_selection_merge.py`
- `propstore/belief_set/ic_merge.py`
- `propstore/storage/merge_commit.py`
- `propstore/app/merge.py`
- `propstore/conflict_detector/orchestrator.py` (detect_conflicts surface)
- `argumentation/partial_af.py` at `C:\Users\Q\code\argumentation\src\argumentation\partial_af.py`

Mode: read + Grep only. No tests executed.

## Principle Violations

### PV1. `create_merge_commit` silently drops every claim that survived as a disagreement alternative

File: `C:\Users\Q\code\propstore\propstore\storage\merge_commit.py:49-56`

```python
sorted_arguments = sorted(merge.arguments, key=lambda argument: argument.claim_id)
artifact_counts = Counter(argument.artifact_id for argument in sorted_arguments)
merged_claims = [
    argument.claim.to_payload()
    for argument in sorted_arguments
    if artifact_counts[argument.artifact_id] == 1
]
```

Severity: **critical**. This is a direct violation of the non-commitment core design principle ("Do not collapse disagreement in storage"). When the classifier correctly emits two disambiguated alternatives (`artifact_id__branch_a` and `artifact_id__branch_b`) for a conflicted claim, both share the same `artifact_id`, so `artifact_counts[artifact_id] == 2` and both are **excluded from the written claims blob**. The merged tree on the target branch contains only the claims that had no disagreement. All disagreement alternatives are written only to the manifest as metadata (name/id only — no claim bodies, no conditions, no values), which is not the same as "materialized into storage."

The design checklist from CLAUDE.md explicitly says:
- "Does this prevent ANY data from reaching the sidecar? If yes → WRONG."
- "Is filtering happening at build time or render time? If build → WRONG."

This filters at merge-commit build time, not render time. The `materialized=False` flag in the manifest entries acknowledges the collapse but does not restore the data — downstream readers cannot reconstruct the lost claim bodies from the manifest alone.

Fix direction: write every argument's claim payload into the merged blob (with disambiguated artifact_ids on the disagreement alternatives), and let render policies filter at query time. If artifact_id collision is a real schema constraint, use the already-disambiguated `claim_id` as the stored id; do not drop.

### PV2. `_classify_pair` defaults same-concept pairs with no detector records to CONFLICT

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:259-261`

```python
if _extract_concept(left_claim) != _extract_concept(right_claim):
    return _DiffKind.COMPATIBLE
return _DiffKind.CONFLICT
```

Severity: **high**. When `detect_conflicts` returns an empty record list, the code treats that as `CONFLICT` if the two claims share a concept. CLAUDE.md explicitly requires "honest ignorance over fabricated confidence" (citing Jøsang vacuous opinions). The honest answer when the detector produces zero records is `UNKNOWN`/`ignorance`, not `CONFLICT`. Fabricating an attack edge where the engine said nothing is the definition of fabricated confidence.

This matters because `attacks` show up as Dung attacks in the PAF and feed `skeptically_accepted` / `credulously_accepted` in `summarize_merge_framework` — a fabricated attack flips acceptance status.

Fix: replace the unconditional `return _DiffKind.CONFLICT` with `return _DiffKind.UNKNOWN` (or `COMPATIBLE` if `_claims_equal` already returned False only because of provenance fields, but that case is excluded by the equality check above).

### PV3. Branch-origin annotation mutates provenance only for conflict branches, not for compatible-keep branches

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:343-399`

When both branches have the claim and they compare equal (line 344), the emit path uses `branch_origins=(branch_a, branch_b)` but does **not** pass `annotate_branch_origin=...`. The `MergeClaim.document` keeps whatever provenance was on the left_idx copy — the right side's provenance (including paper source, extraction model, confidence, etc.) is simply discarded. If the two copies arrived at the same semantic payload via different provenance histories, that history is silently lost at merge time rather than being preserved as two typed provenance records.

Severity: medium. Non-commitment discipline says disagreement in provenance should survive; `_claims_equal` strips provenance from the equality check so two claims can be "equal" while having disjoint provenance payloads. The merge then keeps only one.

Fix: either require provenance equality for `_claims_equal`, or emit both copies when provenance diverges.

### PV4. Structured-merge summary declares `ignorance_relations` as "not_preserved_in_summary"

File: `C:\Users\Q\code\propstore\propstore\merge\structured_merge.py:179-195`

```python
def _summary_relation_surface() -> dict[str, str]:
    return {
        "attack": "preserved_via_projection",
        "non_attack": "not_preserved_in_summary",
        "ignorance": "not_preserved_in_summary",
    }
```

Severity: high. The structured merge pipeline discards `ignorance` when projecting to a Dung `ArgumentationFramework` — the projected framework has only `defeats` and `attacks`, not the three-way partition. Sum/max/leximax merge then run over a framework that has already collapsed unknown-attack to some default (whichever of "in defeats" or "not in defeats" the projection picked). This converts the carefully constructed `ignorance` signal from `build_merge_framework` into a binary value before the IC merge even runs. Downstream IC-merge postulates (Konieczny-Pino Pérez) are only meaningful on the full disagreement signal.

The summary self-documents the lossiness (good), but the architecture then uses the lossy projection as merge input (not good).

Fix: treat `ignorance` as an extra input to structured merge (e.g. separate partial-AF merge over the three-way partition) rather than collapsing before the merge operator runs. `argumentation.partial_af` already has the primitives.

### PV5. `build_merge_framework` tightly couples to `conflict_detector` (heuristic layer) for a source-layer decision

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:210-245`

The "merge is source storage" layer constructs `ConflictClaim` via `conflict_claim_from_payload`, calls `detect_conflicts(...)` with empty `concept_registry={}` and `cel_registry={}`, and catches `Z3TranslationError`. Per CLAUDE.md layering: source storage depends only on lower layers; `conflict_detector` is used by the heuristic/analysis layer. Running Z3/conflict detection at storage-merge-commit time to decide what gets written is a build-time heuristic gate, which the design checklist forbids.

Severity: medium architectural. Empty `concept_registry` and `cel_registry` also means all concept-aware conflict detection is a no-op here — conflicts get downgraded to whatever the raw payload comparators detect. That suggests this call is doing roughly nothing useful while coupling a supposedly-formal layer to an analysis surface.

Fix: if merge needs to classify attacks vs ignorance, it should do so from structural / typed information available in the claim documents themselves, not from a heuristic conflict-detection run at merge time.

## Merge Algebra Correctness

### MA1. `_classify_pair` is order-sensitive where IC merge requires commutativity

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:223-261`

`conflict_claim_from_payload(left...)` and `conflict_claim_from_payload(right...)` are passed in a fixed `[left, right]` order to `detect_conflicts`. `detect_conflicts` (`conflict_detector/orchestrator.py`) iterates claims to build a synthetic source enum, then hands them to `detect_parameter_conflicts`, `detect_measurement_conflicts`, etc. Whether those sub-detectors are order-stable is not guaranteed; `by_concept` grouping is order-sensitive. Konieczny-Pino Pérez postulate (IC2, IC4) requires merge to be commutative in the profile. Any downstream code that uses `build_merge_framework(snap, A, B)` and expects `build_merge_framework(snap, B, A)` to produce the same PAF is at risk.

Severity: high, unverified. The code path must be tested: same two branches, swap `branch_a`/`branch_b`, compare resulting PAFs up to renaming.

Fix: either prove commutativity of the conflict-detection composition and add a test, or canonicalize the claim order passed into `detect_conflicts` by `artifact_id` before calling.

### MA2. Non-commutativity via asymmetric "ancestral" treatment of base claim

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:354-372`

```python
if in_base and _claims_equal(left_claim.claim, base_claim.claim):
    # take right, keep branch_b
    ...
if in_base and _claims_equal(right_claim.claim, base_claim.claim):
    # take left, keep branch_a
    ...
```

This is three-way-merge standard logic and it is symmetric on `left/right` by structure — good. But it is NOT commutative under branch-swap for the **emitted branch_origins tuple**. `build_merge_framework(A, B)` and `build_merge_framework(B, A)` emit different `branch_origins` provenance. Downstream code that filters by `branch_origins` (e.g. `semantic_candidate_details` dumps them verbatim to `branch_origins: [...]`) produces different reports. Symmetric up to relabeling, not identical payloads.

Severity: low (expected and documented by the branch_a/branch_b fields of the output), but worth confirming no caller assumes identity under swap.

### MA3. `_claim_semantic_key` and `_claim_candidate_key` use inconsistent skip-sets

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:118-131`

```python
# _claim_semantic_key
skip = {"artifact_id", "version_id", "provenance"}

# _claim_candidate_key
skip = {"id", "artifact_id", "version_id", "provenance", "logical_ids"}
```

`_claims_equal` (built on `_claim_semantic_key`) includes `logical_ids` and `id` in the equality check; `_claim_candidate_key` excludes both. Two claims differing only in `logical_ids` are:
- "not equal" by `_claims_equal` → emitted as two alternatives with attacks or ignorance
- "semantically equal" by `_claim_candidate_key` → the pair is grouped as a semantic candidate

This produces reports where the same two claim payloads are simultaneously "in conflict" (via attacks) and "semantically equivalent" (via `semantic_candidates`). The two surfaces disagree.

Severity: medium — a semantic-key design drift that leaks into the report. Fix: decide whether `logical_ids` / `id` count for equality, and use the same skip-set everywhere.

### MA4. `_canonical_claim_groups` union-find: logical-id transitivity is silent

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:147-202`

If claim X has logical_ids `{L1}`, claim Y has `{L1, L2}`, claim Z has `{L2}`, then union-find merges X-Y-Z into one canonical group purely because logical_ids share components. That is logical-id coreference by transitive closure with no gate. This is fine IF logical_ids are genuine identity keys — but nothing here verifies that. A multi-assigned logical_id (e.g. an author reused a name) would collapse unrelated claims into one canonical group, suppressing what should be multiple independent disagreements.

Severity: medium, depends on upstream discipline around logical_ids. No audit record exists telling you which claims were unioned via which logical_id.

Fix: record the union chain in provenance-bearing form (e.g. `canonical_via_logical_id: [(X, Y, L1), (Y, Z, L2)]`) so the render layer can see why two claims were treated as the same canonical group.

## Data Loss Risks

### DL1. Dropped disagreement alternatives during `create_merge_commit`

Covered above as PV1. Restating in data-loss terms: the claim *bodies* (value, conditions, stances, provenance, concepts) of every disagreement alternative are present in `merge.arguments` and written to neither the merged claim blob nor the manifest (which only records `claim_id`, `canonical_claim_id`, `artifact_id`, `logical_id`, `branch_origins`, `materialized`). After the merge commit, the two-parent history still has the claim bodies reachable via parent shas, but querying the merge head loses them. Severity: critical.

### DL2. Silent abort of the full merge framework on a single Z3 translation error

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:234-245`

```python
try:
    records = detect_conflicts(...)
except Z3TranslationError:
    left_conditions = sorted(left_claim.document.conditions)
    right_conditions = sorted(right_claim.document.conditions)
    if left_conditions != right_conditions:
        return _DiffKind.PHI_NODE
    raise
```

If the two claims have identical conditions but Z3 cannot translate some expression, the exception propagates up through `build_merge_framework` and aborts construction of the **entire** PAF. A single malformed claim blocks merge inspection of the whole repository.

Severity: high. Fix: catch `Z3TranslationError` and record `UNKNOWN`/`ignorance` for the offending pair; never let one bad claim kill the whole merge.

### DL3. `_extract_concept` only looks at the first concept in `document.concepts`

File: `C:\Users\Q\code\propstore\propstore\merge\merge_claims.py:39-45`, used at `merge_classifier.py:259`

Two claims attached to the concept set `{A, B}` in different orders give different `concept_id` under `_extract_concept`. Downstream `_classify_pair` then treats them as different-concept and returns `COMPATIBLE` (the unconditional return at line 260 when no records are produced). The disagreement is silently dropped to `COMPATIBLE`.

Severity: medium. Fix: compare concept sets, not first-concept-string.

### DL4. `create_merge_commit` keeps only one claim payload per artifact_id even when both are `materialized=True`

File: `C:\Users\Q\code\propstore\propstore\storage\merge_commit.py:50-55`. `artifact_counts[artifact_id] == 1` means a claim is written iff it appeared exactly once among `merge.arguments`. When left+right were equal, the classifier emits ONE `MergeArgument` with both branches in `branch_origins`, and `artifact_counts` is 1. Good. When left-only or right-only, same. When disagreement — both emitted as `__branch_a` and `__branch_b` disambiguations — they share the underlying `artifact_id`, count is 2, both are dropped (see PV1). So the filter logic encodes the PV1 data-loss choice directly.

Severity: critical. Same as PV1; listing separately because it affects the bugs-list reader.

### DL5. Right-side provenance discarded on equal-keep emit

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:343-352`. When both branches agree, only `left_claim.claim` is emitted; the right document, with potentially distinct provenance, is dropped. Covered as PV3.

### DL6. `MergeClaim.concept_id` silently coerces non-string first concept to `""`

File: `C:\Users\Q\code\propstore\propstore\merge\merge_claims.py:39-45`. Iterates `document.concepts` looking for any `isinstance(str) and truthy` entry. If concepts contain only non-string objects, returns `""`. Downstream `_extract_concept` returns `""`, and `_classify_pair` treats both sides as same (empty) concept → falls through to the PV2 path → fabricated `CONFLICT`.

Severity: low, depends on upstream `ClaimDocument.concepts` typing.

## Bugs & Silent Failures

### B1. `Z3TranslationError` re-raised aborts the full merge (same as DL2)

See DL2.

### B2. `_classify_pair` ignores `UNKNOWN` records followed by `ignorance` resolution order

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:247-258`. The code iterates records three times (CONFLICT → PHI_NODE → UNKNOWN priority). If there is any CONFLICT record, it returns CONFLICT even when the same record set contains stronger UNKNOWN signals about other dimensions of disagreement. That's a reasonable priority choice, but paired with PV2 the net effect is: "any evidence of conflict wins; silence also wins." There is no path that produces `UNKNOWN` from the presence of CONFLICT-evidence.

Severity: low. Fix: document the priority explicitly; add a test that asserts the priority behavior on mixed records.

### B3. Cross-canonical attack discovery mutates `attacks`/`ignorance` sets while iterating their membership checks

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:427-453`. The `for arguments in emitted_groups.values()` loop reads and writes to `attacks` and `ignorance` simultaneously. Current iteration uses `pair not in attacks` as a guard before possibly adding `pair` — since it is a fresh pair, the guard is defensive not required. Not a bug today but fragile if anyone adds iteration order dependencies.

Severity: very low. Fix: accumulate new pairs into a staging set, then update at end of loop.

### B4. `semantic_candidates` grouping uses JSON stringification of dict — order-sensitive for nested lists

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:455-458`

```python
semantic_key = json.dumps(_claim_candidate_key(argument.claim), sort_keys=True)
```

`sort_keys=True` sorts dict keys, but does not sort list values. If two claims have the same semantic content but list items (e.g. `concepts: [A, B]` vs `[B, A]`) in different orders, they get different JSON keys and do not group. Compounds with DL3.

Severity: low. Fix: canonicalize list orderings in `_claim_candidate_key` or in `_normalize_for_signature` style.

### B5. `structured_merge._file_stance_rows` filters differently from `_canonical_stance_rows`

File: `C:\Users\Q\code\propstore\propstore\merge\structured_merge.py:247-258` collects all stance rows in the repo keyed by `source_claim`, regardless of whether that source claim is in the current active-claims set. `_canonical_stance_rows` (line 198-220) then filters down to in-scope claim_ids. Two potential issues:
(a) rows where `target_claim_id` is in-scope but `claim_id` is out-of-scope are dropped. That is probably correct, but note it loses inbound stances.
(b) `_stance_row_from_mapping` silently drops rows where `coerce_stance_type` returns None, with no diagnostic — stance-type drift silently reduces the relation surface.

Severity: medium (b), low (a).

### B6. `_summary_content_signature` mixes `claim.to_payload()` (with branch_origin in provenance) with stance payload — signature depends on branch_origin annotation

File: `C:\Users\Q\code\propstore\propstore\merge\structured_merge.py:138-176`. `claim.to_payload()` without args uses `include_branch_origin=True` default. If the same branch is summarized twice — once standalone, once as part of a merge context — `branch_origin` injections can differ and the signature changes for identical underlying storage content. That breaks content-addressable caching.

Severity: medium. Fix: pass `include_branch_origin=False` for signature computation.

### B7. `PartialArgumentationFramework.non_attacks` computed as "everything not in attacks or ignorance" including self-pairs

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:469-476`

```python
argument_ids = frozenset(argument.claim_id for argument in emitted)
ordered_pairs = frozenset(product(argument_ids, argument_ids))
framework = PartialArgumentationFramework(
    arguments=argument_ids,
    attacks=frozenset(attacks),
    ignorance=frozenset(ignorance),
    non_attacks=ordered_pairs - frozenset(attacks) - frozenset(ignorance),
)
```

Self-pairs `(x, x)` are in `ordered_pairs` and therefore land in `non_attacks` unless they appear in `attacks`. Self-attacks in Dung have specific semantics (usually treated as defeat-by-self). Declaring "arg x does not attack itself" for every argument bloats the PAF and may misalign with `argumentation.partial_af` expectations (the module might expect self-pairs handled specially, per `__post_init__`). This is the quadratic-in-argument-count part that makes downstream `enumerate_completions` blow up on any repo with more than ~15 arguments (it enumerates `2^|ignorance|` completions).

Severity: medium; scalability and semantic correctness. Fix: exclude self-pairs from `ordered_pairs`, or if PAF expects them, align with that invariant explicitly.

### B8. `_disambiguate_id` sanitization is too shallow

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:96-98`

```python
def _disambiguate_id(claim_id: str, suffix: str) -> str:
    safe_suffix = suffix.replace("/", "_").replace("-", "_")
    return f"{claim_id}__{safe_suffix}"
```

Only replaces `/` and `-`. Branch names can contain `.`, `@`, `#`, `:`, unicode, spaces, etc. If two branches differ only in non-sanitized characters but collide on sanitization (e.g. `feat/x` vs `feat_x`), two disambiguated ids collide. Also: `claim_id` itself might already contain `__` producing ambiguous parsing back to `(artifact_id, branch)`.

Severity: low (depends on branch-naming discipline). Fix: use a deterministic hash suffix or enforce branch-name validation.

### B9. `MergeClaim.get` / `__getitem__` route through `to_payload(include_id_alias=True)` which includes branch_origin

File: `C:\Users\Q\code\propstore\propstore\merge\merge_claims.py:66-70`. Any code doing `merge_claim["provenance"]` gets provenance with branch_origin injected. If a caller then round-trips this as "original provenance" into storage, branch_origin becomes sticky on the stored document. This is a footgun disguised as compatibility.

Severity: medium. Fix: either drop these accessors or document that they emit merge-flavored views, never source-of-truth views.

## Dead Code / Drift

### D1. `structured_projection.py` Phase-5 delegation wrapper

File: `C:\Users\Q\code\propstore\propstore\structured_projection.py` is a thin facade over `propstore.aspic_bridge.build_aspic_projection`. Module docstring calls itself "Phase 5 cutover" — wrapper exists purely to preserve the import path. After any callers are migrated, this module can be deleted. Check: `Grep` over `from propstore.structured_projection import` — several callers remain (including `propstore/merge/structured_merge.py:17`). Not dead yet; documented as drift.

### D2. `_score_world` in `belief_set/ic_merge.py` uses `BeliefSet.all_worlds(signature)` inside a loop per formula

File: `C:\Users\Q\code\propstore\propstore\belief_set\ic_merge.py:70-78`. Recomputes all worlds for each formula on every candidate. 2^|signature| blow-up is duplicated per formula per candidate. For anything beyond tiny signatures this is unusable. Not a merge-subsystem target; noted as drift for the belief_set layer.

### D3. `merge_classifier._annotate_provenance` re-wraps `MergeClaim` with only `branch_origin` changed

File: `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py:84-85`. Fine — but note that callers (`_emit_argument`) pass `annotate_branch_origin` only on the disagreement path. On the "take-right because left equals base" path (line 354-362), the result is annotated with `branch_b` implicitly via `branch_origins=(branch_b,)` but the underlying `MergeClaim.branch_origin` field is still whatever the right side arrived with. Two views of "which branch" now disagree within one emitted argument.

Severity: low; noise between `MergeArgument.branch_origins` (tuple) and `MergeClaim.branch_origin` (single string). Collapse one or the other.

### D4. `summarize_merge_framework` emits both `statuses` and `argument_details` with 80% overlap

File: `C:\Users\Q\code\propstore\propstore\merge\merge_report.py:49-104`. `statuses[claim_id]` is a strict subset of `argument_details[*]`. Two keys for the same info; callers must choose arbitrarily. Minor drift.

## Positive Observations

- The three-way partition PAF (`attacks` / `ignorance` / `non_attacks`) with explicit ignorance is the right data model for non-commitment. `build_merge_framework` correctly emits two disambiguated alternatives on disagreement rather than picking a winner at this layer. This is the correct design at the classifier level.
- `MergeClaim.provenance_payload` is a clean way to attach merge-time provenance (`branch_origin`) without mutating the underlying `ClaimDocument`.
- `_canonical_stance_rows` canonical sort order and stable signature computation in `_summary_content_signature` is a good discipline (modulo B6).
- `assignment_selection_merge.solve_assignment_selection_merge` correctly emits **all** ties in `winners` rather than picking a single one — that is non-commitment done right for the assignment merge layer. Sort key breaks ties deterministically only for output ordering, not for winner selection.
- `belief_set.ic_merge.merge_belief_profile` correctly returns a `BeliefSet.contradiction(...)` with empty winners when no world satisfies `mu`, instead of fabricating a "best-effort" answer. Honest ignorance.
- The boundary set by `CLAUDE.md` — "assignment-selection merge lives in world.assignment_selection_merge; model-theoretic IC merge lives in belief_set.ic_merge; storage merge in storage" — is respected by all three files. `propstore/merge/` owns the claim-PAF merge and does not reach into either of the other two.
- `create_merge_commit` correctly composes a true git two-parent merge commit (`parents=[left_sha, right_sha]`) with non-claim files unioned from both sides. The *structure* of the git merge is correct — it is only the claims-blob filter (PV1/DL1/DL4) that collapses disagreement.

## Summary of severities

- Critical: PV1 / DL1 / DL4 (same finding, three angles) — merge commit silently drops all disagreement claim bodies.
- High: PV2 (fabricated CONFLICT on silence), PV4 (structured-merge drops ignorance before IC operator runs), MA1 (commutativity unverified), DL2 (one bad claim aborts merge).
- Medium: PV3, PV5, MA3, MA4, DL3, B5b, B6, B7, B9.
- Low: MA2, DL5, DL6, B2, B3, B4, B5a, B8, D3, D4.
- Drift: D1, D2.

Relevant files (all absolute):
- `C:\Users\Q\code\propstore\propstore\merge\merge_classifier.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_claims.py`
- `C:\Users\Q\code\propstore\propstore\merge\merge_report.py`
- `C:\Users\Q\code\propstore\propstore\merge\structured_merge.py`
- `C:\Users\Q\code\propstore\propstore\structured_projection.py`
- `C:\Users\Q\code\propstore\propstore\storage\merge_commit.py`
- `C:\Users\Q\code\propstore\propstore\app\merge.py`
- `C:\Users\Q\code\propstore\propstore\conflict_detector\orchestrator.py`
- `C:\Users\Q\code\argumentation\src\argumentation\partial_af.py`
