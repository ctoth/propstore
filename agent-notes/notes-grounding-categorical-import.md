# Categorical import research lane checkpoint

## Current findings

- Institutions justify typed signatures, sentences, models, signature/theory morphisms, satisfaction-preserving logic translations, and theory colimits. A translation is not an identity assertion: it preserves declared structure or entailment under a stated model reduct.
- DOL distinguishes native-module import, non-logical alignment, logic translation, theory interpretation, conservative/definitional extension, and definable equivalence. Each relation has different validation obligations and must retain its exact logic/translation versions.
- Ologs justify categories as equation-bearing schemas, instances as functors to `Set`, schema translations as functors, data transformations as natural transformations, pullbacks for compatibility/intersection, and pushouts for explicit quotienting/gluing. Pushout quotienting can collapse more identity than intended.
- For Propstore, the emerging boundary is: immutable imported snapshots preserve source identity; typed alignment proposals carry relation, confidence, provenance, and evidence; verified interpretations carry signature/symbol maps and proof obligations; equivalence witnesses remain non-merging; canonical merge is a separate reviewed mutation.

## Observations

- “Same vocabulary” and “same denotation” are not categorical conclusions. Functoriality supplies compositional coherence, while equivalence or identity needs stronger evidence and an explicit semantic claim.
- Universal constructions are justified only over valid typed diagrams. A pushout cannot repair weak or ambiguous mapping legs; it freely propagates the identifications they assert.

## State

- Fully read Institutions, both DOL notes, and Ologs.
- Remaining assigned papers: Functorial Data Migration, Relational Foundations, Algebraic Data Integration, Algebraic Databases, Brown, Hitzler, Zimmermann, and LogMap.
- Current Propstore owners and current official implementation status still need inspection.

## Blocker

- None.

## Next action

- Finish the assigned paper corpus, inspect current concept/alignment/equivalence/same-as/Lemon owners read-only, verify active external implementations from primary sources, then write and audit `reports/research-grounding-architecture-categorical-import.md`.
