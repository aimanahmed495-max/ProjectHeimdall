"""Pure corroboration tests. No network and no LLM."""

from datetime import datetime, timedelta, timezone

from corroboration import CorroborationTracker

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


def make_tracker():
    """Return a tracker with the default five-minute window."""

    return CorroborationTracker(window_seconds=300)


def test_one_source_stays_pending():
    """A single report does not corroborate."""

    assert make_tracker().observe(1, "person", 10, NOW) is None


def test_two_distinct_sources_corroborate():
    """Two source ids reporting the same category inside the window agree."""

    tracker = make_tracker()

    assert tracker.observe(1, "Person", 10, NOW) is None
    result = tracker.observe(2, "person", 20, NOW + timedelta(seconds=30))

    assert result is not None
    assert result.category == "person"
    assert result.source_ids == (1, 2)
    assert result.event_ids == (10, 20)


def test_same_source_twice_does_not_corroborate():
    """Repeated reports from one source never count as a second source."""

    tracker = make_tracker()

    assert tracker.observe(1, "person", 10, NOW) is None
    assert tracker.observe(1, "person", 11, NOW + timedelta(seconds=5)) is None


def test_reports_outside_the_window_do_not_corroborate():
    """A later source does not revive a report older than the window."""

    tracker = make_tracker()

    assert tracker.observe(1, "person", 10, NOW) is None
    later = NOW + timedelta(seconds=301)
    assert tracker.observe(2, "person", 20, later) is None


def test_report_on_the_window_edge_still_counts():
    """A report exactly ``window_seconds`` later is still inside the window."""

    tracker = make_tracker()
    tracker.observe(1, "person", 10, NOW)

    result = tracker.observe(2, "person", 20, NOW + timedelta(seconds=300))

    assert result is not None
    assert result.source_ids == (1, 2)


def test_corroboration_fires_only_once():
    """A third source does not start another corroboration for that category."""

    tracker = make_tracker()
    tracker.observe(1, "person", 10, NOW)
    first = tracker.observe(2, "person", 20, NOW + timedelta(seconds=10))
    second = tracker.observe(3, "person", 30, NOW + timedelta(seconds=20))

    assert first is not None
    assert second is None


def test_different_categories_do_not_corroborate():
    """Agreement is per classified category, not across categories."""

    tracker = make_tracker()

    assert tracker.observe(1, "person", 10, NOW) is None
    assert tracker.observe(2, "vehicle", 20, NOW + timedelta(seconds=5)) is None
