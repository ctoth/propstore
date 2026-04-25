# Research: migration-framework

## Summary

For a migration framework in propstore, the strongest literature is not one paper but three adjacent lines of work: database schema evolution, bidirectional transformations, and ontology evolution. The database papers give you explicit migration operators, correctness criteria, and rewrite machinery for old reads/writes. The bidirectional-transformation papers give you invertibility and round-trip laws, which are the cleanest way to reason about non-lossy migrations. The ontology-evolution papers matter because propstore is not just moving columns around; it changes semantic identity surfaces, canonical forms, and provenance-bearing representations. The recommended shape for this project is an explicit migration framework with typed migration operations, declared preconditions/postconditions, provenance, and hard failures at the boundary rather than silent normalization.

## Approaches Found

### Operator-Based Schema Evolution
**Source:** https://doi.org/10.1007/s00778-012-0302-x  
**Description:** Treat migrations as compositions of named schema modification operators rather than arbitrary scripts.  
**Pros:** Clear audit trail, good fit for explicit migrations, supports reasoning about query/update rewriting.  
**Cons:** Best for structured schema changes; semantic reinterpretations still need domain-specific logic.  
**Complexity:** Medium

### Bidirectional Transformations / Lenses
**Source:** https://doi.org/10.1145/1142351.1142399  
**Description:** Define forward and backward mappings with round-trip laws so migrations can be reasoned about formally.  
**Pros:** Best foundation for invertibility, projections, read-through compatibility, and loss analysis.  
**Cons:** More theory-heavy; not every real migration is perfectly invertible.  
**Complexity:** High

### Ontology Evolution / Semantic Change Management
**Source:** https://doi.org/10.1017/S0269888908001367  
**Description:** Model changes as semantic operations over concepts, relations, identities, and version history, not just structural edits.  
**Pros:** Directly relevant when migrations change meaning, naming, canonicalization, or provenance semantics.  
**Cons:** Literature is broader and less implementation-concrete than database evolution work.  
**Complexity:** Medium

### Multi-Schema-Version Management
**Source:** https://doi.org/10.1007/s00778-018-0508-7  
**Description:** Keep multiple schema versions live at once and propagate writes between them.  
**Pros:** Useful if old and new clients must coexist for a while.  
**Cons:** Probably more than propstore wants if the architecture goal is direct cutover with no long-lived dual path.  
**Complexity:** High

## Key Papers

- [Roddick (1995)](https://doi.org/10.1016/0950-5849(95)91494-K) - Classic survey that cleanly separates schema evolution from schema versioning and frames the core architectural questions.
- [Curino, Moon, and Zaniolo (2008)](https://pubs.dbs.uni-leipzig.de/se/node/867) - PRISM workbench paper; introduces schema modification operators, automatic migration, legacy query rewriting, and provenance-aware documentation.
- [Curino, Moon, Deutsch, and Zaniolo (2013)](https://doi.org/10.1007/s00778-012-0302-x) - Most implementation-relevant database paper here; extends PRISM/PRISM++ with integrity constraints and update rewriting under schema evolution.
- [Velegrakis, Miller, and Popa (2004)](https://doi.org/10.1007/s00778-004-0136-2) - Mapping-consistency paper; important if propstore migrations need to preserve declared correspondences between old and new semantic surfaces.
- [Bohannon, Pierce, and Vaughan (2006)](https://doi.org/10.1145/1142351.1142399) - Relational lenses; the cleanest paper for round-trip laws and principled reasoning about updatable views and invertible transformations.
- [Flouris et al. (2008)](https://doi.org/10.1017/S0269888908001367) - Best survey for ontology change, versioning, and evolution tasks; useful for semantic, not just structural, migrations.
- [Zablith et al. (2015)](https://doi.org/10.1017/S0269888913000349) - Process-centric ontology evolution survey; useful for designing the actual migration lifecycle: detect, suggest, validate, impact-analyze, manage.
- [Klein and Noy (2003)](https://ceur-ws.org/Vol-71/Klein.pdf) - Component-based ontology evolution framework; especially relevant for representing change operations and deriving auxiliary change metadata.
- [Herrmann et al. (2018)](https://doi.org/10.1007/s00778-018-0508-7) - InVerDa / multi-schema-version data management; read this only if you genuinely need coexisting live versions instead of direct cutover.

## Existing Implementations

- **PRISM / PRISM++**: Academic system centered on schema modification operators, automatic migration, and query/update rewriting.
- **InVerDa / BiDEL**: Multi-schema-version database evolution system with a bidirectional evolution language.
- **Edapt**: EMF metamodel/model co-evolution tool; useful as a design reference for typed migration operations plus history.
- **Liquibase / Flyway**: Operational migration tooling, but they are deployment tools more than semantic migration frameworks.

## Complexity vs Quality Tradeoffs

The cheapest workable approach is operator-based explicit migrations plus typed validators and provenance. That gets you durable history, reproducibility, and hard-failure boundaries. Adding lens-like invertibility laws improves rigor substantially, especially for proving that a migration preserves information or for exposing old data through a new surface. Adding ontology-evolution machinery pays off when the migration changes semantic identity, canonical forms, or interpretation rules rather than only file/schema layout. Multi-version live support is highest complexity and only worth it if concurrent old/new readers are a real requirement.

## Recommendations

For this project, start with this reading order:

1. Curino et al. 2013
2. Curino et al. 2008
3. Bohannon et al. 2006
4. Flouris et al. 2008
5. Zablith et al. 2015

Recommended framework shape for propstore:

- Define migrations as typed, named operations over explicit domain objects, not ad hoc scripts.
- Require declared invariants: preserved identities, intentionally rewritten identities, provenance behavior, and reversibility status.
- Separate structural migrations from semantic migrations.
- For structural migrations, prefer operator composition with validation hooks.
- For semantic migrations, record change intent explicitly in an ontology-style change log.
- Where feasible, require round-trip or partial round-trip properties inspired by lenses.
- Do not default to long-lived dual-path runtime compatibility; only add coexisting-version machinery if there is a real external constraint.

## Estimated Implementation Effort

- **Minimal approach:** Migration manifest + typed operation catalog + validator + provenance log. Good enough for explicit repo upgrades.
- **Full approach:** Add declared invertibility classes, derived read/write rewrite support, impact analysis, and semantic change taxonomy. This is much more principled but materially more work.

## Open Questions

- [ ] Do migrations need to support old and new readers concurrently, or is direct cutover acceptable?
- [ ] Which identity surfaces in propstore must be preserved exactly across migrations?
- [ ] Which migrations are structural only, and which are semantic reinterpretations?
- [ ] Is reversibility required, or only forward reproducibility plus provenance?

## References

- Roddick, J. F. (1995). A survey of schema versioning issues for database systems. Information and Software Technology. https://doi.org/10.1016/0950-5849(95)91494-K
- Curino, C. A., Moon, H. J., & Zaniolo, C. (2008). Graceful database schema evolution: the PRISM workbench. VLDB. https://pubs.dbs.uni-leipzig.de/se/node/867
- Curino, C. A., Moon, H. J., Deutsch, A., & Zaniolo, C. (2013). Automating the database schema evolution process. The VLDB Journal. https://doi.org/10.1007/s00778-012-0302-x
- Velegrakis, Y., Miller, R. J., & Popa, L. (2004). Preserving mapping consistency under schema changes. The VLDB Journal. https://doi.org/10.1007/s00778-004-0136-2
- Bohannon, A., Pierce, B. C., & Vaughan, J. A. (2006). Relational lenses: A language for updatable views. PODS. https://doi.org/10.1145/1142351.1142399
- Flouris, G., Manakanatas, D., Kondylakis, H., Plexousakis, D., & Antoniou, G. (2008). Ontology change: Classification and survey. The Knowledge Engineering Review. https://doi.org/10.1017/S0269888908001367
- Zablith, F., Antoniou, G., d'Aquin, M., Flouris, G., Kondylakis, H., Motta, E., Plexousakis, D., & Sabou, M. (2015). Ontology evolution: A process-centric survey. The Knowledge Engineering Review. https://doi.org/10.1017/S0269888913000349
- Klein, M., & Noy, N. F. (2003). A component-based framework for ontology evolution. https://ceur-ws.org/Vol-71/Klein.pdf
- Herrmann, K., Voigt, H., Pedersen, T. B., & Lehner, W. (2018). Multi-schema-version data management: data independence in the twenty-first century. The VLDB Journal. https://doi.org/10.1007/s00778-018-0508-7
