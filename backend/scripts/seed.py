from __future__ import annotations

"""Seed credential types, admin, and clearly labelled DEMO organizations/users."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.config import settings
from app.credentials.service import CredentialService
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
from app.identities.service import IdentityService, make_org_did, make_user_did, slugify
from app.ledger.service import LedgerService
from app.security.passwords import hash_password

CREDENTIAL_TYPES = [
    ("UniversityDegree", "education", "University Degree"),
    ("Degree", "education", "Degree"),
    ("Diploma", "education", "Diploma"),
    ("Certificate", "education", "Certificate"),
    ("Transcript", "education", "Transcript"),
    ("CourseCompletion", "education", "Course Completion"),
    ("Scholarship", "education", "Scholarship"),
    ("AcademicAward", "education", "Academic Award"),
    ("Employment", "professional", "Employment"),
    ("Internship", "professional", "Internship"),
    ("ProfessionalCertification", "professional", "Professional Certification"),
    ("Training", "professional", "Training"),
    ("License", "professional", "License"),
    ("Award", "achievement", "Award"),
    ("Competition", "achievement", "Competition"),
    ("Publication", "achievement", "Publication"),
    ("Project", "achievement", "Project"),
    ("SkillEvidence", "achievement", "Skill Evidence"),
]


def seed_credential_types(db: Session) -> None:
    for code, category, name in CREDENTIAL_TYPES:
        if not db.scalar(select(CredentialType).where(CredentialType.code == code)):
            db.add(CredentialType(code=code, category=category, display_name=name))
    db.flush()


def seed_admin(db: Session) -> User:
    admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
    if admin:
        return admin
    admin = User(
        email=settings.admin_email.lower(),
        password_hash=hash_password(settings.admin_password),
        full_name="PTN Admin",
        username="ptn-admin",
        did=make_user_did(),
        role=UserRole.ADMIN,
        is_demo=False,
    )
    db.add(admin)
    db.flush()
    return admin


def _ensure_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    username: str,
    role: UserRole = UserRole.INDIVIDUAL,
    headline: str | None = None,
) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user:
        return user
    user = User(
        email=email.lower(),
        password_hash=hash_password(settings.demo_password),
        full_name=full_name,
        username=username,
        did=make_user_did(),
        role=role,
        headline=headline,
        country="Pakistan",
        is_demo=True,
    )
    db.add(user)
    db.flush()
    AuditService(db).log(
        "user_registered",
        actor_id=user.did,
        actor_type="user",
        resource_type="user",
        resource_id=str(user.id),
        details={"demo": True},
    )
    return user


def _ensure_org(
    db: Session,
    *,
    name: str,
    org_type: OrgType,
    email: str,
    owner: User,
    description: str,
) -> Organization:
    org = db.scalar(select(Organization).where(Organization.name == name))
    if org:
        return org
    org = Organization(
        name=name,
        slug=slugify(name),
        org_type=org_type,
        country="Pakistan",
        website="https://ptn.local/demo",
        email=email,
        description=description,
        status=OrgStatus.VERIFIED,
        did=make_org_did(),
        is_demo=True,
        demo_label="DEMO — NOT AN ACTUAL VERIFIED INSTITUTION",
    )
    db.add(org)
    db.flush()
    IdentityService(db).create_for_organization(org, actor_id=owner.did)
    db.add(
        OrganizationMember(organization_id=org.id, user_id=owner.id, role=MembershipRole.OWNER)
    )
    AuditService(db).log(
        "organization_created",
        actor_id=owner.did,
        actor_type="user",
        resource_type="organization",
        resource_id=org.did,
        details={"demo": True, "name": name},
    )
    return org


def seed_demo(db: Session) -> dict:
    LedgerService(db).ensure_genesis()
    seed_credential_types(db)
    admin = seed_admin(db)

    uni_user = _ensure_user(
        db,
        email="university@demo.ptn",
        full_name="PTN Demo University Officer",
        username="demo-university",
        role=UserRole.ORGANIZATION,
    )
    emp_user = _ensure_user(
        db,
        email="employer@demo.ptn",
        full_name="PTN Demo Employer User",
        username="demo-employer",
        role=UserRole.ORGANIZATION,
    )
    train_user = _ensure_user(
        db,
        email="training@demo.ptn",
        full_name="PTN Demo Training Officer",
        username="demo-training",
        role=UserRole.ORGANIZATION,
    )
    student = _ensure_user(
        db,
        email="student@demo.ptn",
        full_name="Demo Student",
        username="demo-student",
        role=UserRole.INDIVIDUAL,
        headline="Software Engineer - Verifiable credentials advocate",
    )

    university = _ensure_org(
        db,
        name="PTN Demo University",
        org_type=OrgType.UNIVERSITY,
        email="university@demo.ptn",
        owner=uni_user,
        description="DEMO — NOT AN ACTUAL VERIFIED INSTITUTION. Reference issuer for PTN MVP.",
    )
    employer = _ensure_org(
        db,
        name="PTN Demo Employer",
        org_type=OrgType.EMPLOYER,
        email="employer@demo.ptn",
        owner=emp_user,
        description="DEMO — NOT AN ACTUAL VERIFIED INSTITUTION.",
    )
    training = _ensure_org(
        db,
        name="PTN Demo Training Institute",
        org_type=OrgType.TRAINING_PROVIDER,
        email="training@demo.ptn",
        owner=train_user,
        description="DEMO — NOT AN ACTUAL VERIFIED INSTITUTION.",
    )

    svc = CredentialService(db)
    from app.database.models import Credential

    existing = db.scalar(
        select(Credential).where(
            Credential.holder_id == student.id,
            Credential.title == "BS Computer Science",
        )
    )
    if not existing:
        svc.issue(
            organization=university,
            holder=student,
            type_code="UniversityDegree",
            title="BS Computer Science",
            credential_subject={
                "degree": "BS Computer Science",
                "graduation_year": 2026,
                "program": "Bachelor of Science",
            },
            is_demo=True,
            actor_id=university.did,
        )
        svc.issue(
            organization=employer,
            holder=student,
            type_code="Employment",
            title="Software Engineer",
            credential_subject={
                "role": "Software Engineer",
                "department": "Engineering",
                "employment_type": "Full-time",
            },
            is_demo=True,
            actor_id=employer.did,
        )
        svc.issue(
            organization=training,
            holder=student,
            type_code="ProfessionalCertification",
            title="Blockchain Fundamentals",
            credential_subject={
                "certification": "Blockchain Fundamentals",
                "level": "Foundation",
            },
            is_demo=True,
            actor_id=training.did,
        )
        # Skills evidence
        svc.issue(
            organization=training,
            holder=student,
            type_code="SkillEvidence",
            title="Python",
            credential_subject={"skill": "Python", "evidence": "Course + project assessment"},
            is_demo=True,
            actor_id=training.did,
        )
        svc.issue(
            organization=training,
            holder=student,
            type_code="SkillEvidence",
            title="Machine Learning",
            credential_subject={"skill": "Machine Learning", "evidence": "Capstone project"},
            is_demo=True,
            actor_id=training.did,
        )

    from app.cv.service import CVService

    CVService(db).publish(student, summary="Demo Student - credentials issued by PTN demo institutions.")

    db.commit()
    return {
        "admin_email": settings.admin_email,
        "demo_password": settings.demo_password,
        "accounts": {
            "student": "student@demo.ptn",
            "university": "university@demo.ptn",
            "employer": "employer@demo.ptn",
            "training": "training@demo.ptn",
        },
        "organizations": [university.name, employer.name, training.name],
        "student_username": student.username,
    }


def run_seed() -> None:
    from app.database.session import SessionLocal
    from app.database.base import Base
    from app.database import models  # noqa: F401
    from app.database.session import engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = seed_demo(db)
        print("Seed complete:")
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
