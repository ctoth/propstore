# Epistemic OS WS0 Baseline

Date: 2026-04-25
Workstream: `plans/epistemic-os-workstreams-2026-04-25.md`

## Read Before Baseline

- `plans/epistemic-os-workstreams-2026-04-25.md`
- `proposals/epistemic-operating-system-roadmap.md`
- `proposals/epistemic-operating-system-synthesis-2026-04-21.md`
- `reports/research-structural-predicates-cel-frontend.md`
- `docs/subjective-logic.md`
- `propstore/grounding/predicates.py`
- `propstore/context_lifting.py`
- WS1 notes for Cimiano 2016, Buitelaar 2011, Dowty 1991, Fillmore 1982, and Baker 1998

The retired support files named in the workstream were not present at their
listed paths:

- `proposals/typed-documentstore-and-semantic-families-proposal-2026-04-17.md`
- `plans/typing-strictification-plan-2026-03-29.md`

Their constraints remain active through the reconciled text embedded in the
active workstream.

## Baseline Commands

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label ws0-baseline
uv run pyright propstore
```

## Baseline Results

- Logged pytest: 2788 passed in 74.73s
- Pytest log: `logs/test-runs/ws0-baseline-20260425-175127.log`
- Pyright: 0 errors, 0 warnings, 0 informations

## Scope Boundary

This baseline is WS0 preflight only. No production semantic migration has
started. The first executable code slice remains the workstream's WS0 plus tiny
WS1 relation-kernel skeleton.
