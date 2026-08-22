from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.database.models import (
    Credential,
    CredentialStatus,
    CredentialType,
    Identity,
    Organization,
    OrgStatus,
    Revocation,
    User,
)
from app.ledger.service import LedgerService
from app.network.constants import NETWORK_REPLICA_SENTINEL
from app.security.crypto import (
    canonical_json,
    decrypt_private_key,
    hash_credential_payload,
    sign_ed25519,
    verify_ed25519,
)


DEFAULT_PUBLIC_FIELDS = ["title", "type", "issuer_name", "issued_at", "status"]


def _credential_id() -> str:
    return f"ptn:cred:{secrets.token_hex(12)}"


def _signing_key(identity: Identity) -> str:
    private_key = decrypt_private_key(identity.encrypted_private_key)
    if private_key == NETWORK_REPLICA_SENTINEL:
        raise ValueError(
            "This organization was replicated from the Git network and has no local signing key"
        )
    return private_key


class CredentialService:
    def __init__(self, db: Session):
        self.db = db
        self.ledger = LedgerService(db)
        self.audit = AuditService(db)

    def _signing_message(self, credential_hash: str, issuer_did: str, credential_id: str) -> str:
        return canonical_json(
            {
                "credential_hash": credential_hash,
                "issuer": issuer_did,
                "credential_id": credential_id,
            }
        )

    def issue(
        self,
        *,
        organization: Organization,
        holder: User,
        type_code: str,
        title: str,
        credential_subject: dict[str, Any],
        public_fields: list[str] | None = None,
        actor_id: str | None = None,
        is_demo: bool = False,
    ) -> Credential:
        if organization.status not in (OrgStatus.VERIFIED, OrgStatus.PENDING_VERIFICATION):
            # Allow pending for demo MVP but suspend/revoke cannot issue
            if organization.status in (OrgStatus.SUSPENDED, OrgStatus.REVOKED):
                raise ValueError("Organization cannot issue credentials in current status")

        identity = organization.identity or self.db.scalar(
            select(Identity).where(Identity.organization_id == organization.id)
        )
        if not identity:
            raise ValueError("Organization has no cryptographic identity")

        ctype = self.db.scalar(select(CredentialType).where(CredentialType.code == type_code))
        if not ctype:
            raise ValueError(f"Unknown credential type: {type_code}")

        # Strip sensitive keys from subject before hashing (defense in depth)
        safe_subject = {
            k: v
            for k, v in credential_subject.items()
            if k.lower()
            not in {
                "cnic",
                "passport",
                "passport_number",
                "address",
                "phone",
                "email",
                "date_of_birth",
                "dob",
                "salary",
                "biometric",
            }
        }

        cred_id = _credential_id()
        issued_payload = {
            "credential_id": cred_id,
            "type": type_code,
            "issuer": organization.did,
            "holder": holder.did,
            "title": title,
            "credential_subject": safe_subject,
        }
        credential_hash = hash_credential_payload(issued_payload)
        metadata_hash = hash_credential_payload(
            {"title": title, "type": type_code, "issuer_name": organization.name}
        )

        private_key = _signing_key(identity)
        message = self._signing_message(credential_hash, organization.did, cred_id)
        signature = sign_ed25519(message, private_key)

        credential = Credential(
            credential_id=cred_id,
            type_code=type_code,
            title=title,
            issuer_id=organization.id,
            holder_id=holder.id,
            credential_subject=safe_subject,
            public_fields=public_fields or DEFAULT_PUBLIC_FIELDS,
            credential_hash=credential_hash,
            signature=signature,
            proof_type="Ed25519Signature",
            status=CredentialStatus.ACTIVE,
            metadata_hash=metadata_hash,
            is_demo=is_demo or organization.is_demo,
        )
        self.db.add(credential)
        self.db.flush()

        tx = self.ledger.append_transaction(
            transaction_type="CREDENTIAL_ISSUED",
            issuer_id=organization.did,
            credential_id=cred_id,
            credential_hash=credential_hash,
            digital_signature=signature,
            metadata_hash=metadata_hash,
            payload={
                "type": type_code,
                "issuer_name": organization.name,
                "holder_did": holder.did,
            },
        )
        credential.ledger_tx_id = tx.transaction_id
        self.db.flush()

        self.audit.log(
            "credential_issued",
            actor_id=actor_id or organization.did,
            actor_type="organization",
            resource_type="credential",
            resource_id=cred_id,
            details={"issuer": organization.did, "holder": holder.did, "type": type_code},
        )
        return credential

    def revoke(
        self,
        *,
        credential: Credential,
        organization: Organization,
        reason: str | None = None,
        public_reason: bool = True,
        actor_id: str | None = None,
    ) -> Credential:
        if credential.issuer_id != organization.id:
            raise PermissionError("Only the issuing organization can revoke this credential")
        if credential.status == CredentialStatus.REVOKED:
            raise ValueError("Credential already revoked")

        identity = organization.identity
        if not identity:
            raise ValueError("Organization has no cryptographic identity")

        credential.status = CredentialStatus.REVOKED
        private_key = _signing_key(identity)
        revoke_payload = {
            "action": "REVOKE",
            "credential_id": credential.credential_id,
            "credential_hash": credential.credential_hash,
        }

        meta_hash = hash_credential_payload(revoke_payload)
        message = canonical_json(revoke_payload)
        signature = sign_ed25519(message, private_key)

        tx = self.ledger.append_transaction(
            transaction_type="CREDENTIAL_REVOKED",
            issuer_id=organization.did,
            credential_id=credential.credential_id,
            credential_hash=credential.credential_hash,
            digital_signature=signature,
            metadata_hash=meta_hash,
            payload={"reason_public": public_reason},
        )

        revocation = Revocation(
            credential_id=credential.id,
            revoked_by_org_id=organization.id,
            reason=reason,
            public_reason=public_reason,
            ledger_tx_id=tx.transaction_id,
        )
        self.db.add(revocation)
        credential.ledger_tx_id = tx.transaction_id  # latest status tx
        self.db.flush()

        self.audit.log(
            "credential_revoked",
            actor_id=actor_id or organization.did,
            actor_type="organization",
            resource_type="credential",
            resource_id=credential.credential_id,
            details={"reason": reason if public_reason else None},
        )
        return credential

    def verify(self, credential_id: str, tamper_subject: dict[str, Any] | None = None) -> dict[str, Any]:
        """Full cryptographic + ledger + revocation verification."""
        credential = self.db.scalar(
            select(Credential).where(Credential.credential_id == credential_id)
        )
        if not credential:
            return {
                "found": False,
                "credential_id": credential_id,
                "overall": "NOT_FOUND",
                "checks": {},
            }

        organization = credential.issuer
        identity = organization.identity
        holder = credential.holder

        subject = tamper_subject if tamper_subject is not None else credential.credential_subject
        reconstructed = {
            "credential_id": credential.credential_id,
            "type": credential.type_code,
            "issuer": organization.did,
            "holder": holder.did,
            "title": credential.title,
            "credential_subject": subject,
        }
        computed_hash = hash_credential_payload(reconstructed)
        integrity_ok = computed_hash == credential.credential_hash and tamper_subject is None
        if tamper_subject is not None:
            integrity_ok = computed_hash == credential.credential_hash

        message = self._signing_message(
            credential.credential_hash, organization.did, credential.credential_id
        )
        signature_ok = False
        issuer_ok = False
        if identity:
            issuer_ok = identity.status == "ACTIVE" and bool(identity.public_key)
            signature_ok = verify_ed25519(message, credential.signature, identity.public_key)

        ledger_ok = False
        ledger_tx = None
        if credential.ledger_tx_id:
            ledger_tx = self.ledger.get_transaction(credential.ledger_tx_id)
            if ledger_tx and ledger_tx.credential_hash == credential.credential_hash:
                ledger_ok = True
            # Also accept issuance tx by credential id
            if not ledger_ok:
                from sqlalchemy import select as sel
                from app.database.models import LedgerTransaction

                issuance = self.db.scalar(
                    sel(LedgerTransaction).where(
                        LedgerTransaction.credential_id == credential.credential_id,
                        LedgerTransaction.transaction_type == "CREDENTIAL_ISSUED",
                    )
                )
                if issuance and issuance.credential_hash == credential.credential_hash:
                    ledger_ok = True
                    ledger_tx = issuance

        chain = self.ledger.verify_chain()
        chain_ok = chain["valid"]

        status = credential.status.value
        revoked = credential.status == CredentialStatus.REVOKED
        revocation_info = None
        if credential.revocation:
            revocation_info = {
                "revoked_at": credential.revocation.revoked_at.isoformat(),
                "issuer": organization.name,
                "reason": credential.revocation.reason
                if credential.revocation.public_reason
                else None,
            }

        checks = {
            "issuer_verified": issuer_ok,
            "signature_verified": signature_ok,
            "credential_integrity_verified": integrity_ok and tamper_subject is None,
            "ledger_proof_verified": ledger_ok,
            "chain_integrity_verified": chain_ok,
            "credential_active": not revoked,
        }

        # If deliberately verifying a modified payload
        if tamper_subject is not None:
            checks["credential_integrity_verified"] = False
            checks["tamper_demonstration"] = True

        overall_ok = all(
            [
                checks["issuer_verified"],
                checks["signature_verified"],
                checks["credential_integrity_verified"],
                checks["ledger_proof_verified"],
                not revoked,
            ]
        )

        if revoked:
            overall = "REVOKED"
        elif overall_ok:
            overall = "VERIFIED"
        else:
            overall = "FAILED"

        # Public-safe display fields only
        public_subject = {
            k: v
            for k, v in credential.credential_subject.items()
            if k in (credential.public_fields or []) or k in {"degree", "role", "program", "skill"}
        }

        self.audit.log(
            "credential_verified",
            actor_type="public",
            resource_type="credential",
            resource_id=credential.credential_id,
            details={"overall": overall},
        )

        return {
            "found": True,
            "credential_id": credential.credential_id,
            "title": credential.title,
            "type": credential.type_code,
            "issuer": {
                "name": organization.name,
                "did": organization.did,
                "is_demo": organization.is_demo,
                "demo_label": organization.demo_label,
                "status": organization.status.value,
            },
            "holder": {
                "display_name": holder.full_name.split(" ")[0] + (" " + holder.full_name.split(" ")[-1][0] + "." if len(holder.full_name.split()) > 1 else ""),
                "did": holder.did,
            },
            "issued_at": credential.issued_at.isoformat(),
            "status": status,
            "overall": overall,
            "checks": checks,
            "ledger_transaction": ledger_tx.transaction_id if ledger_tx else None,
            "credential_hash": credential.credential_hash,
            "block_index": ledger_tx.block_index if ledger_tx else None,
            "revocation": revocation_info,
            "public_subject": public_subject,
            "proof": {"type": credential.proof_type},
        }
