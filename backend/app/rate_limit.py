"""In-memory login failure rate limiting."""

from __future__ import annotations

import collections
import logging
import os
import threading
import time
from typing import Callable, Deque, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

UserKey = Tuple[str, str]
FailureKey = Union[UserKey, str]
MAX_TRACKED_KEYS = 10_000


class LoginRateLimiter:
    """Track failed login attempts and decide when to block further tries."""

    def __init__(
        self,
        max_failures: int = 5,
        ip_max_failures: int = 50,
        window_seconds: int = 900,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a limiter.

        Args:
            max_failures: Failures per (IP, username) inside the window before
                429. ``0`` disables the limiter.
            ip_max_failures: Failures per IP across all usernames inside the
                window.
            window_seconds: Sliding window length in seconds.
            clock: Monotonic clock. Injectable so tests can skip ahead.
        """

        self._max_failures = max_failures
        self._ip_max_failures = ip_max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._user_failures: Dict[UserKey, Deque[float]] = {}
        self._ip_failures: Dict[str, Deque[float]] = {}
        self._warned: set[tuple[str, FailureKey]] = set()

    @classmethod
    def from_env(cls) -> LoginRateLimiter:
        """Build a limiter from ``LOGIN_*`` environment variables.

        Returns:
            A ``LoginRateLimiter`` using the configured defaults when unset.
        """

        return cls(
            max_failures=int(os.getenv("LOGIN_MAX_FAILURES", "5")),
            ip_max_failures=int(os.getenv("LOGIN_IP_MAX_FAILURES", "50")),
            window_seconds=int(
                os.getenv("LOGIN_FAILURE_WINDOW_SECONDS", "900")
            ),
        )

    def retry_after(self, ip: str, username: str) -> Optional[int]:
        """Return seconds until a block lifts, or ``None`` if not blocked.

        Args:
            ip: Client IP address.
            username: Lowercased username.

        Returns:
            Seconds until the oldest relevant failure expires if either the
            per-user or per-IP count is at its limit. Otherwise ``None``.
        """

        if self._max_failures == 0:
            return None

        now = self._clock()
        with self._lock:
            user_key = (ip, username)
            user_deque = self._store_pruned(
                self._user_failures,
                user_key,
                now,
            )
            ip_deque = self._store_pruned(self._ip_failures, ip, now)

            user_blocked = (
                user_deque is not None
                and len(user_deque) >= self._max_failures
            )
            ip_blocked = (
                ip_deque is not None
                and len(ip_deque) >= self._ip_max_failures
            )
            if not user_blocked and not ip_blocked:
                return None

            candidates: list[float] = []
            if user_blocked and user_deque is not None:
                candidates.append(user_deque[0])
            if ip_blocked and ip_deque is not None:
                candidates.append(ip_deque[0])
            oldest = min(candidates)
            seconds = int(self._window_seconds - (now - oldest))
            return max(1, seconds)

    def record_failure(self, ip: str, username: str) -> None:
        """Append a failure timestamp for the user and IP keys.

        Args:
            ip: Client IP address.
            username: Lowercased username.

        Returns:
            None.
        """

        if self._max_failures == 0:
            return

        now = self._clock()
        with self._lock:
            user_key = (ip, username)
            user_deque = self._append_failure(
                self._user_failures,
                user_key,
                now,
            )
            ip_deque = self._append_failure(self._ip_failures, ip, now)
            self._evict_if_needed()
            self._warn_if_limit(user_deque, ip_deque, ip, username)

    def record_success(self, ip: str, username: str) -> None:
        """Clear the (IP, username) failure deque after a successful login.

        The IP deque is left alone so one valid login cannot reset a spray
        across other usernames.

        Args:
            ip: Client IP address.
            username: Lowercased username.

        Returns:
            None.
        """

        with self._lock:
            user_key = (ip, username)
            self._user_failures.pop(user_key, None)
            self._warned.discard(("user", user_key))

    def reset(self) -> None:
        """Clear every recorded failure. Used by tests.

        Returns:
            None.
        """

        with self._lock:
            self._user_failures.clear()
            self._ip_failures.clear()
            self._warned.clear()

    def _prune(
        self,
        failures: Optional[Deque[float]],
        now: float,
    ) -> Optional[Deque[float]]:
        """Drop timestamps older than the window.

        Args:
            failures: Failure timestamps for one key, or ``None``.
            now: Current monotonic time.

        Returns:
            The pruned deque, or ``None`` when empty or missing.
        """

        if failures is None:
            return None

        cutoff = now - self._window_seconds
        while failures and failures[0] < cutoff:
            failures.popleft()
        if not failures:
            return None
        return failures

    def _store_pruned(
        self,
        store: Dict[FailureKey, Deque[float]],
        key: FailureKey,
        now: float,
    ) -> Optional[Deque[float]]:
        """Prune one key and drop it from ``store`` when empty.

        Args:
            store: Failure map to update.
            key: User or IP key.
            now: Current monotonic time.

        Returns:
            The pruned deque, or ``None`` when the key has no recent failures.
        """

        pruned = self._prune(store.get(key), now)
        if pruned is None:
            store.pop(key, None)
        else:
            store[key] = pruned
        return pruned

    def _append_failure(
        self,
        store: Dict[FailureKey, Deque[float]],
        key: FailureKey,
        now: float,
    ) -> Deque[float]:
        """Prune, append ``now``, and store the deque.

        Args:
            store: Failure map to update.
            key: User or IP key.
            now: Failure timestamp.

        Returns:
            The updated deque for ``key``.
        """

        failures = self._prune(store.get(key), now) or collections.deque()
        failures.append(now)
        store[key] = failures
        return failures

    def _warn_if_limit(
        self,
        user_deque: Deque[float],
        ip_deque: Deque[float],
        ip: str,
        username: str,
    ) -> None:
        """Emit one WARNING the first time a key reaches its limit.

        Args:
            user_deque: Failures for (IP, username).
            ip_deque: Failures for the IP.
            ip: Client IP address.
            username: Lowercased username.

        Returns:
            None.
        """

        user_key = (ip, username)
        if len(user_deque) >= self._max_failures:
            warn_key: tuple[str, FailureKey] = ("user", user_key)
            if warn_key not in self._warned:
                self._warned.add(warn_key)
                logger.warning(
                    "Login rate limit reached ip=%s username=%s limit=user",
                    ip,
                    username,
                )
        if len(ip_deque) >= self._ip_max_failures:
            warn_key = ("ip", ip)
            if warn_key not in self._warned:
                self._warned.add(warn_key)
                logger.warning(
                    "Login rate limit reached ip=%s username=%s limit=ip",
                    ip,
                    username,
                )

    def _evict_if_needed(self) -> None:
        """Drop the coldest key when total tracked keys exceed the cap.

        Returns:
            None.
        """

        while (
            len(self._user_failures) + len(self._ip_failures)
            > MAX_TRACKED_KEYS
        ):
            coldest_user = self._coldest_key(self._user_failures)
            coldest_ip = self._coldest_key(self._ip_failures)
            if coldest_user is None and coldest_ip is None:
                return
            if coldest_ip is None or (
                coldest_user is not None
                and coldest_user[1] <= coldest_ip[1]
            ):
                assert coldest_user is not None
                self._user_failures.pop(coldest_user[0], None)
                self._warned.discard(("user", coldest_user[0]))
            else:
                self._ip_failures.pop(coldest_ip[0], None)
                self._warned.discard(("ip", coldest_ip[0]))

    @staticmethod
    def _coldest_key(
        store: Dict[FailureKey, Deque[float]],
    ) -> Optional[Tuple[FailureKey, float]]:
        """Find the key whose newest failure is oldest.

        Args:
            store: Failure map to scan.

        Returns:
            ``(key, newest_timestamp)`` for the coldest entry, or ``None``.
        """

        coldest: Optional[Tuple[FailureKey, float]] = None
        for key, failures in store.items():
            newest = failures[-1]
            if coldest is None or newest < coldest[1]:
                coldest = (key, newest)
        return coldest


login_rate_limiter = LoginRateLimiter.from_env()
