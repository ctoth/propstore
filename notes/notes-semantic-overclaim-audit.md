# Semantic Overclaim Audit: ATMS Bounded Replay vs True Revision

## GOAL
Identify where the current ATMS substrate could lie to an intervention planner — specifically, where bounded additive replay could be mistaken for true AGM revision/contraction.

## KEY FILES READ
- `propstore/world/atms.py` — ATMSEngine: global exact-support propagation + bounded future analysis
- `propstore/world/labelled.py` — Label, EnvironmentKey, NogoodSet, combine_labels, merge_labels, normalize_environments
- `propstore/world/model.py` — WorldModel: read-only reasoner over compiled sidecar
- `propstore/world/types.py` — ATMSNodeStatus, ATMSOutKind, QueryableAssumption, ATMSInspection
- `propstore/worldline.py` — WorldlinePolicy explicitly disclaims AGM semantics (line 61)
- `propstore/dung.py` — Pure Dung AF extension semantics
- `propstore/z3_conditions.py` — Z3 condition solver for disjointness/equivalence

## CRITICAL OBSERVATIONS

### 1. The future-replay mechanism is ADDITIVE ONLY
- `_future_engine()` (atms.py:1108-1144) builds future environments by APPENDING queryable assumptions to the current environment
- It creates a new BoundWorld with `future_assumptions = current_assumptions + queryable_assumptions`
- There is NO mechanism to REMOVE an assumption from the current environment
- Each future engine is a fresh full rebuild — not an incremental update

### 2. No retraction/contraction exists anywhere
- Grep for retract/contract/revise/withdraw/entrenchment found ZERO implementation code
- The only mentions are in `scripts/register_concepts.py` (registering concepts ABOUT contraction as domain knowledge) and `scripts/reconcile_vocab.py` (vocabulary about AGM)
- `worldline.py:61` explicitly says "They do not imply AGM-style revision semantics"
- `atms.py:10-11` explicitly disclaims "AGM-style revision, entrenchment maintenance, or a full de Kleer runtime manager"

### 3. NogoodSet is append-only
- `_update_nogoods()` only ADDS nogoods from conflicts — never removes them
- NogoodSet is frozen/immutable — updates create new instances with more entries
- No mechanism to retract a nogood (e.g., "this conflict was resolved")

### 4. Labels propagate but never shrink by policy
- `_propagate_labels()` merges labels monotonically (merge_labels union)
- Labels can shrink via nogood pruning, but nogoods themselves only grow
- There's no "remove this justification" operation

### 5. Stability/relevance analysis answers "could X flip?" but NOT "what should we retract to make X flip?"
- `is_stable()`, `could_become_in()`, `could_become_out()` test additive futures
- `status_flip_witnesses()` returns which ADDITIONS flip status
- None of these answer: "which assumption should we REMOVE to achieve goal G?"

### 6. The honest disclaimers exist but are in docstrings, not in the API surface
- An intervention planner calling `could_become_in()` gets back "add these assumptions"
- But never "retract these assumptions" — that operation doesn't exist
- The API names suggest symmetric capability that isn't there

## WHERE THE LIE LIVES
The system can answer "what happens if we learn more?" but cannot answer "what happens if we unlearn something?" or "what's the minimal retraction to make X consistent?"

An intervention planner needs:
- Contraction: "remove belief B to restore consistency" — NOT SUPPORTED
- Revision: "add A, which forces removing B via AGM" — NOT SUPPORTED
- Entrenchment ordering: "B is less entrenched than C, so retract B first" — NOT SUPPORTED
- Recovery: "after retracting B, what labels survive?" — NOT SUPPORTED

What the system actually provides:
- Expansion: "add assumption A, rebuild, see what happens" — SUPPORTED
- Conflict detection: "these environments are nogood" — SUPPORTED
- Stability: "does adding A flip status?" — SUPPORTED

## NEXT
Formulate the three-section deliverable.
