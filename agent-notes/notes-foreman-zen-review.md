# Foreman notes — harsh zen review of REWRITE_PLAN — COMPLETE (all 5 reports read)

Reports: propstore/reports/rewrite-zen-{A,B,C,D,E}.md.

## FINAL VERDICT
The plan's STRATEGY/shape is zen-sound: non-commitment IS preserved end-to-end in the design (author→source→finalize→
promote[quarantine]→sidecar[quarantine projection]→render[sole filter w/ show-quarantined flags]); cutover reversible
(old master archived, reference retained, flip gated on full green). BUT there are concrete zen risks that MUST be fixed
in the plan+inventory BEFORE building. Not "is this it" = no-as-written; yes-after-hardening.

## THE SINGLE BIGGEST INSIGHT (zen-E global #1 + worst)
Z1 (non-commitment) is enforced only by BEHAVIORAL tests, but the two components that DECIDE quarantine-vs-gate —
the semantic-pass framework (Phase 9, NO reference test, rebuilt blind) and promotion (Phase 8) — have weak/no behavioral
coverage, and the standing CI gates are STRUCTURAL (import-linter catches Z3/Z4/Z6 coercers, CANNOT catch a behavioral Z1
build-time-gate regrowth). The disease re-enters not as a visible coercer but as a build/promote GATE that no gate guards.
=> REQUIRED: a STANDING BEHAVIORAL Z1 GATE in CI from day 0: feed deliberately-invalid concept/claim/form/stance ->
assert each appears as a quarantined sidecar row + diagnostic, ZERO dropped, render filters. Port the quarantine corpus
(remediation T2_2*, FI:69/133) as the semantic-pass framework's ACCEPTANCE test (not a self-authored one).

## GLOBAL TOP-3 (zen-E)
1. Build-time-gate regrowth via blind semantic-pass rebuild (Phase 9). [above]
2. DROP classification can DELETE a non-commitment invariant (irreversible). Concrete: test_codex2_claim_dedupe_diverges_on_version
   is marked DROP (FI:135) but ASSERTS two versions DON'T collapse = the core principle. FIX: re-audit every DROP; default-PORT
   anything named diverge/version/roundtrip/dedupe/collapse/quarantine until proven pure-shape.
3. Promotion (Phase 8) delegates Z1 to inventory not plan: trust calibration must STAMP not GATE; "per-item blocking filter"
   must QUARANTINE not DROP. Spell into plan + behavioral gates.

## PER-SLICE VERDICTS
Ph0 ZEN-RISK (coverage-loss gate hole). Ph1 ZEN-RISK-low (don't bake normalization; render must exercise a real filter).
Ph2 ZEN-VIOLATION (dims_signature re-export). Ph3 ZEN-RISK (F3.1 VIOLATION-grade contract inversion). Ph4 ZEN-RISK (CKR/CSAF
sequencing; missing `unknown` view state). Ph5 CONDITIONAL FAIL (opinion/doxa coercer). Ph6 CONDITIONAL FAIL (ConflictClaim/MergeClaim
views-not-types). Ph7 SPLIT REQUIRED (atms id-owner Z4 back-edge + atom-kind seam + input contract; "compute->emit()" wording wrong).
Ph8 CONDITIONAL PASS (stamp-not-gate, quarantine-not-drop, alignment keeps rival, collapse dups). Ph9 FAIL (highest risk — blind
semantic-pass, build/validate dual-path, charter-FK unproven, backward layer dep artifact_verification->world). Ph10 PASS (strongest;
calibration-split + embeddings call-through-not-wrap; H5 needs honest-ignorance test).

## FULL FIX LIST: see prior consolidated sections in git history of this file + the 5 reports. Headline fixes:
- Standing behavioral Z1 quarantine gate (above) — TOP priority.
- Fix inventory wording "never reaches sidecar" -> "blocked stub row + diagnostics + render filter" (audit all never/reject/block lines).
- opinion/doxa: provenance upstream-into-doxa OR out-of-band git-note; ONE doxa.Opinion; no subtype/shim.
- atms: name id-brand owner (no propstore.core import in kernel); collapse assumption/context 2-tuple to one atom set; define pkg input types;
  strike "compute moves to kind emit()"; SPLIT Ph7 -> 7a-atms(gate on atms tests vs package alone) / 7a-causal / 7a-world / 7b(delegate to belief-set).
- DELETE re-exports: dimensions.dims_signature, argumentation.py marker, merge/description_kinds.py.
- add `unknown` view state (distinct from blocked/missing).
- coverage gate = capability-diff vs reference per-slice count, not green-ports; split hybrid files' PORT half before dropping.
- DROP re-audit (top-3 #2).
- build vs validate: one framework, differ only in sink (no dual-path).
- z3 gate -> "no z3 outside condition-ir consumption surface" (permanent linter).
- resolve eq-equiv pin contradiction; CONSUMEs are verify steps (nothing imports eq-equiv/doxa yet).
- provenance carrier <= Ph5; provenance never in identity from commit1; opinion None->vacuous.
- CKR/CSAF Phase4/5 sequencing fix. backward layer dep (artifact_verification->world) resolve ownership.
- ghost: reproduce grounder.py double-count before fixing. fix DESIGN-doc path in plan §3.
- ConflictClaim/MergeClaim = views over Claim charter. concept alignment = proposals/render/honest-ignorance + keeps rival.

## DECISIONS NEEDING Q (genuine forks)
1. opinion/doxa provenance: UPSTREAM into doxa (opaque payload) vs OUT-OF-BAND git-note carrier.
2. atms id-brand owner: shared id package vs engine generic over opaque atom-id param.
3. provenance carrier resequencing: pull to <= Phase 5 (yes/no).
4. Phase 7 split into 7a-atms / 7a-causal / 7a-world / 7b (yes/no).
5. Add the standing behavioral Z1 quarantine gate as a day-0 CI gate (strongly recommend yes).

## NEXT: present to Q. Amend REWRITE_PLAN.md + FEATURE_INVENTORY.md (needs non-foreman or a dispatched writer agent) after Q decides 1-5.
## Context safe: feature-peak preserved (3702 green); quire green; 2 substrates shipped.
