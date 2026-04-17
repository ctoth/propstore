---
tags: [provenance, ontology, owl2, semantic-web, standards]
---
PROV-O is the W3C Recommendation that encodes the PROV Data Model as an OWL2 ontology, defining Entity/Activity/Agent classes plus a family of binary influence properties and a normative qualification pattern for attaching rich metadata to any provenance relation via intermediate `prov:Influence` instances.
The ontology is explicitly lightweight (five non-OWL-RL axioms, only two asserted inverses, but with a full name-reservation table for all other inverses) and groups its terms into three incremental tiers — Starting Point, Expanded, Qualified — so adopters can choose their level of detail.
It is the P1 provenance-foundations anchor for propstore's provenance-type redesign: the Entity/Activity/Agent/Bundle vocabulary and the qualification pattern map directly onto propstore's requirement that every claim, stance, extraction, and merge proposal carries rich, context-qualified provenance without premature commitment to a single canonical form.
