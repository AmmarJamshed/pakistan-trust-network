"""Credential issuance, signing, verification, revocation tests."""

from sqlalchemy import select

from app.credentials.service import CredentialService
from app.database.models import (
    CredentialStatus,
    CredentialType,
    MembershipRole,
    Organization,
    OrganizationMember,
    OrgStatus,
    OrgType,
    User,
    UserRole,
)
from app.identities.service import IdentityService, make_org_did, make_user_did
from app.security.passwords import hash_password


def _setup_issuer_holder(db):
    if not db.scalar(select(CredentialType).where(CredentialType.code == "UniversityDegree")):
        db.add(
            CredentialType(
                code="UniversityDegree", category="education", display_name="University Degree"
            )
        )
        db.flush()

    issuer_user = User(
        email="issuer@test.ptn",
        password_hash=hash_password("TestPass123!"),
        full_name="Issuer",
        username="issuer",
        did=make_user_did(),
        role=UserRole.ORGANIZATION,
    )
    holder = User(
        email="holder@test.ptn",
        password_hash=hash_password("TestPass123!"),
        full_name="Holder Person",
        username="holder",
        did=make_user_did(),
        role=UserRole.INDIVIDUAL,
    )
    db.add_all([issuer_user, holder])
    db.flush()

    org = Organization(
        name="Test University",
        slug="test-university",
        org_type=OrgType.UNIVERSITY,
        email="org@test.ptn",
        status=OrgStatus.VERIFIED,
        did=make_org_did(),
    )
    db.add(org)
    db.flush()
    IdentityService(db).create_for_organization(org)
    db.add(
        OrganizationMember(
            organization_id=org.id, user_id=issuer_user.id, role=MembershipRole.OWNER
        )
    )
    db.flush()
    return org, holder


def test_issue_sign_verify(db_session):
    org, holder = _setup_issuer_holder(db_session)
    svc = CredentialService(db_session)
    cred = svc.issue(
        organization=org,
        holder=holder,
        type_code="UniversityDegree",
        title="BS Computer Science",
        credential_subject={"degree": "BS Computer Science", "graduation_year": 2026},
    )
    assert cred.signature
    assert cred.ledger_tx_id
    assert len(cred.credential_hash) == 64

    result = svc.verify(cred.credential_id)
    assert result["overall"] == "VERIFIED"
    assert result["checks"]["signature_verified"] is True
    assert result["checks"]["ledger_proof_verified"] is True


def test_hash_mismatch_fails(db_session):
    org, holder = _setup_issuer_holder(db_session)
    svc = CredentialService(db_session)
    cred = svc.issue(
        organization=org,
        holder=holder,
        type_code="UniversityDegree",
        title="BS Computer Science",
        credential_subject={"degree": "BS"},
    )
    result = svc.verify(
        cred.credential_id,
        tamper_subject={"degree": "PhD FAKE"},
    )
    assert result["checks"]["credential_integrity_verified"] is False


def test_revocation(db_session):
    org, holder = _setup_issuer_holder(db_session)
    svc = CredentialService(db_session)
    cred = svc.issue(
        organization=org,
        holder=holder,
        type_code="UniversityDegree",
        title="BS Computer Science",
        credential_subject={"degree": "BS"},
    )
    svc.revoke(credential=cred, organization=org, reason="Issued in error")
    assert cred.status == CredentialStatus.REVOKED
    result = svc.verify(cred.credential_id)
    assert result["overall"] == "REVOKED"
