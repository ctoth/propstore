# Final gate verification

Workstream items: T12.1, T12.2, T12.3.

Full suite:
- Command: `powershell -File scripts/run_logged_pytest.ps1 -Label T12-final-full-suite-after-cayrol-dep tests/`
- Result: 2646 passed in 81.49s.
- Parallelism: `created: 16/16 workers`.
- Log path: `logs/test-runs/T12-final-full-suite-after-cayrol-dep-20260421-221552.log` (not committed).

Pyright:
- Command: `uv run pyright propstore`
- Result: 0 errors, 0 warnings, 0 informations.

Import-linter:
- Command: `uv run lint-imports`
- Result: analyzed 359 files and 2440 dependencies; 4 contracts kept, 0 broken.

Logs policy:
- Test logs were generated under `logs/test-runs/` by the required wrapper and were not staged or committed.

Result: final gates verified.
