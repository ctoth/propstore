"""Characterization tests for the claim compiler middle-end."""

from __future__ import annotations

import yaml

from propstore.families.claims.passes import compile_claim_files, run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle
from propstore.families.registry import semantic_foreign_keys
from tests.family_helpers import build_compilation_context_from_paths, load_claim_files
from tests.conftest import (
    make_concept_registry,
    make_compilation_context,
    make_parameter_claim,
    normalize_claims_payload,
    normalize_concept_payloads,
)
