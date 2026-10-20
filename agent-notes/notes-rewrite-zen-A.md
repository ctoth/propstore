# Harsh zen review — rewrite plan slices Phase 0, 1, 2

(Intended destination reports/rewrite-zen-A.md was blocked by the active foreman
Write hook; this notes- file is the allowed location. Lead: relocate if desired.)

Reviewer: adversarial. Default stance: guilty until proven clean. Reference spec:
propstore @ 20e55cca (`scratchpad/wt-2b240dcb`). Plan:
`scratchpad/REWRITE_PLAN.md`. Zen: `CLAUDE.md`.

## Verdict table

| phase | verdict | principle(s) at risk | the exact concern | the concrete fix |
|---|---|---|---|---|
| **Phase 0 — Cutover & scaffold** (plan 74-81) | **ZEN-RISK** | Z1 (meta), Z7 | The clean-slate (`delete tests/` + re-extract PORT per slice, plan 24-28, 62-66) makes the **human-authored PORT/DROP ledger the de-facto specification of non-commitment**. A non-commitment behavior most naturally lives in a test that *looks* DTO-shaped (e.g. "invalid claim is quarantined but still stored with provenance" vs "claim row has columns X,Y"). Mis-DROP one → that guarantee ships untested, undetectably. The inventory itself admits 13 capabilities with NO gating test and 152 unclaimed master files (FEATURE_INVENTORY headline). Day-0 CI is only the class-B architecture gates; the **non-commitment data-flow invariant tests (remediation/phase_2_gates T2_2*, render_policy_*) are PORT in later slices**, so from Phase 0→Phase 7 nothing enforces "filter at render not build." | (a) Keyword safety-net before deletion: any reference test whose body mentions sidecar/quarantine/visible/blocked/render/provenance is PORT by default — never DROP on shape. (b) Front-load the four design-checklist invariant tests as early as their deps allow; don't defer them to "whenever the owning slice lands." (c) tests/ deletion is reversible (reference branch preserved) so the act is fine — the ledger classification is the hazard, not the delete. |
| **Phase 1 — Walking skeleton** (plan 83-87) | **ZEN-RISK** | Z1, Z3 | Two things smuggle under "minimal": (1) **"minimal build"** can bake raise-on-invalid as the easy path and "fix later" — that is a build-time gate (design checklist Q3/Q4 = WRONG). Reference behavior is *quarantine, not raise* ("Build quarantines invalid form/concept/schema (not raises)", FEATURE_INVENTORY concept-core). (2) **"minimal fields"** on the Concept charter can omit logical-id/version-id identity + status + provenance — but those are the *precondition* for storage to hold two rival normalizations of the same concept. Drop them and the skeleton **commits to one normalization by construction**, violating the core principle, before any feature is even written. | Skeleton's "minimal" Concept charter MUST retain logical-id/version-id identity, status, and provenance from commit 1 (mirror the DESIGN Claim charter's `ContentId` + version-diverging dedupe, DESIGN §5). "Minimal build" = quarantine-to-sidecar path, never raise-on-invalid. A single *charter class* is fine (rivals are separate records); a charter that can't represent a rival is not. |
| **Phase 2 — concept-core + forms/dimensions** (plan 89-94) | **ZEN-RISK** | Z1 (worst), Z3, Z4 | **(1) Coreference build-time-collapse pressure.** Lemon description-claim coreference is Dung-backed, "policy-dependent clusters, not a fact," resolved AT RENDER (CLAUDE.md concept layer; FEATURE_INVENTORY concept-core line 62, "also exercised by merge-conflict M10"). But render/argumentation layers don't exist until Phases 5-7. Phase 2's exit gate is "concept-core PORT green" (plan 94), and gating test `test_lemon_phase3_semantics.py` exercises `coreference_query` — which *resolves*. Making it green in-phase, no render layer, is structural pressure to **compute/store a coreference result at build = collapse rivals in storage = cardinal Z1 violation.** **(2) unit-convert package status undecided + a mirror type.** Plan §5 (line 50) parks `unit-convert` as a "small pure helper in propstore," but `concept-lexical.md` (78-87) classifies `dimensions.py` as **EXTRACT:`unit-convert`** — "Zero propstore domain deps," external consumer material-db. Parking a generic zero-domain-dep substrate as a "helper" guarantees a second spelling the day material-db needs it (Z3). Separately `dimensional_invariants.py` "returns propstore `PiDiagnostic`" wrapping `bridgman.count_pi_groups` (conditions-dimensions-equations.md:57) = a mirror type over a package output. **(3)** "embeddings surface" is layer-3 heuristic placed in a layer-2 slice (minor Z4); fine only if it embeds ALL concepts and never selectively. | **(1) Re-sequence or fence:** Phase 2 *authors/stores* coreference as `MergeArgument` artifacts only; the resolution capability + its gating assertion move to the merge-conflict/argumentation slice (Phase 5/6) where render policy exists. State explicitly: no in-phase coreference resolution. **(2)** Decide unit-convert NOW: zero-domain-dep + external consumer ⇒ extract the package (consume bridgman), don't keep a generic substrate as a helper; delete `PiDiagnostic` — return bridgman's type directly (crossing is a call, not a conversion, CLAUDE.md substrate §3). NOTE this is unit *conversion* (pint), which bridgman lacks, so it is NOT itself a second spelling of bridgman's dimensional algebra — that part is clean. **(3)** Require embeddings over the full corpus; visibility stays a render-policy filter. |

## Worst finding

**Phase 2, Z1 — coreference resolution is gated to go green before its render layer
exists.** CLAUDE.md and the inventory both say description-claim coreference is a
*render-time, policy-dependent* Dung resolution — explicitly "not a fact." Yet the
plan makes "concept-core PORT tests green" (incl. `coreference_query` in
`test_lemon_phase3_semantics.py`) the Phase 2 exit gate, while the render and
argumentation layers that *do* the resolving don't land until Phases 5-7. The only
way to satisfy that gate in-phase is to resolve/store coreference clusters at
build — collapsing rival merge stories in storage, the single principle the whole
repo is built to prevent (CLAUDE.md "Core Design Principle"; design checklist
Q3/Q4). The plan does not *instruct* this, but its sequencing creates the pressure
and its exit gate rewards giving in. Fix: Phase 2 stores coreference as
un-resolved `MergeArgument` artifacts; move the resolution assertion to the
merge/argumentation slice. A sequencing defect fixable by moving one capability's
gating test — left unfixed it is a latent ZEN-VIOLATION baked into exit criteria.

## What is actually clean (so fixes don't over-correct)

- Phase 1 single Concept *charter class* is correct, not a normalization commitment — rivals are separate records under one type.
- unit-convert vs bridgman is a complementary layer (pint conversion vs dim algebra), not a duplicate algebra; the Z3 concern is its *package-vs-helper* status + the `PiDiagnostic` wrapper, not the conversion code's existence.
- Deleting `tests/` and `propstore/**` on the rewrite branch is reversible (reference branch + tag preserved); irreversibility worry is nil. Hazard is the PORT/DROP classification, not the deletion.
