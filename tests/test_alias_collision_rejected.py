from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from quire.references import AmbiguousReferenceError

from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads
