from propstore.heuristic.calibrate import CorpusCalibrator
from propstore.provenance import ProvenanceStatus


def test_to_opinion_stamps_calibrated_and_uses_corpus_base_rate() -> None:
    calibrator = CorpusCalibrator.from_cdf(
        [0.1, 0.2, 0.4, 0.8],
        corpus_base_rate=0.3,
    )

    opinion = calibrator.to_opinion(raw_score=0.25)

    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.CALIBRATED
    assert opinion.provenance.witnesses
    assert (
        opinion.provenance.witnesses[0].source_artifact_code
        == "corpus_cdf_calibration"
    )
    assert opinion.base_rate == 0.3
