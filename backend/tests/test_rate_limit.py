"""Unit and route tests for login rate limiting."""

import pytest

from backend.app.rate_limit import MAX_TRACKED_KEYS, LoginRateLimiter


class FakeClock:
    """Monotonic clock that tests can advance without sleeping."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> LoginRateLimiter:
    return LoginRateLimiter(
        max_failures=3,
        ip_max_failures=5,
        window_seconds=100,
        clock=clock,
    )


def test_retry_after_none_below_max_failures(limiter: LoginRateLimiter):
    limiter.record_failure("10.0.0.1", "alice")
    limiter.record_failure("10.0.0.1", "alice")

    assert limiter.retry_after("10.0.0.1", "alice") is None


def test_user_limit_blocks_one_key_not_other_ip(
    limiter: LoginRateLimiter,
):
    for _ in range(3):
        limiter.record_failure("10.0.0.1", "alice")

    retry = limiter.retry_after("10.0.0.1", "alice")
    assert retry is not None
    assert retry > 0
    assert limiter.retry_after("10.0.0.2", "alice") is None


def test_block_lifts_after_window(
    limiter: LoginRateLimiter,
    clock: FakeClock,
):
    for _ in range(3):
        limiter.record_failure("10.0.0.1", "alice")

    assert limiter.retry_after("10.0.0.1", "alice") is not None

    clock.advance(101)
    assert limiter.retry_after("10.0.0.1", "alice") is None


def test_record_success_clears_user_not_ip(limiter: LoginRateLimiter):
    for _ in range(3):
        limiter.record_failure("10.0.0.1", "alice")
    assert limiter.retry_after("10.0.0.1", "alice") is not None

    limiter.record_success("10.0.0.1", "alice")
    assert limiter.retry_after("10.0.0.1", "alice") is None

    # Alice's three failures remain on the IP deque; two more trip the IP cap.
    limiter.record_failure("10.0.0.1", "bob")
    limiter.record_failure("10.0.0.1", "carol")
    assert limiter.retry_after("10.0.0.1", "dave") is not None
    assert limiter.retry_after("10.0.0.1", "alice") is not None


def test_ip_cap_trips_across_usernames(limiter: LoginRateLimiter):
    for index in range(5):
        limiter.record_failure("10.0.0.1", f"user{index}")

    assert limiter.retry_after("10.0.0.1", "fresh") is not None
    assert limiter.retry_after("10.0.0.2", "fresh") is None


def test_max_failures_zero_never_blocks(clock: FakeClock):
    limiter = LoginRateLimiter(
        max_failures=0,
        ip_max_failures=1,
        window_seconds=100,
        clock=clock,
    )
    for _ in range(20):
        limiter.record_failure("10.0.0.1", "alice")

    assert limiter.retry_after("10.0.0.1", "alice") is None


def test_eviction_keeps_key_count_at_cap(clock: FakeClock):
    limiter = LoginRateLimiter(
        max_failures=5,
        ip_max_failures=50,
        window_seconds=10_000,
        clock=clock,
    )
    for index in range(MAX_TRACKED_KEYS + 25):
        clock.advance(1)
        limiter.record_failure("10.0.0.1", f"user{index}")

    with limiter._lock:
        total = len(limiter._user_failures) + len(limiter._ip_failures)

    assert total <= MAX_TRACKED_KEYS


VALID_USER = {
    "username": "rate.limit.operator",
    "password": "SecurePassword123!",
}
WRONG_PASSWORD = "IncorrectPassword123!"


@pytest.fixture
def tight_login_limits(monkeypatch):
    """Swap the module limiter for small limits used by route tests."""

    clock = FakeClock()
    limiter = LoginRateLimiter(
        max_failures=3,
        ip_max_failures=50,
        window_seconds=900,
        clock=clock,
    )
    monkeypatch.setattr(
        "backend.app.auth.login_rate_limiter",
        limiter,
    )
    monkeypatch.setattr(
        "backend.app.rate_limit.login_rate_limiter",
        limiter,
    )
    return limiter


def _login(client, username: str, password: str):
    return client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )


def test_route_over_limit_returns_429_even_with_correct_password(
    unauthenticated_client,
    tight_login_limits,
):
    unauthenticated_client.post("/auth/register", json=VALID_USER)

    for _ in range(3):
        response = _login(
            unauthenticated_client,
            VALID_USER["username"],
            WRONG_PASSWORD,
        )
        assert response.status_code == 401

    blocked = _login(
        unauthenticated_client,
        VALID_USER["username"],
        VALID_USER["password"],
    )
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == (
        "Too many failed login attempts. Try again later."
    )
    assert blocked.headers["retry-after"].isdigit()


def test_route_unknown_username_blocked_same_body(
    unauthenticated_client,
    tight_login_limits,
):
    for _ in range(3):
        response = _login(
            unauthenticated_client,
            "missing.operator",
            WRONG_PASSWORD,
        )
        assert response.status_code == 401

    blocked = _login(
        unauthenticated_client,
        "missing.operator",
        WRONG_PASSWORD,
    )
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == (
        "Too many failed login attempts. Try again later."
    )
    assert blocked.headers["retry-after"].isdigit()


def test_route_success_resets_per_user_count(
    unauthenticated_client,
    tight_login_limits,
):
    unauthenticated_client.post("/auth/register", json=VALID_USER)

    for _ in range(2):
        response = _login(
            unauthenticated_client,
            VALID_USER["username"],
            WRONG_PASSWORD,
        )
        assert response.status_code == 401

    success = _login(
        unauthenticated_client,
        VALID_USER["username"],
        VALID_USER["password"],
    )
    assert success.status_code == 200

    for _ in range(3):
        response = _login(
            unauthenticated_client,
            VALID_USER["username"],
            WRONG_PASSWORD,
        )
        assert response.status_code == 401

    blocked = _login(
        unauthenticated_client,
        VALID_USER["username"],
        WRONG_PASSWORD,
    )
    assert blocked.status_code == 429


def test_route_separate_usernames_do_not_share_counter(
    unauthenticated_client,
    tight_login_limits,
):
    other = {
        "username": "rate.limit.other",
        "password": "SecurePassword123!",
    }
    unauthenticated_client.post("/auth/register", json=VALID_USER)
    unauthenticated_client.post("/auth/register", json=other)

    for _ in range(3):
        response = _login(
            unauthenticated_client,
            VALID_USER["username"],
            WRONG_PASSWORD,
        )
        assert response.status_code == 401

    other_login = _login(
        unauthenticated_client,
        other["username"],
        other["password"],
    )
    assert other_login.status_code == 200
