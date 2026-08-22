from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Portable JSON: JSONB on PostgreSQL, JSON elsewhere (e.g. SQLite tests)
JSONType = JSON().with_variant(JSONB(), "postgresql")


def _enum(enum_cls: type) -> Enum:
    return Enum(enum_cls, native_enum=False, values_callable=lambda x: [e.value for e in x])

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class UserRole(str, enum.Enum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    ADMIN = "admin"
    VERIFIER = "verifier"


class OrgType(str, enum.Enum):
    UNIVERSITY = "UNIVERSITY"
    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"
    EXAMINATION_BOARD = "EXAMINATION_BOARD"
    TRAINING_PROVIDER = "TRAINING_PROVIDER"
    EMPLOYER = "EMPLOYER"
    PROFESSIONAL_BODY = "PROFESSIONAL_BODY"
    GOVERNMENT = "GOVERNMENT"
    OTHER = "OTHER"


class OrgStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class CredentialStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"


class CVVisibility(str, enum.Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    LINK_ONLY = "LINK_ONLY"


class MembershipRole(str, enum.Enum):
    OWNER = "OWNER"
    ISSUER = "ISSUER"
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    did: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(_enum(UserRole), default=UserRole.INDIVIDUAL, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    headline: Mapped[str | None] = mapped_column(String(300))
    country: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    memberships: Mapped[list[OrganizationMember]] = relationship(back_populates="user")
    credentials_held: Mapped[list[Credential]] = relationship(
        back_populates="holder",
        foreign_keys="Credential.holder_id",
    )
    cv_profile: Mapped[CVProfile | None] = relationship(back_populates="user", uselist=False)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    org_type: Mapped[OrgType] = mapped_column(_enum(OrgType), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="Pakistan")
    website: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[OrgStatus] = mapped_column(
        _enum(OrgStatus),
        default=OrgStatus.PENDING_VERIFICATION,
        nullable=False,
    )
    did: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_label: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    members: Mapped[list[OrganizationMember]] = relationship(back_populates="organization")
    identity: Mapped[Identity | None] = relationship(back_populates="organization", uselist=False)
    credentials_issued: Mapped[list[Credential]] = relationship(back_populates="issuer")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MembershipRole] = mapped_column(_enum(MembershipRole), default=MembershipRole.ISSUER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organization: Mapped[Organization] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class Identity(Base):
    """Institutional cryptographic identity. Private key is encrypted at rest."""

    __tablename__ = "identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    issuer_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_algorithm: Mapped[str] = mapped_column(String(40), default="Ed25519")
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organization: Mapped[Organization] = relationship(back_populates="identity")


class CredentialType(Base):
    __tablename__ = "credential_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)  # education|professional|achievement
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_extensible: Mapped[bool] = mapped_column(Boolean, default=True)


class Credential(Base):
    __tablename__ = "credentials"
    __table_args__ = (
        Index("ix_credentials_issuer_status", "issuer_id", "status"),
        Index("ix_credentials_holder_status", "holder_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    credential_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    type_code: Mapped[str] = mapped_column(String(80), ForeignKey("credential_types.code"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    holder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Off-chain credential subject (never written to ledger as plaintext)
    credential_subject: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    # Fields allowed on public verification page
    public_fields: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    credential_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    proof_type: Mapped[str] = mapped_column(String(40), default="Ed25519Signature")
    status: Mapped[CredentialStatus] = mapped_column(
        _enum(CredentialStatus), default=CredentialStatus.ACTIVE, nullable=False
    )
    ledger_tx_id: Mapped[str | None] = mapped_column(String(80), index=True)
    metadata_hash: Mapped[str | None] = mapped_column(String(64))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    issuer: Mapped[Organization] = relationship(back_populates="credentials_issued")
    holder: Mapped[User] = relationship(back_populates="credentials_held", foreign_keys=[holder_id])
    revocation: Mapped[Revocation | None] = relationship(back_populates="credential", uselist=False)
    shares: Mapped[list[CredentialShare]] = relationship(back_populates="credential")


class CredentialShare(Base):
    __tablename__ = "credential_shares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    credential: Mapped[Credential] = relationship(back_populates="shares")


class Revocation(Base):
    __tablename__ = "revocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credentials.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    revoked_by_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text)
    public_reason: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ledger_tx_id: Mapped[str | None] = mapped_column(String(80), index=True)

    credential: Mapped[Credential] = relationship(back_populates="revocation")


class CVProfile(Base):
    __tablename__ = "cv_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    visibility: Mapped[CVVisibility] = mapped_column(
        _enum(CVVisibility), default=CVVisibility.PRIVATE, nullable=False
    )
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="cv_profile")
    items: Mapped[list[CVItem]] = relationship(back_populates="cv_profile", cascade="all, delete-orphan")


class CVItem(Base):
    __tablename__ = "cv_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cv_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cv_profiles.id", ondelete="CASCADE"), nullable=False
    )
    credential_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credentials.id", ondelete="SET NULL")
    )
    section: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    cv_profile: Mapped[CVProfile] = relationship(back_populates="items")


class LedgerBlock(Base):
    __tablename__ = "ledger_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    index: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(64), nullable=False)
    validator: Mapped[str] = mapped_column(String(80), nullable=False)
    block_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transactions: Mapped[list[LedgerTransaction]] = relationship(back_populates="block")


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        Index("ix_ledger_tx_type", "transaction_type"),
        Index("ix_ledger_tx_credential", "credential_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    transaction_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    issuer_id: Mapped[str | None] = mapped_column(String(80), index=True)
    credential_id: Mapped[str | None] = mapped_column(String(80))
    credential_hash: Mapped[str | None] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    digital_signature: Mapped[str | None] = mapped_column(Text)
    metadata_hash: Mapped[str | None] = mapped_column(String(64))
    block_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_blocks.id", ondelete="SET NULL")
    )
    block_index: Mapped[int | None] = mapped_column(Integer, index=True)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    block: Mapped[LedgerBlock | None] = relationship(back_populates="transactions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_action_created", "action", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(80))
    actor_type: Mapped[str | None] = mapped_column(String(40))
    resource_type: Mapped[str | None] = mapped_column(String(40))
    resource_id: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    details_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
