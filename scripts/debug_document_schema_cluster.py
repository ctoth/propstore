from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import yaml

from propstore.cli.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload


if __name__ == "__main__":
    debug_context_fixture()
    debug_physics_parameterizations()
