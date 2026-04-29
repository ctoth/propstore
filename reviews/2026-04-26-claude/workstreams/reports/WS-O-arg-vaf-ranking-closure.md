# WS-O-arg-vaf-ranking Closure Report

Closed in propstore commit `418d409c` after the final argumentation pin to upstream commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908`.

## Upstream argumentation

- `afe2a5b` renamed Wallner ASPIC subjective filtering from `value_based.py` to `subjective_aspic.py` without a compatibility alias.
- `d569a8e` implemented the Bench-Capon value-based argumentation framework surface: VAF construction, audience-specific defeat, preferred extensions, objective acceptance, and subjective acceptance.
- `3781037` implemented the Atkinson practical-reasoning AATS slice: AS1 plus CQ5, CQ6, and CQ11. The remaining Atkinson CQs hard-fail as out of scope.
- `340a5f9` replaced ranking non-convergence exceptions with the typed `RankingResult` contract and added discussion-based, counting, tuples, h-categoriser, and iterated-graded ranking semantics alongside categoriser and burden.
- `c20f129` completed the ranking axiom surface after the first implementation was found incomplete during closure review. The final surface includes all 11 Amgoud 2013 predicates plus strict-preference transitivity.
- Upstream verification:
  - Focused gate: `uv run pytest tests\test_subjective_aspic.py tests\test_vaf.py tests\test_practical_reasoning.py tests\test_ranking.py tests\test_ranking_axioms.py tests\test_docs_surface.py tests\test_workstream_o_arg_vaf_ranking_done.py` => `41 passed in 1.03s`.
  - Type gate: `uv run pyright src\argumentation` => `0 errors`.
  - Full suite: `uv run pytest --timeout=120 *>&1 | Tee-Object -FilePath logs\post-ws-o-arg-vaf-ranking-axioms.log` => `439 passed in 27.85s`.
- Upstream pushed: `main -> main` through `c20f129`.

## Propstore

- `e6b047d9` first pinned `formal-argumentation` for the VAF/ranking workstream.
- `13511153` removed the stale SHA-only Dung sentinel that blocked the new pin but did not prove behavior.
- `418d409c` pinned `formal-argumentation` to pushed upstream commit `c20f12939ccac558f8467d31c67d6cc1aa9e7908` and tightened `tests/architecture/test_argumentation_pin_vaf_ranking.py` to prove:
  - Bench-Capon Figure 2 objective/subjective VAF acceptance.
  - Typed `RankingResult` non-convergence.
  - All seven ranking semantics are exposed.
  - The complete axiom predicate surface is importable and callable.
  - Atkinson CQ11 objection generation works through the pinned package.
- Targeted logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label arg-vaf-ranking-pin-axioms tests/architecture/test_argumentation_pin_vaf_ranking.py`
  - Result: `4 passed in 2.86s`.
  - Log: `logs/test-runs/arg-vaf-ranking-pin-axioms-20260428-182753.log`.
- Package type gate:
  - `uv run pyright propstore`
  - Result: `0 errors`.
- Full logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label arg-vaf-ranking-full-final-n0 -n 0`
  - Result: `3210 passed in 473.44s`.
  - Log: `logs/test-runs/arg-vaf-ranking-full-final-n0-20260428-183556.log`.

## Property gates

- Bench-Capon Def. 5.3 is covered by a Hypothesis property in upstream `tests/test_vaf.py`: an attack succeeds exactly when the attacked value is not preferred to the attacker's value for the audience.
- Atkinson CQ11 is covered by a generated alternative-action property in upstream `tests/test_practical_reasoning.py`: different promoted values produce CQ11 objections.
- Ranking results are covered by upstream generated order properties in `tests/test_ranking.py`: ranking outputs induce reflexive/transitive comparison behavior.
- Propstore's sentinel exercises the complete public surface under the final pin.

## Issues surfaced

- The first upstream axiom implementation shipped only a partial axiom surface. Closure review caught this before closing the workstream; upstream `c20f129` added the missing predicates and propstore `418d409c` pinned and proved them.
- The old propstore Dung pin sentinel asserted a literal SHA. It failed on the new pin while proving no behavior. `13511153` removed that brittle test.
- The xdist full propstore run crashed one worker at the tail on `tests/test_aspic_bridge.py::TestBridgeRationalityPostulates::test_firm_strict_in_every_complete`. The same test passed in isolation, and the final non-xdist full suite passed.
- The post-compaction paper-image reread found additional Bench-Capon surfaces not implemented by this workstream: argument chains, line-of-argument parity classifications, and fact-as-highest-value uncertainty handling. Those are recorded as open follow-up gaps, not claimed as closed here.
- The Oikarinen initial-image reread reaffirmed that strong/local equivalence kernels remain absent. That gap was already open in `docs/gaps.md`.
