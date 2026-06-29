"""WS-I Step 3: categorical parameterization inputs must be visible."""

from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason="categorical Claim.value needs a charter extension — see docs/gaps.md "
    "(rewrite Claim.value is float-only; categorical providers cannot be authored)"
)
def test_ws_i_categorical_provider_creates_visible_rejected_derived_node() -> None:
    """E.H3: categorical providers are rejected explicitly, not silently dropped.

    Reference gaps Cluster E HIGH E.H3. The engine already surfaces a
    parameterization input-type incompatibility as a visible OUT
    ``ATMSDerivedNode`` carrying
    ``ATMSOutKind.PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE`` (see
    ``ATMSEngine._materialize_parameterization_input_rejection`` — the engine
    behaviour is implemented and honest, never a silent drop). Exercising it,
    however, needs a *categorical claim value* ("red") feeding a
    parameterization, which the float-only rewrite ``Claim.value`` charter
    cannot represent. There is no charter path to author a non-numeric provider
    value, so the behaviour cannot be driven end-to-end in this coverage slice.
    Unskip once the Claim charter carries categorical/boolean values
    (docs/gaps.md categorical-provider entry).
    """
