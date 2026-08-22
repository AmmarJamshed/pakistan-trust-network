from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.database.models import Credential, User, UserRole
from app.database.session import get_db

router = APIRouter(prefix="/wallet", tags=["wallet"])

CATEGORY_MAP = {
    "UniversityDegree": "education",
    "Degree": "education",
    "Diploma": "education",
    "Certificate": "education",
    "Transcript": "education",
    "CourseCompletion": "education",
    "Scholarship": "education",
    "AcademicAward": "education",
    "Employment": "professional",
    "Internship": "professional",
    "ProfessionalCertification": "professional",
    "Training": "professional",
    "License": "professional",
    "Award": "achievement",
    "Competition": "achievement",
    "Publication": "achievement",
    "Project": "achievement",
    "SkillEvidence": "skills",
}


@router.get("/me")
def my_wallet(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    creds = list(
        db.scalars(
            select(Credential)
            .where(Credential.holder_id == user.id)
            .order_by(Credential.issued_at.desc())
        ).all()
    )
    groups: dict[str, list] = {
        "education": [],
        "professional": [],
        "skills": [],
        "achievement": [],
    }
    for c in creds:
        cat = CATEGORY_MAP.get(c.type_code, "achievement")
        groups.setdefault(cat, []).append(
            {
                "credential_id": c.credential_id,
                "title": c.title,
                "type": c.type_code,
                "issuer": c.issuer.name,
                "issuer_did": c.issuer.did,
                "issued_at": c.issued_at.isoformat(),
                "status": c.status.value,
                "verified": c.status.value == "ACTIVE",
                "credential_hash": c.credential_hash,
                "ledger_tx_id": c.ledger_tx_id,
                "verification_url": f"{settings.ptn_frontend_url}/verify/{c.credential_id}",
                "is_demo": c.is_demo,
            }
        )
    return {
        "holder": {"full_name": user.full_name, "did": user.did, "username": user.username},
        "categories": groups,
        "count": len(creds),
    }


@router.get("/users/{user_id}")
def user_wallet(
    user_id: UUID,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if current.id != user_id and current.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    # Reuse logic via temporary swap
    return my_wallet(target, db)
