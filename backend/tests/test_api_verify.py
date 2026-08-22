"""Public verification API flow."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.credentials.service import CredentialService
from app.database.base import Base
from app.database import models  # noqa: F401
from app.database.models import (
    CredentialType,
    MembershipRole,
    Organization,
    OrganizationMember,
    OrgStatus,
    OrgType,
    User,
    UserRole,
)
from app.database.session import get_db
from app.identities.service import IdentityService, make_org_did, make_user_did
from app.ledger.service import LedgerService
from app.main import create_app
from app.security.passwords import hash_password


def test_public_verify_endpoint():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    LedgerService(db).ensure_genesis()
    db.add(
        CredentialType(code="UniversityDegree", category="education", display_name="Degree")
    )
    holder = User(
        email="h@t.ptn",
        password_hash=hash_password("x"),
        full_name="Hold Er",
        username="hold",
        did=make_user_did(),
        role=UserRole.INDIVIDUAL,
    )
    org_user = User(
        email="o@t.ptn",
        password_hash=hash_password("x"),
        full_name="Org",
        username="org",
        did=make_user_did(),
        role=UserRole.ORGANIZATION,
    )
    db.add_all([holder, org_user])
    db.flush()
    org = Organization(
        name="Uni",
        slug="uni",
        org_type=OrgType.UNIVERSITY,
        email="u@t.ptn",
        status=OrgStatus.VERIFIED,
        did=make_org_did(),
    )
    db.add(org)
    db.flush()
    IdentityService(db).create_for_organization(org)
    db.add(OrganizationMember(organization_id=org.id, user_id=org_user.id, role=MembershipRole.OWNER))
    cred = CredentialService(db).issue(
        organization=org,
        holder=holder,
        type_code="UniversityDegree",
        title="BS CS",
        credential_subject={"degree": "BS CS"},
    )
    db.commit()

    app = create_app()

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    client = TestClient(app)
    r = client.get(f"/api/verify/{cred.credential_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["overall"] == "VERIFIED"
    assert body["checks"]["signature_verified"] is True
