# WS-O-gun-garcia closure

Closed: 2026-04-29

Closing commits:
- gunray: `64c4f3d340e0ac54651a9e5dd94bdf4df3d6cb7e`
- propstore implementation: `7caf63a0eef4c65ad5dbd119e15c898bdd7edc8d`

## Findings closed

- Cluster-R MED-4: removed the production `not_defeasibly` section contract. Propstore consumes Garcia `yes/no/undecided/unknown`; production grep over `propstore/` plus `../gunray/src` has zero `not_defeasibly` hits.
- Cluster-B D4/M2: propstore rule documents now distinguish `proper_defeater` and `blocking_defeater`; gunray exposes public defeat classification through `classify_defeat` and `DialecticalNode.defeater_kind`.
- Cluster-B M3: propstore rule bodies now use `BodyLiteralDocument` so Garcia default negation is represented separately from strong negation.
- Cluster-B M4: gunray includes the Garcia 2004 Section 6.3 presumption-specific specificity behavior; propstore pins the pushed gunray commit.
- KLM/property coverage: the upstream gunray run includes the existing Hypothesis/property modules for specificity, dialectic, closure faithfulness, parser, and tree behavior; propstore includes the grounding and bridge property tests in the targeted and full runs.
- Documentation seal: gunray `ARCHITECTURE.md`, `CITATIONS.md`, and `notes/b2_defeater_participation.md` record the Garcia section shape and supersession of the old defeater-touches reading. Propstore `docs/gaps.md` records this closure.

## TDD evidence

Tests were written and run before the corresponding production migrations:

- Propstore rule schema red: `logs/test-runs/WS-O-propstore-rule-kind-red-20260429-153248.log` failed because `BodyLiteralDocument` did not exist / the old schema shape was still active.
- Propstore rule schema green: `logs/test-runs/WS-O-propstore-rule-kind-green-20260429-153548.log` passed 5 tests after the schema widening.
- Propstore bridge/conformance red: `logs/test-runs/WS-O-propstore-bridge-conformance-second-20260429-155849.log` failed 5 evaluator/API expectations while callers still assumed the old policy/section surface.
- Propstore bridge/conformance green: `logs/test-runs/WS-O-propstore-bridge-conformance-noxdist-20260429-161002.log` passed 110 tests after migrating the bridge and conformance resources.
- Full-suite residue red: `logs/test-runs/WS-O-full-20260429-162449.log` failed 6 stale expectations: demo CLI section names, contract manifest versioning, and an import fixture with the old rule-body shape.
- Full-suite residue green: `logs/test-runs/WS-O-full-failure-fixes-20260429-163036.log` passed 31 tests after those residues were fixed.

Scope honesty: the initial WS text named separate gunray files such as `tests/test_garcia_section_3_4.py`. Upstream implementation consolidated those checks into existing canonical modules plus `tests/test_workstream_o_gun_garcia_done.py`, rather than creating wrapper files. The coverage is real, but the filenames differ.

## Logged gates

- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-final-targeted -n 0 ...` -> 219 passed; log `logs/test-runs/WS-O-final-targeted-20260429-162340.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-full-final` -> 3363 passed, 2 skipped; log `logs/test-runs/WS-O-full-final-20260429-163216.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-docstring-hygiene -n 0 tests/test_grounding_grounder.py tests/test_aspic_bridge_grounded.py tests/test_sidecar_grounded_facts.py` -> 47 passed; log `logs/test-runs/WS-O-docstring-hygiene-20260429-163813.log`.
- `uv run pyright propstore` -> 0 errors.
- `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py` -> dependency order OK.

Upstream gunray gates were run in `../gunray` without the propstore logged wrapper:

- `uv run pyright src/gunray` -> 0 errors.
- `uv run ruff check` -> passed.
- `uv run ruff format --check` -> passed after formatting the sentinel.
- `uv run pytest tests/test_workstream_o_gun_garcia_done.py tests/test_specificity.py tests/test_superiority.py tests/test_dialectic.py tests/test_defeasible_evaluator.py tests/test_presumptions.py tests/test_explain.py tests/test_conformance.py tests/test_closure_faithfulness.py tests/test_closure.py` -> 74 passed, 293 skipped, 2 deselected.
- `uv run pytest tests` -> 239 passed, 293 skipped, 2 deselected.

## Files changed

Propstore:
- `pyproject.toml`, `uv.lock`
- `propstore/families/documents/rules.py`
- `propstore/grounding/*`, `propstore/aspic_bridge/*`, `propstore/defeasible_conformance.py`, `propstore/contracts.py`
- `propstore/contract_manifests/semantic-contracts.yaml`
- `tests/test_propstore_rule_kind_widened.py`, grounding/bridge/conformance tests and resources
- `docs/gaps.md`

Gunray:
- Garcia section/runtime/policy/test changes through pushed commit `64c4f3d340e0ac54651a9e5dd94bdf4df3d6cb7e`
- `ARCHITECTURE.md`, `CITATIONS.md`, `notes/b2_defeater_participation.md`
- `tests/test_workstream_o_gun_garcia_done.py`

## Remaining risks

- `../gunray/notes/gaps.md` does not exist, so there was no gunray gaps file to update.
- Gunray still uses `kind="defeater"` internally for runtime defeater rules; the WS explicitly scoped that as still valid. Propstore persistence no longer accepts the collapsed `RuleDocument.kind == "defeater"` surface.
- Historical conformance-suite translators in gunray tests still name upstream legacy sections when translating external reference data. Production code and propstore code no longer use those field names.
