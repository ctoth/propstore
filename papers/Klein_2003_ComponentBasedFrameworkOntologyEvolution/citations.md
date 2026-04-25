# Citations

## Reference List

[1] J. Banerjee, W. Kim, H.-J. Kim, and H. F. Korth. Semantics and implementation of schema evolution in object-oriented databases. In *Proc. of the ACM SIGMOD Conf.*, 1987.

[2] J. Heflin and J. Hendler. Dynamic ontologies on the web. In *Proceedings of the 17th National Conference on Artificial Intelligence (AAAI-2000)*, Austin, TX, 2000. AAAI/MIT Press.

[3] M. Klein, A. Kiryakov, D. Ognyanov, and D. Fensel. Finding and characterizing changes in ontologies. In *21st International Conference on Conceptual Modeling (ER 2002)*, Tampere, Finland, October 2002.

[4] M. Kifer, G. Lausen, and J. Wu. Logical foundations of object-oriented and frame-based languages. *Journal of the ACM*, 42(4):741–843, July 1995.

[5] W. Nejdl, B. Wolf, C. Qu, S. Decker, M. Sintek, A. Naeve, M. Nilsson, M. Palmer, and T. Risch. Edutella: a p2p networking infrastructure based on RDF. In *Proceedings of the 11th International World Wide Web Conference (WWW2002)*, 2002.

[6] N. Noy and M. Klein. PROMPTDIFF: A fixed-point algorithm for comparing ontology versions. In *18th National Conference on Artificial Intelligence (AAAI 2002)*, Edmonton, Canada, 2002.

[7] N. F. Noy and M. Klein. Ontology evolution: Not the same as schema evolution. *Knowledge and Information Systems*, 2003.

[8] D. E. Oliver, Y. Shahar, E. H. Shortliffe, and M. A. Musen. Representation of change in controlled medical terminologies. *Artificial Intelligence in Medicine*, 15:53–76, 1999.

[9] H. S. Pinto and J. P. Martins. Evolving ontologies in distributed and dynamic settings. In *8th International Conference on Principles of Knowledge Representation and Reasoning (KR2002)*, Toulouse France, 2002.

[10] L. Stojanovic, A. Maedche, B. Motik, and N. Stojanovic. User-driven ontology evolution management. In *13th International Conference on Knowledge Engineering and Knowledge Management (EKAW02)*, Sigüenza, Spain, Oct. 1–4, 2002.

[11] Y. Sure, M. Erdmann, J. Angele, S. Staab, R. Studer, and D. Wenke. OntoEdit: Collaborative ontology development for the Semantic Web. In *International Semantic Web Conference (ISWC 2002)*, volume 2342 of *LNCS*, pages 221–235. Springer-Verlag, 2002.

## Key Citations for Follow-up

- **[3] Klein, Kiryakov, Ognyanov, Fensel — "Finding and characterizing changes in ontologies" (ER 2002)**: The structural-diff side of the framework — companion paper that develops the technique for detecting change between two ontology versions. Read this if propstore needs a structural-diff implementation between two source-branch states.

- **[6] Noy & Klein — PROMPTDIFF (AAAI 2002)**: Fixed-point algorithm for diffing ontology versions. Concrete algorithm with termination guarantees; would inform an implementation of propstore's structural-diff layer.

- **[7] Noy & Klein — "Ontology evolution: Not the same as schema evolution" (KAIS 2003)**: Sister paper that argues ontology evolution requires *different* primitives than database schema evolution because semantics, not just structure, must be preserved. Important for justifying why propstore can't reuse off-the-shelf schema-migration tooling.

- **[10] Stojanovic et al. — "User-driven ontology evolution management" (EKAW 2002)**: Adds the user-intent dimension that the K representation gestures at but does not develop. Read if propstore needs to formalize the K layer beyond free text.

- **[1] Banerjee et al. — "Semantics and implementation of schema evolution in object-oriented databases" (SIGMOD 1987)**: Foundational paper for typed, component-targeted change operations; the conceptual ancestor of the basic-change-operation hierarchy in this paper. Useful for justifying the design lineage when wiring `ClaimConceptLinkDeclaration` into propstore.
