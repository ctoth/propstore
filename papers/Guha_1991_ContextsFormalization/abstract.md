# Abstract

## Original Text (Verbatim)

Logical formulas used in representation are traditionally supposed to be objective, decontextualized truths. In reality, they have many contextual aspects. Representations often assume a context of use. This thesis attempts to remedy this by formalizing and developing several applications for contexts, incorporating contexts as rich objects in a first-order framework and extending the logic as required.

*(Per metadata.json, as extracted when the PDF was first retrieved. No prose "Abstract" section appears on the thesis title or contents pages; the abstract above is the standard semantic-scholar/thesis-record abstract.)*

---

## Our Interpretation

Guha takes McCarthy's informal `ist(c, p)` proposal and turns it into a full formal apparatus — syntax, semantics, proof theory, default rules, and scope machinery — then demonstrates the resulting "context toolkit" against 21 real problems encountered during Cyc's development: implicit time handling, static/dynamic theory mixing, hypothetical objects, polysemy, perspectives, granularity, database integration, and mutual inconsistency. The thesis is the canonical operational grounding for treating contexts as first-class logical objects, which is exactly the architectural commitment the propstore project makes. For implementation, Guha provides the formal vocabulary (ist, lifting, DCR/DCT, abnormality, presentIn, derivedContexts, articulation axioms) propstore uses when reasoning about source branches, microtheory-style knowledge partitioning, and render-time resolution of rival claims without premature canonicalization.
