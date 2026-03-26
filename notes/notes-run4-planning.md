# Run 4 Planning — ATMS Semantics & Introspection

## GOAL
Plan Run 4: ATMS semantics and introspection, not more structured argumentation.

## What I've Read

### Current ATMS Engine (propstore/world/atms.py)
- ATMSNode: node_id, kind, payload, label, justification_ids
- ATMSJustification: justification_id, antecedent_ids, consequent_ids, informant
- ATMSEngine: builds assumption nodes, claim nodes, justifications; propagates labels; materializes parameterization justifications; updates nogoods from conflicts
- Public API: `claim_label()`, `supported_claim_ids()`, `derived_label()`, `argumentation_state()`
- `argumentation_state()` returns: backend, supported list, defeated list, nogoods

### Current Integration Points
- **bound.py**: `_reasoning_backend() == "atms"` gates in value_of, derived_value, resolved_value; lazy `atms_engine()` accessor; `_attach_atms_*_label()` methods
- **resolution.py**: `_resolve_atms_support()` — resolution by ATMS-supported status; only checks supported vs not
- **worldline_runner.py**: Section 5 captures `argumentation_state()` when backend=atms
- **compiler_cmds.py:904**: `world extensions --backend atms` explicitly rejected with error "does not expose Dung extensions"
- **types.py**: `ReasoningBackend.ATMS` enum; no ATMS-specific status types

### Current Tests (test_atms_engine.py)
1. Combined support propagation to derived node
2. Nogoods prune derived environments
3. Label propagation is order-independent
4. Cycles don't bootstrap support
5. Supported claims are subset of active (semantic overlap)
6. Context-only claims don't fabricate exact support
7. Context-scoped claim WITH matching assumption gets exact support
8. Worldline policy accepts atms backend, captures atms state
9. CLI rejects atms backend for extensions command

### Paper Notes — What's Missing from Current Implementation

**de Kleer 1986:**
- Four node categories: TRUE (empty env, universal), IN (nonempty label), OUT (empty label), FALSE (never holds). Current engine has NO node status/category system.
- Label properties: consistency, soundness, completeness, minimality. No verification/introspection for these.
- Classes as variables (oneof constraints). Not implemented.
- Defeasibility assumptions for justification retraction. Not implemented.
- Lazy label updates. Not implemented (full eager propagation).

**Dixon 1993:**
- Essential Support: ES(p,E) = intersection of all foundational belief sets. Not computed.
- Entrenchment levels E1-E5 from justificational structure. Not computed.
- Context switching modeled as AGM expansion/contraction. No API for this.

**Ghidini 2001:**
- Local Models Semantics: contexts as partial objects with compatibility. Relevant to multi-context reasoning but more architectural than Run 4.

**Odekerken 2023:**
- Four justification statuses: unsatisfiable, defended, out, blocked. Maps to de Kleer's categories.
- Stability: will status change with more info? Not implemented.
- Relevance: which unresolved queries matter? Not implemented.

## Key Gaps for Run 4 (ATMS semantics + introspection)

1. **No node status categories** — de Kleer's TRUE/IN/OUT/FALSE not exposed
2. **No environment/context inspection** — can't ask "what holds in this environment?"
3. **No label property verification** — consistency/soundness/completeness/minimality not checkable
4. **No essential support** — Dixon's ES(p,E) not computed
5. **No explain/introspect API** — can't ask "why does this node have this label?"
6. **argumentation_state() is minimal** — just supported/defeated/nogoods, no per-node detail
7. **No CLI surface for ATMS introspection** — extensions rejects ATMS, no alternative command
8. **No stability/relevance** (Odekerken) — but this may be out of scope if "not more structured argumentation"

## NEXT
Synthesize into the four requested sections.
