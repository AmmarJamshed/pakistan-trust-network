from __future__ import annotations

import secrets
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.database.models import Identity, Organization
from app.security.crypto import encrypt_private_key, generate_ed25519_keypair


def make_org_did() -> str:
    return f"ptn:org:{secrets.token_hex(8)}"


def make_user_did() -> str:
    return f"ptn:user:{secrets.token_hex(8)}"


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:100] or secrets.token_hex(4)


class IdentityService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def create_for_organization(self, organization: Organization, actor_id: str | None = None) -> Identity:
        existing = self.db.scalar(
            select(Identity).where(Identity.organization_id == organization.id)
        )
        if existing:
            return existing

        public_key, private_key = generate_ed25519_keypair()
        identity = Identity(
            organization_id=organization.id,
            issuer_id=organization.did,
            public_key=public_key,
            encrypted_private_key=encrypt_private_key(private_key),
            key_algorithm="Ed25519",
            status="ACTIVE",
        )
        self.db.add(identity)
        self.db.flush()
        # Never return or log private key
        self.audit.log(
            "identity_created",
            actor_id=actor_id or organization.did,
            actor_type="organization",
            resource_type="identity",
            resource_id=identity.issuer_id,
            details={"algorithm": "Ed25519", "public_key_fingerprint": public_key[:16]},
        )
        return identity
