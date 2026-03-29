import json

import propstore.form_utils as form_utils
import propstore.validate_claims as validate_claims
from propstore.resources import resource_exists


def test_packaged_schema_resources_exist():
    assert resource_exists("schemas/claim.schema.json")
    assert resource_exists("schemas/concept_registry.schema.json")
    assert resource_exists("schemas/form.schema.json")


def test_claim_schema_loads_from_packaged_resources():
    validate_claims._claim_schema_cache = None
    schema = validate_claims._load_claim_schema()
    assert isinstance(schema, dict)
    assert "$defs" in schema
    assert "ClaimFile" in json.dumps(schema)


def test_form_schema_loads_from_packaged_resources():
    form_utils._form_schema_cache = None
    schema = form_utils._load_form_schema()
    assert isinstance(schema, dict)
    assert schema.get("$id") == "https://propstore.dev/schema/form.schema.json"
