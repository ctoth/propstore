# Abstract

## Original Text (Verbatim)

The Semantic Web consists of many RDF graphs nameable by URIs. This paper extends the syntax and semantics of RDF to cover such Named Graphs. This enables RDF statements that describe graphs, which is beneficial in many Semantic Web application areas. As a case study, we explore the application area of Semantic Web publishing: Named Graphs allow publishers to communicate assertional intent, and to sign their graphs; information consumers can evaluate specific graphs using task-specific trust policies, and act on information from those Named Graphs that they accept. Graphs are trusted depending on: their content; information about the graph; and the task the user is performing. The extension of RDF to Named Graphs provides a formally defined framework to be a foundation for the Semantic Web trust layer.

---

## Our Interpretation

Provides the minimal formal machinery needed to talk *about* RDF graphs — their name, provenance, authority, signatures, and propositional-attitude status — without inventing new modal logic or forcing a richer context theory. The key finding is that just *naming* graphs (making them first-class URI-addressable entities) is sufficient to carry provenance, digital signatures, and consumer-side trust policies; complex context semantics are dispensable. Relevant because propstore keeps provenance alongside claims and defers trust/conflict resolution to render time — Named Graphs + SWP are the canonical formal grounding for that pattern.
