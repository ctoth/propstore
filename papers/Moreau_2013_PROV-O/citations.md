# Citations

## Reference List

### Normative references (Section G.1, p.68-69)

- **[IRI]** M. Duerst, M. Suignard. *Internationalized Resource Identifiers (IRI).* January 2005. Internet RFC 3987. URL: http://www.ietf.org/rfc/rfc3987.txt
- **[OWL2-OVERVIEW]** W3C OWL Working Group. *OWL 2 Web Ontology Language: Overview.* 27 October 2009. W3C Recommendation. URL: http://www.w3.org/TR/2009/REC-owl2-overview-20091027/
- **[PROV-CONSTRAINTS]** James Cheney; Paolo Missier; Luc Moreau; eds. *Constraints of the PROV Data Model.* 30 April 2013, W3C Recommendation. URL: http://www.w3.org/TR/2013/REC-prov-constraints-20130430/
- **[PROV-DM]** Luc Moreau; Paolo Missier; eds. *PROV-DM: The PROV Data Model.* 30 April 2013, W3C Recommendation. URL: http://www.w3.org/TR/2013/REC-prov-dm-20130430/
- **[PROV-N]** Luc Moreau; Paolo Missier; eds. *PROV-N: The Provenance Notation.* 30 April 2013, W3C Recommendation. URL: http://www.w3.org/TR/2013/REC-prov-n-20130430/
- **[RDF-CONCEPTS]** Graham Klyne; Jeremy J. Carroll. *Resource Description Framework (RDF): Concepts and Abstract Syntax.* 10 February 2004, W3C Recommendation. URL: http://www.w3.org/TR/2004/REC-rdf-concepts-20040210
- **[RFC2119]** S. Bradner. *Key words for use in RFCs to Indicate Requirement Levels.* March 1997. Internet RFC 2119. URL: http://www.ietf.org/rfc/rfc2119.txt
- **[XMLSCHEMA11-2]** Henry S. Thompson; et al. *W3C XML Schema Definition Language (XSD) 1.1 Part 2: Datatypes.* 5 April 2012, W3C Recommendation. URL: http://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/

### Informative references (Section G.2, p.69)

- **[LD-Patterns-QR]** Leigh Dodds; Ian Davis. *Qualified Relation.* Modified 31 May 2012, accessed 01 June 2012. URL: http://patterns.dataincubator.org/book/qualified-relation.html
- **[OWL2-PRIMER]** Pascal Hitzler; Markus Krötzsch; Bijan Parsia; Peter F. Patel-Schneider; Sebastian Rudolph. *OWL 2 Web Ontology Language: Primer.* 27 October 2009. W3C Recommendation. URL: http://www.w3.org/TR/2009/REC-owl2-primer-20091027/
- **[PROV-AQ]** Graham Klyne; Paul Groth; eds. *Provenance Access and Query.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-aq-20130430/
- **[PROV-DC]** Daniel Garijo; Kai Eckert; eds. *Dublin Core to PROV Mapping.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-dc-20130430/
- **[PROV-DICTIONARY]** Tom De Nies; Sam Coppens; eds. *PROV-Dictionary: Modeling Provenance for Dictionary Data Structures.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-dictionary-20130430/
- **[PROV-LINKS]** Luc Moreau; Timothy Lebo; eds. *Linking Across Provenance Bundles.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-links-20130430/
- **[PROV-OVERVIEW]** Paul Groth; Luc Moreau; eds. *PROV-OVERVIEW: An Overview of the PROV Family of Documents.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-overview-20130430/
- **[PROV-PRIMER]** Yolanda Gil; Simon Miles; eds. *PROV Model Primer.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-primer-20130430/
- **[PROV-SEM]** James Cheney; ed. *Semantics of the PROV Data Model.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-sem-20130430/
- **[PROV-XML]** Hook Hua; Curt Tilmes; Stephan Zednik; eds. *PROV-XML: The PROV XML Schema.* 30 April 2013, W3C Note. URL: http://www.w3.org/TR/2013/NOTE-prov-xml-20130430/
- **[RDF-SCHEMA]** Dan Brickley; Ramanathan V. Guha. *RDF Vocabulary Description Language 1.0: RDF Schema.* 10 February 2004, W3C Recommendation. URL: http://www.w3.org/TR/2004/REC-rdf-schema-20040210
- **[TRIG]** Chris Bizer; Richard Cyganiak. *The TriG Syntax.* Modified 30 July 2007, accessed 05 November 2012. URL: http://wifo5-03.informatik.uni-mannheim.de/bizer/trig/

## Key Citations for Follow-up

1. **[PROV-DM]** — *This is the required companion paper.* PROV-O is a direct OWL encoding of PROV-DM; understanding propstore's provenance model requires reading PROV-DM to see which aspects are inherited vs. elaborated in PROV-O. Already listed as P2 candidate in the semantic-substrate plan; if not already, should be.
2. **[PROV-CONSTRAINTS]** — Defines which PROV graphs are well-formed. Any propstore implementation that emits PROV-O MUST respect these constraints or produce graphs that PROV-aware consumers will reject. Essential for the validation layer of propstore's provenance subsystem.
3. **[PROV-SEM]** — First-order-logic declarative semantics. Bridges PROV to formal reasoning, which is directly relevant to propstore's argumentation layer (ASPIC+ / Dung AF) over provenance-bearing claims.
4. **[LD-Patterns-QR]** — The "Qualified Relation" Linked Data pattern. PROV-O's qualification pattern is an instantiation. propstore can reuse this pattern more broadly (e.g., qualifying concept-merge proposals, qualifying stance extractions) without coupling to PROV-O specifically.
5. **[PROV-PRIMER]** — Informal introduction that uses the same crime-chart scenario as PROV-O's running examples. Cheaper on-ramp for new propstore contributors who need to understand provenance intuitions before hitting PROV-O's formal cross-reference.
