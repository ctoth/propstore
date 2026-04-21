from propstore.opinion import Opinion, consensus


def test_derive_source_trust_in_heuristic_layer() -> None:
    import propstore.heuristic.source_trust as source_trust

    assert source_trust


def test_caller_prior_combined_via_josang_consensus() -> None:
    from propstore.heuristic.source_trust import derive_source_trust

    prior = Opinion(0.7, 0.2, 0.1, 0.5)
    chain = Opinion(0.3, 0.6, 0.1, 0.5)
    combined = derive_source_trust(prior=prior, chain_opinion=chain)

    assert combined == consensus(prior, chain)
    assert combined not in (prior, chain)
