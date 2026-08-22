from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import require_admin
from app.database.models import (
    AuditLog,
    Credential,
    CredentialStatus,
    LedgerBlock,
    LedgerTransaction,
    Organization,
    User,
)
from app.database.session import get_db
from app.ledger.service import LedgerService
from app.schemas import StatsOut

router = APIRouter(tags=["stats", "admin"])


@router.get("/stats", response_model=StatsOut)
def network_stats(db: Annotated[Session, Depends(get_db)]) -> StatsOut:
    orgs = db.scalar(select(func.count()).select_from(Organization)) or 0
    issued = db.scalar(select(func.count()).select_from(Credential)) or 0
    active = (
        db.scalar(
            select(func.count()).select_from(Credential).where(Credential.status == CredentialStatus.ACTIVE)
        )
        or 0
    )
    blocks = db.scalar(select(func.count()).select_from(LedgerBlock)) or 0
    txs = db.scalar(select(func.count()).select_from(LedgerTransaction)) or 0
    verified = (
        db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == "credential_verified"))
        or 0
    )
    return StatsOut(
        organizations=orgs,
        credentials_issued=issued,
        credentials_verified=verified,
        blocks=blocks,
        transactions=txs,
        active_credentials=active,
    )


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/overview")
def admin_overview(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    stats = network_stats(db)
    chain = LedgerService(db).verify_chain()
    audit = AuditService(db).verify_chain()
    recent_orgs = list(
        db.scalars(select(Organization).order_by(Organization.created_at.desc()).limit(20)).all()
    )
    recent_audit = list(
        db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(50)).all()
    )
    return {
        "stats": stats.model_dump(),
        "chain": chain,
        "audit_chain": audit,
        "organizations": [
            {
                "id": str(o.id),
                "name": o.name,
                "status": o.status.value,
                "is_demo": o.is_demo,
                "did": o.did,
            }
            for o in recent_orgs
        ],
        "audit_events": [
            {
                "action": a.action,
                "actor_id": a.actor_id,
                "resource_id": a.resource_id,
                "created_at": a.created_at.isoformat(),
                "entry_hash": a.entry_hash[:16],
            }
            for a in recent_audit
        ],
        "note": "Admin cannot modify ledger history. Ledger is append-only.",
    }
