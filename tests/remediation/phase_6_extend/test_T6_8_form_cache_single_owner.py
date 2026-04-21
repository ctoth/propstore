def test_form_cache_has_single_owner_across_public_and_stage_helpers():
    from propstore.families.forms.stages import (
        _form_cache as stage_cache,
        clear_form_cache as clear_stage_cache,
    )
    from propstore.form_utils import (
        _form_cache as public_cache,
        clear_form_cache as clear_public_cache,
    )

    assert public_cache is stage_cache

    public_cache[("repo", "frequency")] = None
    clear_stage_cache()
    assert public_cache == {}

    stage_cache[("repo", "pressure")] = None
    clear_public_cache()
    assert stage_cache == {}
