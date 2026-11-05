"""Run the real Heimdall API as a subprocess for OSINT pipeline E2E tests."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "ai-brain"))

# Same values as scripts/check and the CI backend job. Variables already set in
# the environment win, so a different local Postgres port can be used.
TEST_ENV = {
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "JWT_SECRET_KEY": "heimdall-ci-test-key-not-for-production-use-only",
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_MINUTES": "30",
}
OSINT_USERNAME = "osint.e2e.pipeline"
OSINT_PASSWORD = "E2ePipelineSyntheticPassword1!"
CAMERA_ID = 1
DORMANT = {"mode": "Dormant", "fps": 5, "resolution": "720p"}
STARTUP_SECONDS = 30
STOP_SECONDS = 10
REQUEST_TIMEOUT = 5


class ApiSession:
    """Authenticated HTTP access to the API for test setup and assertions."""

    def __init__(self, base_url: str, token: str) -> None:
        """Attach a bearer token to every request.

        Args:
            base_url: API origin, for example ``http://127.0.0.1:8123``.
            token: Access token from ``POST /auth/login``.
        """

        self._base_url = base_url
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, path: str) -> requests.Response:
        """Send ``GET path``."""

        return self._session.get(self._base_url + path, timeout=REQUEST_TIMEOUT)

    def post(self, path: str, body: Dict[str, Any]) -> requests.Response:
        """Send ``POST path`` with a JSON body."""

        return self._session.post(
            self._base_url + path, json=body, timeout=REQUEST_TIMEOUT
        )

    def put(self, path: str, body: Dict[str, Any]) -> requests.Response:
        """Send ``PUT path`` with a JSON body."""

        return self._session.put(
            self._base_url + path, json=body, timeout=REQUEST_TIMEOUT
        )


def _backend_python() -> str:
    """Return the backend venv interpreter, or this one when it is absent."""

    venv_python = ROOT / ".venv" / "backend" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def _api_env() -> Dict[str, str]:
    """Build the API environment so it never falls back to the root ``.env``."""

    env = dict(os.environ)
    for name, value in TEST_ENV.items():
        env.setdefault(name, value)
    env["ENABLE_USER_REGISTRATION"] = "true"
    env["PYTHONPATH"] = str(ROOT)
    return env


def _free_port() -> int:
    """Ask the OS for an unused localhost port."""

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_migrations(python: str, env: Dict[str, str]) -> None:
    """Bring the test database to ``alembic upgrade head``."""

    result = subprocess.run(
        [python, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT / "backend",
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.fail(f"alembic upgrade head failed:\n{result.stderr}")


def _wait_until_healthy(
    base_url: str,
    process: subprocess.Popen,
    log_path: Path,
) -> None:
    """Poll ``/health`` until it answers 200, or fail with the API log."""

    deadline = time.monotonic() + STARTUP_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(
                f"API exited with code {process.returncode}:\n{log_path.read_text()}"
            )
        try:
            if requests.get(f"{base_url}/health", timeout=1).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.2)
    pytest.fail(
        f"API was not healthy after {STARTUP_SECONDS}s:\n{log_path.read_text()}"
    )


def _stop(process: subprocess.Popen) -> None:
    """Terminate the API, killing it if it does not exit in time."""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=STOP_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="session")
def api_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start uvicorn on a free localhost port and always stop it afterwards."""

    python = _backend_python()
    env = _api_env()
    _run_migrations(python, env)
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("api") / "uvicorn.log"
    command = [
        python,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    with log_path.open("w") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            _wait_until_healthy(base_url, process, log_path)
            yield base_url
        finally:
            _stop(process)


@pytest.fixture(scope="session")
def osint_user(api_url: str) -> Dict[str, str]:
    """Register the OSINT service user; a user left by an earlier run is reused."""

    credentials = {"username": OSINT_USERNAME, "password": OSINT_PASSWORD}
    response = requests.post(
        f"{api_url}/auth/register", json=credentials, timeout=REQUEST_TIMEOUT
    )
    assert response.status_code in (201, 409), response.text
    return credentials


@pytest.fixture(scope="session")
def api(api_url: str, osint_user: Dict[str, str]) -> ApiSession:
    """Return an authenticated session for setup and verification calls."""

    response = requests.post(
        f"{api_url}/auth/login", json=osint_user, timeout=REQUEST_TIMEOUT
    )
    assert response.status_code == 200, response.text
    return ApiSession(api_url, response.json()["access_token"])


@pytest.fixture
def osint_client(api_url: str, osint_user: Dict[str, str]):
    """Return a logged-in ``HeimdallAPIClient``, as the OSINT module uses it."""

    from osint_client import HeimdallAPIClient

    client = HeimdallAPIClient(
        base_url=api_url,
        username=osint_user["username"],
        password=osint_user["password"],
    )
    client.authenticate()
    return client


@pytest.fixture
def dormant_camera(api: ApiSession) -> int:
    """Register camera 1, or reset it, so each test starts Dormant."""

    response = api.post("/camera-states", {"camera_id": CAMERA_ID, **DORMANT})
    if response.status_code == 409:
        response = api.put(f"/camera-states/{CAMERA_ID}", DORMANT)
    assert response.status_code in (200, 201), response.text
    assert response.json()["mode"] == "Dormant"
    return CAMERA_ID
