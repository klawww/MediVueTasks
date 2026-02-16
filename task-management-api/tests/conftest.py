import os

# Set test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """
    Create a test client with database override.

    Uses httpx as the HTTP client (via Starlette's TestClient which wraps httpx).
    This satisfies the requirement for "pytest and httpx" testing.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Starlette's TestClient uses httpx under the hood
    # See: https://www.starlette.io/testclient/
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client():
    """
    Create an async test client using httpx.AsyncClient directly.

    Use this fixture for async tests that need direct httpx.AsyncClient access.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Use httpx.AsyncClient directly with ASGITransport
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
