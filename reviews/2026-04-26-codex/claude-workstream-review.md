# Review of Claude's expanded workstreams

Date: 2026-04-27

## Read status

I read Claude's `DECISIONS.md`, `REMEDIATION-PLAN.md`, `CROSS-CHECK-vs-codex.md`, `workstreams/INDEX.md`, and the high-risk workstreams most likely to contain ordering or omission errors: WS-A, WS-B, WS-C, WS-D, WS-E, WS-K, WS-L, WS-M, WS-N, WS-O-qui, WS-O-gun, WS-P, and WS-J2.

I did not read every line of every WS-O argumentation substream, WS-F, WS-G, WS-H, WS-I, WS-J, or WS-K2 in this pass. Claims below are limited to the files I read and the searches I ran.

## Verdict

Claude caught a lot that the Codex review either missed or underweighted: the quire substrate bugs, the gunray performance/boundary problems, the source-trust-as-argumentation correction, the source/promote git-before-sidecar decision, the WBF/pignistic decisions, and the need to split Pearl `do()` worlds from hypothetical overlays.

The expanded plan is not yet execution-ready. It has several cross-stream contradictions, a few critical findings that are explicitly deferred but not assigned, and some steps that violate the local no-compatibility/no-old-path rules. Those should be fixed before the workstream set becomes the source of truth.

## Misses and Amendments

### 1. Embedding model-key collisions are still not owned

Codex's finding that `_sanitize_model_key` collapses distinct model names (`a/b`, `a-b`, `a_b`, `a b`) appears only as an out-of-scope note in WS-C and as prior cross-check text. WS-K says embedding registry admission control is "captured here, fix lives elsewhere," but no workstream owns the key-collision bug.

Amendment: add a new task to WS-K or WS-C that replaces sanitized model keys with collision-proof identity, preferably `(provider, model_name, model_version, digest)` as data, not as a lossy SQL/table suffix. First failing test: register four colliding model names and assert they produce distinct sidecar status/cache identities.

### 2. Short/truncated hash policy is deferred without an owner

WS-C says short 16/24-hex identity hashes are a "separate WS." WS-M simultaneously proposes Trusty URI / RFC 6920-style identity. There is no explicit workstream that resolves all truncated identity surfaces.

Amendment: create a small identity-policy stream, or fold it into WS-M, covering every `[:16]`, `[:24]`, shortened SHA, and display-vs-identity split. Done means no production identity is a truncated hash; truncation is display-only.

### 3. WS-C and WS-M conflict on micropub identity

WS-C Step 3 says `artifact_id` hashes the full payload minus `artifact_id`, then computes `version_id` over the now-complete dict, which implies `version_id` includes `artifact_id`. It also says keep the existing `[:24]` truncation for micropub artifact IDs.

WS-M Step 9 says micropub IDs become Trusty URIs over payload minus both `version_id` and `artifact_id`, with full verifiable identity.

These cannot both be true.

Amendment: make WS-M the single authority for micropub identity and update WS-C to depend on that decision. The hash basis must be written once: exactly which fields are excluded for artifact identity, exactly which fields are excluded for version identity, and whether either can include the other.

### 4. WS-M proposes a migration command despite the no-old-data rule

WS-M Step 9 proposes `propstore migrate-micropub-ids`. That conflicts with the project rule and Claude's own D-3 decision: no old-data shims or compatibility/migration paths unless the user explicitly says old repos must be supported.

Amendment: delete the migration command from the default plan. If old repo support becomes required later, add it as an explicitly user-approved compatibility workstream.

### 5. WS-M proposes optional PROV-O alongside internal payload

WS-M says PROV-O may be emitted "optionally" alongside the internal payload. In this repo, optional parallel representations tend to become dual production paths.

Amendment: either make PROV-O the canonical serialization for provenance export only, generated from one internal domain model, or keep it out of production. Do not add a second mutable provenance payload path.

### 6. WS-B has an unresolved policy behavior conflict

WS-B's first step says blocked claim views should raise `ClaimViewBlockedError` and map to 403/404. The same stream also discusses redacted/a11y HTML markers. Those are different product behaviors: no populated page vs populated redacted page.

Amendment: choose one. For repository-local claim pages, I think the stricter behavior is better: blocked means no claim view is rendered at all. A11y tests should assert the error page has a useful title/message, not that redacted claim content is present.

### 7. Branch-head CAS is still under-specified at propstore call sites

WS-O-qui documents quire's expected-head semantics. WS-C and WS-E mention branch-head races. I did not see a concrete propstore-side acceptance gate that every import/finalize/promote path passes the exact branch head it read into the subsequent commit.

Amendment: add a propstore test matrix: concurrent source finalize, source promote, repository import, and materialize/build all lose a race and fail without writing sidecar state. The test should assert the expected head is captured before mutation and threaded to quire, not merely that quire can reject a stale head.

### 8. URI authority and privileged namespace validation are dropped

WS-E explicitly excludes `propstore/uri.py` authority validation and `concept_ids.py` privileged namespace checks. I did not find another owner.

Amendment: add a compact identity-boundary stream or expand WS-A. First failing tests: source-local input cannot mint canonical `ps:`/privileged IDs; source-local aliases cannot collide with reserved canonical namespaces; invalid authorities hard-fail at the IO boundary.

### 9. WS-P conflicts with D-14 on bytecode

DECISIONS.md D-14 says delete the `ast-equiv` bytecode tier. WS-P still mentions whitelisting `Tier.BYTECODE`.

Amendment: remove BYTECODE from WS-P. If the bytecode tier is deleted, CEL equivalence must be parser/AST/symbolic only.

### 10. WS-P's division-by-zero encoding is unsound as written

WS-P proposes encoding division as `If(right == 0, FreshConst(undef), left / right)`. That can make formulas satisfiable through arbitrary undefined values instead of preserving CEL's runtime/error semantics.

Amendment: model definedness explicitly. Every expression should produce `(value, defined)` or an equivalent path condition, and comparisons involving undefined branches should follow the chosen CEL error policy. Do not use unconstrained fresh constants as a semantic substitute.

### 11. WS-P needs domain-aware equivalence tests

WS-P says `log(x*y)` vs `log(x)+log(y)` should not be `DIFFERENT`. Over real arithmetic, that equivalence requires domain assumptions such as `x > 0` and `y > 0`. Without those, the correct answer is at best `UNKNOWN`.

Amendment: every symbolic equivalence fixture must include domain assumptions in the test name and assertion. No algebraic identity should be accepted outside its mathematical domain.

### 12. WS-N is over-dependent on WS-K

WS-N depends on WS-K because the final layered architecture contract needs the heuristic namespace to be settled. But WS-N also contains independent architecture fixes: CLI ownership, shim deletion, import-linter scaffolding, docs drift, and package `__init__` shallowness.

Amendment: split WS-N into:

- WS-N1: immediate architecture gates and CLI-owner extraction that do not depend on WS-K.
- WS-N2: final six-layer contract after WS-K moves heuristic modules.

This prevents the trust-calibration epic from blocking simple architectural hardening.

### 13. WS-M should not default to full gunray argument return before budget wiring

WS-M wants propstore to default `return_arguments=True`. WS-O-gun documents that argument enumeration is exponential and that `EnumerationExceeded` must be wired.

Amendment: WS-M must depend on WS-O-gun's budget/anytime step before enabling argument return by default. Before that, tests should prove budget exhaustion produces `ResultStatus.BUDGET_EXCEEDED`, not a hang or partial "complete" result.

### 14. WS-E's dangling-justification rule may reject valid master references

WS-E says promotion should require every justification conclusion/premise to be in the current batch's `valid_artifact_ids`. That catches source-branch dangling references, but it may also reject a new source claim justified by an already-accepted master claim.

Amendment: the first failing test should distinguish:

- invalid: a premise points to another source-local artifact not promoted in this batch;
- valid: a premise points to an existing canonical/master artifact.

The rule should be "every reference resolves either in the current promotion batch or in the canonical repository snapshot being promoted against."

### 15. WS-C's cache semantic version plan is too manual

WS-C proposes a hand-maintained `BUILD_SEMANTIC_VERSION` plus CI commit-message exceptions. That is weak for a derived sidecar cache.

Amendment: derive the cache compatibility key from the actual inputs: sidecar schema version, pass names/versions, generated schema version, dependency pins that affect derived rows, and config. A manual override can exist, but it should not be the primary invalidation mechanism.

### 16. WS-K leaves two forward/reverse disagreement bugs as deferred

WS-K fixes `dedup_pairs`, but explicitly defers the single bidirectional LLM call and perspective-conflated stance filing. Those are the same non-commitment family as `dedup_pairs`.

Amendment: either keep them in WS-K or create a named WS-K3. Do not leave H10/H11 as prose-only deferrals. First failing tests should prove forward and reverse observations can disagree independently and persist under perspective-specific source claims.

### 17. WS-J2 is a feature epic, not a remediation blocker

The separate `InterventionWorld`/actual-cause stream is good architecture if the project wants Pearl/Halpern causality. It should not block fixing review findings unless a current production path falsely claims Pearl `do()` semantics.

Amendment: mark WS-J2 as a feature/research workstream unless a concrete current bug is tied to it. The bug-fix critical path should be WS-A/B/C/D/E/K/L/M/N plus the relevant dependency streams.

## What Claude Caught That Codex Underweighted

Claude's new plan correctly expands several areas:

- Quire is not just a dependency pin; its canonicalization, CAS, worktree, and reference APIs are part of propstore's correctness boundary.
- Gunray's exponential argument construction and double-grounding are not performance nits; they affect whether provenance can be made default.
- Source trust should be an argumentation output from accepted meta-paper rules, not a heuristic proposal family.
- WBF and pignistic are not naming-only fixes; the math must change to match the cited papers.
- Merge sameAs union-find is the Beek-style pathology and needs defeasible identity assertions, not a nicer grouping function.

## Ordering Changes I Recommend

1. Keep WS-A first, but do not let it absorb unrelated policy work beyond schema/test honesty.
2. Run WS-D and WS-O-qui in parallel with WS-A.
3. Before WS-C/WS-M implementation, settle a single identity policy for micropub, hash truncation, Trusty URI claims, and version-id hash basis.
4. Split WS-N so the independent architecture gates can land early.
5. Gate WS-M's gunray provenance default on WS-O-gun budget handling.
6. Add explicit owners for embedding model-key identity, URI authority/privileged namespace validation, and forward/reverse LLM observation independence.

## Bottom Line

Claude did not merely miss small bugs; it left a few correctness findings without owners and introduced contradictions between workstreams. The most important fixes before execution are: unify identity policy, delete the migration/compatibility path from WS-M, assign embedding and URI namespace bugs, split WS-N, and make WS-M depend on gunray budget handling before default argument provenance is enabled.
