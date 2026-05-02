# Contexts and Micropublications

Grounds WS-A phase 4 (`reviews/2026-04-16-code-review/workstreams/ws-a-semantic-substrate.md`) and composes with the non-Davidsonian event position in `docs/event-semantics.md`.

## Position

propstore represents contextual truth directly: a claim is true in a context as `ist(c, p)`, not as an unqualified fact plus a visibility hierarchy. Contexts are first-class logical terms with authored structure: assumptions, parameters, perspective, and explicit lifting rules. A context may also be interpreted descriptively as the cluster of claims propstore informally calls "the 2024 RHIC run" or "the Stanford Prison Experiment." The cluster's coherence is defeasible and resolved at render time; no event individual is stored underneath it.

Micropublications are the bundle layer over that contextual substrate. A micropublication groups claim references, evidence references, assumptions, stance, provenance, and source identity. In the runtime belief space, a canonical micropublication is also an ATMS node: it is supported only when its context node and member claim nodes are supported.

## Paper Commitments

- McCarthy 1993: `ist(c, p)` is the primary truth form. Contexts can be entered, exited, nested, and related by lifting rules rather than by implicit inheritance.
- Guha 1991: lifting is relative decontextualization. A bridge from source context to target context is authored and mode-bearing; assumptions, parameters, and perspective are part of context structure.
- Giunchiglia and Serafini 1994: local model semantics motivates keeping contextual vocabularies local and relating them by explicit mappings rather than forcing one global language.
- McCarthy and Buvac 1997: nested context statements are a type-level requirement even where full nested operational reasoning is deferred.
- Bozzato, Eiter, and Serafini 2018: CKR justifiable exceptions make context exceptions evidence-bearing. WS-C owns the full defeasible reasoning layer, but WS-A provides the structured contexts and lifting surface it needs.
- Clark 2014: a micropublication is a scientific-claim bundle with evidence, support or challenge relations, attribution, and provenance. propstore uses that shape for source finalization and canonical promotion.

These notes cite the processed paper artifacts under `papers/`. This closure slice did not perform a fresh page-image reread.

## Implemented Shape

`ContextDocument` carries:

- stable identity and description
- structured assumptions
- parameters
- perspective
- explicit lifting rules

`ClaimDocument` requires a `context: ContextReference`. Nested `ist` propositions are represented at the document boundary with atomic and recursive proposition variants, so storage can express `ist(c1, ist(c2, p))` without inventing a second claim language.

`context_hierarchy.py` is gone. Runtime context activation uses `context_lifting.py` and `LiftingSystem`; authored contexts do not inherit visibility by ancestry. Context movement is represented as typed lifting decisions over `ist(source, proposition) -> ist(target, proposition)`. A lifted assertion is materialized only for a `lifted` decision; `blocked` and `unknown` decisions remain provenance and inspection records.

## Micropublication Flow

Source branches author and finalize micropublication bundles:

1. `pks source propose-claim ... --context CTX` writes context-qualified source claims.
2. `pks source finalize SOURCE` composes `micropubs.yaml` from the source-local claim, evidence, stance, assumption, and provenance material.
3. `pks source promote SOURCE` writes canonical `micropubs/{source}.yaml` atomically with valid promoted claim members.
4. The sidecar build creates `micropublication` and `micropublication_claim` tables from canonical micropublication artifacts.
5. `WorldQuery.all_micropublications()` returns typed `ActiveMicropublication` objects for runtime reasoning.

The CLI inspection surface is:

```bash
uv run pks micropub bundle SOURCE
uv run pks micropub show ARTIFACT_ID
uv run pks micropub lift ARTIFACT_ID --target-context TARGET_CONTEXT
```

## ATMS Semantics

ATMS labels now include both assumptions and contexts:

```python
EnvironmentKey(
    assumption_ids=("assumption:a",),
    context_ids=("ctx_lab_run",),
)
```

Context nodes are explicit antecedents. A context-scoped claim is not unconditional merely because it is visible in a bound world; its label records the supporting context ID. Label union, subsumption, normalization, nogood pruning, and minimality include the context dimension.

Micropublication nodes combine support from:

- the micropublication context node
- every member claim node

This makes a micropublication supported only under the environments that support the whole bundle. `ATMSEngine.supported_micropub_ids()` reports supported bundles, and `ATMSEngine.micropub_label(id)` returns the bundle label.

## Non-Davidsonian Composition

The Phase 3 position remains intact: there is no `Event` type and no event-identity primitive. Contexts can name description clusters, but those clusters are render-time products of arguments over claims. `ist(c, p)` says that `p` holds in the described context; it does not say that `c` is an event individual. Clark-style micropublications then package the contextual claims, evidence, and provenance needed to argue about that cluster.

This is why context lifting and micropublication support are exact, authored surfaces. propstore can later add stronger WS-C CKR exception reasoning over the same substrate without backfilling a visibility hierarchy or reifying event identity.

## Verification

Primary gates for this substrate:

- `tests/test_context_lifting_phase4.py`
- `tests/test_micropublications_phase4.py`
- `tests/test_labels_properties.py`
- `tests/test_atms_engine.py`

These cover context identity and lifting, required claim contexts, nested `ist` parsing and round trip, source and canonical micropublication documents, micropublication CLI behavior, ATMS context-label algebra, and micropublications as ATMS nodes.
