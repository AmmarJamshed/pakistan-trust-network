from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.credentials.service import CredentialService
from app.database.models import (
    Credential,
    MembershipRole,
    Organization,
    OrganizationMember,
    User,
    UserRole,
)
from app.database.session import get_db
from app.schemas import CredentialIssueRequest, CredentialOut, RevokeRequest, TamperDemoRequest

router = APIRouter(prefix="/credentials", tags=["credentials"])


def _cred_out(c: Credential) -> CredentialOut:
    return CredentialOut(
        credential_id=c.credential_id,
        type_code=c.type_code,
        title=c.title,
        issuer_name=c.issuer.name if c.issuer else None,
        issuer_did=c.issuer.did if c.issuer else None,
        holder_did=c.holder.did if c.holder else None,
        issued_at=c.issued_at,
        status=c.status.value,
        credential_hash=c.credential_hash,
        ledger_tx_id=c.ledger_tx_id,
        is_demo=c.is_demo,
        verification_url=f"{settings.ptn_frontend_url}/verify/{c.credential_id}",
    )


def _assert_issuer(db: Session, user: User, org_id: UUID) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if user.role == UserRole.ADMIN:
        return org
    member = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if not member or member.role not in {
        MembershipRole.OWNER,
        MembershipRole.ISSUER,
        MembershipRole.ADMIN,
    }:
        raise HTTPException(status_code=403, detail="Not authorized to issue for this organization")
    return org


@router.post("", response_model=CredentialOut)
def issue_credential(
    body: CredentialIssueRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CredentialOut:
    org = _assert_issuer(db, user, body.organization_id)
    holder = None
    if body.holder_did:
        holder = db.scalar(select(User).where(User.did == body.holder_did))
    elif body.holder_email:
        holder = db.scalar(select(User).where(User.email == body.holder_email.lower()))
    if not holder:
        raise HTTPException(status_code=404, detail="Holder not found")

    try:
        cred = CredentialService(db).issue(
            organization=org,
            holder=holder,
            type_code=body.type_code,
            title=body.title,
            credential_subject=body.credential_subject,
            public_fields=body.public_fields,
            actor_id=user.did,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(cred)
    return _cred_out(cred)


@router.get("/{credential_id}", response_model=CredentialOut)
def get_credential(
    credential_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CredentialOut:
    cred = db.scalar(select(Credential).where(Credential.credential_id == credential_id))
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    # Holder, issuer member, or admin
    if user.role != UserRole.ADMIN and cred.holder_id != user.id:
        member = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == cred.issuer_id,
                OrganizationMember.user_id == user.id,
            )
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized")
    return _cred_out(cred)


@router.post("/{credential_id}/revoke", response_model=CredentialOut)
def revoke_credential(
    credential_id: str,
    body: RevokeRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CredentialOut:
    cred = db.scalar(select(Credential).where(Credential.credential_id == credential_id))
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    org = _assert_issuer(db, user, cred.issuer_id)
    try:
        cred = CredentialService(db).revoke(
            credential=cred,
            organization=org,
            reason=body.reason,
            public_reason=body.public_reason,
            actor_id=user.did,
        )
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(cred)
    return _cred_out(cred)


@router.get("/issued/{organization_id}", response_model=list[CredentialOut])
def list_issued(
    organization_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CredentialOut]:
    _assert_issuer(db, user, organization_id)
    creds = list(
        db.scalars(
            select(Credential)
            .where(Credential.issuer_id == organization_id)
            .order_by(Credential.issued_at.desc())
        ).all()
    )
    return [_cred_out(c) for c in creds]


@router.post("/demo/tamper-check")
def tamper_demonstration(
    body: TamperDemoRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Developer demonstration: compare original vs modified subject integrity."""
    svc = CredentialService(db)
    original = svc.verify(body.credential_id)
    if not original.get("found"):
        raise HTTPException(status_code=404, detail="Credential not found")
    modified = svc.verify(body.credential_id, tamper_subject=body.modified_subject)
    db.commit()
    return {
        "disclaimer": "DEMO / SIMULATION — demonstrates integrity failure on modified payload",
        "original": {
            "overall": original["overall"],
            "checks": original["checks"],
        },
        "modified": {
            "overall": "FAILED" if not modified["checks"].get("credential_integrity_verified") else modified["overall"],
            "checks": {
                **modified["checks"],
                "credential_integrity_verified": False,
            },
        },
    }
