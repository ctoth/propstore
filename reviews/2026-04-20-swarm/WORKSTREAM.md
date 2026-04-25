# Review Remediation Workstream — 2026-04-20 (TDD edition)

Source: `reviews/2026-04-20-swarm/SYNTHESIS.md` plus 14 per-subsystem/per-dep reports under the same directory.

## Governing principles

1. **Reach further, not cut down.** Every "dead code that lies" finding becomes an *implementation* commitment, not a deletion.
2. **From the literature, with citations at the site.** Per `feedback_citations_and_tdd` memory: every fix lands with the paper citation in the docstring and inline where a non-obvious invariant is enforced.
3. **TDD hard, red before green.** Every task lands in two commits minimum: one that makes the bug visible as a failing test, one that turns it green. No fix without a prior failing test. Per `feedback_tdd_and_paper_checks` and `feedback_hypothesis_property_tests`: prefer Hypothesis property tests where a formal property applies.
4. **No fallbacks, no compat shims.** Per `feedback_no_fallbacks`: delete the old interface, update callers in one pass.
5. **Honest labeling.** Each task is tagged `[LIT-STRAIGHT]` (paper prescribes fix) or `[DESIGN-ANCHORED]` (principle + literature orient, concrete shape is engineering).

## Per-task TDD protocol

Every numbered task runs this loop:

```
1. Write the test. The test must fail BEFORE the fix and pass AFTER.
2. Run the test, observe RED. Capture the failure output.
3. Commit RED:
     git commit -m "test(<area>): demonstrate <one-line issue summary>

     Failing test for <finding-id> from reviews/2026-04-20-swarm/<report>.md"
4. Implement the fix.
5. Run the test, observe GREEN. Run full suite for regressions.
6. Commit GREEN:
     git commit -m "fix(<area>): <one-line summary> (cites <paper>)

     Closes <finding-id>. Test: <test file>::<test name>."
7. Only then update callers (if any); commit each caller-update separately
   if it spans >1 file.
```

**Commit cadence.** Two commits per task is the floor. Three is normal (red + fix + caller-updates). When a fix spans multiple unrelated modules, split further: one commit per module. Ward's "commit after editing 2+ files" nudge is the minimum cadence — push smaller. A 50-line commit is good; a 500-line commit is a reviewer's enemy.

**Never amend a pushed commit.** Red commits stay in history as bug evidence, even after fix.

**Test runner conventions.**
- Python tests: `powershell -File scripts/run_logged_pytest.ps1 tests/<path> -k <name>`
- Hypothesis profile for property tests with large search spaces: `HYPOTHESIS_PROFILE=overnight`
- Pyright check: `uv run pyright propstore`
- CI will run import-linter (Phase 4); local runs `uv run lint-imports`

---

## Phase sequencing

Phases run in order. Within a phase, subtasks parallelize when file-scope-disjoint.

| # | Name | Findings | Lit-straight | Design-anchored | Depends on |
|---|---|---|---|---|---|
| 0 | Coverage + baseline + TDD scaffolding | — | — | setup | — |
| 1 | Data-loss + directional-lie CRITs | 5 | 3 | 2 | 0 |
| 2 | Rule-5 gate generalization | 26 | 1 pattern | — | 0, 1 |
| 3 | Honest-ignorance propagation | 11 | 8 | 3 | 0, 2 |
| 4 | Layer invariants + import-linter | 8 | 1 | 7 | 0 |
| 5 | ASPIC+/Dung bridge correctness | 10 | 7 | 3 | 4 |
| 6 | Extend-instead-of-delete | 8 | 5 | 3 | 1, 4 |
| 7 | Race / atomicity | 7 | 6 | 1 | 0 |
| 8 | DoS gates + anytime frames | 7 | 2 | 5 | 3 |
| 9 | Consumer-drift / public surfaces | 8 | 4 | 4 | — |
| 10 | Upstream dep fixes | ~15 | 12 | 3 | 9 |
| 11 | CLI hygiene | 27 | all | — | 0 |
| 12 | Final verification + paper-PNG gates | — | — | — | all |

---

## Phase 0 — Coverage + baseline + TDD scaffolding

### T0.1 Fill coverage gaps [no fix — survey only, NO test required]
Read `world/bound.py` (1175 lines) and any unread `worldline/` files. Produce `reviews/2026-04-20-swarm/propstore/world-worldline-bound.md` supplement. **Single commit** when done.

### T0.2 Baseline
```
powershell -File scripts/run_logged_pytest.ps1 tests/ > logs/baseline-2026-04-20.log 2>&1
uv run pyright propstore > logs/pyright-baseline-2026-04-20.log 2>&1
```
Commit logs to `logs/` (gitignored by default — force-add for this record).

### T0.3 TDD scaffolding
- Add `tests/remediation/` directory with one subdir per phase: `tests/remediation/phase_1_crits/`, etc.
- Each task below gets one test file inside its phase dir named after the finding id.
- Commit the empty-scaffold structure before starting Phase 1.

---

## Phase 1 — Data-loss + directional-lie CRITs

### T1.1 [DESIGN-ANCHORED] Preserve rival claim bodies across two-parent merges

**Issue**: `storage/merge_commit.py:49-55` — `Counter(artifact_id) == 1` filter drops rival bodies. Twin at `propstore/merge/`.

**Principle**: Non-commitment discipline; Clark et al. micropublications.

**RED test**: `tests/remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py`
```python
import hypothesis.strategies as st
from hypothesis import given

@given(
    left_body=st.text(min_size=1, max_size=50),
    right_body=st.text(min_size=1, max_size=50),
)
def test_merge_preserves_rival_bodies(left_body, right_body, tmp_repo):
    """Two-parent merge with same artifact_id + different bodies keeps both."""
    if left_body == right_body:
        return  # skip trivially-equal
    a = tmp_repo.create_branch("a")
    b = tmp_repo.create_branch("b")
    a.write_claim(artifact_id="c-001", body=left_body)
    b.write_claim(artifact_id="c-001", body=right_body)
    merge = tmp_repo.merge(a, b)
    bodies = merge.list_claim_bodies(artifact_id="c-001")
    assert len(bodies) == 2
    assert left_body in bodies
    assert right_body in bodies
```
Expected RED: merge exposes only one body (current `Counter == 1` filter drops both).

**Fix**: Write both under disambiguated paths keyed by `branch_origin`; emit a Dung-backed merge argument resolved at render time. Covers the `propstore/merge/` twin in the same commit because they share the classifier path.

**Commits**:
- `test(storage): rival claim bodies must survive two-parent merge (T1.1 RED)`
- `fix(storage,merge): preserve rival bodies via micropublication-keyed paths (Clark et al.)` — body cites `reviews/2026-04-20-swarm/propstore/storage.md`, `.../merge.md`.

---

### T1.2 [LIT-STRAIGHT] `sidecar/build.py:307-311` — narrow BaseException, diagnostic-row not unlink

**RED test**: `tests/remediation/phase_1_crits/test_T1_2_sidecar_survives_exception.py`
```python
def test_sidecar_not_deleted_on_build_exception(tmp_project, monkeypatch):
    # Force a RuntimeError during one pass but not others
    monkeypatch.setattr(
        "propstore.sidecar.passes.build_claims_pass",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    sidecar_path = tmp_project / ".sidecar"
    assert not sidecar_path.exists()
    tmp_project.build(expect_failure=True)
    assert sidecar_path.exists(), "sidecar deleted on partial-build failure"
    rows = tmp_project.query(
        "SELECT * FROM build_diagnostics WHERE diagnostic_kind='build_exception'"
    )
    assert len(rows) >= 1
```
Expected RED: `except BaseException: unlink()` wipes the sidecar; file does not exist after.

**Fix**: Narrow to `except Exception`, do not unlink, append a `build_diagnostics` row.

**Commits**:
- `test(sidecar): partial-build failure must not unlink sidecar (T1.2 RED)`
- `fix(sidecar): replace unlink-on-BaseException with diagnostic row`

---

### T1.3 [LIT-STRAIGHT] Implement Booth-Meyer 2006 restrained revision

**Issue**: `belief_set/iterated.py:42-52` — `restrained_revise` is byte-identical to `revise`, docstring cites Booth-Meyer falsely.

**RED test**: `tests/remediation/phase_1_crits/test_T1_3_restrained_revise.py`
```python
from propstore.belief_set import Spohn, revise, restrained_revise

def test_restrained_distinguishes_from_plain_revise():
    # Construct a Spohn state where restraint matters:
    # K = {p, q}, rank(p)=0, rank(q)=1, p and q independent.
    # Revising by ¬p ∨ ¬q: plain revise drops both at rank 0;
    # restrained revise preserves q (lower-rank alternative exists).
    K = Spohn.from_ranks({"p": 0, "q": 1})
    phi = "not p or not q"
    plain = revise(K, phi)
    restrained = restrained_revise(K, phi)
    assert plain != restrained, "restrained_revise must differ from revise on RR-probing input"
    assert restrained.believes("q")
    assert not plain.believes("q")
```
Expected RED: both calls return identical state.

**Fix**: Implement Booth-Meyer 2006 §3 restrained revision. Key property: `p ∈ K*_r q` iff `p ∈ revise(K,q)` AND `p` is not defeated by `q` in the entrenchment ordering.

**Property extension**:
```python
from hypothesis import given
from tests.helpers.belief_set import spohn_states, formulas

@given(K=spohn_states(), phi=formulas())
def test_restrained_postulates(K, phi):
    """DP1-DP4 + Booth-Meyer RR postulate."""
    R = restrained_revise(K, phi)
    assert R.believes(phi)  # DP1
    if not K.believes(f"not ({phi})"):
        assert K.implies(R)  # RR
```

**Commits**:
- `test(belief_set): restrained_revise must implement Booth-Meyer 2006 (T1.3 RED)`
- `fix(belief_set): implement Booth-Meyer 2006 restrained revision`

---

### T1.4 [LIT-STRAIGHT] Real provenance through revision traces

**Issue**: `belief_set/agm.py:125-143` hardcodes `1970-01-01` / `STATED` / `ws-b-belief-set-layer`.

**RED test**: `tests/remediation/phase_1_crits/test_T1_4_revision_provenance.py`
```python
from datetime import datetime, timezone
from propstore.belief_set import Spohn, revise
from propstore.provenance import TypedProvenance, ProvenanceStatus

def test_revision_stamps_real_provenance():
    K = Spohn.from_ranks({"p": 0})
    before = datetime.now(timezone.utc)
    result = revise(K, "q", provenance=TypedProvenance(
        status=ProvenanceStatus.CALIBRATED,
        source_artifact_code="unit-test",
    ))
    after = datetime.now(timezone.utc)
    trace = result.history[-1]
    assert trace.provenance.status == ProvenanceStatus.CALIBRATED
    assert trace.provenance.source_artifact_code == "unit-test"
    assert before <= trace.timestamp <= after
    assert trace.timestamp.year != 1970

def test_revision_defaults_vacuous_not_stated():
    """No provenance supplied -> VACUOUS per Jøsang 2001, not STATED."""
    K = Spohn.from_ranks({"p": 0})
    result = revise(K, "q")
    assert result.history[-1].provenance.status == ProvenanceStatus.VACUOUS
```

**Fix**: Add `provenance: TypedProvenance | None = None` parameter to `revise/expand/contract`; default `VACUOUS`.

**Commits**:
- `test(belief_set): revision traces must carry real timestamp and typed provenance (T1.4 RED)`
- `fix(belief_set): thread TypedProvenance through AGM ops; default VACUOUS`
- `refactor(belief_set): update every revise/expand/contract caller`

---

### T1.5 [LIT-STRAIGHT] zip-slip hardening in `source/promote.py:743-751`

**RED test**: `tests/remediation/phase_1_crits/test_T1_5_zip_slip.py`
```python
import pytest
from propstore.source.promote import sync_source_branch

@pytest.mark.parametrize("evil_path", [
    "../escape.txt",
    "subdir/../../escape.txt",
    "..\\windows-escape.txt",
    "./safe/../../escape.txt",
])
def test_sync_rejects_escape_paths(tmp_source_branch, tmp_output_dir, evil_path):
    tmp_source_branch.add_tracked_file(evil_path, b"payload")
    with pytest.raises(ValueError, match="path escapes output_dir"):
        sync_source_branch.copy_tree(tmp_source_branch, tmp_output_dir)
    assert not (tmp_output_dir.parent / "escape.txt").exists()
```

**Fix**: `os.path.commonpath([output_dir_resolved, dest_resolved]) == output_dir_resolved`; reject otherwise.

**Commits**:
- `test(source): sync_source_branch must reject path-escape (T1.5 RED)`
- `fix(source): reject tracked paths escaping output_dir`

---

## Phase 2 — Rule-5 gate generalization

### T2.1 [DESIGN-ANCHORED] `sidecar.quarantine` module

**RED test**: `tests/remediation/phase_2_gates/test_T2_1_quarantine_writer.py`
```python
from propstore.sidecar.quarantine import QuarantinableWriter, Written, Quarantined

def test_writer_quarantines_on_any_failure(tmp_sidecar_conn):
    writer = QuarantinableWriter(tmp_sidecar_conn)
    r1 = writer.try_write(artifact_id="c-1", kind="claim", payload={"ok": True})
    assert isinstance(r1, Written)
    r2 = writer.try_write(artifact_id="c-2", kind="claim", payload=None)
    assert isinstance(r2, Quarantined)
    rows = tmp_sidecar_conn.execute(
        "SELECT * FROM build_diagnostics WHERE artifact_id='c-2'"
    ).fetchall()
    assert len(rows) == 1
```

**Commits**:
- `test(sidecar): QuarantinableWriter must quarantine, never raise (T2.1 RED)`
- `feat(sidecar): add QuarantinableWriter for rule-5 generalization`

### T2.2.a–T2.2.z [LIT-STRAIGHT] Migrate 26 sites, one commit per site

For each of the 26 sites in the synthesis Phase-2 list: RED test with a concrete failing payload for that site; route through `QuarantinableWriter`.

**Example** (`T2.2a`, form validation site — template for others):
```python
def test_invalid_form_quarantines_not_raises(tmp_project):
    tmp_project.write_source_file(
        "forms/bogus.yaml",
        "kind: quantity\nname: !!not valid yaml!!"
    )
    result = tmp_project.build(expect_full_success=False)
    assert result.sidecar_exists
    rows = tmp_project.query(
        "SELECT * FROM build_diagnostics WHERE quarantine_kind='form_validation'"
    )
    assert len(rows) == 1
    assert tmp_project.query_forms(kind="quantity")
```

Sites (one red + fix commit per site): T2.2a sidecar/build.py:95-97 form validation, T2.2b sidecar/build.py:159-161 claim-pipeline None, T2.2c–g sidecar/passes.py 5× dangling-ref IntegrityErrors, T2.2h sidecar/claim_utils.py:515-518 in-claim stance, T2.2i–q compiler/workflows.py 9× CompilerWorkflowError aborts, T2.2r source/promote.py:180-206 ValueError on ambiguous concept, T2.2s source/promote.py:504-506 unresolved concept mapping.

### T2.3 Sidecar invariants

- **T2.3a** `content_hash` includes `SCHEMA_VERSION`. RED: bump `SCHEMA_VERSION`, assert `content_hash` changes without any source change.
  ```python
  def test_content_hash_changes_on_schema_version_bump(tmp_project, monkeypatch):
      h1 = tmp_project.build().content_hash
      monkeypatch.setattr("propstore.sidecar.schema.SCHEMA_VERSION", "99.9")
      h2 = tmp_project.build().content_hash
      assert h1 != h2
  ```
- **T2.3b** Atomic sidecar write. RED: crash-injection between write and rename; prior `.sidecar` intact, `.hash` consistent.
- **T2.3c** `except (ImportError, Exception)` at `sidecar/build.py:293` narrowed. RED: an `ImportError` during optional-dep pass writes diagnostic; `RuntimeError` writes diagnostic; neither silently swallows.

One commit per subtask.

---

## Phase 3 — Honest-ignorance propagation

Template for every fabrication-site task:
```python
def test_<site>_emits_vacuous_when_data_missing():
    result = <call the site with missing data>
    assert result.opinion.uncertainty > 0.99  # vacuous per Jøsang 2001 §2.2
    assert result.provenance.status == ProvenanceStatus.VACUOUS
```

### T3.1 `classify.py` ABSTAIN enum + 4 sub-tasks

- **T3.1a** Add `StanceType.ABSTAIN`. RED:
  ```python
  def test_classify_error_routes_to_abstain():
      result = classify_stance_from_llm_output({"type": "error"})
      assert result.stance_type == StanceType.ABSTAIN
      assert result.opinion.uncertainty > 0.99
  ```
- **T3.1b** `classify.py:96-120` confidence-0 → vacuous. RED: missing confidence → ABSTAIN + vacuous.
- **T3.1c** `classify.py:151` strength default removal. RED: missing strength → ABSTAIN, not fabricated "moderate".
- **T3.1d** `classify.py:242` malformed JSON. RED: malformed LLM output does NOT construct reverse stance.

Red + fix commit per sub-task.

### T3.2 `calibrate.py:193-207` CALIBRATED provenance [LIT-STRAIGHT — Guo 2017]

**RED**:
```python
def test_to_opinion_stamps_calibrated_and_uses_corpus_base_rate(corpus_cdf):
    cal = CorpusCalibrator.from_cdf(corpus_cdf, corpus_base_rate=0.3)
    op = cal.to_opinion(raw_score=0.8)
    assert op.provenance.status == ProvenanceStatus.CALIBRATED
    assert op.provenance.source_artifact_code == "corpus_cdf_calibration"
    assert op.base_rate == 0.3
```

### T3.3 `preference.py:32-36` vacuous on missing metadata [LIT-STRAIGHT — Jøsang]

**RED**:
```python
def test_metadata_strength_vector_vacuous_on_missing():
    rule = Rule(name="r", metadata=None)
    v = metadata_strength_vector(rule)
    assert v.uncertainty > 0.99
    assert v.provenance.status == ProvenanceStatus.VACUOUS
```

### T3.4 `source_calibration.py:93-145` move + consensus operator [DESIGN-ANCHORED]

**RED**:
```python
def test_derive_source_trust_in_heuristic_layer():
    import propstore.heuristic.source_trust as st  # new home
    assert st

def test_caller_prior_combined_via_josang_consensus():
    prior = Opinion(0.7, 0.2, 0.1, 0.5)
    chain = Opinion(0.3, 0.6, 0.1, 0.5)
    combined = derive_source_trust(prior=prior, chain_opinion=chain)
    assert combined not in (prior, chain)
    # Jøsang §4.1 consensus: b_combined weighted by 1-u of each
    ...
```

### T3.5 `core/activation._retry_with_standard_bindings` fail loudly

**RED**:
```python
def test_unknown_cel_identifier_raises_with_context():
    with pytest.raises(UnknownConceptInCEL) as ei:
        activate_claim("some_unknown_concept > 5", source_artifact="test-01")
    assert "some_unknown_concept" in str(ei.value)
    assert "test-01" in str(ei.value)
```

### T3.6 `ic_merge.py:76-78` distance = `math.inf` [LIT-STRAIGHT — KPP 2002]

**RED**:
```python
def test_unsat_profile_member_does_not_shift_winner():
    profile_without = [phi1, phi2]
    profile_with_unsat = [phi1, phi2, Unsat]
    assert ic_merge(profile_without).winners == ic_merge(profile_with_unsat).winners
```

### T3.7 `praf/engine.py:380-384` summarize_defeat_relations provenance

**RED**: every opinion emitted by `summarize_defeat_relations` has `ProvenanceStatus.CALIBRATED` + non-zero uncertainty derived from defeat-distribution variance.

### T3.8 `aspic_bridge/projection.csaf_to_projection:102-106`

**RED**:
```python
def test_grounded_argument_strength_not_zero():
    csaf = build_csaf_with_grounded_only_argument(rule_strength=0.7)
    proj = csaf_to_projection(csaf)
    arg = proj.arguments[0]
    assert arg.strength == 0.7  # per M&P §5.2 rule-ordering minimum
    assert arg.strength != 0.0
```

### T3.9 `fragility_contributors.py` — provenance or vacuous

**RED**: every fragility coefficient carries provenance; none STATED without a citation string.

### T3.10 `provenance/__init__.py:349-371` stamp_file requires status

**RED**:
```python
def test_stamp_file_requires_status_arg():
    with pytest.raises(TypeError):
        stamp_file(path, produced_by="x")  # no status kw
```

### T3.11 Dogmatic-opinion audit [LIT-STRAIGHT]

**RED**: AST scanner test across propstore/ finds every `Opinion(` construction; asserts every dogmatic one (u=0) has an `allow_dogmatic=True` flag with a tautology citation comment on the same line.

Each T3.x: red + fix commit.

---

## Phase 4 — Layer invariants + import-linter

### T4.1 Encode layers in `.importlinter`

**RED test**:
```python
def test_importlinter_catches_known_violations():
    result = subprocess.run(["uv", "run", "lint-imports"], capture_output=True)
    assert result.returncode != 0
    violations = result.stdout.decode()
    assert "storage -> merge" in violations
    assert "concept -> argumentation" in violations
    # every known violation from T4.2-T4.8 present here
```

Fix: add `.importlinter` with contracts matching the 6-layer rule. As each subsequent T4.x lands, the corresponding violation drops from the list.

### T4.2 `storage/merge_commit.py:10` — invert

**RED**: `test_storage_does_not_import_merge` via AST scan (independent of import-linter for fast local feedback).

Fix: move shared logic to neutral module OR invert direction.

### T4.3 `source_calibration.py` relocation

RED covered in T3.4 + import-linter confirmation.

### T4.4 `core/lemon/description_kinds.py` — protocol inversion

**RED**:
```python
def test_description_kinds_does_not_import_argumentation():
    import ast
    with open("propstore/core/lemon/description_kinds.py") as f:
        tree = ast.parse(f.read())
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    for imp in imports:
        module = getattr(imp, "module", None) or imp.names[0].name
        assert not module.startswith("argumentation"), \
            f"layer violation: description_kinds imports {module}"
```

Fix: `DescriptionKindMergeProtocol` in concept layer; argumentation implements.

### T4.5 `support_revision` — remove AGM exports

**RED**:
```python
def test_support_revision_does_not_export_agm():
    import propstore.support_revision as sr
    with pytest.raises(AttributeError):
        sr.revise
    with pytest.raises(AttributeError):
        sr.restrained_revise
```

Fix: delete exports; update `worldline/revision_capture.py` to import from `belief_set`.

### T4.6 `grounding._gunray_complement` — `ComplementEncoder` protocol

**RED**: bridge imports only the protocol; gunray-specific encoder lives in a gunray-adapter module.

### T4.7 `praf/engine.enforce_coh` pre-preference only

**RED**:
```python
def test_enforce_coh_requires_attacks():
    csaf = build_csaf(attacks=None)
    with pytest.raises(PreferenceLayerError):
        enforce_coh(csaf)
```

### T4.8 `defeasibility.apply_exception_defeats_to_csaf` post-preference only

**RED**:
```python
def test_ckr_exception_defeats_in_defeats_only_not_attacks():
    csaf = build_csaf_with_ckr_exception()
    enriched = apply_exception_defeats_to_csaf(csaf)
    ckr_edge = enriched.ckr_exception_edges[0]
    assert ckr_edge in enriched.framework.defeats
    assert ckr_edge not in enriched.framework.attacks
```

Each T4.x: red + fix commit.

---

## Phase 5 — ASPIC+/Dung bridge correctness

### T5.1 `translate.py:135-136` — undermines/supersedes NOT contrary [LIT-STRAIGHT — M&P Def 9]

**RED**:
```python
def test_undermines_is_preference_sensitive():
    csaf = build_test_csaf_with_undermines_pair(prefer="r1 > r2")
    defeats = compute_defeats(csaf.framework, csaf.preferences)
    # Current bug: undermines via contrary_pairs bypasses preference
    assert (r2, r1) not in defeats
```

### T5.2 `build.compile_bridge_context:108-111` — order of operations

**RED**: undercut against grounded defeasible rule currently produces no attack; assert it does.

### T5.3 `translate._transitive_closure` delete

**RED**: cycle-containing input → current impl hangs or wrong output; canonical detects.
```python
def test_transitive_closure_detects_cycle():
    order = [("a", "b"), ("b", "c"), ("c", "a")]
    with pytest.raises(PreferenceCycleError):
        translate._transitive_closure(order)  # will GREEN after delegation
```

### T5.4 `query._goal_contraries` delete — differential test

**RED**:
```python
@given(csaf=csaf_strategy())
def test_goal_contraries_matches_canonical(csaf):
    assert set(query._goal_contraries(csaf)) == set(
        argumentation.aspic._contraries_of(csaf)
    )
```

### T5.5 `_coerce_bridge_stance_row:29-37` no silent rewrite

**RED**:
```python
def test_contradicts_stance_quarantines_not_silently_rewrites():
    row = {"stance_type": "contradicts", ...}
    with pytest.raises(UnknownStanceType):
        _coerce_bridge_stance_row(row)
```

### T5.6 `build.py:184-195` — strengthen or delete

**RED**: property test invariant the guard enforces.

### T5.7 `translate.justifications_to_rules:73-76` no silent drop

**RED**: justification with unknown premise appears in `build_diagnostics`.

### T5.8 `projection.csaf_to_projection:76-80` typed ClaimId

**RED**:
```python
def test_claim_id_not_reconstructed_from_predicate_string():
    csaf = build_csaf_with_grounded_predicate_sharing_claim_name("foo")
    proj = csaf_to_projection(csaf)
    # Claim "foo" and grounded predicate "foo" are DIFFERENT in proj
    assert proj.claim_ids("foo") != proj.predicate_ids("foo")
```

### T5.9 `projection:91-95, 123-127` reconcile premise/dependency claim ids

**RED**: differential input → correct impl returns distinct lists.

### T5.10 `defeasibility._pattern_selects_use:416-423` AUTHORING_UNBOUND

**RED**: unbound-variable pattern distinguishable from solver-UNKNOWN.

### T5.11 `defeasibility.apply_exception_defeats_to_csaf:347-350` sibling survival

**RED**:
```python
def test_zero_attacker_exception_does_not_kill_siblings():
    csaf = build_csaf_with_two_exceptions_one_zero_attackers()
    result = apply_exception_defeats_to_csaf(csaf)
    # Sibling exception still produces defeats
    assert result.ckr_exception_edges
```

Each T5.x: red + fix commit.

---

## Phase 6 — Extend-instead-of-delete (reach further)

### T6.1 `source/alignment.classify_relation` ignorance path [DESIGN-ANCHORED]

**RED**:
```python
def test_classify_relation_returns_ignorance_for_vacuous():
    rel = build_relation_with_opinion(Opinion.vacuous(base_rate=0.5))
    assert classify_relation(rel) == "ignorance"
    # Downstream three-way split, not two-way
```

### T6.2 `argumentation.af_revision.baumann_2015_kernel_union_expand` kernel contraction [LIT-STRAIGHT]

**RED**:
```python
def test_baumann_kernel_preserves_alternative_derivations():
    af = construct_af_with_redundant_paths(target="t", paths=["via_a", "via_b"])
    result = baumann_2015_kernel_union_expand(af, remove="t")
    # Kernel property (Baumann 2015 §4): minimal target-entailing hitting set only
    assert preserves_path(result, "via_a")
    assert preserves_path(result, "via_b")

def test_naive_union_fails_kernel_property():
    # Current impl should fail this; post-fix it passes
    ...
```

### T6.3 `AFChangeKind.RESTRICTIVE` + `QUESTIONING` [LIT-STRAIGHT — Baumann-Brewka 2010]

**RED**:
```python
def test_restrictive_classification():
    before, after = build_ext_pair_strict_shrink()
    assert _classify_extension_change(before, after) == AFChangeKind.RESTRICTIVE

def test_questioning_classification():
    before, after = build_ext_pair_accepted_to_undecided()
    assert _classify_extension_change(before, after) == AFChangeKind.QUESTIONING
```

### T6.4 `ast-equiv/canonicalizer.py:291-298` type-aware [LIT-STRAIGHT]

**RED**:
```python
def test_x_eq_True_preserved_for_non_bool():
    src = "def f(x: int): return x == True"
    assert "== True" in canonical_dump(src) or "== 1" in canonical_dump(src)

def test_x_eq_True_rewritten_for_bool():
    src = "def f(x: bool): return x == True"
    assert "== True" not in canonical_dump(src)
```

### T6.5 Side-effect-aware transforms [LIT-STRAIGHT]

**RED**:
```python
def test_temp_var_inlining_preserves_call_order():
    src = """
def f():
    t = produce()
    g()
    return use(t)
"""
    c = canonical_dump(src)
    assert c.index("produce") < c.index("g")
```

### T6.6 `_concept_satisfies_type` transitive closure

**RED**:
```python
def test_satisfies_type_walks_full_chain():
    # A IS_A B IS_A C IS_A D
    assert _concept_satisfies_type("A", type_name="D")  # 3-hop
```

### T6.7 `validate_atom` type-check arguments

**RED**:
```python
def test_validate_atom_rejects_wrong_kind():
    reg = build_registry_with_pred("pred", signature=[KindType.QUANTITY])
    atom = {"predicate": "pred", "args": ["timepoint_value"]}
    with pytest.raises(PredicateArgKindError):
        reg.validate_atom(atom)
```

### T6.8 Collapse duplicate helpers

**RED**:
```python
def test_form_cache_single_owner():
    from propstore.form_utils import _form_cache as a
    from propstore.families.forms.stages import _form_cache as b
    assert a is b
```

Apply pattern to each duplicated helper: `extend_state`, `_transitive_closure`, `_goal_contraries`, `_form_cache`, `clear_form_cache`. Per-duplicate red + fix commit.

---

## Phase 7 — Race / atomicity

### T7.1 `quire` CAS [LIT-STRAIGHT]

**RED** (stateful):
```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

class ConcurrentRefWriteMachine(RuleBasedStateMachine):
    @rule(sha_a=shas(), sha_b=shas())
    def concurrent_write(self, sha_a, sha_b):
        t1 = threading.Thread(target=lambda: store.write_ref("refs/x", sha_a))
        t2 = threading.Thread(target=lambda: store.write_ref("refs/x", sha_b))
        t1.start(); t2.start(); t1.join(); t2.join()
        # Final ref is exactly one of the two SHAs; never mixed/clobbered race
        assert store.read_ref("refs/x") in (sha_a, sha_b)
```

Fix: `dulwich.set_if_equals` everywhere a ref is mutated. Upstream in quire repo (T10 cross-ref).

### T7.2 `propstore/storage/merge_commit.py:114` expected_head

**RED**: simulate concurrent merge; assert no silent file drop.

### T7.3 `sidecar/build.py` atomic write
(covered in T2.3b)

### T7.4 `propstore/concept_ids.py` ref-backed counter [DESIGN-ANCHORED]

**RED**:
```python
def test_concurrent_concept_id_allocation_unique(tmp_repo):
    # Two threads allocate concurrently; all IDs unique
    ids = []
    lock = threading.Lock()
    def alloc():
        for _ in range(100):
            with lock:
                ids.append(next_concept_id_for_repo(tmp_repo))
    threads = [threading.Thread(target=alloc) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(ids) == len(set(ids))
```

### T7.5 SQLite hardening

- **T7.5a** WAL + busy_timeout on every connect. RED:
  ```python
  def test_concurrent_sqlite_writer_does_not_raise_locked():
      # Without WAL, this hits `database is locked` within ms.
      # With WAL + busy_timeout, it waits then succeeds.
      ...
  ```
- **T7.5b** `source/promote.py:361-364` scope DELETE by branch. RED: promoting branch A must not wipe B's diagnostics.
- **T7.5c** `source/status.py:79-92` escape `_` in LIKE. RED: branch `foo_bar` must not match `foobar`.

### T7.6 Full race suite
One commit: stateful machine covering concurrent merges + ref writes + sidecar builds.

---

## Phase 8 — DoS gates + anytime frames

### T8.1 Cardinality ceilings [DESIGN-ANCHORED — Zilberstein 1996]

**RED** template per site:
```python
def test_<site>_returns_EnumerationExceeded_past_ceiling():
    big = construct_large_input(size=100_000)
    result = <site>(big, max_candidates=1_000)
    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1_000
    assert result.remainder_provenance == ProvenanceStatus.VACUOUS
```

Apply to: `sum_merge_frameworks`, `max_merge_frameworks`, `leximax_merge_frameworks`, `_head_only_bindings`, `enumerate_candidate_assignments`, `_choose_incision_set`, `_iter_future_queryable_sets`, `_distance_to_formula`. Red + fix commit per site.

### T8.2 `ic_merge._distance_to_formula` memo

**RED**: benchmark test — post-fix >10× faster on 6-var signature.

### T8.3 `partial_af` merge tractable routing [DESIGN-ANCHORED — Coste-Marquis 2007]

**RED**: bipartition AF completes in ms; general AF falls through to ceiling.

### T8.4 `world.atms._build` termination guard

**RED**: non-terminating ATMS input → ceiling triggers `EnumerationExceeded`.

### T8.5 `aspic.build_arguments_for` cycle idempotence

**RED**:
```python
@given(csaf=csaf_strategy(), seed_order=order_strategy())
def test_build_arguments_for_order_independent(csaf, seed_order):
    a = build_arguments_for(csaf, goal="g", order=seed_order)
    b = build_arguments_for(csaf, goal="g", order=reversed(seed_order))
    assert a == b
```

---

## Phase 9 — Consumer-drift / public surfaces

### T9.1 `gunray` public types

**RED**:
```python
def test_gunray_ground_defeasible_rule_is_public():
    import gunray
    assert "GroundDefeasibleRule" in gunray.__all__
    from gunray import GroundDefeasibleRule  # must not require .types
```

### T9.2 `quire` public submodules

**RED**:
```python
def test_quire_documents_is_public():
    import quire
    assert "documents" in quire.__all__
```

### T9.3 `ast-equiv` tier enum

**RED**:
```python
def test_sympy_tier_distinct_from_bytecode_tier():
    r_sym = compare(sympy_equivalent_pair)
    r_byte = compare(bytecode_equivalent_pair)
    assert r_sym.tier == Tier.SYMPY
    assert r_byte.tier == Tier.BYTECODE
    assert r_sym.tier != r_byte.tier
```

### T9.4 `bridgman` optional-sympy resolution [DESIGN-ANCHORED]

**RED** (in a sympy-free env):
```python
def test_bridgman_imports_without_sympy():
    import bridgman  # must not crash
    with pytest.raises(SympyRequiredError, match="install.*sympy"):
        bridgman.verify_expr("F=m*a")
```

### T9.5 `ast-equiv` consumer-side exception catching

**RED**:
```python
def test_conflict_detector_handles_recursion_error():
    pathological = build_deeply_nested_ast(depth=10_000)
    result = detect_conflict_on_algorithm_body(pathological)
    # Does NOT crash; quarantines
    assert result.quarantined
```

### T9.6 `ast-equiv` canonicalization-pipeline drift

**RED**:
```python
def test_canonical_dump_matches_normalize_and_canonicalize():
    src = "..."
    concept_names = {"foo", "bar"}
    a = canonical_dump(src, concept_names=concept_names)
    b = _normalize_and_canonicalize(src, concept_names=concept_names)
    assert a == b
```

### T9.7 `bridgman` THETA/Theta normalization

**RED**:
```python
def test_no_THETA_uppercase_in_codebase():
    import subprocess
    result = subprocess.run(["git", "grep", "THETA"], capture_output=True, text=True)
    assert "THETA" not in result.stdout
```

Each T9.x: red + fix commit.

---

## Phase 10 — Upstream dep fixes

**Commit cadence**: upstream red + fix + caller-updates in dep repo → dep SHA bump in propstore as SEPARATE commit.

### T10.1 `gunray/schema.py` tuples + unique rule IDs

**RED** (in gunray repo):
```python
def test_rule_body_immutable():
    r = Rule(name="r", body=("a", "b"))
    with pytest.raises(AttributeError):
        r.body.append("c")
    assert hash(r)  # no TypeError

def test_duplicate_rule_id_rejected_cross_kind():
    with pytest.raises(DuplicateRuleId):
        DefeasibleTheory(strict=[Rule(name="r", ...)], defeasible=[Rule(name="r", ...)])
```

### T10.2 `gunray/defeasible.py:84` route closure policies

**RED**: closure-policy input dispatches to `ClosureEvaluator`; not `del`.

### T10.3 `gunray/adapter.py:27` public suite bridge

**RED**: no private `_core` attribute access; uses public constructor.

### T10.4 `argumentation/af_revision.py` Baumann kernels (cross-ref T6.2)

### T10.5 `argumentation/dung.py` stable-extension pinning [DESIGN-ANCHORED]

**RED**: pinning test encoding the chosen semantics; document choice in CITATIONS.md.

### T10.6 `argumentation/af_revision._extend_state:207` unknown rank

**RED**:
```python
def test_unknown_rank_raises():
    state = ...
    with pytest.raises(UnknownArgumentRank) as ei:
        _extend_state(state, unknown_arg="x")
    assert "x" in str(ei.value)
```

### T10.7 `argumentation.semantics.accepted_arguments:103-126`

**RED**:
```python
def test_empty_extension_family_stable_returns_sentinel():
    result = accepted_arguments(frozenset(), semantics="stable")
    assert result is SemanticsUndefined
```

### T10.8 `quire/versions.py:27-30` NotImplemented

**RED**:
```python
def test_version_id_non_calendar_comparison():
    v = VersionId.from_string("2026.01")
    assert v.__lt__(object()) is NotImplemented
```

### T10.9 `quire/git_store.py:163-182` use `_repo_object`

**RED**:
```python
@given(path=paths_and_states())
def test_exists_agrees_with_walk_tree(path):
    assert store.exists(path) == (path in store._walk_tree())
```

### T10.10 `bridgman` symbolic Pow wrap

**RED**:
```python
def test_symbolic_pow_wraps_type_error():
    x, n = sympy.Symbol("x"), sympy.Symbol("n")
    with pytest.raises(DimensionalError, match="non-numeric exponent"):
        bridgman.symbolic.dims_of_expr(x**n)
```

### T10.11 `ast-equiv/sympy_bridge._reduce_stmts` symmetry

**RED**:
```python
@given(a=bodies(), b=bodies())
def test_compare_symmetric(a, b):
    assert compare(a, b).equivalent == compare(b, a).equivalent
```

### T10.12 Dep CLAUDE.md alignment
Non-test doc cleanup. Single commit per dep.

Each upstream task: RED + fix + bump commit in propstore (3 commits per task).

---

## Phase 11 — CLI hygiene

27 items. Per cli.md: pick smallest failing assertion, red + fix.

High-visibility:

### T11.1 `proposal_cmds.py:40-44`

**RED**:
```python
def test_pks_proposal_promote_reports_actual_count(cli_runner, tmp_project):
    tmp_project.stage_proposals(count=3)
    # Promote succeeds on 2 of 3
    tmp_project.force_promote_failure_on_one()
    result = cli_runner.invoke(["proposal", "promote", "--all"])
    assert "Promoted 2 of 3" in result.output  # not "3"
```

### T11.2 `pks show` / `pks checkout` exit codes

**RED**:
```python
def test_pks_show_not_found_returns_2(cli_runner):
    result = cli_runner.invoke(["show", "nonexistent-artifact"])
    assert result.exit_code == 2
    assert "not found" in result.stderr
```

### T11.3 `worldline_refresh` default duplication

**RED**:
```python
def test_worldline_refresh_default_single_source():
    # Change @click.option default via monkeypatch; assert hardcoded default reflects
    ...
```

### T11.4 Dead `emit_prefixed_error` wire or delete

**RED**: AST scan asserts either no error emissions bypass the helper, OR the helper is not imported anywhere post-fix.

### T11.5 `coerce_worldline_cli_value` / `parse_world_binding_args` relocation

**RED**: import-linter rule fires on owner module containing CLI-only helpers.

Remaining 22 items: one red + fix commit each per synthesis list.

---

## Phase 12 — Final verification + paper-PNG gates

**Per `feedback_tdd_and_paper_checks`**: per-chunk foreman + coder + reviewer.

### T12.1 Full suite green
`powershell -File scripts/run_logged_pytest.ps1 tests/` passes. Commit cleared log.

### T12.2 Pyright package check green
`uv run pyright propstore` passes. Commit cleared log.

### T12.3 Import-linter green
`uv run lint-imports` passes on all contracts. Commit cleared log.

### T12.4 Paper-PNG verification pass

For every paper-cited fix, open the paper PNGs and verify the implementation matches the definition verbatim:
- Booth-Meyer 2006 Restrained Revision (T1.3)
- Baumann 2015 Kernel Contraction (T6.2, T10.4)
- Baumann-Brewka 2010 AF revision categories (T6.3)
- Jøsang 2001 Subjective Logic (T1.4, T3.3, T3.4, T3.7)
- Guo et al. 2017 Calibration (T3.2)
- Konieczny-Pino Perez 2002 IC Merging (T3.6)
- Modgil-Prakken ASPIC+ (T5.1, T3.8)
- Dung 1995 AFs (T10.5)
- Coste-Marquis et al. 2007 Merging (T8.3)
- Caminada-Wu 2009 COH (T4.7)
- Chow 1970 reject option (T3.1)
- García-Simari 2004 DeLP (gunray alignment, T10.x)

One verification commit per paper: `chore(verify): <paper> implementation matches PDF pp.X-Y`.

### T12.5 Property-test sweep

Hypothesis property tests for every principle-level invariant:
- Non-commitment preservation (merge does not drop)
- Honest-ignorance preservation (no dogmatic opinion without tautology)
- Layer-import invariant (enforced via import-linter)
- CAS retry (concurrent writers converge)
- Anytime partial-result provenance (incomplete enumerations stamp VACUOUS)

Each property: one commit.

---

## Honest risk ledger

- Phase 1 T1.1 (merge disagreement preservation) and Phase 4 (layer inversions) are the highest-design-load tasks. They may reveal further architecture decisions that require Q alignment mid-phase — pause and discuss per `feedback_friction_not_notes`.
- Phase 10 depends on each dep repo accepting upstream fixes. All are `ctoth/` repos so coordination cost is low.
- Phase 12 paper-PNG checks are time-consuming but non-negotiable.
- Dead-code-lies that correspond to real concepts (restrained_revise, Baumann kernels, ignorance classification, RESTRICTIVE/QUESTIONING) are implementation commitments. If any turn out to require more literature than anticipated, split the phase and escalate.

## Commit count estimate

| Phase | Estimate |
|---|---|
| 0 | ~4 |
| 1 | 5 tasks × 2–3 = ~13 |
| 2 | 1 scaffold + 26 × 2 + 3 invariants = ~56 |
| 3 | 11 × 2–3 = ~30 |
| 4 | 8 × 2 = ~16 |
| 5 | 11 × 2 = ~22 |
| 6 | 8 × 2 = ~16 |
| 7 | 6 × 2–3 = ~16 |
| 8 | 5 × 2 = ~10 |
| 9 | 7 × 2 = ~14 |
| 10 | 12 × 3 = ~36 |
| 11 | ~27 × 2 = ~54 |
| 12 | 12 papers + 5 properties = ~17 |

**Total: ~300 commits.** Small commits, not large ones. Each reversible; each reviewable in under five minutes. The history is the audit trail.
