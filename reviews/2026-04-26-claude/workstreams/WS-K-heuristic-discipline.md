# WS-K: Heuristic discipline & layer-3 boundary

**Status**: CLOSED 3c40537b (rewritten 2026-04-27 per D-8; revised again per D-19 + Codex 1.16)
**Depends on**:
- **WS-A** (schema fidelity) — sidecar Opinion column round-trip and embedding-registry schema migration cannot be verified until WS-A's fixture parity holds.
- **WS-O-arg-argumentation-pkg** (argumentation kernel) — the calibration pipeline runs the kernel; any kernel-level bug in DeLP/ASPIC dispatch leaks into trust outputs.

WS-K does NOT depend on WS-K2. The kernel and all tests use HAND-STUBBED rule fixtures so the source-trust argumentation pipeline can be verified independently. Production trust quality improves once WS-K2 has promoted its first meta-paper rule corpus, but WS-K's implementation, tests, and gating sentinel close on stubs — no cycle with WS-K2.
**Blocks**: WS-N2 (architectural import-linter rewrite). WS-K writes the layered-contract negative scaffolding; WS-N2 inherits it.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

---

## Why this workstream exists

The README declares a six-layer architecture with one-way downward dependencies. Layer 3 emits proposals only; Layer 4 reasons. Four things violate this today.

1. **Package layout lies** — `propstore/heuristic/` is empty of actual heuristic code; embeddings, classification, pair discovery, calibration sit at top level (`embed.py`, `classify.py`, `relate.py`, `calibrate.py`).
2. **Trust calibration is not a heuristic** (D-8) — `derive_source_document_trust` runs `WorldQuery.chain_query` from inside the heuristic package and writes to the source branch unreviewed. Replaced by an argumentation pipeline; the kernel is the author.
3. **Disagreement collapse pervades** (`project_design_principle`) — three collapse points share one family: **H9** `dedup_pairs` minimum-distance collapse, **H10** single bidirectional LLM call, **H11** perspective-conflated stance filing. Codex 1.16 directs WS-K to own all three; H10/H11 are no longer deferred.
4. **Embedding identity collapses on a sanitized string** (D-19) — `_sanitize_model_key` at `propstore/embed.py:88-91` rewrites non-alphanumeric characters to `_`, so `a/b`, `a-b`, `a_b`, `a b` all map to `a_b` and shadow each other in the registry. Folded into WS-K because the registry lives in the heuristic embeddings module WS-K is already disciplining.

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T3.1 / H9 / gaps.md MED** | Claude Cluster H | `propstore/relate.py:67-74` | `dedup_pairs` collapses bidirectional distance to the minimum. |
| **T5.1 / Cluster U U#1** | Claude Cluster U | `propstore/embed.py`, `classify.py`, `relate.py`, `calibrate.py` | Heuristic logic lives at top level; package boundary fictional. |
| **T5.2 / H1 / H3 / H12** | Claude Cluster H | `propstore/heuristic/source_trust.py:103-172` + callers | Trust calibration mislabelled as heuristic, conflates Layer 3 with Layer 4. **Resolved per D-8** by deleting the heuristic and replacing with an argumentation pipeline. |
| **H2** | Cluster H | `.importlinter:13-19` | The `source -> heuristic` contract is vacuously satisfied. |
| **H5** | Cluster H | `sidecar/passes.py:112`, `praf/engine.py:160`, `core/row_types.py:466,655-656,722` | `prior_base_rate` is a bare float; should be `Opinion`. |
| **H6** | Cluster H | `proposals.py:148-163` | Stance proposals carry rich provenance; trust output must too. |
| **H7** | Cluster H | `classify.py:299-302` | `confidence = 0.0` conflates "no relationship" with "calibration failed." |
| **H8** | Cluster H | `heuristic/source_trust.py:168-169` | `CALIBRATED` silently downgraded to `DEFAULTED` — closed by deletion. |
| **H9** | Cluster H | `relate.py:67-74` | Distance minimum collapse. |
| **H10** | Cluster H | `classify.py:324-401` | Single bidirectional LLM call structurally prevents independent forward/reverse disagreement. **In scope** (Codex 1.16). |
| **H11** | Cluster H | `relate.py:258-263` | Stances filed under one source claim regardless of perspective. **In scope** (Codex 1.16). |
| **H14** | Cluster H | `proposals.py:182-202` | `transaction.commit_sha` read AFTER `with` block exits. |
| **H15** | Cluster H | `proposals.py:124-145` | `promote_stance_proposals` no idempotency guard. |
| **H16** | Cluster H | `proposals.py:93-101` | `plan_stance_proposal_promotion` silently drops typo'd paths. |
| **H17** | Cluster H | `proposals.py:30-43` | `cast("Repository", object())` placeholder. |
| **H18** | Cluster H | `proposals.py:179-180` vs `app/claims.py:601-602` | Inconsistent empty-input handling. |
| **Cluster U U#5** | Cluster U | `classify.py:389` | `result.get("forward", result)` silent fallback. |
| **D-19 — embedding-key collision** | DECISIONS.md D-19 / Codex Round 2 | `propstore/embed.py:88-91, 118, 217` | `_sanitize_model_key` collapses `a/b`, `a-b`, `a_b`, `a b` to the same SQL identifier. Distinct models shadow each other in the sidecar registry. |

**Dropped from WS-K (per D-8)**: `proposal_source_trust` family design, `SourceTrustProposalDocument`, `TrustDerivationProvenance`, the `propose / plan / promote` API for trust. Superseded; trust is no longer proposal-gated.

**Moved to WS-K2**: meta-paper rule extraction (D-9), `proposal_rules` family, `knowledge/rules/<paper-name>/` layout (D-10).

## Code references (verified by direct read)

### Heuristic layer leakage
- `propstore/heuristic/__init__.py` — empty.
- `propstore/heuristic/source_trust.py` — only file in heuristic package.
- `propstore/embed.py`, `propstore/classify.py`, `propstore/relate.py`, `propstore/calibrate.py` — top-level heuristic modules.
- `propstore/sidecar/build.py:460,543`, `propstore/world/model.py:973,998`, `propstore/app/claims.py:470,524,574-577`, `propstore/app/concepts/embedding.py:38,101`, `propstore/app/concepts/mutation.py:522,585` — application/storage imports of Layer 3.

### Misdiagnosed-as-heuristic trust calibration
- `propstore/heuristic/source_trust.py:103-172` — `derive_source_document_trust`. Deleted in Step 3.
- `propstore/app/sources.py:190-201`, `:504-516` — call sites.
- `propstore/source/finalize.py:170-185` — writes the heuristic-mutated payload.

### `prior_base_rate` is a bare float
- `propstore/heuristic/source_trust.py:144-156` — `resolved_prior = float(...)`.
- `propstore/sidecar/passes.py:112` — float column.
- `propstore/praf/engine.py:159-161` — float read.
- `propstore/core/row_types.py:466, 655-656, 722` — flat list, no Opinion structure.

### Disagreement-collapse trio
- `propstore/relate.py:67-74` — `dedup_pairs` minimum-distance collapse (H9).
- `propstore/classify.py:324-401` — `classify_stance_async` single bidirectional LLM call (H10).
- `propstore/relate.py:258-263` — perspective-conflated stance filing (H11).
- `propstore/classify.py:299-302` — `confidence = 0.0` conflation (H7).
- `propstore/classify.py:389` — silent fallback (U#5).

### Proposal lifecycle bugs (stance proposals ARE heuristic)
- `propstore/proposals.py:30-43` (H17), `:93-101` (H16), `:124-145` (H15), `:179-180` vs `app/claims.py:601-602` (H18), `:182-202` (H14).

### Embedding-key collision (D-19)
- `propstore/embed.py:88-91` — `_sanitize_model_key`:
  ```python
  def _sanitize_model_key(model_name: str) -> str:
      """Convert a litellm model string to a valid SQL identifier fragment."""
      return "".join(char if char.isalnum() else "_" for char in model_name)
  ```
  Maps `a/b`, `a-b`, `a_b`, `a b` → `a_b`. Distinct models register under the same key.
- `propstore/embed.py:118` — `model_key = _sanitize_model_key(model_name)` consumed by `existing_content_hashes(model_key)` and feeds the cache row identity.
- `propstore/embed.py:217` — second call site, same collapse.

## Argumentation pipeline — design

Calibration runs the argumentation kernel over `(rules, source metadata, world claim graph)`, producing an `Opinion`-typed `prior_base_rate` with full rule-firing provenance, persisted on the source branch as authored content with `author = "propstore.source_trust_argumentation:calibrate_source_trust"`. Runs at promote-time after the git transaction succeeds (D-6). Module lands at `propstore/source_trust_argumentation/` (sibling to `propstore/heuristic/`, NOT inside it). API:

```python
def calibrate_source_trust(repo, source_name, *, rule_corpus=None, world_snapshot=None) -> SourceTrustResult: ...

@dataclass(frozen=True)
class SourceTrustResult:
    prior_base_rate: Opinion
    derived_from: tuple[RuleFiring, ...]
    world_snapshot_sha: str
    kernel_version: str
    status: ProvenanceStatus  # CALIBRATED | DEFAULTED | VACUOUS
```

Status values are explicit: `DEFAULTED` when no rules fired, `VACUOUS` when the kernel returned no extension. The H8 silent downgrade cannot recur.

## Embedding identity tuple — design (D-19)

The replacement for `_sanitize_model_key` is a typed identity, never a lossy SQL suffix:

```python
@dataclass(frozen=True)
class EmbeddingModelIdentity:
    provider: str            # e.g. "openai", "voyage", "litellm-proxy"
    model_name: str          # litellm's full model string, untouched
    model_version: str       # the provider's version pin (or "" if unversioned)
    content_digest: str      # digest of the model spec (model card hash, or per-call config hash)

    @property
    def identity_hash(self) -> str:
        """Stable content-hash of the four-tuple. Used as indexed lookup key."""
        return _stable_hash((self.provider, self.model_name, self.model_version, self.content_digest))
```

`content_digest` is computed from whatever spec the provider exposes:
- If the provider publishes a model card hash, use it.
- Otherwise, hash the per-call config (`{provider, model_name, model_version, dimensions, normalize, **provider_kwargs}`) as canonical JSON.

Identity is data, not a SQL identifier. The sidecar embedding registry stores the four-tuple as typed columns plus the derived `model_identity_hash` for indexed lookup. There is no string suffix on a SQL table; one canonical `embeddings` table is keyed on `(model_identity_hash, entity_id)`.

### Sidecar schema migration

- Drop the sanitized-string column / table-suffix scheme entirely.
- Add typed columns to the embeddings registry: `provider TEXT NOT NULL`, `model_name TEXT NOT NULL`, `model_version TEXT NOT NULL DEFAULT ''`, `content_digest TEXT NOT NULL`, `model_identity_hash TEXT NOT NULL`.
- Add `UNIQUE(model_identity_hash, entity_id)` and an index on `model_identity_hash`.
- Coordinated with WS-A's schema-parity work: the production schema and the test fixture builder both gain these columns at the same commit.

Bulk migration of existing sanitized-key rows is **OUT OF SCOPE** per D-3 (no old-data carve-outs). Existing sanitized rows become invalid; the system iterates to perfection on a fresh repo.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_no_derive_source_document_trust.py`** — AST-walk asserts no module defines `derive_source_document_trust`; `propstore.heuristic.source_trust` lacks the symbol; grep returns zero hits outside `tests/` and `reviews/`.

2. **`tests/test_source_trust_argumentation.py`** — synthetic repo with two meta-paper sources carrying hand-stubbed rule corpora; `calibrate_source_trust` returns `SourceTrustResult` with Opinion `prior_base_rate` (not float), expected `derived_from` outcomes, `status == CALIBRATED` for the rule-satisfying source, `status == DEFAULTED` and vacuous Opinion for a no-rule source.

3. **`tests/test_prior_base_rate_is_opinion.py`** — `SourceTrustBlock.prior_base_rate` round-trips as Opinion through YAML, sidecar, and praf engine; no float coercion path exists.

4. **`tests/test_trust_calibration_runs_at_promote.py`** — promoting a meta-paper that authors a new rule recalibrates dependent sources; new commit lands on the source branch with updated Opinion components reflecting attacks.

5. **`tests/test_heuristic_package_layout.py`** — AST-walks `propstore/`. For each name in `{embed, classify, relate, calibrate}`, asserts the file does NOT exist at `propstore/<name>.py` and DOES exist at `propstore/heuristic/<name>.py`. Asserts `propstore.heuristic.source_trust` does not contain `derive_source_document_trust` or any `WorldQuery`-opening code.

6. **`tests/architecture/test_import_linter_negative.py`** — programmatically writes a temporary module under `propstore/source/` importing `propstore.heuristic.embed`, runs `lint-imports`, asserts non-zero exit. Removes the temp module afterward. WS-N2 inherits this scaffolding.

7. **`tests/test_dedup_pairs_preserves_mirror.py`** — input `[(a, b, 0.3), (b, a, 0.4)]`. `dedup_pairs` returns `(a, b, forward_distance=0.3, reverse_distance=0.4)`; both directions persist; `relate_all_async` calibrator's `reference_distances` includes both.

8. **`tests/test_classify_no_silent_fallback.py`** — mocked LLM response shaped `{"type": "supports"}` (no `forward`/`reverse` keys); `classify_stance_async` raises `BidirectionalShapeError` or returns an explicit `LLM_OUTPUT_SHAPE_UNKNOWN` provenance-marked stance. No silent fallback.

9. **`tests/test_classify_forward_reverse_independent.py`** (NEW per Codex 1.16, H10) — asserts `classify_stance_async` issues two independent LLM calls per pair and that forward and reverse can disagree.
   - Mock the LLM such that the forward call (a→b) returns `supports` and the reverse call (b→a) returns `undercuts`.
   - Assert the returned object exposes both stances as separate values, each with its own `Provenance` (separate `llm_call_id`s, separate prompts captured, separate raw-response captures).
   - Assert the forward stance is NOT silently overwritten by the reverse and vice versa.
   - Assert exactly two LLM calls were issued for the pair (use call-count assertion on the mock).
   - Negative case: mock returns identical `supports` from both directions; assert both stances persist as identical-but-independent records (still two provenance chains, not one shared one).
   - **Must fail today**: `classify.py:324-401` issues a single bidirectional call and parses both directions out of one response, so the two directions share provenance and cannot structurally disagree.

10. **`tests/test_relate_perspective_isolation.py`** (NEW per Codex 1.16, H11) — asserts `relate_all_async` files perspective-specific stances under the perspective-specific source claim.
    - Build claims A and B with distinct source-claim records.
    - Drive `relate_all_async` over a pair (A, B). Mock `classify_stance_async` to emit a forward stance (A→B says "supports") and a reverse stance (B→A says "undercuts").
    - Assert the forward stance is filed under A's source-claim record (perspective: A asserts something about B).
    - Assert the reverse stance is filed under B's source-claim record (perspective: B asserts something about A).
    - Assert the two stance rows do NOT share a perspective key.
    - Assert deletion of A's source-claim removes A's stance toward B but does NOT remove B's stance toward A.
    - **Must fail today**: `relate.py:258-263` files stances under one source claim regardless of which perspective extracted them.

11. **`tests/test_no_embedding_key_collision.py`** (NEW per D-19) — registers four colliding model names; asserts four distinct identities.
    - Register four embedding models with names `a/b`, `a-b`, `a_b`, `a b` (same `provider`, same `model_version`, same `content_digest` if the provider gives one — i.e. ONLY `model_name` differs).
    - Assert four distinct `EmbeddingModelIdentity` values; four distinct `model_identity_hash` values; four distinct rows in the sidecar embedding registry; four distinct cache rows for the same content; four distinct provenance chains threading back to `model_name`.
    - Assert that retrieving embeddings keyed on `model_name="a/b"` returns ONLY the `a/b` rows — never the `a-b`, `a_b`, or `a b` rows.
    - Assert that `_sanitize_model_key` does not exist anywhere in `propstore/`.
    - Assert that no SQL table name, column suffix, or column value in the embeddings registry is derived by character-sanitization of `model_name`.
    - Negative case: a fifth registration with the *exact* same four-tuple as one of the prior four hits the existing identity (idempotent re-registration); no new row.
    - **Must fail today**: all four sanitize to `a_b`; one row, one identity, no boundary between models.

12. **`tests/test_commit_stance_proposals_commit_sha_inside_with.py`** — AST-asserts `transaction.commit_sha` access is inside the `with repo.families.transact(...)` block (H14).

13. **`tests/test_plan_stance_proposal_promotion_typo_path.py`** — typo'd path raises typed `UnknownProposalPath`, NOT `items=()` (H16).

14. **`tests/test_promote_stance_proposals_idempotency.py`** — second promote does not silently overwrite; idempotency guard fires (H15).

15. **`tests/test_workstream_k_done.py`** — gating sentinel; `xfail` until WS-K closes.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-K step N — <slug>`.

### Step 1 — Move heuristic modules under `propstore/heuristic/`
Move `embed.py`, `classify.py`, `relate.py`, `calibrate.py` from top-level into `propstore/heuristic/`. Update every importer. **No shim, no alias** (per `feedback_no_fallbacks` + D-3).

Acceptance: `tests/test_heuristic_package_layout.py` (location half) green.

### Step 2 — Replace `dedup_pairs` minimum-distance collapse (H9)
Change signature to return `(a, b, forward_distance, reverse_distance)`. Update `relate_all_async:213-220` and the calibrator path to consume both. Document the asymmetric-distance contract in the module docstring.

Acceptance: `tests/test_dedup_pairs_preserves_mirror.py` green.

### Step 3 — Replace embedding sanitized-string key with identity tuple (D-19)
- Introduce `propstore.heuristic.embeddings.EmbeddingModelIdentity` (the four-tuple) and `model_identity_hash` derivation. Locate the module at `propstore/heuristic/embedding_identity.py` (sibling to the moved `embed.py`).
- Migrate `_EmbeddingStore.ensure_storage`, `existing_content_hashes`, and every read/write path to take `EmbeddingModelIdentity` (or `model_identity_hash`) instead of `model_key: str`.
- Sidecar schema migration: drop the sanitized-string column scheme; add the four typed columns plus `model_identity_hash` and the `UNIQUE` constraint. Coordinate this DDL change with WS-A's `_REQUIRED_SCHEMA` extension so production and fixture schemas land the new columns in lockstep.
- Delete `_sanitize_model_key` from `propstore/heuristic/embed.py`. Delete every caller. **No shim, no alias** (per `feedback_no_fallbacks` + D-3).
- Update `propstore/heuristic/embed.py:118` and `:217` (post-move locations) to compute `EmbeddingModelIdentity` from the litellm model spec at the call boundary and thread it through.
- Bulk-migration of existing sanitized rows is OUT OF SCOPE per D-3.

Acceptance: `tests/test_no_embedding_key_collision.py` green; grep for `_sanitize_model_key` returns zero hits in `propstore/`.

### Step 4 — Delete `derive_source_document_trust`
Remove the function from `propstore/heuristic/source_trust.py`. Remove call sites at `propstore/app/sources.py:190-201` and `:504-516`. `finalize_source` and `_auto_finalize_source` finalize with `trust.status = DEFAULTED` and a vacuous Opinion; the new pipeline (Step 6) populates trust on a follow-up commit.

**No shim, no alias.** Per `feedback_no_fallbacks` and D-3.

Acceptance: `tests/test_no_derive_source_document_trust.py` green.

### Step 5 — Lift `prior_base_rate` to `Opinion`
- `SourceTrustBlock.prior_base_rate: float | None` → `Opinion | None`.
- `propstore/sidecar/passes.py:112-118` — JSON column for the four Opinion components.
- `propstore/praf/engine.py:159-161` — consume Opinion directly; no float coercion.
- `propstore/core/row_types.py:466,655-656,722` — round-trip Opinion fields.
- Every other consumer the grep turns up — update in one pass; no compat shims.

Acceptance: `tests/test_prior_base_rate_is_opinion.py` green.

### Step 6 — Author the argumentation pipeline
Create `propstore/source_trust_argumentation/__init__.py` exposing `calibrate_source_trust`, `SourceTrustResult`, `RuleFiring`. Implementation loads rules from `knowledge/rules/<paper>/` (WS-K2 produces; WS-K stubs hand-authored fixtures), loads source metadata from `source.yaml`, dispatches to the kernel, and translates the grounded extension into an Opinion per a documented mapping (supporting-undefeated → `b`, attacking-undefeated → `d`, blocked / unfilled → `u`, base rate `a` from field defaults). Cite the mapping in the module docstring.

Acceptance: `tests/test_source_trust_argumentation.py` green.

### Step 7 — Wire promote-time recalibration hook
After `repo.families.transact(...)` succeeds in `propstore/source/promote.py` (per D-6), invoke `calibrate_source_trust` and commit the resulting trust block onto the source branch as a follow-up commit. Recalibration also fires when a rule-authoring meta-paper is promoted or the kernel pin moves.

Acceptance: `tests/test_trust_calibration_runs_at_promote.py` green.

### Step 8 — Replace single bidirectional LLM call with two independent calls (H10, Codex 1.16)
- Refactor `propstore/heuristic/classify.py:classify_stance_async` so it issues TWO independent LLM calls per pair: one for the forward direction (a→b), one for the reverse (b→a).
- Each call gets its own prompt rendering (forward and reverse prompts are distinct templates, NOT a single bidirectional template), its own LLM context, its own raw-response capture, and its own `Provenance` (with distinct `llm_call_id`).
- Return shape: a typed pair `(forward_stance, reverse_stance)` where each is a fully independent stance object with its own opinion and provenance. Forward and reverse can disagree; both opinions persist; nothing in the codepath collapses them.
- Cost note: this doubles the LLM call count per pair. Tradeoff acknowledged. The tests assert that forward/reverse independence is observable; observability is the discipline. Per `project_design_principle`, observable disagreement beats opaque agreement.
- Update every caller (`relate.py:125`, `:228`, `:412`) to consume the new pair shape; delete any code path that flattened the bidirectional response into a single stance.

Acceptance: `tests/test_classify_forward_reverse_independent.py` green.

### Step 9 — Per-perspective stance filing (H11, Codex 1.16)
- Refactor `propstore/heuristic/relate.py:relate_all_async` (lines `:258-263` in current code) so each stance is filed under the source claim that authored its perspective.
- The forward stance (extracted from the forward LLM call) files under claim A's source-claim record; the reverse stance files under claim B's source-claim record. The "perspective" is a structural property of the stance row, not a string label.
- The schema/row shape gains an explicit `perspective_source_claim_id` column (or equivalent typed field on the persisted stance). Coordinate with WS-A schema parity.
- Even when the two stances are extracted from the same Step-8 call pair, they file under distinct perspective records. Deletion of one perspective's source-claim does not affect the other.
- Update every consumer that previously fetched stances by collapsed key to fetch per-perspective; delete the collapsed lookup path.

Acceptance: `tests/test_relate_perspective_isolation.py` green.

### Step 10 — Fix `classify.py` silent fallback and `confidence=0.0` conflation
- `classify.py:389` — replace `result.get("forward", result)` with explicit shape check. On failure, return a stance pair carrying `Provenance(status=ProvenanceStatus.VACUOUS, operations=("llm_output_shape_unknown",))` and a vacuous Opinion. (Note: after Step 8 there are two responses; this shape check applies to each independently.)
- `classify.py:299-302` — when `opinion is None`, `confidence = None` (not `0.0`); serialize as JSON null. Update consumers to inspect `unresolved_calibration` rather than `confidence == 0.0`.

Acceptance: `tests/test_classify_no_silent_fallback.py` green.

### Step 11 — Proposal lifecycle ring of bugs
Five small commits, one each:

- **11a** (H14) — Move `transaction.commit_sha` access inside the `with` block in `propstore/proposals.py:182-202`.
- **11b** (H16) — Raise typed `UnknownProposalPath` in `plan_stance_proposal_promotion` on typo'd path.
- **11c** (H15) — Idempotency guard in `promote_stance_proposals`: record `promoted_from_sha`; refuse re-promote unless `--force`.
- **11d** (H17) — Replace `cast("Repository", object())` placeholder with real construction.
- **11e** (H18) — Reconcile empty-input handling between `commit_stance_proposals` and `app/claims.py:601-602`.

### Step 12 — Negative import-linter test (WS-N2 coordination)
Add `tests/architecture/test_import_linter_negative.py` per the test plan with a single `heuristic -> source.finalize` forbidden contract added to make it pass. WS-N2 inherits.

Acceptance: `tests/architecture/test_import_linter_negative.py` green.

### Step 13 — Close gaps, flip sentinel
Update `docs/gaps.md`: remove `dedup_pairs` MED, add `# WS-K closed <sha>`; remove or close H9, H10, H11, and the embedding-key-collision row. Flip `tests/test_workstream_k_done.py` from `xfail` to `pass`. Update STATUS line to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-K done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors.
- [ ] `uv run lint-imports` — passes with the new `heuristic -> source.finalize` forbidden contract in place.
- [ ] All 15 first-failing tests are green via `scripts/run_logged_pytest.ps1 -Label WS-K <every test path>`.
- [ ] Full suite — no NEW failures vs the WS-A-stabilized baseline.
- [ ] `propstore/embed.py`, `propstore/classify.py`, `propstore/relate.py`, `propstore/calibrate.py` no longer exist at top level; all live under `propstore/heuristic/`.
- [ ] `derive_source_document_trust` does not exist anywhere in `propstore/`.
- [ ] `propstore/source_trust_argumentation/` exists with `calibrate_source_trust` returning `SourceTrustResult`.
- [ ] `SourceTrustBlock.prior_base_rate` is typed `Opinion | None` end-to-end.
- [ ] `propstore/source/promote.py` invokes `calibrate_source_trust` after the git transaction.
- [ ] `_sanitize_model_key` does not exist; embeddings registry stores typed four-tuple identity.
- [ ] `classify_stance_async` issues two independent LLM calls per pair; returns a typed forward/reverse pair with distinct provenance.
- [ ] `relate_all_async` files stances under perspective-specific source claims.
- [ ] WS-K property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-K test run or a named companion run.
- [ ] `docs/gaps.md` has no open row for `dedup_pairs`, "heuristic logic outside `heuristic/`", "trust calibration breaks proposal gate," H10, H11, or the embedding-key-collision finding.
- [ ] STATUS line is `CLOSED <sha>`.

## Done means done

Done when **every finding in the table at the top is closed**. H10 and H11 are no longer deferred; they ship here. The D-19 embedding-key collision ships here. If any acceptance gate is not true, WS-K stays OPEN.

## Cross-stream notes

- **WS-A coordination** — the embedding-registry schema migration (Step 3) and the perspective-source-claim column (Step 9) both extend the production sidecar schema. WS-A's `_REQUIRED_SCHEMA` and the production-schema fixture builder must learn these columns at the same commit; do not split.
- **WS-K2 coordination** — produces the rule corpus under `knowledge/rules/<paper>/`. WS-K consumes; tests use hand-stubbed fixtures so the pipeline can be verified independently of WS-K2's extraction quality.
- **WS-N2 coordination** — Step 12 writes the layered-contract negative scaffolding; WS-N2 replaces the four `forbidden` contracts with a single `layered` contract.
- **WS-O-arg-argumentation-pkg coordination** — kernel ships from the `argumentation` package per D-15. Pin explicitly; re-run on every kernel pin bump.
- **WS-E coordination** — Step 11's proposal lifecycle bug fixes hang off whatever WS-E stabilizes for `propstore/proposals.py`. Rebase if WS-E moves the file.

## What this WS does NOT do

- Does NOT extract meta-paper rules from PDFs — WS-K2.
- Does NOT replace the four `forbidden` contracts with `layered` — WS-N2.
- Does NOT add admission control to the embedding registry. **H13 (Cluster H — `embed.py` accepts arbitrary model names with no admission control) is explicitly OUT OF SCOPE for WS-K** and remains an open separate LOW concern. D-19's identity-tuple migration is a distinct fix (collision-proof identity for *registered* models); it does not gate, govern, or imply admission control over *which* models may register. H13 is owned by a future LOW workstream (TBD). The two findings live in adjacent code (`propstore/heuristic/embed.py` post-Step-1 move) but have orthogonal remediations; do not claim WS-K closes H13.
- Does NOT bulk-migrate existing sanitized-key embedding rows — OUT OF SCOPE per D-3.

## Papers / specs referenced

Load-bearing meta-papers for calibration (WS-K2 extracts trust rules from each): **Ioannidis 2005**, **Begley & Ellis 2012**, **Aarts et al. (OSC) 2015**, **Errington et al. 2021**, **Camerer et al. 2016 / 2018**, **Klein et al. 2018** (Many Labs 2), **Border et al. 2019**, **Horowitz 2021**.

Project memory:

- `feedback_imports_are_opinions` — Steps 5, 6.
- `project_architecture_layers` — Steps 1, 4, 6 move calibration Layer 3 → Layer 4.
- `project_design_principle` — Steps 2, 3, 5, 8, 9 close disagreement-collapse violations.
- `feedback_no_fallbacks` — Steps 1, 3, 4, 5, 8, 9, 10 rip predecessors without compat shims.
