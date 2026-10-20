# Relation, calibration, and extraction research checkpoint

## Current findings

- `propstore.heuristic.relate.ClaimRelationStore` has no production implementation or production caller. The only full implementation is the test fake in `tests/test_relate_perspective_isolation.py`.
- Reusable production similarity code exists under a different API: `WorldQuery.similar_claims()` delegates to `families.embeddings.declaration.world_similar_claims()`, and CLI/web similarity callers already use it.
- Stance classification has a real lazy LiteLLM call (`litellm.acompletion`) and a typed `ClassifiedStance` for one parsing helper, but the end-to-end async path returns loose stance dictionaries.
- Calibration count storage and loading exist as the derived `CalibrationCount` sidecar charter and `load_calibration_counts()`, but production relation orchestration does not load or pass counts. `CategoryPriorRegistry` exists as a type but has no production provider/caller found so far.
- Predicate and rule extraction parse typed payloads and persist proposals; predicate proposal promotion and rule proposal promotion persist canonical artifacts. Both extraction modules have `_llm_call()` stubs that always raise unless a response/fixture is injected.
- Rule extraction is production-reachable from `pks proposal propose-rules`, but without `--mock-llm-fixture` it reaches the raising stub. Predicate extraction has no production caller found yet; the predicate CLI supports manual declaration and promotion instead.

## Repository state

- Branch: `master`.
- Pre-existing untracked files are confined to `pyghidra_mcp_projects/`; they are unrelated and untouched.
- No production or test code has been modified.

## Blocker

- No technical blocker. A tool checkpoint required this notes update; the parent explicitly authorized this exact file as the sole exception to the report-only constraint.

## Next action

- Finish tracing proposal/promotion callers, calibration-count production, category-prior sources, stance proposal persistence, and tests; then write only `docs/reports/relation-calibration-extraction.md`.
