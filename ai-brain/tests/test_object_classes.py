"""Unit tests for shared object-class normalization."""

import pytest
from object_classes import ALLOWED_OBJECT_CLASSES, normalize_object_class
from osint_agent import ThreatClassification
from pydantic import ValidationError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("person", "person"),
        ("Person", "person"),
        (" PERSON ", "person"),
        ("man", "person"),
        ("woman", "person"),
        ("suspect", "person"),
        ("pedestrian", "person"),
        ("vehicle", "vehicle"),
        ("car", "vehicle"),
        ("truck", "vehicle"),
        ("van", "vehicle"),
        ("bus", "vehicle"),
        ("crowd", "crowd"),
        ("mob", "crowd"),
        ("people", "crowd"),
        ("package", "package"),
        ("parcel", "package"),
        ("box", "package"),
        ("backpack", "package"),
        ("unknown", "unknown"),
    ],
)
def test_normalize_maps_allowed_classes_and_synonyms(raw, expected):
    """Each allowed class and listed synonym maps to its shared label."""

    assert normalize_object_class(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["weapon", "firearm", "knife", "drone", "animal", "xyz", ""],
)
def test_normalize_unknown_fallback(raw):
    """Labels outside the synonym map become unknown."""

    assert normalize_object_class(raw) == "unknown"


def test_allowed_object_classes_are_exactly_five():
    """The shared vocabulary is the five classes used for corroboration."""

    assert ALLOWED_OBJECT_CLASSES == {
        "person",
        "vehicle",
        "crowd",
        "package",
        "unknown",
    }


def test_threat_classification_normalizes_synonyms():
    """Classifier structured output is coerced onto a shared class."""

    result = ThreatClassification(object_class="Truck", confidence_score=0.8)

    assert result.object_class == "vehicle"


def test_threat_classification_maps_unknown_labels():
    """Unrecognized classifier labels become unknown, not raw text."""

    result = ThreatClassification(object_class="weapon", confidence_score=0.4)

    assert result.object_class == "unknown"


def test_threat_classification_rejects_blank_object_class():
    """Empty object_class is still invalid structured output."""

    with pytest.raises(ValidationError):
        ThreatClassification(object_class="   ", confidence_score=0.1)
