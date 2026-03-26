# Paper Processing: Gabbay 2012 — Equational Approach to Argumentation Networks

**Date:** 2026-03-24

## Status: Claims extraction in progress

## Completed
- PDF retrieved via sci-hub (57 pages, valid)
- metadata.json updated with abstract, venue, volume, issue, pages
- abstract.md created
- description.md created
- citations.md created
- notes.md created

## Paper directory
`papers/Gabbay_2012_EquationalApproachArgumentationNetworks/`

## Concept registry findings
Relevant existing concepts:
- concept410: equational_semantics (already defined referencing Gabbay!)
- concept183: argumentation_framework
- concept412: complete_labelling
- concept202: complete_extension
- concept241: argument_strength
- ctx_abstract_argumentation: Dung's tradition context

Concepts that may need registering for claims:
- support_relation (exists)
- bipolar_argumentation_framework (exists)
- admissible_set (exists)
- preferred_extension (exists)
- stable_extension (exists)
- grounded_extension (exists)
- semi_stable_extension (exists)
- approximate_admissibility (new - not registered)
- higher_level_attack (new - not registered)
- transmission_factor (new - not registered)

## Next steps
1. Register missing concepts (approximate_admissibility, higher_level_attack, transmission_factor)
2. Write claims.yaml with equations, observations, mechanisms, comparisons
3. Validate claims
4. Write report to reports/paper-gabbay-2012.md

## Dependencies added to pyproject.toml
- arxiv, semanticscholar, pypdf (needed for paper retrieval scripts)
