import os

os.environ["DATABASE_URL"] = "sqlite:///./fitstack-test.db"

import pytest
from fastapi.testclient import TestClient

from database.database import Base, engine
from main import app


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)
