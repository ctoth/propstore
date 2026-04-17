# Axis 3d — Semantic Substrate Fidelity

Scout: Claude Opus 4.7 (1M)
Date: 2026-04-16
Scope: 23 target modules (core/, top-level, source/, cli/) against the 27 Cluster 3d papers in paper-manifest.md.

## Verdict at a glance

| | Count |
|---|---|
| Faithful implementations | 0 |
| Inspired-by implementations | 4 |
| Label-only implementations | 2 |
| Partial implementations | 2 |
| Absent (papers named in CLAUDE.md) | 4 |
| Absent (papers in cluster but not named) | 14 + more |

**Biggest drift:** The four papers CLAUDE.md explicitly names as grounding the concept/semantic layer — Fillmore 1982 (frame semantics), Pustejovsky 1991 (qualia), Buitelaar 2011 (lemon), McCarthy 1993 (`ist(c, p)`) — have **zero** corresponding structural content in the code. `ConceptRecord` has no frame-element, qualia, or lemon-sense fields. `ContextHierarchy` is an ancestry-based visibility tree, not an `ist(c, p)` logic.

**Honest assessment:** The rhetoric in `CLAUDE.md` claims a frame-semantic + generative-lexicon + lemon + `ist(c,p)` substrate. The code implements a dimensional-quantity + SKOS-style ontology + inheritance-tagged context system, with string-token Jaccard vocabulary reconciliation. These are different systems. Severity: HIGH.

---

## Evidence per audit question

### 1. Contexts as logical objects — McCarthy 1993 / Guha 1991 / Ghidini 2001

**Verdict: LABEL-ONLY (McCarthy/Guha) · ABSENT (Ghidini)**

`ContextRecord` (`propstore/context_types.py:16-39`) carries `context_id`, `name`, `description`, `inherits`, `assumptions: tuple[str, ...]`, `excludes: tuple[ContextId, ...]`. No `ist`, no lifting parameters, no `ab1`/`ab2`, no `value(c, term)`, no `corefer`, no `specializes`, no `presentIn`.

`ContextHierarchy` (`propstore/context_hierarchy.py:60-64`):

```python
def is_visible(self, querying_ctx: str, claim_ctx: str) -> bool:
    if claim_ctx == querying_ctx:
        return True
    return claim_ctx in self.ancestors(querying_ctx)
```

This is a tree-ancestry filter. Claims are "visible" in a context iff the claim's context is the querying context or a (transitive) parent. There is no `ist(c, p)` predicate, no lifting rules, no entering/leaving contexts, no transcendence mechanism. `excludes` is a symmetric pair-set (`context_hierarchy.py:27-30`) used by `are_excluded`, with no attached logical semantics about why contexts conflict.

Grep of `propstore/` for McCarthy-1993 machinery:
- `ist\(c|lifting|bridge_rule|LocalModels|MCS` → 0 files
- References to McCarthy 1993 by name: 2 hits, both about temporal specialization, not ist (`propstore/z3_conditions.py:426`, `propstore/_resources/forms/timepoint.yaml:8`)

Compare `McCarthy_1993/notes.md` which catalogs `ist(c, p)`, `value(c, term)`, `specializes(c1,c2)` with `ab1`/`ab2`, `specialize-time(t, c)`, `assuming(p, c)`, quantifier rules for `present(c, x)`, the blocks-world derivation (eqs 5-15), and transcendence. None of these appear in the code.

Compare `Guha_1991/notes.md` which catalogs `ist(c, F)` satisfaction, `CM(C)` structure sets, `presentIn(c, A)`, `corefer(C1, A, C2, B)`, lifting rules (DCR, CR), Problem-Solving Context. None appear in the code.

Kallem 2006 Microtheories and Ghidini 2001 Local Models Semantics (both in Cluster 3d, manifest lines 809-819) — also absent from code. There is no Tarskian local-models semantics, no bridge rules.

**Evidence:** `propstore/context_types.py:16-39`, `propstore/context_hierarchy.py:11-64`, `propstore/validate_contexts.py:29-90`, grep results.

**Recommendation:** Either implement a minimal `ist(c, p)` layer (context-qualified claim visibility + at least one lifting rule type), or remove the "first-class logical objects qualifying truth" claim from `CLAUDE.md` and replace with "inheritance-tagged visibility scopes."

---

### 2. Frame-element structure — Fillmore 1982 / Baker 1998 / Narayanan 2014

**Verdict: ABSENT**

`ConceptRecord` (`propstore/core/concepts.py:126-145`):

```python
@dataclass(frozen=True)
class ConceptRecord:
    artifact_id: ConceptId
    canonical_name: str
    status: ConceptStatus
    definition: str
    form: str
    logical_ids: tuple[LogicalId, ...]
    version_id: str
    domain: str | None = None
    definition_source: str | None = None
    form_parameters: dict[str, Any] | None = None
    range: tuple[float, float] | None = None
    aliases: tuple[ConceptAlias, ...] = ()
    relationships: tuple[ConceptRelationship, ...] = ()
    parameterizations: tuple[ParameterizationSpec, ...] = ()
    replaced_by: ConceptId | None = None
    created_date: str | None = None
    last_modified: str | None = None
    notes: str | None = None
```

No `frame`, `frame_elements`, `frame_id`, `lexical_unit`, no FE/PT/GF annotations. `aliases` are plain `{name, source, note}` (`core/concepts.py:49-60`) — surface-form strings with provenance, not FrameNet lexical units.

`ConceptRelationshipType` (`propstore/core/concept_relationship_types.py:8-17`):

```python
class ConceptRelationshipType(StrEnum):
    BROADER = "broader"
    NARROWER = "narrower"
    RELATED = "related"
    COMPONENT_OF = "component_of"
    DERIVED_FROM = "derived_from"
    CONTESTED_DEFINITION = "contested_definition"
    IS_A = "is_a"
    PART_OF = "part_of"
    KIND_OF = "kind_of"
```

These are SKOS + basic ontology relations. A Fillmorean frame would require at least `FRAME_ELEMENT_OF`, `EVOKES_FRAME`, or `PERSPECTIVE_ON` — none present.

Grep of `propstore/` for any frame vocabulary (`frame_element|frame_type|frame_semantics|FrameNet|\bframe\b` case-insensitive): 1 file — `propstore/opinion.py` — and all hits there are "binomial frame" meaning Dempster–Shafer frame of discernment (`opinion.py:121,123,141,144-145,493-494`), not Fillmore frames.

The Fillmore commercial-transaction example (BUY/SELL/PAY/SPEND/COST/CHARGE all evoking one frame with perspective differences), cataloged in `notes/fillmore-1982-processing.md` at "Section 2", has no counterpart structure in `ConceptRecord`.

**Evidence:** `propstore/core/concepts.py:126-145`, `propstore/core/concept_relationship_types.py:8-17`, grep of entire `propstore/`.

---

### 3. Qualia — Pustejovsky 1991

**Verdict: ABSENT**

Grep of `propstore/` for `qualia|telic|agentive|constitutive|proto_role|proto-role|protoagent|protopatient`: **zero files**.

Pustejovsky's four qualia roles (constitutive, formal, telic, agentive — documented in `notes/pustejovsky-1991-reading.md` Sec 5.3 and Ex 38) have no corresponding field on `ConceptRecord`. There is no Event Structure (states/processes/transitions), no Argument Structure, no type-coercion mechanism, no cocompositionality.

The closest `ConceptRecord` field is `definition: str` — a free-text definition. `form_parameters: dict[str, Any]` is used for form-specific constraints (e.g., `category` concepts store an allowed `values` list; `cli/concept.py:340-360`), not qualia.

Pustejovsky 2013 Dynamic Event Structure (manifest line 845-849) — also absent. No DITL-typed records, no scale-typed attributes beyond the dimensional `form` system.

**Evidence:** grep of entire `propstore/`; `core/concepts.py:126-145`.

---

### 4. Lemon linking — Buitelaar 2011

**Verdict: ABSENT**

Grep of `propstore/` for `lemon|LexicalEntry|LexicalForm|LexicalSense|lexicon`: **zero files**.

The `form` field on `ConceptRecord` (`core/concepts.py:132`) is a *dimension-kind* string, not a lemon lexical Form. `form_utils.py:106-112` maps form names to `KindType.{QUANTITY, CATEGORY, BOOLEAN, STRUCTURAL, TIMEPOINT}`. `form_utils.py:67-77` shows `FormDefinition` carries `name`, `kind`, `unit_symbol`, `allowed_units`, `is_dimensionless`, `parameters`, `dimensions: dict[str, int] | None`, `extra_units`, `conversions: dict[str, UnitConversion]`. This is a pint-compatible physical-unit definition (`form_utils.py:26`: `ureg = pint.UnitRegistry()`), not a lemon Form (morphosyntactic realization).

`cli/form.py` confirms: form creation takes `unit_symbol`, `qudt` (QUDT unit IRI), `dimensions` JSON (SI exponents), `common_alternatives`. These are physical-measurement inputs, not lexical-morphological inputs.

The lemon core four-node chain — Ontology Entity ← Lexical Sense ← Lexical Entry → Lexical Form — has no structural analogue. `ConceptAlias` (`core/concepts.py:49-60`) exists but is flat name+source+note, not a LexicalEntry with a LexicalSense link.

`notes/paper-processing-buitelaar-2011.md:139-148` itself explicitly flags lemon as a gap: "This paper provides the missing formalism underneath propstore's concept registry and vocabulary reconciliation layer." The paper notes describe the expected fit but the code has not adopted the model.

**Evidence:** grep of entire `propstore/`; `propstore/form_utils.py:46-172`, `propstore/cli/form.py:158-251`.

---

### 5. Micropublication structure — Clark 2014

**Verdict: PARTIAL**

What is present:
- `claims.py` loads typed `ClaimsFileDocument` with `source: ClaimSourceDocument(paper)` — Attribution at paper level.
- `source/claims.py:225-237` attaches `SourceProvenanceDocument(paper, page)` — Reference qualifier.
- `stances.py:8-15` defines `StanceType.{REBUTS, UNDERCUTS, UNDERMINES, SUPPORTS, EXPLAINS, SUPERSEDES, NONE}` — maps onto Clark's `supports`/`directlyChallenges`/`indirectlyChallenges` with added SUPERSEDES.
- `source/relations.py:30-95` handles `SourceJustificationDocument(conclusion, premises, rule_kind, attack_target)` — Pollock/ASPIC-style premise list supports Clark's SupportGraph element modelling.

What is missing (relative to `Clark_2014/notes.md`):
- **No typed Micropublication object**. There is no single dataclass that corresponds to `MP = (A_mp, c, A_c, Phi, R)` with invariants "exactly one Claim" + "R+ is a strict partial order" + "A_mp is the Attribution of the MP formalization".
- **No Holotype/Similarity Group mechanism**. The `hasHolotype` property in Clark (`notes/clark-2014-micropublications.md` Key Properties table) has no analogue. Propstore does vocabulary alignment (`source/alignment.py`), but it builds a PartialArgumentationFramework, not a Similarity Group with a canonical representative.
- **No asserts-vs-quotes distinction**. Claims carry `source_local_id` (`source/claims.py:100-107`) but not a Clark-style `assertedBy` vs `quotedBy` attribution distinction.
- **No SupportGraph / ChallengeGraph typed objects** as Clark specifies. Claims + stances + justifications form an equivalent informational structure but without the graph-object typing and the invariants (Claim as greatest element of R+).

Paper-collection drift: `Clark_2014_Micropublications/` and `Clark_2014_MicropublicationsSemanticModel/` are both present; only `MicropublicationsSemanticModel/` carries `paper.pdf`. Both carry a `notes.md` with overlapping but non-identical content (`bash diff` confirmed they differ). Propstore code references neither directory and contains no mentions of "micropub" (grep: 0 hits). Severity: LOW code drift, but flag this for Axis 9 doc-drift.

**Evidence:** `propstore/claims.py:58-71`, `propstore/stances.py:8-15`, `propstore/source/claims.py:100-120`, `propstore/source/relations.py:30-95`; `bash diff -q` on the two Clark directories.

---

### 6. Provenance — Buneman 2001 / Carroll 2005 / Green 2007

**Verdict: LABEL-ONLY (vs. Buneman) · ABSENT (Carroll, Green)**

`propstore/provenance.py` is a **file-stamping utility**. It writes a `produced_by: {agent, skill, plugin_version, timestamp}` block into YAML frontmatter (`provenance.py:29-43`) or top-level YAML (`provenance.py:96-120`), and exposes `stamp_file(path, agent, skill, ...)` (`provenance.py:127-150`). This is agent-attribution provenance — "who ran which script when" — not data provenance.

What Buneman 2001 formalizes (from metadata.json: "Why and Where: A Characterization of Data Provenance"): **why-provenance** (which source tuples contributed to the output) and **where-provenance** (which source cells a value was copied from). Grep of `propstore/` for `why_prov|where_prov`: 0 hits.

What Carroll 2005 formalizes: RDF **named graphs** — graphs whose names are IRIs, enabling meta-statements about provenance/trust of each graph. Grep of `propstore/` for `named_graph`: 0 hits. The `propstore/repo/` git-backed store does carry commit-level attribution, but there is no named-graph semantics exposed at the data layer.

What Green 2007 formalizes: K-annotated tuples where K is a commutative semiring, subsuming bag/set/why-provenance/lineage. No K-annotation anywhere in `propstore/`.

Separately, source-level provenance at claim ingestion uses `SourceProvenanceDocument(paper, page)` (`artifacts/documents/sources.py` referenced from `source/claims.py:225`) — paper + page number. This is a shallow reference pointer, not why/where-provenance over the derivation chain.

Caveat: Buneman_2001 and Carroll_2005 paper directories contain **metadata.json only** (`papers/Buneman_2001_CharacterizationDataProvenance/metadata.json`, `papers/Carroll_2005_NamedGraphsProvenanceTrust/metadata.json`) with no notes.md, no PDF. The manifest (lines 893-903) flagged these as stubs; confirmed. So propstore has not read these papers deeply.

**Evidence:** `propstore/provenance.py:127-150` (entire file), `papers/Buneman_2001_.../metadata.json`, `papers/Carroll_2005_.../metadata.json`, grep of `propstore/`.

---

### 7. sameAs / concept identity — Beek 2018 / Halpin 2010 / Raad 2019 / Melo 2013

**Verdict: ABSENT for sameAs closure; alignment does something different**

Grep of `propstore/` for `sameAs|same_as|owl:sameAs|closure_set|similarity_link`: **zero files**.

`propstore/identity.py` is pure hashing + regex validation:
- `CLAIM_ARTIFACT_ID_RE`, `CONCEPT_ARTIFACT_ID_RE` (lines 12-15) validate `ps:claim:...` / `ps:concept:...` tokens.
- `derive_claim_artifact_id(namespace, value)` (line 54) and `derive_concept_artifact_id` (line 64) hash `namespace:value` and take the first 16 hex chars of SHA-256.
- `compute_claim_version_id` / `compute_concept_version_id` (lines 202, 220) hash canonical content for immutable version IDs.

There is no union-find, no transitive closure, no Beek-style identity-set computation, no Melo 2013 minimum-multicut repair, no Halpin 2010 graded similarity ontology.

What propstore does instead for "concept alignment" (`propstore/source/alignment.py`):

```python
def classify_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["proposed_name"] == right["proposed_name"] and left["form"] == right["form"]:
        return "attack" if left["definition"] != right["definition"] else "non_attack"
    if left["form"] == right["form"] and token_overlap(left["definition"], right["definition"]) >= 0.5:
        return "ignorance"
    return "non_attack"
```
(`source/alignment.py:52-57`)

`token_overlap` (`source/alignment.py:42-49`) is **Jaccard similarity on underscore-separated tokens** of `alignment_slug(string)`. `alignment.py:107-114` then builds a `PartialArgumentationFramework` over the alignment proposals with attack/ignorance/non_attack edges and runs `skeptically_accepted_arguments` / `credulously_accepted_arguments`. Accepted alternatives can then be decided and promoted to canonical concepts (`alignment.py:216-284`).

This is a **non-commitment-style alignment via argumentation on proposals**, which honors CLAUDE.md's design principle (disagreement preserved). But it is structurally unrelated to sameAs closure. It is also **literal-string matching** (Jaccard ≥ 0.5 on definition tokens), not frame-level matching.

**This directly contradicts CLAUDE.md**: "Vocabulary reconciliation operates at the frame level, not string level." Severity: HIGH. The code operates at the string-token level.

**Evidence:** `propstore/identity.py:1-225`, `propstore/source/alignment.py:42-57`, `propstore/source/alignment.py:107-114`; grep of entire `propstore/`.

---

## Smaller findings

### Dowty 1991 Proto-roles — ABSENT
Grep `proto_role|proto-role|protoagent|protopatient`: 0 hits. No thematic role representation.

### Wein 2023 CrossLinguistic AMR — ABSENT
No AMR structures, no Smatch, no cross-lingual alignment.

### Gruber 1993 Ontology Design Principles — INSPIRED-BY
No explicit "minimal ontological commitment" surface; general clarity/coherence practiced in code.

### Juty 2020 PIDs / Kuhn 2014 TrustyURIs — INSPIRED-BY
`propstore/uri.py:19-46`: tag: URIs (RFC 4151) for source/concept/claim; ni:/// URIs (RFC 6920) for content hashes. Close to Kuhn's TrustyURI but lacks the module-marker convention (`trusty:<module>:<base64>`) and granular-reference retrieval layer.

### Wilkinson 2016 FAIR — INSPIRED-BY
Versioned, content-addressable, formally typed. F/A/I/R principles not explicitly surfaced.

### Groth 2010 Nanopublication — PARTIAL
Claims carry artifact ID + source attribution + version hash. No RDF named graphs.

---

## Paper collection drift flag

- `papers/Buneman_2001_CharacterizationDataProvenance/` — metadata.json only, no notes.md, no PDF. Stub confirmed per manifest line 897.
- `papers/Carroll_2005_NamedGraphsProvenanceTrust/` — metadata.json only. Stub confirmed per manifest line 903.
- `papers/Clark_2014_Micropublications/` and `papers/Clark_2014_MicropublicationsSemanticModel/` — both present on disk. `notes.md` differs between the two (bash diff confirmed). Only `MicropublicationsSemanticModel/` has `paper.pdf`. Recommendation: consolidate to the SemanticModel directory (it has the pdf + full pngs); the other is a leftover from an earlier processing run.
- `papers/Fillmore_1982_FrameSemantics/` — has notes.md, paper.pdf, pngs. Fully processed but 0 code references.
- `papers/Pustejovsky_1991_GenerativeLexicon/` — fully processed; 0 code references.
- `papers/McCarthy_1993_FormalizingContext/` — fully processed; 2 code references (both peripheral, about temporal context, not ist(c,p)).
- `papers/Buitelaar_2011_OntologyLexicalizationLemon/` — fully processed; 0 code references. `notes.md:139-148` itself explicitly identifies lemon as the missing formalism that would fit underneath propstore's concept registry.
- `papers/Beek_2018_SameAs.ccClosure500MOwl/` — fully processed (even has claims.yaml). 0 code references to sameAs closure.

---

## Severity-ordered findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| 1 | **crit** | CLAUDE.md claims "frame elements (Fillmore 1982) with structured internal composition (Pustejovsky 1991 qualia)" — code has zero frame-element and zero qualia structure | `core/concepts.py:126-145`, grep |
| 2 | **crit** | CLAUDE.md claims "concept registry formally links linguistic expressions to ontological entities (lemon model)" — no lemon anywhere; `form` is a dimensional kind | `form_utils.py:46-172`, grep |
| 3 | **crit** | CLAUDE.md claims "Contexts are first-class logical objects qualifying when propositions hold (McCarthy 1993 ist(c, p))" — contexts are ancestry-visibility tags | `context_types.py:16-39`, `context_hierarchy.py:60-64` |
| 4 | **high** | CLAUDE.md claims "Vocabulary reconciliation operates at the frame level, not string level" — reconciliation is Jaccard ≥ 0.5 on definition tokens | `source/alignment.py:42-57` |
| 5 | **high** | `provenance.py` is agent-attribution stamping; no why/where provenance (Buneman), no named graphs (Carroll), no semirings (Green) | `provenance.py` entire file |
| 6 | **high** | No sameAs closure (Beek), no identity repair (Melo), no graded identity (Halpin) — identity module is pure version-hashing | `identity.py:1-225` |
| 7 | **med** | No Holotype / Similarity Group mechanism despite micropublication model being partially adopted | `stances.py`, `claims.py`, `source/claims.py` |
| 8 | **med** | No typed `MP = (A_mp, c, A_c, Phi, R)` dataclass; claims + stances + justifications carry the information but without invariant-preserving typing | `claims.py`, `source/relations.py` |
| 9 | **low** | Clark_2014 paper directory duplicated on disk with diverging notes.md | `papers/Clark_2014_Micropublications/` vs `/MicropublicationsSemanticModel/` |
| 10 | **low** | Buneman_2001 and Carroll_2005 are metadata-only stubs — the foundational provenance papers have not been read into the project | `papers/Buneman_2001_*/`, `papers/Carroll_2005_*/` |
| 11 | **note** | `ConceptRelationshipType` uses SKOS relations (BROADER/NARROWER/RELATED/IS_A/PART_OF/KIND_OF) — this is faithful SKOS even if CLAUDE.md doesn't cite Miles 2005 | `core/concept_relationship_types.py:8-17` |
| 12 | **note** | URI surface is solid inspired-by: RFC 4151 tag: + RFC 6920 ni:/// — good hygiene without claiming Kuhn TrustyURI compliance | `uri.py:19-46` |

---

## How much of the semantic rhetoric in CLAUDE.md is cashed out in code?

Honest assessment. Quoting the CLAUDE.md "Concept/semantic layer" paragraph and scoring each clause:

> "Concepts are not labels; they are frame elements (Fillmore 1982) with structured internal composition (Pustejovsky 1991 qualia)."

**FALSE as written.** Concepts are labels. `ConceptRecord` (`core/concepts.py:126-145`) has no frame-element structure, no qualia structure. There is a `definition` text field, not a qualia decomposition.

> "The concept registry formally links linguistic expressions to ontological entities (lemon model)."

**FALSE as written.** No lemon model. The `form` field is a dimension-kind, not a lemon Form. `ConceptAlias` is flat `{name, source, note}`, not a LexicalEntry with sense-disambiguation link.

> "Contexts are first-class logical objects qualifying when propositions hold (McCarthy 1993 `ist(c, p)`)."

**FALSE as written.** Contexts are ancestry-visibility tags plus assumption strings. No `ist`, no lifting, no `value`, no `corefer`.

> "Forms define dimensional structure; CEL + Z3 provide type-checking and condition reasoning."

**TRUE.** Forms (`form_utils.py`) encode SI dimensions + unit conversions; `cel_checker.py` and `z3_conditions.py` typecheck CEL against form kinds and solve conditions. This clause is cashed out.

> "`KindType.TIMEPOINT` maps to `z3.Real` (same as QUANTITY) but is semantically distinct — not valid for parameterization or dimensional algebra."

**TRUE** (based on `validate_concepts.py:354-358`: "parameterization input '…' must be quantity kind"). Cashed out.

> "Vocabulary reconciliation operates at the frame level, not string level."

**FALSE as written.** Reconciliation is Jaccard ≥ 0.5 on definition tokens (`source/alignment.py:42-57`), plus equal proposed_name + form for exact matches, plus argumentation-framework resolution over proposals. The string-token Jaccard is the literal opposite of "frame level."

**Net:** Of 6 clauses in the concept/semantic paragraph, 2 are cashed out (forms + CEL/Z3) and 4 are misdescriptions. The four misdescriptions are precisely the ones that reference semantic-substrate papers (Fillmore, Pustejovsky, lemon, McCarthy) and that would distinguish propstore as a "semantic OS" from a "physical-quantities-plus-ontology-plus-stances" system.

**What propstore actually has** — and this is substantial and good, just not the thing CLAUDE.md names — is:

1. A dimensional-quantity system (forms + units + pint + bridgman) with real dimensional algebra validation (`validate_concepts.py:361-449`).
2. A SKOS-style concept taxonomy with BROADER/NARROWER/IS_A/PART_OF/KIND_OF/COMPONENT_OF relations.
3. A visibility-scoped context inheritance tree with mutual-exclusion pairs.
4. A claim-stance-justification-source model that partially implements Clark's micropublication information (but without the formal typing and without Holotypes).
5. A non-commitment proposal pipeline (`source/alignment.py`) that honors the design principle even if it operates at string level.
6. Content-addressable versioning via SHA-256 (identity.py) and tag:/ni: URIs (uri.py), inspired-by Kuhn TrustyURI and Juty PIDs.

This is a coherent stack, but it is not the stack CLAUDE.md names. A "semantic OS" in the Fillmore/Pustejovsky/Buitelaar/McCarthy sense would require: frame-structured concepts with FE slots, qualia role decomposition, lemon sense-disambiguation for surface forms, and `ist(c, p)` context logic. None of these are present.

---

## Open questions

- I did not read `propstore/cel_registry.py` or `propstore/classify.py`; the manifest links Fillmore/Baker/Narayanan to these files but the names suggest CEL-type registry and text classification. Possible that some frame structure lives there; grep over whole `propstore/` with comprehensive terminology yielded 0 hits, so unlikely, but not directly verified.
- I did not read `propstore/relate.py`, which the manifest links to Wein 2023 AMR. Grep for AMR/Smatch/xling yielded nothing, so I inferred absent, but did not directly verify.
- I did not run any tests; all findings are from source inspection. Runtime behavior (e.g., whether the alignment PAF actually produces sensible reconciliation outputs on real data) is not verified.
- I did not verify whether the CLI `pks concept align` command produces frame-aware output anywhere downstream. Based on `source/alignment.py:42-57`, it operates on string tokens of definitions — unless there is a hidden frame-lookup layer I did not find, the alignment is literal-string.
- I did not check whether Narayanan 2014 FrameNet-bridging or Wein 2023 cross-lingual AMR code lives in `propstore/grounding/` — this directory exists (`ls` listing) but was outside the specified target modules. Grep over the whole `propstore/` tree found no frame/AMR/qualia/lemon terminology, so I believe they are absent, but the grounding directory specifically was not audited.
- Severity assignments reflect the gap between CLAUDE.md's rhetoric and observed code. If CLAUDE.md's rhetoric were rewritten to describe the actual system (dimensional quantities + SKOS + inheritance contexts + string-level alignment + partial micropublication), most of the "crit" findings would become "note." The severity is about the drift, not the code.
- I did not verify whether propstore ever *intends* to implement lemon / frames / qualia / ist(c,p), or whether CLAUDE.md is aspirational rhetoric. If aspirational, it should be in "Known Limitations," not in the core architectural description.
