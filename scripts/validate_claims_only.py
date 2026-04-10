"""Validate claims files only (skip form validation)."""
from pathlib import Path
from propstore.claim_documents import load_claim_files
from propstore.compiler.passes import validate_claims
from propstore.cli.repository import Repository

root = Path(".")
r = Repository(root)
cs = load_claim_files(r.claims_dir)
res = validate_claims(cs, r)
for e in res.errors:
    print(f"ERROR: {e}")
for w in res.warnings:
    print(f"WARNING: {w}")
print(f"\nResult: {'OK' if res.ok else 'FAILED'}, {len(res.errors)} error(s), {len(res.warnings)} warning(s)")
