from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.compiler.workflows import write_repository_world_store as build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads
from tests.family_helpers import (
    claim_artifact_commit_payloads,
    stance_artifact_commit_payload,
)
