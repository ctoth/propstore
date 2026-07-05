# Foreman first-cut analysis — Slice A (Phase 01 `world_charters` import fallout)

Date: 2026-05-24
Decision: Q chose option B (pivot — skip the failing-tests scout, use scout #2's Slice A as the first cut).

## Why Slice A

- It is the exact slice `00-index.md:50-58` calls "First Repair Answer" for the deleted-file fallout: split charter definitions into owning family charter modules, compose the whole derived-store schema through the registry/charter owner, expose only generic registry-level schema access. Do NOT recreate a world-charters module.
- Scout #2 enumerated all 8 production import sites of the deleted `propstore.families.world_charters` module (violation V004). Evidence file:line list is in `reports/scout-field-ownership-violations.md` rows V004 and Phase 01 mapping.
- Deletion-first compliant: the module is already deleted; the slice routes its eight call sites to a registry-level accessor. No shim, no re-export, no compatibility bridge.
- Independent of every other slice — touches only registry composition and the eight import sites. Touches no claim-metadata code (V001-V003 are a separate slice with typed-provenance design work).
- Slice B and Slice C remain queued behind Slice A for sequencing reasons: Slice B needs a Quire-prereq verification (Phase 02 ordering); Slice C is test-only and orthogonal but starting with Slice A lets us prove the verifier-behind-Codex loop on the highest-priority slice first.

## What the verifier (claude general-purpose, after Codex) must check

- HEAD at verification time is one commit ahead of `e13e302d` (or a small commit chain) and the new commit(s) are by Codex.
- `propstore/families/world_charters.py` is still absent. No re-creation under any name.
- No call site re-imports the deleted module under a new name or via a re-export bridge anywhere in `propstore/`.
- The registry/charter composition exposes a single accessor that returns the world schema/catalog; every former call site uses it.
- Phase 01 gate searches (`01-deleted-file-fallout-repair.md:56-61`) return zero production hits per the coder's report.
- Narrow pyright (`01:64-67`) is clean for the touched files.
- Phase 01 named test gates pass (`tests/test_world_query.py`, `tests/test_build_sidecar.py`, `tests/test_source_trust.py`) per the coder's report.
- Codex did not add a shim/alias/fallback/compatibility bridge — the verifier greps for re-exports, `from typing import TYPE_CHECKING`-guarded imports of the dead name, kwargs builders, or `try/except ImportError` blocks. None permitted.
- Codex committed atomically. Commit hash present in the Codex report.

## Slice D (Q decision queued)
Still queued for the make-it-so gate: whether `propstore/world/assignment_selection_policy.py:37 _claim_value` is a 4th duplicate to fold into `ClaimValueResolver` (per V035) or a legitimate separate policy boundary. Phase 09 silent on it. Not relevant for Slice A.