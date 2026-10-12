"""Isolate tests before importing the application or loading developer .env."""
import os
import tempfile
from pathlib import Path

import pytest

_test_root = tempfile.TemporaryDirectory(prefix="recruitment-tests-", ignore_cleanup_errors=True)
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(_test_root.name) / "audit.db").as_posix()
os.environ["SECRET_KEY"] = "test-only-secret-key-with-sufficient-length"
os.environ["GEMINI_API_KEY"] = ""
os.environ["APP_ENV"] = "development"
os.environ["SEED_DEFAULT_JOBS"] = "false"
os.environ["UPLOAD_DIR"] = str(Path(_test_root.name) / "uploads")


@pytest.fixture(scope="module", autouse=True)
def isolated_database():
    import app.models
    from app.core.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def isolated_dependencies(monkeypatch):
    from app.main import app
    from app.core.rate_limit import rate_limiter
    # Workflow tests opt out via dependency overrides; the limiter itself stays
    # active and has dedicated tests with real request clients.
    saved = dict(app.dependency_overrides)
    from app import main
    routes = [route for module in vars(main).values() if hasattr(module, "router") for route in module.router.routes]
    rate_limiter._events.clear()
    rate_limiter._expires.clear()
    for route in routes:
        for dependency in getattr(getattr(route, "dependant", None), "dependencies", []):
            if getattr(dependency.call, "__module__", "") == "app.core.rate_limit":
                app.dependency_overrides[dependency.call] = lambda: None
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setattr("socket.getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("8.8.8.8", 443))])
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


def pytest_sessionfinish(session, exitstatus):
    from app.core.database import engine
    engine.dispose()
    _test_root.cleanup()
