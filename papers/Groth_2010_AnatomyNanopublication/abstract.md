# Abstract

## Original Text (Verbatim)

As the amount of scholarly communication increases, it is increasingly difficult for specific core scientific statements to be found, connected and curated. Additionally, the redundancy of these statements in multiple fora makes it difficult to determine attribution, quality and provenance. To tackle these challenges, the Concept Web Alliance has promoted the notion of nanopublications (core scientific statements with associated context). In this document, we present a model of nanopublications along with a Named Graph/RDF serialization of the model. Importantly, the serialization is defined completely using already existing community-developed technologies. Finally, we discuss the importance of aggregating nanopublications and the role that the Concept Wiki plays in facilitating it.

Keywords: Semantic Web, rich RDF-triples, disambiguation, publication.

---

## Our Interpretation

The paper proposes that an individual scientific assertion, plus the minimum annotations needed to interpret it (provenance, attribution, approval), should itself be a citable publication - the "nanopublication" - and it exhibits a concrete RDF Named-Graph realization built entirely from pre-existing ontologies (SWAN, SWP, FOAF, TRIG) rather than new specifications. The design separates the statement graph from the annotation graph from the attribution graph, and introduces S-Evidence (all nanopublications referring to the same statement) as the aggregation unit over which reasoners and aggregators can operate. This is the direct antecedent of propstore's claim-plus-provenance substrate: the layered model, the authority-pluralism via SWP `assertedBy`, and the explicit non-commitment on a universal minimum-annotation set all line up with propstore's "never collapse disagreement in storage" discipline - while the paper's lack of any conflict or argumentation semantics is exactly the gap propstore's argumentation layer fills.
