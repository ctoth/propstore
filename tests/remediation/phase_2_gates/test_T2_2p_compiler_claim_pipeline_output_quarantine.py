from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.families.claims.stages import ClaimStage
from propstore.families.registry import PropstoreFamily
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic, PipelineResult
from tests.conftest import normalize_claims_payload, normalize_concept_payloads
from tests.family_helpers import claim_artifact_commit_payloads
