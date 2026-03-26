# Semantic Contract Review — 2026-03-23

## GOAL
Review `plans/semantic-contract.md` as an execution-grade contract for the upcoming propstore semantic foundations work.

## WHAT I OBSERVED

### Contract structure
- 6 domain contracts: Contexts, Stances, Measurements, Algorithms, Draft/Final Claims, Sidecar Projection
- Each follows: Meaning → Required Semantics → Allowed Future Evolution → Proof Obligations → Compatibility Expectations
- Plus: Test Contract, Rename/Move/Deletion Contract, Round-Entry/Close Questions, "What This Contract Does Not Settle"
- Authoritative for R0–R6 of `plans/semantic-foundations-and-atms-plan.md`

### Codebase verification (via Explore agent)
All 7 claimed defects confirmed against actual source:

| Claim | Verified? | Evidence |
|-------|-----------|----------|
| Context hierarchy gap in `WorldModel.bind()` | YES | `model.py:337` omits `context_hierarchy` param |
| `_classify_pair_context()` dead code | YES | Exists at `conflict_detector.py:54` but never called in `detect_conflicts()` |
| FK enforcement missing | YES | Schema declares FKs but `PRAGMA foreign_keys=ON` never executed |
| Measurement invisible to concept queries | YES | Stored via `target_concept`, queried only by `concept_id` |
| Algorithm conflict grouped by input concept | YES | `conflict_detector.py:150-157` groups by first variable, not `claim["concept"]` |
| Sidecar cache key incomplete | YES | `_content_hash()` at `build_sidecar.py:31-44` omits contexts, forms, stances |
| No draft/final boundary | YES | `stage` field exists but no enforcement anywhere |
| Stance types match | YES | 7 types exactly as listed |

## REVIEW VERDICT: ACCEPTABLE WITH CHANGES

### Strengths (7)
- Grounded in verified defects, not aspirational
- Consistent proof obligation structure across all domains
- Principled non-commitment via "Allowed Future Evolution" sections
- Mechanical round-entry/close checklists
- Exact stance type enumeration matching code
- Conservative, testable compatibility expectations
- Literature grounding is load-bearing (de Kleer→environments, Dung→graph integrity, etc.)

### Defects (9)
1. **D1**: Draft-claim contract contradicts CLAUDE.md design checklist (items 1 & 2 say no gates before sidecar; contract says drafts are "non-final")
2. **D2**: "Context phi-node" used as required output but downstream semantics undefined
3. **D3**: "Unrelated contexts" never mechanically defined (sibling vs. ancestor ambiguity)
4. **D4**: Measurement proof obligations miss type-distinctness preservation
5. **D5**: `none` stance type has no semantic specification
6. **D6**: Algorithm variable renaming invariant uses undefined "semantics are preserved"
7. **D7**: No contract for stance-context interaction (what if endpoints are in different belief spaces?)
8. **D8**: Schema version marker unspecified concretely
9. **D9**: "Where practical" escape hatch on Hypothesis undermines the gate

### Tightening Changes (9)
- T1: Draft artifacts must compile into sidecar; distinction is a row marker, not a gate
- T2: Define phi-node downstream: excluded from conflict counts, not passed as attacks
- T3: Define "unrelated" = neither is ancestor of the other
- T4: Add proof that measurement rows carry distinguishable type marker
- T5: Specify `none` stance = provenance edge, filtered before AF construction
- T6: Replace vague renaming invariant with "bijective renaming with identical concept refs/conditions/body"
- T7: Add stance-context interaction rule: both endpoints must be visible in active environment
- T8: Schema version = hash of DDL, not manual number
- T9: Remove "where practical" — require Hypothesis for every listed invariant or explain why not

## SESSION 2 — Fresh re-review (2026-03-23)

Re-read contract, plan, CLAUDE.md, and implementation. Verified prior findings still hold.

Additional findings this session:
- Content hash confirmed at build_sidecar.py:159 — only concepts + claim_files
- Stance validation at build_sidecar.py:93-134 — silently skips invalid rows (no error/warning)
- Measurement conflict grouping at conflict_detector.py:294-329 — uses listener_population as phi-node separator, contract is silent on this
- Contract proof obligations for context visibility don't require transitivity; plan P1 does
- Contract says "ancestor visibility holds" without specifying transitivity direction
- "Effective assumptions monotone under inheritance" — direction unspecified (monotone increasing as you descend?)
- No proof obligation for universal claims remaining visible in context-scoped queries (only in compatibility section)
- Inline stances (in claim YAML) — compatibility says they must work but no FK validation specified for them

## NEXT
Write the four-section review output (second pass, stricter).
