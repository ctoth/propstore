# Harsh zen review — rewrite plan, Phases 3 & 4

NOTE: intended target was reports/rewrite-zen-B.md but the foreman-protocol hook blocks Write outside
prompts/ and notes-*.md. Content delivered here + in final message.

Reviewer: adversarial. Scope: Phase 3 (claim + conditions), Phase 4 (context + grounding +
defeasibility). Read-only. Reference worktree consulted at `scratchpad/wt-2b240dcb`.

Verdict summary: **both phases ZEN-RISK** (no outright ZEN-VIOLATION in the plan text, but two
artifacts the implementer is told to follow — the inventory caption and the worked Claim charter —
actively steer toward Z1 and Z2 violations, and Phase 4 has a layer/sequencing inversion).

---

## Phase 3 — claim + conditions

| # | verdict | principle | exact concern | concrete fix |
|---|---------|-----------|---------------|--------------|
| 3a | **ZEN-RISK** | Z1 (non-commitment) | Targeting contract describes quarantine as **"Claim quarantine pipeline (invalid claims never reach sidecar)"** (`inventory/claim-conditions.md:53`, cap 38). Read literally = Z1 checklist Q1 ("prevent ANY data reaching sidecar → WRONG") and Q3 (gate before render). Reference does the OPPOSITE: `test_T2_2b_claim_pipeline_quarantine.py:65-89` asserts `build_sidecar(...) is True` (build SUCCEEDS) and writes the invalid claim to `build_diagnostics` WITH provenance (claim_id/source/severity/blocking/message); excluded only from the active `claims` projection, never blocked from existing. Plan §Phase 3 ("WRITE tests for claim-validate workflow gaps") invites a gate test off the misleading caption. | Restate Phase 3 exit: invalid/malformed claims quarantine into the sidecar diagnostics projection WITH typed provenance; build never fails; data stays queryable; quarantine only drops the claim from the active projection. Make `test_T2_2b/2g/2h/2i/2o/2q` (assert `build is True` + diagnostic row) the gating PORT tests; forbid any "build raises on invalid claim" test. |
| 3b | **ZEN-RISK** | Z2 (honest ignorance) | Worked Claim charter (`projection-audit/DESIGN-projection-registry.md:66-68`) ships `confidence/sample_size/uncertainty` as bare `float\|None`/`int\|None` with NO typed-provenance carrier. CLAUDE.md Z2 requires every probability value carry measured\|calibrated\|stated\|defaulted\|vacuous. DESIGN `opinion` kind never states absent→vacuous. Plan defers opinion/provenance honesty to Phase 5 — a Phase-3 Claim carries a bare probability with no provenance typing for a whole phase. | Bind a typed-provenance carrier to each probability field in Phase 3 (lowering onto refs/notes/provenance per CLAUDE.md); opinion binding maps absent→vacuous; gate with a honest-ignorance/opinion-vacuity test before the field ships. |
| 3c | **ZEN-RISK** | Z2 / Z3 | Same charter stores `conditions: tuple[str,...]  # CEL strings -> ConditionIR compiler (bespoke)`; §5 lists conditions as bespoke recompiled-on-demand. Breaks cap 16 (no CEL reparse at query time), cap 5 (CheckedConditionSet build/dedupe), cap 12 (registry-fingerprint guard) — all PORT (`claim-conditions.md:31,20,27`); also discards fingerprint provenance. | Persist condition-ir's canonical `CheckedConditionSet` (encoded_ir + fingerprint) as a projection-kind output, not raw CEL; query reuses encoded_ir. One canonical CheckedCondition owned by condition-ir, persisted — no propstore reparse path. |
| 3d | **ZEN-RISK** | Z3 (no coercer / one spelling) | "consume eq-equiv (delete in-tree equation_*)" leaves the `ConflictClaim` adapter (`compare_equation_claims`/`equation_signature`, SPEC §B) unexamined. Hazard: eq-equiv `EquationComparisonStatus{EQUIVALENT,DIFFERENT,INCOMPARABLE,UNKNOWN}` (cap 25) vs propstore `ConflictClass{CONFLICT,PHI_NODE,OVERLAP,UNKNOWN}` (cap 17) — a status→status map is the to_X mirror Z3 forbids. Also `CelExpr`/`CelRegistryFingerprint` classified ambiguously "condition-ir / propstore-proper" → two spellings risk. | `ConflictClass` may AGGREGATE eq-equiv status as one signal, never 1:1 re-spell it. Forbid any propstore enum mirroring `EquationComparisonStatus`. Pin `CelExpr`/`CelRegistryFingerprint` to condition-ir; delete `propstore.cel_types`. |
| 3e | **ZEN-CLEAN** | Z2 / Z7 | Honest-ignorance solver surface (Sat/Unsat/Unknown; Z3-unknown→Z3UnknownError) preserved; deletion-first consume of eq-equiv/human-to-sympy, no dual path; exit gate "no direct z3 import" is a good one-owner check. | Keep. |

---

## Phase 4 — context + grounding + defeasibility

| # | verdict | principle | exact concern | concrete fix |
|---|---------|-----------|---------------|--------------|
| 4a | **ZEN-RISK** | Z4 + sequencing | `apply_exception_defeats_to_csaf` (`defeasibility.py:339-395`) takes a CSAF in / returns CSAF out — does not build one. Cap 5 (`test_defeasibility_aspic_integration.py::test_exception_defeat_participates_in_dung_extension_computation`) needs a CSAF built from claims/stances, scheduled in **Phase 5** (`core/analyzers.py`+`aspic_bridge`). Phase 4 exit "green" but cap 5's producer doesn't exist until Phase 5. | Move `apply_exception_defeats_to_csaf`+cap5 to Phase 5, OR have the Phase 4 PORT test build the CSAF directly from consumed `formal-argumentation` + claim fixtures. Don't list cap 5 as a Phase 4 exit gate if its producer is Phase 5. |
| 4b | **ZEN-CLEAN (watch)** | Z4 / layer-4 | Plan keeps CKR deciding ist applicability + injecting Dung defeats at the ASPIC+ boundary without ASPIC+ owning contextual semantics. Verified `defeasibility.py:24-25` imports `argumentation.aspic.CSAF`/`argumentation.dung.ArgumentationFramework` directly (no mirror); `:343-348` adds only defeat edges. | Keep. Watch: don't relocate the injection into `aspic_bridge`. |
| 4c | **ZEN-CLEAN** | Z2 | UNKNOWN first-class, not coerced false. Verified `defeasibility.py:53-55,314-318` (HOLDS/EXCEPTED/UNKNOWN; solver UNKNOWN never positive exception, cap 4) + `LiftingDecisionStatus=={lifted,blocked,unknown}`, `LiftingDecision` typed evidence carrier not boolean (`tests/architecture/test_lifting_decision_contract.py:18-22,52-57`, cap 18). | Keep. Add `test_ist_projection_contract`+`test_lifting_decision_contract` to Phase 4 discipline gates. |
| 4d | **ZEN-RISK** | Z1 | Lifting materializes ist assertions to sidecar (cap 2/14). Z1-OK ONLY because materialized assertions carry rule provenance/support (cap 2/3). Plan §Phase 4 doesn't restate that materialization persists WITH provenance and must not collapse a rival lifting decision into a stored verdict. | State contract: materialized lifted assertions persist with full `LiftingDecision` evidence so render filters; never a collapsed can_lift boolean. Gate `test_lifting_blocked_in_provenance.py` + `test_context_lifting_ws5.py::test_sidecar_stores_lifting_materialization_provenance`. |
| 4e | **ZEN-CLEAN (watch)** | Z1 + Z3 | Grounding preserves 4-valued answer, all 4 sections always present, round-trip read∘populate==sections (caps 7,13) — no storage collapse; plan says "4-section". gunray as one type: `facts.py`→`argumentation.aspic.GroundAtom`, `translator`→`gunray.DefeasibleTheory`, no mirror. | Keep. Watch: `GroundedRulesBundle` must add policy only, never re-type gunray atoms/arguments. |
| 4f | **ZEN-RISK (data)** | correctness / plan honesty | Plan commits to "Fix `grounder.py:342-351` double-count." Code as written (`[0]` selects strict, then +defeasible +defeater) yields strict+defeasible+defeater EACH ONCE — no duplication. SPEC/inventory "double-count" (`SPEC §G`, `context-grounding-defeasibility.md:37`) is suspect. | Write a failing test demonstrating the actual defect before fixing, or downgrade to readability cleanup. Don't ship a fix for a mischaracterized bug without a red test. |

---

## Worst finding

**Phase 3, 3a (Z1).** The artifact an implementer ports from — `inventory/claim-conditions.md:53`, cap
38 "**invalid claims never reach sidecar**" — states the core non-commitment principle backwards. The
reference is Z1-correct (`test_T2_2b_claim_pipeline_quarantine.py:65-89`: build SUCCEEDS, invalid claim
quarantined into `build_diagnostics` WITH provenance, only dropped from the active claims projection).
The plan's "WRITE tests for claim-validate workflow gaps" instruction, fed by that caption, is a direct
invitation to rebuild the one thing CLAUDE.md's design checklist forbids: a build-time gate that
prevents data from reaching the sidecar. Fix the caption to the real contract; make the `build is True`
+ diagnostic-row quarantine tests the non-negotiable Phase 3 exit gate.
