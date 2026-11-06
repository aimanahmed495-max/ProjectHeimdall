"""Per-class cooldown for vision threat-event posts."""

from __future__ import annotations

import time
from typing import Callable, Dict, Optional


class DetectionThrottle:
    """Allow at most one post per object class inside a cooldown window.

    Args:
        cooldown_seconds: Minimum gap between two posts of the same class.
        clock: Monotonic time source, replaced in tests.
    """

    def __init__(
        self,
        cooldown_seconds: float,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock or time.monotonic
        self._last_posted: Dict[str, float] = {}

    def allow(self, object_class: str) -> bool:
        """Return True when ``object_class`` may be posted now.

        Args:
            object_class: Detection class name (raw COCO label).

        Returns:
            ``True`` when no prior post exists for the class, or the
            cooldown has elapsed since the last allowed post.
        """

        now = self._clock()
        previous = self._last_posted.get(object_class)
        if previous is not None and (now - previous) < self._cooldown_seconds:
            return False
        self._last_posted[object_class] = now
        return True
