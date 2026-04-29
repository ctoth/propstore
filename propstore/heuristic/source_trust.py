"""Source-level trust opinion utilities."""

from __future__ import annotations

from propstore.opinion import Opinion, consensus


def derive_source_trust(*, prior: Opinion, chain_opinion: Opinion) -> Opinion:
    """Combine caller prior and source-chain trust by Jøsang consensus.

    Jøsang 2001 (§4.1) combines independent opinions by consensus rather than
    choosing one source of trust and discarding the other.
    """

    return consensus(prior, chain_opinion)
