from __future__ import annotations

import re
import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.deps import get_current_user
from app.database.models import User, UserRole
from app.database.session import get_db
from app.identities.service import make_user_did
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _username_from_name(full_name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "", full_name.lower())[:20] or "user"
    return f"{base}{secrets.token_hex(2)}"


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    username = body.username or _username_from_name(body.full_name)
    if db.scalar(select(User).where(User.username == username)):
        username = f"{username}{secrets.token_hex(2)}"

    role = UserRole.INDIVIDUAL
    if body.account_type == "organization":
        role = UserRole.ORGANIZATION

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        username=username,
        did=make_user_did(),
        role=role,
    )
    db.add(user)
    db.flush()
    AuditService(db).log(
        "user_registered",
        actor_id=user.did,
        actor_type="user",
        resource_type="user",
        resource_id=str(user.id),
        details={"role": role.value},
    )
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value, "did": user.did}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value, "did": user.did}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("not refresh")
        user = db.get(User, uuid.UUID(payload["sub"]))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return TokenResponse(
        access_token=create_access_token(str(user.id), {"role": user.role.value, "did": user.did}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
