---
title: "The anatomy of a nanopublication"
authors: "Paul Groth, Andrew Gibson, Jan Velterop"
year: 2010
venue: "Information Services and Use"
doi_url: "https://doi.org/10.3233/ISU-2010-0613"
---

# The anatomy of a nanopublication

## One-Sentence Summary
Defines the core model and Named Graph/RDF serialization for nanopublications --- minimal citable units of scientific assertion bundled with provenance and attribution metadata.

## Problem Addressed
As scholarly communication volume grows, it becomes impractical to find, curate, and validate specific core scientific statements buried within full publications. Statements are redundantly published across multiple sources, making attribution, quality assessment, and provenance tracking difficult. The challenge is to define a minimal publication unit that makes individual scientific claims first-class, citable, attributable, and aggregatable objects on the Web.

## Key Contributions
- A layered conceptual model for nanopublications with precise definitions (concept, triple, statement, annotation, nanopublication, S-Evidence)
- A concrete serialization using RDF Named Graphs that maps directly to the conceptual model
- An annotation vocabulary drawing from SWAN and Semantic Web Publishing ontologies
- The S-Evidence aggregation mechanism for collecting all nanopublications about the same statement
- Three levels of compatibility for nanopublication adoption (Transformation Compatible, Format Compatible, Concept Wiki Compatible)

## Methodology
Conceptual modeling approach. The paper defines a layered ontology from atomic concepts up to aggregated evidence, then demonstrates how existing Semantic Web standards (Named Graphs, SWAN, SWP, FOAF) can realize the model without inventing new specifications.

## Core Model Definitions

1. **Concept** --- the smallest, unambiguous unit of thought; uniquely identifiable
2. **Triple** --- a tuple of three concepts (subject, predicate, object)
3. **Statement** --- a triple that is uniquely identifiable
4. **Annotation** --- a triple whose subject is a statement
5. **Nanopublication** --- a set of annotations referring to the same statement, containing a minimum set of community-agreed-upon annotations
6. **S-Evidence** --- all nanopublications that refer to the same statement

## Named Graph Realization

The model maps to Named Graphs (RDF extension assigning a URI to an RDF graph):

- Each triple is an RDF-triple
- Each statement is a separate Named Graph
- Each annotation has as its subject the URI of a Named Graph
- All annotations belonging to a nanopublication are part of the same Named Graph

Thus the simplest nanopublication has **two Named Graphs**: one containing the statement, one containing the annotations on that statement.

## Example Serialization (TRIG syntax)

```trig
@prefix swan: <http://swan.mindinformatics.org/ontologies/1.2/pav.owl> .
@prefix cw:   <http://conceptwiki.org/index.php/Concept>.
@prefix swp:  <http://www.w3.org/2004/03/trix/swp-1/>.
@prefix :     <http://www.example.org/thisDocument#> .

:G1  = { cw:malaria cw:isTransmittedBy cw:mosquitoes }

:G2  = { :G1 swan:importedBy cw:TextExtractor,
         :G1 swan:createdOn "2009-09-03"^^xsd:date,
         :G1 swan:authoredBy cw:BobSmith }

:G3  = { :G2 ann:assertedBy cw:SomeOrganization }

:G9  = { :G1 ann:isApprovedBy cw:JohnSmith }
:G10 = { :G9 ann:isAssertedBy cw:ApprovalTrackingSystem }
```

## Annotation Vocabulary

Drawn from SWAN ontology (provenance, annotation, versioning):
- `importedFromSource` --- where the statement was extracted from
- `importedBy` --- what entity imported the statement
- `authoredBy` --- who authored the statement

Uses Semantic Web Publishing ontology (SWP) for:
- `assertedBy` --- relates a Named Graph to an authority claiming it
- Digital signatures on graphs for verification

Extends FOAF for representing people, organizations, software agents.

## S-Evidence and Aggregation

S-Evidence = all nanopublications about the same statement. Key roles for aggregators:
- Find, filter, and combine evidence for a statement
- Ascertain veracity by examining annotations from multiple sources
- Allow reasoning on statements themselves vs. condensed annotation views

Practical requirement: publishers should use the same identifiers for statements and concepts (Linked Data principles). The Concept Wiki provides a centralized repository of unambiguous concept URIs.

## Three Compatibility Levels

1. **Transformation Compatible** --- data can be transformed to CWA format (tool exists to perform transformation)
2. **Format Compatible** --- uses CWA model and endorsed serialization
3. **Concept Wiki Compatible** --- format compatible AND uses only Concept Wiki identifiers

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Named Graphs per nanopub | - | count | 2 | 2+ | minimum: statement graph + annotation graph |

## Implementation Details
- Named Graphs are not yet a W3C standard but widely supported by quad stores (Virtuoso, 4store, NG4J)
- TRIG syntax used for serialization examples
- Concept Wiki provides canonical concept URIs for interoperability
- No new specifications required --- built entirely on existing Semantic Web infrastructure

## Figures of Interest
- **Fig 1 (page 3):** The nanopublication model showing layered hierarchy from Concepts through Triples, Statements, Annotations, to Nanopublications, with S-Evidence aggregation
- **Fig 2 (page 5):** Concrete TRIG example of a nanopublication about "malaria is transmitted by mosquitoes"

## Results Summary
Conceptual paper; no empirical evaluation. Demonstrates feasibility through the Concept Wiki implementation and compatibility with existing Semantic Web standards.

## Limitations
- No formal evaluation or user study
- Named Graphs were not yet a W3C standard at time of publication
- Minimum annotation set left to community agreement (not specified)
- No discussion of versioning or retraction of nanopublications
- Aggregation relies on publishers using shared identifiers (a coordination challenge)

## Testable Properties
- A valid nanopublication must contain at least 2 Named Graphs (statement + annotations)
- Every annotation triple must have a statement URI as its subject
- S-Evidence for a statement S = the set of all nanopublications whose statement graph contains S
- Nanopublication identity is determined by its statement + annotation content

## Relevance to Project
The nanopublication model is structurally analogous to the propstore's claim/micropublication architecture: both decompose scientific assertions into atomic, identifiable, annotatable units with provenance. The Named Graph serialization provides a concrete RDF representation that could serve as an interchange format. The S-Evidence aggregation concept maps directly to the propstore's need to collect and compare multiple sources of support for the same proposition.

## Open Questions
- [ ] How does nanopublication identity work when the same statement appears with different annotations?
- [ ] What is the minimum annotation set that the CWA working group converged on?
- [ ] How does this compare to the Clark 2014 micropublication model already in the collection?

## Collection Cross-References

### Already in Collection
- (none — no cited papers are in the collection yet)

### Cited By (in Collection)
- [[Clark_2014_Micropublications]] — cites this as a "statement-based model comparison" for nanopublications vs micropublications

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] — **Strong.** Both papers define atomic scientific assertion models with layered provenance. Groth's nanopublication (concept→triple→statement→annotation→nanopublication) maps structurally to Clark's micropublication (Claim→Statement→Support→Attribution). Clark's model adds argumentation structure (supports/challenges) that Groth lacks; Groth's model provides a concrete RDF/Named Graph serialization that Clark's lacks. Complementary formalizations of the same core idea.

## Related Work Worth Reading
- Carroll JJ, Bizer C, Hayes P, Stickler P: Named graphs, provenance and trust (2005) - RDF named graph foundations [already a lead from Clark_2014]
- Ciccarese P et al: The SWAN biomedical discourse ontology (2008) - SWAN ontology details [already a lead from Clark_2014]
- Mons B, Velterop J: Nano-publication in the e-science era (SWASD 2009) - earlier concept formulation
- Samwald M, Stenzhorn H: Simple ontology-based representation of biomedical statements through fine-granular entity tagging (Bio-Ontologies 2009)
