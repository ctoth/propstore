# Cluster U: architecture adversary review

## Scope

Targets read for this review (file paths corrected from parent prompt where the parent had stale paths):

- `C:\Users\Q\code\propstore\.importlinter` (repo root, not `propstore/.importlinter`)
- `C:\Users\Q\code\propstore\propstore\contracts.py`
- `C:\Users\Q\code\propstore\propstore\contract_manifests\semantic-contracts.yaml` (head only — generated, 9090+ lines)
- `C:\Users\Q\code\propstore\AGENTS.md`, `README.md`, `TODO.md`, `algorithms.md`, `aspic.md`
- `C:\Users\Q\code\propstore\pyproject.toml`
- `C:\Users\Q\code\propstore\docs\` — `gaps.md` (full), `epistemic-operating-system.md`, `argumentation-package-boundary.md`, `data-model.md` (head), `python-api.md` (head), `integration.md` (head), `semiring-provenance-architecture.md` (head), `structured-argumentation.md` (head), `defeasibility-semantics-decision.md`
- `C:\Users\Q\code\propstore\tests\test_artifact_boundary_failures.py`, `tests\test_artifact_identity_policy.py`, `tests\conftest.py`, `tests\remediation\phase_4_layers\test_T4_1_importlinter_layers.py`
- Targeted production reads driven by grep: `propstore\heuristic\source_trust.py`, `propstore\app\sources.py`, `propstore\source\finalize.py`, `propstore\relate.py`, `propstore\classify.py`, `propstore\world\types.py`, `propstore\world\resolution.py`, `propstore\sidecar\build.py`, `propstore\storage\repository_import.py`, `propstore\grounding\grounder.py`, `propstore\core\concept_status.py`, `propstore\opinion.py`

`propstore/tests/architecture/` does not exist. `tests/test_artifact_*.py` exist at repo-level `tests/`.

OBSERVED vs INFERRED is called out per finding.

## Import-linter contracts: gaps and weak spots

OBSERVED. The full contract surface is four `forbidden` contracts in `.importlinter:5-36`:

```
storage -> merge        (propstore.storage cannot import propstore.merge)
source -> heuristic     (propstore.source cannot import propstore.heuristic)
concept -> argumentation (propstore.core.lemon cannot import argumentation)
worldline -> support_revision (propstore.worldline cannot import propstore.support_revision)
```

OBSERVED weakness #1 — every forbidden contract is **vacuously satisfied today**:
- `propstore/storage/*.py` does not import `propstore.merge`. The reverse (`merge -> storage`) is the actual dependency: `propstore\merge\structured_merge.py:18`, `merge_classifier.py:17`, `merge_commit.py:15` all import `propstore.storage.snapshot.RepositorySnapshot`.
- `propstore/source/*.py` does not import `propstore.heuristic`. The reverse (`heuristic -> source`) is actual: `propstore\heuristic\source_trust.py:14` imports `propstore.source.common`.
- `propstore/core/lemon/*.py` has zero imports of `argumentation.*`.
- `propstore/worldline/*.py` has zero imports of `propstore.support_revision`.

INFERRED: the contracts therefore catch *no current violation*. They were written defensively, but `lint-imports` provides false assurance — passing it means nothing about whether the README's six-layer architecture holds.

OBSERVED weakness #2 — the README claims **six layers** with one-way downward dependencies, but only **four** narrow forbidden edges are encoded. The contract fails to express:
- `propstore.source` cannot import `propstore.argumentation` / `propstore.aspic_bridge` / `propstore.world` / `propstore.belief_set`
- `propstore.storage` cannot import any layer above storage
- `propstore.heuristic` should not be importable from anything claiming to be Layer 1 or 2
- `propstore.app.*` should not be importable from CLI command-family modules without going through declared entry points (AGENTS.md:39-46 explicitly states this rule but no contract enforces it)
- `propstore.web.*` should not be reachable from owner-layer modules

OBSERVED weakness #3 — no `layered` contract type is used at all. `import-linter` supports `type = layers` for ordered stacks; the README's stack is the canonical use case, yet the project chose four spot-checks instead of a single layered contract. The actual implementation cost would have been ~15 lines.

OBSERVED weakness #4 — `pyproject.toml:65` lists `propstore/aspic_bridge.py` in pyright `strict`. That file does not exist (`aspic_bridge/` is a package). The strict-mode entry silently does nothing. This is also called out in `docs/gaps.md` MED ("CLAUDE.md references `aspic_bridge.py` as a file") but was never propagated to `pyproject.toml`.

OBSERVED weakness #5 — the test gating is real but minimal: `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py` shells out to `uv run lint-imports` and asserts return code 0. There is no negative test asserting that a *known violation* would be caught — so the contract surface is never exercised against true bad imports.

## Layering violations (heuristic leakage, source→heuristic, etc.)

OBSERVED — heuristic leakage out of `propstore/heuristic/`:

The `propstore/heuristic/` package contains exactly two files: `__init__.py` and `source_trust.py`. The README (`README.md:11-13`) names Layer 3 as "embeddings, LLM stance classification (proposals only)". The actual heuristic logic — embeddings, similarity scoring, LLM stance classification — lives at the *top level* of the package, not under `heuristic/`:

- `propstore/embed.py` — embedding generation, similarity search
- `propstore/classify.py` — LLM stance classification
- `propstore/relate.py` — pair discovery, batched LLM relation classification
- `propstore/calibrate.py` — calibration logic

OBSERVED — these top-level heuristic modules are imported from layers that should not consume Layer 3 directly:

- `propstore/sidecar/build.py:460` — `from propstore.embed import _load_vec_extension, extract_embeddings`. **Sidecar build is a storage-tier compilation step. It is consuming heuristic artifacts (embeddings) directly.**
- `propstore/world/model.py:973,998` — `from propstore.embed import find_similar, find_similar_concepts`. World/Render layer importing from heuristic.
- `propstore/app/claims.py:470,524,574-577`, `propstore/app/concepts/embedding.py:38,101`, `propstore/app/concepts/mutation.py:522,585` — application layer importing embed/relate.

OBSERVED — `source -> heuristic` direction (the only one the linter defends): no current violations. Direction is backward (`heuristic -> source` at `heuristic\source_trust.py:14`). The contract is defending against the impossible.

OBSERVED — the most damning concrete leak: `propstore/app/sources.py:191-200` and `:505-516` both do:

```python
from propstore.heuristic.source_trust import derive_source_document_trust
...
finalize_source_branch(repo, request.name, source_doc=derive_source_document_trust(repo, source_doc))
```

`derive_source_document_trust` (in `heuristic/source_trust.py:103-172`) returns a *new* `SourceDocument` with a mutated `trust` block. `finalize_source_branch` (in `source/finalize.py:178-185`) writes that document to the source branch via `transaction.source_documents.save(...)`.

**Heuristic-derived trust calibration is being committed to git as the canonical source-branch source document.** Per README ("Layer 3 produces proposals, never mutations"), this is a layering violation. The trust is being *promoted to source-of-truth* without going through any proposal/promote gate.

OBSERVED — `core/lemon` contract overshoot: forbidding `propstore/core/lemon/` from importing `argumentation` is fine, but the contract should logically extend to the entire `propstore.core` and `propstore.families` namespace.

## Non-commitment principle violations (storage-collapse audit)

The principle (per memory): *never collapse disagreement in storage unless user explicitly requests migration*.

OBSERVED — confessed gaps still open in `docs/gaps.md`:

1. **`relate.py:67-74` `dedup_pairs`** — verified verbatim. Mirror pairs `(A,B,d1)` and `(B,A,d2)` are dedup'd by `frozenset({a,b})` keeping the *shortest* `dist`; the rival relation is silently discarded with no provenance. Collapse at the pair-discovery (storage-feeding) level. **NOT YET SCHEDULED**.
2. **`source/finalize.py:178-217` `finalize_source_branch`** — verified verbatim. `attach_source_artifact_codes` returns `updated_source/claims/justifications/stances`; transaction immediately calls `transaction.source_documents.save(ref, ...)`. The branch retains *one* finalized stance, overwriting the authored payload. Authored-vs-finalized rivalry is destroyed in storage. **NOT YET SCHEDULED**.
3. **`sidecar/claim_utils.py:596-606`** (per gaps.md HIGH) — non-SI written to `_si` columns on exception. Did not re-verify in this pass; gaps.md is the authoritative claim.

OBSERVED — newly-flagged collapse sites:

4. **`grounding/grounder.py:141-149`** — self-confessed `# backwards compatibility — existing callers pay no argument-enumeration cost. Block 3 of the gunray refactor exposes this typed view alongside the legacy section projection`. Two parallel views (sections + arguments) maintained for compatibility. Per AGENTS.md:21-22 ("Do not add compatibility shims, aliases, fallback readers, bridge normalizers, or dual-path glue") this should not exist.
5. **`classify.py:389`** — `forward_raw = result.get("forward", result)  # fallback: treat whole response as forward`. When the LLM returns a non-bidirectional response, the code silently treats the whole blob as a forward stance and synthesizes a `{"type": "none", "strength": "weak", "note": "not classified"}` reverse. Should fail loud or carry an `LLM_OUTPUT_SHAPE_UNKNOWN` marker.
6. **`world/types.py:1275-1281` `CONFIDENCE_FALLBACK`** — `# Fall back to raw confidence when opinion is missing (old data).` First-class enum value `DecisionValueSource.CONFIDENCE_FALLBACK` (defined `world/types.py:1206`) with three test files asserting against it. AGENTS.md:21-22 says fallbacks are forbidden unless old data must be supported.
7. **`world/types.py:958-959` and `:1257-1258`** — `decision_criterion: str = "pignistic"` cited as Denoeux 2019 in the field comment but the formula at line 1259 is `b + a*u` (Jøsang Def 6, p.5). The user-visible flag remains "pignistic" while the math is Jøsang's expectation. gaps.md HIGH, axis-3b F2, **PLAN: WS-Z-types**, still open.
8. **`opinion.py:432 wbf()`** — gaps.md HIGH says implementation has three structural divergences from van der Heijden 2018 WBF formula; worked example drifts 0.175 absolute on uncertainty. Function is *named* WBF, computes aCBF.
9. **`core/concept_status.py:13-15`** — `_CONCEPT_STATUS_ALIASES = {"active": ConceptStatus.ACCEPTED}`. Quiet input alias accepting the legacy string `"active"` and silently coercing. Per AGENTS.md, this is forbidden unless old data support is explicit. No comment, no deprecation note, no doc reference.

OBSERVED — counter-examples (good faith): `world/resolution.py:148-177 _resolve_recency` and `:180-199 _resolve_sample_size` correctly return `(None, "tied recency")` rather than picking arbitrarily. Render-time tie handling is honest. Storage-time collapse is the issue.

OBSERVED — silent-drop in `aspic_bridge`:

10. **`docs/structured-argumentation.md:26`** documents: *"Rules where premise or conclusion literals are missing (because the corresponding claim is inactive) are silently dropped."* This is non-commitment violation surfaced honestly in docs but live in code. The drop should at minimum produce a `BridgeDiagnostic`.

## "Imports are opinions" violations

Principle (per memory `feedback_imports_are_opinions.md`): every imported KB row (BFO, QUDT, material-db, OWL rules, mined associations, LLM proposals) is a defeasible claim with provenance, never truth — no source is privileged.

OBSERVED — `propstore/storage/repository_import.py` is the cross-repo import surface. It defines `RepositoryImportPlan`, `RepositoryImportResult`, plans writes, executes commits. **Grep for "provenance" in this file: zero matches.** The import path does not annotate imported rows with any provenance field recording where they came from.

INFERRED — without re-reading the entire flow, I cannot prove that no provenance is attached *anywhere* downstream. But the file that owns the import-write path itself contains no provenance string at all. If provenance is attached, it is happening implicitly via copy-of-payload, which is exactly what `feedback_imports_are_opinions` warns against: a copied row carries the *original* `provenance` block from its source repo and gains no annotation that it was imported into *this* repo by this commit.

OBSERVED — `propstore/heuristic/source_trust.py:108-112` writes status correctly. But the same function unconditionally returns a mutated `SourceDocument` with no record that the trust block was *derived by* a heuristic process — `trust.derived_from` records claim chain, but the *fact that derivation happened by a heuristic stage* is not separately provenanced.

OBSERVED — embeddings stored in sidecar tables are not provenanced as model-opinions in the storage schema. Embeddings are vectors of opinion (the model's geometry of meaning); they should carry model identity, model version, and provenance status.

## Compat-shim / fallback inventory

Strict grep on `# legacy|# deprecated|# compat|# fallback|# shim|# backwards|legacy_` produced only two real production hits (after filtering false positives):

| File:Line | Kind | Verbatim |
|-----------|------|----------|
| `propstore\classify.py:389` | fallback | `forward_raw = result.get("forward", result)  # fallback: treat whole response as forward` |
| `propstore\grounding\grounder.py:141-144` | backwards-compat | `for backwards compatibility — existing callers pay no argument-enumeration cost. Block 3 of the gunray refactor exposes this typed view alongside the legacy section projection` |

Wider grep (`old data|old format|old shape|legacy data|legacy format|backwards|back-compat|retro`):

| File:Line | Kind | Verbatim |
|-----------|------|----------|
| `propstore\world\types.py:1239` | old-data accommodation | `opinion_b/d/u/a: Opinion components (may be None for old data)` |
| `propstore\world\types.py:1275` | old-data fallback | `# Fall back to raw confidence when opinion is missing (old data).` |

First-class shim/alias surfaces (no comment, but architecturally a shim):

| Surface | Location | Smell |
|---------|----------|-------|
| `_CONCEPT_STATUS_ALIASES = {"active": ACCEPTED}` | `core\concept_status.py:13-15` | Silent alias for legacy string |
| `DecisionValueSource.CONFIDENCE_FALLBACK` | `world\types.py:1206` | Enum value committed to fallback path |
| `pyproject.toml:65 propstore/aspic_bridge.py` | `pyproject.toml` | Dead pyright-strict entry pointing at non-existent file |
| Calibration `"fallback_to_default_base_rate"` field | `source\finalize.py:237` | Locks "default" provenance into source-branch report |

OBSERVED non-shims: strict grep on `TODO|FIXME|XXX|HACK` against `propstore/` returned **zero** matches — production code is clean of those markers. Quality discipline is real.

## Doc → code drift

OBSERVED:

1. **`algorithms.md:13-37`** is a stale design briefing referencing files that no longer exist:
   - `propstore/validate_claims.py` — does not exist
   - `propstore/conflict_detector.py` (flat module) — actual is `propstore/conflict_detector/` package
   - `propstore/build_sidecar.py` — actual is `propstore/sidecar/build.py`
   - `propstore/world_model.py` — actual is `propstore/world/model.py`
   - `propstore/description_generator.py` — does not exist
   - `propstore/propagation.py` — does not exist
2. **`aspic.md:13`** references `_resolve_stance` in `propstore/world/resolution.py`. Grep returns no matches — function name has changed to `_resolve_recency`, `_resolve_sample_size`, etc.
3. **gaps.md MED** flags `aspic_bridge.py` references in CLAUDE.md, README.md, `docs/argumentation.md:30`, `docs/data-model.md:332`, `agent-papers.md`, `EXPLORATION_NOTES.txt`, **plus `pyproject.toml:65`** which gaps.md missed. Same drift.
4. **`README.md:75`** lists reasoning backend `aspic` with key files `aspic_bridge/`, `external argumentation.aspic`. Good. README is mostly current.
5. **`docs/integration.md:38-44`** — Reconciliation workflow says "This is automated — no human review required." Cross-check against `docs/integration.md:62` which says "Currently, only stance proposals are supported. Concept and claim proposals must be manually reviewed and moved." Internal contradiction.
6. **`docs/python-api.md:14`** says `WorldModel.from_path("knowledge")`. The architecture commits to multi-world / ATMS reasoning. The *type name* `WorldModel` (singular) is a render-layer commitment-name; what the API returns is a query surface that can produce extensions, hypotheticals, and ATMS labels. INFERRED smell.
7. **`docs/structured-argumentation.md:26`** documents "silently dropped" — *the doc admits the violation*.
8. **`docs/epistemic-operating-system.md`** is a 46-line stub. INFERRED placeholder shape.
9. **`docs/argumentation-package-boundary.md:64`** says "the old propstore module paths are deleted." Cross-check: `pyproject.toml:65` still lists `propstore/aspic_bridge.py`.

## Naming drift (commitment-implying type names)

OBSERVED — types that imply commitment more strongly than the architecture allows:

1. **`WorldModel`** (`propstore/world/model.py`). Singular "world" + "model" suggests a committed view. Actual semantics support multi-extension reasoning, hypotheticals, ATMS branching. `WorldQuery` or `WorldSurface` would carry non-commitment better.
2. **`derive_source_document_trust`** (`heuristic/source_trust.py:103`). "Derive" suggests pure reading; function returns a *mutated* SourceDocument the caller persists. Should be `propose_source_trust_calibration` returning a typed `SourceTrustProposal`.
3. **`Verdict`** appears in code/docstrings (`propstore/grounding/grounder.py:42,102`, `sidecar/rules.py:20,129,243`). "Verdict" is a commitment-laden judicial term. "Outcome", "Status", "Classification" would be neutral.
4. **`DecisionValueSource.CONFIDENCE_FALLBACK`** — naming the enum value `FALLBACK` formalizes the shim. `LEGACY_RAW_CONFIDENCE` would be clearer.
5. **`ConceptStatus.ACCEPTED`** + alias `"active" -> ACCEPTED`. The alias collapses an explicit semantic difference without written justification.
6. **`Truth`/`Fact`/`Belief`/`GroundTruth`**: grep returned **no class definitions** matching these names. Naming hygiene at the type level is generally good. Counter-evidence: `opinion.py` correctly raises on `__bool__` to prevent truthy-coercion accidents (`opinion.py:186-196`).
7. **`Repository.save(...)`** family. "Save" combined with `finalize` overwriting in place — `commit_revision` would carry version semantics more honestly.

## What `docs/gaps.md` says — verbatim inventory

`docs/gaps.md` open gap counts and titles:

**HIGH:** 3
- "CLAUDE.md 'Pignistic' claim names Denoeux but implements Jøsang." (`propstore/world/types.py:1064-1066`, plan WS-Z-types)
- "`opinion.wbf()` is algebraically aCBF, not WBF." (`propstore/opinion.py`, plan WS-Z-types)
- "Sidecar claim SI normalization silently writes non-SI values to `_si` columns." (`propstore/sidecar/claim_utils.py:596-606`, plan not yet scheduled)

**MED:** 7-9
- "`dedup_pairs` collapses mirror pairs without provenance." (`propstore/relate.py:67-74`, plan not yet scheduled)
- "`finalize_source_branch` mutates authored payloads in place." (`propstore/source/finalize.py:96-140`, plan not yet scheduled)
- "Probabilistic argumentation treewidth bound doesn't deliver." (`propstore/praf/treedecomp.py:13-17`)
- "Ordinary-premise ordering remains metadata-derived." (plan future premise-priority workstream)
- "Oikarinen strong-equivalence kernels are absent." (plan future strong-equivalence workstream)
- "`pks world chain` accepts lifecycle flags but does not behaviorally filter."
- "CLAUDE.md references `aspic_bridge.py` as a file, but it is now a package."
- "`aspic.py` cites 'Modgil & Prakken 2018 Def 1 (p.8)' for contrariness — wrong number, wrong page, wrong content."
- "`artifacts/documents/rules.py:120` cites Def 13 for last-link."

**LOW / NOTE:** 7 — pyright errors in `source/common.py`, test markers lying about content, 7 production modules with zero test references, `papers/index.md` 21% incomplete, CLAUDE.md "Defs 1-22" shorthand, CLAUDE.md TIMEPOINT pointing at wrong file, citation-pattern drift cross-cutting.

Cross-check with my findings:
- gaps.md HIGH `world/types.py:1064-1066` — actual location is `:958-959` (default field) and `:1257-1259` (formula). **gaps.md itself has a line-number drift.**
- My findings 4-6 (`grounding/grounder.py:141-144` backwards-compat, `classify.py:389` fallback, `world/types.py:1275-1281` CONFIDENCE_FALLBACK) and finding 9 (`core/concept_status.py:13-15` alias) are NOT in gaps.md. New gaps to add.
- My finding on `pyproject.toml:65 aspic_bridge.py` extends gaps.md MED.
- My finding on import-linter contracts being vacuous and `tests/test_T4_1_importlinter_layers.py` only asserting passing (no negative test) is NOT in gaps.md.
- My finding on `storage/repository_import.py` having zero provenance annotations is NOT in gaps.md.

## Top architectural risks to address before next release

1. **Heuristic logic lives outside `propstore/heuristic/`.** `embed.py`, `classify.py`, `relate.py`, `calibrate.py` are top-level modules invoked from `sidecar/build.py`, `app/claims.py`, `world/model.py`. Either rename the package or move the modules.
2. **`derive_source_document_trust` writes heuristic output to source storage with no proposal gate.** `app/sources.py:191-200,505-516` → `source/finalize.py:178-185`. Layer 3 → Layer 1 mutation in production.
3. **Import-linter contracts are vacuous.** All four forbidden edges have zero current import attempts. Replace with a `layered` contract over the six README layers and add at least one negative test.
4. **Storage-time non-commitment violations remain unscheduled.** `relate.py:67-74` and `source/finalize.py` in-place mutation.
5. **`storage/repository_import.py` has no provenance annotation surface.** Imported rows look identical to authored rows in storage. Direct violation of "imports are opinions".
6. **`CONFIDENCE_FALLBACK`, `_CONCEPT_STATUS_ALIASES`, `# fallback: treat whole response as forward`, `# backwards compatibility` are explicit shims.** Either declare the old-data exception explicitly or delete.
7. **`pyproject.toml:65` strict list is dead.** `propstore/aspic_bridge.py` does not exist. Suggests the strict list is not exercised in CI.
8. **Citation-as-claim drift remains widespread.** Pignistic naming, aspic.py Def 1 vs Def 2; rules.py Def 13 vs Def 20.
9. **`docs/structured-argumentation.md:26` "silently dropped" rules.** ASPIC+ projection silently discards rules whose premise/conclusion claims are inactive. CSAF therefore does not faithfully represent authored knowledge base.
10. **`algorithms.md`, `aspic.md` are stale design briefings.** Move to `docs/historical/` or delete.

## Open questions for Q

1. README architecture diagram (Layer 3 = `propstore/heuristic/`) and actual package layout are inconsistent. Which is the target?
2. Is `app.sources.finalize_source` *intended* to commit heuristic-derived trust calibration directly to source branch?
3. `storage/repository_import.py` attaches no provenance. Deliberate or oversight?
4. `CONFIDENCE_FALLBACK`, `_CONCEPT_STATUS_ALIASES`, `world/types.py:1275 # old data` — is "old data" a project commitment? If yes, document the exception.
5. Four import-linter `forbidden` contracts are vacuous. Replace with `layered`?
6. `gaps.md` line numbers for pignistic/Denoeux are stale. Should `gaps.md` be regenerated with current line numbers?
7. The `Verdict` naming combined with "never collapse a verdict" promise creates conceptual tension. Deliberate?
8. `_CONCEPT_STATUS_ALIASES` carries no comment. Is `"active"` legitimate authored input today or legacy data?
9. There is no negative test for `lint-imports`. Add one or accept residual risk?
10. Cluster H (heuristic focused review) was named in the parent prompt — overlap allocation between U and H clear?

Statement: The principles are stated cleanly. The code respects them in places, betrays them in others, and the linter watches none of it. The codebase tells lies about itself in low-traffic corners (`algorithms.md`, `aspic.md`, `pyproject.toml` strict list) and in higher-traffic ones (Layer 3 mutating Layer 1 storage via `app/sources.finalize_source`). The non-commitment principle has unscheduled violations of MED severity. Imports-as-opinions has a structural blind spot at the cross-repo import surface. Recommendation: stop adding architecture and start adding negative tests.
