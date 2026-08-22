from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Credential,
    CredentialStatus,
    CredentialType,
    Identity,
    LedgerBlock,
    Organization,
    OrgStatus,
    OrgType,
    Revocation,
    User,
    UserRole,
)
from app.identities.service import slugify
from app.ledger.service import LedgerService, _iso
from app.network.constants import NETWORK_REPLICA_SENTINEL
from app.security.crypto import encrypt_private_key
from app.security.passwords import hash_password


def _safe_name(value: str) -> str:
    return value.replace(":", "_").replace("/", "_")


def export_snapshot(db: Session) -> dict[str, Any]:
    ledger = LedgerService(db)
    ledger.ensure_genesis()
    blocks = list(db.scalars(select(LedgerBlock).order_by(LedgerBlock.index.asc())).all())
    orgs = list(db.scalars(select(Organization)).all())
    creds = list(db.scalars(select(Credential)).all())
    return {
        "format": "ptn-network-v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "note": "Public proofs only. No private keys, passwords, emails, or private credential subjects.",
        "blocks": [ledger.export_block(b) for b in blocks],
        "identities": [_export_identity(o) for o in orgs if o.identity],
        "credentials": [_export_credential(c) for c in creds],
    }


def _export_identity(org: Organization) -> dict[str, Any]:
    ident = org.identity
    assert ident is not None
    return {
        "did": org.did,
        "name": org.name,
        "org_type": org.org_type.value,
        "country": org.country,
        "status": org.status.value,
        "is_demo": org.is_demo,
        "demo_label": org.demo_label,
        "issuer_id": ident.issuer_id,
        "public_key": ident.public_key,
        "key_algorithm": ident.key_algorithm,
        "identity_status": ident.status,
    }


def _export_credential(cred: Credential) -> dict[str, Any]:
    holder = cred.holder
    parts = holder.full_name.split()
    display = parts[0]
    if len(parts) > 1:
        display = f"{parts[0]} {parts[-1][0]}."
    public_subject = {
        k: v
        for k, v in (cred.credential_subject or {}).items()
        if k in (cred.public_fields or []) or k in {"degree", "role", "program", "skill", "certification"}
    }
    revocation = None
    if cred.revocation and cred.revocation.public_reason:
        revocation = {
            "revoked_at": _iso(cred.revocation.revoked_at),
            "reason": cred.revocation.reason,
        }
    return {
        "credential_id": cred.credential_id,
        "type_code": cred.type_code,
        "title": cred.title,
        "issuer_did": cred.issuer.did,
        "holder_did": holder.did,
        "holder_display": display,
        "issued_at": _iso(cred.issued_at),
        "credential_hash": cred.credential_hash,
        "signature": cred.signature,
        "proof_type": cred.proof_type,
        "status": cred.status.value,
        "public_fields": cred.public_fields or [],
        "public_subject": public_subject,
        "ledger_tx_id": cred.ledger_tx_id,
        "metadata_hash": cred.metadata_hash,
        "is_demo": cred.is_demo,
        "revocation": revocation,
    }


def import_snapshot(db: Session, snapshot: dict[str, Any]) -> dict[str, Any]:
    ledger = LedgerService(db)
    ledger.ensure_genesis()
    stats = {"identities": 0, "credentials": 0, "blocks": 0, "forks_resolved": 0}

    for ident in snapshot.get("identities") or []:
        if _upsert_identity(db, ident):
            stats["identities"] += 1

    remote_blocks = sorted(snapshot.get("blocks") or [], key=lambda b: int(b["index"]))
    for payload in remote_blocks:
        idx = int(payload["index"])
        local = ledger.get_block(idx)
        if local and local.block_hash != payload["block_hash"]:
            if idx == 0:
                # Adopt shared genesis when this node has no real history yet.
                later = ledger.get_latest_block()
                if later and later.index == 0:
                    db.delete(local)
                    db.flush()
                    ledger.import_block(payload)
                    stats["forks_resolved"] += 1
                    stats["blocks"] += 1
                continue
            ledger.delete_blocks_from(idx)
            stats["forks_resolved"] += 1
            local = None
        if not local:
            ledger.import_block(payload)
            stats["blocks"] += 1

    dangling = ledger.get_unattached_transactions()
    if dangling:
        ledger.mine_pending_block(dangling)

    for cred in snapshot.get("credentials") or []:
        if _upsert_credential(db, cred):
            stats["credentials"] += 1

    db.flush()
    return stats


def _upsert_identity(db: Session, payload: dict[str, Any]) -> bool:
    did = payload["did"]
    org = db.scalar(select(Organization).where(Organization.did == did))
    created = False
    if not org:
        slug = slugify(payload.get("name") or did)
        if db.scalar(select(Organization).where(Organization.slug == slug)):
            slug = slugify(did)
        org = Organization(
            name=payload.get("name") or did,
            slug=slug,
            org_type=OrgType(payload.get("org_type") or "OTHER"),
            country=payload.get("country") or "Pakistan",
            email=f"network-{_safe_name(did)[:40]}@ptn.invalid",
            description="Replicated from the PTN Git network. Public identity only.",
            status=OrgStatus(payload.get("status") or "PENDING_VERIFICATION"),
            did=did,
            is_demo=bool(payload.get("is_demo")),
            demo_label=payload.get("demo_label"),
        )
        db.add(org)
        db.flush()
        created = True
    ident = org.identity or db.scalar(select(Identity).where(Identity.organization_id == org.id))
    if not ident:
        ident = Identity(
            organization_id=org.id,
            issuer_id=payload.get("issuer_id") or did,
            public_key=payload["public_key"],
            encrypted_private_key=encrypt_private_key(NETWORK_REPLICA_SENTINEL),
            key_algorithm=payload.get("key_algorithm") or "Ed25519",
            status=payload.get("identity_status") or "ACTIVE",
        )
        db.add(ident)
        db.flush()
        created = True
    return created


def _upsert_credential(db: Session, payload: dict[str, Any]) -> bool:
    existing = db.scalar(select(Credential).where(Credential.credential_id == payload["credential_id"]))
    if existing:
        if payload.get("status") == "REVOKED" and existing.status != CredentialStatus.REVOKED:
            existing.status = CredentialStatus.REVOKED
        return False

    if not db.scalar(select(CredentialType).where(CredentialType.code == payload["type_code"])):
        db.add(
            CredentialType(
                code=payload["type_code"],
                category="education",
                display_name=payload["type_code"],
            )
        )
        db.flush()

    org = db.scalar(select(Organization).where(Organization.did == payload["issuer_did"]))
    if not org:
        return False
    holder = db.scalar(select(User).where(User.did == payload["holder_did"]))
    if not holder:
        holder = User(
            email=f"{_safe_name(payload['holder_did'])[:48]}@network.ptn",
            password_hash=hash_password(secrets.token_urlsafe(24)),
            full_name=payload.get("holder_display") or "Network Holder",
            username=None,
            did=payload["holder_did"],
            role=UserRole.INDIVIDUAL,
            is_demo=True,
        )
        db.add(holder)
        db.flush()

    issued = datetime.fromisoformat(payload["issued_at"])
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    cred = Credential(
        credential_id=payload["credential_id"],
        type_code=payload["type_code"],
        title=payload["title"],
        issuer_id=org.id,
        holder_id=holder.id,
        issued_at=issued,
        credential_subject=payload.get("public_subject") or {},
        public_fields=payload.get("public_fields") or [],
        credential_hash=payload["credential_hash"],
        signature=payload["signature"],
        proof_type=payload.get("proof_type") or "Ed25519Signature",
        status=CredentialStatus(payload.get("status") or "ACTIVE"),
        ledger_tx_id=payload.get("ledger_tx_id"),
        metadata_hash=payload.get("metadata_hash"),
        is_demo=bool(payload.get("is_demo")),
    )
    db.add(cred)
    db.flush()
    rev = payload.get("revocation")
    if rev and not cred.revocation:
        ts = datetime.fromisoformat(rev["revoked_at"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        db.add(
            Revocation(
                credential_id=cred.id,
                revoked_by_org_id=org.id,
                reason=rev.get("reason"),
                public_reason=True,
                revoked_at=ts,
            )
        )
        cred.status = CredentialStatus.REVOKED
    return True
