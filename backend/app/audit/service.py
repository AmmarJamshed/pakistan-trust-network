from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AuditLog
from app.security.crypto import canonical_json, sha256_hex


class AuditService:
    """Tamper-evident audit log with hash chaining."""

    def __init__(self, db: Session):
        self.db = db

    def _latest_hash(self) -> str | None:
        row = self.db.scalar(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1))
        return row.entry_hash if row else None

    def log(
        self,
        action: str,
        *,
        actor_id: str | None = None,
        actor_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        details = details or {}
        details_hash = sha256_hex(canonical_json(details))
        previous_hash = self._latest_hash()
        entry_payload = {
            "action": action,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details_hash": details_hash,
            "previous_hash": previous_hash,
        }
        entry_hash = sha256_hex(canonical_json(entry_payload))
        row = AuditLog(
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            details_hash=details_hash,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def verify_chain(self, limit: int = 10000) -> dict[str, Any]:
        rows = list(
            self.db.scalars(select(AuditLog).order_by(AuditLog.created_at.asc()).limit(limit)).all()
        )
        errors: list[str] = []
        prev: str | None = None
        for row in rows:
            if row.previous_hash != prev:
                errors.append(f"Audit chain break at {row.id}")
            expected = sha256_hex(
                canonical_json(
                    {
                        "action": row.action,
                        "actor_id": row.actor_id,
                        "actor_type": row.actor_type,
                        "resource_type": row.resource_type,
                        "resource_id": row.resource_id,
                        "details_hash": row.details_hash,
                        "previous_hash": row.previous_hash,
                    }
                )
            )
            if expected != row.entry_hash:
                errors.append(f"Audit hash mismatch at {row.id}")
            prev = row.entry_hash
        return {"valid": len(errors) == 0, "count": len(rows), "errors": errors}
