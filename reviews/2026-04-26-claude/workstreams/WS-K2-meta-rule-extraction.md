# WS-K2: Meta-paper rule extraction pipeline (LLM with proposal-review gate)

**Status**: CLOSED 4a2ce545
**Depends on**: WS-A (schema parity — required so the predicates schema and rule documents round-trip through sidecar without drift) and WS-K consumer API for the end-to-end firing test only (`tests/test_extracted_rules_fire_against_argumentation.py`). WS-K itself ships independently against hand-stubbed rule fixtures; WS-K2 only needs the WS-K kernel API to be in tree so the joint sentinel can fire promoted rules through it.
**Blocks**: nothing structural. WS-K's source-trust pipeline closes on stubs without WS-K2; WS-K2 enriches it with promoted real rules afterward.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Why this workstream exists

D-8 reframed source-trust calibration as an argumentation pipeline: meta-papers ingest as ordinary sources, their propositions become claims, those claims author rules over paper metadata, and the argumentation kernel runs the rules against each source's metadata to produce an `Opinion`-typed prior with full provenance. D-9 decided who writes the rules — LLM extraction with a proposal-review gate, iterated until reliable. D-10 fixed the layout — `knowledge/rules/<paper-name>/` per source, mirroring claims and justifications.

What does not exist yet:

- A `proposal_rules` family parallel to `proposal_stances`, keyed by `(source_paper, rule_id)` and writing into `knowledge/rules/<paper-name>/<rule-id>.yaml`.
- A `proposal_predicates` family parallel to `proposal_rules`, keyed by `(source_paper)` and writing into `knowledge/predicates/<paper-name>/declarations.yaml` (Codex 2.13 — predicate registration must be a first-class proposal/promote workflow inside this WS, not a deferred skill invocation).
- An LLM extraction pipeline that reads a meta-paper's `notes.md` (and `claims.yaml` if present) and proposes DeLP-shaped rules over a registered predicate vocabulary. `propstore/classify.py` is the closest precedent — single LLM call, JSON output, calibrated through `categorical_to_opinion` — but the rule extractor takes notes + a predicate dictionary as input and emits typed rule documents, with iteration on the prompt itself.
- A predicate-declaration extractor whose input is the same `notes.md` + (if present) `claims.yaml` and whose output is a typed list of predicate signatures `(name, arity, arg_types)` covering `sample_size(P, N)`, `replication_status(P, S)`, `field_heat(P, H)`, `effect_size_z(P, Z)`, `peer_reviewed(P, B)`, `preregistered(P, B)`, `conflict_of_interest(P, B)` and whatever the 13 target papers introduce. `knowledge/predicates/` is empty today.
- A CLI surface (`pks proposal predicates declare`, `pks proposal predicates promote`, `pks proposal propose-rules`, `pks proposal promote-rules`) parallel to stances.
- Acceptance criteria binding the extraction loop: the pipeline is done only when ≥70% of proposed rules survive promotion across all 13 papers and survivors fire correctly under WS-K's argumentation kernel.

## Review findings covered

| Finding | Source | Citation | Description |
|---|---|---|---|
| **D-9** | DECISIONS.md | DECISIONS.md:99-111 | "LLM-extraction pass with proposal-review gate; iterate the prompt until extraction produces rules that survive promotion." |
| **D-10** | DECISIONS.md | DECISIONS.md:113-118 | `knowledge/rules/<paper-name>/` per source — mirrors the claims layout. |
| **D-8** (consumer side) | DECISIONS.md | DECISIONS.md:78-98 | The source-trust argumentation pipeline can read the rule corpus this WS authors. WS-K's own tests close on hand-stubbed rules; WS-K2 adds the real promoted corpus and the joint firing sentinel. |
| **Codex 2.13** | DECISIONS.md | DECISIONS.md:316 | "WS-K2 missing skill: write predicate-registration step explicitly; don't reference unavailable skill." |
| **Codex 2.14** | DECISIONS.md | DECISIONS.md:317 | "WS-K2 CLI tests: add logged CLI tests for help/dry-run/propose/promote/unknown id/no-commit-review." |
| **Codex 2.1** | DECISIONS.md | DECISIONS.md:333 | "Owner: TBD — replace each with 'Codex implementation owner + human reviewer required' or named owner where decided." |
| **Empty `knowledge/rules/`** | direct read | `ls knowledge/rules/` returns nothing | No rule corpus exists. |
| **Empty `knowledge/predicates/`** | direct read | `ls knowledge/predicates/` returns nothing | No predicate vocabulary exists. The original WS-K2 deferred this to a `research-papers:register-predicates` skill invocation; per Codex 2.13 the predicate-declaration mechanism is now an explicit propstore CLI subcommand owned by this WS, parallel to the rule-proposal lifecycle. |
| **Stance-only proposal lifecycle** | direct read | `propstore/proposals.py` defines only `PROPOSAL_STANCE_FAMILY` symbols (`stance_proposal_filename`, `stance_proposal_branch`, `plan_stance_proposal_promotion`, `promote_stance_proposals`, `commit_stance_proposals`, `build_stance_document`); no `_rule_*` or `_predicate_*` analogues. | The proposal lifecycle assumes stances; rules and predicates each need a parallel family. |
| **Stance LLM pattern reusable** | direct read | `propstore/classify.py:54-78` (the bidirectional classification prompt), `:103-168` (output → typed `ClassifiedStance` with `Opinion`), `:262-321` (raw → persisted dict with full `Provenance`) | The shape is the precedent — but the rule extractor and the predicate extractor are different prompts and different output schemas. Reuse the calibration plumbing, not the prompt. |
| **`paper-process` ingest covers meta-papers** | direct read | All 13 target paper directories exist under `papers/<dir>/notes.md` (verified by `ls`) | Meta-papers have already been read; their notes are on disk. The extraction has source material to consume. |

Adjacent findings closed in the same PR:

| Finding | Citation | Why included |
|---|---|---|
| `RULE_FILE_FAMILY` exists but has no proposal-side parallel | `propstore/families/registry.py:390-393` (RULE_FILE_FAMILY) vs nothing for proposal_rules | The canonical-rules family already exists. The proposal-side parallel is the gap. |
| `PREDICATE_FILE_FAMILY` exists but has no proposal-side parallel | `propstore/families/registry.py:383-385` (PREDICATE_FILE_FAMILY) vs nothing for proposal_predicates | The canonical-predicates family exists. Predicate authoring needs a proposal-then-promote lifecycle just like rules; without it the predicate vocabulary is uncontrolled. |
| Predicate-vocabulary admission control | nothing today gates whether the LLM uses registered predicate names | Without a check, the LLM will invent predicate names that do not exist and rules will dangle. WS-K2 introduces both an extractor-side admission gate against the registered predicate vocabulary and the registration mechanism itself. |

## Code references (verified by direct read)

### Existing rule infrastructure
- `propstore/families/registry.py:390-393` — `RULE_FILE_FAMILY = ArtifactFamily["Repository", RuleFileRef, RulesFileDocument](...)` — canonical-side family for promoted rules.
- `propstore/families/documents/rules.py` — `RuleDocument` and `RulesFileDocument` types. The `LoadedRuleFile` envelope at `propstore/rule_files.py:9-26` exposes `rules: tuple[RuleDocument, ...]`.
- `propstore/families/registry.py:383-385` — `PREDICATE_FILE_FAMILY = ArtifactFamily["Repository", PredicateFileRef, PredicatesFileDocument](...)` — canonical-side family for predicates.

### Existing proposal lifecycle (the precedent shape)
- `propstore/proposals.py:24-43` — `stance_proposal_filename`, `stance_proposal_relpath`, `stance_proposal_branch` (path-only address helpers, currently relying on the `cast("Repository", object())` placeholder pattern; WS-K Step 5d fixes that — WS-K2 must not re-introduce the cast).
- `propstore/proposals.py:45-69` — `StanceProposalPromotionItem`, `StanceProposalPromotionPlan`, `StanceProposalPromotionResult` dataclasses.
- `propstore/proposals.py:71-145` — `plan_stance_proposal_promotion` and `promote_stance_proposals` (the plan/execute split that WS-K Step 5b/5c fixes for typo paths and idempotency — WS-K2 inherits the fixed shape).
- `propstore/proposals.py:148-202` — `build_stance_document`, `dump_yaml_bytes`, `commit_stance_proposals` (the extractor's persistence path; WS-K Step 5a moves `commit_sha` inside the `with` block — WS-K2 inherits the fixed shape).

### Existing LLM extraction (the prompt-engineering precedent)
- `propstore/classify.py:54-78` — `_CLASSIFICATION_PROMPT` (the prompt format string, JSON-only response contract, explicit relationship taxonomy).
- `propstore/classify.py:103-168` — `classify_stance_from_llm_output` (raw dict → typed `ClassifiedStance` with explicit `Opinion` and `Provenance`; the abstain-on-missing-fields discipline; the `_vacuous_classifier_opinion` pattern).
- `propstore/classify.py:262-321` — `_build_stance_dict` (raw → persisted dict; calibration through `categorical_to_opinion`; full resolution provenance).
- `propstore/classify.py:324-401` — `classify_stance_async` (the async LLM call site, the response-content extraction, the JSON parse failure handling).

### Existing meta-paper notes (the input corpus)
- `papers/Ioannidis_2005_WhyMostPublishedResearch/notes.md` — Bayesian PPV framework; six corollaries; sample-size, statistical-power, pre-study-odds, bias predicates implied directly by the model.
- `papers/Begley_2012_DrugDevelopmentRaiseStandards/notes.md` — 6/53 (11%) reproducibility in preclinical cancer; predicates over `discipline` (preclinical-cancer), `cell-line-quality`, `blinded`, `controls-adequate`, `citation-count`.
- `papers/Aarts_2015_EstimatingReproducibilityPsychologicalScience/notes.md`, `papers/Errington_2021_InvestigatingReplicabilityPreclinicalCancer/notes.md`, `papers/Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments/notes.md`, `papers/Camerer_2018_EvaluatingReplicabilitySocialScience/notes.md`, `papers/Klein_2018_ManyLabs2Investigating/notes.md`, `papers/Border_2019_NoSupportHistoricalCandidate/notes.md`, `papers/Horowitz_2021_EpiPen/notes.md`, `papers/Yang_2020_EstimatingDeepReplicabilityScientific/notes.md`, `papers/Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction/notes.md`, `papers/Dreber_2015_PredictionMarketsEstimateReproducibility/notes.md`, `papers/Altmejd_2019_PredictingReplicabilitySocialScience/notes.md` — all present.

### Empty target trees (proof of gap)
- `knowledge/rules/` — directory exists, contains no files.
- `knowledge/predicates/` — directory exists, contains no files.

## First failing tests (write these first; they MUST fail before any production change)

These tests must fail before any production change lands. The end-to-end test is the gating sentinel; it can only turn green after WS-K's `source_trust_argumentation` pipeline is also green. Tests prefixed `test_cli_*` are CLI-level and run via `scripts/run_logged_pytest.ps1` per Codex 2.14 and the propstore tooling convention from CLAUDE.md / AGENTS.md.

1. **`tests/test_proposal_rules_family.py`** (new)
   - Asserts `propstore.families.registry.PROPOSAL_RULES_FAMILY` exists, registers under `repo.families.proposal_rules`, and addresses to `proposals/rules:knowledge/rules/<paper-name>/<rule-id>.yaml`.
   - Asserts a `RuleProposalDocument` typed payload exists at `propstore/families/documents/rules.py` with fields: `source_paper`, `proposed_rule` (a `RuleDocument`), `extraction_provenance` (operations, agent, model name, prompt sha), `extraction_date`, `predicates_referenced` (tuple, must all be in the registered predicate vocabulary at extraction time).
   - **Must fail today**: neither symbol exists.

2. **`tests/test_proposal_predicates_family.py`** (new — Codex 2.13)
   - Asserts `propstore.families.registry.PROPOSAL_PREDICATES_FAMILY` exists, registers under `repo.families.proposal_predicates`, and addresses to `proposals/predicates:knowledge/predicates/<paper-name>/declarations.yaml`.
   - Asserts a `PredicateProposalDocument` typed payload exists at `propstore/families/documents/predicates.py` with fields: `source_paper`, `proposed_declarations` (tuple of `PredicateDeclaration` records each with `name`, `arity`, `arg_types`), `extraction_provenance`, `extraction_date`.
   - Asserts `PredicateDeclaration.arg_types` is a tuple of one of the closed type tags: `paper_id`, `int`, `float`, `str`, `bool`, `enum:<member>|<member>|...` (the closed predicate-type set listed in Codex 2.13).
   - **Must fail today**: no symbol exists.

3. **`tests/test_propose_predicates_lifecycle.py`** (new)
   - Builds a repo with a single meta-paper source ingested (`Ioannidis_2005`).
   - Calls `propose_predicates_for_paper(repo, source_paper="Ioannidis_2005_WhyMostPublishedResearch", model_name="<test-model>")` with a mocked LLM client returning a fixed JSON shape declaring `sample_size/2 (paper_id, int)`, `statistical_power/2 (paper_id, float)`, `pre_study_odds/2 (paper_id, float)`, `bias/2 (paper_id, float)`.
   - Asserts the canonical `knowledge/predicates/Ioannidis_2005_WhyMostPublishedResearch/` directory is unchanged (empty or absent).
   - Asserts `proposals/predicates` branch contains `knowledge/predicates/Ioannidis_2005_WhyMostPublishedResearch/declarations.yaml` with the typed `PredicateProposalDocument` payload, full `extraction_provenance`, and `prompt_sha` recording the prompt template version.
   - **Must fail today**: `propose_predicates_for_paper` does not exist.

4. **`tests/test_promote_predicates_proposals.py`** (new)
   - Starts with proposals committed by test 3.
   - Calls `plan_predicate_proposal_promotion(repo, source_paper="Ioannidis_2005_WhyMostPublishedResearch")` and `promote_predicate_proposals(repo, plan)`.
   - Asserts the canonical `knowledge/predicates/Ioannidis_2005_WhyMostPublishedResearch/declarations.yaml` exists with the four declarations and `promoted_from_sha = <proposal commit sha>`.
   - Asserts a second call returns `items=()` (idempotent — the canonical declarations file matches the proposal hash).
   - Asserts `plan_predicate_proposal_promotion(repo, source_paper="does-not-exist")` raises `UnknownProposalPath` (the WS-K Step 5b typed exception, reused).
   - **Must fail today**: none of the symbols exist.

5. **`tests/test_propose_rules_lifecycle.py`** (new)
   - Builds a repo with `Ioannidis_2005` ingested AND with the predicate vocabulary above promoted via tests 3-4.
   - Calls `propose_rules_for_paper(repo, source_paper="Ioannidis_2005_WhyMostPublishedResearch", model_name="<test-model>")` with a mocked LLM client returning a fixed JSON shape.
   - Asserts the canonical `knowledge/rules/Ioannidis_2005_WhyMostPublishedResearch/` directory is unchanged (empty or absent).
   - Asserts `proposals/rules` branch contains `knowledge/rules/Ioannidis_2005_WhyMostPublishedResearch/<rule-id>.yaml` for each proposed rule, with the `RuleProposalDocument` payload, full `extraction_provenance`, and a `prompt_sha` recording exactly which prompt template version produced this output.
   - Asserts the extractor refuses to write any rule referencing a predicate not present in the canonical predicates file: such a rule is dropped, the rejection logged with `Provenance(status=VACUOUS, operations=("rule_extraction_predicate_unknown",))`.
   - **Must fail today**: `propose_rules_for_paper` does not exist.

6. **`tests/test_promote_rules_proposals.py`** (new)
   - Starts with proposals committed by test 5.
   - Calls `plan_rule_proposal_promotion(repo, source_paper="Ioannidis_2005_WhyMostPublishedResearch", rule_ids=("rule-001", "rule-003"))` (selective — promotes 2 of N proposals).
   - Calls `promote_rule_proposals(repo, plan)`.
   - Asserts the canonical branch's `knowledge/rules/Ioannidis_2005_WhyMostPublishedResearch/rule-001.yaml` and `rule-003.yaml` exist; `rule-002.yaml` and the rest do NOT.
   - Asserts each promoted file records `promoted_from_sha = <proposal commit sha>` (the audit pointer back to the proposal commit, mirroring WS-K's idempotency model).
   - Asserts a second call to `plan_rule_proposal_promotion` for the same `(source_paper, rule-001)` pair returns `items=()` because the proposal is already marked promoted.
   - Asserts `plan_rule_proposal_promotion(repo, rule_ids=("does-not-exist",))` raises `UnknownProposalPath`.
   - **Must fail today**: none of the symbols exist.

7. **`tests/test_extracted_rules_lint_clean.py`** (new)
   - For each of the 13 target papers, runs the rule extractor in dry-run mode (returns the typed `RuleProposalDocument` list without committing).
   - Validates each proposed rule against the propstore rule schema: every predicate in the rule body and head must be in the paper's `knowledge/predicates/<paper-name>/declarations.yaml` registration; arity must match; the rule type (strict / defeasible / defeater) must be a valid `RuleDocument` discriminator; CEL conditions must parse; the rule_id must follow the canonical naming convention.
   - **Must fail today**: extractor does not exist; predicate files do not exist; no rules to lint.

8. **`tests/test_extracted_rules_fire_against_argumentation.py`** (new — joint sentinel with WS-K)
   - For each of the 13 target papers, after extraction and promotion, builds a synthetic `SourceMetadata` payload covering the predicates the paper's rules quantify over (e.g. `sample_size = 30`, `replication_status = "failed-replication"`, `peer_reviewed = True`).
   - Runs `propstore.source_trust_argumentation.evaluate(repo, source_name="<synthetic>", metadata=<payload>)` — the pipeline introduced by WS-K.
   - Asserts the returned `Opinion` has `provenance.witnesses` containing at least one rule from each paper that has a rule applicable to the synthetic metadata.
   - Asserts the rules **fire** — i.e., they produce an argument the kernel evaluates, not just a static reference.
   - **Must fail today**: the kernel exists in WS-K's plan but has no rule corpus to consume.
   - **Coordination point**: this test is the joint sentinel for WS-K and WS-K2. Both must close before it goes green.

### CLI tests (new — Codex 2.14; all run via `scripts/run_logged_pytest.ps1`)

9. **`tests/test_cli_propose_rules_help.py`** (new)
   - Invokes `pks proposal propose-rules --help` via `subprocess.run` and asserts the help text loads (exit 0), lists `--paper` as a required arg, and lists `--model`, `--prompt-version`, `--dry-run`, `--mock-llm-fixture` as optional args.
   - Symmetric assertions for `pks proposal predicates declare --help` and `pks proposal predicates promote --help`.
   - **Must fail today**: subcommands do not exist; argparse will return non-zero.

10. **`tests/test_cli_propose_rules_dry_run.py`** (new)
    - Invokes `pks proposal propose-rules --paper Ioannidis_2005_WhyMostPublishedResearch --dry-run --mock-llm-fixture tests/fixtures/llm_rule_extraction_ioannidis.json` against a tempdir-scoped repo fixture.
    - Asserts stdout contains the JSON-serialized rule proposal shapes; asserts no commit was made on the `proposals/rules` branch (`git rev-parse proposals/rules` matches the pre-run sha).
    - **Must fail today**: subcommand does not exist; no `--dry-run` mode.

11. **`tests/test_cli_propose_rules_with_mocked_llm.py`** (new)
    - Uses a pytest fixture (`mock_llm_client`) patching `propstore.heuristic.rule_extraction._llm_call` to return a deterministic JSON payload.
    - Invokes `pks proposal propose-rules --paper Ioannidis_2005_WhyMostPublishedResearch --model test-model`.
    - Asserts exit 0, asserts a new commit exists on `proposals/rules` whose tree contains the expected rule files, asserts each rule file's `extraction_provenance.prompt_sha` matches the loaded prompt template hash, and asserts each rule's `predicates_referenced` is a subset of the registered predicate vocabulary.
    - **Must fail today**: subcommand and the mocked-LLM hook do not exist.

12. **`tests/test_cli_promote_rules_selective.py`** (new)
    - Pre-seeds `proposals/rules` with three proposed rules via the test 11 fixture.
    - Invokes `pks proposal promote-rules --paper Ioannidis_2005_WhyMostPublishedResearch --rule-id rule-001 --rule-id rule-003`.
    - Asserts the canonical branch contains `rule-001.yaml` and `rule-003.yaml` and does NOT contain `rule-002.yaml`.
    - Asserts the `proposals/rules` branch is unchanged for `rule-002.yaml` (it remains a live proposal).
    - **Must fail today**: subcommand does not exist.

13. **`tests/test_cli_promote_rules_unknown_id.py`** (new)
    - Invokes `pks proposal promote-rules --paper Ioannidis_2005_WhyMostPublishedResearch --rule-id rule-does-not-exist` against a repo where that rule is absent from `proposals/rules`.
    - Asserts non-zero exit (specifically the propstore convention for typed user errors), asserts stderr contains the literal exception class name `UnknownProposalPath` and the offending rule id, asserts no canonical-branch mutation occurred.
    - **Must fail today**: subcommand does not exist; no typed exit-code mapping.

14. **`tests/test_cli_review_no_commit.py`** (new)
    - Invokes `pks proposal promote-rules --paper Ioannidis_2005_WhyMostPublishedResearch` with neither `--rule-id` nor `--all` (review mode).
    - Asserts exit 0, asserts stdout shows the plan: per proposed rule, the rule_id, rule_type, head, body, predicates referenced, and the page reference.
    - Asserts no commit on either `proposals/rules` or canonical: head shas of both branches are unchanged.
    - **Must fail today**: subcommand does not exist; review-mode no-op behavior is unspecified.

15. **`tests/test_workstream_k2_done.py`** (new — gating sentinel)
    - `xfail` until WS-K2 closes; flips to `pass` on the final commit.
    - Additional assertion: across the 13 target papers, the human reviewer accepted ≥70% of proposed rules at promotion time. This is recorded as a CSV file `reviews/2026-04-26-claude/workstreams/WS-K2-acceptance-log.csv` checked in alongside the closing commit; the test reads that CSV and asserts the global ratio.
    - **Must fail today**: file does not exist; no extraction has happened; no review has happened.

## New `proposal_rules` and `proposal_predicates` families — design

These are the architectural deliverables WS-K2 must produce. The shape parallels `PROPOSAL_STANCE_FAMILY` (per `propstore/proposals.py` and the existing stance family) and the canonical `RULE_FILE_FAMILY` / `PREDICATE_FILE_FAMILY`.

### Family registration (`propstore/families/registry.py`)

```python
PROPOSAL_RULES_FAMILY = ArtifactFamily["Repository", RuleProposalRef, RuleProposalDocument](
    name="proposal_rules",
    branch_template="proposals/rules",
    placement=BranchPlacement(
        ref=lambda r: f"knowledge/rules/{r.source_paper}/{r.rule_id}.yaml",
        branch=lambda r: "proposals/rules",
    ),
    document_type=RuleProposalDocument,
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    repo_attr="proposal_rules",
)

PROPOSAL_PREDICATES_FAMILY = ArtifactFamily["Repository", PredicateProposalRef, PredicateProposalDocument](
    name="proposal_predicates",
    branch_template="proposals/predicates",
    placement=BranchPlacement(
        ref=lambda r: f"knowledge/predicates/{r.source_paper}/declarations.yaml",
        branch=lambda r: "proposals/predicates",
    ),
    document_type=PredicateProposalDocument,
    contract_version=ARTIFACT_FAMILY_CONTRACT_VERSION,
    repo_attr="proposal_predicates",
)
```

### Proposal documents

```python
# propstore/families/documents/predicates.py
@dataclass(frozen=True)
class PredicateProposalRef:
    source_paper: str    # e.g. "Ioannidis_2005_WhyMostPublishedResearch"

PredicateArgType = Literal["paper_id", "int", "float", "str", "bool"] | str  # "enum:hot|warm|cold"

@dataclass(frozen=True)
class PredicateDeclaration:
    name: str                                # "sample_size"
    arity: int                               # 2
    arg_types: tuple[PredicateArgType, ...]  # ("paper_id", "int")
    description: str                         # one-line LLM-supplied gloss

@dataclass(frozen=True)
class PredicateProposalDocument:
    source_paper: str
    proposed_declarations: tuple[PredicateDeclaration, ...]
    extraction_provenance: PredicateExtractionProvenance
    extraction_date: str
    promoted_from_sha: str | None

# propstore/families/documents/rules.py
@dataclass(frozen=True)
class RuleProposalRef:
    source_paper: str
    rule_id: str

@dataclass(frozen=True)
class RuleProposalDocument:
    source_paper: str
    rule_id: str
    proposed_rule: RuleDocument
    predicates_referenced: tuple[str, ...]   # arity-qualified, e.g. "sample_size/2"
    extraction_provenance: RuleExtractionProvenance
    extraction_date: str
    promoted_from_sha: str | None

@dataclass(frozen=True)
class RuleExtractionProvenance:
    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    predicates_sha: str
    status: ProvenanceStatus
```

### Why parallel families rather than reusing `PROPOSAL_STANCE_FAMILY`

`proposal_stances` is keyed by `source_claim_id` and stores a `StanceFileDocument`. `proposal_rules` is keyed by `(source_paper, rule_id)` and `proposal_predicates` is keyed by `source_paper`. The three are disjoint in identity space and disjoint in document polymorphism. WS-K rejected polymorphism in favour of a parallel family for `proposal_source_trust`; WS-K2 follows the same precedent for the same reasons.

### Why one rule file per rule, one declarations file per paper

The canonical layout under `knowledge/rules/<paper-name>/` is intentionally one-file-per-rule (D-10) because promotion is selective per rule. Predicates are different: a paper's predicate vocabulary is a single coherent declaration set — a partial-promote of "half the predicates" leaves the rule corpus citing undeclared symbols, which is precisely the failure mode the admission gate prevents. Predicates promote whole-document; rules promote per-id.

## API surface and CLI

### Modules
- New module `propstore/heuristic/predicate_extraction.py` exposes `propose_predicates_for_paper(repo, source_paper, *, model_name, prompt_version=LATEST) -> (commit_sha, list[PredicateDeclaration])`.
- New module `propstore/heuristic/rule_extraction.py` exposes `propose_rules_for_paper(repo, source_paper, *, model_name, prompt_version=LATEST) -> (commit_sha, list[rule_id])`.
- New module `propstore/proposals_predicates.py` exposes `plan_predicate_proposal_promotion(repo, *, source_paper)` and `promote_predicate_proposals(repo, plan)`.
- New module `propstore/proposals_rules.py` exposes `plan_rule_proposal_promotion(repo, *, source_paper=None, rule_ids=None)` and `promote_rule_proposals(repo, plan)`.

All four modules follow the stance-side dataclass-plan-then-execute pattern.

### CLI subcommands under `pks proposal`

- `pks proposal predicates declare --paper <paper-name> [--model <model-name>] [--prompt-version <version>] [--dry-run] [--mock-llm-fixture <path>]` — runs the predicate extractor, commits to `proposals/predicates`, prints the proposed declarations.
- `pks proposal predicates promote --paper <paper-name>` — promotes the proposed declarations file for `<paper-name>` to canonical. Whole-document promotion (no per-predicate selectivity at promotion time; the human reviewer edits the proposal YAML in the proposal branch if a subset is wanted, then re-promotes).
- `pks proposal propose-rules --paper <paper-name> [--model <model-name>] [--prompt-version <version>] [--dry-run] [--mock-llm-fixture <path>]` — runs the rule extractor, commits the batch, prints commit sha and proposed rule ids.
- `pks proposal promote-rules --paper <paper-name> [--rule-id <id>]... [--all]` — selective or full promotion. Without `--rule-id` and without `--all`, prints the plan and exits 0 without committing (review mode).

The `--mock-llm-fixture` flag exists for testability per Codex 2.14 — it loads a JSON file from disk in place of an LLM call. Production use leaves the flag absent.

## The predicate-extraction prompt — design

### Inputs
The predicate prompt is fed:
1. The meta-paper's `notes.md` (full content).
2. The meta-paper's `claims.yaml` if present.
3. A short controlled list of the predicate-type tags (`paper_id`, `int`, `float`, `str`, `bool`, `enum:<member>|<member>|...`).
4. Five hand-authored exemplar declarations covering each type tag.

### Output contract
Strict JSON, schema-validated. Each declaration object has fields: `name`, `arity`, `arg_types` (a tuple matching `arity`), `description`. `name` matches `[a-z_][a-z0-9_]*`; `arity` ≥ 1; the first `arg_type` must be `paper_id` (every meta-paper predicate is paper-scoped).

### Iteration loop
Same shape as the rule loop below: per-paper acceptance/rejection logged, prompt edited, version bumped, prior version archived. Predicate-prompt versions live under `propstore/heuristic/__resources__/predicate_extraction_prompts/v<N>.txt`.

## The rule-extraction prompt — design

The prompt is the iterated artifact. Its version is recorded in the proposal provenance via `prompt_sha`. The template lives at `propstore/heuristic/__resources__/rule_extraction_prompt.txt` and is loaded through the package resource loader; the sha is computed at extraction time and stamped on every proposal.

### Inputs
1. The meta-paper's `notes.md` (full content).
2. The meta-paper's `claims.yaml` if present.
3. The full canonical `knowledge/predicates/<source_paper>/declarations.yaml` predicate vocabulary, formatted as a numbered list with arity, type signature, and description per predicate. The prompt explicitly instructs the LLM to use only these predicates.
4. The propstore rule schema as a JSON Schema fragment.
5. Three one-shot examples (strict / defeasible / defeater) drawn from `propstore/heuristic/rule_extraction_examples.yaml`.

### Output contract
Strict JSON, schema-validated. Each rule object has fields: `rule_id`, `rule_type` (one of `strict`, `defeasible`, `defeater`), `head`, `body` (list of literals), `derived_from_paper_section`, `notes`. Predicate references are arity-qualified strings.

### Iteration loop
Per D-9: (1) run extractor on all 13 papers with prompt version N; (2) reviewer accepts/rejects/edits each proposal; (3) acceptance rate computed per-paper and globally; (4) rejection reasons logged to `reviews/2026-04-26-claude/workstreams/WS-K2-rejection-log.csv`; (5) prompt edited; (6) bump prompt version, re-run on below-threshold papers; (7) recompute. Done when global acceptance ≥ 70% and per-paper ≥ 50%. Each prompt version is archived under `reviews/2026-04-26-claude/workstreams/WS-K2-prompt-iterations/v<N>.md`; `prompt_sha` on each proposal pins which version produced it.

## Predicate vocabulary — bootstrap target

The minimum vocabulary covering the 13 target papers. The LLM-driven `pks proposal predicates declare` per-paper run produces a superset; the human reviewer trims and promotes. Where a predicate is used by multiple papers, the first paper to register it wins; subsequent papers must reuse the canonical name (the rule-extraction prompt's predicate vocabulary input is per-paper and includes already-canonical predicates from prior papers as "shared" entries).

| Predicate | Arity | arg_types | First registered by |
|---|---|---|---|
| `sample_size` | 2 | (paper_id, int) | Ioannidis_2005 |
| `statistical_power` | 2 | (paper_id, float) | Ioannidis_2005 |
| `pre_study_odds` | 2 | (paper_id, float) | Ioannidis_2005 |
| `bias` | 2 | (paper_id, float) | Ioannidis_2005 |
| `replication_status` | 2 | (paper_id, enum:replicated\|failed-replication\|untested) | Aarts_2015 |
| `field_heat` | 2 | (paper_id, enum:hot\|warm\|cold) | Ioannidis_2005 |
| `effect_size_z` | 2 | (paper_id, float) | Camerer_2016 |
| `peer_reviewed` | 2 | (paper_id, bool) | Begley_2012 |
| `preregistered` | 2 | (paper_id, bool) | Klein_2018 |
| `conflict_of_interest` | 2 | (paper_id, bool) | Begley_2012 |
| `blinded` | 2 | (paper_id, bool) | Begley_2012 |
| `discipline` | 2 | (paper_id, enum:preclinical-cancer\|psychology\|social-science\|economics) | Errington_2021 |
| `prediction_market_price` | 2 | (paper_id, float) | Dreber_2015 |
| `peer_prediction_score` | 2 | (paper_id, float) | Gordon_2021 |
| `citation_count` | 2 | (paper_id, int) | Begley_2012 |
| `cell_line_quality` | 2 | (paper_id, enum:validated\|inadequate\|unknown) | Begley_2012 |
| `candidate_gene_finding` | 2 | (paper_id, bool) | Border_2019 |

## Production change sequence

Each step lands in its own commit with a message of the form `WS-K2 step N — <slug>`.

### Step 1 — Implement predicate registration as a propstore CLI subcommand (Codex 2.13)

Replaces the original "run the `research-papers:register-predicates` skill" step. Implementation deliverables:

- New `propstore/families/documents/predicates.py` adding `PredicateProposalRef`, `PredicateDeclaration`, `PredicateProposalDocument`, `PredicateExtractionProvenance`. The `PredicateArgType` literal set is closed: `paper_id`, `int`, `float`, `str`, `bool`, plus `enum:<member>|<member>|...`. No callable types; no nested types. The closed set is enforced at construction time.
- New `PROPOSAL_PREDICATES_FAMILY` registration in `propstore/families/registry.py` adjacent to `PREDICATE_FILE_FAMILY` (line 383-385). Bump `ARTIFACT_FAMILY_CONTRACT_VERSION` if necessary. Wire `repo.families.proposal_predicates` so the family is reachable through the same accessor pattern as `proposal_stances`.
- New `propstore/heuristic/predicate_extraction.py` housing `propose_predicates_for_paper`. The LLM call shape mirrors `propstore/classify.py:classify_stance_async` (litellm async, JSON response_format, exception handling). Inputs: notes.md, claims.yaml (if present), the closed type-tag list, the seed exemplars. Output: typed `PredicateDeclaration` tuple. Persistence uses `repo.families.transact(...)` and reads `transaction.commit_sha` *inside* the `with` block (inheriting WS-K Step 5a's fix; do not regress).
- New `propstore/proposals_predicates.py` housing `plan_predicate_proposal_promotion` and `promote_predicate_proposals`. Reuses `UnknownProposalPath`. Promotion is whole-document (the canonical declarations file is replaced atomically). Idempotency via `promoted_from_sha` recorded on the canonical-side document; refuse re-promotion of an already-promoted sha unless `--force`.
- New CLI subcommand group `pks proposal predicates` with `declare` and `promote` subcommands as specified in the CLI section above.
- Run `pks proposal predicates declare --paper <name>` against each of the 13 target papers; review output; promote selectively. Hand-edit the proposed YAML on the proposal branch where the LLM missed predicates the table above lists; re-promote.

Acceptance: `tests/test_proposal_predicates_family.py`, `tests/test_propose_predicates_lifecycle.py`, `tests/test_promote_predicates_proposals.py` turn green; `knowledge/predicates/` contains a `<paper>/declarations.yaml` per target paper; every predicate in the table above is registered against its first-registered-by paper.

### Step 2 — Define `RuleProposalDocument` and `PROPOSAL_RULES_FAMILY`

- Add `RuleProposalRef`, `RuleProposalDocument`, `RuleExtractionProvenance` to `propstore/families/documents/rules.py` per the design above.
- Add `PROPOSAL_RULES_FAMILY` to `propstore/families/registry.py` adjacent to `RULE_FILE_FAMILY` (line 390-393).
- Wire `repo.families.proposal_rules`.
- Acceptance: `tests/test_proposal_rules_family.py` turns green.

### Step 3 — Author the rule-extraction prompt and seed examples

- Hand-author `propstore/heuristic/__resources__/rule_extraction_prompt.txt` (v1).
- Hand-author `propstore/heuristic/rule_extraction_examples.yaml` with three exemplar rules from Ioannidis_2005 (strict / defeasible / defeater).
- Compute `prompt_sha` deterministically over the prompt template at module-load time; cache for stamping into provenance.
- Acceptance: prompt template loads, sha is reproducible across runs.

### Step 4 — Implement `propose_rules_for_paper`

- New module `propstore/heuristic/rule_extraction.py` housing `propose_rules_for_paper`, a `_validate_against_predicates` helper (loads canonical `knowledge/predicates/<paper>/declarations.yaml`), and persistence mirroring `propstore/proposals.py:commit_stance_proposals` but writing into `proposal_rules`.
- The LLM call shape mirrors `propstore/classify.py:classify_stance_async`. The prompt template is loaded through the package resource loader; the response is parsed against the rule output schema; each candidate rule has its `predicates_referenced` admission-checked against the loaded predicate vocabulary; rules referencing unregistered predicates are rejected at extraction time and recorded as `Provenance(status=VACUOUS, operations=("rule_extraction_predicate_unknown",))`.
- Persistence uses `repo.families.transact(...)` with `commit_sha` inside the `with` block.
- Acceptance: `tests/test_propose_rules_lifecycle.py` turns green.

### Step 5 — Implement `plan_rule_proposal_promotion` and `promote_rule_proposals`

- Add planning and promotion functions to a new module `propstore/proposals_rules.py` (parallel to `propstore/proposals.py`).
- Reuse `UnknownProposalPath`. Reuse the idempotency guard pattern (`promoted_from_sha` recorded on every promoted rule; refuse re-promotion unless `--force`).
- The promote step writes into `RULE_FILE_FAMILY` on the canonical branch; it does not mutate the predicate file.
- Acceptance: `tests/test_promote_rules_proposals.py` turns green.

### Step 6 — CLI surface for rules

- Add `pks proposal propose-rules` and `pks proposal promote-rules` subcommands. Mirror the stance-side argument shape exactly except for the keying (`--paper` instead of `--claim-id`).
- The propose subcommand prints, for each proposed rule, the rule_id, rule_type, head, body, predicates referenced, and the page reference.
- The promote subcommand without `--all` and without explicit `--rule-id` runs in review mode: prints the plan and exits 0 without committing. With `--rule-id <id>` arguments (repeatable), it promotes only those.
- Acceptance: the six CLI tests (tests 9-14 above) turn green when run via `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K2-cli tests/test_cli_propose_rules_help.py tests/test_cli_propose_rules_dry_run.py tests/test_cli_propose_rules_with_mocked_llm.py tests/test_cli_promote_rules_selective.py tests/test_cli_promote_rules_unknown_id.py tests/test_cli_review_no_commit.py`.

### Step 7 — Run rule extraction across the 13 target papers (iteration 1)

- Run `propose_rules_for_paper` on all 13 papers with prompt v1.
- Manually review every proposal. Record acceptance/rejection in `reviews/2026-04-26-claude/workstreams/WS-K2-acceptance-log.csv` and rejection reasons in `reviews/2026-04-26-claude/workstreams/WS-K2-rejection-log.csv`.
- Compute global acceptance rate.
- If < 70%, proceed to step 8. If ≥ 70%, proceed to step 9.

### Step 8 — Iterate the prompt

Read the rejection log; identify top three failure modes; edit `propstore/heuristic/__resources__/rule_extraction_prompt.txt` to address them; bump version, archive prior version under `propstore/heuristic/__resources__/rule_extraction_prompts/v<N>.txt`; record rationale under `reviews/2026-04-26-claude/workstreams/WS-K2-prompt-iterations/v<N+1>.md`; re-run extraction on below-threshold papers; re-review. Repeat until ≥ 70% globally and ≥ 50% per-paper.

### Step 9 — End-to-end test against the WS-K argumentation pipeline

- After WS-K's `source_trust_argumentation` pipeline is green, run `tests/test_extracted_rules_fire_against_argumentation.py`.
- For each of the 13 target papers, the test constructs a synthetic source-metadata payload exercising the predicates that paper's promoted rules quantify over.
- If a paper has no firing rule for any reasonable synthetic metadata, that paper's rules are not earning their place in the corpus. Either the rules need rework or the paper should be dropped from the target list (recorded as a closed-with-reason entry in the acceptance log).
- Acceptance: `tests/test_extracted_rules_fire_against_argumentation.py` turns green.

### Step 10 — Lint and freshness gates

- Add a lint pass that walks `knowledge/rules/<paper>/*.yaml` and asserts every predicate referenced is registered in `knowledge/predicates/<paper>/declarations.yaml`. Run as a `pks` subcommand and as a CI step.
- Add a freshness gate: if any of the 13 target papers' `notes.md` changes after this WS closes, both predicate extraction and rule extraction are re-run and the proposals re-reviewed. The freshness gate compares each paper's `notes_sha` against the current `notes.md` sha and `predicates_sha` against the current declarations file sha.

### Step 11 — Close gaps, flip sentinel

- Update `docs/gaps.md`: add `# WS-K2 closed <sha>` line listing the 13 papers and the global acceptance rate achieved.
- Flip `tests/test_workstream_k2_done.py` from `xfail` to `pass`.
- Update STATUS line in this file to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-K2 done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors on the new `predicate_extraction.py`, `rule_extraction.py`, `proposals_predicates.py`, `proposals_rules.py`, and the `families/documents/predicates.py` and `families/documents/rules.py` additions. Evidence: `uv run pyright propstore`, 0 errors.
- [x] `uv run lint-imports` — passes; the new heuristic modules live under the heuristic layer and do not import any source-writer module. Evidence: `uv run lint-imports`, 5 kept / 0 broken.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K2 tests/test_proposal_rules_family.py tests/test_proposal_predicates_family.py tests/test_propose_predicates_lifecycle.py tests/test_promote_predicates_proposals.py tests/test_propose_rules_lifecycle.py tests/test_promote_rules_proposals.py tests/test_extracted_rules_lint_clean.py tests/test_extracted_rules_fire_against_argumentation.py tests/test_workstream_k2_done.py` — all green. Evidence: `logs/test-runs/WS-K2-20260429-205025.log`.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K2-cli tests/test_cli_propose_rules_help.py tests/test_cli_propose_rules_dry_run.py tests/test_cli_propose_rules_with_mocked_llm.py tests/test_cli_promote_rules_selective.py tests/test_cli_promote_rules_unknown_id.py tests/test_cli_review_no_commit.py` — all green. Evidence: `logs/test-runs/WS-K2-cli-20260429-205025.log`.
- [x] Full suite — no NEW failures vs the WS-K-stabilized baseline. Evidence: `logs/test-runs/WS-K2-full-after-resources-20260429-211305.log`, 3425 passed / 2 skipped.
- [x] `knowledge/predicates/<paper>/declarations.yaml` exists for every target paper; every predicate the table lists is registered against its first-registered-by paper. Evidence: nested `knowledge` commit `47c82cc`.
- [x] `knowledge/rules/<paper-name>/` contains promoted rules for every paper whose acceptance survived the loop. Evidence: nested `knowledge` commit `47c82cc`.
- [x] `propstore/families/registry.py` exposes `PROPOSAL_RULES_FAMILY` and `PROPOSAL_PREDICATES_FAMILY`.
- [x] `propstore/heuristic/predicate_extraction.py`, `propstore/heuristic/rule_extraction.py`, `propstore/proposals_predicates.py`, `propstore/proposals_rules.py` exist with the documented surfaces.
- [x] `propstore/heuristic/__resources__/rule_extraction_prompt.txt` and `propstore/heuristic/__resources__/predicate_extraction_prompt.txt` are at their latest committed versions; archived prompt versions live under `propstore/heuristic/__resources__/rule_extraction_prompts/` and `propstore/heuristic/__resources__/predicate_extraction_prompts/`.
- [x] `reviews/2026-04-26-claude/workstreams/WS-K2-acceptance-log.csv` shows ≥ 70% global acceptance; per-paper acceptance ≥ 50%. Evidence: 26/26 accepted, 100% global and 100% per paper.
- [x] `reviews/2026-04-26-claude/workstreams/WS-K2-rejection-log.csv` and `WS-K2-prompt-iterations/v<N>.md` files exist and explain every prompt revision.
- [x] WS-K2 property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-K2 test run or a named companion run. Evidence: `logs/test-runs/WS-K2-property-gates-20260429-210148.log`.
- [x] `docs/gaps.md` records WS-K2 closure with the 13 paper list and the achieved acceptance rate.
- [x] STATUS line is `CLOSED 4a2ce545`.

## Done means done

This workstream is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- D-9 (LLM extraction with proposal-review gate) — implemented and exercised on 13 papers, for both predicates and rules.
- D-10 (`knowledge/rules/<paper-name>/` layout) — every promoted rule is under a paper-named subdirectory; nothing dangles.
- D-8 consumer side — WS-K's `source_trust_argumentation` pipeline runs on real promoted rules and the joint sentinel test (`tests/test_extracted_rules_fire_against_argumentation.py`) is green.
- Codex 2.13 — predicate registration is implemented as `pks proposal predicates declare/promote` inside propstore, not as a deferred skill invocation. Empty-`knowledge/predicates/` gap closed.
- Codex 2.14 — all six CLI tests run via `scripts/run_logged_pytest.ps1` and pass.
- The empty-`knowledge/rules/` gap is closed.
- The prompt-iteration log shows a real iteration loop, not a single-shot extraction. If the first prompt produced ≥ 70% acceptance, document why and keep the loop infrastructure committed for future re-runs.

If any one is not true, WS-K2 stays OPEN. No "we'll get the prediction-market papers later." Either the 13 papers are all extracted, reviewed, and either promoted or explicitly closed-with-reason, or this WS is explicitly rescoped in this file before declaring done.

## Cross-stream notes

- **WS-K joint sentinel**: `tests/test_extracted_rules_fire_against_argumentation.py` is the joint gate. Order: WS-A merges; WS-K Steps 1-7 land; WS-K2 Steps 1-8 run in parallel with WS-K's Step 8 (the `source_trust_argumentation` pipeline); the joint sentinel runs once both are wired.
- **WS-A dependency**: predicate and rule documents round-trip through the sidecar. WS-A's parity tests must be green before WS-K2 Step 4 runs against a real sidecar.
- **WS-N coordination**: the new heuristic modules must obey WS-N's `layered` import contract — no imports into source writers, no imports into world-model query layer except the proposal/promote API. WS-K's negative-import-linter test catches leaks.
- **Proposal-lifecycle inherited fixes**: WS-K2 inherits WS-K Step 5's fixes (commit_sha inside `with`, `UnknownProposalPath`, idempotency via `promoted_from_sha`). The new persistence modules must not regress these.
- **Skills coexistence**: `research-papers:register-predicates` and `research-papers:author-rules` are interactive agent skills useful for one-off paper work. WS-K2's CLI is the programmatic batch path. Both are allowed to exist; this WS does not depend on either.
- **Deferred research extension**: a successor WS could run the extractor twice with different prompt seeds and compare rule sets (within-extractor agreement). Recorded; not built here.

## What this WS does NOT do

- Does NOT depend on any external skill for predicate registration. Per Codex 2.13, predicate registration is implemented inside propstore as a CLI subcommand; the workflow is reproducible with `pks proposal predicates declare/promote` alone.
- Does NOT author rules by hand. The seed examples in `rule_extraction_examples.yaml` are exemplars for the LLM, not the rule corpus.
- Does NOT change the canonical `RULE_FILE_FAMILY` or `PREDICATE_FILE_FAMILY` shape, or `RuleDocument` / `PredicatesFileDocument` document types. The proposal-side documents carry embedded canonical types and additional extraction provenance.
- Does NOT extend the predicate vocabulary beyond the 13 target papers' needs.
- Does NOT implement a forward/reverse independence check on the LLM extraction.
- Does NOT replace the `research-papers:author-rules` interactive skill; WS-K2's `propose_rules_for_paper` is the programmatic batch path. Both target `RULE_FILE_FAMILY`.
- Does NOT calibrate `Opinion` values for fired rules. Rules are categorical (strict / defeasible / defeater) inputs; the kernel's weighting and the final `Opinion` belong to WS-K's `source_trust_argumentation` pipeline.

## Papers / specs referenced

The 13 target meta-papers (extraction inputs, all under `papers/<dir>/notes.md`):

- Ioannidis 2005, *Why Most Published Research Findings Are False* — Bayesian PPV; anchors the `sample_size`, `statistical_power`, `pre_study_odds`, `bias` predicate cluster.
- Begley & Ellis 2012, *Drug development: Raise standards for preclinical cancer research* — 6/53 (11%) preclinical reproducibility; cell-line quality, blinding, controls, citation-count predicates.
- Aarts (Open Science Collaboration) 2015, *Estimating the reproducibility of psychological science* — `replication_status` predicate.
- Errington et al. 2021, *Investigating the replicability of preclinical cancer biology* — empirical replication data crossing Begley_2012.
- Camerer et al. 2016, *Evaluating replicability of laboratory experiments in economics* — `effect_size_z` predicate.
- Camerer et al. 2018, *Evaluating the replicability of social science experiments in Nature and Science 2010-2015*.
- Klein et al. 2018, *Many Labs 2* — `preregistered` predicate.
- Border et al. 2019, *No support for historical candidate gene…* — `candidate_gene_finding` predicate.
- Horowitz et al. 2021, *EpiPen*.
- Yang et al. 2020, *Estimating the deep replicability of scientific findings…*.
- Gordon et al. 2021, *Predicting replicability — Analysis by Survey and Prediction Markets* — `peer_prediction_score`.
- Dreber et al. 2015, *Using prediction markets to estimate the reproducibility of scientific research* — `prediction_market_price`.
- Altmejd et al. 2019, *Predicting the replicability of social science lab experiments*.

Internal references: DECISIONS.md D-8, D-9, D-10 (authoritative); Codex round-2 findings 2.1, 2.13, 2.14 (authoritative); WS-K-heuristic-discipline.md (consumer + inherited lifecycle fixes); WS-A-schema-fidelity.md (schema substrate); project memory `feedback_imports_are_opinions` (every imported KB row is a defeasible claim — the proposal-review gate operationalizes this for both predicates and rules); `project_design_principle` (selective promotion preserves disagreement).
