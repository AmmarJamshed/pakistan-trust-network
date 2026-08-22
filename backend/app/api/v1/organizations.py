from __future__ import annotations

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import get_current_user, require_admin
from app.database.models import (
    Identity,
    MembershipRole,
    Organization,
    OrganizationMember,
    OrgStatus,
    User,
    UserRole,
)
from app.database.session import get_db
from app.identities.service import IdentityService, make_org_did, slugify
from app.schemas import IdentityOut, OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _org_out(org: Organization) -> OrganizationOut:
    return OrganizationOut(
        id=org.id,
        name=org.name,
        slug=org.slug,
        org_type=org.org_type,
        country=org.country,
        website=org.website,
        email=org.email,
        description=org.description,
        status=org.status,
        did=org.did,
        is_demo=org.is_demo,
        demo_label=org.demo_label,
        has_identity=org.identity is not None,
    )


@router.post("", response_model=OrganizationOut)
def create_organization(
    body: OrganizationCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationOut:
    slug = slugify(body.name)
    if db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{slug}-{secrets.token_hex(3)}"

    org = Organization(
        name=body.name,
        slug=slug,
        org_type=body.org_type,
        country=body.country,
        website=body.website,
        email=body.email.lower(),
        description=body.description,
        status=OrgStatus.PENDING_VERIFICATION,
        did=make_org_did(),
        is_demo=False,
    )
    db.add(org)
    db.flush()

    # Create identity immediately
    IdentityService(db).create_for_organization(org, actor_id=user.did)

    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=MembershipRole.OWNER,
        )
    )
    if user.role == UserRole.INDIVIDUAL:
        user.role = UserRole.ORGANIZATION

    AuditService(db).log(
        "organization_created",
        actor_id=user.did,
        actor_type="user",
        resource_type="organization",
        resource_id=org.did,
        details={"name": org.name, "type": org.org_type.value},
    )
    db.commit()
    db.refresh(org)
    return _org_out(org)


@router.get("", response_model=list[OrganizationOut])
def list_organizations(
    db: Annotated[Session, Depends(get_db)],
    status_filter: OrgStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OrganizationOut]:
    q = select(Organization).order_by(Organization.created_at.desc()).offset(offset).limit(min(limit, 100))
    if status_filter:
        q = q.where(Organization.status == status_filter)
    orgs = list(db.scalars(q).all())
    return [_org_out(o) for o in orgs]


@router.get("/mine", response_model=list[OrganizationOut])
def my_organizations(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OrganizationOut]:
    members = list(
        db.scalars(select(OrganizationMember).where(OrganizationMember.user_id == user.id)).all()
    )
    return [_org_out(m.organization) for m in members]


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: UUID, db: Annotated[Session, Depends(get_db)]) -> OrganizationOut:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _org_out(org)


@router.post("/{org_id}/identity", response_model=IdentityOut)
def create_identity(
    org_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> IdentityOut:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    member = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if not member and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not a member")
    identity = IdentityService(db).create_for_organization(org, actor_id=user.did)
    db.commit()
    return IdentityOut(
        issuer_id=identity.issuer_id,
        public_key=identity.public_key,
        key_algorithm=identity.key_algorithm,
        status=identity.status,
        created_at=identity.created_at,
    )


@router.get("/{org_id}/identity", response_model=IdentityOut)
def get_identity(org_id: UUID, db: Annotated[Session, Depends(get_db)]) -> IdentityOut:
    identity = db.scalar(select(Identity).where(Identity.organization_id == org_id))
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return IdentityOut(
        issuer_id=identity.issuer_id,
        public_key=identity.public_key,
        key_algorithm=identity.key_algorithm,
        status=identity.status,
        created_at=identity.created_at,
    )


@router.post("/{org_id}/status", response_model=OrganizationOut)
def set_status(
    org_id: UUID,
    new_status: OrgStatus,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationOut:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.status = new_status
    AuditService(db).log(
        "organization_status_changed",
        actor_id=admin.did,
        actor_type="admin",
        resource_type="organization",
        resource_id=org.did,
        details={"status": new_status.value},
    )
    db.commit()
    return _org_out(org)
