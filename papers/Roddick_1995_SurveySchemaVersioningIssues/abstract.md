# Abstract

## Original Text (Verbatim)

Schema versioning is one of a number of related areas dealing with the same general problem - that of using multiple heterogeneous schemata for various database related tasks. In particular, schema versioning, and its weaker companion, schema evolution, deal with the need to retain current data and software system functionality in the face of changing database structure. Schema versioning and schema evolution offer a solution to the problem by enabling intelligent handling of any temporal mismatch between data and data structure. This survey discusses the modelling, architectural and query language issues relating to the support of evolving schemata in database systems. An indication of the future directions of schema versioning research are also given.

**Keywords:** Schema Evolution, Schema Versioning, Evolving Database Systems

---

## Our Interpretation

The paper's working problem is terminological discipline plus survey: the schema-evolution literature uses "modification," "evolution," and "versioning" inconsistently, and Roddick fixes the vocabulary with formal definitions and a four-point distinction between evolution and versioning. The key finding is that *evolution* is loss-free schema change while *versioning* additionally requires a retained history of named, retrospectively- and prospectively-queryable schema definitions; versioning further splits into partial (update-current-only) and full (update-anywhere) variants. For propstore the paper is foundational: it provides the canonical vocabulary the migration framework will reuse, and the symmetry / reversibility / algebraic-expressibility / temporal-substrate-optional constraints map directly onto propstore's non-commitment discipline.
