from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.cv.service import CVService
from app.database.models import CVVisibility, User
from app.database.session import get_db
from app.schemas import CVPublishRequest

router = APIRouter(prefix="/cv", tags=["cv"])


@router.get("/me")
def my_cv(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    profile = CVService(db).sync_from_wallet(user)
    db.commit()
    return {
        "username": profile.username,
        "visibility": profile.visibility.value,
        "summary": profile.summary,
        "share_token": profile.share_token,
        "public_url": f"{settings.ptn_frontend_url}/cv/{profile.username}"
        if profile.visibility != CVVisibility.PRIVATE
        else None,
        "items": [
            {
                "section": i.section,
                "title": i.title,
                "subtitle": i.subtitle,
                "credential_id": None,
            }
            for i in profile.items
        ],
    }


@router.post("/publish")
def publish_cv(
    body: CVPublishRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    profile = CVService(db).publish(user, visibility=body.visibility, summary=body.summary)
    db.commit()
    url = f"{settings.ptn_frontend_url}/cv/{profile.username}"
    if profile.visibility == CVVisibility.LINK_ONLY and profile.share_token:
        url = f"{url}?token={profile.share_token}"
    return {
        "username": profile.username,
        "visibility": profile.visibility.value,
        "public_url": url,
        "share_token": profile.share_token,
        "qr_target": url,
    }


@router.post("/unpublish")
def unpublish_cv(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    profile = CVService(db).unpublish(user)
    db.commit()
    return {"username": profile.username, "visibility": profile.visibility.value}


@router.get("/{username}")
def public_cv(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    token: str | None = None,
) -> dict:
    data = CVService(db).public_view(username, share_token=token)
    if not data:
        raise HTTPException(status_code=404, detail="CV not found or not public")
    return data
