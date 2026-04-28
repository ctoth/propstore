# WS-CM: Micropub canonical payload and Trusty URI identity

**Status**: OPEN
**Depends on**: WS-A (schema fidelity; canonical payload construction must use the real micropub schema), RFC 6920 / Kuhn 2014 Trusty URI reference already cited by WS-M.
**Blocks**: WS-C Step 3 (sidecar micropub dedupe-shape correctness), WS-M Trusty URI provenance integration.
**Owner**: Codex implementation owner + human reviewer required.

---

## Why this workstream exists

WS-C needs content-derived micropub ids so sidecar dedupe is honest. WS-M needs Trusty URI identity and verification so provenance is content-addressed. The previous plans let WS-C wait on WS-M's hash helper while WS-M waited on WS-C's payload shape; WS-C then proposed a placeholder hash to break the cycle. That is the wrong shape: identity is not a temporary surface.

D-7 and D-29 settle the ownership: this workstream owns the canonical micropub payload and the Trusty URI artifact id over that payload. WS-C and WS-M both consume it.

No placeholder hash. No `(source_id, claim_id)` identity. No transition id. No fallback reader for old micropub ids.

## Review findings covered

| Finding | Source | Description |
|---|---|---|
| D-7 | DECISIONS.md | Micropub identity is content-derived from full canonical payload. |
| D-29 | DECISIONS.md | Break WS-C/WS-M cycle by extracting shared prerequisite. |
| Codex re-review | WS-C/WS-M | Remove placeholder hash path and contradictory ownership text. |

## Target surface

New owner-layer API:

```python
def canonical_micropub_payload(document: MicropublicationDocument) -> bytes:
    """Return deterministic canonical bytes for micropub identity."""

def micropub_artifact_id(document: MicropublicationDocument) -> str:
    """Return ni:///sha-256;<digest> over canonical_micropub_payload(document)."""
```

The implementation may live in `propstore/source/finalize.py` only if that is the owner layer for the `MicropublicationDocument` type. If the canonical payload is shared outside source finalization, move it to the narrowest owner module that does not import CLI, sidecar SQL, or presentation code.

The canonical payload includes authored micropub content and excludes recursive identity fields (`artifact_id`, `version_id`) whose values are derived from the payload. It must not include render-only ordering or readability metadata.

## First failing tests

1. **`tests/test_micropub_identity_trusty_uri.py`**
   - Build two micropub documents with the same canonical content but different input key/order presentation.
   - Assert `micropub_artifact_id(doc1) == micropub_artifact_id(doc2)`.
   - Assert the id starts with `ni:///sha-256;`.
   - Mutate one semantic field and assert the id changes.
   - Must fail today: `_stable_micropub_artifact_id` hashes `(source_id, claim_id)` and truncates.

2. **`tests/test_micropub_identity_not_logical_handle.py`**
   - Generate or construct two micropubs with the same `(source_id, claim_id)` but different authored content.
   - Assert they produce different artifact ids.
   - Assert no code path computes micropub artifact id from only `(source_id, claim_id)`.

3. **`tests/test_micropub_trusty_verification.py`**
   - Assert `verify_ni_uri(micropub_artifact_id(doc), canonical_micropub_payload(doc))` succeeds.
   - Assert verification against mutated canonical bytes fails.

4. **Hypothesis property gates** from `reviews/2026-04-26-claude/PROPERTY-BASED-TDD.md`
   - Same canonical micropub payload always produces the same id.
   - Non-semantic ordering permutations do not change the id.
   - Semantic mutations change the id.
   - Verification succeeds only against exact canonical bytes.

## Production change sequence

1. Add the tests above. Keep them red until the production identity surface changes.
2. Delete `_stable_micropub_artifact_id(source_id, claim_id)` as an identity surface.
3. Add `canonical_micropub_payload(document)` and `micropub_artifact_id(document)` over the full canonical payload.
4. Update source finalization to call `micropub_artifact_id(document)` when assigning the micropub artifact id.
5. Expose the Trusty URI verification helper needed by WS-M, or import the existing WS-M helper only if that helper has already landed without introducing a reverse dependency.
6. Update `docs/gaps.md` and flip `tests/test_workstream_cm_done.py` from `xfail` to `pass`.

## Acceptance gates

- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-CM tests/test_micropub_identity_trusty_uri.py tests/test_micropub_identity_not_logical_handle.py tests/test_micropub_trusty_verification.py tests/test_workstream_cm_done.py`
- [ ] Relevant Hypothesis property tests from `PROPERTY-BASED-TDD.md` are included in that logged run or in a named companion run.
- [ ] `rg -F "_stable_micropub_artifact_id(source_id, claim_id)" propstore tests` finds no production identity surface.
- [ ] No placeholder hash or TODO identity function exists.
- [ ] This file's STATUS is `CLOSED <sha>`.

## Cross-stream notes

- **WS-C** consumes this workstream for sidecar dedupe-shape tests. WS-C does not define the hash basis and does not install a placeholder.
- **WS-M** consumes this workstream for Trusty URI provenance verification. WS-M can own broader provenance export, but not the micropub payload shape.
- **WS-E** source promotion can assume micropub ids are already content-derived once WS-CM closes.
