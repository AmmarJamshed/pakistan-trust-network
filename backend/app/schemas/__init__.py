from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.database.models import CVVisibility, OrgStatus, OrgType, UserRole


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=64)
    account_type: str = Field(default="individual")  # individual | organization


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    username: str | None
    did: str
    role: UserRole
    headline: str | None = None
    country: str | None = None
    is_demo: bool = False

    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    org_type: OrgType
    country: str = "Pakistan"
    website: str | None = None
    email: EmailStr
    description: str | None = None


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    org_type: OrgType
    country: str
    website: str | None
    email: EmailStr
    description: str | None
    status: OrgStatus
    did: str
    is_demo: bool
    demo_label: str | None = None
    has_identity: bool = False

    model_config = {"from_attributes": True}


class IdentityOut(BaseModel):
    issuer_id: str
    public_key: str
    key_algorithm: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialIssueRequest(BaseModel):
    organization_id: UUID
    holder_email: EmailStr | None = None
    holder_did: str | None = None
    type_code: str
    title: str = Field(min_length=2, max_length=300)
    credential_subject: dict[str, Any] = Field(default_factory=dict)
    public_fields: list[str] | None = None


class CredentialOut(BaseModel):
    credential_id: str
    type_code: str
    title: str
    issuer_name: str | None = None
    issuer_did: str | None = None
    holder_did: str | None = None
    issued_at: datetime
    status: str
    credential_hash: str
    ledger_tx_id: str | None
    is_demo: bool = False
    verification_url: str | None = None

    model_config = {"from_attributes": True}


class RevokeRequest(BaseModel):
    reason: str | None = None
    public_reason: bool = True


class CVPublishRequest(BaseModel):
    visibility: CVVisibility = CVVisibility.PUBLIC
    summary: str | None = None


class StatsOut(BaseModel):
    organizations: int
    credentials_issued: int
    credentials_verified: int
    blocks: int
    transactions: int
    active_credentials: int


class TamperDemoRequest(BaseModel):
    credential_id: str
    modified_subject: dict[str, Any]
