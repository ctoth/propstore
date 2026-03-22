---
title: "The anatomy of a nanopublication"
authors: "Paul Groth, Andrew Gibson, Jan Velterop"
year: 2010
venue: "Information Services and Use"
doi_url: "https://doi.org/10.3233/ISU-2010-0613"
---

# The anatomy of a nanopublication

## One-Sentence Summary
Defines the core model and Named Graph/RDF serialization for nanopublications --- minimal citable units of scientific assertion bundled with provenance and attribution metadata. *(p.51)*

## Problem Addressed
As scholarly communication volume grows, it becomes impractical to find, curate, and validate specific core scientific statements buried within full publications. *(p.51)* Statements are redundantly published across multiple sources, making attribution, quality assessment, and provenance tracking difficult. *(p.51)* The challenge is to define a minimal publication unit that makes individual scientific claims first-class, citable, attributable, and aggregatable objects on the Web. *(p.51)*

## Key Contributions
- A layered conceptual model for nanopublications with precise definitions (concept, triple, statement, annotation, nanopublication, S-Evidence) *(p.52)*
- A concrete serialization using RDF Named Graphs that maps directly to the conceptual model *(p.53)*
- An annotation vocabulary drawing from SWAN and Semantic Web Publishing ontologies *(p.54)*
- The S-Evidence aggregation mechanism for collecting all nanopublications about the same statement *(p.52)*
- Three levels of compatibility for nanopublication adoption (Transformation Compatible, Format Compatible, Concept Wiki Compatible) *(p.55--56)*

## Methodology
Conceptual modeling approach. The paper defines a layered ontology from atomic concepts up to aggregated evidence, then demonstrates how existing Semantic Web standards (Named Graphs, SWAN, SWP, FOAF) can realize the model without inventing new specifications. *(p.52--53)*

## Core Model Definitions

1. **Concept** --- the smallest, unambiguous unit of thought; uniquely identifiable *(p.52)*
2. **Triple** --- a tuple of three concepts (subject, predicate, object) *(p.52)*
3. **Statement** --- a triple that is uniquely identifiable *(p.52)*
4. **Annotation** --- a triple whose subject is a statement *(p.52)*
5. **Nanopublication** --- a set of annotations referring to the same statement, containing a minimum set of community-agreed-upon annotations *(p.52)*
6. **S-Evidence** --- all nanopublications that refer to the same statement *(p.52)*

The paper notes that different communities may require different sets of annotations beyond the core, allowing for subtypes of nanopublications (e.g. curated, observational, hypothetical) as suggested by reference [4]. *(p.52)*

## Basic Requirements for Nanopublication Format

The model places the following basic requirements on any format: *(p.52--53)*
- The ability to uniquely identify a concept *(p.52)*
- The ability to uniquely identify a statement *(p.52)*
- The ability to refer to all uniquely identified entities *(p.53)*

The paper emphasizes that community agreement on the vocabulary of annotations is more important than the specific format chosen. *(p.53)*

## Named Graph Realization

The model maps to Named Graphs (RDF extension assigning a URI to an RDF graph): *(p.53)*

- Each triple is an RDF-triple *(p.53)*
- Each statement is a separate Named Graph *(p.53)*
- Each annotation has as its subject the URI of a Named Graph *(p.53)*
- All annotations belonging to a nanopublication are part of the same Named Graph *(p.53)*

Thus the simplest nanopublication has **two Named Graphs**: one containing the statement, one containing the annotations on that statement. *(p.53)*

Named Graphs are not yet a W3C standard but are widely supported by quad stores (Virtuoso, 4store, NG4J). *(p.53)*

## Annotations (Section 4)

The paper adopts the SWAN ontology to describe the annotation vocabulary rather than inventing new terms. *(p.54)* SWAN enables describing complex associations between concepts as a SWAN Research Statement. *(p.54)* The key capabilities for nanopublications are to determine the overlapped ontologies, specifically the provenance, annotation and versioning of the SWAN ontology. *(p.54)*

Examples of annotations provided: *(p.54)*
- `importedFrom/ce` --- identifies where the research statement was extracted from
- `importedBy` --- identifies what entity is responsible for importing a statement
- `authoredBy` --- identifies the author of a research statement

The paper also notes that SWAN extends FOAF, so people, organizations and software agents can be represented. A system should understand the subclasses of FOAF Agent such as Person, Organization, and Group. *(p.54)*

## Attribution, Review, Citation (Section 5)

Annotations provide a mechanism to describe information about a statement: who authored it, when, what software created it, etc. *(p.54)* Uses include: *(p.54)*
- Allowing a reviewer to approve or cite a nanopublication
- Enabling claims of attribution (e.g., to select a nanopublication as a whole, for citation)

The paper proposes using the Semantic Web Publishing (SWP) ontology for this purpose. *(p.54)* SWP provides an `assertedBy` relationship that relates a particular Named Graph to an entity (a URI, an authority). *(p.54)* An entity can state they asserted a nanopublication and its claims. *(p.54)* SWP also provides the capability to express digital signatures on each graph, which may be important for verifying claims. *(p.54)*

Multiple nanopublications about the same statement can be "asserted by" different accounts of the same statement. *(p.54)* This notion of different views or accounts of the same statement is inspired by the Open Provenance Model [5]. *(p.54)*

Attribution is essential to nanopublications; other metadata (e.g. review, citation, institutional association) may also be necessary but is left to community decision. *(p.54)*

## Example Serialization (TRIG syntax)

*(p.55)*

```trig
@prefix swan: <http://www.mindinfomatics.org/ontologies/1.2/pav.owl> .
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

The example shows a nanopublication about the statement "malaria is transmitted by mosquitoes," authored by Bob Smith, imported by a text extractor, created in September 2009, and asserted by SomeOrganization. *(p.55)* The example uses TRIG syntax (TriG) [9]. *(p.55)*

## S-Evidence and Aggregation

S-Evidence = all nanopublications about the same statement. *(p.52, p.55)* Key roles for aggregators:
- Find, filter, and combine evidence for a statement *(p.55)*
- Ascertain veracity by examining annotations from multiple sources *(p.55)*
- Allow reasoning on statements themselves vs. condensed annotation views *(p.55)*

Practical requirement: publishers should use the same identifiers for statements and concepts (Linked Data principles). The Concept Wiki provides a centralized repository of unambiguous concept URIs. *(p.55)*

A benefit of separating statements from their various annotations is that it allows reasoning on only statements, or only annotations, or only a condensed view of the statement and associated annotations. *(p.55)*

The Concept Web Alliance (CWA) is a non-profit organization whose mission is "to enable an open collaborative environment to jointly address the challenges associated with high volume scholarly and professional data production, storage, interoperability and analyses for knowledge discovery." *(p.52)*

## Three Compatibility Levels

*(p.55--56)*

1. **Transformation Compatible** --- data can be transformed to CWA format where a tool exists to perform the transformation *(p.55)*
2. **Format Compatible** --- these nanopublications use the CWA model and endorsed serialization *(p.55)*
3. **Concept Wiki Compatible** --- not only format compatible but also only use Concept Wiki identifiers *(p.56)*

Additionally, the Concept Wiki provides a place for users to easily create nanopublications. The Concept Wiki follows the principles of Linked Data and provides programmatic access to nanopublications following the CWA format. *(p.56)*

The paper mentions tools such as eLiXir (a simple conversion tool for representing annotated research statements with the SRK vocabulary [7]) and aLiXa (which allows users to easily extract information from existing Semantic Web data) that support nanopublications. *(p.56)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Named Graphs per nanopub | - | count | 2 | 2+ | p.53 | minimum: statement graph + annotation graph |

## Implementation Details
- Named Graphs are not yet a W3C standard but widely supported by quad stores (Virtuoso, 4store, NG4J) *(p.53)*
- TRIG syntax used for serialization examples *(p.55)*
- Concept Wiki provides canonical concept URIs for interoperability *(p.55)*
- No new specifications required --- built entirely on existing Semantic Web infrastructure *(p.53, p.56)*
- The CWA working group aims not to develop new specifications but instead to identify existing technology and formats that can be used for aggregating nanopublications *(p.56)*

## Figures of Interest
- **Fig 1 (p.53):** The nanopublication model showing layered hierarchy from Concepts through Triples, Statements, Annotations, to Nanopublications, with S-Evidence aggregation
- **Fig 2 (p.55):** Concrete TRIG example of a nanopublication about "malaria is transmitted by mosquitoes"

## Results Summary
Conceptual paper; no empirical evaluation. Demonstrates feasibility through the Concept Wiki implementation and compatibility with existing Semantic Web standards. *(p.55--56)*

## Arguments Against Prior Work

### Against Traditional Publications as Unit of Scholarly Communication *(p.51)*
- As the volume of scholarly communication grows, it becomes increasingly difficult to find specific core scientific statements within full publications *(p.51)*
- The statement itself --- a scientific assertion --- exists many times over in the published literature, redundantly published across multiple sources, making attribution, quality assessment, and provenance tracking difficult *(p.51)*
- Statements need to be taken into account in full view of their context, which increasingly becomes a practical impossibility as the number of relevant published articles keeps growing *(p.51)*

### Against Ad-Hoc Statement Extraction *(p.51--52)*
- It can be expected that the number of systems that facilitate the creation of statements will increase further, coming in the form of both processes designed to extract statements from existing material and systems that facilitate de novo statement creation *(p.52)*
- Newer standards like RDFa also facilitate this and integrate with current third-party content *(p.52)*
- However, these systems lack a common format for nanopublications that enables their aggregation and the correct preservation of associated provenance --- the paper argues for a standardized model rather than ad-hoc extraction *(p.52)*

### Against Inventing New Specifications *(p.53, 56)*
- The CWA working group aims not to develop new specifications but instead to identify existing technology and formats that can be used for aggregating nanopublications *(p.56)*
- The paper deliberately reuses existing ontologies (SWAN, SWP, FOAF) rather than creating new vocabularies, arguing that community agreement on annotation vocabulary is more important than the specific format *(p.53)*
- Named Graphs were specifically designed with use cases similar to nanopublications in mind --- provenance tracking and context definition --- so no new infrastructure is needed *(p.53)*

### Against Uncontextualized Scientific Claims *(p.51)*
- A statement can only be validated scientifically if you take into consideration its context *(p.51)*
- Traditionally, the context of a scientific statement is implicit in its immediate environment (the scientific publication), but the paper argues this must be made explicit and machine-readable through structured annotations *(p.51)*

## Design Rationale

### Why the layered model (concept -> triple -> statement -> annotation -> nanopublication) *(p.52)*
Each layer adds a new capability: concepts provide unambiguous identification, triples add relational structure, statements add unique identifiability (via URIs), annotations add metadata about statements, and nanopublications bundle annotations into citable units. The hierarchy ensures each layer is independently useful and composable. *(p.52)*

### Why Named Graphs for serialization *(p.53)*
Named Graphs provide exactly the capability needed: assigning a URI to an RDF graph so that statements about the graph (annotations) can reference it. Named Graphs were specifically designed for provenance tracking and context definition --- the same use cases nanopublications require. They are widely supported by existing quad stores (Virtuoso, 4store, NG4J) even though not yet a W3C standard. *(p.53)*

### Why SWAN ontology for annotations *(p.54)*
Rather than inventing new annotation terms, the paper adopts the SWAN (Semantic Web Applications in Neuromedicine) ontology, which already provides vocabulary for describing provenance, annotation, and versioning of research statements. SWAN also extends FOAF for representing people, organizations, and software agents. Reusing SWAN ensures compatibility with existing biomedical discourse tools. *(p.54)*

### Why SWP for attribution *(p.54)*
The Semantic Web Publishing (SWP) ontology provides an `assertedBy` relationship that relates a Named Graph to an authority. This enables multiple entities to independently assert the same nanopublication, and SWP supports digital signatures on each graph for verification. Attribution is essential to nanopublications --- it establishes who stands behind a claim. *(p.54)*

### Why S-Evidence as an aggregation concept *(p.52, 55)*
S-Evidence (all nanopublications about the same statement) enables evidence aggregation: finding, filtering, and combining multiple sources of support or challenge for a single scientific claim. Separating statements from annotations allows reasoning on statements alone, annotations alone, or condensed views. This is key to the nanopublication vision of enabling computational assessment of statement veracity. *(p.52, 55)*

### Why three compatibility levels *(p.55--56)*
Different publishers and communities have different levels of investment in Semantic Web infrastructure. The three levels (Transformation Compatible, Format Compatible, Concept Wiki Compatible) provide a gradual adoption path: even data that merely can be transformed into the format benefits from the ecosystem, while fully compatible nanopublications using Concept Wiki identifiers enable the richest aggregation and interoperability. *(p.55--56)*

### Why Concept Wiki for shared identifiers *(p.55--56)*
For nanopublication aggregation to work at scale, publishers must use the same identifiers for the same concepts and statements. The Concept Wiki provides a centralized repository of unambiguous concept URIs following Linked Data principles, solving the coordination problem of identifier alignment across publishers. *(p.55--56)*

## Limitations
- No formal evaluation or user study *(p.56)*
- Named Graphs were not yet a W3C standard at time of publication *(p.53)*
- Minimum annotation set left to community agreement (not specified) *(p.52, p.54)*
- No discussion of versioning or retraction of nanopublications *(p.56)*
- Aggregation relies on publishers using shared identifiers (a coordination challenge) *(p.55)*
- The paper acknowledges it may not be practical for all publishers to use the same identifiers, and that in the real world any Semantic Web resource can be used *(p.55)*

## Testable Properties
- A valid nanopublication must contain at least 2 Named Graphs (statement + annotations) *(p.53)*
- Every annotation triple must have a statement URI as its subject *(p.53)*
- S-Evidence for a statement S = the set of all nanopublications whose statement graph contains S *(p.52)*
- Nanopublication identity is determined by its statement + annotation content *(p.52)*
- A nanopublication must contain a minimum set of community-agreed-upon annotations *(p.52)*
- The SWP `assertedBy` relationship can carry digital signatures for verification *(p.54)*

## Relevance to Project
The nanopublication model is structurally analogous to the propstore's claim/micropublication architecture: both decompose scientific assertions into atomic, identifiable, annotatable units with provenance. The Named Graph serialization provides a concrete RDF representation that could serve as an interchange format. The S-Evidence aggregation concept maps directly to the propstore's need to collect and compare multiple sources of support for the same proposition.

## Open Questions
- [ ] How does nanopublication identity work when the same statement appears with different annotations?
- [ ] What is the minimum annotation set that the CWA working group converged on?
- [ ] How does this compare to the Clark 2014 micropublication model already in the collection?

## Collection Cross-References

### Already in Collection
- (none --- no cited papers are in the collection yet)

### Cited By (in Collection)
- [[Clark_2014_Micropublications]] --- cites this as a "statement-based model comparison" for nanopublications vs micropublications

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] --- **Strong.** Both papers define atomic scientific assertion models with layered provenance. Groth's nanopublication (concept->triple->statement->annotation->nanopublication) maps structurally to Clark's micropublication (Claim->Statement->Support->Attribution). Clark's model adds argumentation structure (supports/challenges) that Groth lacks; Groth's model provides a concrete RDF/Named Graph serialization that Clark's lacks. Complementary formalizations of the same core idea.

## Related Work Worth Reading
- Carroll JJ, Bizer C, Hayes P, Stickler P: Named graphs, provenance and trust (2005) - RDF named graph foundations [already a lead from Clark_2014] *(p.56, ref [1])*
- Ciccarese P et al: The SWAN biomedical discourse ontology (2008) - SWAN ontology details [already a lead from Clark_2014] *(p.56, ref [2])*
- Mons B, Velterop J: Nano-publication in the e-science era (SWASD 2009) - earlier concept formulation *(p.56, ref [4])*
- Samwald M, Stenzhorn H: Simple ontology-based representation of biomedical statements through fine-granular entity tagging (Bio-Ontologies 2009) *(p.56, ref [8])*
- Groza S, Handschuh S, Clark T, et al: A short survey of discourse representation models (Workshop on Semantic Web Applications in Scientific Discourse, ISWC 2009) *(p.56, ref [3])*
- Pasualt A, Ciccarese P, Greville J, et al: SWANSIOC: aligning scientific discourse representation and social semantics (Workshop on Semantic Web Applications in Scientific Discourse, ISWC 2009) *(p.56, ref [6])*
- Open Provenance Model *(p.54, ref [5])*
