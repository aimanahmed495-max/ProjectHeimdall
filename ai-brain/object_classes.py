"""Shared visual object classes for OSINT classification and corroboration."""

from __future__ import annotations

# Canonical classes shared by the classifier and corroboration tracker.
ALLOWED_OBJECT_CLASSES = frozenset(
    {"person", "vehicle", "crowd", "package", "unknown"}
)

# Obvious synonyms the classifier may emit for the same visual class.
_SYNONYMS: dict[str, str] = {
    # person
    "man": "person",
    "woman": "person",
    "men": "person",
    "women": "person",
    "guy": "person",
    "girl": "person",
    "male": "person",
    "female": "person",
    "suspect": "person",
    "pedestrian": "person",
    "individual": "person",
    "human": "person",
    "intruder": "person",
    # vehicle
    "car": "vehicle",
    "truck": "vehicle",
    "van": "vehicle",
    "bus": "vehicle",
    "automobile": "vehicle",
    "motorcycle": "vehicle",
    "bike": "vehicle",
    "bicycle": "vehicle",
    "suv": "vehicle",
    "taxi": "vehicle",
    "sedan": "vehicle",
    # crowd
    "mob": "crowd",
    "group": "crowd",
    "gathering": "crowd",
    "people": "crowd",
    "protesters": "crowd",
    "protestors": "crowd",
    "riot": "crowd",
    # package
    "parcel": "package",
    "box": "package",
    "bag": "package",
    "backpack": "package",
    "suitcase": "package",
    "luggage": "package",
    "bundle": "package",
}


def normalize_object_class(raw: str) -> str:
    """Map a classifier label to one shared object class.

    Args:
        raw: Free-form class string from the model or a test double.

    Returns:
        One of ``person``, ``vehicle``, ``crowd``, ``package``, or
        ``unknown``. Empty input becomes ``unknown``.
    """

    key = raw.strip().lower()
    if not key:
        return "unknown"
    if key in ALLOWED_OBJECT_CLASSES:
        return key
    return _SYNONYMS.get(key, "unknown")
