# ID Papers

Reading list for identifier design in propstore.

Working question:

- What ID model should propstore use for claims, concepts, and other first-class artifacts so independently built repos can merge safely?

Suggested design direction from this reading:

- `artifact_id` for immutable object identity
- namespaced `logical_id` for human/source-facing identity
- explicit equivalence or reconciliation links for separately minted-but-semantically-same objects

## Priority 1

### 1. Unique, Persistent, Resolvable: Identifiers as the Foundation of FAIR

- Authors: Nick Juty, Sarala M. Wimalaratne, Stian Soiland-Reyes, John Kunze, Carole A. Goble, Tim Clark
- Year: 2019
- DOI: https://doi.org/10.1162/dint_a_00025
- Open manuscript: https://pure.manchester.ac.uk/ws/files/112037636/Unique_Persistent_Resolvable_accepted.pdf
- Why grab it:
  - best high-level paper on identifier requirements
  - separates uniqueness, persistence, resolvability, scope, indirection, and metadata
  - directly relevant to how propstore IDs should look on the outside

### 2. Trusty URIs: Verifiable, Immutable, and Permanent Digital Artifacts for Linked Data

- Authors: Tobias Kuhn, Michel Dumontier
- Year: 2014
- arXiv: https://arxiv.org/abs/1401.5775
- Why grab it:
  - strongest paper here for content-addressed artifact identity
  - useful for immutable artifact/version IDs
  - useful warning that content hashes are good for artifacts, but not sufficient for logical identity

### 3. The sameAs Problem: A Survey on Identity Management in the Web of Data

- Authors: Joe Raad, Nathalie Pernelle, Fatiha Saïs
- Year: 2019
- arXiv: https://arxiv.org/abs/1907.10528
- Survey page: https://www.semantic-web-journal.net/content/sameas-problem-survey-identity-management-web-data
- Why grab it:
  - directly about the “two things minted separately, but maybe actually the same thing” problem
  - relevant if propstore gets `same_as`, reconciliation, clustering, or canonicalization layers

## Priority 2

### 4. The Anatomy of a Nanopublication

- Authors: Paul Groth, Andrew Gibson, Jan Velterop
- Year: 2010
- Local status: already in collection as [Groth_2010_AnatomyNanopublication](C:/Users/Q/code/propstore/papers/Groth_2010_AnatomyNanopublication)
- Why keep it in the ID reading stack:
  - granular scientific assertions with provenance
  - very relevant for what a claim object is and what should travel with its identity
  - useful precedent for statement-level scientific objects rather than only document-level identifiers

### 5. Making Digital Artifacts on the Web Verifiable and Reliable

- Authors: Tobias Kuhn, Michel Dumontier
- Year: 2015
- arXiv: https://arxiv.org/abs/1507.01697
- Why grab it:
  - extended trusty-URI treatment
  - more useful than the shorter paper if we want artifact verification and long-term reproducibility of referenced objects

### 6. Reliable Granular References to Changing Linked Data

- Authors: Tobias Kuhn, Egon Willighagen, Chris Evelo, Nuria Queralt-Rosinach, Emilio Centeno, Laura I. Furlong
- Year: 2017
- arXiv: https://arxiv.org/abs/1708.09193
- Why grab it:
  - important if propstore wants IDs that survive evolving datasets and still support precise references
  - highly relevant to branch/import/merge worlds where the larger corpus changes over time

## Priority 3

### 7. Joint Declaration of Data Citation Principles

- Authors: Data Citation Synthesis Group
- Year: 2014
- URL: https://force11.org/info/joint-declaration-of-data-citation-principles-final
- Why grab it:
  - not a paper in the same sense, but too relevant to skip
  - gives the citation-grade constraints: persistence, specificity, verifiability, attribution
  - useful for deciding what “referencing a claim/artifact correctly” should mean

### 8. The FAIR Guiding Principles for Scientific Data Management and Stewardship

- Authors: Mark D. Wilkinson et al.
- Year: 2016
- DOI: https://doi.org/10.1038/sdata.2016.18
- Why grab it:
  - broad, but identifiers are foundational in it
  - useful for checking that propstore ID design does not optimize locally and fail at interoperability

## Nice-To-Have Extras

These are not all “ID papers” strictly speaking, but they are likely useful once the core list is in hand.

### 9. Cool URIs for the Semantic Web

- Author: Leo Sauermann, Richard Cyganiak
- Year: 2008
- URL: https://www.w3.org/TR/cooluris/
- Why grab it:
  - practical URI design guidance
  - useful if propstore exposes resolvable external IDs or landing pages

### 10. RFC 3986: Uniform Resource Identifier (URI): Generic Syntax

- Authors: Tim Berners-Lee, Roy Fielding, Larry Masinter
- Year: 2005
- URL: https://www.rfc-editor.org/rfc/rfc3986
- Why grab it:
  - not a paper, but the base standard
  - worth having if propstore formalizes resolvable IDs or namespace syntax

## Suggested Grab Order

1. Juty et al. 2019
2. Kuhn and Dumontier 2014
3. Raad et al. 2019
4. Groth et al. 2010
5. Kuhn et al. 2017
6. Kuhn and Dumontier 2015
7. JDDCP
8. FAIR

## What Each One Answers

- Juty et al.:
  - what makes an identifier good in infrastructure terms
- Trusty URIs papers:
  - when to use immutable/content-verifiable IDs
- sameAs survey:
  - what to do when identity must be reconciled rather than assumed
- Nanopublication:
  - what a granular scientific assertion object should carry with it
- Reliable Granular References:
  - how to refer stably into changing corpora
- JDDCP + FAIR:
  - what good scientific references must support operationally

## Propstore Translation

If this reading stack holds up, propstore should probably avoid choosing exactly one ID.

The likely end state is:

- `artifact_id`: immutable identity of the stored object
- `logical_id`: namespaced source-facing identity such as `paper_slug:claim1`
- provenance/version IDs: git/blob/hash level identity for serialized states
- reconciliation links: explicit relations for semantic equivalence across independently minted objects
