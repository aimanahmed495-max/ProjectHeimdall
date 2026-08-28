import pytest

from backend.app.state import determine_threat_level


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0, "NORMAL"),
        (30, "NORMAL"),
        (31, "SUSPICIOUS"),
        (50, "SUSPICIOUS"),
        (51, "ELEVATED"),
        (70, "ELEVATED"),
        (71, "HIGH_THREAT"),
        (90, "HIGH_THREAT"),
        (91, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_determine_threat_level_boundaries(score, expected_level):
    assert determine_threat_level(score) == expected_level


@pytest.mark.parametrize("score", [-1, 101])
def test_determine_threat_level_rejects_out_of_range_scores(score):
    with pytest.raises(ValueError):
        determine_threat_level(score)