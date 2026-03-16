# Propositional Knowledge Store — Design Document

## The Problem

The research-papers plugin is a knowledge compiler with no IR.

PDFs go in. What comes out is structured extraction: equations, parameters with ranges
and units, testable properties, methodologies, stances, cross-references. The reconcile
skill finds tensions between findings, mechanisms that explain observations in other
papers, conceptual convergence across different research traditions. This is genuine
knowledge synthesis — not citation management.

But it lowers into flat markdown files. Every downstream operation — find contradictions,
trace a claim, resolve conflicting parameter values — requires an LLM to re-derive what
should already be structurally obvious. Grep over 370 markdown files. Flat tags. An
index.md that's just a list.

The unit of storage is wrong. Papers contain claims, but papers are the atoms. The
inversion: **store claims that cite papers**.

## Core Principle

**SSA for knowledge.** Every proposition gets one canonical statement. Each has a unique
identity. Each paper is a source that *defines* or *references* propositions. When a new
paper reports a different value for the same phenomenon under different conditions, that's
a φ-node — "under conditions A the value is X, under conditions B the value is Y" — not
a contradiction.

This is the same principle across all of Q's projects:

- **Qlatt**: declare rules in YAML with citations, compile to the synthesizer
- **Uniform**: bijective parse/render, the IR preserves everything
- **physgen**: dimensional analysis enforces correctness by constraint
- **polyarray**: declare once in YAML, compile to 18 languages

The move: **compile, don't interpret. Make the machine be brilliant mechanically.**

## Architecture: Three Stages, Two Boundaries

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│  LLM reads  │         │  Mechanical   │         │   Query index   │
│  papers     │────────▶│  compiler     │────────▶│   (sidecar)     │
│             │  YAML   │  (Python, no  │  derived│                 │
│  (extract)  │  claims │   LLM)        │  store  │  sqlite-vec,    │
│             │         │               │         │  FTS5, +/- RDF  │
└─────────────┘         └──────────────┘         └─────────────────┘
      ▲                       ▲                          │
      │           ┌───────────┴──────────┐               │
      │           │  Concept Registry    │               │
      │           │  (YAML files, peer   │               │
      │           │   to claim store)    │               │
      │           │                      │               │
      │           │  concepts/*.yaml     │               │
      │           │  LinkML schema       │               │
      │           │  QUDT units          │               │
      │           │  parameterization    │               │
      │           │  relationships       │               │
      │           └───────────┬──────────┘               │
      │                       │                          │
      │           ┌───────────┴──────────┐               │
      └───────────│  LLM assists         │◀──────────────┘
                  │  proposition ID +    │  candidate matches
                  │  concept alignment   │  via embeddings
                  │  (φ-node judge)      │
                  └──────────────────────┘
```

### Stage 1: LLM Extraction → YAML Claim Files

The paper-reader skill produces notes.md (human narrative) AND structured claim YAML
(machine-readable propositions). These are the parse tree. Human-readable, inspectable,
editable, git-diffable. This is what you actually look at.

### Stage 2: Mechanical Compiler → Sidecar Index

A deterministic Python compiler (no LLM) lowers the YAML into a queryable sidecar.
Reproducible — run it twice, get the same output. If something looks wrong in a query
result, check the YAML source file, not the compiled index.

The sidecar is **derived, not primary**. You never edit it. You never look at it.
If it corrupts, recompile from YAML source. This is Uniform's bijective principle:
the YAML is the source representation, the index is the compiled output.

### Stage 3: LLM Proposition Identity (the φ-node decision)

The one place the LLM re-enters: "Is this new claim from Paper 371 the same proposition
as an existing one, or a new one?" Embeddings do candidate generation (semantic
similarity via sqlite-vec). LLM confirms and classifies the relationship.

**Critical**: the decision gets *recorded in the YAML* as an explicit link:
```yaml
same_as: claim_0847
# or
refines: claim_0233
# or
contradicts: claim_0119
conditions_differ: "speaking rate > 5 syllables/sec vs. normal"
```

After that, the mechanical compiler just follows the pointer. The LLM makes the judgment
once, writes it down, and everything downstream is structure.

### Why Separate Extraction from Lowering?

Same reason Qlatt has separate pipeline stages instead of one giant prompt. If the
summarizer LLM emits the lowered representation directly:

- Can't see what it extracted before compilation
- Can't debug whether a bad query result is from wrong extraction or wrong lowering
- Lose the intermediate representation
- Non-reproducible (LLM output varies)

The YAML is the parse tree. The sidecar is the compiled binary. You debug at the
parse tree level.

## The True Name Problem: Concept Registry

The hardest problem isn't storing claims — it's knowing when two claims are about
the same thing. Paper A calls it `Ps`. Paper B calls it `subglottal pressure`.
Paper C calls it `P_sub`. Paper D calls it `lung pressure` and means something
slightly different. Gobl calls it `ra`, Fant calls it the same but normalizes
differently, and someone else calls it `return phase ratio`.

Without a concept registry, cross-referencing is string matching. With one, you
can ask "show me every claim about subglottal pressure" regardless of what each
paper called it.

### Architecture

The concept registry is a **peer to the claim store**, not a layer above or below it.
Claims bind to concept IDs, not to paper-local variable names.

```
concepts/
  subglottal_pressure.yaml     # concept_0012
  fundamental_frequency.yaml   # concept_0001
  return_phase_ratio.yaml      # concept_0089
  open_quotient.yaml           # concept_0034
  ...
```

Each concept file:

```yaml
# concepts/subglottal_pressure.yaml
id: concept_0012
status: accepted  # proposed | accepted | deprecated
canonical_name: subglottal_pressure
definition: >
  Air pressure below the glottis during phonation,
  measured or estimated at the tracheal level.
definition_source: Titze_1994_PrinciplesVoiceProduction

aliases:
  - { name: "Ps",     source: Sundberg_1993 }
  - { name: "P_sub",  source: Holmberg_1988 }
  - { name: "P_s",    source: Titze_1994 }
  - { name: "lung pressure", source: Lieberman_1967,
      note: "approximate; includes tracheal losses" }

unit:
  qudt: qudt:PA          # QUDT URI for pascals
  common_alternatives:
    - { unit: cmH2O, multiplier: 98.0665 }
    - { unit: hPa,   multiplier: 100.0 }

domain: speech_physiology

relationships:
  - type: component_of
    target: concept_0045  # transglottal_pressure
  - type: drives
    target: concept_0003  # voicing_amplitude
  - type: related
    target: concept_0078  # intraoral_pressure
```

### Parameterization Relationships — The Novel Piece

No existing system captures algebraic relationships between different
parameterizations of the same phenomenon. QUDT handles unit conversion.
Dimensional analysis handles derived quantities. But "Gobl's ra = Fant's
Ra / T0" is neither — it's same-phenomenon re-parameterization.

This is a genuine gap in the literature. The concept registry fills it:

```yaml
# concepts/return_phase_ratio.yaml
id: concept_0089
canonical_name: return_phase_ratio
aliases:
  - { name: "ra", source: Gobl_1988 }
  - { name: "Ra", source: Fant_1985, note: "unnormalized" }

parameterization_relationships:
  - formula: "gobl_ra = fant_Ra / T0"
    sympy: "Eq(gobl_ra, fant_Ra / T0)"
    inputs: [concept_0089_gobl, concept_0089_fant, concept_0001]
    source: Gobl_1988
    note: "Gobl normalizes by fundamental period"
    bidirectional: true

  - formula: "ra = ta / T0"
    sympy: "Eq(ra, ta / T0)"
    inputs: [concept_0089, concept_0091, concept_0001]
    source: Fant_1985_LFModelGlottalFlow
    note: "Definition in terms of return phase time constant"
    bidirectional: true
```

And for the non-trivial cases:

```yaml
# concepts/open_quotient.yaml
id: concept_0034
canonical_name: open_quotient

parameterization_relationships:
  - formula: "OQ + CQ = 1"
    sympy: "Eq(OQ + CQ, 1)"
    inputs: [concept_0034, concept_0035]
    bidirectional: true
    source: multiple

  - formula: "OQ = 1 / (2 * Rg * (1 + Rk))"
    sympy: "Eq(OQ, 1 / (2 * Rg * (1 + Rk)))"
    inputs: [concept_0034, concept_0036, concept_0037]
    source: Fant_1995
    bidirectional: false  # regression-derived, not exact
    note: "Approximate; assumes symmetric opening phase"
```

This means when the compiler encounters `ra = 5%` in one paper and
`Ra = 0.005` in another, it can *mechanically check* whether these are
consistent by following the parameterization chain. physgen does this for
physical dimensions. This does it for parameterizations.

### Intake Pipeline

For ~370 papers at ~200-2000 concepts, the whole registry fits in an LLM
context window. Hybrid LLM-classical alignment achieves F1 0.83-0.95 on
biomedical benchmarks. Cost: ~$0.05-0.20 per paper.

Pipeline:
1. Paper-reader LLM extracts variables/terms with their paper-local names
2. Exact string match against existing concept labels/aliases
3. Embedding similarity on definitions for non-exact matches
4. LLM evaluates borderline cases (with existing concept definitions in context)
5. Human reviews proposed new concepts and contested matches
6. Accepted mappings written into paper's claims.yaml; new concepts get files

LLM failure modes to watch for:
- Polysemy confusion ("peak" vs "average" variants of same measure)
- Align-up errors (mapping to superclass: "pressure" instead of "subglottal pressure")
- Conflating differently-normalized variants (the ra/Ra problem)
- Confidence scores are NOT calibrated — human review is non-optional

### Design Principles (from real failures)

Five lessons from CDISC, CF Conventions, BIDS, OBO Foundry, and Cyc's $60M:

1. **Start minimal**: 200 well-defined concepts beats an elaborate OWL ontology
   with 50. LinkML provides schema that generates JSON Schema + Python + RDF
   from a single YAML source.

2. **Never delete, only deprecate**: Every concept gets a permanent ID.
   Deprecated concepts link to successors. Universal lesson from every surviving
   vocabulary.

3. **Separate proposal from acceptance**: Even solo, the "sleep on it" principle
   prevents vocabulary drift. New concepts start as `status: proposed`.

4. **Enforce through tooling, not policy**: The compiler rejects claims that
   reference unregistered concepts. This makes adoption self-enforcing.

5. **Budget for maintenance**: OBO Foundry's 25% obsolescence rate shows that
   creation without maintenance planning produces orphans. Keep scope narrow
   enough for one person to maintain.

### SKOS for the Taxonomy Layer

Tags become a SKOS concept scheme in the sidecar. `acoustics` → `glottal-source`
→ `lf-model` gets `broader`/`narrower` relationships. The flat tag list in
description.md frontmatter becomes a reference into the taxonomy. Lightweight —
SKOS is dramatically simpler than OWL while covering 90% of vocabulary needs.

## Claim Types (Refined from Actual Notes)

Looking at actual notes.md files, most claims aren't fuzzy prose — they're
**parameter bindings with conditions**. The claim schema needs first-class
types for the common patterns.

### Type: parameter

The dominant form. Each row in Gobl's Table III is one of these.

```yaml
- id: claim_0042
  type: parameter
  concept: concept_0089  # return_phase_ratio
  value: [2, 3]
  unit: "%"
  conditions:
    context: vowels
    population: adult
  source:
    paper: Gobl_1988
    table: "III"
    page: 12
```

### Type: equation

Explicit mathematical relationships with fit statistics.

```yaml
- id: claim_0088
  type: equation
  expression: "log(Ps) = 1.00 + 0.88 * log(F0)"
  sympy: "Eq(log(Ps), 1.00 + 0.88 * log(F0))"
  variables:
    Ps: { concept: concept_0012, role: dependent }
    F0: { concept: concept_0001, role: independent }
  fit:
    r: 0.965
    r_sd: 0.04
    slope: 0.88
    slope_sd: 0.186
  conditions:
    population: male singers
    phonation: mixed
  source:
    paper: Sundberg_1993
    table: "3"
    page: 19
```

### Type: observation (qualitative)

For claims that resist parameterization.

```yaml
- id: claim_0103
  type: observation
  statement: >
    Pulse shape becomes more symmetrical as F0 approaches F1,
    with skewing asymptotically approaching 0.6 when F1/F0 > 3.
  concepts: [concept_0001, concept_0022, concept_0048]
  conditions:
    domain: singing
    range: "F1/F0 ratio < 3"
  source:
    paper: Sundberg_1993
    page: 23
    figure: "Fig. 6"
```

### Type: model (parameterized equation system)

For multi-equation frameworks like Broad & Clermont's transition model.

```yaml
- id: claim_0200
  type: model
  name: "Exponential transition model (Model IVb)"
  equations:
    - "f_CV(t) = kappa_C * (T_V - L_C) * exp(-beta_C * t)"
    - "g_VC(t') = kappa'_C * (T_V - L'_C) * exp(-beta'_C * t')"
    - "F_CVC(t) = f_CV(t) + T_V + g_VC(t)"
  parameters:
    L_C: { concept: concept_0150, note: "consonant locus" }
    T_V: { concept: concept_0151, note: "vowel target" }
    beta_C: { concept: concept_0152, note: "reciprocal time constant" }
    kappa_C: { concept: concept_0153, note: "exponential scale factor" }
  parameter_values_source:
    paper: Broad_Clermont_1987
    table: "VI"
    # actual values stored as nested parameter claims
  conditions:
    consonants: [b, d, g]
    vowels: "10 American English vowels"
  source:
    paper: Broad_Clermont_1987
    equations: "38-39"
    page: 162
```

## Claim YAML Full Schema

Each paper gets a claim file alongside its notes.md. The schema captures propositions
as first-class objects, not triples. All claims bind to concepts, not paper-local names.

```yaml
# papers/Hertz_1991_StableTransitions/claims.yaml
source:
  paper: Hertz_1991_StableTransitions
  extraction_model: claude-opus-4-20250514
  extraction_date: 2026-03-15
  extraction_prompt_hash: a1b2c3d4

claims:
  - id: claim_0042
    type: empirical_observation
    statement: >
      Formant transitions hold at approximately 65ms duration regardless of
      speaking rate, while steady-state vowel portions stretch proportionally.
    parameters:
      - name: transition_duration
        value: 65
        unit: ms
        range: [50, 80]
        conditions: "normal to fast speaking rates"
    evidence:
      methodology: acoustic analysis of CV syllables
      population: 6 adult speakers of American English
      conditions:
        speaking_rate: [normal, fast, very_fast]
    provenance:
      page: 4
      section: "Results"
      figure: "Fig. 3"
      quote_fragment: "transition durations remained stable at..."
    stances: []  # populated by reconcile / proposition-identity pass

  - id: claim_0043
    type: theoretical_prediction
    statement: >
      The stability of transition duration is consistent with a gesturally
      specified system where transition stiffness is an intrinsic property
      of the articulatory gesture.
    supports:
      - claim_0042
    related_framework: articulatory_phonology
    provenance:
      page: 7
      section: "Discussion"

  - id: claim_0044
    type: parameter_value
    statement: >
      CV formant transition durations for labial consonants average 55ms.
    parameters:
      - name: labial_transition_duration
        value: 55
        unit: ms
        range: [45, 65]
        conditions: "labial stops in VCV context"
    refines: claim_0042  # more specific version
    provenance:
      page: 5
      table: "Table 2"
```

### Stance Relations (populated during reconciliation)

```yaml
stances:
  - type: supported_by
    target: claim_0891  # from another paper
    strength: strong
    note: "Same phenomenon observed with different methodology"
  - type: contradicted_by
    target: claim_0119
    strength: moderate
    conditions_differ: "speaking rate range extended to very slow"
    note: "Contradiction resolves as φ-node: transitions stretch below 2 syl/sec"
  - type: superseded_by
    target: claim_0567
    note: "Later study with larger N and more controlled methodology"
  - type: mechanism_for
    target: claim_0234
    note: "Gestural stiffness explains the stable-transition observation"
```

## The Explain System

Directly modeled on Qlatt's provenance collector. Every claim carries enough information
to answer "why do we believe this?"

The provenance chain:

```
Query: "Why do we believe formant transitions hold at ~65ms?"

→ claim_0042 (Hertz_1991)
  evidence: acoustic analysis, 6 speakers, CV syllables
  supported_by: claim_0891 (Stevens_1998) — same observation, different framework
  supported_by: claim_1203 (Browman_1990) — predicted by gestural model
  contradicted_by: claim_0119 (Lindblom_1963) — but conditions differ (very slow rate)
  φ-node: claim_0119 resolves as boundary condition, not true contradiction
  superseded_by: claim_0567 (Cho_2006) — larger study, confirms with refinement
```

This is a SPARQL query walking named graphs, not an LLM re-reading papers.
Mechanical. Deterministic. Auditable.

## Sidecar Architecture

The compiled sidecar has three layers:

### Layer 1: Structured Claims (pyoxigraph / TriG)

Each paper's claims in a named graph. Typed edges for stances. PROV-O for extraction
provenance. Queryable via SPARQL.

Use cases:
- "Which claims about F0 range conflict?"
- "What is the provenance chain for claim_0042?"
- "Which papers' claims have been superseded?"
- "Show all φ-nodes (conditional contradictions)"

### Layer 2: Semantic Search (sqlite-vec)

Embeddings over claim statements for proposition-identity candidate generation.
Also enables fuzzy queries: "anything about duration and speaking rate?"

### Layer 3: Full-Text Search (FTS5)

Keyword search over claim text and parameters. Catches what embeddings miss:
specific parameter names, numeric values, author names, exact terms.

### All Three Are Derived

If any sidecar layer corrupts or gets out of sync, `python compile.py` rebuilds
it from the YAML claim files. The YAML is always authoritative.

## Relationship to Existing Work

### What We're Taking

- **Nanopublications**: the atomic structure (assertion + provenance + pub info),
  but as YAML files, not TriG authoring
- **Wikidata model**: claims with qualifiers, references, and ranks — our YAML
  schema is essentially this
- **Companions/NextKB**: microtheory-style contextual reasoning, provenance events,
  supersede/retract behavior. Closest architectural ancestor.
- **PROV-O**: provenance vocabulary for the compiled RDF layer
- **LinkML**: schema definition (define once in YAML, compile to JSON Schema for
  validation + RDF for the store). This is polyarray for ontologies.
- **Qlatt's provenance collector**: the explain pattern — every decision carries
  stage, parents, citations, reason

### What We're Not Taking

- **Raw RDF authoring**: sucks to use. YAML is the authoring format.
- **SPARQL as the user interface**: agents query it; humans read YAML files.
- **Cyc's manual encoding**: the LLM is the compiler frontend.
- **Knowledge fusion** (Diffbot/Google KV style): we preserve disagreement,
  not collapse it into probabilities.
- **Full argumentation frameworks** (ASPIC+, Dung): too heavyweight as the
  store model. The stance relations in YAML capture what we need. Could add
  formal argumentation as a reasoning overlay later.

## Pipeline Integration

### How the Research Papers Plugin Changes

The paper-reader skill gains one new output: `claims.yaml` alongside `notes.md`.
The notes.md stays human-narrative. The claims.yaml is structured extraction.

The reconcile skill's markdown-grep approach gets replaced by:
1. New paper's claims.yaml is written by extraction
2. Proposition identity pass: embed new claims, find candidates in sidecar,
   LLM confirms matches and classifies relationships
3. Write stance links into the YAML (both the new paper's and existing papers')
4. Mechanical compiler re-indexes the sidecar

The lint skill gains checks for claim schema validity.

The index is no longer a flat markdown list — it's a compiled artifact.

### Agent Access

The sidecar exposes an MCP server (or just Python functions callable from
Claude Code) with:

- `search_claims(query)` — semantic + keyword hybrid
- `get_claim(id)` — full claim with all stances
- `explain(claim_id)` — provenance chain traversal
- `find_conflicts(topic)` — claims with contradicts/φ-node edges
- `parameter_lookup(name)` — all values for a parameter across papers
- `what_changed(since_date)` — incremental update summary

## Open Questions

### Resolved
- [x] Tag ontology → yes, SKOS concept schemes in the sidecar
- [x] Schema framework → LinkML (YAML source, compiles to JSON Schema + RDF)
- [x] Can LLMs do concept alignment? → yes, F1 0.83-0.97 in hybrid systems
- [x] Unit handling → QUDT for units, custom layer for parameterization relationships

### Still Open
- [ ] Exact LinkML schema definition for claims AND concepts (spike needed)
- [ ] Proposition identity threshold tuning — when is "similar" actually "same"?
- [ ] How to handle claims that span multiple papers (review articles, meta-analyses)
- [ ] Granularity: when is a claim too fine-grained? Too coarse?
- [ ] Should claims.yaml live *inside* each paper directory or in a separate
      claims/ directory? (Inside keeps locality; separate enables cross-paper tools)
- [ ] Versioning strategy for claim IDs when propositions get merged/split
- [ ] How does this interact with the Obsidian vault / knowledge pipeline project?
- [ ] Named graph granularity: one per paper? One per claim?
- [ ] SymPy vs MathML for parameterization relationship formulas
- [ ] How to bootstrap the concept registry from 370 existing notes.md files —
      bulk extraction pass or incremental as papers are re-processed?
- [ ] Concept ID namespace: local integers (concept_0012) or something more
      semantic (speech:subglottal_pressure)?
- [ ] When does a concept alias become a distinct concept? The "lung pressure"
      problem — Lieberman means something slightly different, is that an alias
      with a note or a separate concept with an `approximation_of` edge?
- [ ] How to handle concepts that exist in narratology but have no speech analog
      and vice versa — shared namespace or per-domain registries?
- [ ] Minimum viable concept entry: what fields are actually required vs nice-to-have?
- [ ] The "sleep on it" principle for solo use: proposed→accepted workflow or overkill?

## Prior Art References

### Propositional Store
- Companions/NextKB/PlanB (Northwestern QRG) — closest architectural ancestor
- Ai2 Theorizer — LAW/SCOPE/EVIDENCE structured extraction target
- MDKG — qualified claims with conditions/confidence/provenance
- PROV-K nanopublication extensions — multi-source support/conflict
- AEVS — character-level provenance for extracted claims
- DARPA AIDA/AIF — multi-hypothesis semantic interchange
- W3C PKN (Plausible Knowledge Notation) — draft standard for defeasible knowledge
- SciClaim — typed/qualified scientific assertion extraction

### Concept Registry
- CDISC — top-down clinical variable harmonization (regulatory success, rigidity cost)
- CF Conventions / CF Standard Names — hybrid governance, 2072 names, scaled to IPCC
- BIDS — bottom-up neuroimaging standard, ecosystem lock-in over mandate
- OBO Foundry — most successful coordinated ontology ecosystem, 25% obsolescence rate
- QUDT 3.1.4 — 2896 unit resources, NASA-origin, handles affine conversions but NOT
  parameterization relationships
- OM 2.0 — "best performer worldwide" among unit ontologies
- SKOS — right level of formalism for taxonomy (broader/narrower/related/exactMatch)
- LinkML — YAML schema → JSON Schema + Python + RDF, "polyarray for ontologies"
- Maelstrom Research — "comparability is always context-dependent" (key insight)

### LLM Alignment
- MILA (2025) — F1 0.83-0.95 with 92% reduction in LLM calls
- MapperGPT — GPT-4 recognizes lexical variations, ~67% on hard cases
- Claude 3 Sonnet — F1 0.967 on IEEE Thesaurus broader/narrower/same-as
- OAEI-LLM benchmark — six hallucination categories for alignment

### The Gap
- Parameterization equivalence: no maintained system captures "ra = Ra / T0"
- CellML MathML variable connections — closest precedent for equation relationships
- Modelica acausal equations — right paradigm but wrong domain
- EngMath (1994) — conceptual foundation, never maintained

## What This Enables

When this works, the question "which parameters have conflicting values across papers"
is a **query**, not a **research project**. "This new paper's finding about gesture
duration — does it confirm or challenge existing propositions?" is a **join**, not a
hundred-line reconcile skill. The agents don't need to be smart at retrieval time
because the structure already encodes the relationships.

The concept registry adds a second tier: "are Gobl's ra values consistent with Fant's
Ra values?" becomes a mechanical check — follow the parameterization chain, apply the
transform, compare. "What do we know about subglottal pressure?" returns every claim
across every paper regardless of whether they called it Ps, P_sub, or lung pressure.

For the metanovel domain: the concept registry starts empty and grows as narratology
papers are read. When Genette's "focalization" and Bal's "focalization" turn out to
mean different things, that's a `contested_definition` edge — not a bug, but
first-class knowledge about the field's own terminology disputes.

The parameterization relationship layer is the novel contribution. physgen does
dimensional analysis. This does parameterization analysis. Nobody has built the
maintained system that captures "OQ + CQ = 1" and "OQ ≈ 1/(2·Rg·(1+Rk))" as
machine-checkable algebraic constraints over a concept space.

Compile harder. Don't leave it to runtime.
