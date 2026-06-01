from __future__ import annotations

from pathlib import Path

from quire.derived_store import DerivedStoreHandle
import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads
