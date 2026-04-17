---
tags: [lemon, ontology-lexicon, rdf, semantic-web, frame-semantics]
---
Introduces the canonical lemon (Lexicon Model for Ontologies) — an RDF(S) model linking lexical entries to Semantic-Web ontologies via LexicalEntry / Form / LexicalSense / Reference, deliberately agnostic to the linguistic-category inventory and reusing external registries such as ISOcat, GOLD, or OLiA.
Contributes the core class graph, the lemon-LexInfo extension with OWL-composed subcategorization frames (reducing COMLEX's 163 frames to 36+4), and three worked experiments: WordNet→lemon conversion, auto-generating a FOAF lexicon at 81.5% entry accuracy, and merging the two with 69% reuse of WordNet entries.
Anchor paper for propstore's concept/semantic layer — the formal basis for the project's form/concept/condition model and its non-commitment design principle, where senses are explicitly not assumed finite or disjoint and category inventories are externalised rather than prescribed.
