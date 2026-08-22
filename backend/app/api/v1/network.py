from fastapi import APIRouter

from app.network.sync import status, sync_once

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/status")
def network_status() -> dict:
    """Public status of the Git-backed localhost mesh."""
    return status()


@router.post("/sync")
def trigger_sync() -> dict:
    """Pull proofs from GitHub, merge into this node, push if credentials exist."""
    return sync_once()
