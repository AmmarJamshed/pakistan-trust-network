"""Authentication API tests."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database import models  # noqa: F401
from app.database.session import get_db
from app.ledger.service import LedgerService
from app.main import create_app


def _client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    LedgerService(db).ensure_genesis()
    db.commit()

    app = create_app()

    def override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override
    return TestClient(app), db


def test_register_login():
    client, _ = _client()
    r = client.post(
        "/api/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePass1!",
            "full_name": "Alice Example",
            "username": "alice",
        },
    )
    assert r.status_code == 200
    assert "access_token" in r.json()

    r2 = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "SecurePass1!"},
    )
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


def test_unauthorized_me():
    client, _ = _client()
    assert client.get("/api/auth/me").status_code == 401
