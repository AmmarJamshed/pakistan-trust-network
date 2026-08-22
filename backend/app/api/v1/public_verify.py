from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.credentials.service import CredentialService
from app.database.session import get_db

router = APIRouter(tags=["verification"])


@router.get("/verify/{credential_id}")
def verify_credential(credential_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Public verification — no authentication required."""
    result = CredentialService(db).verify(credential_id)
    db.commit()  # persist audit log
    return result
