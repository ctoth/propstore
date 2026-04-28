# WS-O-arg-dung-extensions Closure Report

Closed in propstore commit `00076004` after the Coste-Marquis prudent-semantics correction.

## Upstream argumentation

- `c267c2b` recorded the Step 0 source/paper inventory in `../argumentation/notes/WS-O-arg-dung-extensions.md`.
- `c941fe4` implemented operational Caminada labellings, semi-stable/eager/stage2/prudent Dung surfaces, Cayrol bipolar grounded/complete surfaces, and deleted `argumentation.dung_z3`.
- `c69bf76` added Coste-Marquis et al. 2005 pp. 1-3 prudent-semantics regressions after the missing local paper was processed.
- `98a7325` corrected prudent indirect attacks to odd-length directed paths and implemented grounded prudent semantics by iterating `F^p_AF` from the empty set.
- Upstream verification:
  - `uv run pytest tests/test_dung_extensions_workstream.py -q` => `11 passed in 0.82s`.
  - `uv run pyright src/argumentation` => `0 errors`.
  - `uv run pytest -q -k "not test_firm_strict_in_every_complete"` => `409 passed, 1 deselected in 94.76s`.
  - Full `uv run pytest -q` was interrupted twice after stalling in the ASPIC Hypothesis area; `uv run pytest tests/test_aspic.py::TestRationalityPostulates::test_firm_strict_in_every_complete -vv` passed in isolation.
- Upstream pushed: `9887559..98a7325 main -> main`.

## Propstore

- Pinned `formal-argumentation` to `98a7325f4e599a33740c0ee61495ce3222c6e992`.
- Added `tests/architecture/test_argumentation_pin_dung_extensions.py` as the propstore-side behavior sentinel.
- Updated the propstore sentinel to prove Coste-Marquis et al. 2005 pp. 1-3: indirect attacks are odd-length paths, AF1 excludes `{a,i,n}`, and preferred/grounded prudent extension is `{i,n}`.
- Updated the old ideal-extension sentinel to the new deletion-first Dung API with no backend selector.
- Targeted logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-dung-extensions-target tests/architecture/test_argumentation_pin_dung_extensions.py tests/architecture/test_argumentation_pin_ideal_admissibility.py tests/architecture/test_argumentation_pin_aba_adf.py`
  - Result: `9 passed in 3.35s`.
  - Log: `logs/test-runs/ws-o-arg-dung-extensions-target-20260428-145620.log`.
- Corrective targeted logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label prudent-semantics-repin tests/architecture/test_argumentation_pin_dung_extensions.py`
  - Result: `6 passed in 4.40s`.
  - Log: `logs/test-runs/prudent-semantics-repin-20260428-165704.log`.
- Package type gate:
  - `uv run pyright propstore`
  - Result: `0 errors`.
- Full logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-dung-extensions-full-final`
  - Result: `3205 passed in 128.98s`.
  - Log: `logs/test-runs/ws-o-arg-dung-extensions-full-final-20260428-150020.log`.
- Corrective full logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label prudent-semantics-correction-full`
  - Result: `3206 passed in 137.00s`.
  - Log: `logs/test-runs/prudent-semantics-correction-full-20260428-165953.log`.
- Checklist order gate:
  - `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py`
  - Result: `INDEX.md dependency order OK (31 rows checked).`

## Issues surfaced

- The first upstream labelling implementation enumerated all three-valued labellings and made the full suite effectively hang. It was replaced with candidate-IN-set enumeration plus an acyclic grounded fast path before closure.
- The initial prudent implementation used the missing paper indirectly and encoded even-length paths plus a grounded-as-first-complete shortcut. After `papers/Coste-Marquis_2005_PrudentSemantics/notes.md` was created, this was corrected with paper-cited tests from Coste-Marquis et al. 2005 pp. 1-3.
- The upstream full suite currently has an unrelated full-order verification issue: `test_firm_strict_in_every_complete` passes alone but the full suite stalls in the ASPIC Hypothesis region. The prudent target suite, pyright, and full suite with only that property deselected passed.
