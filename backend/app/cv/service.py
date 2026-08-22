from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.database.models import CVItem, CVProfile, CVVisibility, Credential, CredentialStatus, User


SECTION_MAP = {
    "UniversityDegree": "education",
    "Degree": "education",
    "Diploma": "education",
    "Certificate": "education",
    "Transcript": "education",
    "CourseCompletion": "education",
    "Scholarship": "education",
    "AcademicAward": "awards",
    "Employment": "employment",
    "Internship": "employment",
    "ProfessionalCertification": "certifications",
    "Training": "certifications",
    "License": "certifications",
    "Award": "awards",
    "Competition": "achievements",
    "Publication": "publications",
    "Project": "projects",
    "SkillEvidence": "skills",
}


class CVService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def get_or_create(self, user: User) -> CVProfile:
        profile = user.cv_profile or self.db.scalar(
            select(CVProfile).where(CVProfile.user_id == user.id)
        )
        if profile:
            return profile
        username = user.username or f"user-{secrets.token_hex(4)}"
        profile = CVProfile(
            user_id=user.id,
            username=username,
            visibility=CVVisibility.PRIVATE,
            summary=user.headline,
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def sync_from_wallet(self, user: User) -> CVProfile:
        profile = self.get_or_create(user)
        # Clear and rebuild from verified credentials
        for item in list(profile.items):
            self.db.delete(item)
        self.db.flush()

        creds = list(
            self.db.scalars(
                select(Credential).where(
                    Credential.holder_id == user.id,
                    Credential.status == CredentialStatus.ACTIVE,
                )
            ).all()
        )
        for i, cred in enumerate(creds):
            section = SECTION_MAP.get(cred.type_code, "achievements")
            item = CVItem(
                cv_profile_id=profile.id,
                credential_id=cred.id,
                section=section,
                title=cred.title,
                subtitle=cred.issuer.name,
                sort_order=i,
                is_visible=True,
            )
            self.db.add(item)
        self.db.flush()
        return profile

    def publish(
        self,
        user: User,
        visibility: CVVisibility = CVVisibility.PUBLIC,
        summary: str | None = None,
    ) -> CVProfile:
        profile = self.sync_from_wallet(user)
        profile.visibility = visibility
        if summary is not None:
            profile.summary = summary
        if visibility == CVVisibility.LINK_ONLY and not profile.share_token:
            profile.share_token = secrets.token_urlsafe(24)
        if visibility == CVVisibility.PUBLIC:
            profile.published_at = datetime.now(timezone.utc)
        elif visibility == CVVisibility.LINK_ONLY:
            profile.published_at = datetime.now(timezone.utc)
        self.db.flush()
        self.audit.log(
            "cv_published",
            actor_id=user.did,
            actor_type="user",
            resource_type="cv",
            resource_id=profile.username,
            details={"visibility": visibility.value},
        )
        return profile

    def unpublish(self, user: User) -> CVProfile:
        profile = self.get_or_create(user)
        profile.visibility = CVVisibility.PRIVATE
        profile.published_at = None
        self.db.flush()
        self.audit.log(
            "cv_unpublished",
            actor_id=user.did,
            actor_type="user",
            resource_type="cv",
            resource_id=profile.username,
        )
        return profile

    def public_view(self, username: str, share_token: str | None = None) -> dict[str, Any] | None:
        profile = self.db.scalar(select(CVProfile).where(CVProfile.username == username))
        if not profile:
            return None
        if profile.visibility == CVVisibility.PRIVATE:
            return None
        if profile.visibility == CVVisibility.LINK_ONLY:
            if not share_token or share_token != profile.share_token:
                return None

        user = profile.user
        sections: dict[str, list[dict[str, Any]]] = {}
        for item in sorted(profile.items, key=lambda x: x.sort_order):
            if not item.is_visible:
                continue
            cred = None
            if item.credential_id:
                cred = self.db.get(Credential, item.credential_id)
            entry = {
                "title": item.title,
                "subtitle": item.subtitle,
                "verified": bool(cred and cred.status == CredentialStatus.ACTIVE),
                "credential_id": cred.credential_id if cred else None,
                "status": cred.status.value if cred else None,
            }
            sections.setdefault(item.section, []).append(entry)

        return {
            "username": profile.username,
            "full_name": user.full_name,
            "headline": user.headline,
            "summary": profile.summary,
            "visibility": profile.visibility.value,
            "published_at": profile.published_at.isoformat() if profile.published_at else None,
            "sections": sections,
            "disclaimer": "PTN verifies institutional issuance of credentials. Not a government endorsement.",
        }
