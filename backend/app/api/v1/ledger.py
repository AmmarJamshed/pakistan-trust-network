from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.database.models import LedgerBlock, LedgerTransaction, User
from app.database.session import get_db
from app.ledger.service import LedgerService

router = APIRouter(prefix="/ledger", tags=["ledger"])


def _block_dict(b: LedgerBlock) -> dict:
    return {
        "index": b.index,
        "timestamp": b.timestamp.isoformat(),
        "previous_hash": b.previous_hash,
        "merkle_root": b.merkle_root,
        "validator": b.validator,
        "block_hash": b.block_hash,
        "transaction_count": b.transaction_count,
    }


def _tx_dict(t: LedgerTransaction) -> dict:
    return {
        "transaction_id": t.transaction_id,
        "transaction_type": t.transaction_type,
        "issuer_id": t.issuer_id,
        "credential_id": t.credential_id,
        "credential_hash": t.credential_hash,
        "timestamp": t.timestamp.isoformat(),
        "metadata_hash": t.metadata_hash,
        "block_index": t.block_index,
        # Intentionally omit full digital_signature payload details that aren't needed publicly
        "has_signature": bool(t.digital_signature),
    }


@router.get("/blocks")
def list_blocks(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
    offset: int = 0,
) -> dict:
    total = db.scalar(select(LedgerBlock).order_by(LedgerBlock.index.desc()).limit(1))
    blocks = list(
        db.scalars(
            select(LedgerBlock)
            .order_by(LedgerBlock.index.desc())
            .offset(offset)
            .limit(min(limit, 100))
        ).all()
    )
    return {
        "height": total.index if total else 0,
        "blocks": [_block_dict(b) for b in blocks],
    }


@router.get("/blocks/{height}")
def get_block(height: int, db: Annotated[Session, Depends(get_db)]) -> dict:
    block = LedgerService(db).get_block(height)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    txs = list(
        db.scalars(select(LedgerTransaction).where(LedgerTransaction.block_id == block.id)).all()
    )
    return {**_block_dict(block), "transactions": [_tx_dict(t) for t in txs]}


@router.get("/transactions/{tx_id}")
def get_transaction(tx_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    tx = LedgerService(db).get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _tx_dict(tx)


@router.get("/search")
def search(q: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    result = LedgerService(db).search(q)
    return {
        "blocks": [_block_dict(b) for b in result["blocks"]],
        "transactions": [_tx_dict(t) for t in result["transactions"]],
    }


@router.get("/verify-chain")
def verify_chain(db: Annotated[Session, Depends(get_db)]) -> dict:
    return LedgerService(db).verify_chain()


@router.post("/dev/tamper-block/{height}")
def tamper_block_demo(
    height: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    DEVELOPMENT ONLY: deliberately corrupt a block hash to demonstrate tamper detection.
    Clearly labelled DEMO / SIMULATION. Does not provide a way to forge valid credentials.
    """
    from app.config import settings

    if settings.is_production:
        raise HTTPException(status_code=403, detail="Disabled in production")
    block = LedgerService(db).get_block(height)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    if height == 0:
        raise HTTPException(status_code=400, detail="Cannot tamper genesis in this demo")
    original = block.block_hash
    block.block_hash = "deadbeef" + original[8:]
    db.commit()
    result = LedgerService(db).verify_chain()
    return {
        "disclaimer": "DEMO / SIMULATION — block deliberately corrupted for education",
        "original_hash": original,
        "corrupted_hash": block.block_hash,
        "chain_verification": result,
    }
