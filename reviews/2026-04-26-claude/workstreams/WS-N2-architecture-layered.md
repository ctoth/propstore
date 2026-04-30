# WS-N2: Architecture — final layered import-linter contract over six README layers

**Status**: OPEN
**Depends on**:
- **WS-K** (heuristic relocation — moves `embed.py`, `classify.py`, `relate.py`, `calibrate.py` under `propstore/heuristic/` so Layer 3 in the layered contract has a real namespace to bind).
- **WS-N1** (shims gone, CLI ownership extracted, `_canonical_json` collapsed, renames complete — without these, the layered contract surfaces noise that obscures the layering invariant).
**Blocks**: nothing. Terminal workstream for the architecture-decoration tier.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Why this workstream exists (and why it is split from WS-N1)

WS-N originally bundled the layered-contract work with the shim/rename/CLI hygiene. Per `reviews/2026-04-26-claude/DECISIONS.md` D-26, that bundling forced WS-N to wait on WS-K (heuristic relocation) before any of it could land — including hygiene work that has no WS-K dependency. The split puts WS-N1 (immediate) on its own track and reserves WS-N2 for the work that genuinely depends on WS-K.

The README declares six architectural layers (storage → typing → heuristic → argumentation → render → agent workflow). The `import-linter` configuration declares four `forbidden` contracts, each over a single edge nothing currently imports. Per cluster U §"Import-linter contracts": every one is *vacuously satisfied today*. The reverse direction is the actual dependency in three of four cases (`merge → storage` at `propstore/merge/structured_merge.py:18`; `heuristic → source` at `propstore/heuristic/source_trust.py:14`). The fourth (`core.lemon → argumentation`) targets an edge that does not exist.

The `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py` test asserts only `result.returncode == 0`. No companion negative test exists. The linter is green for the wrong reason: there is nothing for the four spot-check contracts to catch.

WS-N2 closes the gap between *stated* architecture (six layers) and *enforced* architecture (one `layered` contract over those six layers, plus a negative-injection test that fails-closed when the contract erodes).

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `gaps.md` and has a green test gating it.

| Finding | Source | Citation | Decided |
|---|---|---|---|
| **T0.3** | Claude REMEDIATION-PLAN | `.importlinter:5-36` | Add a negative test that injects a known violation and asserts `lint-imports` rejects it. |
| **T5.3** | Claude REMEDIATION-PLAN / Cluster U | `.importlinter:5-36` | Replace four `forbidden` contracts with one `layered` contract over the six README layers. |

The layered-contract change will *surface* further violations (cluster U §"OBSERVED layering violations" enumerated them: `sidecar/build.py` imports `propstore.embed`; `world/model.py` imports `propstore.embed`; etc.). Those violations are the **point** of WS-N2 — they are real, they were always real, and the four-spot-check setup hid them. The fixes for those violations live in WS-K (heuristic relocation moves the imported targets into Layer 3) and the cleanup workstreams that follow. WS-N2's job is to make the contract honest; the violations the honest contract surfaces are downstream cleanup.

## Resolved decisions (formerly "Open questions for Q")

Decided in `reviews/2026-04-26-claude/DECISIONS.md`, now locked-in scope.

- **Cluster U Q3 — Replace `forbidden` with `layered`?** **Yes.** One `layered` contract over the six README layers. The four `forbidden` contracts are removed in the same commit.
- **Layer ordering** (top to bottom, i.e., outermost packages depend on innermost):
  1. `propstore.web` | `propstore.cli` (agent workflow)
  2. `propstore.app` (render / orchestration)
  3. `propstore.argumentation` | `propstore.aspic_bridge` | `propstore.world` | `propstore.belief_set` (typed reasoning)
  4. `propstore.heuristic` (heuristic / proposals only)
  5. `propstore.source` (source storage)
  6. `propstore.storage` (substrate storage)

This ordering matches `README.md:11-13` and the `project_architecture_layers` memory entry. Higher layers may import from lower layers; the reverse is forbidden.

Implementation note: the landed `.importlinter` contract uses `containers = propstore` and relative package names. It uses `:` inside the same six vertical rows (`web : cli`, `argumentation : aspic_bridge : world : belief_set`) because import-linter treats `|` as an independent-layer delimiter that forbids imports among same-row packages; `:` represents packages that share a row without imposing intra-row independence.

## Code references (verified by direct read)

### Import-linter contract surface (the decoration)

`C:\Users\Q\code\propstore\.importlinter` (repo root, not `propstore/.importlinter`) holds exactly four `forbidden` contracts: `storage→merge`, `source→heuristic`, `core.lemon→argumentation`, `worldline→support_revision`. Per Cluster U §"Import-linter contracts" verbatim: every one is *vacuously satisfied today*. The reverse direction is the actual dependency in three of four cases.

`tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py` is 21 lines, single test, asserts only `result.returncode == 0`. No companion negative test.

### Heuristic location (WS-K's responsibility, but the reason WS-N2 waits)

Today, `propstore/embed.py`, `propstore/classify.py`, `propstore/relate.py`, `propstore/calibrate.py` are top-level modules. They are heuristic-layer logic by stated architecture. The package `propstore/heuristic/` contains exactly two files. Until WS-K moves the heuristic logic under `propstore/heuristic/`, declaring `propstore.heuristic` as Layer 3 in the layered contract binds against an almost-empty namespace, and the layered enforcement mis-attributes violations (`sidecar/build.py` imports `propstore.embed` — under the layered contract, that's currently a Layer 6 → Layer 1 import, not the Layer 1 → Layer 3 it should be).

WS-N2 lands *after* WS-K so the layer bindings reflect reality.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_import_linter_negative.py`** (new — T0.3 gate)
   - Programmatically writes a temp module under a sandboxed copy of `propstore/` that introduces a known violation: e.g. inject `import propstore.app` into a synthetic `propstore.storage._test_violation` module (this is a Layer 6 → Layer 2 import, forbidden by the layered contract).
   - Runs `lint-imports` against the sandboxed root.
   - Asserts return code is non-zero AND stdout/stderr names the violated contract.
   - Runs once per declared layer pair: for each (lower, higher) pair, inject `import <higher>` from `<lower>` and assert rejection.
   - **Must fail today** for any sandboxed cross-layer edge that the four `forbidden` contracts do not catch — e.g. an injected `propstore.storage._test_violation -> propstore.app` is *not* caught by the existing four contracts, confirming weakness #2 in Cluster U: the contracts are spot-checks, not a layered invariant.

2. **`tests/test_layered_contract_covers_six_readme_layers.py`** (new — T5.3 gate)
   - Parses `.importlinter` via `configparser`.
   - Asserts exactly one contract of `type = layers`.
   - Asserts the layer list matches the six README layers in order:
     1. `propstore.web | propstore.cli`
     2. `propstore.app`
     3. `propstore.argumentation | propstore.aspic_bridge | propstore.world | propstore.belief_set`
     4. `propstore.heuristic`
     5. `propstore.source`
     6. `propstore.storage`
   - Asserts the four legacy `forbidden` contracts (`storage→merge`, `source→heuristic`, `core.lemon→argumentation`, `worldline→support_revision`) are **absent**.
   - **Must fail today**: `.importlinter` has zero `layers` contracts and four `forbidden` contracts.

3. **`tests/test_workstream_n2_done.py`** (new — gating sentinel)
   - `xfail` until WS-N2 closes; flips to `pass` on the final commit. Per Mechanism 2 in `REMEDIATION-PLAN.md` Part 2.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-N2 step N — <slug>`.

### Step 1 — Negative-test scaffolding (T0.3)
Land `tests/test_import_linter_negative.py` first, *before* changing any contract. The harness:

1. Copies `.importlinter` and `propstore/` (read-only relevant subset — `.py` files, `__init__.py`, the configuration) into a tempdir under `tests/_tmp/`.
2. Generates a synthetic violation module: writes `propstore/<lower-layer>/_test_violation_<uuid>.py` containing `import <higher-layer>` for the targeted edge.
3. Runs `uv run lint-imports --config <tempdir>/.importlinter` from the tempdir cwd.
4. Asserts return code != 0.
5. Asserts the violated contract's name appears in the linter output.
6. Cleans up the tempdir.

Parameterize over the layer pairs from the layered contract. The harness must produce a violation that the **current** four `forbidden` contracts do not catch — that's the weakness it documents.

Acceptance: harness lands green against the *target* layered contract (Step 2). Until Step 2 lands, the harness is `xfail` because the four `forbidden` contracts cannot reject most injected violations.

### Step 2 — Replace four `forbidden` with one `layered` (T5.3)
Edit `.importlinter`:

```ini
[importlinter]
root_package = propstore
include_external_packages = True

[importlinter:contract:propstore-six-layers]
name = propstore six-layer architecture
type = layers
layers =
    propstore.web | propstore.cli
    propstore.app
    propstore.argumentation | propstore.aspic_bridge | propstore.world | propstore.belief_set
    propstore.heuristic
    propstore.source
    propstore.storage
containers =
    propstore
```

Delete the four `[importlinter:contract:*]` `forbidden` blocks. They are removed in the same commit, not deprecated, not left as comments.

Run `lint-imports`. Expected fallout: every Cluster U "OBSERVED layering violations" entry surfaces. These are *real* violations the four-spot-check setup hid:
- `propstore.sidecar.build` imports `propstore.embed` (Layer 6 → Layer 4 if `embed` is in `propstore.heuristic`, post-WS-K).
- `propstore.world.model` imports `propstore.embed` (Layer 3 → Layer 4 — wrong direction).
- `propstore.merge.structured_merge:18` imports from `propstore.storage` (currently a sibling not in the contract; this is fine under the layered binding only if `propstore.merge` lives under `propstore.storage` or `propstore.app` — verify post-WS-K).
- `propstore.heuristic.source_trust:14` imports `propstore.source` (Layer 4 → Layer 5 — correct under the layered ordering, allowed).

Triage of the layering violations the new contract surfaces is **in scope for WS-N2 closure** per D-27. WS-N2's job is to land the honest contract AND to ensure `lint-imports` exits clean against it. The surfaced violations may route to WS-K (heuristic relocation), WS-L (merge), or new follow-up workstreams for *implementation*, but WS-N2 does not close until each of those is resolved and the layered contract passes with zero residual violations. There is no soft-gate, no allowlist, no "warn until later."

Per D-27 (Codex re-review #7) + `feedback_no_fallbacks.md`: hard-fail clean only. If WS-K closes with residual violations needing further design, WS-N2 stays OPEN until they are resolved upstream and `lint-imports` reports zero violations against the layered six-contract. The previously-considered "soft gate with allowlist" path is **rejected** — it is a fallback shim by another name and contradicts Q's "no old repos / iterate to perfection" rule.

Acceptance: `tests/test_layered_contract_covers_six_readme_layers.py` turns green; `tests/test_import_linter_negative.py` turns green for every parameterized pair; `lint-imports` exits with code 0 against the layered six-contract with **zero residual violations** (no allowlist file, no soft-gate warn mode).

### Step 3 — Update `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py`
The existing test asserts only `result.returncode == 0`. Update to:
- Assert `result.returncode == 0` against the layered contract — passes when the codebase satisfies all six layers cleanly. Per D-27, this is the only acceptable state; there is no allowlist branch.
- Asserts the four legacy `forbidden` contracts are gone (configparser check).
- Asserts no `tests/_allowlists/layered_contract_residual.txt` (or equivalent allowlist artifact) exists in the tree — the soft-gate allowlist is forbidden by D-27.

The negative test (`test_import_linter_negative.py`) gates fail-closed behavior; the positive test gates today's known-good state. Both must be hard-green at WS-N2 close.

### Step 4 — Close gaps and gate
- Update `docs/gaps.md`: remove entries for T0.3 and T5.3; add a `# WS-N2 closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_n2_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-N2 done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors. Evidence: 2026-04-30 local run.
- [x] `uv run lint-imports` — passes against the new layered contract with **zero residual violations** (per D-27: hard-fail clean only, no allowlist, no soft-gate). Evidence: 2026-04-30 local run, `propstore six-layer architecture KEPT`.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-N2 tests/test_import_linter_negative.py tests/test_layered_contract_covers_six_readme_layers.py tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py tests/test_workstream_n2_done.py` — all green. Evidence: pending closure gate.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs the WS-A baseline. Evidence: pending closure full-suite gate.
- [x] `.importlinter` contains exactly one `[importlinter:contract:*]` block, of `type = layers`, with the six README layers in order.
- [x] No `forbidden` contracts remain.
- [x] The negative-test harness rejects an injected violation for every layer pair.
- [x] No `tests/_allowlists/layered_contract_residual.txt` (or equivalent) exists in the tree (per D-27).
- [x] `docs/gaps.md` has no open rows for T0.3 or T5.3.
- [ ] This file's STATUS line is `CLOSED <sha>`.

## Done means done

WS-N2 closes when **every finding in the table at the top is closed**:

- T0.3: negative-test harness lands; injecting a known violation produces non-zero return from `lint-imports`; the violated contract is named in output; the harness runs once per declared layer pair.
- T5.3: one `layered` contract over the six README layers replaces the four `forbidden` contracts; the layer ordering matches the README and the project memory `project_architecture_layers`.
- The layered contract passes hard-clean against the codebase: `lint-imports` returns 0 with **zero residual violations**, no allowlist, no soft-gate (per D-27). If WS-K's heuristic relocation surfaces a violation needing further design, WS-N2 stays OPEN until that design is resolved upstream and the contract is clean.
- `gaps.md` updated; `tests/test_workstream_n2_done.py` flipped from xfail to pass.

If any one is not true, WS-N2 stays OPEN.

## Papers / specs referenced

None directly. WS-N2 is internal infrastructure. References are project-internal: `project_architecture_layers` (the layered contract is its mechanical encoding), `feedback_imports_are_opinions` (the layered contract is the substrate that lets "imports are opinions" be enforced one provenance check at a time, against a known topology).

## Cross-stream notes

- **WS-N2 ↔ WS-K**: WS-K is the hard prerequisite. WS-K moves heuristic modules under `propstore/heuristic/` so Layer 3 has its declared content. If WS-K closes with residual heuristic-import violations from non-heuristic layers (e.g. `world/model.py` imports `propstore.embed`), those violations belong to the workstreams that own those callers — WS-N2 surfaces them and routes them, but does not fix them.
- **WS-N2 ↔ WS-N1**: WS-N1 deletes shims, extracts CLI ownership, collapses `_canonical_json`, and runs the two renames. Without WS-N1, the layered contract surfaces additional noise (e.g. CLI-shaped types crossing layer boundaries via app-layer dataclasses, `_canonical_json` duplication suggesting non-existent boundaries). WS-N1 first; WS-N2 against the cleaner substrate.
- **WS-N2 ↔ WS-L**: `propstore/merge/` is not currently in the README layer list. After Step 2, the layered contract will either accept `propstore.merge` (as a sibling of `propstore.storage` in Layer 6, if WS-L's merge layer is logically substrate) or reject it (forcing a structural decision). Coordinate with WS-L on which layer `merge` belongs to before authoring the contract.
- **WS-N2 ↔ WS-A**: WS-A's full-suite baseline is the comparison anchor for the "no NEW failures" gate. WS-N2 must not regress against `logs/test-runs/pytest-20260426-154852.log`.

## What this WS does NOT do

- Does NOT fix any layering violations the new layered contract surfaces. Those route to WS-K (heuristic-import callers in `world/model.py`, `sidecar/build.py`), WS-L (merge layer placement), or new workstreams.
- Does NOT delete shims, extract CLI ownership, collapse `_canonical_json`, or run the renames. Those are WS-N1.
- Does NOT move `embed.py`, `classify.py`, `relate.py`, `calibrate.py` under `propstore/heuristic/`. That is WS-K.
- Does NOT add provenance to `propstore/storage/repository_import.py`. Cluster U "imports are opinions" stays open.
- Does NOT regenerate `gaps.md` line numbers.
- Does NOT change `semantic-contracts.yaml` runtime-enforcement question.
