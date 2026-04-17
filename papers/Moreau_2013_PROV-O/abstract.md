# Abstract

## Original Text (Verbatim)

The PROV Ontology (PROV-O) expresses the PROV Data Model [PROV-DM] using the OWL2 Web Ontology Language (OWL2) [OWL2-OVERVIEW]. It provides a set of classes, properties, and restrictions that can be used to represent and interchange provenance information generated in different systems and under different contexts. It can also be specialized to create new classes and properties to model provenance information for different applications and domains. The PROV Document Overview describes the overall state of PROV, and should be read before other PROV documents.

The namespace for all PROV-O terms is `http://www.w3.org/ns/prov#`.

The OWL encoding of the PROV Ontology is available [at the W3C].

---

## Our Interpretation

PROV-O is the normative OWL2 encoding of the W3C PROV Data Model. It gives an RDF-consumable vocabulary of three core classes (Entity, Activity, Agent), a dozen binary relations among them (wasGeneratedBy, used, wasDerivedFrom, etc.), and a *qualification pattern* that lets asserters attach arbitrary metadata (time, location, role, plan) to any relation via an intermediate `prov:Influence` instance. The ontology is intentionally lightweight: it conforms to OWL 2 RL except for five explicit axioms, defines only two OWL inverses, and reserves the names of all other inverses in the PROV namespace to prevent interoperability fracture from parallel asserter-invented vocabularies.

For propstore, this is the P1 anchor paper for the provenance-type redesign: the Entity/Activity/Agent triad, the Bundle-as-named-provenance-set construct, and the qualification pattern all map directly onto propstore's need to carry rich, context-qualified provenance on every claim, stance, extraction, and merge proposal without forcing early commitment to a single canonical form.
