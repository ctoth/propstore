# Axis 5 — Silent Failures & Fabricated Confidence

## Summary

The system has a systemic, high-severity violation of its own "honest ignorance over fabricated confidence" principle. The most concerning category is **swallowed solver unknowns**: the Z3 wrapper (`z3_conditions.py`) collapses the three-valued solver result (sat / unsat / unknown) into two values everywhere it is called. Every downstream conflict-class decision, context-activation decision, and IC-merge validity check silently maps `unknown` to a plausible-looking Boolean outcome. A separate high-severity cluster is in `praf/engine.py` and `classify.py`, where the argumentation layer fabricates `Opinion.dogmatic_true()` or writes structurally invalid opinion fields (`b=d=u=0`) whenever calibration or classification data is missing. In total: 26 distinct findings, 7 CRIT, 9 HIGH, 7 MED, 3 LOW/NOTE.

## Findings by category

### Category 1: Fabricated defaults

#### Finding 1.1 — `p_arg_from_claim` defaults to `Opinion.dogmatic_true()` when no calibration data

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\praf\engine.py:155-157,197-199`
  ```python
          if not has_structured_fields:
              return Opinion.dogmatic_true()
  ```
  (both `ClaimRow` and `dict` branches; also unreachable line 174)
- Claim: The argumentation-layer hook that derives argument-existence probability from a claim row silently returns **maximum certainty** (b=1, d=0, u=0) whenever the claim lacks `source.trust`, `claim_probability`, `confidence`, or `source_quality_opinion`. Every unrated claim fed into the PrAF framework is thereby treated as a dogmatically true argument. This is the exact anti-pattern CLAUDE.md forbids — fabricated 1.0 where a vacuous opinion (0, 0, 1) is the correct representation of "we have no calibration evidence".
- Vacuous alternative: `return Opinion.vacuous(a=prior_base_rate or 0.5)` with a `DecisionValueSource`-style tag recording the absence of structured fields.
- Recommendation: kill the "backward compat" branch. Force callers to decide whether absent data should be vacuous or rejected.

#### Finding 1.2 — `p_relation_from_stance` defaults to `Opinion.dogmatic_true()` with comment "backward compat"

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\praf\engine.py:252-253`
  ```python
      # No opinion or confidence data — certain defeat (backward compat).
      return Opinion.dogmatic_true()
  ```
- Claim: Same problem as 1.1 for stance-derived attack edges. Every edge whose stance lacks opinion columns AND lacks a `confidence` scalar becomes maximum-strength certain defeat. The "backward compat" comment acknowledges this is a known hack.
- Vacuous alternative: `Opinion.vacuous(a=0.5)` or raise — missing edge evidence must not silently become dogmatic.

#### Finding 1.3 — classify.py stores structurally invalid opinion when stance_type == "none"

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\classify.py:148-161`
  ```python
      else:
          confidence = 0.0
          opinion = None
      ...
      "opinion_belief": opinion.b if opinion else 0.0,
      "opinion_disbelief": opinion.d if opinion else 0.0,
      "opinion_uncertainty": opinion.u if opinion else 0.0,
      "opinion_base_rate": opinion.a if opinion else 0.5,
  ```
- Claim: When the LLM classifier emits `"type": "none"` (no meaningful relationship), the stored stance has `opinion_belief = opinion_disbelief = opinion_uncertainty = 0.0`. `b + d + u = 0 ≠ 1.0`, so this triple violates `Opinion.__post_init__`. The stance persists as a dict, bypassing the constraint, then downstream `p_relation_from_stance` reads these fields, sees all three are not `None`, and calls `Opinion(0, 0, 0, 0.5)` — which will **raise** if it hits the validator, or silently carry nonsense if written to sidecar and re-read as raw columns. The correct encoding of "no meaningful relationship" is vacuous: `b=0, d=0, u=1`.
- Vacuous alternative: `opinion_belief=0.0, opinion_disbelief=0.0, opinion_uncertainty=1.0, opinion_base_rate=0.5`.
- Recommendation: mint a vacuous opinion on the "none" branch and set `confidence = opinion.expectation()`.

#### Finding 1.4 — classify.py `_build_error_pair` emits stance with zero-confidence but no vacuous marker

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\classify.py:95-119`
  ```python
      base = {
          "type": "error",
          "strength": "weak",
          "note": note,
          "conditions_differ": None,
          "resolution": {
              "method": "nli", "model": model_name,
              "embedding_model": embedding_model,
              "embedding_distance": embedding_distance,
              "confidence": 0.0,
          },
      }
  ```
- Claim: When the LLM API call fails (connection error, JSON parse failure, missing response content), this builds a stance artifact labelled `"type": "error"` with `confidence: 0.0` and no opinion fields at all. The stance is subsequently persisted as evidence; if a downstream consumer filters by `type != "error"` the artifact is dropped, but any consumer that doesn't (or that uses stance existence as an attack-edge signal) treats the failure as a meaningful low-confidence classification. There is no vacuous opinion marker, no provenance flag distinguishing "model said this" from "API failed".
- Vacuous alternative: populate opinion fields with `u=1.0`, add `resolution.source="api_failure"` so downstream reasoning can distinguish.

#### Finding 1.5 — `p_relation_from_stance` maps `confidence=0.0` to `dogmatic_false`

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\praf\engine.py:247-248`
  ```python
      if confidence <= 1e-12:
          return Opinion.dogmatic_false(a)
  ```
- Claim: Combined with 1.4: any stance produced by `_build_error_pair` (API failure) has `confidence=0.0`, which `p_relation_from_stance` maps to `Opinion.dogmatic_false()` — maximum certainty that the relation does **not** exist. The absence of the classifier's output is thereby fabricated into a strong negative claim. This is the composition from classifier-failure to argumentation layer, and it produces the opposite of ignorance.
- Vacuous alternative: special-case the error branch upstream, or treat `confidence == 0` only as probability zero (→ `from_probability(0, n)`) when `n > 0`, otherwise vacuous.

#### Finding 1.6 — `metadata_strength_vector` invents 0.5 confidence and 1.0 inverse-uncertainty

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\preference.py:94-98`
  ```python
      return [
          math.log1p(sample_size) if sample_size and sample_size > 0 else 0.0,
          1.0 / uncertainty if uncertainty and uncertainty > 0 else 1.0,
          confidence if confidence is not None else 0.5,
      ]
  ```
- Claim: When a claim has no `confidence` metadata, the strength vector used for ASPIC+ preference ordering falls back to `0.5` (fabricated middle confidence) and when uncertainty is missing / zero it uses `1.0` (fabricated low uncertainty). These vectors determine which claims defeat which in the argumentation layer. Every unrated claim competes at a fabricated middle score.
- Vacuous alternative: return a sentinel (e.g. `None` in that slot) and teach the comparator to treat missing-vs-present incomparably; or use `math.nan` and a strict-comparison preference rule.

#### Finding 1.7 — relate.py fabricates `distance=1.0` when candidate missing `distance`

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\relate.py:211`
  ```python
          pairs.append((claim_a, claim_b, c.get("distance", 1.0)))
  ```
- Claim: `find_similar` is expected to always return `distance`, but `.get(..., 1.0)` silently substitutes a maximum-dissimilarity distance on any shape deviation. That value then enters `reference_distances` for `CorpusCalibrator`, biasing the CDF.
- Vacuous alternative: raise KeyError; a missing `distance` key indicates upstream schema drift and should not be smoothed over.

#### Finding 1.8 — `enforce_coh` invents `evidence_n=10.0` for dogmatic opinions

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\praf\engine.py:286-289`
  ```python
          if op.u > 1e-9:
              evidence_n[arg] = W * (1.0 / op.u - 1.0)
          else:
              evidence_n[arg] = 10.0  # default for dogmatic opinions
  ```
- Claim: When a dogmatic opinion needs to be rescaled for COH, the "evidence count" is made up as 10.0 — an arbitrary integer with no provenance. Every rebuilt opinion uses this fabricated n to invert `from_probability`, then writes the resulting Opinion back into the PrAF with no marker that n was fabricated.
- Vacuous alternative: if `op.u ≈ 0`, you cannot legitimately rescale its expectation without inventing evidence — either refuse to rescale (keep original) or explicitly carry a `fabricated_n` flag through the record.

### Category 2: Swallowed solver unknowns

This is the single most dangerous category. The Z3 wrapper treats `solver.check()` as a two-valued predicate, silently collapsing `z3.unknown` (timeout, incomplete theory, stuck on nonlinear arithmetic, etc.) into a False answer on one side.

#### Finding 2.1 — `Z3ConditionSolver.is_condition_satisfied` maps unknown to unsatisfiable

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\z3_conditions.py:442-444`
  ```python
          for name, value in bindings.items():
              solver.add(self._binding_to_z3(name, value))
          return solver.check() == z3.sat
  ```
- Claim: Returns False whenever Z3 returns `unknown`. Callers (activation, IC merge CEL evaluator, world value resolver) treat False as "condition violated / inactive / invalid". Silent fabrication.
- Vacuous alternative: raise `Z3UnknownError`, or return a tri-valued result (`Satisfied | Unsatisfied | Unknown`) and force callers to handle the unknown branch explicitly.

#### Finding 2.2 — `Z3ConditionSolver.are_disjoint` maps unknown to "not disjoint"

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\z3_conditions.py:459-463`
  ```python
          solver.add(expr_a)
          solver.add(expr_b)
          self._add_temporal_constraints(solver)
          return solver.check() == z3.unsat
  ```
- Claim: Unknown → False. Semantically becomes "these condition sets **overlap**". Downstream conflict detection records a CONFLICT/OVERLAP warning class instead of correctly marking the pair as "undecidable conflict under current solver capabilities".
- Vacuous alternative: tri-valued return.

#### Finding 2.3 — `Z3ConditionSolver.are_equivalent` maps unknown to "not equivalent"

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\z3_conditions.py:481,489`
  ```python
          if s1.check() != z3.unsat:
              return False
          ...
          return s2.check() == z3.unsat
  ```
- Claim: Either side returning unknown collapses to False.

#### Finding 2.4 — `classify_conditions` silently maps unknown to ConflictClass.OVERLAP

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\condition_classifier.py:32-36`
  ```python
      if solver.are_equivalent(conditions_a, conditions_b):
          return ConflictClass.CONFLICT
      if solver.are_disjoint(conditions_a, conditions_b):
          return ConflictClass.PHI_NODE
      return ConflictClass.OVERLAP
  ```
- Claim: Composes 2.2 and 2.3 into a fabricated conflict class. When Z3 is unsure, the classifier asserts "conditions OVERLAP" — a positive claim about logical relationships — rather than admitting "undecidable". This is a direct violation of the honest-ignorance principle at the core of the conflict-detection layer.
- Vacuous alternative: add `ConflictClass.UNDECIDABLE` and return it when either Z3 call reports unknown.

#### Finding 2.5 — cross-class parameter conflict detection inherits the same silent mapping

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\conflict_detector\parameter_claims.py:208-213`
  ```python
              try:
                  cross_class = (
                      ConflictClass.PHI_NODE
                      if z3_solver.are_disjoint(rep_i, rep_j)
                      else ConflictClass.OVERLAP
                  )
  ```
- Claim: Unknown → are_disjoint False → OVERLAP. Silently fabricates an overlap classification between equivalence-class representatives.

#### Finding 2.6 — is_claim_node_active defaults to ACTIVE on unknown

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\core\activation.py:146-147,182-183`
  ```python
      try:
          return not solver.are_disjoint(binding_conditions, claim_conditions)
      except Z3TranslationError:
          ...
  ```
- Claim: `are_disjoint` unknown → False → `not False` = True. The claim is considered **active** in the environment. This flips the direction of error depending on which check is called — activation is biased toward "keep the claim" on unknown, while conflict detection is biased toward "flag a conflict" on unknown. Either direction is fabrication, and the inconsistency between them is worse.

#### Finding 2.7 — IC merge CEL constraint silently rejects candidates on Z3 unknown

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\ic_merge.py:170-181,194-196`
  ```python
      def _eval_cel_constraint_z3(...)
      ...
          return solver.is_condition_satisfied(checked, bindings)
  ```
- Claim: `is_condition_satisfied` unknown → False → merge candidate silently excluded as violating constraint. Candidate that *might* satisfy the constraint never reaches the solver.winners set.

#### Finding 2.8 — Dung Z3 extension enumeration silently terminates on unknown

- Severity: **med-high**
- Evidence: `C:\Users\Q\code\propstore\propstore\dung_z3.py:151,197`
  ```python
      while solver.check() == sat:
  ```
- Claim: Unknown terminates the `while` loop exactly like unsat, and the caller receives what looks like a complete list of extensions. For stable / complete / preferred extension enumeration, a silently-truncated list changes which arguments appear acceptable.
- Vacuous alternative: check `result` explicitly; on unknown, raise or attach a partial-result flag to the return.

### Category 3: Exception swallowing

#### Finding 3.1 — sidecar claim SI normalization silently writes unnormalized values to `value_si`

- Severity: **crit**
- Evidence: `C:\Users\Q\code\propstore\propstore\sidecar\claim_utils.py:596-606`
  ```python
      if form_def is not None:
          try:
              if value_si is not None:
                  value_si = normalize_to_si(float(value_si), unit, form_def)
              ...
          except (ValueError, TypeError):
              value_si = typed_fields.value
              lower_bound_si = typed_fields.lower_bound
              upper_bound_si = typed_fields.upper_bound
  ```
- Claim: The sidecar has columns explicitly named `value_si`, `lower_bound_si`, `upper_bound_si`. When unit conversion fails (ValueError from `form_utils.to_si` — raised on `UndefinedUnitError` or `DimensionalityError`), the code silently falls back to writing the **unnormalized** values into the `_si` columns. Downstream world queries, conflict detection, and IC merge all trust the `_si` suffix to mean SI units. Every query against this claim will compare non-SI numbers as if they were SI. No warning is logged.
- Vacuous alternative: leave the `_si` columns NULL and record the normalization failure in a separate status column or log; refuse to commit a claim whose unit cannot be validated.

#### Finding 3.2 — sidecar build swallows embedding restore failure and marks success

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\sidecar\build.py:230-242`
  ```python
          if embedding_snapshot is not None:
              try:
                  ...
                  restore_embeddings(conn, embedding_snapshot)
                  conn.row_factory = None
              except (ImportError, Exception) as exc:
                  import sys
                  print(f"Warning: embedding restore failed: {exc}", file=sys.stderr)
                  conn.row_factory = None
  ```
- Claim: `except (ImportError, Exception)` is semantically `except Exception`; all failures during embedding restore are caught, a stderr warning is printed, and then `conn.commit()` runs as if the build succeeded. The sidecar is content-hash addressed (CLAUDE.md: "rebuilt only when source changes"), so the caller caches this hash and will not re-attempt. Future similarity queries silently see missing vectors.
- Vacuous alternative: let the exception escape; sidecar should not be marked complete if embedding restore failed. At minimum, record the failure in a persistent `build_metadata` row so queries can tell.

#### Finding 3.3 — `evaluate_parameterization` returns None for 4+ distinct failure modes

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\propagation.py:82-113`
  ```python
      try:
          from sympy import Equality, Symbol, solve
      except ImportError:
          return None
      ...
      try:
          ...
          if solutions:
              return float(solutions[0])
          return None
      except (TypeError, ValueError, ZeroDivisionError, AttributeError):
          return None
  ```
- Claim: None means "sympy missing" OR "no solution found" OR "substitution type error" OR "division by zero". Callers cannot distinguish.
- Vacuous alternative: raise distinct exception types or return a discriminated union (`Derived(x)`, `NoSolution`, `SympyMissing`, `EvaluationError(exc)`).

#### Finding 3.4 — `derive_scored_concepts` bare-Exception catch conflates empty-vs-failed

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:82-99`
  ```python
      try:
          concepts: set[str] = { ... }
          ...
          return sorted(concepts)
      except Exception as exc:
          warnings.warn(...)
          return []
  ```
- Claim: On any failure (store lookup exception, coercion error, etc.) the function returns an empty list with a warning. Downstream fragility scoring then silently reports "no concepts to score". Callers should not treat this identically to "store has zero concepts".
- Vacuous alternative: raise; let the caller decide whether to degrade to empty.

#### Finding 3.5 — ATMS concept stability failures silently dropped

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:121-129`, `C:\Users\Q\code\propstore\propstore\fragility_scoring.py:200-204`
  ```python
          try:
              stability = engine.concept_stability(concept_id, queryables, limit=atms_limit)
          except Exception as exc:
              warnings.warn(...)
              continue
  ```
- Claim: A concept whose stability computation raises is silently skipped from the aggregation. The resulting `contributions` map pretends the skipped concept had zero witnesses — which in turn drives `weighted_epistemic_score` toward 0 for any intervention that only touched that concept.

#### Finding 3.6 — `verify_form_algebra_dimensions` returns False on ImportError

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\form_utils.py:335-336`
  ```python
      except (KeyError, ValueError, ImportError):
          return False
  ```
- Claim: If `bridgman` is not installed, the function returns False — semantically "dimensionally inconsistent". Callers that reject forms on `not verify_form_algebra_dimensions(...)` will ban valid form algebra purely because of a missing dependency. ImportError is not a dimensional outcome.
- Vacuous alternative: split the import error into a separate exception; callers decide.

#### Finding 3.7 — ATMS `_exact_antecedent_sets` returns [] on JSON decode failure

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\atms.py:1392-1395`
  ```python
          try:
              conditions = json.loads(conditions_cel)
          except (TypeError, json.JSONDecodeError):
              return []
  ```
- Claim: Malformed `conditions_cel` is indistinguishable from "no conditions at all". The ATMS belief base then reasons as if the node had no antecedent constraints, which changes the supported / blocked status of downstream environments.

#### Finding 3.8 — `_collect_known_values` silently drops non-numeric concept values

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\value_resolver.py:102-112`
  ```python
      for cid in variable_concepts:
          ...
          try:
              known[normalized_cid] = float(val)
          except (TypeError, ValueError):
              pass
      return known
  ```
- Claim: Concepts whose current determined value is non-numeric are silently absent from the `known` dict. Downstream parameterization evaluation sees them as "unknown" and cannot evaluate the expression. No diagnostic logged.

#### Finding 3.9 — `_algorithm_matches_direct_value` asserts equivalent=False when body missing

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\value_resolver.py:520-526`
  ```python
                  body_a = normalized_claims[i].body or ""
                  body_b = normalized_claims[j].body or ""
                  if not body_a or not body_b:
                      # Benign: cannot compare without bodies. Not a parse
                      # failure — mirror previous behavior of signalling
                      # non-equivalence to the caller.
                      return _AlgorithmComparison(equivalent=False)
  ```
- Claim: "Cannot compare" is coerced into "not equivalent" — a positive claim of inequality. The comment acknowledges the confusion ("benign: cannot compare") but still returns the false signal.
- Vacuous alternative: return `_BENIGN_INCONCLUSIVE` like the sibling cases.

#### Finding 3.10 — Opinion fuse(method="auto") silently falls back WBF→CCF

- Severity: **low**
- Evidence: `C:\Users\Q\code\propstore\propstore\opinion.py:438-442`
  ```python
      elif method == "auto":
          try:
              return wbf(*opinions)
          except ValueError:
              return ccf(*opinions)
  ```
- Claim: Documented behavior, but the caller has no way to tell which method produced the fused opinion. Result carries no provenance flag. Low severity because it's documented and both methods are principled.

#### Finding 3.11 — `categorical_to_opinion` does the right thing (GOOD — no finding, listed for contrast)

- Severity: **note**
- Evidence: `C:\Users\Q\code\propstore\propstore\calibrate.py:280-289`
- Claim: This module is the model. When calibration counts are absent it returns `Opinion.vacuous(a=base_rate)` with explicit literature citations. The praf and classify modules should adopt this pattern.

### Category 4: Heuristic output missing provenance

#### Finding 4.1 — classify.py stance has no `source` or `calibration` marker on opinion fields

- Severity: **high**
- Evidence: `C:\Users\Q\code\propstore\propstore\classify.py:152-162`
- Claim: The persisted `resolution` dict records `method`, `model`, `embedding_model`, `embedding_distance`, `confidence`, and opinion-quadruple fields — but no flag distinguishing "LLM-derived uncalibrated" from "LLM + corpus-CDF calibrated" from "LLM + external validation counts". When `reference_distances` and `calibration_counts` are both available, the resulting opinion is a `fuse()` of two opinions with different provenance; only the model-name and embedding-model survive. Downstream consumers cannot tell whether a given opinion carries empirical evidence counts, calibrated CDF probability, or an uncalibrated default-base-rate vacuous.
- Vacuous alternative: explicit `resolution.opinion_source = "fused(categorical, corpus_cdf)"` or similar structured provenance tag.

#### Finding 4.2 — `reference_distances` accepts fabricated 1.0 default without flag

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\relate.py:211,223`
- Claim: See 1.7. Any pair whose distance defaulted to 1.0 enters the corpus CDF without a marker; percentile ranks for genuine distances are pulled toward higher percentiles.

### Category 5: Bool coercion losing uncertainty

#### Finding 5.1 — `is_claim_node_active` / `is_active_claim_active` coerce Z3-unknown via `not are_disjoint`

- Severity: **high** (same as 2.6; listed here for the bool-coercion framing)
- Evidence: `C:\Users\Q\code\propstore\propstore\core\activation.py:147,183`
- Claim: The Boolean inversion `not are_disjoint(...)` composes with the Z3 unknown-to-False mapping to yield True on unknown. The function's return type is `bool`, so any uncertainty is discarded — the argumentation layer has no channel to observe the solver's ignorance.
- Vacuous alternative: return a tri-valued enum or propagate an `UnknownActivation` exception.

#### Finding 5.2 — `_AlgorithmComparison(equivalent=bool(result.equivalent))` drops nuance

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\value_resolver.py:507`
- Claim: `ast_compare` may return an object whose `.equivalent` is a tri-valued or optional field. `bool(...)` coerces None / sentinel values to False, which the caller reads as "not equivalent". Need to cross-check the ast_compare return shape (not in scope for this pass).
- Vacuous alternative: explicit `if result.equivalent is None: return _BENIGN_INCONCLUSIVE`.

#### Finding 5.3 — `_in_extension` returns True on any coercion failure

- Severity: **med**
- Evidence: `C:\Users\Q\code\propstore\propstore\fragility_contributors.py:51-60`
  ```python
  def _in_extension(current_status: object) -> bool:
      try:
          normalized = ValueStatus(str(current_status))
      except Exception:
          return True
      return normalized in { ValueStatus.DETERMINED, ... }
  ```
- Claim: An unrecognized status string silently becomes True — "in the extension". The default biases fragility scoring away from flagging interventions as potentially fragile.

### Category 6: None-means-too-many-things

#### Finding 6.1 — `propagation.evaluate_parameterization` returns None for 4 distinct causes

- Severity: **med** (duplicate of 3.3; listed here for the None-overloading framing)
- Evidence: `C:\Users\Q\code\propstore\propstore\propagation.py:84-113`

#### Finding 6.2 — `_override_value` collapses "not in overrides" and "unparseable" into None

- Severity: **low-med**
- Evidence: `C:\Users\Q\code\propstore\propstore\world\value_resolver.py:450-461`
  ```python
      if not override_values or override_key not in override_values:
          return None
      override_value = override_values[override_key]
      if override_value is None:
          return None
      try:
          return float(override_value)
      except (TypeError, ValueError):
          return None
  ```
- Claim: Caller cannot tell whether the user did not override (`key absent`) or tried to override with unparseable data (`float() raised`). The semantics diverge: "not overridden" should fall back to stored value; "bad override" should error.

#### Finding 6.3 — `_get_claim_text` returns None for both "missing claim" and zero-row queries

- Severity: **low**
- Evidence: `C:\Users\Q\code\propstore\propstore\relate.py:27-42`
- Claim: Low severity because the caller only needs to skip missing claims, but the function signature conceals the reason.

## Hot-zones map

Findings per file (ordered by severity-weighted count):

| File | CRIT | HIGH | MED | LOW | total |
|------|------|------|-----|-----|-------|
| `propstore/praf/engine.py` | 2 | 2 | 0 | 0 | 4 |
| `propstore/z3_conditions.py` | 2 | 1 | 0 | 0 | 3 |
| `propstore/classify.py` | 1 | 1 | 0 | 0 | 2 |
| `propstore/conflict_detector/parameter_claims.py` | 1 | 0 | 0 | 0 | 1 |
| `propstore/condition_classifier.py` | 1 | 0 | 0 | 0 | 1 |
| `propstore/sidecar/claim_utils.py` | 1 | 0 | 0 | 0 | 1 |
| `propstore/core/activation.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/sidecar/build.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/world/ic_merge.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/world/atms.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/form_utils.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/dung_z3.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/preference.py` | 0 | 1 | 0 | 0 | 1 |
| `propstore/relate.py` | 0 | 0 | 2 | 1 | 3 |
| `propstore/fragility_contributors.py` | 0 | 0 | 3 | 0 | 3 |
| `propstore/world/value_resolver.py` | 0 | 0 | 3 | 0 | 3 |
| `propstore/propagation.py` | 0 | 0 | 1 | 0 | 1 |
| `propstore/fragility_scoring.py` | 0 | 0 | 1 | 0 | 1 |
| `propstore/opinion.py` | 0 | 0 | 0 | 1 | 1 |

## Most dangerous single site

**`propstore/condition_classifier.py:32-36`** — `classify_conditions` composes three Z3 silent-unknown mappings (`are_equivalent → False`, `are_disjoint → False`, fall-through) to produce a fabricated `ConflictClass.OVERLAP` from "we cannot decide". This is the entry point used by `detect_conflicts`, which in turn drives `repo/merge_classifier.py`, `conflict_detector/parameter_claims.py`, and every downstream argumentation step. Every Z3 timeout in the system becomes a fabricated "OVERLAP" conflict classification. The CLAUDE.md design checklist item "Does this add a gate anywhere before render time?" is violated exactly here: the classification is hardened into a persistable conflict record without any `unknown` tag.

## Open questions

1. **Tri-valued Z3 wrapper redesign impact.** Fixing Category 2 at the root (making `Z3ConditionSolver.are_disjoint` etc. return `Sat | Unsat | Unknown`) will ripple through activation, conflict detection, IC merge, and Dung enumeration. I did not trace the full blast radius; Axis 1 (architecture) should confirm whether `ConflictClass` has space for an UNDECIDABLE variant.
2. **classify.py "none" stance invariant violation.** I did not confirm whether `p_relation_from_stance` actually gets called with `b=d=u=0.0` stance rows in practice, or whether a validator elsewhere catches it first. Worth a runtime test: build a sidecar from a corpus that includes at least one "none" classification, then run `pks world query` with argumentation enabled and watch for Opinion validator exceptions.
3. **Unverified: ast_compare return shape.** Finding 5.2 assumes `result.equivalent` can be None. I did not open the algorithm comparison module to verify; if it's always bool, 5.2 drops to NOTE.
4. **embedding dimension discovery silent failure.** `embed.py:252-258` unconditionally trusts the first-successful-batch's `len(response.data[0]["embedding"])` as the model's dimension and INSERT OR REPLACEs the embedding_model row. If a model returns inconsistent dimensions across batches (rare but possible with some LLM routers), later rows would be silently rejected by the vec table. Did not fully trace.
5. **source/alignment.py token_overlap(empty, empty) = 1.0.** I left this as low-priority but it could matter if alignment heuristics use token_overlap as a gate for "are these concepts the same?". Two concepts with empty/missing definitions would be flagged as identical.
6. **Grounding layer is clean in this sweep.** I did not find silent failures in `propstore/grounding/`, but I did not check the full module exhaustively — worth a second pass.
7. **CEL checker error modes.** `cel_checker.py:434,469` catch ValueError; did not trace whether the caller downstream trusts the return when the check failed.
