# WS-O-arg-dung-extensions Closure Report

Closed in propstore commit `04281337`.

## Upstream argumentation

- `c267c2b` recorded the Step 0 source/paper inventory in `../argumentation/notes/WS-O-arg-dung-extensions.md`.
- `c941fe4` implemented operational Caminada labellings, semi-stable/eager/stage2/prudent Dung surfaces, Cayrol bipolar grounded/complete surfaces, and deleted `argumentation.dung_z3`.
- Upstream verification:
  - `uv run pytest -q` => `409 passed in 97.16s`.
  - `uv run pyright src/argumentation` => `0 errors`.
- Upstream pushed: `9887559..c941fe4 main -> main`.

## Propstore

- Pinned `formal-argumentation` to `c941fe4e3b795406003b64090529c9b2d7fc037b`.
- Added `tests/architecture/test_argumentation_pin_dung_extensions.py` as the propstore-side behavior sentinel.
- Updated the old ideal-extension sentinel to the new deletion-first Dung API with no backend selector.
- Targeted logged gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-dung-extensions-target tests/architecture/test_argumentation_pin_dung_extensions.py tests/architecture/test_argumentation_pin_ideal_admissibility.py tests/architecture/test_argumentation_pin_aba_adf.py`
  - Result: `9 passed in 3.35s`.
  - Log: `logs/test-runs/ws-o-arg-dung-extensions-target-20260428-145620.log`.

## Issues surfaced

- The first upstream labelling implementation enumerated all three-valued labellings and made the full suite effectively hang. It was replaced with candidate-IN-set enumeration plus an acyclic grounded fast path before closure.
- `Coste-Marquis_2005_PrudentSemantics/notes.md` is absent from the local paper collection. The prudent implementation used Baroni 2007's prudent-definition summary plus the Coste-Marquis paper PDF found via CiteSeerX for the Step 0 inventory; the adjacent local `Coste-Marquis_2005_SymmetricArgumentationFrameworks` notes were not treated as a substitute.
