# Axis 1 — Principle Adherence

*Returned inline by adversary subagent (no Write tool); saved here verbatim.*

## Summary

propstore honors the non-commitment and proposals-not-mutations principles at the *storage-branch* level — proposal families (`PROPOSAL_STANCE_FAMILY` on `proposal/stances`, `CONCEPT_ALIGNMENT_FAMILY` on `proposal/concepts`) are cleanly separated and heuristic writers only reach primary-branch families through the explicit user-driven `source/promote.py` path. But the design-checklist principles and honest-ignorance principle are violated systemically. The **worst structural decision** is `calibrate._DEFAULT_BASE_RATES` — a hardcoded category-keyed prior dict that is silently folded into *every* vacuous opinion returned for uncalibrated LLM classifications, corrupting the `a` parameter (the one signal the Opinion algebra reserves for honest priors) with a fabricated constant. The build pipeline further installs two hard gates — `sidecar/build.py:75-82` aborts the sidecar build entirely when any claim has a raw-id error, and `compiler/passes.py:289-307` drops every `stage: draft` file from the semantic bundle — both of which directly violate design-checklist items 1, 2, and 4 ("prevent any data from reaching sidecar," "require human action before queryable," "filtering at build time").

Finding counts: **2 CRIT, 3 HIGH, 4 MED, 2 NOTE.**

## Findings by principle

### Principle 1 — Non-commitment discipline

#### Finding 1.1 — Proposal-branch separation is structurally correct (NOTE / positive)

- Severity: **note**
- Principle clause: "Do not collapse disagreement in storage unless the user explicitly requests a migration. The repository must be able to hold multiple rival normalizations, multiple candidate stances, multiple competing supersession stories…"
- Observation: `propstore/artifacts/families.py:165-178, 180-184, 410-420, 422-426` — `STANCE_FILE_FAMILY` writes to `_primary_branch(repo)`, `PROPOSAL_STANCE_FAMILY` writes to `STANCE_PROPOSAL_BRANCH`, `CONCEPT_ALIGNMENT_FAMILY` writes to `proposal/concepts`. Heuristic classify-and-emit (`propstore/proposals.py:55-87`) writes only to `PROPOSAL_STANCE_FAMILY`. The only call-sites that write `STANCE_FILE_FAMILY` or `CANONICAL_SOURCE_FAMILY` to primary are `propstore/source/promote.py:288,293,299,310,316` and `propstore/repo/repo_import.py:489` — both user-initiated. `cli/__init__.py:374-377` implements the promote step from proposal to stance.
- Why this is good: At the family/branch layer, the non-commitment discipline is encoded in types. Rival stances can coexist on the proposal branch. No heuristic-emitted data mutates canonical storage.

#### Finding 1.2 — `dedup_pairs` collapses mirror pairs without provenance (MED)

- Severity: **med**
- Principle clause: "Do not collapse disagreement in storage unless the user explicitly requests a migration."
- Violation: `propstore/relate.py:67-74`
  ```python
  def dedup_pairs(pairs: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
      best: dict[frozenset[str], tuple[int, float]] = {}
      for i, (a, b, dist) in enumerate(pairs):
          key = frozenset({a, b})
          if key not in best or dist < best[key][1]:
              best[key] = (i, dist)
  ```
- Why this violates it: `find_similar` is not guaranteed to produce symmetric distances. When `(A,B,0.3)` and `(B,A,0.4)` both exist, this keeps `(A,B,0.3)` and *throws away* `(B,A,0.4)`. That is a silent collapse of two rival evidence records at pair-selection time, not a rendering choice. The dropped pair may have participated in a bidirectional classification with different enrichment context. Record both, let the render layer pick.
- Recommendation: preserve both orientations; collapse only at render with a policy flag.

#### Finding 1.3 — `attach_source_artifact_codes` in `finalize_source_branch` rewrites stance/claim payloads at finalize time (MED)

- Severity: **med**
- Principle clause: "Never mutated by heuristic or LLM output. Immutable except by explicit user migration."
- Violation: `propstore/source/finalize.py:96-140` — finalize mutates source-branch artifacts in place (saves `SOURCE_DOCUMENT_FAMILY`, `SOURCE_CLAIMS_FAMILY`, `SOURCE_JUSTIFICATIONS_FAMILY`, `SOURCE_STANCES_FAMILY` with `updated_*` documents), overwriting the originals on the source branch.
- Why this matters: finalize is user-initiated (so it isn't a heuristic mutation), but the operation replaces the authored payload on the same branch instead of producing a finalized child or proposal. The branch's history preserves prior state via git, but the working artifact's *logical identity* for that branch is now "finalized." If the user re-runs extract-claims before promote, the finalized layer gets clobbered. This is a subtle non-commitment violation: the source branch holds exactly one stance (the latest finalize), not the rival "authored vs. finalized" distinction.
- Recommendation: put finalize outputs on a side-label (e.g. `finalized/<source>`) rather than overwriting the source-branch claims/stances files.

### Principle 2 — Honest ignorance over fabricated confidence

#### Finding 2.1 — `_DEFAULT_BASE_RATES` fabricates a "corpus frequency prior" that has no empirical basis (CRIT)

- Severity: **crit** (structural — worst single design decision found)
- Principle clause: "Every probability that enters the argumentation layer must carry provenance: either empirical evidence counts, a calibrated model output, or an explicit vacuous marker. 'I don't know' is a valid and important signal; a made-up 0.75 is not."
- Violation: `propstore/calibrate.py:211-217`
  ```python
  # Default base rates per category — corpus frequency priors.
  _DEFAULT_BASE_RATES: dict[str, float] = {
      "strong": 0.7,
      "moderate": 0.5,
      "weak": 0.3,
      "none": 0.1,
  }
  ```
  Used at line 278-281:
  ```python
  base_rate = _DEFAULT_BASE_RATES[cat]
  if calibration_counts is None:
      return Opinion.vacuous(a=base_rate)
  ```
- Why this violates it: The Opinion algebra reserves `a` (base rate / atomicity) as the honest component of a vacuous opinion — it is literally the "what to fall back on when we have zero evidence" signal (Jøsang 2001 p.8). This module hard-codes category-specific base rates (0.7 for "strong", 0.3 for "weak", etc.) that are documented as "corpus frequency priors" — but no corpus is sampled, no calibration is performed, and the comment itself reveals the mismatch: they're called "frequency priors" without any frequency measurement. Every uncalibrated LLM stance classification (the default path, because calibration rarely exists) goes through `Opinion.vacuous(a=_DEFAULT_BASE_RATES[cat])`. The "vacuous" marker is technically honest about the *evidence count* (u=1, r=s=0), but it lies through the base rate — a claim labelled "strong" gets `a=0.7` for free, which feeds directly into `E(ω) = b + a*u = 0 + 0.7*1 = 0.7` the moment anyone takes an expectation. The system has exactly one place to honestly encode "we don't know the prior either" — `a = 0.5` with a provenance marker — and it is being quietly filled with category-keyed guesses.
- Recommendation: either (a) make `_DEFAULT_BASE_RATES` a CLI/config parameter with provenance, (b) ship `a=0.5` as the module default plus a mandatory `CalibrationSource` tag distinguishing "default", "measured from corpus", "user-supplied", (c) error out if `calibration_counts is None` and require the caller to opt in to a named "I want the default" mode.

#### Finding 2.2 — `p_arg_from_claim` and `p_relation_from_stance` fallback to `Opinion.dogmatic_true()` (CRIT — overlap with axis 5)

- Severity: **crit**
- Principle clause: same as 2.1.
- Violation: `propstore/praf/engine.py:155-157, 197-199, 245-253`.
- Cross-ref: axis 5 findings 1.1, 1.2 cover the line-level detail. Axis 1 note: the structural issue is that the call-site of `p_arg_from_claim` (PrAF construction) has no way to distinguish "we verified this claim is maximally certain" from "we had no calibration data." The type of the return is `Opinion`, and `Opinion(1,0,0,0.5)` is valid; the violation is that the *source of the 1.0* is invisible downstream. The fix requires a type change, not a line fix.
- Recommendation: Return `Opinion | Vacuous(source="no_calibration_fields")` from the hook, not a dogmatic opinion; PrAF must treat the two cases differently.

#### Finding 2.3 — `fragility_scoring.imps_rev` fabricates dogmatic opinions for every argument and defeat (HIGH)

- Severity: **high**
- Principle clause: same as 2.1.
- Violation: `propstore/fragility_scoring.py:366-367`
  ```python
  p_args = {argument: Opinion.dogmatic_true() for argument in framework.arguments}
  p_defeats = {defeat: Opinion.dogmatic_true() for defeat in framework.defeats}
  ```
- Why this violates it: sensitivity analysis (`imps_rev` computes "removal-of-attack change in strength") is sold by the name as measuring *how fragile* a conclusion is under uncertainty. But it feeds a PrAF whose argument-existence and defeat probabilities are all fabricated as 1.0 before the analysis begins. The computation silently reports *only* the dfquad strength delta, not the true probabilistic fragility. No provenance marker on the result surfaces this.
- Recommendation: accept the real `p_args` / `p_defeats` (or compute them from the claim rows via `p_arg_from_claim`) instead of fabricating; if the caller wants deterministic analysis, force them to pass `vacuous` and interpret the dfquad output as a point estimate.

#### Finding 2.4 — `source_calibration.derive_source_trust` silently defaults `prior_base_rate=0.5` without provenance on the stored payload (HIGH)

- Severity: **high**
- Principle clause: "Every probability that enters the argumentation layer must carry provenance."
- Violation: `propstore/source_calibration.py:39, 65, 94-97`:
  ```python
  prior = float(trust.get("prior_base_rate", 0.5))
  …
  trust["prior_base_rate"] = prior
  trust["quality"] = quality
  trust["derived_from"] = derived_from
  updated["trust"] = trust
  ```
  The finalize report (`source/finalize.py:156-160`) separately records `calibration.fallback_to_default_base_rate: bool` — but this boolean lives *on the report*, not on the `SourceTrustDocument` itself. Once finalize is consumed and trust is loaded by `p_arg_from_claim` (`praf/engine.py:142-143`), the `0.5` is indistinguishable from a real derived prior.
- Why this violates it: The stored trust payload carries a `float` that could mean either "we derived this from a chain query" or "we had nothing and used 0.5." `SourceTrustDocument` has no field for this distinction. The only provenance marker is `derived_from: tuple[str,...]` — an empty tuple is the signal for "unknown," but nothing enforces that readers check it.
- Recommendation: add an explicit `prior_base_rate_status: Literal["derived","default","vacuous"]` to `SourceTrustDocument` so the provenance rides with the number, not in a sibling report.

#### Finding 2.5 — `SourceTrustQualityDocument` fields are mandatory floats, no vacuous sentinel (MED)

- Severity: **med**
- Principle clause: "'I don't know' is a valid and important signal."
- Violation: `propstore/artifacts/documents/sources.py:43-55` — `b, d, u, a: float | int` (required, no `None`).
- Why this violates it: in principle `b=0, d=0, u=1, a=0.5` *is* a valid vacuous Opinion (enforced by `opinion.py:33-43`), so the document can express ignorance numerically. But the type carries no `status` field — readers can't distinguish "we intentionally recorded vacuous" from "we put zeros because we had nothing else." Combined with 2.4, the `SourceTrust` subtree is a type that *can* express ignorance but cannot *label* ignorance.
- Recommendation: add `status: Literal["measured","vacuous","default"]` on `SourceTrustQualityDocument`, or swap the representation to a tagged union.

#### Finding 2.6 — Opinion invariant `b+d+u=1.0` prevents clean "no opinion" representation at the field level (NOTE)

- Severity: **note** / structural observation
- Principle clause: "'I don't know' is a valid and important signal; a made-up 0.75 is not."
- Observation: `propstore/opinion.py:33-43` enforces `b+d+u ≈ 1.0`. The enforcement is correct (invariant of the algebra). But `ResolutionDocument` at `propstore/artifacts/documents/claims.py:137-168` makes each of `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, `opinion_base_rate` independently `float | int | None` — so the document can hold `(None, None, None, None)` (means "no opinion recorded") or a valid opinion tuple. Axis 5 Finding 1.3 documents that `classify.py:148-161` nonetheless writes `(0.0, 0.0, 0.0, 0.5)` in the "no stance" case — bypassing both the vacuous representation `(0, 0, 1, a)` and the `None` sentinel. The type is honest; the writer isn't. Structural fix: the type could be `resolution.opinion: Opinion | None` (single tagged field) instead of four independent optional scalars, making the "valid-or-absent" invariant enforceable at the type boundary.
- Recommendation: collapse the four scalar fields into a single `opinion: OpinionDocument | None`.

### Principle 3 — Design checklist

#### Finding 3.1 — `sidecar/build.py` aborts the entire build when any claim has a raw-id error (CRIT — worst checklist violation)

- Severity: **crit**
- Principle clause: "Does this prevent ANY data from reaching the sidecar? → WRONG. … Does this require human action before data becomes queryable? → WRONG."
- Violation: `propstore/sidecar/build.py:75-82, 148`:
  ```python
  def _raise_on_raw_id_claim_inputs(claim_bundle: ClaimCompilationBundle) -> None:
      raw_id_errors = [
          diagnostic.message
          for diagnostic in claim_bundle.diagnostics
          if diagnostic.is_error and "raw 'id' input" in diagnostic.message
      ]
      if raw_id_errors:
          raise ValueError("\n".join(raw_id_errors))
  ```
  Called unconditionally at line 148 before any `populate_*` runs.
- Why this violates it: One bad claim file anywhere in `knowledge/claims/` prevents the sidecar being built at all. Every other valid claim, concept, context, justification, stance, source, and embedding in the tree becomes unqueryable until a human fixes the offender and re-runs build. This hits checklist items 1 (prevents data from reaching sidecar), 2 (requires human action), 3 (adds a gate before render), and 4 (filtering at build time). The principle says data should flow into storage with provenance and the render layer filters — here the build layer refuses the whole batch.
- Recommendation: record the raw-id diagnostic as a sidecar row (`build_diagnostics` table) and populate everything else. Let render policy filter claims with unresolved-id diagnostics.

#### Finding 3.2 — `compiler/passes.py` drops every `stage: draft` file from the semantic bundle (HIGH)

- Severity: **high**
- Principle clause: "Is filtering happening at build time or render time? If build → WRONG."
- Violation: `propstore/compiler/passes.py:289-307`:
  ```python
  if claim_file_stage(normalized_file) == "draft":
      file_diagnostics.append(
          SemanticDiagnostic(
              level="error",
              filename=normalized_file.filename,
              message=(
                  "draft artifacts are not accepted in the final claim validation path"
              ),
          )
      )
      diagnostics.extend(file_diagnostics)
      semantic_files.append(
          SemanticClaimFile(
              loaded_entry=original_file,
              normalized_entry=normalized_file,
              claims=tuple(),
          )
      )
      continue
  ```
  and the schema at `propstore/_resources/schemas/claim.schema.json:716` (`"description": "Optional file-level processing stage marker used to reject draft claim files from the canonical validation path"`).
- Why this violates it: draft is a render-time concern — "don't *display* drafts" is a legitimate render policy. But this code filters drafts out of the semantic bundle (the claims become an empty tuple), so the sidecar never sees them. Users asking "what drafts am I working on?" get nothing from `pks` queries. This is exactly the "gate anywhere before render time" pattern the checklist forbids.
- Recommendation: populate draft claims into the sidecar with a `stage='draft'` column; let render policy's `draft_visibility` flag choose inclusion.

#### Finding 3.3 — `promote_source_branch` requires `report.status == "ready"` before allowing promotion (MED)

- Severity: **med**
- Principle clause: "Does this require human action before data becomes queryable?"
- Violation: `propstore/source/promote.py:186-188`:
  ```python
  if report is None or report.status != "ready":
      raise ValueError(f"Source {source_name!r} must be finalized successfully before promotion")
  ```
- Why this violates it (partial): promote *is* the explicit user-migration gate, so requiring finalize-first is philosophically consistent with "explicit user migration" — but the coupling is transitive: finalize itself has hard error conditions (claim_errors / justification_errors / stance_errors in `source/finalize.py:52-77`) that force status="blocked." A source with even one broken stance reference can never be promoted, even partially. The user's *recourse* is to edit the source branch — which is fine — but the *data on the source branch is still never queryable from the primary-branch sidecar*. Principle says data flows with provenance, render filters. Here, blocked sources are invisible.
- Recommendation: allow partial promotion (promote valid claims, leave invalid ones on the source branch with a `promotion_status="blocked"` marker in the sidecar).

### Principle 4 — Proposals, not mutations

#### Finding 4.1 — Heuristic classifiers correctly target proposal families (NOTE / positive)

- Severity: **note**
- Principle clause: "Heuristic analysis layer — All output is **proposal artifacts**, never source mutations."
- Observation: grep for `transaction.save` call-sites shows heuristic modules (`classify.py`, `relate.py`, `embed.py`) do not call `transaction.save` directly; the single heuristic write path is `propstore/proposals.py:77-82` which targets `PROPOSAL_STANCE_FAMILY` on the `STANCE_PROPOSAL_BRANCH`. All `STANCE_FILE_FAMILY` writes to primary branch are from `source/promote.py:316` (user-initiated promote).

#### Finding 4.2 — `attach_source_artifact_codes` inside finalize mutates claims/stances/justifications payloads before write (LOW)

- Severity: **low**
- Principle clause: same as 4.1.
- Violation: `propstore/source/finalize.py:96-101`:
  ```python
  updated_source, updated_claims, updated_justifications, updated_stances = attach_source_artifact_codes(
      source_doc.to_payload(),
      None if claims_doc is None else claims_doc.to_payload(),
      …
  )
  ```
  This mutates the authored payloads by attaching `artifact_code` fields. Same pattern in `promote.py:230-235`.
- Why this violates it (weakly): `artifact_code` is deterministic content-addressing (not a heuristic), and it's done inside user-triggered finalize/promote. Not a heuristic bleed. The violation is cosmetic — the *authored* `SourceClaimsDocument` now has a `artifact_code` it didn't carry before, and if the user reads the file after finalize they see fields they didn't write. Log it under "mild non-commitment violation": the authored and finalized payloads have merged at the document level.

## Structural concerns (types/shapes that embed violations)

### S1 — `_DEFAULT_BASE_RATES` is a module-level constant, not a configurable provenance-bearing object

The dict at `calibrate.py:211-217` is imported transitively by the argumentation layer. Every path that calls `categorical_to_opinion(cat, pass_n)` without passing `calibration_counts` picks up these four guesses as the `a` parameter of a vacuous opinion. There is no way to replace them per-repo, no way to mark the resulting Opinion as "base rate is guess," no way for the render layer to know. This is the single highest-leverage fix in the codebase: replace the dict with a `CategoryPrior` object carrying a provenance tag.

### S2 — `SourceTrustDocument` and `SourceTrustQualityDocument` lack `status` fields

`prior_base_rate: float | int | None = None` is three-valued: absent, integer, float. None of those values means "I was defaulted to 0.5 because I had nothing." The finalize report carries `calibration.fallback_to_default_base_rate: bool` on a *separate* document — when the trust payload migrates into the argumentation layer, the report is not co-located. See Finding 2.4.

### S3 — `ResolutionDocument` has four independent optional scalar opinion fields instead of a single `Opinion | None`

`propstore/artifacts/documents/claims.py:137-168` — the four-scalar shape permits `(0.0, 0.0, 0.0, 0.5)`, which `classify.py:148-161` writes but is not a valid opinion and is not `None`. Collapsing to `opinion: OpinionDocument | None` would make the invariant enforceable at parse time.

### S4 — Build-time gating functions take a `ClaimCompilationBundle` and decide "abort everything" in one go

`_raise_on_raw_id_claim_inputs` at `sidecar/build.py:75-82` has a binary output (raise or return). There is no per-claim filter that says "this one gets a `build_status='blocked'` row, the rest proceed." The *shape* of the function embeds the principle violation — you cannot fix the behavior without changing the signature.

## Overlap with other axes

- **Axis 5 Finding 1.1, 1.2** (`praf/engine.py:155-157,252`) — axis 1 Finding 2.2 cross-references these but re-frames them as a structural return-type problem: the hook cannot distinguish "calibrated to certain" from "no data." The line-level fix of swapping `dogmatic_true()` for `vacuous()` does not solve the structural problem.
- **Axis 5 Finding 1.3** (`classify.py:148-161` writing `b=d=u=0.0`) — axis 1 Finding 2.6 / Structural S3 re-frames this as a shape problem: the 4-scalar layout of `ResolutionDocument` is what allows the violation; a `Opinion | None` shape would prevent it.
- **Axis 5 Finding 1.4** (`sidecar/claim_utils.py:596-606` mislabelling on SI failure) — not re-reported here.
- **Axis 5** (`condition_classifier.py:32-36` Z3 unknown → OVERLAP) — axis 1 frames this as an additional build-time filter: the `ConflictClass` enum is ternary-labelled (CONFLICT / PHI_NODE / OVERLAP) but has no fourth value for "unknown / solver gave up," so the unknown is silently folded into OVERLAP at build time. Structural Finding: `ConflictClass` needs a `UNKNOWN` variant, and callers need to propagate it to the render layer.
- **Axis 2** (`source/` runtime-imports `cli.repository`) — orthogonal layer-discipline concern; not re-reported.
- **Axis 2** (`aspic_bridge.py` phantom strict file) — orthogonal; not re-reported.

## Open questions

1. Is `calibrate._DEFAULT_BASE_RATES` intended to be replaced by real corpus measurement later, or is it the intended production fallback? The comment "corpus frequency priors" implies the former — if so, the fix is a calibration CLI (`pks calibrate measure-base-rates`) that writes a `CalibrationDocument` to the primary branch; the defaults become `Opinion.vacuous(a=0.5)` with `a_status="default"`.
2. Does `finalize_source_branch` need to be idempotent? Current behavior overwrites the source-branch claims file; Finding 1.3 recommends a side-label. Is there a reason to prefer in-place?
3. Is there an existing mechanism for "partial promote"? `source/promote.py` is all-or-nothing. If there's a design intent to support per-claim promotion later, Finding 3.3's recommendation is already on the roadmap.
4. Is the `_raise_on_raw_id_claim_inputs` gate there for schema safety (sidecar tables would fail foreign-key constraints on bad IDs)? If so, the fix needs a per-claim quarantine row, not removal of the check.
