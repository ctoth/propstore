---
title: "A Survey of Schema Versioning Issues for Database Systems"
authors: "John F. Roddick"
year: 1995
venue: "Information and Software Technology, vol. 37, no. 7, pp. 383-393"
doi_url: "https://doi.org/10.1016/0950-5849(95)91494-K"
pages: "383-393"
affiliation: "Advanced Computing Research Centre, School of Computer and Information Science, University of South Australia"
produced_by:
  agent: "Claude Opus 4.7 (1M context)"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-25T08:44:58Z"
---
# A Survey of Schema Versioning Issues for Database Systems

## Extraction Status (CHECKPOINT — 2026-04-25, fourth checkpoint)

paper-reader skill: COMPLETE
- 27 page images read. Dense surrogate notes complete.
- metadata.json, description.md, abstract.md, citations.md all written.
- papers/index.md updated with Roddick entry.
- /research-papers:reconcile invoked successfully — 0 already-in-collection direct citation matches, 12 new leads recorded, 3 cited-by entries (Sarkar 2004 nanopass, Klein 2003 ontology evolution, Bohannon 2006 relational lenses), 3 conceptual links bidirectional from earlier passes.
- pks source stamp-provenance applied (Claude Opus 4.7, paper-reader, status=stated).

orchestrator step 4: source-bootstrap — COMPLETE
- pks source init "Roddick_1995_SurveySchemaVersioningIssues" --kind academic_paper --origin-type doi --origin-value "10.1016/0950-5849(95)91494-K" — succeeded.
- pks source write-notes / write-metadata — both succeeded.

orchestrator step 5: author-context — COMPLETE
- Context name: ctx_roddick_1995_schema_versioning_survey
- Authored with parameters (publication_year, venue, doi, literature_window_start/end_year, n_references_surveyed, n_papers_in_underlying_bibliography) and perspective=authors_primary_analysis.
- No CEL assumptions added — Roddick is a terminological-vocabulary survey paper, not an empirical trial; the policy-doc framing of population/intervention/follow-up assumptions doesn't apply, and forcing assumptions risks fabricating structural commitments the paper doesn't actually make. Parameters carry the paper's structural identity (DOI, venue, literature window, sample of references).

**Side observation worth surfacing to Q:**
- `pks concept list` printed a `quire.documents.schema.DocumentSchemaError: master:concepts/abstract_object_function.yaml: Object contains unknown field 'canonical_name'` BEFORE printing the actual list. The list still printed (66 lines). `pks context add` worked fine. This is an existing-master-data schema mismatch unrelated to Roddick — likely a stale field on `abstract_object_function.yaml` from a prior schema iteration. Surfacing in the final orchestrator report.

**Steps remaining in orchestrator:**
- Step 6: register-concepts.
- Step 7: extract-claims.
- Step 8: iterate concepts/claims as needed.
- Step 9: extract-justifications.
- Step 10: extract-stances.
- Step 11: source-promote.
- Step 12: pks build.
- Step 13: write report to reports/paper-Roddick_1995_SurveySchemaVersioningIssues.md.

**Current blocker:** None. Continuing to register-concepts.

## One-Sentence Summary
Roddick (1995) is the canonical vocabulary paper for schema-evolving databases: it formally distinguishes **schema modification** (allowing changes to the schema of a populated database), **schema evolution** (modifying the schema *without loss of existing data*), and **schema versioning** (allowing access to all data both retrospectively and prospectively through user-definable version interfaces); refines schema versioning into **partial** (read-many, update-current-only) and **full** (read-many, update-many); and surveys data-modelling, architectural, and query-language consequences of admitting evolving schemata.

## Problem Addressed
- ≥50% of programmer effort happens after release as system maintenance (Lientz 1983) and a substantial fraction of those changes touch schema (Sjøberg 1992, 1993). *(p.1)*
- Database systems are rarely stable post-deployment, but DBMS support for schema evolution and versioning is poor and the literature uses the terms inconsistently. *(p.1, p.3)*
- The paper's mission is twofold: (a) fix terminology, (b) survey the open issues across modelling, architecture, and query languages. *(p.0 abstract; p.3 §1.3)*

## Key Contributions
- Crisp definitions of **schema modification / evolution / versioning** with explicit four-point distinction between evolution and versioning. *(p.3, §2.1)*
- Refinement of versioning into **partial schema versioning** (retrieval-many, update-only-through-current) and **full schema versioning** (retrieval-and-update across all versions). *(p.4)*
- Table 1 — taxonomy unifying schema evolution / schema versioning / data integration / view integration as four flavours of "using multiple heterogeneous schemata." *(p.5)*
- Five-level taxonomy of query-language support for evolving schemata (ignore, restrict, full multi-time, "all-points effective," "any-point completed schema"). *(p.13)*
- Identification of the **completed schema** construct (union of all attributes ever defined, with least-general domain that covers all values) as a query-time abstraction over versioned data. *(p.14)*
- Extension of Zaniolo's three-valued null logic to a **seven-valued null logic** where attribute applicability and definedness are crossed with value-known/unknown — needed once attributes can be undefined at a given point in time. *(p.14, Table 3)*
- Definition of **schema-time** as a fourth time dimension orthogonal to valid-time and transaction-time. *(p.12)*
- "Schema projection" as a query-time operation analogous to relational projection but selecting *which schema version* to view through. *(p.15-16, §5.5)*
- Constraint vocabulary: symmetry, reversibility, algebraic expressibility, no required temporal substrate, minimal DBA intervention. *(p.2)*

## Section 1 — Introduction

### §1.1 Background *(p.1)*
- Database/software systems rarely stable post-implementation. >50% of programmer effort post-deployment (Lientz 1983).
- Schema-touching modifications are frequent (Sjøberg 1992, 1993).
- Schema evolution (loose definition, p.1): "the ability for a database schema to evolve without the loss of existing information."
- Schema evolution and versioning are also relevant to legacy-system support (Stonebraker et al. 1993) and non-stop industrial-strength databases (Selinger 1993).
- Bibliography of schema evolution research (Roddick 1994) lists >50 papers; only a handful pre-1987.
- Two source communities: temporal-databases tradition; OO paradigm (CAD/engineering).

### §1.2 Pragmatic considerations any solution must satisfy *(p.2-3)*
1. **Minimal DBA intervention** appropriate to the change. Implementation choices like strict-vs-lazy conversion are environmental, not user-facing.
2. **Symmetry**: existing data must be viewable through new schema *and* later data must be viewable under previous schemata. Promotes operational stability — applications need not be recompiled.
3. **Reversibility / lossless DDL**: data definition functions should operate losslessly; erroneous changes must be removable.
4. **Algebraic expressibility**: schema modifications should be expressible as definable algebraic operations on the schema, supporting formal verification. Prefer composition of elementary operators over a sprawling vocabulary of large change operators.
5. **Temporal substrate not a prerequisite**: many models need transaction-time to identify versions, but it should not be a base-architecture requirement (although §2.3 explores parallels).

### §1.3 Outline *(p.2)*
§2 definitions; §3 data-modelling issues; §4 architectural issues; §5 query-language issues; §6 misc; §7 future research.

## Section 2 — Handling heterogeneous schemata

### §2.1 The three core definitions *(p.3)*

**Definition — Schema Modification.** "Schema Modification is accommodated when a database system allows changes to the schema definition of a populated database."

**Definition — Schema Evolution.** "Schema Evolution is accommodated when a database system facilitates the modification of the database schema without loss of existing data."

**Definition — Schema Versioning.** "Schema Versioning is accommodated when a database system allows the accessing of all data, both retrospectively and prospectively, through user definable version interfaces."

#### Four points distinguishing evolution from versioning *(p.3)*
1. Evolution does NOT imply full historical schema support; only loss-free change. Versioning, even at simplest, requires a *history of schema changes* be maintained.
2. The decisive difference: versioning lets users **identify quiescent / stable points** in the definition and label the schema in force at that time for later reference. Evolution does not require versioning of data nor a viewing mechanism over past schemata.
3. Schema changes do not necessarily produce new versions. **Schema changes are typically finer-grained than versions.**
4. Versions are usually labelled by transaction time or user-defined name; evolution changes are referenced only by time of change.

The note at the bottom of p.3 refines schema versioning further into retrieval-only vs retrieval+update by introducing partial vs full versioning on p.4.

### Definitions on p.4 (refinement)

**Definition — Partial Schema Versioning.** "Partial Schema Versioning is accommodated when a database system allows the viewing of all data, both retrospectively and prospectively, through user definable version interfaces. **Data updates are allowable through reference to one designated (normally the current) schema definition only.**"

**Definition — Full Schema Versioning.** "Full Schema Versioning is accommodated when a database system allows the **viewing and update** of all data, both retrospectively and prospectively, through user definable version interfaces."

The term "evolutionary" is also used in genetic-algorithm contexts (van Bommel 1993) but unrelated to schema evolution in the database sense; flagged to avoid confusion. *(p.4)*

### §2.2 Data and view integration *(p.4-5)*
- Data and view integration: merge multiple schemata for view/update purposes. Normally targets heterogeneous-system integration, but applicable to schema evolution.
- Miller, Ioannidis, Ramakrishnan (1993) introduce **information capacity** of a schema to test whether integration is lossless; their taxonomy distinguishes translation ability for retrieval vs update.
- Orlowska and Ewald (1991, 1992); Ewald and Orlowska (1994) treat schema integration as schema evolution: pick one of the schemata and apply facts held in the others.
- Geller et al. (1992) propose a "dual" model maintaining separate structural and semantic representations to integrate structurally-similar but semantically-dissimilar datasets.
- Other work: Atzeni et al. (1982); Larson, Navathe, Elmasri (1989).
- Conjecture: schema/view integration of *temporal* databases not yet investigated as of 1995.

#### Table 1 — Connection between research areas *(p.5)*

Cells answer: which research areas concern themselves with this combination of (schema used for the function) × (format the data was stored under) × (function: retrieval, update, structural alteration)?

| Schema used for function | Data held in format corresponding to | Data Retrieval | Data Update | Structural Alterations |
|--------------------------|---------------------------------------|----------------|-------------|------------------------|
| Primary | Primary schema | SE, SV, DI, (VI) | SE, SV, DI, (VI) | SE, SV |
| Primary | Secondary schema | SE, SV, DI | SE, SV, DI | (same SE, SV cell) |
| Secondary | Primary schema | SV, VI | FSV, VI | ? |
| Secondary | Secondary schema | SV, VI, (DI) | FSV, VI, (DI) | ? |

Key: SE = Schema Evolution; SV = Schema Versioning (partial or full); FSV = Full Schema Versioning; DI = Data Integration; VI = View Integration; ? = little published research; parentheses = pathological cases (user-view = integrated view, or local = integrated).

Implication: structural alteration *under a secondary schema* is the under-studied corner. *(p.5)*

### §2.3 Temporal database systems *(p.5-6)*
Brief recap because the vocabulary overlaps. Refers readers out to Clifford and Ariav 1986, Snodgrass and Ahn 1986, Dean and McDermott 1987, Roddick and Patrick 1992, Tansel et al. 1993.

Two orthogonal time dimensions:
- **Valid-time** = real-world time (formerly "historical")
- **Transaction-time** = database-system time (formerly "rollback")

Systems are valid-time, transaction-time, or **bitemporal** depending on which dimensions they support. Bitemporal query languages let users specify either or both for retrieval, but only valid-time for update (transaction-time is a function of update time, not user-specifiable).

Time references can be **absolute** (point on a continuum) or **relative / indirect** (relative to other events).

**Temporal density** = mechanism by which values are inferred at points not explicitly recorded. Types: stepwise change, discrete event, continuous change. **For schema evolution, stepwise change of database objects is usually assumed.** *(p.6)*

Footnote: nomenclature throughout the paper follows Jensen et al. 1994. The earlier Snodgrass-Ahn 1985 taxonomy used "temporal," "historical," "rollback" — now replaced by "(any time-supporting)," "valid-time," "transaction-time" respectively. *(p.9)*

## Section 3 — Data Modelling Issues

Opening point (Miller et al. 1993, p.6): for true mutual update through opposite schemata, schemata S1 and S2 must be **equivalent** — every valid instance under S1 must be storable under S2 and vice versa. This is too strong in practice; most papers therefore adopt **partial schema versioning** where any historical schema can be *viewed* through any other, but updates are only through the current schema.

### §3.1 Domain/type evolution *(p.7-8)*
- Even simple domain changes are non-trivial in a populated database.
- Footnote 1: "the schema is considered the repository for knowledge about the (evolving) structure of the database" — under some paradigms hard to isolate, but the abstract idea of an *all-knowing* schema is used.
- Worked example (Figure 2, salary relation, Roddick 1992a): replacing alphanumeric position codes with four-digit numeric codes raises three problems:
  i. Should the column type stay alphanumeric (hybrid) despite codes now being numeric?
  ii. Is a separate attribute required for old codes? For how long? How are old/new related by applications?
  iii. What about position histories and retired employees who never get a new code?
- Reduction in primary-key domain may yield illegal duplicate values.
- Ventrone and Heiler (1991) classify domain-change interpretation problems as either **Object-System-generated** (cardinality, granularity changes) or **Database-Administration-generated** (field recycling, encoding changes); they push for capturing semantics in metadata so the problem becomes "syntactic heterogeneity rather than semantic heterogeneity." *(p.8)*
- Domain evolution is tied to type-system expressiveness. SQL's character/exact-numeric/approximate-numeric typing requires more DBA intervention than systems with C-like casts (SQL-92 or weakly-typed systems). TSQL2 uses SQL-92 casting plus rules for conversion plus null/other-value fallback when not convertible. *(p.8)*
- Footnote 2: TSQL2 was the language design proposal for a temporal extension to SQL-92; relevant: Hsu, Jensen, Snodgrass 1992a, 1992b; Snodgrass 1992; Roddick and Snodgrass 1993, 1994; Snodgrass et al. 1994.
- **Domain evolution as the canonical example of evolution-vs-versioning (p.8):** "Under schema evolution, existing instances must be converted to the new format ... and thus existing applications are rendered incompatible. **Versioning promotes program compatibility by leaving the existing definition in place** (Zdonik 1990; Clamen 1992)."

### §3.2 Relation/class evolution *(p.8-10)*
Includes attribute and relation/class definition, redefinition, deletion, class lattice modification. In TDB paradigm: also deactivation/reactivation.

Two design approaches:
- **OO paradigm**: a set of *invariants* to ensure semantic integrity + a set of rules/primitives to effect schema changes (Banerjee et al. 1986; Bretl et al. 1989; Lerner and Habermann 1990).
- **Relational paradigm**: a set of *atomic operations* yielding consistent and where-possible reversible structure (Shneiderman and Thomas 1982).

Evolutionary history of relational/class structure must be **traceable**: DDL must be both logically complete (no need to drop to DML to modify data) and clear in specification and action.

Earlier Roddick taxonomy (Roddick 1993; Roddick, Craske, Richards 1993) uses a transaction-time meta-relation: previous schemata can be reconstructed by temporal rollback of the meta-relations. *(p.9)*

**Schema-level (DDL) commit/rollback should be separate from data-level (DML) commit/rollback.** Data-level commits may also need to behave differently when schema-level transactions are active, e.g. data updated to a revised schema may be inapplicable until the schema change itself is committed. The example pseudo-code:

```
Add attribute(s) to relation;
Populate attribute(s);
Data level commit;
Run test programs;
If tests successful
   Schema-level-commit;
else
   Schema-level-rollback;
```

This treats definition + population as one molecular operation. Long-lived and nested transactions are an active area of research; schema-evolution proposals should not be isolated from that work. *(p.9)*

### §3.3 Algebras supporting schema evolution *(p.9)*
- Codd 1970, 1972, 1979 establishes a logically complete algebra for static relations.
- Time-related algebras extending the static relational model: Clifford and Tansel 1985; Tansel 1986; Clifford and Croker 1987; McKenzie and Snodgrass 1987a, 1987c, 1990; Gadia 1988; Lorentzos and Johnson 1988; Sarda 1990; Tuzhilin and Clifford 1990.
- McKenzie and Snodgrass 1991 surveys 12 valid-time / bitemporal algebras.
- **Of those 12, only McKenzie & Snodgrass 1987b, 1990 and McKenzie 1988 are extended to deal explicitly with schema evolution.** *(p.9)*
- Footnote 3 (p.9): adopts Jensen et al. 1994 nomenclature where "bitemporal" = both valid-time and transaction-time.

## Section 4 — Architectural Issues

### §4.1 Schema conversion mechanisms *(p.10)*
Four physical-level approaches:
1. **Whole-schema-version conversion** (Orion: Banerjee et al. 1986; Kim et al. 1989, 1990). Conceptually simple but blocks parallel schema versions.
2. **Class-level versioning** (Encore: Skarra and Zdonik 1986, 1987; Zdonik 1986). Permits parallel changes when in different classes.
3. **View/context-based** (Kim and Chou 1988; later Andany, Leonard, Palisser 1991): views/contexts are constructed and schema evolution is achieved through view creation. Allows multiple concurrent versions. Relational equivalent ≈ creation of a completed/meta-schema.
4. **Self-descriptive objects** (Charly: Palisser 1989). Object and schema modification become homogeneous. Powerful but versioning becomes difficult; Andary et al. later rejected it for the Kim-Chou approach.

### §4.2 Data conversion mechanisms *(p.10-11)*
Three options (analogous to functional-programming evaluation strategies):
- **Strict / eager / early** conversion (GemStone: Penney and Stein 1987). Schema change immediately propagates to data. Slower DDL but faster subsequent reads. Lerner and Habermann (1990) extend this with a data-transformation table generator that produces routines to assist the DBA.
- **Lazy** conversion (Tan and Katayama 1989). Data converted only when accessed. Advantages:
  i. Faster schema changes.
  ii. No need to identify obsolete data.
  iii. Schema-change withdrawal is possible without effect; compensating schema changes may require no physical data change.
  - Footnote 4: example — a reversed business decision not to hold cents on financial values.
- **Logical conversion only / "screens"** (Orion: Banerjee et al. 1986, 1987b; Kim and Chou 1988). A system of screens translates attributes into the required format at access time. Avoids GemStone's DDL overhead and Tan-Katayama's per-access overhead, but database complexity grows over time and must be rationalised at quiet points.

Skarra and Zdonik introduce a method similar to Orion's where identifiable versions are defined periodically to link instances; an error-handling routine deals with instances that don't match the version interface. Access to data may involve double-modification: once to fit the version interface, once for caller's required format. *(p.11)*

### §4.3 Access right considerations *(p.11)*
In OO databases with method/attribute inheritance, schema evolution can violate access rights. Example: a user modifies an Employee class; an Engineer subclass inherits Employee attributes, but the user has no legitimate access to Engineer. Any change to inherited attributes can be considered a violation.

Also: in some systems class ownership does not imply ownership of all instances. GemStone (Bretl et al. 1989) treats class ownership as sufficient authorisation for all instances and inheriting subclasses.

### §4.4 Concurrency considerations and concurrent schemata *(p.11-12)*
- Multi-user schema modification while another user accesses the database. Schema versioning ameliorates this; static schema evolution alone makes it harder. Even harder when two users modify related schema definitions concurrently. (Sockut and Iyer 1993)
- Multiple concurrent versions, esp. Zdonik (1986): **surface of consistency**. Two users can both read+modify+update the same schema version, yielding two probably-inconsistent versions both consistent with the rest of the database. New transactions choose between alternative surfaces of consistency at start. **Conversational merging** coalesces divergent paths.
- Ties to meta-level transactions (§3.2). Multiple future schema versions can be tested as alternatives; conversational merging at implementation time produces a unified version with translation functions imposed.

## Section 5 — Issues in query language support *(p.12)*

Three (or four) independent time mechanisms for viewing data once schema versioning is added:
i. **Valid-time** — time pertaining to reality.
ii. **Transaction-time** — time data was stored.
iii. **Schema-time** — time indicating the format of the data via the schema active at that time.
A fourth dimension (meta-database equivalent of valid-time): the time the *object model structure* changed.

The first two are well-studied; this section focuses on **schema-time** in query languages. *(p.12)*

Footnote 5: this content was first published as part of an SQL extension in Roddick 1992b; parts also appear as TSQL2 commentaries (ISO 1992; Roddick and Snodgrass 1993, 1994; Snodgrass et al. 1994).

### §5.1 Five-level taxonomy of schema-evolution query-language support *(p.13)*
Five approaches:
i. **Ignore schema change.** Schema is immutable once set up, or queries against old definitions are illegal. Default of most DB query languages. Doesn't preclude TDB systems as long as all data adhere to the same schema.
ii. **Restrict.** No schema changes during the intervals used to satisfy the query.
iii. **Full multi-time.** Queries may use any/all of valid-, transaction-, schema-time. Example: "Find all employees who earned more than $40,000 in 1992, as recorded on January 1, 1993, and report the details using the format in use in March 1993." Maximum resilience for application programs.
iv. **Effective schema = all-points intersection.** Effective schema is the schema containing all attributes that were defined for the relation at *all* points during the transaction-time intervals used to satisfy the query.
v. **Effective schema = any-point completion.** Effective schema is the union (completion) of all attributes that were defined for the relation at *any* point during the transaction-time intervals used to satisfy the query (Clifford and Warren 1983; Roddick 1991).

Approaches i-ii are simple but overly restrictive (Sjøberg 1992, 1993).
Approach iii is the most expressive; iv-v are simplifications.
Approach v is preferred over iii for these reasons:
i. Degrades to static case when schema evolution unused.
ii. Query language semantics intuitively degrade to conventional static DB query.
iii. All relevant attributes displayable without intuitively-irrelevant ones.
iv. Conceptually simple (though not as simple as static).
v. Schema can be free of inactive attributes while still providing historical retrieval.

Footnote 6: some researchers identify situations needing >3 time dimensions.

### §5.2 Completed schemata *(p.14)*
Clifford and Warren (1983) define **completed relation** = a relation containing a tuple for every key that has ever existed in the relation.

Applied to schemata: a **completed schema** = relations containing the union of attributes ever defined, each with **the least general domain that includes all domain values**. Where no general domain exists, attributes must be duplicated with enough different domains to hold all values.

The completed schema can be considered an overarching version usable to extract data across versions. Difficult to implement in some proposals (notably Palisser 1989) because of the search needed to compile the completed schema.

### §5.3 Problems presented by null values *(p.14-15)*

Three-valued null logic (Zaniolo 1984; Roth, Korth, Silberschatz 1989) presupposes a static schema. Once attributes can be undefined at a given time, null semantics extend.

#### Table 3 — Null value interpretations *(p.14)*

| | Attribute Defined / Value Known | Attribute Defined / Value Unknown | Attribute Not Defined / Value Known | Attribute Not Defined / Value Unknown |
|---|---|---|---|---|
| **Attribute Applicable** | value | ω₁ = UNK | ω₄ | ω₅ |
| **Attribute Inapplicable** | (impossible) | ω₂ = DNE | (impossible) | ω₆ |
| **Applicability Unknown** | ω₃ = NI (spans Attribute Defined, both Known/Unknown) | (same) | ω₇ (spans Attribute Not Defined, both Known/Unknown) | (same) |

So Φ ≡ {ω₁ … ω₇}, a **7-valued null logic**. ω₄–ω₇ have different semantics from ω₁–ω₃: e.g. ω₄ = the database holds a known value in an applicable attribute but the schema being used prohibits its display (structural rather than security reasons).

Example: a student does not cease to have a marital status because the information stops being collected → "value unknown" null. Subdivision of a University into Faculties may add new attributes → "attribute inapplicable" null for extant data. *(p.15)*

Footnote 7 (p.15): null problems also tied to fuzzy data, unreliable data, unavailable data, granularity mismatch. Researchers on access-authorisation (esp. OODB) have suggested "Not Authorised" nulls (Gal-Oz, Gudes, Fernandez 1993). Roddick has proposed "Temporally Inapplicable Attributes" nulls (Roddick 1991). Acknowledges this is outside the scope of the paper. See also Atzeni and De Antonellis 1993.

### §5.4 Schema valid-time support *(p.15)*
The valid/transaction duality applies also to schema definitions:
- Date the schema change is to take effect (schema valid-time).
- Date the schema modification is recorded in the meta-database (schema transaction-time).

McKenzie and Snodgrass (1990) extend the relational algebra to support schema transaction-time but argue schema valid-time is not necessary "since it (schema evolution) defines how reality is modeled by the database." Roddick disputes: the same audit/rollback motivations for valid-time data apply to schema valid-time. Utility depends on application's auditing requirements and capacity to hold such data.

### §5.5 Schema-time projection *(p.15-16)*
Relation projection selects a subset of attributes through which the relation is viewed. Versioning requires we choose **which schema to use for retrieval** — also a kind of view. Term: **schema projection**. Two aspects: method of schema specification, method of effective-schema construction.

#### §5.5.1 Implicit vs explicit specification *(p.15-16)*
**Implicit** schema selection options:
i. Current schema.
ii. A default schema (which may not be current).
iii. Function of (implicit/explicit) transaction-time of the query.
iv. Function of (implicit/explicit) valid-time of the query.

The first option is simplest and arguably most attractive given legacy applications. The others require temporal-query-language support beyond schema versioning.

**Explicit** schema specification options:
i. By version date.
ii. By version name (if applicable).
iii. By reference to transaction-time interval in the query.
iv. By reference to valid-time interval in the query.

The first allows program stability via embedded queries that specify *version as at <compile-time>*.

#### §5.5.2 Simple vs constructed schemata *(p.16)*
Explicit schema-time can be given as either:
- An **event** = schema current at a specified instant. The simple mode. Sufficient to give absolute time or version name.
- An **interval** = schema constructed from versions active during the interval. The two obvious construction functions are intersection and union (completion) of attributes.

### §5.6 Schema-time selection *(p.16-17)*
Used to access data based on the schema under which data was stored or the format the data currently adheres to. May be necessary to access old-format data. Architecture-level decision, but query language must support **selection predicates indicating schema format time**. Note: transaction-time values used in temporal-query languages may not suffice — they record only the date of last modification by a *user*, not modifications by the system for performance.

### §5.7 Version naming *(p.17)*
Versioning requires a version-naming method: user-defined convention, system-defined convention, or system-defined time-stamping. On schema commit, three actions:
i. New version is created and referenceable through (function of) creation time *or* user-defined name.
ii. New version is created and referenceable only through (function of) creation time.
iii. No new version created — multiple evolutionary transactions may occur between versions.

Naming most likely happens at schema-level commit time because (a) many query languages including SQL have no transaction-start command, (b) version naming is only relevant if the change commits.

### §5.8 Casting of output attribute domains *(p.17)*
Casting (C, SQL-92) is not strictly required for schema evolution but provides stability for embedded queries by letting applications coerce data to the required format. Conversion routines are intuitively simple; null or another specified value may be used when conversion fails. Roddick 1993 proposed a user-defined value (essentially a second null) for incompatible data.

## Section 6 — Other related research issues *(p.17-18)*

Sjøberg (1992, 1993) quantifies how schema changes are actually applied — useful for choosing lazy vs eager data conversion architecturally.

**Vacuuming** (Jensen 1993): physical deletion of temporal data when retention cost exceeds utility. Roddick and Snodgrass (1994) propose two pragmatic positions on vacuuming schema definitions:
i. All schema definitions which pre-date all data (in format and in transaction-time values) are obsolete and should be deleted.
ii. Old schema definitions are valuable independent of data existence and can be deleted only via a special form of vacuuming.

Roddick and Snodgrass adopted (i) for simplicity; both are worth further research.

## Section 7 — Further Research *(p.18)*

Three named open issues:
i. Accommodating schema evolution within existing database systems including their query languages.
ii. The relationship of database schema evolution to **software systems evolution**.
iii. Pragmatic limits of automated schema evolution: when can the system assume existing data fit the revised structure, and when must the DBA direct?

Mentioned in passing:
- Prototype system **Boswell** under construction at the time, aiming to combine schema evolution (structure-driven) with transient inductively-generated facts from data mining (update-driven schema evolution). (Roddick, Craske, Richards 1994)
- Some ideas have been proposed as background to TSQL2 (temporal SQL92 extension); commentaries available via anonymous FTP at FTP.cs.arizona.edu in `tsql/doc`.

## Methodology
Survey paper. No empirical study. Synthesis and definitional refinement over the schema-evolution literature 1982–1994.

## Key Equations / Statistical Models
The paper contains no formal equations. The primary formal-vocabulary contribution is set-valued: Φ ≡ {ω₁, …, ω₇} as the 7-valued null space (p.14). All other content is definitional, taxonomic, or example-based.

## Parameters

The paper has no quantitative parameters in the modelling sense. Definitional / categorical parameters that downstream consumers should treat as the paper's authored vocabulary:

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Schema modification (SM) | SM | — | — | — | 3 | Allows changes to schema of a populated DB |
| Schema evolution (SE) | SE | — | — | — | 3 | Loss-free schema modification |
| Schema versioning (SV) | SV | — | — | — | 3 | Retro+prospective access via version interfaces |
| Partial schema versioning | PSV | — | — | — | 4 | Read-many, update-current-only |
| Full schema versioning | FSV | — | — | — | 4 | Read-many, update-many |
| Valid-time | VT | time | — | — | 6, 12 | Real-world time the fact is true |
| Transaction-time | TT | time | — | — | 6, 12 | Time data was stored in DB |
| Schema-time | ST | time | — | — | 12 | Time indicating data format via active schema |
| Information capacity | — | — | — | — | 4 | Miller et al. 1993 — per-schema; equality required for lossless integration |
| Surface of consistency | — | — | — | — | 12 | Zdonik 1986 — concurrent-version coalescing primitive |
| Completed schema | — | — | — | — | 14 | Union of all attributes ever defined; least-general domain covering all values |
| 7-valued null logic | Φ = {ω₁..ω₇} | — | — | — | 14 | Roddick's expansion of Zaniolo's 3-valued null logic |
| ω₁ | UNK | — | — | — | 14 | Attribute applicable, defined, value unknown |
| ω₂ | DNE | — | — | — | 14 | Attribute inapplicable, defined, value unknown |
| ω₃ | NI | — | — | — | 14 | Applicability unknown, attribute defined |
| ω₄ | — | — | — | — | 14, fn7 | DB holds known value in applicable attribute but schema prohibits display (structural) |
| ω₅ | — | — | — | — | 14 | Attribute applicable, not defined, value unknown |
| ω₆ | — | — | — | — | 14 | Attribute inapplicable, not defined, value unknown |
| ω₇ | — | — | — | — | 14 | Applicability unknown, attribute not defined |
| Schema projection | — | — | — | — | 15 | Query-time choice of which schema version to view through |
| Vacuuming (schema) | — | — | — | — | 18 | Physical deletion of obsolete schema definitions |

## Effect Sizes / Key Quantitative Results
None — survey paper, no empirical study.

## Methods & Implementation Details
- Survey methodology: synthesis of >50 schema-evolution papers (Roddick 1994 bibliography, p.1).
- Definitional consistency check against Beech and Mahbod 1988; Narayanaswamy and Bapa Rao 1988; Bjornerstedt and Hulten 1989; Osborn 1989; Andany, Leonard, Palisser 1991; Ariav 1991; Monk and Sommerville 1992, 1993; Jensen et al. 1994. *(p.3)*
- Boswell prototype: combines structure-driven and data-mining-driven schema evolution (Roddick, Craske, Richards 1994). *(p.18)*

## Figures of Interest
- **Figure 2 (p.7):** Example salary relation from Roddick 1992a — the canonical motivating example for domain/type evolution. Three rows of Staff Id / Position Code (alphanumeric like "G55", "A05") / Salary (e.g. $33,000), used to motivate three problems when migrating to numeric position codes.
- **Table 1 (p.5):** Connection between schema-handling research areas, mapping {primary,secondary} schema × {primary,secondary} stored format × {retrieve, update, structurally alter} to which fields work on each cell.
- **Table 3 (p.14):** Null value interpretations — the 7-valued null logic.

## Results Summary
- Vocabulary fix: schema modification ⊋ schema evolution ⊋ schema versioning ⊋ full schema versioning. *(p.3-4)*
- Schema evolution loses application compatibility on incompatible domain change; schema versioning preserves it. *(p.8)*
- The decisive operational difference between evolution and versioning: versioning lets users name and label *quiescent points*. *(p.3)*
- Five query-language postures toward schema change exist; option v (any-point completed schema) recommended over the more expressive option iii (full multi-time). *(p.13)*
- Null logic must extend from 3 to 7 values once attributes can be undefined at a point in time. *(p.14)*
- Schema-time is a fourth orthogonal time dimension. *(p.12)*
- Schema-level commit/rollback should be separate from data-level commit/rollback. *(p.9)*

## Limitations *(p.18)*
- Roddick and Snodgrass 1994 chose vacuuming option (i) "for simplicity" — both options are worth further research.
- Schema integration of *temporal* databases not yet investigated as of writing (p.4).
- Self-descriptive object approach (Charly) was abandoned by its successors due to versioning difficulty (p.10).
- Of 12 surveyed temporal algebras, only 3 (McKenzie & Snodgrass 1987b, 1990; McKenzie 1988) explicitly handle schema evolution (p.9).
- Pragmatic limits of automated schema evolution remain open (p.18).
- The relationship of schema evolution to software-systems evolution remains open (p.18).

## Arguments Against Prior Work
- **Against Miller, Ioannidis, Ramakrishnan (1993):** their schema-equivalence requirement (every valid instance under S1 is storable under S2 and vice versa) is "too strong a condition to impose in many cases" because the future requirements of the database cannot be foreseen and it is generally only possible to create a new version superseding the old. Most papers therefore adopt **partial schema versioning**. *(p.6)*
- **Against McKenzie and Snodgrass (1990):** they argue schema valid-time is unnecessary because "schema evolution defines how reality is modeled by the database." Roddick counters that the same audit/rollback motivations for valid-time data apply to schema valid-time. *(p.15)*
- **Against approach iii of query-language taxonomy (full multi-time):** while most expressive, it does not gracefully degrade to the static case; option v does. *(p.13)*
- **Against the strict (eager) data conversion model of GemStone (Penney and Stein 1987):** central, slow, blocking — versioning provides program compatibility (Zdonik 1990; Clamen 1992) where strict conversion does not. *(p.8, p.10-11)*
- **Against the self-descriptive object approach (Charly: Palisser 1989):** abandoned by its successors (Andary et al.) because schema versioning by this method is difficult. *(p.10)*
- **Against the assumption that old schema definitions must be deleted whenever no data adheres to them** (Roddick and Snodgrass 1994 option i): chosen "for simplicity" but the alternative is also worth research. *(p.18)*

## Design Rationale
- **Symmetry over one-directional readability** *(p.2)*: applications should not need recompilation just because the DB structure changed.
- **Reversibility / lossless DDL** *(p.2)*: erroneous schema changes must be undoable.
- **Algebra of schema change operators** *(p.2)*: prefer compositional small-operator vocabulary over a sprawling change-operator catalogue, to support formal verification.
- **Temporal substrate optional** *(p.2)*: don't force every system to be a TDB just to evolve schemata.
- **Versioning over evolution when application compatibility matters** *(p.8)*: leaving the existing definition in place is better than converting in-place if applications would otherwise break.
- **Partial schema versioning as the practical default** *(p.6)*: the equivalence required for lossless mutual update is too strong; allow read-anywhere, update-current-only.
- **Option v over option iii for query languages** *(p.13)*: degradation to the static case is more important than maximum temporal expressivity.
- **Separate DDL and DML commit/rollback** *(p.9)*: data committed under an uncommitted schema is in limbo; molecular operations enabling test-then-commit (the pseudocode example) are the discipline.
- **Schema-level vacuuming options** *(p.18)*: deleting orphan schemata is convenient; preserving them is intellectually defensible. Both worth studying.

## Testable Properties
- **Schema evolution preserves data**: Modifying schema S → S' under SE must not lose any data instances of S. *(p.3)*
- **Schema versioning preserves history**: SV implies a history of schema changes is maintained. *(p.3)*
- **Schema versioning supports retrospective AND prospective access** *(p.3)*: data viewable through past and future schema versions, not only current.
- **Schema changes are typically finer-grained than versions** *(p.3, point iii)*: |schema changes| ≥ |versions|.
- **Partial schema versioning constraint**: in PSV, updates flow only through the current/designated schema version; reads flow through any. *(p.4)*
- **Full schema versioning constraint**: in FSV, both reads and updates flow through any version. *(p.4)*
- **Symmetric viewing** *(p.2)*: existing data viewable via new schema AND new data viewable via old schema.
- **Lossless DDL** *(p.2)*: every DDL operation must be reversible, i.e. no information lost after issuing it.
- **Algebraic decomposition** *(p.2)*: every schema change should decompose into a fixed set of elementary algebraic operators.
- **Minimal DBA intervention monotonicity** *(p.2)*: bigger required intervention should correspond to bigger semantic change, not bigger physical change.
- **DDL completeness** *(p.9)*: users must not need to drop to DML to modify data on schema change.
- **DDL/DML commit independence** *(p.9)*: schema-level commit can be issued independently of data-level commit, and data committed under uncommitted schema is held until schema-commit.
- **Information capacity equivalence required for lossless mutual update** *(p.6)*: S₁ and S₂ admit lossless mutual update iff every valid instance of S₁ is storable under S₂ and vice versa.
- **Strict data conversion makes existing applications incompatible** *(p.8)*: SE that propagates immediately renders apps incompatible; SV preserves them.
- **Lazy conversion withdrawability** *(p.10-11)*: under lazy data conversion, a schema change can be withdrawn before any data is touched and compensating changes may yield no physical data change.
- **Schema-time orthogonal to valid-/transaction-time** *(p.12)*: schema-time selection is independent of valid-time and transaction-time selection in the same query.
- **Option v effective schema = ⋃ defined-attributes-during-interval** *(p.13)*: the recommended query-language option computes the effective schema as the union of all attributes defined at any point during the interval.
- **Completed schema = least-general-domain union** *(p.14)*: the completed schema's domain for each attribute is the least general domain covering all historical values; otherwise duplicate the attribute.
- **Null logic must be 7-valued under schema versioning** *(p.14)*: |Φ| ≥ 7 once attribute applicability and definedness are crossed with value-known/unknown.
- **Schema commit and version naming co-occur** *(p.17)*: version naming should occur at schema-level-commit time.
- **Vacuuming option (i) ⇒ schema dropped when no data references it** *(p.18)*.
- **Vacuuming option (ii) ⇒ schema retained regardless of data references** *(p.18)*.

## Relevance to Project (propstore migration framework)

Roddick is the **vocabulary backbone** for propstore's migration framework. Direct mappings:

- **Schema modification → "raw mutation of authored knowledge structure"** — the unprincipled baseline propstore explicitly forbids ("never mutated by heuristic or LLM output").
- **Schema evolution → "loss-free knowledge-store schema migration"** — closest direct analog. Propstore's principle "do not collapse disagreement in storage unless the user explicitly requests a migration" is the SE constraint specialised: data must not be lost under schema change.
- **Schema versioning → propstore's actual non-commitment discipline at the semantic core** — keeping multiple rival normalisations queryable through user-definable views (render policies) is exactly the SV definition. Propstore's "render layer filters based on policy. Multiple render policies over the same underlying corpus" is the user-definable version interface concept.
- **Partial vs Full Schema Versioning → propstore's read/write asymmetry over historical contexts.** Authoring a new claim under an old context (writing through a historical schema) is the FSV case. The default propstore stance — read across all contexts, but write through the current vocabulary — is exactly PSV.
- **Symmetry constraint** ↔ propstore's bidirectional-readability principle: old claims readable under new vocabulary AND new claims projectable onto old vocabulary at render time.
- **Reversibility / lossless DDL** ↔ propstore's "never collapse disagreement in storage" rule. A migration that destroys past forms is not a propstore-compatible migration.
- **Algebraic expressibility / compositional change operators** → directly motivates a small-set propstore migration operator algebra (rename concept, split sense, merge entries, refine ontology reference, etc.) rather than ad-hoc commands.
- **Schema-level vs data-level commit independence** → propstore migration plans should separate vocabulary commit from claim re-projection commit, with rollback at each level.
- **Completed schema** → propstore's "render across all historical contexts" view is structurally a completed schema.
- **7-valued null logic** → directly relevant: when a claim's concept is undefined under a chosen render policy, "did not exist," "structurally hidden," and "unknown" are different states; propstore should not collapse them. This maps onto the existing typed-provenance discipline (`vacuous`, `defaulted`, etc.) but adds the structural-applicability axis.
- **Schema-time as fourth dimension** → propstore already has time-of-claim, valid-time, and (implicitly) provenance-time; "vocabulary-time" / "context-version-time" is the missing fourth axis Roddick names.
- **Vacuuming options** → propstore's stance matches Roddick option (ii): old vocabulary versions stay even when no claim references them, because they may be cited later. Option (i) would violate the non-commitment discipline.
- **Schema valid-time** → propstore should distinguish the time a vocabulary change *takes effect in modelled reality* from the time it is *recorded* in the store, mirroring McKenzie-Snodgrass-versus-Roddick.
- **The Boswell pattern** (structure-driven + data-mining-driven schema evolution) is conceptually parallel to propstore's distinction between user-authored concept changes and heuristically-mined proposal artifacts.

## Open Questions
- [ ] Does propstore want partial (PSV) or full (FSV) versioning over contexts? Current discipline implies PSV-by-default but FSV for explicit migration authoring.
- [ ] Is propstore's "concept" boundary a "schema" in Roddick's sense, or is the *context* the schema and the concept the populated data? Both readings are defensible.
- [ ] Should propstore adopt schema-time as a first-class query dimension on render policies, distinct from claim-time?
- [ ] How does propstore's typed provenance interact with Roddick's 7-valued null logic? The structural-applicability axis (ω₅, ω₆, ω₇) is not currently distinguished.
- [ ] Does propstore need an explicit "completed schema" render policy that unions all historical concept vocabularies?
- [ ] Should DDL-style migration commits be separate transactional artifacts from the resulting claim re-projections?
- [ ] Roddick option iii's full multi-time query was rejected for static-case-degradation reasons; does that argument apply to propstore render policies?

## Related Work Worth Reading
- **Miller, Ioannidis, Ramakrishnan (1993)** "Use of information capacity in schema integration and translation" — the formal lossless-integration criterion. Already on the propstore reading radar likely; central to migration-framework rigor.
- **McKenzie and Snodgrass (1990)** "Schema evolution and the relational algebra" — one of three temporal algebras explicitly extended for SE.
- **Lerner and Habermann (1990)** "Beyond schema evolution to database reorganisation" — strict-conversion data-transformation table generators.
- **Tan and Katayama (1989)** "Meta operations for type management ... a lazy mechanism for schema evolution" — lazy conversion canonical reference.
- **Zdonik (1986, 1990)** — surface of consistency, OO type evolution; both heavily cited for the application-compatibility argument.
- **Clamen (1992)** "Class evolution and instance adaptation" — the canonical SV-preserves-applications reference.
- **Jensen et al. (1994)** "A consensus glossary of temporal database concepts" — Roddick adopts this nomenclature.
- **Roddick (1992a)** "Schema evolution in database systems - an annotated bibliography" — the bibliographic substrate for this survey.
- **Roddick (1993)** "Implementing schema evolution in relational database systems: an approach based on historical schemata" — Roddick's own concrete proposal.
- **Roddick, Craske, Richards (1993)** "A taxonomy for schema versioning based on the relational and entity relationship models" — Roddick's earlier taxonomy.
- **Sjøberg (1992, 1993)** — empirical quantification of schema change in real systems; relevant to choosing eager vs lazy.
- **Ventrone and Heiler (1991)** "Semantic heterogeneity as a result of domain evolution" — semantic-vs-syntactic heterogeneity argument.

## Collection Cross-References

### Already in Collection
- (none — the propstore collection does not currently hold any of the 1980s/early-1990s database-systems literature Roddick cites; Miller-Ioannidis-Ramakrishnan 1993, McKenzie-Snodgrass 1990, Jensen-et-al 1994, Clamen 1992, Lerner-Habermann 1990, Sjøberg 1993, etc., are all candidate leads but not present at time of reconciliation)

### New Leads (Not Yet in Collection)
- Miller, R.J., Ioannidis, Y.E. and Ramakrishnan, R. (1993) — "The use of information capacity in schema integration and translation" — VLDB '93 — formal lossless-integration criterion; foundational for any propstore migration framework that wants a precise loss-detection rule.
- McKenzie, L.E. and Snodgrass, R.T. (1990) — "Schema evolution and the relational algebra" — *Inf. Syst.* 15(2):207-232 — one of three temporal algebras explicitly extended for schema evolution; the algebraic-expressibility precedent.
- Jensen, C. et al. (1994) — "A consensus glossary of temporal database concepts" — *SIGMOD Rec.* 23(1):52-64 — the nomenclature substrate Roddick adopts; needed for cross-paper terminological consistency in the migration batch.
- Clamen, S.W. (1992) — "Class evolution and instance adaptation" — CMU-CS-92-133 — canonical case for "versioning preserves application compatibility where strict-conversion evolution does not."
- Sjøberg, D. (1993) — "Quantifying schema evolution" — *Inf. Softw. Technol.* 35(1):35-44 — empirical data on real-world schema-change rates; relevant for choosing lazy vs eager re-projection on evidence.
- Lerner, B.S. and Habermann, A.N. (1990) — "Beyond schema evolution to database reorganisation" — *SIGPLAN Not.* 25(10):67-76 — strict-conversion data-transformation table generators.
- Tan, L. and Katayama, T. (1989) — "Meta operations for type management in object-oriented databases - a lazy mechanism for schema evolution" — DOOD '89 — lazy-conversion canonical reference.
- Zdonik, S.B. (1986, 1990) — "Version management in an object-oriented database" / "Object-oriented type evolution" — the surface-of-consistency concept for concurrent-version coalescing; central to the application-compatibility argument.
- Codd, E.F. (1970, 1972, 1979) — relational-model foundations Roddick treats as substrate; potentially worth collecting for grounding propstore's algebraic-expressibility constraint.
- Ventrone, V. and Heiler, S. (1991) — "Semantic heterogeneity as a result of domain evolution" — semantic-vs-syntactic heterogeneity argument relevant to propstore's vocabulary-reconciliation policy.
- Roddick, J.F., Craske, N.G. and Richards, T.J. (1993) — "A taxonomy for schema versioning based on the relational and entity relationship models" — Roddick's earlier taxonomy; the precursor to the 1995 survey.
- Roddick (1992b) — "SQL/SE — a query language extension for databases supporting schema evolution" — the concrete query-language proposal underlying §5.

### Supersedes or Recontextualizes
- (none — Roddick 1995 is itself a vocabulary-fixing survey paper; it does not supersede any paper in the propstore collection. It is, however, the substrate that Klein/Noy 2003 ports into the ontology setting and that Bohannon 2006 operationalizes via lens laws — see Cited By and Conceptual Links below.)

### Cited By (in Collection)
- [A Nanopass Infrastructure for Compiler Education](../Sarkar_2004_Nanopass/notes.md) — cites Roddick for the schema-modification / schema-evolution / schema-versioning trichotomy as a parallel to nanopass same-IL vs IL-changing passes.
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — cites Roddick as the database-systems ancestor of ontology evolution vocabulary; Klein/Noy port the SE/SV trichotomy into the ontology setting and extend with a third representation K (conceptual change description).
- [Relational Lenses: A Language for Updatable Views](../Bohannon_2006_RelationalLensesLanguageUpdatable/notes.md) — cites Roddick for the "lossless schema integration" criterion that the lens-law family (GetPut, PutGet, PutPut) operationalizes; Roddick's vocabulary points at the obligation, lens laws supply the test.

### Conceptual Links (not citation-based)
- [A Nanopass Infrastructure for Compiler Education](../Sarkar_2004_Nanopass/notes.md) — Sarkar, Waddell, Dybvig propose typed pass chains between formally-specified intermediate languages — the compiler-construction sibling of Roddick's schema-versioning architectural taxonomy. Roddick's distinction between *schema modification* (in-place edit), *schema evolution* (modify schema while preserving data), and *schema versioning* (retain past schema definitions) corresponds to nanopass's distinction between same-IL passes (verification, improvement) and IL-changing passes (simplification, conversion). A propstore migration framework needs Roddick's evolution-vs-versioning axis at the architectural level *and* nanopass's typed-pass-with-validation discipline at the per-migration level.
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — Klein and Noy port Roddick's database-side schema-evolution / schema-versioning vocabulary into the ontology setting and add a third representation (K — conceptual change description) that the database setting does not require. Klein/Noy's three-layer chain (T_set ⊂ T_set+K ⊂ T_set+K+log) is the ontology analog of Roddick's modification / evolution / versioning trichotomy. Read together they ground propstore's migration framework in both traditions: Roddick provides the formal vocabulary and lossless-integration criterion; Klein/Noy provide the typed-component-targeted change-operation discipline a knowledge graph needs.
- [Relational Lenses: A Language for Updatable Views](../Bohannon_2006_RelationalLensesLanguageUpdatable/notes.md) — STRONG: Bohannon, Pierce, Vaughan operationalize Roddick's "lossless schema integration" (via Miller-Ioannidis-Ramakrishnan information capacity) into the lens-law family GetPut + PutGet (well-behaved) + PutPut (very well-behaved). A migration that satisfies the lens laws is a lossless schema-evolution step in Roddick's sense; a migration that does not is at most a partial schema-versioning step. The lens framework supplies the operational test Roddick's vocabulary points at without specifying — propstore's migration framework needs Roddick's architectural taxonomy at the evolution/versioning axis *and* lens laws as the per-migration information-preservation criterion.
